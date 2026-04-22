#!/usr/bin/env python3
"""size_tracker.py — Herramienta #107: Tracking de tamaño de archivos y directorio.

Mide el tamaño de archivos y directorios, detecta archivos grandes,
y permite comparar contra un baseline para detectar crecimientos inesperados.

Uso:
    bago size-track [TARGET] [--top N] [--min-kb N] [--ext py,js]
                    [--save-baseline] [--compare-baseline] [--baseline FILE]
                    [--json] [--test]

Opciones:
    TARGET              Archivo o directorio (default: ./)
    --top N             Mostrar top N archivos más grandes (default: 20)
    --min-kb N          Solo archivos >= N KB (default: 0)
    --ext               Filtrar por extensiones (coma-separadas)
    --save-baseline     Guardar snapshot de tamaños como baseline
    --compare-baseline  Comparar con baseline guardado
    --baseline FILE     Ruta del baseline (default: .bago/state/size_baseline.json)
    --json              Output en JSON
    --test              Self-tests
"""
from __future__ import annotations

import json
import datetime
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional

BAGO_ROOT    = Path(__file__).parent.parent
DEFAULT_BASE = BAGO_ROOT / "state" / "size_baseline.json"

_RED  = "\033[0;31m"
_GRN  = "\033[0;32m"
_YEL  = "\033[0;33m"
_RST  = "\033[0m"
_BOLD = "\033[1m"
_DIM  = "\033[2m"

SKIP_DIRS = {"node_modules", "__pycache__", ".git", "venv", ".venv", ".mypy_cache"}


@dataclass
class FileEntry:
    path:    str
    size_b:  int
    size_kb: float
    ext:     str


def scan_dir(target: str, min_kb: float = 0,
             exts: Optional[set[str]] = None) -> list[FileEntry]:
    root = Path(target)
    files: list[FileEntry] = []
    if root.is_file():
        sz = root.stat().st_size
        if sz / 1024 >= min_kb:
            files.append(FileEntry(str(root), sz, round(sz/1024, 2), root.suffix.lstrip(".")))
        return files
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if any(d in f.parts for d in SKIP_DIRS):
            continue
        if exts and f.suffix.lstrip(".") not in exts:
            continue
        sz = f.stat().st_size
        if sz / 1024 < min_kb:
            continue
        files.append(FileEntry(
            path=str(f.relative_to(root)),
            size_b=sz, size_kb=round(sz/1024, 2),
            ext=f.suffix.lstrip(".")
        ))
    return files


def _fmt_size(size_b: int) -> str:
    if size_b >= 1_048_576:
        return f"{size_b/1_048_576:.1f}MB"
    if size_b >= 1024:
        return f"{size_b/1024:.1f}KB"
    return f"{size_b}B"


def _bar(size_b: int, max_b: int, width: int = 20) -> str:
    ratio  = min(size_b / max(max_b, 1), 1.0)
    filled = int(ratio * width)
    return "█" * filled + "░" * (width - filled)


def save_baseline(files: list[FileEntry], path: Path, target: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "saved_at": datetime.datetime.now().isoformat(),
        "target":   target,
        "total_kb": round(sum(f.size_kb for f in files), 2),
        "files":    {f.path: f.size_b for f in files},
    }
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_baseline(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def compare_baseline(files: list[FileEntry], old: dict) -> dict:
    old_files = old.get("files", {})
    curr_map  = {f.path: f.size_b for f in files}
    old_keys  = set(old_files.keys())
    curr_keys = set(curr_map.keys())

    added   = {k: curr_map[k] for k in curr_keys - old_keys}
    removed = {k: old_files[k] for k in old_keys - curr_keys}
    grown   = {k: (old_files[k], curr_map[k])
               for k in old_keys & curr_keys
               if curr_map[k] > old_files[k] * 1.5 and curr_map[k] - old_files[k] > 10240}

    total_old  = sum(old_files.values())
    total_curr = sum(curr_map.values())
    return {
        "added": added, "removed": removed, "grown": grown,
        "total_old_kb":  round(total_old / 1024, 2),
        "total_curr_kb": round(total_curr / 1024, 2),
        "delta_kb":      round((total_curr - total_old) / 1024, 2),
    }


def main(argv: list[str]) -> int:
    target     = "./"
    top_n      = 20
    min_kb     = 0.0
    ext_filter = None
    save_bl    = False
    cmp_bl     = False
    baseline   = DEFAULT_BASE
    as_json    = False

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--top" and i + 1 < len(argv):
            top_n = int(argv[i + 1]); i += 2
        elif a == "--min-kb" and i + 1 < len(argv):
            min_kb = float(argv[i + 1]); i += 2
        elif a == "--ext" and i + 1 < len(argv):
            ext_filter = {e.strip().lstrip(".") for e in argv[i+1].split(",")}; i += 2
        elif a == "--save-baseline":
            save_bl = True; i += 1
        elif a == "--compare-baseline":
            cmp_bl = True; i += 1
        elif a == "--baseline" and i + 1 < len(argv):
            baseline = Path(argv[i + 1]); i += 2
        elif a == "--json":
            as_json = True; i += 1
        elif not a.startswith("--"):
            target = a; i += 1
        else:
            i += 1

    files = sorted(scan_dir(target, min_kb, ext_filter), key=lambda f: -f.size_b)

    if save_bl:
        save_baseline(files, baseline, target)
        if as_json:
            print(json.dumps({"action": "saved", "files": len(files),
                               "total_kb": round(sum(f.size_kb for f in files), 2)}))
        else:
            print(f"{_GRN}✅ Baseline guardado:{_RST} {baseline}  ({len(files)} archivos)")
        return 0

    if cmp_bl:
        old = load_baseline(baseline)
        if not old:
            print(f"{_YEL}⚠️  Sin baseline. Usa --save-baseline primero{_RST}")
            return 1
        diff = compare_baseline(files, old)
        if as_json:
            print(json.dumps(diff, indent=2))
            return 1 if diff["grown"] else 0
        print(f"\n{_BOLD}Size Comparison{_RST}  (baseline: {old.get('saved_at','?')[:19]})\n")
        print(f"  Total anterior:  {diff['total_old_kb']} KB")
        print(f"  Total actual:    {diff['total_curr_kb']} KB")
        delta = diff['delta_kb']
        clr   = _RED if delta > 100 else (_YEL if delta > 0 else _GRN)
        print(f"  Delta:           {clr}{delta:+.2f} KB{_RST}\n")
        if diff["grown"]:
            print(f"  {_RED}Archivos que crecieron >50% y >10KB:{_RST}")
            for k, (old_b, new_b) in diff["grown"].items():
                print(f"    {k}: {_fmt_size(old_b)} → {_fmt_size(new_b)}")
        if diff["added"]:
            print(f"  {_GRN}Nuevos:{_RST}")
            for k, sz in list(diff["added"].items())[:5]:
                print(f"    +{k} ({_fmt_size(sz)})")
        if not diff["grown"] and not diff["added"]:
            print(f"  {_GRN}✅ Sin cambios significativos de tamaño{_RST}")
        return 1 if diff["grown"] else 0

    top = files[:top_n]
    total_kb = round(sum(f.size_kb for f in files), 2)
    max_b    = top[0].size_b if top else 1

    if as_json:
        print(json.dumps({
            "target": target, "total_files": len(files),
            "total_kb": total_kb,
            "top": [asdict(f) for f in top],
        }, indent=2))
        return 0

    print(f"\n{_BOLD}Size Tracker — {target}{_RST}")
    print(f"Archivos: {len(files)} | Total: {_fmt_size(int(total_kb*1024))}\n")
    for f in top:
        bar = _bar(f.size_b, max_b)
        clr = _RED if f.size_kb > 500 else (_YEL if f.size_kb > 100 else "")
        print(f"  {clr}{_fmt_size(f.size_b):8s}{_RST} {bar}  {f.path}")
    return 0


def _self_test() -> None:
    import tempfile
    print("Tests de size_tracker.py...")
    fails: list[str] = []
    def ok(n): print(f"  OK: {n}")
    def fail(n, m): fails.append(n); print(f"  FAIL: {n}: {m}")

    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "big.py").write_text("x " * 5000)
        (root / "small.js").write_text("a=1")
        (root / "ignore.txt").write_text("text")

        # T1 — scan_dir detecta archivos
        files = scan_dir(td)
        names = [f.path for f in files]
        if any("big.py" in n for n in names) and any("small.js" in n for n in names):
            ok("size_tracker:scan_detects_files")
        else:
            fail("size_tracker:scan_detects_files", f"names={names}")

        # T2 — extensión filtrada
        py_only = scan_dir(td, exts={"py"})
        if all(f.ext == "py" for f in py_only):
            ok("size_tracker:ext_filter")
        else:
            fail("size_tracker:ext_filter", f"exts={[f.ext for f in py_only]}")

        # T3 — min_kb filtra archivos pequeños
        large = scan_dir(td, min_kb=1)
        sizes = [f.size_kb for f in large]
        if all(s >= 1 for s in sizes):
            ok("size_tracker:min_kb_filter")
        else:
            fail("size_tracker:min_kb_filter", f"sizes={sizes}")

        # T4 — save/load baseline
        bl = root / "bl.json"
        save_baseline(files, bl, td)
        loaded = load_baseline(bl)
        if loaded and "files" in loaded and "total_kb" in loaded:
            ok("size_tracker:save_load_baseline")
        else:
            fail("size_tracker:save_load_baseline", f"loaded={loaded}")

        # T5 — compare_baseline: archivo nuevo detectado
        (root / "newfile.py").write_text("y = 1")
        new_files = scan_dir(td)
        diff = compare_baseline(new_files, loaded)
        if any("newfile.py" in k for k in diff["added"]):
            ok("size_tracker:compare_detects_added")
        else:
            fail("size_tracker:compare_detects_added", f"added={diff['added']}")

        # T6 — _fmt_size formatea correctamente
        if _fmt_size(500) == "500B" and "KB" in _fmt_size(2048) and "MB" in _fmt_size(2_000_000):
            ok("size_tracker:fmt_size_correct")
        else:
            fail("size_tracker:fmt_size_correct", f"500B={_fmt_size(500)}")

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
