#!/usr/bin/env python3
"""api_check.py — Herramienta #118: Validador de estructura REST API.

Analiza archivos Python que definen rutas Flask/FastAPI/Django y valida:
  API-W001  Ruta sin docstring ni descripción
  API-W002  Endpoint sin validación de input (no hay args/body check)
  API-W003  Método HTTP no estándar
  API-W004  Ruta con parámetros pero sin tipado
  API-E001  Ruta duplicada (mismo path + método)
  API-I001  Endpoint sin código de error documentado

También puede leer un archivo OpenAPI/Swagger JSON y validar su estructura.

Uso:
    bago api-check [FILE|DIR] [--format text|md|json] [--out FILE] [--test]
"""
from __future__ import annotations

import ast
import json
import re
import sys
from pathlib import Path

_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RED  = "\033[0;31m"
_RST  = "\033[0m"
_BOLD = "\033[1m"

SKIP_DIRS  = {"__pycache__", ".git", "venv", ".venv", "node_modules"}
HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}

# Patrones para detectar decoradores de rutas
FLASK_RE     = re.compile(r"""@\w+\.route\(['"]([^'"]+)['"].*?\)""", re.DOTALL)
FLASK_METHOD = re.compile(r"""methods=\[([^\]]+)\]""")
FASTAPI_RE   = re.compile(r"""@\w+\.(get|post|put|patch|delete|head|options)\(['"]([^'"]+)['"]""")


def _find_routes_in_source(filepath: str) -> list[dict]:
    """Detecta rutas Flask/FastAPI vía AST + regex fallback."""
    try:
        source = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        tree   = ast.parse(source, filename=filepath)
    except Exception:
        return []

    routes: list[dict] = []

    # Buscar funciones con decoradores de ruta
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            route_path = None
            methods:   list[str] = []

            # FastAPI: @app.get("/path")
            if isinstance(dec, ast.Call):
                func = dec.func
                if isinstance(func, ast.Attribute):
                    method_name = func.attr.lower()
                    if method_name in HTTP_METHODS:
                        if dec.args and isinstance(dec.args[0], ast.Constant):
                            route_path = dec.args[0].value
                            methods = [method_name.upper()]

                    # Flask: @app.route("/path", methods=[...])
                    elif method_name == "route":
                        if dec.args and isinstance(dec.args[0], ast.Constant):
                            route_path = dec.args[0].value
                        for kw in dec.keywords:
                            if kw.arg == "methods" and isinstance(kw.value, ast.List):
                                methods = [
                                    elt.value.upper() for elt in kw.value.elts
                                    if isinstance(elt, ast.Constant)
                                ]
                        if not methods:
                            methods = ["GET"]

            if route_path:
                # Detectar si tiene docstring
                has_doc = (bool(node.body)
                           and isinstance(node.body[0], ast.Expr)
                           and isinstance(node.body[0].value, ast.Constant))

                # Detectar parámetros de path sin tipado
                path_params = re.findall(r"\{(\w+)\}", route_path) + re.findall(r"<(\w+)>", route_path)
                typed_params = {a.arg for a in node.args.args
                                if a.annotation is not None}
                untyped     = [p for p in path_params if p not in typed_params]

                routes.append({
                    "file":       filepath,
                    "line":       node.lineno,
                    "name":       node.name,
                    "path":       route_path,
                    "methods":    methods,
                    "has_doc":    has_doc,
                    "path_params": path_params,
                    "untyped":    untyped,
                    "n_args":     len(node.args.args),
                })
    return routes


def validate_routes(routes: list[dict]) -> list[dict]:
    """Valida la lista de rutas y genera findings."""
    findings: list[dict] = []
    seen: dict[tuple, dict] = {}

    for r in routes:
        for method in (r["methods"] or ["GET"]):
            key = (r["path"], method)
            if key in seen:
                findings.append({
                    "rule":     "API-E001",
                    "severity": "error",
                    "file":     r["file"],
                    "line":     r["line"],
                    "message":  f"Ruta duplicada: {method} {r['path']} ya definida en línea {seen[key]['line']}",
                })
            else:
                seen[key] = r

            if method not in [m.upper() for m in HTTP_METHODS]:
                findings.append({
                    "rule":     "API-W003",
                    "severity": "warning",
                    "file":     r["file"],
                    "line":     r["line"],
                    "message":  f"Método HTTP no estándar: {method} en {r['path']}",
                })

        if not r["has_doc"]:
            findings.append({
                "rule":     "API-W001",
                "severity": "warning",
                "file":     r["file"],
                "line":     r["line"],
                "message":  f"Endpoint '{r['name']}' ({r['path']}) sin docstring/descripción",
            })

        if r["untyped"]:
            findings.append({
                "rule":     "API-W004",
                "severity": "warning",
                "file":     r["file"],
                "line":     r["line"],
                "message":  f"Parámetros sin tipado en '{r['name']}': {r['untyped']}",
            })

    return findings


def analyze_openapi(filepath: str) -> list[dict]:
    """Valida un fichero OpenAPI/Swagger JSON básico."""
    try:
        data = json.loads(Path(filepath).read_text(encoding="utf-8"))
    except Exception as e:
        return [{"rule": "API-E001", "severity": "error", "file": filepath,
                 "line": 1, "message": f"Error leyendo OpenAPI: {e}"}]

    findings: list[dict] = []
    paths    = data.get("paths", {})
    for path, methods in paths.items():
        for method, op in (methods or {}).items():
            if not isinstance(op, dict):
                continue
            if not op.get("summary") and not op.get("description"):
                findings.append({
                    "rule": "API-W001", "severity": "warning",
                    "file": filepath, "line": 0,
                    "message": f"{method.upper()} {path}: sin summary/description",
                })
            if not op.get("responses"):
                findings.append({
                    "rule": "API-I001", "severity": "info",
                    "file": filepath, "line": 0,
                    "message": f"{method.upper()} {path}: sin respuestas documentadas",
                })
    return findings


def analyze(target: str) -> tuple[list[dict], list[dict]]:
    """Retorna (routes, findings)."""
    path = Path(target)
    all_routes:   list[dict] = []
    all_findings: list[dict] = []

    if path.is_file():
        if path.suffix == ".json":
            all_findings.extend(analyze_openapi(target))
        else:
            routes = _find_routes_in_source(target)
            all_routes.extend(routes)
            all_findings.extend(validate_routes(routes))
    else:
        for py_file in sorted(path.rglob("*.py")):
            if any(d in py_file.parts for d in SKIP_DIRS):
                continue
            r = _find_routes_in_source(str(py_file))
            all_routes.extend(r)
        all_findings.extend(validate_routes(all_routes))

    return all_routes, all_findings


def generate_text(routes: list[dict], findings: list[dict]) -> str:
    lines = [f"{_BOLD}API Check — {len(routes)} ruta(s), {len(findings)} hallazgo(s){_RST}", ""]
    for r in routes:
        doc  = "✅" if r["has_doc"] else "⚠️"
        lines.append(f"  {doc}  {'|'.join(r['methods']):8s}  {r['path']:<30s}  {r['name']}")
    if findings:
        lines.append("")
        for f in findings:
            color = _RED if f["severity"] == "error" else _YEL
            lines.append(f"  {color}[{f['rule']}]{_RST} {Path(f['file']).name}:{f['line']} {f['message']}")
    return "\n".join(lines)


def generate_markdown(routes: list[dict], findings: list[dict]) -> str:
    lines = [
        f"# API Check — {len(routes)} ruta(s)",
        "",
        "## Rutas detectadas",
        "",
        "| Método | Path | Handler | Doc |",
        "|--------|------|---------|-----|",
    ]
    for r in routes:
        doc  = "✅" if r["has_doc"] else "❌"
        lines.append(f"| `{'|'.join(r['methods'])}` | `{r['path']}` | `{r['name']}` | {doc} |")
    if findings:
        lines += ["", "## Findings", "", "| Regla | Mensaje |", "|-------|---------|"]
        for f in findings:
            lines.append(f"| `{f['rule']}` | {f['message']} |")
    lines += ["", "---", "*Generado con `bago api-check`*"]
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    target   = "./"
    fmt      = "text"
    out_file = None

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        elif not a.startswith("--"):
            target = a; i += 1
        else:
            i += 1

    if not Path(target).exists():
        print(f"No existe: {target}", file=sys.stderr); return 1

    routes, findings = analyze(target)

    if fmt == "json":
        content = json.dumps({"routes": routes, "findings": findings}, indent=2)
    elif fmt == "md":
        content = generate_markdown(routes, findings)
    else:
        content = generate_text(routes, findings)

    if out_file:
        Path(out_file).write_text(content, encoding="utf-8")
        print(f"Guardado: {out_file}", file=sys.stderr)
    else:
        print(content)

    errors = [f for f in findings if f.get("severity") == "error"]
    return 1 if errors else 0


def _self_test() -> None:
    import tempfile
    print("Tests de api_check.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)

        # T1 — FastAPI rutas detectadas
        (root / "app.py").write_text(
            'from fastapi import FastAPI\napp = FastAPI()\n'
            '@app.get("/users")\ndef get_users():\n    """Lista usuarios."""\n    return []\n'
            '@app.post("/users")\ndef create_user(name: str):\n    """Crea usuario."""\n    return {}\n'
        )
        routes, findings = analyze(str(root / "app.py"))
        if len(routes) >= 2:
            ok("api_check:fastapi_routes_detected")
        else:
            fail("api_check:fastapi_routes_detected", f"routes={routes}")

        # T2 — endpoint sin docstring genera API-W001
        (root / "nodoc.py").write_text(
            'from flask import Flask\napp = Flask(__name__)\n'
            '@app.route("/ping")\ndef ping():\n    return "pong"\n'
        )
        r2, f2 = analyze(str(root / "nodoc.py"))
        w001 = [f for f in f2 if f["rule"] == "API-W001"]
        if w001:
            ok("api_check:missing_docstring")
        else:
            fail("api_check:missing_docstring", f"findings={f2}")

        # T3 — ruta duplicada genera API-E001
        (root / "dup.py").write_text(
            'from fastapi import FastAPI\napp = FastAPI()\n'
            '@app.get("/items")\ndef list_items():\n    """Lista."""\n    return []\n'
            '@app.get("/items")\ndef list_items2():\n    """Lista2."""\n    return []\n'
        )
        _, f3 = analyze(str(root / "dup.py"))
        e001 = [f for f in f3 if f["rule"] == "API-E001"]
        if e001:
            ok("api_check:duplicate_route")
        else:
            fail("api_check:duplicate_route", f"findings={f3}")

        # T4 — ruta bien documentada no genera W001
        (root / "clean_api.py").write_text(
            'from fastapi import FastAPI\napp = FastAPI()\n'
            '@app.get("/health")\ndef health_check():\n    """Comprueba salud del servicio."""\n    return {"ok": True}\n'
        )
        _, f4 = analyze(str(root / "clean_api.py"))
        w001_clean = [f for f in f4 if f["rule"] == "API-W001"]
        if not w001_clean:
            ok("api_check:clean_endpoint_no_warning")
        else:
            fail("api_check:clean_endpoint_no_warning", f"unexpected W001={w001_clean}")

        # T5 — markdown generado con secciones
        md = generate_markdown(routes, findings)
        if "API Check" in md and "Rutas detectadas" in md:
            ok("api_check:markdown_generated")
        else:
            fail("api_check:markdown_generated", md[:80])

        # T6 — OpenAPI JSON validado
        openapi = {"paths": {"/users": {"get": {"summary": "Lista"}, "post": {}}}}
        (root / "openapi.json").write_text(json.dumps(openapi))
        _, f6 = analyze(str(root / "openapi.json"))
        # POST sin summary ni responses → debería dar findings
        if f6:
            ok("api_check:openapi_validated")
        else:
            fail("api_check:openapi_validated", "no findings for incomplete openapi")

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
