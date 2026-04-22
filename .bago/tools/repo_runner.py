#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repo_runner.py — Ejecuta operaciones explícitas sobre el proyecto intervenido.

Tipos de proyecto soportados:
  node (package.json), python (pyproject.toml), rust (Cargo.toml), go (go.mod),
  java (pom.xml / build.gradle), kotlin (build.gradle + *.kt),
  csharp (*.csproj / *.sln), ruby (Gemfile), php (composer.json),
  swift (Package.swift)

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


def _is_not_found(text: str) -> bool:
    """Return True when subprocess output indicates the executable was not found."""
    low = text.lower()
    return "not found" in low or "no such file" in low or "Could not find command" in text


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


def _java_operation(repo_root: Path, operation: str) -> tuple[bool, str, list[str]]:
    """Maven or Gradle (plain Java)."""
    use_gradle = (repo_root / "build.gradle").exists() or (repo_root / "build.gradle.kts").exists()
    use_maven  = (repo_root / "pom.xml").exists()

    if use_gradle:
        wrapper    = repo_root / "gradlew"
        gradle_cmd = [str(wrapper) if wrapper.exists() else "gradle"]
        if operation == "lint":
            cmd, label = gradle_cmd + ["checkstyleMain", "--quiet"], "gradle checkstyleMain"
        elif operation == "test":
            cmd, label = gradle_cmd + ["test", "--quiet"], "gradle test"
        else:
            cmd, label = gradle_cmd + ["build", "--quiet"], "gradle build"
    elif use_maven:
        if operation == "lint":
            cmd, label = ["mvn", "checkstyle:check", "-q"], "mvn checkstyle:check"
        elif operation == "test":
            cmd, label = ["mvn", "test", "-q"], "mvn test"
        else:
            cmd, label = ["mvn", "package", "-q"], "mvn package"
    else:
        return False, "", ["No se encontró pom.xml ni build.gradle."]

    rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
    text = (err or out or "").strip()
    if rc == 0:
        return True, label, [f"{operation} OK"]
    tail = text.splitlines()[-1] if text else f"{operation} falló"
    return False, label, [tail]


def _kotlin_operation(repo_root: Path, operation: str) -> tuple[bool, str, list[str]]:
    """Gradle-based Kotlin projects."""
    wrapper    = repo_root / "gradlew"
    gradle_cmd = [str(wrapper) if wrapper.exists() else "gradle"]
    if operation == "lint":
        cmd, label = gradle_cmd + ["ktlintCheck", "--quiet"], "gradle ktlintCheck"
    elif operation == "test":
        cmd, label = gradle_cmd + ["test", "--quiet"], "gradle test"
    else:
        cmd, label = gradle_cmd + ["build", "--quiet"], "gradle build"

    rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
    text = (err or out or "").strip()
    if rc == 0:
        return True, label, [f"{operation} OK"]
    tail = text.splitlines()[-1] if text else f"{operation} falló"
    return False, label, [tail]


def _dotnet_operation(repo_root: Path, operation: str) -> tuple[bool, str, list[str]]:
    """dotnet CLI for C# projects."""
    if operation == "lint":
        cmd   = ["dotnet", "format", "--verify-no-changes"]
        label = "dotnet format --verify-no-changes"
    elif operation == "test":
        cmd   = ["dotnet", "test", "--nologo", "-q"]
        label = "dotnet test --nologo -q"
    else:
        cmd   = ["dotnet", "build", "--nologo", "-q"]
        label = "dotnet build --nologo -q"

    rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
    text = (err or out or "").strip()
    if rc == 0:
        return True, label, [f"{operation} OK"]
    tail = text.splitlines()[-1] if text else f"{operation} falló"
    return False, label, [tail]


def _ruby_operation(repo_root: Path, operation: str) -> tuple[bool, str, list[str]]:
    """Bundler-based Ruby projects."""
    use_bundler = (repo_root / "Gemfile.lock").exists()
    prefix      = ["bundle", "exec"] if use_bundler else []

    if operation == "lint":
        cmd   = prefix + ["rubocop", "-q"]
        label = " ".join(cmd)
        rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
        text = (err or out or "").strip()
        if rc == 0:
            return True, label, ["lint OK"]
        tail = text.splitlines()[-1] if text else "lint falló"
        return False, label, [tail]

    if operation == "test":
        for test_cmd, test_label in [
            (prefix + ["rspec", "--format", "progress"], " ".join(prefix + ["rspec"])),
            (prefix + ["rake", "test"], " ".join(prefix + ["rake", "test"])),
        ]:
            rc, out, err = _run(test_cmd, cwd=repo_root, timeout=300)
            text = (err or out or "").strip()
            if rc == 0:
                return True, test_label, ["test OK"]
            if _is_not_found(text):
                continue
            tail = text.splitlines()[-1] if text else "test falló"
            return False, test_label, [tail]
        return False, "", ["No se encontró runner de test Ruby (rspec/rake)."]

    # build → bundle install
    cmd, label = ["bundle", "install"], "bundle install"
    rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
    text = (err or out or "").strip()
    if rc == 0:
        return True, label, ["build OK"]
    tail = text.splitlines()[-1] if text else "build falló"
    return False, label, [tail]


def _php_operation(repo_root: Path, operation: str) -> tuple[bool, str, list[str]]:
    """Composer-based PHP projects."""
    if operation == "lint":
        candidates = [
            (["./vendor/bin/phpcs", "."], "./vendor/bin/phpcs ."),
            (["phpcs", "."], "phpcs ."),
        ]
        for cmd, label in candidates:
            rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
            text = (err or out or "").strip()
            if rc == 0:
                return True, label, ["lint OK"]
            if _is_not_found(text):
                continue
            tail = text.splitlines()[-1] if text else "lint falló"
            return False, label, [tail]
        return False, "", ["No hay runner de lint PHP disponible (phpcs)."]

    if operation == "test":
        candidates = [
            (["./vendor/bin/phpunit"], "./vendor/bin/phpunit"),
            (["composer", "run-script", "test"], "composer run-script test"),
        ]
        for cmd, label in candidates:
            rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
            text = (err or out or "").strip()
            if rc == 0:
                return True, label, ["test OK"]
            if _is_not_found(text):
                continue
            tail = text.splitlines()[-1] if text else "test falló"
            return False, label, [tail]
        return False, "", ["No hay runner de test PHP disponible (phpunit)."]

    # build → composer install
    cmd, label = ["composer", "install", "--no-interaction"], "composer install --no-interaction"
    rc, out, err = _run(cmd, cwd=repo_root, timeout=300)
    text = (err or out or "").strip()
    if rc == 0:
        return True, label, ["build OK"]
    tail = text.splitlines()[-1] if text else "build falló"
    return False, label, [tail]


def _swift_operation(repo_root: Path, operation: str) -> tuple[bool, str, list[str]]:
    """Swift Package Manager projects."""
    if operation == "lint":
        cmd, label = ["swiftlint", "lint", "--quiet"], "swiftlint lint --quiet"
    elif operation == "test":
        cmd, label = ["swift", "test"], "swift test"
    else:
        cmd, label = ["swift", "build"], "swift build"

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
    elif (
        (repo_root / "pom.xml").exists()
        or (repo_root / "build.gradle").exists()
        or (repo_root / "build.gradle.kts").exists()
    ):
        # Kotlin projects use Gradle too — prefer kotlin runner when .kt sources exist.
        # Use next() to stop scanning once the first .kt file is found (avoids full tree walk).
        if next(repo_root.rglob("*.kt"), None) is not None:
            ok, runner, details = _kotlin_operation(repo_root, operation)
            kind = "kotlin"
        else:
            ok, runner, details = _java_operation(repo_root, operation)
            kind = "java"
    elif any(repo_root.glob("*.csproj")) or any(repo_root.glob("*.sln")):
        ok, runner, details = _dotnet_operation(repo_root, operation)
        kind = "csharp"
    elif (repo_root / "Gemfile").exists():
        ok, runner, details = _ruby_operation(repo_root, operation)
        kind = "ruby"
    elif (repo_root / "composer.json").exists():
        ok, runner, details = _php_operation(repo_root, operation)
        kind = "php"
    elif (repo_root / "Package.swift").exists():
        ok, runner, details = _swift_operation(repo_root, operation)
        kind = "swift"
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
