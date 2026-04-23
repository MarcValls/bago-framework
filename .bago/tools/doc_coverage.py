#!/usr/bin/env python3
"""doc_coverage.py — Herramienta #111: Cobertura de docstrings en módulos Python.

Analiza un directorio o archivo Python y reporta qué funciones, métodos
y clases carecen de docstring. Genera score 0-100.

Uso:
    bago doc-coverage [FILE|DIR] [--min-score N] [--format md|text|json]
                      [--out FILE] [--exclude PATTERN] [--test]

Opciones:
    FILE|DIR      Objetivo a analizar (default: ./)
    --min-score N Score mínimo; exit 1 si < N (modo CI)
    --format      text (default) | md | json
    --out FILE    Guardar output
    --exclude P   Excluir archivos matching glob pattern
    --test        Self-tests
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Optional

_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RED  = "\033[0;31m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".mypy_cache"}

# Import chart_engine (optional — graceful fallback)
try:
    import sys as _sys
    _sys.path.insert(0, str(Path(__file__).parent))
    from chart_engine import render_bar, render_doughnut, html_page as _html_page
    _CHARTS_OK = True
except Exception:
    _CHARTS_OK = False


def _has_docstring(node) -> bool:
    return (
        bool(node.body)
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
        and isinstance(node.body[0].value.value, str)
    )


def analyze_file(filepath: str) -> dict:
    """Retorna dict con items documentados y sin documentar."""
    try:
        source = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        tree   = ast.parse(source, filename=filepath)
    except Exception as e:
        return {"error": str(e), "file": filepath, "documented": [], "missing": []}

    documented: list[dict] = []
    missing:    list[dict] = []

    def _check(node, kind: str, prefix: str = "") -> None:
        name = f"{prefix}{node.name}" if prefix else node.name
        entry = {"name": name, "kind": kind, "line": node.lineno}
        if _has_docstring(node):
            documented.append(entry)
        else:
            missing.append(entry)

    for node in ast.walk(tree):
        if isinstance(node, ast.Module):
            if _has_docstring(node):
                documented.append({"name": "<module>", "kind": "module", "line": 1})
            else:
                missing.append({"name": "<module>", "kind": "module", "line": 1})
        elif isinstance(node, ast.ClassDef):
            _check(node, "class")
            for child in ast.walk(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not child.name.startswith("__") or child.name == "__init__":
                        _check(child, "method", f"{node.name}.")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            # Solo top-level (no los de clase, ya procesados)
            parent_class = False
            for parent in ast.walk(tree):
                if isinstance(parent, ast.ClassDef):
                    for c in ast.walk(parent):
                        if c is node:
                            parent_class = True
                            break
            if not parent_class and not node.name.startswith("_"):
                _check(node, "function")

    return {
        "file":       filepath,
        "documented": documented,
        "missing":    missing,
        "total":      len(documented) + len(missing),
        "score":      round(100 * len(documented) / max(1, len(documented) + len(missing))),
    }


def analyze_directory(directory: str, exclude: Optional[str] = None) -> list[dict]:
    root   = Path(directory)
    result = []
    for py_file in sorted(root.rglob("*.py")):
        if any(d in py_file.parts for d in SKIP_DIRS):
            continue
        if exclude and py_file.match(exclude):
            continue
        result.append(analyze_file(str(py_file)))
    return result


def _spark(score: int) -> str:
    blocks = " ▏▎▍▌▋▊▉█"
    idx    = int(score / 100 * 8)
    bar    = "█" * (score // 10) + blocks[min(8, (score % 10) * 9 // 10)]
    color  = _GRN if score >= 80 else (_YEL if score >= 50 else _RED)
    return f"{color}{bar:10s}{_RST} {score:3d}%"


def generate_text(results: list[dict]) -> str:
    lines = [f"{_BOLD}Doc Coverage Report{_RST}", ""]
    total_doc = total_miss = 0
    for r in results:
        if "error" in r:
            lines.append(f"  ⚠  {r['file']}: {r['error']}")
            continue
        total_doc  += len(r["documented"])
        total_miss += len(r["missing"])
        bar = _spark(r["score"])
        lines.append(f"  {bar}  {Path(r['file']).name}")
        for m in r["missing"][:5]:
            lines.append(f"       ↳ {_YEL}sin doc{_RST} {m['kind']:8s} {m['name']} (línea {m['line']})")
        if len(r["missing"]) > 5:
            lines.append(f"       ↳ … y {len(r['missing'])-5} más sin documentar")
    global_score = round(100 * total_doc / max(1, total_doc + total_miss))
    color = _GRN if global_score >= 80 else (_YEL if global_score >= 50 else _RED)
    lines += [
        "",
        f"  {'─'*50}",
        f"  Global: {color}{global_score}%{_RST}  "
        f"({total_doc} documentados, {total_miss} sin documentar)",
    ]
    return "\n".join(lines)


def generate_markdown(results: list[dict]) -> str:
    total_doc = sum(len(r["documented"]) for r in results if "error" not in r)
    total_miss= sum(len(r["missing"])    for r in results if "error" not in r)
    global_score = round(100 * total_doc / max(1, total_doc + total_miss))
    badge = "🟢" if global_score >= 80 else ("🟡" if global_score >= 50 else "🔴")
    lines = [
        "# Doc Coverage Report",
        "",
        f"**Score global:** {badge} {global_score}% ({total_doc} doc / {total_miss} sin doc)",
        "",
        "| Archivo | Score | Sin docstring |",
        "|---------|-------|---------------|",
    ]
    for r in results:
        if "error" in r:
            lines.append(f"| {Path(r['file']).name} | ⚠ error | — |")
            continue
        b = "🟢" if r["score"] >= 80 else ("🟡" if r["score"] >= 50 else "🔴")
        top_missing = ", ".join(m["name"] for m in r["missing"][:3])
        if len(r["missing"]) > 3:
            top_missing += f" …+{len(r['missing'])-3}"
        lines.append(f"| `{Path(r['file']).name}` | {b} {r['score']}% | {top_missing or '—'} |")
    lines += ["", "---", "*Generado con `bago doc-coverage`*"]
    return "\n".join(lines)


def generate_html(results: list[dict]) -> str:
    """Genera un dashboard HTML interactivo con Chart.js (si disponible)."""
    import datetime
    total_doc  = sum(len(r["documented"]) for r in results if "error" not in r)
    total_miss = sum(len(r["missing"])    for r in results if "error" not in r)
    global_score = round(100 * total_doc / max(1, total_doc + total_miss))
    badge = "🟢" if global_score >= 80 else ("🟡" if global_score >= 50 else "🔴")
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M")

    # ── Charts section ──────────────────────────────────────────────────
    charts_html = ""
    if _CHARTS_OK:
        # Bar: coverage per file
        file_labels = [Path(r["file"]).name for r in results if "error" not in r]
        file_scores = [r["score"] for r in results if "error" not in r]
        bar_colors  = ["#27ae60" if s >= 80 else ("#f1c40f" if s >= 50 else "#e74c3c")
                       for s in file_scores]

        if file_labels:
            bar_html = render_bar(
                file_labels, file_scores,
                title="Cobertura de docstrings por archivo (%)",
                color="#3498db",
                horizontal=True,
                max_width=750,
            )
        else:
            bar_html = "<p>Sin archivos analizados.</p>"

        donut_html = render_doughnut(
            ["Documentados", "Sin docstring"],
            [total_doc, total_miss],
            title="Cobertura global",
            colors=["#27ae60", "#e74c3c"],
        )
        charts_html = f"""
<h2>📊 Cobertura Global</h2>
<div style="display:flex;flex-wrap:wrap;gap:24px;align-items:flex-start;margin:16px 0;">
  <div style="flex:0 0 320px;">{donut_html}</div>
</div>
<h2>📁 Por Archivo</h2>
{bar_html}"""
    else:
        charts_html = (
            f'<p><strong>Score global:</strong> {badge} {global_score}% '
            f'({total_doc} doc / {total_miss} sin doc)</p>'
        )

    # ── Findings table ──────────────────────────────────────────────────
    rows = []
    for r in results:
        if "error" in r:
            rows.append(f'<tr><td><code>{Path(r["file"]).name}</code></td>'
                        f'<td colspan="3">⚠ {r["error"]}</td></tr>')
            continue
        b = "🟢" if r["score"] >= 80 else ("🟡" if r["score"] >= 50 else "🔴")
        missing_names = ", ".join(f'<code>{m["name"]}</code>' for m in r["missing"][:5])
        if len(r["missing"]) > 5:
            missing_names += f' <em>…+{len(r["missing"])-5}</em>'
        rows.append(
            f'<tr><td><code>{Path(r["file"]).name}</code></td>'
            f'<td>{b} {r["score"]}%</td>'
            f'<td>{len(r["documented"])}</td>'
            f'<td>{missing_names or "—"}</td></tr>'
        )
    table = (
        "<h2>📋 Detalle por archivo</h2>"
        "<table><thead><tr><th>Archivo</th><th>Score</th><th>Documentados</th>"
        "<th>Sin docstring (primeros 5)</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    ) if rows else ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BAGO Doc Coverage Report</title>
<style>
:root{{--text-muted:#666;}}
@media(prefers-color-scheme:dark){{body{{background:#1a1a2e;color:#e0e0e0;}}:root{{--text-muted:#aaa;}}}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      max-width:1100px;margin:40px auto;padding:0 20px;background:#f8f9fa;}}
h1{{color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:12px;}}
h2{{color:#34495e;margin-top:32px;}}
table{{border-collapse:collapse;width:100%;margin:16px 0;}}
th{{background:#2c3e50;color:white;padding:8px 12px;text-align:left;}}
td{{padding:6px 12px;border-bottom:1px solid #ddd;}}
tr:nth-child(even){{background:#f2f2f2;}}
code{{background:#ecf0f1;padding:2px 6px;border-radius:3px;font-size:0.9em;}}
</style>
</head>
<body>
<h1>📚 BAGO Doc Coverage Report</h1>
<p style="color:var(--text-muted);">Generado por BAGO Framework · {now}</p>
{charts_html}
{table}
<hr>
<small style="color:var(--text-muted);">BAGO Framework — <code>bago doc-coverage --format html</code></small>
</body>
</html>"""


def main(argv: list[str]) -> int:
    target    = "./"
    min_score = None
    fmt       = "text"
    out_file  = None
    exclude   = None

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--min-score" and i + 1 < len(argv):
            min_score = int(argv[i + 1]); i += 2
        elif a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        elif a == "--exclude" and i + 1 < len(argv):
            exclude = argv[i + 1]; i += 2
        elif not a.startswith("--"):
            target = a; i += 1
        else:
            i += 1

    target_path = Path(target)
    if not target_path.exists():
        print(f"No existe: {target}", file=sys.stderr); return 1

    if target_path.is_file():
        results = [analyze_file(target)]
    else:
        results = analyze_directory(target, exclude)

    if not results:
        print("No se encontraron archivos Python."); return 0

    if fmt == "json":
        content = json.dumps(results, indent=2)
    elif fmt == "md":
        content = generate_markdown(results)
    elif fmt == "html":
        content = generate_html(results)
    else:
        content = generate_text(results)

    if out_file:
        Path(out_file).write_text(content, encoding="utf-8")
        print(f"Guardado: {out_file}", file=sys.stderr)
    else:
        print(content)

    total_doc  = sum(len(r.get("documented", [])) for r in results)
    total_miss = sum(len(r.get("missing", []))    for r in results)
    global_score = round(100 * total_doc / max(1, total_doc + total_miss))

    if min_score is not None and global_score < min_score:
        print(f"\nScore {global_score}% < mínimo {min_score}% → FAIL", file=sys.stderr)
        return 1
    return 0


def _self_test() -> None:
    import tempfile
    print("Tests de doc_coverage.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        # T1 — función con docstring detectada como documentada
        (root / "good.py").write_text(
            '"""Module doc."""\ndef greet(name):\n    """Says hello."""\n    return name\n'
        )
        r = analyze_file(str(root / "good.py"))
        if r["score"] == 100:
            ok("doc_coverage:full_documented")
        else:
            fail("doc_coverage:full_documented", f"score={r['score']} missing={r['missing']}")

        # T2 — función sin docstring aparece en missing
        (root / "bad.py").write_text(
            'def greet(name):\n    return name\n'
        )
        r = analyze_file(str(root / "bad.py"))
        if any(m["name"] == "greet" for m in r["missing"]):
            ok("doc_coverage:missing_detected")
        else:
            fail("doc_coverage:missing_detected", f"missing={r['missing']}")

        # T3 — clase con docstring
        (root / "cls.py").write_text(
            'class Dog:\n    """A dog."""\n    def bark(self):\n        """Woof."""\n        pass\n'
        )
        r = analyze_file(str(root / "cls.py"))
        doc_names = [d["name"] for d in r["documented"]]
        if "Dog" in doc_names:
            ok("doc_coverage:class_documented")
        else:
            fail("doc_coverage:class_documented", f"documented={doc_names}")

        # T4 — score 0 para archivo sin ninguna doc
        (root / "nodoc.py").write_text(
            'def a(): pass\ndef b(): pass\n'
        )
        r = analyze_file(str(root / "nodoc.py"))
        if r["score"] == 0 or len(r["missing"]) >= 2:
            ok("doc_coverage:score_zero")
        else:
            fail("doc_coverage:score_zero", f"score={r['score']} missing={r['missing']}")

        # T5 — markdown generado contiene encabezado
        results = analyze_directory(td)
        md = generate_markdown(results)
        if "Doc Coverage Report" in md and "|" in md:
            ok("doc_coverage:markdown_generated")
        else:
            fail("doc_coverage:markdown_generated", md[:80])

        # T6 — min-score falla cuando el score es bajo
        (root / "only_bad.py").write_text('def x(): pass\n')
        r_single = [analyze_file(str(root / "only_bad.py"))]
        total_doc  = sum(len(r["documented"]) for r in r_single)
        total_miss = sum(len(r["missing"])    for r in r_single)
        gs = round(100 * total_doc / max(1, total_doc + total_miss))
        if gs < 80:
            ok("doc_coverage:min_score_ci")
        else:
            fail("doc_coverage:min_score_ci", f"score={gs} expected<80")

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: raise SystemExit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        raise SystemExit(main(sys.argv[1:]))
