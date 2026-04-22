#!/usr/bin/env python3
"""complexity.py — Herramienta #104: Analizador de complejidad ciclomática (Python).

Calcula la complejidad ciclomática de Mccabe para funciones y métodos Python.
Identifica funciones complejas (hotspots de mantenibilidad).

Métricas:
  1-5  → Simple (verde)
  6-10 → Moderada (amarillo)
  11+  → Alta (rojo, candidato a refactor)

Uso:
    bago complexity [TARGET] [--min N] [--max N] [--json] [--sort]
                    [--functions-only] [--test]

Opciones:
    TARGET         Archivo o directorio (default: ./)
    --min N        Solo mostrar funciones con complejidad >= N (default: 1)
    --max N        Solo mostrar funciones con complejidad <= N
    --json         Output en JSON
    --sort         Ordenar por complejidad (mayor primero)
    --functions-only  Solo funciones, no métodos de clase
    --test         Self-tests
"""
from __future__ import annotations

import ast
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

_RED  = "\033[0;31m"
_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RST  = "\033[0m"
_BOLD = "\033[1m"
_DIM  = "\033[2m"


@dataclass
class FuncComplexity:
    file:       str
    name:       str
    lineno:     int
    complexity: int
    is_method:  bool
    class_name: str = ""


def _cyclomatic_complexity(node: ast.AST) -> int:
    """Calcula complejidad ciclomática de un nodo función/método.
    Complejidad = 1 + #decisiones (if, elif, for, while, with, assert, except, and, or, ternary)
    """
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler,
                               ast.With, ast.Assert, ast.comprehension)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, ast.IfExp):  # ternary a if cond else b
            complexity += 1
    return complexity


def analyze_file(filepath: str, functions_only: bool = False) -> list[FuncComplexity]:
    """Analiza un archivo Python y devuelve complejidad por función/método."""
    path = Path(filepath)
    if not path.exists() or path.suffix != ".py":
        return []
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        tree   = ast.parse(source, filename=filepath)
    except SyntaxError:
        return []

    results: list[FuncComplexity] = []

    # Top-level functions
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            cc = _cyclomatic_complexity(node)
            results.append(FuncComplexity(
                file=filepath, name=node.name, lineno=node.lineno,
                complexity=cc, is_method=False
            ))
        elif isinstance(node, ast.ClassDef) and not functions_only:
            for child in ast.iter_child_nodes(node):
                if isinstance(child, ast.FunctionDef):
                    cc = _cyclomatic_complexity(child)
                    results.append(FuncComplexity(
                        file=filepath, name=child.name, lineno=child.lineno,
                        complexity=cc, is_method=True, class_name=node.name
                    ))

    return results


def analyze_target(target: str, functions_only: bool = False) -> list[FuncComplexity]:
    """Escanea archivo o directorio."""
    p = Path(target)
    files: list[Path] = []
    if p.is_file():
        files = [p]
    elif p.is_dir():
        files = [f for f in p.rglob("*.py")
                 if not any(x in f.parts for x in ("node_modules", "__pycache__", ".git", "venv", ".venv"))]
    all_results: list[FuncComplexity] = []
    for f in sorted(files):
        all_results.extend(analyze_file(str(f), functions_only))
    return all_results


def _sev_label(cc: int) -> tuple[str, str]:
    if cc >= 11:
        return _RED, "ALTA"
    if cc >= 6:
        return _YEL, "MEDIA"
    return _GRN, "SIMPLE"


def _spark_bar(cc: int, max_cc: int = 20) -> str:
    blocks = "▏▎▍▌▋▊▉█"
    ratio  = min(cc / max_cc, 1.0)
    n_full = int(ratio * 10)
    return "█" * n_full + "░" * (10 - n_full)


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    target         = "./"
    min_cc         = 1
    max_cc_filter  = None
    as_json        = False
    do_sort        = False
    functions_only = False

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--min" and i + 1 < len(argv):
            min_cc = int(argv[i + 1]); i += 2
        elif a == "--max" and i + 1 < len(argv):
            max_cc_filter = int(argv[i + 1]); i += 2
        elif a == "--json":
            as_json = True; i += 1
        elif a == "--sort":
            do_sort = True; i += 1
        elif a == "--functions-only":
            functions_only = True; i += 1
        elif not a.startswith("--"):
            target = a; i += 1
        else:
            i += 1

    results = analyze_target(target, functions_only)

    # Filtros
    results = [r for r in results if r.complexity >= min_cc]
    if max_cc_filter is not None:
        results = [r for r in results if r.complexity <= max_cc_filter]
    if do_sort:
        results.sort(key=lambda r: -r.complexity)

    if as_json:
        max_val = max((r.complexity for r in results), default=1)
        out = {
            "target": target,
            "total_functions": len(results),
            "high_complexity": sum(1 for r in results if r.complexity >= 11),
            "medium_complexity": sum(1 for r in results if 6 <= r.complexity < 11),
            "max_complexity": max_val,
            "avg_complexity": round(sum(r.complexity for r in results) / len(results), 2) if results else 0,
            "functions": [asdict(r) for r in results],
        }
        print(json.dumps(out, indent=2))
        return 1 if any(r.complexity >= 11 for r in results) else 0

    if not results:
        print(f"{_GRN}✅ Sin funciones en el rango especificado{_RST}")
        return 0

    high   = [r for r in results if r.complexity >= 11]
    medium = [r for r in results if 6 <= r.complexity < 11]
    max_cc = max(r.complexity for r in results)

    print(f"\n{_BOLD}Complexity Scan — {target}{_RST}")
    print(f"Funciones: {len(results)} | Alta: {len(high)} | Media: {len(medium)} | Max: {max_cc}\n")

    for r in results:
        color, label = _sev_label(r.complexity)
        bar = _spark_bar(r.complexity, max_cc)
        name = f"{r.class_name}.{r.name}" if r.class_name else r.name
        print(f"  {color}{r.complexity:3d}{_RST} {bar} {color}{label:6s}{_RST}  "
              f"{r.file}:{r.lineno}  {name}")

    if high:
        print(f"\n{_RED}⚠️  {len(high)} función(es) con complejidad ALTA (≥11) — candidatas a refactor{_RST}")

    return 1 if high else 0


# ─── Self-tests ────────────────────────────────────────────────────────────

def _self_test() -> None:
    import tempfile, textwrap
    print("Tests de complexity.py...")
    fails: list[str] = []
    def ok(n: str): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    # T1 — función simple: complejidad 1
    src1 = "def simple(): return 42\n"
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(src1); tmp1 = f.name
    r = analyze_file(tmp1)
    if r and r[0].complexity == 1 and r[0].name == "simple":
        ok("complexity:simple_func_cc1")
    else:
        fail("complexity:simple_func_cc1", f"cc={r[0].complexity if r else 'None'}")

    # T2 — función con if/elif aumenta complejidad
    src2 = textwrap.dedent("""\
        def complex_func(x):
            if x > 0:
                return 1
            elif x < 0:
                return -1
            elif x == 0:
                return 0
            else:
                for i in range(x):
                    if i % 2 == 0:
                        continue
                return -2
    """)
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(src2); tmp2 = f.name
    r2 = analyze_file(tmp2)
    if r2 and r2[0].complexity >= 5:
        ok("complexity:complex_func_high_cc")
    else:
        fail("complexity:complex_func_high_cc", f"cc={r2[0].complexity if r2 else 'None'}")

    # T3 — método de clase detectado
    src3 = textwrap.dedent("""\
        class MyClass:
            def my_method(self, x):
                if x: return x
                return 0
    """)
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as f:
        f.write(src3); tmp3 = f.name
    r3 = analyze_file(tmp3)
    methods = [x for x in r3 if x.is_method and x.class_name == "MyClass"]
    if methods:
        ok("complexity:method_detected")
    else:
        fail("complexity:method_detected", f"r3={r3}")

    # T4 — analyze_target con archivo .py directo
    r4 = analyze_target(tmp1)
    if r4 and r4[0].name == "simple":
        ok("complexity:analyze_target_file")
    else:
        fail("complexity:analyze_target_file", f"r4={r4}")

    # T5 — directorio vacío sin .py → lista vacía
    with tempfile.TemporaryDirectory() as td:
        (Path(td) / "test.txt").write_text("hello")
        r5 = analyze_target(td)
    if r5 == []:
        ok("complexity:empty_dir_no_results")
    else:
        fail("complexity:empty_dir_no_results", f"found {len(r5)}")

    # T6 — _sev_label clasifica correctamente
    c1, l1 = _sev_label(1)
    c2, l2 = _sev_label(7)
    c3, l3 = _sev_label(15)
    if l1 == "SIMPLE" and l2 == "MEDIA" and l3 == "ALTA":
        ok("complexity:sev_label_correct")
    else:
        fail("complexity:sev_label_correct", f"labels={l1},{l2},{l3}")

    for t in [tmp1, tmp2, tmp3]:
        Path(t).unlink(missing_ok=True)

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
