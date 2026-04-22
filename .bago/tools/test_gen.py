#!/usr/bin/env python3
"""test_gen.py — Herramienta #109: Generador de tests unitarios para funciones Python.

Analiza un archivo Python via AST e genera tests unitarios stub para cada
función/método pública, listos para completar. Soporta pytest y unittest.

Uso:
    bago test-gen FILE [--framework pytest|unittest] [--out FILE]
                       [--class-prefix] [--test]

Opciones:
    FILE              Archivo Python a analizar
    --framework       pytest (default) | unittest
    --out FILE        Archivo de salida (default: stdout)
    --class-prefix    Agrupar tests en clase TestXxx
    --test            Self-tests
"""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

_GRN  = "\033[0;32m"
_RST  = "\033[0m"


@dataclass
class FuncInfo:
    name:       str
    lineno:     int
    args:       list[str]
    returns:    str
    is_method:  bool
    class_name: str = ""
    docstring:  str = ""


def _get_arg_names(args: ast.arguments) -> list[str]:
    names = [a.arg for a in args.args]
    return [n for n in names if n != "self" and n != "cls"]


def _get_return_annotation(node: ast.FunctionDef) -> str:
    if node.returns:
        try:
            return ast.unparse(node.returns)
        except Exception:
            return "?"
    return ""


def _get_docstring(node: ast.FunctionDef) -> str:
    if (node.body and isinstance(node.body[0], ast.Expr)
            and isinstance(node.body[0].value, ast.Constant)
            and isinstance(node.body[0].value.value, str)):
        return node.body[0].value.value.strip().splitlines()[0][:80]
    return ""


def analyze(filepath: str) -> list[FuncInfo]:
    path = Path(filepath)
    if not path.exists() or path.suffix != ".py":
        return []
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        tree   = ast.parse(source, filename=filepath)
    except SyntaxError:
        return []

    funcs: list[FuncInfo] = []
    module_name = path.stem

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith("_"):
                continue
            funcs.append(FuncInfo(
                name=node.name, lineno=node.lineno,
                args=_get_arg_names(node.args),
                returns=_get_return_annotation(node),
                is_method=False,
                docstring=_get_docstring(node),
            ))
        elif isinstance(node, ast.ClassDef):
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.FunctionDef) and not child.name.startswith("_"):
                    funcs.append(FuncInfo(
                        name=child.name, lineno=child.lineno,
                        args=_get_arg_names(child.args),
                        returns=_get_return_annotation(child),
                        is_method=True, class_name=node.name,
                        docstring=_get_docstring(child),
                    ))
    return funcs


def _args_stub(args: list[str]) -> str:
    """Genera argumentos stub."""
    defaults = {
        0: "None", 1: "1", 2: '"test_value"',
    }
    return ", ".join(defaults.get(i % 3, f'"{a}"') for i, a in enumerate(args))


def generate_pytest(funcs: list[FuncInfo], module_name: str,
                    use_class: bool = False) -> str:
    lines = [
        f"\"\"\"Tests generados automáticamente para {module_name}.py\"\"\"",
        "import pytest",
        f"from {module_name} import *",
        "",
    ]

    if use_class:
        lines.append(f"class Test{module_name.title().replace('_', '')}:")
        indent = "    "
    else:
        indent = ""

    for f in funcs:
        fname = f"{f.class_name}_{f.name}" if f.class_name else f.name
        stub_args = _args_stub(f.args)
        ret_comment = f"  # → {f.returns}" if f.returns else ""
        doc = f'        """{f.docstring}"""' if f.docstring else ""

        lines += [
            f"",
            f"{indent}def test_{fname}():",
        ]
        if doc:
            lines.append(f"{indent}    # {f.docstring}")
        if f.args:
            lines.append(f"{indent}    # arrange")
            for arg in f.args:
                lines.append(f"{indent}    {arg} = None  # TODO: set value")
        lines += [
            f"{indent}    # act",
            f"{indent}    result = {fname}({', '.join(f.args)}){ret_comment}",
            f"{indent}    # assert",
            f"{indent}    assert result is not None  # TODO: refine assertion",
        ]

    lines.append("")
    return "\n".join(lines)


def generate_unittest(funcs: list[FuncInfo], module_name: str) -> str:
    lines = [
        f'"""Tests generados automáticamente para {module_name}.py"""',
        "import unittest",
        f"from {module_name} import *",
        "",
        f"class Test{module_name.title().replace('_', '')}(unittest.TestCase):",
        "",
    ]
    for f in funcs:
        fname = f"{f.class_name}_{f.name}" if f.class_name else f.name
        ret_comment = f"  # → {f.returns}" if f.returns else ""
        lines += [
            f"    def test_{fname}(self):",
        ]
        if f.docstring:
            lines.append(f"        # {f.docstring}")
        for arg in f.args:
            lines.append(f"        {arg} = None  # TODO: set value")
        lines += [
            f"        result = {fname}({', '.join(f.args)}){ret_comment}",
            f"        self.assertIsNotNone(result)  # TODO: refine",
            f"",
        ]
    lines += [
        'if __name__ == "__main__":',
        "    unittest.main()",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("--"):
        print("Uso: bago test-gen FILE [--framework pytest|unittest] [--out FILE]")
        return 1

    filepath  = argv[0]
    framework = "pytest"
    out_file  = None
    use_class = False

    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--framework" and i + 1 < len(argv):
            framework = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        elif a == "--class-prefix":
            use_class = True; i += 1
        else:
            i += 1

    funcs = analyze(filepath)
    if not funcs:
        print("Sin funciones públicas encontradas.", file=sys.stderr)
        return 1

    module_name = Path(filepath).stem
    if framework == "unittest":
        code = generate_unittest(funcs, module_name)
    else:
        code = generate_pytest(funcs, module_name, use_class)

    if out_file:
        Path(out_file).write_text(code, encoding="utf-8")
        print(f"{_GRN}✅ Tests generados: {out_file} ({len(funcs)} función(es)){_RST}",
              file=sys.stderr)
    else:
        print(code)
    return 0


def _self_test() -> None:
    import tempfile, textwrap
    print("Tests de test_gen.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    SRC = textwrap.dedent("""\
        def add(a, b):
            \"\"\"Add two numbers.\"\"\"
            return a + b

        def multiply(x, y):
            return x * y

        def _private():
            pass

        class Calculator:
            def divide(self, a, b):
                \"\"\"Divide a by b.\"\"\"
                return a / b
    """)
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(SRC); tmp = f.name
    path = Path(tmp)

    # T1 — analyze detecta funciones públicas
    funcs = analyze(tmp)
    names = [f.name for f in funcs]
    if "add" in names and "multiply" in names:
        ok("test_gen:analyze_detects_public_funcs")
    else:
        fail("test_gen:analyze_detects_public_funcs", f"names={names}")

    # T2 — _private excluida
    if "_private" not in names:
        ok("test_gen:private_excluded")
    else:
        fail("test_gen:private_excluded", "_private apareció")

    # T3 — método de clase detectado
    methods = [f for f in funcs if f.is_method]
    if methods and methods[0].name == "divide" and methods[0].class_name == "Calculator":
        ok("test_gen:method_detected")
    else:
        fail("test_gen:method_detected", f"methods={methods}")

    # T4 — pytest generado contiene estructura correcta
    code = generate_pytest(funcs, "calculator")
    if "def test_add" in code and "def test_multiply" in code and "import pytest" in code:
        ok("test_gen:pytest_structure")
    else:
        fail("test_gen:pytest_structure", "estructura incorrecta")

    # T5 — unittest generado
    code_u = generate_unittest(funcs, "calculator")
    if "unittest.TestCase" in code_u and "def test_add" in code_u:
        ok("test_gen:unittest_structure")
    else:
        fail("test_gen:unittest_structure", "estructura incorrecta")

    # T6 — docstring incluida como comentario
    if "Add two numbers" in code:
        ok("test_gen:docstring_in_comment")
    else:
        fail("test_gen:docstring_in_comment", "docstring no aparece")

    path.unlink(missing_ok=True)
    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
