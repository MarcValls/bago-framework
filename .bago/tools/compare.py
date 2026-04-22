#!/usr/bin/env python3
"""
bago compare — comparativa lado a lado entre dos periodos, workflows o roles.

Uso:
    bago compare --wf W2 W9          → compara workflow W2 vs W9
    bago compare --period A B        → periodos como YYYY-MM-DD..YYYY-MM-DD
    bago compare --role R1 R2        → comparar sesiones dominadas por rol R1 vs R2
    bago compare --wf W2 W9 --json  → output JSON
    bago compare --test              → tests integrados
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict
import datetime

BAGO_ROOT = Path(__file__).parent.parent
SESSIONS_DIR = BAGO_ROOT / "state" / "sessions"


def _load_sessions_all():
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("SES-*.json")):
        try:
            s = json.loads(f.read_text())
            s["_file"] = f.name
            sessions.append(s)
        except Exception:
            pass
    return sessions


def _stats(group: list) -> dict:
    if not group:
        return {"sessions": 0, "artifacts": 0, "decisions": 0, "roles": 0,
                "bugs": 0, "arts_per_ses": 0.0, "decs_per_ses": 0.0,
                "workflows": {}, "top_roles": {}}
    total_arts = sum(len(s.get("artifacts", [])) for s in group)
    total_decs = sum(len(s.get("decisions", [])) for s in group)
    total_roles = sum(len(s.get("roles_activated", [])) for s in group)
    total_bugs = sum(len(s.get("bugs_found", [])) for s in group)
    n = len(group)

    wf_count = defaultdict(int)
    for s in group:
        wf_count[s.get("selected_workflow", "?")] += 1

    role_count = defaultdict(int)
    for s in group:
        for r in s.get("roles_activated", []):
            role_count[r] += 1

    return {
        "sessions": n,
        "artifacts": total_arts,
        "decisions": total_decs,
        "roles": total_roles,
        "bugs": total_bugs,
        "arts_per_ses": round(total_arts / n, 1),
        "decs_per_ses": round(total_decs / n, 1),
        "workflows": dict(sorted(wf_count.items(), key=lambda x: -x[1])),
        "top_roles": dict(sorted(role_count.items(), key=lambda x: -x[1])[:5]),
    }


def _delta_icon(a, b) -> str:
    if a == b:
        return "="
    return "▲" if b > a else "▼"


def _render_compare(label_a: str, label_b: str, sa: dict, sb: dict, as_json: bool):
    if as_json:
        print(json.dumps({
            label_a: sa,
            label_b: sb,
        }, indent=2, ensure_ascii=False))
        return

    W = 18
    print(f"\n  Comparativa BAGO: {label_a}  vs  {label_b}\n")

    def row(metric, va, vb, fmt="{}", higher_is_better=True):
        delta = _delta_icon(va, vb)
        if delta != "=":
            delta = ("▲" if (vb > va) == higher_is_better else "▼")
        s_va = fmt.format(va) if not isinstance(va, float) else f"{va:.1f}"
        s_vb = fmt.format(vb) if not isinstance(vb, float) else f"{vb:.1f}"
        print(f"  {metric:20s}  {s_va:>10s}  {s_vb:>10s}  {delta}")

    header = f"  {'Métrica':20s}  {label_a[:10]:>10s}  {label_b[:10]:>10s}  Δ"
    print(header)
    print("  " + "-" * (len(header) - 2))

    row("Sesiones",     sa["sessions"],     sb["sessions"])
    row("Artefactos",   sa["artifacts"],    sb["artifacts"])
    row("Decisiones",   sa["decisions"],    sb["decisions"])
    row("Bugs",         sa["bugs"],         sb["bugs"], higher_is_better=False)
    row("Arts/sesión",  sa["arts_per_ses"], sb["arts_per_ses"])
    row("Decs/sesión",  sa["decs_per_ses"], sb["decs_per_ses"])

    # Workflow distribution
    print(f"\n  Workflows — {label_a}:")
    for w, c in list(sa["workflows"].items())[:4]:
        print(f"    {w[-20:]:20s} {c}")
    print(f"\n  Workflows — {label_b}:")
    for w, c in list(sb["workflows"].items())[:4]:
        print(f"    {w[-20:]:20s} {c}")

    # Top roles
    print(f"\n  Roles top — {label_a}: " + ", ".join(f"{r}({c})" for r, c in list(sa["top_roles"].items())[:3]))
    print(f"  Roles top — {label_b}: " + ", ".join(f"{r}({c})" for r, c in list(sb["top_roles"].items())[:3]))
    print()


def _parse_period(spec: str):
    """Parse 'YYYY-MM-DD..YYYY-MM-DD' into (start, end)."""
    if ".." in spec:
        parts = spec.split("..")
        try:
            start = datetime.date.fromisoformat(parts[0].strip())
            end = datetime.date.fromisoformat(parts[1].strip())
            return start, end
        except ValueError:
            pass
    raise ValueError(f"Formato de periodo inválido: '{spec}'. Usar YYYY-MM-DD..YYYY-MM-DD")


def _session_date(s: dict):
    created = s.get("created_at", "")[:10]
    try:
        return datetime.date.fromisoformat(created)
    except Exception:
        return None


def cmd_compare(args):
    all_sessions = _load_sessions_all()

    if args.wf and len(args.wf) == 2:
        wf_a, wf_b = args.wf
        group_a = [s for s in all_sessions if s.get("selected_workflow", "").endswith(wf_a.lower()) or wf_a.lower() in s.get("selected_workflow", "")]
        group_b = [s for s in all_sessions if s.get("selected_workflow", "").endswith(wf_b.lower()) or wf_b.lower() in s.get("selected_workflow", "")]
        _render_compare(f"wf:{wf_a}", f"wf:{wf_b}", _stats(group_a), _stats(group_b), args.json)

    elif args.period and len(args.period) == 2:
        try:
            start_a, end_a = _parse_period(args.period[0])
            start_b, end_b = _parse_period(args.period[1])
        except ValueError as e:
            print(f"  ERROR: {e}")
            sys.exit(1)

        def in_period(s, start, end):
            d = _session_date(s)
            return d is not None and start <= d <= end

        group_a = [s for s in all_sessions if in_period(s, start_a, end_a)]
        group_b = [s for s in all_sessions if in_period(s, start_b, end_b)]
        la = f"{start_a}..{end_a}"
        lb = f"{start_b}..{end_b}"
        _render_compare(la, lb, _stats(group_a), _stats(group_b), args.json)

    elif args.role and len(args.role) == 2:
        role_a, role_b = args.role
        group_a = [s for s in all_sessions if role_a in s.get("roles_activated", [])]
        group_b = [s for s in all_sessions if role_b in s.get("roles_activated", [])]
        _render_compare(f"role:{role_a}", f"role:{role_b}", _stats(group_a), _stats(group_b), args.json)

    else:
        print("  ERROR: especifica --wf A B  |  --period P1 P2  |  --role R1 R2")
        sys.exit(1)


def run_tests():
    print("Ejecutando tests de compare.py...")
    errors = 0

    def ok(name):
        print(f"  OK: {name}")

    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    # Fake sessions
    fake_a = [
        {"artifacts": ["a", "b", "c"], "decisions": ["d1", "d2"], "roles_activated": ["r1"], "bugs_found": [], "selected_workflow": "w2_impl"},
        {"artifacts": ["x"], "decisions": ["d3"], "roles_activated": ["r1", "r2"], "bugs_found": ["bug1"], "selected_workflow": "w2_impl"},
    ]
    fake_b = [
        {"artifacts": ["p", "q"], "decisions": [], "roles_activated": [], "bugs_found": [], "selected_workflow": "w9_harvest"},
    ]

    # Test 1: _stats basic
    sa = _stats(fake_a)
    if sa["sessions"] == 2 and sa["artifacts"] == 4 and sa["decisions"] == 3:
        ok("compare:stats_basic")
    else:
        fail("compare:stats_basic", str(sa))

    # Test 2: arts_per_ses
    if sa["arts_per_ses"] == 2.0:
        ok("compare:arts_per_ses")
    else:
        fail("compare:arts_per_ses", f"got {sa['arts_per_ses']}")

    # Test 3: empty group
    se = _stats([])
    if se["sessions"] == 0 and se["arts_per_ses"] == 0.0:
        ok("compare:empty_group")
    else:
        fail("compare:empty_group", str(se))

    # Test 4: delta icon
    if _delta_icon(3, 5) == "▲" and _delta_icon(5, 3) == "▼" and _delta_icon(3, 3) == "=":
        ok("compare:delta_icon")
    else:
        fail("compare:delta_icon", "wrong icons")

    # Test 5: period parse
    try:
        s, e = _parse_period("2026-04-01..2026-04-15")
        if str(s) == "2026-04-01" and str(e) == "2026-04-15":
            ok("compare:period_parse")
        else:
            fail("compare:period_parse", f"{s}..{e}")
    except Exception as ex:
        fail("compare:period_parse", str(ex))

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago compare", add_help=False)
    parser.add_argument("--wf", nargs=2, default=None, metavar=("A", "B"))
    parser.add_argument("--period", nargs=2, default=None, metavar=("P1", "P2"))
    parser.add_argument("--role", nargs=2, default=None, metavar=("R1", "R2"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--test", action="store_true")
    parser.add_argument("--help", action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.help:
        parser.print_help()
    else:
        cmd_compare(args)


if __name__ == "__main__":
    main()