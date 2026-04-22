#!/usr/bin/env python3
"""coverage_gate.py — Herramienta #119: Quality gate de cobertura de tests.

Ejecuta pytest --cov y compara el resultado contra un umbral configurable.
Si la cobertura cae por debajo del umbral, sale con código 1 (CI fail).
Persiste la cobertura histórica para detectar regresiones.

Uso:
    bago coverage-gate [DIR] [--threshold N] [--save] [--compare]
                       [--format text|json] [--test-cmd CMD] [--test]

Opciones:
    --threshold N   Cobertura mínima % (default: 80)
    --save          Guarda cobertura actual como baseline
    --compare       Compara con baseline guardada; falla si baja
    --test-cmd CMD  Comando personalizado de tests (default: pytest --cov)
    --test          Self-tests
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from pathlib import Path

_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RED  = "\033[0;31m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

BASELINE_FILE = ".bago_coverage_baseline.json"


def run_coverage(test_cmd: str, directory: str) -> dict:
    """Ejecuta tests y parsea el % de cobertura del output."""
    cmd  = test_cmd.split() if isinstance(test_cmd, str) else test_cmd
    # Asegurar que usamos --cov y --cov-report=term
    if "pytest" in cmd[0] and "--cov-report" not in " ".join(cmd):
        cmd += ["--cov-report=term-missing", "--tb=no", "-q"]
    if "pytest" in cmd[0] and "--cov" not in " ".join(cmd):
        cmd += [f"--cov={directory}"]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=300, cwd=directory
        )
        output = result.stdout + result.stderr
        return _parse_coverage_output(output, result.returncode)
    except FileNotFoundError:
        return {"error": "pytest not found", "coverage": None, "rc": -1, "output": ""}
    except subprocess.TimeoutExpired:
        return {"error": "timeout", "coverage": None, "rc": -2, "output": ""}


def _parse_coverage_output(output: str, rc: int) -> dict:
    """Parsea el % de cobertura total del output de pytest-cov."""
    # Buscar línea como "TOTAL   1234   100   80%"
    total_re = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", output)
    if total_re:
        coverage = int(total_re.group(1))
        return {"coverage": coverage, "rc": rc, "output": output, "error": None}

    # Línea simplificada "Coverage: 85%"
    simple = re.search(r"[Cc]overage[:\s]+(\d+)\s*%", output)
    if simple:
        coverage = int(simple.group(1))
        return {"coverage": coverage, "rc": rc, "output": output, "error": None}

    return {"coverage": None, "rc": rc, "output": output,
            "error": "No se pudo parsear cobertura del output"}


def save_baseline(coverage: int, directory: str) -> None:
    baseline = {
        "coverage":  coverage,
        "timestamp": int(time.time()),
        "directory": directory,
    }
    baseline_path = Path(directory) / BASELINE_FILE
    baseline_path.write_text(json.dumps(baseline, indent=2))


def load_baseline(directory: str) -> dict | None:
    baseline_path = Path(directory) / BASELINE_FILE
    if not baseline_path.exists():
        return None
    try:
        return json.loads(baseline_path.read_text())
    except Exception:
        return None


def check_gate(coverage: int, threshold: int,
               baseline: dict | None, compare: bool) -> tuple[bool, str]:
    """Retorna (passed, message)."""
    color  = _GRN if coverage >= threshold else _RED
    msgs   = [f"  Cobertura: {color}{coverage}%{_RST}  (umbral: {threshold}%)"]
    passed = coverage >= threshold

    if compare and baseline:
        prev = baseline.get("coverage", 0)
        diff = coverage - prev
        arrow = "↑" if diff > 0 else ("↓" if diff < 0 else "→")
        diff_color = _GRN if diff >= 0 else _RED
        msgs.append(f"  Baseline:  {prev}%  {diff_color}{arrow} {diff:+d}pp{_RST}")
        if diff < 0:
            passed = False
            msgs.append(f"  {_RED}❌ Regresión de cobertura: bajó {abs(diff)}pp{_RST}")

    if not passed and coverage < threshold:
        msgs.append(f"  {_RED}❌ Cobertura {coverage}% < umbral {threshold}%{_RST}")
    elif passed:
        msgs.append(f"  {_GRN}✅ Quality gate OK{_RST}")

    return passed, "\n".join(msgs)


def main(argv: list[str]) -> int:
    directory  = "./"
    threshold  = 80
    save       = False
    compare    = False
    fmt        = "text"
    test_cmd   = "pytest --cov"

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--threshold" and i + 1 < len(argv):
            threshold = int(argv[i + 1]); i += 2
        elif a == "--save":
            save = True; i += 1
        elif a == "--compare":
            compare = True; i += 1
        elif a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--test-cmd" and i + 1 < len(argv):
            test_cmd = argv[i + 1]; i += 2
        elif not a.startswith("--"):
            directory = a; i += 1
        else:
            i += 1

    if not Path(directory).exists():
        print(f"No existe: {directory}", file=sys.stderr); return 1

    print(f"Ejecutando tests en {directory}…", file=sys.stderr)
    result = run_coverage(test_cmd, directory)

    if result.get("error") and result["coverage"] is None:
        print(f"{_RED}Error: {result['error']}{_RST}", file=sys.stderr)
        if result.get("output"):
            print(result["output"][-500:], file=sys.stderr)
        return 1

    cov      = result["coverage"] or 0
    baseline = load_baseline(directory) if compare else None
    passed, msg = check_gate(cov, threshold, baseline, compare)

    if fmt == "json":
        out = {"coverage": cov, "threshold": threshold, "passed": passed,
               "baseline": baseline}
        print(json.dumps(out, indent=2))
    else:
        print(f"\n{_BOLD}Coverage Gate{_RST}")
        print(msg)

    if save and result["coverage"] is not None:
        save_baseline(result["coverage"], directory)
        print(f"  Baseline guardada: {cov}%", file=sys.stderr)

    return 0 if passed else 1


def _self_test() -> None:
    import tempfile
    print("Tests de coverage_gate.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    # T1 — _parse_coverage_output parsea TOTAL line
    out = "TOTAL        1234     100      80%\n"
    r = _parse_coverage_output(out, 0)
    if r["coverage"] == 80:
        ok("coverage_gate:parse_total_line")
    else:
        fail("coverage_gate:parse_total_line", str(r))

    # T2 — formato Coverage: 85%
    out2 = "Coverage: 85%\n"
    r2 = _parse_coverage_output(out2, 0)
    if r2["coverage"] == 85:
        ok("coverage_gate:parse_simple_format")
    else:
        fail("coverage_gate:parse_simple_format", str(r2))

    # T3 — output sin cobertura → error
    r3 = _parse_coverage_output("No tests found\n", 1)
    if r3["coverage"] is None:
        ok("coverage_gate:no_coverage_in_output")
    else:
        fail("coverage_gate:no_coverage_in_output", str(r3))

    # T4 — check_gate pasa con cobertura >= threshold
    passed, msg = check_gate(85, 80, None, False)
    if passed and "OK" in msg:
        ok("coverage_gate:gate_pass")
    else:
        fail("coverage_gate:gate_pass", f"passed={passed} msg={msg}")

    # T5 — check_gate falla con regresión
    baseline = {"coverage": 90}
    passed2, msg2 = check_gate(85, 80, baseline, compare=True)
    if not passed2 and "Regresión" in msg2:
        ok("coverage_gate:regression_detected")
    else:
        fail("coverage_gate:regression_detected", f"passed={passed2} msg={msg2}")

    # T6 — save/load baseline roundtrip
    with tempfile.TemporaryDirectory() as td:
        save_baseline(75, td)
        b = load_baseline(td)
        if b and b["coverage"] == 75:
            ok("coverage_gate:baseline_roundtrip")
        else:
            fail("coverage_gate:baseline_roundtrip", str(b))

    total = 6; passed_count = total - len(fails)
    print(f"\n  {passed_count}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
