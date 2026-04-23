#!/usr/bin/env python3
"""
context_detector.py — BAGO ESCENARIO-003
Detecta señales de madurez cognitiva y técnica en el workspace.
Emite un veredicto: HARVEST / WATCH / CLEAN

Uso:
  python3 .bago/tools/context_detector.py
  python3 .bago/tools/context_detector.py --json
  python3 .bago/tools/context_detector.py --watch  (monitoreo continuo)
"""

import json, os, re, subprocess, sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

# ─── Configuración ────────────────────────────────────────────────────────────
BAGO_ROOT   = Path(__file__).resolve().parent.parent
REPO_ROOT   = BAGO_ROOT.parent
STATE_DIR   = BAGO_ROOT / "state"
SESSIONS    = STATE_DIR / "sessions"
CHANGES     = STATE_DIR / "changes"

# Keywords cognitivas que indican pensamiento maduro
COGNITIVE_KEYWORDS = [
    r"\bdecid[íi]\b",
    r"\bdescarto\b", r"\bdescartamos\b", r"\bdescartado\b",
    r"\bmejor opci[oó]n\b",
    r"\bla soluci[oó]n\b", r"\bes mejor\b",
    r"\bno vale\b", r"\bno sirve\b",
    r"\bfrente a\b", r"\bcomparado con\b", r"\bvs\b",
    r"\bpor tanto\b", r"\bpor lo tanto\b", r"\bconcluyo\b",
    r"\bpreferible\b", r"\boptamos\b",
    r"\bproblema resuelto\b", r"\bya funciona\b",
    r"\bel siguiente paso\b", r"\bnext step\b",
]

HARVEST_THRESHOLD = 2   # señales de peso alto mínimas para sugerir cosecha
SKIP_DIRS = {
    ".bago", ".git", "node_modules", "dist", "build", "coverage",
    ".next", ".turbo", ".venv", "venv", "__pycache__", ".pytest_cache",
    "TESTS", "RELEASE", "bago-viewer", "cleanversion",
}
SKIP_FILENAMES = {"CHANGELOG.md", "CHECKSUMS.sha256", "TREE.txt"}
MAX_FILE_BYTES = 256_000


# ─── Señales técnicas ─────────────────────────────────────────────────────────

def _git_modified_files():
    """Ficheros modificados en el repo desde el último commit."""
    try:
        r = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, timeout=5
        )
        files = [f.strip() for f in r.stdout.splitlines() if f.strip()]
        # También ficheros sin stage
        r2 = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "status", "--short"],
            capture_output=True, text=True, timeout=5
        )
        for line in r2.stdout.splitlines():
            fname = line[3:].strip().strip('"')
            if fname and fname not in files:
                files.append(fname)
        return files
    except Exception:
        return []


def _registered_chg_files():
    """Ficheros ya cubiertos por algún CHG aplicado."""
    covered = set()
    for f in CHANGES.glob("*.json"):
        try:
            d = json.loads(f.read_text())
            for comp in d.get("affected_components", []):
                covered.add(comp)
        except Exception:
            pass
    return covered


def _unregistered_files():
    """Ficheros modificados que no están en ningún CHG."""
    modified = _git_modified_files()
    covered = _registered_chg_files()
    unregistered = []
    for mf in modified:
        # Comparar por sufijo (los CHG guardan rutas relativas a .bago)
        if not any(mf.endswith(c) or c.endswith(mf) for c in covered):
            unregistered.append(mf)
    return unregistered


def _commits_without_session():
    """Número de commits recientes sin sesión BAGO asociada.
    Un commit se considera cubierto si:
      1. El session_id aparece en el mensaje del commit, O
      2. El commit fue realizado durante el período activo de una sesión BAGO.
    """
    try:
        # Commits con timestamps (usar | como separador para evitar split por espacio)
        r = subprocess.run(
            ["git", "-C", str(REPO_ROOT), "log", "--format=%H|%aI|%s", "-10"],
            capture_output=True, text=True, timeout=5
        )
        lines = r.stdout.strip().splitlines()

        # Rangos temporales de sesiones BAGO
        sessions = []
        session_ids = set()
        for f in SESSIONS.glob("*.json"):
            try:
                d = json.loads(f.read_text())
                sid = d.get("session_id", "")
                session_ids.add(sid)
                ca = d.get("created_at") or d.get("updated_at")
                ua = d.get("closed_at") or d.get("updated_at") or ca
                if ca:
                    sessions.append((
                        datetime.fromisoformat(ca.replace("Z", "+00:00")),
                        datetime.fromisoformat(ua.replace("Z", "+00:00")) if ua else None
                    ))
            except Exception:
                pass

        # Buffer de 30 minutos: commits justo después del cierre de sesión también cuentan
        SESSION_BUFFER = timedelta(minutes=30)

        orphan = 0
        for line in lines:
            parts = line.split("|", 2)
            if len(parts) < 3:
                continue
            sha, ts_str, msg = parts[0], parts[1], parts[2]
            # Check 1: session_id en el mensaje
            if any(sid in msg for sid in session_ids if sid):
                continue
            # Check 2: commit dentro del período de una sesión (±buffer)
            try:
                commit_dt = datetime.fromisoformat(ts_str)
                covered = False
                for (ses_start, ses_end) in sessions:
                    effective_end = (ses_end or ses_start) + SESSION_BUFFER
                    if ses_start <= commit_dt <= effective_end:
                        covered = True
                        break
                if covered:
                    continue
            except Exception:
                pass
            orphan += 1

        return orphan
    except Exception:
        return 0


# ─── Señales cognitivas ───────────────────────────────────────────────────────

def _scan_cognitive(max_files=40, extensions=(".md", ".txt")):
    """
    Busca keywords cognitivas en ficheros de notas/documentación recientes.
    Solo escanea .md y .txt — el código fuente (.py, .ts, .js) no es fuente cognitiva.
    Devuelve lista de (fichero, keyword_encontrada, fragmento).
    """
    hits = []
    candidates = []

    # Rutas que no contienen señales cognitivas del usuario
    COGNITIVE_SKIP_PREFIXES = (
        str(BAGO_ROOT / "state") + "/",
        str(BAGO_ROOT / "docs") + "/",
        str(REPO_ROOT / "TESTS") + "/",
        str(REPO_ROOT / "RELEASE") + "/",
        str(REPO_ROOT / "bago-viewer") + "/",
    )
    COGNITIVE_SKIP_NAMES = {"CHANGELOG.md", "CHECKSUMS.sha256", "TREE.txt"}

    def _is_cognitive_candidate(path: Path) -> bool:
        s = str(path)
        if path.name in COGNITIVE_SKIP_NAMES:
            return False
        return not any(s.startswith(pfx) for pfx in COGNITIVE_SKIP_PREFIXES)

    # Ficheros modificados primero (excluyendo state/ y docs/ del framework)
    for mf in _git_modified_files():
        p = REPO_ROOT / mf
        if p.exists() and p.suffix in extensions and _is_cognitive_candidate(p):
            candidates.append(p)

    # Completar con ficheros recientes si hacen falta, evitando directorios pesados.
    if len(candidates) < max_files:
        recent_files = []
        for root, dirnames, filenames in os.walk(REPO_ROOT):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for filename in filenames:
                if filename in SKIP_FILENAMES:
                    continue
                path = Path(root) / filename
                if path.suffix not in extensions:
                    continue
                if path in candidates:
                    continue
                if not _is_cognitive_candidate(path):
                    continue
                try:
                    stat = path.stat()
                except Exception:
                    continue
                if stat.st_size > MAX_FILE_BYTES:
                    continue
                recent_files.append((stat.st_mtime, path))
        for _, path in sorted(recent_files, key=lambda item: item[0], reverse=True):
            candidates.append(path)
            if len(candidates) >= max_files:
                break

    for p in candidates:
        try:
            if p.stat().st_size > MAX_FILE_BYTES:
                continue
            text = p.read_text(errors="ignore")
            for pattern in COGNITIVE_KEYWORDS:
                for m in re.finditer(pattern, text, re.IGNORECASE):
                    start = max(0, m.start() - 40)
                    fragment = text[start: m.end() + 40].replace("\n", " ").strip()
                    # Ignorar ocurrencias de "vs" dentro de celdas de tabla Markdown
                    if m.group().lower() == "vs" and re.search(r"\|[^|]*\bvs\b[^|]*\|", fragment, re.IGNORECASE):
                        break
                    hits.append({"file": str(p.relative_to(REPO_ROOT)),
                                 "keyword": m.group(), "fragment": fragment})
                    break  # una hit por patrón por fichero
        except Exception:
            pass
    return hits


def _detect_comparisons(cognitive_hits):
    """Detecta si hay al menos 1 alternativa comparada en los hits (solo en notas, no en código o tablas)."""
    comparison_patterns = [r"\bvs\b", r"\bfrente a\b", r"\bcomparado con\b",
                            r"\bmejor que\b", r"\bpeor que\b"]
    for h in cognitive_hits:
        if h.get("file", "").endswith(".py"):
            continue  # Las señales cognitivas no vienen de código Python
        fragment = h["fragment"]
        # Ignorar "vs" en celdas de tabla Markdown (rodeado de pipes)
        if re.search(r"\|[^|]*\bvs\b[^|]*\|", fragment):
            continue
        for p in comparison_patterns:
            if re.search(p, fragment, re.IGNORECASE):
                return True
    return False


def _detect_discards(cognitive_hits):
    """Detecta si hay al menos 1 descarte explícito (solo en notas, no en código)."""
    discard_patterns = [r"\bdescart", r"\bno vale\b", r"\bno sirve\b",
                        r"\babandon", r"\brechaz"]
    for h in cognitive_hits:
        if h.get("file", "").endswith(".py"):
            continue  # Los print("RECHAZADA") de código no son señales cognitivas
        for p in discard_patterns:
            if re.search(p, h["fragment"], re.IGNORECASE):
                return True
    return False


# ─── Motor de señales ─────────────────────────────────────────────────────────

def evaluate():
    """
    Evalúa todas las señales y devuelve un dict con el veredicto.
    """
    unregistered = _unregistered_files()
    orphan_commits = _commits_without_session()
    cognitive_hits = _scan_cognitive()
    has_comparison = _detect_comparisons(cognitive_hits)
    has_discard    = _detect_discards(cognitive_hits)
    has_keywords   = len(cognitive_hits) > 0

    signals = []

    # Señales técnicas
    if len(unregistered) >= 3:
        signals.append({"id": "unregistered_files", "weight": "high",
                         "desc": f"{len(unregistered)} ficheros sin CHG asociado",
                         "detail": unregistered[:5]})
    elif len(unregistered) >= 1:
        signals.append({"id": "unregistered_files_low", "weight": "medium",
                         "desc": f"{len(unregistered)} fichero(s) sin CHG",
                         "detail": unregistered})

    if orphan_commits >= 1:
        signals.append({"id": "orphan_commits", "weight": "medium",
                         "desc": f"{orphan_commits} commit(s) sin sesión BAGO"})

    # Señales cognitivas
    if has_comparison:
        signals.append({"id": "comparison_detected", "weight": "very_high",
                         "desc": "Alternativa comparada detectada en texto reciente"})
    if has_discard:
        signals.append({"id": "discard_detected", "weight": "very_high",
                         "desc": "Descarte explícito detectado en texto reciente"})
    if has_keywords and not has_comparison and not has_discard:
        signals.append({"id": "cognitive_keywords", "weight": "high",
                         "desc": f"{len(cognitive_hits)} keyword(s) de pensamiento maduro detectada(s)"})

    # Contar señales de peso alto
    high_signals = [s for s in signals if s["weight"] in ("high", "very_high")]
    score = len(high_signals)

    if score >= HARVEST_THRESHOLD:
        verdict = "HARVEST"
        message = "Contexto suficiente — hay valor para cosechar ahora."
    elif signals:
        verdict = "WATCH"
        message = "Señales débiles — continúa explorando, el contexto madura."
    else:
        verdict = "CLEAN"
        message = "Sin señales. No hay nada que cosechar todavía."

    return {
        "verdict": verdict,
        "message": message,
        "score": score,
        "threshold": HARVEST_THRESHOLD,
        "signals": signals,
        "cognitive_hits": cognitive_hits[:5],
        "unregistered_files": unregistered,
        "evaluated_at": datetime.now(timezone.utc).isoformat()
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _bar(score, threshold, width=20):
    filled = min(int(width * score / max(threshold * 1.5, 1)), width)
    return "█" * filled + "░" * (width - filled)


def print_report(result):
    v = result["verdict"]
    icon = {"HARVEST": "🌾", "WATCH": "👁️ ", "CLEAN": "✅"}.get(v, "?")
    color_open  = {"HARVEST": "\033[93m", "WATCH": "\033[96m", "CLEAN": "\033[92m"}.get(v, "")
    color_close = "\033[0m"

    print()
    print("╔══════════════════════════════════════════╗")
    print(f"║   BAGO · Context Detector                ║")
    print("╠══════════════════════════════════════════╣")
    print(f"║  {icon} {color_open}{v:<10}{color_close}  {result['message'][:28]:<28} ║")
    bar = _bar(result["score"], result["threshold"])
    print(f"║  Score: {result['score']}/{result['threshold']}  [{bar}]  ║")
    print("╠══════════════════════════════════════════╣")

    if result["signals"]:
        print("║  Señales detectadas:                     ║")
        for s in result["signals"]:
            w = {"very_high": "🔴", "high": "🟠", "medium": "🟡"}.get(s["weight"], "⚪")
            desc = s["desc"][:36]
            print(f"║    {w} {desc:<36} ║")
    else:
        print("║  Sin señales activas.                    ║")

    if result["cognitive_hits"]:
        print("╠══════════════════════════════════════════╣")
        print("║  Hits cognitivos (muestra):               ║")
        for h in result["cognitive_hits"][:3]:
            kw = h["keyword"][:14]
            frag = h["fragment"][:26]
            print(f"║    «{kw}» … {frag:<26} ║")

    print("╚══════════════════════════════════════════╝")

    if v == "HARVEST":
        print()
        print("  → Ejecuta:  python3 .bago/tools/cosecha.py")
    print()


if __name__ == "__main__":
    import time

    if "--watch" in sys.argv:
        interval = 60
        print(f"Modo watch — comprobando cada {interval}s. Ctrl+C para salir.")
        while True:
            result = evaluate()
            if result["verdict"] == "HARVEST":
                print_report(result)
            else:
                print(f"\r[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {result['verdict']} "
                      f"(score={result['score']}/{result['threshold']}) — "
                      f"{result['message'][:50]}   ", end="", flush=True)
            time.sleep(interval)
    elif "--json" in sys.argv:
        print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
    else:
        result = evaluate()
        print_report(result)
