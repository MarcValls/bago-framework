#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iteration_logger.py — Registro de iteraciones de trabajo BAGO

Registra cada invocación de bago en .bago/state/iterations/ para acumular
datos que permitan detectar patrones de evolución del framework:
  - comandos más usados
  - workspaces recurrentes
  - workflows con mayor rotación
  - síntomas de necesidad de nuevos agentes, roles, herramientas o prompts

Uso:
  python3 .bago/tools/iteration_logger.py log --cmd "bago ideas" [--workspace <path>]
  python3 .bago/tools/iteration_logger.py summary
  python3 .bago/tools/iteration_logger.py summary --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

# ─── Rutas ────────────────────────────────────────────────────────────────────
BAGO_ROOT      = Path(__file__).resolve().parent.parent          # .bago/
STATE_DIR      = BAGO_ROOT / "state"
ITERATIONS_DIR = STATE_DIR / "iterations"
CONTEXT_PATH   = STATE_DIR / "repo_context.json"

# ─── Colores ANSI ─────────────────────────────────────────────────────────────
USE_COLOR = sys.stdout.isatty() and "--plain" not in sys.argv

def _c(code: str, text: str) -> str:
    return f"\033[{code}m{text}\033[0m" if USE_COLOR else text

CYAN   = lambda t: _c("1;36", t)
GREEN  = lambda t: _c("1;32", t)
YELLOW = lambda t: _c("1;33", t)
BOLD   = lambda t: _c("1",    t)
DIM    = lambda t: _c("2",    t)

# ─── Tipos de evolución sugeribles ───────────────────────────────────────────
EVOLUTION_TYPES = [
    "prompt",       # afinar prompt de agente
    "role",         # nuevo o ajustado rol
    "agent",        # nuevo agente
    "workflow",     # nuevo o mejorado workflow
    "tool",         # nueva herramienta / script
    "documentation",# actualizar documentación
]

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _load_context() -> dict:
    if CONTEXT_PATH.exists():
        try:
            return json.loads(CONTEXT_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def _next_iter_id() -> str:
    ITERATIONS_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(ITERATIONS_DIR.glob("ITER-*.json"))
    if not existing:
        return "ITER-0001"
    last = existing[-1].stem          # e.g. "ITER-0042"
    try:
        n = int(last.split("-")[1]) + 1
    except (IndexError, ValueError):
        n = len(existing) + 1
    return f"ITER-{n:04d}"


def log_iteration(cmd: str, workspace: str | None = None, notes: str = "") -> dict:
    """Registra una iteración de trabajo y la persiste en JSON."""
    ctx = _load_context()
    iter_id = _next_iter_id()

    record = {
        "id": iter_id,
        "timestamp": _now_iso(),
        "cmd": cmd,
        "workspace": workspace or ctx.get("repo_root", ""),
        "working_mode": ctx.get("working_mode", ""),
        "notes": notes,
    }

    path = ITERATIONS_DIR / f"{iter_id}.json"
    path.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return record


def load_all_iterations() -> list[dict]:
    if not ITERATIONS_DIR.exists():
        return []
    records = []
    for f in sorted(ITERATIONS_DIR.glob("ITER-*.json")):
        try:
            records.append(json.loads(f.read_text(encoding="utf-8")))
        except Exception:
            pass
    return records


# ─── Análisis de evolución ────────────────────────────────────────────────────

def _evolution_hints(records: list[dict]) -> list[dict]:
    """Genera sugerencias de evolución basadas en patrones de uso."""
    hints: list[dict] = []
    if not records:
        return hints

    cmd_counter   = Counter(r.get("cmd", "") for r in records)
    ws_counter    = Counter(r.get("workspace", "") for r in records)
    mode_counter  = Counter(r.get("working_mode", "") for r in records)
    total         = len(records)

    # Comando más frecuente → podría necesitar optimización de prompt/rol
    top_cmd, top_count = cmd_counter.most_common(1)[0]
    if top_count >= max(3, total * 0.3):
        hints.append({
            "type": "prompt",
            "reason": f"El comando '{top_cmd}' representa {top_count}/{total} iteraciones.",
            "suggestion": f"Revisar y afinar el prompt/rol asociado a '{top_cmd}'.",
        })

    # Uso frecuente en modo external → podría merecer un agente o workflow dedicado
    if mode_counter.get("external", 0) >= max(3, total * 0.4):
        hints.append({
            "type": "workflow",
            "reason": "Alta proporción de sesiones en modo externo (external).",
            "suggestion": "Considerar un workflow dedicado a integración de repos externos.",
        })

    # Workspace recurrente → podría merecer un preset/configuración guardada
    top_ws, ws_count = ws_counter.most_common(1)[0]
    if ws_count >= max(3, total * 0.25) and top_ws:
        hints.append({
            "type": "tool",
            "reason": f"El workspace '{top_ws}' aparece en {ws_count}/{total} iteraciones.",
            "suggestion": "Crear un preset de workspace para acceso rápido.",
        })

    # Muchas iteraciones sin workflows → posible falta de automatización
    if total >= 10 and mode_counter.get("self", 0) >= 5:
        hints.append({
            "type": "documentation",
            "reason": f"Con {total} iteraciones acumuladas, puede haber patrones no documentados.",
            "suggestion": "Revisar ESTADO_BAGO_ACTUAL.md y actualizar guías de uso frecuente.",
        })

    return hints


# ─── Resumen ──────────────────────────────────────────────────────────────────

def _print_summary(records: list[dict], hints: list[dict]) -> None:
    total = len(records)
    print()
    print(BOLD(CYAN("═══ BAGO · Iteraciones de trabajo ═══════════════════════")))
    print(f"  Total iteraciones registradas: {BOLD(str(total))}")

    if not records:
        print(DIM("  Sin datos aún. Cada invocación de bago se irá registrando."))
        print()
        return

    # Distribución de comandos
    cmd_counter = Counter(r.get("cmd", "") for r in records)
    print()
    print(BOLD("  Comandos más usados:"))
    for cmd, count in cmd_counter.most_common(8):
        bar = "█" * count
        print(f"    {CYAN(cmd or '(vacío)'):35s} {count:3d}  {DIM(bar)}")

    # Distribución de modos
    mode_counter = Counter(r.get("working_mode", "") for r in records)
    print()
    print(BOLD("  Modos de trabajo:"))
    for mode, count in mode_counter.most_common():
        pct = int(count / total * 100)
        label = {"self": "framework", "external": "externo", "parent": "padre"}.get(mode, mode)
        print(f"    {CYAN(label):15s}  {count:3d}  ({pct}%)")

    # Última iteración
    last = records[-1]
    print()
    print(BOLD("  Última iteración:"))
    print(f"    id:        {DIM(last.get('id', '?'))}")
    print(f"    timestamp: {DIM(last.get('timestamp', '?'))}")
    print(f"    cmd:       {last.get('cmd', '?')}")
    print(f"    workspace: {DIM(last.get('workspace', '?'))}")

    # Sugerencias de evolución
    if hints:
        print()
        print(BOLD(YELLOW("  💡 Sugerencias de evolución:")))
        for h in hints:
            etype = h.get("type", "?")
            print(f"    [{CYAN(etype):15s}] {h.get('suggestion', '')}")
            print(f"    {DIM('Razón: ' + h.get('reason', ''))}")
            print()
    else:
        print()
        print(DIM("  Sin sugerencias de evolución aún (se necesitan más datos)."))

    print()


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _parse() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="iteration_logger",
        description="Registro y análisis de iteraciones BAGO.",
    )
    sub = p.add_subparsers(dest="action")

    log_p = sub.add_parser("log", help="Registra una iteración")
    log_p.add_argument("--cmd",       default="",  help="Comando invocado")
    log_p.add_argument("--workspace", default=None, help="Ruta del workspace activo")
    log_p.add_argument("--notes",     default="",  help="Notas opcionales")

    sum_p = sub.add_parser("summary", help="Muestra resumen y sugerencias de evolución")
    sum_p.add_argument("--json", action="store_true", dest="as_json")

    return p.parse_args()


def main() -> int:
    args = _parse()

    if args.action == "log":
        record = log_iteration(cmd=args.cmd, workspace=args.workspace, notes=args.notes)
        print(json.dumps(record, indent=2, ensure_ascii=False))
        return 0

    if args.action == "summary" or args.action is None:
        records = load_all_iterations()
        hints   = _evolution_hints(records)
        if getattr(args, "as_json", False):
            print(json.dumps({"total": len(records), "records": records, "hints": hints},
                             indent=2, ensure_ascii=False))
        else:
            _print_summary(records, hints)
        return 0

    print(f"Acción desconocida: {args.action}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
