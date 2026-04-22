#!/usr/bin/env python3
"""ci_report.py — Herramienta #125: Reporte CI unificado listo para PRs.

Ejecuta todos los scanners BAGO relevantes sobre un directorio/archivo y
genera un resumen markdown compacto apto para pegar en un GitHub PR comment,
Slack message, o guardar como artefacto CI.

Scanners incluidos (los que estén disponibles):
    lint, complexity, dead-code, duplicate-check, secret-scan,
    naming-check, type-check, license-check, dep-audit, doc-coverage

Output:
    - Sección por scanner con conteo de issues
    - Score global 0-100
    - Veredicto: ✅ MERGE OK / ⚠️ REVISAR / ❌ NO MERGE
    - Tiempo de ejecución total

Uso:
    bago ci-report [DIR] [--format md|text|json]
                   [--out FILE] [--fail-on error|warning]
                   [--skip TOOL,...] [--test]
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RED  = "\033[0;31m"
_CYN  = "\033[0;36m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

TOOLS_DIR = Path(__file__).parent

# Definición de scanners: (comando, peso_errores, peso_warnings)
SCANNERS = [
    ("lint",            "lint.py",            3.0, 1.0),
    ("complexity",      "complexity.py",       2.0, 0.5),
    ("dead-code",       "dead_code.py",        1.5, 0.5),
    ("duplicate-check", "duplicate_check.py",  2.0, 1.0),
    ("secret-scan",     "secret_scan.py",      5.0, 2.0),
    ("naming-check",    "naming_check.py",     1.0, 0.5),
    ("type-check",      "type_check.py",       1.0, 0.3),
    ("license-check",   "license_check.py",    1.5, 0.5),
    ("dep-audit",       "dep_audit.py",        4.0, 1.5),
    ("doc-coverage",    "doc_coverage.py",     1.0, 0.3),
]


def _run_scanner(tool_file: str, target: str, timeout: int = 60) -> dict:
    """Ejecuta un scanner y retorna {name, rc, findings_json, elapsed, error}."""
    tool_path = TOOLS_DIR / tool_file
    if not tool_path.exists():
        return {"available": False}

    start = time.time()
    try:
        result = subprocess.run(
            ["python3", str(tool_path), target, "--format", "json"],
            capture_output=True, text=True, timeout=timeout
        )
        elapsed = time.time() - start
        try:
            findings = json.loads(result.stdout or "[]")
        except json.JSONDecodeError:
            findings = []
        return {
            "available": True,
            "rc":        result.returncode,
            "findings":  findings if isinstance(findings, list) else [],
            "elapsed":   round(elapsed, 2),
            "error":     result.stderr[:200] if result.returncode != 0 and not findings else "",
        }
    except subprocess.TimeoutExpired:
        return {"available": True, "rc": -1, "findings": [], "elapsed": timeout, "error": "timeout"}
    except Exception as e:
        return {"available": True, "rc": -1, "findings": [], "elapsed": 0.0, "error": str(e)}


def run_all(target: str, skip: set[str] = None) -> dict:
    """Corre todos los scanners y retorna resultados agregados."""
    if skip is None:
        skip = set()

    results   = {}
    total_w   = 0.0
    t_start   = time.time()

    for name, tool_file, w_err, w_warn in SCANNERS:
        if name in skip:
            continue
        data = _run_scanner(tool_file, target)
        if not data.get("available"):
            continue
        findings = data["findings"]
        errors   = len([f for f in findings if f.get("severity") == "error"])
        warnings = len([f for f in findings if f.get("severity") == "warning"])
        infos    = len([f for f in findings if f.get("severity") == "info"])
        penalty  = errors * w_err + warnings * w_warn
        total_w += penalty
        results[name] = {
            "findings": findings,
            "errors":   errors,
            "warnings": warnings,
            "infos":    infos,
            "penalty":  round(penalty, 2),
            "elapsed":  data["elapsed"],
            "rc":       data["rc"],
        }

    score   = max(0, round(100 - min(total_w * 2, 100)))
    elapsed = round(time.time() - t_start, 2)

    if score >= 80:
        verdict = "✅ MERGE OK"
    elif score >= 50:
        verdict = "⚠️ REVISAR"
    else:
        verdict = "❌ NO MERGE"

    return {
        "target":  target,
        "score":   score,
        "verdict": verdict,
        "elapsed": elapsed,
        "scanners": results,
        "total_errors":   sum(v["errors"]   for v in results.values()),
        "total_warnings": sum(v["warnings"] for v in results.values()),
        "total_infos":    sum(v["infos"]    for v in results.values()),
    }


def generate_markdown(report: dict) -> str:
    score   = report["score"]
    verdict = report["verdict"]
    lines   = [
        f"## 🔍 BAGO CI Report — {verdict}",
        "",
        f"**Score:** `{score}/100` | "
        f"**Errors:** `{report['total_errors']}` | "
        f"**Warnings:** `{report['total_warnings']}` | "
        f"**Target:** `{Path(report['target']).name}` | "
        f"**Time:** `{report['elapsed']}s`",
        "",
        "| Scanner | Errors | Warnings | Infos | Penalty |",
        "|---------|--------|----------|-------|---------|",
    ]
    for name, data in report["scanners"].items():
        status = "🔴" if data["errors"] else ("🟡" if data["warnings"] else "🟢")
        lines.append(
            f"| {status} `{name}` | {data['errors']} | {data['warnings']} "
            f"| {data['infos']} | {data['penalty']:.1f} |"
        )

    # Top findings
    all_findings = []
    for name, data in report["scanners"].items():
        for f in data["findings"]:
            if f.get("severity") in ("error", "warning"):
                all_findings.append((name, f))

    if all_findings:
        lines += ["", "### Top Issues", ""]
        for name, f in sorted(all_findings, key=lambda x: x[1].get("severity","") == "error", reverse=True)[:10]:
            sev = "🔴" if f.get("severity") == "error" else "🟡"
            rule = f.get("rule", "?")
            msg  = f.get("message", "")[:80]
            fname = Path(f.get("file", "?")).name
            line  = f.get("line", 0)
            lines.append(f"- {sev} `[{rule}]` `{fname}:{line}` — {msg}")

    lines += ["", "---", f"*Generado con `bago ci-report` — BAGO v3.0*"]
    return "\n".join(lines)


def generate_text(report: dict) -> str:
    score   = report["score"]
    verdict = report["verdict"]
    color   = _GRN if score >= 80 else (_YEL if score >= 50 else _RED)
    lines   = [
        f"{_BOLD}BAGO CI Report{_RST}",
        f"  {color}{verdict}{_RST}  Score: {score}/100  "
        f"({report['total_errors']} errors, {report['total_warnings']} warnings)  "
        f"[{report['elapsed']}s]",
        "",
    ]
    for name, data in report["scanners"].items():
        icon = "🔴" if data["errors"] else ("🟡" if data["warnings"] else "🟢")
        lines.append(
            f"  {icon}  {name:20s}  "
            f"err={data['errors']}  warn={data['warnings']}  [{data['elapsed']}s]"
        )
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    target   = "./"
    fmt      = "md"
    out_file = None
    fail_on  = "error"
    skip: set[str] = set()

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        elif a == "--fail-on" and i + 1 < len(argv):
            fail_on = argv[i + 1]; i += 2
        elif a == "--skip" and i + 1 < len(argv):
            skip = set(argv[i + 1].split(",")); i += 2
        elif not a.startswith("--"):
            target = a; i += 1
        else:
            i += 1

    if not Path(target).exists():
        print(f"No existe: {target}", file=sys.stderr); return 1

    print(f"  Ejecutando scanners BAGO sobre {target}...", file=sys.stderr)
    report = run_all(target, skip)

    if fmt == "json":
        content = json.dumps(report, indent=2)
    elif fmt == "text":
        content = generate_text(report)
    else:
        content = generate_markdown(report)

    if out_file:
        Path(out_file).write_text(content, encoding="utf-8")
        print(f"  Guardado: {out_file}", file=sys.stderr)
    else:
        print(content)

    if fail_on == "error" and report["total_errors"] > 0:
        return 1
    if fail_on == "warning" and (report["total_errors"] + report["total_warnings"]) > 0:
        return 1
    return 0


def _self_test() -> None:
    import tempfile
    print("Tests de ci_report.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    # T1 — _run_scanner con tool inexistente → available=False
    r1 = _run_scanner("nonexistent_tool_xyz.py", ".")
    if not r1.get("available"):
        ok("ci_report:scanner_not_available")
    else:
        fail("ci_report:scanner_not_available", f"r={r1}")

    # T2 — _run_scanner con tool real (lint.py) → available=True
    r2 = _run_scanner("lint.py", str(TOOLS_DIR))
    if r2.get("available") and "findings" in r2:
        ok("ci_report:scanner_runs_lint")
    else:
        fail("ci_report:scanner_runs_lint", f"r={r2}")

    # T3 — run_all retorna estructura correcta
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "sample.py").write_text('def foo(): pass\n')
        report = run_all(td, skip={"secret-scan", "dep-audit"})
        if "score" in report and "verdict" in report and "scanners" in report:
            ok("ci_report:run_all_structure")
        else:
            fail("ci_report:run_all_structure", f"keys={list(report.keys())}")

    # T4 — score 100 → MERGE OK
    mock_report = {
        "target": ".", "score": 95, "verdict": "✅ MERGE OK",
        "elapsed": 0.5, "total_errors": 0, "total_warnings": 2, "total_infos": 5,
        "scanners": {
            "lint": {"findings": [], "errors": 0, "warnings": 2, "infos": 0,
                     "penalty": 1.0, "elapsed": 0.1, "rc": 0},
        }
    }
    md = generate_markdown(mock_report)
    if "MERGE OK" in md and "Score" in md and "| Scanner |" in md:
        ok("ci_report:markdown_merge_ok")
    else:
        fail("ci_report:markdown_merge_ok", md[:100])

    # T5 — score bajo → NO MERGE
    mock_bad = dict(mock_report)
    mock_bad["score"]   = 20
    mock_bad["verdict"] = "❌ NO MERGE"
    mock_bad["total_errors"] = 15
    md_bad = generate_markdown(mock_bad)
    if "NO MERGE" in md_bad:
        ok("ci_report:markdown_no_merge")
    else:
        fail("ci_report:markdown_no_merge", md_bad[:100])

    # T6 — generate_text funciona
    txt = generate_text(mock_report)
    if "BAGO CI Report" in txt and "MERGE OK" in txt:
        ok("ci_report:text_output")
    else:
        fail("ci_report:text_output", txt[:100])

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
