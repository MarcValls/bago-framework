#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
workflow_selector.py — Selector formal de workflow BAGO.

Modo interactivo: hace 4-5 preguntas y recomienda el workflow más adecuado.
Modo importable: workflow_selector.recommend(context_dict) → str

Workflows disponibles:
  W7_FOCO_SESION              — tarea técnica concreta definida
  W8_EXPLORACION              — exploración sin destino fijo
  W9_COSECHA                  — formalizar contexto acumulado
  W0_FREE_SESSION             — libre, experimental
  W2_IMPLEMENTACION_CONTROLADA — implementación con control de calidad
  W1_COLD_START               — bootstrap en repo nuevo
  workflow_system_change       — cambio al pack BAGO mismo

Uso:
  python3 .bago/tools/workflow_selector.py             # interactivo
  python3 .bago/tools/workflow_selector.py --auto      # modo automático (usa global_state)
"""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
GLOBAL_STATE = ROOT / "state" / "global_state.json"


def ask(question: str, default: str = "n") -> bool:
    """Pregunta sí/no, devuelve True si sí."""
    hint = "[S/n]" if default.lower() == "s" else "[s/N]"
    ans = input(f"  {question} {hint}: ").strip().lower()
    if not ans:
        return default.lower() == "s"
    return ans in ("s", "si", "sí", "yes", "y", "1")


def recommend(ctx: dict) -> str:
    """
    Dado un contexto dict, recomienda un workflow.
    ctx puede contener:
      - has_task: bool         (¿hay tarea técnica concreta?)
      - is_exploration: bool   (¿es exploración?)
      - has_accumulated: bool  (¿hay contexto acumulado para formalizar?)
      - is_bago_change: bool   (¿cambio al pack BAGO?)
      - is_new_repo: bool      (¿bootstrap en repo nuevo?)
      - needs_quality_gate: bool (¿requiere gate de calidad estricto?)
    """
    if ctx.get("is_bago_change"):
        return "workflow_system_change"
    if ctx.get("is_new_repo"):
        return "W1_COLD_START"
    if ctx.get("has_task"):
        if ctx.get("needs_quality_gate"):
            return "W2_IMPLEMENTACION_CONTROLADA"
        return "W7_FOCO_SESION"
    if ctx.get("is_exploration"):
        return "W8_EXPLORACION"
    if ctx.get("has_accumulated"):
        return "W9_COSECHA"
    return "W0_FREE_SESSION"


def describe(workflow: str) -> str:
    descriptions = {
        "W7_FOCO_SESION":               "Tarea técnica definida, ejecución focalizada",
        "W8_EXPLORACION":               "Exploración libre sin entregable fijo",
        "W9_COSECHA":                   "Formalizar contexto y decisiones acumuladas",
        "W0_FREE_SESSION":              "Sesión libre, experimental o de baja estructura",
        "W2_IMPLEMENTACION_CONTROLADA": "Implementación con gate de calidad estricto",
        "W1_COLD_START":                "Bootstrap en repo o proyecto nuevo",
        "workflow_system_change":        "Cambio estructural al pack BAGO mismo",
    }
    return descriptions.get(workflow, "Workflow BAGO")


def auto_recommend() -> tuple[str, dict]:
    """Analiza global_state para recomendar sin interacción."""
    if not GLOBAL_STATE.exists():
        return "W7_FOCO_SESION", {}
    gs = json.loads(GLOBAL_STATE.read_text(encoding="utf-8"))

    ctx = {
        "has_task": False,
        "is_exploration": False,
        "has_accumulated": False,
        "is_bago_change": False,
        "is_new_repo": False,
        "needs_quality_gate": False,
    }

    # Heurísticas desde global_state
    last_wf = gs.get("last_completed_workflow", "")
    last_type = gs.get("last_completed_task_type", "")
    active_scenarios = gs.get("active_scenarios", [])
    system_health = gs.get("system_health", "stable")

    # Si hay escenarios activos → probablemente hay tarea
    if active_scenarios:
        ctx["has_task"] = True

    # Si último tipo fue harvest → posiblemente hay más contexto para cosechar
    if last_type in ("harvest", "cosecha"):
        ctx["has_accumulated"] = True

    # Si health no es stable → posiblemente exploración o cierre
    if system_health in ("degraded", "review_needed"):
        ctx["is_exploration"] = True

    return recommend(ctx), ctx


def interactive_mode() -> str:
    print()
    print("═══ BAGO Workflow Selector ══════════════════════════════")
    print("  Responde las preguntas para recibir una recomendación.")
    print()

    ctx = {}

    ctx["is_bago_change"] = ask("¿Estás modificando el propio pack BAGO (herramientas, core, estructura)?")
    if ctx["is_bago_change"]:
        wf = recommend(ctx)
        _print_result(wf)
        return wf

    ctx["is_new_repo"] = ask("¿Es un bootstrap en un repositorio o proyecto completamente nuevo?")
    if ctx["is_new_repo"]:
        wf = recommend(ctx)
        _print_result(wf)
        return wf

    ctx["has_task"] = ask("¿Hay una tarea técnica concreta y definida que completar?")
    if ctx["has_task"]:
        ctx["needs_quality_gate"] = ask("¿Requiere gate de calidad estricto (TDD, revisión formal, contrato)?")
        wf = recommend(ctx)
        _print_result(wf)
        return wf

    ctx["is_exploration"] = ask("¿Es exploración, investigación o análisis sin entregable fijo?")
    if ctx["is_exploration"]:
        wf = recommend(ctx)
        _print_result(wf)
        return wf

    ctx["has_accumulated"] = ask("¿Hay contexto, decisiones o artefactos acumulados que formalizar?")
    wf = recommend(ctx)
    _print_result(wf)
    return wf


def _print_result(wf: str):
    print()
    print(f"  → Workflow recomendado: {wf}")
    print(f"    {describe(wf)}")
    print()


def main():
    auto = "--auto" in sys.argv or "--no-interactive" in sys.argv

    if auto:
        wf, ctx = auto_recommend()
        print(f"Workflow recomendado: {wf}")
        print(f"  {describe(wf)}")
        return 0

    try:
        wf = interactive_mode()
    except (KeyboardInterrupt, EOFError):
        print("\n  Selección cancelada.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
