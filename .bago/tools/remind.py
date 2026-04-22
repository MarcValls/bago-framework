#!/usr/bin/env python3
"""
bago remind — gestiona recordatorios ligados a sesiones, sprints o fechas.

Los recordatorios se guardan en .bago/state/reminders/ como JSON.
Al ejecutar 'bago remind', muestra los pendientes y vencidos.

Uso:
    bago remind                     → muestra pendientes y vencidos
    bago remind add <texto>         → añade recordatorio
    bago remind add <texto> --due YYYY-MM-DD  → con fecha de vencimiento
    bago remind add <texto> --sprint SPRINT-ID
    bago remind done <ID>           → marca completado
    bago remind list [--all]        → lista todos (default: solo pendientes)
    bago remind --test              → tests integrados
"""

import argparse
import json
import sys
import datetime
import uuid
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent
REMINDERS_DIR = BAGO_ROOT / "state" / "reminders"


def _load_reminders() -> list:
    if not REMINDERS_DIR.exists():
        return []
    out = []
    for f in sorted(REMINDERS_DIR.glob("REM-*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except Exception:
            pass
    return out


def _save_reminder(rem: dict):
    REMINDERS_DIR.mkdir(parents=True, exist_ok=True)
    rid = rem["id"]
    p = REMINDERS_DIR / f"{rid}.json"
    p.write_text(json.dumps(rem, indent=2, ensure_ascii=False))
    return p


def _today() -> datetime.date:
    return datetime.date.today()


def cmd_add(text: str, due: str = None, sprint: str = None):
    rid = "REM-" + uuid.uuid4().hex[:8].upper()
    rem = {
        "id": rid,
        "text": text,
        "status": "pending",
        "due_date": due,
        "sprint_ref": sprint,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "done_at": None,
    }
    p = _save_reminder(rem)
    due_str = f" (due: {due})" if due else ""
    sprint_str = f" [sprint: {sprint}]" if sprint else ""
    print(f"  ✅ Recordatorio añadido: {rid}{due_str}{sprint_str}")
    print(f"     {text}")


def cmd_done(rem_id: str):
    if not REMINDERS_DIR.exists():
        print("  No hay recordatorios.")
        sys.exit(1)
    found = list(REMINDERS_DIR.glob(f"*{rem_id}*.json"))
    if not found:
        print(f"  No encontrado: {rem_id}")
        sys.exit(1)
    for f in found:
        rem = json.loads(f.read_text())
        rem["status"] = "done"
        rem["done_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        f.write_text(json.dumps(rem, indent=2, ensure_ascii=False))
        print(f"  ✅ Marcado como hecho: {rem['id']}")


def cmd_list(show_all: bool = False):
    reminders = _load_reminders()
    if not show_all:
        reminders = [r for r in reminders if r.get("status") == "pending"]

    today = _today()
    overdue = [r for r in reminders if r.get("due_date") and datetime.date.fromisoformat(r["due_date"]) < today and r.get("status") == "pending"]
    pending = [r for r in reminders if r.get("status") == "pending" and r not in overdue]
    done = [r for r in reminders if r.get("status") == "done"]

    print(f"\n  Recordatorios BAGO")

    if overdue:
        print(f"\n  🔴 VENCIDOS ({len(overdue)}):")
        for r in overdue:
            print(f"    [{r['id']}] {r['text']}  (due: {r['due_date']})")

    if pending:
        print(f"\n  🟡 Pendientes ({len(pending)}):")
        for r in pending:
            due = f"  (due: {r['due_date']})" if r.get("due_date") else ""
            spr = f"  [sprint: {r['sprint_ref']}]" if r.get("sprint_ref") else ""
            print(f"    [{r['id']}] {r['text']}{due}{spr}")

    if show_all and done:
        print(f"\n  ✅ Completados ({len(done)}):")
        for r in done[-5:]:
            print(f"    [{r['id']}] {r['text']}")

    if not overdue and not pending:
        print("\n  (sin recordatorios pendientes)\n")
    else:
        print()


def cmd_show():
    """Muestra recordatorios vencidos o urgentes al inicio."""
    reminders = _load_reminders()
    today = _today()
    overdue = [
        r for r in reminders
        if r.get("status") == "pending" and r.get("due_date")
        and datetime.date.fromisoformat(r["due_date"]) < today
    ]
    soon = [
        r for r in reminders
        if r.get("status") == "pending" and r.get("due_date")
        and 0 <= (datetime.date.fromisoformat(r["due_date"]) - today).days <= 2
    ]
    pending_no_date = [r for r in reminders if r.get("status") == "pending" and not r.get("due_date")]

    if not reminders:
        print("\n  (sin recordatorios)\n")
        return

    if overdue:
        print(f"\n  ⚠️  {len(overdue)} recordatorio(s) VENCIDO(s):")
        for r in overdue[:3]:
            print(f"    [{r['id']}] {r['text']}  (due: {r['due_date']})")
    if soon:
        print(f"\n  🕐 {len(soon)} vencen pronto (≤2 días):")
        for r in soon[:3]:
            print(f"    [{r['id']}] {r['text']}  (due: {r['due_date']})")
    if pending_no_date:
        print(f"\n  📌 {len(pending_no_date)} pendientes sin fecha")
    print()


def run_tests():
    import tempfile, os, shutil
    print("Ejecutando tests de remind.py...")
    errors = 0

    def ok(name): print(f"  OK: {name}")
    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    # Temp reminders dir
    tmp_dir = Path(tempfile.mkdtemp())
    global REMINDERS_DIR
    orig_dir = REMINDERS_DIR
    REMINDERS_DIR = tmp_dir

    try:
        # Test 1: add reminder
        cmd_add("Test reminder 1")
        rems = _load_reminders()
        if len(rems) == 1 and rems[0]["text"] == "Test reminder 1":
            ok("remind:add_and_load")
        else:
            fail("remind:add_and_load", str(rems))

        # Test 2: add with due date
        cmd_add("Test reminder 2", due="2099-12-31")
        rems = _load_reminders()
        due_rems = [r for r in rems if r.get("due_date") == "2099-12-31"]
        if due_rems:
            ok("remind:add_with_due")
        else:
            fail("remind:add_with_due", str(rems))

        # Test 3: done
        rid = rems[0]["id"]
        cmd_done(rid)
        updated = _load_reminders()
        done_r = next((r for r in updated if r["id"] == rid), None)
        if done_r and done_r["status"] == "done":
            ok("remind:mark_done")
        else:
            fail("remind:mark_done", str(done_r))

        # Test 4: list pending only
        pending = [r for r in _load_reminders() if r.get("status") == "pending"]
        if len(pending) == 1:
            ok("remind:list_pending_filter")
        else:
            fail("remind:list_pending_filter", f"{len(pending)} pending")

        # Test 5: add with sprint ref
        cmd_add("Sprint reminder", sprint="SPRINT-004")
        rems2 = _load_reminders()
        spr_rems = [r for r in rems2 if r.get("sprint_ref") == "SPRINT-004"]
        if spr_rems:
            ok("remind:add_with_sprint")
        else:
            fail("remind:add_with_sprint", str(rems2))

    finally:
        REMINDERS_DIR = orig_dir
        shutil.rmtree(tmp_dir)

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago remind", add_help=False)
    sub = parser.add_subparsers(dest="action")

    sa = sub.add_parser("add")
    sa.add_argument("text")
    sa.add_argument("--due", default=None)
    sa.add_argument("--sprint", default=None)

    sd = sub.add_parser("done")
    sd.add_argument("rem_id")

    sl = sub.add_parser("list")
    sl.add_argument("--all", action="store_true")

    parser.add_argument("--test", action="store_true")

    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.action == "add":
        cmd_add(args.text, due=args.due, sprint=args.sprint)
    elif args.action == "done":
        cmd_done(args.rem_id)
    elif args.action == "list":
        cmd_list(show_all=args.all)
    else:
        cmd_show()


if __name__ == "__main__":
    main()