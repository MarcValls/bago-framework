#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repo_runner.py — Ejecuta operaciones explícitas sobre el proyecto intervenido.

Uso:
  python3 .bago/tools/repo_runner.py lint [PATH]
  python3 .bago/tools/repo_runner.py test [PATH]
  python3 .bago/tools/repo_runner.py build [PATH]
  python3 .bago/tools/repo_runner.py lint --json
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

from bago_debug import _default_repo_target, _detect_package_manager, _load_json, _run


def _parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("operation", choices=["lint", "test", "build"])
    parser.add_argument("path", nargs="*")
    parser.add_argument("--json", action="store_true", dest="as_json")
    ns = parser.parse_args()
    ns.path = " ".join(ns.path) if ns.path else None
    return ns


def _node_operation(repo_root: Path, operation: str) -> tuple[bool, str, list[str]]:
    data = _load_json(repo_root / "package.json") or {}
    scripts = data.get("scripts", {})
    if operation not in scripts:
        return False, "", [f"package.json sin script '{operation}'."]

    if not (repo_root / "node_modules").exists():
        return False, "", ["Proyecto Node sin node_modules; no se puede ejecutar el script local."]

    pm = _detect_package_manager(repo_root)
    cmd = pm + ["run", operation]
    rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
    detail = (out or err or "").strip().splitlines()
    tail = detail[-1] if detail else ""
    return rc == 0, " ".join(cmd), ([f"{operation} OK"] if rc == 0 else [tail or f"{operation} falló"])


def _python_operation(repo_root: Path, operation: str) -> tuple[bool, str, list[str]]:
    if operation == "lint":
        candidates = [
            ([sys.executable, "-m", "ruff", "check", "."], "python -m ruff check ."),
            (["ruff", "check", "."], "ruff check ."),
            ([sys.executable, "-m", "flake8", "."], "python -m flake8 ."),
            (["flake8", "."], "flake8 ."),
        ]
        for cmd, label in candidates:
            if shutil.which(cmd[0]) or (cmd[0] == sys.executable):
                rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
                if rc == 0:
                    return True, label, ["lint OK"]
                text = (err or out or "").strip()
                if "No module named" in text or "not found" in text:
                    continue
                tail = text.splitlines()[-1] if text else "lint falló"
                return False, label, [tail]
        return False, "", ["No hay runner de lint Python disponible (ruff/flake8)."]

    if operation == "test":
        cmd = [sys.executable, "-m", "pytest", "-q"]
        rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
        text = (err or out or "").strip()
        if rc == 0:
            return True, "python -m pytest -q", ["test OK"]
        if "No module named pytest" in text:
            return False, "", ["pytest no está disponible en el entorno."]
        tail = text.splitlines()[-1] if text else "test falló"
        return False, "python -m pytest -q", [tail]

    if operation == "build":
        cmd = [sys.executable, "-m", "build"]
        rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
        text = (err or out or "").strip()
        if rc == 0:
            return True, "python -m build", ["build OK"]
        if "No module named build" in text:
            return False, "", ["El módulo 'build' no está disponible en el entorno."]
        tail = text.splitlines()[-1] if text else "build falló"
        return False, "python -m build", [tail]

    return False, "", [f"Operación Python no soportada: {operation}"]


def _cargo_operation(repo_root: Path, operation: str) -> tuple[bool, str, list[str]]:
    if operation == "lint":
        candidates = [
            (["cargo", "clippy", "--quiet"], "cargo clippy --quiet"),
            (["cargo", "check", "--quiet"], "cargo check --quiet"),
        ]
    elif operation == "test":
        candidates = [(["cargo", "test", "--quiet"], "cargo test --quiet")]
    else:
        candidates = [(["cargo", "build", "--quiet"], "cargo build --quiet")]

    for cmd, label in candidates:
        rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
        text = (err or out or "").strip()
        if rc == 0:
            return True, label, [f"{operation} OK"]
        if "no such command" in text.lower():
            continue
        tail = text.splitlines()[-1] if text else f"{operation} falló"
        return False, label, [tail]
    return False, "", [f"No hay runner Cargo disponible para '{operation}'."]


def _go_operation(repo_root: Path, operation: str) -> tuple[bool, str, list[str]]:
    if operation == "lint":
        cmd, label = ["go", "vet", "./..."], "go vet ./..."
    elif operation == "test":
        cmd, label = ["go", "test", "./..."], "go test ./..."
    else:
        cmd, label = ["go", "build", "./..."], "go build ./..."
    rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
    text = (err or out or "").strip()
    if rc == 0:
        return True, label, [f"{operation} OK"]
    tail = text.splitlines()[-1] if text else f"{operation} falló"
    return False, label, [tail]


def _resolve_target(path_arg: str | None) -> Path:
    if path_arg:
        return Path(path_arg).resolve()
    return _default_repo_target()


def _run_operation(operation: str, repo_root: Path) -> dict[str, object]:
    if not repo_root.exists():
        return {
            "ok": False,
            "operation": operation,
            "target": str(repo_root),
            "runner": "",
            "kind": "unknown",
            "details": [f"Ruta no encontrada: {repo_root}"],
        }

    if (repo_root / "package.json").exists():
        ok, runner, details = _node_operation(repo_root, operation)
        kind = "node"
    elif (repo_root / "pyproject.toml").exists():
        ok, runner, details = _python_operation(repo_root, operation)
        kind = "python"
    elif (repo_root / "Cargo.toml").exists():
        ok, runner, details = _cargo_operation(repo_root, operation)
        kind = "rust"
    elif (repo_root / "go.mod").exists():
        ok, runner, details = _go_operation(repo_root, operation)
        kind = "go"
    else:
        ok, runner, details, kind = False, "", ["No se detectó manifiesto soportado."], "unknown"

    return {
        "ok": ok,
        "operation": operation,
        "target": str(repo_root),
        "runner": runner,
        "kind": kind,
        "details": details,
    }


def _print_human(result: dict[str, object]) -> None:
    print()
    print("═══ BAGO REPO RUNNER ═══════════════════════════════════")
    print(f"Operación: {result.get('operation')}")
    print(f"Objetivo:  {result.get('target')}")
    print(f"Tipo:      {result.get('kind')}")
    if result.get("runner"):
        print(f"Runner:    {result.get('runner')}")
    print()
    for detail in result.get("details", []):
        print(f"- {detail}")
    print()
    print(f"Resultado: {'OK' if result.get('ok') else 'FAIL'}")
    print()


def main() -> int:
    args = _parse()
    repo_root = _resolve_target(args.path)
    result = _run_operation(args.operation, repo_root)
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_human(result)
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
