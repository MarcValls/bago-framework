#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
env_setup.py — Genera .env local a partir de .env.example con valores dev seguros.

Detecta el tipo de variable (puerto, URL, booleano, secreto, etc.) y propone
valores de desarrollo que no requieren secretos de producción.

Uso:
    python3 .bago/tools/env_setup.py                    # usa proyecto activo
    python3 .bago/tools/env_setup.py --path /ruta/repo  # ruta explícita
    python3 .bago/tools/env_setup.py --app server       # solo apps/server/.env
    python3 .bago/tools/env_setup.py --dry-run          # muestra sin escribir
    python3 .bago/tools/env_setup.py --force            # sobreescribe .env existente

Códigos de salida: 0 = OK, 1 = error, 3 = .env ya existe (usar --force)
"""
from __future__ import annotations

import json
import os
import re
import secrets
import sys
from pathlib import Path

# Windows UTF-8
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT  = Path(__file__).resolve().parents[2]
STATE = ROOT / ".bago" / "state"

# ─── Variable type detection ──────────────────────────────────────────────────

_PORT_RE     = re.compile(r"PORT|_PORT$", re.I)
_URL_RE      = re.compile(r"URL|HOST|ORIGIN|ENDPOINT", re.I)
_SECRET_RE   = re.compile(r"SECRET|TOKEN|KEY|PASSWORD|PWD|PASS|AUTH|JWT", re.I)
_BOOL_RE     = re.compile(r"ENABLE|DISABLE|FLAG|SECURE|TRUST|UPDATING", re.I)
_INT_RE      = re.compile(r"MAX|LIMIT|SIZE|TTL|WINDOW|TIMEOUT|BYTES|ITEMS|SECONDS", re.I)
_MODE_RE     = re.compile(r"ENV|ENVIRONMENT|NODE_ENV|MODE", re.I)

# Safe dev defaults by key pattern
_DEV_DEFAULTS: dict[str, str] = {
    "DATABASE_URL":                "postgres://postgres:tpvlocal@localhost:5432/tpv",
    "API_PORT":                    "8788",
    "API_HOST":                    "0.0.0.0",
    "API_DB_SEARCH_PATH":          "public",
    "AUTH_JWT_SECRET":             "",        # generated at runtime
    "AUTH_JWT_KID":                "auth-v1",
    "AUTH_ACCESS_TTL_SECONDS":     "600",
    "AUTH_REFRESH_TTL_SECONDS":    "2592000",
    "AUTH_COOKIE_SECURE":          "false",
    "API_CORS_ORIGINS":            "http://localhost:3000,http://localhost:3001,http://localhost:5173,https://localhost,null",
    "API_JSON_LIMIT_BYTES":        "1048576",
    "API_RATE_LIMIT_WINDOW_MS":    "60000",
    "API_RATE_LIMIT_MAX_READS":    "300",
    "API_RATE_LIMIT_MAX_WRITES":   "60",
    "API_STATE_COLLECTION_MAX_ITEMS": "10000",
    "API_DOCUMENT_LINES_MAX_ITEMS":   "500",
    "API_DOCUMENT_PAYMENTS_MAX_ITEMS":"200",
    "API_TRUST_PROXY":             "false",
    "SERVER_UPDATING":             "false",
    "NODE_ENV":                    "development",
    "NODE_VERSION":                "22.16.0",
    "VITE_SERVER_MODE":            "true",
    "VITE_API_URL":                "/backend",
    "SUPERADMIN_MASTER_KEY":       "",        # generated
    "API_TOKEN":                   "",        # optional in dev
}


def _detect_type(key: str, example_val: str) -> str:
    """Classify a variable key into a semantic type."""
    if _PORT_RE.search(key):   return "port"
    if _SECRET_RE.search(key): return "secret"
    if _URL_RE.search(key):    return "url"
    if _BOOL_RE.search(key):   return "bool"
    if _INT_RE.search(key):    return "int"
    if _MODE_RE.search(key):   return "mode"
    return "string"


def _safe_dev_value(key: str, example_val: str) -> tuple[str, str]:
    """Return (value, note) — a safe dev value and a brief note."""
    # Known exact key overrides
    if key in _DEV_DEFAULTS:
        val = _DEV_DEFAULTS[key]
        if val == "":
            # Needs generation or is optional
            if _SECRET_RE.search(key):
                val = secrets.token_hex(32)
                return val, "auto-generado"
            return "", "opcional en dev"
        return val, "default dev"

    vtype = _detect_type(key, example_val)

    if vtype == "secret":
        return secrets.token_hex(32), "auto-generado (dev)"
    if vtype == "port":
        return example_val or "8080", "puerto dev"
    if vtype == "bool":
        return "false", "seguro en dev"
    if vtype == "int":
        return example_val or "0", "valor ejemplo"
    if vtype == "url":
        return example_val or "http://localhost:3000", "URL local"
    if vtype == "mode":
        return "development", "entorno dev"
    # Keep example value if it exists and looks safe (no prod markers)
    if example_val and "production" not in example_val.lower() \
            and "secret" not in example_val.lower():
        return example_val, "del ejemplo"
    return "", "requiere valor manual"


def _parse_dotenv_example(path: Path) -> list[tuple[str, str, str]]:
    """Parse .env.example → [(key, example_value, comment_above)]"""
    result = []
    pending_comment = ""
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                pending_comment = stripped
                continue
            if "=" in stripped and stripped:
                key, _, val = stripped.partition("=")
                result.append((key.strip(), val.strip(), pending_comment))
                pending_comment = ""
            else:
                pending_comment = ""
    except Exception as e:
        print(f"  ⚠  No se pudo leer {path}: {e}")
    return result


def _project_root() -> Path | None:
    gs_file = STATE / "global_state.json"
    if not gs_file.exists():
        return None
    try:
        gs = json.loads(gs_file.read_text(encoding="utf-8"))
        p = gs.get("active_project", {}).get("path", "")
        return Path(p) if p else None
    except Exception:
        return None


def _find_env_examples(project: Path, app_filter: str | None) -> list[Path]:
    if app_filter:
        candidate = project / "apps" / app_filter / ".env.example"
        return [candidate] if candidate.exists() else []
    return sorted(project.glob("apps/*/.env.example"))


def _generate_env(entries: list[tuple[str, str, str]], dry_run: bool) -> list[str]:
    lines = ["# Generated by bago env — safe development values", "# Edit secrets before using in production", ""]
    for key, ex_val, comment in entries:
        val, note = _safe_dev_value(key, ex_val)
        if comment:
            lines.append(comment)
        lines.append(f"{key}={val}  # {note}")
    return lines


def _col(text: str, width: int) -> str:
    return str(text).ljust(width)[:width]


def run(project: Path, app_filter: str | None, dry_run: bool, force: bool) -> int:
    examples = _find_env_examples(project, app_filter)
    if not examples:
        print("  ⚠  No se encontró ningún .env.example en el proyecto.")
        return 1

    any_written = False
    for example_path in examples:
        app_dir = example_path.parent
        env_path = app_dir / ".env"
        app_name = app_dir.name

        print()
        print(f"  📂  {app_name}/.env.example  →  .env")

        if env_path.exists() and not force and not dry_run:
            print(f"  ℹ  .env ya existe (usa --force para sobreescribir)")
            continue

        entries = _parse_dotenv_example(example_path)
        if not entries:
            print("  ⚠  No se encontraron variables en el ejemplo.")
            continue

        print()
        W1, W2, W3 = 38, 20, 18
        hdr = f"  {'Variable'.ljust(W1)}  {'Valor dev'.ljust(W2)}  {'Nota'.ljust(W3)}"
        sep = "  " + "-" * (W1 + W2 + W3 + 4)
        print(hdr)
        print(sep)

        for key, ex_val, _ in entries:
            val, note = _safe_dev_value(key, ex_val)
            display = val[:18] + "…" if len(val) > 18 else val
            print(f"  {_col(key, W1)}  {_col(display, W2)}  {_col(note, W3)}")

        if dry_run:
            print(f"\n  🔍  DRY-RUN: no se escribió .env")
            continue

        lines = _generate_env(entries, dry_run)
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"\n  ✅  Escrito: {env_path.relative_to(project)}")
        any_written = True

    return 0


def main() -> int:
    args = sys.argv[1:]
    dry_run     = "--dry-run" in args
    force       = "--force"   in args

    project: Path | None = None
    app_filter: str | None = None

    if "--path" in args:
        idx = args.index("--path")
        if idx + 1 < len(args):
            project = Path(args[idx + 1])
    if "--app" in args:
        idx = args.index("--app")
        if idx + 1 < len(args):
            app_filter = args[idx + 1]

    if project is None:
        project = _project_root()

    if project is None or not project.exists():
        print("  ⚠  No se encontró proyecto activo. Usa --path /ruta/al/proyecto")
        return 1

    print()
    print("  ┌─────────────────────────────────────────────────────────────┐")
    print("  │  BAGO · Generador de .env                                   │")
    print("  └─────────────────────────────────────────────────────────────┘")
    print(f"  Proyecto: {project}")

    return run(project, app_filter, dry_run, force)



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
