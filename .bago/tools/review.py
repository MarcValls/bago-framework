#!/usr/bin/env python3
"""
bago review — genera un informe de revisión periódica del pack.

Consolida sesiones, cambios, insights y hábitos del último período
en un informe Markdown estructurado listo para compartir o archivar.

Uso:
    bago review                     → revisión semanal (últimos 7 días)
    bago review --period monthly    → últimos 30 días
    bago review --period N          → últimos N días
    bago review --out FILE          → guarda en archivo
    bago review --json              → output JSON
    bago review --test              → tests integrados
"""

import argparse
import json
import sys
import datetime
from pathlib import Path
from collections import defaultdict, Counter

BAGO_ROOT = Path(__file__).parent.parent
STATE_DIR = BAGO_ROOT / "state"
SESSIONS_DIR = STATE_DIR / "sessions"
CHANGES_DIR = STATE_DIR / "changes"


def _date(s: str):
    try:
        return datetime.date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def _load_sessions_in_period(days: int) -> list:
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    out = []
    for f in sorted(SESSIONS_DIR.glob("SES-*.json")):
        try:
            s = json.loads(f.read_text())
            d = _date(s.get("created_at"))
            if d and d >= cutoff:
                out.append(s)
        except Exception:
            pass
    return out


def _load_changes_in_period(days: int) -> list:
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    out = []
    for f in sorted(CHANGES_DIR.glob("BAGO-CHG-*.json")):
        try:
            c = json.loads(f.read_text())
            d = _date(c.get("created_at"))
            if d and d >= cutoff:
                out.append(c)
        except Exception:
            pass
    return out


def build_review(days: int) -> dict:
    sessions = _load_sessions_in_period(days)
    changes = _load_changes_in_period(days)

    period_label = {7: "semanal", 30: "mensual"}.get(days, f"últimos {days} días")
    today = datetime.date.today()
    start = today - datetime.timedelta(days=days)

    # Session summary
    closed = [s for s in sessions if s.get("status") == "closed"]
    open_s = [s for s in sessions if s.get("status") == "open"]
    total_arts = sum(len(s.get("artifacts", [])) for s in sessions)
    total_decs = sum(len(s.get("decisions", [])) for s in sessions)

    # Workflow breakdown
    wf_count = Counter(s.get("selected_workflow", "?") for s in sessions)

    # Top sessions by artifacts
    top_sessions = sorted(sessions, key=lambda s: len(s.get("artifacts", [])), reverse=True)[:3]

    # Key decisions
    all_decisions = []
    for s in closed:
        for d in s.get("decisions", [])[:2]:
            if isinstance(d, str) and d.strip():
                all_decisions.append(d)

    # Changes summary
    chg_by_sev = Counter(c.get("severity", "?") for c in changes)

    return {
        "period": period_label,
        "date_range": f"{start} → {today}",
        "days": days,
        "sessions": {
            "total": len(sessions),
            "closed": len(closed),
            "open": len(open_s),
            "total_artifacts": total_arts,
            "total_decisions": total_decs,
            "top_workflows": dict(wf_count.most_common(3)),
            "top_sessions": [
                {"id": s.get("session_id", "?"), "artifacts": len(s.get("artifacts", [])),
                 "workflow": s.get("selected_workflow", "?")}
                for s in top_sessions
            ],
        },
        "changes": {
            "total": len(changes),
            "by_severity": dict(chg_by_sev),
            "titles": [c.get("title", "")[:80] for c in changes[:5]],
        },
        "key_decisions": all_decisions[:10],
    }


def render_markdown(review: dict) -> str:
    lines = []
    today = datetime.date.today().isoformat()

    lines.append(f"# Revisión {review['period']} BAGO — {today}")
    lines.append(f"\n**Período:** {review['date_range']}  \n")

    lines.append("## 📊 Sesiones\n")
    s = review["sessions"]
    lines.append(f"- Total sesiones: **{s['total']}** (cerradas: {s['closed']}, abiertas: {s['open']})")
    lines.append(f"- Artefactos producidos: **{s['total_artifacts']}**")
    lines.append(f"- Decisiones capturadas: **{s['total_decisions']}**")

    if s["top_workflows"]:
        wf_str = ", ".join(f"`{k}` ({v})" for k, v in s["top_workflows"].items())
        lines.append(f"- Workflows: {wf_str}")

    if s["top_sessions"]:
        lines.append("\n### Top sesiones\n")
        lines.append("| Sesión | Artefactos | Workflow |")
        lines.append("|--------|-----------|---------|")
        for ts in s["top_sessions"]:
            lines.append(f"| `{ts['id']}` | {ts['artifacts']} | {ts['workflow']} |")

    if review["changes"]["total"] > 0:
        lines.append("\n## 🔄 Cambios registrados\n")
        c = review["changes"]
        lines.append(f"- Total cambios: **{c['total']}**")
        sev_str = ", ".join(f"{k}:{v}" for k, v in c["by_severity"].items())
        if sev_str:
            lines.append(f"- Severidades: {sev_str}")
        if c["titles"]:
            lines.append("\n### Cambios destacados\n")
            for t in c["titles"]:
                lines.append(f"- {t}")

    if review["key_decisions"]:
        lines.append("\n## 🎯 Decisiones clave\n")
        for d in review["key_decisions"]:
            lines.append(f"- {d}")

    lines.append(f"\n---\n*Generado por `bago review` el {today}*\n")
    return "\n".join(lines)


def run_tests():
    print("Ejecutando tests de review.py...")
    errors = 0

    def ok(name): print(f"  OK: {name}")
    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    # Test 1: build_review returns dict with all keys
    rev = build_review(days=7)
    for key in ("period", "date_range", "sessions", "changes", "key_decisions"):
        if key not in rev:
            fail("review:build_review_keys", f"missing {key}")
            break
    else:
        ok("review:build_review_keys")

    # Test 2: period labels
    rev30 = build_review(days=30)
    if rev30["period"] == "mensual":
        ok("review:period_label_monthly")
    else:
        fail("review:period_label_monthly", rev30["period"])

    # Test 3: render_markdown returns string with headers
    md = render_markdown(rev)
    if "## 📊 Sesiones" in md and "# Revisión" in md:
        ok("review:render_markdown_headers")
    else:
        fail("review:render_markdown_headers", md[:200])

    # Test 4: _load_sessions_in_period with 0 days = empty or recent only
    today_ses = _load_sessions_in_period(0)
    all_ses = _load_sessions_in_period(9999)
    if len(all_ses) >= len(today_ses):
        ok("review:period_filter_works")
    else:
        fail("review:period_filter_works", f"0d={len(today_ses)}, 9999d={len(all_ses)}")

    # Test 5: build_review 365 days covers all sessions
    rev_all = build_review(days=365)
    if rev_all["sessions"]["total"] >= 1:
        ok("review:build_review_365_days")
    else:
        fail("review:build_review_365_days", str(rev_all["sessions"]["total"]))

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago review", add_help=False)
    parser.add_argument("--period", default="weekly",
                        help="weekly|monthly|N (days)")
    parser.add_argument("--out", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--test", action="store_true")

    args = parser.parse_args()

    if args.test:
        run_tests()
        return

    period = args.period
    if period == "weekly":
        days = 7
    elif period == "monthly":
        days = 30
    else:
        try:
            days = int(period)
        except ValueError:
            print(f"Período inválido: {period}", file=sys.stderr)
            sys.exit(1)

    review = build_review(days=days)

    if args.json:
        print(json.dumps(review, indent=2, ensure_ascii=False))
    else:
        md = render_markdown(review)
        if args.out:
            Path(args.out).write_text(md)
            print(f"  Revisión guardada en: {args.out}")
        else:
            print(md)


if __name__ == "__main__":
    main()