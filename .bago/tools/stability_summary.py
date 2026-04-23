#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
stability_summary.py — Resumen único de estabilidad operacional.

Lee los últimos informes de sandbox (smoke, VM, soak, matrix) y el estado
de los validadores canónicos (validate_manifest, validate_state) para
emitir un bloque conciso de salud antes de avanzar a implementación.

Salida:
  GO   → todos los gates en verde; se puede avanzar a W2.
  WARN → algún gate advertido pero no bloqueante.
  KO   → al menos un gate bloqueante; no avanzar hasta reparar.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BAGO_ROOT = Path(__file__).resolve().parents[1]

# ── helpers ───────────────────────────────────────────────────────────────────

def load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def run_validator(script: str) -> tuple[str, str]:
    """Returns (status, output) where status is 'GO' or 'KO'."""
    result = subprocess.run(
        [sys.executable, str(BAGO_ROOT / "tools" / script)],
        capture_output=True,
        text=True,
    )
    out = (result.stdout + result.stderr).strip()
    status = "GO" if result.returncode == 0 else "KO"
    return status, out


def report_gate(name: str, report: dict | None) -> tuple[str, str]:
    """Returns (status, summary_line)."""
    if report is None:
        return "WARN", f"{name}: no disponible"
    overall = report.get("status", report.get("overall_status", "unknown"))
    failures = report.get("failure_count", "n/a")
    workers = report.get("workers", "n/a")
    duration = report.get("duration_seconds", "n/a")
    st = "GO" if str(overall).lower() in ("pass", "ok", "green", "success") else "KO"
    return st, f"{name}: status={overall}, failures={failures}, workers={workers}, duration={duration}s"


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    as_json = "--json" in sys.argv

    if not as_json:
        print("BAGO stability summary")
        print("=" * 44)

    gates: list[tuple[str, str]] = []

    # 1. Canonical validators
    for script, label in [("validate_manifest.py", "validate_manifest"), ("validate_state.py", "validate_state")]:
        st, out = run_validator(script)
        # extract first meaningful line
        first_line = next((l for l in out.splitlines() if l.strip()), out)
        gates.append((st, f"{label}: {first_line}"))

    # 2. Sandbox reports
    report_paths = {
        "smoke":  ROOT / "sandbox/runtime/last-report.json",
        "vm":     ROOT / "sandbox/runtime-vm/last-report-vm.json",
        "soak":   ROOT / "sandbox/runtime-vm/last-soak-report-vm.json",
        "matrix": ROOT / "sandbox/runtime-vm/matrix/last-matrix-summary.json",
    }
    for name, path in report_paths.items():
        report = load_json(path)
        st, line = report_gate(name, report)
        gates.append((st, line))

    # 3. Task W2 staleness
    task_data = load_json(BAGO_ROOT / "state" / "pending_w2_task.json")
    if task_data is not None and task_data.get("status") != "done":
        accepted_at_str = task_data.get("accepted_at")
        if accepted_at_str:
            try:
                accepted_at = datetime.fromisoformat(accepted_at_str)
                if accepted_at.tzinfo is None:
                    accepted_at = accepted_at.replace(tzinfo=timezone.utc)
                days_open = (datetime.now(timezone.utc) - accepted_at).days
                if days_open > 3:
                    title = task_data.get("idea_title", "?")
                    gates.append(("WARN", f"task_stale: '{title}' lleva {days_open}d abierta sin completarse"))
            except Exception:
                pass

    # 4. Print gates / JSON
    has_ko = any(st == "KO" for st, _ in gates)
    has_warn = any(st == "WARN" for st, _ in gates)
    decision = "KO" if has_ko else ("WARN" if has_warn else "GO")

    if as_json:
        print(json.dumps({
            "decision": decision,
            "gates": [{"status": st, "detail": line} for st, line in gates],
        }, indent=2, ensure_ascii=False))
        return 1 if has_ko else 0

    print()
    for st, line in gates:
        icon = "✓" if st == "GO" else ("⚠" if st == "WARN" else "✗")
        print(f"  [{st}] {icon} {line}")

    # 5. Overall decision
    print()
    if has_ko:
        print("DECISIÓN: KO — reparar antes de avanzar a W2.")
        print("  → Ejecuta `python3 .bago/tools/validate_pack.py` para diagnóstico completo.")
        return 1
    elif has_warn:
        print("DECISIÓN: WARN — sandbox no disponible; validadores canónicos en verde.")
        print("  → Puedes avanzar a W2 si el trabajo no depende del sandbox.")
        return 0
    else:
        print("DECISIÓN: GO — todos los gates en verde. Avanzar a W2.")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
