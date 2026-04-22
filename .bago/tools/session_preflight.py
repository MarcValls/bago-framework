#!/usr/bin/env python3
"""
session_preflight.py — Validador de reglas W7 antes de abrir una sesión BAGO.

Verifica que se cumplen las reglas del ESCENARIO-001 + continuidad de handoff:
  Regla A: ≥3 artefactos pre-declarados (no contar el JSON de sesión)
  Regla B: ≤2 roles activados
  Regla C: objetivo con formato "Verbo + objeto + criterio de done"
  Regla D: cadena de handoff de roles explícita y cerrando en validación

Uso:
  python3 tools/session_preflight.py \
    --objetivo "Crear X para que Y" \
    --roles "role_architect,role_validator" \
    --artefactos "docs/A.md,state/changes/CHG.json,tools/script.py" \
    --handoff-chain "role_analyst>role_architect>role_generator>role_validator>role_vertice"

Salida:
  GO  — cumple todas las reglas, listo para abrir sesión
  KO  — indica qué regla falla y cómo corregirla
"""

import argparse
import sys

ROLE_MAP = {
    "system_change":       ("role_architect", "role_validator"),
    "analysis":            ("role_auditor", "role_organizer"),
    "execution":           ("role_executor", "role_validator"),
    "sprint":              ("role_organizer", "role_vertice"),
    "project_bootstrap":   ("role_architect", "role_organizer"),
}

PROTOCOL_ARTIFACTS = {
    "state/sessions", "state/changes", "state/evidences",
    "TREE.txt", "CHECKSUMS.sha256",
}

VERBS_ES = [
    "crear", "actualizar", "corregir", "migrar", "añadir", "eliminar",
    "refactorizar", "documentar", "validar", "analizar", "implementar",
    "generar", "registrar", "cerrar", "optimizar", "diseñar",
]


def check_objetivo(objetivo: str) -> tuple[bool, str]:
    if not objetivo or len(objetivo.strip()) < 15:
        return False, "El objetivo es demasiado corto. Mínimo 15 caracteres con Verbo+Objeto+Done."
    low = objetivo.lower()
    has_verb = any(v in low for v in VERBS_ES)
    if not has_verb:
        return False, f"El objetivo no contiene un verbo de acción reconocido. Usa uno de: {', '.join(VERBS_ES[:8])}..."
    has_para = "para que" in low or "para " in low or " que " in low
    if not has_para:
        return False, "El objetivo no incluye criterio de done. Añade 'para que [resultado verificable]'."
    return True, "OK"


def check_roles(roles_raw: str) -> tuple[bool, str]:
    roles = [r.strip() for r in roles_raw.split(",") if r.strip()]
    if len(roles) == 0:
        return False, "Debes declarar al menos 1 rol."
    if len(roles) > 2:
        return False, f"Regla B: máximo 2 roles por sesión. Declaraste {len(roles)}: {roles}. Elimina los roles no esenciales."
    return True, f"OK ({len(roles)} rol/es: {roles})"


def is_protocol_artifact(path: str) -> bool:
    for prefix in PROTOCOL_ARTIFACTS:
        if path.startswith(prefix):
            return True
    return False


def check_artefactos(artefactos_raw: str) -> tuple[bool, str]:
    all_arts = [a.strip() for a in artefactos_raw.split(",") if a.strip()]
    useful = [a for a in all_arts if not is_protocol_artifact(a)]
    if len(useful) < 3:
        ejemplos = [a for a in all_arts if is_protocol_artifact(a)]
        msg = f"Regla A: necesitas ≥3 artefactos útiles (no de protocolo). Tienes {len(useful)}"
        if ejemplos:
            msg += f". Estos NO cuentan (protocolo): {ejemplos}"
        msg += ". Añade documentos, scripts, templates u otros archivos con valor real."
        return False, msg
    return True, f"OK ({len(useful)} artefactos útiles de {len(all_arts)} declarados)"


def check_handoff_chain(chain_raw: str, roles_raw: str) -> tuple[bool, str]:
    chain = [r.strip() for r in chain_raw.split(">") if r.strip()]
    active_roles = [r.strip() for r in roles_raw.split(",") if r.strip()]

    if not chain:
        return False, (
            "Regla D: falta --handoff-chain. "
            "Declara una secuencia de relevo: role_a>role_b>role_validator."
        )
    if len(chain) < 3:
        return False, (
            f"Regla D: handoff demasiado corto ({chain}). "
            "Necesitas al menos 3 etapas de relevo."
        )
    if any(chain[idx] == chain[idx - 1] for idx in range(1, len(chain))):
        return False, (
            f"Regla D: hay roles repetidos en pasos consecutivos ({chain}). "
            "Define una secuencia limpia sin duplicados contiguos."
        )
    if "role_validator" not in chain:
        return False, (
            "Regla D: la cadena no incluye role_validator. "
            "Todo cierre debe pasar por validación."
        )
    if chain[-1] not in {"role_validator", "role_vertice"}:
        return False, (
            f"Regla D: el último relevo debe cerrar en validación/supervisión, no en '{chain[-1]}'."
        )
    missing = [role for role in active_roles if role not in chain]
    if missing:
        return False, (
            f"Regla D: roles activos fuera del handoff {missing}. "
            "Alinea --roles con --handoff-chain."
        )
    return True, f"OK ({len(chain)} etapas: {' > '.join(chain)})"


def main():
    parser = argparse.ArgumentParser(
        description="Valida las reglas W7 antes de abrir una sesión BAGO (ESCENARIO-001)."
    )
    parser.add_argument("--objetivo",    required=True, help="Objetivo de la sesión: Verbo + objeto + criterio de done")
    parser.add_argument("--roles",       required=True, help="Roles separados por coma. Máximo 2.")
    parser.add_argument("--artefactos",  required=True, help="Artefactos pre-declarados separados por coma. Mínimo 3 útiles.")
    parser.add_argument("--handoff-chain", required=False, default="", help="Cadena de relevo entre roles: role_a>role_b>role_validator")
    parser.add_argument("--task-type",   default="system_change", help="Tipo de tarea (para sugerir roles). Default: system_change")
    args = parser.parse_args()

    results = []
    all_ok = True

    ok, msg = check_objetivo(args.objetivo)
    results.append(("Regla C — Objetivo", ok, msg))
    if not ok:
        all_ok = False

    ok, msg = check_roles(args.roles)
    results.append(("Regla B — Roles", ok, msg))
    if not ok:
        all_ok = False

    ok, msg = check_artefactos(args.artefactos)
    results.append(("Regla A — Artefactos", ok, msg))
    if not ok:
        all_ok = False

    ok, msg = check_handoff_chain(args.handoff_chain, args.roles)
    results.append(("Regla D — Handoff", ok, msg))
    if not ok:
        all_ok = False

    print()
    print("=" * 60)
    print("  BAGO · Session Preflight — ESCENARIO-001")
    print("=" * 60)
    for label, ok, msg in results:
        icon = "✅" if ok else "❌"
        print(f"\n  {icon} {label}")
        print(f"     {msg}")

    print()
    if all_ok:
        print("  ✅ GO — Sesión lista para abrir.")
        suggested = ROLE_MAP.get(args.task_type, None)
        if suggested:
            print(f"     Roles sugeridos para '{args.task_type}': {suggested[0]} + {suggested[1]}")
    else:
        print("  ❌ KO — Corrige los puntos marcados antes de abrir la sesión.")
        print("     Ver reglas completas en: workflows/W7_FOCO_SESION.md")
    print()

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
