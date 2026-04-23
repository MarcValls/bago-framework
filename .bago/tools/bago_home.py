#!/usr/bin/env python3
"""
bago_home.py — Información sobre BAGO_HOME y proyectos vinculados.

Muestra:
  - Dónde está instalado BAGO (BAGO_HOME)
  - Versión del framework
  - Proyectos que usan esta instalación
  - Estado actual del proyecto (si BAGO_PROJECT_ROOT está definido)

Uso:
  python3 .bago/tools/bago_home.py
  bago home
  bago home --list-projects
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bago_utils import get_state_dir, get_bago_tools_dir, get_project_root, bold, colored, GREEN, CYAN, YELLOW, DIM, RESET

BAGO_HOME  = Path(__file__).resolve().parents[2]   # BAGO_CAJAFISICA/
BAGO_ROOT  = BAGO_HOME / ".bago"
STATE      = get_state_dir()


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _mode() -> str:
    """Detecta si estamos en modo framework (self) o modo proyecto."""
    env_state = os.environ.get('BAGO_STATE_DIR')
    if env_state:
        proj_root = os.environ.get('BAGO_PROJECT_ROOT', 'desconocido')
        return f"proyecto  ({proj_root})"
    return "framework (self)"


def show_home(list_projects: bool = False) -> None:
    gs = _load_json(STATE / "global_state.json")
    pack = _load_json(BAGO_HOME / "pack.json")
    registry = _load_json(BAGO_ROOT / "state" / "linked_projects.json")

    print()
    print(bold("╔═══ BAGO HOME ═══════════════════════════════════╗"))
    print(f"  {bold('BAGO_HOME')}   : {BAGO_HOME}")
    print(f"  {bold('Versión')}     : {pack.get('version', gs.get('bago_version', '?'))}")
    print(f"  {bold('Tools')}       : {BAGO_ROOT / 'tools'}")
    print(f"  {bold('Mode actual')} : {_mode()}")
    print(f"  {bold('State activo')}: {STATE}")
    print()

    # Estado del framework
    health = gs.get('system_health', '?')
    tests  = gs.get('integration_suite', '?')
    chg    = gs.get('changes', '?')
    baseline = gs.get('baseline_status', '?')
    print(colored("  Framework state:", CYAN))
    print(f"    health     : {health}")
    print(f"    tests      : {tests}")
    print(f"    CHGs       : {chg}")
    print(f"    baseline   : {baseline}")
    print()

    # Proyectos vinculados
    if registry:
        print(colored(f"  Proyectos vinculados ({len(registry)}):", CYAN))
        for path_str, info in sorted(registry.items()):
            name = info.get('name', Path(path_str).name)
            reg  = info.get('registered_at', '')[:10]
            exists = "✅" if Path(path_str).exists() else "⚠️  (no encontrado)"
            print(f"    {exists}  {bold(name):<20} {DIM}{path_str}{RESET}")
            if list_projects:
                state_dir = Path(info.get('state_dir', path_str + '/.bago/state'))
                if state_dir.exists():
                    n_ses = len(list(( state_dir / 'sessions').glob('*.json'))) if (state_dir / 'sessions').exists() else 0
                    n_chg = len(list((state_dir / 'changes').glob('*.json'))) if (state_dir / 'changes').exists() else 0
                    print(f"             sessions={n_ses}  changes={n_chg}  registrado={reg}")
    else:
        print(colored("  Sin proyectos vinculados.", YELLOW))
        print(f"  {DIM}Usa 'bago init /ruta/proyecto' para inicializar uno.{RESET}")

    print()
    print(bold("  Comandos útiles:"))
    print("    bago init /ruta/proyecto    → inicializar proyecto nuevo")
    print("    bago home --list-projects   → ver estado de cada proyecto")
    print(bold("╚═════════════════════════════════════════════════╝"))
    print()


def main():
    import argparse
    p = argparse.ArgumentParser(description="bago_home — info del framework y proyectos")
    p.add_argument("--list-projects", action="store_true", help="Mostrar detalle de proyectos")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    if args.test:
        _run_tests()
        return

    show_home(list_projects=args.list_projects)


def _run_tests():
    from bago_utils import print_ok, print_fail, finish_tests, reset_test_state
    reset_test_state()

    # Test: BAGO_HOME is correct
    if BAGO_HOME.is_dir() and (BAGO_HOME / ".bago" / "tools").is_dir():
        print_ok("bago_home:bago_home_exists")
    else:
        print_fail("bago_home:bago_home_exists", f"BAGO_HOME not found: {BAGO_HOME}")

    # Test: tools dir matches get_bago_tools_dir()
    if get_bago_tools_dir() == BAGO_HOME / ".bago" / "tools":
        print_ok("bago_home:tools_dir_consistent")
    else:
        print_fail("bago_home:tools_dir_consistent", f"mismatch: {get_bago_tools_dir()} vs {BAGO_HOME / '.bago' / 'tools'}")

    # Test: mode detection (no env var = framework mode)
    mode = _mode()
    if "framework" in mode:
        print_ok("bago_home:mode_self")
    else:
        print_fail("bago_home:mode_self", f"unexpected mode: {mode}")

    raise SystemExit(finish_tests(3))


if __name__ == "__main__":
    main()
