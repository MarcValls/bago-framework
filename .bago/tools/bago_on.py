#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bago_on.py — Activa explícitamente el modo BAGO sobre el host del pack.

Uso:
  python3 .bago/tools/bago_on.py
  python3 .bago/tools/bago_on.py --json
"""

from __future__ import annotations

import argparse
import json

from repo_context_guard import detected_context, save_context


def _parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--json", action="store_true", dest="as_json")
    return parser.parse_args()


def _result() -> dict[str, object]:
    ctx = detected_context()
    save_context(ctx)
    commands = [
        {"cmd": "bago", "scope": "pack", "reason": "banner y estado operativo del pack"},
        {"cmd": "bago dashboard", "scope": "pack", "reason": "panel de salud del pack"},
        {"cmd": "bago ideas", "scope": "pack", "reason": "entrada normal de ideación"},
        {"cmd": "bago task", "scope": "pack", "reason": "consulta de handoff activo"},
        {"cmd": "bago session", "scope": "pack", "reason": "entrada a ejecución controlada"},
        {"cmd": "bago cosecha", "scope": "pack", "reason": "cierre o formalización W9"},
        {"cmd": "bago debug", "scope": "dual", "reason": "debug del propio pack"},
        {"cmd": "bago validate", "scope": "pack", "reason": "integridad canónica"},
    ]
    workflows = [
        {"id": "workflow_system_change", "reason": "si el trabajo afecta al propio pack BAGO"},
        {"id": "W6_IDEACION_APLICADA", "reason": "para seleccionar mejoras o nuevas tareas"},
        {"id": "W7_FOCO_SESION", "reason": "para trabajo productivo concreto dentro del host"},
        {"id": "W9_COSECHA", "reason": "para formalizar contexto acumulado o cierre"},
    ]
    workflow_chains = [
        "W6_IDEACION_APLICADA -> W7_FOCO_SESION -> W9_COSECHA",
        "workflow_system_change -> W2_IMPLEMENTACION_CONTROLADA -> W9_COSECHA",
    ]
    command_chains = [
        "bago ideas -> bago task -> bago session -> bago cosecha",
        "bago debug -> bago validate -> bago dashboard",
    ]
    return {
        "context": ctx,
        "commands": commands,
        "workflows": workflows,
        "workflow_chains": workflow_chains,
        "command_chains": command_chains,
    }


def _print_human(result: dict[str, object]) -> None:
    print()
    print("═══ BAGO ON ════════════════════════════════════════════")
    print(f"Modo activo: {result['context']['working_mode']}")
    print(f"Host:        {result['context']['repo_root']}")
    print()
    print("Comandos BAGO disponibles:")
    for item in result["commands"]:
        print(f"  - [{item['scope']}] {item['cmd']}")
        print(f"    {item['reason']}")
    print()
    print("Workflows posibles:")
    for item in result["workflows"]:
        print(f"  - {item['id']}")
        print(f"    {item['reason']}")
    print()
    print("Cadenas WF sugeridas:")
    for item in result["workflow_chains"]:
        print(f"  - {item}")
    print()
    print("Cadenas de comandos sugeridas:")
    for item in result["command_chains"]:
        print(f"  - {item}")
    print()
    print("Cambiar a repo externo:")
    print("  - bago repo-on /ruta/al/repo")
    print()


def main() -> int:
    args = _parse()
    result = _result()
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_human(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
