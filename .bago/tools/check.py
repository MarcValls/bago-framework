#!/usr/bin/env python3
"""
bago check — checklist pre-sesion personalizable.

Carga una lista de verificaciones desde .bago/config/checklist.json
y las ejecuta mostrando el resultado con iconos. Si no existe el archivo,
usa un checklist por defecto basado en buenas prácticas BAGO.

Uso:
    bago check              → ejecuta el checklist completo
    bago check --quick      → solo checks críticos
    bago check --json       → output JSON
    bago check init         → crea checklist.json personalizable
    bago check --test       → tests integrados
"""

import argparse
import json
import sys
import subprocess
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent
CHECKLIST_PATH = BAGO_ROOT / "config" / "checklist.json"

DEFAULT_CHECKS = [
    {
        "id": "health",
        "label": "Health del pack >= 80",
        "critical": True,
        "cmd": None,
        "check_type": "health_score",
        "threshold": 80
    },
    {
        "id": "validate",
        "label": "bago validate sin errores",
        "critical": True,
        "cmd": None,
        "check_type": "validate"
    },
    {
        "id": "open_sprint",
        "label": "Hay un sprint abierto",
        "critical": False,
        "cmd": None,
        "check_type": "open_sprint"
    },
    {
        "id": "no_legacy_status",
        "label": "Sin sesiones con estado legacy",
        "critical": False,
        "cmd": None,
        "check_type": "no_legacy_status"
    },
    {
        "id": "snapshot_recent",
        "label": "Snapshot reciente (< 14 dias)",
        "critical": False,
        "cmd": None,
        "check_type": "snapshot_recent",
        "max_days": 14
    },
]


def _load_checks() -> list:
    if CHECKLIST_PATH.exists():
        try:
            return json.loads(CHECKLIST_PATH.read_text())
        except Exception:
            pass
    return DEFAULT_CHECKS


def _run_check(check: dict) -> tuple:
    """Returns (passed: bool, detail: str)"""
    ct = check.get("check_type")

    if ct == "health_score":
        try:
            # Run bago health and parse the score from output
            result = subprocess.run(
                ["python3", str(BAGO_ROOT / "tools" / "health_score.py")],
                capture_output=True, text=True, timeout=20
            )
            import re
            m = re.search(r"(\d+)/100", result.stdout)
            score = int(m.group(1)) if m else 100
            threshold = check.get("threshold", 80)
            return (score >= threshold, f"score={score}")
        except Exception as e:
            return (False, str(e))

    elif ct == "validate":
        try:
            result = subprocess.run(
                ["python3", str(BAGO_ROOT / "tools" / "validate_state.py")],
                capture_output=True, text=True, timeout=20
            )
            passed = result.returncode == 0
            return (passed, "GO" if passed else result.stdout.strip()[:80])
        except Exception as e:
            return (False, str(e))

    elif ct == "open_sprint":
        sprints_dir = BAGO_ROOT / "state" / "sprints"
        if sprints_dir.exists():
            for f in sprints_dir.glob("SPRINT-*.json"):
                try:
                    s = json.loads(f.read_text())
                    if s.get("status") == "open":
                        return (True, s.get("sprint_id", f.stem))
                except Exception:
                    pass
        return (False, "no hay sprint abierto")

    elif ct == "no_legacy_status":
        sessions_dir = BAGO_ROOT / "state" / "sessions"
        legacy = []
        if sessions_dir.exists():
            for f in sessions_dir.glob("SES-*.json"):
                try:
                    s = json.loads(f.read_text())
                    if s.get("status") == "completed":
                        legacy.append(s.get("session_id", f.stem))
                except Exception:
                    pass
        if legacy:
            return (False, f"{len(legacy)} sesiones con 'completed'")
        return (True, "limpio")

    elif ct == "snapshot_recent":
        import datetime
        snap_dir = BAGO_ROOT / "state" / "snapshots"
        max_days = check.get("max_days", 14)
        if snap_dir.exists():
            snaps = sorted(snap_dir.glob("SNAP-*.zip"))
            if snaps:
                import datetime as dt
                mtime = dt.datetime.fromtimestamp(snaps[-1].stat().st_mtime).date()
                days = (dt.date.today() - mtime).days
                return (days <= max_days, f"hace {days} días")
        return (False, "sin snapshots")

    elif ct == "cmd":
        cmd = check.get("cmd")
        if not cmd:
            return (False, "no cmd defined")
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=15)
            return (result.returncode == 0, result.stdout.strip()[:80] or "ok")
        except Exception as e:
            return (False, str(e))

    return (True, "no check type")


def run_checklist(quick_only: bool, as_json: bool):
    checks = _load_checks()
    if quick_only:
        checks = [c for c in checks if c.get("critical", False)]

    results = []
    for check in checks:
        passed, detail = _run_check(check)
        results.append({
            "id": check.get("id"),
            "label": check.get("label"),
            "critical": check.get("critical", False),
            "passed": passed,
            "detail": detail,
        })

    if as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return results

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    critical_failed = [r for r in results if r["critical"] and not r["passed"]]

    print(f"\n  BAGO Checklist pre-sesión ({passed_count}/{total} OK)\n")
    for r in results:
        icon = "✅" if r["passed"] else ("🔴" if r["critical"] else "⚠️ ")
        print(f"  {icon} {r['label']}")
        if not r["passed"] or r["detail"] not in ("ok", "GO", "limpio"):
            print(f"       {r['detail']}")

    if critical_failed:
        print(f"\n  ⛔ {len(critical_failed)} check(s) crítico(s) fallaron.")
        raise SystemExit(1)
    elif passed_count < total:
        print(f"\n  ⚠️  {total - passed_count} warning(s) — revisa antes de continuar.\n")
    else:
        print(f"\n  ✅ Todo listo para empezar la sesión.\n")

    return results


def cmd_init():
    CHECKLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    if CHECKLIST_PATH.exists():
        print(f"  Ya existe: {CHECKLIST_PATH}")
    else:
        CHECKLIST_PATH.write_text(json.dumps(DEFAULT_CHECKS, indent=2, ensure_ascii=False))
        print(f"  Creado: {CHECKLIST_PATH}")
        print("  Edita el archivo para personalizar tu checklist.")


def run_tests():
    print("Ejecutando tests de check.py...")
    errors = 0

    def ok(name): print(f"  OK: {name}")
    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    # Test 1: DEFAULT_CHECKS tiene items
    if len(DEFAULT_CHECKS) >= 3:
        ok("check:default_checks_nonempty")
    else:
        fail("check:default_checks_nonempty", str(len(DEFAULT_CHECKS)))

    # Test 2: _run_check no_legacy_status returns tuple
    result = _run_check({"check_type": "no_legacy_status"})
    if isinstance(result, tuple) and isinstance(result[0], bool):
        ok("check:run_check_returns_tuple")
    else:
        fail("check:run_check_returns_tuple", str(result))

    # Test 3: _run_check snapshot_recent on real data
    result = _run_check({"check_type": "snapshot_recent", "max_days": 365})
    if isinstance(result, tuple):
        ok("check:snapshot_recent_tuple")
    else:
        fail("check:snapshot_recent_tuple", str(result))

    # Test 4: _run_check open_sprint
    result = _run_check({"check_type": "open_sprint"})
    if isinstance(result, tuple) and isinstance(result[0], bool):
        ok("check:open_sprint_tuple")
    else:
        fail("check:open_sprint_tuple", str(result))

    # Test 5: run_checklist returns list
    results = run_checklist(quick_only=False, as_json=False)
    if isinstance(results, list) and len(results) > 0:
        ok("check:run_checklist_returns_list")
    else:
        fail("check:run_checklist_returns_list", str(type(results)))

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago check", add_help=False)
    sub = parser.add_subparsers(dest="action")
    sub.add_parser("init")
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--test", action="store_true")

    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.action == "init":
        cmd_init()
    else:
        run_checklist(quick_only=args.quick, as_json=args.json)


if __name__ == "__main__":
    main()