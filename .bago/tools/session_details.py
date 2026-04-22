#!/usr/bin/env python3
"""
bago session-stats — estadísticas detalladas de sesiones individuales o del pack.

Uso:
    bago session-stats               → top 10 sesiones por producción
    bago session-stats --id SES-ID   → breakdown completo de una sesión
    bago session-stats --top N       → top N sesiones
    bago session-stats --workflow W  → filtrar por workflow
    bago session-stats --json        → output JSON
    bago session-stats --test        → tests integrados
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict

BAGO_ROOT = Path(__file__).parent.parent
SESSIONS_DIR = BAGO_ROOT / "state" / "sessions"


WORKFLOW_LABEL = {
    "w1_onboarding": "W1 Onboarding",
    "w2_implementacion": "W2 Implement",
    "w3_debug": "W3 Debug",
    "w4_revision": "W4 Review",
    "w5_arquitectura": "W5 Architect",
    "w6_consolidacion": "W6 Consolidate",
    "w7_preflight": "W7 Preflight",
    "w8_exploracion": "W8 Explore",
    "w9_cosecha": "W9 Harvest",
}


def _load_sessions(workflow_filter=None):
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("SES-*.json")):
        try:
            s = json.loads(f.read_text())
            s["_file"] = f.name
            if workflow_filter and s.get("selected_workflow", "") != workflow_filter:
                continue
            sessions.append(s)
        except Exception:
            pass
    return sessions


def _score(s: dict) -> int:
    arts = len(s.get("artifacts", []))
    decs = len(s.get("decisions", []))
    roles = len(s.get("roles_activated", []))
    return arts * 3 + decs * 2 + roles


def _bar(n: int, max_n: int, width: int = 20) -> str:
    if max_n == 0:
        return ""
    filled = int(round(n / max_n * width))
    return "█" * filled + "░" * (width - filled)


def cmd_show_id(sid: str):
    """Detailed breakdown of a single session."""
    sessions = _load_sessions()
    match = [s for s in sessions if s.get("session_id", "") == sid or s["_file"].startswith(sid)]
    if not match:
        print(f"  ERROR: sesión no encontrada: {sid}")
        sys.exit(1)
    s = match[0]

    arts = s.get("artifacts", [])
    decs = s.get("decisions", [])
    roles = s.get("roles_activated", [])
    wf = WORKFLOW_LABEL.get(s.get("selected_workflow", ""), s.get("selected_workflow", "?"))
    score = _score(s)

    print(f"\n  ╔══ Sesión: {s.get('session_id', s['_file'])} ══")
    print(f"  Workflow:  {wf}")
    print(f"  Objetivo:  {str(s.get('user_goal', ''))[:80]}")
    print(f"  Estado:    {s.get('status', '?')}")
    print(f"  Modo BAGO: {s.get('bago_mode', '?')}")
    print(f"  Creada:    {s.get('created_at', '?')[:19]}")
    print(f"  Score:     {score}  (arts×3 + decs×2 + roles)")
    print()

    print(f"  Roles ({len(roles)}):")
    for r in roles:
        print(f"    · {r}")
    if not roles:
        print("    (ninguno)")

    print(f"\n  Artefactos ({len(arts)}):")
    for a in arts:
        print(f"    + {a}")
    if not arts:
        print("    (ninguno)")

    print(f"\n  Decisiones ({len(decs)}):")
    for i, d in enumerate(decs, 1):
        print(f"    {i}. {str(d)[:90]}")
    if not decs:
        print("    (ninguna)")

    bugs = s.get("bugs_found", [])
    if bugs:
        print(f"\n  Bugs encontrados ({len(bugs)}):")
        for b in bugs:
            print(f"    ! {b}")

    summary = s.get("summary", "")
    if summary:
        print(f"\n  Resumen:")
        for line in str(summary).split("\n")[:5]:
            if line.strip():
                print(f"    {line.strip()}")
    print()


def cmd_top(n: int, workflow: str, as_json: bool):
    sessions = _load_sessions(workflow_filter=workflow)
    if not sessions:
        print("  (sin sesiones)")
        return

    scored = sorted(sessions, key=_score, reverse=True)[:n]
    max_score = _score(scored[0]) if scored else 1

    if as_json:
        result = []
        for s in scored:
            result.append({
                "session_id": s.get("session_id", s["_file"]),
                "workflow": s.get("selected_workflow", ""),
                "artifacts": len(s.get("artifacts", [])),
                "decisions": len(s.get("decisions", [])),
                "roles": len(s.get("roles_activated", [])),
                "score": _score(s),
            })
        print(json.dumps(result, indent=2))
        return

    print(f"\n  Top {n} sesiones por producción")
    if workflow:
        print(f"  Filtro: workflow={workflow}")
    print()
    print(f"  {'Sesión':30s} {'WF':5s} {'Arts':5s} {'Decs':5s} {'Score':6s}  Bar")
    print(f"  {'-'*30} {'-'*5} {'-'*5} {'-'*5} {'-'*6}  {'-'*20}")

    for s in scored:
        sid = s.get("session_id", s["_file"])[:30]
        wf = s.get("selected_workflow", "")[-2:].upper() if s.get("selected_workflow") else "?"
        arts = len(s.get("artifacts", []))
        decs = len(s.get("decisions", []))
        sc = _score(s)
        bar = _bar(sc, max_score)
        print(f"  {sid:30s} {wf:5s} {arts:5d} {decs:5d} {sc:6d}  {bar}")

    # Workflow breakdown
    wf_counts = defaultdict(lambda: {"sessions": 0, "arts": 0, "decs": 0})
    for s in sessions:
        w = s.get("selected_workflow", "unknown")
        wf_counts[w]["sessions"] += 1
        wf_counts[w]["arts"] += len(s.get("artifacts", []))
        wf_counts[w]["decs"] += len(s.get("decisions", []))

    print(f"\n  Desglose por workflow ({len(sessions)} sesiones totales):")
    print(f"  {'Workflow':20s} {'Ses':5s} {'Arts':6s} {'Decs':6s}")
    print(f"  {'-'*20} {'-'*5} {'-'*6} {'-'*6}")
    for w, c in sorted(wf_counts.items(), key=lambda x: -x[1]["sessions"]):
        label = WORKFLOW_LABEL.get(w, w)[-20:]
        print(f"  {label:20s} {c['sessions']:5d} {c['arts']:6d} {c['decs']:6d}")
    print()


def run_tests():
    print("Ejecutando tests de session_stats.py...")
    errors = 0

    def ok(name):
        print(f"  OK: {name}")

    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    # Test 1: _score with known values
    fake = {"artifacts": [1, 2], "decisions": [1, 2, 3], "roles_activated": ["x"]}
    s = _score(fake)
    expected = 2*3 + 3*2 + 1  # 13
    if s == expected:
        ok("session_stats:score_calc")
    else:
        fail("session_stats:score_calc", f"expected {expected} got {s}")

    # Test 2: _bar edges
    b = _bar(0, 10)
    if b == "░" * 20:
        ok("session_stats:bar_zero")
    else:
        fail("session_stats:bar_zero", repr(b))

    b2 = _bar(10, 10)
    if b2 == "█" * 20:
        ok("session_stats:bar_full")
    else:
        fail("session_stats:bar_full", repr(b2))

    # Test 3: load_sessions returns list
    sessions = _load_sessions()
    if isinstance(sessions, list) and len(sessions) > 0:
        ok("session_stats:load_sessions")
    else:
        fail("session_stats:load_sessions", f"got {type(sessions)} len={len(sessions)}")

    # Test 4: workflow filter works
    all_sess = _load_sessions()
    if all_sess:
        first_wf = all_sess[0].get("selected_workflow", "")
        if first_wf:
            filtered = _load_sessions(workflow_filter=first_wf)
            all_match = all(s.get("selected_workflow") == first_wf for s in filtered)
            if all_match:
                ok("session_stats:workflow_filter")
            else:
                fail("session_stats:workflow_filter", "non-matching session in filtered list")
        else:
            ok("session_stats:workflow_filter")  # skip if no workflow
    else:
        ok("session_stats:workflow_filter")

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago session-stats", add_help=False)
    parser.add_argument("--id", default=None, help="ID de sesión para breakdown")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--workflow", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.id:
        cmd_show_id(args.id)
    elif args.help:
        parser.print_help()
    else:
        cmd_top(args.top, args.workflow, args.json)


if __name__ == "__main__":
    main()