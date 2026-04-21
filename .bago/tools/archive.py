#!/usr/bin/env python3
"""
bago archive — archiva sesiones cerradas antiguas en un subdirectorio.

Mueve sesiones con status 'closed' anteriores a N días (default 30)
a .bago/state/sessions/archive/, reduciendo el ruido en la carpeta principal
sin perder historial.

Uso:
    bago archive list              → lista candidatas al archivo
    bago archive run               → archiva las candidatas (confirmar)
    bago archive run --days N      → sesiones con >N días (default 30)
    bago archive run --yes         → sin confirmación interactiva
    bago archive restore <SES-ID>  → restaura una sesion archivada
    bago archive --test            → tests integrados
"""

import argparse
import json
import sys
import shutil
import datetime
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent
SESSIONS_DIR = BAGO_ROOT / "state" / "sessions"
ARCHIVE_DIR = SESSIONS_DIR / "archive"


def _session_age_days(s: dict) -> int:
    try:
        created = datetime.date.fromisoformat(str(s.get("created_at", ""))[:10])
        return (datetime.date.today() - created).days
    except Exception:
        return 0


def list_candidates(days: int = 30) -> list:
    candidates = []
    for f in sorted(SESSIONS_DIR.glob("SES-*.json")):
        try:
            s = json.loads(f.read_text())
            if s.get("status") in ("closed",) and _session_age_days(s) > days:
                candidates.append({
                    "path": f,
                    "session_id": s.get("session_id", f.stem),
                    "age_days": _session_age_days(s),
                    "workflow": s.get("selected_workflow", "?"),
                    "artifacts": len(s.get("artifacts", [])),
                })
        except Exception:
            pass
    return sorted(candidates, key=lambda x: x["age_days"], reverse=True)


def cmd_list(days: int):
    candidates = list_candidates(days)
    print(f"\n  Candidatas a archivar (closed, >{days} días)\n")
    if not candidates:
        print("  (ninguna sesión cumple los criterios)\n")
        return
    for c in candidates:
        print(f"  {c['session_id']:40s}  {c['age_days']:4d}d  wf={c['workflow']}  arts={c['artifacts']}")
    print(f"\n  Total: {len(candidates)} sesiones\n")


def cmd_run(days: int, yes: bool):
    candidates = list_candidates(days)
    if not candidates:
        print(f"  No hay sesiones closed con >{days} días para archivar.")
        return

    print(f"\n  Se archivarán {len(candidates)} sesiones (>{days} días, status=closed)\n")
    for c in candidates[:5]:
        print(f"    {c['session_id']}  ({c['age_days']}d)")
    if len(candidates) > 5:
        print(f"    ... y {len(candidates)-5} más")

    if not yes:
        try:
            resp = input("\n  ¿Proceder? [s/N]: ").strip().lower()
            if resp not in ("s", "si", "sí", "y", "yes"):
                print("  Cancelado.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelado.")
            return

    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    archived = 0
    for c in candidates:
        dest = ARCHIVE_DIR / c["path"].name
        if dest.exists():
            print(f"  SKIP (ya archivado): {c['path'].name}")
            continue
        shutil.move(str(c["path"]), str(dest))
        archived += 1

    print(f"\n  ✅ {archived} sesiones archivadas → {ARCHIVE_DIR}\n")


def cmd_restore(session_id: str):
    if not ARCHIVE_DIR.exists():
        print("  No existe el directorio de archivo.")
        sys.exit(1)
    # Try exact match first
    candidates = list(ARCHIVE_DIR.glob(f"*{session_id}*.json"))
    if not candidates:
        print(f"  No se encontró '{session_id}' en el archivo.")
        sys.exit(1)
    for f in candidates:
        dest = SESSIONS_DIR / f.name
        if dest.exists():
            print(f"  Ya existe en sessions/: {f.name}")
            continue
        shutil.move(str(f), str(dest))
        print(f"  ✅ Restaurada: {f.name}")


def run_tests():
    import tempfile, os
    print("Ejecutando tests de archive.py...")
    errors = 0

    def ok(name): print(f"  OK: {name}")
    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    # Test 1: _session_age_days with past date
    s = {"created_at": "2020-01-01", "status": "closed"}
    age = _session_age_days(s)
    if age > 365:
        ok("archive:age_days_past")
    else:
        fail("archive:age_days_past", f"age={age}")

    # Test 2: _session_age_days with today
    today_str = datetime.date.today().isoformat()
    s2 = {"created_at": today_str}
    age2 = _session_age_days(s2)
    if age2 == 0:
        ok("archive:age_days_today")
    else:
        fail("archive:age_days_today", f"age={age2}")

    # Test 3: list_candidates returns list
    candidates = list_candidates(days=0)
    if isinstance(candidates, list):
        ok("archive:list_candidates_returns_list")
    else:
        fail("archive:list_candidates_returns_list", str(type(candidates)))

    # Test 4: list_candidates with very high days threshold = empty
    candidates_none = list_candidates(days=99999)
    if len(candidates_none) == 0:
        ok("archive:list_candidates_empty_with_high_days")
    else:
        fail("archive:list_candidates_empty_with_high_days", f"{len(candidates_none)} found")

    # Test 5: ARCHIVE_DIR path is correct
    expected = SESSIONS_DIR / "archive"
    if ARCHIVE_DIR == expected:
        ok("archive:archive_dir_path")
    else:
        fail("archive:archive_dir_path", str(ARCHIVE_DIR))

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago archive", add_help=False)
    sub = parser.add_subparsers(dest="action")

    sub.add_parser("list")
    sr = sub.add_parser("run")
    sr.add_argument("--days", type=int, default=30)
    sr.add_argument("--yes", action="store_true")

    srs = sub.add_parser("restore")
    srs.add_argument("session_id")

    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--yes", action="store_true")
    parser.add_argument("--test", action="store_true")

    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.action == "list":
        cmd_list(days=args.days)
    elif args.action == "run":
        cmd_run(days=args.days, yes=args.yes)
    elif args.action == "restore":
        cmd_restore(args.session_id)
    else:
        cmd_list(days=args.days)


if __name__ == "__main__":
    main()