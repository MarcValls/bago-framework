#!/usr/bin/env python3
"""bago_session_router — Ciclo de vida de sesiones BAGO.

Uso:
  bago session open      → abre sesión W2 pre-rellenada desde handoff
  bago session open --dry → muestra args sin ejecutar
  bago session close     → genera artefacto SESSION_CLOSE
  bago session harvest   → protocolo W9: cosecha + CHG + EVD automáticos
  bago session v2        → checklist de cierre técnico V2
  bago session           → muestra este menú
"""
import subprocess, sys
from pathlib import Path

TOOLS = Path(__file__).parent
PYTHON = sys.executable

SUBCOMMANDS = {
    "open":    (TOOLS / "session_opener.py",         []),
    "start":   (TOOLS / "session_opener.py",         []),   # alias
    "close":   (TOOLS / "session_close_generator.py",[]),
    "harvest": (TOOLS / "cosecha.py",                []),
    "cosecha": (TOOLS / "cosecha.py",                []),   # alias
    "v2":      (TOOLS / "v2_close_checklist.py",     []),
}

DESCRIPTIONS = {
    "open":    "abre sesión W2 pre-rellenada desde handoff",
    "close":   "genera artefacto SESSION_CLOSE al terminar",
    "harvest": "protocolo W9 — cierra sesión + CHG + EVD automáticos",
    "v2":      "checklist de cierre técnico V2 (validate/reconcile/stale)",
}

def _usage():
    print(__doc__)
    print("Subcomandos:")
    for k, desc in DESCRIPTIONS.items():
        print(f"  bago session {k:<10} → {desc}")

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        _usage(); return
    sub = args[0].lower()
    if sub not in SUBCOMMANDS:
        print(f"❌ Subcomando desconocido: '{sub}'"); _usage(); sys.exit(1)
    script, extra = SUBCOMMANDS[sub]
    sys.exit(subprocess.call([PYTHON, str(script)] + extra + args[1:]))

if __name__ == "__main__":
    main()
