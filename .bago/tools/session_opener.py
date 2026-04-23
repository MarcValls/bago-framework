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
sys.path.insert(0, str(Path(__file__).parent))
from bago_utils import get_state_dir, get_bago_tools_dir, get_project_root

ROOT       = get_project_root()
_STATE     = get_state_dir()
_TOOLS     = get_bago_tools_dir()
TASK_FILE  = _STATE / "pending_w2_task.json"
PREFLIGHT  = _TOOLS / "session_preflight.py"

WORKFLOW_ROLES: dict[str, str] = {
    "W2":  "role_architect,role_validator",
    "W3":  "role_executor,role_validator",
    "W4":  "role_auditor,role_organizer",
    "W5":  "role_executor,role_organizer",
    "W7":  "role_architect,role_validator",
    "W9":  "role_organizer,role_vertice",
}

DEFAULT_ROLES = "role_architect,role_validator"
DEFAULT_HANDOFF = "role_analyst>role_architect>role_generator>role_validator>role_vertice"

WORKFLOW_HANDOFFS: dict[str, str] = {
    "W2": "role_analyst>role_architect>role_generator>role_validator>role_vertice",
    "W3": "role_analyst>role_generator>role_validator>role_vertice",
    "W4": "role_auditor>role_organizer>role_validator>role_vertice",
    "W5": "role_generator>role_organizer>role_validator>role_vertice",
    "W7": "role_analyst>role_architect>role_generator>role_validator>role_vertice",
    "W9": "role_organizer>role_validator>role_vertice",
}


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
    wf = str(task.get("workflow", "")).strip().upper()
    handoff_chain = str(task.get("handoff_chain", "")).strip()
    if not handoff_chain:
        for key, chain in WORKFLOW_HANDOFFS.items():
            if key in wf:
                handoff_chain = chain
                break
    if not handoff_chain:
        handoff_chain = DEFAULT_HANDOFF
    return {
        "objetivo": objetivo,
        "roles": roles,
        "artefactos": artefactos,
        "handoff_chain": handoff_chain,
    }


def main() -> int:
    dry = "--dry" in sys.argv

    task = _load_task()
    if task is None:
        print()
        print("  ℹ  No hay tarea W2 registrada.")
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
    print(f"  Handoff   : {args['handoff_chain']}")
    print(f"  Artefactos: {args['artefactos']}")
    print()

    if dry:
        print("  [--dry] Comando que se ejecutaría:")
        print(f"  python3 {PREFLIGHT} \\")
        print(f"    --objetivo \"{args['objetivo']}\" \\")
        print(f"    --roles \"{args['roles']}\" \\")
        print(f"    --artefactos \"{args['artefactos']}\" \\")
        print(f"    --handoff-chain \"{args['handoff_chain']}\"")
        print()
        return 0

    cmd = [
        "python3", str(PREFLIGHT),
        "--objetivo", args["objetivo"],
        "--roles",    args["roles"],
        "--artefactos", args["artefactos"],
        "--handoff-chain", args["handoff_chain"],
    ]
    result = subprocess.run(cmd, cwd=str(ROOT))
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
