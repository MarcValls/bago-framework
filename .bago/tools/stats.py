#!/usr/bin/env python3
"""
bago stats — dashboard agregado de estadísticas del pack.

Presenta un resumen numérico exhaustivo de sesiones, cambios, sprints,
metas y actividad, con sparklines de tendencia semanal.

Uso:
    bago stats              → dashboard completo
    bago stats --section S  → solo seccion (sessions/changes/sprints/goals/activity)
    bago stats --json       → output JSON
    bago stats --test       → tests integrados
"""

import argparse
import json
import sys
import datetime
from pathlib import Path
from collections import defaultdict

BAGO_ROOT = Path(__file__).parent.parent
STATE_DIR = BAGO_ROOT / "state"
SESSIONS_DIR = STATE_DIR / "sessions"
CHANGES_DIR = STATE_DIR / "changes"
SPRINTS_DIR = STATE_DIR / "sprints"
GOALS_DIR = STATE_DIR / "goals"


def _sparkline(values: list, width: int = 8) -> str:
    """Genera un sparkline ASCII de 8 posiciones."""
    bars = " ▁▂▃▄▅▆▇█"
    if not values or max(values) == 0:
        return "─" * width
    mn, mx = min(values), max(values)
    span = mx - mn or 1
    return "".join(bars[min(8, int((v - mn) / span * 8))] for v in values[-width:])


def _load_sessions() -> list:
    out = []
    for f in sorted(SESSIONS_DIR.glob("SES-*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except Exception:
            pass
    return out


def _load_changes() -> list:
    out = []
    for f in sorted(CHANGES_DIR.glob("BAGO-CHG-*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except Exception:
            pass
    return out


def _load_sprints() -> list:
    out = []
    if SPRINTS_DIR.exists():
        for f in sorted(SPRINTS_DIR.glob("SPRINT-*.json")):
            try:
                out.append(json.loads(f.read_text()))
            except Exception:
                pass
    return out


def _load_goals() -> list:
    out = []
    if GOALS_DIR.exists():
        for f in sorted(GOALS_DIR.glob("GOAL-*.json")):
            try:
                out.append(json.loads(f.read_text()))
            except Exception:
                pass
    return out


def _date(s: str) -> datetime.date | None:
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def _sessions_per_week(sessions: list, n_weeks: int = 8) -> list:
    today = datetime.date.today()
    weeks = []
    for i in range(n_weeks, 0, -1):
        wstart = today - datetime.timedelta(weeks=i)
        wend = wstart + datetime.timedelta(days=7)
        count = sum(
            1 for s in sessions
            if _date(s.get("created_at")) and wstart <= _date(s.get("created_at")) < wend
        )
        weeks.append(count)
    return weeks


def section_sessions(sessions: list) -> dict:
    total = len(sessions)
    closed = sum(1 for s in sessions if s.get("status") == "closed")
    open_s = sum(1 for s in sessions if s.get("status") == "open")
    legacy = sum(1 for s in sessions if s.get("status") == "completed")
    avg_arts = sum(len(s.get("artifacts", [])) for s in sessions) / total if total else 0
    avg_decs = sum(len(s.get("decisions", [])) for s in sessions) / total if total else 0
    wf_count = defaultdict(int)
    for s in sessions:
        wf_count[s.get("selected_workflow", "?")] += 1
    top_wf = max(wf_count, key=wf_count.get) if wf_count else "?"
    weekly = _sessions_per_week(sessions)
    return {
        "total": total,
        "closed": closed,
        "open": open_s,
        "legacy_status": legacy,
        "avg_artifacts": round(avg_arts, 1),
        "avg_decisions": round(avg_decs, 1),
        "top_workflow": top_wf,
        "weekly_sparkline": _sparkline(weekly),
        "weekly_values": weekly,
    }


def section_changes(changes: list) -> dict:
    total = len(changes)
    by_severity = defaultdict(int)
    by_type = defaultdict(int)
    for c in changes:
        by_severity[c.get("severity", "?")] += 1
        by_type[c.get("type", "?")] += 1
    return {
        "total": total,
        "by_severity": dict(by_severity),
        "by_type": dict(by_type),
    }


def section_sprints(sprints: list) -> dict:
    total = len(sprints)
    done = sum(1 for s in sprints if s.get("status") == "done")
    open_s = sum(1 for s in sprints if s.get("status") == "open")
    return {
        "total": total,
        "done": done,
        "open": open_s,
    }


def section_goals(goals: list) -> dict:
    total = len(goals)
    closed = sum(1 for g in goals if g.get("status") == "closed")
    open_g = sum(1 for g in goals if g.get("status") == "open")
    return {
        "total": total,
        "closed": closed,
        "open": open_g,
        "completion_rate": f"{int(closed/total*100)}%" if total else "N/A",
    }


def section_activity(sessions: list) -> dict:
    today = datetime.date.today()
    last_7  = sum(1 for s in sessions if _date(s.get("created_at")) and (today - _date(s.get("created_at"))).days <= 7)
    last_30 = sum(1 for s in sessions if _date(s.get("created_at")) and (today - _date(s.get("created_at"))).days <= 30)
    total_arts = sum(len(s.get("artifacts", [])) for s in sessions)
    total_decs = sum(len(s.get("decisions", [])) for s in sessions)
    return {
        "sessions_last_7d": last_7,
        "sessions_last_30d": last_30,
        "total_artifacts": total_arts,
        "total_decisions": total_decs,
    }


def render_stats(data: dict, as_json: bool):
    if as_json:
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    W = "\033[1m"
    R = "\033[0m"

    def hdr(title):
        print(f"\n  {W}── {title} ──{R}")

    hdr("SESIONES")
    ses = data["sessions"]
    print(f"  Total: {ses['total']}  |  Cerradas: {ses['closed']}  |  Abiertas: {ses['open']}  |  Legacy: {ses['legacy_status']}")
    print(f"  Media arts/sesión: {ses['avg_artifacts']}  |  Media decs/sesión: {ses['avg_decisions']}")
    print(f"  Workflow dominante: {ses['top_workflow']}")
    print(f"  Actividad (8 semanas): {ses['weekly_sparkline']}")

    hdr("CAMBIOS")
    chg = data["changes"]
    print(f"  Total: {chg['total']}")
    sev_line = "  ".join(f"{k}:{v}" for k, v in chg["by_severity"].items())
    print(f"  Severidad:  {sev_line}")
    type_line = "  ".join(f"{k}:{v}" for k, v in chg["by_type"].items())
    print(f"  Tipo:       {type_line}")

    hdr("SPRINTS")
    spr = data["sprints"]
    print(f"  Total: {spr['total']}  |  Done: {spr['done']}  |  Open: {spr['open']}")

    hdr("METAS")
    g = data["goals"]
    print(f"  Total: {g['total']}  |  Cerradas: {g['closed']}  |  Abiertas: {g['open']}  |  Tasa: {g['completion_rate']}")

    hdr("ACTIVIDAD RECIENTE")
    act = data["activity"]
    print(f"  Sesiones últimos 7d:  {act['sessions_last_7d']}")
    print(f"  Sesiones últimos 30d: {act['sessions_last_30d']}")
    print(f"  Total artefactos producidos: {act['total_artifacts']}")
    print(f"  Total decisiones capturadas: {act['total_decisions']}")
    print()


def build_stats(section_filter: str = None) -> dict:
    sessions = _load_sessions()
    changes  = _load_changes()
    sprints  = _load_sprints()
    goals    = _load_goals()

    data = {
        "sessions":  section_sessions(sessions),
        "changes":   section_changes(changes),
        "sprints":   section_sprints(sprints),
        "goals":     section_goals(goals),
        "activity":  section_activity(sessions),
    }
    if section_filter and section_filter in data:
        return {section_filter: data[section_filter]}
    return data


def run_tests():
    print("Ejecutando tests de stats.py...")
    errors = 0

    def ok(name): print(f"  OK: {name}")
    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    # Test 1: _sparkline basic
    sp = _sparkline([0, 1, 2, 3, 4, 5, 6, 7])
    if len(sp) == 8:
        ok("stats:sparkline_length")
    else:
        fail("stats:sparkline_length", f"len={len(sp)}")

    # Test 2: section_sessions with fake data
    fake = [
        {"status": "closed", "artifacts": ["a","b"], "decisions": ["d1"], "created_at": "2026-04-01", "selected_workflow": "W2"},
        {"status": "closed", "artifacts": [], "decisions": [], "created_at": "2026-04-10", "selected_workflow": "W2"},
        {"status": "open",   "artifacts": ["x"], "decisions": [], "created_at": "2026-04-20", "selected_workflow": "W9"},
    ]
    ses = section_sessions(fake)
    assert ses["total"] == 3, ses
    assert ses["closed"] == 2, ses
    ok("stats:section_sessions")

    # Test 3: section_changes with fake
    fchg = [
        {"severity": "minor", "type": "architecture"},
        {"severity": "minor", "type": "governance"},
        {"severity": "major", "type": "architecture"},
    ]
    chg = section_changes(fchg)
    assert chg["total"] == 3, chg
    assert chg["by_severity"]["minor"] == 2, chg
    ok("stats:section_changes")

    # Test 4: build_stats on real data returns dict with all sections
    data = build_stats()
    assert all(k in data for k in ["sessions","changes","sprints","goals","activity"]), data.keys()
    ok("stats:build_stats_all_sections")

    # Test 5: section_filter
    filt = build_stats(section_filter="sessions")
    assert list(filt.keys()) == ["sessions"], list(filt.keys())
    ok("stats:section_filter")

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago stats", add_help=False)
    parser.add_argument("--section", default=None,
                        help="sessions|changes|sprints|goals|activity")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--test", action="store_true")

    args = parser.parse_args()

    if args.test:
        run_tests()
    else:
        data = build_stats(section_filter=args.section)
        render_stats(data, as_json=args.json)


if __name__ == "__main__":
    main()