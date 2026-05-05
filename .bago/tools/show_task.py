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
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT            = Path(__file__).resolve().parents[2]
TASK_FILE       = ROOT / ".bago" / "state" / "pending_w2_task.json"
IMPLEMENTED_FILE = ROOT / ".bago" / "state" / "implemented_ideas.json"
DB_PATH         = ROOT / ".bago" / "state" / "bago.db"
CLOSE_DIR       = ROOT / ".bago" / "state"


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
    """Añade el título de la idea a implemented_ideas.json y a bago.db."""
    title = (task.get("title") or task.get("idea_title") or "").strip()
    now   = datetime.now(timezone.utc).isoformat()

    # ── JSON registry ───────────────────────────────────────────────────────
    try:
        if IMPLEMENTED_FILE.exists():
            data = json.loads(IMPLEMENTED_FILE.read_text(encoding="utf-8"))
            # Normalizar: soportar clave legacy "ideas_completed" y nueva "implemented"
            existing = data.get("implemented") or data.get("ideas_completed") or []
        else:
            existing = []

        if title and not any(e.get("title") == title for e in existing):
            existing.append({
                "title":   title,
                "slot":    task.get("slot"),
                "done_at": now,
            })
        IMPLEMENTED_FILE.write_text(
            json.dumps({"implemented": existing, "updated_at": now},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass

    # ── SQLite registry ─────────────────────────────────────────────────────
    try:
        if DB_PATH.exists() and title:
            import hashlib
            idea_id = hashlib.sha256(title.encode()).hexdigest()[:16]
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "INSERT OR IGNORE INTO implemented_ideas"
                " (id, idea_title, session_id, implemented_at) VALUES (?, ?, ?, ?)",
                (idea_id, title, "show_task", now),
            )
            conn.commit()
            conn.close()
    except Exception:
        pass


def _load_implemented_summary() -> str:
    """Devuelve un resumen en Markdown de las ideas ya implementadas."""
    try:
        if IMPLEMENTED_FILE.exists():
            data = json.loads(IMPLEMENTED_FILE.read_text(encoding="utf-8"))
            entries = data.get("implemented") or []
            if entries:
                lines = [f"- {e.get('title', '—')} ({e.get('done_at', '')[:10]})" for e in entries]
                return "\n".join(lines)
    except Exception:
        pass
    return "- (sin registro de ideas previas)"


def _get_git_recent_changes() -> str:
    """Devuelve los archivos cambiados recientemente según git."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~3", "HEAD"],
            capture_output=True, text=True, cwd=str(ROOT), timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            files = result.stdout.strip().splitlines()[:10]
            return "\n".join(f"- `{f}`" for f in files)
    except Exception:
        pass
    return "- (git no disponible)"


def _generate_session_close(task: dict) -> Path | None:
    """Genera el artefacto de cierre de sesión en .bago/state/."""
    try:
        now      = datetime.now(timezone.utc)
        ts       = now.strftime("%Y%m%d_%H%M%S")
        title    = task.get("title") or task.get("idea_title", "tarea")
        objetivo = task.get("objetivo", "—")
        alcance  = task.get("alcance",  "—")
        metric   = task.get("validacion") or task.get("metric", "—")
        archivos = task.get("archivos") or task.get("archivos_candidatos", [])
        slot     = task.get("slot")
        gen      = task.get("generation")
        accepted_at = task.get("accepted_at", "—")
        done_at     = task.get("done_at", now.isoformat())

        slot_label = f"SLOT {slot} GEN {gen}" if slot else "sin-slot"
        archivos_md = "\n".join(f"- `{f}`" for f in archivos) if archivos else "- (no especificados)"
        impl_summary = _load_implemented_summary()
        git_changes = _get_git_recent_changes()

        md = f"""# Cierre de sesión — {title}

**Fecha inicio** : {accepted_at[:19].replace('T', ' ')} UTC
**Fecha cierre** : {done_at[:19].replace('T', ' ')} UTC
**Idea**         : {slot_label}
**Estado**       : ✅ COMPLETADA

## Objetivo
{objetivo}

## Alcance implementado
{alcance}

## Archivos candidatos
{archivos_md}

## Cambios recientes en git
{git_changes}

## Métrica de aceptación
{metric}

## Historial de ideas implementadas en esta sesión
{impl_summary}

## Notas
Artefacto generado automáticamente por `bago task --done`.
"""
        out_path = CLOSE_DIR / f"session_close_{ts}.md"
        out_path.write_text(md, encoding="utf-8")
        return out_path
    except Exception:
        return None


def _reopen_from_continuity() -> int:
    """
    Muestra el artefacto de la última sesión cerrada para retomar el contexto.
    Ayuda a reactivar la sesión sin reconstruir contexto manualmente.
    """
    close_files = sorted(CLOSE_DIR.glob("session_close_*.md"), reverse=True)
    if not close_files:
        print()
        print("  ℹ  No hay artefactos de cierre previos.")
        print("     Cierra una tarea con: bago task --done")
        print()
        return 0

    last = close_files[0]
    print()
    print("  ┌──────────────────────────────────────────────────────────┐")
    print(f"  │  🔄  Continuidad desde: {last.name[:46]}  │")
    print("  └──────────────────────────────────────────────────────────┘")
    print()
    # Mostrar contenido del artefacto
    try:
        content = last.read_text(encoding="utf-8")
        for line in content.splitlines():
            print(f"  {line}")
    except Exception as e:
        print(f"  ⚠  No se pudo leer el artefacto: {e}")
    print()
    if len(close_files) > 1:
        print(f"  📂  {len(close_files)} artefactos disponibles en .bago/state/")
    print("  💡  Acepta una nueva idea con: bago ideas --accept N")
    print()
    return 0


def main() -> int:
    args = sys.argv[1:]
    clear  = "--clear"  in args
    done   = "--done"   in args
    reopen = "--reopen" in args

    if reopen:
        return _reopen_from_continuity()

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
        task["done_at"] = datetime.now(timezone.utc).isoformat()
        TASK_FILE.write_text(json.dumps(task, ensure_ascii=False, indent=2), encoding="utf-8")
        _register_implemented(task)
        close_path = _generate_session_close(task)
        print("  ✅ Tarea marcada como completada.")
        if close_path:
            print(f"  📄 Artefacto de cierre: {close_path.relative_to(ROOT)}")
        _display(task)
        # ── Recordatorio de cosecha ──────────────────────────────────────────
        print("  ┌──────────────────────────────────────────────────────────┐")
        print("  │  🌾  Siguiente paso recomendado:                          │")
        print("  │                                                           │")
        print("  │     bago cosecha   →  preserva el artefacto de sesión    │")
        print("  │     bago ideas     →  selecciona la próxima mejora       │")
        print("  └──────────────────────────────────────────────────────────┘")
        print()
        return 0

    _display(task)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
