#!/usr/bin/env python3
"""
bago velocity — métricas de velocidad de trabajo por período.

Calcula la velocidad del pack en términos de artefactos, decisiones
y sesiones por unidad de tiempo, con comparativa período a período
y proyección a fin de mes.

Uso:
    bago velocity              → velocidad última semana vs anterior
    bago velocity --period N   → últimos N días (default 7)
    bago velocity --rolling    → velocidad rolling en ventanas de 7 días
    bago velocity --json       → output JSON
    bago velocity --test       → tests integrados
"""

import argparse
import json
import sys
import datetime
from pathlib import Path
from collections import defaultdict

BAGO_ROOT = Path(__file__).parent.parent
SESSIONS_DIR = BAGO_ROOT / "state" / "sessions"


def _date(s: str):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def _load_all_sessions() -> list:
    out = []
    for f in sorted(SESSIONS_DIR.glob("SES-*.json")):
        try:
            out.append(json.loads(f.read_text()))
        except Exception:
            pass
    return out


def velocity_for_period(sessions: list, start: datetime.date, end: datetime.date) -> dict:
    period_sess = [s for s in sessions
                   if _date(s.get("created_at")) and start <= _date(s.get("created_at")) < end]
    n_days = max(1, (end - start).days)
    n_sess = len(period_sess)
    n_arts = sum(len(s.get("artifacts", [])) for s in period_sess)
    n_decs = sum(len(s.get("decisions", [])) for s in period_sess)
    n_closed = sum(1 for s in period_sess if s.get("status") == "closed")
    return {
        "sessions": n_sess,
        "closed": n_closed,
        "artifacts": n_arts,
        "decisions": n_decs,
        "days": n_days,
        "sess_per_day":  round(n_sess / n_days, 2),
        "arts_per_day":  round(n_arts / n_days, 2),
        "decs_per_day":  round(n_decs / n_days, 2),
        "arts_per_sess": round(n_arts / n_sess, 1) if n_sess else 0,
        "decs_per_sess": round(n_decs / n_sess, 1) if n_sess else 0,
    }


def rolling_velocity(sessions: list, n_windows: int = 8, window_days: int = 7) -> list:
    today = datetime.date.today()
    windows = []
    for i in range(n_windows, 0, -1):
        end   = today - datetime.timedelta(days=(i - 1) * window_days)
        start = end - datetime.timedelta(days=window_days)
        v = velocity_for_period(sessions, start, end)
        windows.append({
            "start": start.isoformat(),
            "end": end.isoformat(),
            **v,
        })
    return windows


def _sparkline(values: list, width: int = 8) -> str:
    bars = " ▁▂▃▄▅▆▇█"
    if not values or max(values) == 0:
        return "─" * width
    mn, mx = min(values), max(values)
    span = mx - mn or 1
    return "".join(bars[min(8, int((v - mn) / span * 8))] for v in values[-width:])


def render_velocity(current: dict, previous: dict, rolling: list, as_json: bool):
    if as_json:
        print(json.dumps({
            "current_period": current,
            "previous_period": previous,
            "rolling_8w": rolling,
        }, indent=2, ensure_ascii=False))
        return

    RESET = "\033[0m"
    GREEN = "\033[32m"
    RED   = "\033[31m"
    BOLD  = "\033[1m"

    def delta_str(curr_val, prev_val, unit=""):
        if prev_val == 0:
            return ""
        pct = int((curr_val - prev_val) / prev_val * 100)
        color = GREEN if pct >= 0 else RED
        arrow = "↑" if pct >= 0 else "↓"
        return f" {color}{arrow}{abs(pct)}%{RESET}"

    print(f"\n  {BOLD}BAGO Velocity{RESET}\n")

    print(f"  {BOLD}Período actual{RESET} ({current['days']}d)  vs  anterior ({previous['days']}d)\n")

    rows = [
        ("Sesiones",    current["sessions"],  previous["sessions"]),
        ("Cerradas",    current["closed"],     previous["closed"]),
        ("Artefactos",  current["artifacts"],  previous["artifacts"]),
        ("Decisiones",  current["decisions"],  previous["decisions"]),
        ("Ses/día",     current["sess_per_day"], previous["sess_per_day"]),
        ("Arts/día",    current["arts_per_day"], previous["arts_per_day"]),
        ("Arts/sesión", current["arts_per_sess"], previous["arts_per_sess"]),
    ]

    for label, curr, prev in rows:
        d = delta_str(curr, prev)
        print(f"  {label:15s}  {str(curr):>8s}  (prev: {prev}){d}")

    # Rolling sparklines
    arts_vals = [w["artifacts"] for w in rolling]
    sess_vals = [w["sessions"]  for w in rolling]
    print(f"\n  Rolling 8 semanas:")
    print(f"    Sesiones:    {_sparkline(sess_vals)}  ({' '.join(str(v) for v in sess_vals)})")
    print(f"    Artefactos:  {_sparkline(arts_vals)}  ({' '.join(str(v) for v in arts_vals)})")

    # Projection
    days_in_month = datetime.date.today().day
    if current["days"] > 0 and current["sessions"] > 0:
        proj_sess = int(current["sess_per_day"] * 30)
        proj_arts = int(current["arts_per_day"] * 30)
        print(f"\n  Proyección a 30 días (ritmo actual):")
        print(f"    ~{proj_sess} sesiones  ·  ~{proj_arts} artefactos")

    print()


def run_tests():
    print("Ejecutando tests de velocity.py...")
    errors = 0

    def ok(name): print(f"  OK: {name}")
    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    today = datetime.date.today()
    fake = [
        {"created_at": (today - datetime.timedelta(days=3)).isoformat(),
         "status": "closed", "artifacts": ["a","b"], "decisions": ["d1"]},
        {"created_at": (today - datetime.timedelta(days=5)).isoformat(),
         "status": "closed", "artifacts": ["c"], "decisions": ["d2","d3"]},
        {"created_at": (today - datetime.timedelta(days=10)).isoformat(),
         "status": "closed", "artifacts": ["e","f","g"], "decisions": []},
    ]

    # Test 1: velocity_for_period counts correctly
    start = today - datetime.timedelta(days=7)
    v = velocity_for_period(fake, start, today)
    if v["sessions"] == 2 and v["artifacts"] == 3:
        ok("velocity:period_counts")
    else:
        fail("velocity:period_counts", str(v))

    # Test 2: arts_per_sess calculation
    if v["arts_per_sess"] == 1.5:
        ok("velocity:arts_per_sess")
    else:
        fail("velocity:arts_per_sess", str(v["arts_per_sess"]))

    # Test 3: rolling_velocity returns 8 windows
    all_sessions = _load_all_sessions()
    rolling = rolling_velocity(all_sessions)
    if len(rolling) == 8:
        ok("velocity:rolling_8_windows")
    else:
        fail("velocity:rolling_8_windows", str(len(rolling)))

    # Test 4: each window has required keys
    w = rolling[0]
    for k in ("start","end","sessions","artifacts","decisions","sess_per_day"):
        if k not in w:
            fail("velocity:window_keys", f"missing {k}")
            break
    else:
        ok("velocity:window_keys")

    # Test 5: _sparkline with all zeros is dashes
    sp = _sparkline([0,0,0,0], width=4)
    if len(sp) == 4 and all(c == "─" for c in sp):
        ok("velocity:sparkline_zeros")
    else:
        fail("velocity:sparkline_zeros", repr(sp))

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago velocity", add_help=False)
    parser.add_argument("--period", type=int, default=7)
    parser.add_argument("--rolling", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--test", action="store_true")

    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    sessions = _load_all_sessions()
    today = datetime.date.today()
    period = args.period

    current  = velocity_for_period(sessions, today - datetime.timedelta(days=period), today)
    previous = velocity_for_period(sessions, today - datetime.timedelta(days=period*2),
                                             today - datetime.timedelta(days=period))
    rolling  = rolling_velocity(sessions)

    render_velocity(current, previous, rolling, as_json=args.json)


if __name__ == "__main__":
    main()