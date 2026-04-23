#!/usr/bin/env python3
"""
bago diff — muestra qué ha cambiado en state/ desde el último snapshot o validate.

Compara el estado actual del directorio state/ con el último snapshot disponible
(o con un snapshot específico) y muestra archivos: añadidos, eliminados, modificados.

Uso:
    bago diff              → diff vs snapshot más reciente
    bago diff --snap ID    → diff vs snapshot específico
    bago diff --since DATE → solo archivos modificados desde esa fecha (YYYY-MM-DD)
    bago diff --json       → output JSON
    bago diff --test       → tests integrados
"""

import argparse
import json
import sys
import zipfile
import hashlib
import datetime
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent
STATE_DIR = BAGO_ROOT / "state"
SNAPSHOT_DIR = STATE_DIR / "snapshots"


def _file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _get_latest_snapshot() -> Path | None:
    if not SNAPSHOT_DIR.exists():
        return None
    snaps = sorted(SNAPSHOT_DIR.glob("SNAP-*.zip"))
    return snaps[-1] if snaps else None


def _snap_file_hashes(zip_path: Path) -> dict:
    """Returns {arcname: md5hex} for all state/ files in the zip."""
    hashes = {}
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if info.filename.startswith("state/") and not info.is_dir():
                data = zf.read(info.filename)
                hashes[info.filename] = hashlib.md5(data).hexdigest()
    return hashes


def _current_file_hashes() -> dict:
    """Returns {rel_path_str: md5hex} for all files in state/."""
    hashes = {}
    for f in STATE_DIR.rglob("*"):
        if f.is_file():
            rel = str(f.relative_to(BAGO_ROOT))
            hashes[rel] = _file_hash(f)
    return hashes


def _classify(snap_hashes: dict, curr_hashes: dict) -> tuple:
    added = []
    removed = []
    modified = []
    snap_keys = set(snap_hashes)
    curr_keys = set(curr_hashes)

    for k in sorted(curr_keys - snap_keys):
        added.append(k)
    for k in sorted(snap_keys - curr_keys):
        removed.append(k)
    for k in sorted(snap_keys & curr_keys):
        if snap_hashes[k] != curr_hashes[k]:
            modified.append(k)

    return added, removed, modified


def cmd_diff(args):
    # Resolve snapshot
    if args.snap:
        zip_path = SNAPSHOT_DIR / f"{args.snap}.zip"
        if not zip_path.exists():
            print(f"  ERROR: snapshot no encontrado: {zip_path}")
            raise SystemExit(1)
    else:
        zip_path = _get_latest_snapshot()
        if zip_path is None:
            print("  ERROR: no hay snapshots. Crea uno con: bago snapshot")
            raise SystemExit(1)

    snap_id = zip_path.stem

    # Collect hashes
    snap_hashes = _snap_file_hashes(zip_path)
    curr_hashes = _current_file_hashes()

    added, removed, modified = _classify(snap_hashes, curr_hashes)

    # Apply --since filter
    since = None
    if args.since:
        try:
            since = datetime.datetime.fromisoformat(args.since)
        except ValueError:
            print(f"  ERROR: formato de fecha inválido: {args.since} (usar YYYY-MM-DD)")
            raise SystemExit(1)
        def was_modified_since(rel_path: str) -> bool:
            p = BAGO_ROOT / rel_path
            if not p.exists():
                return False
            mtime = datetime.datetime.fromtimestamp(p.stat().st_mtime)
            return mtime >= since
        added = [k for k in added if was_modified_since(k)]
        modified = [k for k in modified if was_modified_since(k)]

    if args.json:
        result = {
            "snapshot": snap_id,
            "added": added,
            "removed": removed,
            "modified": modified,
            "counts": {
                "added": len(added),
                "removed": len(removed),
                "modified": len(modified),
                "total": len(added) + len(removed) + len(modified),
            }
        }
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return

    # Human output
    total = len(added) + len(removed) + len(modified)
    print(f"\n  BAGO Diff — vs {snap_id}")
    if since:
        print(f"  Filtro: modificado desde {args.since}")
    print(f"  Cambios: +{len(added)} -{len(removed)} ~{len(modified)}  ({total} total)\n")

    if not total:
        print("  (sin cambios desde el snapshot)\n")
        return

    for f in added:
        print(f"  \033[32m+ {f}\033[0m")
    for f in removed:
        print(f"  \033[31m- {f}\033[0m")
    for f in modified:
        print(f"  \033[33m~ {f}\033[0m")
    print()


def run_tests():
    import tempfile, shutil, os
    print("Ejecutando tests de diff.py...")
    errors = 0

    def ok(name):
        print(f"  OK: {name}")

    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Create a fake mini state
        fake_state = tmp_path / "fake_bago" / "state"
        fake_state.mkdir(parents=True)
        (fake_state / "file_a.json").write_text('{"a": 1}')
        (fake_state / "file_b.json").write_text('{"b": 2}')

        # Create snapshot from fake state
        snap_dir = tmp_path / "snapshots"
        snap_dir.mkdir()
        snap_path = snap_dir / "SNAP-TEST0001.zip"
        with zipfile.ZipFile(snap_path, "w") as zf:
            zf.write(fake_state / "file_a.json", "state/file_a.json")
            zf.write(fake_state / "file_b.json", "state/file_b.json")

        # Test 1: _snap_file_hashes returns correct count
        hashes = _snap_file_hashes(snap_path)
        if len(hashes) == 2:
            ok("diff:snap_hashes")
        else:
            fail("diff:snap_hashes", f"expected 2 got {len(hashes)}")

        # Test 2: no diff when identical
        curr = {k: v for k, v in hashes.items()}
        added, removed, modified = _classify(hashes, curr)
        if added == [] and removed == [] and modified == []:
            ok("diff:no_changes")
        else:
            fail("diff:no_changes", f"got {added} {removed} {modified}")

        # Test 3: detect added file
        curr2 = dict(curr)
        curr2["state/file_c.json"] = "abc123"
        added, removed, modified = _classify(hashes, curr2)
        if "state/file_c.json" in added:
            ok("diff:detect_added")
        else:
            fail("diff:detect_added", str(added))

        # Test 4: detect removed file
        curr3 = {"state/file_a.json": curr["state/file_a.json"]}
        added, removed, modified = _classify(hashes, curr3)
        if "state/file_b.json" in removed:
            ok("diff:detect_removed")
        else:
            fail("diff:detect_removed", str(removed))

        # Test 5: detect modified file
        curr4 = dict(curr)
        curr4["state/file_a.json"] = "different_hash"
        added, removed, modified = _classify(hashes, curr4)
        if "state/file_a.json" in modified:
            ok("diff:detect_modified")
        else:
            fail("diff:detect_modified", str(modified))

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago diff", add_help=False)
    parser.add_argument("--snap", default=None, help="ID del snapshot base")
    parser.add_argument("--since", default=None, help="filtrar por fecha YYYY-MM-DD")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.help:
        parser.print_help()
    else:
        cmd_diff(args)


if __name__ == "__main__":
    main()