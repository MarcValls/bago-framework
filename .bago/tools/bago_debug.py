#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bago_debug.py — Auditoría y reparación de bugs del pack BAGO o del repo intervenido.

Modos:
  - pack (por defecto): estado y automatismos de .bago
  - repo (--repo [PATH]): checks del proyecto intervenido

Uso:
  python3 .bago/tools/bago_debug.py
  python3 .bago/tools/bago_debug.py --check
  python3 .bago/tools/bago_debug.py --json
  python3 .bago/tools/bago_debug.py --repo
  python3 .bago/tools/bago_debug.py --repo ../otro-proyecto --check --json
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from target_selector import has_supported_manifest


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
TOOLS = ROOT / "tools"
STATE = ROOT / "state"
TASK_FILE = STATE / "pending_w2_task.json"


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 120) -> tuple[int, str, str]:
    env = dict(os.environ)
    env["BAGO_SKIP_DEBUG"] = "1"
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd or PROJECT_ROOT),
        timeout=timeout,
        env=env,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def _load_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _repo_context() -> dict:
    return _load_json(STATE / "repo_context.json") or {}


def _default_repo_target() -> Path:
    ctx = _repo_context()
    repo_root = ctx.get("repo_root")
    if ctx.get("working_mode") == "external" and repo_root:
        candidate = Path(repo_root).resolve()
        if candidate.exists():
            return candidate
    cwd = Path.cwd().resolve()
    if cwd != PROJECT_ROOT:
        return cwd
    if has_supported_manifest(PROJECT_ROOT):
        return PROJECT_ROOT
    raise SystemExit("No hay repo objetivo claro. Usa `bago repo-on` para seleccionar uno o pasa una ruta explícita.")


def _inventory_diff() -> dict[str, tuple[int, int]]:
    gs = _load_json(STATE / "global_state.json") or {}
    inventory = gs.get("inventory", {})
    folders = {
        "sessions": STATE / "sessions",
        "changes": STATE / "changes",
        "evidences": STATE / "evidences",
    }
    diffs: dict[str, tuple[int, int]] = {}
    for key, folder in folders.items():
        expected = int(inventory.get(key, 0))
        real = len([p for p in folder.glob("*.json") if p.name.lower() != "readme.md"])
        if expected != real:
            diffs[key] = (expected, real)
    return diffs


def _stale_done_task() -> dict | None:
    if not TASK_FILE.exists():
        return None
    data = _load_json(TASK_FILE)
    if data and data.get("status") == "done":
        return data
    return None


def _detector_alignment_issue() -> str | None:
    rc_ctx, out_ctx, _ = _run([sys.executable, str(TOOLS / "context_detector.py"), "--json"])
    rc_auto, out_auto, _ = _run([sys.executable, str(TOOLS / "auto_mode.py"), "--json"])
    if rc_ctx != 0 or rc_auto != 0:
        return "No se pudo verificar la alineación entre context_detector y auto_mode."
    try:
        ctx = json.loads(out_ctx)
        auto = json.loads(out_auto)
    except json.JSONDecodeError:
        return "Salida JSON inválida al comparar context_detector y auto_mode."

    ctx_verdict = ctx.get("verdict")
    ctx_score = ctx.get("score")
    auto_verdict = auto.get("state", {}).get("detector")
    auto_high = auto.get("state", {}).get("high_signals")
    if ctx_verdict != auto_verdict or ctx_score != auto_high:
        return (
            "auto_mode y context_detector no están alineados: "
            f"detector={ctx_verdict}/{ctx_score} vs auto={auto_verdict}/{auto_high}"
        )
    return None


def _stale_warnings() -> list[str]:
    rc, out, _ = _run([sys.executable, str(TOOLS / "stale_detector.py")])
    if not out:
        return []
    warns = [line for line in out.splitlines() if "[WARN]" in line]
    return warns if rc == 0 or warns else []


def _validate_pack() -> tuple[int, str]:
    rc, out, err = _run([sys.executable, str(TOOLS / "validate_pack.py")])
    merged = "\n".join(part for part in (out, err) if part).strip()
    return rc, merged


def _validate_manifest_state() -> tuple[int, str]:
    rc_m, out_m, err_m = _run([sys.executable, str(TOOLS / "validate_manifest.py")])
    rc_s, out_s, err_s = _run([sys.executable, str(TOOLS / "validate_state.py")])
    merged = "\n".join(part for part in (out_m, err_m, out_s, err_s) if part).strip()
    return 0 if rc_m == 0 and rc_s == 0 else 1, merged


def _scan_pack() -> dict[str, object]:
    bugs: list[str] = []
    silent_bugs: list[str] = []
    fixable: list[str] = []

    rc_vs, validate_summary = _validate_manifest_state()
    if rc_vs != 0:
        bugs.append("validate_manifest o validate_state falla.")

    inventory_diffs = _inventory_diff()
    if inventory_diffs:
        joined = ", ".join(
            f"{key}: global={expected} disco={real}"
            for key, (expected, real) in inventory_diffs.items()
        )
        bugs.append(f"Inventario desalineado: {joined}")
        fixable.append("inventory")

    if _stale_done_task() is not None:
        silent_bugs.append("pending_w2_task.json persiste una tarea W2 ya cerrada (status=done).")
        fixable.append("done_task")

    alignment_issue = _detector_alignment_issue()
    if alignment_issue:
        bugs.append(alignment_issue)

    silent_bugs.extend(_stale_warnings())

    rc_pack, pack_summary = _validate_pack()
    if rc_pack != 0:
        bugs.append("validate_pack falla tras el escaneo inicial.")

    return {
        "mode": "pack",
        "applicable": True,
        "bugs": bugs,
        "silent_bugs": silent_bugs,
        "fixable": sorted(set(fixable)),
        "validate_summary": validate_summary,
        "pack_summary": pack_summary,
        "bug_count": len(bugs),
        "silent_bug_count": len(silent_bugs),
        "auto_fixable_count": len(set(fixable)),
    }


def _apply_pack_fixes(summary: dict[str, object]) -> tuple[list[str], list[str]]:
    repairs: list[str] = []
    remaining: list[str] = []
    fixable = set(summary.get("fixable", []))

    if "inventory" in fixable:
        rc, out, err = _run([sys.executable, str(TOOLS / "reconcile_state.py"), "--fix"])
        if rc == 0:
            repairs.append(out or "Inventario reconciliado.")
        else:
            remaining.append(err or out or "No se pudo reconciliar el inventario.")

    if "done_task" in fixable and TASK_FILE.exists():
        try:
            TASK_FILE.unlink()
            repairs.append("pending_w2_task.json eliminado tras detectar status=done.")
        except Exception as exc:
            remaining.append(f"No se pudo eliminar pending_w2_task.json: {exc}")

    rc_pack, pack_out = _validate_pack()
    if rc_pack == 0:
        repairs.extend(
            line for line in pack_out.splitlines()
            if line.strip() and ("regenerado" in line.lower() or line.strip() == "GO pack")
        )
    else:
        remaining.append("validate_pack sigue fallando después de aplicar reparaciones.")
        remaining.extend(line for line in pack_out.splitlines() if line.strip())

    return repairs, remaining


def _parse_repo_target(argv: list[str]) -> Path:
    if "--repo" not in argv:
        return PROJECT_ROOT
    idx = argv.index("--repo")
    next_idx = idx + 1
    if next_idx < len(argv) and not argv[next_idx].startswith("--"):
        return Path(argv[next_idx]).resolve()
    return _default_repo_target()


def _detect_package_manager(repo_root: Path) -> list[str]:
    if (repo_root / "pnpm-lock.yaml").exists():
        return ["pnpm"]
    if (repo_root / "yarn.lock").exists():
        return ["yarn"]
    return ["npm"]


def _git_status(repo_root: Path) -> list[str]:
    rc, out, _ = _run(["git", "-C", str(repo_root), "status", "--short"], cwd=repo_root, timeout=30)
    if rc != 0 or not out:
        return []
    return [line for line in out.splitlines() if line.strip()]


def _find_conflict_markers(repo_root: Path) -> list[str]:
    pattern = r"^(<<<<<<<|=======|>>>>>>>)"
    # git grep es el más rápido: solo busca en archivos tracked
    candidates = [
        ["git", "grep", "-l", "-E", pattern],
        ["rg", "-l", pattern, str(repo_root)],
    ]
    for cmd in candidates:
        try:
            rc, out, _ = _run(cmd, cwd=repo_root, timeout=15)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
        if rc not in (0, 1) or not out:
            return []
        return [line.strip() for line in out.splitlines() if line.strip()]
    return []


def _run_named_check(label: str, cmd: list[str], cwd: Path, timeout: int = 180) -> tuple[bool, str]:
    try:
        rc, out, err = _run(cmd, cwd=cwd, timeout=timeout)
    except subprocess.TimeoutExpired:
        return False, f"{label} agotó el tiempo"
    if rc == 0:
        return True, f"{label} OK"
    detail = (err or out or "").splitlines()
    tail = detail[-1] if detail else "sin detalle"
    return False, f"{label} falla: {tail}"


def _scan_repo(repo_root: Path) -> dict[str, object]:
    bugs: list[str] = []
    silent_bugs: list[str] = []
    fixable: list[str] = []
    checks: list[str] = []

    if not repo_root.exists():
        return {
            "mode": "repo",
            "applicable": False,
            "target": str(repo_root),
            "bugs": [f"Ruta no encontrada: {repo_root}"],
            "silent_bugs": [],
            "fixable": [],
            "bug_count": 1,
            "silent_bug_count": 0,
            "auto_fixable_count": 0,
            "checks": [],
        }

    package_json = repo_root / "package.json"
    pyproject = repo_root / "pyproject.toml"
    cargo = repo_root / "Cargo.toml"
    gomod = repo_root / "go.mod"
    tsconfig = repo_root / "tsconfig.json"
    tests_dir = repo_root / "tests"

    manifests = [p.name for p in (package_json, pyproject, cargo, gomod) if p.exists()]
    applicable = bool(manifests or tsconfig.exists() or tests_dir.exists())

    conflicts = _find_conflict_markers(repo_root)
    if conflicts:
        bugs.append(f"Markers de merge conflict en {len(conflicts)} archivo(s).")

    git_dirty = _git_status(repo_root)
    if git_dirty:
        silent_bugs.append(f"Working tree con {len(git_dirty)} cambio(s) sin consolidar.")

    if package_json.exists():
        data = _load_json(package_json) or {}
        scripts = data.get("scripts", {})
        pm = _detect_package_manager(repo_root)
        node_modules = (repo_root / "node_modules").exists()
        lockfiles = ["package-lock.json", "pnpm-lock.yaml", "yarn.lock"]
        if not any((repo_root / name).exists() for name in lockfiles):
            silent_bugs.append("package.json presente sin lockfile.")
        if not node_modules:
            silent_bugs.append("Proyecto Node sin node_modules; no se pueden validar scripts locales.")
        else:
            for script_name in ("lint", "typecheck", "test", "build"):
                if script_name in scripts:
                    ok, message = _run_named_check(
                        f"{pm[0]} run {script_name}",
                        pm + ["run", script_name],
                        repo_root,
                    )
                    checks.append(message)
                    if not ok:
                        bugs.append(message)
            if "lint:fix" in scripts:
                fixable.append("node_lint_fix")
            elif "fix" in scripts:
                fixable.append("node_fix")
            elif "format" in scripts:
                fixable.append("node_format")
        if not any(name in scripts for name in ("lint", "typecheck", "test", "build")):
            silent_bugs.append("package.json sin scripts de lint/typecheck/test/build.")

    if pyproject.exists():
        ok, message = _run_named_check(
            "python -m compileall",
            [sys.executable, "-m", "compileall", "-q", str(repo_root)],
            repo_root,
        )
        checks.append(message)
        if not ok:
            bugs.append(message)

        if tests_dir.exists() or (repo_root / "pytest.ini").exists():
            ok, message = _run_named_check(
                "python -m pytest -q",
                [sys.executable, "-m", "pytest", "-q"],
                repo_root,
            )
            checks.append(message)
            if not ok:
                bugs.append(message)

        pycache_dirs = list(repo_root.rglob("__pycache__"))
        if pycache_dirs:
            fixable.append("pycache")

    if cargo.exists():
        ok, message = _run_named_check("cargo check", ["cargo", "check", "--quiet"], repo_root)
        checks.append(message)
        if not ok:
            bugs.append(message)
        if shutil.which("cargo"):
            fixable.append("cargo_fmt")

    if gomod.exists():
        ok, message = _run_named_check("go test ./...", ["go", "test", "./..."], repo_root)
        checks.append(message)
        if not ok:
            bugs.append(message)

    return {
        "mode": "repo",
        "applicable": applicable,
        "target": str(repo_root),
        "manifests": manifests,
        "bugs": bugs,
        "silent_bugs": silent_bugs,
        "fixable": sorted(set(fixable)),
        "checks": checks,
        "bug_count": len(bugs),
        "silent_bug_count": len(silent_bugs),
        "auto_fixable_count": len(set(fixable)),
    }


def _apply_repo_fixes(summary: dict[str, object], repo_root: Path) -> tuple[list[str], list[str]]:
    repairs: list[str] = []
    remaining: list[str] = []
    fixable = set(summary.get("fixable", []))
    package_json = repo_root / "package.json"
    data = _load_json(package_json) or {}
    scripts = data.get("scripts", {})
    pm = _detect_package_manager(repo_root)

    if "node_lint_fix" in fixable:
        rc, out, err = _run(pm + ["run", "lint:fix"], cwd=repo_root, timeout=180)
        if rc == 0:
            repairs.append("npm/pnpm/yarn run lint:fix ejecutado.")
        else:
            remaining.append(err or out or "Falló lint:fix.")
    elif "node_fix" in fixable:
        rc, out, err = _run(pm + ["run", "fix"], cwd=repo_root, timeout=180)
        if rc == 0:
            repairs.append("npm/pnpm/yarn run fix ejecutado.")
        else:
            remaining.append(err or out or "Falló fix.")
    elif "node_format" in fixable and "format" in scripts:
        rc, out, err = _run(pm + ["run", "format"], cwd=repo_root, timeout=180)
        if rc == 0:
            repairs.append("npm/pnpm/yarn run format ejecutado.")
        else:
            remaining.append(err or out or "Falló format.")

    if "pycache" in fixable:
        removed = 0
        for path in repo_root.rglob("__pycache__"):
            shutil.rmtree(path, ignore_errors=True)
            removed += 1
        if removed:
            repairs.append(f"__pycache__ limpiados: {removed}")

    if "cargo_fmt" in fixable and shutil.which("cargo"):
        rc, out, err = _run(["cargo", "fmt"], cwd=repo_root, timeout=180)
        if rc == 0:
            repairs.append("cargo fmt ejecutado.")
        else:
            remaining.append(err or out or "Falló cargo fmt.")

    return repairs, remaining


def _print_human(summary: dict[str, object], repairs: list[str], remaining: list[str], check_only: bool) -> None:
    print()
    header = "BAGO DEBUG REPO" if summary.get("mode") == "repo" else "BAGO DEBUG"
    print(f"═══ {header} ═══════════════════════════════════════════")
    print()

    if summary.get("mode") == "repo":
        print(f"Objetivo: {summary.get('target')}")
        manifests = summary.get("manifests", [])
        if manifests:
            print(f"Manifests: {', '.join(manifests)}")
        print()

    bugs = summary.get("bugs", [])
    silent_bugs = summary.get("silent_bugs", [])
    if not bugs and not silent_bugs:
        print("Sin bugs ni bugs silenciosos detectables.")
    else:
        if bugs:
            print("Bugs:")
            for item in bugs:
                print(f"  - {item}")
            print()
        if silent_bugs:
            print("Posibles bugs silenciosos:")
            for item in silent_bugs:
                print(f"  - {item}")
            print()

    checks = summary.get("checks", [])
    if checks:
        print("Checks ejecutados:")
        for item in checks:
            print(f"  - {item}")
        print()

    if repairs:
        print("Reparaciones aplicadas:")
        for item in repairs:
            print(f"  - {item}")
        print()

    if remaining:
        print("Pendiente manual:")
        for item in remaining:
            print(f"  - {item}")
        print()

    mode = "check-only" if check_only else "fix"
    print(
        f"Resumen: bugs={summary.get('bug_count', 0)} "
        f"silent={summary.get('silent_bug_count', 0)} "
        f"auto_fixable={summary.get('auto_fixable_count', 0)} "
        f"mode={mode}"
    )
    print()


def main() -> int:
    argv = sys.argv[1:]
    check_only = "--check" in argv
    as_json = "--json" in argv
    repo_mode = "--repo" in argv

    if repo_mode:
        repo_root = _parse_repo_target(argv)
        summary = _scan_repo(repo_root)
        repairs: list[str] = []
        remaining: list[str] = []
        if not check_only and summary.get("auto_fixable_count", 0) > 0:
            repairs, remaining = _apply_repo_fixes(summary, repo_root)
            summary = _scan_repo(repo_root)
        result = {**summary, "repairs_applied": repairs, "remaining": remaining}
    else:
        summary = _scan_pack()
        repairs = []
        remaining = []
        if not check_only and summary.get("auto_fixable_count", 0) > 0:
            repairs, remaining = _apply_pack_fixes(summary)
            summary = _scan_pack()
        result = {**summary, "repairs_applied": repairs, "remaining": remaining}

    if as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        _print_human(summary, repairs, remaining, check_only)

    return 1 if result.get("bug_count", 0) > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
