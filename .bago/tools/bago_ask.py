#!/usr/bin/env python3
"""
bago_ask — Búsqueda en lenguaje natural sobre el historial BAGO.

Busca en: sesiones, decisiones, notas, changes (CHG), sprints, evidencias, notas de sesión.

Uso:
  bago ask "qué decidimos sobre hotspots"
  bago ask "errores en scan" --scope changes
  bago ask "sprint 3" --scope sprints
  bago ask --interactive
  bago ask --recent 5        → últimas 5 sesiones con resumen
"""
import argparse, json, re, sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"

# ─── Indexer ─────────────────────────────────────────────────────────────────

def load_corpus() -> list:
    """Load all searchable documents from BAGO state."""
    corpus = []

    def _add(source: str, doc_id: str, date: str, title: str, text: str):
        corpus.append({
            "source": source,
            "id":     doc_id,
            "date":   date,
            "title":  title,
            "text":   text,
            "searchable": f"{title} {text}".lower(),
        })

    # Sessions
    sessions_dir = STATE / "sessions"
    if sessions_dir.exists():
        for f in sorted(sessions_dir.glob("*.json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                text_parts = []
                for key in ("summary", "notes", "decisions", "description",
                            "what_happened", "context", "observations"):
                    v = d.get(key, "")
                    if isinstance(v, list):
                        text_parts.extend(str(x) for x in v)
                    elif v:
                        text_parts.append(str(v))
                _add("session", f.stem,
                     d.get("date", d.get("created_at", "")),
                     d.get("title", d.get("id", f.stem)),
                     " ".join(text_parts))
            except Exception:
                pass

    # Changes (CHG)
    changes_dir = STATE / "changes"
    if changes_dir.exists():
        for f in sorted(changes_dir.glob("*.json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                text = " ".join(filter(None, [
                    d.get("title", ""),
                    d.get("description", ""),
                    d.get("motivation", ""),
                    d.get("details", ""),
                    str(d.get("scope", "")),
                    str(d.get("affected_components", "")),
                ]))
                _add("change", f.stem,
                     d.get("created_at", d.get("date", "")),
                     d.get("title", d.get("change_id", f.stem)),
                     text)
            except Exception:
                pass

    # Sprints
    sprints_dir = STATE / "sprints"
    if sprints_dir.exists():
        for f in sorted(sprints_dir.glob("*.json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                goals = d.get("goals", [])
                if isinstance(goals, list):
                    goals_text = " ".join(str(g) for g in goals)
                else:
                    goals_text = str(goals)
                text = " ".join(filter(None, [
                    d.get("name", ""),
                    d.get("description", ""),
                    goals_text,
                    str(d.get("status", "")),
                ]))
                _add("sprint", f.stem,
                     d.get("start_date", d.get("created_at", "")),
                     d.get("name", f.stem),
                     text)
            except Exception:
                pass

    # Evidences
    evidences_dir = STATE / "evidences"
    if evidences_dir.exists():
        for f in sorted(evidences_dir.glob("*.json")):
            try:
                d = json.loads(f.read_text(encoding="utf-8"))
                text = " ".join(filter(None, [
                    d.get("title", ""),
                    d.get("description", ""),
                    str(d.get("findings", "")),
                    str(d.get("metrics", "")),
                ]))
                _add("evidence", f.stem,
                     d.get("date", d.get("created_at", "")),
                     d.get("title", f.stem),
                     text)
            except Exception:
                pass

    # Notes (bago notes tool)
    notes_file = STATE / "notes.json"
    if notes_file.exists():
        try:
            notes_data = json.loads(notes_file.read_text(encoding="utf-8"))
            notes_list = notes_data if isinstance(notes_data, list) else notes_data.get("notes", [])
            for n in notes_list:
                _add("note",
                     n.get("id", "note"),
                     n.get("date", n.get("created_at", "")),
                     n.get("content", "")[:60],
                     n.get("content", ""))
        except Exception:
            pass

    return corpus


# ─── Search engine ────────────────────────────────────────────────────────────

def tokenize(query: str) -> list:
    """Split query into tokens, normalize."""
    return [t.lower().strip() for t in re.split(r'\s+', query.strip()) if t]


def score_document(doc: dict, tokens: list) -> int:
    """Score a document against query tokens. Higher = better match."""
    searchable = doc["searchable"]
    score = 0
    for tok in tokens:
        if tok in searchable:
            score += 1
            # Title match = bonus
            if tok in doc.get("title", "").lower():
                score += 2
    return score


def search(corpus: list, query: str, scope: Optional[str] = None,
           top_n: int = 10) -> list:
    tokens = tokenize(query)
    if not tokens:
        return []

    results = []
    for doc in corpus:
        if scope and doc["source"] != scope:
            continue
        s = score_document(doc, tokens)
        if s > 0:
            results.append((s, doc))

    results.sort(key=lambda x: x[0], reverse=True)
    return [(s, d) for s, d in results[:top_n]]


# ─── Display ─────────────────────────────────────────────────────────────────

SOURCE_ICONS = {
    "session":  "📋",
    "change":   "🔧",
    "sprint":   "🏃",
    "evidence": "📊",
    "note":     "📝",
}

def display_results(results: list, query: str, verbose: bool = False):
    if not results:
        print(f"\n  No se encontraron resultados para: \"{query}\"")
        print("  Intenta con términos más generales o usa --scope para filtrar.")
        return

    print(f"\n  Resultados para: \"{query}\"  ({len(results)} encontrados)")
    print()

    for score, doc in results:
        icon  = SOURCE_ICONS.get(doc["source"], "•")
        date  = doc["date"][:10] if doc["date"] else "?"
        title = doc["title"][:70] if doc["title"] else doc["id"]
        src   = doc["source"].upper()
        print(f"  {icon} [{src}] {date}  {title}")
        print(f"     ID: {doc['id']}  |  Score: {score}")

        if verbose and doc["text"]:
            # Show snippet around first token match
            text   = doc["text"]
            tokens = [t for t in query.lower().split() if t]
            snippet = text[:200]
            for tok in tokens:
                idx = text.lower().find(tok)
                if idx >= 0:
                    start  = max(0, idx - 40)
                    end    = min(len(text), idx + 120)
                    snippet = ("..." if start > 0 else "") + text[start:end] + ("..." if end < len(text) else "")
                    break
            print(f"     …{snippet}…")
        print()


def show_recent(corpus: list, n: int):
    """Show N most recent items with dates."""
    # Sort by date desc
    dated = [(d.get("date", ""), d) for d in corpus if d.get("date")]
    dated.sort(key=lambda x: x[0], reverse=True)
    dated = dated[:n]

    print(f"\n  Últimas {n} entradas BAGO:")
    print()
    for date_str, doc in dated:
        icon  = SOURCE_ICONS.get(doc["source"], "•")
        date  = date_str[:10]
        title = doc["title"][:70]
        src   = doc["source"].upper()
        print(f"  {icon} [{src}] {date}  {title}")
    print()


# ─── Interactive mode ─────────────────────────────────────────────────────────

def interactive_mode(corpus: list):
    print("\n  bago ask — Modo interactivo")
    print("  Escribe una consulta en lenguaje natural. 'salir' para terminar.")
    print()
    while True:
        try:
            query = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not query:
            continue
        if query.lower() in ("salir", "exit", "quit", "q"):
            break
        results = search(corpus, query)
        display_results(results, query)


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        prog="bago ask",
        description="Búsqueda en lenguaje natural sobre historial BAGO.")
    p.add_argument("query", nargs="*", help="Consulta de búsqueda")
    p.add_argument("--scope", choices=["session","change","sprint","evidence","note"],
                   help="Limitar búsqueda a un tipo")
    p.add_argument("--top", type=int, default=10, help="Máximo de resultados (default: 10)")
    p.add_argument("--verbose", "-v", action="store_true", help="Mostrar extractos")
    p.add_argument("--recent", type=int, metavar="N",
                   help="Muestra N entradas más recientes sin buscar")
    p.add_argument("--interactive", "-i", action="store_true",
                   help="Modo interactivo")
    p.add_argument("--json", action="store_true", help="Salida JSON")
    p.add_argument("--test", action="store_true", help="Self-tests")
    args = p.parse_args()

    if args.test:
        _self_test()
        return

    corpus = load_corpus()

    if not corpus:
        print("  ℹ️  No se encontraron documentos BAGO para buscar.")
        print("     Asegúrate de estar en el directorio raíz del proyecto BAGO.")
        return

    if args.recent:
        show_recent(corpus, args.recent)
        return

    if args.interactive:
        interactive_mode(corpus)
        return

    if not args.query:
        p.print_help()
        print(f"\n  Corpus cargado: {len(corpus)} documentos")
        return

    query   = " ".join(args.query)
    results = search(corpus, query, scope=args.scope, top_n=args.top)

    if args.json:
        out = [{"score": s, "source": d["source"], "id": d["id"],
                "date": d["date"], "title": d["title"]} for s, d in results]
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return

    display_results(results, query, verbose=args.verbose)


def _self_test():
    print("Ejecutando self-tests de bago_ask.py...")
    errors = []

    # Test 1: load_corpus returns list
    corpus = load_corpus()
    if not isinstance(corpus, list):
        errors.append("load_corpus: not a list")
    else:
        print(f"  OK: load_corpus — {len(corpus)} documentos cargados")

    # Test 2: each doc has required keys
    required = {"source", "id", "title", "text", "searchable"}
    bad_docs = [d for d in corpus if not required.issubset(d.keys())]
    if bad_docs:
        errors.append(f"corpus docs missing keys: {len(bad_docs)} bad")
    else:
        print(f"  OK: todos los docs tienen keys requeridos")

    # Test 3: search finds something for broad query
    if corpus:
        results = search(corpus, "bago sprint")
        if not isinstance(results, list):
            errors.append("search: not a list")
        else:
            print(f"  OK: search('bago sprint') → {len(results)} resultados")

    # Test 4: tokenize
    toks = tokenize("Qué decidimos sobre  hotspots")
    if toks != ["qué", "decidimos", "sobre", "hotspots"]:
        errors.append(f"tokenize: unexpected {toks}")
    else:
        print("  OK: tokenize funciona")

    # Test 5: score_document
    doc = {"searchable": "bago sprint health code", "title": "sprint 004"}
    s = score_document(doc, ["sprint", "health"])
    if s < 2:
        errors.append(f"score_document: expected >=2, got {s}")
    else:
        print(f"  OK: score_document → {s}")

    n = 5
    print(f"\n  {n - len(errors)}/{n} tests pasaron")
    if errors:
        for e in errors: print(f"  FAIL: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    main()