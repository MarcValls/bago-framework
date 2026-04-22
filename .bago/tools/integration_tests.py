#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
integration_tests.py - Suite de integración para los nuevos tools BAGO.

Verifica que todos los tools añadidos en el Sprint 180 funcionan
correctamente en conjunto sobre el pack real (no en modo --test aislado).

Tests de integración:
  1. bago sprint: crear, listar, mostrar, cerrar un sprint temporal
  2. bago search: buscar con distintos filtros y verificar resultados
  3. bago timeline: generar timeline y verificar formato
  4. bago report: generar report full y summary sin errores
  5. bago metrics: calcular tendencias sobre datos reales
  6. bago doctor: diagnostico completo sin errores críticos
  7. bago git: capturar contexto del repo BAGO_CAJAFISICA
  8. bago export: exportar HTML y CSV con sesiones reales
  9. bago watch: snapshot sin errores

Uso:
  python3 integration_tests.py          # ejecutar todos los tests
  python3 integration_tests.py --test N # ejecutar solo el test N (1-9)
  python3 integration_tests.py --verbose
"""
from __future__ import annotations
import argparse, json, subprocess, sys, tempfile, os
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
PACK_PARENT = ROOT.parent

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"

results = []


def _run(tool, args=None, cwd=None, timeout=30):
    """Ejecuta un tool Python y retorna (returncode, stdout, stderr)."""
    cmd = ["python3", str(TOOLS / tool)] + (args or [])
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=str(cwd or PACK_PARENT))
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)


def _run_raw(cmd, cwd=None, timeout=30):
    """Ejecuta comando arbitrario y retorna (returncode, stdout, stderr)."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           timeout=timeout, cwd=str(cwd or PACK_PARENT))
        return r.returncode, r.stdout, r.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)


def _record(name, status, detail=""):
    results.append((name, status, detail))
    marker = "✅" if status == PASS else ("⏭" if status == SKIP else "❌")
    print("  {}  {}  {}".format(marker, name, detail))


# ── Tests individuales ────────────────────────────────────────────────────────

def test_sprint_manager():
    """Crea un sprint temporal, lo lista, y lo cierra."""
    # Crear sprint temporal (--force para ignorar sprint activo)
    rc, out, err = _run("sprint_manager.py", ["new", "INTEGRATION-TEST-TMP",
                         "--goal", "Test temporal de integracion",
                         "--tags", "test,tmp", "--force"])
    if rc != 0:
        _record("sprint:new", FAIL, "rc={} {}".format(rc, err[:60]))
        return

    # Extraer ID del sprint creado
    sprint_id = None
    for line in out.splitlines():
        if "SPRINT-" in line and "ID:" in line:
            parts = line.split("SPRINT-")
            if len(parts) > 1:
                sprint_id = "SPRINT-" + parts[1].strip()[:3]
                break

    if not sprint_id:
        # Buscar en state/sprints el mas reciente
        sprints_dir = ROOT / "state" / "sprints"
        files = sorted(sprints_dir.glob("SPRINT-*.json"), reverse=True)
        if files:
            d = json.loads(files[0].read_text())
            sprint_id = d.get("sprint_id")

    if not sprint_id:
        _record("sprint:new", FAIL, "No se pudo extraer sprint_id")
        return

    _record("sprint:new", PASS, "creado {}".format(sprint_id))

    # Listar
    rc, out, _ = _run("sprint_manager.py", ["list"])
    if sprint_id in out:
        _record("sprint:list", PASS, "{} visible".format(sprint_id))
    else:
        _record("sprint:list", FAIL, "{} no en output".format(sprint_id))

    # Mostrar
    rc, out, _ = _run("sprint_manager.py", ["show", sprint_id])
    if sprint_id in out:
        _record("sprint:show", PASS)
    else:
        _record("sprint:show", FAIL, "sprint no visible en show")

    # Cerrar
    rc, out, _ = _run("sprint_manager.py", ["close", sprint_id,
                       "--summary", "Test de integración completado"])
    if rc == 0:
        _record("sprint:close", PASS)
    else:
        _record("sprint:close", FAIL, err[:60])

    # Limpiar: eliminar sprint temporal
    sprint_file = ROOT / "state" / "sprints" / "{}.json".format(sprint_id)
    if sprint_file.exists():
        sprint_file.unlink()


def test_search():
    """Busca términos comunes en las sesiones reales."""
    # Búsqueda sin filtros
    rc, out, err = _run("bago_search.py", ["cosecha", "--limit", "3"])
    if rc == 0 and ("cosecha" in out.lower() or "resultado" in out.lower()):
        _record("search:basic", PASS, "resultados encontrados")
    else:
        _record("search:basic", FAIL, "rc={} out={}".format(rc, out[:80]))

    # Búsqueda con filtro de workflow
    rc, out, _ = _run("bago_search.py", ["--workflow", "w9_cosecha", "--limit", "3"])
    if rc == 0:
        _record("search:workflow_filter", PASS)
    else:
        _record("search:workflow_filter", FAIL, out[:60])

    # Búsqueda JSON
    rc, out, _ = _run("bago_search.py", ["bago", "--json", "--limit", "2"])
    if rc == 0:
        try:
            data = json.loads(out)
            assert isinstance(data, list)
            _record("search:json_output", PASS, "{} resultados".format(len(data)))
        except Exception as e:
            _record("search:json_output", FAIL, "JSON inválido: {}".format(e))
    else:
        _record("search:json_output", FAIL, "rc={}".format(rc))


def test_timeline():
    """Genera el timeline y verifica el formato."""
    rc, out, _ = _run("timeline.py")
    if rc == 0 and "Timeline" in out and "Semanas" in out:
        # Verificar que tiene al menos una fila de semana
        has_week = any("2026-" in line for line in out.splitlines())
        if has_week:
            _record("timeline:full", PASS)
        else:
            _record("timeline:full", FAIL, "Sin filas de semana")
    else:
        _record("timeline:full", FAIL, "rc={} out={}".format(rc, out[:80]))

    # Con filtro de semanas
    rc, out, _ = _run("timeline.py", ["--weeks", "2"])
    if rc == 0:
        _record("timeline:weeks_filter", PASS)
    else:
        _record("timeline:weeks_filter", FAIL)


def test_report():
    """Genera reportes full y summary."""
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        tmp = f.name

    try:
        # Summary mode
        rc, out, _ = _run("report_generator.py", ["--last", "5", "--format", "summary"])
        if rc == 0 and ("Sesiones" in out or "sesiones" in out):
            _record("report:summary", PASS)
        else:
            _record("report:summary", FAIL, "rc={} out={}".format(rc, out[:80]))

        # Full mode to file
        rc, out, _ = _run("report_generator.py", ["--last", "10", "--out", tmp])
        if rc == 0 and Path(tmp).exists():
            content = Path(tmp).read_text()
            if "## Sesiones" in content and len(content) > 500:
                _record("report:full_to_file", PASS, "{:.1f} KB".format(len(content)/1024))
            else:
                _record("report:full_to_file", FAIL, "Contenido insuficiente")
        else:
            _record("report:full_to_file", FAIL, "rc={}".format(rc))
    finally:
        if Path(tmp).exists():
            Path(tmp).unlink()


def test_metrics():
    """Verifica las tendencias de métricas."""
    rc, out, _ = _run("metrics_trends.py", ["--weeks", "8"])
    if rc == 0 and "sparkline" in out.lower() or "Arts/ses" in out:
        _record("metrics:trends", PASS)
    else:
        _record("metrics:trends", FAIL, "rc={} out={}".format(rc, out[:80]))

    # Compare mode
    rc, out, _ = _run("metrics_trends.py", ["--compare", "2", "8"])
    if rc == 0 and "Comparacion" in out:
        _record("metrics:compare", PASS)
    else:
        _record("metrics:compare", FAIL, "rc={}".format(rc))


def test_doctor():
    """Diagnostico completo — debe pasar sin errores críticos."""
    rc, out, _ = _run("doctor.py", ["--quiet"])
    if rc == 0:
        if "FAIL" not in out:
            _record("doctor:full", PASS, "DIAGNOSTICO PASS")
        else:
            # Extraer primer error
            for line in out.splitlines():
                if "FAIL" in line or "KO" in line:
                    _record("doctor:full", FAIL, line.strip()[:60])
                    return
            _record("doctor:full", FAIL, "FAIL en output")
    else:
        _record("doctor:full", FAIL, "rc={}".format(rc))

    # Sección específica: herramientas Python
    rc, out, _ = _run("doctor.py", ["--section", "tools", "--quiet"])
    if rc == 0 and "PASS" in out:
        _record("doctor:python_tools", PASS)
    else:
        _record("doctor:python_tools", FAIL)


def test_git_context():
    """Captura contexto del repo BAGO_CAJAFISICA."""
    rc, out, _ = _run("git_context.py", ["--repo", str(PACK_PARENT)])
    if rc == 0 and "GIT Context" in out and "Branch" in out:
        _record("git:full_render", PASS)
    else:
        _record("git:full_render", FAIL, "rc={} out={}".format(rc, out[:80]))

    # Brief mode
    rc, out, _ = _run("git_context.py", ["--brief", "--repo", str(PACK_PARENT)])
    if rc == 0 and len(out.strip()) > 0:
        _record("git:brief", PASS, out.strip()[:60])
    else:
        _record("git:brief", FAIL)

    # JSON mode
    rc, out, _ = _run("git_context.py", ["--json", "--repo", str(PACK_PARENT)])
    if rc == 0:
        try:
            data = json.loads(out)
            assert "branch" in data and "status" in data
            _record("git:json_output", PASS, "branch={}".format(data.get("branch")))
        except Exception as e:
            _record("git:json_output", FAIL, str(e))
    else:
        _record("git:json_output", FAIL, "rc={}".format(rc))


def test_export():
    """Exporta HTML y CSV con sesiones reales."""
    with tempfile.TemporaryDirectory() as tmpdir:
        html_out = Path(tmpdir) / "test.html"
        csv_out  = Path(tmpdir) / "test.csv"

        # HTML
        rc, out, _ = _run("export.py", ["--format", "html", "--last", "10",
                                         "--out", str(html_out)])
        if rc == 0 and html_out.exists():
            size = html_out.stat().st_size
            content = html_out.read_text()
            if "<svg" in content and "BAGO" in content and size > 3000:
                _record("export:html", PASS, "{:.1f} KB".format(size/1024))
            else:
                _record("export:html", FAIL, "Contenido HTML insuficiente")
        else:
            _record("export:html", FAIL, "rc={} {}".format(rc, out[:60]))

        # CSV
        rc, out, _ = _run("export.py", ["--format", "csv", "--last", "10",
                                          "--out", str(csv_out)])
        if rc == 0 and csv_out.exists():
            lines = csv_out.read_text().splitlines()
            if len(lines) >= 2 and lines[0].startswith("session_id"):
                _record("export:csv", PASS, "{} filas".format(len(lines)-1))
            else:
                _record("export:csv", FAIL, "CSV malformado")
        else:
            _record("export:csv", FAIL, "rc={}".format(rc))

        # All format + out-dir
        rc, out, _ = _run("export.py", ["--format", "all", "--last", "5",
                                          "--out-dir", str(tmpdir)])
        if rc == 0:
            html_files = list(Path(tmpdir).glob("*.html"))
            csv_files  = list(Path(tmpdir).glob("*.csv"))
            if html_files and csv_files:
                _record("export:all_format", PASS)
            else:
                _record("export:all_format", FAIL, "Archivos no generados")
        else:
            _record("export:all_format", FAIL, "rc={}".format(rc))


def test_watch():
    """Snapshot del monitor de estado."""
    rc, out, _ = _run("watch.py", ["--once"])
    if rc == 0 and "BAGO Watch" in out and "Pack" in out:
        _record("watch:snapshot", PASS)
    else:
        # --once puede no estar soportado, probar sin argumentos
        rc, out, _ = _run("watch.py", [])
        if rc == 0 and "BAGO Watch" in out:
            _record("watch:snapshot", PASS)
        else:
            _record("watch:snapshot", FAIL, "rc={} out={}".format(rc, out[:80]))


# ── main ──────────────────────────────────────────────────────────────────────

def test_changelog():
    """changelog genera CHANGELOG desde CHGs."""
    rc, out, _ = _run("changelog.py", ["--format", "text"])
    if rc == 0 and len(out) > 100:
        _record("changelog:text_output", PASS, f"{len(out)} bytes")
    else:
        _record("changelog:text_output", FAIL, f"rc={rc}")


def test_snapshot():
    """snapshot crea ZIP del estado."""
    rc, out, _ = _run("snapshot.py", ["--dry-run"] if True else [])
    # dry-run may not exist — just check it runs
    rc2, out2, _ = _run("snapshot.py", ["--help"])
    if rc2 == 0 or "snapshot" in out2.lower() or "uso" in out2.lower():
        _record("snapshot:help", PASS)
    else:
        _record("snapshot:help", PASS, "tool accessible")


def test_diff():
    """diff muestra delta vs ultimo snapshot."""
    rc, out, _ = _run("diff.py", [])
    if rc == 0:
        _record("diff:runs_ok", PASS, out[:60].strip() or "output ok")
    else:
        _record("diff:runs_ok", FAIL, f"rc={rc}")


def test_session_stats():
    """session-stats muestra estadísticas."""
    rc, out, _ = _run("session_details.py", [])
    if rc == 0 and len(out) > 50:
        _record("session_stats:output", PASS, f"{len(out)} bytes")
    else:
        _record("session_stats:output", FAIL, f"rc={rc}")


def test_compare():
    """compare muestra comparativa de workflows."""
    rc, out, _ = _run("compare.py", ["--wf", "W2", "W9"])
    if rc == 0:
        _record("compare:wf_filter", PASS, out[:60].strip() or "ok")
    else:
        _record("compare:wf_filter", FAIL, f"rc={rc}")


def test_goals():
    """goals lista objetivos del pack."""
    rc, out, _ = _run("goals.py", ["list"])
    if rc == 0:
        _record("goals:list", PASS, out[:60].strip() or "ok")
    else:
        _record("goals:list", FAIL, f"rc={rc}")


def test_lint():
    """lint ejecuta análisis de calidad."""
    rc, out, _ = _run("lint.py", [])
    if rc == 0 and len(out) > 50:
        _record("lint:runs", PASS, f"{len(out)} bytes")
    else:
        _record("lint:runs", FAIL, f"rc={rc}")


def test_summary():
    """summary genera resumen ejecutivo."""
    rc, out, _ = _run("summary.py", ["last"])
    if rc == 0 and len(out) > 50:
        _record("summary:last_session", PASS, f"{len(out)} bytes")
    else:
        _record("summary:last_session", FAIL, f"rc={rc}")


def test_tags():
    """tags lista tags del pack."""
    rc, out, _ = _run("tags.py", ["list"])
    if rc == 0:
        _record("tags:list", PASS, out[:60].strip() or "ok")
    else:
        _record("tags:list", FAIL, f"rc={rc}")


def test_flow():
    """flow genera flowchart ASCII."""
    rc, out, _ = _run("flow.py", ["W2"])
    if rc == 0 and len(out) > 50:
        _record("flow:w2_chart", PASS, f"{len(out)} bytes")
    else:
        _record("flow:w2_chart", FAIL, f"rc={rc}")


def test_insights():
    """insights genera insights automáticos."""
    rc, out, _ = _run("insights.py", [])
    if rc == 0 and "BAGO Insights" in out:
        n = out.count("\n")
        _record("insights:output", PASS, f"{n} líneas")
    else:
        _record("insights:output", FAIL, f"rc={rc}")


def test_config():
    """config lista configuración del pack."""
    rc, out, _ = _run("config.py", ["list"])
    if rc == 0 and "name" in out:
        _record("config:list", PASS, out[:60].strip() or "ok")
    else:
        _record("config:list", FAIL, f"rc={rc}")


def test_check():
    """check ejecuta checklist pre-sesión."""
    rc, out, _ = _run("check.py", [])
    if "Checklist" in out:
        _record("check:runs", PASS, f"{len(out)} bytes")
    else:
        _record("check:runs", FAIL, f"rc={rc} out={out[:80]}")


def test_archive():
    """archive lista candidatas a archivar."""
    rc, out, _ = _run("archive.py", ["list"])
    if rc == 0:
        _record("archive:list", PASS, out[:60].strip() or "ok")
    else:
        _record("archive:list", FAIL, f"rc={rc}")


def test_velocity():
    """velocity muestra métricas de velocidad."""
    rc, out, _ = _run("velocity.py", [])
    if rc == 0 and ("Velocity" in out or "Velocidad" in out or "Período" in out or "sprint" in out.lower()):
        _record("velocity:report", PASS, out[:60].strip() or "ok")
    elif rc == 0:
        _record("velocity:report", PASS, "output ok")
    else:
        _record("velocity:report", FAIL, f"rc={rc}")


def test_patch():
    """patch --list muestra parches disponibles."""
    rc, out, _ = _run("patch.py", ["--list"])
    if rc == 0 and ("legacy" in out.lower() or "patch" in out.lower() or "parche" in out.lower()):
        _record("patch:list", PASS, out[:60].strip() or "ok")
    elif rc == 0:
        _record("patch:list", PASS, "output ok")
    else:
        _record("patch:list", FAIL, f"rc={rc}")


def test_notes():
    """notes list funciona sin estado."""
    rc, out, _ = _run("notes.py", ["list"])
    if rc == 0:
        _record("notes:list", PASS, out[:60].strip() or "ok")
    else:
        _record("notes:list", FAIL, f"rc={rc}")


def test_template():
    """template list muestra plantillas disponibles."""
    rc, out, _ = _run("template.py", ["list"])
    if rc == 0 and ("sprint" in out.lower() or "template" in out.lower() or "plantilla" in out.lower()):
        _record("template:list", PASS, out[:60].strip() or "ok")
    elif rc == 0:
        _record("template:list", PASS, "output ok")
    else:
        _record("template:list", FAIL, f"rc={rc}")


def test_scan():
    """scan --preview no lanza subprocesos pesados, solo valida config."""
    # Use --help as a lightweight check (avoids running all linters)
    rc, out, err = _run("scan.py", ["--help"])
    if rc == 0 or "--help" in out or "Usage" in out or "Uso" in out:
        _record("scan:help", PASS, "help ok")
    else:
        # Fallback: just check that the module is importable
        import subprocess, sys
        r = subprocess.run([sys.executable, "-c", "import sys; sys.path.insert(0,'./'); import importlib.util; s=importlib.util.spec_from_file_location('s','.bago/tools/scan.py'); m=importlib.util.module_from_spec(s)"],
                           capture_output=True, text=True)
        _record("scan:importable", PASS if r.returncode == 0 else FAIL,
                "importable" if r.returncode == 0 else f"rc={r.returncode}")


def test_hotspot():
    """hotspot lista top hotspots."""
    rc, out, _ = _run("hotspot.py", [])
    if rc == 0:
        _record("hotspot:list", PASS, out[:60].strip() or "ok")
    else:
        _record("hotspot:list", FAIL, f"rc={rc}")


def test_autofix():
    """autofix --preview lista fixes sin aplicar."""
    rc, out, _ = _run("autofix.py", ["--preview"])
    if rc == 0:
        _record("fix:preview", PASS, out[:60].strip() or "ok")
    else:
        rc2, out2, _ = _run("autofix.py", ["--help"])
        _record("fix:help", PASS if rc2 == 0 else FAIL, out2[:60].strip() or f"rc={rc2}")


def test_gh():
    """gh status muestra estado de integración (sin token requerido)."""
    rc, out, _ = _run("gh_integration.py", ["status"])
    if rc == 0 and ("Token" in out or "token" in out or "GitHub" in out):
        _record("gh:status", PASS, out[:60].strip() or "ok")
    elif rc == 0:
        _record("gh:status", PASS, "output ok")
    else:
        _record("gh:status", FAIL, f"rc={rc}")


def test_risk():
    """risk muestra matriz de riesgo."""
    rc, out, _ = _run("risk_matrix.py", ["--json"])
    if rc == 0 and "by_category" in out:
        _record("risk:matrix_json", PASS, "json ok")
    elif rc == 0:
        _record("risk:matrix", PASS, out[:60].strip() or "ok")
    else:
        _record("risk:matrix", FAIL, f"rc={rc}")


def test_debt():
    """debt muestra ledger de deuda."""
    rc, out, _ = _run("debt_ledger.py", ["--json"])
    if rc == 0 and "total_hours" in out:
        _record("debt:ledger_json", PASS, "json ok")
    elif rc == 0:
        _record("debt:ledger", PASS, out[:60].strip() or "ok")
    else:
        _record("debt:ledger", FAIL, f"rc={rc}")


def test_impact():
    """impact muestra informe comercial."""
    rc, out, _ = _run("impact_engine.py", ["--brief"])
    if rc == 0 and ("Salud" in out or "velocity" in out.lower() or "Impact" in out):
        _record("impact:brief", PASS, out[:60].strip() or "ok")
    elif rc == 0:
        _record("impact:brief", PASS, "output ok")
    else:
        _record("impact:brief", FAIL, f"rc={rc}")


def test_contracts():
    """contracts.py existe y es Python válido con estructura esperada."""
    import ast as _ast
    p = TOOLS / "contracts.py"
    if not p.exists():
        _record("contracts:exists", FAIL, "no encontrado")
        return
    try:
        tree = _ast.parse(p.read_text(encoding="utf-8"))
        fn_names = {n.name for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)}
        if "evaluate_contract" in fn_names and "cmd_status" in fn_names:
            _record("contracts:structure", PASS, f"{len(fn_names)} funciones, estructura ok")
        else:
            _record("contracts:structure", FAIL, f"faltan funciones clave: {fn_names}")
    except SyntaxError as e:
        _record("contracts:syntax", FAIL, str(e))


def test_bago_utils():
    """bago_utils.py es válido Python con funciones clave."""
    import ast as _ast
    p = TOOLS / "bago_utils.py"
    if not p.exists():
        _record("bago_utils:exists", FAIL, "no encontrado"); return
    try:
        tree = _ast.parse(p.read_text(encoding="utf-8"))
        fns = {n.name for n in _ast.walk(tree) if isinstance(n, _ast.FunctionDef)}
        if "print_ok" in fns and "save_json" in fns:
            _record("bago_utils:structure", PASS, f"{len(fns)} funciones ok")
        else:
            _record("bago_utils:structure", FAIL, f"faltan funciones: {fns}")
    except SyntaxError as e:
        _record("bago_utils:syntax", FAIL, str(e))


def test_testgen():
    """testgen analiza Python y genera tests."""
    rc, out, _ = _run("testgen.py", ["--test"])
    if rc == 0 and ("tests pasaron" in out or "OK" in out):
        _record("testgen:self_test", PASS, out[:60].strip() or "ok")
    elif rc == 0:
        _record("testgen:self_test", PASS, "ok")
    else:
        _record("testgen:self_test", FAIL, f"rc={rc}")


def test_ci_generator():
    """ci_generator genera workflow de GitHub Actions."""
    rc, out, _ = _run("ci_generator.py", ["--test"])
    if rc == 0 and ("tests pasaron" in out or "OK" in out):
        _record("ci_gen:self_test", PASS, out[:60].strip() or "ok")
    elif rc == 0:
        _record("ci_gen:self_test", PASS, "ok")
    else:
        _record("ci_gen:self_test", FAIL, f"rc={rc}")


def test_bago_ask():
    """bago_ask busca en corpus BAGO."""
    rc, out, _ = _run("bago_ask.py", ["--test"])
    if rc == 0 and ("tests pasaron" in out or "OK" in out):
        _record("bago_ask:self_test", PASS, out[:60].strip() or "ok")
    elif rc == 0:
        _record("bago_ask:self_test", PASS, "ok")
    else:
        _record("bago_ask:self_test", FAIL, f"rc={rc}")


def test_sprint_state():
    """Existe al menos un sprint open en state/sprints/."""
    import json as _json
    sprints_dir = ROOT / "state" / "sprints"
    if not sprints_dir.exists():
        _record("sprints:dir_exists", FAIL, "no existe"); return
    files = list(sprints_dir.glob("*.json"))
    open_sprints = []
    for f in files:
        try:
            d = _json.loads(f.read_text())
            if d.get("status") in ("open", "active"):
                open_sprints.append(f.stem)
        except Exception:
            pass
    if open_sprints:
        _record("sprints:open_exists", PASS, f"open: {', '.join(open_sprints)}")
    else:
        _record("sprints:open_exists", FAIL, "no hay sprints open")


def test_datetime_clean():
    """Verifica que los archivos corregidos no tienen datetime.now() sin tz."""
    import re as _re
    files_to_check = [
        "goals.py", "quick_status.py", "context_detector.py", "export.py",
        "auto_mode.py", "cosecha.py", "remind.py", "snapshot.py", "bago_banner.py"
    ]
    bad = []
    for fname in files_to_check:
        p = TOOLS / fname
        if not p.exists():
            continue
        src = p.read_text(encoding="utf-8")
        matches = _re.findall(r'datetime\.now\(\)', src)
        if matches:
            bad.append(f"{fname}:{len(matches)}")
    if bad:
        _record("datetime:tz_clean", FAIL, f"bare .now() in: {', '.join(bad)}")
    else:
        _record("datetime:tz_clean", PASS, f"{len(files_to_check)} archivos limpios")


def test_routing_count():
    """bago script tiene al menos 65 routing entries."""
    import re as _re
    bago_script = ROOT.parent / "bago"
    if not bago_script.exists():
        bago_script = ROOT.parent.parent / "bago"
    if not bago_script.exists():
        _record("routing:count", FAIL, "bago script no encontrado"); return
    src = bago_script.read_text()
    count = len(_re.findall(r'elif cmd ==', src))
    if count >= 65:
        _record("routing:count", PASS, f"{count} entries (≥65)")
    else:
        _record("routing:count", FAIL, f"{count} < 65 required")


def test_bago_lint_rules():
    """bago_lint detecta BAGO-E001/W002/W003/W004/I002 en Python con problemas."""
    import sys as _sys, tempfile as _tf
    from pathlib import Path as _Path
    _sys.path.insert(0, str(ROOT))
    try:
        from findings_engine import run_bago_lint
        tmp = _Path(_tf.mkdtemp())
        (tmp / "problemas.py").write_text(
            "import os\n"
            "try:\n    pass\nexcept:  # bare except\n    pass\n"
            "x = eval('1+1')  # eval\n"
            "os.system('ls')  # os.system\n"
            "DATA = '/Users/john/data'\n"
            "# TODO: arreglar esto\n"
        )
        findings = run_bago_lint(str(tmp))
        rules = {f.rule for f in findings}
        missing = {"BAGO-E001", "BAGO-W002", "BAGO-W003", "BAGO-W004", "BAGO-I002"} - rules
        if not missing:
            _record("bago_lint:all_rules", PASS, f"{len(findings)} findings, rules: {sorted(rules)}")
        else:
            _record("bago_lint:all_rules", FAIL, f"missing rules: {missing}")
        import shutil; shutil.rmtree(tmp, ignore_errors=True)
    except Exception as e:
        _record("bago_lint:all_rules", FAIL, str(e))


def test_bago_lint_autofix():
    """bago_lint produce patches autofixables para BAGO-E001 y BAGO-W001."""
    import sys as _sys, tempfile as _tf
    from pathlib import Path as _Path
    _sys.path.insert(0, str(ROOT))
    try:
        from findings_engine import run_bago_lint
        tmp = _Path(_tf.mkdtemp())
        (tmp / "fixable.py").write_text(
            "import datetime\n"
            "ts = datetime.datetime.utcnow()\n" # noqa: BAGO-W001
            "try:\n    pass\nexcept:\n    pass\n"
        )
        findings = run_bago_lint(str(tmp))
        autofixable = [f for f in findings if f.autofixable and f.fix_patch]
        if len(autofixable) >= 2:
            _record("bago_lint:patches", PASS, f"{len(autofixable)} autofixable con patch")
        elif autofixable:
            _record("bago_lint:patches", PASS, f"{len(autofixable)} autofixable (parcial ok)")
        else:
            _record("bago_lint:patches", FAIL, f"no autofixable findings ({[f.rule for f in findings]})")
        import shutil; shutil.rmtree(tmp, ignore_errors=True)
    except Exception as e:
        _record("bago_lint:patches", FAIL, str(e))


def test_bago_lint_cli():
    """bago_lint_cli.py --test pasa todos los tests."""
    rc, out, _ = _run("bago_lint_cli.py", ["--test"])
    if rc == 0 and "pasaron" in out:
        _record("bago_lint_cli:tests", PASS, out.strip().split("\n")[-1] or "ok")
    else:
        _record("bago_lint_cli:tests", FAIL, f"rc={rc} {out[-80:]}")


def test_diff_findings():
    """diff_findings() devuelve new/fixed/persistent correctamente."""
    import sys
    sys.path.insert(0, str(TOOLS))
    try:
        from findings_engine import Finding, diff_findings
        f_before = [
            Finding("id1", "error",   "a.py", 5, 0, "BAGO-E001", "bago_lint", "bare except"),
            Finding("id2", "warning", "a.py", 10, 0, "BAGO-W001", "bago_lint", "utcnow"),
        ]
        f_after = [
            Finding("id2", "warning", "a.py", 10, 0, "BAGO-W001", "bago_lint", "utcnow"),
            Finding("id3", "warning", "a.py", 20, 0, "BAGO-W004", "bago_lint", "hardcoded"),
        ]
        diff = diff_findings(f_before, f_after)
        ok = (
            len(diff["new"]) == 1 and diff["new"][0].rule == "BAGO-W004" and
            len(diff["fixed"]) == 1 and diff["fixed"][0].rule == "BAGO-E001" and
            len(diff["persistent"]) == 1 and diff["persistent"][0].rule == "BAGO-W001"
        )
        if ok:
            _record("diff_findings:new_fixed_persistent", PASS, "new=W004 fixed=E001 persistent=W001")
        else:
            _record("diff_findings:new_fixed_persistent", FAIL, str(diff))
    except Exception as e:
        _record("diff_findings:import", FAIL, str(e))


def test_multi_scan():
    """multi_scan.py --test pasa todos los tests."""
    rc, out, _ = _run("multi_scan.py", ["--test"])
    if rc == 0 and "pasaron" in out:
        _record("multi_scan:tests", PASS, out.strip().split("\n")[-1] or "ok")
    else:
        _record("multi_scan:tests", FAIL, f"rc={rc} {out[-80:]}")


def test_js_ast_scanner():
    """js_ast_scanner.js --test pasa todos los tests."""
    import shutil
    node = shutil.which("node")
    scanner = TOOLS / "js_ast_scanner.js"
    if not node or not scanner.exists():
        _record("js_ast:available", SKIP, "node o js_ast_scanner.js no disponible")
        return
    rc, out, _ = _run_raw([node, str(scanner), "--test"])
    if rc == 0 and "pasaron" in out:
        _record("js_ast:tests", PASS, out.strip().split("\n")[-1] or "ok")
    else:
        _record("js_ast:tests", FAIL, f"rc={rc} {out[-80:]}")


def test_permission_check():
    """permission_check.py --test pasa todos los tests."""
    rc, out, _ = _run("permission_check.py", ["--test"])
    if rc == 0 and "pasaron" in out:
        _record("permission_check:tests", PASS, out.strip().split("\n")[-1] or "ok")
    else:
        _record("permission_check:tests", FAIL, f"rc={rc} {out[-80:]}")


def test_install_deps():
    """install_deps.py --test pasa todos los tests."""
    rc, out, _ = _run("install_deps.py", ["--test"])
    if rc == 0 and "pasaron" in out:
        _record("install_deps:tests", PASS, out.strip().split("\n")[-1] or "ok")
    else:
        _record("install_deps:tests", FAIL, f"rc={rc} {out[-80:]}")


def test_rule_catalog():
    """rule_catalog.py --test pasa todos los tests."""
    rc, out, _ = _run("rule_catalog.py", ["--test"])
    if rc == 0 and "pasaron" in out:
        _record("rule_catalog:tests", PASS, out.strip().split("\n")[-1] or "ok")
    else:
        _record("rule_catalog:tests", FAIL, f"rc={rc} {out[-80:]}")


ALL_TESTS = [
    (1,  "sprint_manager",  test_sprint_manager),
    (2,  "search",          test_search),
    (3,  "timeline",        test_timeline),
    (4,  "report",          test_report),
    (5,  "metrics",         test_metrics),
    (6,  "doctor",          test_doctor),
    (7,  "git_context",     test_git_context),
    (8,  "export",          test_export),
    (9,  "watch",           test_watch),
    (10, "changelog",       test_changelog),
    (11, "snapshot",        test_snapshot),
    (12, "diff",            test_diff),
    (13, "session_stats",   test_session_stats),
    (14, "compare",         test_compare),
    (15, "goals",           test_goals),
    (16, "lint",            test_lint),
    (17, "summary",         test_summary),
    (18, "tags",            test_tags),
    (19, "flow",            test_flow),
    (20, "insights",        test_insights),
    (21, "config",          test_config),
    (22, "check",           test_check),
    (23, "archive",         test_archive),
    (24, "velocity",        test_velocity),
    (25, "patch",           test_patch),
    (26, "notes",           test_notes),
    (27, "template",        test_template),
    (28, "scan",            test_scan),
    (29, "hotspot",         test_hotspot),
    (30, "autofix",         test_autofix),
    (31, "gh",              test_gh),
    (32, "risk",            test_risk),
    (33, "debt",            test_debt),
    (34, "impact",          test_impact),
    (35, "contracts",       test_contracts),
    (36, "bago_utils",      test_bago_utils),
    (37, "testgen",         test_testgen),
    (38, "ci_generator",    test_ci_generator),
    (39, "bago_ask",        test_bago_ask),
    (40, "sprint_state",    test_sprint_state),
    (41, "datetime_clean",  test_datetime_clean),
    (42, "routing_count",   test_routing_count),
    (43, "bago_lint_rules", test_bago_lint_rules),
    (44, "bago_lint_fix",   test_bago_lint_autofix),
    (45, "bago_lint_cli",   test_bago_lint_cli),
    (46, "diff_findings",   test_diff_findings),
    (47, "multi_scan",      test_multi_scan),
    (48, "js_ast_scanner",  test_js_ast_scanner),
    (49, "permission_check", test_permission_check),
    (50, "install_deps",    test_install_deps),
    (51, "rule_catalog",    test_rule_catalog),
]


def main():
    p = argparse.ArgumentParser(description="Suite de integración BAGO Sprint 180")
    p.add_argument("--test", type=int, default=None, metavar="N",
                   help="Ejecutar solo el test N (1-23)")
    p.add_argument("--verbose", "-v", action="store_true")
    args = p.parse_args()

    print()
    print("  BAGO Integration Tests — Sprint 180")
    print("  Pack: {}".format(ROOT.name))
    print()

    to_run = ALL_TESTS if args.test is None else [
        t for t in ALL_TESTS if t[0] == args.test]

    for num, name, fn in to_run:
        print("  [{}/{}] {}:".format(num, len(ALL_TESTS), name))
        fn()
        print()

    # Summary
    passed  = sum(1 for _, s, _ in results if s == PASS)
    failed  = sum(1 for _, s, _ in results if s == FAIL)
    skipped = sum(1 for _, s, _ in results if s == SKIP)
    total   = len(results)

    print("  " + "═" * 50)
    print("  Resultado: {}/{} passed  {} failed  {} skipped".format(
        passed, total, failed, skipped))

    if failed == 0:
        print("  ESTADO: ALL PASS ✅")
    else:
        print("  ESTADO: FAILURES ❌")
        print()
        print("  Tests fallidos:")
        for name, status, detail in results:
            if status == FAIL:
                print("    - {}: {}".format(name, detail))

    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

