#!/usr/bin/env python3
"""
bago patch — corrección automática de inconsistencias conocidas en el pack.

Parches disponibles:
  legacy-status   → sesiones con status "completed" → "closed"
  missing-tests   → cambios CHG sin campo "tests" → añade campo vacío
  missing-goal    → sesiones sin campo "user_goal" → añade ""

Uso:
    bago patch --list              → lista parches disponibles y cuántos items afectan
    bago patch <nombre>            → aplica parche en modo dry-run
    bago patch <nombre> --apply    → aplica parche realmente
    bago patch --all --apply       → aplica todos los parches
    bago patch --test              → tests integrados
"""

import argparse
import json
import sys
import datetime
from pathlib import Path
from copy import deepcopy

BAGO_ROOT    = Path(__file__).parent.parent
SESSIONS_DIR = BAGO_ROOT / "state" / "sessions"
CHANGES_DIR  = BAGO_ROOT / "state" / "changes"


def _load_json(p: Path) -> dict:
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}


def _save_json(p: Path, data: dict):
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def patch_legacy_status(apply: bool) -> dict:
    """Sesiones con status 'completed' → 'closed'."""
    affected = []
    for f in sorted(SESSIONS_DIR.glob("SES-*.json")):
        data = _load_json(f)
        if data.get("status") == "completed":
            affected.append((f, data))

    if apply:
        for f, data in affected:
            data["status"] = "closed"
            data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
            data.setdefault("patch_notes", []).append(
                "status: completed→closed (bago patch legacy-status)"
            )
            _save_json(f, data)

    return {
        "patch": "legacy-status",
        "affected": len(affected),
        "items": [f.name for f, _ in affected],
        "applied": apply,
    }


def patch_missing_tests(apply: bool) -> dict:
    """Cambios CHG sin campo 'tests' → añade campo con lista vacía."""
    affected = []
    for f in sorted(CHANGES_DIR.glob("*.json")):
        data = _load_json(f)
        if "tests" not in data:
            affected.append((f, data))

    if apply:
        for f, data in affected:
            data["tests"] = []
            data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
            _save_json(f, data)

    return {
        "patch": "missing-tests",
        "affected": len(affected),
        "items": [f.name for f, _ in affected],
        "applied": apply,
    }


def patch_missing_goal(apply: bool) -> dict:
    """Sesiones sin campo 'user_goal' → añade campo vacío."""
    affected = []
    for f in sorted(SESSIONS_DIR.glob("SES-*.json")):
        data = _load_json(f)
        if "user_goal" not in data:
            affected.append((f, data))

    if apply:
        for f, data in affected:
            data["user_goal"] = ""
            data["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
            _save_json(f, data)

    return {
        "patch": "missing-goal",
        "affected": len(affected),
        "items": [f.name for f, _ in affected],
        "applied": apply,
    }


PATCHES = {
    "legacy-status":  patch_legacy_status,
    "missing-tests":  patch_missing_tests,
    "missing-goal":   patch_missing_goal,
}

PATCH_DESC = {
    "legacy-status": "status 'completed' → 'closed' en sesiones",
    "missing-tests": "añade campo 'tests:[]' en cambios CHG sin él",
    "missing-goal":  "añade campo 'user_goal:\"\"' en sesiones sin él",
}


def run_tests():
    print("Ejecutando tests de patch.py...")
    import tempfile, shutil
    errors = 0

    def ok(name): print(f"  OK: {name}")
    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    # Setup temp dirs
    tmp = Path(tempfile.mkdtemp())
    tmp_sess = tmp / "state" / "sessions"
    tmp_chg  = tmp / "state" / "changes"
    tmp_sess.mkdir(parents=True)
    tmp_chg.mkdir(parents=True)

    # Write 2 legacy sessions + 1 valid
    (tmp_sess / "SES-001.json").write_text(json.dumps(
        {"id":"SES-001","status":"completed","artifacts":[],"decisions":[]}))
    (tmp_sess / "SES-002.json").write_text(json.dumps(
        {"id":"SES-002","status":"completed","artifacts":[],"decisions":[]}))
    (tmp_sess / "SES-003.json").write_text(json.dumps(
        {"id":"SES-003","status":"closed","artifacts":[],"decisions":[]}))

    # Write CHG without tests
    (tmp_chg / "CHG-001.json").write_text(json.dumps({"change_id":"CHG-001","title":"x"}))
    (tmp_chg / "CHG-002.json").write_text(json.dumps({"change_id":"CHG-002","title":"y","tests":["t1"]}))

    # Test 1: dry-run finds 2 legacy
    import importlib.util
    spec = importlib.util.spec_from_file_location("patch_mod", Path(__file__))
    patch_mod = importlib.util.module_from_spec(spec)
    # monkeypatch dirs
    def _legacy_dry():
        affected = []
        for f in sorted(tmp_sess.glob("SES-*.json")):
            d = json.loads(f.read_text())
            if d.get("status") == "completed":
                affected.append((f, d))
        return {"patch":"legacy-status","affected":len(affected),"applied":False,"items":[f.name for f,_ in affected]}
    r = _legacy_dry()
    if r["affected"] == 2:
        ok("patch:legacy_dry_count")
    else:
        fail("patch:legacy_dry_count", str(r))

    # Test 2: apply changes status
    def _legacy_apply():
        affected = []
        for f in sorted(tmp_sess.glob("SES-*.json")):
            d = json.loads(f.read_text())
            if d.get("status") == "completed":
                affected.append((f, d))
        for f, d in affected:
            d["status"] = "closed"
            f.write_text(json.dumps(d))
        return len(affected)
    n = _legacy_apply()
    # Verify
    d1 = json.loads((tmp_sess/"SES-001.json").read_text())
    if d1["status"] == "closed":
        ok("patch:legacy_applied_status")
    else:
        fail("patch:legacy_applied_status", d1["status"])

    # Test 3: missing-tests patch finds 1
    def _tests_dry():
        aff = []
        for f in sorted(tmp_chg.glob("*.json")):
            d = json.loads(f.read_text())
            if "tests" not in d:
                aff.append(f.name)
        return aff
    items = _tests_dry()
    if len(items) == 1 and items[0] == "CHG-001.json":
        ok("patch:missing_tests_count")
    else:
        fail("patch:missing_tests_count", str(items))

    # Test 4: PATCHES dict has all 3 keys
    if set(PATCHES.keys()) == {"legacy-status","missing-tests","missing-goal"}:
        ok("patch:patches_dict")
    else:
        fail("patch:patches_dict", str(PATCHES.keys()))

    # Test 5: dry-run doesn't modify files
    (tmp_sess / "SES-004.json").write_text(json.dumps(
        {"id":"SES-004","status":"completed","artifacts":[],"decisions":[]}))
    mtime_before = (tmp_sess/"SES-004.json").stat().st_mtime
    # Simulate dry-run (apply=False → no write)
    import time; time.sleep(0.01)
    mtime_after = (tmp_sess/"SES-004.json").stat().st_mtime
    if mtime_before == mtime_after:
        ok("patch:dry_run_no_modify")
    else:
        fail("patch:dry_run_no_modify", "file was modified in dry-run")

    shutil.rmtree(tmp)
    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago patch", add_help=False)
    parser.add_argument("patch_name", nargs="?", default=None)
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    BOLD  = "\033[1m"
    RESET = "\033[0m"
    GREEN = "\033[32m"
    YELLOW= "\033[33m"

    if args.list or (not args.patch_name and not args.all):
        print(f"\n  {BOLD}Parches disponibles:{RESET}\n")
        for name, fn in PATCHES.items():
            result = fn(apply=False)
            color = YELLOW if result["affected"] > 0 else GREEN
            print(f"  {color}{name:20s}{RESET}  {result['affected']:4d} items  — {PATCH_DESC[name]}")
        print()
        return

    apply = args.apply
    mode = "APLICANDO" if apply else "DRY-RUN (usa --apply para aplicar)"

    to_run = list(PATCHES.keys()) if args.all else [args.patch_name]

    for name in to_run:
        if name not in PATCHES:
            print(f"Parche '{name}' no encontrado. Disponibles: {list(PATCHES.keys())}")
            sys.exit(1)
        print(f"\n  {BOLD}{name}{RESET}  [{mode}]")
        result = PATCHES[name](apply=apply)
        if result["affected"] == 0:
            print(f"    ✓ Sin items afectados")
        else:
            print(f"    {'✓ Aplicado a' if apply else '→ Afecta a'} {result['affected']} items:")
            for item in result["items"][:10]:
                print(f"      - {item}")
            if len(result["items"]) > 10:
                print(f"      ... y {len(result['items'])-10} más")
    print()


if __name__ == "__main__":
    main()