#!/usr/bin/env python3
"""ci_baseline.py — Herramienta #99: Gestión de baselines de findings para CI.

Guarda un snapshot de findings como baseline y permite comparar futuras
ejecuciones contra él. Salida con exit 0 si no hay regresión, exit 1 si
aparecen hallazgos NUEVOS respecto al baseline.

Uso:
    bago ci-baseline save   [--file BASELINE] [--from-scan TARGET]
    bago ci-baseline compare [--file BASELINE] [--from-scan TARGET]
    bago ci-baseline status  [--file BASELINE]
    bago ci-baseline diff    [--file BASELINE] [--from-scan TARGET]
    python3 ci_baseline.py --test

Opciones:
    save     Guarda baseline actual (sobreescribe si existe)
    compare  Compara scan actual con baseline — exit 1 si hay regresión
    status   Muestra info del baseline guardado
    diff     Muestra hallazgos nuevos/resueltos/persistentes
    --file   Ruta del archivo baseline (default: .bago/state/ci_baseline.json)
    --from-scan  Target a escanear (default: ./ via bago-lint)
    --json   Output en JSON
    --test   Self-tests
"""
from __future__ import annotations

import json
import subprocess
import sys
import os
import datetime
from pathlib import Path
from typing import Optional

BAGO_ROOT = Path(__file__).parent.parent
DEFAULT_BASELINE = BAGO_ROOT / "state" / "ci_baseline.json"
TOOLS = BAGO_ROOT / "tools"


# ─── Finding helpers ───────────────────────────────────────────────────────

def _identity(f: dict) -> tuple:
    """Clave de identidad estable entre ejecuciones."""
    return (f.get("file", ""), f.get("line", 0), f.get("rule", ""))


def _run_scan(target: str) -> list[dict]:
    """Ejecuta bago-lint --json en target y devuelve findings."""
    try:
        r = subprocess.run(
            [sys.executable, str(TOOLS / "bago_lint_cli.py"), target, "--json"],
            capture_output=True, text=True, timeout=60
        )
        data = json.loads(r.stdout)
        return data.get("findings", []) if isinstance(data, dict) else []
    except Exception:
        return []


# ─── Operaciones ───────────────────────────────────────────────────────────

def save_baseline(findings: list[dict], baseline_path: Path,
                  target: str = "") -> dict:
    """Guarda findings como baseline en JSON."""
    data = {
        "saved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "target": target,
        "count": len(findings),
        "findings": findings,
        "identities": [list(_identity(f)) for f in findings],
    }
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    baseline_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


def load_baseline(baseline_path: Path) -> Optional[dict]:
    """Carga baseline desde JSON. None si no existe."""
    if not baseline_path.exists():
        return None
    try:
        return json.loads(baseline_path.read_text(encoding="utf-8"))
    except Exception:
        return None


def diff_findings(baseline_findings: list[dict],
                  current_findings: list[dict]) -> dict:
    """Compara dos listas de findings. Devuelve new/fixed/persistent."""
    base_ids  = {_identity(f) for f in baseline_findings}
    curr_ids  = {_identity(f) for f in current_findings}

    new_ids        = curr_ids - base_ids
    fixed_ids      = base_ids - curr_ids
    persistent_ids = base_ids & curr_ids

    new        = [f for f in current_findings  if _identity(f) in new_ids]
    fixed      = [f for f in baseline_findings if _identity(f) in fixed_ids]
    persistent = [f for f in current_findings  if _identity(f) in persistent_ids]

    return {"new": new, "fixed": fixed, "persistent": persistent}


# ─── CLI ───────────────────────────────────────────────────────────────────

_RED  = "\033[0;31m"
_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RST  = "\033[0m"
_BOLD = "\033[1m"


def main(argv: list[str]) -> int:
    if not argv:
        print("Uso: bago ci-baseline <save|compare|status|diff> [opciones]")
        return 1

    subcmd    = argv[0]
    baseline  = DEFAULT_BASELINE
    target    = "./"
    as_json   = False

    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--file" and i + 1 < len(argv):
            baseline = Path(argv[i + 1]); i += 2
        elif a == "--from-scan" and i + 1 < len(argv):
            target = argv[i + 1]; i += 2
        elif a == "--json":
            as_json = True; i += 1
        else:
            i += 1

    # ── save ──────────────────────────────────────────────────────────
    if subcmd == "save":
        print(f"Escaneando {target}...")
        findings = _run_scan(target)
        data = save_baseline(findings, baseline, target)
        if as_json:
            print(json.dumps(data, indent=2))
        else:
            print(f"{_GRN}✅ Baseline guardado:{_RST} {baseline}")
            print(f"   Hallazgos: {len(findings)}  |  Fecha: {data['saved_at'][:19]}")
        return 0

    # ── status ────────────────────────────────────────────────────────
    if subcmd == "status":
        data = load_baseline(baseline)
        if not data:
            print(f"{_YEL}⚠️  No existe baseline en {baseline}{_RST}")
            return 1
        if as_json:
            print(json.dumps({k: v for k, v in data.items() if k != "findings"}, indent=2))
        else:
            print(f"\n{_BOLD}CI Baseline — {baseline}{_RST}")
            print(f"  Guardado:   {data.get('saved_at','?')[:19]}")
            print(f"  Target:     {data.get('target','?')}")
            print(f"  Hallazgos:  {data.get('count', len(data.get('findings', [])))}")
        return 0

    # ── compare / diff ────────────────────────────────────────────────
    if subcmd in ("compare", "diff"):
        data = load_baseline(baseline)
        if not data:
            print(f"{_RED}ERROR: No existe baseline. Ejecuta: bago ci-baseline save{_RST}")
            return 2

        print(f"Escaneando {target}...")
        current = _run_scan(target)
        result  = diff_findings(data.get("findings", []), current)

        new        = result["new"]
        fixed      = result["fixed"]
        persistent = result["persistent"]

        if as_json:
            print(json.dumps(result, indent=2))
            return 1 if new else 0

        print(f"\n{_BOLD}CI Baseline diff{_RST}  (baseline: {data.get('saved_at','?')[:19]})\n")
        if new:
            print(f"  {_RED}🔴 Nuevos ({len(new)}):{_RST}")
            for f in new[:10]:
                print(f"    {f.get('file','')}:{f.get('line','')}  [{f.get('rule','')}]  {f.get('message','')[:60]}")
            if len(new) > 10:
                print(f"    ... y {len(new)-10} más")
        if fixed:
            print(f"  {_GRN}✅ Resueltos ({len(fixed)}):{_RST}")
            for f in fixed[:5]:
                print(f"    {f.get('file','')}:{f.get('line','')}  [{f.get('rule','')}]")
        if persistent:
            print(f"  ⚪ Persistentes: {len(persistent)}")

        print()
        if new:
            print(f"  {_RED}❌ REGRESIÓN — {len(new)} hallazgo(s) nuevo(s){_RST}")
            return 1
        else:
            print(f"  {_GRN}✅ SIN REGRESIÓN — el baseline se mantiene{_RST}")
            return 0

    print(f"Subcomando desconocido: {subcmd}")
    return 1


# ─── Self-tests ────────────────────────────────────────────────────────────

def _self_test() -> None:
    import tempfile

    print("Tests de ci_baseline.py...")
    fails: list[str] = []

    def ok(name: str) -> None:
        print(f"  OK: {name}")

    def fail(name: str, msg: str) -> None:
        fails.append(name)
        print(f"  FAIL: {name}: {msg}")

    SAMPLE = [
        {"file": "a.py", "line": 1, "rule": "BAGO-E001", "message": "bare except"},
        {"file": "a.py", "line": 5, "rule": "BAGO-W001", "message": "utcnow"},
        {"file": "b.py", "line": 3, "rule": "BAGO-I002", "message": "TODO"},
    ]

    tmp = Path(tempfile.mktemp(suffix=".json"))

    # T1 — save crea archivo con estructura correcta
    data = save_baseline(SAMPLE, tmp, target="./test")
    if tmp.exists() and data["count"] == 3 and "saved_at" in data:
        ok("ci_baseline:save_creates_file")
    else:
        fail("ci_baseline:save_creates_file", "archivo no creado o estructura incorrecta")

    # T2 — load devuelve los mismos datos
    loaded = load_baseline(tmp)
    if loaded and loaded["count"] == 3 and len(loaded["findings"]) == 3:
        ok("ci_baseline:load_returns_data")
    else:
        fail("ci_baseline:load_returns_data", f"loaded: {loaded}")

    # T3 — diff_findings: sin cambios → todo persistente  # noqa: BAGO-I002
    result = diff_findings(SAMPLE, SAMPLE)
    if not result["new"] and not result["fixed"] and len(result["persistent"]) == 3:
        ok("ci_baseline:diff_no_changes")
    else:
        fail("ci_baseline:diff_no_changes", f"new={len(result['new'])} fixed={len(result['fixed'])}")

    # T4 — diff_findings: nuevo hallazgo detectado
    new_findings = SAMPLE + [{"file": "c.py", "line": 1, "rule": "JS-E001", "message": "eval"}]
    result2 = diff_findings(SAMPLE, new_findings)
    if len(result2["new"]) == 1 and result2["new"][0]["rule"] == "JS-E001":
        ok("ci_baseline:diff_detects_new")
    else:
        fail("ci_baseline:diff_detects_new", f"new={result2['new']}")

    # T5 — diff_findings: hallazgo resuelto detectado
    fewer = SAMPLE[:2]
    result3 = diff_findings(SAMPLE, fewer)
    if len(result3["fixed"]) == 1 and result3["fixed"][0]["rule"] == "BAGO-I002":
        ok("ci_baseline:diff_detects_fixed")
    else:
        fail("ci_baseline:diff_detects_fixed", f"fixed={result3['fixed']}")

    # T6 — load de archivo inexistente → None
    missing = load_baseline(Path("/tmp/no_existe_jamas.json"))
    if missing is None:
        ok("ci_baseline:load_missing_returns_none")
    else:
        fail("ci_baseline:load_missing_returns_none", "no devolvió None")

    tmp.unlink(missing_ok=True)
    total = 6
    passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails:
        raise SystemExit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        raise SystemExit(main(sys.argv[1:]))
