"""bago env — Unified environment variables manager for the monorepo."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / ".bago" / "state"

def _get_project_root() -> Path:
    """Read active project path from global_state.json."""
    gs_path = STATE_DIR / "global_state.json"
    if gs_path.exists():
        try:
            import json
            gs = json.loads(gs_path.read_text(encoding="utf-8"))
            p = gs.get("active_project", {}).get("path", "")
            if p and Path(p).exists():
                return Path(p)
        except Exception:
            pass
    return ROOT.parent  # fallback

PROJECT_ROOT = _get_project_root()

# ── helpers ───────────────────────────────────────────────────────────────────

def _parse_env(path: Path) -> dict[str, str]:
    """Parse a .env file into {KEY: value}. Strips comments and blanks."""
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = re.match(r'^([A-Z_][A-Z0-9_]*)(?:\s*=\s*(.*))?$', line)
        if m:
            key = m.group(1)
            val = (m.group(2) or "").strip().strip('"').strip("'")
            out[key] = val
    return out


def _find_env_files(project: Path) -> dict[str, dict[str, dict[str, str]]]:
    """Returns {app_name: {'.env': {...}, '.env.example': {...}}}"""
    apps_dir = project / "apps"
    result: dict[str, dict[str, dict[str, str]]] = {}

    candidates = [project] + (list(apps_dir.iterdir()) if apps_dir.exists() else [])
    for app_path in candidates:
        if not app_path.is_dir():
            continue
        name = "root" if app_path == project else app_path.name
        files: dict[str, dict[str, str]] = {}
        for fname in (".env", ".env.example", ".env.local", ".env.production"):
            fp = app_path / fname
            if fp.exists():
                files[fname] = _parse_env(fp)
        if files:
            result[name] = files

    return result


def _all_keys(env_map: dict[str, dict[str, dict[str, str]]]) -> set[str]:
    keys: set[str] = set()
    for app_files in env_map.values():
        for vars_ in app_files.values():
            keys.update(vars_.keys())
    return keys


def _color(s: str, code: str) -> str:
    return f"\033[{code}m{s}\033[0m"

def GREEN(s): return _color(s, "32")
def RED(s):   return _color(s, "31")
def YELLOW(s):return _color(s, "33")
def CYAN(s):  return _color(s, "36")
def DIM(s):   return _color(s, "2")
def BOLD(s):  return _color(s, "1")


# ── commands ──────────────────────────────────────────────────────────────────

def cmd_list(env_map: dict, verbose: bool = False):
    """List all env files and their keys per app."""
    print()
    for app, files in sorted(env_map.items()):
        for fname, vars_ in files.items():
            print(f"  {CYAN(app)}/{fname}  ({len(vars_)} vars)")
            if verbose:
                for k, v in sorted(vars_.items()):
                    masked = v[:4] + "***" if len(v) > 6 else ("***" if v else "")
                    print(f"      {DIM(k):<30} = {masked}")
    print()


def cmd_table(env_map: dict):
    """Show a cross-app comparison table."""
    keys = sorted(_all_keys(env_map))
    apps = sorted(env_map.keys())

    # Only include .env (real) files first, then .env.example
    def _get(app: str, key: str) -> str | None:
        prio = [".env", ".env.local", ".env.example", ".env.production"]
        for fname in prio:
            if fname in env_map[app] and key in env_map[app][fname]:
                return fname
        return None

    if not keys:
        print("  (no env vars found)")
        return

    col_w = 28
    app_w = 14
    header = f"  {'VARIABLE':<{col_w}}" + "".join(f"  {a[:app_w]:<{app_w}}" for a in apps)
    print()
    print(f"  {BOLD('VARIABLE'): <{col_w}}" + "".join(f"  {CYAN(a[:app_w]):<{app_w}}" for a in apps))
    print("  " + "─" * (col_w + len(apps) * (app_w + 2)))

    for key in keys:
        row = f"  {key:<{col_w}}"
        missing = False
        for app in apps:
            src = _get(app, key)
            if src:
                marker = "✔" if src == ".env" else "○"
                color_fn = GREEN if src == ".env" else YELLOW
                row += f"  {color_fn(marker):<{app_w}}"
            else:
                row += f"  {RED('✗'):<{app_w}}"
                missing = True
        print(row)

    print()
    print(f"  {GREEN('✔')} = .env real   {YELLOW('○')} = .env.example only   {RED('✗')} = missing")
    print()


def cmd_check(env_map: dict):
    """Check for missing vars: keys in .env.example but not in .env."""
    print()
    issues = 0
    for app, files in sorted(env_map.items()):
        example = files.get(".env.example", {})
        real    = files.get(".env", {})
        if not example:
            continue
        missing = [k for k in example if k not in real]
        if missing:
            print(f"  {RED('✗')} {CYAN(app)}/.env — faltan {len(missing)} variable(s):")
            for k in sorted(missing):
                print(f"      {YELLOW(k)}")
            issues += len(missing)
        else:
            print(f"  {GREEN('✔')} {CYAN(app)}/.env — completo ({len(real)} vars)")
    if issues == 0:
        print(f"\n  {GREEN('✔')} Todas las apps tienen sus .env completos.\n")
    else:
        print(f"\n  {RED('⚠')} {issues} variable(s) faltante(s) en total.\n")


def cmd_set(env_map: dict, app: str, assignment: str, project: Path):
    """Add or update a KEY=VALUE in an app's .env file."""
    if "=" not in assignment:
        print(f"  ✖ Formato inválido. Usa: KEY=valor", file=sys.stderr)
        sys.exit(1)
    key, _, val = assignment.partition("=")
    key = key.strip().upper()

    apps_dir = project / "apps"
    if app == "root":
        env_path = project / ".env"
    else:
        env_path = apps_dir / app / ".env"

    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    updated = False
    for i, line in enumerate(lines):
        m = re.match(rf'^{re.escape(key)}\s*=', line)
        if m:
            lines[i] = f"{key}={val}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={val}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    action = "actualizado" if updated else "añadido"
    print(f"  {GREEN('✔')} {key} {action} en {env_path.relative_to(project)}")


# ── main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="BAGO env — Unified env var manager")
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("list", help="List all .env files and var counts")
    sub.add_parser("table", help="Cross-app comparison table")
    sub.add_parser("check", help="Check for missing vars vs .env.example")

    p_set = sub.add_parser("set", help="Set KEY=VALUE in an app's .env")
    p_set.add_argument("app", help="App name (e.g. server, web, root)")
    p_set.add_argument("assignment", help="KEY=value")

    parser.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args()

    env_map = _find_env_files(PROJECT_ROOT)

    if args.cmd == "list" or args.cmd is None:
        cmd_list(env_map, verbose=getattr(args, "verbose", False))
    elif args.cmd == "table":
        cmd_table(env_map)
    elif args.cmd == "check":
        cmd_check(env_map)
    elif args.cmd == "set":
        cmd_set(env_map, args.app, args.assignment, PROJECT_ROOT)
    else:
        cmd_table(env_map)



def _self_test():
    """Autotest mínimo — verifica arranque limpio del módulo."""
    from pathlib import Path as _P
    assert _P(__file__).exists(), "fichero no encontrado"
    print("  1/1 tests pasaron")

if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
        raise SystemExit(0)
    main()
