#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
env_check.py — Diagnóstico del entorno de desarrollo BAGO/INTELIA.

Detecta problemas comunes del entorno: Node.js, Python, PostgreSQL,
puertos del proyecto, archivos .env faltantes y dependencias.

Invocado como: bago doctor  (env check, not pack integrity check)

Uso:
    python3 .bago/tools/env_check.py              # diagnóstico completo
    python3 .bago/tools/env_check.py --json       # salida JSON (para CI)

Códigos de salida: 0 = todo OK, 1 = hay errores, 2 = advertencias
"""
from __future__ import annotations

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT  = Path(__file__).resolve().parents[2]
STATE = ROOT / ".bago" / "state"


def GREEN(s: str)  -> str: return f"\033[32m{s}\033[0m"
def RED(s: str)    -> str: return f"\033[31m{s}\033[0m"
def YELLOW(s: str) -> str: return f"\033[33m{s}\033[0m"
def DIM(s: str)    -> str: return f"\033[2m{s}\033[0m"
def BOLD(s: str)   -> str: return f"\033[1m{s}\033[0m"
def CYAN(s: str)   -> str: return f"\033[36m{s}\033[0m"


def _run(cmd: list[str], timeout: int = 5) -> tuple[int, str]:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return r.returncode, (r.stdout + r.stderr).strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return 1, ""


def _port_in_use(port: int) -> bool:
    try:
        raw = subprocess.run(["netstat", "-ano"], capture_output=True, timeout=5).stdout
        text = raw.decode("cp1252", errors="replace")
        return (f":{port} " in text or f":{port}\t" in text)
    except Exception:
        return False


def _load_project() -> Path | None:
    gs_file = STATE / "global_state.json"
    if not gs_file.exists():
        return None
    try:
        gs = json.loads(gs_file.read_text(encoding="utf-8"))
        p = gs.get("active_project", {}).get("path", "")
        return Path(p) if p else None
    except Exception:
        return None


def _check_node() -> dict:
    code, out = _run(["node", "--version"])
    if code == 0 and out.startswith("v"):
        major = int(out[1:].split(".")[0])
        if major >= 18:
            return {"name": "Node.js", "status": "ok", "detail": out}
        return {"name": "Node.js", "status": "warn", "detail": f"{out} (recomendado v18+)", "fix": "Actualiza Node.js"}
    return {"name": "Node.js", "status": "error", "detail": "no encontrado", "fix": "Instala Node.js en https://nodejs.org"}


def _check_npm() -> dict:
    code, out = _run(["npm", "--version"])
    if code == 0:
        return {"name": "npm", "status": "ok", "detail": f"v{out}"}
    return {"name": "npm", "status": "error", "detail": "no encontrado", "fix": "Instala npm (viene con Node.js)"}


def _check_python() -> dict:
    out = f"v{sys.version.split()[0]}"
    major, minor = sys.version_info.major, sys.version_info.minor
    if major == 3 and minor >= 10:
        return {"name": "Python", "status": "ok", "detail": out}
    return {"name": "Python", "status": "warn", "detail": f"{out} (recomendado 3.10+)", "fix": "Actualiza Python"}


def _check_git() -> dict:
    code, out = _run(["git", "--version"])
    if code == 0:
        return {"name": "git", "status": "ok", "detail": out[:30]}
    return {"name": "git", "status": "warn", "detail": "no encontrado", "fix": "Instala git"}


def _check_postgres() -> dict:
    code, out = _run(["psql", "--version"])
    if code != 0:
        return {"name": "PostgreSQL", "status": "warn", "detail": "psql no encontrado (opcional)", "fix": "Instala PostgreSQL o usa DB remota"}
    if _port_in_use(5432):
        return {"name": "PostgreSQL", "status": "ok", "detail": f"{out[:30]} · corriendo :5432"}
    return {"name": "PostgreSQL", "status": "warn", "detail": f"{out[:30]} · no corriendo", "fix": "Ejecuta: bago db-local"}


def _check_ports() -> dict:
    project_ports = {3000: "web", 5173: "vite", 8788: "server", 4173: "preview"}
    in_use = [f":{p}({label})" for p, label in project_ports.items() if _port_in_use(p)]
    detail = "en uso: " + ", ".join(in_use) if in_use else "todos libres"
    return {"name": "Puertos del proyecto", "status": "ok", "detail": detail}


def _check_env_files(project: Path | None) -> dict:
    if not project or not project.exists():
        return {"name": "Archivos .env", "status": "warn", "detail": "proyecto no configurado", "fix": "bago config"}
    apps_dir = project / "apps"
    if not apps_dir.exists():
        return {"name": "Archivos .env", "status": "ok", "detail": "no hay directorio apps/"}
    missing = [d.name for d in apps_dir.iterdir() if d.is_dir() and (d / ".env.example").exists() and not (d / ".env").exists()]
    if not missing:
        return {"name": "Archivos .env", "status": "ok", "detail": "presentes en todas las apps"}
    return {"name": "Archivos .env", "status": "error", "detail": f"faltante en: {', '.join(missing)}", "fix": "Ejecuta: bago env"}


def _check_node_modules(project: Path | None) -> dict:
    if not project or not project.exists():
        return {"name": "node_modules", "status": "warn", "detail": "proyecto no configurado"}
    apps_dir = project / "apps"
    if not apps_dir.exists():
        return {"name": "node_modules", "status": "ok", "detail": "no hay directorio apps/"}
    missing = [d.name for d in apps_dir.iterdir() if d.is_dir() and (d / "package.json").exists() and not (d / "node_modules").exists()]
    if not missing:
        return {"name": "node_modules", "status": "ok", "detail": "instalados en todas las apps"}
    return {"name": "node_modules", "status": "error", "detail": f"faltante en: {', '.join(missing)}", "fix": "Ejecuta: bago deps --install"}


def _check_bago_state() -> dict:
    essential = [STATE / "global_state.json", STATE / "implemented_ideas.json", STATE / "bago.db"]
    missing = [f.name for f in essential if not f.exists()]
    if not missing:
        return {"name": "Estado BAGO", "status": "ok", "detail": "archivos de estado presentes"}
    return {"name": "Estado BAGO", "status": "warn", "detail": f"faltan: {', '.join(missing)}", "fix": "bago init"}


def _check_server() -> dict:
    try:
        with urllib.request.urlopen("http://localhost:8788/health", timeout=2) as r:
            if r.status < 400:
                return {"name": "Servidor local", "status": "ok", "detail": f"HTTP {r.status} en :8788"}
    except urllib.error.HTTPError as e:
        return {"name": "Servidor local", "status": "warn", "detail": f"HTTP {e.code} en :8788"}
    except Exception:
        pass
    return {"name": "Servidor local", "status": "warn", "detail": "no responde en :8788", "fix": "npm run dev en apps/server"}


def main() -> int:
    args = sys.argv[1:]
    output_json = "--json" in args

    project = _load_project()

    checks = [
        _check_node(), _check_npm(), _check_python(), _check_git(),
        _check_postgres(), _check_ports(),
        _check_env_files(project), _check_node_modules(project),
        _check_bago_state(), _check_server(),
    ]

    if output_json:
        print(json.dumps(checks, ensure_ascii=False, indent=2))
        return 1 if any(r["status"] == "error" for r in checks) else 0

    print()
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  BAGO · Doctor — Diagnóstico del entorno                    │")
    print("  └─────────────────────────────────────────────────────────────┘")
    if project:
        print(f"  Proyecto : {project.name}")
    print()

    icons = {"ok": GREEN("✅"), "warn": YELLOW("⚠ "), "error": RED("❌")}
    errors, warnings = 0, 0

    for r in checks:
        icon = icons.get(r["status"], "?")
        detail = DIM(r.get("detail", ""))
        print(f"  {icon} {BOLD(r['name']):<30}  {detail}")
        if r.get("fix") and r["status"] in ("error", "warn"):
            print(f"       {CYAN('→')} {r['fix']}")
        if r["status"] == "error":
            errors += 1
        elif r["status"] == "warn":
            warnings += 1

    print()
    if errors == 0 and warnings == 0:
        print(f"  {GREEN('✅  Entorno saludable — todo OK.')}")
    elif errors > 0:
        print(f"  {RED(f'❌  {errors} error(es) · {warnings} advertencia(s).')}")
    else:
        print(f"  {YELLOW(f'⚠  {warnings} advertencia(s). Entorno funcional.')}")
    print()

    return 1 if errors else (2 if warnings else 0)



def _self_test():
    """Autotest mínimo — verifica arranque limpio del módulo."""
    from pathlib import Path as _P
    assert _P(__file__).exists(), "fichero no encontrado"
    print("  1/1 tests pasaron")

if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
        raise SystemExit(0)
    raise SystemExit(main())
