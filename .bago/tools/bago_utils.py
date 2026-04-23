#!/usr/bin/env python3
"""
bago_utils — Utilidades compartidas para todos los tools BAGO.

Proporciona:
  - print_ok / print_fail / print_skip — salida de tests consistente
  - run_inline_tests — runner estándar para flags --test
  - colored / dim / bold — helpers ANSI
  - load_json / save_json — con encoding y error handling
  - ensure_dir — crea directorio si no existe
  - format_timedelta — "2h 15m", "45s"
  - truncate — trunca texto a N chars con "…"

NO tiene dependencias externas.
"""
import json, sys
from datetime import timedelta
from pathlib import Path

# ─── ANSI ─────────────────────────────────────────────────────────────────────
BOLD="\033[1m"; DIM="\033[2m"; RESET="\033[0m"
RED="\033[31m"; GREEN="\033[32m"; YELLOW="\033[33m"; CYAN="\033[36m"
MAGENTA="\033[35m"

def colored(text: str, color: str) -> str:
    return f"{color}{text}{RESET}"

def bold(text: str) -> str:
    return f"{BOLD}{text}{RESET}"

def dim(text: str) -> str:
    return f"{DIM}{text}{RESET}"

# ─── Test helpers ─────────────────────────────────────────────────────────────
_test_errors: list = []

def reset_test_state():
    global _test_errors
    _test_errors = []

def print_ok(name: str, detail: str = ""):
    suffix = f" — {detail}" if detail else ""
    print(f"  OK: {name}{suffix}")

def print_fail(name: str, detail: str = ""):
    _test_errors.append(name)
    print(f"  FAIL: {name} — {detail}")

def print_skip(name: str, reason: str = ""):
    print(f"  SKIP: {name}" + (f" ({reason})" if reason else ""))

def finish_tests(total: int | None = None) -> int:
    """Print summary and return exit code. Call at end of --test block."""
    passed = (total or 0) - len(_test_errors) if total else "?"
    n_fail = len(_test_errors)
    print(f"\n  {passed}/{total or '?'} tests pasaron")
    return 0 if n_fail == 0 else 1

def run_inline_tests(test_fn, label: str = ""):
    """Standard --test runner. test_fn populates _test_errors via print_fail."""
    reset_test_state()
    banner = f"Ejecutando tests de {label}..." if label else "Ejecutando tests..."
    print(banner)
    test_fn()
    code = finish_tests()
    raise SystemExit(code)

# ─── JSON I/O ─────────────────────────────────────────────────────────────────
def load_json(path: Path | str, default=None):
    p = Path(path)
    if not p.exists():
        return default
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"{RED}✗ Error leyendo {p}: {e}{RESET}", file=sys.stderr)
        return default

def save_json(path: Path | str, data, indent: int = 2):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=indent, ensure_ascii=False) + "\n",
                 encoding="utf-8")

# ─── Path helpers ─────────────────────────────────────────────────────────────
def ensure_dir(path: Path | str) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p

# ─── Format helpers ───────────────────────────────────────────────────────────
def format_timedelta(td: timedelta) -> str:
    total = int(abs(td.total_seconds()))
    if total < 60:   return f"{total}s"
    if total < 3600: return f"{total//60}m {total%60:02d}s"
    h = total // 3600; m = (total % 3600) // 60
    return f"{h}h {m:02d}m"

def truncate(text: str, max_len: int = 60) -> str:
    return text if len(text) <= max_len else text[:max_len-1] + "…"

def pluralize(n: int, singular: str, plural: str | None = None) -> str:
    return f"{n} {singular if n == 1 else (plural or singular+'s')}"

# ─── Self-test ────────────────────────────────────────────────────────────────
def _run_self_tests():
    reset_test_state()
    assert colored("hi", RED).startswith("\033[31m"),  "colored"
    assert bold("x").startswith("\033[1m"),            "bold"
    assert dim("x").startswith("\033[2m"),             "dim"
    assert format_timedelta(timedelta(seconds=45)) == "45s"
    assert format_timedelta(timedelta(minutes=90)) == "1h 30m"
    assert truncate("hello world", 8) == "hello w…"
    assert truncate("short", 20) == "short"
    print_ok("utils:ansi_helpers")
    print_ok("utils:format_timedelta")
    print_ok("utils:truncate")
    tmp = Path("/tmp/bago_utils_test.json")
    save_json(tmp, {"x": 1})
    loaded = load_json(tmp)
    assert loaded == {"x": 1}
    tmp.unlink(missing_ok=True)
    print_ok("utils:json_round_trip")
    assert load_json("/nonexistent.json", "default") == "default"
    print_ok("utils:json_missing_default")

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--test", action="store_true")
    args = p.parse_args()
    if args.test:
        print("Ejecutando tests de bago_utils.py...")
        reset_test_state()
        _run_self_tests()
        code = finish_tests(5)
        raise SystemExit(code)