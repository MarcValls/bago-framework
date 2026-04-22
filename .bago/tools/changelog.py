#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
changelog.py - Generador de CHANGELOG desde los cambios BAGO registrados.

Lee todos los archivos BAGO-CHG-*.json del state/changes/ y genera
un CHANGELOG.md estructurado, agrupado por mes y ordenado por fecha.

Formatos:
  - markdown: CHANGELOG.md estándar (Keep a Changelog)
  - text:     formato legible en terminal
  - json:     datos estructurados para integración

Uso:
  python3 changelog.py                     # imprime en terminal
  python3 changelog.py --format markdown   # formato Keep a Changelog
  python3 changelog.py --format json       # output JSON
  python3 changelog.py --out CHANGELOG.md  # guardar en archivo
  python3 changelog.py --since 2026-04-01  # filtrar por fecha
  python3 changelog.py --type governance   # filtrar por tipo
  python3 changelog.py --test
"""
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
from datetime import date, datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "state"

# Tipos de cambios → emojis + sección Keep a Changelog
TYPE_META = {
    "architecture": ("🏛", "Changed"),
    "governance":   ("⚙️",  "Changed"),
    "migration":    ("🔄", "Changed"),
    "feature":      ("✨", "Added"),
    "fix":          ("🐛", "Fixed"),
    "security":     ("🔒", "Security"),
    "deprecated":   ("⚠️",  "Deprecated"),
    "removed":      ("🗑",  "Removed"),
}

SEVERITY_ORDER = {"critical": 0, "major": 1, "minor": 2, "patch": 3}


def _load_changes(since=None, type_filter=None):
    """Carga todos los cambios BAGO-CHG-*.json."""
    folder = STATE / "changes"
    if not folder.exists():
        return []
    changes = []
    for f in sorted(folder.glob("BAGO-CHG-*.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            # Filtro de fecha
            if since:
                chg_date = d.get("created_at", "")[:10]
                if chg_date < since:
                    continue
            # Filtro de tipo
            if type_filter and d.get("type") != type_filter:
                continue
            d["_file"] = f.name
            changes.append(d)
        except Exception:
            continue
    # Ordenar por fecha descendente
    changes.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    return changes


def _group_by_month(changes):
    """Agrupa cambios por mes YYYY-MM."""
    by_month = defaultdict(list)
    for c in changes:
        month = c.get("created_at", "")[:7] or "unknown"
        by_month[month].append(c)
    return dict(sorted(by_month.items(), reverse=True))


def _change_line(c, fmt="text"):
    """Genera una línea de changelog para un cambio."""
    chg_id   = c.get("change_id", c.get("_file", "?"))
    title    = c.get("title", "Sin título")
    ctype    = c.get("type", "governance")
    severity = c.get("severity", "minor")
    status   = c.get("status", "?")
    chg_date = c.get("created_at", "")[:10]
    emoji, _ = TYPE_META.get(ctype, ("•", "Changed"))

    if fmt == "markdown":
        components = c.get("affected_components", [])
        comp_str = ", ".join("`{}`".format(comp.split("/")[-1])
                             for comp in components[:3])
        extra = " — {}".format(comp_str) if comp_str else ""
        return "- {} **{}** `{}` *{}*{}".format(
            emoji, title, chg_id, severity, extra)
    else:
        return "  {} [{:>8}] {:>12}  {}".format(
            emoji, severity, chg_id, title[:60])


def render_text(changes):
    """Renderiza en formato terminal."""
    if not changes:
        print("  No hay cambios registrados.")
        return

    by_month = _group_by_month(changes)
    print()
    print("  BAGO Changelog")
    print("  Pack: {}  ({} cambios)".format(ROOT.name, len(changes)))
    print()

    for month, chgs in by_month.items():
        try:
            month_label = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
        except Exception:
            month_label = month
        print("  ── {} ({}) ──".format(month_label, len(chgs)))
        # Ordenar por severidad dentro del mes
        chgs_sorted = sorted(chgs, key=lambda c: SEVERITY_ORDER.get(c.get("severity","minor"), 2))
        for c in chgs_sorted:
            print(_change_line(c, "text"))
        print()


def render_markdown(changes, pack_id="bago"):
    """Genera CHANGELOG.md en formato Keep a Changelog."""
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        "# Changelog — {}".format(pack_id),
        "",
        "> Formato: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)",
        "> Generado por `bago changelog` el {}".format(now_str),
        "",
        "---",
        "",
    ]

    by_month = _group_by_month(changes)

    for month, chgs in by_month.items():
        try:
            month_label = datetime.strptime(month, "%Y-%m").strftime("%B %Y")
        except Exception:
            month_label = month

        lines.append("## [{}]".format(month_label))
        lines.append("")

        # Agrupar por sección Keep a Changelog
        sections = defaultdict(list)
        for c in chgs:
            ctype = c.get("type", "governance")
            _, section = TYPE_META.get(ctype, ("•", "Changed"))
            sections[section].append(c)

        section_order = ["Added", "Changed", "Fixed", "Security", "Deprecated", "Removed"]
        for section in section_order:
            if section not in sections:
                continue
            lines.append("### {}".format(section))
            lines.append("")
            for c in sorted(sections[section],
                            key=lambda x: SEVERITY_ORDER.get(x.get("severity","minor"), 2)):
                lines.append(_change_line(c, "markdown"))
            lines.append("")

    return "\n".join(lines)


def render_json_output(changes):
    """Output JSON estructurado."""
    return json.dumps([{
        "id": c.get("change_id"),
        "title": c.get("title"),
        "type": c.get("type"),
        "severity": c.get("severity"),
        "status": c.get("status"),
        "date": c.get("created_at", "")[:10],
        "components": c.get("affected_components", []),
    } for c in changes], indent=2, ensure_ascii=False)


def _run_tests():
    print("  Ejecutando tests de changelog.py...")
    import tempfile

    # Mock de cambios
    mock_changes = [
        {"change_id": "BAGO-CHG-001", "title": "Init", "type": "architecture",
         "severity": "major", "status": "applied",
         "created_at": "2026-04-10T10:00:00Z", "affected_components": ["main.py"]},
        {"change_id": "BAGO-CHG-002", "title": "Governance fix", "type": "governance",
         "severity": "minor", "status": "applied",
         "created_at": "2026-04-15T10:00:00Z", "affected_components": []},
        {"change_id": "BAGO-CHG-003", "title": "Migration v2", "type": "migration",
         "severity": "major", "status": "applied",
         "created_at": "2026-03-20T10:00:00Z", "affected_components": ["migrate.py"]},
    ]

    # Test group by month
    by_month = _group_by_month(mock_changes)
    assert "2026-04" in by_month, "Mes 2026-04 no encontrado"
    assert "2026-03" in by_month, "Mes 2026-03 no encontrado"
    assert len(by_month["2026-04"]) == 2, "Conteo incorrecto en 2026-04"

    # Test _change_line text
    line = _change_line(mock_changes[0], "text")
    assert "Init" in line and "BAGO-CHG-001" in line, "Line text incorrecta"

    # Test render_markdown
    md = render_markdown(mock_changes, "test_pack")
    assert "# Changelog" in md, "Header faltante"
    assert "BAGO-CHG-001" in md, "CHG-001 no en markdown"
    assert "## [" in md, "Sección de mes faltante"

    # Test render_json
    j = render_json_output(mock_changes)
    data = json.loads(j)
    assert len(data) == 3
    assert data[0]["id"] == "BAGO-CHG-001"

    # Test con datos reales
    real_changes = _load_changes()
    assert len(real_changes) > 0, "Sin cambios reales"
    assert all("change_id" in c for c in real_changes[:5]), "change_id faltante"

    print("  OK: todos los tests pasaron (5/5)")


def main():
    p = argparse.ArgumentParser(description="Generador de CHANGELOG desde cambios BAGO")
    p.add_argument("--format", choices=["text", "markdown", "json"], default="text")
    p.add_argument("--out", default=None, metavar="FILE", help="Guardar en archivo")
    p.add_argument("--since", default=None, metavar="DATE", help="Desde fecha YYYY-MM-DD")
    p.add_argument("--type", dest="type_filter", default=None,
                   choices=["architecture", "governance", "migration"],
                   metavar="TYPE", help="Filtrar por tipo")
    p.add_argument("--test", action="store_true")
    args = p.parse_args()

    if args.test:
        _run_tests()
        return

    changes = _load_changes(since=args.since, type_filter=args.type_filter)

    if args.format == "text":
        render_text(changes)
        return

    pack_data = {}
    pack_path = ROOT / "pack.json"
    if pack_path.exists():
        try:
            pack_data = json.loads(pack_path.read_text(encoding="utf-8"))
        except Exception:
            pass
    pack_id = pack_data.get("id", "bago")

    if args.format == "markdown":
        content = render_markdown(changes, pack_id)
    else:
        content = render_json_output(changes)

    if args.out:
        Path(args.out).write_text(content, encoding="utf-8")
        print("  Changelog guardado en: {} ({} cambios, {:.1f} KB)".format(
            args.out, len(changes), len(content)/1024))
    else:
        print(content)


if __name__ == "__main__":
    main()
