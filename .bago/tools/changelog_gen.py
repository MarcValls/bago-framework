#!/usr/bin/env python3
"""changelog_gen.py — Herramienta #101: Generador de CHANGELOG desde git log.

Analiza el historial git del repositorio y produce un CHANGELOG.md estructurado
agrupando commits por tipo (feat/fix/chore/docs/refactor/test) y por versión/tag.

Uso:
    bago changelog-gen [--since TAG|SHA|DATE] [--out FILE] [--format md|html]
                       [--max N] [--no-body] [--test]

Opciones:
    --since      Desde qué punto (tag, SHA o fecha ISO). Default: todos los commits.
    --out        Guardar en archivo (default: stdout)
    --format     md (default) | html
    --max        Máximo de commits (default: 200)
    --no-body    Sin cuerpo de commit, solo summary
    --test       Self-tests
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import datetime
from pathlib import Path
from collections import defaultdict
from typing import Optional

BAGO_ROOT = Path(__file__).parent.parent

_GREEN = "\033[0;32m"
_RST   = "\033[0m"

# Conventional commits prefix → grupo legible
TYPE_MAP = {
    "feat":     "✨ Nuevas Funcionalidades",
    "fix":      "🐛 Correcciones",
    "docs":     "📝 Documentación",
    "refactor": "♻️  Refactor",
    "test":     "🧪 Tests",
    "perf":     "⚡ Rendimiento",
    "chore":    "🔧 Chore / Mantenimiento",
    "ci":       "🤖 CI/CD",
    "style":    "💄 Estilo",
    "build":    "📦 Build",
    "revert":   "⏪ Revertidos",
    "other":    "🗂️  Otros",
}

COMMIT_RE = re.compile(
    r'^(?P<type>feat|fix|docs|refactor|test|perf|chore|ci|style|build|revert)'
    r'(?:\((?P<scope>[^)]+)\))?(?P<breaking>!)?:\s*(?P<desc>.+)',
    re.IGNORECASE
)


def _git_log(since: Optional[str], max_commits: int, cwd: str) -> list[dict]:
    """Ejecuta git log y devuelve lista de commits parseados."""
    fmt = "%H%n%h%n%D%n%ai%n%an%n%s%n%b%n---COMMIT_END---"
    cmd = ["git", "--no-pager", "log", f"--pretty=format:{fmt}", f"-{max_commits}"]
    if since:
        cmd.append(f"{since}..HEAD")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=cwd)
        return _parse_git_output(r.stdout)
    except Exception:
        return []


def _parse_git_output(raw: str) -> list[dict]:
    commits = []
    for block in raw.split("---COMMIT_END---"):
        lines = block.strip().splitlines()
        if len(lines) < 5:
            continue
        sha_full = lines[0].strip()
        sha_short = lines[1].strip()
        refs     = lines[2].strip()
        date     = lines[3].strip()[:10]  # solo YYYY-MM-DD
        author   = lines[4].strip()
        subject  = lines[5].strip() if len(lines) > 5 else ""
        body     = "\n".join(lines[6:]).strip() if len(lines) > 6 else ""

        # Detectar tags
        tags = re.findall(r'tag:\s*([\w.\-]+)', refs)

        # Parse conventional commit
        m = COMMIT_RE.match(subject)
        if m:
            ctype    = m.group("type").lower()
            scope    = m.group("scope") or ""
            breaking = bool(m.group("breaking"))
            desc     = m.group("desc")
        else:
            ctype    = "other"
            scope    = ""
            breaking = False
            desc     = subject

        commits.append({
            "sha": sha_full, "short": sha_short, "tags": tags,
            "date": date, "author": author,
            "type": ctype, "scope": scope, "breaking": breaking,
            "desc": desc, "body": body,
        })
    return commits


def _group_by_version(commits: list[dict]) -> list[tuple[str, list[dict]]]:
    """Agrupa commits por versión (tag). Unreleased si no hay tag."""
    groups: list[tuple[str, list[dict]]] = []
    current_version = "Unreleased"
    current_group: list[dict] = []

    for c in commits:
        if c["tags"]:
            if current_group:
                groups.append((current_version, current_group))
            current_version = c["tags"][0]
            current_group = [c]
        else:
            current_group.append(c)

    if current_group:
        groups.append((current_version, current_group))

    return groups


def generate_markdown(commits: list[dict], title: str = "CHANGELOG",
                      include_body: bool = True) -> str:
    groups = _group_by_version(commits)
    now    = datetime.datetime.now().strftime("%Y-%m-%d")
    lines  = [f"# {title}\n", f"*Generado automáticamente — {now}*\n", "---\n"]

    for version, group in groups:
        # Fecha del primer commit del grupo
        date = group[0]["date"] if group else now
        lines.append(f"\n## [{version}] — {date}\n")

        # Agrupar por tipo
        by_type: dict[str, list[dict]] = defaultdict(list)
        for c in group:
            by_type[c["type"]].append(c)

        # Breaking changes primero
        breaking = [c for cs in by_type.values() for c in cs if c["breaking"]]
        if breaking:
            lines.append("### ⚠️ BREAKING CHANGES\n")
            for c in breaking:
                scope_str = f"**{c['scope']}**: " if c["scope"] else ""
                lines.append(f"- {scope_str}{c['desc']} (`{c['short']}`)")
            lines.append("")

        # Por tipo
        for ctype, label in TYPE_MAP.items():
            entries = by_type.get(ctype, [])
            if not entries:
                continue
            lines.append(f"### {label}\n")
            for c in entries:
                scope_str = f"**{c['scope']}**: " if c["scope"] else ""
                lines.append(f"- {scope_str}{c['desc']} (`{c['short']}`) — {c['author']}")
                if include_body and c["body"]:
                    for bl in c["body"].splitlines():
                        if bl.strip():
                            lines.append(f"  > {bl.strip()}")
            lines.append("")

    lines.append("\n---\n*Generado con `bago changelog-gen`*\n")
    return "\n".join(lines)


def generate_html(commits: list[dict], title: str = "CHANGELOG") -> str:
    md = generate_markdown(commits, title, include_body=False)
    rows = []
    for c in commits[:100]:
        icon = {"feat": "✨", "fix": "🐛", "docs": "📝", "chore": "🔧"}.get(c["type"], "🗂️")
        rows.append(
            f"<tr><td><code>{c['short']}</code></td>"
            f"<td>{c['date']}</td>"
            f"<td>{icon} {c['type']}</td>"
            f"<td>{c['desc'][:80]}</td>"
            f"<td>{c['author']}</td></tr>"
        )
    table = (
        "<table><thead><tr><th>SHA</th><th>Fecha</th><th>Tipo</th>"
        "<th>Descripción</th><th>Autor</th></tr></thead>"
        "<tbody>" + "".join(rows) + "</tbody></table>"
    ) if rows else ""

    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"><title>{title}</title>
<style>
body{{font-family:-apple-system,sans-serif;max-width:1100px;margin:40px auto;padding:0 20px;}}
h1{{color:#2c3e50;border-bottom:2px solid #3498db;padding-bottom:12px;}}
table{{border-collapse:collapse;width:100%;}}
th{{background:#2c3e50;color:white;padding:8px 12px;text-align:left;}}
td{{padding:6px 12px;border-bottom:1px solid #ddd;}}
code{{background:#ecf0f1;padding:2px 6px;border-radius:3px;}}
</style></head>
<body><h1>📋 {title}</h1>{table}
<hr><small>Generado con BAGO Framework</small></body></html>"""


# ─── CLI ───────────────────────────────────────────────────────────────────

def main(argv: list[str]) -> int:
    since    = None
    out_file = None
    fmt      = "md"
    max_c    = 200
    no_body  = False
    cwd      = "."

    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--since" and i + 1 < len(argv):
            since = argv[i + 1]; i += 2
        elif a == "--out" and i + 1 < len(argv):
            out_file = argv[i + 1]; i += 2
        elif a == "--format" and i + 1 < len(argv):
            fmt = argv[i + 1]; i += 2
        elif a == "--max" and i + 1 < len(argv):
            max_c = int(argv[i + 1]); i += 2
        elif a == "--no-body":
            no_body = True; i += 1
        elif not a.startswith("--"):
            cwd = a; i += 1
        else:
            i += 1

    commits = _git_log(since, max_c, cwd)
    if not commits:
        print("No se encontraron commits.", file=sys.stderr)
        return 1

    if fmt == "html":
        content = generate_html(commits)
    else:
        content = generate_markdown(commits, include_body=not no_body)

    if out_file:
        Path(out_file).write_text(content, encoding="utf-8")
        print(f"{_GREEN}✅ CHANGELOG guardado en {out_file}{_RST}", file=sys.stderr)
    else:
        print(content)

    return 0


# ─── Self-tests ────────────────────────────────────────────────────────────

def _self_test() -> None:
    print("Tests de changelog_gen.py...")
    fails: list[str] = []
    def ok(n: str):   print(f"  OK: {n}")
    def fail(n, m):   fails.append(n); print(f"  FAIL: {n}: {m}")

    SAMPLE = [
        {"sha": "abc123def456", "short": "abc123", "tags": [],
         "date": "2024-01-15", "author": "Alice",
         "type": "feat", "scope": "scanner", "breaking": False,
         "desc": "add JS AST scanner", "body": "Uses acorn v8"},
        {"sha": "bbb000ccc111", "short": "bbb000", "tags": ["v2.5"],
         "date": "2024-01-10", "author": "Bob",
         "type": "fix", "scope": "", "breaking": False,
         "desc": "fix noqa regex digits", "body": ""},
        {"sha": "ddd111eee222", "short": "ddd111", "tags": [],
         "date": "2024-01-08", "author": "Charlie",
         "type": "chore", "scope": "", "breaking": True,
         "desc": "rename bago-root env var", "body": ""},
    ]

    # T1 — markdown contiene secciones clave
    md = generate_markdown(SAMPLE, title="TEST CHANGELOG")
    if "TEST CHANGELOG" in md and "Nuevas Funcionalidades" in md and "Correcciones" in md:
        ok("changelog_gen:markdown_sections")
    else:
        fail("changelog_gen:markdown_sections", "secciones faltantes")

    # T2 — sha corto aparece en md
    if "abc123" in md and "bbb000" in md:
        ok("changelog_gen:sha_in_output")
    else:
        fail("changelog_gen:sha_in_output", "sha no aparece")

    # T3 — breaking change detectado
    if "BREAKING" in md and "rename bago-root" in md:
        ok("changelog_gen:breaking_change_detected")
    else:
        fail("changelog_gen:breaking_change_detected", "breaking no aparece")

    # T4 — group_by_version separa por tags
    groups = _group_by_version(SAMPLE)
    if len(groups) == 2 and groups[0][0] == "Unreleased":
        ok("changelog_gen:group_by_version")
    else:
        fail("changelog_gen:group_by_version", f"groups={[(g[0], len(g[1])) for g in groups]}")

    # T5 — parse conventional commit
    m = COMMIT_RE.match("feat(auth)!: add OAuth2 support")
    if m and m.group("type") == "feat" and m.group("scope") == "auth" and m.group("breaking"):
        ok("changelog_gen:parse_conventional_commit")
    else:
        fail("changelog_gen:parse_conventional_commit", f"m={m}")

    # T6 — html generado
    html = generate_html(SAMPLE)
    if "<!DOCTYPE html>" in html and "abc123" in html:
        ok("changelog_gen:html_output")
    else:
        fail("changelog_gen:html_output", "html incompleto")

    total = 6; passed = total - len(fails)
    print(f"\n  {passed}/{total} tests pasaron")
    if fails: sys.exit(1)


if __name__ == "__main__":
    if "--test" in sys.argv:
        _self_test()
    else:
        sys.exit(main(sys.argv[1:]))
