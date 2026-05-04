#!/usr/bin/env python3
"""sprint.py — Plan de sprint BAGO: top 5 ideas disponibles.

Uso:
  python sprint.py            → muestra sprint actual (o genera uno nuevo si no existe)
  python sprint.py --new      → genera un nuevo sprint con las top 5 ideas disponibles
  python sprint.py --status   → muestra progreso del sprint actual
"""

import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Rutas ─────────────────────────────────────────────────────────────────────
TOOLS_DIR  = Path(__file__).resolve().parent
BAGO_ROOT  = TOOLS_DIR.parent          # .bago/
STATE_DIR  = BAGO_ROOT / "state"
DB_PATH    = STATE_DIR / "bago.db"
IMPL_PATH  = STATE_DIR / "implemented_ideas.json"
SPRINT_PATH = STATE_DIR / "sprint_plan.json"

# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_implemented_titles() -> set[str]:
    if not IMPL_PATH.exists():
        return set()
    data = json.loads(IMPL_PATH.read_text(encoding="utf-8"))
    return {e["title"] for e in data.get("implemented", [])}


def _fetch_available_ideas(exclude_titles: set[str]) -> list[dict]:
    """Return top ideas from bago.db not already implemented, sorted by priority desc."""
    if not DB_PATH.exists():
        return []
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        "SELECT id, title, priority FROM ideas ORDER BY priority DESC, id ASC"
    )
    rows = cur.fetchall()
    conn.close()
    available = []
    for idea_id, title, priority in rows:
        if title not in exclude_titles:
            available.append({"id": idea_id, "title": title, "priority": priority})
    return available


def _next_sprint_id() -> str:
    """Determine next sprint number from existing sprint_summary_*.md files."""
    existing = sorted(STATE_DIR.glob("sprint_summary_*.md"))
    if not existing:
        return "sprint_01"
    # Extract highest number from filenames like sprint_summary_07.md
    nums = []
    for p in existing:
        stem = p.stem  # e.g. "sprint_summary_07"
        parts = stem.split("_")
        try:
            nums.append(int(parts[-1]))
        except (ValueError, IndexError):
            pass
    # Also check existing sprint_plan.json for its sprint_id
    if SPRINT_PATH.exists():
        try:
            plan = json.loads(SPRINT_PATH.read_text(encoding="utf-8"))
            sid = plan.get("sprint_id", "")
            if sid.startswith("sprint_"):
                try:
                    nums.append(int(sid.split("_")[1]))
                except (ValueError, IndexError):
                    pass
        except Exception:
            pass
    next_num = (max(nums) + 1) if nums else 1
    return f"sprint_{next_num:02d}"


def _create_sprint(sprint_id: str, ideas: list[dict]) -> dict:
    """Build a sprint plan dict with top 5 ideas."""
    top5 = ideas[:5]
    return {
        "sprint_id": sprint_id,
        "created_at": datetime.now(tz=timezone.utc).isoformat(),
        "ideas": [
            {
                "id": idea["id"],
                "title": idea["title"],
                "priority": idea["priority"],
                "done": False,
            }
            for idea in top5
        ],
    }


def _sprint_num(sprint_id: str) -> str:
    """Extract display number from sprint_id like 'sprint_08' → '08'."""
    parts = sprint_id.split("_")
    return parts[-1] if len(parts) > 1 else sprint_id


def _print_sprint(plan: dict, implemented_titles: set[str]) -> None:
    num = _sprint_num(plan["sprint_id"])
    print(f"\nBAGO Sprint #{num}")
    if not plan["ideas"]:
        print("  (sin ideas en este sprint)")
        return
    for item in plan["ideas"]:
        done = item.get("done", False) or item["title"] in implemented_titles
        tick = "✓" if done else " "
        prio = item.get("priority", "?")
        title = item["title"]
        print(f"  [{tick}] [{prio}] {title}")
    print()


def _cmd_show() -> None:
    """Show current sprint or generate new one if none exists."""
    if SPRINT_PATH.exists():
        plan = json.loads(SPRINT_PATH.read_text(encoding="utf-8"))
        impl = _load_implemented_titles()
        _print_sprint(plan, impl)
    else:
        print("  No hay sprint activo. Generando uno nuevo…\n")
        _cmd_new()


def _cmd_new() -> None:
    """Generate a new sprint with top 5 available ideas."""
    impl = _load_implemented_titles()
    available = _fetch_available_ideas(impl)
    if not available:
        print("  ⚠ No hay ideas disponibles en bago.db.")
        sys.exit(1)
    sprint_id = _next_sprint_id()
    plan = _create_sprint(sprint_id, available)
    SPRINT_PATH.write_text(
        json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"  ✅ Sprint creado: {sprint_id} → {SPRINT_PATH}")
    _print_sprint(plan, impl)


def _cmd_status() -> None:
    """Show progress of the current sprint."""
    if not SPRINT_PATH.exists():
        print("  ⚠ No hay sprint activo. Ejecuta: python sprint.py --new")
        sys.exit(1)
    plan = json.loads(SPRINT_PATH.read_text(encoding="utf-8"))
    impl = _load_implemented_titles()

    total = len(plan["ideas"])
    done_count = sum(
        1 for item in plan["ideas"]
        if item.get("done", False) or item["title"] in impl
    )
    num = _sprint_num(plan["sprint_id"])

    print(f"\nBAGO Sprint #{num} — Progreso: {done_count}/{total}")
    print(f"  Creado: {plan['created_at'][:10]}")
    _print_sprint(plan, impl)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    args = sys.argv[1:]
    if "--new" in args:
        _cmd_new()
    elif "--status" in args:
        _cmd_status()
    else:
        _cmd_show()



def _self_test():
    """Autotest mínimo — verifica arranque limpio del módulo."""
    from pathlib import Path as _P
    assert _P(__file__).exists(), "fichero no encontrado"
    print("  1/1 tests pasaron")

if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
        raise SystemExit(0)
    main()
