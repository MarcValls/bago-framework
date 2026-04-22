#!/usr/bin/env python3
"""refactor_suggest.py — Herramienta #117: Sugerencias concretas de refactorización.

Analiza código Python y propone refactorizaciones específicas basadas en:
  RF-W001  Función demasiado larga (>50 líneas) — sugiere split
  RF-W002  Complejidad ciclomática alta (>10) — sugiere extracción de casos
  RF-W003  Función sin docstring con >5 args — sugiere documentar + wrapper
  RF-W004  Clase con >10 métodos públicos — sugiere dividir responsabilidades
  RF-W005  Importaciones redundantes (mismo módulo en múltiples formas)
  RF-I001  Parámetros booleanos en firma — sugiere usar Enum o dos funciones
  RF-I002  Bloques try/except muy amplios — sugiere acotar el try

Uso:
    bago refactor-suggest [FILE|DIR] [--min-severity warn|info]
                          [--format text|md|json] [--out FILE] [--test]
"""
from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RED  = "\033[0;31m"
_CYN  = "\033[0;36m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

SKIP_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules"}


@dataclass
class Suggestion:
    rule:       str
    severity:   str       # "warning" | "info"
    file:       str
    line:       int
    name:       str
    message:    str
    suggestion: str


def _cyclomatic(node) -> int:
    count = 1
    for n in ast.walk(node):
        if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                          ast.With, ast.Assert)):
            count += 1
        elif isinstance(n, ast.BoolOp):
            count += len(n.values) - 1
        elif isinstance(n, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            count += 1
    return count


def _func_lines(node) -> int:
    if not node.body:
        return 0
    first = node.body[0].lineno if hasattr(node.body[0], "lineno") else node.lineno
    # count non-empty lines
    return (node.end_lineno or node.lineno) - node.lineno + 1


def _bool_params(node) -> list[str]:
    """Detecta parámetros con default=True/False."""
    params = []
    for default, arg in zip(
        reversed(node.args.defaults),
        reversed(node.args.args)
    ):
        if isinstance(default, ast.Constant) and isinstance(default.value, bool):
            params.append(arg.arg)
    return params


def analyze_file(filepath: str) -> list[Suggestion]:
    try:
        source = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        tree   = ast.parse(source, filename=filepath)
    except Exception:
        return []

    suggestions: list[Suggestion] = []

    # RF-W005: importaciones redundantes
    import_modules: dict[str, list[int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                import_modules.setdefault(name, []).append(node.lineno)
        elif isinstance(node, ast.ImportFrom):
            name = node.module or ""
            import_modules.setdefault(name, []).append(node.lineno)

    for mod, lines in import_modules.items():
        if len(lines) > 1:
            suggestions.append(Suggestion(
                rule="RF-W005", severity="warning",
                file=filepath, line=lines[0], name=mod,
                message=f"Módulo '{mod}' importado en {len(lines)} líneas diferentes ({lines})",
                suggestion=f"Consolidar todas las importaciones de '{mod}' en una sola línea.",
            ))

    # Analizar funciones y métodos
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        name     = node.name
        lineno   = node.lineno
        n_lines  = _func_lines(node)
        n_args   = len(node.args.args)
        cx       = _cyclomatic(node)

        # RF-W001: función larga
        if n_lines > 50:
            suggestions.append(Suggestion(
                rule="RF-W001", severity="warning",
                file=filepath, line=lineno, name=name,
                message=f"Función '{name}' tiene {n_lines} líneas (límite: 50)",
                suggestion=(
                    f"Extrae subfunciones con nombres descriptivos. "
                    f"Busca bloques 'if/for' que puedan ser funciones independientes."
                ),
            ))

        # RF-W002: complejidad alta
        if cx > 10:
            suggestions.append(Suggestion(
                rule="RF-W002", severity="warning",
                file=filepath, line=lineno, name=name,
                message=f"'{name}' complejidad ciclomática {cx} (límite: 10)",
                suggestion=(
                    f"Usa early returns para reducir niveles de if/else. "
                    f"Extrae cada rama compleja a su propia función auxiliar."
                ),
            ))

        # RF-W003: muchos args sin docstring
        has_doc = (bool(node.body) and isinstance(node.body[0], ast.Expr)
                   and isinstance(node.body[0].value, ast.Constant))
        if n_args > 5 and not has_doc:
            suggestions.append(Suggestion(
                rule="RF-W003", severity="warning",
                file=filepath, line=lineno, name=name,
                message=f"'{name}' tiene {n_args} parámetros y no tiene docstring",
                suggestion=(
                    f"Agrega docstring. Considera agrupar parámetros relacionados "
                    f"en un dataclass o TypedDict."
                ),
            ))

        # RF-I001: parámetros booleanos
        bool_args = _bool_params(node)
        if bool_args:
            suggestions.append(Suggestion(
                rule="RF-I001", severity="info",
                file=filepath, line=lineno, name=name,
                message=f"'{name}' usa parámetros booleanos: {bool_args}",
                suggestion=(
                    f"Los flags booleanos suelen indicar que la función hace dos cosas. "
                    f"Considera separar en dos funciones o usar Enum."
                ),
            ))

        # RF-I002: try/except amplios
        for child in ast.walk(node):
            if isinstance(child, ast.Try):
                try_lines = (getattr(child, "end_lineno", child.lineno) - child.lineno)
                if try_lines > 10:
                    suggestions.append(Suggestion(
                        rule="RF-I002", severity="info",
                        file=filepath, line=child.lineno, name=name,
                        message=f"Bloque try/except de {try_lines} líneas en '{name}'",
                        suggestion=(
                            f"Acota el bloque try a la mínima operación que puede fallar. "
                            f"Maneja excepciones específicas, no `Exception` genérica."
                        ),
                    ))

    # RF-W004: clases con muchos métodos públicos
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        public_methods = [
            c for c in node.body
            if isinstance(c, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not c.name.startswith("_")
        ]
        if len(public_methods) > 10:
            suggestions.append(Suggestion(
                rule="RF-W004", severity="warning",
                file=filepath, line=node.lineno, name=node.name,
                message=f"Clase '{node.name}' tiene {len(public_methods)} métodos públicos",
                suggestion=(
                    f"Aplica Single Responsibility Principle: divide '{node.name}' "
                    f"en clases más pequeñas por responsabilidad."
                ),
            ))

    return suggestions


def analyze_directory(directory: str) -> list[Suggestion]:
    root = Path(directory)
    all_suggestions: list[Suggestion] = []
    for py_file in sorted(root.rglob("*.py")):
        if any(d in py_file.parts for d in SKIP_DIRS):
            continue
        all_suggestions.extend(analyze_file(str(py_file)))
    return all_suggestions


def generate_text(suggestions: list[Suggestion], min_sev: str = "info") -> str:
    filtered = [s for s in suggestions
                if min_sev == "info" or s.severity == "warning"]
    if not filtered:
        return f"{_GRN}✅ No se encontraron sugerencias de refactorización{_RST}"
    lines = [f"{_BOLD}Refactor Suggestions — {len(filtered)} sugerencia(s){_RST}", ""]
    for s in filtered:
        color = _YEL if s.severity == "warning" else _CYN
        lines += [
            f"  {color}[{s.rule}]{_RST} {Path(s.file).name}:{s.line} → {_BOLD}{s.name}{_RST}",
            f"    ⚠  {s.message}",
            f"    💡 {s.suggestion}",
            "",
        ]
    return "\n".join(lines)


def generate_markdown(suggestions: list[Suggestion]) -> str:
    if not suggestions:
        return "# Refactor Suggestions\n\n✅ No se encontraron sugerencias.\n"
    lines = [
        f"# Refactor Suggestions — {len(suggestions)} sugerencia(s)",
        "",
        "| Regla | Archivo | Línea | Función | Mensaje |",
        "|-------|---------|-------|---------|---------|",
    ]
    for s in suggestions:
        lines.append(
            f"| `{s.rule}` | `{Path(s.file).name}` | {s.line} "
            f"| `{s.name}` | {s.message} |"
        )
    lines += [
        "",
        "## Sugerencias detalladas",
        "",
    ]
    for s in suggestions:
        lines += [
            f"### `{s.rule}` — {s.name} ({Path(s.file).name}:{s.line})",
            f"",
            f"**Problema:** {s.message}",
            f"",
            f"**Sugerencia:** {s.suggestion}",
            f"",
        ]
    lines += ["---", "*Generado con `bago refactor-suggest`*"]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    target  = "./"
    min_sev = "info"
    fmt     = "text"
    out_file= None

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--min-severity" and i + 1 < len(argv):
            min_sev = argv[i + 1]; i += 2
        elif a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        elif not a.startswith("--"):
            target = a; i += 1
        else:
            i += 1

    target_path = Path(target)
    if not target_path.exists():
        print(f"No existe: {target}", file=sys.stderr); return 1

    if target_path.is_file():
        suggestions = analyze_file(target)
    else:
        suggestions = analyze_directory(target)

    if fmt == "json":
        content = json.dumps([asdict(s) for s in suggestions], indent=2)
    elif fmt == "md":
        content = generate_markdown(suggestions)
    else:
        content = generate_text(suggestions, min_sev)

    if out_file:
        Path(out_file).write_text(content, encoding="utf-8")
        print(f"Guardado: {out_file}", file=sys.stderr)
    else:
        print(content)
    return 0


def _self_test() -> None:
    import tempfile
    print("Tests de refactor_suggest.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        # T1 — función larga detectada RF-W001
        long_func = "def long_function():\n" + "    x = 1\n" * 55 + "    return x\n"
        (root / "long.py").write_text(long_func)
        suggs = analyze_file(str(root / "long.py"))
        rf001 = [s for s in suggs if s.rule == "RF-W001"]
        if rf001:
            ok("refactor_suggest:long_function")
        else:
            fail("refactor_suggest:long_function", f"suggs={suggs}")

        # T2 — función con bool param → RF-I001
        (root / "flags.py").write_text(
            "def send(msg, verbose=True, dry_run=False):\n    return msg\n"
        )
        suggs2 = analyze_file(str(root / "flags.py"))
        rf_i001 = [s for s in suggs2 if s.rule == "RF-I001"]
        if rf_i001:
            ok("refactor_suggest:bool_params")
        else:
            fail("refactor_suggest:bool_params", f"suggs={suggs2}")

        # T3 — importación duplicada RF-W005
        (root / "imports.py").write_text(
            "import os\nimport os.path\nfrom os import getcwd\n"
        )
        suggs3 = analyze_file(str(root / "imports.py"))
        rf_w005 = [s for s in suggs3 if s.rule == "RF-W005"]
        if rf_w005:
            ok("refactor_suggest:duplicate_imports")
        else:
            fail("refactor_suggest:duplicate_imports", f"suggs={[s.rule for s in suggs3]}")

        # T4 — clase con muchos métodos RF-W004
        methods  = "\n".join(f"    def method_{i}(self): pass" for i in range(12))
        (root / "bigcls.py").write_text(f"class BigClass:\n{methods}\n")
        suggs4 = analyze_file(str(root / "bigcls.py"))
        rf_w004 = [s for s in suggs4 if s.rule == "RF-W004"]
        if rf_w004:
            ok("refactor_suggest:big_class")
        else:
            fail("refactor_suggest:big_class", f"suggs={[s.rule for s in suggs4]}")

        # T5 — archivo limpio sin sugerencias
        (root / "clean.py").write_text(
            '"""Módulo limpio."""\ndef add(a, b):\n    """Suma."""\n    return a + b\n'
        )
        clean = analyze_file(str(root / "clean.py"))
        if not clean:
            ok("refactor_suggest:clean_no_suggestions")
        else:
            fail("refactor_suggest:clean_no_suggestions", f"unexpected={clean}")

        # T6 — markdown generado
        md = generate_markdown(rf001)
        if "Refactor Suggestions" in md and "RF-W001" in md:
            ok("refactor_suggest:markdown_output")
        else:
            fail("refactor_suggest:markdown_output", md[:80])

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
