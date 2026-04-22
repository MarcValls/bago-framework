#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
context_collector.py — modo RECOLECTA DE CONTEXTO

Analiza uno o varios directorios y construye un resumen de contexto operativo:
- existencia y tipo de ruta
- señales de Git (branch/dirty)
- señales BAGO (.bago/pack.json)
- volumen básico (dirs/files/extensiones top)

Uso:
  python3 .bago/tools/context_collector.py
  python3 .bago/tools/context_collector.py /ruta/a /ruta/b
  python3 .bago/tools/context_collector.py --json /ruta
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache",
    ".next", ".turbo", "dist", "build", "coverage",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def ask_directories() -> list[str]:
    print()
    print("BAGO · MODO RECOLECTA DE CONTEXTO")
    print("¿Qué directorio/s quieres recolectar contexto?")
    print("Puedes escribir varias rutas separadas por coma.")
    print("Enter vacío = directorio actual.")
    raw = input("directorios → ").strip()
    if not raw:
        return [str(Path.cwd())]
    parts = [p.strip().strip('"').strip("'") for p in re.split(r"[,\n;]+", raw)]
    return [p for p in parts if p]


def _git_info(path: Path) -> dict:
    info = {"is_git": False, "root": None, "branch": None, "dirty_files": 0}
    try:
        inside = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
            capture_output=True, text=True, timeout=4,
        )
        if inside.returncode != 0 or inside.stdout.strip() != "true":
            return info
        info["is_git"] = True

        root = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=4,
        )
        if root.returncode == 0:
            info["root"] = root.stdout.strip()

        branch = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=4,
        )
        if branch.returncode == 0:
            info["branch"] = branch.stdout.strip()

        dirty = subprocess.run(
            ["git", "-C", str(path), "status", "--porcelain"],
            capture_output=True, text=True, timeout=6,
        )
        if dirty.returncode == 0:
            info["dirty_files"] = len([ln for ln in dirty.stdout.splitlines() if ln.strip()])
    except Exception:
        return info
    return info


def _find_bago_nodes(root: Path, max_depth: int = 4, max_nodes: int = 20) -> list[str]:
    found: list[str] = []
    queue: list[tuple[Path, int]] = [(root, 0)]
    visited: set[Path] = set()

    while queue and len(found) < max_nodes:
        current, depth = queue.pop(0)
        try:
            real = current.resolve()
        except OSError:
            continue
        if real in visited:
            continue
        visited.add(real)

        if (current / ".bago" / "pack.json").exists():
            found.append(str(current))
        if current.name == ".bago" and (current / "pack.json").exists():
            found.append(str(current.parent))

        if depth >= max_depth:
            continue
        try:
            children = list(current.iterdir())
        except Exception:
            continue

        for c in children:
            if not c.is_dir():
                continue
            if c.name in SKIP_DIRS:
                continue
            if c.name.startswith(".") and c.name != ".bago":
                continue
            queue.append((c, depth + 1))

    # dedupe manteniendo orden
    seen = set()
    unique = []
    for p in found:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


def _tree_stats(root: Path, max_depth: int = 3, max_files: int = 12000) -> dict:
    files = 0
    dirs = 0
    ext = Counter()
    queue: list[tuple[Path, int]] = [(root, 0)]
    visited: set[Path] = set()

    while queue and files < max_files:
        current, depth = queue.pop(0)
        try:
            real = current.resolve()
        except OSError:
            continue
        if real in visited:
            continue
        visited.add(real)
        dirs += 1

        try:
            entries = list(current.iterdir())
        except Exception:
            continue

        for e in entries:
            if e.is_file():
                files += 1
                suffix = e.suffix.lower() or "<sin_ext>"
                ext[suffix] += 1
                if files >= max_files:
                    break
            elif e.is_dir() and depth < max_depth:
                if e.name in SKIP_DIRS:
                    continue
                if e.name.startswith(".") and e.name != ".bago":
                    continue
                queue.append((e, depth + 1))

    return {
        "dirs_scanned": dirs,
        "files_scanned": files,
        "top_ext": ext.most_common(6),
        "truncated": files >= max_files,
    }


def analyze_directory(raw_path: str) -> dict:
    path = Path(raw_path).expanduser()
    result = {
        "input": raw_path,
        "resolved": str(path.resolve()) if path.exists() else str(path),
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "errors": [],
    }
    if not path.exists():
        result["errors"].append("path_not_found")
        return result
    if not path.is_dir():
        result["errors"].append("not_a_directory")
        return result

    root = path.resolve()
    result["git"] = _git_info(root)
    bago_nodes = _find_bago_nodes(root)
    result["bago"] = {
        "nodes_count": len(bago_nodes),
        "nodes": bago_nodes[:8],
    }
    result["stats"] = _tree_stats(root)

    recs = []
    if result["bago"]["nodes_count"] > 0:
        recs.append("detectado_pack_bago")
    if result["git"].get("is_git"):
        recs.append("repo_git_detectado")
    if result["git"].get("dirty_files", 0) > 0:
        recs.append("cambios_sin_commit")
    if not recs:
        recs.append("contexto_basico_sin_senales_fuertes")
    result["recommendations"] = recs
    return result


def print_human_report(payload: dict) -> None:
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║   BAGO · RECOLECTA DE CONTEXTO                      ║")
    print("╠══════════════════════════════════════════════════════╣")
    print(f"║  Directorios analizados: {payload['summary']['total']:>3}                      ║")
    print(f"║  OK: {payload['summary']['ok']:>3}  ·  Error: {payload['summary']['error']:>3}                     ║")
    print("╚══════════════════════════════════════════════════════╝")

    for item in payload["results"]:
        print()
        print(f"• {item['resolved']}")
        if item["errors"]:
            print(f"  estado: ERROR ({', '.join(item['errors'])})")
            continue
        git = item["git"]
        bago = item["bago"]
        stats = item["stats"]
        git_txt = "sí" if git["is_git"] else "no"
        print(f"  git: {git_txt}", end="")
        if git["is_git"]:
            print(f"  | branch: {git.get('branch') or '?'}  | dirty: {git.get('dirty_files', 0)}")
        else:
            print()
        print(f"  bago: {bago['nodes_count']} nodo(s) detectados")
        if bago["nodes"]:
            for n in bago["nodes"][:3]:
                print(f"    - {n}")
        exts = ", ".join(f"{k}:{v}" for k, v in stats["top_ext"]) or "n/a"
        trunc = " (truncado)" if stats["truncated"] else ""
        print(f"  volumen: dirs={stats['dirs_scanned']} files={stats['files_scanned']}{trunc}")
        print(f"  extensiones top: {exts}")
        print(f"  señales: {', '.join(item['recommendations'])}")
    print()


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Recolecta contexto de directorios.")
    parser.add_argument("paths", nargs="*", help="Rutas a analizar")
    parser.add_argument("--json", dest="json_out", action="store_true", help="Salida JSON")
    args = parser.parse_args(argv[1:])

    paths = args.paths or ask_directories()
    results = [analyze_directory(p) for p in paths]
    ok = sum(1 for r in results if not r["errors"])
    payload = {
        "generated_at": now_iso(),
        "summary": {"total": len(results), "ok": ok, "error": len(results) - ok},
        "results": results,
    }

    if args.json_out:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_human_report(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
