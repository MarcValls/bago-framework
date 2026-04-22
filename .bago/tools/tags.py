#!/usr/bin/env python3
"""
bago tags — sistema de etiquetas para sesiones y cambios BAGO.

Mantiene un índice de tags en state/tags_index.json.
Permite etiquetar sesiones y cambios, buscar por tag, y listar el vocabulario.

Uso:
    bago tags list                    → listar todos los tags con conteo
    bago tags add SES-ID tag1 tag2    → etiquetar una sesion
    bago tags find tag                → sesiones/cambios con ese tag
    bago tags suggest                 → sugerir tags basados en contenido
    bago tags --test                  → tests integrados
"""

import argparse
import json
import sys
from pathlib import Path
from collections import defaultdict

BAGO_ROOT = Path(__file__).parent.parent
STATE_DIR = BAGO_ROOT / "state"
SESSIONS_DIR = STATE_DIR / "sessions"
TAGS_INDEX = STATE_DIR / "tags_index.json"


def _load_index() -> dict:
    if TAGS_INDEX.exists():
        try:
            return json.loads(TAGS_INDEX.read_text())
        except Exception:
            pass
    return {"tags": {}, "entities": {}}


def _save_index(index: dict):
    TAGS_INDEX.write_text(json.dumps(index, indent=2, ensure_ascii=False))


def cmd_list(args):
    index = _load_index()
    tags = index.get("tags", {})
    if not tags:
        print("\n  (sin tags registrados)")
        print("  Añade: bago tags add SES-ID mi-tag\n")
        return

    sorted_tags = sorted(tags.items(), key=lambda x: -x[1]["count"])
    print(f"\n  Tags BAGO ({len(sorted_tags)} únicos)\n")
    print(f"  {'Tag':25s} {'Count':6s}  Entidades")
    print(f"  {'-'*25} {'-'*6}  {'-'*30}")
    for tag, info in sorted_tags[:30]:
        entities = info.get("entities", [])
        sample = ", ".join(entities[:3])
        if len(entities) > 3:
            sample += f" (+{len(entities)-3})"
        print(f"  {tag:25s} {info['count']:6d}  {sample}")
    print()


def cmd_add(args):
    if not args.entity_id or not args.tags:
        print("  ERROR: indica entidad ID y tags")
        sys.exit(1)

    index = _load_index()
    eid = args.entity_id
    new_tags = args.tags

    # Update entity → tags
    entities = index.setdefault("entities", {})
    if eid not in entities:
        entities[eid] = {"tags": []}
    entity_tags = entities[eid]["tags"]

    added = []
    for tag in new_tags:
        tag = tag.lower().strip().replace(" ", "-")
        if tag and tag not in entity_tags:
            entity_tags.append(tag)
            added.append(tag)

            # Update tags → entities
            tag_info = index.setdefault("tags", {}).setdefault(tag, {"count": 0, "entities": []})
            tag_info["count"] += 1
            if eid not in tag_info["entities"]:
                tag_info["entities"].append(eid)

    _save_index(index)
    if added:
        print(f"  Tags añadidos a {eid}: {', '.join(added)}")
    else:
        print(f"  (tags ya existentes, sin cambios)")


def cmd_find(args):
    if not args.tag:
        print("  ERROR: indica un tag")
        sys.exit(1)

    index = _load_index()
    tag = args.tag.lower().strip()
    tag_info = index.get("tags", {}).get(tag)

    if not tag_info:
        # Try partial match
        matches = [t for t in index.get("tags", {}) if tag in t]
        if matches:
            print(f"\n  Tag '{tag}' no exacto. Similares: {', '.join(matches)}")
        else:
            print(f"  Tag '{tag}' no encontrado")
        return

    entities = tag_info.get("entities", [])
    print(f"\n  Tag: #{tag}  ({len(entities)} entidades)\n")
    for e in entities:
        print(f"  · {e}")
    print()


def cmd_suggest(args):
    """Auto-suggest tags from session content."""
    sessions = []
    for f in sorted(SESSIONS_DIR.glob("SES-*.json")):
        try:
            s = json.loads(f.read_text())
            s["_file"] = f.stem
            sessions.append(s)
        except Exception:
            pass

    # Keywords → tag mappings
    KEYWORD_TAGS = {
        "python": "python",
        "javascript": "js",
        "typescript": "ts",
        "docker": "docker",
        "api": "api",
        "test": "testing",
        "debug": "debug",
        "bug": "bug",
        "refactor": "refactor",
        "docs": "docs",
        "documentation": "docs",
        "performance": "perf",
        "security": "security",
        "deploy": "deploy",
        "migration": "migration",
        "audit": "audit",
        "cosecha": "harvest",
        "explore": "exploration",
        "sprint": "sprint",
        "validate": "validation",
    }

    suggestions = defaultdict(set)
    for s in sessions:
        sid = s.get("session_id", s["_file"])
        text = " ".join([
            str(s.get("user_goal", "")),
            str(s.get("summary", "")),
            " ".join(str(d) for d in s.get("decisions", [])),
            " ".join(str(a) for a in s.get("artifacts", [])),
            s.get("selected_workflow", ""),
        ]).lower()

        for keyword, tag in KEYWORD_TAGS.items():
            if keyword in text:
                suggestions[sid].add(tag)

        # Workflow-based tags
        wf = s.get("selected_workflow", "")
        if wf:
            short = wf.replace("w_", "").replace("workflow_", "")[:8]
            suggestions[sid].add(f"wf-{short}")

    # Show top suggestions
    index = _load_index()
    existing = index.get("entities", {})

    to_show = [(sid, tags) for sid, tags in suggestions.items() if sid not in existing][:20]
    already = [(sid, tags) for sid, tags in suggestions.items() if sid in existing][:5]

    print(f"\n  Sugerencias de tags ({len(to_show)} sesiones sin etiquetar)\n")
    if to_show:
        for sid, tags in to_show[:10]:
            tag_str = " ".join(f"#{t}" for t in sorted(tags))
            print(f"  {sid}")
            print(f"    Sugeridos: {tag_str}")
            print(f"    Comando:   bago tags add {sid} {' '.join(sorted(tags))}")
            print()
    else:
        print("  (todas las sesiones ya están etiquetadas)")
    print()


def run_tests():
    import tempfile, shutil
    print("Ejecutando tests de tags.py...")
    errors = 0

    def ok(name):
        print(f"  OK: {name}")

    def fail(name, msg):
        nonlocal errors
        errors += 1
        print(f"  FAIL: {name} — {msg}")

    with tempfile.TemporaryDirectory() as tmp:
        # Patch TAGS_INDEX
        global TAGS_INDEX
        orig_index = TAGS_INDEX
        TAGS_INDEX = pathlib.Path(tmp) / "tags_index.json"

        # Test 1: empty index
        idx = _load_index()
        if idx == {"tags": {}, "entities": {}}:
            ok("tags:empty_index")
        else:
            fail("tags:empty_index", str(idx))

        # Test 2: add tags
        class FakeArgs:
            entity_id = "SES-T001"
            tags = ["python", "testing", "api"]
        cmd_add(FakeArgs())
        idx2 = _load_index()
        if "python" in idx2["tags"] and idx2["tags"]["python"]["count"] == 1:
            ok("tags:add_creates_entry")
        else:
            fail("tags:add_creates_entry", str(idx2["tags"]))

        # Test 3: entity appears in tag
        if "SES-T001" in idx2["tags"]["python"]["entities"]:
            ok("tags:entity_in_tag")
        else:
            fail("tags:entity_in_tag", str(idx2["tags"]["python"]))

        # Test 4: duplicate tag not counted twice
        cmd_add(FakeArgs())
        idx3 = _load_index()
        if idx3["tags"]["python"]["count"] == 1:
            ok("tags:no_duplicate")
        else:
            fail("tags:no_duplicate", f"count={idx3['tags']['python']['count']}")

        # Test 5: find returns entity
        class FindArgs:
            tag = "python"
        # Just verify the index lookup works
        tag_info = idx3.get("tags", {}).get("python")
        if tag_info and "SES-T001" in tag_info["entities"]:
            ok("tags:find_entity")
        else:
            fail("tags:find_entity", str(tag_info))

        TAGS_INDEX = orig_index

    total = 5
    passed = total - errors
    print(f"\n  {passed}/{total} tests pasaron")
    if errors:
        sys.exit(1)

import pathlib  # ensure available in run_tests scope

def main():
    parser = argparse.ArgumentParser(prog="bago tags", add_help=False)
    sub = parser.add_subparsers(dest="subcmd")

    sub.add_parser("list")

    p_add = sub.add_parser("add")
    p_add.add_argument("entity_id", nargs="?")
    p_add.add_argument("tags", nargs="*")

    p_find = sub.add_parser("find")
    p_find.add_argument("tag", nargs="?")

    sub.add_parser("suggest")

    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    if args.test:
        run_tests()
    elif args.subcmd == "add":
        cmd_add(args)
    elif args.subcmd == "find":
        cmd_find(args)
    elif args.subcmd == "suggest":
        cmd_suggest(args)
    else:
        cmd_list(args)


if __name__ == "__main__":
    main()