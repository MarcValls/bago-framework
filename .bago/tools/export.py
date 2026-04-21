#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
export.py - Exportador de datos BAGO a HTML y CSV.

Genera reportes visuales listos para compartir o archivar:
  - HTML: tabla de sesiones con colores, gráfico de barras SVG inline, CSS integrado
  - CSV: datos tabulados para análisis en Excel/Calc/Pandas

Uso:
  python3 export.py --format html                  # reporte HTML completo
  python3 export.py --format csv                   # CSV de sesiones
  python3 export.py --format html --last 20        # últimas 20 sesiones
  python3 export.py --format html --out report.html
  python3 export.py --format csv --out sessions.csv
  python3 export.py --format all --out-dir /tmp/bago_export/
  python3 export.py --test
"""
from __future__ import annotations
import argparse, csv, io, json, os, sys
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"

# ── helpers ──────────────────────────────────────────────────────────────────

def _load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _load_sessions(last=None, since=None):
    folder = STATE / "sessions"
    if not folder.exists():
        return []
    sessions = []
    for f in folder.glob("*.json"):
        s = _load_json(f)
        if s and s.get("created_at"):
            sessions.append(s)
    sessions.sort(key=lambda s: s.get("created_at", ""))
    if since:
        sessions = [s for s in sessions if s["created_at"][:10] >= since]
    if last:
        sessions = sessions[-last:]
    return sessions


def _artifacts_useful(session):
    excl = {"state/sessions/", "state/changes/", "state/evidences/",
            "TREE.txt", "CHECKSUMS.sha256"}
    return [a for a in session.get("artifacts", [])
            if not any(a.startswith(e) for e in excl)]


def _wf_short(wf):
    mapping = {
        "w0_automode": "W0", "w1_cold_start": "W1", "w2_implementacion": "W2",
        "w3_debug": "W3", "w4_review": "W4", "w5_refactor": "W5",
        "w6_docs": "W6", "w7_foco_sesion": "W7", "w8_audit": "W8",
        "w9_cosecha": "W9", "workflow_system_change": "SC",
        "workflow_experiment": "EX", "workflow_analysis": "AN",
        "workflow_bootstrap": "BS", "workflow_role": "RL",
    }
    return mapping.get(wf, wf[:4].upper() if wf else "??")


def _wf_color(wf):
    colors = {
        "W9": "#6366f1", "W1": "#10b981", "W7": "#f59e0b", "W2": "#3b82f6",
        "SC": "#8b5cf6", "W0": "#ec4899", "W8": "#ef4444", "AN": "#06b6d4",
        "EX": "#84cc16", "BS": "#f97316", "RL": "#14b8a6",
    }
    short = _wf_short(wf)
    return colors.get(short, "#6b7280")


# ── CSV export ────────────────────────────────────────────────────────────────

def export_csv(sessions, out_path=None):
    """Exporta sesiones a CSV."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "session_id", "date", "workflow", "status",
        "artifacts", "decisions", "roles", "goal"
    ])
    for s in sessions:
        arts = len(_artifacts_useful(s))
        decs = len(s.get("decisions", []))
        roles = ",".join(s.get("roles_activated", s.get("roles", [])))
        goal = (s.get("user_goal") or s.get("summary") or "")[:80]
        writer.writerow([
            s.get("session_id", ""),
            s.get("created_at", "")[:10],
            s.get("selected_workflow", ""),
            s.get("status", ""),
            arts, decs, roles, goal
        ])
    content = buf.getvalue()
    if out_path:
        Path(out_path).write_text(content, encoding="utf-8")
        print("  CSV exportado: {} ({} sesiones)".format(out_path, len(sessions)))
    return content


# ── SVG inline bar chart ──────────────────────────────────────────────────────

def _svg_bar_chart(sessions, width=700, height=180):
    """Genera un SVG de barras apiladas por workflow por semana."""
    from collections import defaultdict
    from datetime import date, timedelta

    def week_start(d):
        return d - timedelta(days=d.weekday())

    by_week = defaultdict(lambda: defaultdict(int))
    wf_set = set()
    for s in sessions:
        try:
            d = date.fromisoformat(s["created_at"][:10])
        except Exception:
            continue
        ws = week_start(d)
        wf = _wf_short(s.get("selected_workflow", "??"))
        by_week[ws][wf] += 1
        wf_set.add(wf)

    if not by_week:
        return "<p>Sin datos</p>"

    weeks = sorted(by_week.keys())
    max_count = max(sum(by_week[w].values()) for w in weeks)
    wf_list = sorted(wf_set)

    pad_l, pad_r, pad_t, pad_b = 45, 15, 15, 35
    inner_w = width - pad_l - pad_r
    inner_h = height - pad_t - pad_b
    bar_w = max(8, min(40, inner_w // max(len(weeks), 1) - 4))
    bar_gap = inner_w // max(len(weeks), 1)

    wf_colors = {wf: _wf_color(wf) for wf in wf_list}

    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="{}" height="{}" style="font-family:monospace">'.format(width, height)]
    # Background
    parts.append('<rect width="{}" height="{}" fill="#1e1e2e" rx="8"/>'.format(width, height))
    # Y axis
    parts.append('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="#444" stroke-width="1"/>'.format(
        pad_l, pad_t, pad_l, pad_t + inner_h))
    # Y labels
    for i in range(5):
        y_val = int(max_count * (4 - i) / 4)
        y_pos = pad_t + inner_h * i // 4
        parts.append('<text x="{}" y="{}" fill="#888" font-size="9" text-anchor="end">{}</text>'.format(
            pad_l - 3, y_pos + 4, y_val))
        parts.append('<line x1="{}" y1="{}" x2="{}" y2="{}" stroke="#333" stroke-width="1"/>'.format(
            pad_l, y_pos, pad_l + inner_w, y_pos))

    # Bars
    for i, week in enumerate(weeks):
        x = pad_l + i * bar_gap + (bar_gap - bar_w) // 2
        y_cur = pad_t + inner_h
        wf_counts = by_week[week]
        total = sum(wf_counts.values())
        for wf in wf_list:
            cnt = wf_counts.get(wf, 0)
            if cnt == 0:
                continue
            bar_h = max(2, int(cnt / max_count * inner_h))
            y_cur -= bar_h
            color = wf_colors.get(wf, "#6b7280")
            parts.append('<rect x="{}" y="{}" width="{}" height="{}" fill="{}" rx="2"><title>{}: {}</title></rect>'.format(
                x, y_cur, bar_w, bar_h, color, wf, cnt))
        # X label
        label = week.strftime("%m/%d")
        parts.append('<text x="{}" y="{}" fill="#888" font-size="8" text-anchor="middle">{}</text>'.format(
            x + bar_w // 2, pad_t + inner_h + 14, label))

    # Legend
    legend_x = pad_l
    for j, wf in enumerate(wf_list[:8]):
        lx = legend_x + j * 55
        if lx + 50 > width:
            break
        parts.append('<rect x="{}" y="{}" width="10" height="10" fill="{}"/>'.format(
            lx, pad_t + inner_h + 22, wf_colors.get(wf, "#6b7280")))
        parts.append('<text x="{}" y="{}" fill="#aaa" font-size="9">{}</text>'.format(
            lx + 13, pad_t + inner_h + 31, wf))

    parts.append('</svg>')
    return "\n".join(parts)


# ── HTML export ───────────────────────────────────────────────────────────────

_HTML_CSS = """
body{font-family:system-ui,-apple-system,sans-serif;background:#0f0f1a;color:#e2e8f0;margin:0;padding:24px}
h1{color:#a78bfa;border-bottom:2px solid #312e81;padding-bottom:8px}
h2{color:#818cf8;margin-top:32px}
.meta{color:#64748b;font-size:0.85em;margin-bottom:24px}
.card{background:#1e1e2e;border:1px solid #2d2b55;border-radius:10px;padding:20px;margin-bottom:20px}
.stats{display:flex;gap:20px;flex-wrap:wrap;margin-bottom:20px}
.stat{background:#1e1e2e;border:1px solid #2d2b55;border-radius:8px;padding:16px 24px;text-align:center}
.stat .val{font-size:2em;font-weight:700;color:#a78bfa}
.stat .lbl{font-size:0.75em;color:#64748b;text-transform:uppercase;letter-spacing:.05em}
table{width:100%;border-collapse:collapse;font-size:0.85em}
th{background:#312e81;color:#c4b5fd;padding:8px 12px;text-align:left;font-weight:600}
td{padding:7px 12px;border-bottom:1px solid #1e1e3a}
tr:hover td{background:#1e1e3a}
.badge{display:inline-block;padding:2px 8px;border-radius:12px;font-size:0.75em;font-weight:600}
.status-closed{background:#064e3b;color:#34d399}
.status-open{background:#7c2d12;color:#fb923c}
.num{text-align:right;font-variant-numeric:tabular-nums}
.goal{color:#94a3b8;max-width:280px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
"""

def export_html(sessions, out_path=None, pack_id="bago"):
    """Genera un reporte HTML completo con gráfico SVG inline."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # Stats
    total_arts = sum(len(_artifacts_useful(s)) for s in sessions)
    total_decs = sum(len(s.get("decisions", [])) for s in sessions)
    closed = sum(1 for s in sessions if s.get("status") == "closed")
    wf_counter = defaultdict(int)
    for s in sessions:
        wf_counter[s.get("selected_workflow", "unknown")] += 1
    top_wf = max(wf_counter, key=wf_counter.get) if wf_counter else "—"

    avg_arts = total_arts / len(sessions) if sessions else 0
    svg = _svg_bar_chart(sessions)

    # Table rows
    rows = []
    for s in reversed(sessions):
        sid = s.get("session_id", "")
        d = s.get("created_at", "")[:10]
        wf = s.get("selected_workflow", "")
        wf_s = _wf_short(wf)
        color = _wf_color(wf)
        status = s.get("status", "")
        arts = len(_artifacts_useful(s))
        decs = len(s.get("decisions", []))
        goal = (s.get("user_goal") or s.get("summary") or "")[:70]
        rows.append(
            '<tr>'
            '<td><code style="color:#a78bfa">{}</code></td>'
            '<td>{}</td>'
            '<td><span class="badge" style="background:{};color:#fff">{}</span></td>'
            '<td><span class="badge status-{}">{}</span></td>'
            '<td class="num">{}</td>'
            '<td class="num">{}</td>'
            '<td class="goal" title="{}">{}</td>'
            '</tr>'.format(
                sid, d, color, wf_s, status, status, arts, decs, goal, goal)
        )

    html = """<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width">
<title>BAGO Report — {pack}</title>
<style>{css}</style>
</head>
<body>
<h1>BAGO Framework — Reporte de Sesiones</h1>
<p class="meta">Pack: <strong>{pack}</strong> &nbsp;·&nbsp; Generado: {now} &nbsp;·&nbsp; {n} sesiones</p>

<div class="stats">
  <div class="stat"><div class="val">{n}</div><div class="lbl">Sesiones</div></div>
  <div class="stat"><div class="val">{arts}</div><div class="lbl">Artefactos</div></div>
  <div class="stat"><div class="val">{decs}</div><div class="lbl">Decisiones</div></div>
  <div class="stat"><div class="val">{avg:.1f}</div><div class="lbl">Arts/Sesión</div></div>
  <div class="stat"><div class="val">{closed}</div><div class="lbl">Cerradas</div></div>
  <div class="stat"><div class="val">{top_wf}</div><div class="lbl">Top Workflow</div></div>
</div>

<div class="card">
<h2>Actividad por semana</h2>
{svg}
</div>

<h2>Sesiones</h2>
<table>
<thead><tr>
  <th>ID</th><th>Fecha</th><th>Workflow</th><th>Estado</th>
  <th class="num">Arts</th><th class="num">Decs</th><th>Objetivo</th>
</tr></thead>
<tbody>
{rows}
</tbody>
</table>

<p class="meta" style="margin-top:32px">Generado por <code>bago export</code> · BAGO Framework</p>
</body></html>""".format(
        pack=pack_id, css=_HTML_CSS, now=now_str, n=len(sessions),
        arts=total_arts, decs=total_decs, avg=avg_arts,
        closed=closed, top_wf=_wf_short(top_wf),
        svg=svg, rows="\n".join(rows)
    )

    if out_path:
        Path(out_path).write_text(html, encoding="utf-8")
        print("  HTML exportado: {} ({} sesiones, {:.1f} KB)".format(
            out_path, len(sessions), len(html) / 1024))
    return html


# ── tests ─────────────────────────────────────────────────────────────────────

def _run_tests():
    print("  Ejecutando tests de export.py...")
    import tempfile

    today = date.today()
    sessions = [
        {"session_id": "SES-TST-{}".format(i),
         "created_at": (today - timedelta(days=i)).isoformat() + "T10:00:00Z",
         "status": "closed" if i > 1 else "open",
         "selected_workflow": ["w9_cosecha", "w7_foco_sesion", "w1_cold_start"][i % 3],
         "artifacts": ["a{}.py".format(j) for j in range(i % 4 + 1)],
         "decisions": ["d{}".format(j) for j in range(i % 3 + 1)],
         "roles_activated": ["role_a"],
         "user_goal": "Test sesion {}".format(i)}
        for i in range(1, 12)
    ]

    # Test CSV
    csv_content = export_csv(sessions)
    lines = csv_content.strip().splitlines()
    assert lines[0].startswith("session_id"), "CSV header wrong: " + lines[0]
    assert len(lines) == len(sessions) + 1, "CSV row count wrong"

    # Test CSV to file
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        tmp_csv = f.name
    export_csv(sessions, tmp_csv)
    assert Path(tmp_csv).exists()
    Path(tmp_csv).unlink()

    # Test HTML
    html = export_html(sessions, pack_id="test_pack")
    assert "BAGO Framework" in html
    assert "SES-TST-1" in html
    assert "<svg" in html
    assert len(html) > 5000, "HTML demasiado corto: {}".format(len(html))

    # Test HTML to file
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as f:
        tmp_html = f.name
    export_html(sessions, tmp_html, pack_id="test_pack")
    assert Path(tmp_html).exists()
    Path(tmp_html).unlink()

    # Test SVG
    svg = _svg_bar_chart(sessions)
    assert svg.startswith("<svg")
    assert "rect" in svg

    print("  OK: todos los tests pasaron (5/5)")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Exportador BAGO a HTML/CSV")
    p.add_argument("--format", choices=["html", "csv", "all"], default="html")
    p.add_argument("--last", type=int, default=None, metavar="N")
    p.add_argument("--since", default=None, metavar="DATE")
    p.add_argument("--out", default=None, metavar="FILE")
    p.add_argument("--out-dir", default=None, metavar="DIR")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    if args.test:
        _run_tests()
        return

    sessions = _load_sessions(last=args.last, since=args.since)
    if not sessions:
        print("  No hay sesiones para exportar.")
        return

    pack_data = _load_json(ROOT / "pack.json")
    pack_id = pack_data.get("id", "bago")

    if args.out_dir:
        out_dir = Path(args.out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        export_html(sessions, out_dir / "bago_report_{}.html".format(ts), pack_id)
        export_csv(sessions, out_dir / "bago_sessions_{}.csv".format(ts))
        return

    fmt = args.format
    if fmt in ("html", "all"):
        out = args.out or "bago_report_{}.html".format(
            datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
        export_html(sessions, out, pack_id)
    if fmt in ("csv", "all"):
        out = args.out or "bago_sessions_{}.csv".format(
            datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S"))
        export_csv(sessions, out)


if __name__ == "__main__":
    main()
