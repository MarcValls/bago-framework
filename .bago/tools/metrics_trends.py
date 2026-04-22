#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
metrics_trends.py - Tendencias de metricas BAGO con sparklines ASCII.

Analiza la evolucion de metricas clave a lo largo del tiempo:
  - Artefactos/sesion (rolling 4 semanas)
  - Decisiones/sesion
  - Roles/sesion
  - Health score (desde snapshots)
  - Workflows distribution

Uso:
  python3 metrics_trends.py             # vista completa
  python3 metrics_trends.py --weeks 8   # ultimas 8 semanas
  python3 metrics_trends.py --metric artifacts  # solo artefactos
  python3 metrics_trends.py --compare 4 8      # comparar 4 vs 8 semanas
  python3 metrics_trends.py --test
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
NL = "\n"

SPARKLINE_CHARS = [" ", ".", ":", "-", "=", "+", "*", "#", "@", "X"]


def _load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_sessions():
    folder = STATE / "sessions"
    if not folder.exists():
        return []
    sessions = []
    for f in folder.glob("*.json"):
        s = _load_json(f)
        if s and s.get("created_at"):
            sessions.append(s)
    sessions.sort(key=lambda s: s.get("created_at", ""))
    return sessions


def _artifacts_useful(session):
    excl = {"state/sessions/", "state/changes/", "state/evidences/",
            "TREE.txt", "CHECKSUMS.sha256"}
    return [a for a in session.get("artifacts", [])
            if not any(a.startswith(e) for e in excl)]


def _parse_date(s):
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        return date.today()


def _week_start(d):
    return d - timedelta(days=d.weekday())


def _sessions_by_week(sessions):
    """Agrupa sesiones por semana ISO. Retorna dict week_str -> list."""
    by_week = defaultdict(list)
    for s in sessions:
        d = _parse_date(s.get("created_at", ""))
        ws = _week_start(d)
        by_week[ws].append(s)
    return by_week


def _rolling_metrics(sessions, last_weeks=8):
    """Calcula metricas semanales para las ultimas N semanas."""
    today = date.today()
    cutoff = today - timedelta(weeks=last_weeks)
    recent = [s for s in sessions if _parse_date(s.get("created_at", "")) >= cutoff]

    by_week = _sessions_by_week(recent)
    sorted_weeks = sorted(by_week.keys())

    weeks_data = []
    for ws in sorted_weeks:
        slist = by_week[ws]
        arts_list = [len(_artifacts_useful(s)) for s in slist]
        decs_list = [len(s.get("decisions", [])) for s in slist]
        roles_list = [len(s.get("roles_activated", s.get("roles", []))) for s in slist]

        weeks_data.append({
            "week": ws,
            "n_sessions": len(slist),
            "avg_artifacts": sum(arts_list) / len(arts_list) if arts_list else 0,
            "avg_decisions": sum(decs_list) / len(decs_list) if decs_list else 0,
            "avg_roles": sum(roles_list) / len(roles_list) if roles_list else 0,
            "total_artifacts": sum(arts_list),
            "total_decisions": sum(decs_list),
        })

    return weeks_data


def _sparkline(values, width=20):
    """Genera sparkline ASCII para una lista de valores."""
    if not values:
        return " " * width
    mn, mx = min(values), max(values)
    rng = mx - mn
    result = []
    for v in values[-width:]:
        if rng == 0:
            idx = len(SPARKLINE_CHARS) // 2
        else:
            idx = int((v - mn) / rng * (len(SPARKLINE_CHARS) - 1))
        result.append(SPARKLINE_CHARS[min(idx, len(SPARKLINE_CHARS) - 1)])
    # Pad left if shorter than width
    while len(result) < width:
        result.insert(0, " ")
    return "".join(result)


def _bar(value, max_val, width=20):
    """Genera barra horizontal proporcional."""
    if max_val == 0:
        return " " * width
    filled = int((value / max_val) * width)
    return "#" * filled + "." * (width - filled)


def _compare_periods(sessions, weeks_a=4, weeks_b=8):
    """Compara metricas entre dos periodos."""
    today = date.today()

    def period_stats(weeks):
        cutoff = today - timedelta(weeks=weeks)
        recent = [s for s in sessions if _parse_date(s.get("created_at", "")) >= cutoff]
        if not recent:
            return {}
        arts = [len(_artifacts_useful(s)) for s in recent]
        decs = [len(s.get("decisions", [])) for s in recent]
        roles = [len(s.get("roles_activated", s.get("roles", []))) for s in recent]
        return {
            "n": len(recent),
            "avg_arts": sum(arts) / len(arts),
            "avg_decs": sum(decs) / len(decs),
            "avg_roles": sum(roles) / len(roles),
        }

    return period_stats(weeks_a), period_stats(weeks_b)


def render_metrics(sessions, weeks=8):
    """Render completo de metricas con sparklines."""
    weeks_data = _rolling_metrics(sessions, last_weeks=weeks)

    if not weeks_data:
        print("  No hay datos suficientes para calcular tendencias.")
        return

    all_sessions = sessions[-weeks*7:]  # aproximado

    print()
    print("  BAGO - Tendencias de metricas (ultimas {} semanas)".format(weeks))
    print()

    # All-time stats
    all_arts = [len(_artifacts_useful(s)) for s in sessions]
    all_decs = [len(s.get("decisions", [])) for s in sessions]
    all_roles = [len(s.get("roles_activated", s.get("roles", []))) for s in sessions]

    global_avg_arts  = sum(all_arts) / len(all_arts) if all_arts else 0
    global_avg_decs  = sum(all_decs) / len(all_decs) if all_decs else 0
    global_avg_roles = sum(all_roles) / len(all_roles) if all_roles else 0

    print("  Globales (todas las sesiones: {})".format(len(sessions)))
    print("    Artefactos/ses  : {:.1f}  (target: >=4.0)  {}".format(
        global_avg_arts, "OK" if global_avg_arts >= 4 else "BAJO"))
    print("    Decisiones/ses  : {:.1f}  (target: >=2.0)  {}".format(
        global_avg_decs, "OK" if global_avg_decs >= 2 else "BAJO"))
    print("    Roles/ses       : {:.1f}  (target: <=2.0)  {}".format(
        global_avg_roles, "OK" if global_avg_roles <= 2 else "ALTO"))
    print()

    # Sparklines
    arts_vals  = [w["avg_artifacts"] for w in weeks_data]
    decs_vals  = [w["avg_decisions"] for w in weeks_data]
    roles_vals = [w["avg_roles"] for w in weeks_data]
    sess_vals  = [w["n_sessions"] for w in weeks_data]

    print("  Sparklines (izq=anterior, der=reciente):")
    print()
    print("    Arts/ses  [{}]  {:.1f} -> {:.1f}".format(
        _sparkline(arts_vals, 24),
        arts_vals[0] if arts_vals else 0,
        arts_vals[-1] if arts_vals else 0))
    print("    Decs/ses  [{}]  {:.1f} -> {:.1f}".format(
        _sparkline(decs_vals, 24),
        decs_vals[0] if decs_vals else 0,
        decs_vals[-1] if decs_vals else 0))
    print("    Roles/ses [{}]  {:.1f} -> {:.1f}".format(
        _sparkline(roles_vals, 24),
        roles_vals[0] if roles_vals else 0,
        roles_vals[-1] if roles_vals else 0))
    print("    Sesiones  [{}]  {} -> {}".format(
        _sparkline(sess_vals, 24),
        int(sess_vals[0]) if sess_vals else 0,
        int(sess_vals[-1]) if sess_vals else 0))
    print()

    # Weekly table
    print("  Detalle semanal:")
    print()
    print("  {:<12}  {:>4}  {:>8}  {:>8}  {:>8}  {}".format(
        "Semana", "Ses", "Arts/s", "Decs/s", "Roles/s", "Artefactos totales"))
    print("  {}  {}  {}  {}  {}  {}".format(
        "-"*12, "-"*4, "-"*8, "-"*8, "-"*8, "-"*20))

    for w in weeks_data:
        week_s = w["week"].strftime("%Y-%m-%d")
        n = w["n_sessions"]
        aa = w["avg_artifacts"]
        ad = w["avg_decisions"]
        ar = w["avg_roles"]
        ta = w["total_artifacts"]
        arts_bar = _bar(ta, max(wd["total_artifacts"] for wd in weeks_data) or 1, width=20)
        print("  {:<12}  {:>4}  {:>8.1f}  {:>8.1f}  {:>8.1f}  |{}| {}".format(
            week_s, n, aa, ad, ar, arts_bar, ta))
    print()

    # Trend analysis
    if len(weeks_data) >= 2:
        first_half = weeks_data[:len(weeks_data)//2]
        second_half = weeks_data[len(weeks_data)//2:]

        avg_arts_first = sum(w["avg_artifacts"] for w in first_half) / len(first_half)
        avg_arts_second = sum(w["avg_artifacts"] for w in second_half) / len(second_half)
        delta_arts = avg_arts_second - avg_arts_first

        avg_decs_first = sum(w["avg_decisions"] for w in first_half) / len(first_half)
        avg_decs_second = sum(w["avg_decisions"] for w in second_half) / len(second_half)
        delta_decs = avg_decs_second - avg_decs_first

        trend_arts = "mejorando" if delta_arts > 0.2 else ("empeorando" if delta_arts < -0.2 else "estable")
        trend_decs = "mejorando" if delta_decs > 0.2 else ("empeorando" if delta_decs < -0.2 else "estable")

        print("  Tendencia (primera mitad vs segunda mitad del periodo):")
        print("    Artefactos: {:+.1f}  ({})".format(delta_arts, trend_arts))
        print("    Decisiones: {:+.1f}  ({})".format(delta_decs, trend_decs))
        print()


def render_comparison(sessions, weeks_a=4, weeks_b=8):
    """Muestra tabla comparativa entre dos periodos."""
    stats_a, stats_b = _compare_periods(sessions, weeks_a, weeks_b)

    if not stats_a or not stats_b:
        print("  Datos insuficientes para comparar periodos.")
        return

    print()
    print("  Comparacion: ultimas {} semanas vs {} semanas".format(weeks_a, weeks_b))
    print()
    print("  {:<20}  {:>10}  {:>10}  {:>10}".format("Metrica", "{}w".format(weeks_a), "{}w".format(weeks_b), "Delta"))
    print("  {}  {}  {}  {}".format("-"*20, "-"*10, "-"*10, "-"*10))

    for key, label in [("avg_arts", "Arts/sesion"), ("avg_decs", "Decs/sesion"),
                       ("avg_roles", "Roles/sesion"), ("n", "Sesiones")]:
        va = stats_a.get(key, 0)
        vb = stats_b.get(key, 0)
        delta = va - vb
        fmt = "{:.1f}" if isinstance(va, float) else "{}"
        print("  {:<20}  {:>10}  {:>10}  {:>+10.1f}".format(
            label, round(va, 1), round(vb, 1), delta))
    print()


def _run_tests():
    print("  Ejecutando tests de metrics_trends...")
    from datetime import date, timedelta

    today = date.today()
    sessions = [
        {"session_id": "S{}".format(i),
         "created_at": (today - timedelta(days=i)).isoformat() + "T10:00:00Z",
         "status": "closed",
         "selected_workflow": "w7_foco_sesion",
         "artifacts": ["a.py"] * (i % 5 + 1),
         "decisions": ["d"] * (i % 3 + 1),
         "roles_activated": ["role_a"] if i % 2 == 0 else ["role_a", "role_b"]}
        for i in range(1, 20)
    ]

    # Test sparkline
    vals = [1, 2, 3, 4, 5]
    spark = _sparkline(vals, width=5)
    assert len(spark) == 5, "sparkline length wrong"

    # Test _bar
    bar = _bar(5, 10, width=10)
    assert bar == "#####.....", "bar wrong: " + bar

    # Test rolling metrics
    data = _rolling_metrics(sessions, last_weeks=4)
    assert len(data) > 0, "no weekly data"
    for w in data:
        assert "avg_artifacts" in w
        assert w["n_sessions"] > 0

    # Test compare
    sa, sb = _compare_periods(sessions, 2, 4)
    assert "avg_arts" in sa
    assert sa["n"] <= sb["n"]

    print("  OK: todos los tests pasaron (4/4)")


def main():
    p = argparse.ArgumentParser(description="Tendencias de metricas BAGO")
    p.add_argument("--weeks", type=int, default=8, help="Semanas de historia (default: 8)")
    p.add_argument("--metric", choices=["artifacts", "decisions", "roles", "all"],
                   default="all", help="Metrica a mostrar")
    p.add_argument("--compare", nargs=2, type=int, metavar=("WA", "WB"),
                   help="Comparar dos periodos en semanas")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    if args.test:
        _run_tests()
        return

    sessions = _load_sessions()
    if not sessions:
        print("  No hay sesiones para analizar.")
        return

    if args.compare:
        render_comparison(sessions, args.compare[0], args.compare[1])
    else:
        render_metrics(sessions, weeks=args.weeks)


if __name__ == "__main__":
    main()
