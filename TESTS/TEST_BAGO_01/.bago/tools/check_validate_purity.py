#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_validate_purity.py — Static checker for write-free validation tools.

Scans all tools/validate_*.py files and fails if any contains file-write
operations. Enforces the governance rule:

  validate_* tools must be side-effect free.

Usage:
  python3 .bago/tools/check_validate_purity.py
  (called by CI job: validate-purity-static)
"""

import re
import sys
from pathlib import Path

TOOLS = Path(__file__).resolve().parent

FORBIDDEN = [
    (r"\.write_text\s*\(",       "write_text()"),
    (r"\.write_bytes\s*\(",      "write_bytes()"),
    (r"open\s*\([^)]*[\"'](w|wb|a|ab)[\"'][^)]*\)", "open() with write mode"),
    (r"\bjson\.dump\s*\(",       "json.dump() — writes to file handle"),
    (r"\.unlink\s*\(",           ".unlink()"),
    (r"\.mkdir\s*\(",            ".mkdir()"),
    (r"\bshutil\.",              "shutil usage"),
    (r"\bos\.makedirs\s*\(",     "os.makedirs()"),
    (r"\bos\.remove\s*\(",       "os.remove()"),
    (r"\bos\.rename\s*\(",       "os.rename()"),
]
COMPILED = [(re.compile(pat), label) for pat, label in FORBIDDEN]

targets = sorted(TOOLS.glob("validate_*.py"))
if not targets:
    print("WARN: no validate_*.py files found")
    sys.exit(0)

violations = []
for path in targets:
    lines = path.read_text(encoding="utf-8").splitlines()
    for lineno, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        for pattern, label in COMPILED:
            if pattern.search(line):
                violations.append(f"  {path.name}:{lineno}  [{label}]  {stripped}")

if violations:
    print("FAIL — write operations found in validate_* tools:")
    for v in violations:
        print(v)
    print()
    print("Rule: validate_* tools must be side-effect free.")
    print("Move any write logic to a sync_* or fix_* tool.")
    sys.exit(1)

checked = ", ".join(p.name for p in targets)
print(f"OK — {len(targets)} validate_* tool(s) are write-free: {checked}")
