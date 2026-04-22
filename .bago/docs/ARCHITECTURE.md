# Arquitectura del Sistema BAGO

> Documento técnico de referencia para entender cómo está construido el framework BAGO.

---

## 1. Diagrama general del sistema

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          BAGO FRAMEWORK v2.5                            │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │                     CAPA CLI                                     │  │
│  │                                                                  │  │
│  │   ./bago <subcomando>   ──→   dispatch tabla de comandos        │  │
│  │   (shell script)              en el script `bago`              │  │
│  └─────────────────────────────┬────────────────────────────────────┘  │
│                                │                                        │
│  ┌─────────────────────────────▼────────────────────────────────────┐  │
│  │                     CAPA TOOLS                                   │  │
│  │                                                                  │  │
│  │   .bago/tools/                                                  │  │
│  │   ├── health_score.py    ← bago health                         │  │
│  │   ├── insights.py        ← bago insights                       │  │
│  │   ├── velocity.py        ← bago velocity                       │  │
│  │   ├── sprint_manager.py  ← bago sprint                         │  │
│  │   └── ... (50+ herramientas)                                   │  │
│  └─────────────────────────────┬────────────────────────────────────┘  │
│                                │ lee / escribe                          │
│  ┌─────────────────────────────▼────────────────────────────────────┐  │
│  │                     CAPA STATE                                   │  │
│  │                                                                  │  │
│  │   .bago/state/                                                  │  │
│  │   ├── sessions/          SES-*.json                            │  │
│  │   ├── changes/           BAGO-CHG-*.json + BAGO-EVD-*.json    │  │
│  │   ├── sprints/           SPRINT-*.json                         │  │
│  │   ├── goals/             GOAL-*.json                           │  │
│  │   ├── reminders/         REM-*.json                            │  │
│  │   ├── snapshots/         SNAP-*.zip                            │  │
│  │   ├── global_state.json  (estado global)                       │  │
│  │   └── ESTADO_BAGO_ACTUAL.md                                    │  │
│  └─────────────────────────────┬────────────────────────────────────┘  │
│                                │                                        │
│  ┌─────────────────────────────▼────────────────────────────────────┐  │
│  │                     CAPA DOCS                                    │  │
│  │                                                                  │  │
│  │   .bago/docs/                                                   │  │
│  │   ├── tools/             doc por cada herramienta               │  │
│  │   ├── CHANGELOG.md       historial de versiones                 │  │
│  │   ├── ARCHITECTURE.md    (este documento)                       │  │
│  │   └── CONTRIBUTING.md    guía de contribución                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘

  ┌──────────────┐    ┌──────────────────┐    ┌───────────────────────┐
  │  BAGO Viewer │    │  GitHub Copilot  │    │  Git / GitHub Actions │
  │  menu.html   │◄──►│  extensions/     │    │  (próx: bago gh)      │
  │  + servidor  │    │  .bago/prompts/  │    └───────────────────────┘
  └──────────────┘    └──────────────────┘
```

---

## 2. Capas del sistema

### 2.1 Capa CLI (`bago` script)

El script `bago` (shell) actúa como dispatcher. Cada subcomando se mapea a un archivo Python en `.bago/tools/`:

```bash
# Estructura interna del script bago:
COMMANDS_MAIN=(start ideas session status)
COMMANDS_ADVANCED=(health audit validate doctor lint check patch workflow ...)
COMMANDS_SPRINT180=(sprint search timeline report metrics ...)
```

El script:
1. Parsea el primer argumento (subcomando)
2. Busca el `.py` correspondiente en `.bago/tools/`
3. Ejecuta `python3 .bago/tools/<tool>.py [args]`

### 2.2 Capa Tools (`.bago/tools/`)

Cada herramienta es un módulo Python independiente que:
- Lee datos de `.bago/state/` (JSON)
- Puede escribir en `.bago/state/` (sesiones, cambios, etc.)
- Escribe output a stdout (texto, tablas ASCII, Markdown)
- Soporta `--test` para validación rápida sin efectos
- Tiene docstring en el encabezado con descripción y uso

**Convenciones de naming:**
- Un archivo `.py` por subcomando
- Nombre del archivo = nombre del subcomando (con guiones → guiones bajos)
- Excepciones: `session-stats` → `session_details.py`, `ss` (alias) → mismo archivo

### 2.3 Capa State (`.bago/state/`)

Fuente de verdad del sistema. Todos los datos son JSON legibles. Ninguna herramienta debe modificar state/ directamente desde fuera del sistema BAGO.

**Estructura de directorios:**
```
state/
├── sessions/           # Una por sesión de trabajo
│   └── archive/        # Sesiones archivadas (>30 días, cerradas)
├── changes/            # Registro de cambios (CHG) y evidencias (EVD)
├── sprints/            # Sprints de gestión de trabajo
├── goals/              # Objetivos con progreso
├── reminders/          # Recordatorios con due-date
├── snapshots/          # ZIPs point-in-time
├── findings/           # (futuro) Hallazgos de análisis estático
├── patches/            # (futuro) Parches generados por autofix
├── global_state.json   # Estado global: modo, sesión activa, rol
├── pack.json           # Configuración del pack
└── ESTADO_BAGO_ACTUAL.md  # Resumen humano del estado
```

### 2.4 Capa Docs (`.bago/docs/`)

Documentación técnica del framework:
- `tools/` — Referencia de cada herramienta CLI
- `CHANGELOG.md` — Historial siguiendo Keep a Changelog
- `ARCHITECTURE.md` — Este documento
- `CONTRIBUTING.md` — Guía de contribución
- Otros: `BAGO_REFERENCIA_COMPLETA.md`, `GLOSARIO.md`, `MAPA_DEL_SISTEMA.md`, etc.

---

## 3. Formatos de datos en state/

### SES-*.json — Sesión de trabajo

```json
{
  "id": "SES-SPRINT-2026-04-22-001",
  "workflow": "w7_foco_sesion",
  "status": "closed",
  "started_at": "2026-04-22T10:00:00Z",
  "closed_at": "2026-04-22T12:30:00Z",
  "decisions": ["Decisión A", "Decisión B"],
  "artifacts": ["archivo1.py", "archivo2.md"],
  "roles": ["role_generativo"],
  "metrics": {
    "decisions_count": 2,
    "artifacts_count": 2,
    "score": 85
  }
}
```

### BAGO-CHG-*.json — Cambio registrado

```json
{
  "id": "BAGO-CHG-077",
  "type": "feature",
  "description": "Descripción del cambio",
  "session_id": "SES-SPRINT-2026-04-22-001",
  "files": ["tools/velocity.py", "tools/patch.py"],
  "severity": "minor",
  "timestamp": "2026-04-22T12:30:00Z"
}
```

### SPRINT-*.json — Sprint

```json
{
  "id": "SPRINT-004",
  "name": "Sprint 180 Fase 5-6",
  "goal": "Implementar herramientas de análisis y velocidad",
  "status": "open",
  "started_at": "2026-04-22",
  "velocity": {
    "sessions_per_day": 2.1,
    "artifacts_per_day": 4.3
  },
  "items": []
}
```

### GOAL-*.json — Objetivo

```json
{
  "id": "GOAL-001",
  "title": "Título del objetivo",
  "criterion": "Criterio de éxito medible",
  "status": "open",
  "progress": 75,
  "linked_sessions": ["SES-001", "SES-002"],
  "created_at": "2026-04-20"
}
```

### REM-*.json — Recordatorio

```json
{
  "id": "REM-001",
  "text": "Revisar health antes de sprint review",
  "due_date": "2026-04-25",
  "sprint_ref": "SPRINT-004",
  "status": "pending",
  "created_at": "2026-04-22"
}
```

---

## 4. Flujos de datos principales

### 4.1 Flujo de sesión

```
./bago session
    │
    ▼
session_opener.py
    ├── Lee global_state.json (sesión activa, modo)
    ├── Lee pending_w2_task.json (tarea pendiente)
    ├── Muestra contexto precargado al usuario
    └── Crea SES-*.json en state/sessions/
           │
           ▼
    [trabajo durante la sesión]
           │
           ▼
./bago task --done
    └── show_task.py actualiza pending_w2_task.json

./bago cosecha
    └── cosecha.py genera BAGO-CHG-*.json + BAGO-EVD-*.json
```

### 4.2 Flujo de health/validación

```
./bago health
    │
    ▼
health_score.py
    ├── Lee state/sessions/ → disciplina workflow (20 pts)
    ├── Lee state/sessions/ → captura decisiones (20 pts)
    ├── Ejecuta validate_pack → integridad (25 pts)
    ├── Ejecuta stale_detector → estado stale (15 pts)
    └── Reconcilia inventario → consistencia (20 pts)
           │
           ▼
    Score 0-100 con semáforo 🟢/🟡/🔴
```

### 4.3 Flujo de insights

```
./bago insights
    │
    ▼
insights.py
    ├── Analiza SES-*.json → categoría PRODUCCION
    ├── Analiza patrones temporales → categoría PATRON
    ├── Detecta riesgos (stale, health<80) → categoría RIESGO
    ├── Calcula tendencias rolling → categoría TENDENCIA
    └── Genera recomendaciones → categoría RECOMENDACION
           │
           ▼
    Lista de insights priorizados con nivel de prioridad
```

### 4.4 Pipeline GitHub (en construcción)

```
./bago scan
    ├── Ejecuta linters (pylint, flake8, etc.)
    └── Genera BAGO-FINDING-*.json en state/findings/
           │
           ▼
./bago hotspot
    ├── Lee state/findings/ + state/changes/
    └── Detecta archivos con mayor densidad de problemas
           │
           ▼
./bago fix
    ├── Lee BAGO-FINDING-*.json
    ├── Genera parches diff
    ├── Valida con validate_pack
    └── Crea BAGO-PATCH-*.json en state/patches/
           │
           ▼
./bago gh
    ├── Lee BAGO-PATCH-*.json
    ├── Publica en GitHub Check Runs
    └── Añade comentarios en PRs via GitHub API
```

---

## 5. Relaciones entre módulos

### Módulos que se invocan entre sí

| Módulo | Invoca a | Para |
|--------|----------|------|
| `health_score.py` | `validate_pack.py` | Validación de integridad |
| `health_score.py` | `stale_detector.py` | Detección de stale |
| `audit_v2.py` | `health_score.py` | Score en la auditoría |
| `audit_v2.py` | `validate_pack.py` | Validación en auditoría |
| `doctor.py` | múltiples | Diagnóstico integral |
| `session_opener.py` | Ninguno directo | Lee state/ directamente |
| `insights.py` | Ninguno directo | Lee state/ directamente |

### Módulos que comparten state/

- **Lectores globales:** `health_score.py`, `insights.py`, `stats.py`, `velocity.py`, `review.py`
- **Escritores de sesiones:** `session_opener.py`, `cosecha.py`, `show_task.py`
- **Escritores de cambios:** `cosecha.py`
- **Escritores de sprints:** `sprint_manager.py`
- **Escritores de goals:** `goals.py`
- **Escritores de reminders:** `remind.py`

---

## 6. Extensibilidad

### Añadir un nuevo comando

1. Crear `.bago/tools/<nombre>.py`
2. Registrar en el script `bago` (tabla de comandos correspondiente)
3. Crear tests en `integration_tests.py`
4. Documentar en `.bago/docs/tools/<nombre>.md`

Ver guía completa: [CONTRIBUTING.md](CONTRIBUTING.md)

### Añadir un nuevo workflow

1. Crear `.bago/workflows/W<N>_<NOMBRE>.md`
2. Registrar en `workflow_selector.py`
3. Actualizar `WORKFLOWS_INDEX.md`

---

*Última actualización: 2026-04-22 · BAGO v2.5-stable*
