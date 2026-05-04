"""bago backup — Create and manage project state backups."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / ".bago" / "state"
BACKUP_DIR = ROOT / ".bago" / "backups"


def _get_project_root() -> Path:
    gs_path = STATE_DIR / "global_state.json"
    if gs_path.exists():
        try:
            gs = json.loads(gs_path.read_text(encoding="utf-8"))
            p = gs.get("active_project", {}).get("path", "")
            if p and Path(p).exists():
                return Path(p)
        except Exception:
            pass
    return ROOT.parent


PROJECT_ROOT = _get_project_root()

def GREEN(s):  return f"\033[32m{s}\033[0m"
def RED(s):    return f"\033[31m{s}\033[0m"
def CYAN(s):   return f"\033[36m{s}\033[0m"
def YELLOW(s): return f"\033[33m{s}\033[0m"
def DIM(s):    return f"\033[2m{s}\033[0m"
def BOLD(s):   return f"\033[1m{s}\033[0m"


def _add_dir(zf: zipfile.ZipFile, src: Path, arcname: str):
    """Recursively add directory to zip."""
    for f in src.rglob("*"):
        if f.is_file() and "node_modules" not in f.parts:
            zf.write(f, arcname + "/" + str(f.relative_to(src)))


def _add_file(zf: zipfile.ZipFile, src: Path, arcname: str):
    if src.exists():
        zf.write(src, arcname)


def cmd_create(tag: str | None, include_project: bool):
    """Create a new backup ZIP."""
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    label = f"_{tag}" if tag else ""
    fname = f"bago_backup_{ts}{label}.zip"
    out = BACKUP_DIR / fname

    print(f"\n  🗜  Creando backup: {fname}\n")

    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Always include BAGO state
        if STATE_DIR.exists():
            _add_dir(zf, STATE_DIR, "bago_state")
            print(f"  {GREEN('✔')} bago/state/")

        # Snapshots
        snap_dir = ROOT / ".bago" / "snapshots"
        if snap_dir.exists():
            _add_dir(zf, snap_dir, "snapshots")
            print(f"  {GREEN('✔')} bago/snapshots/")

        # Project config files
        config_files = [
            PROJECT_ROOT / "package.json",
            PROJECT_ROOT / "pnpm-workspace.yaml",
            PROJECT_ROOT / "tsconfig.json",
            PROJECT_ROOT / ".gitignore",
        ]
        for f in config_files:
            if f.exists():
                _add_file(zf, f, "project/" + f.name)
        print(f"  {GREEN('✔')} Archivos de configuración del proyecto")

        # .env files (if include_project)
        if include_project:
            for env in PROJECT_ROOT.rglob(".env"):
                if "node_modules" not in env.parts:
                    rel = env.relative_to(PROJECT_ROOT)
                    _add_file(zf, env, "project/" + str(rel))
            for env in PROJECT_ROOT.rglob(".env.example"):
                if "node_modules" not in env.parts:
                    rel = env.relative_to(PROJECT_ROOT)
                    _add_file(zf, env, "project/" + str(rel))
            print(f"  {GREEN('✔')} Archivos .env")

    size_kb = out.stat().st_size // 1024
    print(f"\n  {GREEN('✅')} Backup creado: {BOLD(str(out))}")
    print(f"  Tamaño: {size_kb} KB\n")


def cmd_list():
    """List existing backups."""
    if not BACKUP_DIR.exists():
        print("\n  (no hay backups todavía)\n")
        return

    backups = sorted(BACKUP_DIR.glob("*.zip"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not backups:
        print("\n  (no hay backups todavía)\n")
        return

    print(f"\n  {BOLD('BACKUP'):<45}  {'TAMAÑO':>8}  FECHA")
    print("  " + "─" * 75)
    for i, f in enumerate(backups, 1):
        sz = f.stat().st_size // 1024
        mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"  {i:>3}.  {CYAN(f.name):<45}  {sz:>5} KB  {DIM(mtime)}")
    print()


def cmd_restore(index: int):
    """Restore BAGO state from a backup."""
    backups = sorted(BACKUP_DIR.glob("*.zip"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not backups:
        print("  ✖ No hay backups disponibles.", file=sys.stderr)
        sys.exit(1)
    if index < 1 or index > len(backups):
        print(f"  ✖ Índice inválido. Rango: 1-{len(backups)}", file=sys.stderr)
        sys.exit(1)

    backup = backups[index - 1]
    print(f"\n  Restaurando desde: {CYAN(backup.name)}")
    print(f"  {YELLOW('⚠')} Esto sobreescribirá .bago/state/")
    confirm = input("  ¿Continuar? [s/N] ").strip().lower()
    if confirm != "s":
        print("  Cancelado.")
        return

    with zipfile.ZipFile(backup, "r") as zf:
        members = [m for m in zf.namelist() if m.startswith("bago_state/")]
        for m in members:
            rel = m[len("bago_state/"):]
            if not rel:
                continue
            dest = STATE_DIR / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(m))

    print(f"  {GREEN('✅')} Estado BAGO restaurado desde {backup.name}\n")


def main():
    parser = argparse.ArgumentParser(description="BAGO backup — Project state backups")
    sub = parser.add_subparsers(dest="cmd")

    p_create = sub.add_parser("create", help="Create new backup")
    p_create.add_argument("--tag", "-t", help="Optional label for the backup file")
    p_create.add_argument("--include-env", action="store_true",
                          help="Include .env files in backup")

    sub.add_parser("list", help="List existing backups")

    p_restore = sub.add_parser("restore", help="Restore BAGO state from backup")
    p_restore.add_argument("index", type=int, help="Backup index from list")

    args = parser.parse_args()

    if args.cmd == "create" or args.cmd is None:
        tag = getattr(args, "tag", None)
        include_env = getattr(args, "include_env", False)
        cmd_create(tag, include_env)
    elif args.cmd == "list":
        cmd_list()
    elif args.cmd == "restore":
        cmd_restore(args.index)
    else:
        cmd_create(None, False)


if __name__ == "__main__":
    main()
