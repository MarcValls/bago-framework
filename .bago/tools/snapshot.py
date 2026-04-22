#!/usr/bin/env python3
"""
bago snapshot — archivado ZIP point-in-time del estado BAGO

Genera un ZIP que contiene:
- Todo el directorio state/ (sessions, changes, evidences, sprints, metrics...)
- pack.json y AGENT_START.md
- Un índice JSON generado automáticamente con metadatos del snapshot

Uso:
    bago snapshot              → crea snapshot en state/snapshots/
    bago snapshot --out DIR    → crea snapshot en DIR
    bago snapshot --list       → lista snapshots existentes
    bago snapshot --show ID    → muestra índice de un snapshot
    bago snapshot --test       → tests integrados
"""

import argparse
import json
import sys
import zipfile
import datetime
import hashlib
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent
STATE_DIR = BAGO_ROOT / "state"
SNAPSHOT_DIR = STATE_DIR / "snapshots"


def _count_dir(d: Path, ext: str = ".json") -> int:
    if not d.exists():
        return 0
    return sum(1 for f in d.rglob(f"*{ext}") if f.is_file())


def _build_index(zip_file: zipfile.ZipFile, meta: dict) -> dict:
    """Generate snapshot index from zip contents."""
    names = zip_file.namelist()
    index = {
        "snapshot_id": meta["snapshot_id"],
        "created_at": meta["created_at"],
        "pack_id": meta.get("pack_id", ""),
        "bago_version": meta.get("bago_version", ""),
        "summary": {
            "total_files": len(names),
            "sessions": sum(1 for n in names if "/sessions/" in n and n.endswith(".json")),
            "changes": sum(1 for n in names if "/changes/" in n and n.endswith(".json")),
            "evidences": sum(1 for n in names if "/evidences/" in n and n.endswith(".json")),
            "sprints": sum(1 for n in names if "/sprints/" in n and n.endswith(".json")),
        },
        "files": sorted(names),
    }
    return index


def cmd_create(args):
    now = datetime.datetime.now(datetime.timezone.utc)
    ts = now.strftime("%Y%m%d_%H%M%S")
    snap_id = f"SNAP-{ts}"

    out_dir = Path(args.out) if args.out else SNAPSHOT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{snap_id}.zip"

    # Load pack metadata
    pack_path = BAGO_ROOT / "pack.json"
    pack_meta = {}
    if pack_path.exists():
        try:
            pack_meta = json.loads(pack_path.read_text())
        except Exception:
            pass

    gs_path = STATE_DIR / "global_state.json"
    bago_version = ""
    if gs_path.exists():
        try:
            gs = json.loads(gs_path.read_text())
            bago_version = gs.get("bago_version", "")
        except Exception:
            pass

    meta = {
        "snapshot_id": snap_id,
        "created_at": now.isoformat(),
        "pack_id": pack_meta.get("id", ""),
        "bago_version": bago_version,
    }

    files_to_add = []

    # state/ directory
    if STATE_DIR.exists():
        for f in STATE_DIR.rglob("*"):
            if f.is_file():
                rel = f.relative_to(BAGO_ROOT)
                files_to_add.append((f, str(rel)))

    # pack.json + AGENT_START.md
    for name in ["pack.json", "AGENT_START.md"]:
        p = BAGO_ROOT / name
        if p.exists():
            files_to_add.append((p, name))

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for src, arcname in files_to_add:
            zf.write(src, arcname)

        # Build and add index
        index = _build_index(zf, meta)
        zf.writestr("SNAPSHOT_INDEX.json", json.dumps(index, indent=2, ensure_ascii=False))

    # Compute checksum
    sha256 = hashlib.sha256(zip_path.read_bytes()).hexdigest()[:12]
    final_size = zip_path.stat().st_size

    print(f"\n  BAGO Snapshot creado")
    print(f"  ID:      {snap_id}")
    print(f"  Archivo: {zip_path}")
    print(f"  Tamaño:  {final_size / 1024:.1f} KB")
    print(f"  SHA256:  {sha256}...")
    print(f"  Archivos incluidos: {index['summary']['total_files']}")
    print(f"    sesiones:  {index['summary']['sessions']}")
    print(f"    cambios:   {index['summary']['changes']}")
    print(f"    evidencias:{index['summary']['evidences']}")
    print(f"    sprints:   {index['summary']['sprints']}")
    print()

    return snap_id


def cmd_list(args):
    out_dir = Path(args.out) if args.out else SNAPSHOT_DIR
    if not out_dir.exists():
        print("  (sin snapshots)")
        return

    snaps = sorted(out_dir.glob("SNAP-*.zip"))
    if not snaps:
        print("  (sin snapshots)")
        return

    print(f"\n  BAGO Snapshots ({len(snaps)} encontrados)\n")
    print(f"  {'ID':25s} {'Tamaño':10s} {'Fecha':20s}")
    print(f"  {'-'*25} {'-'*10} {'-'*20}")
    for s in snaps:
        size_kb = s.stat().st_size / 1024
        mtime = datetime.datetime.fromtimestamp(s.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        snap_id = s.stem
        print(f"  {snap_id:25s} {size_kb:8.1f} KB  {mtime}")
    print()


def cmd_show(args):
    if not args.id:
        print("  ERROR: indica el ID del snapshot (--show SNAP-YYYYMMDD_HHMMSS)")
        sys.exit(1)

    out_dir = Path(args.out) if args.out else SNAPSHOT_DIR
    zip_path = out_dir / f"{args.id}.zip"
    if not zip_path.exists():
        print(f"  ERROR: snapshot no encontrado: {zip_path}")
        sys.exit(1)

    with zipfile.ZipFile(zip_path, "r") as zf:
        if "SNAPSHOT_INDEX.json" not in zf.namelist():
            print("  ERROR: snapshot no tiene índice")
            sys.exit(1)
        index = json.loads(zf.read("SNAPSHOT_INDEX.json"))

    print(f"\n  Snapshot: {index['snapshot_id']}")
    print(f"  Creado:   {index['created_at']}")
    print(f"  Pack:     {index['pack_id']}  v{index['bago_version']}")
    s = index["summary"]
    print(f"  Archivos: {s['total_files']}  (ses:{s['sessions']} chg:{s['changes']} evd:{s['evidences']} spr:{s['sprints']})")
    print()


def run_tests():
    import tempfile, os
    print("Ejecutando tests de snapshot.py...")
    errors = 0

    def ok(name):
        print(f"  OK: {name}")

    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    with tempfile.TemporaryDirectory() as tmp:
        # Test 1: create snapshot
        class FakeArgs:
            out = tmp
            id = None
        try:
            snap_id = cmd_create(FakeArgs())
            ok("snapshot:create")
        except Exception as e:
            fail("snapshot:create", str(e))
            snap_id = None

        # Test 2: list shows the snapshot
        if snap_id:
            snaps = list(Path(tmp).glob("SNAP-*.zip"))
            if snaps:
                ok("snapshot:list_finds_file")
            else:
                fail("snapshot:list_finds_file", "no zip found")

        # Test 3: index present
        if snap_id:
            zip_path = Path(tmp) / f"{snap_id}.zip"
            if zip_path.exists():
                with zipfile.ZipFile(zip_path) as zf:
                    names = zf.namelist()
                if "SNAPSHOT_INDEX.json" in names:
                    ok("snapshot:index_present")
                else:
                    fail("snapshot:index_present", "SNAPSHOT_INDEX.json missing")

        # Test 4: index has valid structure
        if snap_id:
            zip_path = Path(tmp) / f"{snap_id}.zip"
            if zip_path.exists():
                with zipfile.ZipFile(zip_path) as zf:
                    index = json.loads(zf.read("SNAPSHOT_INDEX.json"))
                required = ["snapshot_id", "created_at", "summary", "files"]
                missing = [k for k in required if k not in index]
                if not missing:
                    ok("snapshot:index_structure")
                else:
                    fail("snapshot:index_structure", f"missing keys: {missing}")

        # Test 5: show command works
        if snap_id:
            class ShowArgs:
                out = tmp
                id = snap_id
            try:
                cmd_show(ShowArgs())
                ok("snapshot:show")
            except Exception as e:
                fail("snapshot:show", str(e))

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago snapshot", add_help=False)
    parser.add_argument("--out", default=None, help="directorio de salida")
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--show", metavar="ID", default=None)
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.list:
        cmd_list(args)
    elif args.show:
        args.id = args.show
        cmd_show(args)
    elif args.help:
        parser.print_help()
    else:
        cmd_create(args)


if __name__ == "__main__":
    main()