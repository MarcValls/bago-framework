#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
make_clean_pack.py — Genera un ZIP de arranque limpio de BAGO sin historial.

Ubicación: .bago/dist/source/make_clean_pack.py
Ejecutar desde la raíz del proyecto (donde está el script `bago`):
    python3 .bago/dist/source/make_clean_pack.py

El ZIP resultante contiene el pack BAGO completo con:
  - Toda la estructura operativa (.bago/, bago, Makefile)
  - Directorios de estado vacíos (sin sesiones/cambios/evidencias)
  - Ficheros de estado reseteados a valores iniciales
  - TREE.txt y CHECKSUMS.sha256 regenerados sobre el contenido limpio
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

# ─── Rutas base ────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent          # .bago/dist/source/
BAGO_ROOT    = SCRIPT_DIR.parent.parent                 # .bago/
PROJECT_ROOT = BAGO_ROOT.parent                         # directorio raíz del proyecto

VERSION   = "2.4-v2rc"
TIMESTAMP = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
ZIP_NAME  = f"BAGO_{VERSION}_clean_{TIMESTAMP}.zip"
ZIP_PATH  = SCRIPT_DIR / ZIP_NAME

# ─── Reglas de exclusión ───────────────────────────────────────────────────────
# Rutas relativas a BAGO_ROOT que se excluyen completamente
EXCLUDE_DIRS = {
    "state/metrics/runs",
    "state/migrated_sessions",
    "state/migrated_changes",
}

# Glob patterns de ficheros excluidos (relativo a BAGO_ROOT)
EXCLUDE_FILE_PATTERNS = {
    "state/sessions/*.json",
    "state/changes/*.json",
    "state/evidences/*.json",
    "dist/source/*.zip",
}

# Ficheros/directorios excluidos de raíz (no dentro de .bago)
EXCLUDE_ROOT_FILES = set()   # nada extra en raíz por ahora

# Exclusiones globales (por nombre de fichero o directorio, en cualquier nivel)
EXCLUDE_NAMES = {"__pycache__", ".DS_Store"}
EXCLUDE_EXTENSIONS = {".pyc"}

# ─── Ficheros excluidos adicionales dentro de .bago (rutas relativas a BAGO_ROOT)
EXCLUDE_INDIVIDUAL = {
    "state/user_personality_profile.json",   # datos personales
}

# ─── Contenido de reset ───────────────────────────────────────────────────────
RESET_GLOBAL_STATE = {
    "bago_version": VERSION,
    "canon_version": VERSION,
    "system_health": "stable",
    "active_session_id": None,
    "active_task_type": None,
    "active_roles": [],
    "open_changes": [],
    "active_scenarios": [],
    "active_workflows": [],
    "history_migration_status": "clean_start",
    "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000+00:00"),
    "v2_status": "completed",
    "notes": "",
    "last_completed_session_id": None,
    "last_completed_task_type": None,
    "last_completed_workflow": None,
    "last_completed_roles": [],
    "last_completed_change_id": None,
    "last_completed_evidence_id": None,
    "inventory": {
        "sessions": 0,
        "changes": 0,
        "evidences": 0
    },
    "last_validation": {
        "pack": "GO",
        "state": "GO",
        "manifest": "GO",
        "recorded_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000000+00:00")
    },
    "baseline_code": f"clean_start_{TIMESTAMP}",
    "baseline_status": "active_clean_core",
    "sprint_status": {}
}

RESET_REPO_CONTEXT = {
    "role": "external_repo_pointer",
    "note": "Ejecuta `python3 bago` para sincronizar este fichero al directorio actual.",
    "working_mode": "self",
    "repo_root": None,
    "bago_host_root": None,
    "repo_fingerprint": None,
    "recorded_at": None
}

RESET_ESTADO_MD = """# ESTADO_BAGO_ACTUAL

> **Pack BAGO {version} · Arranque limpio.**  
> Ejecuta `python3 bago` para inicializar el contexto en este directorio.

## Versión activa

**BAGO v{version}** — Dynamic-BAGO con runtime governance  
**Estado:** arranque limpio — sin historial previo

## Inventario

- Sesiones: **0**
- Cambios: **0**
- Evidencias: **0**

## Próximo paso

```bash
# Desde el directorio del proyecto:
python3 bago          # inicializa + muestra banner
python3 bago validate # verifica integridad del pack
python3 bago audit    # auditoría completa
python3 bago workflow # selector interactivo de workflow
```
""".format(version=VERSION)

RESET_METRICS_SNAPSHOT: dict = {}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _is_excluded_dir(rel: Path) -> bool:
    """True si la ruta relativa (respecto a BAGO_ROOT) cae dentro de un dir excluido."""
    rel_str = rel.as_posix()
    for excl in EXCLUDE_DIRS:
        if rel_str == excl or rel_str.startswith(excl + "/"):
            return True
    return False


def _is_excluded_file(rel: Path) -> bool:
    """True si el fichero debe excluirse."""
    rel_str = rel.as_posix()

    # Exclusiones individuales
    if rel_str in EXCLUDE_INDIVIDUAL:
        return True

    # Por nombre de fichero (en cualquier nivel)
    if rel.name in EXCLUDE_NAMES:
        return True

    # Por extensión
    if rel.suffix in EXCLUDE_EXTENSIONS:
        return True

    # Por glob patterns explícitos
    for pattern in EXCLUDE_FILE_PATTERNS:
        pat = Path(pattern)
        # Simular glob: dir/nombre/*.json → comprobar parent y extensión
        parent_pat = pat.parent.as_posix()
        name_pat   = pat.name
        if rel.parent.as_posix() == parent_pat:
            if name_pat.startswith("*"):
                ext = name_pat[1:]          # e.g. ".json"
                if rel.suffix == ext or (not ext and True):
                    return True
            elif rel.name == name_pat:
                return True
    return False


def _is_reset_file(rel: Path) -> tuple[bool, object]:
    """Devuelve (True, content) si el fichero debe resetearse, (False, None) si no."""
    rel_str = rel.as_posix()
    resets = {
        "state/global_state.json":         (json.dumps(RESET_GLOBAL_STATE, indent=2, ensure_ascii=False) + "\n"),
        "state/repo_context.json":         (json.dumps(RESET_REPO_CONTEXT, indent=2, ensure_ascii=False) + "\n"),
        "state/ESTADO_BAGO_ACTUAL.md":     RESET_ESTADO_MD,
        "state/metrics/metrics_snapshot.json": (json.dumps(RESET_METRICS_SNAPSHOT, indent=2) + "\n"),
    }
    if rel_str in resets:
        return True, resets[rel_str]
    return False, None


def _regenerate_tree_checksums(bago_tmp: Path) -> tuple[int, int]:
    """Regenera TREE.txt y CHECKSUMS.sha256 dentro de bago_tmp. Devuelve (n_entries, n_checksums)."""
    entries = sorted(
        str(p.relative_to(bago_tmp)) + ("/" if p.is_dir() else "")
        for p in bago_tmp.rglob("*")
    )
    (bago_tmp / "TREE.txt").write_text("\n".join(entries) + "\n", encoding="utf-8")

    lines = []
    for p in sorted(bago_tmp.rglob("*")):
        if p.is_file() and p.name != "CHECKSUMS.sha256":
            digest = hashlib.sha256(p.read_bytes()).hexdigest()
            lines.append(f"{digest}  {p.relative_to(bago_tmp)}")
    (bago_tmp / "CHECKSUMS.sha256").write_text("\n".join(lines) + "\n", encoding="utf-8")

    return len(entries), len(lines)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print()
    print("  ╔══════════════════════════════════════════════════════╗")
    print("  ║  BAGO · make_clean_pack — ZIP de arranque limpio     ║")
    print("  ╚══════════════════════════════════════════════════════╝")
    print()

    included: list[str] = []
    excluded: list[str] = []
    reset:    list[str] = []

    with tempfile.TemporaryDirectory(prefix="bago_clean_") as tmpdir:
        tmp     = Path(tmpdir)
        staging = tmp / f"BAGO_{VERSION}_clean_{TIMESTAMP}"

        # ── 1. Copiar .bago/ con filtros ──────────────────────────────────────
        bago_tmp = staging / ".bago"
        bago_tmp.mkdir(parents=True)

        for src in sorted(BAGO_ROOT.rglob("*")):
            rel = src.relative_to(BAGO_ROOT)

            # Saltar directorios — los crearemos implícitamente al copiar ficheros
            if src.is_dir():
                continue

            # Saltar ficheros dentro de directorios excluidos
            if _is_excluded_dir(rel.parent if not src.is_dir() else rel):
                excluded.append(f".bago/{rel}")
                continue

            # Saltar el propio script en dist/source/ de la copia... no, incluirlo
            # (es una herramienta válida del pack limpio)

            # Saltar ficheros excluidos individualmente
            if _is_excluded_file(rel):
                excluded.append(f".bago/{rel}")
                continue

            dst = bago_tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)

            # ¿Es un fichero de reset?
            is_reset, content = _is_reset_file(rel)
            if is_reset:
                dst.write_text(content, encoding="utf-8")
                reset.append(f".bago/{rel}")
                included.append(f".bago/{rel}  [RESET]")
            else:
                shutil.copy2(src, dst)
                included.append(f".bago/{rel}")

        # Asegurar que los directorios "vacíos" existen con sus README si lo tenían
        for empty_rel in ["state/sessions", "state/changes", "state/evidences",
                          "state/metrics/runs"]:
            empty_dst = bago_tmp / empty_rel
            empty_dst.mkdir(parents=True, exist_ok=True)
            # Copiar README.md si existe en el original
            src_readme = BAGO_ROOT / empty_rel / "README.md"
            if src_readme.exists():
                shutil.copy2(src_readme, empty_dst / "README.md")

        # ── 2. Copiar bago (script raíz) ──────────────────────────────────────
        bago_script_src = PROJECT_ROOT / "bago"
        if bago_script_src.exists():
            bago_script_dst = staging / "bago"
            shutil.copy2(bago_script_src, bago_script_dst)
            bago_script_dst.chmod(0o755)
            included.append("bago")
        else:
            print("  ⚠️  script 'bago' no encontrado en PROJECT_ROOT")

        # ── 3. Copiar Makefile ─────────────────────────────────────────────────
        makefile_src = PROJECT_ROOT / "Makefile"
        if makefile_src.exists():
            shutil.copy2(makefile_src, staging / "Makefile")
            included.append("Makefile")

        # ── 4. Regenerar TREE.txt y CHECKSUMS.sha256 dentro del .bago limpio ──
        n_entries, n_checksums = _regenerate_tree_checksums(bago_tmp)
        print(f"  📋 TREE.txt regenerado    — {n_entries} entradas")
        print(f"  🔐 CHECKSUMS.sha256 regen — {n_checksums} ficheros")
        print()

        # ── 5. Crear ZIP ───────────────────────────────────────────────────────
        ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(ZIP_PATH, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            for file_path in sorted(staging.rglob("*")):
                if file_path.is_file():
                    arcname = file_path.relative_to(tmp)
                    zf.write(file_path, arcname)

        zip_size_kb = ZIP_PATH.stat().st_size / 1024

        # ── 6. Resumen ─────────────────────────────────────────────────────────
        print(f"  📦 ZIP creado: {ZIP_PATH.relative_to(PROJECT_ROOT)}")
        print(f"  📏 Tamaño:     {zip_size_kb:.1f} KB")
        print()
        print(f"  ✅ Incluidos:   {len(included)} ficheros")
        print(f"  🔄 Reseteados:  {len(reset)} ficheros")
        print(f"  🚫 Excluidos:   {len(excluded)} ficheros")
        print()
        print("  Ficheros reseteados:")
        for r in reset:
            print(f"    → {r}")
        print()
        print("  ╔══════════════════════════════════════════════════════╗")
        print("  ║  ✅ Pack limpio generado correctamente               ║")
        print("  ╚══════════════════════════════════════════════════════╝")
        print()
        print("  Para usar en un proyecto nuevo:")
        print(f"    unzip {ZIP_PATH.name} -d /ruta/nuevo_proyecto/")
        print(f"    cd /ruta/nuevo_proyecto/BAGO_{VERSION}_clean_{TIMESTAMP}/")
        print("    python3 bago")
        print()


if __name__ == "__main__":
    main()
