#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
timeline.py - Timeline visual ASCII de sesiones BAGO.

Muestra sesiones agrupadas por semana con emojis de workflow,
indicadores de artefactos y health score en hitos clave.

Uso:
  python3 timeline.py                  # ultimas 8 semanas
  python3 timeline.py --weeks 4        # ultimas 4 semanas
  python3 timeline.py --all            # todas las sesiones
  python3 timeline.py --sprint S1      # solo sesiones de sprint S1
  python3 timeline.py --workflow W7    # filtrar por workflow
  python3 timeline.py --test
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"

WORKFLOW_ICON = {
    "w0_free_session":              "W0",
    "w1_cold_start":                "W1",
    "w2_implementacion_controlada": "W2",
    "w3_refactor_sensible":         "W3",
    "w4_debug_multicausa":          "W4",
    "w5_cierre_continuidad":        "W5",
    "w6_ideacion_aplicada":         "W6",
    "w7_foco_sesion":               "W7",
    "w8_exploracion":               "W8",
    "w9_cosecha":                   "W9",
    "workflow_system_change":       "SC",
    "workflow_analysis":            "AN",
    "workflow_execution":           "EX",
    "workflow_bootstrap_repo_first":"BS",
}

STATUS_MARK = {"closed": "*", "open": "o", "active": "o"}


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_all_sessions() -> list:
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


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _parse_date(s: str) -> date:
    """Parsea YYYY-MM-DD o ISO datetime."""
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        return date.today()


def _workflow_label(wf: str) -> str:
    return WORKFLOW_ICON.get(wf, wf[:4].upper() if wf else "??")


def _artifacts_count(session: dict) -> int:
    excl = {"state/sessions/", "state/changes/", "state/evidences/", "TREE.txt", "CHECKSUMS.sha256"}
    arts = [a for a in session.get("artifacts", [])
            if not any(a.startswith(e) for e in excl)]
    return len(arts)


def _build_timeline(sessions: list, weeks: int = 8, sprint_id: str = "",
                    workflow_filter: str = "") -> list:
    """Devuelve lista de dict por semana con sesiones."""
    if not sessions:
        return []

    # Aplicar filtros
    filtered = sessions
    if workflow_filter:
        filtered = [s for s in filtered
                    if workflow_filter.lower() in s.get("selected_workflow", "").lower()]
    if sprint_id:
        sprint_file = STATE / "sprints" / "{}.json".format(sprint_id)
        sprint = _load_json(sprint_file)
        sprint_sessions = set(sprint.get("sessions", []))
        filtered = [s for s in filtered
                    if s.get("session_id", "") in sprint_sessions]

    if not filtered:
        return []

    # Determinar rango de fechas
    today = date.today()
    if weeks > 0:
        cutoff = today - timedelta(weeks=weeks)
        filtered = [s for s in filtered if _parse_date(s.get("created_at", "")) >= cutoff]

    # Agrupar por semana
    weeks_map = defaultdict(list)
    for s in filtered:
        d = _parse_date(s.get("created_at", ""))
        ws = _week_start(d)
        weeks_map[ws].append(s)

    # Construir lista ordenada de semanas
    result = []
    all_weeks = sorted(weeks_map.keys())
    for ws in all_weeks:
        slist = sorted(weeks_map[ws], key=lambda s: s.get("created_at", ""))
        result.append({"week_start": ws, "sessions": slist})
    return result


def render_timeline(sessions: list, weeks: int = 8, all_sessions: bool = False,
                    sprint_id: str = "", workflow_filter: str = "") -> None:
    effective_weeks = 0 if all_sessions else weeks
    timeline = _build_timeline(sessions, weeks=effective_weeks,
                               sprint_id=sprint_id, workflow_filter=workflow_filter)

    if not timeline:
        print("  No hay sesiones para mostrar con los filtros aplicados.")
        return

    total_sessions = sum(len(w["sessions"]) for w in timeline)
    print()
    print("  BAGO - Timeline de sesiones")
    print("  Semanas: {}  |  Sesiones: {}".format(len(timeline), total_sessions))
    if workflow_filter:
        print("  Filtro workflow: {}".format(workflow_filter))
    if sprint_id:
        print("  Sprint: {}".format(sprint_id))
    print()
    print("  {:<12}  {:<6}  {}".format("Semana", "Count", "Sesiones"))
    print("  {}  {}  {}".format("-" * 12, "-" * 6, "-" * 60))

    for week in timeline:
        ws = week["week_start"]
        slist = week["sessions"]
        count = len(slist)
        # Barra visual proporcional
        bar_width = min(count * 3, 30)
        bar = "#" * bar_width

        # Detalles de sesiones: WF[status][arts]
        details = []
        for s in slist:
            wf = _workflow_label(s.get("selected_workflow", ""))
            st = STATUS_MARK.get(s.get("status", ""), "-")
            an = _artifacts_count(s)
            arts_str = "+{}a".format(an) if an > 0 else ""
            details.append("[{}{}{}]".format(wf, st, arts_str))

        details_str = " ".join(details)
        week_str = ws.strftime("%Y-%m-%d")
        print("  {:<12}  {:>3}/wk  {}  {}".format(
            week_str, count, bar.ljust(30), details_str))

    print()
    # Summary stats
    all_arts = sum(_artifacts_count(s) for w in timeline for s in w["sessions"])
    all_decisions = sum(len(s.get("decisions", [])) for w in timeline for s in w["sessions"])
    print("  Totales: {} artefactos, {} decisiones en {} sesiones".format(
        all_arts, all_decisions, total_sessions))

    # Most active workflow
    wf_count = defaultdict(int)
    for w in timeline:
        for s in w["sessions"]:
            wf = s.get("selected_workflow", "unknown")
            wf_count[wf] += 1
    if wf_count:
        top_wf = max(wf_count, key=wf_count.get)
        print("  Workflow mas usado: {} ({} sesiones)".format(top_wf, wf_count[top_wf]))
    print()


def _run_tests():
    print("  Ejecutando tests de timeline...")
    today = date.today()

    # Datos de prueba
    sessions = [
        {"session_id": "S1", "selected_workflow": "w7_foco_sesion",
         "created_at": (today - timedelta(days=3)).isoformat() + "T10:00:00Z",
         "status": "closed", "artifacts": ["tool.py", "doc.md"], "decisions": ["d1"]},
        {"session_id": "S2", "selected_workflow": "w9_cosecha",
         "created_at": (today - timedelta(days=2)).isoformat() + "T10:00:00Z",
         "status": "closed", "artifacts": [], "decisions": ["d1", "d2"]},
        {"session_id": "S3", "selected_workflow": "w7_foco_sesion",
         "created_at": (today - timedelta(days=10)).isoformat() + "T10:00:00Z",
         "status": "closed", "artifacts": ["tool2.py"], "decisions": []},
    ]

    # Test _week_start
    d = date(2026, 4, 20)  # Monday (Apr 20 2026)
    assert _week_start(d) == date(2026, 4, 20)
    d2 = date(2026, 4, 23)  # Thursday of same week
    assert _week_start(d2) == date(2026, 4, 20)

    # Test _workflow_label
    assert _workflow_label("w7_foco_sesion") == "W7"
    assert _workflow_label("w9_cosecha") == "W9"
    assert _workflow_label("unknown_wf") == "UNKN"

    # Test _build_timeline
    tl = _build_timeline(sessions, weeks=4, workflow_filter="w7")
    assert len(tl) > 0
    # All sessions in filtered timeline should be w7
    for week in tl:
        for s in week["sessions"]:
            assert "w7" in s["selected_workflow"]

    # Test _artifacts_count
    assert _artifacts_count(sessions[0]) == 2
    assert _artifacts_count(sessions[1]) == 0

    print("  OK: todos los tests pasaron (5/5)")


def main():
    p = argparse.ArgumentParser(description="Timeline visual BAGO")
    p.add_argument("--weeks", type=int, default=8, help="Semanas a mostrar (default: 8)")
    p.add_argument("--all", dest="all_sessions", action="store_true",
                   help="Mostrar todas las sesiones")
    p.add_argument("--sprint", default="", help="Filtrar por sprint ID")
    p.add_argument("--workflow", default="", help="Filtrar por workflow")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    if args.test:
        _run_tests()
        return

    sessions = _load_all_sessions()
    if not sessions:
        print("  No hay sesiones registradas.")
        return

    render_timeline(
        sessions,
        weeks=args.weeks,
        all_sessions=args.all_sessions,
        sprint_id=args.sprint,
        workflow_filter=args.workflow,
    )


if __name__ == "__main__":
    main()
