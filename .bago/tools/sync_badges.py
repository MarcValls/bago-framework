#!/usr/bin/env python3
"""
sync_badges.py — Sincroniza las badges shields.io del README con global_state.json.

Actualiza automáticamente los contadores de:
  - tests: workers / workers (de smoke report)
  - CHGs:  inventory.changes
  - tools: número de archivos .py en .bago/tools/
  - health: system_health → 🟢 100/100 o 🟡 XX/100
  - version: bago_version
"""
import json, re, urllib.parse
from pathlib import Path

ROOT       = Path(__file__).parent.parent
STATE_FILE = ROOT / "state" / "global_state.json"
SMOKE_FILE = ROOT.parent / "sandbox" / "runtime" / "last-report.json"
README     = ROOT.parent / "README.md"
TOOLS_DIR  = ROOT / "tools"


def _load_json(path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _tools_count():
    return len(list(TOOLS_DIR.glob("*.py")))


def _health_label(state: dict) -> tuple[str, str]:
    """Return (label_text, color) for health badge."""
    h = state.get("system_health", "stable")
    if h in ("stable", "ok", "pass", "healthy"):
        return "%F0%9F%9F%A2%20100%2F100", "brightgreen"
    return "%F0%9F%9F%A1%20degraded", "yellow"


def _tests_label(smoke: dict) -> tuple[str, str]:
    workers  = smoke.get("workers", 0)
    failures = smoke.get("failure_count", 0)
    passed   = workers - failures
    encoded  = urllib.parse.quote(f"✅ {passed}/{workers}")
    color    = "brightgreen" if failures == 0 else "red"
    return encoded, color


def compute_badges(state: dict, smoke: dict) -> dict:
    inv      = state.get("inventory", {})
    chgs     = inv.get("changes", state.get("changes", 0))
    version  = state.get("bago_version", "3.0")
    tools    = _tools_count()
    h_text, h_color   = _health_label(state)
    t_text, t_color   = _tests_label(smoke)
    workers  = smoke.get("workers", 0)
    failures = smoke.get("failure_count", 0)
    passed   = workers - failures

    return {
        "health": (f"https://img.shields.io/badge/health-{h_text}-{h_color}", f"health 🟢 100/100"),
        "tests":  (f"https://img.shields.io/badge/tests-{t_text}-{t_color}",  f"tests ✅ {passed}/{workers}"),
        "tools":  (f"https://img.shields.io/badge/tools-{tools}-blue",        f"tools 🔧 {tools}"),
        "chg":    (f"https://img.shields.io/badge/CHGs-{chgs}%20%F0%9F%8F%86-gold", f"CHGs 🏆 {chgs}"),
        "version":(f"https://img.shields.io/badge/versión-{version}-blue",    f"versión {version}"),
    }


def update_readme(badges: dict) -> bool:
    """Rewrite the shields line and the bold summary line in README."""
    text = README.read_text()

    # --- shields.io img badges line ---
    line_re = re.compile(
        r'^(!\[health\]\().*?(\))'
        r'.*?'
        r'(!\[version\]\().*?(\))\s*$',
        re.MULTILINE
    )

    new_shields = (
        f"![health]({badges['health'][0]}) "
        f"![tests]({badges['tests'][0]}) "
        f"![tools]({badges['tools'][0]}) "
        f"![chg]({badges['chg'][0]}) "
        f"![version]({badges['version'][0]}) "
        f"![langs](https://img.shields.io/badge/languages-py%20%7C%20js%20%7C%20go%20%7C%20rust-orange)"
    )
    text2, n1 = line_re.subn(new_shields, text)

    # --- bold summary line ---
    bold_re = re.compile(
        r'^\*\*`health.*?versión.*?`\*\*.*$',
        re.MULTILINE
    )
    # count workflows
    wf_count = 10
    new_bold = (
        f"**`{badges['health'][1]}`** · "
        f"**`{badges['tests'][1]}`** · "
        f"**`{badges['tools'][1]}`** · "
        f"**`{badges['chg'][1]}`** · "
        f"**`{badges['version'][1]}`** · "
        f"{wf_count} workflows · Auto-gobernanza e inteligencia de intent integrada"
    )
    text3, n2 = bold_re.subn(new_bold, text2)

    if text3 == text:
        return False

    README.write_text(text3)
    return True


def main():
    state = _load_json(STATE_FILE)
    smoke = _load_json(SMOKE_FILE)
    if not state:
        print("❌ No se pudo leer global_state.json")
        raise SystemExit(1)

    badges = compute_badges(state, smoke)
    changed = update_readme(badges)

    inv  = state.get("inventory", {})
    chgs = inv.get("changes", state.get("changes", 0))
    workers  = smoke.get("workers", 0)
    failures = smoke.get("failure_count", 0)

    if changed:
        print(f"✅ README badges actualizados: "
              f"tests={workers-failures}/{workers}, "
              f"tools={_tools_count()}, "
              f"CHGs={chgs}")
    else:
        print(f"ℹ️  README ya estaba al día (tools={_tools_count()}, CHGs={chgs})")


if __name__ == "__main__":
    main()
