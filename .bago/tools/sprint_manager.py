#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sprint_manager.py - Gestor de sprints BAGO.

Crea, lista, cierra y consulta sprints de trabajo.
Estados almacenados en .bago/state/sprints/SPRINT-*.json.

Uso:
  python3 sprint_manager.py new "Nombre del sprint" [--goal G] [--tags a,b]
  python3 sprint_manager.py list
  python3 sprint_manager.py status
  python3 sprint_manager.py active
  python3 sprint_manager.py close [SPRINT-ID] [--summary texto]
  python3 sprint_manager.py show SPRINT-ID
  python3 sprint_manager.py link SPRINT-ID SESSION-ID
  python3 sprint_manager.py --test
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
SPRINTS_DIR = STATE / "sprints"
GLOBAL_STATE = STATE / "global_state.json"


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _all_sprints() -> list:
    SPRINTS_DIR.mkdir(parents=True, exist_ok=True)
    result = []
    for f in SPRINTS_DIR.glob("SPRINT-*.json"):
        s = _load_json(f)
        if s:
            result.append(s)
    result.sort(key=lambda s: s.get("created_at", ""))
    return result


def _next_sprint_id() -> str:
    existing = list(SPRINTS_DIR.glob("SPRINT-*.json"))
    nums = []
    for f in existing:
        parts = f.stem.split("-")
        if len(parts) >= 2:
            try:
                nums.append(int(parts[-1]))
            except ValueError:
                pass
    n = (max(nums) + 1) if nums else 1
    return "SPRINT-{:03d}".format(n)


def _active_sprint() -> Optional[dict]:
    for s in _all_sprints():
        if s.get("status") == "open":
            return s
    return None


def _sprint_file(sprint_id: str) -> Path:
    return SPRINTS_DIR / "{}.json".format(sprint_id)


def _sync_global_state(sprints: list) -> None:
    gs = _load_json(GLOBAL_STATE)
    sprint_map = {}
    for s in sprints:
        sprint_map[s["sprint_id"]] = s.get("status", "unknown")
    gs["sprint_status"] = sprint_map
    gs["updated_at"] = _now_iso()
    _save_json(GLOBAL_STATE, gs)


# ---- Comandos ---------------------------------------------------------------

def cmd_new(name: str, goal: str = "", tags: list = None, force: bool = False) -> None:
    active = _active_sprint()
    if active and not force:
        print("  Ya hay un sprint abierto: {} -- {}".format(active["sprint_id"], active["name"]))
        print("  Cierralo primero con: bago sprint close")
        print("  O usa --force para crear igualmente.")
        raise SystemExit(1)
    sprint_id = _next_sprint_id()
    sprint = {
        "sprint_id": sprint_id,
        "name": name,
        "goal": goal or name,
        "status": "open",
        "tags": tags or [],
        "sessions": [],
        "artifacts": [],
        "decisions": [],
        "created_at": _now_iso(),
        "closed_at": None,
        "summary": None,
    }
    _save_json(_sprint_file(sprint_id), sprint)
    _sync_global_state(_all_sprints())
    print()
    print("  +----------------------------------------------------------+")
    print("  |  Sprint creado                                           |")
    print("  +----------------------------------------------------------+")
    print("  ID:     {}".format(sprint_id))
    print("  Nombre: {}".format(name))
    if goal and goal != name:
        print("  Obj:    {}".format(goal))
    print("  Estado: open")
    print()
    print("  Comandos utiles:")
    print("    bago sprint status   -> ver estado")
    print("    bago sprint close    -> cerrar sprint")
    print()


def cmd_list() -> None:
    sprints = _all_sprints()
    if not sprints:
        print("  No hay sprints. Usa: bago sprint new 'Nombre'")
        return
    print()
    print("  BAGO - Sprints")
    print()
    ICONS = {"open": "[OPEN]", "closed": "[DONE]", "cancelled": "[CANC]"}
    for s in reversed(sprints):
        icon = ICONS.get(s.get("status", ""), "[----]")
        sid = s.get("sprint_id", "?")
        name = s.get("name", "--")
        created = s.get("created_at", "")[:10]
        closed = s.get("closed_at", "")
        closed_str = closed[:10] if closed else "abierto"
        sn = len(s.get("sessions", []))
        an = len(s.get("artifacts", []))
        print("  {}  {:<14}  {:<35}  {} -> {}".format(icon, sid, name[:35], created, closed_str))
        if sn or an:
            print("               sesiones={}  artefactos={}".format(sn, an))
    print()


def cmd_status() -> None:
    active = _active_sprint()
    if not active:
        closed = [s for s in _all_sprints() if s.get("status") == "closed"]
        if closed:
            last = closed[-1]
            print("  No hay sprint activo. Ultimo cerrado: {} -- {}".format(
                last["sprint_id"], last["name"]))
        else:
            print("  No hay sprints. Crea uno: bago sprint new Nombre")
        return
    print()
    print("  [OPEN] Sprint activo")
    print("  ID:        {}".format(active["sprint_id"]))
    print("  Nombre:    {}".format(active["name"]))
    print("  Objetivo:  {}".format(active.get("goal", "--")))
    print("  Creado:    {} UTC".format(active.get("created_at", "")[:16].replace("T", " ")))
    sessions = active.get("sessions", [])
    artifacts = active.get("artifacts", [])
    decisions = active.get("decisions", [])
    print("  Sesiones:  {}".format(len(sessions)))
    for sid in sessions[-3:]:
        print("               * {}".format(sid))
    if len(sessions) > 3:
        print("               ... +{} mas".format(len(sessions) - 3))
    print("  Artefactos: {}".format(len(artifacts)))
    for art in artifacts[-5:]:
        print("               * {}".format(art))
    if len(artifacts) > 5:
        print("               ... +{} mas".format(len(artifacts) - 5))
    print("  Decisiones: {}".format(len(decisions)))
    for d in decisions[-3:]:
        print("               * {}".format(d))
    tags = active.get("tags", [])
    if tags:
        print("  Tags:      {}".format(", ".join(tags)))
    print()


def cmd_active() -> None:
    active = _active_sprint()
    print(active["sprint_id"] if active else "none")


def cmd_close(sprint_id: str = None, summary: str = "") -> None:
    if sprint_id:
        path = _sprint_file(sprint_id)
        if not path.exists():
            print("  Sprint no encontrado: {}".format(sprint_id))
            raise SystemExit(1)
        sprint = _load_json(path)
    else:
        sprint = _active_sprint()
        if not sprint:
            print("  No hay sprint activo para cerrar.")
            return
        path = _sprint_file(sprint["sprint_id"])
    if sprint.get("status") == "closed":
        print("  El sprint {} ya esta cerrado.".format(sprint["sprint_id"]))
        return
    sprint["status"] = "closed"
    sprint["closed_at"] = _now_iso()
    sprint["summary"] = summary or sprint.get("summary") or         "Sprint cerrado -- {} artefactos, {} sesiones.".format(
            len(sprint.get("artifacts", [])), len(sprint.get("sessions", [])))
    _save_json(path, sprint)
    _sync_global_state(_all_sprints())
    print()
    print("  [DONE] Sprint cerrado: {}".format(sprint["sprint_id"]))
    print("  Nombre:  {}".format(sprint["name"]))
    print("  Resumen: {}".format(sprint["summary"]))
    print()


def cmd_show(sprint_id: str) -> None:
    path = _sprint_file(sprint_id)
    if not path.exists():
        print("  Sprint no encontrado: {}".format(sprint_id))
        raise SystemExit(1)
    print(json.dumps(_load_json(path), indent=2, ensure_ascii=False))


def cmd_link(sprint_id: str, session_id: str) -> None:
    path = _sprint_file(sprint_id)
    if not path.exists():
        print("  Sprint no encontrado: {}".format(sprint_id))
        raise SystemExit(1)
    sprint = _load_json(path)
    sessions = sprint.setdefault("sessions", [])
    if session_id not in sessions:
        sessions.append(session_id)
        _save_json(path, sprint)
        print("  Sesion {} enlazada a {}".format(session_id, sprint_id))
    else:
        print("  Sesion {} ya enlazada a {}".format(session_id, sprint_id))


def cmd_add_artifact(sprint_id: str, artifact: str) -> None:
    """API programatica: anade artefacto a sprint activo/especificado."""
    if not sprint_id or sprint_id == "none":
        return
    path = _sprint_file(sprint_id)
    if not path.exists():
        return
    sprint = _load_json(path)
    arts = sprint.setdefault("artifacts", [])
    if artifact not in arts:
        arts.append(artifact)
        _save_json(path, sprint)


# ---- Tests ------------------------------------------------------------------

def _run_tests() -> None:
    import tempfile
    print("  Ejecutando tests de sprint_manager...")
    import sprint_manager as sm
    orig_sd, orig_gs = sm.SPRINTS_DIR, sm.GLOBAL_STATE
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        sm.SPRINTS_DIR = tmp_path
        sm.GLOBAL_STATE = tmp_path / "gs.json"
        sm.GLOBAL_STATE.write_text("{}", encoding="utf-8")

        assert sm._next_sprint_id() == "SPRINT-001"
        sm.cmd_new("Test Sprint", goal="Objetivo test")
        assert (tmp_path / "SPRINT-001.json").exists()
        active = sm._active_sprint()
        assert active is not None and active["sprint_id"] == "SPRINT-001"
        try:
            sm.cmd_new("Segundo Sprint")
            assert False
        except SystemExit:
            pass
        sm.cmd_close(summary="Test cerrado")
        assert sm._active_sprint() is None
        sm.cmd_new("Sprint Dos")
        assert sm._next_sprint_id() == "SPRINT-003"
        sm.SPRINTS_DIR, sm.GLOBAL_STATE = orig_sd, orig_gs
    print("  OK: todos los tests pasaron (6/6)")


# ---- Main -------------------------------------------------------------------

def main() -> None:
    p = argparse.ArgumentParser(description="Gestor de sprints BAGO")
    sub = p.add_subparsers(dest="cmd")

    pn = sub.add_parser("new")
    pn.add_argument("name")
    pn.add_argument("--goal", default="")
    pn.add_argument("--tags", default="")
    pn.add_argument("--force", action="store_true", help="Crear aunque haya sprint abierto")

    sub.add_parser("list")
    sub.add_parser("status")
    sub.add_parser("active")

    pc = sub.add_parser("close")
    pc.add_argument("sprint_id", nargs="?", default=None)
    pc.add_argument("--summary", default="")

    ps = sub.add_parser("show")
    ps.add_argument("sprint_id")

    pl = sub.add_parser("link")
    pl.add_argument("sprint_id")
    pl.add_argument("session_id")

    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    if args.test:
        _run_tests()
    elif args.cmd == "new":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []
        cmd_new(args.name, goal=args.goal, tags=tags, force=args.force)
    elif args.cmd == "list":
        cmd_list()
    elif args.cmd == "status":
        cmd_status()
    elif args.cmd == "active":
        cmd_active()
    elif args.cmd == "close":
        cmd_close(args.sprint_id, summary=args.summary)
    elif args.cmd == "show":
        cmd_show(args.sprint_id)
    elif args.cmd == "link":
        cmd_link(args.sprint_id, args.session_id)
    else:
        cmd_status()


if __name__ == "__main__":
    main()
