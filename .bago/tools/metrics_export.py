#!/usr/bin/env python3
"""metrics_export.py — Herramienta #115: Exporta métricas BAGO como JSON/Prometheus.

Agrega resultados de todos los scanners BAGO disponibles y los exporta
en formato JSON plano, Prometheus text format, o CSV para ingestion en
dashboards (Grafana, Datadog, etc.).

Uso:
    bago metrics-export [DIR] [--format json|prometheus|csv]
                        [--out FILE] [--prefix PREFIX] [--test]

Formatos:
    json        Objeto JSON con todas las métricas
    prometheus  Prometheus text exposition format (default)
    csv         CSV con timestamp, metric, value, labels
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import time
from pathlib import Path

_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RST  = "\033[0m"

SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules"}


# ── Colectores ───────────────────────────────────────────────────────────────

def _collect_file_metrics(directory: str) -> dict:
    """Cuenta archivos Python, líneas totales, funciones, clases."""
    root = Path(directory)
    py_files  = [f for f in root.rglob("*.py") if not any(d in f.parts for d in SKIP_DIRS)]
    total_lines = total_funcs = total_classes = 0
    for f in py_files:
        try:
            source = f.read_text(encoding="utf-8", errors="ignore")
            total_lines += len(source.splitlines())
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    total_funcs  += 1
                elif isinstance(node, ast.ClassDef):
                    total_classes += 1
        except Exception:
            pass
    return {
        "python_files":   len(py_files),
        "total_lines":    total_lines,
        "total_functions": total_funcs,
        "total_classes":  total_classes,
    }


def _collect_complexity_metrics(directory: str) -> dict:
    """Ejecuta complexity.py y agrega stats."""
    tools_dir = Path(__file__).parent
    complexity_py = tools_dir / "complexity.py"
    if not complexity_py.exists():
        return {}
    try:
        result = subprocess.run(
            ["python3", str(complexity_py), directory, "--format", "json"],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout or "[]")
        if not data:
            return {}
        scores = [item.get("complexity", 1) for item in data]
        return {
            "complexity_mean":    round(sum(scores) / len(scores), 2),
            "complexity_max":     max(scores),
            "complexity_high":    sum(1 for s in scores if s > 10),
            "complexity_medium":  sum(1 for s in scores if 6 <= s <= 10),
            "complexity_simple":  sum(1 for s in scores if s <= 5),
            "complexity_total_funcs": len(scores),
        }
    except Exception:
        return {}


def _collect_git_metrics(directory: str) -> dict:
    """Commits últimos 30 días, autores, archivos modificados."""
    try:
        result = subprocess.run(
            ["git", "-C", directory, "log", "--oneline", "--since=30.days"],
            capture_output=True, text=True, timeout=10
        )
        commits_30d = len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0

        result2 = subprocess.run(
            ["git", "-C", directory, "log", "--format=%ae", "--since=30.days"],
            capture_output=True, text=True, timeout=10
        )
        authors = len(set(result2.stdout.strip().splitlines())) if result2.stdout.strip() else 0

        result3 = subprocess.run(
            ["git", "-C", directory, "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True, text=True, timeout=10
        )
        files_last = len(result3.stdout.strip().splitlines()) if result3.stdout.strip() else 0

        return {
            "git_commits_30d":    commits_30d,
            "git_authors_30d":    authors,
            "git_files_last_commit": files_last,
        }
    except Exception:
        return {}


def _collect_doc_metrics(directory: str) -> dict:
    """Cobertura de docstrings global."""
    tools_dir = Path(__file__).parent
    doc_py = tools_dir / "doc_coverage.py"
    if not doc_py.exists():
        return {}
    try:
        result = subprocess.run(
            ["python3", str(doc_py), directory, "--format", "json"],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(result.stdout or "[]")
        total_doc = sum(len(r.get("documented", [])) for r in data if "error" not in r)
        total_miss= sum(len(r.get("missing", []))    for r in data if "error" not in r)
        total     = total_doc + total_miss
        return {
            "doc_coverage_pct":  round(100 * total_doc / max(1, total), 1),
            "doc_total":         total,
            "doc_documented":    total_doc,
            "doc_missing":       total_miss,
        }
    except Exception:
        return {}


def collect_all(directory: str) -> dict:
    ts = int(time.time())
    metrics = {"timestamp": ts, "directory": directory}
    metrics.update(_collect_file_metrics(directory))
    metrics.update(_collect_complexity_metrics(directory))
    metrics.update(_collect_git_metrics(directory))
    metrics.update(_collect_doc_metrics(directory))
    return metrics


# ── Formateadores ─────────────────────────────────────────────────────────────

def format_prometheus(metrics: dict, prefix: str = "bago") -> str:
    ts_ms  = metrics.get("timestamp", 0) * 1000
    directory = metrics.get("directory", ".")
    label  = f'dir="{directory}"'
    lines  = [
        f"# HELP {prefix}_info BAGO framework metrics",
        f"# TYPE {prefix}_info gauge",
        f'{prefix}_info{{{label}}} 1 {ts_ms}',
    ]
    skip = {"timestamp", "directory"}
    for key, val in metrics.items():
        if key in skip:
            continue
        if not isinstance(val, (int, float)):
            continue
        metric_name = f"{prefix}_{key}"
        lines += [
            f"# TYPE {metric_name} gauge",
            f"{metric_name}{{{label}}} {val} {ts_ms}",
        ]
    return "\n".join(lines) + "\n"


def format_csv(metrics: dict) -> str:
    import csv, io
    ts = metrics.get("timestamp", 0)
    directory = metrics.get("directory", ".")
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "metric", "value", "directory"])
    for key, val in metrics.items():
        if key in {"timestamp", "directory"}:
            continue
        if isinstance(val, (int, float)):
            writer.writerow([ts, key, val, directory])
    return buf.getvalue()


def main(argv: list[str]) -> int:
    directory = "./"
    fmt       = "prometheus"
    out_file  = None
    prefix    = "bago"

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        elif a == "--prefix" and i + 1 < len(argv):
            prefix = argv[i + 1]; i += 2
        elif not a.startswith("--"):
            directory = a; i += 1
        else:
            i += 1

    if not Path(directory).exists():
        print(f"No existe: {directory}", file=sys.stderr); return 1

    print(f"{_YEL}Recopilando métricas…{_RST}", file=sys.stderr)
    metrics = collect_all(directory)

    if fmt == "json":
        content = json.dumps(metrics, indent=2)
    elif fmt == "csv":
        content = format_csv(metrics)
    else:
        content = format_prometheus(metrics, prefix)

    if out_file:
        Path(out_file).write_text(content, encoding="utf-8")
        print(f"{_GRN}✅ Métricas guardadas: {out_file}{_RST}", file=sys.stderr)
    else:
        print(content)
    return 0


def _self_test() -> None:
    import tempfile
    print("Tests de metrics_export.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "sample.py").write_text(
            '"""Módulo."""\ndef hello():\n    """Saluda."""\n    return "hi"\n'
        )

        # T1 — collect_all retorna dict con timestamp
        m = collect_all(td)
        if "timestamp" in m and isinstance(m["timestamp"], int):
            ok("metrics_export:timestamp_present")
        else:
            fail("metrics_export:timestamp_present", str(m.get("timestamp")))

        # T2 — métricas de archivo
        if "python_files" in m and m["python_files"] >= 1:
            ok("metrics_export:file_metrics")
        else:
            fail("metrics_export:file_metrics", str(m))

        # T3 — total_lines > 0
        if m.get("total_lines", 0) > 0:
            ok("metrics_export:lines_counted")
        else:
            fail("metrics_export:lines_counted", f"total_lines={m.get('total_lines')}")

        # T4 — prometheus format contiene TYPE
        prom = format_prometheus(m)
        if "# TYPE" in prom and "bago_python_files" in prom:
            ok("metrics_export:prometheus_format")
        else:
            fail("metrics_export:prometheus_format", prom[:120])

        # T5 — json format es parseable
        j = json.dumps(m, indent=2)
        parsed = json.loads(j)
        if parsed["python_files"] == m["python_files"]:
            ok("metrics_export:json_roundtrip")
        else:
            fail("metrics_export:json_roundtrip", "mismatch")

        # T6 — csv format tiene cabecera correcta
        csv_out = format_csv(m)
        if csv_out.startswith("timestamp,metric,value,directory"):
            ok("metrics_export:csv_header")
        else:
            fail("metrics_export:csv_header", csv_out[:80])

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
