#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
show_task.py — Muestra la tarea W2 registrada generada por `bago ideas --accept N`.

Uso:
  python3 .bago/tools/show_task.py            # muestra la tarea registrada
  python3 .bago/tools/show_task.py --done --test-cmd "<cmd>" --human-check "<texto>"
                                                # ejecuta tests + validación humana y marca completada
  python3 .bago/tools/show_task.py --clear    # elimina pending_w2_task.json
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT            = Path(__file__).resolve().parents[2]
TASK_FILE       = ROOT / ".bago" / "state" / "pending_w2_task.json"
IMPLEMENTED_FILE = ROOT / ".bago" / "state" / "implemented_ideas.json"
CLOSURE_HELPER  = ROOT / ".bago" / "tools" / "generate_task_closure.py"


def _load() -> dict | None:
    if not TASK_FILE.exists():
        return None
    try:
        return json.loads(TASK_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def _display(task: dict) -> None:
    done = task.get("status") == "done"
    status_icon = "✅" if done else "⏳"
    heading = "BAGO · Tarea W2 completada" if done else "BAGO · Tarea W2 pendiente"
    print()
    print("  ┌──────────────────────────────────────────────────────────┐")
    print(f"  │  {heading}  {status_icon}                          │")
    print("  └──────────────────────────────────────────────────────────┘")
    print(f"  Idea #{task.get('idea_index', '?')}: {task.get('idea_title', '—')}")
    print(f"  Prioridad : {task.get('priority', '—')}")
    print(f"  Workflow  : {task.get('workflow', '—')}")
    print(f"  Aceptada  : {task.get('accepted_at', '—')}")
    print()
    print(f"  Objetivo   : {task.get('objetivo', '—')}")
    print(f"  Alcance    : {task.get('alcance', '—')}")
    print(f"  No alcance : {task.get('no_alcance', '—')}")
    print()
    files = task.get("archivos_candidatos", [])
    print(f"  Archivos candidatos ({len(files)}):")
    for f in files:
        print(f"    · {f}")
    print()
    raw_validation = task.get("validacion_minima", [])
    if isinstance(raw_validation, str):
        validation = [raw_validation]
    elif isinstance(raw_validation, list):
        validation = [str(v) for v in raw_validation]
    else:
        validation = []
    print(f"  Validación mínima ({len(validation)}):")
    for v in validation:
        print(f"    ✓ {v}")
    print()
    metric = task.get("metric", "").strip()
    if metric:
        print(f"  Métrica      : {metric}")
    handoff_chain = task.get("handoff_chain", "").strip()
    if handoff_chain:
        print(f"  Handoff roles: {handoff_chain}")
    print(f"  Siguiente paso: {task.get('siguiente_paso', '—')}")
    gate = task.get("completion_gate", {})
    if gate:
        print()
        print(f"  Gate cierre : {gate.get('status', '—')}")
        print(f"  Human check : {gate.get('human_check', '—')}")
        tests = gate.get("tests", [])
        print(f"  Tests cierre ({len(tests)}):")
        for item in tests:
            status = "OK" if item.get("ok") else "KO"
            print(f"    · [{status}] {item.get('cmd','')}")
    print()
    print("  Comandos:")
    print("    bago task --done --test-cmd \"<cmd>\" --human-check \"<texto>\"")
    print("                     → ejecuta test gate + validación humana y marca completada")
    print("    bago task --clear  → limpiar tarea")
    print()


def _register_implemented(task: dict) -> None:
    """Añade el título de la idea a implemented_ideas.json."""
    try:
        if IMPLEMENTED_FILE.exists():
            data = json.loads(IMPLEMENTED_FILE.read_text(encoding="utf-8"))
        else:
            data = {"implemented": [], "updated_at": None}

        title = task.get("idea_title", "").strip()
        if title and not any(e.get("title") == title for e in data["implemented"]):
            data["implemented"].append({
                "title": title,
                "idea_index": task.get("idea_index"),
                "done_at": datetime.now(timezone.utc).isoformat(),
            })
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            IMPLEMENTED_FILE.write_text(
                json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
            )
    except Exception:
        pass  # registro no crítico


def _parse_done_args(args: list[str]) -> tuple[list[str], str]:
    test_cmds: list[str] = []
    human_check = ""
    idx = 0
    while idx < len(args):
        arg = args[idx]
        if arg == "--test-cmd":
            if idx + 1 >= len(args):
                raise SystemExit("  ❌ --test-cmd requiere un comando.")
            test_cmds.append(args[idx + 1].strip())
            idx += 2
            continue
        if arg == "--human-check":
            if idx + 1 >= len(args):
                raise SystemExit("  ❌ --human-check requiere un texto.")
            human_check = args[idx + 1].strip()
            idx += 2
            continue
        idx += 1
    return [cmd for cmd in test_cmds if cmd], human_check


def _run_test_gate(test_cmds: list[str], human_check: str) -> tuple[bool, dict]:
    if not test_cmds:
        return False, {
            "status": "KO",
            "reason": "Debes declarar al menos un --test-cmd para cerrar la tarea.",
            "tests": [],
            "human_check": human_check,
        }
    if len(human_check) < 20:
        return False, {
            "status": "KO",
            "reason": "Debes declarar --human-check con mínimo 20 caracteres.",
            "tests": [],
            "human_check": human_check,
        }

    tests = []
    for cmd in test_cmds:
        result = subprocess.run(
            ["/bin/zsh", "-lc", cmd],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        tests.append(
            {
                "cmd": cmd,
                "exit_code": result.returncode,
                "ok": result.returncode == 0,
            }
        )

    failed = [item for item in tests if not item["ok"]]
    if failed:
        return False, {
            "status": "KO",
            "reason": "Falló al menos un test de cierre.",
            "tests": tests,
            "human_check": human_check,
        }
    return True, {
        "status": "GO",
        "reason": "Tests de cierre en verde + validación humana declarada.",
        "tests": tests,
        "human_check": human_check,
    }


def main() -> int:
    args = sys.argv[1:]
    clear = "--clear" in args
    done = "--done" in args

    if clear:
        if TASK_FILE.exists():
            TASK_FILE.unlink()
            print("  ✅ Tarea eliminada.")
        else:
            print("  ℹ  No hay tarea pendiente.")
        return 0

    task = _load()
    if task is None:
        print()
        print("  ℹ  No hay tarea W2 registrada.")
        print("     Acepta una idea con: bago ideas --accept N")
        print()
        return 0

    if done:
        test_cmds, human_check = _parse_done_args(args)
        ok, gate = _run_test_gate(test_cmds, human_check)
        if not ok:
            print(f"  ❌ Gate de cierre: {gate.get('reason')}")
            print("     Reintenta con:")
            print("     bago task --done --test-cmd \"<comando test>\" --human-check \"<validación humana>\"")
            if gate.get("tests"):
                for item in gate["tests"]:
                    status = "OK" if item.get("ok") else "KO"
                    print(f"     [{status}] {item.get('cmd')}")
            return 1

        task["status"] = "done"
        task["completed_at"] = datetime.now(timezone.utc).isoformat()
        task["completion_gate"] = gate
        TASK_FILE.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
        print("  ✅ Tarea marcada como completada.")

        result = subprocess.run(
            [sys.executable, str(CLOSURE_HELPER)],
            capture_output=True,
            text=True,
            cwd=str(ROOT),
        )
        if result.stdout.strip():
            print(result.stdout.rstrip())
        if result.returncode != 0:
            if result.stderr.strip():
                print(result.stderr.rstrip(), file=sys.stderr)
            return result.returncode

        _register_implemented(task)
        _display(task)
        return 0

    _display(task)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
