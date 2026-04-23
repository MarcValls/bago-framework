#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).parent))
from bago_utils import get_state_dir, get_bago_tools_dir, get_project_root

_BAGO_ROOT  = Path(__file__).resolve().parent.parent   # .bago/
ROOT        = get_project_root()                        # project root (BAGO_PROJECT_ROOT or parent of .bago)
_STATE      = get_state_dir()                           # env-aware state dir
_TOOLS      = get_bago_tools_dir()
MIN_IDEAS = 5
MAX_IDEAS = 20

FALLBACK_IDEAS: list[dict[str, object]] = [
    {
        "priority": 66,
        "section": "respaldo",
        "risk": "low",
        "metric": "README y selector describen la misma ruta de arranque.",
        "title": "Alinear README con selector",
        "summary": "Hacer que la entrada humana y el selector de ideas expliquen el mismo recorrido sin ambiguedades.",
        "detail": [
            "Entrada: README y comandos cortos del pack.",
            "Salida: navegacion coherente entre ideas, WF y arranque.",
            "Ventaja: reduce la friccion en el primer paso de cada sesion.",
        ],
        "w2": "Actualizar la documentacion de entrada sin tocar la logica del selector.",
    },
    {
        "priority": 64,
        "section": "respaldo",
        "risk": "low",
        "metric": "El selector siempre publica el rango 5-20 sin desviaciones.",
        "title": "Reforzar rango del selector",
        "summary": "Hacer explicito el limite de 5 a 20 ideas en la salida del selector.",
        "detail": [
            "Entrada: enumeracion actual del selector.",
            "Salida: reglas de cantidad visibles para el usuario.",
            "Ventaja: evita listas demasiado cortas o excesivas.",
        ],
        "w2": "Codificar el rango de salida en el selector y verificarlo con una ejecucion real.",
    },
    {
        "priority": 62,
        "section": "respaldo",
        "risk": "low",
        "metric": "La recomendacion final queda en una sola accion explícita.",
        "title": "Compactar recomendacion final",
        "summary": "Reducir la friccion del final del selector con una recomendacion mas directa.",
        "detail": [
            "Entrada: salida de ideas ya ordenadas.",
            "Salida: siguiente paso corto y visible.",
            "Ventaja: facilita pasar de idea a decision sin leer de nuevo toda la lista.",
        ],
        "w2": "Ajustar el texto final de `./ideas` sin alterar el ranking.",
    },
    {
        "priority": 58,
        "section": "respaldo",
        "risk": "low",
        "metric": "Sesión activa abierta con summary y workflow antes de W2.",
        "title": "Abrir sesión de trabajo con contexto",
        "summary": "Registrar una sesión BAGO antes de iniciar trabajo para que los commits queden vinculados.",
        "detail": [
            "Entrada: sesiones recientes y estado del detector.",
            "Salida: SES-*.json con descripcion y workflow asignado.",
            "Ventaja: evita commits huérfanos y preserva continuidad.",
        ],
        "w2": "Ejecutar `bago session` para abrir o continuar la sesión activa.",
    },
    {
        "priority": 54,
        "section": "respaldo",
        "risk": "low",
        "metric": "Documentación del sprint activo refleja el estado real.",
        "title": "Sincronizar documentación de sprint",
        "summary": "Actualizar el sprint activo con decisiones, cambios y progreso del ciclo en curso.",
        "detail": [
            "Entrada: SPRINT-*.json activo y cambios pendientes.",
            "Salida: sprint con status, goals y evidencias actualizadas.",
            "Ventaja: el estado del sprint es auditable y no requiere reconstrucción.",
        ],
        "w2": "Ejecutar `bago sprint status` y actualizar los campos desactualizados.",
    },
    {
        "priority": 60,
        "section": "respaldo",
        "risk": "low",
        "metric": "El indicador vm muestra datos reales en lugar de 'no disponible'.",
        "title": "Stub report para indicador vm",
        "summary": "Crear un sandbox/runtime-vm/last-report-vm.json mínimo para que el selector muestre estado vm.",
        "detail": [
            "Entrada: sandbox/runtime-vm/ actualmente vacío.",
            "Salida: last-report-vm.json con status y failure_count.",
            "Ventaja: los 4 indicadores del selector muestran datos reales.",
        ],
        "w2": "Crear sandbox/runtime-vm/ y escribir last-report-vm.json con status=pass y failure_count=0.",
    },
    {
        "priority": 57,
        "section": "respaldo",
        "risk": "low",
        "metric": "El smoke se ejecuta automáticamente después de cada commit.",
        "title": "Hook post-commit para bago smoke",
        "summary": "Añadir .git/hooks/post-commit que ejecute bago smoke y actualice last-report.json.",
        "detail": [
            "Entrada: .git/hooks/ vacío.",
            "Salida: hook ejecutable que lanza smoke en background.",
            "Ventaja: el indicador de smoke siempre refleja el último commit.",
        ],
        "w2": "Crear .git/hooks/post-commit con `bago smoke &` y hacerlo ejecutable.",
    },
    {
        "priority": 53,
        "section": "respaldo",
        "risk": "low",
        "metric": "README badges muestran el conteo correcto de tests, CHGs y tools.",
        "title": "Sincronizar badges README con global_state",
        "summary": "Actualizar automáticamente los shields.io del README leyendo los valores de global_state.json.",
        "detail": [
            "Entrada: README.md con badges estáticos y global_state.json con valores reales.",
            "Salida: script que reescribe los badges con los conteos actuales.",
            "Ventaja: el README siempre muestra cifras fieles al estado del sistema.",
        ],
        "w2": "Crear tools/sync_readme_badges.py que lee global_state y reescribe las líneas de shields.io.",
    },
    {
        "priority": 50,
        "section": "respaldo",
        "risk": "low",
        "metric": "smoke_runner.py tiene ≥3 tests de integración propios.",
        "title": "Tests de integración para smoke_runner",
        "summary": "Ampliar integration_tests.py con tests que cubran smoke_runner.py end-to-end.",
        "detail": [
            "Entrada: smoke_runner.py con 3 self-tests pero sin tests en la suite principal.",
            "Salida: test_smoke_runner_*() en integration_tests.py.",
            "Ventaja: el runner de smoke queda bajo el mismo gate de calidad que el resto.",
        ],
        "w2": "Añadir test_smoke_runner_pass(), test_smoke_runner_report_keys() y test_smoke_runner_isolated() a integration_tests.py.",
    },
    {
        "priority": 47,
        "section": "respaldo",
        "risk": "low",
        "metric": "Los últimos 5 CHGs son visibles en la salida de bago dashboard.",
        "title": "Últimos CHGs en bago dashboard",
        "summary": "Mostrar los 5 cambios más recientes en la sección inferior del dashboard.",
        "detail": [
            "Entrada: state/changes/ con CHGs ordenados por created_at.",
            "Salida: bloque 'Cambios recientes' en bago dashboard con id, título y fecha.",
            "Ventaja: el dashboard es el punto de partida completo de cada sesión.",
        ],
        "w2": "Modificar metrics_dashboard.py para leer los 5 CHGs más recientes y añadirlos al output.",
    },
    {
        "priority": 44,
        "section": "respaldo",
        "risk": "low",
        "metric": "Los scan files de más de 30 días se eliminan automáticamente.",
        "title": "Auto-limpieza de scans antiguos",
        "summary": "Añadir rutina de limpieza en scan.py o como comando bago que elimine SCAN-*.json obsoletos.",
        "detail": [
            "Entrada: state/findings/ con hasta 45 archivos de scans históricos.",
            "Salida: solo se conservan los SCAN de los últimos 30 días.",
            "Ventaja: el state no crece indefinidamente y risk_matrix lee datos relevantes.",
        ],
        "w2": "Añadir función purge_old_scans(days=30) en scan.py invocable como `bago scan --purge`.",
    },
    {
        "priority": 41,
        "section": "respaldo",
        "risk": "low",
        "metric": "La sección 'Observaciones' del reporte de evolución es dinámica.",
        "title": "Observaciones dinámicas en reporte evolución",
        "summary": "Reemplazar el texto fijo de Observaciones por puntos generados desde global_state y métricas reales.",
        "detail": [
            "Entrada: BAGO_EVOLUCION_SISTEMA.md con observaciones hardcodeadas.",
            "Salida: bullets generados dinámicamente (health, tests, changes, smoke).",
            "Ventaja: el reporte refleja el estado real del sistema en cada ejecución.",
        ],
        "w2": "Modificar generate_bago_evolution_report.py para construir la sección Observaciones desde variables.",
    },
    {
        "priority": 38,
        "section": "respaldo",
        "risk": "low",
        "metric": "El dashboard no muestra métricas de cobertura de tests por módulo.",
        "title": "Coverage por módulo en dashboard",
        "summary": "Añadir sección en pack_dashboard.py mostrando % de tools cubiertos por tests en integration_tests.",
        "detail": [
            "Entrada: integration_tests.py + lista de tools en .bago/tools/.",
            "Salida: porcentaje de cobertura y lista de tools sin test.",
            "Ventaja: visibilidad directa de gaps de cobertura.",
        ],
        "w2": "Parsear ALL_TESTS en integration_tests.py para extraer qué tools tienen test y calcular % sobre todos los .py.",
    },
    {
        "priority": 35,
        "section": "respaldo",
        "risk": "low",
        "metric": "bago scan --purge no tiene test de integración.",
        "title": "Tests para scan --purge",
        "summary": "Añadir test_scan_purge() en integration_tests.py que verifique que --purge elimina solo archivos viejos.",
        "detail": [
            "Crear SCAN-*.json sintéticos con mtime antiguo en tmp dir.",
            "Ejecutar scan.py --purge --days 0 con BAGO_STATE_DIR apuntando al tmp.",
            "Verificar que solo los archivos con mtime < cutoff fueron eliminados.",
        ],
        "w2": "Añadir test_scan_purge() a integration_tests.py, registrar en ALL_TESTS.",
    },
    {
        "priority": 55,
        "section": "respaldo",
        "risk": "low",
        "metric": "Dashboard muestra deuda 0.0h/€0 pero debt_ledger tiene datos reales.",
        "title": "Dashboard deuda real desde debt_ledger",
        "summary": "Hacer que section_debt() en pack_dashboard.py lea debt_ledger.json real en lugar de calcular desde scan.",
        "detail": [
            "Leer state/debt_ledger.json si existe para obtener total_hours y total_cost.",
            "Mostrar en sección DEUDA TÉCNICA con datos reales.",
            "Fallback a cálculo actual si el fichero no existe.",
        ],
        "w2": "Actualizar section_debt() en pack_dashboard.py para leer debt_ledger.json.",
    },
    {
        "priority": 52,
        "section": "respaldo",
        "risk": "low",
        "metric": "Dashboard muestra exposición 0.0 pero puede haber risk_matrix real.",
        "title": "Dashboard riesgo real desde risk_matrix --json",
        "summary": "Verificar que section_risks() en pack_dashboard.py muestra exposición real cuando risk_matrix tiene datos.",
        "detail": [
            "Añadir test que ejecute risk_matrix --json y compare con lo mostrado en dashboard.",
            "Asegurar que cuando exposure > 0 el dashboard no muestra 'Sin riesgos activos'.",
            "Ya verificado por test_dashboard_risk_exposure — confirmar que funciona end-to-end.",
        ],
        "w2": "Añadir test de regresión end-to-end risk → dashboard en integration_tests.py.",
    },
    {
        "priority": 44,
        "section": "respaldo",
        "risk": "low",
        "metric": "findings_engine.py no tiene test directo en ALL_TESTS.",
        "title": "Test directo para findings_engine",
        "summary": "Añadir test_findings_engine() que verifique CRUD de findings con BAGO_STATE_DIR isolation.",
        "detail": [
            "Crear finding sintético con findings_engine.save_finding() en tmp dir.",
            "Verificar que load_findings() lo recupera correctamente.",
            "Verificar que el finding aparece en list_findings() filtrado por severity.",
        ],
        "w2": "Añadir test_findings_engine() a integration_tests.py, registrar en ALL_TESTS.",
    },
    {
        "priority": 40,
        "section": "respaldo",
        "risk": "low",
        "metric": "sync_badges.py no tiene test de integración en ALL_TESTS.",
        "title": "Test para sync_badges",
        "summary": "Añadir test_sync_badges() que verifique que sync_badges actualiza README con datos de global_state.",
        "detail": [
            "Ejecutar sync_badges.py sobre README temporal.",
            "Verificar que las badges shields.io se actualizan con los datos de global_state.json.",
            "Verificar que el script sale rc=0.",
        ],
        "w2": "Añadir test_sync_badges() a integration_tests.py, registrar en ALL_TESTS.",
    },
    {
        "priority": 50,
        "section": "respaldo",
        "risk": "low",
        "metric": "scan.py no tiene modo --dry-run para previsualizar sin escribir archivos.",
        "title": "scan --dry-run mode",
        "summary": "Añadir --dry-run a scan.py: ejecuta análisis pero no escribe SCAN-*.json, solo imprime conteo.",
        "detail": [
            "Añadir argparse flag --dry-run en scan.py main().",
            "Cuando --dry-run, realizar el scan normal pero no llamar db.save().",
            "Imprimir '(dry-run) N hallazgos encontrados, no se escribió SCAN file'.",
        ],
        "w2": "Añadir --dry-run flag a scan.py y test_scan_dry_run() en integration_tests.py.",
    },
    {
        "priority": 48,
        "section": "respaldo",
        "risk": "low",
        "metric": "generate_bago_evolution_report.py no tiene test en ALL_TESTS.",
        "title": "Test para evolution report HTML",
        "summary": "Añadir test que verifique que generate_bago_evolution_report.py produce HTML válido con secciones requeridas.",
        "detail": [
            "Ejecutar generate_bago_evolution_report.py con --html.",
            "Verificar que el output contiene <html>, <h1>, Observaciones.",
            "Verificar rc=0.",
        ],
        "w2": "Añadir test_evolution_report_html() a integration_tests.py, registrar en ALL_TESTS.",
    },
    {
        "priority": 46,
        "section": "respaldo",
        "risk": "low",
        "metric": "Dashboard sección INVENTARIO no está verificada contra state/ real.",
        "title": "Test inventario dashboard vs state real",
        "summary": "Añadir test que compare conteos de sesiones/cambios del dashboard con ficheros reales en state/.",
        "detail": [
            "Contar BAGO-CHG-*.json en state/changes/ y sesiones en state/sessions/.",
            "Ejecutar pack_dashboard.py --json y comparar con conteos reales.",
            "Verificar que la diferencia es ≤2 (margen de race condition).",
        ],
        "w2": "Añadir test_dashboard_inventory_accuracy() a integration_tests.py, registrar en ALL_TESTS.",
    },
    {
        "priority": 42,
        "section": "respaldo",
        "risk": "low",
        "metric": "artifact_counter.py no tiene test en ALL_TESTS.",
        "title": "Test para artifact_counter",
        "summary": "Añadir test que verifique que artifact_counter.py cuenta artefactos correctamente.",
        "detail": [
            "Ejecutar artifact_counter.py con --json si disponible.",
            "Verificar rc=0 y que retorna un número entero de artefactos.",
        ],
        "w2": "Añadir test_artifact_counter() a integration_tests.py, registrar en ALL_TESTS.",
    },
    {
        "priority": 50,
        "section": "respaldo",
        "risk": "low",
        "metric": "stability_tracker.py no tiene test de regresión en ALL_TESTS.",
        "title": "Test para stability_tracker",
        "summary": "Añadir test que verifique que stability_tracker.py retorna rc=0 con output estructurado.",
        "detail": [
            "Ejecutar stability_tracker.py y verificar rc=0.",
            "Verificar que el output contiene una puntuación de estabilidad.",
        ],
        "w2": "Añadir test_stability_tracker() a integration_tests.py, registrar en ALL_TESTS.",
    },
    {
        "priority": 48,
        "section": "respaldo",
        "risk": "low",
        "metric": "scan.py --json no tiene test de estructura en ALL_TESTS.",
        "title": "scan --json output de hallazgos",
        "summary": "Añadir scan.py --json flag que emite hallazgos estructurados; test verifica formato.",
        "detail": [
            "Añadir --json a scan.py render_findings para emitir JSON.",
            "Test verifica rc=0, JSON con campo 'findings' y 'total'.",
        ],
        "w2": "Modificar render_findings para soportar --json y añadir test_scan_json() a ALL_TESTS.",
    },
    {
        "priority": 46,
        "section": "respaldo",
        "risk": "low",
        "metric": "health_check.py (u otros) no tiene test en ALL_TESTS.",
        "title": "Test para health score CLI",
        "summary": "Añadir test que ejecuta el comando bago health y verifica que produce score numérico.",
        "detail": [
            "Ejecutar pack_health.py o equivalente con --json.",
            "Verificar rc=0 y un campo score o health >= 0.",
        ],
        "w2": "Añadir test_health_score() a integration_tests.py, registrar en ALL_TESTS.",
    },
    {
        "priority": 44,
        "section": "respaldo",
        "risk": "low",
        "metric": "session_manager.py no tiene test directo en ALL_TESTS.",
        "title": "Test para session_manager --list",
        "summary": "Verificar que session_manager.py --list retorna rc=0 y lista de sesiones.",
        "detail": [
            "Ejecutar session_manager.py --list.",
            "Verificar rc=0 y que output contiene al menos una sesión SES-*.",
        ],
        "w2": "Añadir test_session_manager_list() a integration_tests.py, registrar en ALL_TESTS.",
    },
]


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def file_exists(path: Path) -> bool:
    return path.exists() and path.is_file()


def parse_state_sections(state_text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = None
    buffer: list[str] = []

    for line in state_text.splitlines():
        if line.startswith("## "):
            if current is not None:
                sections[current] = "\n".join(buffer).strip()
            current = line[3:].strip().lower()
            buffer = []
            continue
        if current is not None:
            buffer.append(line)

    if current is not None:
        sections[current] = "\n".join(buffer).strip()
    return sections


def score(pairs: list[tuple[int, str]]) -> list[tuple[int, str]]:
    return sorted(pairs, key=lambda item: (-item[0], item[1]))


def report_status(path: Path) -> dict | None:
    if not file_exists(path):
        return None
    try:
        return load_json(path)
    except Exception:
        return None


def summarize_report(name: str, report: dict | None) -> str:
    if not report:
        return f"{name}: no disponible"
    status = report.get("status", report.get("overall_status", "unknown"))
    return (
        f"{name}: status={status}, "
        f"failures={report.get('failure_count', 'n/a')}, "
        f"workers={report.get('workers', 'n/a')}, "
        f"duration={report.get('duration_seconds', 'n/a')}s"
    )


def order_ideas_by_section(sections: dict[str, list[dict[str, object]]]) -> list[dict[str, object]]:
    return sections["contextuales"] + sections["respaldo"]


# ── canonical gate ─────────────────────────────────────────────────────────────

def run_canonical_gate(smoke_path: Path) -> tuple[bool, list[str], list[str]]:
    """Run validate_pack + validate_state and check smoke if available.

    Returns (all_passed, ko_messages, warn_messages).
    KO on any canonical validator failure or if smoke is available but failing.
    WARN (non-blocking) if smoke is unavailable.
    """
    bago_tools = _TOOLS
    ko: list[str] = []
    warn: list[str] = []

    for script in ("validate_pack.py", "validate_state.py"):
        result = subprocess.run(
            [sys.executable, str(bago_tools / script)],
            capture_output=True,
            text=True,
        )
        out_lines = [l for l in (result.stdout + result.stderr).splitlines() if l.strip()]
        if result.returncode != 0:
            # Find the detail error line (comes after KO) or the KO line itself
            error_line = ""
            for i, line in enumerate(out_lines):
                if line.strip().startswith("KO") and i + 1 < len(out_lines):
                    error_line = out_lines[i + 1]
                    break
                if any(kw in line for kw in ("mismatch", "missing", "error", "Error", "reference found", "unknown")):
                    error_line = line
                    break
            if not error_line:
                error_line = out_lines[-1] if out_lines else script
            ko.append(f"  [KO] ✗ {script}: {error_line}")
        else:
            first_line = out_lines[-1] if out_lines else script
            warn.append(f"  [GO] ✓ {script}: {first_line}")

    smoke_report = report_status(smoke_path)
    if smoke_report is None:
        warn.append("  [WARN] ⚠ smoke: no disponible (no bloqueante)")
    else:
        smoke_status = str(smoke_report.get("status", "unknown")).lower()
        if smoke_status in ("pass", "ok", "green", "success") and smoke_report.get("failure_count", 1) == 0:
            warn.append(f"  [GO] ✓ smoke: status={smoke_status}")
        else:
            ko.append(f"  [KO] ✗ smoke: status={smoke_status}, failures={smoke_report.get('failure_count', 'n/a')}")

    return len(ko) == 0, ko, warn


def filter_ideas_for_baseline_mode(items: list[dict[str, object]]) -> list[dict[str, object]]:
    filtered: list[dict[str, object]] = []
    for item in items:
        risk = str(item.get("risk", "")).lower().strip()
        metric = str(item.get("metric", "")).strip()
        if risk != "low":
            continue
        if not metric:
            continue
        filtered.append(item)
    return filtered


def detect_implemented_features() -> dict[str, bool]:
    """Detecta qué ideas ya están implementadas inspeccionando el filesystem."""
    tools = _TOOLS
    state = _STATE
    bago_readme = _BAGO_ROOT / "README.md"
    banner_text = (tools / "bago_banner.py").read_text(encoding="utf-8") if (tools / "bago_banner.py").exists() else ""

    def _pending_task_is_active() -> bool:
        task_file = state / "pending_w2_task.json"
        if not task_file.exists():
            return False
        try:
            data = json.loads(task_file.read_text(encoding="utf-8"))
            return data.get("status") == "pending"
        except Exception:
            return False

    return {
        "handoff_w2":       (tools / "show_task.py").exists(),
        "stability_cmd":    (ROOT / "stability-summary").exists() and (tools / "stability_summary.py").exists(),
        "ideas_wrapper":    (ROOT / "ideas").exists(),
        "gate_in_code":     True,  # siempre presente en emit_ideas.py
        "readme_aligned":   bago_readme.exists() and "bago stability" in bago_readme.read_text(encoding="utf-8"),
        "pending_task":     _pending_task_is_active(),
        "session_opener":   (tools / "session_opener.py").exists(),
        "banner_shows_task": "_active_task" in banner_text,
        "impl_registry":    (state / "implemented_ideas.json").exists(),
    }


def load_implemented_titles() -> set[str]:
    """Devuelve el conjunto de títulos de ideas ya registradas como implementadas."""
    impl_file = _STATE / "implemented_ideas.json"
    if not impl_file.exists():
        return set()
    try:
        data = json.loads(impl_file.read_text(encoding="utf-8"))
        return {str(e.get("title", "")) for e in data.get("implemented", [])}
    except Exception:
        return set()


def _title_similarity(a: str, b: str) -> float:
    """Simple token overlap similarity between two strings (0.0 to 1.0)."""
    tokens_a = set(a.lower().split())
    tokens_b = set(b.lower().split())
    if not tokens_a or not tokens_b:
        return 0.0
    overlap = tokens_a & tokens_b
    return len(overlap) / max(len(tokens_a), len(tokens_b))


def apply_dynamic_scoring(
    ideas: list[dict[str, object]],
    done_titles: set[str],
    penalty: int = 20,
    similarity_threshold: float = 0.5,
) -> list[dict[str, object]]:
    """Aplica penalización de score a ideas similares (no iguales) a las ya implementadas.

    Las ideas exactamente implementadas se filtran fuera; las similares bajan su prioridad.
    """
    result = []
    for idea in ideas:
        title = str(idea.get("title", ""))
        if title in done_titles:
            continue  # filtro exacto: ya implementada
        max_sim = max(
            (_title_similarity(title, done) for done in done_titles),
            default=0.0,
        )
        if max_sim >= similarity_threshold:
            adjusted = dict(idea)
            adjusted["priority"] = max(0, int(str(idea.get("priority", 0))) - penalty)
            adjusted["_penalized"] = True
            result.append(adjusted)
        else:
            result.append(idea)
    return result


def register_implemented_idea(title: str, idea_index: int) -> None:
    """Registra una idea como implementada en implemented_ideas.json."""
    impl_file = _STATE / "implemented_ideas.json"
    try:
        data = json.loads(impl_file.read_text(encoding="utf-8")) if impl_file.exists() else {}
    except Exception:
        data = {}
    entries = data.get("implemented", [])
    if not any(str(e.get("title", "")) == title for e in entries):
        entries.append({
            "title": title,
            "idea_index": idea_index,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        })
    data["implemented"] = entries
    impl_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def build_idea_sections(items: list[dict[str, object]], done_titles: set[str] | None = None) -> dict[str, list[dict[str, object]]]:
    # 5–20 range is intentional: below 5 risks too little choice for decision;
    # above 20 causes cognitive overload. If fewer than 5 are available, show all.
    done_titles = done_titles or set()
    contextual = [
        item
        for item in items
        if str(item.get("section", "contextuales")) == "contextuales"
    ]
    contextual = sorted(contextual, key=lambda item: (-int(item["priority"]), str(item["title"])))
    contextual = contextual[:MAX_IDEAS]  # hard cap: contextual ideas never exceed 20

    respaldo: list[dict[str, object]] = []
    if len(contextual) < MIN_IDEAS:
        seen_titles = {str(item["title"]) for item in contextual}
        for fallback in FALLBACK_IDEAS:
            if len(contextual) + len(respaldo) >= MIN_IDEAS:
                break
            title = str(fallback["title"])
            if title in seen_titles or title in done_titles:
                continue
            respaldo.append(dict(fallback))
            seen_titles.add(title)

    respaldo = sorted(respaldo, key=lambda item: (-int(item["priority"]), str(item["title"])))

    # Explicit final cap: total output must not exceed MAX_IDEAS (cognitive load boundary)
    if len(contextual) + len(respaldo) > MAX_IDEAS:
        excess = len(contextual) + len(respaldo) - MAX_IDEAS
        respaldo = respaldo[:max(0, len(respaldo) - excess)]

    return {"contextuales": contextual, "respaldo": respaldo}


def print_sectioned_ideas(sections: dict[str, list[dict[str, object]]]) -> None:
    total = len(sections["contextuales"]) + len(sections["respaldo"])
    print(
        f"Total ideas: {total} "
        f"(contextuales={len(sections['contextuales'])}, respaldo={len(sections['respaldo'])}) "
        f"[rango: {MIN_IDEAS}\u201320]"
    )
    counter = 1
    for item in order_ideas_by_section(sections):
        w2 = str(item.get("w2", "Sin siguiente paso definido"))
        print(f"{counter}. [{item['priority']}] {item['title']}")
        print(f"   descripcion: {item['summary']}")
        print(f"   siguiente paso: {w2}")
        print("")
        counter += 1


def render_handoff(selected: dict[str, object]) -> list[str]:
    title = str(selected["title"])
    summary = str(selected["summary"])
    detail = [str(line) for line in selected["detail"]]  # type: ignore[index]
    w2 = str(selected["w2"])
    metric = str(selected.get("metric", "")).strip()

    if title == "Handoff idea -> W2":
        objective = "Idea → tarea W2 lista para implementar."
        scope = "Salida accionable al aceptar; sin tocar ranking."
        non_scope = "Sin cambios al ranking ni reports."
        files = [
            ".bago/tools/emit_ideas.py",
        ]
        validation = [
            "`./ideas --detail 1` mantiene la salida actual.",
            "`./ideas --accept 1` muestra objetivo y validación.",
            "`./ideas` sin flags conserva el selector existente.",
        ]
    else:
        objective = summary
        scope = "Materializar con el mínimo cambio suficiente."
        non_scope = "No expandir el alcance fuera de la idea elegida."
        files = [".bago/tools/emit_ideas.py"]
        validation = [
            "Explica cambio, archivos y verificación mínima.",
        ]
        if metric:
            validation.append(f"Métrica objetivo: {metric}")

    lines = [
        "- Handoff:",
        f"  - Objetivo: {objective}",
        f"  - Alcance: {scope}",
        f"  - No alcance: {non_scope}",
        f"  - Archivos candidatos: {', '.join(files)}",
        "  - Validación mínima:",
    ]
    lines.extend(f"    - {item}" for item in validation)
    lines.append(f"  - Siguiente paso: {w2}")
    if detail:
        lines.append("  - Contexto de la idea:")
        lines.extend(f"    - {line}" for line in detail)
    return lines


def build_handoff_data(selected: dict[str, object], index: int) -> dict[str, object]:
    """Construye el dict estructurado del handoff para persistir en disco."""
    title = str(selected["title"])
    summary = str(selected["summary"])
    detail = [str(line) for line in selected["detail"]]  # type: ignore[index]
    w2 = str(selected["w2"])
    metric = str(selected.get("metric", "")).strip()
    priority = int(str(selected.get("priority", 0)))

    if title == "Handoff idea -> W2":
        objective = "Idea → tarea W2 lista para implementar."
        scope = "Salida accionable al aceptar; sin tocar ranking."
        non_scope = "Sin cambios al ranking ni reports."
        files = [".bago/tools/emit_ideas.py"]
        validation = [
            "`./ideas --detail 1` mantiene la salida actual.",
            "`./ideas --accept 1` muestra objetivo y validación.",
            "`./ideas` sin flags conserva el selector existente.",
        ]
    else:
        objective = summary
        scope = "Materializar con el mínimo cambio suficiente."
        non_scope = "No expandir el alcance fuera de la idea elegida."
        files = [".bago/tools/emit_ideas.py"]
        validation = ["Explica cambio, archivos y verificación mínima."]
        if metric:
            validation.append(f"Métrica objetivo: {metric}")

    return {
        "idea_index": index,
        "idea_title": title,
        "priority": priority,
        "workflow": "W2_IMPLEMENTACION_CONTROLADA",
        "objetivo": objective,
        "alcance": scope,
        "no_alcance": non_scope,
        "archivos_candidatos": files,
        "validacion_minima": validation,
        "siguiente_paso": w2,
        "metric": metric,
        "handoff_chain": "role_analyst>role_architect>role_generator>role_validator>role_vertice",
        "human_validation_prompt": "Describe en 1-2 frases qué experiencia humana mejora y cómo lo verificaste.",
        "contexto": detail,
        "status": "pending",
        "accepted_at": datetime.now(timezone.utc).isoformat(),
    }


def save_handoff(data: dict[str, object]) -> Path:
    """Escribe el handoff en .bago/state/pending_w2_task.json y devuelve la ruta."""
    dest = _STATE / "pending_w2_task.json"
    dest.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return dest


def parse_args(argv: list[str]) -> tuple[int | None, bool, bool]:
    detail_index = None
    accept = False
    as_json = False
    idx = 1

    while idx < len(argv):
        arg = argv[idx]
        if arg in {"-h", "--help"}:
            print(
                "Usage: emit_ideas.py [--detail N] [--accept N] [--json]\n\n"
                "Show 5 to 20 contextual ideas prioritized by stability. Use --detail "
                "to expand a selected idea and --accept to mark it ready for W2.\n"
                "--json  Output ideas as structured JSON."
            )
            raise SystemExit(0)
        if arg == "--detail":
            if idx + 1 >= len(argv):
                raise SystemExit("--detail requires a numeric idea index")
            detail_index = int(argv[idx + 1])
            idx += 2
            continue
        if arg == "--accept":
            if idx + 1 >= len(argv):
                raise SystemExit("--accept requires a numeric idea index")
            detail_index = int(argv[idx + 1])
            accept = True
            idx += 2
            continue
        if arg == "--json":
            as_json = True
            idx += 1
            continue
        raise SystemExit(f"Unknown argument: {arg}")

    return detail_index, accept, as_json


def _run_tool_json(tool_name: str, extra_args: list[str] | None = None) -> dict | list | None:
    """Ejecuta un tool BAGO con --json y devuelve el resultado parseado."""
    tool_path = _TOOLS / tool_name
    cmd = [sys.executable, str(tool_path), "--json"] + (extra_args or [])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        text = result.stdout.strip()
        # Algunos tools emiten una línea de estado antes del JSON; saltar al primer {/[
        for start_ch in ('{', '['):
            idx = text.find(start_ch)
            if idx != -1:
                return json.loads(text[idx:])
    except Exception:
        pass
    return None


def _real_state_ideas() -> list[dict[str, object]]:
    """Genera ideas contextuales basadas en el estado real de deuda, riesgo y detector."""
    ideas: list[dict[str, object]] = []

    # ── Riesgo real ────────────────────────────────────────────────────────────
    risk_data = _run_tool_json("risk_matrix.py")
    if isinstance(risk_data, dict):
        exposure = float(risk_data.get("total_exposure", 0))
        risk_items = int(risk_data.get("items", 0))
        by_cat = risk_data.get("by_category", {})
        top_cat = max(by_cat, key=lambda k: by_cat[k].get("total_exposure", 0), default=None) if by_cat else None
        if exposure > 100:
            severity_label = "CRÍTICA" if exposure > 200 else "ALTA"
            ideas.append({
                "priority": 95,
                "section": "contextuales",
                "risk": "low",
                "metric": f"Reducir exposición total de riesgo desde {exposure:.1f} ({severity_label}) a < 100.",
                "title": f"Reducir riesgo {severity_label}: {risk_items} hallazgos ({top_cat or 'VelocityDrag'})",
                "summary": (
                    f"El risk_matrix reporta exposición {exposure:.1f} ({severity_label}) con {risk_items} items. "
                    f"Categoría dominante: {top_cat or 'N/A'}. Cada sys.exit() sin manejo añade 1.2h de deuda operativa."
                ),
                "detail": [
                    f"Exposición total: {exposure:.1f} ({severity_label}) — {risk_items} hallazgos activos.",
                    f"Categoría principal: {top_cat or 'VelocityDrag'} — replace bare sys.exit() with SystemExit o raise.",
                    "Herramienta: bago scan → bago debt → bago risk para ver la evolución.",
                    "Reducir al menos 50 items en una sesión baja la exposición a < 183.",
                ],
                "w2": "Ejecutar scan.py, identificar los 10 ficheros con más BAGO-I001 y hacer refactor mínimo.",
            })
        elif exposure > 0:
            ideas.append({
                "priority": 88,
                "section": "contextuales",
                "risk": "low",
                "metric": f"Reducir riesgo desde {exposure:.1f} a 0.",
                "title": f"Limpiar riesgo residual: {risk_items} hallazgos",
                "summary": f"Quedan {risk_items} hallazgos con exposición {exposure:.1f}. Eliminarlos consolida el baseline.",
                "detail": [
                    f"risk_matrix muestra {risk_items} items con exposición {exposure:.1f}.",
                    "Ejecuta: bago scan && bago risk para el detalle.",
                ],
                "w2": "Resolver los hallazgos de menor esfuerzo (BAGO-I001) en una pasada rápida.",
            })

    # ── Deuda técnica real ─────────────────────────────────────────────────────
    debt_data = _run_tool_json("debt_ledger.py")
    if isinstance(debt_data, dict):
        hours = float(debt_data.get("total_hours", 0))
        cost = float(debt_data.get("total_cost", 0))
        debt_items = int(debt_data.get("items", 0))
        if hours > 10:
            ideas.append({
                "priority": 92,
                "section": "contextuales",
                "risk": "low",
                "metric": f"Reducir deuda técnica desde {hours:.1f}h/€{cost:.0f} a menos de 10h.",
                "title": f"Reducir deuda técnica: {hours:.1f}h / €{cost:.0f} ({debt_items} items)",
                "summary": (
                    f"debt_ledger detecta {debt_items} items de deuda = {hours:.1f}h / €{cost:.0f}. "
                    "La mayoría son sys.exit() sin manejo adecuado (BAGO-I001). "
                    "Resolver 50 items en una sesión = ahorrar ~10h de deuda."
                ),
                "detail": [
                    f"Total deuda: {hours:.1f}h / €{cost:.0f} en {debt_items} items.",
                    "Herramienta: bago scan --lang py → bago debt para ver el desglose.",
                    "Estrategia: reemplazar sys.exit(N) por raise SystemExit(N) en tools/*.py.",
                    "Impacto por item: ~0.12h / €9.7 de deuda eliminada.",
                ],
                "w2": "Identificar los 10 archivos con más hallazgos BAGO-I001 y hacer refactor masivo.",
            })

    # ── Detector WATCH/HARVEST ─────────────────────────────────────────────────
    detector_data = _run_tool_json("context_detector.py")
    if isinstance(detector_data, dict):
        verdict = str(detector_data.get("verdict", ""))
        signals = detector_data.get("signals", [])
        orphan_signal = next((s for s in signals if "orphan" in s.get("id", "")), None)
        unregistered = detector_data.get("unregistered_files", [])

        if orphan_signal:
            ideas.append({
                "priority": 85,
                "section": "contextuales",
                "risk": "low",
                "metric": "Reducir commits sin sesión BAGO a 0 (detector deja de reportar orphan_commits).",
                "title": f"Cerrar {orphan_signal.get('desc', 'commits huérfanos')} → W9",
                "summary": (
                    f"El detector ({verdict}) detecta {orphan_signal.get('desc', 'commits sin sesión')}. "
                    "Hacer cosecha (W9) vincula los commits recientes a una sesión y limpia las señales."
                ),
                "detail": [
                    f"Señal activa: {orphan_signal.get('desc')} — detector en {verdict}.",
                    "Ejecuta: bago cosecha → responde las 3 preguntas de W9.",
                    "El W9 genera el resumen de sesión y vincula los commits al registro.",
                    "Tras la cosecha, el detector debería bajar a CLEAR.",
                ],
                "w2": "Ejecutar `bago cosecha` con las 3 respuestas: qué decidiste, qué descartaste, próximo paso.",
            })

        if unregistered:
            ideas.append({
                "priority": 83,
                "section": "contextuales",
                "risk": "low",
                "metric": "0 ficheros sin CHG (detector deja de reportar unregistered_files).",
                "title": f"Registrar {len(unregistered)} fichero(s) sin CHG",
                "summary": (
                    f"{len(unregistered)} fichero(s) modificados sin CHG asociado: "
                    f"{', '.join(unregistered[:3])}{'...' if len(unregistered) > 3 else ''}."
                ),
                "detail": [
                    f"Ficheros sin CHG: {unregistered[:5]}",
                    "Ejecuta: bago chg new → tipo=governance, severity=patch/minor.",
                    "Después: bago validate confirma el estado correcto.",
                ],
                "w2": "Crear CHG para cada fichero nuevo con affected_components correctos.",
            })

    return ideas


def main() -> int:
    detail_index, accept, as_json = parse_args(sys.argv)
    state_path = _STATE / "ESTADO_BAGO_ACTUAL.md"
    global_state_path = _STATE / "global_state.json"
    smoke_path = ROOT / "sandbox/runtime/last-report.json"
    vm_path = ROOT / "sandbox/runtime-vm/last-report-vm.json"
    soak_path = ROOT / "sandbox/runtime-vm/last-soak-report-vm.json"
    matrix_path = ROOT / "sandbox/runtime-vm/matrix/last-matrix-summary.json"
    readme_path = ROOT / "README.md"

    # ── canonical gate ─────────────────────────────────────────────────────────
    gate_passed, gate_ko, gate_warn = run_canonical_gate(smoke_path)
    if not gate_passed:
        print("BAGO ideas selector — GATE KO")
        print("=" * 44)
        print("Validadores canónicos en fallo. Repara antes de idear.")
        print("")
        for msg in gate_ko:
            print(msg)
        for msg in gate_warn:
            print(msg)
        print("")
        print("KO → ninguna idea avanza. Ejecuta `bago stability` para el detalle.")
        return 1
    # ── /gate ──────────────────────────────────────────────────────────────────

    state_text = read_text(state_path) if file_exists(state_path) else ""
    sections = parse_state_sections(state_text)
    global_state = load_json(global_state_path) if file_exists(global_state_path) else {}

    smoke = report_status(smoke_path)
    vm = report_status(vm_path)
    soak = report_status(soak_path)
    matrix = report_status(matrix_path)

    repo_lines = 0
    if file_exists(readme_path):
        repo_lines = len(read_text(readme_path).splitlines())

    baseline_clean_mode = global_state.get("baseline_status") == "active_clean_core"
    feat = detect_implemented_features()

    ideas: list[dict[str, object]] = []

    # ── Idea 1: Handoff W2 → Opener → Cierre automático ──────────────────────
    if not feat["handoff_w2"]:
        ideas.append({
            "priority": 90,
            "section": "contextuales",
            "risk": "low",
            "metric": "El handoff incluye objetivo, alcance, no alcance, archivos y validación mínima.",
            "title": "Handoff idea -> W2",
            "summary": "Añadir una plantilla de salida que convierta una idea seleccionada en tarea lista para implementar con alcance, archivos y validación.",
            "detail": [
                "Entrada: una idea elegida tras revisar el selector.",
                "Salida: objetivo, alcance, archivos candidatos y validación mínima.",
                "Ventaja: reduce la fricción entre ideación e implementación.",
            ],
            "w2": "Pasar la idea elegida a W2 con un alcance pequeño y un criterio de salida claro.",
        })
    elif not feat["session_opener"]:
        # Generación 2: opener de sesión desde la tarea aceptada
        ideas.append({
            "priority": 90,
            "section": "contextuales",
            "risk": "low",
            "metric": "bago session lee pending_w2_task.json y lanza session_preflight con objetivo, roles y artefactos pre-rellenados.",
            "title": "Opener de sesión desde task",
            "summary": "Añadir `bago session` que lee el handoff aceptado y abre la sesión W2 con preflight pre-rellenado, evitando trabajo manual.",
            "detail": [
                "Entrada: pending_w2_task.json con objetivo, archivos y validación.",
                "Salida: llamada a session_preflight.py con los datos del handoff.",
                "Ventaja: elimina el paso manual de copiar datos del handoff al preflight.",
            ],
            "w2": "Implementar bago session en el script raíz delegando en session_preflight.py.",
        })
    else:
        # Generación 3: cierre automático de sesión desde bago task --done
        ideas.append({
            "priority": 90,
            "section": "contextuales",
            "risk": "low",
            "metric": "bago task --done genera y guarda automáticamente el artefacto de cierre de sesión.",
            "title": "Cierre automático de sesión",
            "summary": "Al marcar la tarea como done, generar automáticamente el artefacto de cierre con resumen de cambios y evidencias.",
            "detail": [
                "Entrada: tarea W2 completada (pending_w2_task.json con status=done).",
                "Salida: artefacto de cierre con resumen, CHG/EVD generados y estado actualizado.",
                "Ventaja: elimina el paso manual de redactar el cierre después de implementar.",
            ],
            "w2": "Extender show_task.py --done para llamar al generador de cierre de sesión.",
        })

    # ── Idea 2: Stability → Banner → Stale task alert ─────────────────────────
    if not feat["stability_cmd"]:
        ideas.append({
            "priority": 86,
            "section": "contextuales",
            "risk": "low",
            "metric": "El resumen incluye estado de smoke, VM y soak en un único bloque.",
            "title": "Resumen único de estabilidad",
            "summary": "Consolidar smoke, VM y soak en un informe corto para decidir si una idea nueva compite con estabilidad antes de tocar código.",
            "detail": [
                "Entrada: los últimos reports del sandbox.",
                "Salida: un resumen de salud operacional para decidir si conviene proponer cambios.",
                "Ventaja: evita idear sobre una base ya inestable.",
            ],
            "w2": "Si el resumen está en verde, permitir avanzar a una idea concreta.",
        })
    elif not feat["banner_shows_task"]:
        # Generación 2: mostrar task pendiente en el banner
        ideas.append({
            "priority": 86,
            "section": "contextuales",
            "risk": "low",
            "metric": "El banner muestra el estado de la tarea W2 activa (título + estado) si pending_w2_task.json existe.",
            "title": "Banner muestra task activa",
            "summary": "Mostrar en el banner de BAGO si hay una tarea W2 pendiente o completada, para visibilidad inmediata al arrancar.",
            "detail": [
                "Entrada: pending_w2_task.json si existe.",
                "Salida: línea extra en el banner con título y estado (⏳/✅).",
                "Ventaja: el usuario sabe al abrir BAGO si tiene trabajo en curso.",
            ],
            "w2": "Leer pending_w2_task.json en bago_banner.py y añadir línea condicional al banner.",
        })
    else:
        # Generación 3: alerta de tarea obsoleta
        ideas.append({
            "priority": 86,
            "section": "contextuales",
            "risk": "low",
            "metric": "bago stability y el banner alertan si la task lleva más de 3 días sin completarse.",
            "title": "Alerta de task obsoleta",
            "summary": "Si pending_w2_task.json lleva más de 3 días sin marcarse done, mostrar aviso en banner y en bago stability.",
            "detail": [
                "Entrada: pending_w2_task.json con campo accepted_at.",
                "Salida: aviso visual (⚠️) en banner y en stability cuando la task supera 3 días.",
                "Ventaja: evita que tareas abiertas queden olvidadas.",
            ],
            "w2": "Añadir lógica de antigüedad en bago_banner.py y stability_summary.py.",
        })

    # ── Idea 3: Gate → Registro → Selector filtra por registro ───────────────
    stable_reports = all(
        report and report.get("status") == "pass" and report.get("failure_count", 1) == 0
        for report in (smoke, vm, soak)
        if report is not None
    )
    if not feat["gate_in_code"] and stable_reports:
        ideas.append({
            "priority": 84,
            "section": "contextuales",
            "risk": "low",
            "metric": "Ninguna idea avanza si validate_pack/validate_state/smoke no están en verde.",
            "title": "Gate seguro antes de implementar",
            "summary": "Bloquear sugerencias nuevas si validate_pack, validate_state o smoke no están en verde.",
            "detail": [
                "Entrada: validadores canónicos y smoke del sandbox.",
                "Salida: permiso o bloqueo para seguir ideando e implementar.",
                "Ventaja: protege la estabilidad antes de abrir trabajo nuevo.",
            ],
            "w2": "Si el gate pasa, la idea elegida puede convertirse en W2.",
        })
    elif feat["gate_in_code"] and not feat["impl_registry"]:
        # Generación 2: registro de ideas implementadas para no repetirlas
        ideas.append({
            "priority": 84,
            "section": "contextuales",
            "risk": "low",
            "metric": "El selector no repite una idea marcada como implementada en implemented_ideas.json.",
            "title": "Registro de ideas implementadas",
            "summary": "Guardar en estado qué ideas ya fueron implementadas para que el selector evolucione en lugar de repetirlas en cada sesión.",
            "detail": [
                "Entrada: lista de ideas aceptadas e implementadas.",
                "Salida: archivo .bago/state/implemented_ideas.json con IDs y fechas.",
                "Ventaja: el selector siempre propone trabajo nuevo, no repetido.",
            ],
            "w2": "Crear implemented_ideas.json y leerlo en emit_ideas para filtrar ideas ya hechas.",
        })
    elif feat["impl_registry"]:
        # Generación 3: puntuación dinámica basada en registro
        ideas.append({
            "priority": 84,
            "section": "contextuales",
            "risk": "low",
            "metric": "El scoring de ideas sube cuando la feature que proponen no está en implemented_ideas.json.",
            "title": "Scoring dinámico por registro",
            "summary": "Ajustar la prioridad de las ideas en función de si la feature que proponen ya fue implementada, incrementando el score de las que aportan trabajo nuevo.",
            "detail": [
                "Entrada: implemented_ideas.json con historial de ideas completadas.",
                "Salida: ideas reordenadas priorizando trabajo genuinamente nuevo.",
                "Ventaja: el selector se vuelve más preciso con el tiempo.",
            ],
            "w2": "Leer implemented_ideas.json en emit_ideas y aplicar penalización de score a ideas similares ya hechas.",
        })

    if matrix and matrix.get("status") == "pass":
        ideas.append({
            "priority": 82,
            "section": "contextuales",
            "risk": "medium",
            "metric": "WF responde por intención y reduce navegación manual.",
            "title": "Selector por intención",
            "summary": "Extender WF para filtrar ideas y workflows por intención, por ejemplo idea, implementar, depurar o cerrar.",
            "detail": [
                "Entrada: intención del usuario.",
                "Salida: selector más fino para aterrizar al workflow correcto.",
                "Ventaja: evita navegar manualmente cuando la intención ya está clara.",
            ],
            "w2": "Usar la intención seleccionada para orientar la tarea siguiente.",
        })

    if baseline_clean_mode:
        ideas.append({
            "priority": 78,
            "section": "contextuales",
            "risk": "low",
            "metric": "Cada idea aceptada declara una mejora medible en trazabilidad u operación.",
            "title": "Ideas orientadas a baseline",
            "summary": "Proponer solo cambios que mantengan el baseline limpio y generen un incremento medible en trazabilidad u operacion.",
            "detail": [
                "Entrada: baseline limpio y estable.",
                "Salida: ideas pequeñas con mejora mensurable.",
                "Ventaja: alinea la ideación con la continuidad del pack.",
            ],
            "w2": "Seleccionar una idea que preserve el baseline y tenga bajo riesgo.",
        })

    if sections.get("cierre de sesión"):
        ideas.append({
            "priority": 74,
            "section": "contextuales",
            "risk": "medium",
            "metric": "Reapertura evita reconstrucción manual y reduce pasos de arranque.",
            "title": "Reabrir desde continuidad",
            "summary": "Añadir un modo para reactivar la sesión desde el cierre actual sin reconstruir contexto manualmente.",
            "detail": [
                "Entrada: cierre de sesión ya escrito en estado.",
                "Salida: reanudación más rápida sin perder contexto.",
                "Ventaja: mantiene continuidad de trabajo entre sesiones.",
            ],
            "w2": "Si se acepta, convertirlo en una mejora pequeña y segura de continuidad.",
        })

    if repo_lines > 0:
        ideas.append({
            "priority": 70,
            "section": "contextuales",
            "risk": "medium",
            "metric": "La primera decisión del usuario llega a una acción en un paso.",
            "title": "Entrada rápida del repo",
            "summary": "Conectar ideas con README y WF para que la primera decisión del usuario vaya a una acción concreta sin leer toda la canonica.",
            "detail": [
                "Entrada: comandos cortos y selector de workflows.",
                "Salida: menos fricción para abrir ideas o W2.",
                "Ventaja: mejora la usabilidad diaria del repo.",
            ],
            "w2": "Promover la idea seleccionada a una tarea corta y directa.",
        })

    ideas.append({
        "priority": 68,
        "section": "contextuales",
        "risk": "medium",
        "metric": "El ranking refleja señales de estado actual y reduce recomendaciones estáticas.",
        "title": "Mejorar ranking de ideas",
        "summary": "Ajustar el scoring para reflejar señales del estado actual y evitar prioridades estáticas que oculten trabajo real.",
        "detail": [
            "Entrada: estado BAGO, salud de reports y workflow activo.",
            "Salida: orden de ideas más sensible al contexto operativo.",
            "Ventaja: reduce sesgos de ranking y evita ciclos de recomendación.",
        ],
        "w2": "Implementar un ranking contextual acotado y validarlo con ejemplos reales del estado.",
    })

    # ── Ideas dinámicas basadas en estado real (debt, risk, detector) ──────────
    ideas.extend(_real_state_ideas())

    if baseline_clean_mode:
        ideas = filter_ideas_for_baseline_mode(ideas)

    # Scoring dinámico: penaliza ideas similares a las ya implementadas, filtra exactas
    done_titles = load_implemented_titles()
    ideas = apply_dynamic_scoring(ideas, done_titles)

    sections = build_idea_sections(ideas, done_titles)
    ideas = order_ideas_by_section(sections)

    if as_json:
        print(json.dumps({
            "total": len(ideas),
            "gate": "pass",
            "baseline_clean_mode": baseline_clean_mode,
            "ideas": [
                {
                    "rank": i + 1,
                    "priority": idea.get("priority", 0),
                    "section": idea.get("section", ""),
                    "risk": idea.get("risk", ""),
                    "title": str(idea.get("title", "")),
                    "summary": str(idea.get("summary", "")),
                    "metric": str(idea.get("metric", "")),
                    "next_step": str(idea.get("w2", "")),
                }
                for i, idea in enumerate(ideas)
            ]
        }, indent=2, ensure_ascii=False))
        return 0

    # ── working mode header ────────────────────────────────────────────────────
    repo_ctx_path = _STATE / "repo_context.json"
    repo_ctx = load_json(repo_ctx_path) if file_exists(repo_ctx_path) else {}
    working_mode = repo_ctx.get("working_mode", "self")
    ext_repo = Path(repo_ctx.get("repo_root", "")).name if working_mode == "external" else ""

    print("BAGO ideas selector")
    if working_mode == "external" and ext_repo:
        print(f"modo: 🏠 framework  ·  proyecto externo activo: 📂 {ext_repo}")
        print("⚠  Las ideas de abajo son mejoras del FRAMEWORK BAGO, no del proyecto externo.")
        print("   Para trabajar en el proyecto usa: bago analyze <ruta> o bago session --repo <ruta>")
    else:
        print("modo: 🏠 framework (self)")
    # ── /working mode header ───────────────────────────────────────────────────

    print(summarize_report("smoke", smoke))
    print(summarize_report("vm", vm))
    print(summarize_report("soak", soak))
    print(summarize_report("matrix", matrix))
    if baseline_clean_mode:
        print("baseline_clean_mode: activo (solo ideas low-risk con métrica)")
    print("")
    if working_mode == "external" and ext_repo:
        print(f"── Ideas del framework BAGO ──────────────────────────────────")
    print_sectioned_ideas(sections)

    print("")
    if detail_index is None:
        print(
            f"→ `bago ideas --accept 1`"
        )
        return 0

    if detail_index < 1 or detail_index > len(ideas):
        raise SystemExit(f"Invalid idea index: {detail_index}")

    selected = ideas[detail_index - 1]
    print(f"Selected idea: {detail_index}. {selected['title']}")
    for line in selected["detail"]:
        print(f"- {line}")
    print(f"- Next step: {selected['w2']}")
    if accept:
        metric = str(selected.get("metric", "")).strip()
        if not metric:
            print("- Status: RECHAZADA — sin métrica medible")
            print("  Sin 'metric': elige idea con mejora verificable.")
            return 1
        print("- Status: accepted for W2")
        print("- Workflow: run `make workflow-tactical NAME=W2`")
        for line in render_handoff(selected):
            print(line)
        handoff_data = build_handoff_data(selected, detail_index)
        saved_path = save_handoff(handoff_data)
        register_implemented_idea(str(selected["title"]), detail_index)
        print(f"\n→ Tarea guardada en {saved_path.relative_to(ROOT)}")
        print("  Consulta con: bago task")
    else:
        print("- Status: awaiting acceptance")
        print(f"- If you want to accept it, run `./ideas --accept {detail_index}`")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
