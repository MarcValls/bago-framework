#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
STATE_PATH = ROOT / ".bago/state/repo_context.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def detect_repo_root() -> Path:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        return Path(result.stdout.strip()).resolve()
    except Exception:
        return ROOT.resolve()


def repo_fingerprint(repo_root: Path) -> str:
    marker = [
        str(repo_root),
        str(ROOT.resolve()),
    ]

    top_entries = sorted(
        p.name for p in repo_root.iterdir() if p.name != ".bago"
    )
    marker.extend(top_entries[:200])
    payload = "\n".join(marker).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def detect_working_mode(repo_root: Path) -> str:
    """Return 'self' if BAGO is operating in its own host directory (no external project),
    or 'external' if it is being used as a tool for a different project."""
    return "self" if repo_root.resolve() == ROOT.resolve() else "external"


def current_context() -> dict:
    repo_root = detect_repo_root()
    return {
        "repo_root": str(repo_root),
        "bago_host_root": str(ROOT.resolve()),
        "repo_fingerprint": repo_fingerprint(repo_root),
        "working_mode": detect_working_mode(repo_root),
        "recorded_at": now_iso(),
    }


def load_previous() -> dict | None:
    if not STATE_PATH.exists():
        return None
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_context(ctx: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Preserve extra metadata fields that may have been added manually
    existing = {}
    if STATE_PATH.exists():
        try:
            existing = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    preserved_keys = {"role", "note"}
    for key in preserved_keys:
        if key in existing:
            ctx[key] = existing[key]
    STATE_PATH.write_text(
        json.dumps(ctx, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def compare_context(previous: dict | None, current: dict) -> str:
    if previous is None:
        return "new"
    if (
        previous.get("repo_root") == current.get("repo_root")
        and previous.get("repo_fingerprint") == current.get("repo_fingerprint")
    ):
        return "match"
    return "mismatch"


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Detecta si BAGO está ejecutándose en el mismo contexto de repo."
    )
    parser.add_argument("mode", choices=["check", "sync"], help="check=verifica, sync=sincroniza")
    args = parser.parse_args(argv[1:])

    prev = load_previous()
    cur = current_context()
    status = compare_context(prev, cur)

    if args.mode == "sync":
        save_context(cur)
        print(json.dumps({"status": "synced", "context": cur}, indent=2, ensure_ascii=False))
        return 0

    print(
        json.dumps(
            {
                "status": status,
                "previous": prev,
                "current": cur,
            },
            indent=2,
            ensure_ascii=False,
        )
    )
    if status == "match":
        return 0
    # new or mismatch: require repo-first bootstrap
    return 3


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
