#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
session_close_generator.py — Genera el artefacto de cierre de sesión.

Se llama automáticamente desde show_task.py --done.
También puede invocarse de forma independiente:

  python3 .bago/tools/session_close_generator.py [--task-file PATH] [--out PATH]

El artefacto se escribe en:
  .bago/state/sessions/SESSION_CLOSE_<YYYYMMDD_HHMMSS>.md
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT          = Path(__file__).resolve().parents[2]
STATE_DIR     = ROOT / ".bago" / "state"
SESSIONS_DIR  = STATE_DIR / "sessions"
CHANGES_DIR   = STATE_DIR / "changes"
EVIDENCES_DIR = STATE_DIR / "evidences"
TASK_FILE     = STATE_DIR / "pending_w2_task.json"


def _load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _count_dir(path: Path, pattern: str = "*.json") -> int:
    if not path.exists():
        return 0
    return len(list(path.glob(pattern)))


def generate(task: dict | None = None, out_path: Path | None = None) -> Path:
    """Genera el artefacto de cierre y devuelve la ruta del archivo creado."""
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

    now     = datetime.now(timezone.utc)
    ts      = now.strftime("%Y%m%d_%H%M%S")
    ts_iso  = now.isoformat()

    if task is None:
        task = _load_json(TASK_FILE) or {}

    idea_title = task.get("idea_title", "—")
    idea_index = task.get("idea_index", "?")
    objetivo   = task.get("objetivo", "—")
    alcance    = task.get("alcance", "—")
    workflow   = task.get("workflow", "—")
    metric     = task.get("metric", "—").strip() if task.get("metric") else "—"

    # Contar artefactos de estado
    n_changes   = _count_dir(CHANGES_DIR)
    n_evidences = _count_dir(EVIDENCES_DIR)

    # Últimos 5 cambios
    changes_block = ""
    if CHANGES_DIR.exists():
        files = sorted(CHANGES_DIR.glob("*.json"), reverse=True)[:5]
        lines = []
        for f in files:
            data = _load_json(f) or {}
            chg_id  = data.get("id", f.stem)
            summary = data.get("summary", data.get("description", "—"))
            lines.append(f"- **{chg_id}**: {summary}")
        if lines:
            changes_block = "\n".join(lines)

    if not changes_block:
        changes_block = "_Sin cambios registrados en este cierre._"

    content = f"""# Cierre de sesión — {ts_iso}

## Tarea completada

| Campo | Valor |
|-------|-------|
| Idea | #{idea_index} — {idea_title} |
| Workflow | {workflow} |
| Objetivo | {objetivo} |
| Alcance | {alcance} |
| Métrica | {metric} |

## Resumen de cambios ({n_changes} total)

{changes_block}

## Evidencias acumuladas

{n_evidences} evidencias registradas en `.bago/state/evidences/`.

## Estado del sistema al cierre

| Métrica | Valor |
|---------|-------|
| Cambios totales | {n_changes} |
| Evidencias totales | {n_evidences} |
| Timestamp cierre | {ts_iso} |

---
_Generado automáticamente por `session_close_generator.py`_
"""

    if out_path is None:
        out_path = SESSIONS_DIR / f"SESSION_CLOSE_{ts}.md"

    out_path.write_text(content, encoding="utf-8")
    return out_path


def main() -> int:
    args = sys.argv[1:]

    task_file = TASK_FILE
    out_path  = None

    i = 0
    while i < len(args):
        if args[i] == "--task-file" and i + 1 < len(args):
            task_file = Path(args[i + 1])
            i += 2
        elif args[i] == "--out" and i + 1 < len(args):
            out_path = Path(args[i + 1])
            i += 2
        else:
            i += 1

    task = _load_json(task_file) if task_file.exists() else {}
    result = generate(task=task, out_path=out_path)
    print(f"  📄 Artefacto de cierre generado: {result.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
