#!/usr/bin/env python3
"""
metrics_dashboard.py — Dashboard HTML interactivo de métricas BAGO.

Genera un HTML con Chart.js que se auto-refresca cada 5 minutos.
Muestra: health, velocity, debt, risk, hotspots, sprint progress, sessions.

Uso:
    python3 metrics_dashboard.py              # genera una vez
    python3 metrics_dashboard.py --watch 300  # regenera cada 300s
    python3 metrics_dashboard.py --open       # genera y abre en browser
"""
import argparse, json, subprocess, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent
TOOLS     = Path(__file__).parent
STATE     = BAGO_ROOT / "state"
OUT_HTML  = BAGO_ROOT.parent / "BAGO_METRICS.html"

sys.path.insert(0, str(TOOLS))
from chart_engine import render_gauge, render_bar, render_line, render_doughnut

# ─── data collectors ─────────────────────────────────────────────────────────

def _run(tool, args=(), timeout=15):
    cmd = ["python3", str(TOOLS / tool)] + list(args)
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           cwd=str(BAGO_ROOT.parent))
        return r.stdout
    except Exception:
        return ""

def _load_gs():
    try:
        return json.loads((STATE / "global_state.json").read_text())
    except Exception:
        return {}

def _health_score():
    out = _run("health_report.py", ["--json"])
    try:
        start = out.find("{")
        if start >= 0:
            d = json.loads(out[start:])
            return d.get("score", 0), d.get("breakdown", {})
    except Exception:
        pass
    return 0, {}

def _velocity_data():
    sessions_dir = STATE / "sessions"
    now = datetime.now(timezone.utc)
    weeks = {}
    for f in sessions_dir.glob("*.json"):
        try:
            d = json.loads(f.read_text())
            ts = d.get("created_at") or d.get("updated_at", "")
            if not ts:
                continue
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            delta = (now - dt).days
            week_n = delta // 7
            if week_n < 8:
                weeks[week_n] = weeks.get(week_n, 0) + 1
        except Exception:
            pass
    labels = [f"-{i}sem" for i in range(7, -1, -1)]
    values = [weeks.get(i, 0) for i in range(7, -1, -1)]
    return labels, values

def _debt_data():
    out = _run("debt_ledger.py", ["--json"])
    try:
        start = out.find("{")
        if start >= 0:
            d = json.loads(out[start:])
            return d
    except Exception:
        pass
    return {}

def _risk_data():
    out = _run("risk_matrix.py", ["--json"])
    try:
        d = json.loads(out)
        return d
    except Exception:
        return {}

def _hotspots():
    out = _run("hotspot.py", ["--json", "--top", "8"])
    try:
        d = json.loads(out)
        return d if isinstance(d, list) else d.get("hotspots", [])
    except Exception:
        return []

def _sprint():
    sdir = STATE / "sprints"
    for f in sorted(sdir.glob("*.json"), reverse=True):
        try:
            d = json.loads(f.read_text())
            if d.get("status") == "open":
                return d
        except Exception:
            pass
    return {}

def _sessions_by_workflow():
    wf_count = {}
    for f in (STATE / "sessions").glob("*.json"):
        try:
            d = json.loads(f.read_text())
            wf = d.get("selected_workflow", "unknown")
            wf_count[wf] = wf_count.get(wf, 0) + 1
        except Exception:
            pass
    return wf_count

def _recent_changes(n=8):
    changes = []
    for f in sorted((STATE / "changes").glob("BAGO-CHG-*.json"), reverse=True)[:n]:
        try:
            d = json.loads(f.read_text())
            changes.append(d)
        except Exception:
            pass
    return changes

# ─── HTML rendering ───────────────────────────────────────────────────────────

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #0d1117; color: #e6edf3; font-family: 'Segoe UI', system-ui, sans-serif; }
.header { background: linear-gradient(135deg, #161b22 0%, #1f2937 100%);
          border-bottom: 1px solid #30363d; padding: 20px 32px; display: flex;
          align-items: center; gap: 16px; }
.header h1 { font-size: 22px; font-weight: 700; color: #58a6ff; letter-spacing: 0.5px; }
.header .sub { font-size: 12px; color: #8b949e; margin-top: 2px; }
.badge { background: #1f6feb; color: #fff; border-radius: 6px; padding: 3px 10px;
         font-size: 11px; font-weight: 600; }
.badge.green { background: #238636; }
.badge.red { background: #b91c1c; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
        gap: 20px; padding: 24px 32px; }
.card { background: #161b22; border: 1px solid #30363d; border-radius: 10px;
        padding: 20px; }
.card.wide { grid-column: span 2; }
.card h2 { font-size: 13px; font-weight: 600; color: #8b949e; text-transform: uppercase;
           letter-spacing: 1px; margin-bottom: 16px; }
.stat-row { display: flex; justify-content: space-between; align-items: center;
            padding: 8px 0; border-bottom: 1px solid #21262d; }
.stat-row:last-child { border-bottom: none; }
.stat-label { color: #8b949e; font-size: 13px; }
.stat-value { font-size: 14px; font-weight: 600; color: #e6edf3; }
.stat-value.green { color: #3fb950; }
.stat-value.red { color: #f85149; }
.stat-value.yellow { color: #e3b341; }
.stat-value.blue { color: #58a6ff; }
.refresh { font-size: 11px; color: #8b949e; }
.chg-item { padding: 6px 0; border-bottom: 1px solid #21262d; font-size: 12px; }
.chg-item .chg-id { color: #58a6ff; font-weight: 600; }
.chg-item .chg-title { color: #c9d1d9; }
.sprint-bar-outer { background: #21262d; border-radius: 4px; height: 8px; margin: 8px 0 4px; }
.sprint-bar-inner { background: #238636; height: 8px; border-radius: 4px; transition: width 0.5s; }
.goal-item { font-size: 12px; color: #8b949e; padding: 3px 0; }
.goal-item.done { color: #3fb950; }
canvas { max-width: 100%; }
"""

def _card(title, inner_html, wide=False):
    cls = 'card wide' if wide else 'card'
    return f'<div class="{cls}"><h2>{title}</h2>{inner_html}</div>'

def _stat(label, value, color=""):
    cls = f" {color}" if color else ""
    return f'<div class="stat-row"><span class="stat-label">{label}</span><span class="stat-value{cls}">{value}</span></div>'

def generate(output_path: Path):
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    # ── collect data ──────────────────────────────────────────────────────────
    gs           = _load_gs()
    score, brkdwn= _health_score()
    vel_labels, vel_vals = _velocity_data()
    debt         = _debt_data()
    risk         = _risk_data()
    hotspots     = _hotspots()
    sprint       = _sprint()
    wf_counts    = _sessions_by_workflow()
    recent_chgs  = _recent_changes(8)

    inv = gs.get("inventory", {})
    ses_cnt  = inv.get("sessions", 0)
    chg_cnt  = inv.get("changes", 0)
    evd_cnt  = inv.get("evidences", 0)

    debt_h   = debt.get("total_hours", 0)
    debt_eur = debt.get("total_cost", 0)
    debt_items = debt.get("items", 0)

    risk_exp = risk.get("total_exposure", 0.0)
    risk_items = risk.get("items", 0)
    by_cat   = risk.get("by_category", {})

    score_color = "green" if score >= 90 else ("yellow" if score >= 70 else "red")

    # ── health gauge ──────────────────────────────────────────────────────────
    gauge_html = render_gauge(score, "Health Score", max_val=100)

    # ── velocity line chart ────────────────────────────────────────────────────
    vel_html = render_line(
        labels=vel_labels,
        datasets=[{"label": "Sesiones/semana", "data": vel_vals, "color": "#58a6ff"}],
        title="Velocidad — sesiones por semana (últimas 8 sem)",
    )

    # ── debt bar chart ─────────────────────────────────────────────────────────
    by_q = debt.get("by_quadrant", {})
    if by_q:
        debt_html = render_bar(
            labels=list(by_q.keys()),
            values=[v.get("hours", v) if isinstance(v, dict) else v for v in by_q.values()],
            title=f"Deuda técnica por cuadrante — {debt_h:.1f}h / €{int(debt_eur)}",
            color="#e3b341",
        )
    else:
        debt_html = f"<p style='color:#8b949e;font-size:13px'>Sin datos de deuda. Ejecuta: bago scan</p>"

    # ── risk doughnut ──────────────────────────────────────────────────────────
    risk_labels = list(by_cat.keys()) or ["Sin datos"]
    risk_vals   = [v.get("count", 0) if isinstance(v, dict) else 0 for v in by_cat.values()] or [0]
    risk_colors = ["#f85149","#e3b341","#58a6ff","#3fb950","#d29922"]
    risk_html   = render_doughnut(
        labels=risk_labels,
        values=risk_vals,
        title=f"Distribución riesgo — exposición {risk_exp:.1f}",
        colors=risk_colors[:len(risk_labels)],
    )

    # ── hotspots bar ──────────────────────────────────────────────────────────
    if hotspots:
        hs_labels = [Path(h.get("file","?")).name[:20] for h in hotspots]
        hs_scores = [h.get("score", 0) for h in hotspots]
        hs_html   = render_bar(
            labels=hs_labels,
            values=hs_scores,
            title="Top hotspots (score = commits × complejidad × LOC)",
            color="#e3b341",
            horizontal=True,
        )
    else:
        hs_html = "<p style='color:#8b949e;font-size:13px'>Sin hotspots detectados</p>"

    # ── workflow doughnut ─────────────────────────────────────────────────────
    wf_top = sorted(wf_counts.items(), key=lambda x: x[1], reverse=True)[:8]
    if wf_top:
        wf_html = render_doughnut(
            labels=[w for w,_ in wf_top],
            values=[c for _,c in wf_top],
            title="Sesiones por workflow",
            colors=["#58a6ff","#3fb950","#e3b341","#f85149","#d29922","#a371f7","#39d353","#ff7b72"],
        )
    else:
        wf_html = ""

    # ── sprint progress ────────────────────────────────────────────────────────
    sp_name  = sprint.get("name", sprint.get("sprint_id", "—"))[:50]
    sp_goals = sprint.get("goals", [])
    sp_total = len(sp_goals)
    sp_done  = sum(1 for g in sp_goals if (isinstance(g, str) and g.startswith("✅"))
                                       or (isinstance(g, dict) and g.get("status") == "done"))
    sp_pct   = int(sp_done / sp_total * 100) if sp_total else 0
    sp_goals_html = ""
    for g in sp_goals[:10]:
        gstr  = str(g)[:80]
        gclass = "done" if gstr.startswith("✅") else ""
        sp_goals_html += f'<div class="goal-item {gclass}">{gstr}</div>'
    sprint_html = f"""
<div style="font-size:14px;color:#58a6ff;margin-bottom:8px">{sp_name}</div>
<div style="font-size:12px;color:#8b949e">Progreso: {sp_done}/{sp_total} goals ({sp_pct}%)</div>
<div class="sprint-bar-outer"><div class="sprint-bar-inner" style="width:{sp_pct}%"></div></div>
{sp_goals_html}"""

    # ── recent changes ─────────────────────────────────────────────────────────
    chg_html = ""
    for chg in recent_chgs:
        cid   = chg.get("change_id","?")
        title = chg.get("title","")[:60]
        sev   = chg.get("severity","")
        chg_html += f'<div class="chg-item"><span class="chg-id">{cid}</span> <span class="badge" style="font-size:10px">{sev}</span> <div class="chg-title">{title}</div></div>'

    # ── inventory stats card ───────────────────────────────────────────────────
    inv_html = (
        _stat("Sesiones registradas", ses_cnt, "blue") +
        _stat("Cambios (CHGs)", chg_cnt, "blue") +
        _stat("Evidencias", evd_cnt) +
        _stat("Health Score", f"{score}/100", score_color) +
        _stat("Deuda técnica", f"{debt_h:.1f}h / €{int(debt_eur)}", "yellow" if debt_h > 0 else "green") +
        _stat("Ítems de deuda", debt_items) +
        _stat("Exposición riesgo", f"{risk_exp:.1f}", "red" if risk_exp > 50 else "green") +
        _stat("Ítems de riesgo", risk_items)
    )

    # ── assemble HTML ──────────────────────────────────────────────────────────
    cards = "\n".join([
        _card("📊 Inventario & KPIs", inv_html),
        _card("💚 Health Score", gauge_html),
        _card("🚀 Velocidad por Semana", vel_html),
        _card("💸 Deuda Técnica por Cuadrante", debt_html),
        _card("🔴 Distribución de Riesgo", risk_html),
        _card("📋 Sesiones por Workflow", wf_html),
        _card("🔥 Top Hotspots", hs_html),
        _card("🏃 Sprint Activo", sprint_html),
        _card("📝 Últimos Cambios Registrados", chg_html),
    ])

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="300">
<title>⚡ BAGO Metrics Dashboard</title>
<style>{CSS}</style>
</head>
<body>
<div class="header">
  <div>
    <h1>⚡ BAGO Metrics Dashboard</h1>
    <div class="sub">Pack: {BAGO_ROOT.name} &nbsp;·&nbsp; Actualizado: {now_str}
      &nbsp;·&nbsp; <span class="refresh">⟳ Auto-refresh cada 5 min</span>
    </div>
  </div>
  <span class="badge {'green' if score >= 90 else 'red'}">{score}/100</span>
  <span class="badge" style="background:#6e40c9">SPRINT-007</span>
</div>
<div class="grid">
{cards}
</div>
<script>
// Countdown to next refresh
(function() {{
  var secs = 300;
  setInterval(function() {{
    secs--;
    if (secs <= 0) {{ location.reload(); return; }}
    var el = document.querySelector('.refresh');
    if (el) el.textContent = '⟳ Refresco en ' + secs + 's';
  }}, 1000);
}})();
</script>
</body>
</html>"""

    output_path.write_text(html, encoding="utf-8")
    return output_path

# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="BAGO Metrics Dashboard HTML generator")
    p.add_argument("--out",   default=str(OUT_HTML), help="Output HTML file path")
    p.add_argument("--watch", type=int, default=0, metavar="SECS", help="Regenerar cada N segundos")
    p.add_argument("--open",  action="store_true", help="Abrir en browser después de generar")
    args = p.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            generated = generate(out_path)
            now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")
            print(f"[{now_str}] ✅  Dashboard generado → {generated}", flush=True)
        except Exception as e:
            print(f"[ERROR] {e}", flush=True)

        if args.open:
            import subprocess as _sp
            _sp.Popen(["open", str(out_path)])
            args.open = False  # solo abrir la primera vez

        if args.watch <= 0:
            break
        time.sleep(args.watch)

if __name__ == "__main__":
    main()
