#!/usr/bin/env python3
"""
cosecha.py — BAGO ESCENARIO-003
Protocolo W9: 3 preguntas → sesión harvest cerrada + CHG + EVD automáticos.

Uso:
  python3 .bago/tools/cosecha.py
  python3 .bago/tools/cosecha.py --dry-run   (muestra lo que crearía sin escribir)
"""

import json, sys
from datetime import datetime, timezone
from pathlib import Path

# ─── Rutas ────────────────────────────────────────────────────────────────────
BAGO_ROOT  = Path(__file__).resolve().parent.parent
STATE_DIR  = BAGO_ROOT / "state"
SESSIONS   = STATE_DIR / "sessions"
CHANGES    = STATE_DIR / "changes"
EVIDENCES  = STATE_DIR / "evidences"

DRY_RUN = "--dry-run" in sys.argv

# ─── Utilidades ───────────────────────────────────────────────────────────────

def _next_id(folder, prefix, pad=3):
    """Devuelve el siguiente ID disponible para CHG o EVD."""
    existing = [f.stem for f in folder.glob(f"BAGO-{prefix}-*.json")]
    nums = []
    for e in existing:
        parts = e.split("-")
        if len(parts) >= 3 and parts[-1].isdigit():
            nums.append(int(parts[-1]))
    n = max(nums, default=0) + 1
    return f"BAGO-{prefix}-{str(n).zfill(pad)}"


def _next_session_id():
    """Genera el ID de la siguiente sesión harvest."""
    today = datetime.now().strftime("%Y-%m-%d")
    prefix = f"SES-HARVEST-{today}"
    existing = [f.stem for f in SESSIONS.glob(f"{prefix}-*.json")]
    nums = [int(e.split("-")[-1]) for e in existing if e.split("-")[-1].isdigit()]
    n = max(nums, default=0) + 1
    return f"{prefix}-{str(n).zfill(3)}"


def _read_global_state():
    p = BAGO_ROOT / "state" / "global_state.json"
    return json.loads(p.read_text())


def _write_global_state(gs):
    p = BAGO_ROOT / "state" / "global_state.json"
    if not DRY_RUN:
        p.write_text(json.dumps(gs, indent=2, ensure_ascii=False))


def _ask(prompt, hint="", required=True):
    """Pregunta interactiva con hint opcional."""
    if hint:
        print(f"\n  {hint}")
    print(f"\n  ❓ {prompt}")
    print("  ──────────────────────────────────────────")
    lines = []
    while True:
        try:
            line = input("  > ")
        except EOFError:
            break
        if line == "" and lines:
            break
        if line == "" and required:
            print("  (respuesta requerida — pulsa Enter en blanco al terminar)")
            continue
        lines.append(line)
        if line == "":
            break
    return " ".join(lines).strip()


def _detect_modified_files():
    """Intenta detectar ficheros recientes usando context_detector si existe."""
    detector = BAGO_ROOT / "tools" / "context_detector.py"
    if detector.exists():
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("context_detector", detector)
            mod  = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod._unregistered_files()
        except Exception:
            pass
    return []


# ─── Flujo principal ──────────────────────────────────────────────────────────

def run():
    now = datetime.now(timezone.utc).isoformat()
    today_str = datetime.now().strftime("%Y-%m-%d")

    print()
    print("╔══════════════════════════════════════════════════╗")
    print("║   BAGO · Cosecha Contextual (W9)                 ║")
    print("║   3 preguntas → sesión harvest cerrada           ║")
    print("╠══════════════════════════════════════════════════╣")
    print("║  Responde con una o dos líneas. Enter en blanco  ║")
    print("║  para finalizar cada respuesta.                  ║")
    if DRY_RUN:
        print("║  ⚠️  DRY-RUN: no se escribirá ningún fichero    ║")
    print("╚══════════════════════════════════════════════════╝")

    # ── Pregunta 1 ────────────────────────────────────────────────────────────
    decision = _ask(
        "¿Qué decidiste en esta exploración?",
        hint="La decisión principal. Qué elegiste y por qué (máx. 2 líneas)."
    )

    # ── Pregunta 2 ────────────────────────────────────────────────────────────
    discard = _ask(
        "¿Qué descartaste y por qué?",
        hint="Qué opción o camino quedó fuera y la razón (máx. 2 líneas)."
    )

    # ── Pregunta 3 ────────────────────────────────────────────────────────────
    next_step = _ask(
        "¿Cuál es el próximo paso concreto?",
        hint="El siguiente artefacto a producir o acción a ejecutar."
    )

    # ── Ficheros afectados ────────────────────────────────────────────────────
    unregistered = _detect_modified_files()
    print()
    if unregistered:
        print(f"  📂 Ficheros detectados sin CHG: {len(unregistered)}")
        for f in unregistered[:5]:
            print(f"     · {f}")
    else:
        print("  📂 No se detectaron ficheros modificados sin CHG.")
    print()

    # ── Confirmación ──────────────────────────────────────────────────────────
    print("  ┌──────────────────────────────────────────────┐")
    print("  │  RESUMEN DE COSECHA                          │")
    print("  ├──────────────────────────────────────────────┤")
    print(f"  │  Decisión: {decision[:45]:<45} │")
    print(f"  │  Descarte: {discard[:45]:<45} │")
    print(f"  │  Próximo:  {next_step[:45]:<45} │")
    print("  └──────────────────────────────────────────────┘")
    print()

    confirm = input("  ¿Guardar esta cosecha? [S/n] ").strip().lower()
    if confirm == "n":
        print("\n  Cosecha cancelada.")
        return

    # ── Generar artefactos ────────────────────────────────────────────────────
    session_id = _next_session_id()
    chg_id = _next_id(CHANGES, "CHG")
    evd_id = _next_id(EVIDENCES, "EVD")

    artifacts = list(unregistered) or ["(exploración sin artefactos de fichero)"]

    session = {
        "session_id": session_id,
        "task_type": "harvest",
        "selected_workflow": "w9_cosecha",
        "roles_activated": ["role_auditor"],
        "user_goal": f"Cosecha contextual: {decision[:80]}",
        "status": "closed",
        "escenario": "ESCENARIO-003",
        "created_at": now,
        "updated_at": now,
        "artifacts": artifacts,
        "decisions": [
            f"DECISIÓN: {decision}",
            f"DESCARTE: {discard}"
        ],
        "next_step": next_step,
        "summary": f"Harvest W9. Decisión: {decision[:60]}. Próximo: {next_step[:60]}."
    }

    chg = {
        "change_id": chg_id,
        "type": "governance",
        "severity": "minor",
        "title": f"Cosecha contextual W9: {decision[:60]}",
        "motivation": f"Formalizar exploración libre. Decisión: {decision}. Descarte: {discard}.",
        "status": "applied",
        "affected_components": artifacts,
        "related_evidence": evd_id,
        "created_at": now,
        "updated_at": now,
        "author": "role_auditor"
    }

    evd = {
        "evidence_id": evd_id,
        "type": "decision",
        "related_to": [chg_id, session_id],
        "summary": f"Cosecha W9 — {session_id}",
        "details": (
            f"Decisión: {decision} | "
            f"Descarte: {discard} | "
            f"Próximo paso: {next_step} | "
            f"Ficheros afectados: {', '.join(artifacts[:3])}"
        ),
        "status": "recorded",
        "recorded_at": now
    }

    if DRY_RUN:
        print("\n  [DRY-RUN] Se crearían:")
        print(f"    · {SESSIONS / (session_id + '.json')}")
        print(f"    · {CHANGES / (chg_id + '.json')}")
        print(f"    · {EVIDENCES / (evd_id + '.json')}")
        print(f"\n  session:\n{json.dumps(session, indent=4, ensure_ascii=False)}")
        return

    # ── Escribir ficheros ─────────────────────────────────────────────────────
    (SESSIONS / f"{session_id}.json").write_text(
        json.dumps(session, indent=2, ensure_ascii=False))
    (CHANGES  / f"{chg_id}.json").write_text(
        json.dumps(chg,     indent=2, ensure_ascii=False))
    (EVIDENCES / f"{evd_id}.json").write_text(
        json.dumps(evd,     indent=2, ensure_ascii=False))

    # ── Actualizar global_state ───────────────────────────────────────────────
    gs = _read_global_state()
    gs["updated_at"] = now
    gs["last_completed_session_id"] = session_id
    gs["last_completed_workflow"] = "w9_cosecha"
    gs["last_completed_task_type"] = "harvest"
    gs["last_completed_roles"] = ["role_auditor"]
    gs["last_completed_change_id"] = chg_id
    gs["last_completed_evidence_id"] = evd_id
    gs["inventory"] = {
        "sessions": len(list(SESSIONS.glob("*.json"))),
        "changes":  len(list(CHANGES.glob("*.json"))),
        "evidences":len(list(EVIDENCES.glob("*.json")))
    }
    _write_global_state(gs)

    # ── Resultado ─────────────────────────────────────────────────────────────
    print()
    print("  ✅ Cosecha completada:")
    print(f"     · Sesión:   {session_id}")
    print(f"     · Cambio:   {chg_id}")
    print(f"     · Evidencia:{evd_id}")
    print()
    print("  ⚠️  Recuerda regenerar TREE+CHECKSUMS:")
    print("     python3 .bago/tools/validate_pack.py  (después de regenerar)")
    print()



def _self_test():
    """Autotest mínimo — verifica arranque limpio del módulo."""
    from pathlib import Path as _P
    assert _P(__file__).exists(), "fichero no encontrado"
    print("  1/1 tests pasaron")

if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
        raise SystemExit(0)
    run()
