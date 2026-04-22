#!/usr/bin/env python3
"""install_deps.py — Herramienta #95: Auto-instalador de dependencias opcionales de BAGO.

Verifica y opcionalmente instala: flake8, pylint, mypy, bandit, black,
eslint (npx), acorn, acorn-walk, golangci-lint, cargo/clippy.

Uso:
    python3 install_deps.py [--check] [--install] [--json] [--test]
    bago install-deps [--check] [--install]

Opciones:
    --check     Solo verificar disponibilidad (sin instalar)
    --install   Instalar los que falten (pip/npm según corresponda)
    --json      Output en JSON
    --test      Ejecutar self-tests y salir
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

# ─── Dependencias conocidas ────────────────────────────────────────────────

@dataclass
class Dep:
    name: str                  # nombre de visualización
    cmd: str                   # comando a buscar con shutil.which
    lang: str                  # py / js / go / rust / node
    install_cmd: list[str]     # comando de instalación
    version_flag: str = "--version"  # cómo obtener versión
    optional: bool = True      # ¿se puede funcionar sin él?
    alt_check: Optional[str] = None  # alternativa si cmd no está en PATH


DEPS: list[Dep] = [
    # Python
    Dep("flake8",   "flake8",       "py",   ["pip", "install", "flake8"]),
    Dep("pylint",   "pylint",       "py",   ["pip", "install", "pylint"]),
    Dep("mypy",     "mypy",         "py",   ["pip", "install", "mypy"]),
    Dep("bandit",   "bandit",       "py",   ["pip", "install", "bandit"]),
    Dep("black",    "black",        "py",   ["pip", "install", "black"]),
    # JS / Node
    Dep("node",     "node",         "node", [],   optional=False),
    Dep("npm",      "npm",          "node", []),
    Dep("npx",      "npx",          "node", []),
    Dep("eslint (npx)", "npx",      "js",   [],   alt_check="eslint"),
    # npm packages (verificados como módulos node)
    Dep("acorn",    "acorn",        "js",   ["npm", "install", "acorn"],
        version_flag="", alt_check="node_modules/acorn"),
    Dep("acorn-walk", "acorn-walk", "js",   ["npm", "install", "acorn-walk"],
        version_flag="", alt_check="node_modules/acorn-walk"),
    # Go
    Dep("golangci-lint", "golangci-lint", "go", [], version_flag="--version"),
    # Rust
    Dep("cargo",    "cargo",        "rust", []),
    Dep("clippy",   "cargo",        "rust", [],   alt_check="clippy"),
]


# ─── Checks ────────────────────────────────────────────────────────────────

import os as _os

BAGO_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), "..", ".."))


@dataclass
class DepResult:
    name: str
    lang: str
    available: bool
    version: str = ""
    install_cmd: list[str] = field(default_factory=list)
    optional: bool = True


def _check_dep(dep: Dep) -> DepResult:
    """Verifica si una dependencia está disponible."""
    available = False
    version = ""

    if dep.alt_check and dep.alt_check.startswith("node_modules/"):
        # npm package — verificar en node_modules
        pkg_path = _os.path.join(BAGO_ROOT, dep.alt_check)
        available = _os.path.isdir(pkg_path)
        if available:
            pkg_json = _os.path.join(pkg_path, "package.json")
            if _os.path.exists(pkg_json):
                try:
                    with open(pkg_json) as f:
                        data = json.load(f)
                    version = data.get("version", "")
                except Exception:
                    version = ""
    elif dep.alt_check == "clippy":
        # cargo +stable clippy --version
        try:
            r = subprocess.run(
                ["cargo", "clippy", "--version"],
                capture_output=True, text=True, timeout=5
            )
            available = r.returncode == 0
            version = r.stdout.strip().split("\n")[0]
        except Exception:
            available = False
    elif dep.alt_check == "eslint":
        try:
            r = subprocess.run(
                ["npx", "eslint", "--version"],
                capture_output=True, text=True, timeout=8
            )
            available = r.returncode == 0
            version = r.stdout.strip()
        except Exception:
            available = False
    else:
        path = shutil.which(dep.cmd)
        if path:
            available = True
            if dep.version_flag:
                try:
                    r = subprocess.run(
                        [dep.cmd, dep.version_flag],
                        capture_output=True, text=True, timeout=5
                    )
                    out = r.stdout.strip() or r.stderr.strip()
                    version = out.split("\n")[0]
                except Exception:
                    version = ""

    return DepResult(
        name=dep.name,
        lang=dep.lang,
        available=available,
        version=version,
        install_cmd=dep.install_cmd,
        optional=dep.optional,
    )


def check_all() -> list[DepResult]:
    return [_check_dep(d) for d in DEPS]


# ─── Instalación ───────────────────────────────────────────────────────────

def install_missing(results: list[DepResult]) -> dict[str, bool]:
    """Intenta instalar los deps ausentes que tienen install_cmd."""
    installed: dict[str, bool] = {}
    for r in results:
        if r.available or not r.install_cmd:
            continue
        cmd = r.install_cmd
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            installed[r.name] = proc.returncode == 0
        except Exception as e:
            installed[r.name] = False
    return installed


# ─── CLI ───────────────────────────────────────────────────────────────────

_RED   = "\033[0;31m"
_GRN   = "\033[0;32m"
_YEL   = "\033[0;33m"
_CYAN  = "\033[0;36m"
_RST   = "\033[0m"
_BOLD  = "\033[1m"


def _color(text: str, col: str) -> str:
    return f"{col}{text}{_RST}"


def print_results(results: list[DepResult], install_info: Optional[dict] = None) -> None:
    langs = {}
    for r in results:
        langs.setdefault(r.lang, []).append(r)

    lang_labels = {"py": "Python", "node": "Node.js", "js": "JS/TS", "go": "Go", "rust": "Rust"}

    for lang, deps in langs.items():
        print(f"\n  {_BOLD}{lang_labels.get(lang, lang)}{_RST}")
        for r in deps:
            if r.available:
                ver = f" ({r.version})" if r.version else ""
                print(f"    {_color('✓', _GRN)} {r.name}{ver}")
            else:
                tag = "opcl" if r.optional else "req "
                extra = ""
                if install_info and r.name in install_info:
                    extra = _color(" → instalado ✓", _GRN) if install_info[r.name] else _color(" → FALLÓ", _RED)
                elif r.install_cmd:
                    extra = _color(f" → sugerencia: {' '.join(r.install_cmd)}", _YEL)
                print(f"    {_color('✗', _RED)} {r.name}  [{tag}]{extra}")


def main(argv: list[str]) -> int:
    check_only = "--check" in argv
    do_install  = "--install" in argv
    as_json     = "--json" in argv

    results = check_all()

    if as_json:
        missing  = [asdict(r) for r in results if not r.available]
        available= [asdict(r) for r in results if r.available]
        print(json.dumps({"available": available, "missing": missing}, indent=2))
        return 0

    ok   = sum(1 for r in results if r.available)
    miss = len(results) - ok

    print(f"\n{_BOLD}BAGO install-deps — Dependencias opcionales{_RST}\n")

    install_info: Optional[dict] = None
    if do_install and miss > 0:
        install_info = install_missing(results)
        # re-check after install
        results = check_all()
        ok   = sum(1 for r in results if r.available)
        miss = len(results) - ok

    print_results(results, install_info)

    req_missing = [r for r in results if not r.available and not r.optional]
    print(f"\n  Disponibles: {ok}/{len(results)}")
    if miss:
        print(f"  Ausentes:    {miss} ({'críticos: ' + str(len(req_missing)) if req_missing else 'todos opcionales'})")
        if not do_install and not check_only:
            print(f"  {_YEL}Usa --install para instalar los que tengan sugerencia de instalación.{_RST}")
    else:
        print(f"  {_GRN}Todas las dependencias están disponibles.{_RST}")

    return 1 if req_missing else 0


# ─── Self-tests ────────────────────────────────────────────────────────────

def _self_test() -> None:
    import tempfile, os

    print("Tests de install_deps.py...")

    fails: list[str] = []

    def ok(name: str) -> None:
        print(f"  OK: {name}")

    def fail(name: str, msg: str) -> None:
        fails.append(name)
        print(f"  FAIL: {name}: {msg}")

    # T1 — check_all devuelve lista con todos los deps
    results = check_all()
    if len(results) == len(DEPS):
        ok("install_deps:check_all_returns_all")
    else:
        fail("install_deps:check_all_returns_all", f"got {len(results)}, expected {len(DEPS)}")

    # T2 — DepResult tiene campos requeridos
    r = results[0]
    if hasattr(r, "name") and hasattr(r, "available") and hasattr(r, "lang"):
        ok("install_deps:result_fields")
    else:
        fail("install_deps:result_fields", "campos faltantes en DepResult")

    # T3 — node detectado si está en PATH
    import shutil as _sh
    node_present = bool(_sh.which("node"))
    node_result = next((r for r in results if r.name == "node"), None)
    if node_result and node_result.available == node_present:
        ok("install_deps:node_detection")
    else:
        fail("install_deps:node_detection", f"node_present={node_present} but result.available={node_result.available if node_result else 'N/A'}")

    # T4 — acorn detección via node_modules
    acorn_result = next((r for r in results if r.name == "acorn"), None)
    if acorn_result is not None:
        ok("install_deps:acorn_check_exists")
    else:
        fail("install_deps:acorn_check_exists", "acorn no en lista de resultados")

    # T5 — json output funciona
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        main(["--json"])
    data = json.loads(buf.getvalue())
    if "available" in data and "missing" in data:
        ok("install_deps:json_output")
    else:
        fail("install_deps:json_output", "JSON sin campos expected")

    n_ok = len(DEPS) - len(fails)  # use len(DEPS) as denominator count proxy
    total = 5
    passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails:
        sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
