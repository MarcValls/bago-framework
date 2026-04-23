#!/usr/bin/env python3
"""
bago notes — notas ligeras ligadas a sesiones o sprints.

Uso:
    bago notes add "texto"                 → nueva nota (sesión/sprint actual)
    bago notes add "texto" --session SES-X → nota ligada a sesión específica
    bago notes add "texto" --sprint SPRINT-004
    bago notes list                        → listar todas las notas
    bago notes list --session SES-X        → notas de una sesión
    bago notes show NOTE-001               → ver nota completa
    bago notes delete NOTE-001             → borrar nota
    bago notes search <término>            → buscar en notas
    bago notes --test                      → tests integrados
"""
import argparse, json, sys, datetime, re
from pathlib import Path

BAGO_ROOT  = Path(__file__).parent.parent
NOTES_DIR  = BAGO_ROOT / "state" / "notes"
NOTES_DIR.mkdir(parents=True, exist_ok=True)

BOLD  = "\033[1m"
DIM   = "\033[2m"
CYAN  = "\033[36m"
RESET = "\033[0m"
YELLOW= "\033[33m"


def _next_id() -> str:
    existing = sorted(NOTES_DIR.glob("NOTE-*.json"))
    if not existing:
        return "NOTE-001"
    last = int(existing[-1].stem.split("-")[1])
    return f"NOTE-{last+1:03d}"


def _load(note_id: str) -> dict:
    f = NOTES_DIR / f"{note_id}.json"
    if not f.exists():
        print(f"Nota '{note_id}' no encontrada.")
        raise SystemExit(1)
    return json.loads(f.read_text())


def _save(data: dict):
    nid = data["id"]
    (NOTES_DIR / f"{nid}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    )


def _all_notes() -> list:
    out = []
    for f in sorted(NOTES_DIR.glob("NOTE-*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except Exception:
            pass
    return out


def cmd_add(text: str, session: str | None, sprint: str | None):
    note = {
        "id":         _next_id(),
        "text":       text,
        "session":    session or "",
        "sprint":     sprint  or "",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    _save(note)
    print(f"\n  {BOLD}Nota creada:{RESET} {note['id']}")
    print(f"  {DIM}{note['text']}{RESET}")
    if note["session"]: print(f"  → sesión: {note['session']}")
    if note["sprint"]:  print(f"  → sprint: {note['sprint']}")
    print()


def cmd_list(session: str | None, sprint: str | None):
    notes = _all_notes()
    if session:
        notes = [n for n in notes if n.get("session") == session]
    if sprint:
        notes = [n for n in notes if n.get("sprint") == sprint]
    if not notes:
        print("\n  Sin notas" + (f" para {session or sprint}" if session or sprint else "") + "\n")
        return
    print(f"\n  {BOLD}Notas ({len(notes)}){RESET}\n")
    for n in notes:
        tag = ""
        if n.get("session"): tag = f"  {DIM}[{n['session']}]{RESET}"
        if n.get("sprint"):  tag += f"  {DIM}[{n['sprint']}]{RESET}"
        ts = n.get("created_at","")[:10]
        text_preview = n["text"][:72] + ("…" if len(n["text"]) > 72 else "")
        print(f"  {CYAN}{n['id']}{RESET}  {DIM}{ts}{RESET}{tag}")
        print(f"    {text_preview}\n")


def cmd_show(note_id: str):
    n = _load(note_id)
    print(f"\n  {BOLD}{n['id']}{RESET}  {DIM}{n.get('created_at','')[:19]}{RESET}")
    if n.get("session"): print(f"  Sesión: {n['session']}")
    if n.get("sprint"):  print(f"  Sprint: {n['sprint']}")
    print(f"\n  {n['text']}\n")


def cmd_delete(note_id: str):
    f = NOTES_DIR / f"{note_id}.json"
    if not f.exists():
        print(f"Nota '{note_id}' no encontrada.")
        raise SystemExit(1)
    f.unlink()
    print(f"  Nota {note_id} eliminada.")


def cmd_search(term: str):
    pattern = re.compile(term, re.IGNORECASE)
    notes   = [n for n in _all_notes() if pattern.search(n.get("text",""))]
    if not notes:
        print(f"\n  Sin resultados para '{term}'\n")
        return
    print(f"\n  {BOLD}Resultados ({len(notes)}){RESET}\n")
    for n in notes:
        hi = re.sub(f"({re.escape(term)})", f"{YELLOW}\\1{RESET}", n["text"][:80], flags=re.IGNORECASE)
        print(f"  {CYAN}{n['id']}{RESET}  {hi}\n")


def run_tests():
    import tempfile, shutil
    print("Ejecutando tests de notes.py...")
    errors = 0
    def ok(name): print(f"  OK: {name}")
    def fail(name, msg):
        nonlocal errors; errors += 1; print(f"  FAIL: {name} — {msg}")

    tmp = Path(tempfile.mkdtemp()) / "notes"
    tmp.mkdir()

    # Monkeypatch NOTES_DIR
    import importlib.util
    spec = importlib.util.spec_from_file_location("notes_mod", Path(__file__))
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.NOTES_DIR = tmp

    # Test 1: _next_id empty dir → NOTE-001
    if mod._next_id() == "NOTE-001":
        ok("notes:next_id_empty")
    else:
        fail("notes:next_id_empty", mod._next_id())

    # Test 2: save + load roundtrip
    note = {"id":"NOTE-001","text":"hola","session":"","sprint":"","created_at":"2026-01-01T00:00:00Z"}
    mod._save(note)
    loaded = mod._load("NOTE-001")
    if loaded["text"] == "hola":
        ok("notes:save_load")
    else:
        fail("notes:save_load", str(loaded))

    # Test 3: _next_id after one note → NOTE-002
    if mod._next_id() == "NOTE-002":
        ok("notes:next_id_increment")
    else:
        fail("notes:next_id_increment", mod._next_id())

    # Test 4: _all_notes returns list
    all_n = mod._all_notes()
    if isinstance(all_n, list) and len(all_n) == 1:
        ok("notes:all_notes")
    else:
        fail("notes:all_notes", str(all_n))

    # Test 5: search finds match, ignores non-match
    note2 = {"id":"NOTE-002","text":"python es genial","session":"","sprint":"","created_at":"2026-01-02T00:00:00Z"}
    mod._save(note2)
    import re as re_
    results = [n for n in mod._all_notes() if re_.search("python", n["text"], re_.IGNORECASE)]
    if len(results) == 1 and results[0]["id"] == "NOTE-002":
        ok("notes:search")
    else:
        fail("notes:search", str(results))

    shutil.rmtree(tmp.parent)
    total = 5; passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors: raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago notes", add_help=False)
    sub = parser.add_subparsers(dest="subcmd")

    p_add = sub.add_parser("add")
    p_add.add_argument("text")
    p_add.add_argument("--session", default=None)
    p_add.add_argument("--sprint", default=None)

    p_list = sub.add_parser("list")
    p_list.add_argument("--session", default=None)
    p_list.add_argument("--sprint", default=None)

    p_show   = sub.add_parser("show");   p_show.add_argument("note_id")
    p_delete = sub.add_parser("delete"); p_delete.add_argument("note_id")
    p_search = sub.add_parser("search"); p_search.add_argument("term")

    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests(); return
    if args.subcmd == "add":
        cmd_add(args.text, args.session, args.sprint)
    elif args.subcmd == "list":
        cmd_list(args.session, args.sprint)
    elif args.subcmd == "show":
        cmd_show(args.note_id)
    elif args.subcmd == "delete":
        cmd_delete(args.note_id)
    elif args.subcmd == "search":
        cmd_search(args.term)
    else:
        cmd_list(None, None)

if __name__ == "__main__":
    main()