#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
show_task.py — Muestra la tarea W2 pendiente generada por `bago ideas --accept N`.

Uso:
  python3 .bago/tools/show_task.py            # muestra la tarea activa
  python3 .bago/tools/show_task.py --done     # marca la tarea como completada
  python3 .bago/tools/show_task.py --clear    # elimina pending_w2_task.json
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT            = Path(__file__).resolve().parents[2]
TASK_FILE       = ROOT / ".bago" / "state" / "pending_w2_task.json"
IMPLEMENTED_FILE = ROOT / ".bago" / "state" / "implemented_ideas.json"


def _load() -> dict | None:
    if not TASK_FILE.exists():
        return None
    try:
        return json.loads(TASK_FILE.read_text(encoding="utf-8"))
    except Exception:
        return None


def _display(task: dict) -> None:
    status_icon = "✅" if task.get("status") == "done" else "⏳"
    print()
    print("  ┌──────────────────────────────────────────────────────────┐")
    print(f"  │  BAGO · Tarea W2 pendiente  {status_icon}                          │")
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
    validation = task.get("validacion_minima", [])
    print(f"  Validación mínima ({len(validation)}):")
    for v in validation:
        print(f"    ✓ {v}")
    print()
    metric = task.get("metric", "").strip()
    if metric:
        print(f"  Métrica      : {metric}")
    print(f"  Siguiente paso: {task.get('siguiente_paso', '—')}")
    print()
    print("  Comandos:")
    print("    bago task --done   → marcar completada")
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


def _generate_close_artifact(task: dict) -> None:
    """Llama a session_close_generator para crear el artefacto de cierre."""
    try:
        import importlib.util
        gen_path = Path(__file__).parent / "session_close_generator.py"
        spec = importlib.util.spec_from_file_location("session_close_generator", gen_path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        result = mod.generate(task=task)
        print(f"  📄 Artefacto de cierre: {result.relative_to(ROOT)}")
    except Exception as exc:
        print(f"  ⚠  No se pudo generar el artefacto de cierre: {exc}")


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
        print("  ℹ  No hay tarea W2 pendiente.")
        print("     Acepta una idea con: bago ideas --accept N")
        print()
        return 0

    if done:
        task["status"] = "done"
        TASK_FILE.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
        _register_implemented(task)
        print("  ✅ Tarea marcada como completada.")
        _generate_close_artifact(task)
        _display(task)
        return 0

    _display(task)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
