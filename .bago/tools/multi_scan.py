#!/usr/bin/env python3
"""
bago multi-scan — Escanea TODOS los lenguajes presentes en un proyecto.

A diferencia de `bago scan` (un solo lenguaje dominante), multi-scan detecta
todos los lenguajes presentes y ejecuta los linters apropiados para cada uno,
devolviendo hallazgos agregados en un único informe.

Lenguajes soportados:
  Python  — flake8 + pylint + mypy + bandit + bago-lint
  JS/TS   — ESLint (via npx)
  Go      — golangci-lint
  Rust    — cargo clippy

Usage:
    bago multi-scan [path]            escanear todo (default: directorio actual)
    bago multi-scan --langs py,js     forzar lenguajes (ignorar detección)
    bago multi-scan --json            output JSON
    bago multi-scan --summary         solo totales por lenguaje/regla
    bago multi-scan --since FILE      diff contra snapshot previo
    bago multi-scan --min-severity W  umbral mínimo: E=error, W=warning, I=info
    bago multi-scan --test            ejecutar self-tests
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

BAGO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).parent))

try:
    import findings_engine as fe
except ImportError:
    print("ERROR: findings_engine.py no encontrado", file=sys.stderr)
    raise SystemExit(1)

try:
    import scan as scan_mod
except ImportError:
    scan_mod = None  # type: ignore

# ── ANSI ─────────────────────────────────────────────────────────────────────
_TTY = sys.stdout.isatty()
GREEN  = "\033[32m" if _TTY else ""
YELLOW = "\033[33m" if _TTY else ""
RED    = "\033[31m" if _TTY else ""
BLUE   = "\033[34m" if _TTY else ""
DIM    = "\033[2m"  if _TTY else ""
BOLD   = "\033[1m"  if _TTY else ""
RESET  = "\033[0m"  if _TTY else ""

_SEV_COLOR = {"error": RED, "warning": YELLOW, "info": BLUE, "hint": DIM}

_SEVERITY_RANK = {"error": 3, "warning": 2, "info": 1, "hint": 0}

# ── Language detection ────────────────────────────────────────────────────────

def detect_all_langs(target: str) -> List[str]:
    """Return all languages present in target (not just the dominant one)."""
    counts = {"py": 0, "js": 0, "go": 0, "rust": 0}
    ext_map = {
        ".py": "py",
        ".js": "js", ".ts": "js", ".jsx": "js", ".tsx": "js",
        ".go": "go",
        ".rs": "rust",
    }
    manifest_map = {
        "package.json": "js",
        "go.mod": "go",
        "Cargo.toml": "rust",
        "requirements.txt": "py",
        "setup.py": "py",
        "pyproject.toml": "py",
    }

    p = Path(target)
    if not p.is_dir():
        suf = p.suffix.lower()
        lang = ext_map.get(suf)
        return [lang] if lang else []

    for item in p.rglob("*"):
        if any(part.startswith(".") or part == "node_modules" or part == "__pycache__"
               for part in item.parts):
            continue
        if item.is_file():
            name = item.name.lower()
            if name in manifest_map:
                counts[manifest_map[name]] += 1
            suf = item.suffix.lower()
            lang = ext_map.get(suf)
            if lang:
                counts[lang] += 1

    return [lang for lang, count in counts.items() if count > 0]


# ── Per-language scan ─────────────────────────────────────────────────────────

def _scan_python(target: str) -> List:
    """Run bago-lint + available Python linters."""
    findings = list(fe.run_bago_lint(target))

    def _try_linter(cmd, parser):
        out, _ = fe.run_linter(cmd, parser, cwd=str(BAGO_ROOT.parent))
        findings.extend(out)

    _try_linter(
        ["python3", "-m", "flake8", "--max-line-length=120",
         "--format=%(path)s:%(row)d:%(col)d: %(code)s %(text)s", target],
        fe.parse_flake8,
    )
    _try_linter(
        ["python3", "-m", "pylint", "--output-format=json",
         "--disable=C0114,C0115,C0116,R0903", target],
        fe.parse_pylint,
    )
    _try_linter(
        ["python3", "-m", "mypy", "--ignore-missing-imports",
         "--no-error-summary", target],
        fe.parse_mypy,
    )
    _try_linter(
        ["python3", "-m", "bandit", "-r", "-f", "json", target],
        fe.parse_bandit,
    )
    return findings


def _scan_js(target: str) -> List:
    """Run ESLint via npx + BAGO AST scanner."""
    findings = []
    eslint_findings, err = fe.run_linter(
        ["npx", "--yes", "eslint", "--format=json", target],
        fe.parse_eslint, cwd=str(BAGO_ROOT.parent),
    )
    if not err:
        findings.extend(eslint_findings)
    else:
        eslint2, err2 = fe.run_linter(
            ["eslint", "--format=json", target],
            fe.parse_eslint, cwd=str(BAGO_ROOT.parent),
        )
        if not err2:
            findings.extend(eslint2)

    # Always run BAGO AST scanner — works without eslint
    ast_findings = fe.run_js_ast_scan(target)
    findings.extend(ast_findings)
    return findings


def _scan_go(target: str) -> List:
    """Run golangci-lint."""
    findings, _ = fe.run_linter(
        ["golangci-lint", "run", "--out-format=json", target],
        fe.parse_golangci, cwd=target,
    )
    return findings


def _scan_rust(target: str) -> List:
    """Run cargo clippy."""
    findings, _ = fe.run_linter(
        ["cargo", "clippy", "--message-format=json", "--", "-D", "warnings"],
        fe.parse_clippy, cwd=target,
    )
    return findings


_LANG_SCANNERS = {
    "py":   (_scan_python, "Python"),
    "js":   (_scan_js,     "JS/TS"),
    "go":   (_scan_go,     "Go"),
    "rust": (_scan_rust,   "Rust"),
}


# ── Multi-scan core ───────────────────────────────────────────────────────────

def run_multi_scan(target: str, langs: Optional[List[str]] = None) -> dict:
    """Scan all languages in target.

    Returns:
        {
          "findings": [Finding, ...],            # all findings merged
          "by_lang": {"py": [...], "js": [...]}   # per-language breakdown
          "langs_detected": ["py", "js"],
          "langs_scanned":  ["py"],               # those that produced results
        }
    """
    if langs is None:
        langs = detect_all_langs(target)

    all_findings: List = []
    by_lang: dict = {}
    langs_scanned = []

    for lang in langs:
        scanner, label = _LANG_SCANNERS.get(lang, (None, lang))
        if scanner is None:
            continue
        try:
            found = scanner(target)
            by_lang[lang] = found
            all_findings.extend(found)
            if found:
                langs_scanned.append(lang)
        except Exception as e:  # noqa: BAGO-W002
            by_lang[lang] = []
            print(f"  {YELLOW}WARN{RESET}: {label} scanner error — {e}", file=sys.stderr)

    return {
        "findings":       all_findings,
        "by_lang":        by_lang,
        "langs_detected": langs,
        "langs_scanned":  langs_scanned,
    }


# ── Output ────────────────────────────────────────────────────────────────────

def _sev_color(sev: str) -> str:
    return _SEV_COLOR.get(sev, "") + sev.upper()[:4] + RESET


def _filter_severity(findings: List, min_sev: str) -> List:
    rank = _SEVERITY_RANK.get(min_sev, 0)
    return [f for f in findings if _SEVERITY_RANK.get(f.severity, 0) >= rank]


def _print_results(result: dict, base: Path, min_sev: str = "info") -> None:
    findings = _filter_severity(result["findings"], min_sev)

    if not findings:
        print(f"\n  {GREEN}✓ Sin hallazgos{RESET}\n")
        return

    by_file: dict = {}
    for f in findings:
        by_file.setdefault(f.file, []).append(f)

    for filepath, ff in sorted(by_file.items()):
        try:
            rel = str(Path(filepath).relative_to(base))
        except ValueError:
            rel = filepath
        print(f"\n  {BOLD}{rel}{RESET}")
        for f in sorted(ff, key=lambda x: x.line):
            fx = f"  {GREEN}[fix]{RESET}" if f.autofixable else ""
            print(f"    L{f.line:4d}  {_sev_color(f.severity)}  {f.rule:20s}  {f.message[:80]}{fx}")


def _print_summary(result: dict, min_sev: str = "info") -> None:
    findings = _filter_severity(result["findings"], min_sev)
    by_lang = result["by_lang"]
    langs_detected = result["langs_detected"]
    langs_scanned  = result["langs_scanned"]

    total    = len(findings)
    errors   = sum(1 for f in findings if f.severity == "error")
    warnings = sum(1 for f in findings if f.severity == "warning")
    infos    = sum(1 for f in findings if f.severity == "info")
    fixable  = sum(1 for f in findings if f.autofixable)

    lang_labels = {"py": "Python", "js": "JS/TS", "go": "Go", "rust": "Rust"}

    print(f"\n  {BOLD}Lenguajes detectados:{RESET}  "
          + "  ".join(f"{BOLD}{lang_labels.get(l,l)}{RESET}" for l in langs_detected))
    print(f"  {BOLD}Lenguajes escaneados:{RESET}  "
          + "  ".join(f"{GREEN}{lang_labels.get(l,l)}{RESET}" for l in langs_scanned)
          + (f"  {DIM}(ninguno){RESET}" if not langs_scanned else ""))

    print(f"\n  {BOLD}Total hallazgos: {total}{RESET}  "
          f"({RED}{errors} error{RESET}  "
          f"{YELLOW}{warnings} warning{RESET}  "
          f"{BLUE}{infos} info{RESET}  "
          f"/ {GREEN}{fixable} autofixables{RESET})\n")

    print(f"  {'Lenguaje':<10}  {'Hallazgos':>10}  {'Errores':>8}  {'Warnings':>9}")
    print(f"  {'-'*10}  {'-'*10}  {'-'*8}  {'-'*9}")
    for lang in langs_detected:
        lf = _filter_severity(by_lang.get(lang, []), min_sev)
        le = sum(1 for f in lf if f.severity == "error")
        lw = sum(1 for f in lf if f.severity == "warning")
        label = lang_labels.get(lang, lang)
        print(f"  {label:<10}  {len(lf):>10}  {le:>8}  {lw:>9}")
    print()


def _print_diff(diff: dict, base: Path) -> None:
    new        = diff["new"]
    fixed      = diff["fixed"]
    persistent = diff["persistent"]

    print(f"\n  {BOLD}Multi-scan diff:{RESET}")
    print(f"  {GREEN}✓ Resueltos:    {len(fixed):3d}{RESET}")
    print(f"  {RED}✗ Nuevos:       {len(new):3d}{RESET}")
    print(f"  {DIM}  Persistentes: {len(persistent):3d}{RESET}\n")

    if new:
        print(f"  {BOLD}{RED}── NUEVOS ──{RESET}")
        for f in sorted(new, key=lambda x: (x.file, x.line)):
            try:
                rel = str(Path(f.file).relative_to(base))
            except ValueError:
                rel = f.file
            print(f"    {RED}+{RESET} {rel}:{f.line}  {_sev_color(f.severity)}  {f.rule}  {f.message[:60]}")

    if fixed:
        print(f"\n  {BOLD}{GREEN}── RESUELTOS ──{RESET}")
        for f in sorted(fixed, key=lambda x: (x.file, x.line)):
            try:
                rel = str(Path(f.file).relative_to(base))
            except ValueError:
                rel = f.file
            print(f"    {GREEN}-{RESET} {rel}:{f.line}  {_sev_color(f.severity)}  {f.rule}  {f.message[:60]}")


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(
        description="BAGO multi-scan — escanea todos los lenguajes del proyecto",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("path",         nargs="?", default=".", help="Directorio a escanear")
    p.add_argument("--langs",      default=None, help="Lenguajes forzados: py,js,go,rust")
    p.add_argument("--json",       action="store_true", help="Output JSON (snapshot para --since)")
    p.add_argument("--since",      default=None, metavar="FILE", help="Diff contra snapshot previo")
    p.add_argument("--summary",    action="store_true", help="Solo resumen por lenguaje")
    p.add_argument("--min-severity", default="info",
                   choices=["error", "warning", "info"],
                   help="Umbral mínimo de severidad (default: info)")
    p.add_argument("--test",       action="store_true", help="Ejecutar self-tests")
    args = p.parse_args()

    if args.test:
        return _run_tests()

    target = str(Path(args.path).resolve())
    base   = Path(target)
    if not base.exists():
        print(f"ERROR: path no encontrado: {target}", file=sys.stderr)
        return 1

    forced_langs = [l.strip() for l in args.langs.split(",")] if args.langs else None
    result = run_multi_scan(target, forced_langs)
    findings = result["findings"]

    if args.json:
        data = [
            {"file": f.file, "line": f.line, "col": f.col,
             "rule": f.rule, "severity": f.severity, "source": f.source,
             "message": f.message, "autofixable": f.autofixable,
             "fix_suggestion": f.fix_suggestion,
             "id": f.id}
            for f in findings
        ]
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    if args.since:
        since_path = Path(args.since)
        if not since_path.exists():
            print(f"ERROR: snapshot no encontrado: {since_path}", file=sys.stderr)
            return 1
        try:
            raw = json.loads(since_path.read_text(encoding="utf-8"))
            before = [fe.Finding.from_dict({
                "id": item.get("id", ""),
                "severity": item.get("severity", "warning"),
                "file": item.get("file", ""),
                "line": item.get("line", 0),
                "col": item.get("col", 0),
                "rule": item.get("rule", ""),
                "source": item.get("source", "unknown"),
                "message": item.get("message", ""),
                "fix_suggestion": item.get("fix_suggestion", ""),
                "autofixable": item.get("autofixable", False),
            }) for item in raw]
        except Exception as e:
            print(f"ERROR: leyendo snapshot: {e}", file=sys.stderr)
            return 1
        diff = fe.diff_findings(before, findings)
        _print_diff(diff, base)
        return 1 if any(f.severity == "error" for f in diff["new"]) else 0

    if args.summary:
        _print_summary(result, args.min_severity)
        return 0

    _print_results(result, base, args.min_severity)
    _print_summary(result, args.min_severity)

    return 1 if any(f.severity == "error" for f in findings) else 0


# ── Self-tests ────────────────────────────────────────────────────────────────

def _run_tests() -> int:
    import tempfile
    import shutil

    errors = 0
    print("\nTests de multi_scan.py...")

    def ok(name: str) -> None:
        print(f"  OK: {name}")

    def fail(name: str, detail: str) -> None:
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {detail}")

    # T1: detect_all_langs — Python only
    tmp1 = Path(tempfile.mkdtemp())
    (tmp1 / "main.py").write_text("print('hello')\n")
    langs1 = detect_all_langs(str(tmp1))
    if langs1 == ["py"]:
        ok("multi:detect_python_only")
    else:
        fail("multi:detect_python_only", f"got: {langs1}")
    shutil.rmtree(tmp1)

    # T2: detect_all_langs — Python + JS
    tmp2 = Path(tempfile.mkdtemp())
    (tmp2 / "app.py").write_text("x = 1\n")
    (tmp2 / "app.js").write_text("const x = 1;\n")
    langs2 = detect_all_langs(str(tmp2))
    if "py" in langs2 and "js" in langs2:
        ok("multi:detect_py_and_js")
    else:
        fail("multi:detect_py_and_js", f"got: {langs2}")
    shutil.rmtree(tmp2)

    # T3: run_multi_scan Python — finds BAGO rules
    tmp3 = Path(tempfile.mkdtemp())
    (tmp3 / "code.py").write_text(
        "import os\ntry:\n    pass\nexcept:\n    pass\n"
        "os.system('ls')\n# TODO: fix\n"  # noqa: BAGO-W003, BAGO-I002
    )
    result3 = run_multi_scan(str(tmp3), langs=["py"])
    rules3 = {f.rule for f in result3["findings"]}
    if "BAGO-E001" in rules3 and "BAGO-W003" in rules3 and "BAGO-I002" in rules3:
        ok("multi:python_scan_finds_bago_rules")
    else:
        fail("multi:python_scan_finds_bago_rules", f"rules: {rules3}")
    shutil.rmtree(tmp3)

    # T4: by_lang breakdown keys are correct
    tmp4 = Path(tempfile.mkdtemp())
    (tmp4 / "x.py").write_text("# TODO: fix\n")  # noqa: BAGO-I002
    result4 = run_multi_scan(str(tmp4), langs=["py", "go"])
    if "py" in result4["by_lang"] and "go" in result4["by_lang"]:
        ok("multi:by_lang_keys")
    else:
        fail("multi:by_lang_keys", str(result4.keys()))
    shutil.rmtree(tmp4)

    # T5: detect_all_langs on single .py file
    tmp5 = Path(tempfile.mkdtemp())
    pf = tmp5 / "single.py"
    pf.write_text("pass\n")
    langs5 = detect_all_langs(str(pf))
    if langs5 == ["py"]:
        ok("multi:detect_single_file")
    else:
        fail("multi:detect_single_file", f"got: {langs5}")
    shutil.rmtree(tmp5)

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
