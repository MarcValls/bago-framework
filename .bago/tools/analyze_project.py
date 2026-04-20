#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_project.py — Análisis estático completo de un proyecto.

Busca bugs potenciales, inconsistencias, duplicidades y oportunidades
de simplificación. Genera un informe priorizado en Markdown.

Uso:
  python3 .bago/tools/analyze_project.py /ruta/al/proyecto
  python3 .bago/tools/analyze_project.py /ruta/al/proyecto --output informe.md
  python3 .bago/tools/analyze_project.py /ruta/al/proyecto --json
"""

from pathlib import Path
from collections import defaultdict
from datetime import datetime
import sys, re, os, hashlib, json, ast

# ── Configuración ──────────────────────────────────────────────────────────────

IGNORE_DIRS = {
    '.git', 'node_modules', '__pycache__', '.bago', 'venv', 'env', '.env',
    'dist', 'build', '.next', '.nuxt', 'coverage', '.cache', 'vendor',
    '.tox', '.eggs', 'bower_components', '.idea', '.vscode', '.mypy_cache',
    'htmlcov', 'site-packages',
}
IGNORE_EXTS = {
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe', '.bin',
    '.jpg', '.jpeg', '.png', '.gif', '.svg', '.ico', '.pdf', '.woff',
    '.woff2', '.ttf', '.eot', '.mp4', '.mp3', '.zip', '.tar', '.gz',
    '.lock', '.map',
}
TEXT_EXTS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala', '.lua',
    '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat',
    '.md', '.txt', '.rst', '.yml', '.yaml', '.json', '.toml', '.ini',
    '.cfg', '.conf', '.html', '.css', '.scss', '.sass', '.less',
    '.vue', '.svelte', '.sql', '.r', '.R', '.m', '.dart',
}

# Patrones de credenciales hardcoded
CRED_PATTERNS = [
    (r'(?i)(password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']',      'Contraseña hardcoded'),
    (r'(?i)(api[_-]?key)\s*=\s*["\'][^"\']{8,}["\']',              'API key hardcoded'),
    (r'(?i)(secret[_-]?key|app[_-]?secret)\s*=\s*["\'][^"\']{8,}["\']', 'Secret hardcoded'),
    (r'(?i)(token)\s*=\s*["\'][^"\']{10,}["\']',                   'Token hardcoded'),
    (r'(?i)(aws_access|aws_secret)\s*=\s*["\'][^"\']{8,}["\']',    'AWS key hardcoded'),
    (r'AKIA[0-9A-Z]{16}',                                           'AWS Access Key ID'),
    (r'(?i)bearer\s+[a-zA-Z0-9\-_\.]{20,}',                       'Bearer token en código'),
]
RE_CREDS = [(re.compile(p), label) for p, label in CRED_PATTERNS]

RE_CRITICAL = re.compile(r'(?i)#\s*(SECURITY|CRITICAL|DANGER|UNSAFE|VULNERABLE|EXPLOIT|HACK\s*:)', re.M)
RE_TODO     = re.compile(r'(?i)(?:#|//|/\*)\s*(TODO|FIXME|HACK|XXX|BUG|NOCOMMIT|TEMP)\b')
RE_DEBUG_PY = re.compile(r'^\s*(print\s*\(|pprint\s*\()', re.M)
RE_DEBUG_JS = re.compile(r'^\s*(console\.(log|warn|error|debug)\s*\()', re.M)
RE_COMMENTED_CODE = re.compile(r'^\s*#\s+(?:def |class |import |from |if |for |while |return )', re.M)
RE_LONG_LINE = re.compile(r'^.{121,}$', re.M)

# ── Tipos de lenguajes ─────────────────────────────────────────────────────────

LANG_MAP = {
    '.py':'Python', '.js':'JavaScript', '.ts':'TypeScript', '.jsx':'JSX',
    '.tsx':'TSX', '.java':'Java', '.c':'C', '.cpp':'C++', '.h':'C/C++ header',
    '.cs':'C#', '.go':'Go', '.rs':'Rust', '.rb':'Ruby', '.php':'PHP',
    '.swift':'Swift', '.kt':'Kotlin', '.scala':'Scala', '.lua':'Lua',
    '.sh':'Shell', '.bash':'Bash', '.ps1':'PowerShell', '.bat':'Batch',
    '.md':'Markdown', '.yml':'YAML', '.yaml':'YAML', '.json':'JSON',
    '.toml':'TOML', '.html':'HTML', '.css':'CSS', '.scss':'SCSS',
    '.sass':'Sass', '.vue':'Vue', '.svelte':'Svelte', '.sql':'SQL',
    '.dart':'Dart', '.go':'Go',
}


# ── Colección de datos ─────────────────────────────────────────────────────────

def collect_files(root: Path) -> list[Path]:
    """Devuelve todos los archivos de texto del proyecto."""
    files = []
    for p in root.rglob('*'):
        if p.is_file():
            parts = set(p.parts)
            if parts & IGNORE_DIRS:
                continue
            if any(str(p).endswith(e) for e in IGNORE_DIRS):
                continue
            ext = p.suffix.lower()
            if ext in IGNORE_EXTS:
                continue
            if ext in TEXT_EXTS or p.stat().st_size < 512_000:
                files.append(p)
    return sorted(files)


def read_safe(path: Path) -> str | None:
    """Lee un archivo de texto de forma segura."""
    try:
        return path.read_text(encoding='utf-8', errors='replace')
    except Exception:
        return None


# ── Análisis ───────────────────────────────────────────────────────────────────

class Finding:
    def __init__(self, priority: str, category: str, title: str,
                 detail: str = '', file: str = '', line: int = 0):
        self.priority = priority   # P1 / P2 / P3
        self.category = category
        self.title    = title
        self.detail   = detail
        self.file     = file
        self.line     = line

    def __repr__(self):
        loc = f" [{self.file}:{self.line}]" if self.file else ""
        return f"[{self.priority}] {self.category} — {self.title}{loc}"


def analyze(root: Path) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    stats: dict = {
        'files': 0, 'lines': 0, 'code_lines': 0,
        'languages': defaultdict(int),
        'largest_files': [],
        'duplicates': 0,
    }

    files = collect_files(root)
    stats['files'] = len(files)

    hashes: dict[str, list[Path]] = defaultdict(list)   # content hash → files
    name_groups: dict[str, list[Path]] = defaultdict(list)  # filename → paths
    func_lines: list[tuple[int, Path]] = []

    has_tests = False
    has_src   = False
    has_readme = (root / 'README.md').exists() or (root / 'README.rst').exists()
    has_env_example = any(root.glob('*.env.example')) or (root / '.env.example').exists()
    has_dotenv = (root / '.env').exists()

    lang_lines: dict[str, int] = defaultdict(int)

    for fpath in files:
        ext  = fpath.suffix.lower()
        lang = LANG_MAP.get(ext, ext.lstrip('.').upper() if ext else 'OTHER')
        content = read_safe(fpath)
        if content is None:
            continue

        lines = content.splitlines()
        nlines = len(lines)
        stats['lines'] += nlines
        stats['languages'][lang] += 1
        lang_lines[lang] += nlines

        fname = fpath.name.lower()
        if 'test' in fname or 'spec' in fname or fname.startswith('test_'):
            has_tests = True
        if any(part.lower() in ('src', 'lib', 'app', 'source') for part in fpath.parts):
            has_src = True

        # Archivos grandes
        if nlines > 500:
            stats['largest_files'].append((nlines, str(fpath.relative_to(root))))

        # Hash para duplicados (solo archivos de código)
        if ext in TEXT_EXTS and nlines > 10:
            h = hashlib.md5(content.encode('utf-8', errors='replace')).hexdigest()
            hashes[h].append(fpath)

        # Nombres de archivo duplicados
        name_groups[fpath.name].append(fpath)

        # ── P1: Credenciales hardcoded ──────────────────────────────────────
        for pattern, label in RE_CREDS:
            for m in pattern.finditer(content):
                lineno = content[:m.start()].count('\n') + 1
                # Skip if in .env or example files
                if '.env' in fpath.name or 'example' in fpath.name.lower():
                    continue
                findings.append(Finding(
                    'P1', 'Seguridad', label,
                    f'`{m.group()[:60].strip()}`',
                    str(fpath.relative_to(root)), lineno
                ))

        # ── P1: Comentarios de seguridad críticos ───────────────────────────
        for m in RE_CRITICAL.finditer(content):
            lineno = content[:m.start()].count('\n') + 1
            findings.append(Finding(
                'P1', 'Seguridad', f'Comentario crítico: {m.group().strip()[:60]}',
                '', str(fpath.relative_to(root)), lineno
            ))

        # ── P2: TODO / FIXME / HACK ─────────────────────────────────────────
        todo_count = len(RE_TODO.findall(content))
        if todo_count > 0:
            # Group instead of individual (too noisy)
            findings.append(Finding(
                'P2', 'Deuda técnica', f'{todo_count} TODO/FIXME/HACK en el archivo',
                'Revisar y resolver o eliminar',
                str(fpath.relative_to(root))
            ))

        # ── P2: Archivos muy grandes ─────────────────────────────────────────
        if nlines > 800:
            findings.append(Finding(
                'P2', 'Complejidad', f'Archivo muy grande ({nlines} líneas)',
                'Considerar dividir en módulos más pequeños',
                str(fpath.relative_to(root))
            ))
        elif nlines > 500:
            findings.append(Finding(
                'P3', 'Complejidad', f'Archivo grande ({nlines} líneas)',
                'Revisar si puede modularizarse',
                str(fpath.relative_to(root))
            ))

        # ── P2: Funciones largas (Python) ────────────────────────────────────
        if ext == '.py':
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        end = getattr(node, 'end_lineno', node.lineno + 1)
                        length = end - node.lineno
                        if length > 100:
                            findings.append(Finding(
                                'P2', 'Complejidad',
                                f'Función `{node.name}` muy larga ({length} líneas)',
                                'Candidata a refactoring',
                                str(fpath.relative_to(root)), node.lineno
                            ))
                        elif length > 60:
                            findings.append(Finding(
                                'P3', 'Complejidad',
                                f'Función `{node.name}` larga ({length} líneas)',
                                'Considerar dividir',
                                str(fpath.relative_to(root)), node.lineno
                            ))
            except SyntaxError as e:
                findings.append(Finding(
                    'P1', 'Bugs', f'Error de sintaxis Python: {e.msg}',
                    str(e), str(fpath.relative_to(root)), e.lineno or 0
                ))
            except Exception:
                pass

        # ── P3: Debug prints ─────────────────────────────────────────────────
        if ext == '.py':
            debug_count = len(RE_DEBUG_PY.findall(content))
            if debug_count > 2:
                findings.append(Finding(
                    'P3', 'Limpieza', f'{debug_count} print() de depuración',
                    'Eliminar o reemplazar por logging',
                    str(fpath.relative_to(root))
                ))
        elif ext in ('.js', '.ts', '.jsx', '.tsx'):
            debug_count = len(RE_DEBUG_JS.findall(content))
            if debug_count > 2:
                findings.append(Finding(
                    'P3', 'Limpieza', f'{debug_count} console.log/warn/error',
                    'Eliminar o reemplazar por logger',
                    str(fpath.relative_to(root))
                ))

        # ── P3: Líneas muy largas ─────────────────────────────────────────────
        long_lines = RE_LONG_LINE.findall(content)
        if len(long_lines) > 5:
            findings.append(Finding(
                'P3', 'Estilo', f'{len(long_lines)} líneas >120 chars',
                'Mejorar legibilidad',
                str(fpath.relative_to(root))
            ))

        # ── P3: Código comentado ──────────────────────────────────────────────
        cc = RE_COMMENTED_CODE.findall(content)
        if len(cc) > 3:
            findings.append(Finding(
                'P3', 'Limpieza', f'{len(cc)} bloques de código comentado',
                'Eliminar código muerto',
                str(fpath.relative_to(root))
            ))

    # ── Duplicados de contenido ───────────────────────────────────────────────
    dup_groups = {h: paths for h, paths in hashes.items() if len(paths) > 1}
    stats['duplicates'] = len(dup_groups)
    for h, paths in dup_groups.items():
        rel = [str(p.relative_to(root)) for p in paths]
        findings.append(Finding(
            'P2', 'Duplicidades',
            f'Archivo duplicado: {paths[0].name}',
            'Mismo contenido en: ' + ', '.join(rel),
        ))

    # ── Nombres de archivo duplicados ─────────────────────────────────────────
    for name, paths in name_groups.items():
        if len(paths) > 1 and not name.startswith('.'):
            rel = [str(p.relative_to(root)) for p in paths]
            findings.append(Finding(
                'P3', 'Duplicidades',
                f'Nombre de archivo repetido: {name}',
                'En: ' + ', '.join(rel)
            ))

    # ── Sin tests ─────────────────────────────────────────────────────────────
    if has_src and not has_tests:
        findings.append(Finding(
            'P2', 'Calidad',
            'No se detectaron archivos de test',
            'Añadir tests unitarios para los módulos principales'
        ))

    # ── Sin README ────────────────────────────────────────────────────────────
    if not has_readme:
        findings.append(Finding(
            'P2', 'Documentación',
            'No hay README en la raíz',
            'Añadir README.md con descripción, instalación y uso'
        ))

    # ── .env sin .env.example ─────────────────────────────────────────────────
    if has_dotenv and not has_env_example:
        findings.append(Finding(
            'P1', 'Seguridad',
            'Existe .env pero no .env.example',
            'Riesgo de commit accidental de credenciales. Añadir .env.example y .gitignore'
        ))

    # Ordenar: P1 primero
    order = {'P1': 0, 'P2': 1, 'P3': 2}
    findings.sort(key=lambda f: (order.get(f.priority, 9), f.category, f.file))

    # Top archivos grandes
    stats['largest_files'].sort(reverse=True)
    stats['largest_files'] = stats['largest_files'][:10]

    return findings, stats


# ── Generación del informe ─────────────────────────────────────────────────────

def generate_report(root: Path, findings: list[Finding], stats: dict) -> str:
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    p1 = [f for f in findings if f.priority == 'P1']
    p2 = [f for f in findings if f.priority == 'P2']
    p3 = [f for f in findings if f.priority == 'P3']

    top_langs = sorted(stats['languages'].items(), key=lambda x: -x[1])[:8]
    lang_str = ', '.join(f'{l} ({n})' for l, n in top_langs)

    lines = [
        '# BAGO — Análisis de Proyecto',
        '',
        f'**Proyecto:** `{root}`  ',
        f'**Fecha:** {now}  ',
        f'**Archivos analizados:** {stats["files"]}  ',
        f'**Líneas totales:** {stats["lines"]:,}  ',
        f'**Lenguajes:** {lang_str}  ',
        '',
        '---',
        '',
        '## Resumen de hallazgos',
        '',
        f'| Prioridad | N° | Descripción |',
        f'|---|---|---|',
        f'| 🔴 P1 — Crítico | {len(p1)} | Seguridad, bugs, errores de sintaxis |',
        f'| 🟠 P2 — Importante | {len(p2)} | Deuda técnica, complejidad, duplicados |',
        f'| 🟡 P3 — Menor | {len(p3)} | Limpieza, estilo, documentación |',
        f'| **Total** | **{len(findings)}** | |',
        '',
    ]

    # P1
    if p1:
        lines += ['---', '', '## 🔴 P1 — Hallazgos Críticos', '', '_Resolver antes de cualquier otra cosa._', '']
        for i, f in enumerate(p1, 1):
            loc = f' — `{f.file}:{f.line}`' if f.file else ''
            lines.append(f'### P1-{i:02d}. [{f.category}] {f.title}')
            if f.detail:
                lines.append(f'> {f.detail}')
            if loc:
                lines.append(f'> Localización: {loc}')
            lines.append('')

    # P2
    if p2:
        lines += ['---', '', '## 🟠 P2 — Hallazgos Importantes', '', '_Resolver en el siguiente sprint._', '']
        for i, f in enumerate(p2, 1):
            loc = f' — `{f.file}:{f.line}`' if f.file and f.line else (f' — `{f.file}`' if f.file else '')
            lines.append(f'### P2-{i:02d}. [{f.category}] {f.title}')
            if f.detail:
                lines.append(f'> {f.detail}')
            if loc:
                lines.append(f'> Localización: {loc}')
            lines.append('')

    # P3
    if p3:
        lines += ['---', '', '## 🟡 P3 — Hallazgos Menores', '', '_Resolver cuando haya oportunidad._', '']
        for i, f in enumerate(p3, 1):
            loc = f' — `{f.file}:{f.line}`' if f.file and f.line else (f' — `{f.file}`' if f.file else '')
            lines.append(f'### P3-{i:02d}. [{f.category}] {f.title}')
            if f.detail:
                lines.append(f'> {f.detail}')
            if loc:
                lines.append(f'> Localización: {loc}')
            lines.append('')

    # Archivos grandes
    if stats['largest_files']:
        lines += ['---', '', '## Archivos más complejos (por LOC)', '']
        for nlines, fname in stats['largest_files'][:5]:
            lines.append(f'- `{fname}` — {nlines:,} líneas')
        lines.append('')

    # Plan de implementación
    lines += [
        '---',
        '',
        '## Plan de implementación sugerido',
        '',
        '### Fase 1 — Crítico (P1)',
    ]
    if p1:
        cats = sorted(set(f.category for f in p1))
        for cat in cats:
            items = [f for f in p1 if f.category == cat]
            lines.append(f'- **{cat}**: resolver {len(items)} hallazgo(s)')
    else:
        lines.append('- ✅ Sin hallazgos críticos')
    lines.append('')
    lines.append('### Fase 2 — Importante (P2)')
    if p2:
        cats = sorted(set(f.category for f in p2))
        for cat in cats:
            items = [f for f in p2 if f.category == cat]
            lines.append(f'- **{cat}**: resolver {len(items)} hallazgo(s)')
    else:
        lines.append('- ✅ Sin hallazgos importantes')
    lines.append('')
    lines.append('### Fase 3 — Menor (P3)')
    if p3:
        cats = sorted(set(f.category for f in p3))
        for cat in cats:
            items = [f for f in p3 if f.category == cat]
            lines.append(f'- **{cat}**: resolver {len(items)} hallazgo(s)')
    else:
        lines.append('- ✅ Sin hallazgos menores')

    lines += [
        '',
        '---',
        '',
        '## Instrucciones para el agente de IA',
        '',
        '> Lee este archivo completo antes de hacer cualquier cambio.',
        '> Usa el workflow W2 (Implementación Controlada) para cada hallazgo P1.',
        '> Usa el workflow W7 (Foco de Sesión) para agrupar los P2 del mismo módulo.',
        '> Ejecuta `python3 bago validate` antes y después de cada sesión.',
        '',
        '---',
        '',
        f'*Generado por BAGO analyze_project · {now}*',
    ]

    return '\n'.join(lines)


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]
    output_file = None
    as_json = False

    # Parse args
    filtered = []
    i = 0
    while i < len(args):
        if args[i] == '--output' and i + 1 < len(args):
            output_file = args[i + 1]
            i += 2
        elif args[i] == '--json':
            as_json = True
            i += 1
        else:
            filtered.append(args[i])
            i += 1

    if not filtered:
        print('Uso: python3 analyze_project.py <ruta_proyecto> [--output informe.md] [--json]')
        sys.exit(1)

    root = Path(filtered[0]).expanduser().resolve()
    if not root.exists():
        print(f'  ⚠  Ruta no encontrada: {root}')
        sys.exit(1)
    if not root.is_dir():
        print(f'  ⚠  La ruta debe ser un directorio: {root}')
        sys.exit(1)

    print(f'\n  Analizando: {root}')
    print('  Esto puede tardar unos segundos...\n')

    findings, stats = analyze(root)

    if as_json:
        data = {
            'project': str(root),
            'stats': {**stats, 'largest_files': stats['largest_files']},
            'findings': [
                {'priority': f.priority, 'category': f.category,
                 'title': f.title, 'detail': f.detail,
                 'file': f.file, 'line': f.line}
                for f in findings
            ]
        }
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return

    report = generate_report(root, findings, stats)

    if output_file:
        Path(output_file).write_text(report, encoding='utf-8')
        print(f'  ✅ Informe guardado en: {output_file}')
    else:
        # Save to project root by default
        out = root / 'BAGO_ANALYSIS.md'
        out.write_text(report, encoding='utf-8')
        print(f'  ✅ Informe guardado en: {out}')

    # Print summary to terminal
    p1 = [f for f in findings if f.priority == 'P1']
    p2 = [f for f in findings if f.priority == 'P2']
    p3 = [f for f in findings if f.priority == 'P3']

    print(f'  Archivos: {stats["files"]}  |  Líneas: {stats["lines"]:,}  |  Hallazgos: {len(findings)}')
    print()
    print(f'  🔴 P1 Crítico:     {len(p1):3d}')
    print(f'  🟠 P2 Importante:  {len(p2):3d}')
    print(f'  🟡 P3 Menor:       {len(p3):3d}')
    print()

    if p1:
        print('  P1 — Críticos:')
        for f in p1[:5]:
            loc = f' [{f.file}:{f.line}]' if f.file else ''
            print(f'    • [{f.category}] {f.title}{loc}')
        if len(p1) > 5:
            print(f'    ... y {len(p1)-5} más (ver informe completo)')
        print()

    print(f'  Informe completo → {root / "BAGO_ANALYSIS.md"}')
    print()


if __name__ == '__main__':
    main()
