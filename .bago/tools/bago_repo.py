#!/usr/bin/env python3
"""bago_repo — Gestión de repositorios BAGO.

Router de subcomandos para operaciones de repositorio.

Uso:
  bago repo list            → lista repos del workspace
  bago repo clone <url>     → clona un repo con setup BAGO
  bago repo switch <name>   → cambia el repo activo
  bago repo                 → muestra este menú
"""
import subprocess, sys
from pathlib import Path

TOOLS = Path(__file__).parent
PYTHON = sys.executable

SUBCOMMANDS = {
    "list":   (TOOLS / "repo_list.py",   []),
    "ls":     (TOOLS / "repo_list.py",   []),
    "clone":  (TOOLS / "repo_clone.py",  []),
    "switch": (TOOLS / "repo_switch.py", []),
    "sw":     (TOOLS / "repo_switch.py", []),
}

def _usage():
    print(__doc__)
    print("Subcomandos disponibles:")
    for k in ["list", "clone", "switch"]:
        print(f"  bago repo {k}")

def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        _usage(); return
    sub = args[0].lower()
    if sub not in SUBCOMMANDS:
        print(f"❌ Subcomando desconocido: '{sub}'"); _usage(); sys.exit(1)
    script, extra = SUBCOMMANDS[sub]
    cmd = [PYTHON, str(script)] + extra + args[1:]
    sys.exit(subprocess.call(cmd))

if __name__ == "__main__":
    main()
