#!/usr/bin/env python3
"""chart_engine.py — Herramienta #112: Motor de gráficas interactivas con Chart.js.

Genera snippets HTML auto-contenidos con gráficas interactivas (Chart.js 4.4, CDN).
Funciones de importación directa para otros tools BAGO:

    from chart_engine import render_gauge, render_bar, render_line
    from chart_engine import render_doughnut, render_heatmap

Cada función retorna un bloque <div>+<canvas>+<script> listo para embeber.
No requiere paquetes Python externos — sólo stdlib + Chart.js CDN en el HTML.

Uso CLI:
    python3 chart_engine.py --test    # 6 self-tests
    python3 chart_engine.py --demo    # genera demo.html con todas las gráficas
"""
from __future__ import annotations

import html as _html
import json
import sys
from pathlib import Path
from typing import Optional

CHARTJS_CDN = "https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"

# ─── Internal counter for unique canvas IDs ────────────────────────────────
_ctr = [0]


def _uid() -> str:
    _ctr[0] += 1
    return f"bago_c{_ctr[0]}"


def _cdn_loader() -> str:
    """CDN <script> loader — deduplicado por ID en el DOM."""
    return (
        '<script>'
        'if(!document.getElementById("_bago_chartjs_cdn")){'
        'var _bcj=document.createElement("script");'
        f'_bcj.src="{CHARTJS_CDN}";'
        '_bcj.id="_bago_chartjs_cdn";'
        'document.head.appendChild(_bcj);'
        '}'
        '</script>'
    )


def _init_script(cid: str, chart_type: str, data_js: str, options_js: str) -> str:
    """Wrapper JS que espera a que Chart.js cargue antes de inicializar."""
    return f"""<script>
(function(){{
  var _el=document.getElementById('{cid}');
  if(!_el)return;
  function _init(){{
    if(typeof Chart==='undefined'){{setTimeout(_init,80);return;}}
    new Chart(_el,{{type:'{chart_type}',data:{data_js},options:{options_js}}});
  }}
  _init();
}})();
</script>"""


def _color_for_score(score: float) -> str:
    if score >= 90:
        return "#27ae60"
    if score >= 70:
        return "#f1c40f"
    if score >= 50:
        return "#e67e22"
    return "#e74c3c"


# ─── Public chart functions ────────────────────────────────────────────────

def render_gauge(score: int, label: str = "Score", max_val: int = 100) -> str:
    """Gauge (semicírculo) para score 0-100.

    Usa doughnut de Chart.js con circumference=180 y rotation=-90.
    """
    cid = _uid()
    score = max(0, min(max_val, score))
    color = _color_for_score(score * 100 / max(1, max_val))

    data = {
        "labels": [label, ""],
        "datasets": [{
            "data": [score, max_val - score],
            "backgroundColor": [color, "#e0e0e0"],
            "borderWidth": 0,
        }],
    }
    options = {
        "responsive": True,
        "circumference": 180,
        "rotation": -90,
        "animation": {"duration": 900, "easing": "easeInOutQuart"},
        "cutout": "70%",
        "plugins": {
            "legend": {"display": False},
            "tooltip": {
                "callbacks": {
                    "label": "function(c){return c.label+': '+c.raw+'/'+c.dataset.data.reduce(function(a,b){return a+b;},0);}"
                }
            },
        },
    }
    options_str = json.dumps(options)
    # Fix: tooltip callback must be raw JS, not JSON-escaped string
    options_str = options_str.replace(
        '"function(c){return c.label+\\\':\\\'+c.raw+\\\'/\\\'+c.dataset.data.reduce(function(a,b){return a+b;},0);}"',
        'function(c){return c.label+": "+c.raw+"/"+c.dataset.data.reduce(function(a,b){return a+b;},0);}',
    )

    # Build options manually to keep callback as raw JS
    opts_js = (
        "{"
        "responsive:true,"
        "circumference:180,"
        "rotation:-90,"
        "animation:{duration:900,easing:'easeInOutQuart'},"
        "cutout:'70%',"
        "plugins:{"
        "legend:{display:false},"
        "tooltip:{callbacks:{label:function(c){return c.label+': '+c.raw+'/'+c.dataset.data.reduce(function(a,b){return a+b;},0);}}}"
        "}"
        "}"
    )

    return (
        f'{_cdn_loader()}'
        f'<div style="position:relative;width:100%;max-width:300px;margin:0 auto;text-align:center;">'
        f'<canvas id="{cid}" role="img" aria-label="{_html.escape(label)}: {score}/{max_val}"></canvas>'
        f'<div style="position:absolute;bottom:0;width:100%;font-size:1.8em;font-weight:bold;color:{color};">'
        f'{score}/{max_val}</div>'
        f'<div style="font-size:0.85em;color:var(--text-muted,#666);padding-top:4px;">{_html.escape(label)}</div>'
        f'</div>'
        + _init_script(cid, "doughnut", json.dumps(data), opts_js)
    )


def render_bar(
    labels: list[str],
    values: list[float],
    title: str = "",
    color: str = "#3498db",
    horizontal: bool = False,
    max_width: int = 700,
) -> str:
    """Bar chart (vertical u horizontal).

    Args:
        labels:     Etiquetas del eje X (o Y si horizontal).
        values:     Valores numéricos.
        title:      Título de la gráfica.
        color:      Color de las barras (hex/rgba).
        horizontal: Si True, gráfica horizontal.
        max_width:  Ancho máximo en px.
    """
    cid = _uid()
    chart_type = "bar"
    safe_labels = [_html.escape(str(l)) for l in labels]
    data = {
        "labels": safe_labels,
        "datasets": [{
            "label": title,
            "data": [float(v) for v in values],
            "backgroundColor": color,
            "borderColor": color,
            "borderWidth": 1,
            "borderRadius": 4,
        }],
    }
    index_axis = "'y'" if horizontal else "'x'"
    opts_js = (
        "{"
        f"indexAxis:{index_axis},"
        "responsive:true,"
        "animation:{duration:800},"
        "plugins:{"
        "legend:{display:false},"
        "title:{display:" + ("true" if title else "false") + f",text:'{_html.escape(title)}'}},"
        "tooltip:{mode:'index',intersect:false}"
        "},"
        "scales:{"
        "x:{grid:{color:'rgba(0,0,0,0.05)'}},"
        "y:{grid:{color:'rgba(0,0,0,0.05)'}}"
        "}"
        "}"
    )
    return (
        f'{_cdn_loader()}'
        f'<div style="width:100%;max-width:{max_width}px;margin:0 auto;">'
        f'<canvas id="{cid}" role="img" aria-label="{_html.escape(title)}"></canvas>'
        f'</div>'
        + _init_script(cid, chart_type, json.dumps(data), opts_js)
    )


def render_line(
    labels: list[str],
    datasets: list[dict],
    title: str = "",
    max_width: int = 800,
) -> str:
    """Line chart para tendencias.

    Args:
        labels:   Etiquetas del eje X (fechas, versiones…).
        datasets: Lista de dicts: {"label": str, "data": [float...], "color": "#hex"}.
        title:    Título de la gráfica.
    """
    cid = _uid()
    default_colors = ["#3498db", "#e74c3c", "#27ae60", "#9b59b6", "#e67e22"]
    ds_list = []
    for i, ds in enumerate(datasets):
        c = ds.get("color", default_colors[i % len(default_colors)])
        ds_list.append({
            "label": ds.get("label", f"Serie {i+1}"),
            "data": [float(v) for v in ds.get("data", [])],
            "borderColor": c,
            "backgroundColor": c.replace("#", "rgba(").rstrip(")") if "rgba" not in c else c,
            "fill": False,
            "tension": 0.3,
            "pointRadius": 4,
            "pointHoverRadius": 6,
        })
    # Fix backgroundColor — simple approach using opacity
    for i, ds_j in enumerate(ds_list):
        ds_j["backgroundColor"] = default_colors[i % len(default_colors)] + "33"

    data = {"labels": [str(l) for l in labels], "datasets": ds_list}
    opts_js = (
        "{"
        "responsive:true,"
        "animation:{duration:800},"
        "interaction:{mode:'index',intersect:false},"
        "plugins:{"
        "legend:{display:" + ("true" if len(datasets) > 1 else "false") + "},"
        "title:{display:" + ("true" if title else "false") + f",text:'{_html.escape(title)}'}},"
        "tooltip:{mode:'index'}"
        "},"
        "scales:{"
        "x:{grid:{color:'rgba(0,0,0,0.05)'}},"
        "y:{grid:{color:'rgba(0,0,0,0.05)'},beginAtZero:true}"
        "}"
        "}"
    )
    return (
        f'{_cdn_loader()}'
        f'<div style="width:100%;max-width:{max_width}px;margin:0 auto;">'
        f'<canvas id="{cid}" role="img" aria-label="{_html.escape(title)}"></canvas>'
        f'</div>'
        + _init_script(cid, "line", json.dumps(data), opts_js)
    )


def render_doughnut(
    labels: list[str],
    values: list[float],
    title: str = "",
    colors: Optional[list[str]] = None,
    max_width: int = 400,
) -> str:
    """Doughnut chart para distribuciones (PASS/FAIL/WARN, etc.).

    Args:
        labels: Etiquetas de cada segmento.
        values: Valores numéricos.
        title:  Título.
        colors: Lista de colores (opcional, usa paleta BAGO por defecto).
    """
    cid = _uid()
    default_colors = ["#27ae60", "#e74c3c", "#f1c40f", "#3498db", "#9b59b6", "#e67e22", "#1abc9c"]
    bg_colors = colors if colors else default_colors[:len(labels)]

    data = {
        "labels": [_html.escape(str(l)) for l in labels],
        "datasets": [{
            "data": [float(v) for v in values],
            "backgroundColor": bg_colors,
            "borderWidth": 2,
            "borderColor": "#fff",
            "hoverOffset": 8,
        }],
    }
    opts_js = (
        "{"
        "responsive:true,"
        "animation:{duration:900,animateRotate:true},"
        "cutout:'55%',"
        "plugins:{"
        "legend:{position:'right',labels:{padding:16}},"
        "title:{display:" + ("true" if title else "false") + f",text:'{_html.escape(title)}'}},"
        "tooltip:{callbacks:{label:function(c){var total=c.dataset.data.reduce(function(a,b){{return a+b;}},0);var pct=total>0?Math.round(c.raw*100/total):0;return c.label+': '+c.raw+' ('+pct+'%)';}}}"
        "}"
        "}"
    )
    return (
        f'{_cdn_loader()}'
        f'<div style="width:100%;max-width:{max_width}px;margin:0 auto;">'
        f'<canvas id="{cid}" role="img" aria-label="{_html.escape(title)}"></canvas>'
        f'</div>'
        + _init_script(cid, "doughnut", json.dumps(data), opts_js)
    )


def render_heatmap(
    rows: list[str],
    cols: list[str],
    matrix: list[list[float]],
    title: str = "",
    max_width: int = 800,
) -> str:
    """Heatmap como tabla HTML con colores escalados (no requiere Chart.js).

    Args:
        rows:   Etiquetas de filas.
        cols:   Etiquetas de columnas.
        matrix: Lista de listas (len(rows) × len(cols)).
        title:  Título.
    """
    # Find min/max for color scaling
    flat = [v for row in matrix for v in row]
    vmin = min(flat) if flat else 0
    vmax = max(flat) if flat else 1
    vrange = max(1e-9, vmax - vmin)

    def cell_color(v: float) -> str:
        t = (v - vmin) / vrange  # 0..1
        # low=light blue, high=deep green
        r = int(255 * (1 - t * 0.6))
        g = int(200 + 55 * t)
        b = int(255 * (1 - t))
        return f"rgb({r},{g},{b})"

    def text_color(v: float) -> str:
        t = (v - vmin) / vrange
        return "#1a1a1a" if t < 0.7 else "#fff"

    th_style = "padding:6px 10px;background:#2c3e50;color:#fff;font-weight:600;font-size:0.85em;white-space:nowrap;"
    title_html = f"<h3 style='margin:0 0 8px;color:#2c3e50;font-size:1em;'>{_html.escape(title)}</h3>" if title else ""

    header = "<tr><th style='" + th_style + "'></th>" + "".join(
        f"<th style='{th_style}'>{_html.escape(str(c))}</th>" for c in cols
    ) + "</tr>"

    body_rows = []
    for ri, row_label in enumerate(rows):
        cells = [f"<th style='{th_style}'>{_html.escape(str(row_label))}</th>"]
        for ci in range(len(cols)):
            v = matrix[ri][ci] if ci < len(matrix[ri]) else 0
            bg = cell_color(v)
            fg = text_color(v)
            cells.append(
                f"<td style='padding:6px 10px;background:{bg};color:{fg};"
                f"text-align:center;font-size:0.85em;font-weight:500;'>{v:.1f}</td>"
            )
        body_rows.append("<tr>" + "".join(cells) + "</tr>")

    table_html = (
        f"<table style='border-collapse:collapse;width:100%;'>"
        f"<thead>{header}</thead>"
        f"<tbody>{''.join(body_rows)}</tbody>"
        f"</table>"
    )
    return (
        f'<div style="width:100%;max-width:{max_width}px;margin:0 auto;overflow-x:auto;">'
        f"{title_html}{table_html}"
        f"</div>"
    )


# ─── Helper: full HTML page wrapper ───────────────────────────────────────

def html_page(*snippets: str, title: str = "BAGO Charts") -> str:
    """Envuelve snippets en una página HTML completa."""
    body = "\n<hr style='margin:24px 0;border:none;border-top:1px solid #ddd;'>\n".join(snippets)
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_html.escape(title)}</title>
<style>
:root {{--text-muted:#666;}}
@media(prefers-color-scheme:dark){{
  body{{background:#1a1a2e;color:#e0e0e0;}}
  :root{{--text-muted:#aaa;}}
}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      max-width:1100px;margin:40px auto;padding:0 24px;}}
h2{{color:#2c3e50;margin-top:32px;}}
</style>
</head>
<body>
<h1 style="color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:12px;">{_html.escape(title)}</h1>
{body}
<hr style="margin:32px 0;"><small style="color:var(--text-muted);">Generado con BAGO chart_engine — Chart.js 4.4</small>
</body>
</html>"""


# ─── CLI: demo / test ──────────────────────────────────────────────────────

def _demo() -> None:
    gauge   = render_gauge(78, "Health Score")
    bar     = render_bar(
        ["BAGO-E001", "BAGO-W001", "BAGO-W003", "BAGO-I002", "BAGO-E002"],
        [12, 8, 5, 3, 1],
        title="Top Reglas", color="#e74c3c",
    )
    line    = render_line(
        ["Ene", "Feb", "Mar", "Abr", "May", "Jun"],
        [
            {"label": "Errores",  "data": [10, 8, 6, 4, 3, 1], "color": "#e74c3c"},
            {"label": "Warnings", "data": [20, 18, 15, 12, 10, 8], "color": "#f1c40f"},
        ],
        title="Evolución de hallazgos",
    )
    donut   = render_doughnut(
        ["PASS", "WARN", "ERROR"],
        [42, 15, 8],
        title="Distribución de severidad",
        colors=["#27ae60", "#f1c40f", "#e74c3c"],
    )
    heatmap = render_heatmap(
        rows=["health_report.py", "doc_coverage.py", "changelog_gen.py"],
        cols=["Complejidad", "Cobertura doc", "Hallazgos"],
        matrix=[[72, 85, 3], [60, 90, 1], [55, 70, 5]],
        title="Heatmap de métricas",
    )
    page = html_page(gauge, bar, line, donut, heatmap, title="BAGO Chart Engine — Demo")
    out = Path(__file__).parent / "chart_engine_demo.html"
    out.write_text(page, encoding="utf-8")
    print(f"Demo generada: {out}")


def _self_test() -> None:
    print("Tests de chart_engine.py...")
    fails: list[str] = []

    def ok(n: str):         print(f"  OK: {n}")
    def fail(n: str, m: str): fails.append(n); print(f"  FAIL: {n}: {m}")

    # T1 — render_gauge genera canvas y Chart.js ref (CDN usa chart.js lowercase)
    html = render_gauge(75, "Health Score")
    if "<canvas" in html and "chart.js" in html.lower() and "75/100" in html:
        ok("chart_engine:gauge_structure")
    else:
        fail("chart_engine:gauge_structure", f"html snippet incomplete: {html[:120]}")

    # T2 — render_bar genera canvas con labels correctos
    html = render_bar(["A", "B", "C"], [10, 20, 30], title="Test Bar")
    if "<canvas" in html and '"A"' in html and "Test Bar" in html:
        ok("chart_engine:bar_labels")
    else:
        fail("chart_engine:bar_labels", f"bar snippet: {html[:120]}")

    # T3 — render_line genera múltiples datasets
    html = render_line(
        ["Ene", "Feb"],
        [{"label": "S1", "data": [1, 2]}, {"label": "S2", "data": [3, 4]}],
        title="Test Line",
    )
    if "<canvas" in html and "S1" in html and "S2" in html:
        ok("chart_engine:line_datasets")
    else:
        fail("chart_engine:line_datasets", f"line snippet: {html[:120]}")

    # T4 — render_doughnut genera datos con colores
    html = render_doughnut(["PASS", "FAIL"], [80, 20], title="Test Donut")
    if "<canvas" in html and "PASS" in html and "doughnut" in html:
        ok("chart_engine:doughnut_data")
    else:
        fail("chart_engine:doughnut_data", f"doughnut snippet: {html[:120]}")

    # T5 — render_heatmap genera tabla HTML (sin canvas)
    html = render_heatmap(
        rows=["f1.py", "f2.py"],
        cols=["Doc", "Complejidad"],
        matrix=[[80, 5], [60, 10]],
        title="Test Heatmap",
    )
    if "<table" in html and "f1.py" in html and "Test Heatmap" in html:
        ok("chart_engine:heatmap_table")
    else:
        fail("chart_engine:heatmap_table", f"heatmap snippet: {html[:120]}")

    # T6 — html_page envuelve en documento completo
    page = html_page(render_gauge(90, "Score"), title="My Test Page")
    if "<!DOCTYPE html>" in page and "My Test Page" in page and "chart.js" in page.lower():
        ok("chart_engine:html_page_wrapper")
    else:
        fail("chart_engine:html_page_wrapper", f"page: {page[:120]}")

    total = 6
    passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    elif "--demo" in sys.argv:
        _demo()
    else:
        print(__doc__)
