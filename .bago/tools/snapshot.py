#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
snapshot.py — Exporta el estado de BAGO a un archivo ZIP de respaldo.

Captura: .bago/state/, .bago/ideas_catalog.json, .bago/tools/*.py

Uso:
    python3 .bago/tools/snapshot.py              # crea snapshot ahora
    python3 .bago/tools/snapshot.py --list       # lista snapshots existentes
    python3 .bago/tools/snapshot.py --out DIR    # directorio destino
    python3 .bago/tools/snapshot.py --verify N   # verifica snapshot N (más reciente)

Snapshots guardados en: .bago/snapshots/
Formato: bago_snapshot_YYYYMMDD_HHMMSS.zip
Códigos de salida: 0 = OK, 1 = error
"""
from __future__ import annotations

import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT        = Path(__file__).resolve().parents[2]
BAGO_DIR    = ROOT / ".bago"
STATE_DIR   = BAGO_DIR / "state"
SNAP_DIR    = BAGO_DIR / "snapshots"


def GREEN(s: str)  -> str: return f"\033[32m{s}\033[0m"
def RED(s: str)    -> str: return f"\033[31m{s}\033[0m"
def YELLOW(s: str) -> str: return f"\033[33m{s}\033[0m"
def DIM(s: str)    -> str: return f"\033[2m{s}\033[0m"
def BOLD(s: str)   -> str: return f"\033[1m{s}\033[0m"
def CYAN(s: str)   -> str: return f"\033[36m{s}\033[0m"


def _collect_files() -> list[tuple[Path, str]]:
    """Return list of (absolute_path, archive_name) to include in snapshot."""
    files: list[tuple[Path, str]] = []

    # Everything in .bago/state/
    if STATE_DIR.exists():
        for f in sorted(STATE_DIR.rglob("*")):
            if f.is_file():
                arc_name = f.relative_to(BAGO_DIR.parent).as_posix()
                files.append((f, arc_name))

    # ideas_catalog.json
    catalog = BAGO_DIR / "ideas_catalog.json"
    if catalog.exists():
        files.append((catalog, catalog.relative_to(BAGO_DIR.parent).as_posix()))

    # All Python tools
    tools_dir = BAGO_DIR / "tools"
    if tools_dir.exists():
        for f in sorted(tools_dir.glob("*.py")):
            arc_name = f.relative_to(BAGO_DIR.parent).as_posix()
            files.append((f, arc_name))

    return files


def _create_snapshot(out_dir: Path) -> Path | None:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts    = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    name  = f"bago_snapshot_{ts}.zip"
    dest  = out_dir / name
    files = _collect_files()

    try:
        with zipfile.ZipFile(dest, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Write manifest
            manifest = {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "files": [arc for _, arc in files],
                "root": str(ROOT),
            }
            zf.writestr(".bago_manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False))
            for abs_path, arc_name in files:
                try:
                    zf.write(abs_path, arc_name)
                except (PermissionError, OSError):
                    pass  # Skip locked files (e.g. .db WAL)
        return dest
    except Exception as e:
        print(f"  {RED('❌')} Error al crear snapshot: {e}")
        return None


def _list_snapshots(snap_dir: Path) -> list[Path]:
    if not snap_dir.exists():
        return []
    return sorted(snap_dir.glob("bago_snapshot_*.zip"), reverse=True)


def _format_size(path: Path) -> str:
    size = path.stat().st_size
    if size < 1024:
        return f"{size}B"
    elif size < 1024 * 1024:
        return f"{size/1024:.1f}KB"
    else:
        return f"{size/1024/1024:.1f}MB"


def main() -> int:
    args = sys.argv[1:]
    do_list  = "--list" in args or "-l" in args
    verify   = "--verify" in args

    out_dir = SNAP_DIR
    if "--out" in args:
        idx = args.index("--out")
        if idx + 1 < len(args):
            out_dir = Path(args[idx + 1])

    print()
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  BAGO · Snapshot                                            │")
    print("  └─────────────────────────────────────────────────────────────┘")

    if do_list:
        snaps = _list_snapshots(SNAP_DIR)
        if not snaps:
            print(f"\n  {YELLOW('⚠')} No hay snapshots en {SNAP_DIR}\n")
            return 0
        print()
        for i, snap in enumerate(snaps):
            label = GREEN("← último") if i == 0 else ""
            ts_raw = snap.stem.replace("bago_snapshot_", "")
            try:
                ts = datetime.strptime(ts_raw, "%Y%m%d_%H%M%S")
                ts_str = ts.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                ts_str = ts_raw
            size = _format_size(snap)
            print(f"  {snap.name}  {DIM(size):<8}  {DIM(ts_str)}  {label}")
        print()
        return 0

    if verify:
        snaps = _list_snapshots(SNAP_DIR)
        if not snaps:
            print(f"\n  {YELLOW('⚠')} No hay snapshots para verificar.\n")
            return 1
        snap = snaps[0]
        print(f"\n  Verificando: {snap.name}")
        with zipfile.ZipFile(snap, "r") as zf:
            bad = zf.testzip()
        if bad is None:
            print(f"  {GREEN('✅ ZIP íntegro')}")
        else:
            print(f"  {RED(f'❌ Archivo dañado: {bad}')}")
            return 1
        print()
        return 0

    # Create snapshot
    print(f"\n  Recopilando archivos...")
    files = _collect_files()
    print(f"  {len(files)} archivos a comprimir")

    dest = _create_snapshot(out_dir)
    if dest is None:
        return 1

    size = _format_size(dest)
    print(f"\n  {GREEN('✅ Snapshot creado')}")
    print(f"  Archivo: {BOLD(dest.name)}")
    print(f"  Tamaño:  {size}")
    print(f"  Ruta:    {DIM(str(dest))}")
    print()
    print(f"  Usa {CYAN('bago snapshot --list')} para ver todos los snapshots")
    print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
