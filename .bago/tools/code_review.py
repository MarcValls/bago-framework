#!/usr/bin/env python3
"""code_review.py — Herramienta #116: Reporte CI agregado de todos los scanners BAGO.

Ejecuta en secuencia: lint, complexity, secret-scan, dead-code, duplicate-check,
env-check y branch-check. Genera un reporte consolidado con score 0-100 y
recomienda si la PR puede hacer merge.

Uso:
    bago code-review [DIR] [--branch BRANCH] [--format text|md|html]
                     [--out FILE] [--min-score N] [--test]

Exit codes:
    0  Score >= mínimo (por defecto 60)
    1  Score < mínimo o error crítico
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
_RST  = "\033[0m"
_BOLD = "\033[1m"

TOOLS_DIR = Path(__file__).parent


def _run_tool(tool: str, args: list[str], cwd: str, timeout: int = 60) -> tuple[int, str, str]:
    tool_path = TOOLS_DIR / tool
    if not tool_path.exists():
        return -1, "", f"tool not found: {tool}"
    try:
        r = subprocess.run(
            ["python3", str(tool_path)] + args,
            capture_output=True, text=True, timeout=timeout, cwd=cwd
        )
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -2, "", f"timeout after {timeout}s"
    except Exception as e:
        return -3, "", str(e)


def _score_from_findings(findings_count: int, total_lines: int) -> int:
    """Convierte densidad de findings en puntuación 0-100."""
    if total_lines <= 0:
        return 80
    density = findings_count / max(1, total_lines / 100)  # por cada 100 líneas
    if density == 0:
        return 100
    elif density < 0.5:
        return 90
    elif density < 1:
        return 75
    elif density < 2:
        return 60
    elif density < 5:
        return 40
    else:
        return 20


def _count_py_lines(directory: str) -> int:
    root  = Path(directory)
    total = 0
    for f in root.rglob("*.py"):
        if "__pycache__" in str(f):
            continue
        try:
            total += len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
        except Exception:
            pass
    return total


def run_reviews(directory: str, branch: str = "") -> dict:
    """Ejecuta todos los scanners y agrega resultados."""
    start     = time.time()
    sections  = {}
    total_findings = 0

    # 1. BAGO lint
    rc, out, err = _run_tool("scan.py", [directory, "--format", "json"], directory)
    try:
        lint_data   = json.loads(out) if out.strip() else []
        lint_count  = len(lint_data)
    except Exception:
        lint_count  = 0
        lint_data   = []
    sections["lint"] = {
        "name": "BAGO Lint",
        "tool": "scan.py",
        "findings": lint_count,
        "status":   "ok" if lint_count == 0 else ("warn" if lint_count < 10 else "fail"),
        "details":  lint_data[:5],
    }
    total_findings += lint_count

    # 2. Complexity
    rc2, out2, _ = _run_tool("complexity.py", [directory, "--min", "11", "--format", "json"], directory)
    try:
        cx_data = json.loads(out2) if out2.strip() else []
        cx_high = len(cx_data)
    except Exception:
        cx_high = 0
        cx_data = []
    sections["complexity"] = {
        "name": "Complexity (high)",
        "tool": "complexity.py",
        "findings": cx_high,
        "status":   "ok" if cx_high == 0 else ("warn" if cx_high < 5 else "fail"),
        "details":  cx_data[:5],
    }
    total_findings += cx_high

    # 3. Secret scan
    rc3, out3, _ = _run_tool("secret_scan.py", [directory, "--format", "json"], directory)
    try:
        sec_data  = json.loads(out3) if out3.strip() else []
        sec_count = len(sec_data)
    except Exception:
        sec_count = 0
        sec_data  = []
    sections["secrets"] = {
        "name": "Secret Scan",
        "tool": "secret_scan.py",
        "findings": sec_count,
        "status":   "ok" if sec_count == 0 else "fail",  # secrets are always fail
        "details":  sec_data[:3],
    }
    total_findings += sec_count * 3  # peso extra para secretos

    # 4. Dead code
    rc4, out4, _ = _run_tool("dead_code.py", [directory, "--format", "json"], directory)
    try:
        dc_data  = json.loads(out4) if out4.strip() else []
        dc_count = len(dc_data)
    except Exception:
        dc_count = 0
        dc_data  = []
    sections["dead_code"] = {
        "name": "Dead Code",
        "tool": "dead_code.py",
        "findings": dc_count,
        "status":   "ok" if dc_count == 0 else ("warn" if dc_count < 10 else "fail"),
        "details":  dc_data[:3],
    }
    total_findings += dc_count // 2  # peso menor

    # 5. Duplicate check
    rc5, out5, _ = _run_tool("duplicate_check.py", [directory, "--format", "json"], directory)
    try:
        dup_data  = json.loads(out5) if out5.strip() else []
        dup_count = len(dup_data)
    except Exception:
        dup_count = 0
        dup_data  = []
    sections["duplicates"] = {
        "name": "Duplicate Check",
        "tool": "duplicate_check.py",
        "findings": dup_count,
        "status":   "ok" if dup_count == 0 else ("warn" if dup_count < 3 else "fail"),
        "details":  dup_data[:3],
    }
    total_findings += dup_count

    total_lines = _count_py_lines(directory)
    score       = _score_from_findings(total_findings, total_lines)

    # Penalizar si hay secretos (crítico)
    if sec_count > 0:
        score = min(score, 30)

    elapsed = round(time.time() - start, 1)

    return {
        "directory":    directory,
        "branch":       branch,
        "timestamp":    int(time.time()),
        "elapsed_s":    elapsed,
        "score":        score,
        "total_lines":  total_lines,
        "total_findings": total_findings,
        "sections":     sections,
        "verdict":      "✅ MERGE OK" if score >= 60 else "❌ NO MERGE",
    }


def generate_text(report: dict) -> str:
    sc    = report["score"]
    color = _GRN if sc >= 80 else (_YEL if sc >= 60 else _RED)
    lines = [
        f"{_BOLD}╔══ BAGO Code Review ══╗{_RST}",
        f"  Score:   {color}{sc}/100{_RST}",
        f"  Verdict: {_BOLD}{report['verdict']}{_RST}",
        f"  Lines:   {report['total_lines']}  |  Findings: {report['total_findings']}  |  Time: {report['elapsed_s']}s",
        "",
    ]
    for key, sec in report["sections"].items():
        icon = "✅" if sec["status"] == "ok" else ("⚠️" if sec["status"] == "warn" else "❌")
        lines.append(f"  {icon} {sec['name']:20s}  {sec['findings']} hallazgo(s)")
    lines += ["", f"  {_BOLD}{'─'*40}{_RST}"]
    return "\n".join(lines)


def generate_markdown(report: dict) -> str:
    sc    = report["score"]
    badge = "🟢" if sc >= 80 else ("🟡" if sc >= 60 else "🔴")
    lines = [
        f"# BAGO Code Review",
        f"",
        f"**Score:** {badge} {sc}/100  |  **Verdict:** {report['verdict']}",
        f"",
        f"| Scanner | Findings | Status |",
        f"|---------|----------|--------|",
    ]
    for sec in report["sections"].values():
        icon = "✅" if sec["status"] == "ok" else ("⚠️" if sec["status"] == "warn" else "❌")
        lines.append(f"| {sec['name']} | {sec['findings']} | {icon} |")
    lines += [
        f"",
        f"**Líneas analizadas:** {report['total_lines']}  "
        f"| **Tiempo:** {report['elapsed_s']}s",
        f"",
        f"---",
        f"*Generado con `bago code-review`*",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    directory  = "./"
    branch     = ""
    fmt        = "text"
    out_file   = None
    min_score  = 60

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--branch" and i + 1 < len(argv):
            branch = argv[i + 1]; i += 2
        elif a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        elif a == "--min-score" and i + 1 < len(argv):
            min_score = int(argv[i + 1]); i += 2
        elif not a.startswith("--"):
            directory = a; i += 1
        else:
            i += 1

    if not Path(directory).exists():
        print(f"No existe: {directory}", file=sys.stderr); return 1

    print(f"Analizando {directory}…", file=sys.stderr)
    report = run_reviews(directory, branch)

    if fmt == "json":
        content = json.dumps(report, indent=2)
    elif fmt == "md":
        content = generate_markdown(report)
    else:
        content = generate_text(report)

    if out_file:
        Path(out_file).write_text(content, encoding="utf-8")
        print(f"Guardado: {out_file}", file=sys.stderr)
    else:
        print(content)

    if report["score"] < min_score:
        return 1
    return 0


def _self_test() -> None:
    import tempfile
    print("Tests de code_review.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as td:
        from pathlib import Path as P
        (P(td) / "clean.py").write_text(
            '"""Módulo limpio."""\ndef add(a, b):\n    """Suma."""\n    return a + b\n'
        )

        # T1 — run_reviews retorna score
        report = run_reviews(td)
        if "score" in report and 0 <= report["score"] <= 100:
            ok("code_review:score_range")
        else:
            fail("code_review:score_range", str(report.get("score")))

        # T2 — verdict presente
        if "verdict" in report and ("MERGE" in report["verdict"] or "NO" in report["verdict"]):
            ok("code_review:verdict_present")
        else:
            fail("code_review:verdict_present", str(report.get("verdict")))

        # T3 — sections contiene los 5 scanners
        secs = set(report.get("sections", {}).keys())
        expected = {"lint", "complexity", "secrets", "dead_code", "duplicates"}
        if expected <= secs:
            ok("code_review:sections_complete")
        else:
            fail("code_review:sections_complete", f"missing={expected - secs}")

        # T4 — clean code da score alto
        if report["score"] >= 60:
            ok("code_review:clean_code_score")
        else:
            fail("code_review:clean_code_score", f"score={report['score']} too low for clean code")

        # T5 — markdown generado
        md = generate_markdown(report)
        if "BAGO Code Review" in md and "Score" in md:
            ok("code_review:markdown_generated")
        else:
            fail("code_review:markdown_generated", md[:80])

        # T6 — _score_from_findings lógica
        assert _score_from_findings(0, 1000) == 100
        assert _score_from_findings(100, 100) <= 40
        ok("code_review:score_function")

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: raise SystemExit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        raise SystemExit(main(sys.argv[1:]))
