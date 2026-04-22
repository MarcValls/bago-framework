#!/usr/bin/env python3
"""
bago bago-lint — BAGO's own code linter, zero external dependencies.

Scans Python files in a directory and reports code quality issues:
  BAGO-E001  bare except: clause (autofixable)
  BAGO-W001  datetime.utcnow() deprecated (autofixable)
  BAGO-W002  eval()/exec() usage — security risk
  BAGO-W003  os.system() — should use subprocess
  BAGO-W004  hardcoded absolute user path — not portable
  BAGO-I001  sys.exit(1) without visible message
  BAGO-I002  TODO/FIXME/HACK comments — tech debt

Usage:
    bago bago-lint [path]             scan path (default: current dir)
    bago bago-lint --fix              apply autofixable patches
    bago bago-lint --preview          show what --fix would do (dry run)
    bago bago-lint --rule BAGO-W001   filter to specific rule
    bago bago-lint --json             output JSON (saves snapshot for --since)
    bago bago-lint --since FILE.json  diff against a previous JSON snapshot
    bago bago-lint --summary          counts by rule only
    bago bago-lint --test             run self-tests
"""

from __future__ import annotations

import argparse
import json
import sys
import os
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(Path(__file__).parent))

try:
    import findings_engine as fe
except ImportError:
    print("ERROR: findings_engine.py no encontrado", file=sys.stderr)
    sys.exit(1)

# ── ANSI colours ─────────────────────────────────────────────────────────────
GREEN  = "\033[32m" if sys.stdout.isatty() else ""
YELLOW = "\033[33m" if sys.stdout.isatty() else ""
RED    = "\033[31m" if sys.stdout.isatty() else ""
BLUE   = "\033[34m" if sys.stdout.isatty() else ""
DIM    = "\033[2m"  if sys.stdout.isatty() else ""
BOLD   = "\033[1m"  if sys.stdout.isatty() else ""
RESET  = "\033[0m"  if sys.stdout.isatty() else ""

_SEVERITY_COLOR = {
    "error":   RED,
    "warning": YELLOW,
    "info":    BLUE,
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def _color_severity(sev: str) -> str:
    return _SEVERITY_COLOR.get(sev, "") + sev.upper() + RESET


def _relative(path: str, base: Path) -> str:
    try:
        return str(Path(path).relative_to(base))
    except ValueError:
        return path


def _apply_fixes(findings: list, dry_run: bool) -> dict:
    """Apply autofixable patches in-place. Returns {applied, failed, skipped}."""
    results: dict = {"applied": [], "failed": [], "skipped": []}

    by_file: dict = {}
    for f in findings:
        if f.autofixable and f.fix_patch:
            by_file.setdefault(f.file, []).append(f)

    for filepath, file_findings in sorted(by_file.items()):
        try:
            p = Path(filepath)
            original = p.read_text(encoding="utf-8")
            lines = original.splitlines(keepends=True)

            # Sort by line descending so replacements don't shift offsets
            sorted_findings = sorted(file_findings, key=lambda x: x.line, reverse=True)
            modified = list(lines)

            for finding in sorted_findings:
                lineno = finding.line - 1  # 0-indexed
                if 0 <= lineno < len(modified):
                    old_line = modified[lineno]
                    if finding.rule == "BAGO-E001":
                        new_line = old_line.replace("except:", "except Exception:", 1)
                    elif finding.rule == "BAGO-W001":
                        import re
                        new_line = re.sub(
                            r'datetime\.datetime\.utcnow\(\)',
                            'datetime.datetime.now(datetime.timezone.utc)',
                            re.sub(r'datetime\.utcnow\(\)',
                                   'datetime.datetime.now(datetime.timezone.utc)',
                                   old_line)
                        )
                    else:
                        new_line = old_line
                    if new_line != old_line:
                        if not dry_run:
                            modified[lineno] = new_line
                        results["applied"].append(f"{filepath}:{finding.line} [{finding.rule}]")
                    else:
                        results["skipped"].append(f"{filepath}:{finding.line} [{finding.rule}]")
                else:
                    results["failed"].append(f"{filepath}:{finding.line} [{finding.rule}] — line out of range")

            if not dry_run and results["applied"]:
                p.write_text("".join(modified), encoding="utf-8")

        except Exception as e:
            results["failed"].append(f"{filepath} — {e}")

    return results


# ── Output formatters ─────────────────────────────────────────────────────────

def _print_findings(findings: list, base: Path, show_context: bool = True) -> None:
    if not findings:
        print(f"\n  {GREEN}✓ Sin hallazgos{RESET}\n")
        return

    by_file: dict = {}
    for f in findings:
        by_file.setdefault(f.file, []).append(f)

    for filepath, ff in sorted(by_file.items()):
        rel = _relative(filepath, base)
        print(f"\n  {BOLD}{rel}{RESET}")
        for f in sorted(ff, key=lambda x: x.line):
            sev_str = _color_severity(f.severity)
            fix_mark = f"  {GREEN}[autofixable]{RESET}" if f.autofixable else ""
            print(f"    L{f.line:4d}  {sev_str}  {f.rule}  {f.message}{fix_mark}")
            if f.fix_suggestion and not f.autofixable:
                print(f"           {DIM}↳ {f.fix_suggestion}{RESET}")


def _print_summary(findings: list) -> None:
    if not findings:
        print(f"  {GREEN}✓ Sin hallazgos{RESET}")
        return

    by_rule: dict = {}
    for f in findings:
        by_rule.setdefault(f.rule, {"count": 0, "autofixable": 0, "severity": f.severity})
        by_rule[f.rule]["count"] += 1
        if f.autofixable:
            by_rule[f.rule]["autofixable"] += 1

    total     = len(findings)
    fixable   = sum(f.autofixable for f in findings)
    errors    = sum(1 for f in findings if f.severity == "error")
    warnings  = sum(1 for f in findings if f.severity == "warning")
    infos     = sum(1 for f in findings if f.severity == "info")

    print(f"\n  {BOLD}Resumen: {total} hallazgos{RESET}  "
          f"({RED}{errors} error{RESET}  "
          f"{YELLOW}{warnings} warning{RESET}  "
          f"{BLUE}{infos} info{RESET}  "
          f"/ {GREEN}{fixable} autofixables{RESET})\n")

    for rule, data in sorted(by_rule.items()):
        c = data["count"]
        a = data["autofixable"]
        sev = _color_severity(data["severity"])
        fix = f"  {GREEN}[{a} autofixable]{RESET}" if a else ""
        print(f"  {sev}  {BOLD}{rule}{RESET}  {c} ocurrencias{fix}")


def _print_diff(diff: dict, base: Path) -> None:
    """Print the result of diff_findings() with coloured new/fixed/persistent sections."""
    new        = diff["new"]
    fixed      = diff["fixed"]
    persistent = diff["persistent"]

    print(f"\n  {BOLD}Diff de hallazgos:{RESET}")
    print(f"  {GREEN}✓ Resueltos:    {len(fixed):3d}{RESET}")
    print(f"  {RED}✗ Nuevos:       {len(new):3d}{RESET}")
    print(f"  {DIM}  Persistentes: {len(persistent):3d}{RESET}\n")

    if new:
        print(f"  {BOLD}{RED}── NUEVOS ──{RESET}")
        _print_findings(new, base)

    if fixed:
        print(f"  {BOLD}{GREEN}── RESUELTOS ──{RESET}")
        _print_findings(fixed, base)


def main() -> int:
    p = argparse.ArgumentParser(
        description="BAGO lint — linter de código Python sin dependencias externas",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("path", nargs="?", default=".", help="Directorio a escanear (default: .)")
    p.add_argument("--fix",     action="store_true", help="Aplicar patches autofixables")
    p.add_argument("--preview", action="store_true", help="Mostrar qué haría --fix (dry run)")
    p.add_argument("--rule",    default=None, help="Filtrar a regla específica (ej: BAGO-W001)")
    p.add_argument("--json",    action="store_true", help="Output JSON (snapshot para --since)")
    p.add_argument("--since",   default=None, metavar="FILE", help="Diff contra snapshot JSON anterior")
    p.add_argument("--summary", action="store_true", help="Solo totales por regla")
    p.add_argument("--test",    action="store_true", help="Ejecutar self-tests")
    args = p.parse_args()

    if args.test:
        return _run_tests()

    target = Path(args.path).resolve()
    if not target.exists():
        print(f"ERROR: path no encontrado: {target}", file=sys.stderr)
        return 1

    findings = fe.run_bago_lint(str(target))

    if args.rule:
        findings = [f for f in findings if f.rule == args.rule]

    # ── --since: diff mode ────────────────────────────────────────────────────
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
                "source": item.get("source", "bago_lint"),
                "message": item.get("message", ""),
                "fix_suggestion": item.get("fix_suggestion", ""),
                "autofixable": item.get("autofixable", False),
            }) for item in raw]
        except Exception as e:
            print(f"ERROR: no se pudo leer snapshot: {e}", file=sys.stderr)
            return 1
        diff = fe.diff_findings(before, findings)
        _print_diff(diff, target)
        has_new_errors = any(f.severity == "error" for f in diff["new"])
        return 1 if has_new_errors else 0

    if args.json:
        data = [
            {"file": f.file, "line": f.line, "rule": f.rule,
             "severity": f.severity, "message": f.message,
             "autofixable": f.autofixable, "fix_suggestion": f.fix_suggestion}
            for f in findings
        ]
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return 0

    if args.summary:
        _print_summary(findings)
        return 0

    # Handle fix / preview
    if args.fix or args.preview:
        fixable = [f for f in findings if f.autofixable and f.fix_patch]
        if not fixable:
            print(f"\n  {GREEN}✓ Sin hallazgos autofixables{RESET}\n")
        else:
            dry = args.preview
            action = "PREVIEW (dry run)" if dry else "APLICANDO FIXES"
            print(f"\n  {BOLD}{action} — {len(fixable)} hallazgos autofixables{RESET}\n")
            results = _apply_fixes(fixable, dry_run=dry)
            for r in results["applied"]:
                verb = "Aplicaría" if dry else "Aplicado"
                print(f"  {GREEN}✓{RESET} {verb}: {r}")
            for r in results["failed"]:
                print(f"  {RED}✗{RESET} Falló: {r}")
            for r in results["skipped"]:
                print(f"  {DIM}— Sin cambio: {r}{RESET}")
            print()

        # Show remaining non-fixable findings
        remaining = [f for f in findings if not f.autofixable]
        if remaining:
            print(f"  {BOLD}Hallazgos no autofixables ({len(remaining)}){RESET}")
            _print_findings(remaining, target)
    else:
        _print_findings(findings, target)
        _print_summary(findings)

    # Exit code: 1 if errors found
    has_errors = any(f.severity == "error" for f in findings)
    return 1 if has_errors else 0


# ── Self-tests ───────────────────────────────────────────────────────────────

def _run_tests() -> int:
    import tempfile
    import shutil

    errors = 0
    print("\nTests de bago_lint_cli.py...")

    def ok(name: str) -> None:
        print(f"  OK: {name}")

    def fail(name: str, detail: str) -> None:
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {detail}")

    # T1: scan detects BAGO-E001/W002/W003/W004/I002
    tmp = Path(tempfile.mkdtemp())
    (tmp / "code.py").write_text(
        "import os\n"
        "try:\n    pass\nexcept:\n    pass\n"
        "x = eval('1+1')\n"
        "os.system('ls')\n"
        "DATA = '/Users/john/things'\n"
        "# TODO: fix\n"
    )
    findings = fe.run_bago_lint(str(tmp))
    rules = {f.rule for f in findings}
    want = {"BAGO-E001", "BAGO-W002", "BAGO-W003", "BAGO-W004", "BAGO-I002"}
    missing = want - rules
    if not missing:
        ok("cli:detect_all_rules")
    else:
        fail("cli:detect_all_rules", f"missing: {missing}")

    # T2: --fix applies BAGO-E001 patch
    tmp2 = Path(tempfile.mkdtemp())
    pyf = tmp2 / "fixable.py"
    pyf.write_text("try:\n    pass\nexcept:\n    pass\n")
    fixable = [f for f in fe.run_bago_lint(str(tmp2)) if f.autofixable and f.fix_patch]
    if fixable:
        result = _apply_fixes(fixable, dry_run=False)
        content = pyf.read_text()
        if "except Exception:" in content:
            ok("cli:fix_applies_patch")
        else:
            fail("cli:fix_applies_patch", f"content: {content!r}")
    else:
        fail("cli:fix_applies_patch", "no autofixable findings found")

    # T3: --preview does NOT modify file
    tmp3 = Path(tempfile.mkdtemp())
    pyf3 = tmp3 / "preview.py"
    pyf3.write_text("try:\n    pass\nexcept:\n    pass\n")
    original = pyf3.read_text()
    fixable3 = [f for f in fe.run_bago_lint(str(tmp3)) if f.autofixable and f.fix_patch]
    if fixable3:
        _apply_fixes(fixable3, dry_run=True)
        after = pyf3.read_text()
        if after == original:
            ok("cli:preview_no_modify")
        else:
            fail("cli:preview_no_modify", "file was modified in dry run!")
    else:
        fail("cli:preview_no_modify", "no autofixable findings for preview test")

    # T4: JSON output structure
    tmp4 = Path(tempfile.mkdtemp())
    (tmp4 / "j.py").write_text("# TODO: something\n")
    findings4 = fe.run_bago_lint(str(tmp4))
    j = [
        {"file": f.file, "line": f.line, "rule": f.rule,
         "severity": f.severity, "message": f.message,
         "autofixable": f.autofixable, "fix_suggestion": f.fix_suggestion}
        for f in findings4
    ]
    if j and "rule" in j[0] and "severity" in j[0]:
        ok("cli:json_structure")
    else:
        fail("cli:json_structure", str(j[:1]))

    # T5: --since diff mode
    tmp5 = Path(tempfile.mkdtemp())
    py5 = tmp5 / "evolving.py"
    # "before" snapshot: has bare except only
    py5.write_text("try:\n    pass\nexcept:\n    pass\n")
    before_findings = fe.run_bago_lint(str(tmp5))
    snapshot = [
        {"file": f.file, "line": f.line, "rule": f.rule,
         "severity": f.severity, "message": f.message,
         "autofixable": f.autofixable, "fix_suggestion": f.fix_suggestion,
         "id": f.id, "col": f.col, "source": f.source}
        for f in before_findings
    ]
    snapshot_file = tmp5 / "baseline.json"
    snapshot_file.write_text(json.dumps(snapshot), encoding="utf-8")

    # "after" scan: fixed the except, but added an eval
    py5.write_text("try:\n    pass\nexcept Exception:\n    pass\nx = eval('1')\n")
    after_findings = fe.run_bago_lint(str(tmp5))

    raw_snap = json.loads(snapshot_file.read_text(encoding="utf-8"))
    b4 = [fe.Finding.from_dict({
        "id": item.get("id", ""), "severity": item.get("severity", "warning"),
        "file": item.get("file", ""), "line": item.get("line", 0),
        "col": item.get("col", 0), "rule": item.get("rule", ""),
        "source": item.get("source", "bago_lint"), "message": item.get("message", ""),
        "fix_suggestion": item.get("fix_suggestion", ""),
        "autofixable": item.get("autofixable", False),
    }) for item in raw_snap]
    diff = fe.diff_findings(b4, after_findings)

    ok_diff = (
        any(f.rule == "BAGO-W002" for f in diff["new"]) and
        any(f.rule == "BAGO-E001" for f in diff["fixed"])
    )
    if ok_diff:
        ok("cli:diff_since")
    else:
        fail("cli:diff_since", f"new={[f.rule for f in diff['new']]} fixed={[f.rule for f in diff['fixed']]}")

    for t in [tmp, tmp2, tmp3, tmp4, tmp5]:
        shutil.rmtree(t, ignore_errors=True)

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
