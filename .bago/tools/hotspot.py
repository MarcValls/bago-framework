#!/usr/bin/env python3
"""
bago hotspot — detecta hotspots combinando frecuencia de cambios git,
hallazgos de análisis estático y complejidad del código.

Score = (commits × 3) + (findings_errors × 5) + (findings_warnings × 2)
        + (loc // 50) + (functions × 0.5) + (ci_failures × 8)

Soporta Python (.py), JavaScript/TypeScript (.js/.ts), Go (.go) y Rust (.rs).
Para Rust: análisis basado en git history + findings (sin complejidad AST).

Uso:
    bago hotspot                  → hotspot en .bago/tools/
    bago hotspot <ruta>           → hotspot en directorio dado
    bago hotspot --top N          → top N archivos (default 10)
    bago hotspot --since YYYY-MM  → solo commits desde fecha
    bago hotspot --lang py|js|go|auto  → fuerza lenguaje
    bago hotspot --json           → output JSON
    bago hotspot --heatmap        → mapa de calor ASCII
    bago hotspot --ci             → incluye historial de fallos CI de scans previos
    bago hotspot --test           → tests integrados
"""

import argparse, ast, json, re, subprocess, sys
from collections import defaultdict
from pathlib import Path
from typing import Optional

TOOLS_DIR = Path(__file__).parent
sys.path.insert(0, str(TOOLS_DIR))
import findings_engine as fe
try:
    from permission_fixer import run_with_permission_fix as _run_cmd, node_setup_hint
except ImportError:
    def _run_cmd(cmd, *, capture_output=True, text=True, timeout=60,  # type: ignore[misc]
                 cwd=None, env=None, silent=True, **_):
        return subprocess.run(cmd, capture_output=capture_output, text=text,
                              timeout=timeout, cwd=cwd, env=env)
    def node_setup_hint() -> str: return ""

BAGO_ROOT = Path(__file__).parent.parent
BOLD  = "\033[1m"; DIM = "\033[2m"; RESET = "\033[0m"
RED   = "\033[31m"; YELLOW = "\033[33m"; GREEN = "\033[32m"; CYAN = "\033[36m"
COLORS = [GREEN, CYAN, YELLOW, RED, "\033[91m"]   # cool → hot


# ─── Language detection ──────────────────────────────────────────────────────

def _detect_lang(target_dir: str) -> str:
    p = Path(target_dir)
    if not p.is_dir():
        return {"py": "py", ".js": "js", ".ts": "js", ".go": "go"}.get(
            Path(target_dir).suffix, "py")
    counts = {"py": 0, "js": 0, "go": 0}
    for f in p.rglob("*"):
        if f.suffix == ".py":              counts["py"] += 1
        elif f.suffix in (".js", ".ts"):   counts["js"] += 1
        elif f.suffix == ".go":            counts["go"] += 1
    dominant = max(counts, key=lambda k: counts[k])
    return dominant if counts[dominant] > 0 else "py"


def _glob_by_lang(target_dir: str, lang: str) -> list:
    p = Path(target_dir)
    if lang == "py":
        files = list(p.rglob("*.py"))
    elif lang in ("js", "ts"):
        files = list(p.rglob("*.js")) + list(p.rglob("*.ts"))
        files = [f for f in files if "node_modules" not in str(f)]
    elif lang == "go":
        files = [f for f in p.rglob("*.go") if "vendor" not in str(f)]
    elif lang == "rust":
        files = list(p.rglob("*.rs"))
    else:
        files = list(p.rglob("*.py"))
    return sorted(files)


# ─── Git change frequency ────────────────────────────────────────────────────

def git_commit_counts(target_dir: str, since: Optional[str] = None) -> dict:
    """Returns {filepath: commit_count} for all source files under target_dir."""
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
            if not line:
                continue
            # Match any source file under the target prefix
            rel_target = target_dir.replace(str(BAGO_ROOT.parent) + "/", "")
            if rel_target in line:
                counts[line] += 1
        return dict(counts)
    except Exception:
        return {}


# ─── CI failures from scan history ──────────────────────────────────────────

def ci_failures_by_file() -> dict:
    """Count how many scans each file appeared with errors (proxy for CI failures)."""
    findings_dir = BAGO_ROOT / "state" / "findings"
    counts: dict = defaultdict(int)
    scans = sorted(findings_dir.glob("SCAN-*.json"))[-20:]  # last 20 scans
    for scan_path in scans:
        try:
            data = json.loads(scan_path.read_text())
            seen_files: set = set()
            for f in data.get("findings", []):
                if f.get("severity") == "error" and f.get("file") not in seen_files:
                    counts[f["file"]] += 1
                    seen_files.add(f["file"])
        except Exception:
            pass
    return dict(counts)


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


# ─── JS/TS pre-compiled patterns ─────────────────────────────────────────────
_JS_FN_RE = re.compile(
    r'(?:'
    r'(?<!\w)(?:async\s+)?function\s*\*?\s*\w*\s*\('                          # function decl/expr
    r'|(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?(?:\([^)]*\)|\w+)\s*=>'    # arrow: const f = () =>
    r'|^\s{2,}(?:static\s+)?(?:async\s+)?(?:get\s+|set\s+)?'                 # method shorthand indent
    r'(?!(?:if|for|while|switch|return|else|try|catch|finally|throw'
    r'|new|typeof|delete|void|yield|await|import|export|class'
    r'|const|let|var|true|false|null|undefined)\b)'
    r'\w+\s*\([^)]*\)\s*\{)',                                                   # name(args) {
    re.MULTILINE,
)
_JS_CLASS_RE    = re.compile(r'(?<!\w)(?:abstract\s+)?class\s+\w+', re.MULTILINE)
_JS_SIMPLE_ARROW = re.compile(r'(?:const|let|var)\s+\w+\s*=\s*(?:async\s+)?\w+\s*=>\s*\S')


def _node_available() -> bool:
    """Return True if Node.js is available on PATH."""
    try:
        subprocess.run(["node", "--version"], capture_output=True, timeout=5, check=True)
        return True
    except Exception:
        return False


def node_setup_hint() -> str:
    """Return a human-readable hint for installing Node.js if missing."""
    if _node_available():
        return ""
    import platform
    sys_name = platform.system()
    if sys_name == "Darwin":
        cmd = "brew install node"
    elif sys_name == "Linux":
        cmd = "sudo apt install nodejs npm   # o: nvm install --lts"
    else:
        cmd = "https://nodejs.org"
    return (
        f"\n  ℹ  Node.js no encontrado — análisis JS/TS usa regex (menos preciso).\n"
        f"     Para análisis AST real: {cmd}\n"
        f"     Después: cd {BAGO_ROOT.parent} && npm install\n"
    )


def _count_js_ast_nodes(node: object) -> tuple:
    """Recursively count (functions, classes) in an acorn AST dict.
    Counts each function/arrow/expression exactly once at its own node level.
    """
    if not isinstance(node, dict):
        return 0, 0
    fn = cl = 0
    t = node.get("type", "")
    # Every callable is a FunctionDeclaration, FunctionExpression, or ArrowFunctionExpression
    if t in ("FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression"):
        fn += 1
    if t in ("ClassDeclaration", "ClassExpression"):
        cl += 1
    for val in node.values():
        if isinstance(val, dict):
            f2, c2 = _count_js_ast_nodes(val);  fn += f2; cl += c2
        elif isinstance(val, list):
            for item in val:
                f2, c2 = _count_js_ast_nodes(item); fn += f2; cl += c2
    return fn, cl


def _js_node_ast(filepath: str) -> Optional[dict]:
    """Parse JS file with npx acorn → accurate AST function/class count.

    Uses 'npx --yes acorn' so acorn is auto-downloaded on first use.
    TypeScript files are routed to _ts_node_ast() instead.
    Returns None if Node.js is unavailable or parsing fails → caller uses regex.
    """
    if filepath.endswith((".ts", ".tsx")):
        return _ts_node_ast(filepath)
    try:
        r = _run_cmd(
            ["npx", "--yes", "acorn", "--ecma2022", "--module", filepath],
            capture_output=True, text=True, timeout=30, silent=True,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return None
        ast_data = json.loads(r.stdout)
        fn, cl = _count_js_ast_nodes(ast_data)
        return {"functions": fn, "classes": cl}
    except Exception:
        return None


def _ts_node_ast(filepath: str) -> Optional[dict]:
    """Parse TypeScript/TSX with @typescript-eslint/typescript-estree via ts_ast.js.

    ts_ast.js must exist in the same directory as this file and requires
    @typescript-eslint/typescript-estree to be installed (via npm install).
    Returns None on any failure → caller falls back to enhanced regex.
    """
    ts_script = Path(__file__).parent / "ts_ast.js"
    if not ts_script.exists():
        return None
    try:
        r = _run_cmd(
            ["node", str(ts_script), filepath],
            capture_output=True, text=True, timeout=30, silent=True,
        )
        if r.returncode != 0 or not r.stdout.strip():
            return None
        ast_data = json.loads(r.stdout)
        fn, cl = _count_ts_ast_nodes(ast_data)
        return {"functions": fn, "classes": cl}
    except Exception:
        return None


def _count_ts_ast_nodes(node: object) -> tuple:
    """Count (functions, classes) in a TypeScript ESTree AST.

    Same as _count_js_ast_nodes but also handles TypeScript-specific nodes:
    - TSMethodSignature (interface method signature — NOT a body, skip)
    - TSFunctionType (type annotation — NOT a body, skip)
    - MethodDefinition inside ClassBody IS counted via its FunctionExpression value.
    We intentionally do NOT count TSMethodSignature/TSFunctionType because they
    are type declarations without executable bodies.
    """
    if not isinstance(node, dict):
        return 0, 0
    fn = cl = 0
    t = node.get("type", "")
    if t in ("FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression"):
        fn += 1
    if t in ("ClassDeclaration", "ClassExpression"):
        cl += 1
    for val in node.values():
        if isinstance(val, dict):
            f2, c2 = _count_ts_ast_nodes(val);  fn += f2; cl += c2
        elif isinstance(val, list):
            for item in val:
                f2, c2 = _count_ts_ast_nodes(item); fn += f2; cl += c2
    return fn, cl


def analyze_js_complexity(filepath: str) -> dict:
    """JS/TS complexity: LOC + accurate function/class count.

    Primary: Node.js + acorn AST (catches arrow fns, method shorthands,
             object literal methods, getters/setters).
    Fallback: enhanced regex covering the same patterns without Node.js.
    """
    try:
        src   = Path(filepath).read_text(errors="replace")
        lines = src.splitlines()
        loc   = sum(1 for l in lines if l.strip() and not l.strip().startswith("//"))

        # Try accurate AST parse via Node.js first
        ast_result = _js_node_ast(filepath)
        if ast_result:
            return {"loc": loc, "functions": ast_result["functions"],
                    "classes": ast_result["classes"], "max_nesting": 0}

        # Enhanced regex fallback — covers what the old single-pattern missed
        funcs   = len(_JS_FN_RE.findall(src)) + len(_JS_SIMPLE_ARROW.findall(src))
        classes = len(_JS_CLASS_RE.findall(src))
        return {"loc": loc, "functions": funcs, "classes": classes, "max_nesting": 0}
    except Exception:
        return {"loc": 0, "functions": 0, "classes": 0, "max_nesting": 0}


def analyze_go_complexity(filepath: str) -> dict:
    """Rough Go complexity: LOC + func count via regex."""
    try:
        src   = Path(filepath).read_text(errors="replace")
        lines = src.splitlines()
        loc   = sum(1 for l in lines if l.strip() and not l.strip().startswith("//"))
        funcs = len(re.findall(r'^\s*func\s+', src, re.MULTILINE))
        structs = len(re.findall(r'^\s*type\s+\w+\s+struct\b', src, re.MULTILINE))
        return {"loc": loc, "functions": funcs, "classes": structs, "max_nesting": 0}
    except Exception:
        return {"loc": 0, "functions": 0, "classes": 0, "max_nesting": 0}


def analyze_rust_complexity(filepath: str) -> dict:
    """Rust complexity: LOC + pub/priv function count + impl blocks + struct count.

    Uses regex — reliable for Rust's regular syntax. Counts:
    - pub fn / pub async fn / pub unsafe fn  → public functions
    - fn (non-pub, non-test)                 → private functions
    - structs (pub or private)               → classes proxy
    """
    try:
        src   = Path(filepath).read_text(errors="replace")
        lines = src.splitlines()
        loc   = sum(1 for l in lines if l.strip()
                    and not l.strip().startswith("//")
                    and not l.strip().startswith("///"))
        pub_fns = len(re.findall(
            r'^\s*pub\s+(?:async\s+|unsafe\s+|extern\s+"[^"]+"\s+)?fn\s+\w+',
            src, re.MULTILINE))
        all_fns = len(re.findall(r'^\s*(?:pub\s+)?(?:async\s+|unsafe\s+)?fn\s+\w+',
                                  src, re.MULTILINE))
        test_fns = len(re.findall(r'^\s*fn\s+test_\w+', src, re.MULTILINE))
        total_fns = max(0, all_fns - test_fns)
        structs = len(re.findall(r'^\s*(?:pub(?:\s*\([^)]*\))?\s+)?struct\s+\w+',
                                  src, re.MULTILINE))
        return {"loc": loc, "functions": total_fns, "classes": structs, "max_nesting": 0}
    except Exception:
        return {"loc": 0, "functions": 0, "classes": 0, "max_nesting": 0}


def _analyze_file(filepath: str, lang: str) -> dict:
    if lang == "py":
        return analyze_complexity(filepath)
    elif lang in ("js", "ts"):
        return analyze_js_complexity(filepath)
    elif lang == "go":
        return analyze_go_complexity(filepath)
    elif lang == "rust":
        return analyze_rust_complexity(filepath)
    return analyze_complexity(filepath)


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

def compute_hotspots(target_dir: str, since: Optional[str], top_n: int,
                     lang: str = "auto", include_ci: bool = False) -> list:
    if lang == "auto":
        lang = _detect_lang(target_dir)

    source_files = _glob_by_lang(target_dir, lang)
    commits      = git_commit_counts(target_dir, since)
    find_data    = findings_by_file()
    ci_data      = ci_failures_by_file() if include_ci else {}

    results = []
    for f in source_files:
        rel = str(f)
        short = rel.replace(str(BAGO_ROOT.parent) + "/", "")

        cmx   = commits.get(short, commits.get(rel, 0))
        fd    = find_data.get(rel, find_data.get(short, {"errors":0,"warnings":0,"total":0}))
        comp  = _analyze_file(rel, lang)
        ci_f  = ci_data.get(rel, ci_data.get(short, 0))

        score = (
            cmx    * 3 +
            fd["errors"]   * 5 +
            fd["warnings"] * 2 +
            comp["loc"] // 50 +
            int(comp["functions"] * 0.5) +
            ci_f   * 8
        )
        results.append({
            "file":        short,
            "score":       score,
            "commits":     cmx,
            "errors":      fd["errors"],
            "warnings":    fd["warnings"],
            "findings":    fd["total"],
            "loc":         comp["loc"],
            "functions":   comp["functions"],
            "max_nesting": comp["max_nesting"],
            "ci_failures": ci_f,
            "lang":        lang,
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
        print("\n  Sin archivos de código fuente en el directorio objetivo.\n")
        return

    max_score = hotspots[0]["score"] if hotspots else 1
    lang = hotspots[0].get("lang", "py") if hotspots else "py"

    print(f"\n  {BOLD}BAGO Hotspots{RESET}  [{lang}]\n")

    if heatmap:
        print(f"  {'Archivo':45s}  {'Score':>6}  {'Commits':>7}  {'Findings':>8}  {'LOC':>5}  {'CI↑':>4}  Calor")
        print(f"  {'─'*45}  {'─'*6}  {'─'*7}  {'─'*8}  {'─'*5}  {'─'*4}  {'─'*20}")
        for h in hotspots:
            bar   = _heat_bar(h["score"], max_score)
            short = h["file"][-45:] if len(h["file"]) > 45 else h["file"]
            e_col = RED if h["errors"] > 0 else RESET
            ci_col = YELLOW if h.get("ci_failures",0) > 0 else DIM
            print(f"  {short:45s}  {h['score']:6d}  {h['commits']:7d}  "
                  f"{e_col}{h['findings']:8d}{RESET}  {h['loc']:5d}  "
                  f"{ci_col}{h.get('ci_failures',0):4d}{RESET}  {bar}")
    else:
        print(f"  {'#':3}  {'Score':>6}  {'File'}")
        print(f"  {'─'*3}  {'─'*6}  {'─'*50}")
        for i, h in enumerate(hotspots, 1):
            bucket = min(4, int(h["score"] / max(max_score,1) * 5))
            color  = COLORS[bucket]
            short  = h["file"][-55:] if len(h["file"]) > 55 else h["file"]
            print(f"  {i:3d}  {color}{h['score']:6d}{RESET}  {short}")
            detail = []
            if h["commits"]:                detail.append(f"commits={h['commits']}")
            if h["errors"]:                 detail.append(f"{RED}errors={h['errors']}{RESET}")
            if h["warnings"]:               detail.append(f"{YELLOW}warns={h['warnings']}{RESET}")
            if h.get("ci_failures",0) > 0:  detail.append(f"{YELLOW}ci_fails={h['ci_failures']}{RESET}")
            detail.append(f"loc={h['loc']}")
            detail.append(f"fns={h['functions']}")
            if detail:
                print(f"       {DIM}{' · '.join(detail)}{RESET}")

    # Risk summary
    critical = [h for h in hotspots if h["errors"] > 0]
    ci_risky = [h for h in hotspots if h.get("ci_failures", 0) >= 3]
    if critical:
        print(f"\n  {RED}{BOLD}⚠ Archivos con errores ({len(critical)}):{RESET}")
        for h in critical:
            print(f"    {h['file']}  ({h['errors']} errores)")
    if ci_risky:
        print(f"\n  {YELLOW}{BOLD}⚠ Hotspots por fallos CI repetidos ({len(ci_risky)}):{RESET}")
        for h in ci_risky:
            print(f"    {h['file']}  ({h['ci_failures']} scans con error)")
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
    if errors: raise SystemExit(1)

    # ── Extended tests ─────────────────────────────────────────────────────
    errors2 = 0
    print("\nTests de multi-lenguaje y CI failures...")
    tmp2 = Path(tempfile.mkdtemp())

    # T6: analyze_js_complexity — covers function, arrow+braces, arrow no-braces,
    #     method shorthand, getter, class (separated from functions)
    js = tmp2 / "app.js"
    js.write_text(
        "function foo() {}\n"                      # regular function
        "const bar = () => { return 1; }\n"        # arrow with braces
        "const baz = x => x + 1\n"                 # arrow without braces  ← was missed
        "const obj = {\n"
        "  method() { return 0; }\n"               # object literal shorthand ← was missed
        "}\n"
        "class Baz {\n"
        "  get value() { return 1; }\n"            # getter ← was missed
        "}\n"
    )
    cj = analyze_js_complexity(str(js))
    if cj["functions"] >= 4 and cj["classes"] >= 1 and cj["loc"] >= 5:
        print("  OK: hotspot:js_complexity")
    else:
        errors2 += 1; print(f"  FAIL: hotspot:js_complexity — {cj}")

    # T7: analyze_go_complexity
    go = tmp2 / "main.go"
    go.write_text("package main\nfunc Foo() {}\nfunc Bar() int { return 1 }\ntype Point struct{ X int }\n")
    cg = analyze_go_complexity(str(go))
    if cg["functions"] == 2 and cg["classes"] == 1:
        print("  OK: hotspot:go_complexity")
    else:
        errors2 += 1; print(f"  FAIL: hotspot:go_complexity — {cg}")

    # T8: compute_hotspots with lang=js returns js files
    hotspots_js = compute_hotspots(str(tmp2), None, 10, lang="js")
    if all(h["lang"] == "js" for h in hotspots_js):
        print("  OK: hotspot:lang_js_filter")
    else:
        errors2 += 1; print(f"  FAIL: hotspot:lang_js_filter — {hotspots_js}")

    # T9: ci_failures_by_file returns dict
    ci = ci_failures_by_file()
    if isinstance(ci, dict):
        print("  OK: hotspot:ci_failures_dict")
    else:
        errors2 += 1; print(f"  FAIL: hotspot:ci_failures_dict — {type(ci)}")

    # T10: TypeScript AST via typescript-estree (if available)
    ts_src = (
        "interface IGreeter { greet(name: string): void; }\n"
        "class Greeter implements IGreeter {\n"
        "  private name: string;\n"
        "  constructor(name: string) { this.name = name; }\n"
        "  greet(name: string): void { console.log('hi'); }\n"
        "  private helper = (x: number): number => x * 2;\n"
        "}\n"
        "export function createGreeter(n: string): IGreeter { return new Greeter(n); }\n"
        "export const greetAll = async (names: string[]): Promise<void> => {};\n"
    )
    ts_file = tmp2 / "greeter.ts"
    ts_file.write_text(ts_src)
    ct = analyze_js_complexity(str(ts_file))
    # Should detect: constructor, greet, helper arrow, createGreeter, greetAll = 5 funcs, 1 class
    ts_ast_ok = ct["functions"] >= 4 and ct["classes"] >= 1 and ct["loc"] >= 7
    if ts_ast_ok:
        mode = "AST" if _ts_node_ast(str(ts_file)) else "regex"
        print(f"  OK: hotspot:ts_complexity ({mode}) — {ct['functions']} fns, {ct['classes']} class")
    else:
        errors2 += 1; print(f"  FAIL: hotspot:ts_complexity — {ct}")

    # T11: analyze_rust_complexity
    rs_file = tmp2 / "lib.rs"
    rs_file.write_text(
        "pub struct Config { pub value: u32 }\n"
        "struct Internal { data: Vec<u8> }\n"
        "pub fn process(cfg: &Config) -> u32 { cfg.value }\n"
        "pub async fn fetch(url: &str) -> String { url.to_string() }\n"
        "fn helper() -> bool { true }\n"
        "fn test_helper() { assert!(true); }\n"   # should NOT count (test)
    )
    cr = analyze_rust_complexity(str(rs_file))
    # Expected: 3 fns (process, fetch, helper — test_helper excluded), 2 structs
    if cr["functions"] == 3 and cr["classes"] == 2 and cr["loc"] >= 5:
        print(f"  OK: hotspot:rust_complexity — {cr['functions']} fns, {cr['classes']} structs")
    else:
        errors2 += 1; print(f"  FAIL: hotspot:rust_complexity — {cr}")

    shutil.rmtree(tmp2)
    total2 = 6; passed2 = total2 - errors2
    print(f"\n  {passed2}/{total2} tests multi-lenguaje pasaron")
    if errors2: raise SystemExit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago hotspot", add_help=False)
    parser.add_argument("target", nargs="?", default=str(BAGO_ROOT / "tools"))
    parser.add_argument("--top",     type=int, default=10)
    parser.add_argument("--since",   default=None)
    parser.add_argument("--lang",    default="auto",
                        choices=["auto","py","js","ts","go","rust"],
                        help="Lenguaje a analizar (default: auto-detección)")
    parser.add_argument("--ci",      action="store_true",
                        help="Incluir historial de fallos CI de scans previos")
    parser.add_argument("--json",    action="store_true")
    parser.add_argument("--heatmap", action="store_true")
    parser.add_argument("--test",    action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests(); return

    lang = "js" if args.lang == "ts" else args.lang
    hotspots = compute_hotspots(args.target, args.since, args.top,
                                lang=lang, include_ci=args.ci)
    render_hotspots(hotspots, args.json, args.heatmap)

if __name__ == "__main__":
    main()