#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bago_search.py - Motor de busqueda BAGO.

Busqueda full-text sobre sesiones, cambios, evidencias y decisiones.

Uso:
  python3 bago_search.py TERMINO [TERMINO2 ...]
  python3 bago_search.py TERMINO --type sessions
  python3 bago_search.py TERMINO --workflow W7
  python3 bago_search.py TERMINO --since 2026-04-01
  python3 bago_search.py TERMINO --role role_auditor
  python3 bago_search.py TERMINO --status closed
  python3 bago_search.py TERMINO --limit 20
  python3 bago_search.py --test
"""
from __future__ import annotations
import argparse, json, sys, re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"

SEARCH_TYPES = ("sessions", "changes", "evidences", "all")


def _load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _match(text: str, terms: list) -> bool:
    """Retorna True si todos los terminos estan en el texto (case insensitive)."""
    t = text.lower()
    return all(term.lower() in t for term in terms)


def _obj_to_text(obj: dict) -> str:
    """Convierte dict a texto plano recursivamente para busqueda."""
    parts = []
    for v in obj.values():
        if isinstance(v, str):
            parts.append(v)
        elif isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    parts.append(_obj_to_text(item))
        elif isinstance(v, dict):
            parts.append(_obj_to_text(v))
    return " ".join(parts)


def _date_ok(obj: dict, since: str) -> bool:
    """True si el objeto es mas reciente que since (YYYY-MM-DD)."""
    if not since:
        return True
    for key in ("created_at", "updated_at", "closed_at"):
        val = obj.get(key, "")
        if val and val[:10] >= since:
            return True
    return False


def _filter_session(obj: dict, workflow: str, role: str, status: str) -> bool:
    if workflow and workflow.lower() not in obj.get("selected_workflow", "").lower():
        return False
    if role:
        roles = obj.get("roles_activated", obj.get("roles", []))
        if isinstance(roles, list):
            if not any(role.lower() in r.lower() for r in roles):
                return False
    if status and obj.get("status", "") != status:
        return False
    return True


def _filter_change(obj: dict, status: str) -> bool:
    if status and obj.get("status", "") != status:
        return False
    return True


def search_sessions(terms: list, since="", workflow="", role="", status="", limit=20):
    results = []
    folder = STATE / "sessions"
    if not folder.exists():
        return results
    for f in sorted(folder.glob("*.json"), reverse=True):
        obj = _load_json(f)
        if not obj:
            continue
        if not _date_ok(obj, since):
            continue
        if not _filter_session(obj, workflow, role, status):
            continue
        text = _obj_to_text(obj)
        if _match(text, terms):
            results.append({
                "id": obj.get("session_id", f.stem),
                "type": "session",
                "title": obj.get("user_goal", obj.get("summary", "")),
                "workflow": obj.get("selected_workflow", ""),
                "status": obj.get("status", ""),
                "date": obj.get("created_at", "")[:10],
                "roles": obj.get("roles_activated", []),
                "decisions": obj.get("decisions", []),
                "snippets": _find_snippets(text, terms),
            })
            if len(results) >= limit:
                break
    return results


def search_changes(terms: list, since="", status="", limit=20):
    results = []
    folder = STATE / "changes"
    if not folder.exists():
        return results
    for f in sorted(folder.glob("BAGO-CHG-*.json"), reverse=True):
        obj = _load_json(f)
        if not obj:
            continue
        if not _date_ok(obj, since):
            continue
        if not _filter_change(obj, status):
            continue
        text = _obj_to_text(obj)
        if _match(text, terms):
            results.append({
                "id": obj.get("change_id", f.stem),
                "type": "change",
                "title": obj.get("title", ""),
                "change_type": obj.get("type", ""),
                "status": obj.get("status", ""),
                "date": obj.get("created_at", "")[:10],
                "snippets": _find_snippets(text, terms),
            })
            if len(results) >= limit:
                break
    return results


def search_evidences(terms: list, since="", limit=20):
    results = []
    folder = STATE / "evidences"
    if not folder.exists():
        return results
    for f in sorted(folder.glob("BAGO-EVD-*.json"), reverse=True):
        obj = _load_json(f)
        if not obj:
            continue
        if not _date_ok(obj, since):
            continue
        text = _obj_to_text(obj)
        if _match(text, terms):
            results.append({
                "id": obj.get("evidence_id", f.stem),
                "type": "evidence",
                "title": obj.get("title", obj.get("description", "")),
                "status": obj.get("status", ""),
                "date": obj.get("created_at", "")[:10],
                "snippets": _find_snippets(text, terms),
            })
            if len(results) >= limit:
                break
    return results


def _find_snippets(text: str, terms: list, window=60, max_snips=2) -> list:
    """Extrae fragmentos con contexto alrededor de los terminos encontrados."""
    snippets = []
    tl = text.lower()
    used_positions = set()
    for term in terms[:2]:  # max 2 terminos para snippets
        idx = tl.find(term.lower())
        while idx != -1 and len(snippets) < max_snips:
            if idx not in used_positions:
                start = max(0, idx - window)
                end = min(len(text), idx + len(term) + window)
                snip = text[start:end].replace(chr(10), " ").strip()
                if start > 0:
                    snip = "..." + snip
                if end < len(text):
                    snip = snip + "..."
                snippets.append(snip)
                used_positions.add(idx)
            idx = tl.find(term.lower(), idx + 1)
            if len(snippets) >= max_snips:
                break
    return snippets


def print_results(results: list, terms: list) -> None:
    if not results:
        print("  No se encontraron resultados.")
        return

    TYPE_ICON = {"session": "[S]", "change": "[C]", "evidence": "[E]"}
    STATUS_ICON = {"closed": "v", "validated": "v", "open": "o", "active": "o"}

    print()
    print("  Resultados ({}):".format(len(results)))
    print()

    for r in results:
        icon = TYPE_ICON.get(r["type"], "[?]")
        st = STATUS_ICON.get(r.get("status", ""), "-")
        date = r.get("date", "")
        rid = r["id"]
        title = r.get("title", "")[:70]
        workflow = r.get("workflow", r.get("change_type", ""))

        print("  {} [{}] {}  {}  {}".format(icon, st, rid, date, workflow))
        print("     {}".format(title))

        # Decisions for sessions
        decs = r.get("decisions", [])
        if decs:
            for d in decs[:2]:
                print("     > {}".format(d[:80]))

        # Snippets
        for snip in r.get("snippets", [])[:1]:
            # Highlight terms
            highlighted = snip
            for term in terms:
                idx = highlighted.lower().find(term.lower())
                if idx != -1:
                    highlighted = highlighted[:idx] + "**" + highlighted[idx:idx+len(term)] + "**" + highlighted[idx+len(term):]
                    break
            print("     ~ {}".format(highlighted[:100]))
        print()


def _run_tests():
    import tempfile, json
    print("  Ejecutando tests de bago_search...")

    # Test _match
    assert _match("hello world python", ["python", "hello"]) == True
    assert _match("hello world", ["python"]) == False
    assert _match("BAGO Framework", ["bago"]) == True

    # Test _obj_to_text
    obj = {"a": "foo", "b": ["bar", "baz"], "c": {"d": "qux"}}
    text = _obj_to_text(obj)
    assert "foo" in text and "bar" in text and "qux" in text

    # Test _find_snippets
    text = "Este es un texto de prueba con la palabra BAGO en medio de la oracion"
    snips = _find_snippets(text, ["BAGO"], window=20)
    assert len(snips) > 0
    assert "BAGO" in snips[0]

    # Test _date_ok
    obj_new = {"created_at": "2026-04-20T10:00:00Z"}
    obj_old = {"created_at": "2026-03-01T10:00:00Z"}
    assert _date_ok(obj_new, "2026-04-01") == True
    assert _date_ok(obj_old, "2026-04-01") == False
    assert _date_ok(obj_old, "") == True

    print("  OK: todos los tests pasaron (5/5)")


def main():
    p = argparse.ArgumentParser(description="Busqueda BAGO")
    p.add_argument("terms", nargs="*", help="Terminos de busqueda")
    p.add_argument("--type", choices=SEARCH_TYPES, default="all",
                   help="Tipo de objeto a buscar (default: all)")
    p.add_argument("--since", default="", metavar="YYYY-MM-DD",
                   help="Solo resultados desde esta fecha")
    p.add_argument("--workflow", default="", help="Filtrar sesiones por workflow")
    p.add_argument("--role", default="", help="Filtrar sesiones por rol")
    p.add_argument("--status", default="", help="Filtrar por status")
    p.add_argument("--limit", type=int, default=20, help="Max resultados (default: 20)")
    p.add_argument("--json", action="store_true", dest="json_out",
                   help="Salida en JSON")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    if args.test:
        _run_tests()
        return

    if not args.terms:
        p.print_help()
        sys.exit(0)

    results = []
    search_type = args.type

    if search_type in ("sessions", "all"):
        results += search_sessions(
            args.terms, since=args.since,
            workflow=args.workflow, role=args.role,
            status=args.status, limit=args.limit)

    if search_type in ("changes", "all"):
        results += search_changes(
            args.terms, since=args.since,
            status=args.status, limit=args.limit)

    if search_type in ("evidences", "all"):
        results += search_evidences(
            args.terms, since=args.since, limit=args.limit)

    # Sort by date desc
    results.sort(key=lambda r: r.get("date", ""), reverse=True)
    results = results[:args.limit]

    if args.json_out:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print_results(results, args.terms)


if __name__ == "__main__":
    main()
