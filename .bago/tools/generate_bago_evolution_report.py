#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import csv
import datetime as dt
import json
from collections import Counter, defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "analysis"
FIG_DIR = OUT_DIR / "figures"
MADRID = ZoneInfo("Europe/Madrid")
UTC = dt.timezone.utc


def parse_iso(ts: str) -> dt.datetime:
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return dt.datetime.fromisoformat(ts)


def fmt_local(ts: str) -> str:
    return parse_iso(ts).astimezone(MADRID).strftime("%Y-%m-%d %H:%M")


def fmt_utc(ts: str) -> str:
    return parse_iso(ts).astimezone(UTC).strftime("%Y-%m-%d %H:%M")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value: object) -> str:
    return (
        str(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def svg_template(title: str, width: int, height: int, body: str) -> str:
    return f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}' viewBox='0 0 {width} {height}'>
<style>
text {{ font-family: Menlo, Consolas, monospace; fill: #0f172a; }}
.axis {{ stroke: #64748b; stroke-width: 1; }}
.grid {{ stroke: #cbd5e1; stroke-width: 1; stroke-dasharray: 3 3; }}
.title {{ font-size: 17px; font-weight: 700; }}
.label {{ font-size: 11px; }}
.small {{ font-size: 10px; }}
</style>
<rect x='0' y='0' width='{width}' height='{height}' fill='#f8fafc'/>
<text x='20' y='26' class='title'>{esc(title)}</text>
{body}
</svg>
"""


def write_svg(path: Path, svg: str) -> None:
    path.write_text(svg, encoding="utf-8")


def simple_bar_chart(labels, values, title, y_label, out_path: Path, color="#2563eb") -> None:
    width, height = 980, 420
    left, right, top, bottom = 70, 30, 52, 80
    cw = width - left - right
    ch = height - top - bottom
    n = max(1, len(values))
    ymax = max(values) if values else 1
    ymax = ymax if ymax > 0 else 1
    bar_w = cw / n * 0.68
    step = cw / n
    body = []
    for i in range(6):
        yv = ymax * i / 5
        y = top + ch - (yv / ymax) * ch
        body.append(f"<line x1='{left}' y1='{y:.2f}' x2='{left+cw}' y2='{y:.2f}' class='grid' />")
        body.append(f"<text x='8' y='{y+4:.2f}' class='label'>{yv:.1f}</text>")
    for i, (label, value) in enumerate(zip(labels, values)):
        x = left + i * step + (step - bar_w) / 2
        h = (value / ymax) * ch if ymax else 0
        y = top + ch - h
        body.append(
            f"<rect x='{x:.2f}' y='{y:.2f}' width='{bar_w:.2f}' height='{h:.2f}' fill='{color}' rx='3'/>"
        )
        body.append(
            f"<text x='{x + bar_w/2:.2f}' y='{top+ch+16:.2f}' text-anchor='middle' class='label'>{esc(label)}</text>"
        )
        body.append(
            f"<text x='{x + bar_w/2:.2f}' y='{y-6:.2f}' text-anchor='middle' class='label'>{value:.1f}</text>"
        )
    body.extend(
        [
            f"<line x1='{left}' y1='{top+ch}' x2='{left+cw}' y2='{top+ch}' class='axis' />",
            f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top+ch}' class='axis' />",
            f"<text x='{width/2:.0f}' y='{height-12}' text-anchor='middle' class='label'>{esc(y_label)}</text>",
            f"<text x='14' y='{top-8}' class='label'>valor</text>",
        ]
    )
    write_svg(out_path, svg_template(title, width, height, "\n".join(body)))


def grouped_bar_chart(groups, categories, values, title, out_path: Path) -> None:
    width, height = 980, 440
    left, right, top, bottom = 80, 30, 55, 95
    cw = width - left - right
    ch = height - top - bottom
    max_total = max(sum(values[g].get(cat, 0) for cat in categories) for g in groups) if groups else 1
    max_total = max_total if max_total > 0 else 1
    group_w = cw / max(1, len(groups))
    bar_w = group_w * 0.55
    palette = ["#1d4ed8", "#0f766e", "#c2410c", "#7c3aed", "#b91c1c", "#0369a1"]
    body = []
    for i in range(6):
        yv = max_total * i / 5
        y = top + ch - (yv / max_total) * ch
        body.append(f"<line x1='{left}' y1='{y:.2f}' x2='{left+cw}' y2='{y:.2f}' class='grid' />")
        body.append(f"<text x='8' y='{y+4:.2f}' class='label'>{yv:.1f}</text>")

    for gi, group in enumerate(groups):
        x_center = left + gi * group_w + group_w / 2
        x = x_center - bar_w / 2
        y_cursor = top + ch
        total = sum(values[group].get(cat, 0) for cat in categories)
        for ci, cat in enumerate(categories):
            val = values[group].get(cat, 0)
            h = (val / max_total) * ch if max_total else 0
            y = y_cursor - h
            if val > 0:
                body.append(
                    f"<rect x='{x:.2f}' y='{y:.2f}' width='{bar_w:.2f}' height='{h:.2f}' fill='{palette[ci % len(palette)]}' rx='2'/>"
                )
            y_cursor = y
        body.append(
            f"<text x='{x_center:.2f}' y='{top+ch+16:.2f}' text-anchor='middle' class='label'>{esc(group)}</text>"
        )
        body.append(
            f"<text x='{x_center:.2f}' y='{top+ch+32:.2f}' text-anchor='middle' class='small'>{total}</text>"
        )

    legend_x = left
    legend_y = height - 30
    for ci, cat in enumerate(categories):
        x = legend_x + ci * 150
        body.append(f"<rect x='{x}' y='{legend_y-10}' width='12' height='12' fill='{palette[ci % len(palette)]}' rx='2'/>")
        body.append(f"<text x='{x+18}' y='{legend_y}' class='label'>{esc(cat)}</text>")

    body.extend(
        [
            f"<line x1='{left}' y1='{top+ch}' x2='{left+cw}' y2='{top+ch}' class='axis' />",
            f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top+ch}' class='axis' />",
            f"<text x='{width/2:.0f}' y='{height-12}' text-anchor='middle' class='label'>fase</text>",
        ]
    )
    write_svg(out_path, svg_template(title, width, height, "\n".join(body)))


def timeline_chart(clusters, title, out_path: Path) -> None:
    width, height = 1180, 420
    left, right, top, bottom = 145, 30, 55, 80
    cw = width - left - right
    ch = height - top - bottom
    t0 = min(c["start"] for c in clusters)
    t1 = max(c["end"] for c in clusters)
    span = (t1 - t0).total_seconds() or 1
    row_h = ch / max(1, len(clusters))
    body = []

    for i in range(6):
        frac = i / 5
        x = left + frac * cw
        body.append(f"<line x1='{x:.2f}' y1='{top}' x2='{x:.2f}' y2='{top+ch}' class='grid' />")
        tick_t = t0 + dt.timedelta(seconds=span * frac)
        body.append(
            f"<text x='{x:.2f}' y='{top+ch+18}' text-anchor='middle' class='small'>{tick_t.strftime('%d/%m %H:%M')}</text>"
        )

    for idx, c in enumerate(clusters):
        y = top + idx * row_h + row_h * 0.25
        h = row_h * 0.5
        x1 = left + ((c["start"] - t0).total_seconds() / span) * cw
        x2 = left + ((c["end"] - t0).total_seconds() / span) * cw
        body.append(f"<rect x='{x1:.2f}' y='{y:.2f}' width='{max(3, x2-x1):.2f}' height='{h:.2f}' fill='#0f766e' rx='4'/>")
        label = (
            f"{c['label']} | {c['run_count']} corridas | "
            f"{round(c['duration_s'],1)} s | {c['requests']} req"
        )
        body.append(f"<text x='{left-10}' y='{y + h*0.72:.2f}' text-anchor='end' class='label'>{esc(label)}</text>")
        body.append(
            f"<text x='{x1+4:.2f}' y='{y - 4:.2f}' class='small'>{c['start_local']}</text>"
        )

    body.extend(
        [
            f"<line x1='{left}' y1='{top+ch}' x2='{left+cw}' y2='{top+ch}' class='axis' />",
            f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top+ch}' class='axis' />",
            f"<text x='{width/2:.0f}' y='{height-12}' text-anchor='middle' class='label'>tiempo</text>",
        ]
    )
    write_svg(out_path, svg_template(title, width, height, "\n".join(body)))


def heatmap_chart(rows, cols, values, title, out_path: Path) -> None:
    width, height = 1180, 520
    left, right, top, bottom = 160, 40, 70, 90
    cw = width - left - right
    ch = height - top - bottom
    row_h = ch / max(1, len(rows))
    col_w = cw / max(1, len(cols))
    max_value = max((values.get(r, {}).get(c, 0) for r in rows for c in cols), default=1)
    max_value = max_value if max_value > 0 else 1
    body = []

    def fill_for(v: int) -> str:
        # Simple blue-green ramp without external dependencies.
        if v <= 0:
            return "#e2e8f0"
        ratio = v / max_value
        if ratio < 0.25:
            return "#c7f9cc"
        if ratio < 0.5:
            return "#86efac"
        if ratio < 0.75:
            return "#34d399"
        return "#0f766e"

    for i in range(6):
        frac = i / 5
        x = left + frac * cw
        body.append(f"<line x1='{x:.2f}' y1='{top}' x2='{x:.2f}' y2='{top+ch}' class='grid' />")
    for i, row in enumerate(rows):
        y = top + i * row_h
        body.append(f"<line x1='{left}' y1='{y:.2f}' x2='{left+cw}' y2='{y:.2f}' class='grid' />")
        body.append(f"<text x='{left-12}' y='{y + row_h*0.68:.2f}' text-anchor='end' class='label'>{esc(row)}</text>")
        for j, col in enumerate(cols):
            v = values.get(row, {}).get(col, 0)
            x = left + j * col_w
            fill = fill_for(v)
            body.append(
                f"<rect x='{x:.2f}' y='{y:.2f}' width='{col_w:.2f}' height='{row_h:.2f}' fill='{fill}' stroke='#ffffff' stroke-width='1'/>"
            )
            if v > 0:
                body.append(
                    f"<text x='{x + col_w/2:.2f}' y='{y + row_h/2 + 4:.2f}' text-anchor='middle' class='label'>{v}</text>"
                )
    for j, col in enumerate(cols):
        x = left + j * col_w + col_w / 2
        body.append(f"<text x='{x:.2f}' y='{top-10}' text-anchor='middle' class='small'>{esc(col)}</text>")

    body.extend(
        [
            f"<line x1='{left}' y1='{top+ch}' x2='{left+cw}' y2='{top+ch}' class='axis' />",
            f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top+ch}' class='axis' />",
            f"<text x='{width/2:.0f}' y='{height-12}' text-anchor='middle' class='label'>fecha local (Europe/Madrid)</text>",
        ]
    )
    write_svg(out_path, svg_template(title, width, height, "\n".join(body)))


def phase_task_mix_chart(early_counts, late_counts, title, out_path: Path) -> None:
    phases = ["inicio", "ahora"]
    categories = ["system_change", "project_bootstrap", "analysis", "repository_audit", "execution"]
    values = {
        "inicio": early_counts,
        "ahora": late_counts,
    }
    grouped_bar_chart(phases, categories, values, title, out_path)


def radar_chart(
    labels: list[str],
    values: list[float],
    title: str,
    out_path: Path,
    color: str = "#2563eb",
    max_val: float = 100.0,
) -> None:
    """Renders a radar/spider chart as SVG (pure Python, no external deps)."""
    import math

    n = len(labels)
    if n < 3:
        return

    width, height = 520, 480
    cx, cy = width // 2, height // 2 + 10
    r = min(cx, cy) - 70  # radius of the outermost ring

    body: list[str] = []

    # Draw concentric grid rings (5 levels)
    levels = 5
    for lvl in range(1, levels + 1):
        ring_r = r * lvl / levels
        points = []
        for i in range(n):
            angle = math.pi / 2 - 2 * math.pi * i / n
            px = cx + ring_r * math.cos(angle)
            py = cy - ring_r * math.sin(angle)
            points.append(f"{px:.1f},{py:.1f}")
        body.append(f"<polygon points='{' '.join(points)}' fill='none' stroke='#cbd5e1' stroke-width='1' stroke-dasharray='3 3'/>")
        # Label the % at the top axis
        top_angle = math.pi / 2
        lx = cx + ring_r * math.cos(top_angle)
        ly = cy - ring_r * math.sin(top_angle)
        body.append(f"<text x='{lx+4:.1f}' y='{ly:.1f}' class='small' fill='#94a3b8'>{int(lvl * max_val / levels)}</text>")

    # Draw axis lines from center to each vertex
    for i in range(n):
        angle = math.pi / 2 - 2 * math.pi * i / n
        px = cx + r * math.cos(angle)
        py = cy - r * math.sin(angle)
        body.append(f"<line x1='{cx}' y1='{cy}' x2='{px:.1f}' y2='{py:.1f}' class='axis'/>")

    # Draw data polygon
    data_points = []
    for i, val in enumerate(values):
        clipped = max(0.0, min(float(val), max_val))
        frac = clipped / max_val
        angle = math.pi / 2 - 2 * math.pi * i / n
        px = cx + r * frac * math.cos(angle)
        py = cy - r * frac * math.sin(angle)
        data_points.append(f"{px:.1f},{py:.1f}")
    hex_color = color
    body.append(f"<polygon points='{' '.join(data_points)}' fill='{hex_color}' fill-opacity='0.25' stroke='{hex_color}' stroke-width='2'/>")

    # Dots at data points
    for pt in data_points:
        px, py = pt.split(",")
        body.append(f"<circle cx='{px}' cy='{py}' r='4' fill='{hex_color}'/>")

    # Axis labels (outside the ring)
    for i, label in enumerate(labels):
        angle = math.pi / 2 - 2 * math.pi * i / n
        lx = cx + (r + 26) * math.cos(angle)
        ly = cy - (r + 26) * math.sin(angle)
        # Choose anchor based on position
        if abs(math.cos(angle)) < 0.15:
            anchor = "middle"
        elif math.cos(angle) > 0:
            anchor = "start"
        else:
            anchor = "end"
        val_str = f"{values[i]:.0f}%"
        body.append(f"<text x='{lx:.1f}' y='{ly:.1f}' text-anchor='{anchor}' class='label' font-weight='600'>{esc(label)}</text>")
        # Value label slightly inward
        vx = cx + (r + 44) * math.cos(angle)
        vy = cy - (r + 44) * math.sin(angle)
        body.append(f"<text x='{vx:.1f}' y='{vy+13:.1f}' text-anchor='{anchor}' class='small' fill='{hex_color}'>{val_str}</text>")

    write_svg(out_path, svg_template(title, width, height, "\n".join(body)))


def build_html_report(
    *,
    metrics_snapshot: dict,
    current_state: dict,
    start_corpus: int,
    current_corpus: int,
    today_local: dt.date,
    state_ref_day: dt.date,
    today_session_count: int,
    today_change_count: int,
    today_evidence_count: int,
    today_run_count: int,
    today_request_count: int,
    early_counts: Counter,
    late_counts: Counter,
    cluster_rows: list[dict],
    task_types: list[str],
    all_days: list[str],
    task_values: dict,
    radar_labels: list[str] | None = None,
    radar_values: list[float] | None = None,
    changes: list | None = None,
    sessions: list | None = None,
) -> str:
    def card(title: str, value: str, subtitle: str = "") -> str:
        return f"""
        <div class="card">
          <div class="card-title">{esc(title)}</div>
          <div class="card-value">{esc(value)}</div>
          <div class="card-subtitle">{esc(subtitle)}</div>
        </div>
        """

    def counts_for_phase(counter: Counter) -> str:
        parts = [f"{k}: {counter.get(k, 0)}" for k in ["system_change", "project_bootstrap", "analysis", "repository_audit", "execution"]]
        return " | ".join(parts)

    rows = "".join(
        f"<tr><td>{esc(row)}</td>" + "".join(
            f"<td>{task_values.get(row, {}).get(task, 0)}</td>" for task in task_types
        ) + "</tr>"
        for row in all_days
    )

    cluster_rows_html = "".join(
        f"<tr><td>{esc(c['label'])}</td><td>{c['start'].astimezone(MADRID).strftime('%d/%m %H:%M')}</td>"
        f"<td>{c['end'].astimezone(MADRID).strftime('%d/%m %H:%M')}</td>"
        f"<td>{c['duration_s']:.3f}s</td><td>{c['requests']}</td><td>{c['run_count']}</td></tr>"
        for c in cluster_rows
    )

    obs_html = build_dynamic_html_observations(
        current_state, changes or [], sessions or [], state_ref_day
    )

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Evolución del sistema BAGO</title>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: #111827;
      --card: #1e293b;
      --text: #e2e8f0;
      --muted: #94a3b8;
      --accent: #22c55e;
      --accent2: #38bdf8;
      --line: #334155;
    }}
    body {{
      margin: 0;
      font-family: Inter, system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: linear-gradient(180deg, #0b1120 0%, #111827 100%);
      color: var(--text);
    }}
    .wrap {{ max-width: 1200px; margin: 0 auto; padding: 32px 20px 56px; }}
    h1, h2, h3 {{ margin: 0 0 12px; line-height: 1.15; }}
    h1 {{ font-size: 2.2rem; }}
    h2 {{ margin-top: 38px; font-size: 1.35rem; }}
    p, li, td {{ color: var(--text); line-height: 1.55; }}
    .muted {{ color: var(--muted); }}
    .grid {{ display: grid; gap: 14px; }}
    .cards {{ grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin: 18px 0 10px; }}
    .card {{
      background: rgba(30, 41, 59, 0.8);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
      box-shadow: 0 10px 25px rgba(0,0,0,.18);
    }}
    .card-title {{ color: var(--muted); font-size: .82rem; text-transform: uppercase; letter-spacing: .06em; }}
    .card-value {{ font-size: 1.35rem; font-weight: 700; margin-top: 8px; }}
    .card-subtitle {{ color: var(--muted); margin-top: 6px; font-size: .92rem; }}
    .panel {{
      background: rgba(17, 24, 39, 0.9);
      border: 1px solid var(--line);
      border-radius: 20px;
      padding: 20px;
      box-shadow: 0 16px 32px rgba(0,0,0,.22);
      margin-top: 20px;
    }}
    img.svg {{
      width: 100%;
      height: auto;
      display: block;
      background: #f8fafc;
      border-radius: 14px;
      border: 1px solid #cbd5e1;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 12px;
      font-size: .95rem;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 10px 8px;
      text-align: left;
      vertical-align: top;
    }}
    th {{ color: var(--accent2); font-weight: 600; }}
    code, pre {{
      background: #0b1220;
      border: 1px solid var(--line);
      border-radius: 12px;
      color: #dbeafe;
    }}
    pre {{
      padding: 14px;
      overflow: auto;
    }}
    .two-col {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 14px;
    }}
    .box {{
      background: rgba(30, 41, 59, 0.55);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 16px;
    }}
    .diagram-title {{ color: var(--accent2); margin-bottom: 10px; }}
  </style>
</head>
<body>
  <div class="wrap">
    <h1>Evolución del sistema BAGO</h1>
    <p class="muted">Comparación entre el arranque de corrección/migración y el estado actual operativo. Generado desde `state/` y `state/metrics/runs/`.</p>

    <div class="grid cards">
      {card("Corpus inicial", f"{start_corpus} artefactos", f"Snapshot base {metrics_snapshot['captured_at']}")}
      {card("Corpus actual", f"{current_corpus} artefactos", f"Inventario visible: {current_state['inventory']['sessions']} sesiones, {current_state['inventory']['changes']} cambios, {current_state['inventory']['evidences']} evidencias")}
      {card("Integridad", f"{current_state['last_validation']['pack']} / {current_state['last_validation']['state']} / {current_state['last_validation']['manifest']}", "Validación más reciente")}
      {card("Última sesión", current_state["last_completed_session_id"], current_state["last_completed_workflow"] or "sin workflow")}
    </div>

    <div class="panel">
      <h2>Lectura ejecutiva</h2>
      <div class="two-col">
        <div class="box">
          <h3 class="diagram-title">Al principio</h3>
          <p>BAGO se enfocaba en <code>system_change</code>, preservación canónica, migración histórica y validación documental. La variedad funcional era baja y el trabajo era esencialmente de consolidación.</p>
          <p class="muted">{counts_for_phase(early_counts)}</p>
        </div>
        <div class="box">
          <h3 class="diagram-title">Ahora</h3>
          <p>El sistema trabaja de forma más madura: bootstrap del repo, análisis, auditoría, ejecución y cierre de ciclos con evidencias y estado vivo actualizado.</p>
          <p class="muted">{counts_for_phase(late_counts)}</p>
        </div>
      </div>
    </div>

    <div class="panel">
      <h2>Métricas de hoy</h2>
      <div class="grid cards" style="margin-top: 10px;">
        {card("Hoy local", today_local.strftime("%d/%m/%Y"), "reloj del entorno de trabajo")}
        {card("Sesiones de hoy", str(today_session_count), "sin actividad si vale 0")}
        {card("Cambios de hoy", str(today_change_count), "sin actividad si vale 0")}
        {card("Evidencias de hoy", str(today_evidence_count), "sin actividad si vale 0")}
        {card("Corridas autónomas", str(today_run_count), "ventanas de metrics/runs")}
        {card("Solicitudes hoy", str(today_request_count), "total en corridas que tocan hoy")}
      </div>
      <p class="muted">Si la cifra es 0, no hay registros fechados hoy en el reloj local del entorno.</p>
    </div>

    <div class="panel">
      <h2>Actividad diaria</h2>
      <img class="svg" src="figures/activity_by_day.svg" alt="Actividad diaria" />
    </div>

    <div class="panel">
      <h2>Radar de salud BAGO</h2>
      <img class="svg" src="figures/health_radar.svg" alt="Radar de salud del sistema" />
    </div>

    <div class="panel">
      <h2>Mezcla de trabajo por fase</h2>
      <img class="svg" src="figures/session_mix_by_phase.svg" alt="Mezcla de trabajo por fase" />
      <table>
        <thead><tr><th>Fase</th><th>system_change</th><th>project_bootstrap</th><th>analysis</th><th>repository_audit</th><th>execution</th><th>Total</th></tr></thead>
        <tbody>
          <tr><td>Inicio</td><td>{early_counts.get("system_change", 0)}</td><td>{early_counts.get("project_bootstrap", 0)}</td><td>{early_counts.get("analysis", 0)}</td><td>{early_counts.get("repository_audit", 0)}</td><td>{early_counts.get("execution", 0)}</td><td>{sum(early_counts.values())}</td></tr>
          <tr><td>Ahora</td><td>{late_counts.get("system_change", 0)}</td><td>{late_counts.get("project_bootstrap", 0)}</td><td>{late_counts.get("analysis", 0)}</td><td>{late_counts.get("repository_audit", 0)}</td><td>{late_counts.get("execution", 0)}</td><td>{sum(late_counts.values())}</td></tr>
        </tbody>
      </table>
    </div>

    <div class="panel">
      <h2>Evolución de tipos de trabajo</h2>
      <img class="svg" src="figures/task_type_evolution.svg" alt="Evolución de tipos de trabajo por día" />
      <table>
        <thead><tr><th>Día</th>{''.join(f'<th>{esc(t)}</th>' for t in task_types)}</tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>

    <div class="panel">
      <h2>Crecimiento del corpus</h2>
      <img class="svg" src="figures/corpus_growth.svg" alt="Crecimiento del corpus" />
    </div>

    <div class="panel">
      <h2>Ventanas de trabajo autónomo</h2>
      <img class="svg" src="figures/runs_clusters.svg" alt="Ventanas de trabajo autónomo" />
      <table>
        <thead><tr><th>Bloque</th><th>Inicio local</th><th>Fin local</th><th>Duración activa</th><th>Solicitudes</th><th>Corridas</th></tr></thead>
        <tbody>{cluster_rows_html}</tbody>
      </table>
    </div>

    <div class="panel">
      <h2>Diagramas</h2>
      <div class="two-col">
        <div class="box">
          <h3 class="diagram-title">Evolución funcional</h3>
          <pre>flowchart LR
  A["Corrección y migración"] --&gt; B["Endurecimiento estructural"]
  B --&gt; C["Performance y release"]
  C --&gt; D["Bootstrap repo-first"]
  D --&gt; E["Evaluación y reconstrucción"]
  E --&gt; F["Operación estable"]</pre>
        </div>
        <div class="box">
          <h3 class="diagram-title">Ciclo autónomo</h3>
          <pre>stateDiagram-v2
  [*] --&gt; Session
  Session --&gt; Change
  Change --&gt; Evidence
  Evidence --&gt; GlobalState
  GlobalState --&gt; NextSession
  NextSession --&gt; Session</pre>
        </div>
      </div>
    </div>

    <div class="panel">
      <h2>Observaciones técnicas</h2>
{obs_html}
    </div>
  </div>
</body>
</html>
"""


def counts_by_day(records, ts_field: str, tz: ZoneInfo):
    counts = defaultdict(int)
    for r in records:
        ts = parse_iso(r[ts_field]).astimezone(tz).date().isoformat()
        counts[ts] += 1
    return dict(sorted(counts.items()))


def collect_json_records(folder: Path):
    return [load_json(p) for p in sorted(folder.glob("*.json"))]


def build_dynamic_observations(
    current_state: dict,
    changes: list,
    sessions: list,
    state_ref_day,
) -> str:
    """Generate dynamic observation bullets from real system metrics."""
    inv     = current_state.get("inventory", {})
    health  = current_state.get("system_health", "unknown")
    n_chgs  = inv.get("changes", len(changes))
    n_sess  = inv.get("sessions", len(sessions))
    n_evid  = inv.get("evidences", 0)
    version = current_state.get("bago_version", "?")

    # smoke report
    smoke_path = ROOT.parent / "sandbox" / "runtime" / "last-report.json"
    smoke_status, smoke_workers = "desconocido", 0
    if smoke_path.exists():
        try:
            s = json.loads(smoke_path.read_text())
            smoke_status  = s.get("status", "desconocido")
            smoke_workers = s.get("workers", 0)
        except Exception:
            pass

    # Recent CHGs (last 5)
    chg_titles = []
    for c in sorted(changes, key=lambda x: x.get("created_at", ""), reverse=True)[:5]:
        t = c.get("title", "")
        if t:
            chg_titles.append(f"  - {t[:70]}")

    bullets = [
        f"- **Snapshot:** {state_ref_day.strftime('%d/%m/%Y')} · versión {version} · estado del sistema: `{health}`.",
        f"- **Corpus total:** {n_sess} sesiones · {n_chgs} cambios · {n_evid} evidencias.",
        f"- **Suite de tests:** `{smoke_status}` · {smoke_workers} workers registrados.",
    ]
    if chg_titles:
        bullets.append("- **Últimos cambios aplicados:**")
        bullets.extend(chg_titles)
    else:
        bullets.append("- Sin cambios recientes registrados.")

    bullets.append(
        "- La evolución del sistema es de especialización progresiva: "
        "cada sprint aumenta la capacidad de auto-gobernanza y cierre de ciclos con evidencias."
    )
    return "\n".join(bullets)


def build_dynamic_html_observations(
    current_state: dict,
    changes: list,
    sessions: list,
    state_ref_day,
) -> str:
    """Generate HTML observation list from real system metrics."""
    inv     = current_state.get("inventory", {})
    health  = current_state.get("system_health", "unknown")
    n_chgs  = inv.get("changes", len(changes))
    n_sess  = inv.get("sessions", len(sessions))
    n_evid  = inv.get("evidences", 0)
    version = current_state.get("bago_version", "?")

    smoke_path = ROOT.parent / "sandbox" / "runtime" / "last-report.json"
    smoke_status, smoke_workers = "desconocido", 0
    if smoke_path.exists():
        try:
            s = json.loads(smoke_path.read_text())
            smoke_status  = s.get("status", "desconocido")
            smoke_workers = s.get("workers", 0)
        except Exception:
            pass

    items = [
        f"Snapshot: {state_ref_day.strftime('%d/%m/%Y')} · versión {version} · estado: <strong>{health}</strong>.",
        f"Corpus: {n_sess} sesiones · {n_chgs} cambios · {n_evid} evidencias.",
        f"Suite de tests: <code>{smoke_status}</code> · {smoke_workers} workers.",
    ]
    for c in sorted(changes, key=lambda x: x.get("created_at", ""), reverse=True)[:3]:
        t = c.get("title", "")
        if t:
            items.append(f"CHG reciente: {t[:70]}")

    items.append(
        "La evolución es de especialización progresiva: "
        "cada sprint aumenta la capacidad de auto-gobernanza y cierre de ciclos."
    )
    li_items = "".join(f"      <li>{i}</li>\n" for i in items)
    return f"      <ul>\n{li_items}      </ul>"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    metrics_snapshot = load_json(ROOT / "state" / "metrics" / "metrics_snapshot.json")
    current_state = load_json(ROOT / "state" / "global_state.json")

    sessions = collect_json_records(ROOT / "state" / "sessions")
    changes = collect_json_records(ROOT / "state" / "changes")
    evidences = collect_json_records(ROOT / "state" / "evidences")
    run_summaries = [load_json(p) for p in sorted((ROOT / "state" / "metrics" / "runs").glob("*/summary.json"))]
    today_local = dt.date.today()
    state_ref_day = parse_iso(current_state["updated_at"]).astimezone(MADRID).date()

    # Comparative corpus metrics.
    start_corpus = (
        metrics_snapshot["native_sessions_completed"]
        + metrics_snapshot["migrated_sessions_count"]
        + metrics_snapshot["migrated_changes_count"]
        + metrics_snapshot["validated_changes"]
    )
    current_corpus = (
        current_state["inventory"]["sessions"]
        + current_state["inventory"]["changes"]
        + current_state["inventory"]["evidences"]
    )

    # Daily activity by Europe/Madrid local day.
    session_days = counts_by_day(sessions, "created_at", MADRID)
    change_days = counts_by_day(changes, "created_at", MADRID)
    evidence_days = counts_by_day(evidences, "recorded_at", MADRID)
    task_types = ["analysis", "design", "execution", "validation", "organization", "system_change", "project_bootstrap", "repository_audit", "history_migration"]
    all_days = sorted(set(session_days) | set(change_days) | set(evidence_days))
    task_values = {
        day: {task: 0 for task in task_types}
        for day in all_days
    }
    for session in sessions:
        day = parse_iso(session["created_at"]).astimezone(MADRID).date().isoformat()
        if day in task_values:
            task = session.get("task_type", "unknown")
            if task not in task_values[day]:
                task_values[day][task] = 0
            task_values[day][task] += 1
    day_values = {
        day: {
            "sessions": session_days.get(day, 0),
            "changes": change_days.get(day, 0),
            "evidences": evidence_days.get(day, 0),
        }
        for day in all_days
    }
    # Build grouped bar chart as three stacked categories per day.
    # We render it as stacked bars for readability.
    width, height = 1180, 440
    left, right, top, bottom = 80, 30, 55, 100
    cw = width - left - right
    ch = height - top - bottom
    max_total = max(sum(v.values()) for v in day_values.values()) if day_values else 1
    max_total = max_total if max_total > 0 else 1
    day_step = cw / max(1, len(all_days))
    bar_w = day_step * 0.56
    palette = {"sessions": "#1d4ed8", "changes": "#0f766e", "evidences": "#c2410c"}
    body = []
    for i in range(6):
        yv = max_total * i / 5
        y = top + ch - (yv / max_total) * ch
        body.append(f"<line x1='{left}' y1='{y:.2f}' x2='{left+cw}' y2='{y:.2f}' class='grid' />")
        body.append(f"<text x='8' y='{y+4:.2f}' class='label'>{yv:.1f}</text>")
    for i, day in enumerate(all_days):
        x = left + i * day_step + (day_step - bar_w) / 2
        y_cursor = top + ch
        total = 0
        for cat in ("sessions", "changes", "evidences"):
            val = day_values[day][cat]
            total += val
            h = (val / max_total) * ch if max_total else 0
            y = y_cursor - h
            if val > 0:
                body.append(
                    f"<rect x='{x:.2f}' y='{y:.2f}' width='{bar_w:.2f}' height='{h:.2f}' fill='{palette[cat]}' rx='2'/>"
                )
            y_cursor = y
        body.append(f"<text x='{x + bar_w/2:.2f}' y='{top+ch+16:.2f}' text-anchor='middle' class='label'>{day}</text>")
        body.append(f"<text x='{x + bar_w/2:.2f}' y='{top+ch+31:.2f}' text-anchor='middle' class='small'>{total}</text>")
    body.extend(
        [
            f"<rect x='{left}' y='{height-32}' width='12' height='12' fill='{palette['sessions']}' rx='2'/>",
            f"<text x='{left+18}' y='{height-22}' class='label'>sessions</text>",
            f"<rect x='{left+120}' y='{height-32}' width='12' height='12' fill='{palette['changes']}' rx='2'/>",
            f"<text x='{left+138}' y='{height-22}' class='label'>changes</text>",
            f"<rect x='{left+240}' y='{height-32}' width='12' height='12' fill='{palette['evidences']}' rx='2'/>",
            f"<text x='{left+258}' y='{height-22}' class='label'>evidences</text>",
            f"<line x1='{left}' y1='{top+ch}' x2='{left+cw}' y2='{top+ch}' class='axis' />",
            f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top+ch}' class='axis' />",
            f"<text x='{width/2:.0f}' y='{height-12}' text-anchor='middle' class='label'>fecha local (Europe/Madrid)</text>",
        ]
    )
    write_svg(FIG_DIR / "activity_by_day.svg", svg_template("Actividad diaria del sistema", width, height, "\n".join(body)))

    today_session_count = sum(1 for s in sessions if parse_iso(s["created_at"]).astimezone(MADRID).date() == today_local)
    today_change_count = sum(1 for c in changes if parse_iso(c["created_at"]).astimezone(MADRID).date() == today_local)
    today_evidence_count = sum(1 for e in evidences if parse_iso(e["recorded_at"]).astimezone(MADRID).date() == today_local)
    today_run_summaries = []
    for item in run_summaries:
        start = parse_iso(item["started_at_utc"]).astimezone(MADRID)
        end = parse_iso(item["ended_at_utc"]).astimezone(MADRID)
        if start.date() == today_local or end.date() == today_local:
            today_run_summaries.append(item)

    # Session type mix by phase.
    early_sessions = [s for s in sessions if parse_iso(s["created_at"]) < dt.datetime(2026, 4, 14, tzinfo=UTC)]
    late_sessions = [s for s in sessions if parse_iso(s["created_at"]) >= dt.datetime(2026, 4, 14, tzinfo=UTC)]
    early_counts = Counter(s["task_type"] for s in early_sessions)
    late_counts = Counter(s["task_type"] for s in late_sessions)
    grouped_bar_chart(
        ["inicio", "ahora"],
        ["system_change", "project_bootstrap", "analysis", "repository_audit", "execution"],
        {"inicio": early_counts, "ahora": late_counts},
        "Cambio de mezcla de trabajo por fase",
        FIG_DIR / "session_mix_by_phase.svg",
    )

    heatmap_chart(
        all_days,
        task_types,
        task_values,
        "Evolución de tipos de trabajo por día",
        FIG_DIR / "task_type_evolution.svg",
    )

    # Corpus growth chart.
    simple_bar_chart(
        ["inicio", "ahora"],
        [start_corpus, current_corpus],
        "Crecimiento del corpus estructurado",
        "artifacts registrados",
        FIG_DIR / "corpus_growth.svg",
        color="#7c3aed",
    )

    # Health radar chart — derived from global_state and smoke report.
    smoke_report_path = ROOT / "sandbox" / "runtime" / "last-report.json"
    smoke_data: dict = {}
    if smoke_report_path.exists():
        try:
            smoke_data = load_json(smoke_report_path)
        except Exception:
            pass
    _test_suite = str(current_state.get("integration_suite", "0/0"))
    _parts = _test_suite.split("/")
    _passed = int(_parts[0]) if _parts and _parts[0].isdigit() else 0
    _total = int(_parts[1]) if len(_parts) > 1 and _parts[1].isdigit() else max(1, _passed)
    test_score = round(100.0 * _passed / _total) if _total else 0

    changes_total = int(current_state.get("changes", 0))
    changes_score = min(100, round(changes_total / 1.2))  # 120 changes → 100%

    sessions_total = int(current_state.get("inventory", {}).get("sessions", 0))
    sessions_score = min(100, round(sessions_total / 0.6))  # 60 sessions → 100%

    tools_total = len(list((ROOT / "tools").glob("*.py"))) if (ROOT / "tools").is_dir() else 0
    tools_score = min(100, round(tools_total / 1.5))  # 150 tools → 100%

    _smoke_ok = smoke_data.get("status", "fail") in ("pass", "ok", "green", "success") and smoke_data.get("failure_count", 1) == 0
    smoke_score = 100 if _smoke_ok else 0

    evidences_total = int(current_state.get("inventory", {}).get("evidences", 0))
    evidences_score = min(100, round(evidences_total / 0.5))  # 50 evidences → 100%

    radar_labels = ["Tests", "CHGs", "Sesiones", "Tools", "Smoke", "Evidencias"]
    radar_values = [float(test_score), float(changes_score), float(sessions_score), float(tools_score), float(smoke_score), float(evidences_score)]
    radar_chart(
        radar_labels,
        radar_values,
        "Radar de salud BAGO",
        FIG_DIR / "health_radar.svg",
        color="#0f766e",
    )

    # Runs clusters.
    runs = []
    for item in run_summaries:
        start = parse_iso(item["started_at_utc"])
        end = parse_iso(item["ended_at_utc"])
        runs.append(
            {
                "start": start,
                "end": end,
                "duration_s": float(item["duration_s"]),
                "requests": int(item["total_requests"]),
                "simulate": bool(item.get("simulate")),
                "name": item["model"],
                "run_dir": Path(item.get("run_dir", "")).name if item.get("run_dir") else "",
            }
        )
    runs.sort(key=lambda r: r["start"])
    clusters = []
    current = []
    for run in runs:
        if not current:
            current = [run]
            continue
        gap = (run["start"] - current[-1]["end"]).total_seconds()
        if gap <= 1200:
            current.append(run)
        else:
            clusters.append(current)
            current = [run]
    if current:
        clusters.append(current)
    cluster_rows = []
    for idx, cluster in enumerate(clusters, 1):
        cluster_rows.append(
            {
                "label": f"bloque {idx}",
                "run_count": len(cluster),
                "start": cluster[0]["start"],
                "end": cluster[-1]["end"],
                "start_local": cluster[0]["start"].astimezone(MADRID).strftime("%d/%m %H:%M"),
                "duration_s": sum(r["duration_s"] for r in cluster),
                "requests": sum(r["requests"] for r in cluster),
            }
        )
    timeline_chart(cluster_rows, "Ventanas de trabajo autónomo en metrics/runs", FIG_DIR / "runs_clusters.svg")

    # Session counts by type for the report.
    session_type_counts = Counter(s["task_type"] for s in sessions)
    phase_role_early = sorted({r for s in early_sessions for r in s.get("roles_activated", [])})
    phase_role_late = sorted({r for s in late_sessions for r in s.get("roles_activated", [])})

    report_path = OUT_DIR / "BAGO_EVOLUCION_SISTEMA.md"
    report = f"""# Evolución del sistema BAGO

Este informe compara la fase inicial de corrección y migración con el estado operativo actual del repositorio.

## Fuentes

- [state/metrics/metrics_snapshot.json](/Users/INTELIA_Manager/Documents/INTELIA_Manager_2026/Contabilidad/TPV_Contabilidad%202/.bago/state/metrics/metrics_snapshot.json)
- [state/global_state.json](/Users/INTELIA_Manager/Documents/INTELIA_Manager_2026/Contabilidad/TPV_Contabilidad%202/.bago/state/global_state.json)
- [state/sessions/](/Users/INTELIA_Manager/Documents/INTELIA_Manager_2026/Contabilidad/TPV_Contabilidad%202/.bago/state/sessions)
- [state/changes/](/Users/INTELIA_Manager/Documents/INTELIA_Manager_2026/Contabilidad/TPV_Contabilidad%202/.bago/state/changes)
- [state/evidences/](/Users/INTELIA_Manager/Documents/INTELIA_Manager_2026/Contabilidad/TPV_Contabilidad%202/.bago/state/evidences)
- [state/metrics/runs/](/Users/INTELIA_Manager/Documents/INTELIA_Manager_2026/Contabilidad/TPV_Contabilidad%202/.bago/state/metrics/runs)

## Lectura ejecutiva

Al principio, BAGO trabajaba como un sistema de corrección y preservación canónica:

- centrado en `system_change`,
- con roles amplios y generales,
- con prioridad en migración, validación y consolidación documental,
- y con poca variedad de tipos de tarea.

Ahora trabaja como un sistema operativo más maduro:

- tiene `project_bootstrap`, `analysis`, `repository_audit` y `execution` además de `system_change`,
- separa mejor los roles por función,
- conserva trazabilidad de cambio, evidencia y estado,
- y ejecuta corridas autónomas de stress con ventanas temporales medibles.

## Métricas comparativas

| Métrica | Inicio | Ahora |
| --- | ---:| ---:|
| Snapshot documental mínimo | {start_corpus} artefactos | {current_corpus} artefactos |
| Sesiones nativas visibles | {metrics_snapshot["native_sessions_completed"]} | {current_state["inventory"]["sessions"]} |
| Sesiones migradas preservadas | {metrics_snapshot["migrated_sessions_count"]} | 4 preservadas en `state/migrated_sessions/` |
| Cambios migrados/validados | {metrics_snapshot["migrated_changes_count"] + metrics_snapshot["validated_changes"]} | {current_state["inventory"]["changes"]} |
| Evidencias registradas | no consolidado en snapshot inicial | {current_state["inventory"]["evidences"]} |
| Integridad del pack | {metrics_snapshot["pack_integrity_last_check"].upper()} | {current_state["last_validation"]["pack"]} / {current_state["last_validation"]["state"]} / {current_state["last_validation"]["manifest"]} |

## Métricas de hoy

Hoy local: **{today_local.strftime("%d/%m/%Y")}**.

| Métrica | Valor |
| --- | ---: |
| Sesiones de hoy | {today_session_count} |
| Cambios de hoy | {today_change_count} |
| Evidencias de hoy | {today_evidence_count} |
| Corridas autónomas de hoy | {len(today_run_summaries)} |
| Solicitudes de hoy en `metrics/runs` | {sum(int(r.get("total_requests", 0)) for r in today_run_summaries)} |

Si hoy no aparece actividad, significa que el árbol visible no contiene registros fechados en el día local del entorno.

## Cómo trabajaba al principio

Rango base del arranque: **11/04/2026**.

- La sesión dominante era `system_change`.
- El trabajo giraba alrededor de corrección del pack, migración histórica y oficialización canónica.
- La mezcla de roles era más generalista:
  - `{", ".join(phase_role_early) if phase_role_early else "n/a"}`
- La actividad se concentró en pocas ventanas de alta densidad documental.

## Cómo trabaja ahora

Rango visible del estado actual: **14/04/2026-15/04/2026** en el árbol local, con `global_state.json` actualizado al **17/04/2026 19:35 UTC**.

- La sesión incluye tareas más especializadas.
- La mezcla de trabajo se diversifica:
  - `{", ".join(phase_role_late) if phase_role_late else "n/a"}`
- El sistema ya no solo corrige canon:
  - arranca repo,
  - audita,
  - ejecuta,
  - evalúa,
  - reconstruye,
  - y consolida.

## Actividad por día

![Actividad diaria](figures/activity_by_day.svg)

## Cambio de mezcla de trabajo

![Mezcla por fase](figures/session_mix_by_phase.svg)

| Fase | system_change | project_bootstrap | analysis | repository_audit | execution | Total |
| --- | ---:| ---:| ---:| ---:| ---:| ---:|
| Inicio | {early_counts.get("system_change", 0)} | {early_counts.get("project_bootstrap", 0)} | {early_counts.get("analysis", 0)} | {early_counts.get("repository_audit", 0)} | {early_counts.get("execution", 0)} | {sum(early_counts.values())} |
| Ahora | {late_counts.get("system_change", 0)} | {late_counts.get("project_bootstrap", 0)} | {late_counts.get("analysis", 0)} | {late_counts.get("repository_audit", 0)} | {late_counts.get("execution", 0)} | {sum(late_counts.values())} |

## Evolución de tipos de trabajo

![Tipos de trabajo por día](figures/task_type_evolution.svg)

## Crecimiento del corpus

![Crecimiento del corpus](figures/corpus_growth.svg)

## Ventanas de trabajo autónomo

Las corridas de `state/metrics/runs/` sí traen duración real y permiten medir trabajo autónomo continuo.

![Ventanas autónomas](figures/runs_clusters.svg)

| Bloque | Inicio local | Fin local | Duración activa | Solicitudes | Corridas |
| --- | --- | --- | ---:| ---:| ---:|
"""
    for cluster in cluster_rows:
        report += f"| {cluster['label']} | {cluster['start'].astimezone(MADRID).strftime('%d/%m %H:%M')} | {cluster['end'].astimezone(MADRID).strftime('%d/%m %H:%M')} | {cluster['duration_s']:.3f}s | {cluster['requests']} | {cluster['run_count']} |\n"
    report += """

## Diagramas

### Evolución funcional

```mermaid
flowchart LR
  A["Corrección y migración"] --> B["Endurecimiento estructural"]
  B --> C["Performance y release"]
  C --> D["Bootstrap repo-first"]
  D --> E["Evaluación y reconstrucción"]
  E --> F["Operación estable"]
```

### Ciclo autónomo

```mermaid
stateDiagram-v2
  [*] --> Session
  Session --> Change
  Change --> Evidence
  Evidence --> GlobalState
  GlobalState --> NextSession
  NextSession --> Session
```

## Observaciones

"""
    report += build_dynamic_observations(current_state, changes, sessions, state_ref_day) + "\n"
    report_path.write_text(report, encoding="utf-8")

    html_path = OUT_DIR / "BAGO_EVOLUCION_SISTEMA.html"
    html_path.write_text(build_html_report(
        metrics_snapshot=metrics_snapshot,
        current_state=current_state,
        start_corpus=start_corpus,
        current_corpus=current_corpus,
        today_local=today_local,
        state_ref_day=state_ref_day,
        today_session_count=today_session_count,
        today_change_count=today_change_count,
        today_evidence_count=today_evidence_count,
        today_run_count=len(today_run_summaries),
        today_request_count=sum(int(r.get("total_requests", 0)) for r in today_run_summaries),
        early_counts=early_counts,
        late_counts=late_counts,
        cluster_rows=cluster_rows,
        task_types=task_types,
        all_days=all_days,
        task_values=task_values,
        radar_labels=radar_labels,
        radar_values=radar_values,
        changes=changes,
        sessions=sessions,
    ), encoding="utf-8")

    print(f"OK {report_path}")
    print(f"OK {html_path}")
    print(f"OK {FIG_DIR / 'activity_by_day.svg'}")
    print(f"OK {FIG_DIR / 'session_mix_by_phase.svg'}")
    print(f"OK {FIG_DIR / 'task_type_evolution.svg'}")
    print(f"OK {FIG_DIR / 'corpus_growth.svg'}")
    print(f"OK {FIG_DIR / 'runs_clusters.svg'}")
    print(f"OK {FIG_DIR / 'health_radar.svg'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
