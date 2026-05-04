#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
env_diff.py — Compara .env con .env.example por cada app del proyecto.

Detecta claves que faltan en .env (necesarias) o extras (no documentadas).

Uso:
    python3 .bago/tools/env_diff.py             # revisa todas las apps
    python3 .bago/tools/env_diff.py server      # solo server
    python3 .bago/tools/env_diff.py --missing   # solo muestra las faltantes

Códigos de salida: 0 = todo OK, 1 = hay claves faltantes
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT  = Path(__file__).resolve().parents[2]
STATE = ROOT / ".bago" / "state"


def GREEN(s: str)  -> str: return f"\033[32m{s}\033[0m"
def RED(s: str)    -> str: return f"\033[31m{s}\033[0m"
def YELLOW(s: str) -> str: return f"\033[33m{s}\033[0m"
def DIM(s: str)    -> str: return f"\033[2m{s}\033[0m"
def BOLD(s: str)   -> str: return f"\033[1m{s}\033[0m"
def CYAN(s: str)   -> str: return f"\033[36m{s}\033[0m"


def _load_project() -> Path | None:
    gs = STATE / "global_state.json"
    if not gs.exists():
        return None
    try:
        data = json.loads(gs.read_text(encoding="utf-8"))
        p = data.get("active_project", {}).get("path", "")
        return Path(p) if p else None
    except Exception:
        return None


def _parse_env_file(path: Path) -> dict[str, str]:
    """Parse a .env file and return {KEY: VALUE} dict."""
    result: dict[str, str] = {}
    if not path.exists():
        return result
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            result[key.strip()] = value.strip()
        else:
            result[line] = ""
    return result


def _check_app(app_name: str, app_dir: Path, only_missing: bool) -> int:
    """Compare .env vs .env.example for an app. Returns 0 if OK, 1 if missing keys."""
    env_file = app_dir / ".env"
    example_file = app_dir / ".env.example"

    if not example_file.exists():
        print(f"  {YELLOW('⚠')} {BOLD(app_name):<16} sin .env.example")
        return 0

    env_keys     = set(_parse_env_file(env_file).keys())
    example_keys = set(_parse_env_file(example_file).keys())

    missing = example_keys - env_keys   # in .example but not in .env
    extra   = env_keys - example_keys   # in .env but not in .example

    if not missing and not extra:
        print(f"  {GREEN('✅')} {BOLD(app_name):<16} {DIM(str(len(env_keys)))} claves — OK")
        return 0

    has_missing = len(missing) > 0
    status_icon = RED("❌") if has_missing else YELLOW("⚠")
    status_msg  = f"{RED(str(len(missing)) + ' faltantes')}  " if has_missing else ""
    extra_msg   = f"{YELLOW(str(len(extra)) + ' extras')}" if extra else ""
    print(f"  {status_icon} {BOLD(app_name):<16} {status_msg}{extra_msg}")

    if missing:
        print(f"    {RED('Faltan en .env')} (definidas en .env.example):")
        for key in sorted(missing):
            print(f"      {RED('─')} {key}")

    if extra and not only_missing:
        print(f"    {YELLOW('Extra en .env')} (no en .env.example):")
        for key in sorted(extra):
            print(f"      {YELLOW('+')} {DIM(key)}")

    return 1 if has_missing else 0


def main() -> int:
    args = sys.argv[1:]
    only_missing = "--missing" in args
    filters = [a for a in args if not a.startswith("-")]

    project = _load_project()
    if not project:
        print(f"\n  {RED('❌')} No hay proyecto configurado. Ejecuta: bago config\n")
        return 1

    # Scan apps directories for .env.example
    candidates = [
        ("root",     project),
        ("server",   project / "apps" / "server"),
        ("web",      project / "apps" / "web"),
        ("electron", project / "apps" / "electron"),
    ]
    apps = [(name, path) for name, path in candidates if path.exists()]

    if filters:
        apps = [(n, p) for n, p in apps if n in filters]
        if not apps:
            print(f"\n  {RED('❌')} App no encontrada: {', '.join(filters)}\n")
            return 1

    print()
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  BAGO · Env Diff                                            │")
    print("  └─────────────────────────────────────────────────────────────┘")
    print(f"  Proyecto: {DIM(str(project))}")
    print()

    total_issues = 0
    for app_name, app_dir in apps:
        total_issues += _check_app(app_name, app_dir, only_missing)

    print()
    if total_issues == 0:
        print(f"  {GREEN('✅ Todo OK')} — sin claves faltantes")
    else:
        print(f"  {RED(f'❌ {total_issues} app(s) con claves faltantes')}")
    print()

    return 0 if total_issues == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
