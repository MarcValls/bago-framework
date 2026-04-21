#!/usr/bin/env python3
"""
testgen — Genera una suite de tests completa para repositorios o directorios desconocidos.

Soporta:
  Python  → analiza AST, genera pytest con fixtures + mocks
  JS/TS   → análisis regex, genera jest skeletons
  Generic → genera tests básicos de integración (imports, CLI, etc.)

Uso:
  bago testgen <ruta>            → genera tests para Python por defecto
  bago testgen <ruta> --lang py  → Python explícito
  bago testgen <ruta> --lang js  → JavaScript/TypeScript
  bago testgen <ruta> --output tests/   → directorio de salida
  bago testgen <ruta> --dry-run  → muestra sin escribir
  bago testgen <ruta> --summary  → solo resumen
"""
import ast, argparse, json, os, re, sys
from pathlib import Path
from typing import Optional

# ─── Python analysis ─────────────────────────────────────────────────────────

def _python_signature(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Returns 'func(arg1, arg2)' string from AST node."""
    args = node.args
    all_args = []
    # positional
    for a in args.args:
        all_args.append(a.arg)
    for a in args.kwonlyargs:
        all_args.append(a.arg)
    if args.vararg:
        all_args.append("*" + args.vararg.arg)
    if args.kwarg:
        all_args.append("**" + args.kwarg.arg)
    return f"{node.name}({', '.join(all_args)})"


def _is_private(name: str) -> bool:
    return name.startswith("_")


def _classify_func(node) -> str:
    """Returns hint about what kind of test to write."""
    body_src = ast.unparse(node) if hasattr(ast, "unparse") else ""
    if "raise" in body_src:       return "raises"
    if "return" in body_src:      return "returns"
    if "open(" in body_src:       return "io"
    if "subprocess" in body_src:  return "subprocess"
    return "general"


def analyze_python_file(path: Path) -> dict:
    """Parse a Python file and extract testable units."""
    try:
        src = path.read_text(encoding="utf-8", errors="replace")
        tree = ast.parse(src, filename=str(path))
    except SyntaxError as e:
        return {"path": str(path), "error": str(e), "functions": [], "classes": []}

    functions = []
    classes   = []
    imports   = set()

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split(".")[0])
            else:
                imports.add((node.module or "").split(".")[0])

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not _is_private(node.name):
                functions.append({
                    "name":  node.name,
                    "sig":   _python_signature(node),
                    "kind":  _classify_func(node),
                    "args":  [a.arg for a in node.args.args],
                    "async": isinstance(node, ast.AsyncFunctionDef),
                    "line":  node.lineno,
                })
        elif isinstance(node, ast.ClassDef):
            methods = []
            for child in ast.iter_child_nodes(node):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    if not _is_private(child.name) or child.name in ("__init__",):
                        methods.append({
                            "name":  child.name,
                            "sig":   _python_signature(child),
                            "kind":  _classify_func(child),
                            "async": isinstance(child, ast.AsyncFunctionDef),
                            "line":  child.lineno,
                        })
            classes.append({
                "name":    node.name,
                "methods": methods,
                "line":    node.lineno,
            })

    return {
        "path":      str(path),
        "module":    path.stem,
        "imports":   sorted(imports - {""}),
        "functions": functions,
        "classes":   classes,
    }


def generate_python_test_file(analysis: dict, rel_path: Path) -> str:
    """Generate pytest file content from analysis dict."""
    mod  = analysis["module"]
    src  = Path(analysis["path"])
    # build relative import
    # We'll use a generic import that the user will need to adjust
    lines = [
        "\"\"\"",
        f"Tests auto-generados por bago testgen para: {src.name}",
        "IMPORTANTE: Revisa y ajusta los assertions — son placeholders.",
        "\"\"\"",
        "import pytest",
        "",
    ]

    # detect if we need asyncio
    has_async = any(f["async"] for f in analysis["functions"]) or any(
        m["async"] for c in analysis["classes"] for m in c["methods"])
    if has_async:
        lines.append("import asyncio")
        lines.append("")

    # detect imports for mocking
    needs_mock = any(f["kind"] in ("io","subprocess") for f in analysis["functions"])
    if needs_mock:
        lines.append("from unittest.mock import patch, MagicMock, mock_open")
        lines.append("")

    # Try to build a sensible import
    lines.append(f"# Ajusta la ruta de import según tu proyecto")
    lines.append(f"# from {mod} import ...")
    lines.append("")

    # ── standalone functions ───────────────────────────────────────────────
    if analysis["functions"]:
        lines.append("")
        lines.append("# " + "─" * 60)
        lines.append(f"# Funciones de módulo: {src.name}")
        lines.append("# " + "─" * 60)
        for fn in analysis["functions"]:
            lines += _gen_function_test(fn, mod)

    # ── classes ───────────────────────────────────────────────────────────
    for cls in analysis["classes"]:
        lines.append("")
        lines.append("")
        lines.append("# " + "─" * 60)
        lines.append(f"class Test{cls['name']}:")
        lines.append(f"    \"\"\"Tests para {cls['name']} (línea {cls['line']})\"\"\"")
        lines.append("")
        if not cls["methods"]:
            lines.append("    def test_instantiation(self):")
            lines.append(f"        # obj = {cls['name']}()")
            lines.append("        # assert obj is not None")
            lines.append("        pass")
        for m in cls["methods"]:
            lines += _gen_method_test(m, cls["name"])

    if analysis.get("error"):
        lines = [f"# ERROR al parsear {src.name}: {analysis['error']}",
                 "# No se pudieron generar tests."]

    return "\n".join(lines) + "\n"


def _gen_function_test(fn: dict, mod: str) -> list:
    name  = fn["name"]
    sig   = fn["sig"]
    kind  = fn["kind"]
    args  = [a for a in fn["args"] if a not in ("self","cls")]
    lines = ["", f"def test_{name}():"]
    lines.append(f"    \"\"\"Test para {name}({', '.join(args)}) — {kind}\"\"\"")

    if kind == "raises":
        lines.append(f"    # Verifica que {name} lanza excepción con inputs inválidos")
        lines.append(f"    with pytest.raises(Exception):")
        placeholder = ", ".join("None" for _ in args)
        lines.append(f"        # {mod}.{name}({placeholder})")
        lines.append("        pass")
    elif kind == "io":
        lines.append(f"    with patch('builtins.open', mock_open(read_data='test')):")
        lines.append(f"        # result = {mod}.{name}({', '.join('None' for _ in args)})")
        lines.append("        # assert result is not None")
        lines.append("        pass")
    elif kind == "subprocess":
        lines.append(f"    with patch('subprocess.run') as mock_run:")
        lines.append("        mock_run.return_value.returncode = 0")
        lines.append(f"        # result = {mod}.{name}({', '.join('None' for _ in args)})")
        lines.append("        # assert result is not None")
        lines.append("        pass")
    else:
        if args:
            placeholders = ", ".join("None" for _ in args)
            lines.append(f"    # result = {mod}.{name}({placeholders})")
            lines.append("    # assert result is not None")
        else:
            lines.append(f"    # result = {mod}.{name}()")
            lines.append("    # assert result is not None")
        lines.append("    pass")

    return lines


def _gen_method_test(m: dict, cls_name: str) -> list:
    name  = m["name"]
    kind  = m["kind"]
    args  = [a for a in m.get("args", ["self"])[1:] if a not in ("cls",)]
    lines = ["", f"    def test_{name}(self):"]
    lines.append(f"        \"\"\"Test para {cls_name}.{name}\"\"\"")
    if args:
        placeholders = ", ".join("None" for _ in args)
        lines.append(f"        # obj = {cls_name}()")
        lines.append(f"        # result = obj.{name}({placeholders})")
        lines.append("        # assert result is not None")
    else:
        lines.append(f"        # obj = {cls_name}()")
        if name == "__init__":
            lines.append(f"        # assert obj is not None")
        else:
            lines.append(f"        # result = obj.{name}()")
            lines.append("        # assert result is not None")
    lines.append("        pass")
    return lines


# ─── JS/TS analysis ──────────────────────────────────────────────────────────

def analyze_js_file(path: Path) -> dict:
    src = path.read_text(encoding="utf-8", errors="replace")
    # regex-based extraction
    funcs = re.findall(
        r'(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*\(([^)]*)\)', src)
    arrows = re.findall(
        r'(?:export\s+)?(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>', src)
    classes = re.findall(r'class\s+(\w+)', src)
    return {
        "path":    str(path),
        "module":  path.stem,
        "funcs":   [{"name": n, "params": p} for n, p in funcs + arrows],
        "classes": classes,
    }


def generate_js_test_file(analysis: dict) -> str:
    mod  = analysis["module"]
    path = Path(analysis["path"])
    lines = [
        f"// Tests auto-generados por bago testgen para: {path.name}",
        f"// IMPORTANTE: Revisa y ajusta los assertions — son placeholders.",
        "",
        f"const {{ {', '.join(f['name'] for f in analysis['funcs'][:5]) or mod} }} = require('./{path.stem}');",
        "",
        "describe('" + mod + "', () => {",
    ]
    for fn in analysis["funcs"]:
        name   = fn["name"]
        params = fn["params"].strip()
        placeholders = ", ".join("null" for _ in params.split(",")) if params else ""
        lines += [
            f"  it('should work: {name}', () => {{",
            f"    // const result = {name}({placeholders});",
            f"    // expect(result).toBeDefined();",
            "    expect(true).toBe(true); // placeholder",
            "  });",
            "",
        ]
    for cls in analysis["classes"]:
        lines += [
            f"  describe('{cls}', () => {{",
            f"    it('should instantiate', () => {{",
            f"      // const obj = new {cls}();",
            f"      // expect(obj).toBeDefined();",
            "      expect(true).toBe(true); // placeholder",
            "    });",
            "  });",
            "",
        ]
    lines += ["});"]
    return "\n".join(lines) + "\n"


# ─── Discovery ────────────────────────────────────────────────────────────────

def discover_files(target: Path, lang: str) -> list:
    """Walk target dir and collect files to analyze."""
    if target.is_file():
        return [target]

    results = []
    if lang in ("py", "python"):
        patterns = ["**/*.py"]
    elif lang in ("js", "ts", "javascript", "typescript"):
        patterns = ["**/*.js", "**/*.ts", "**/*.mjs"]
    else:
        patterns = ["**/*.py", "**/*.js", "**/*.ts"]

    for pat in patterns:
        for f in target.glob(pat):
            # skip common noise dirs
            parts = f.parts
            if any(p in parts for p in ("node_modules", "__pycache__", ".git",
                                        "dist", "build", ".venv", "venv", "env")):
                continue
            if f.name.startswith("test_") or f.name.endswith("_test.py"):
                continue  # skip existing tests
            results.append(f)

    return sorted(results)


def _output_path(src: Path, target: Path, output_dir: Path, lang: str) -> Path:
    try:
        rel = src.relative_to(target if target.is_dir() else target.parent)
    except ValueError:
        rel = Path(src.name)

    if lang in ("js", "ts", "javascript", "typescript"):
        stem = rel.stem
        parts = list(rel.parent.parts) + [f"{stem}.test.{rel.suffix.lstrip('.') or 'js'}"]
        return output_dir / Path(*parts)
    else:
        parts = list(rel.parent.parts) + [f"test_{rel.stem}.py"]
        return output_dir / Path(*parts)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        prog="bago testgen",
        description="Genera tests para repositorios o directorios desconocidos.")
    p.add_argument("target", nargs="?", default=".", help="Ruta al repo o directorio")
    p.add_argument("--lang", default="py", choices=["py","js","ts"],
                   help="Lenguaje objetivo (default: py)")
    p.add_argument("--output", "-o", default=None,
                   help="Directorio de salida (default: <target>/tests/generated/)")
    p.add_argument("--dry-run", action="store_true",
                   help="Muestra qué se generaría sin escribir")
    p.add_argument("--summary", action="store_true",
                   help="Solo resumen, sin mostrar código")
    p.add_argument("--max-files", type=int, default=50,
                   help="Máximo de archivos a procesar (default: 50)")
    p.add_argument("--test", action="store_true", help="Ejecuta self-tests")
    args = p.parse_args()

    if args.test:
        _self_test()
        return

    target = Path(args.target).resolve()
    if not target.exists():
        print(f"✗ No existe: {target}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output).resolve() if args.output else (
        (target if target.is_dir() else target.parent) / "tests" / "generated")

    lang = args.lang
    files = discover_files(target, lang)
    if not files:
        print(f"No se encontraron archivos {lang} en {target}")
        return

    if len(files) > args.max_files:
        print(f"  Limitando a {args.max_files} archivos (de {len(files)} encontrados)")
        files = files[:args.max_files]

    print(f"\n  bago testgen — Generador de tests")
    print(f"  Target: {target}")
    print(f"  Lenguaje: {lang}  |  Archivos: {len(files)}")
    if not args.dry_run:
        print(f"  Output: {output_dir}")
    print()

    total_tests = 0
    generated   = []

    for src in files:
        if lang in ("py", "python"):
            analysis = analyze_python_file(src)
            n_tests  = len(analysis["functions"]) + sum(
                len(c["methods"]) for c in analysis["classes"])
            content  = generate_python_test_file(analysis, src.relative_to(
                target if target.is_dir() else target.parent))
        else:
            analysis = analyze_js_file(src)
            n_tests  = len(analysis["funcs"])
            content  = generate_js_test_file(analysis)

        out_path = _output_path(src, target, output_dir, lang)
        total_tests += n_tests
        generated.append((src, out_path, content, n_tests))

        rel = str(src.relative_to(target if target.is_dir() else target.parent))
        status = "✗ error" if analysis.get("error") else f"{n_tests} tests"
        print(f"  {rel}  →  {status}")

        if not args.summary and not args.dry_run:
            pass  # written below

    print(f"\n  Total: {len(files)} archivos  |  ~{total_tests} test placeholders")

    if args.dry_run:
        print(f"\n  [dry-run] Se escribirían {len(files)} archivos en {output_dir}")
        return

    if args.summary:
        return

    # Write files
    written = 0
    for src, out_path, content, _ in generated:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(content, encoding="utf-8")
        written += 1

    # Write conftest.py if Python
    if lang == "py":
        conftest = output_dir / "conftest.py"
        if not conftest.exists():
            conftest.write_text(
                '"""Conftest auto-generado por bago testgen."""\n'
                'import sys, os\n'
                '# sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))\n',
                encoding="utf-8")
            written += 1

    print(f"\n  ✅ {written} archivos escritos en {output_dir}")
    print(f"  Ejecuta: cd {output_dir.parent.parent} && pytest {output_dir.relative_to(output_dir.parent.parent)}")


def _self_test():
    import tempfile, os
    print("Ejecutando self-tests de testgen.py...")
    errors = []

    # Test 1: analyze_python_file on itself
    me = Path(__file__)
    result = analyze_python_file(me)
    if result.get("error"):
        errors.append(f"analyze self: {result['error']}")
    elif not result["functions"]:
        errors.append("analyze self: no functions found")
    else:
        print(f"  OK: analyze_python_file — {len(result['functions'])} funciones encontradas")

    # Test 2: generate_python_test_file
    content = generate_python_test_file(result, me)
    if "def test_" not in content and "class Test" not in content:
        errors.append("generate_python: no test defs generated")
    else:
        print(f"  OK: generate_python_test_file — {content.count('def test_')} test_ defs")

    # Test 3: discover_files on temp dir
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "foo.py").write_text("def bar(): pass\n")
        (tdp / "baz.py").write_text("class MyClass:\n    def method(self): pass\n")
        files = discover_files(tdp, "py")
        if len(files) != 2:
            errors.append(f"discover_files: expected 2, got {len(files)}")
        else:
            print(f"  OK: discover_files — {len(files)} archivos encontrados")

    # Test 4: JS analysis
    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        (tdp / "util.js").write_text("function greet(name) { return 'hi'; }\n")
        files = discover_files(tdp, "js")
        if not files:
            errors.append("discover_files js: no js files found")
        else:
            a = analyze_js_file(files[0])
            if not a["funcs"]:
                errors.append("analyze_js: no funcs found")
            else:
                print(f"  OK: analyze_js_file — {len(a['funcs'])} funciones")
                content = generate_js_test_file(a)
                if "describe(" not in content:
                    errors.append("generate_js: no describe() block")
                else:
                    print(f"  OK: generate_js_test_file — describe block found")

    n = 4
    passed = n - len(errors)
    print(f"\n  {passed}/{n} tests pasaron")
    if errors:
        for e in errors:
            print(f"  FAIL: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()