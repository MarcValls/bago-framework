#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config_show.py — Muestra la configuración actual de BAGO en detalle.

Agrega información de: proyecto activo, herramientas registradas, ideas implementadas,
estado de la base de datos, snapshots disponibles, y configuración env.

Uso:
    python3 .bago/tools/config_show.py            # resumen completo
    python3 .bago/tools/config_show.py --json     # salida JSON
    python3 .bago/tools/config_show.py --section tools|project|ideas|db  # solo sección
    python3 .bago/tools/config_show.py --short    # resumen de una pantalla

Códigos de salida: 0 = OK
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from datetime import datetime, timezone

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT  = Path(__file__).resolve().parents[2]
STATE = ROOT / ".bago" / "state"
TOOLS = ROOT / ".bago" / "tools"


def BOLD(s: str)   -> str: return f"\033[1m{s}\033[0m"
def DIM(s: str)    -> str: return f"\033[2m{s}\033[0m"
def GREEN(s: str)  -> str: return f"\033[32m{s}\033[0m"
def YELLOW(s: str) -> str: return f"\033[33m{s}\033[0m"
def RED(s: str)    -> str: return f"\033[31m{s}\033[0m"
def CYAN(s: str)   -> str: return f"\033[36m{s}\033[0m"
def MAGENTA(s: str)-> str: return f"\033[35m{s}\033[0m"


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _parse_dt(s: str) -> datetime | None:
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)
    except Exception:
        return None


def section_project() -> dict:
    gs = _load_json(STATE / "global_state.json")
    if not gs or not isinstance(gs, dict):
        return {"error": "global_state.json no encontrado"}
    proj = gs.get("active_project", {})
    return {
        "name":        proj.get("name", "?"),
        "path":        proj.get("path", "?"),
        "session_id":  gs.get("session_id", "?"),
        "started_at":  gs.get("started_at", "?"),
        "bago_version": gs.get("version", "?"),
    }


def section_ideas() -> dict:
    impl = _load_json(STATE / "implemented_ideas.json")
    if not impl or not isinstance(impl, dict):
        return {"total": 0, "last": None}
    items = impl.get("implemented", [])
    last  = items[0] if items else None
    return {
        "total":    len(items),
        "updated":  impl.get("updated_at", "?"),
        "last":     last.get("title", "?") if last else None,
        "last_at":  last.get("done_at", "?") if last else None,
    }


def section_tools() -> dict:
    tools_py = list(TOOLS.glob("*.py"))
    registry = _load_json(TOOLS / "tool_registry.py")  # can't parse directly

    # Count from actual .py files (excluding base files)
    BASE_FILES = {"tool_registry.py", "bago_core.py", "__init__.py", "db_init.py",
                  "idea_gen.py", "validate.py"}
    tool_files = [f for f in tools_py if f.name not in BASE_FILES]
    return {
        "tool_files":    len(tool_files),
        "tool_names":    sorted(f.stem for f in tool_files),
    }


def section_db() -> dict:
    db_path = STATE / "bago.db"
    if not db_path.exists():
        return {"exists": False}
    size_kb = db_path.stat().st_size // 1024
    return {
        "exists":   True,
        "path":     str(db_path),
        "size_kb":  size_kb,
    }


def section_snapshots() -> dict:
    snap_dir = ROOT / ".bago" / "snapshots"
    if not snap_dir.exists():
        return {"count": 0}
    snaps = sorted(snap_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    total_kb = sum(s.stat().st_size // 1024 for s in snaps)
    return {
        "count":    len(snaps),
        "latest":   snaps[0].name if snaps else None,
        "total_kb": total_kb,
    }


def section_task() -> dict:
    task_file = STATE / "pending_w2_task.json"
    if not task_file.exists():
        return {"active": False}
    data = _load_json(task_file)
    if not data or not isinstance(data, dict):
        return {"active": False}
    return {
        "active":    True,
        "title":     data.get("idea_title", data.get("title", "?")),
        "priority":  data.get("priority", "?"),
        "slot":      data.get("idea_index", data.get("slot", "?")),
    }


def main() -> int:
    args     = sys.argv[1:]
    as_json  = "--json" in args
    short    = "--short" in args
    section  = None

    if "--section" in args:
        idx = args.index("--section")
        if idx + 1 < len(args):
            section = args[idx + 1]

    info = {
        "project":   section_project(),
        "ideas":     section_ideas(),
        "tools":     section_tools(),
        "db":        section_db(),
        "snapshots": section_snapshots(),
        "task":      section_task(),
    }

    if section and section in info:
        info = {section: info[section]}

    if as_json:
        print(json.dumps(info, indent=2, ensure_ascii=False))
        return 0

    print()
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  BAGO · Configuración                                       │")
    print("  └─────────────────────────────────────────────────────────────┘")

    # Project
    p = info.get("project", {})
    print(f"  {BOLD('Proyecto activo:')}")
    print(f"    Nombre:     {CYAN(p.get('name', '?'))}")
    print(f"    Ruta:       {DIM(p.get('path', '?'))}")
    print(f"    Session:    {DIM(p.get('session_id', '?')[:20] + '...')}")
    print()

    # Task
    t = info.get("task", {})
    if t.get("active"):
        prio = t["priority"]
        print(f"  {BOLD('Tarea activa:')}  {YELLOW(t['title'])}  {DIM(f'(prioridad {prio})')}")
    else:
        print(f"  {BOLD('Tarea activa:')}  {DIM('ninguna')}")
    print()

    # Ideas
    i = info.get("ideas", {})
    print(f"  {BOLD('Ideas implementadas:')}  {GREEN(str(i.get('total', 0)))}")
    if i.get("last"):
        print(f"    Última:   {DIM(i['last'])}")
    print()

    # Tools
    tools = info.get("tools", {})
    names = tools.get("tool_names", [])
    print(f"  {BOLD('Herramientas registradas:')}  {len(names)}")
    if not short:
        chunks = [names[i:i+5] for i in range(0, len(names), 5)]
        for chunk in chunks:
            print(f"    {DIM('  '.join(chunk))}")
    print()

    # DB
    db = info.get("db", {})
    if db.get("exists"):
        print(f"  {BOLD('Base de datos:')}  {GREEN('✅')} {DIM(str(db['size_kb']) + 'KB')}  {DIM(db.get('path', ''))}")
    else:
        print(f"  {BOLD('Base de datos:')}  {RED('✗ no encontrada')}")
    print()

    # Snapshots
    snaps = info.get("snapshots", {})
    count = snaps.get("count", 0)
    print(f"  {BOLD('Snapshots:')}")
    if count:
        print(f"    {GREEN(str(count))} disponibles  |  Último: {DIM(snaps.get('latest', '?'))}  |  Total: {DIM(str(snaps.get('total_kb', 0)) + 'KB')}")
    else:
        print(f"    {YELLOW('ninguno')}  —  Usa: bago snapshot")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
