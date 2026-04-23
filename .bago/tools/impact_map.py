#!/usr/bin/env python3
"""impact_map.py — Herramienta #110: Mapa de impacto de cambios en archivos Python.

Para un archivo dado, detecta qué otros archivos lo importan y qué archivos
importa él. Genera un mapa de dependencias directo en Markdown/JSON.
Útil para evaluar el riesgo de un cambio antes de hacerlo.

Uso:
    bago impact-map FILE [TARGET_DIR] [--depth N] [--format md|json|dot]
                         [--out FILE] [--test]

Opciones:
    FILE         Archivo Python a analizar
    TARGET_DIR   Directorio raíz donde buscar dependientes (default: ./)
    --depth N    Profundidad del grafo transitivo (default: 2)
    --format     md (default) | json | dot (Graphviz)
    --out FILE   Guardar en archivo
    --test       Self-tests
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from typing import Optional

_BLU  = "\033[0;34m"
_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RED  = "\033[0;31m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

SKIP_DIRS = {"node_modules", "__pycache__", ".git", "venv", ".venv", ".mypy_cache"}


def _get_imports(filepath: str) -> set[str]:
    """Extrae nombres de módulos importados en el archivo."""
    try:
        source = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        tree   = ast.parse(source, filename=filepath)
    except Exception:
        return set()

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
    return imports


def _collect_py_files(directory: str) -> list[Path]:
    root = Path(directory)
    return [f for f in root.rglob("*.py")
            if not any(d in f.parts for d in SKIP_DIRS)]


def find_dependents(target_file: str, search_dir: str) -> list[str]:
    """Encuentra archivos que importan el módulo del target_file."""
    target_name = Path(target_file).stem
    dependents: list[str] = []
    for py_file in _collect_py_files(search_dir):
        if str(py_file) == str(Path(target_file).resolve()):
            continue
        imports = _get_imports(str(py_file))
        if target_name in imports:
            dependents.append(str(py_file))
    return sorted(dependents)


def find_dependencies(target_file: str, search_dir: str) -> list[str]:
    """Encuentra archivos locales que target_file importa."""
    imports = _get_imports(target_file)
    py_files = _collect_py_files(search_dir)
    stems    = {f.stem: str(f) for f in py_files}
    return sorted(stems[m] for m in imports if m in stems)


def build_impact_graph(target_file: str, search_dir: str,
                        depth: int = 2) -> dict:
    """Construye grafo de impacto hasta depth niveles."""
    graph: dict[str, dict] = {}
    visited: set[str] = set()

    def _explore(filepath: str, current_depth: int) -> None:
        if current_depth <= 0 or filepath in visited:
            return
        visited.add(filepath)
        deps  = find_dependencies(filepath, search_dir)
        users = find_dependents(filepath, search_dir)
        graph[filepath] = {
            "imports":    deps,
            "imported_by": users,
            "depth": depth - current_depth,
        }
        for dep in deps + users:
            _explore(dep, current_depth - 1)

    _explore(str(Path(target_file).resolve()), depth)
    return graph


def generate_markdown(target: str, graph: dict, search_dir: str) -> str:
    root_data = graph.get(str(Path(target).resolve()), {})
    deps      = root_data.get("imports", [])
    users     = root_data.get("imported_by", [])
    lines = [
        f"# Impact Map — `{Path(target).name}`",
        f"",
        f"> Análisis de dependencias para evaluar riesgo de cambio.",
        f"",
        f"---",
        f"",
        f"## 📥 Dependencias directas ({len(deps)} archivos)",
        f"",
        f"*Archivos que `{Path(target).name}` importa:*",
        f"",
    ]
    if deps:
        for d in deps:
            lines.append(f"- `{Path(d).name}`  ← `{d}`")
    else:
        lines.append("- *(sin dependencias locales)*")

    lines += [
        f"",
        f"## 📤 Dependientes directos ({len(users)} archivos)",
        f"",
        f"*Archivos que importan `{Path(target).name}`:*",
        f"",
    ]
    if users:
        for u in users:
            risk = "🔴 ALTO" if len(users) > 5 else ("🟡 MEDIO" if len(users) > 2 else "🟢 BAJO")
            lines.append(f"- `{Path(u).name}`  `{u}`")
        lines += [
            f"",
            f"**Nivel de impacto de un cambio:** {risk}",
        ]
    else:
        lines.append("- *(nadie importa este módulo localmente)*")
        lines.append("")
        lines.append("**Nivel de impacto:** 🟢 BAJO (módulo hoja)")

    # Transitivo
    transitive = {k for k in graph if k != str(Path(target).resolve())}
    if transitive:
        lines += [
            f"",
            f"## 🔗 Afectados transitivos ({len(transitive)} archivos)",
            f"",
        ]
        for t in sorted(transitive):
            lines.append(f"- `{Path(t).name}`")

    lines += ["", "---", f"*Generado con `bago impact-map`*", ""]
    return "\n".join(lines)


def generate_dot(target: str, graph: dict) -> str:
    """Genera formato Graphviz DOT."""
    lines = ["digraph impact {", '  rankdir=LR;', '  node [shape=box];']
    root = str(Path(target).resolve())
    lines.append(f'  "{Path(root).stem}" [style=filled, fillcolor=lightblue];')
    for filepath, data in graph.items():
        src = Path(filepath).stem
        for dep in data["imports"]:
            lines.append(f'  "{src}" -> "{Path(dep).stem}";')
    lines.append("}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    if not argv or argv[0].startswith("--"):
        print("Uso: bago impact-map FILE [TARGET_DIR] [--depth N] [--format md|json|dot]")
        return 1

    target     = argv[0]
    search_dir = "./"
    depth      = 2
    fmt        = "md"
    out_file   = None

    i = 1
    while i < len(argv):
        a = argv[i]
        if a == "--depth" and i + 1 < len(argv):
            depth = int(argv[i + 1]); i += 2
        elif a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        elif not a.startswith("--"):
            search_dir = a; i += 1
        else:
            i += 1

    if not Path(target).exists():
        print(f"Archivo no encontrado: {target}", file=sys.stderr)
        return 1

    graph = build_impact_graph(target, search_dir, depth)

    if fmt == "json":
        content = json.dumps(graph, indent=2)
    elif fmt == "dot":
        content = generate_dot(target, graph)
    else:
        content = generate_markdown(target, graph, search_dir)

    if out_file:
        Path(out_file).write_text(content, encoding="utf-8")
        print(f"{_GRN}✅ Impact map guardado: {out_file}{_RST}", file=sys.stderr)
    else:
        print(content)
    return 0


def _self_test() -> None:
    import tempfile, textwrap
    print("Tests de impact_map.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        # Crear módulo base
        (root / "utils.py").write_text("def helper(): pass\n")
        # Crear módulo que importa utils
        (root / "service.py").write_text("from utils import helper\ndef run(): helper()\n")
        # Crear módulo que no importa nada local
        (root / "standalone.py").write_text("import os\ndef main(): pass\n")

        # T1 — _get_imports detecta imports
        imports = _get_imports(str(root / "service.py"))
        if "utils" in imports:
            ok("impact_map:get_imports")
        else:
            fail("impact_map:get_imports", f"imports={imports}")

        # T2 — find_dependents: service.py usa utils.py
        deps = find_dependents(str(root / "utils.py"), td)
        if any("service.py" in d for d in deps):
            ok("impact_map:find_dependents")
        else:
            fail("impact_map:find_dependents", f"deps={deps}")

        # T3 — find_dependencies: service.py depende de utils.py
        local_deps = find_dependencies(str(root / "service.py"), td)
        if any("utils.py" in d for d in local_deps):
            ok("impact_map:find_dependencies")
        else:
            fail("impact_map:find_dependencies", f"local_deps={local_deps}")

        # T4 — standalone no tiene dependientes ni dependencias locales
        dep4 = find_dependents(str(root / "standalone.py"), td)
        dep5 = find_dependencies(str(root / "standalone.py"), td)
        if not dep4 and not dep5:
            ok("impact_map:standalone_no_deps")
        else:
            fail("impact_map:standalone_no_deps", f"dep4={dep4} dep5={dep5}")

        # T5 — markdown generado contiene secciones clave
        graph = build_impact_graph(str(root / "utils.py"), td, depth=1)
        md = generate_markdown(str(root / "utils.py"), graph, td)
        if "Dependientes" in md and "Dependencias" in md:
            ok("impact_map:markdown_sections")
        else:
            fail("impact_map:markdown_sections", "secciones faltantes")

        # T6 — dot generado
        dot = generate_dot(str(root / "utils.py"), graph)
        if "digraph impact" in dot:
            ok("impact_map:dot_generated")
        else:
            fail("impact_map:dot_generated", f"dot={dot[:50]}")

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: raise SystemExit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        raise SystemExit(main(sys.argv[1:]))
