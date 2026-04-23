#!/usr/bin/env python3
"""
bago_init.py — Inicializar un nuevo proyecto con BAGO.

Crea la estructura .bago/ en el directorio del proyecto con:
  - state/          → sesiones, cambios, sprints del proyecto
  - config/         → pack.json del proyecto
  - docs/           → documentación técnica del proyecto
  - bago            → launcher delgado que apunta a BAGO_HOME

Los tools siempre vienen de BAGO_HOME (el framework central).
El state es 100% local al proyecto — cada proyecto tiene su propia historia.

Uso:
  python3 .bago/tools/bago_init.py /ruta/del/proyecto
  bago init /ruta/del/proyecto
  bago init .            # inicializar el directorio actual

Modo self (ejecutado desde BAGO_CAJAFISICA):
  Si se ejecuta sin argumentos o con '.', crea el estado del framework mismo.
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from bago_utils import get_state_dir, get_bago_tools_dir

# BAGO_HOME = directorio donde vive el framework central
BAGO_HOME = Path(__file__).resolve().parents[2]   # BAGO_CAJAFISICA/


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _make_initial_global_state(project_name: str) -> dict:
    """Crea un global_state.json mínimo para un proyecto nuevo."""
    return {
        "bago_version": "3.0",
        "canon_version": "3.0",
        "project_name": project_name,
        "system_health": "green",
        "active_session_id": None,
        "active_task_type": None,
        "active_roles": [],
        "open_changes": 0,
        "baseline_status": "init",
        "baseline_code": None,
        "sprint_status": {},
        "tool_count": 0,
        "integration_suite": "0/0",
        "changes": 0,
        "inventory": {
            "sessions": 0,
            "changes": 0,
            "evidences": 0
        },
        "notes": f"Proyecto inicializado con bago init — {_now()}",
        "updated_at": _now()
    }


def _make_project_pack_json(project_name: str, project_root: Path) -> dict:
    """Crea un pack.json mínimo para el proyecto."""
    return {
        "id": project_name.lower().replace(" ", "_"),
        "name": project_name,
        "version": "1.0",
        "encoding": "UTF-8",
        "manifest": ".bago/config/pack.json",
        "description": f"Proyecto BAGO: {project_name}",
        "bago_home": str(BAGO_HOME),
        "state_dir": ".bago/state",
        "created_at": _now(),
        "principles": ["Balanceado", "Adaptativo", "Generativo", "Organizativo"],
        "governance": {
            "change_protocol": "CHG manual en .bago/state/changes/",
            "session_protocol": "W7 o W2 según complejidad"
        }
    }


def _make_launcher_script(project_bago_dir: Path) -> str:
    """Genera el script 'bago' launcher para el proyecto."""
    return f'''#!/usr/bin/env python3
"""
BAGO Project Launcher — auto-generado por 'bago init'.

Apunta al BAGO_HOME central para usar siempre los tools más actualizados.
El estado del proyecto se lee de .bago/state/ (local a este proyecto).

Para actualizar los tools: actualiza BAGO en {BAGO_HOME}
Para ver el estado: python3 {BAGO_HOME}/bago health
"""
import os
import sys
import subprocess
from pathlib import Path

# BAGO_HOME: instalación central del framework
BAGO_HOME = Path("{BAGO_HOME}")

# Rutas locales del proyecto
_HERE = Path(__file__).resolve().parent
BAGO_STATE_DIR = _HERE / ".bago" / "state"
BAGO_PROJECT_ROOT = _HERE

# Inyectar en entorno para que los tools lean el state del proyecto
env = os.environ.copy()
env["BAGO_STATE_DIR"] = str(BAGO_STATE_DIR)
env["BAGO_PROJECT_ROOT"] = str(BAGO_PROJECT_ROOT)
env["BAGO_HOME"] = str(BAGO_HOME)

# Delegar al BAGO central
raise SystemExit(subprocess.call(
    [sys.executable, str(BAGO_HOME / "bago")] + sys.argv[1:],
    env=env
))
'''


def scaffold_project(target: Path, project_name: str | None = None) -> int:
    """Inicializa la estructura BAGO en target_dir. Devuelve 0=ok, 1=error."""
    target = target.resolve()
    name = project_name or target.name

    if not target.exists():
        print(f"  ❌ El directorio no existe: {target}")
        return 1

    bago_dir = target / ".bago"
    state_dir = bago_dir / "state"
    config_dir = bago_dir / "config"
    docs_dir = bago_dir / "docs"

    # Subdirectorios de state
    for sub in ["sessions", "changes", "sprints", "evidences", "schema"]:
        (state_dir / sub).mkdir(parents=True, exist_ok=True)

    config_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)

    # global_state.json
    gs_path = state_dir / "global_state.json"
    if not gs_path.exists():
        gs_path.write_text(
            json.dumps(_make_initial_global_state(name), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"  ✅ {gs_path.relative_to(target)}")
    else:
        print(f"  ⚠️  {gs_path.relative_to(target)} ya existe — no sobreescrito")

    # pack.json (config)
    pack_path = config_dir / "pack.json"
    if not pack_path.exists():
        pack_path.write_text(
            json.dumps(_make_project_pack_json(name, target), indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"  ✅ {pack_path.relative_to(target)}")
    else:
        print(f"  ⚠️  {pack_path.relative_to(target)} ya existe — no sobreescrito")

    # launcher bago script
    launcher_path = target / "bago"
    if not launcher_path.exists():
        launcher_path.write_text(_make_launcher_script(bago_dir), encoding="utf-8")
        launcher_path.chmod(0o755)
        print(f"  ✅ {launcher_path.relative_to(target)} (launcher)")
    else:
        print(f"  ⚠️  {launcher_path.relative_to(target)} ya existe — no sobreescrito")

    # AGENT_START.md mínimo para el proyecto
    agent_start = bago_dir / "AGENT_START.md"
    if not agent_start.exists():
        agent_start.write_text(
            f"# BAGO — {name}\n\n"
            f"Proyecto inicializado con `bago init` el {_now()[:10]}.\n\n"
            f"## BAGO_HOME\n`{BAGO_HOME}`\n\n"
            f"## Estado local\n`.bago/state/` — sesiones, cambios, sprints de este proyecto.\n\n"
            f"## Primeros pasos\n"
            f"```\n./bago health   # ver estado\n"
            f"./bago session  # abrir sesión W7\n"
            f"./bago ideas    # ver ideas priorizadas\n```\n",
            encoding="utf-8"
        )
        print(f"  ✅ .bago/AGENT_START.md")

    # Registrar el proyecto en BAGO_HOME's global state (linked projects)
    _register_project(target, name)

    print()
    print(f"🎉 Proyecto '{name}' inicializado en {target}")
    print(f"   BAGO_HOME  : {BAGO_HOME}")
    print(f"   State local: {state_dir}")
    print()
    print("   Próximos pasos:")
    print(f"     cd {target}")
    print("     ./bago health")
    print("     ./bago session")
    return 0


def _register_project(project_path: Path, name: str) -> None:
    """Registra el proyecto en BAGO_HOME para tracking de proyectos."""
    registry_path = BAGO_HOME / ".bago" / "state" / "linked_projects.json"
    try:
        registry = json.loads(registry_path.read_text(encoding="utf-8")) if registry_path.exists() else {}
        registry[str(project_path)] = {
            "name": name,
            "registered_at": _now(),
            "state_dir": str(project_path / ".bago" / "state")
        }
        registry_path.write_text(json.dumps(registry, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"  ⚠️  No se pudo registrar en linked_projects: {e}")


def main():
    p = argparse.ArgumentParser(
        description="bago init — inicializa un proyecto con BAGO",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  bago init .                    # inicializar directorio actual
  bago init /path/to/my-project  # directorio específico
  bago init ~/projects/foo --name "Mi Proyecto Foo"
"""
    )
    p.add_argument("path", nargs="?", default=".", help="Ruta del proyecto (default: directorio actual)")
    p.add_argument("--name", default=None, help="Nombre del proyecto (default: nombre del directorio)")
    p.add_argument("--test", action="store_true", help="Ejecutar tests self-check")
    args = p.parse_args()

    if args.test:
        _run_tests()
        return

    target = Path(args.path).resolve()
    raise SystemExit(scaffold_project(target, args.name))


def _run_tests():
    """Tests self-check del scaffolder."""
    import tempfile
    from bago_utils import print_ok, print_fail, finish_tests, reset_test_state
    reset_test_state()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "test_proj"
        tmp_path.mkdir()

        rc = scaffold_project(tmp_path, "TestProj")
        if rc == 0:
            print_ok("bago_init:scaffold_ok")
        else:
            print_fail("bago_init:scaffold_ok", "scaffold returned non-zero")

        launcher = tmp_path / "bago"
        if launcher.exists() and launcher.stat().st_mode & 0o100:
            print_ok("bago_init:launcher_executable")
        else:
            print_fail("bago_init:launcher_executable", "launcher missing or not executable")

        gs = tmp_path / ".bago" / "state" / "global_state.json"
        if gs.exists():
            d = json.loads(gs.read_text())
            if d.get("project_name") == "TestProj" and d.get("changes") == 0:
                print_ok("bago_init:global_state_schema")
            else:
                print_fail("bago_init:global_state_schema", f"unexpected: {d}")
        else:
            print_fail("bago_init:global_state_schema", "global_state.json not found")

        pack = tmp_path / ".bago" / "config" / "pack.json"
        if pack.exists() and "bago_home" in json.loads(pack.read_text()):
            print_ok("bago_init:pack_json_bago_home")
        else:
            print_fail("bago_init:pack_json_bago_home", "pack.json missing or no bago_home field")

        state_subdirs = ["sessions", "changes", "sprints", "evidences", "schema"]
        all_ok = all((tmp_path / ".bago" / "state" / s).is_dir() for s in state_subdirs)
        if all_ok:
            print_ok("bago_init:state_subdirs")
        else:
            print_fail("bago_init:state_subdirs", "some state subdirs missing")

    raise SystemExit(finish_tests(5))


if __name__ == "__main__":
    main()
