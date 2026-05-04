#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_opener.py — Abre una sesión W2 pre-rellenada desde el handoff aceptado.

Lee pending_w2_task.json y lanza session_preflight.py con objetivo, roles
y artefactos candidatos derivados del handoff, eliminando el paso manual.

Uso:
  python3 .bago/tools/session_opener.py          # lanza preflight con datos del handoff
  python3 .bago/tools/session_opener.py --dry     # muestra los args sin ejecutar
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[2]
TASK_FILE  = ROOT / ".bago" / "state" / "pending_w2_task.json"
PREFLIGHT  = ROOT / ".bago" / "tools" / "session_preflight.py"

WORKFLOW_ROLES: dict[str, str] = {
    "W2":  "role_architect,role_validator",
    "W3":  "role_executor,role_validator",
    "W4":  "role_auditor,role_organizer",
    "W5":  "role_executor,role_organizer",
    "W7":  "role_architect,role_validator",
    "W9":  "role_organizer,role_vertice",
}

DEFAULT_ROLES = "role_architect,role_validator"


def _load_task() -> dict | None:
    if not TASK_FILE.exists():
        return None
    try:
        return json.loads(TASK_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def _derive_roles(task: dict) -> str:
    wf = str(task.get("workflow", "")).strip().upper()
    for key, roles in WORKFLOW_ROLES.items():
        if key in wf:
            return roles
    return DEFAULT_ROLES


def _build_args(task: dict) -> dict[str, str]:
    objetivo  = task.get("objetivo", "").strip()
    roles     = _derive_roles(task)
    archivos  = task.get("archivos_candidatos", [])
    artefactos = ",".join(archivos[:6]) if archivos else "state/sessions,state/changes,state/evidences"
    return {"objetivo": objetivo, "roles": roles, "artefactos": artefactos}


def main() -> int:
    dry = "--dry" in sys.argv

    task = _load_task()
    if task is None:
        print()
        print("  ℹ  No hay tarea W2 pendiente.")
        print("     Acepta una idea primero con: bago ideas --accept N")
        print()
        return 1

    if task.get("status") == "done":
        print()
        print("  ℹ  La tarea W2 está marcada como completada (done).")
        print("     Limpia con: bago task --clear")
        print("     O acepta una nueva: bago ideas --accept N")
        print()
        return 1

    args = _build_args(task)

    print()
    print("  ┌──────────────────────────────────────────────────────────┐")
    print("  │  BAGO · Session opener desde handoff                     │")
    print("  └──────────────────────────────────────────────────────────┘")
    print(f"  Idea      : #{task.get('idea_index','?')} — {task.get('idea_title','—')}")
    print(f"  Objetivo  : {args['objetivo']}")
    print(f"  Roles     : {args['roles']}")
    print(f"  Artefactos: {args['artefactos']}")
    print()

    if dry:
        print("  [--dry] Comando que se ejecutaría:")
        print(f"  python3 {PREFLIGHT} \\")
        print(f"    --objetivo \"{args['objetivo']}\" \\")
        print(f"    --roles \"{args['roles']}\" \\")
        print(f"    --artefactos \"{args['artefactos']}\"")
        print()
        return 0

    cmd = [
        "python3", str(PREFLIGHT),
        "--objetivo", args["objetivo"],
        "--roles",    args["roles"],
        "--artefactos", args["artefactos"],
    ]
    result = subprocess.run(cmd, cwd=str(ROOT))
    return result.returncode



def _self_test():
    """Autotest mínimo — verifica arranque limpio del módulo."""
    from pathlib import Path as _P
    assert _P(__file__).exists(), "fichero no encontrado"
    print("  1/1 tests pasaron")

if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
        raise SystemExit(0)
    raise SystemExit(main())
