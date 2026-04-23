#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import hashlib
import subprocess
import sys
import re

root = Path(__file__).resolve().parents[1]

def run(script: str):
    result = subprocess.run([sys.executable, str(root / "tools" / script)], capture_output=True, text=True)
    print(result.stdout.strip())
    if result.returncode != 0:
        if result.stderr.strip():
            print(result.stderr.strip())
        raise SystemExit(result.returncode)

run("validate_manifest.py")
run("validate_state.py")

tree = root / "TREE.txt"
checks = root / "CHECKSUMS.sha256"

# ── Auto-regeneración silenciosa de TREE.txt y CHECKSUMS.sha256 ──────────────
# Regenerar TREE.txt
real_paths = sorted(
    str(p.relative_to(root)).replace("\\", "/") + ("/" if p.is_dir() else "")
    for p in root.rglob("*")
)
new_tree = "\n".join(real_paths)
old_tree = tree.read_text(encoding="utf-8").rstrip("\n") if tree.exists() else ""
if new_tree != old_tree:
    tree.write_text(new_tree, encoding="utf-8")
    print("TREE.txt regenerado")

# Regenerar CHECKSUMS.sha256
checksum_lines = []
for p in sorted(root.rglob("*")):
    if p.is_dir():
        continue
    rel = str(p.relative_to(root)).replace("\\", "/")
    if rel == "CHECKSUMS.sha256":
        continue
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    checksum_lines.append(f"{digest}  {rel}")
new_checksums = "\n".join(checksum_lines)
old_checksums = checks.read_text(encoding="utf-8").rstrip("\n") if checks.exists() else ""
if new_checksums != old_checksums:
    checks.write_text(new_checksums, encoding="utf-8")
    print("CHECKSUMS.sha256 regenerado")
# ─────────────────────────────────────────────────────────────────────────────

excluded_prefixes = [
    "docs/migration/",
    "docs/migration/legacy/",
    "state/migrated_changes/",
    "state/migrated_sessions/",
    "docs/V2_PROPUESTA.md",
]
legacy_re = re.compile(r"(?:\b2\.1\.[0-9]+\b|\bV2\.1(?:\.[0-9]+)?\b|\bv2_1\b)", re.IGNORECASE)

for p in sorted(root.rglob("*")):
    if not p.is_file():
        continue
    rel = str(p.relative_to(root)).replace("\\", "/")
    if any(rel.startswith(prefix) for prefix in excluded_prefixes):
        continue
    if p.suffix.lower() not in {".md", ".json", ".txt", ".py"}:
        continue
    text = p.read_text(encoding="utf-8")
    if legacy_re.search(text):
        print("KO")
        print(f"legacy 2.1 reference found outside migration/legacy: {rel}")
        raise SystemExit(1)

role_dir_to_family = {
    "gobierno": "government",
    "produccion": "production",
    "supervision": "supervision",
    "especialistas": "specialist",
}
role_family_re = re.compile(r"^- family:\s*([A-Za-z_]+)\s*$", re.M)

for p in sorted((root / "roles").glob("*/*.md")):
    rel = str(p.relative_to(root)).replace("\\", "/")
    physical_family = role_dir_to_family.get(p.parent.name)
    if not physical_family:
        print("KO")
        print(f"unknown role directory family for {rel}")
        raise SystemExit(1)
    text = p.read_text(encoding="utf-8")
    m = role_family_re.search(text)
    if not m:
        print("KO")
        print(f"role without parseable family: {rel}")
        raise SystemExit(1)
    declared_family = m.group(1).strip()
    if declared_family != physical_family:
        print("KO")
        print(
            f"role family mismatch for {rel}: declared={declared_family} physical={physical_family}"
        )
        raise SystemExit(1)

print("GO pack")
