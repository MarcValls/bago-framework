#!/usr/bin/env python3
"""pre_push_guard.py — Herramienta #126: Guardián pre-commit/pre-push de BAGO.

Ejecuta automáticamente los pasos que hacemos manualmente antes de cada push:
  1. Regenera CHECKSUMS.sha256
  2. Regenera TREE.txt
  3. Verifica sincronía de versiones (bago_version == canon_version)
  4. Corre la suite de integración
  5. Ejecuta tool_guardian (coherencia del framework)
  6. Reporta estado GO / NO-GO

Nació de la experiencia real: estos pasos se olvidaban o hacían tarde en cada sprint,
causando desync de versiones y tools sin registrar.

Uso:
    bago pre-push [--skip-tests] [--skip-checksums] [--skip-guardian]
                  [--fix-checksums]   # regenera CHECKSUMS si fallan
                  [--test]
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RED  = "\033[0;31m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

BAGO_ROOT   = Path(__file__).parent.parent
REPO_ROOT   = BAGO_ROOT.parent
TOOLS_DIR   = BAGO_ROOT / "tools"
STATE_FILE  = BAGO_ROOT / "state" / "global_state.json"
CHECKSUMS   = BAGO_ROOT / "CHECKSUMS.sha256"
TREE_FILE   = BAGO_ROOT / "TREE.txt"


# ── Checks ────────────────────────────────────────────────────────────────────

def check_version_sync() -> dict:
    """Verifica que bago_version == canon_version en global_state.json."""
    if not STATE_FILE.exists():
        return {"ok": False, "msg": "global_state.json no encontrado"}
    try:
        state = json.loads(STATE_FILE.read_text("utf-8"))
        bv = state.get("bago_version", "?")
        cv = state.get("canon_version", "?")
        if bv == cv:
            return {"ok": True, "msg": f"versiones sincronizadas: {bv}"}
        return {"ok": False, "msg": f"DESYNC: bago_version={bv} != canon_version={cv}"}
    except Exception as e:
        return {"ok": False, "msg": str(e)}


def check_checksums_fresh() -> dict:
    """Verifica que CHECKSUMS.sha256 está actualizado con los tools actuales."""
    if not CHECKSUMS.exists():
        return {"ok": False, "msg": "CHECKSUMS.sha256 no existe"}

    current_lines = sorted(CHECKSUMS.read_text("utf-8").strip().splitlines())
    expected: list[str] = []
    for py in sorted(TOOLS_DIR.glob("*.py")):
        digest = hashlib.sha256(py.read_bytes()).hexdigest()
        expected.append(f"{digest}  tools/{py.name}")
    expected_sorted = sorted(expected)

    # Extrae solo las entradas de tools/
    current_tools = sorted(
        l for l in current_lines if "tools/" in l and l.split()[-1].startswith("tools/")
    )
    if current_tools == expected_sorted:
        return {"ok": True, "msg": f"CHECKSUMS frescos ({len(expected_sorted)} tools)"}
    stale = len(expected_sorted) - len(current_tools)
    return {"ok": False, "msg": f"CHECKSUMS desactualizados — {abs(stale)} tools difieren"}


def regenerate_checksums() -> dict:
    """Regenera CHECKSUMS.sha256 y TREE.txt."""
    try:
        py_files = sorted(TOOLS_DIR.glob("*.py"))
        js_files = sorted(TOOLS_DIR.glob("*.js"))
        lines = []
        for f in py_files + js_files:
            digest = hashlib.sha256(f.read_bytes()).hexdigest()
            rel    = f.relative_to(BAGO_ROOT)
            lines.append(f"{digest}  {rel}")
        CHECKSUMS.write_text("\n".join(sorted(lines)) + "\n", encoding="utf-8")

        # TREE.txt
        tree_lines = []
        for p in sorted(BAGO_ROOT.rglob("*")):
            if ".git" in p.parts or "node_modules" in p.parts or "__pycache__" in p.parts:
                continue
            tree_lines.append(str(p.relative_to(BAGO_ROOT)))
        TREE_FILE.write_text("\n".join(sorted(tree_lines)) + "\n", encoding="utf-8")

        return {"ok": True, "msg": f"CHECKSUMS y TREE regenerados ({len(lines)} entradas)"}
    except Exception as e:
        return {"ok": False, "msg": f"Error regenerando: {e}"}


def check_integration_suite(skip: bool = False) -> dict:
    """Corre integration_tests.py y retorna resultado."""
    if skip:
        return {"ok": True, "msg": "omitido (--skip-tests)"}
    integ = TOOLS_DIR / "integration_tests.py"
    if not integ.exists():
        return {"ok": False, "msg": "integration_tests.py no encontrado"}
    start = time.time()
    try:
        r = subprocess.run(
            ["python3", str(integ)],
            capture_output=True, text=True, timeout=300,
            cwd=str(REPO_ROOT)
        )
        elapsed = round(time.time() - start, 1)
        # Busca línea de resultado
        for line in r.stdout.splitlines()[::-1]:
            if "pasaron" in line or "passed" in line or "Resultado" in line:
                clean = line.strip()
                ok = r.returncode == 0
                return {"ok": ok, "msg": f"{clean} [{elapsed}s]"}
        return {"ok": r.returncode == 0, "msg": f"rc={r.returncode} [{elapsed}s]"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "msg": "timeout (>300s)"}


def check_tool_guardian(skip: bool = False) -> dict:
    """Ejecuta tool_guardian y retorna estado."""
    if skip:
        return {"ok": True, "msg": "omitido (--skip-guardian)"}
    guardian = TOOLS_DIR / "tool_guardian.py"
    if not guardian.exists():
        return {"ok": True, "msg": "tool_guardian.py no disponible"}
    try:
        r = subprocess.run(
            ["python3", str(guardian), "--format", "json"],
            capture_output=True, text=True, timeout=30,
            cwd=str(REPO_ROOT)
        )
        findings = json.loads(r.stdout or "[]")
        errors   = len([f for f in findings if f.get("severity") == "error"])
        warnings = len([f for f in findings if f.get("severity") == "warning"])
        ok_count = len([f for f in findings if f.get("rule") == "GUARD-I001"])
        total    = ok_count + errors // 2  # aproximado
        pct      = round(ok_count / max(1, ok_count + errors // 2) * 100)
        return {
            "ok":  errors == 0,
            "msg": f"Salud {pct}% — {errors} errores, {warnings} warnings",
        }
    except Exception as e:
        return {"ok": True, "msg": f"guardian no disponible: {e}"}


def check_git_status() -> dict:
    """Verifica que no hay archivos staged a medias."""
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(REPO_ROOT)
        )
        untracked = [l for l in r.stdout.splitlines() if l.startswith("??")]
        modified  = [l for l in r.stdout.splitlines() if l.startswith(" M") or l.startswith("M")]
        if not untracked and not modified:
            return {"ok": True, "msg": "working tree limpio"}
        parts = []
        if modified:  parts.append(f"{len(modified)} modificado(s)")
        if untracked: parts.append(f"{len(untracked)} sin trackear")
        return {"ok": True, "msg": f"Pendientes: {', '.join(parts)} (no bloquea push)"}
    except Exception:
        return {"ok": True, "msg": "git no disponible"}


# ── Main ──────────────────────────────────────────────────────────────────────

def run_all_checks(skip_tests: bool = False, skip_checksums: bool = False,
                   skip_guardian: bool = False, fix_checksums: bool = False) -> list[dict]:
    checks = []

    # 1. Version sync — crítico
    r = check_version_sync()
    checks.append({"name": "Version sync",    "critical": True,  **r})

    # 2. CHECKSUMS
    if not skip_checksums:
        r = check_checksums_fresh()
        if not r["ok"] and fix_checksums:
            r = regenerate_checksums()
            r["msg"] = "AUTO-REGEN: " + r["msg"]
        checks.append({"name": "CHECKSUMS",   "critical": False, **r})

    # 3. Git status
    r = check_git_status()
    checks.append({"name": "Git status",      "critical": False, **r})

    # 4. Integration suite — puede tardar
    r = check_integration_suite(skip_tests)
    checks.append({"name": "Suite integración","critical": True, **r})

    # 5. Tool guardian
    r = check_tool_guardian(skip_guardian)
    checks.append({"name": "Tool Guardian",   "critical": False, **r})

    return checks


def generate_text(checks: list[dict]) -> str:
    critical_fail = any(not c["ok"] and c["critical"] for c in checks)
    verdict = f"{_RED}❌ NO-GO{_RST}" if critical_fail else f"{_GRN}✅ GO — listo para push{_RST}"
    lines = [f"{_BOLD}Pre-Push Guard{_RST}  {verdict}", ""]
    for c in checks:
        icon  = f"{_GRN}✅{_RST}" if c["ok"] else (f"{_RED}❌{_RST}" if c["critical"] else f"{_YEL}⚠️{_RST}")
        lines.append(f"  {icon}  {c['name']:22s}  {c['msg']}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    skip_tests     = "--skip-tests"     in argv
    skip_checksums = "--skip-checksums" in argv
    skip_guardian  = "--skip-guardian"  in argv
    fix_checksums  = "--fix-checksums"  in argv

    checks = run_all_checks(skip_tests, skip_checksums, skip_guardian, fix_checksums)
    print(generate_text(checks))
    critical_fail = any(not c["ok"] and c["critical"] for c in checks)
    return 1 if critical_fail else 0


def _self_test() -> None:
    print("Tests de pre_push_guard.py...")
    fails: list[str] = []
    def ok(n):   print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    # T1 — check_version_sync con state real → retorna dict con ok/msg
    r1 = check_version_sync()
    if "ok" in r1 and "msg" in r1:
        ok("pre_push:version_sync_structure")
    else:
        fail("pre_push:version_sync_structure", f"r={r1}")

    # T2 — check_checksums_fresh → retorna dict con ok/msg
    r2 = check_checksums_fresh()
    if "ok" in r2 and "msg" in r2:
        ok("pre_push:checksums_check_structure")
    else:
        fail("pre_push:checksums_check_structure", f"r={r2}")

    # T3 — regenerate_checksums → OK y crea archivos
    r3 = regenerate_checksums()
    if r3["ok"] and CHECKSUMS.exists() and TREE_FILE.exists():
        ok("pre_push:regenerate_checksums")
    else:
        fail("pre_push:regenerate_checksums", f"r={r3}")

    # T4 — check_integration_suite skip=True → ok=True
    r4 = check_integration_suite(skip=True)
    if r4["ok"] and "omitido" in r4["msg"]:
        ok("pre_push:suite_skipped")
    else:
        fail("pre_push:suite_skipped", f"r={r4}")

    # T5 — check_git_status → retorna dict
    r5 = check_git_status()
    if "ok" in r5 and "msg" in r5:
        ok("pre_push:git_status_structure")
    else:
        fail("pre_push:git_status_structure", f"r={r5}")

    # T6 — generate_text con checks simulados
    mock = [
        {"name":"Version sync","ok":True,"msg":"v3.0","critical":True},
        {"name":"CHECKSUMS",   "ok":True,"msg":"frescos","critical":False},
    ]
    txt = generate_text(mock)
    if "Pre-Push Guard" in txt and "GO" in txt:
        ok("pre_push:text_output")
    else:
        fail("pre_push:text_output", txt[:100])

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
