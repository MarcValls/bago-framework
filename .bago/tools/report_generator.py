#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
report_generator.py - Generador de reportes Markdown BAGO.

Uso:
  python3 report_generator.py                    # ultimas 10 sesiones
  python3 report_generator.py --last 20
  python3 report_generator.py --since 2026-04-01
  python3 report_generator.py --sprint SPRINT-001
  python3 report_generator.py --workflow W7
  python3 report_generator.py --out report.md
  python3 report_generator.py --format summary
  python3 report_generator.py --test
"""
from __future__ import annotations
import argparse, json, sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"
NL = "\n"


def _load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_sessions(last=0, since="", workflow=""):
    folder = STATE / "sessions"
    if not folder.exists():
        return []
    sessions = []
    for f in folder.glob("*.json"):
        s = _load_json(f)
        if not s:
            continue
        if since and s.get("created_at", "")[:10] < since:
            continue
        if workflow and workflow.lower() not in s.get("selected_workflow", "").lower():
            continue
        sessions.append(s)
    sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
    return sessions[:last] if last > 0 else sessions


def _load_sprint_sessions(sprint_id):
    sprint_file = STATE / "sprints" / "{}.json".format(sprint_id)
    sprint = _load_json(sprint_file)
    ids = set(sprint.get("sessions", []))
    if not ids:
        return []
    folder = STATE / "sessions"
    sessions = []
    for f in folder.glob("*.json"):
        s = _load_json(f)
        if s and s.get("session_id", "") in ids:
            sessions.append(s)
    sessions.sort(key=lambda s: s.get("created_at", ""))
    return sessions


def _artifacts_useful(session):
    excl = {"state/sessions/", "state/changes/", "state/evidences/",
            "TREE.txt", "CHECKSUMS.sha256"}
    return [a for a in session.get("artifacts", [])
            if not any(a.startswith(e) for e in excl)]


def generate_full_report(sessions, title="Reporte BAGO"):
    lines = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines.append("# {}".format(title))
    lines.append("")
    lines.append("> Generado por `bago report` el {}".format(now_str))
    lines.append("> BAGO v2.5-stable")
    lines.append("")

    if not sessions:
        lines.append("_No hay sesiones para reportar._")
        return NL.join(lines)

    total = len(sessions)
    total_arts = sum(len(_artifacts_useful(s)) for s in sessions)
    total_decs = sum(len(s.get("decisions", [])) for s in sessions)
    workflows = set(s.get("selected_workflow", "?") for s in sessions)
    d_start = min(s.get("created_at", "")[:10] for s in sessions)
    d_end   = max(s.get("created_at", "")[:10] for s in sessions)

    lines.append("## Resumen ejecutivo")
    lines.append("")
    lines.append("| Metrica | Valor |")
    lines.append("|---------|-------|")
    lines.append("| Sesiones totales | {} |".format(total))
    lines.append("| Artefactos utiles | {} |".format(total_arts))
    lines.append("| Decisiones capturadas | {} |".format(total_decs))
    lines.append("| Artefactos/sesion | {:.1f} |".format(total_arts/total if total else 0))
    lines.append("| Decisiones/sesion | {:.1f} |".format(total_decs/total if total else 0))
    lines.append("| Rango de fechas | {} a {} |".format(d_start, d_end))
    lines.append("| Workflows usados | {} |".format(", ".join(sorted(workflows))))
    lines.append("")

    wf_count = defaultdict(int)
    for s in sessions:
        wf_count[s.get("selected_workflow", "unknown")] += 1

    lines.append("## Distribucion por workflow")
    lines.append("")
    lines.append("| Workflow | Sesiones | % |")
    lines.append("|---------|---------|---|")
    for wf, count in sorted(wf_count.items(), key=lambda x: -x[1]):
        pct = 100 * count / total
        lines.append("| {} | {} | {:.0f}% |".format(wf, count, pct))
    lines.append("")

    lines.append("## Sesiones")
    lines.append("")
    lines.append("| ID | Fecha | Workflow | Estado | Arts | Decs | Objetivo |")
    lines.append("|---|---|---|---|---|---|---|")
    for s in sorted(sessions, key=lambda s: s.get("created_at", ""), reverse=True):
        sid    = s.get("session_id", "?")
        date_s = s.get("created_at", "")[:10]
        wf     = s.get("selected_workflow", "")
        status = s.get("status", "")
        an     = len(_artifacts_useful(s))
        dn     = len(s.get("decisions", []))
        goal   = s.get("user_goal", s.get("summary", ""))[:60]
        lines.append("| {} | {} | {} | {} | {} | {} | {} |".format(
            sid, date_s, wf, status, an, dn, goal))
    lines.append("")

    all_arts = []
    for s in sessions:
        for art in _artifacts_useful(s):
            all_arts.append({"session": s.get("session_id", ""), "artifact": art,
                             "date": s.get("created_at", "")[:10]})

    if all_arts:
        lines.append("## Artefactos producidos ({} total)".format(len(all_arts)))
        lines.append("")
        by_ext = defaultdict(list)
        for a in all_arts:
            ext = Path(a["artifact"]).suffix or "(sin ext)"
            by_ext[ext].append(a)
        for ext, items in sorted(by_ext.items(), key=lambda x: -len(x[1])):
            lines.append("### `{}` ({})".format(ext, len(items)))
            for item in items[:8]:
                lines.append("- `{}` — *{}*".format(item["artifact"], item["session"]))
            if len(items) > 8:
                lines.append("- _... y {} mas_".format(len(items) - 8))
            lines.append("")

    all_decs = []
    for s in sessions:
        for d in s.get("decisions", []):
            all_decs.append({"session": s.get("session_id", ""),
                             "date": s.get("created_at", "")[:10], "decision": d})
    if all_decs:
        lines.append("## Decisiones ({} total)".format(len(all_decs)))
        lines.append("")
        for item in all_decs[-25:]:
            lines.append("- **{}** `{}`: {}".format(
                item["date"], item["session"], item["decision"][:100]))
        if len(all_decs) > 25:
            lines.append("")
            lines.append("_... y {} decisiones adicionales_".format(len(all_decs) - 25))
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("_Reporte generado con `bago report`. Framework BAGO v2.5-stable._")
    lines.append("")
    return NL.join(lines)


def generate_summary_report(sessions, title="Resumen BAGO"):
    lines = []
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    total  = len(sessions)
    t_arts = sum(len(_artifacts_useful(s)) for s in sessions)
    t_decs = sum(len(s.get("decisions", [])) for s in sessions)
    wf_count = defaultdict(int)
    for s in sessions:
        wf_count[s.get("selected_workflow", "unknown")] += 1
    top_wf = max(wf_count, key=wf_count.get) if wf_count else "--"

    lines.append("# {} - {}".format(title, now_str))
    lines.append("")
    lines.append("- **Sesiones:** {}".format(total))
    lines.append("- **Artefactos utiles:** {} ({:.1f}/ses)".format(
        t_arts, t_arts/total if total else 0))
    lines.append("- **Decisiones:** {} ({:.1f}/ses)".format(
        t_decs, t_decs/total if total else 0))
    lines.append("- **Workflow predominante:** {}".format(top_wf))
    lines.append("")
    if sessions:
        last = sessions[0]
        lines.append("**Ultima sesion:** `{}` - {}".format(
            last.get("session_id", ""), last.get("user_goal", "")[:80]))
        lines.append("")
    return NL.join(lines)


def _run_tests():
    print("  Ejecutando tests de report_generator...")
    sessions = [
        {"session_id": "S1", "selected_workflow": "w7_foco_sesion",
         "created_at": "2026-04-20T10:00:00Z", "status": "closed",
         "artifacts": ["tool.py", "doc.md"], "decisions": ["d1", "d2"],
         "user_goal": "Crear herramientas BAGO"},
        {"session_id": "S2", "selected_workflow": "w9_cosecha",
         "created_at": "2026-04-21T10:00:00Z", "status": "closed",
         "artifacts": ["harvest.md"], "decisions": ["d3"],
         "user_goal": "Cosecha contextual"},
    ]

    report = generate_full_report(sessions, title="Test Report")
    assert "Test Report" in report, "title missing"
    assert "Resumen ejecutivo" in report, "section missing"
    assert "Sesiones totales | 2" in report, "count wrong"
    assert "Artefactos utiles | 3" in report, "artifacts wrong"
    assert "tool.py" in report, "artifact missing"
    assert "d1" in report, "decision missing"

    summary = generate_summary_report(sessions, "Test Sum")
    assert "Test Sum" in summary

    s_filt = {"artifacts": ["tool.py", "TREE.txt", "CHECKSUMS.sha256", "state/sessions/x.json"]}
    assert _artifacts_useful(s_filt) == ["tool.py"], "filter failed"

    print("  OK: todos los tests pasaron (3/3)")


def main():
    p = argparse.ArgumentParser(description="Generador de reportes Markdown BAGO")
    p.add_argument("--last", type=int, default=10)
    p.add_argument("--since", default="", metavar="YYYY-MM-DD")
    p.add_argument("--sprint", default="")
    p.add_argument("--workflow", default="")
    p.add_argument("--out", default="", metavar="FILE")
    p.add_argument("--format", choices=["full", "summary"], default="full")
    p.add_argument("--title", default="")
    p.add_argument("--all-sessions", dest="all_sessions", action="store_true")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    if args.test:
        _run_tests()
        return

    if args.sprint:
        sessions = _load_sprint_sessions(args.sprint)
        default_title = "Reporte Sprint {}".format(args.sprint)
    elif args.since:
        sessions = _load_sessions(since=args.since, workflow=args.workflow)
        default_title = "Reporte desde {}".format(args.since)
    else:
        last = 0 if args.all_sessions else args.last
        sessions = _load_sessions(last=last, workflow=args.workflow)
        n = len(sessions) if args.all_sessions else args.last
        default_title = "Reporte BAGO - ultimas {} sesiones".format(n)

    title = args.title or default_title

    if args.format == "summary":
        content = generate_summary_report(sessions, title=title)
    else:
        content = generate_full_report(sessions, title=title)

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(content, encoding="utf-8")
        print("  Reporte guardado en: {}".format(out_path.resolve()))
        print("  Sesiones: {}  |  Formato: {}".format(len(sessions), args.format))
    else:
        print(content)


if __name__ == "__main__":
    main()
