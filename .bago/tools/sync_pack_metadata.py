#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
sync_pack_metadata.py — Regenera TREE.txt y CHECKSUMS.sha256.

Uso:
  python3 .bago/tools/sync_pack_metadata.py
  bago sync
"""

from pathlib import Path
import hashlib

root = Path(__file__).resolve().parents[1]

tree_file = root / "TREE.txt"
checks_file = root / "CHECKSUMS.sha256"

# Regenerar TREE.txt
real_paths = sorted(
    str(p.relative_to(root)).replace("\\", "/") + ("/" if p.is_dir() else "")
    for p in root.rglob("*")
)
new_tree = "\n".join(real_paths)
old_tree = tree_file.read_text(encoding="utf-8").rstrip("\n") if tree_file.exists() else ""
if new_tree != old_tree:
    tree_file.write_text(new_tree, encoding="utf-8")
    print("TREE.txt regenerado")
else:
    print("TREE.txt sin cambios")

EXCLUDED_FROM_CHECKSUMS = {
    "CHECKSUMS.sha256",
    "state/repo_context.json",  # volatile runtime file — changes on every bago invocation
}

# Regenerar CHECKSUMS.sha256
checksum_lines = []
for p in sorted(root.rglob("*")):
    if p.is_dir():
        continue
    rel = str(p.relative_to(root)).replace("\\", "/")
    if rel in EXCLUDED_FROM_CHECKSUMS:
        continue
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    checksum_lines.append(f"{digest}  {rel}")
new_checksums = "\n".join(checksum_lines)
old_checksums = checks_file.read_text(encoding="utf-8").rstrip("\n") if checks_file.exists() else ""
if new_checksums != old_checksums:
    checks_file.write_text(new_checksums, encoding="utf-8")
    print("CHECKSUMS.sha256 regenerado")
else:
    print("CHECKSUMS.sha256 sin cambios")
