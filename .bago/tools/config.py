#!/usr/bin/env python3
"""
bago config — gestiona los valores configurables del pack BAGO.

Permite leer, actualizar y resetear claves de pack.json de forma segura,
con validación de tipos y sin editar el JSON manualmente.

Uso:
    bago config list              → muestra todas las claves del pack
    bago config get <clave>       → valor actual de una clave
    bago config set <clave> <val> → actualiza una clave
    bago config reset <clave>     → restaura al valor por defecto
    bago config --test            → tests integrados
"""

import argparse
import json
import sys
from pathlib import Path

BAGO_ROOT = Path(__file__).parent.parent
PACK_PATH = BAGO_ROOT / "pack.json"

DEFAULTS = {
    "name":         {"type": str,  "default": "mi_pack", "writable": False},
    "description":  {"type": str,  "default": "",        "writable": True},
    "mode":         {"type": str,  "default": "balanced","writable": True,
                     "choices": ["balanced","strict","lite"]},
    "language":     {"type": str,  "default": "es",      "writable": True,
                     "choices": ["es","en"]},
    "review_freq":  {"type": str,  "default": "weekly",  "writable": True,
                     "choices": ["daily","weekly","monthly"]},
    "team_size":    {"type": int,  "default": 1,         "writable": True},
    "notifications":{"type": bool, "default": True,      "writable": True},
    "auto_snapshot":{"type": bool, "default": False,     "writable": True},
    "lint_level":   {"type": str,  "default": "warn",    "writable": True,
                     "choices": ["off","warn","error"]},
}


def _load_pack() -> dict:
    return json.loads(PACK_PATH.read_text())


def _save_pack(pack: dict):
    PACK_PATH.write_text(json.dumps(pack, indent=2, ensure_ascii=False))


def _coerce(key: str, val_str: str):
    meta = DEFAULTS.get(key, {})
    t = meta.get("type", str)
    if t == bool:
        if val_str.lower() in ("true","1","yes","si","sí"):
            return True
        if val_str.lower() in ("false","0","no"):
            return False
        raise ValueError(f"'{val_str}' no es un booleano (true/false)")
    if t == int:
        try:
            return int(val_str)
        except ValueError:
            raise ValueError(f"'{val_str}' no es un entero")
    return val_str


def cmd_list(pack: dict):
    print("\n  Pack config — valores actuales\n")
    for key, meta in DEFAULTS.items():
        val = pack.get(key, meta["default"])
        writable = "rw" if meta.get("writable", True) else "ro"
        choices = f"  [{'/'.join(str(c) for c in meta['choices'])}]" if "choices" in meta else ""
        lock = "🔒" if not meta.get("writable", True) else "  "
        print(f"  {lock} {key:20s} = {str(val):<20s} ({writable}){choices}")
    print()


def cmd_get(pack: dict, key: str):
    if key not in DEFAULTS:
        print(f"Clave desconocida: {key}", file=sys.stderr)
        sys.exit(1)
    val = pack.get(key, DEFAULTS[key]["default"])
    print(val)


def cmd_set(pack: dict, key: str, val_str: str):
    if key not in DEFAULTS:
        print(f"Clave desconocida: {key}", file=sys.stderr)
        sys.exit(1)
    meta = DEFAULTS[key]
    if not meta.get("writable", True):
        print(f"'{key}' es de solo lectura", file=sys.stderr)
        sys.exit(1)
    val = _coerce(key, val_str)
    if "choices" in meta and val not in meta["choices"]:
        print(f"Valor inválido '{val}'. Opciones: {meta['choices']}", file=sys.stderr)
        sys.exit(1)
    old = pack.get(key, meta["default"])
    pack[key] = val
    _save_pack(pack)
    print(f"  {key}: {old} → {val}")


def cmd_reset(pack: dict, key: str):
    if key not in DEFAULTS:
        print(f"Clave desconocida: {key}", file=sys.stderr)
        sys.exit(1)
    meta = DEFAULTS[key]
    if not meta.get("writable", True):
        print(f"'{key}' es de solo lectura", file=sys.stderr)
        sys.exit(1)
    old = pack.get(key, meta["default"])
    pack[key] = meta["default"]
    _save_pack(pack)
    print(f"  {key}: {old} → {meta['default']} (default)")


def run_tests():
    import tempfile, os
    print("Ejecutando tests de config.py...")
    errors = 0

    def ok(name):
        print(f"  OK: {name}")

    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    # Temporary pack for tests
    tmp_pack = {"name": "test_pack", "mode": "balanced", "team_size": 1}

    # Test 1: _coerce bool
    try:
        assert _coerce("notifications", "true") is True
        assert _coerce("notifications", "false") is False
        ok("config:coerce_bool")
    except Exception as e:
        fail("config:coerce_bool", str(e))

    # Test 2: _coerce int
    try:
        assert _coerce("team_size", "5") == 5
        ok("config:coerce_int")
    except Exception as e:
        fail("config:coerce_int", str(e))

    # Test 3: _coerce invalid int
    try:
        _coerce("team_size", "abc")
        fail("config:coerce_invalid_int", "should have raised ValueError")
    except ValueError:
        ok("config:coerce_invalid_int")

    # Test 4: set / get round-trip on temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"name": "t", "mode": "balanced"}, f)
        tmp_path = f.name

    global PACK_PATH
    orig = PACK_PATH
    PACK_PATH = Path(tmp_path)
    try:
        pack = _load_pack()
        cmd_set(pack, "mode", "strict")
        pack2 = _load_pack()
        assert pack2.get("mode") == "strict", f"got {pack2.get('mode')}"
        ok("config:set_get_roundtrip")
    except Exception as e:
        fail("config:set_get_roundtrip", str(e))
    finally:
        PACK_PATH = orig
        os.unlink(tmp_path)

    # Test 5: cmd_get on real pack
    try:
        pack = _load_pack()
        import io
        from contextlib import redirect_stdout
        buf = io.StringIO()
        with redirect_stdout(buf):
            cmd_get(pack, "name")
        out = buf.getvalue().strip()
        assert out, "empty output"
        ok("config:get_name_real_pack")
    except Exception as e:
        fail("config:get_name_real_pack", str(e))

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(prog="bago config", add_help=False)
    sub = parser.add_subparsers(dest="action")

    sub.add_parser("list")
    sg = sub.add_parser("get")
    sg.add_argument("key")
    ss = sub.add_parser("set")
    ss.add_argument("key")
    ss.add_argument("value")
    sr = sub.add_parser("reset")
    sr.add_argument("key")

    parser.add_argument("--test", action="store_true")
    parser.add_argument("--help", "-h", action="store_true")

    args, extra = parser.parse_known_args()

    if args.test:
        run_tests()
        return
    if args.help or not args.action:
        print(__doc__)
        return

    pack = _load_pack()
    if args.action == "list":
        cmd_list(pack)
    elif args.action == "get":
        cmd_get(pack, args.key)
    elif args.action == "set":
        cmd_set(pack, args.key, args.value)
    elif args.action == "reset":
        cmd_reset(pack, args.key)


if __name__ == "__main__":
    main()