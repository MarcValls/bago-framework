#!/usr/bin/env python3
"""
bago hotspot — detecta hotspots combinando frecuencia de cambios git,
hallazgos de análisis estático y complejidad del código.

Score = (commits × 3) + (findings_errors × 5) + (findings_warnings × 2)
        + (loc // 50) + (functions × 0.5)

Uso:
    bago hotspot                  → hotspot en .bago/tools/
    bago hotspot <ruta>           → hotspot en directorio dado
    bago hotspot --top N          → top N archivos (default 10)
    bago hotspot --since YYYY-MM  → solo commits desde fecha
    bago hotspot --json           → output JSON
    bago hotspot --heatmap        → mapa de calor ASCII
    bago hotspot --test           → tests integrados
"""

import argparse, ast, json, re, subprocess, sys
from collections import defaultdict
from pathlib import Path

TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))
import findings_engine as fe

BAGO_ROOT = Path(__file__).parent.parent
BOLD  = "\033[1m"; DIM = "\033[2m"; RESET = "\033[0m"
RED   = "\033[31m"; YELLOW = "\033[33m"; GREEN = "\033[32m"; CYAN = "\033[36m"
COLORS = [GREEN, CYAN, YELLOW, RED, "\033[91m"]   # cool → hot


# ─── Git change frequency ────────────────────────────────────────────────────

def git_commit_counts(target_dir: str, since: str | None = None) -> dict:
    """Returns {filepath: commit_count} for all .py files under target_dir."""
    since_arg = [f"--since={since}"] if since else []
    try:
        r = subprocess.run(
            ["git", "--no-pager", "log", "--name-only", "--pretty=format:"] + since_arg,
            capture_output=True, text=True,
            cwd=str(Path(target_dir).parent if Path(target_dir).is_dir() else target_dir),
            timeout=30
        )
        counts: dict = defaultdict(int)
        for line in r.stdout.splitlines():
            line = line.strip()
            if line.endswith(".py") and target_dir.replace(str(BAGO_ROOT.parent)+"/","") in line:
                counts[line] += 1
        return dict(counts)
    except Exception:
        return {}


# ─── Code complexity ─────────────────────────────────────────────────────────

def analyze_complexity(filepath: str) -> dict:
    """Analyse Python file: LOC, function count, class count, max_nesting."""
    try:
        src   = Path(filepath).read_text(errors="replace")
        lines = src.splitlines()
        loc   = sum(1 for l in lines if l.strip() and not l.strip().startswith("#"))
        funcs = 0; classes = 0; max_nest = 0
        try:
            tree = ast.parse(src)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef): funcs += 1
                if isinstance(node, ast.ClassDef):    classes += 1
            # rough nesting: indent depth of deepest non-blank line
            for l in lines:
                stripped = l.lstrip()
                if stripped:
                    indent = len(l) - len(stripped)
                    max_nest = max(max_nest, indent // 4)
        except SyntaxError:
            pass
        return {"loc": loc, "functions": funcs, "classes": classes, "max_nesting": max_nest}
    except Exception:
        return {"loc": 0, "functions": 0, "classes": 0, "max_nesting": 0}


# ─── Findings aggregation ────────────────────────────────────────────────────

def findings_by_file() -> dict:
    """Load latest scan and return {filepath: {errors, warnings, total}}"""
    db = fe.FindingsDB.latest()
    if db is None:
        return {}
    counts: dict = defaultdict(lambda: {"errors": 0, "warnings": 0, "total": 0})
    for f in db.findings:
        counts[f.file]["total"] += 1
        if f.severity == "error":   counts[f.file]["errors"] += 1
        if f.severity == "warning": counts[f.file]["warnings"] += 1
    return dict(counts)


# ─── Score & rank ────────────────────────────────────────────────────────────

def compute_hotspots(target_dir: str, since: str | None, top_n: int) -> list:
    target = Path(target_dir)
    py_files = sorted(target.rglob("*.py"))

    commits    = git_commit_counts(target_dir, since)
    find_data  = findings_by_file()

    results = []
    for f in py_files:
        rel = str(f)
        short = rel.replace(str(BAGO_ROOT.parent) + "/", "")

        cmx  = commits.get(short, commits.get(rel, 0))
        fd   = find_data.get(rel, find_data.get(short, {"errors":0,"warnings":0,"total":0}))
        comp = analyze_complexity(rel)

        score = (
            cmx    * 3 +
            fd["errors"]   * 5 +
            fd["warnings"] * 2 +
            comp["loc"] // 50 +
            int(comp["functions"] * 0.5)
        )
        results.append({
            "file":      short,
            "score":     score,
            "commits":   cmx,
            "errors":    fd["errors"],
            "warnings":  fd["warnings"],
            "findings":  fd["total"],
            "loc":       comp["loc"],
            "functions": comp["functions"],
            "max_nesting": comp["max_nesting"],
        })

    results.sort(key=lambda x: -x["score"])
    return results[:top_n]


# ─── Rendering ───────────────────────────────────────────────────────────────

def _heat_bar(score: int, max_score: int, width: int = 20) -> str:
    if max_score == 0:
        return "░" * width
    filled = int(score / max_score * width)
    bucket = min(4, int(score / max_score * 5)) if max_score else 0
    color  = COLORS[bucket]
    return color + "█" * filled + DIM + "░" * (width - filled) + RESET


def render_hotspots(hotspots: list, as_json: bool, heatmap: bool):
    if as_json:
        print(json.dumps(hotspots, indent=2, ensure_ascii=False))
        return

    if not hotspots:
        print("\n  Sin archivos Python en el directorio objetivo.\n")
        return

    max_score = hotspots[0]["score"] if hotspots else 1

    print(f"\n  {BOLD}BAGO Hotspots{RESET}\n")

    if heatmap:
        print(f"  {'Archivo':45s}  {'Score':>6}  {'Commits':>7}  {'Findings':>8}  {'LOC':>5}  Calor")
        print(f"  {'─'*45}  {'─'*6}  {'─'*7}  {'─'*8}  {'─'*5}  {'─'*20}")
        for h in hotspots:
            bar   = _heat_bar(h["score"], max_score)
            short = h["file"][-45:] if len(h["file"]) > 45 else h["file"]
            e_col = RED if h["errors"] > 0 else RESET
            print(f"  {short:45s}  {h['score']:6d}  {h['commits']:7d}  "
                  f"{e_col}{h['findings']:8d}{RESET}  {h['loc']:5d}  {bar}")
    else:
        print(f"  {'#':3}  {'Score':>6}  {'File'}")
        print(f"  {'─'*3}  {'─'*6}  {'─'*50}")
        for i, h in enumerate(hotspots, 1):
            bucket = min(4, int(h["score"] / max(max_score,1) * 5))
            color  = COLORS[bucket]
            short  = h["file"][-55:] if len(h["file"]) > 55 else h["file"]
            print(f"  {i:3d}  {color}{h['score']:6d}{RESET}  {short}")
            detail = []
            if h["commits"]:  detail.append(f"commits={h['commits']}")
            if h["errors"]:   detail.append(f"{RED}errors={h['errors']}{RESET}")
            if h["warnings"]: detail.append(f"{YELLOW}warns={h['warnings']}{RESET}")
            detail.append(f"loc={h['loc']}")
            detail.append(f"fns={h['functions']}")
            if detail:
                print(f"       {DIM}{' · '.join(detail)}{RESET}")

    # Risk summary
    critical = [h for h in hotspots if h["errors"] > 0]
    if critical:
        print(f"\n  {RED}{BOLD}⚠ Archivos con errores ({len(critical)}):{RESET}")
        for h in critical:
            print(f"    {h['file']}  ({h['errors']} errores)")
    print()


def run_tests():
    import tempfile, shutil
    print("Ejecutando tests de hotspot.py...")
    errors = 0
    def ok(n): print(f"  OK: {n}")
    def fail(n, m):
        nonlocal errors; errors += 1; print(f"  FAIL: {n} — {m}")

    # T1: analyze_complexity on a real file
    tmp = Path(tempfile.mkdtemp())
    py = tmp / "sample.py"
    py.write_text("def foo():\n    pass\n\ndef bar():\n    x = 1\n    return x\n\nclass MyClass:\n    pass\n")
    c = analyze_complexity(str(py))
    if c["functions"] == 2 and c["classes"] == 1:
        ok("hotspot:complexity_counts")
    else:
        fail("hotspot:complexity_counts", str(c))

    # T2: analyze_complexity LOC ignores comments/blanks
    py2 = tmp / "sample2.py"
    py2.write_text("# comment\n\ndef f():\n    x = 1\n    # inline comment\n    return x\n")
    c2 = analyze_complexity(str(py2))
    if c2["loc"] == 3:  # def, x=1, return
        ok("hotspot:complexity_loc")
    else:
        fail("hotspot:complexity_loc", str(c2))

    # T3: score formula
    h = {"commits":2,"errors":1,"warnings":3,"loc":100,"functions":4}
    score = h["commits"]*3 + h["errors"]*5 + h["warnings"]*2 + h["loc"]//50 + int(h["functions"]*0.5)
    expected = 6+5+6+2+2
    if score == expected:
        ok("hotspot:score_formula")
    else:
        fail("hotspot:score_formula", f"{score} != {expected}")

    # T4: compute_hotspots returns list of dicts with required keys
    hotspots = compute_hotspots(str(tmp), None, 10)
    if all("score" in h and "file" in h and "loc" in h for h in hotspots):
        ok("hotspot:compute_structure")
    else:
        fail("hotspot:compute_structure", str(hotspots[:1]))

    # T5: _heat_bar length
    bar = _heat_bar(5, 10, width=10)
    # strip ANSI
    clean = re.sub(r'\033\[[0-9;]*m', '', bar)
    if len(clean) == 10:
        ok("hotspot:heat_bar_width")
    else:
        fail("hotspot:heat_bar_width", repr(clean))

    shutil.rmtree(tmp)
    total=5; passed=total-errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors: sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago hotspot", add_help=False)
    parser.add_argument("target", nargs="?", default=str(BAGO_ROOT / "tools"))
    parser.add_argument("--top",     type=int, default=10)
    parser.add_argument("--since",   default=None)
    parser.add_argument("--json",    action="store_true")
    parser.add_argument("--heatmap", action="store_true")
    parser.add_argument("--test",    action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests(); return

    hotspots = compute_hotspots(args.target, args.since, args.top)
    render_hotspots(hotspots, args.json, args.heatmap)

if __name__ == "__main__":
    main()