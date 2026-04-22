#!/usr/bin/env python3
"""
bago_watch.py — Smart file watcher with delta findings.
Watches .bago/state/ for changes and shows what changed.
Also runs a quick health check after each detected change.

Usage:
  python3 .bago/tools/bago_watch.py              # watch loop
  python3 .bago/tools/bago_watch.py --once       # single snapshot + exit
  python3 .bago/tools/bago_watch.py --interval N # custom interval (seconds, default 5)
  python3 .bago/tools/bago_watch.py --dir PATH   # watch a different directory
"""
import argparse, hashlib, json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

BAGO_ROOT   = Path(__file__).resolve().parent.parent
PROJECT_DIR = BAGO_ROOT.parent
STATE_DIR   = BAGO_ROOT / "state"
TOOLS       = BAGO_ROOT / "tools"

WATCH_DIRS  = [
    STATE_DIR / "changes",
    STATE_DIR / "sessions",
    STATE_DIR / "findings",
    STATE_DIR / "sprints",
]
FINDINGS_DIR = STATE_DIR / "findings"


# ─── snapshot ────────────────────────────────────────────────────────────────

def _snapshot(dirs):
    """Returns {path: sha256} for all JSON files in dirs."""
    snap = {}
    for d in dirs:
        if not d.exists():
            continue
        for f in d.rglob("*.json"):
            try:
                h = hashlib.sha256(f.read_bytes()).hexdigest()[:12]
                snap[str(f)] = h
            except Exception:
                pass
    return snap


def _diff_snapshots(before, after):
    """Returns (added, removed, modified) path sets."""
    added    = set(after)  - set(before)
    removed  = set(before) - set(after)
    modified = {p for p in set(before) & set(after) if before[p] != after[p]}
    return added, removed, modified


# ─── findings delta ──────────────────────────────────────────────────────────

def _load_findings_index(snap_keys):
    """Extract {finding_id: severity} from findings files in the snapshot."""
    index = {}
    for path in snap_keys:
        if "findings" not in path:
            continue
        try:
            data = json.loads(Path(path).read_text())
            items = data if isinstance(data, list) else data.get("findings", [])
            for item in items:
                fid = item.get("id") or item.get("rule") or item.get("message", "")[:40]
                if fid:
                    index[fid] = item.get("severity", "?")
        except Exception:
            pass
    return index


def _findings_delta(before_keys, after_keys):
    """New vs resolved findings between two snapshots."""
    before_idx = _load_findings_index(before_keys)
    after_idx  = _load_findings_index(after_keys)
    new_findings = {k: v for k, v in after_idx.items() if k not in before_idx}
    resolved     = {k: v for k, v in before_idx.items() if k not in after_idx}
    return new_findings, resolved


# ─── health quick check ───────────────────────────────────────────────────────

def _quick_health():
    try:
        sys.path.insert(0, str(TOOLS))
        import health_score as hs
        results = [
            hs.score_integridad(),
            hs.score_disciplina_workflow(),
            hs.score_captura_decisiones(),
            hs.score_estado_stale(),
            hs.score_consistencia_inventario(),
        ]
        total = sum(r[0] for r in results)
        icon  = "🟢" if total >= 90 else ("🟡" if total >= 50 else "🔴")
        return total, icon
    except Exception:
        return -1, "?"


# ─── display ─────────────────────────────────────────────────────────────────

def _ts():
    return datetime.now(timezone.utc).strftime("%H:%M:%S")

def _rel(path):
    try:
        return Path(path).relative_to(PROJECT_DIR).as_posix()
    except Exception:
        return path

def _print_delta(added, removed, modified, new_f, resolved_f, health):
    score, icon = health
    ts = _ts()
    if not (added or removed or modified):
        return  # nothing to print
    print(f"\n[{ts}] Change detected — health {icon} {score}/100")
    for p in sorted(added):
        print(f"  ✅  + {_rel(p)}")
    for p in sorted(removed):
        print(f"  🗑   - {_rel(p)}")
    for p in sorted(modified):
        print(f"  ✏️   ~ {_rel(p)}")
    if new_f:
        sev_icons = {"critical":"🔴","error":"🟠","warning":"🟡","info":"🔵"}
        print(f"  📋 New findings: {len(new_f)}")
        for fid, sev in list(new_f.items())[:5]:
            ico = sev_icons.get(sev, "⚪")
            print(f"       {ico} [{sev}] {fid[:60]}")
    if resolved_f:
        print(f"  ✅ Resolved findings: {len(resolved_f)}")
        for fid in list(resolved_f.keys())[:3]:
            print(f"       ✔  {fid[:60]}")


# ─── main watch loop ──────────────────────────────────────────────────────────

def watch(dirs, interval=5, once=False):
    print(f"🔍 BAGO Watch — monitoring {len(dirs)} directories")
    for d in dirs:
        print(f"   · {_rel(str(d))}")
    print(f"   interval: {interval}s  {'(single run)' if once else '(Ctrl+C to stop)'}")
    print()

    prev = _snapshot(dirs)
    if once:
        score, icon = _quick_health()
        ts = _ts()
        total_files = len(prev)
        total_findings = sum(
            len(json.loads(Path(p).read_text()) if isinstance(json.loads(Path(p).read_text()), list)
                else json.loads(Path(p).read_text()).get("findings", []))
            for p in prev
            if "findings" in p
        )
        print(f"[{ts}] Snapshot: {total_files} files  health {icon} {score}/100")
        if total_findings:
            print(f"  📋 Active findings: {total_findings}")
        return

    print(f"[{_ts()}] Initial snapshot: {len(prev)} files  — watching...")
    try:
        while True:
            time.sleep(interval)
            curr = _snapshot(dirs)
            added, removed, modified = _diff_snapshots(prev, curr)
            if added or removed or modified:
                new_f, resolved_f = _findings_delta(set(prev), set(curr))
                health = _quick_health()
                _print_delta(added, removed, modified, new_f, resolved_f, health)
                prev = curr
    except KeyboardInterrupt:
        print(f"\n[{_ts()}] Watch stopped.")


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="BAGO Watch — smart state file watcher")
    p.add_argument("--once",       action="store_true",  help="Single snapshot report, no loop")
    p.add_argument("--interval",   type=int, default=5,  help="Poll interval in seconds (default: 5)")
    p.add_argument("--dir",        type=str, default=None, help="Extra directory to watch")
    args = p.parse_args()

    dirs = list(WATCH_DIRS)
    if args.dir:
        extra = Path(args.dir).expanduser().resolve()
        if extra.exists():
            dirs.append(extra)
        else:
            print(f"Warning: --dir '{args.dir}' does not exist, ignoring.")

    watch(dirs, interval=args.interval, once=args.once)
