#!/usr/bin/env python3
"""
bago start — Entrada rápida al repo.

Ejecuta en secuencia:
  1. bago health      (semáforo de estado global)
  2. bago ideas       (top 5 ideas priorizadas)
  3. Prompt: ¿aceptar idea top? (s/N)
     - Si s → bago ideas --accept 1  (genera pending_w2_task.json)
     - Si n → salir

Equivale a la secuencia manual de inicio de sesión de trabajo BAGO.
SLOT 7 GEN 1 · Entrada rápida del repo
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT  = Path(__file__).resolve().parent.parent.parent   # C:\Marc_max_20gb
TOOLS = ROOT / ".bago" / "tools"


def _run(args: list[str]) -> int:
    """Execute a list command, stream output, return exit code."""
    result = subprocess.run(args, cwd=str(ROOT))
    return result.returncode


def main() -> None:
    sep = "=" * 52

    # ── 1. Health ────────────────────────────────────────────
    print(sep)
    print("BAGO START · health")
    print(sep)
    rc = _run([sys.executable, str(TOOLS / "health_score.py")])
    if rc != 0:
        print("\n⚠  Health reportó fallos. Revisa antes de continuar.")
        # No bloqueamos — el usuario decide

    print()

    # ── 2. Ideas ─────────────────────────────────────────────
    print(sep)
    print("BAGO START · ideas top")
    print(sep)
    rc_ideas = _run([sys.executable, str(TOOLS / "emit_ideas.py")])

    if rc_ideas != 0:
        print("\nKO en ideas — gate no pasa. Repara el baseline primero.")
        sys.exit(rc_ideas)

    print()

    # ── 3. Prompt de aceptación ───────────────────────────────
    print(sep)
    try:
        answer = input("¿Aceptar idea #1 como tarea activa? [s/N]: ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        print("Saliendo sin aceptar.")
        sys.exit(0)

    if answer in {"s", "si", "sí", "y", "yes"}:
        print()
        rc_accept = _run([sys.executable, str(TOOLS / "emit_ideas.py"), "--accept", "1"])
        sys.exit(rc_accept)
    else:
        print("Ninguna idea aceptada. Usa `bago ideas --accept N` cuando quieras.")
        sys.exit(0)


if __name__ == "__main__":
    main()
