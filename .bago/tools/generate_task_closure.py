#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_task_closure.py — Genera artefactos de cierre para una tarea W2.

Lee pending_w2_task.json, crea un CHG y una EVD de cierre, y actualiza
global_state.json con el nuevo inventario y referencias finales.
"""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

# Importar StateStore (este fichero vive en .bago/tools/)
sys.path.insert(0, str(Path(__file__).parent))
from state_store import StateStore

ROOT  = Path(__file__).resolve().parents[2]
_store = StateStore(ROOT)


def _build_change(task: dict, change_id: str, evidence_id: str, now: str) -> dict:
    title = str(task.get("idea_title", "Cierre automático de sesión")).strip()
    return {
        "change_id": change_id,
        "type": "governance",
        "severity": "minor",
        "title": f"{title} · cierre W2 automático",
        "motivation": (
            "Registrar el cierre automático de la tarea W2 y dejar "
            "evidencia persistente del handoff completado."
        ),
        "status": "applied",
        "affected_components": [
            ".bago/tools/show_task.py",
            ".bago/tools/generate_task_closure.py",
            ".bago/state/pending_w2_task.json",
            ".bago/state/global_state.json",
        ],
        "related_evidence": evidence_id,
        "created_at": now,
        "updated_at": now,
        "author": "role_organizer",
    }


def _build_evidence(task: dict, change_id: str, evidence_id: str, now: str) -> dict:
    title = str(task.get("idea_title", "Cierre automático de sesión")).strip()
    summary = f"Cierre W2 automático: {title}"
    files = ", ".join(str(path) for path in task.get("archivos_candidatos", [])) or "sin archivos candidatos"
    gate = task.get("completion_gate", {}) or {}
    gate_status = gate.get("status", "KO")
    human_check = gate.get("human_check", "")
    tests = gate.get("tests", [])
    tests_text = ", ".join(
        f"{item.get('cmd', '')}=>{item.get('exit_code', '?')}" for item in tests
    ) or "sin tests"
    details = (
        "La tarea W2 quedó marcada como done, se generó un CHG de gobernanza "
        "y se actualizó global_state con el nuevo inventario. "
        f"Archivos candidatos de la tarea: {files}. "
        f"Gate de cierre: {gate_status}. "
        f"Tests ejecutados: {tests_text}. "
        f"Validación humana: {human_check}"
    )
    return {
        "evidence_id": evidence_id,
        "type": "closure",
        "related_to": [change_id, str(task.get("idea_title", ""))],
        "summary": summary,
        "details": details,
        "status": "recorded",
        "recorded_at": now,
    }


def _update_global_state(change_id: str, evidence_id: str, now: str) -> dict:
    # Mantenida por compatibilidad — ya no se usa en main(); usar StateStore directamente.
    gs = _store.global_state.get()
    gs["last_completed_change_id"]   = change_id
    gs["last_completed_evidence_id"] = evidence_id
    gs["updated_at"]                 = now
    gs["inventory"]                  = _store.inventory()
    _store.global_state.set(gs)
    return gs


def main() -> int:
    if not _store.pending_task.exists():
        print("  ❌ No existe pending_w2_task.json.")
        return 1

    try:
        task = _store.pending_task.get()
    except Exception as exc:
        print(f"  ❌ No se pudo leer la tarea W2: {exc}")
        return 1

    if str(task.get("status", "")).strip().lower() != "done":
        print("  ❌ La tarea W2 debe estar marcada como done antes de generar el cierre.")
        return 1

    now         = datetime.now(timezone.utc).isoformat()
    change_num  = _store.changes.next_num()
    evidence_num = _store.evidences.next_num()
    change_id   = f"BAGO-CHG-{change_num:03d}"
    evidence_id = f"BAGO-EVD-{evidence_num:03d}"

    change   = _build_change(task, change_id, evidence_id, now)
    evidence = _build_evidence(task, change_id, evidence_id, now)

    # Actualiza global_state con inventario real post-escritura
    inv_after = {
        "sessions":  _store.sessions.count(),
        "changes":   _store.changes.count() + 1,   # +1 porque aún no se ha guardado
        "evidences": _store.evidences.count() + 1,
    }

    with _store.transaction() as txn:
        txn.changes.save(change)
        txn.evidences.save(evidence)
        gs = _store.global_state.get()
        gs["last_completed_change_id"]   = change_id
        gs["last_completed_evidence_id"] = evidence_id
        gs["updated_at"]                 = now
        gs["inventory"]                  = inv_after
        txn.global_state.set(gs)

    print("  ✅ Cierre automático generado.")
    print(f"  CHG: {change_id}")
    print(f"  EVD: {evidence_id}")
    print(
        f"  Inventario: "
        f"ses={inv_after['sessions']} "
        f"chg={inv_after['changes']} "
        f"evd={inv_after['evidences']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
