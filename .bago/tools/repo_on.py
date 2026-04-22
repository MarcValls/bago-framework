#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repo_on.py — Activa un repo externo como objetivo operativo de BAGO
y muestra qué comandos/workflows son viables sobre él.

Uso:
  python3 .bago/tools/repo_on.py /ruta/al/repo
  python3 .bago/tools/repo_on.py --json /ruta/al/repo
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from bago_debug import _detect_package_manager, _find_conflict_markers, _git_status, _load_json
from repo_context_guard import ROOT as HOST_ROOT, STATE_PATH, repo_fingerprint
from target_selector import choose_path, discover_project_candidates, has_supported_manifest


DEFAULT_NOTE = (
    "Este archivo es SOLO un puntero al repo externo intervenido. "
    "No contiene progreso funcional del pack BAGO ni estado canónico. "
    "El estado del pack vive en global_state.json. "
    "El snapshot legible vive en ESTADO_BAGO_ACTUAL.md. "
    "working_mode=external indica que BAGO opera como herramienta sobre un proyecto distinto al directorio donde reside."
)


def _parse() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=False)
    # nargs="*" para tolerar paths con espacios sin comillas
    parser.add_argument("path", nargs="*")
    parser.add_argument("--json", action="store_true", dest="as_json")
    ns = parser.parse_args()
    # Unir fragmentos en un solo string (ej: TPV_Contabilidad 2 → "TPV_Contabilidad 2")
    ns.path = " ".join(ns.path) if ns.path else None
    return ns


def _existing_context() -> dict:
    return _load_json(STATE_PATH) or {}


def _resolve_target(path_arg: str | None) -> Path:
    if path_arg:
        return Path(path_arg).resolve()

    ctx = _existing_context()
    if ctx.get("working_mode") == "external" and ctx.get("repo_root"):
        candidate = Path(ctx["repo_root"]).resolve()
        if candidate.exists():
            return candidate

    cwd = Path.cwd().resolve()
    if cwd != HOST_ROOT.resolve():
        return cwd

    if has_supported_manifest(HOST_ROOT):
        return HOST_ROOT.resolve()

    candidates = discover_project_candidates(HOST_ROOT, cwd=cwd, state_dir=STATE_PATH.parent)
    selected = choose_path(
        candidates[:8],
        title="BAGO · Selecciona el proyecto sobre el que quieres operar",
        custom_label="Ruta exacta…",
        custom_prompt="  Ruta exacta del repo: ",
    )
    if selected:
        return Path(selected).expanduser().resolve()

    raise SystemExit("No hay repo externo seleccionado. Usa: bago repo-on /ruta/al/repo")


def _detect_kind(repo_root: Path) -> tuple[str, list[str], dict[str, object]]:
    package_json = repo_root / "package.json"
    pyproject = repo_root / "pyproject.toml"
    cargo = repo_root / "Cargo.toml"
    gomod = repo_root / "go.mod"

    if package_json.exists():
        data = _load_json(package_json) or {}
        scripts = data.get("scripts", {})
        lockfiles = [name for name in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock") if (repo_root / name).exists()]
        return "node", ["package.json"], {
            "scripts": sorted(scripts.keys()),
            "package_manager": _detect_package_manager(repo_root)[0],
            "node_modules": (repo_root / "node_modules").exists(),
            "lockfiles": lockfiles,
        }

    if pyproject.exists():
        return "python", ["pyproject.toml"], {
            "has_tests_dir": (repo_root / "tests").exists(),
            "has_pytest_ini": (repo_root / "pytest.ini").exists(),
        }

    if cargo.exists():
        return "rust", ["Cargo.toml"], {}

    if gomod.exists():
        return "go", ["go.mod"], {}

    return "unknown", [], {}


def _command_catalog(repo_root: Path, kind: str, meta: dict[str, object]) -> list[dict[str, str]]:
    target = str(repo_root)
    commands = [
        {"cmd": f"bago repo-debug {target}", "status": "ready", "reason": "inspección base del repo objetivo"},
    ]

    def add(op: str, status: str, reason: str) -> None:
        commands.append({"cmd": f"bago repo-{op} {target}", "status": status, "reason": reason})

    if kind == "node":
        scripts = set(meta.get("scripts", []))
        node_modules = bool(meta.get("node_modules"))
        env_reason = "listo" if node_modules else "requiere node_modules"
        for op in ("lint", "test", "build"):
            if op in scripts:
                add(op, "ready" if node_modules else "blocked", f"script '{op}' detectado; {env_reason}")

    elif kind == "python":
        add("lint", "ready", "repo Python con pyproject")
        if meta.get("has_tests_dir") or meta.get("has_pytest_ini"):
            add("test", "ready", "tests Python detectados")
        add("build", "ready", "build Python potencial vía pyproject")

    elif kind in ("rust", "go"):
        add("lint", "ready", f"runner {kind} soportado")
        add("test", "ready", f"runner {kind} soportado")
        add("build", "ready", f"runner {kind} soportado")

    return commands


def _workflow_analysis(repo_root: Path, kind: str, meta: dict[str, object]) -> tuple[list[dict[str, str]], list[str], list[str]]:
    dirty = len(_git_status(repo_root))
    conflicts = _find_conflict_markers(repo_root)
    workflows: list[dict[str, str]] = []
    chains: list[str] = []
    command_chains: list[str] = []

    if kind == "unknown":
        workflows.append({"id": "W1_COLD_START", "reason": "repo sin manifiesto soportado; hace falta bootstrap repo-first"})
        workflows.append({"id": "W8_EXPLORACION", "reason": "superficie aún no clasificada; conviene exploración"})
        chains.append("W1_COLD_START -> W8_EXPLORACION")
        command_chains.append(f"bago repo-debug {repo_root}")
        return workflows, chains, command_chains

    if conflicts:
        workflows.append({"id": "W4_DEBUG_MULTICAUSA", "reason": f"{len(conflicts)} archivo(s) con conflict markers"})
        chains.append("W4_DEBUG_MULTICAUSA -> W2_IMPLEMENTACION_CONTROLADA -> W9_COSECHA")

    if kind == "node" and not meta.get("node_modules"):
        workflows.append({"id": "W1_COLD_START", "reason": "repo Node sin dependencias instaladas"})
        chains.append("W1_COLD_START -> W7_FOCO_SESION -> W2_IMPLEMENTACION_CONTROLADA -> W9_COSECHA")

    available_ops = []
    if kind == "node":
        available_ops = [op for op in ("lint", "test", "build") if op in set(meta.get("scripts", []))]
    elif kind == "python":
        available_ops = ["lint", "build"]
        if meta.get("has_tests_dir") or meta.get("has_pytest_ini"):
            available_ops.insert(1, "test")
    elif kind in ("rust", "go"):
        available_ops = ["lint", "test", "build"]

    if available_ops:
        workflows.append({"id": "W7_FOCO_SESION", "reason": "hay comandos operativos concretos sobre el repo"})
    if len(available_ops) >= 2:
        workflows.append({"id": "W2_IMPLEMENTACION_CONTROLADA", "reason": "el repo soporta gates o checks reutilizables"})
        chains.append("W7_FOCO_SESION -> W2_IMPLEMENTACION_CONTROLADA -> W9_COSECHA")
    else:
        workflows.append({"id": "W8_EXPLORACION", "reason": "conviene explorar antes de forzar implementación"})
        chains.append("W8_EXPLORACION -> W7_FOCO_SESION")

    if dirty > 0:
        workflows.append({"id": "W9_COSECHA", "reason": f"hay {dirty} cambio(s) en working tree que podrían requerir cierre o formalización"})
    else:
        workflows.append({"id": "W9_COSECHA", "reason": "workflow disponible como cierre cuando haya contexto acumulado"})

    base_cmd = [f"bago repo-debug {repo_root}"]
    if "lint" in available_ops:
        base_cmd.append(f"bago repo-lint {repo_root}")
    if "test" in available_ops:
        base_cmd.append(f"bago repo-test {repo_root}")
    if "build" in available_ops:
        base_cmd.append(f"bago repo-build {repo_root}")
    if len(base_cmd) > 1:
        command_chains.append(" -> ".join(base_cmd))

    unique_workflows = []
    seen = set()
    for item in workflows:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        unique_workflows.append(item)

    unique_chains = []
    seen_chains = set()
    for item in chains:
        if item in seen_chains:
            continue
        seen_chains.add(item)
        unique_chains.append(item)

    unique_command_chains = []
    seen_cmd = set()
    for item in command_chains:
        if item in seen_cmd:
            continue
        seen_cmd.add(item)
        unique_command_chains.append(item)

    return unique_workflows, unique_chains, unique_command_chains


def _save_context(repo_root: Path) -> dict[str, object]:
    previous = _existing_context()
    ctx = {
        "bago_host_root": str(HOST_ROOT.resolve()),
        "note": previous.get("note", DEFAULT_NOTE),
        "recorded_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "repo_fingerprint": repo_fingerprint(repo_root),
        "repo_root": str(repo_root),
        "role": previous.get("role", "external_repo_pointer"),
        "working_mode": "external",
    }
    STATE_PATH.write_text(json.dumps(ctx, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return ctx


def _human_report(result: dict[str, object]) -> None:
    print()
    print("═══ BAGO REPO-ON ═══════════════════════════════════════")
    print(f"Repo activo: {result['context']['repo_root']}")
    print(f"Tipo:       {result['repo']['kind']}")
    manifests = ", ".join(result["repo"]["manifests"]) if result["repo"]["manifests"] else "sin manifiesto soportado"
    print(f"Manifests:  {manifests}")
    print()
    print("Comandos repo:")
    for item in result["commands"]:
        print(f"  - [{item['status']}] {item['cmd']}")
        print(f"    {item['reason']}")
    print()
    print("Workflows posibles:")
    for item in result["workflows"]:
        print(f"  - {item['id']}")
        print(f"    {item['reason']}")
    print()
    if result["workflow_chains"]:
        print("Cadenas WF detectadas:")
        for item in result["workflow_chains"]:
            print(f"  - {item}")
        print()
    if result["command_chains"]:
        print("Cadenas de comandos detectadas:")
        for item in result["command_chains"]:
            print(f"  - {item}")
        print()
    print("Desactivar modo repo:")
    print("  - bago on")
    print()


def main() -> int:
    args = _parse()
    repo_root = _resolve_target(args.path)
    if not repo_root.exists():
        print(f"Ruta no encontrada: {repo_root}")
        return 1
    if repo_root.resolve() == HOST_ROOT.resolve():
        print("El repo objetivo coincide con el host BAGO. Usa `bago setup` para permanecer en self.")
        return 1

    kind, manifests, meta = _detect_kind(repo_root)
    commands = _command_catalog(repo_root, kind, meta)
    workflows, workflow_chains, command_chains = _workflow_analysis(repo_root, kind, meta)
    ctx = _save_context(repo_root)

    result = {
        "context": ctx,
        "repo": {
            "kind": kind,
            "manifests": manifests,
            "meta": meta,
        },
        "commands": commands,
        "workflows": workflows,
        "workflow_chains": workflow_chains,
        "command_chains": command_chains,
    }

    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _human_report(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
