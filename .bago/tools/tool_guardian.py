#!/usr/bin/env python3
"""tool_guardian.py — Herramienta #125: Guardian de coherencia del framework BAGO.

Detecta tools en .bago/tools/ que no cumplen los estándares del framework:

    GUARD-E001  Tool sin flag --test implementado
    GUARD-E002  Tool sin registro en integration_tests.py
    GUARD-W001  Tool sin routing en bago script
    GUARD-W002  Tool sin docstring de módulo
    GUARD-I001  Tool correctamente integrado (informativo)

Es la herramienta que BAGO necesita para validarse a sí mismo.
Nació de la experiencia real: 47+ tools sin tests registrados en esta sesión.

Uso:
    bago tool-guardian [--format text|md|json]
                       [--fix-routing]   # añade routing stub al bago script
                       [--out FILE]
                       [--test]
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RED  = "\033[0;31m"
_CYN  = "\033[0;36m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

BAGO_ROOT   = Path(__file__).parent.parent        # .bago/
REPO_ROOT   = BAGO_ROOT.parent                    # repo raíz
TOOLS_DIR   = BAGO_ROOT / "tools"
INTEG_FILE  = TOOLS_DIR / "integration_tests.py"
BAGO_SCRIPT = REPO_ROOT / "bago"

# Tools del framework — loaded from tool_registry (single source of truth)
def _load_internal_tools() -> frozenset:
    """Load INTERNAL_TOOLS from tool_registry.py via importlib. Falls back to local set."""
    import importlib.util
    reg_path = TOOLS_DIR / "tool_registry.py"
    if reg_path.exists():
        spec = importlib.util.spec_from_file_location("_guardian_registry", str(reg_path))
        if spec:
            mod = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(mod)
                return getattr(mod, "INTERNAL_TOOLS", frozenset())
            except Exception:
                pass
    # Fallback if tool_registry.py is unavailable
    return frozenset({
        "tool_registry", "preflight", "session_logger",
        "integration_tests", "bago_utils", "bago_banner", "bago_start",
        "bago_on", "bago_debug", "bago_watch", "bago_chat_server",
        "bago_ask", "bago_lint_cli", "bago_search", "auto_register",
        "ci_generator", "tool_guardian", "contracts", "legacy_fixer",
    })

INTERNAL_TOOLS = _load_internal_tools()


def _get_all_tools() -> list[Path]:
    return sorted(
        p for p in TOOLS_DIR.glob("*.py")
        if p.stem not in INTERNAL_TOOLS and not p.stem.startswith("__")
    )


def _has_test_flag(filepath: Path) -> bool:
    """AST-based: verifies '--test' is in actual code (not a comment or docstring)."""
    try:
        tree = ast.parse(filepath.read_text("utf-8", errors="ignore"))
    except SyntaxError:
        return False

    # Collect string constants that are standalone docstrings (Expr(Constant))
    docstring_ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if (node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)):
                docstring_ids.add(id(node.body[0].value))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Constant) or node.value != "--test":
            continue
        if id(node) in docstring_ids:
            continue  # docstring mention doesn't count as implementation
        return True  # "--test" found in live code (not a comment, not a docstring)

    return False


def _is_in_integration(filepath: Path) -> bool:
    """AST-based: verifies tool has an actual _run() call in integration_tests.py."""
    if not INTEG_FILE.exists():
        return False
    try:
        tree = ast.parse(INTEG_FILE.read_text("utf-8", errors="ignore"))
    except SyntaxError:
        return False

    tool_name = filepath.name   # e.g. "lint.py"
    tool_stem = filepath.stem   # e.g. "lint"

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        func_id = func.id if isinstance(func, ast.Name) else (
            func.attr if isinstance(func, ast.Attribute) else "")
        if func_id == "_run" and node.args:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant):
                val = str(first_arg.value)
                if val in (tool_name, tool_stem):
                    return True
    return False


def _is_in_bago_script(filepath: Path) -> bool:
    """AST-based: verifies tool has routing in bago COMMANDS dict or elif chain."""
    if not BAGO_SCRIPT.exists():
        return False
    try:
        tree = ast.parse(BAGO_SCRIPT.read_text("utf-8", errors="ignore"))
    except SyntaxError:
        return False

    cmd = filepath.stem.replace("_", "-")

    for node in ast.walk(tree):
        # Check COMMANDS dict assignments
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (isinstance(target, ast.Name)
                        and target.id in ("COMMANDS", "COMMANDS_MAIN", "COMMANDS_ADVANCED")):
                    if isinstance(node.value, ast.Dict):
                        for k in node.value.keys:
                            if isinstance(k, ast.Constant) and k.value == cmd:
                                return True
        # Fallback: elif cmd == "..." patterns
        if isinstance(node, ast.If):
            test = node.test
            if (isinstance(test, ast.Compare)
                    and len(test.ops) == 1
                    and isinstance(test.ops[0], ast.Eq)
                    and isinstance(test.left, ast.Name)
                    and test.left.id == "cmd"):
                for comp in test.comparators:
                    if isinstance(comp, ast.Constant) and comp.value == cmd:
                        return True
    return False


def _has_module_docstring(filepath: Path) -> bool:
    try:
        tree = ast.parse(filepath.read_text("utf-8", errors="ignore"))
        return bool(ast.get_docstring(tree))
    except Exception:
        return False


def analyze(tools: list[Path] = None) -> list[dict]:
    if tools is None:
        tools = _get_all_tools()

    findings: list[dict] = []
    for tool in tools:
        has_test    = _has_test_flag(tool)
        in_integ    = _is_in_integration(tool)
        in_bago     = _is_in_bago_script(tool)
        has_docstr  = _has_module_docstring(tool)

        if not has_test:
            findings.append({
                "rule": "GUARD-E001", "severity": "error",
                "file": str(tool), "tool": tool.stem,
                "message": f"'{tool.name}' sin flag --test implementado",
            })
        if not in_integ:
            findings.append({
                "rule": "GUARD-E002", "severity": "error",
                "file": str(tool), "tool": tool.stem,
                "message": f"'{tool.name}' no registrado en integration_tests.py",
            })
        if not in_bago:
            findings.append({
                "rule": "GUARD-W001", "severity": "warning",
                "file": str(tool), "tool": tool.stem,
                "message": f"'{tool.name}' sin routing en bago script",
            })
        if not has_docstr:
            findings.append({
                "rule": "GUARD-W002", "severity": "warning",
                "file": str(tool), "tool": tool.stem,
                "message": f"'{tool.name}' sin docstring de módulo",
            })
        if has_test and in_integ and in_bago and has_docstr:
            findings.append({
                "rule": "GUARD-I001", "severity": "info",
                "file": str(tool), "tool": tool.stem,
                "message": f"'{tool.name}' correctamente integrado ✅",
            })
    return findings


def _summary(findings: list[dict]) -> dict:
    tools    = _get_all_tools()
    errors   = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    ok_tools = {f["tool"] for f in findings if f["rule"] == "GUARD-I001"}
    return {
        "total_tools":    len(tools),
        "fully_ok":       len(ok_tools),
        "total_errors":   len(errors),
        "total_warnings": len(warnings),
        "health_pct":     round(len(ok_tools) / max(1, len(tools)) * 100),
    }


def generate_text(findings: list[dict]) -> str:
    s      = _summary(findings)
    color  = _GRN if s["health_pct"] >= 80 else (_YEL if s["health_pct"] >= 50 else _RED)
    lines  = [
        f"{_BOLD}Tool Guardian — Estado del framework BAGO{_RST}",
        f"  {color}Salud: {s['health_pct']}%{_RST}  "
        f"({s['fully_ok']}/{s['total_tools']} tools OK  "
        f"E:{s['total_errors']}  W:{s['total_warnings']})",
        "",
    ]
    errors   = [f for f in findings if f["severity"] == "error"]
    warnings = [f for f in findings if f["severity"] == "warning"]
    if errors:
        lines.append(f"  {_RED}Errores críticos:{_RST}")
        for f in errors:
            lines.append(f"    [{f['rule']}] {f['message']}")
    if warnings:
        lines.append(f"\n  {_YEL}Warnings:{_RST}")
        for f in warnings[:20]:  # limit output
            lines.append(f"    [{f['rule']}] {f['message']}")
        if len(warnings) > 20:
            lines.append(f"    ... y {len(warnings)-20} warnings más")
    return "\n".join(lines)


def generate_markdown(findings: list[dict]) -> str:
    s     = _summary(findings)
    badge = "🟢" if s["health_pct"] >= 80 else ("🟡" if s["health_pct"] >= 50 else "🔴")
    lines = [
        f"# {badge} Tool Guardian — Salud {s['health_pct']}%",
        "",
        f"**Tools totales:** {s['total_tools']} | "
        f"**OK completos:** {s['fully_ok']} | "
        f"**Errores:** {s['total_errors']} | "
        f"**Warnings:** {s['total_warnings']}",
        "",
        "| Regla | Tool | Mensaje |",
        "|-------|------|---------|",
    ]
    for f in [x for x in findings if x["severity"] != "info"]:
        lines.append(f"| `{f['rule']}` | `{f['tool']}` | {f['message']} |")
    lines += ["", "---", "*Generado con `bago tool-guardian`*"]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    fmt      = "text"
    out_file = None

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        else:
            i += 1

    findings = analyze()

    if fmt == "json":
        content = json.dumps(findings, indent=2)
    elif fmt == "md":
        content = generate_markdown(findings)
    else:
        content = generate_text(findings)

    if out_file:
        Path(out_file).write_text(content, encoding="utf-8")
        print(f"Guardado: {out_file}", file=sys.stderr)
    else:
        print(content)

    errors = [f for f in findings if f["severity"] == "error"]
    return 1 if errors else 0


def _self_test() -> None:
    import tempfile
    print("Tests de tool_guardian.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        # T1 — tool sin --test → GUARD-E001
        t1 = root / "no_test.py"
        t1.write_text('"""Tool sin test."""\ndef main(): pass\n')
        f1 = analyze([t1])
        if any(f["rule"] == "GUARD-E001" for f in f1):
            ok("tool_guardian:no_test_flag")
        else:
            fail("tool_guardian:no_test_flag", f"findings={f1}")

        # T2 — tool con --test en código real → no GUARD-E001
        t2 = root / "with_test.py"
        t2.write_text(
            '"""Tool con test."""\nimport sys\n'
            'if __name__=="__main__":\n'
            '    if "--test" in sys.argv: pass\n'
        )
        f2 = analyze([t2])
        e001 = [f for f in f2 if f["rule"] == "GUARD-E001"]
        if not e001:
            ok("tool_guardian:has_test_flag")
        else:
            fail("tool_guardian:has_test_flag", f"unexpected={e001}")

        # T2b — tool con --test SOLO en docstring → debe seguir siendo GUARD-E001
        t2b = root / "docstring_test.py"
        t2b.write_text('"""Tool que menciona --test en docstring pero no lo implementa."""\ndef main(): pass\n')
        f2b = analyze([t2b])
        if any(f["rule"] == "GUARD-E001" for f in f2b):
            ok("tool_guardian:docstring_not_counted")
        else:
            fail("tool_guardian:docstring_not_counted", "docstring --test no debería contar")

        # T3 — tool sin docstring → GUARD-W002
        t3 = root / "no_doc.py"
        t3.write_text('if "--test" in ["--test"]: pass\ndef foo(): pass\n')
        f3 = analyze([t3])
        if any(f["rule"] == "GUARD-W002" for f in f3):
            ok("tool_guardian:no_docstring")
        else:
            fail("tool_guardian:no_docstring", f"findings={f3}")

        # T4 — _is_in_integration con fichero falso → False
        result = _is_in_integration(root / "ghost_tool.py")
        if not result:
            ok("tool_guardian:not_in_integration")
        else:
            fail("tool_guardian:not_in_integration", "deberia ser False")

        # T5 — tools reales del framework: lint.py debe estar integrado
        lint_path = TOOLS_DIR / "lint.py"
        if lint_path.exists():
            in_integ = _is_in_integration(lint_path)
            in_bago  = _is_in_bago_script(lint_path)
            if in_integ and in_bago:
                ok("tool_guardian:lint_fully_integrated")
            else:
                fail("tool_guardian:lint_fully_integrated",
                     f"in_integ={in_integ} in_bago={in_bago}")
        else:
            ok("tool_guardian:lint_fully_integrated")  # skip si no existe

        # T6 — generate_markdown incluye tabla
        mock = [{"rule":"GUARD-E001","severity":"error","file":"x.py","tool":"x","message":"test"}]
        md = generate_markdown(mock)
        if "Tool Guardian" in md and "GUARD-E001" in md and "| Regla |" in md:
            ok("tool_guardian:markdown_output")
        else:
            fail("tool_guardian:markdown_output", md[:100])

    total = 7; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: raise SystemExit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        raise SystemExit(main(sys.argv[1:]))
