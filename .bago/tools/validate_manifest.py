#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
import json
import sys

root = Path(__file__).resolve().parents[1]
manifest = root / "pack.json"
state = root / "state/global_state.json"

errors = []

def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

data = load_json(manifest)
gs = load_json(state)

def check_rel(label: str, relpath: str):
    path = root / relpath
    if not path.exists():
        errors.append(f"{label}: missing -> {relpath}")

if data.get("version") != gs.get("bago_version"):
    errors.append(
        f"version mismatch: pack.json={data.get('version')} state={gs.get('bago_version')}"
    )

for section in ("entrypoints", "contracts", "workflows", "governance", "docs", "bootstrap"):
    for key, value in data.get(section, {}).items():
        if isinstance(value, str):
            if value.startswith("../"):
                errors.append(f"{section}.{key}: forbidden relative escape -> {value}")
            else:
                check_rel(f"{section}.{key}", value)

bootstrap_path = root / "core/workflows/workflow_bootstrap_repo_first.md"
if bootstrap_path.exists():
    wf_rel = data.get("workflows", {}).get("repo_bootstrap")
    if wf_rel != "core/workflows/workflow_bootstrap_repo_first.md":
        errors.append("workflows.repo_bootstrap missing or incorrect in pack.json")

# Check: review_role must be a non-empty string
review_role = data.get("review_role")
if not isinstance(review_role, str) or not review_role.strip():
    errors.append("pack.json: review_role must be a non-empty string")

if errors:
    print("KO")
    for e in errors:
        print(e)
    raise SystemExit(1)

print("GO manifest")
