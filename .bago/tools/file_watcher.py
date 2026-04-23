#!/usr/bin/env python3
"""file_watcher.py — Herramienta #106: Vigilante de cambios en archivos del proyecto.

Monitoriza un directorio y ejecuta un comando cuando detecta cambios.
Modo snapshot (--once) para CI: compara estado actual vs baseline guardado.

Uso:
    bago watch [TARGET] [--cmd COMMAND] [--ext py,js,go] [--interval N]
               [--once] [--baseline FILE] [--json] [--test]

Modos:
    watch (default)  Vigila continuamente y ejecuta --cmd al detectar cambios
    --once           Snapshot único: guarda o compara baseline, exit 1 si hay cambios

Opciones:
    TARGET        Directorio a vigilar (default: ./)
    --cmd         Comando a ejecutar al detectar cambios (default: solo reportar)
    --ext         Extensiones a vigilar, sin punto, coma-separadas (default: py,js,ts,go)
    --interval    Segundos entre checks (default: 2)
    --once        Modo snapshot: compara vs baseline, exit 1 si hay cambios
    --baseline    Archivo de baseline para --once (default: .bago/state/watch_baseline.json)
    --json        Output en JSON (solo con --once)
    --test        Self-tests
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import datetime
from pathlib import Path
from typing import Optional

BAGO_ROOT    = Path(__file__).parent.parent
DEFAULT_BASE = BAGO_ROOT / "state" / "watch_baseline.json"

_RED  = "\033[0;31m"
_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_BLU  = "\033[0;34m"
_RST  = "\033[0m"
_BOLD = "\033[1m"
_DIM  = "\033[2m"

DEFAULT_EXTS = {"py", "js", "ts", "go", "rs", "sh"}


def _hash_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except Exception:
        return "error"


def snapshot(target: str, exts: set[str]) -> dict[str, str]:
    """Genera snapshot {relpath: sha256[:16]} de todos los archivos vigilados."""
    root = Path(target)
    result: dict[str, str] = {}
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if any(x in f.parts for x in ("node_modules", "__pycache__", ".git", "venv", ".venv")):
            continue
        if f.suffix.lstrip(".") not in exts:
            continue
        rel = str(f.relative_to(root))
        result[rel] = _hash_file(f)
    return result


def diff_snapshots(old: dict, new: dict) -> dict:
    """Compara dos snapshots. Devuelve added/removed/modified."""
    old_keys = set(old.keys())
    new_keys = set(new.keys())
    added    = sorted(new_keys - old_keys)
    removed  = sorted(old_keys - new_keys)
    modified = sorted(k for k in old_keys & new_keys if old[k] != new[k])
    return {"added": added, "removed": removed, "modified": modified}


def save_baseline(snap: dict, path: Path, target: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "saved_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "target":   target,
        "files":    len(snap),
        "snapshot": snap,
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_baseline(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


# ─── Watch loop ────────────────────────────────────────────────────────────

def watch_loop(target: str, exts: set[str], cmd: Optional[str],
               interval: int) -> None:
    print(f"{_BLU}Vigilando {target} (ext: {','.join(sorted(exts))}) — Ctrl+C para salir{_RST}")
    prev = snapshot(target, exts)
    while True:
        time.sleep(interval)
        curr = snapshot(target, exts)
        diff = diff_snapshots(prev, curr)
        changes = diff["added"] + diff["removed"] + diff["modified"]
        if changes:
            ts = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M:%S")
            print(f"\n{_YEL}[{ts}] Cambios detectados:{_RST}")
            for f in diff["added"]:
                print(f"  {_GRN}+{_RST} {f}")
            for f in diff["removed"]:
                print(f"  {_RED}-{_RST} {f}")
            for f in diff["modified"]:
                print(f"  {_YEL}~{_RST} {f}")
            if cmd:
                print(f"  Ejecutando: {cmd}")
                subprocess.run(cmd, shell=True)
            prev = curr


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    target   = "./"
    cmd      = None
    ext_str  = "py,js,ts,go"
    interval = 2
    once     = False
    baseline = DEFAULT_BASE
    as_json  = False

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--cmd" and i + 1 < len(argv):
            cmd = argv[i + 1]; i += 2
        elif a == "--ext" and i + 1 < len(argv):
            ext_str = argv[i + 1]; i += 2
        elif a == "--interval" and i + 1 < len(argv):
            interval = int(argv[i + 1]); i += 2
        elif a == "--once":
            once = True; i += 1
        elif a == "--baseline" and i + 1 < len(argv):
            baseline = Path(argv[i + 1]); i += 2
        elif a == "--json":
            as_json = True; i += 1
        elif not a.startswith("--"):
            target = a; i += 1
        else:
            i += 1

    exts = {e.strip().lstrip(".") for e in ext_str.split(",") if e.strip()}

    if once:
        curr = snapshot(target, exts)
        old  = load_baseline(baseline)
        if old is None:
            save_baseline(curr, baseline, target)
            if as_json:
                print(json.dumps({"action": "saved", "files": len(curr), "baseline": str(baseline)}))
            else:
                print(f"{_GRN}✅ Baseline guardado:{_RST} {baseline}  ({len(curr)} archivos)")
            return 0
        diff = diff_snapshots(old["snapshot"], curr)
        total_changes = len(diff["added"]) + len(diff["removed"]) + len(diff["modified"])
        if as_json:
            print(json.dumps({"changes": total_changes, "diff": diff,
                               "baseline_date": old.get("saved_at", "?")}))
            return 1 if total_changes else 0
        if total_changes:
            print(f"{_YEL}⚠️  {total_changes} cambio(s) desde baseline ({old.get('saved_at','?')[:19]}){_RST}")
            for f in diff["added"]:   print(f"  {_GRN}+{_RST} {f}")
            for f in diff["removed"]: print(f"  {_RED}-{_RST} {f}")
            for f in diff["modified"]:print(f"  {_YEL}~{_RST} {f}")
            return 1
        print(f"{_GRN}✅ Sin cambios desde baseline{_RST}")
        return 0

    try:
        watch_loop(target, exts, cmd, interval)
    except KeyboardInterrupt:
        print(f"\n{_DIM}Vigilancia detenida{_RST}")
    return 0


# ─── Self-tests ────────────────────────────────────────────────────────────

def _self_test() -> None:
    import tempfile
    print("Tests de file_watcher.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "a.py").write_text("x = 1")
        (root / "b.js").write_text("const x = 1;")
        (root / "c.txt").write_text("ignored")

        # T1 — snapshot solo incluye extensiones vigiladas
        snap = snapshot(td, {"py", "js"})
        if "a.py" in snap and "b.js" in snap and "c.txt" not in snap:
            ok("file_watcher:snapshot_filters_ext")
        else:
            fail("file_watcher:snapshot_filters_ext", f"keys={list(snap.keys())}")

        # T2 — snapshot sin cambios → diff vacío
        snap2 = snapshot(td, {"py", "js"})
        diff = diff_snapshots(snap, snap2)
        if not diff["added"] and not diff["removed"] and not diff["modified"]:
            ok("file_watcher:diff_no_changes")
        else:
            fail("file_watcher:diff_no_changes", f"diff={diff}")

        # T3 — archivo nuevo detectado
        (root / "new.py").write_text("y = 2")
        snap3 = snapshot(td, {"py", "js"})
        diff3 = diff_snapshots(snap, snap3)
        if "new.py" in diff3["added"]:
            ok("file_watcher:new_file_detected")
        else:
            fail("file_watcher:new_file_detected", f"added={diff3['added']}")

        # T4 — modificación detectada
        (root / "a.py").write_text("x = 99")
        snap4 = snapshot(td, {"py", "js"})
        diff4 = diff_snapshots(snap, snap4)
        if "a.py" in diff4["modified"]:
            ok("file_watcher:modified_detected")
        else:
            fail("file_watcher:modified_detected", f"modified={diff4['modified']}")

        # T5 — save/load baseline
        bl_path = root / "test_baseline.json"
        save_baseline(snap, bl_path, td)
        loaded = load_baseline(bl_path)
        if loaded and "a.py" in loaded["snapshot"]:
            ok("file_watcher:save_load_baseline")
        else:
            fail("file_watcher:save_load_baseline", f"loaded={loaded}")

        # T6 — load de archivo inexistente → None
        missing = load_baseline(root / "no_existe.json")
        if missing is None:
            ok("file_watcher:load_missing_returns_none")
        else:
            fail("file_watcher:load_missing_returns_none", "no devolvió None")

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: raise SystemExit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        raise SystemExit(main(sys.argv[1:]))
