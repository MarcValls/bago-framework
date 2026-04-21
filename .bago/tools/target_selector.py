#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
target_selector.py — selección segura de directorio objetivo.

Objetivo:
- priorizar el contexto operativo ya conocido,
- evitar asumir carpetas históricas/test por defecto,
- ofrecer selección interactiva con flechas cuando hay ambigüedad,
- permitir introducir una ruta exacta como último recurso.
"""

from __future__ import annotations

import json
import os
import sys
import termios
import tty
from pathlib import Path


EXCLUDED_NAMES = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".bago",
    "node_modules",
    "dist",
    "build",
    "coverage",
    "__pycache__",
    ".venv",
    "venv",
}

LOW_PRIORITY_MARKERS = {
    "tests",
    "test",
    "release",
    "releases",
    "audit",
    "audits",
    "archive",
    "archives",
    "backup",
    "backups",
    "cleanversion",
    "snapshot",
    "snapshots",
    "tmp",
    "temp",
}

SUPPORTED_MANIFESTS = ("package.json", "pyproject.toml", "Cargo.toml", "go.mod")


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def has_supported_manifest(path: Path) -> bool:
    return any((path / name).exists() for name in SUPPORTED_MANIFESTS)


def _path_score(path: Path, cwd: Path, current_external: Path | None) -> int:
    score = 0
    if path == cwd:
        score += 100
    if current_external and path == current_external:
        score += 80
    if has_supported_manifest(path):
        score += 40
    if (path / ".git").exists():
        score += 15
    if (path / "src").exists():
        score += 10

    lowered_parts = {part.lower() for part in path.parts}
    if lowered_parts & LOW_PRIORITY_MARKERS:
        score -= 80
    return score


def discover_project_candidates(
    search_root: Path,
    *,
    cwd: Path | None = None,
    state_dir: Path | None = None,
    max_depth: int = 4,
) -> list[dict[str, str]]:
    """Descubre candidatos de proyecto priorizando el contexto operativo."""
    search_root = search_root.resolve()
    cwd = (cwd or Path.cwd()).resolve()
    current_external: Path | None = None
    entries: dict[str, dict[str, str | int]] = {}

    def add(path: Path, reason: str) -> None:
        path = path.resolve()
        if not path.exists() or not path.is_dir():
            return
        key = str(path)
        if key in entries:
            return
        entries[key] = {
            "path": key,
            "label": path.name or key,
            "reason": reason,
            "_score": _path_score(path, cwd, current_external),
        }

    if state_dir:
        repo_ctx = _load_json(state_dir / "repo_context.json")
        if repo_ctx.get("working_mode") == "external" and repo_ctx.get("repo_root"):
            candidate = Path(repo_ctx["repo_root"]).resolve()
            if candidate.exists():
                current_external = candidate
                add(candidate, "contexto externo actual")

        context_map = _load_json(state_dir / "context_map.json")
        for node in context_map.get("nodes", []):
            mode = node.get("working_mode", "")
            raw = (node.get("repo_root") or node.get("path")) if mode == "external" else node.get("path")
            if not raw:
                continue
            add(Path(raw), "contexto reciente")

    if cwd != search_root:
        add(cwd, "cwd actual")

    if has_supported_manifest(search_root):
        add(search_root, "raíz actual con manifiesto")

    for root, dirs, files in os.walk(search_root):
        root_path = Path(root)
        depth = len(root_path.relative_to(search_root).parts)
        if depth > max_depth:
            dirs[:] = []
            continue

        dirs[:] = [d for d in dirs if d not in EXCLUDED_NAMES]
        if any(name in files for name in SUPPORTED_MANIFESTS):
            add(root_path, "manifiesto detectado")
            dirs[:] = []

    sorted_entries = sorted(
        entries.values(),
        key=lambda item: (-int(item["_score"]), str(item["path"])),
    )
    return [
        {
            "path": str(item["path"]),
            "label": str(item["label"]),
            "reason": str(item["reason"]),
        }
        for item in sorted_entries
    ]


def _render_menu(title: str, entries: list[dict[str, str]], selected: int, custom_label: str) -> None:
    sys.stdout.write("\x1b[2J\x1b[H")
    print(f"{title}\n")
    print("Usa ↑/↓ y Enter. `q` cancela.\n")
    for idx, item in enumerate(entries):
        marker = "›" if idx == selected else " "
        print(f"{marker} {item['label']}")
        print(f"  {item['path']}")
        if item.get("reason"):
            print(f"  {item['reason']}")
        print()

    marker = "›" if selected == len(entries) else " "
    print(f"{marker} {custom_label}")
    print("  Pedir ruta exacta")


def _read_key() -> str:
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch1 = sys.stdin.read(1)
        if ch1 == "\x1b":
            ch2 = sys.stdin.read(1)
            ch3 = sys.stdin.read(1)
            return ch1 + ch2 + ch3
        return ch1
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _pick_with_arrows(title: str, entries: list[dict[str, str]], custom_label: str) -> str | None:
    selected = 0
    while True:
        _render_menu(title, entries, selected, custom_label)
        key = _read_key()
        if key in ("\x03", "q"):
            return None
        if key in ("\x1b[A", "k"):
            selected = (selected - 1) % (len(entries) + 1)
            continue
        if key in ("\x1b[B", "j"):
            selected = (selected + 1) % (len(entries) + 1)
            continue
        if key in ("\r", "\n"):
            if selected == len(entries):
                return "__CUSTOM__"
            return entries[selected]["path"]


def _pick_with_numbers(title: str, entries: list[dict[str, str]], custom_label: str) -> str | None:
    print()
    print(title)
    print()
    for idx, item in enumerate(entries, 1):
        print(f"  [{idx}] {item['label']}")
        print(f"      {item['path']}")
        if item.get("reason"):
            print(f"      {item['reason']}")
    custom_n = len(entries) + 1
    print(f"  [{custom_n}] {custom_label}")
    print("  [0] Cancelar")
    print()

    try:
        raw = input("  Selección: ").strip()
    except (KeyboardInterrupt, EOFError):
        return None

    if raw == "0":
        return None
    if raw.isdigit():
        n = int(raw)
        if 1 <= n <= len(entries):
            return entries[n - 1]["path"]
        if n == custom_n:
            return "__CUSTOM__"
    if raw:
        candidate = Path(raw).expanduser()
        if candidate.exists():
            return str(candidate.resolve())
    print("  ⚠️  Opción no válida.")
    return None


def choose_path(
    entries: list[dict[str, str]],
    *,
    title: str,
    custom_label: str = "Ruta exacta…",
    custom_prompt: str = "Ruta exacta: ",
) -> str | None:
    if not entries:
        try:
            raw = input(custom_prompt).strip()
        except (KeyboardInterrupt, EOFError):
            return None
        return raw or None

    use_arrows = sys.stdin.isatty() and sys.stdout.isatty()
    selected = _pick_with_arrows(title, entries, custom_label) if use_arrows else _pick_with_numbers(title, entries, custom_label)

    if selected != "__CUSTOM__":
        if use_arrows:
            sys.stdout.write("\x1b[2J\x1b[H")
        return selected

    try:
        raw = input(custom_prompt).strip()
    except (KeyboardInterrupt, EOFError):
        return None
    return raw or None
