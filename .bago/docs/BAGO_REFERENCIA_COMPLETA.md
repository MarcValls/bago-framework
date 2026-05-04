# BAGO · Referencia Completa del Sistema

> Versión: 2.5-stable · Fecha: 2026-04-20  
> Documento de referencia integral — todas las capacidades, herramientas, workflows y patrones de uso.

---

## ÍNDICE

1. [¿Qué es BAGO?](#1-qué-es-bago)
2. [Filosofía y principios](#2-filosofía-y-principios)
3. [Arquitectura del sistema](#3-arquitectura-del-sistema)
4. [CLI — Referencia de comandos](#4-cli--referencia-de-comandos)
5. [Workflows (W0–W9)](#5-workflows-w0w9)
6. [Roles del sistema](#6-roles-del-sistema)
7. [Artefactos de estado](#7-artefactos-de-estado)
8. [Herramientas (tools/)](#8-herramientas-tools)
9. [Sistema de ideas y handoff](#9-sistema-de-ideas-y-handoff)
10. [Ciclo de sesión completo](#10-ciclo-de-sesión-completo)
11. [Métricas de salud](#11-métricas-de-salud)
12. [Gates y validación](#12-gates-y-validación)
13. [Detectores automáticos](#13-detectores-automáticos)
14. [Escenarios de experimentación](#14-escenarios-de-experimentación)
15. [Perfil de personalidad](#15-perfil-de-personalidad)
16. [Extensiones Copilot CLI](#16-extensiones-copilot-cli)
17. [Gobernanza y canon](#17-gobernanza-y-canon)
18. [Glosario operativo](#18-glosario-operativo)

---

## 1. ¿Qué es BAGO?

BAGO es el **sistema operativo de trabajo técnico** para programación y generación compleja asistida por IA.

No es una metodología de gestión de proyectos ni un framework de desarrollo. Es la **capa de gobierno** que hace que el trabajo técnico avanzado — el que requiere contexto acumulado, decisiones en cadena y múltiples artefactos — sea **reproducible, auditable y medible**.

### El problema que resuelve

El trabajo técnico complejo tiene un problema estructural: el **contexto se pierde entre sesiones**. Cada vez que se abre una nueva sesión, el modelo o el desarrollador no sabe qué se decidió antes, por qué, qué está en marcha, qué está bloqueado.

Resultado: tres pérdidas reales:
1. **Pérdida de decisiones** — se retoman debates ya resueltos
2. **Pérdida de estado** — no se sabe qué hay que hacer ni dónde se está
3. **Pérdida de trazabilidad** — no se puede auditar por qué el sistema está como está

### La solución

BAGO formaliza el ciclo de trabajo en tres capas de registro:

| Capa | Qué registra | Ubicación |
|---|---|---|
| **Sesiones** | Qué se hizo, con qué workflow, qué roles | `state/sessions/` |
| **Cambios (CHG)** | Qué cambió estructuralmente y por qué | `state/changes/` |
| **Evidencias (EVD)** | Qué se decidió, validó o midió | `state/evidences/` |

Cada sesión arranca con **contexto completo** y cada cierre deja el sistema en estado auditable.

---

## 2. Filosofía y principios

### El ciclo BAGO

Las cuatro letras definen los cuatro modos cognitivos del trabajo técnico:

| Letra | Modo | Función |
|---|---|---|
| **B** | **Balanceado** | Clarifica objetivo, alcance, restricciones, riesgos y criterio de done |
| **A** | **Adaptativo** | Elige estrategia y secuencia realistas según el estado real del repositorio |
| **G** | **Generativo** | Produce artefactos útiles: código, tests, docs, scripts, planes técnicos |
| **O** | **Organizativo** | Ordena, empaqueta, actualiza estado y deja continuidad |

### Reglas maestras

- **No generar antes de entender.** El modo G no se activa hasta que B y A hayan resuelto qué y cómo.
- **No rediseñar por impulso.** Cambios estructurales requieren justificación explícita.
- **No cerrar sin dejar siguiente paso claro.** O siempre deja contexto para la próxima sesión.
- **No confundir documentación con progreso.** Un artefacto sin cambio real no cuenta.
- **Preferir cambios mínimos, claros y trazables.** Cirugía antes que refactor total.
- **Repo-first.** Se lee el repositorio real antes de sobrerrepresentar metaestructura.
- **Activación mínima suficiente.** Solo se activan los roles necesarios para la tarea actual.

---

## 3. Arquitectura del sistema

### Estructura de directorios

```
BAGO_ROOT/
├── bago                          ← CLI raíz (entrada principal)
├── ideas                         ← wrapper → bago ideas
├── stability-summary             ← wrapper → bago stability
├── .bago/
│   ├── AGENT_START.md            ← punto de arranque para agentes IA
│   ├── README.md                 ← documentación técnica principal
│   ├── pack.json                 ← manifiesto del pack (versión, inventario)
│   ├── CHECKSUMS.sha256          ← hashes de integridad
│   ├── TREE.txt                  ← árbol del pack (auto-generado)
│   ├── agents/                   ← agentes BAGO (MAESTRO, ANALISTA, etc.)
│   ├── core/                     ← cerebro, contratos, workflows, orquestador
│   │   ├── canon/                ← CANON, TAXONOMIA, REGLAS, CONTRATOS
│   │   ├── orchestrator/         ← ORQUESTADOR_CENTRAL, ROUTER, MATRIZ
│   │   ├── supervision/          ← AUDITOR_CANONICO, VERTICE, ALERTAS
│   │   └── workflows/            ← workflows internos del núcleo cognitivo
│   ├── docs/                     ← documentación, guías, análisis, gobernanza
│   ├── state/                    ← estado vivo del sistema
│   │   ├── global_state.json     ← estado centralizado del pack
│   │   ├── sessions/             ← artefactos de sesión (SES-*.json)
│   │   ├── changes/              ← cambios (BAGO-CHG-*.json)
│   │   ├── evidences/            ← evidencias (BAGO-EVD-*.json)
│   │   ├── metrics/              ← métricas de rendimiento
│   │   ├── scenarios/            ← escenarios de experimentación
│   │   ├── pending_w2_task.json  ← tarea W2 activa (handoff)
│   │   ├── implemented_ideas.json ← registro de ideas ya implementadas
│   │   └── ESTADO_BAGO_ACTUAL.md ← snapshot humano del estado
│   ├── templates/                ← plantillas para cambios, evidencias, roles, workflows
│   ├── tools/                    ← herramientas Python del sistema
│   └── workflows/                ← definiciones de workflows W0–W9
```

### Capas del sistema

```
Usuario / Agente IA
        ↓
   AGENT_START.md
        ↓
   bago (CLI raíz)
        ↓
   bago_banner.py  ←── estado, inventario, task activa, detector W9
        ↓
   Workflow selector  ←── W0–W9
        ↓
   Roles activados  ←── MAESTRO, ANALISTA, ARQUITECTO, GENERADOR, ORGANIZADOR, VÉRTICE
        ↓
   Herramientas (tools/)
        ↓
   Artefactos → state/sessions + changes + evidences
        ↓
   validate_pack / validate_state  ←── gate de cierre
```

---

## 4. CLI — Referencia de comandos

El punto de entrada único es el script `bago` en la raíz del repositorio.

### Comando raíz

```bash
python3 bago          # muestra banner con estado completo
```

El banner muestra:
- Estado del pack (GO/KO), versión
- Inventario (ses / chg / evd)
- Modo de trabajo (self / external)
- Escenarios activos
- Veredicto detector W9 (HARVEST / WATCH / CLEAN)
- Última sesión completada
- Task W2 activa si existe (⏳/✅)
- Tabla de comandos disponibles

### Comandos de inspección y estado

| Comando | Herramienta | Descripción |
|---|---|---|
| `bago` | `bago_banner.py` | Banner completo con estado y comandos |
| `bago health` | `health_score.py` | Score 0-100 en 5 dimensiones |
| `bago dashboard` | `pack_dashboard.py` | Dashboard con semáforos y KPIs |
| `bago dashboard --full` | `pack_dashboard.py` | Dashboard extendido |
| `bago audit` | `audit_v2.py` | Auditoría integral (< 30 seg) |
| `bago stability` | `stability_summary.py` | Resumen smoke/VM/soak + validadores |
| `bago validate` | `validate_pack.py` | Validación directa del pack |
| `bago detector` | `context_detector.py` | Detecta HARVEST/WATCH/CLEAN |
| `bago stale` | `stale_detector.py` | Detecta contradicciones en estado |

### Comandos de trabajo

| Comando | Herramienta | Descripción |
|---|---|---|
| `bago ideas` | `emit_ideas.py` | Lista 5 ideas priorizadas y contextuales |
| `bago ideas --detail N` | `emit_ideas.py` | Amplía descripción de la idea N |
| `bago ideas --accept N` | `emit_ideas.py` | Genera handoff W2 para la idea N |
| `bago task` | `show_task.py` | Muestra tarea W2 pendiente |
| `bago task --done` | `show_task.py` | Marca tarea como completada + registra en implemented_ideas.json |
| `bago task --clear` | `show_task.py` | Elimina la tarea pendiente |
| `bago session` | `session_opener.py` | Abre sesión W2 con preflight pre-rellenado desde handoff |
| `bago session --dry` | `session_opener.py` | Muestra args del preflight sin ejecutar |
| `bago cosecha` | `cosecha.py` | Protocolo W9 — formaliza contexto libre |
| `bago workflow` | `workflow_selector.py` | Selector interactivo de workflows |

### Comandos de mantenimiento

| Comando | Herramienta | Descripción |
|---|---|---|
| `bago setup` | `repo_context_guard.py` | Sincroniza repo_context + instala extensiones |
| `bago extensions` | interno | Lista/instala extensiones Copilot CLI |
| `bago versions` | interno | Lista cleanversions disponibles |
| `bago v2` | `v2_close_checklist.py` | Checklist de cierre V2 |

### Wrappers raíz

```bash
./ideas               # equivale a: python3 bago ideas (con todos los flags)
./stability-summary   # equivale a: python3 bago stability
```

### Instalación como alias global

```bash
echo 'alias bago="python3 $(pwd)/bago"' >> ~/.zshrc
# Luego: bago ideas, bago health, etc. desde cualquier directorio
```

---

## 5. Workflows (W0–W9)

Los workflows son **contratos de atención**: definen qué artefactos se esperan, qué roles se activan y cuál es el criterio de done. No son procesos rígidos — son marcos de trabajo.

### W0 · Sesión Libre

**ID:** `w0_free_session`  
**Cuándo usar:** Exclusivamente en ESCENARIO-002 (competición on vs off). No usar en sesiones productivas normales.  
**Características:**
- Sin preflight obligatorio
- Sin pre-declaración de artefactos
- Sin restricción de roles
- Modo `.bago/off`

### W1 · Cold Start

**ID:** `w1_cold_start`  
**Cuándo usar:** Primer arranque en un repositorio desconocido.  
**Flujo:**
1. Cargar bootstrap canónico
2. Detectar stack y estructura real
3. Contrastar estado vs repo
4. Registrar divergencias
5. Proponer objetivo técnico inicial
6. Definir siguiente paso útil

**Criterio de done:** El repositorio es operable con criterio — no necesariamente perfecto.

### W2 · Implementación Controlada

**ID:** `w2_implementacion_controlada`  
**Cuándo usar:** Tarea técnica con objetivo definido, acotada, de bajo riesgo de expansión.  
**Flujo BAGO:**
- [B] Entender la tarea, aclarar alcance y no-alcance
- [A] Elegir enfoque mínimo viable
- [G] Implementar el cambio
- [O] Cerrar, registrar CHG + EVD, actualizar estado

**Regla:** No expandir alcance sin justificación explícita.  
**Artefactos mínimos:** 1 CHG, 1 EVD, estado actualizado, validate_pack GO.

### W3 · Refactor Sensible

**ID:** `w3_refactor_sensible`  
**Cuándo usar:** Refactorización que toca contratos, interfaces o estructura.  
**Requisitos:**
- Alcance delimitado antes de empezar
- Contratos afectados identificados
- Validación humana si toca arquitectura
- Registro de cambio obligatorio

### W4 · Debug Multicausa

**ID:** `w4_debug_multicausa`  
**Cuándo usar:** Fallos con varias causas plausibles, donde hay que investigar antes de corregir.  
**Flujo:**
1. Separar síntomas de hipótesis
2. Priorizar causas probables
3. Reducir superficie de búsqueda
4. Probar correcciones mínimas
5. Registrar hallazgos y descartes

### W5 · Cierre y Continuidad

**ID:** `w5_cierre_y_continuidad`  
**Cuándo usar:** Al finalizar cualquier sesión de trabajo con trabajo parcial.  
**Debe dejar:**
- Objetivo vigente
- Qué se hizo
- Qué queda pendiente
- Decisiones congeladas
- Siguiente paso concreto

### W6 · Ideación Aplicada

**ID:** `w6_ideacion_aplicada`  
**Cuándo usar:** Cuando se quiere analizar el repo y generar ideas de mejora contextualizadas.  
**Flujo:**
1. Leer estado y contexto real del repo
2. Detectar oportunidades de mejora o extensión
3. Priorizar por impacto, riesgo y coste de implementación
4. Devolver lista corta de ideas accionables
5. Pedir detalle de idea concreta si hace falta
6. Confirmar si entra en W2
7. Descartar propuestas que añadan complejidad sin beneficio

### W7 · Foco de Sesión *(preferido para trabajo productivo)*

**ID:** `w7_foco_sesion`  
**Cuándo usar:** Siempre que el objetivo sea concreto y acotado. Preferir sobre W1 en sesiones productivas normales.  
**Prerequisito:** Pack en estado GO · Escenario ESCENARIO-001 activo  
**Paso 0 — Preflight obligatorio:**

```bash
python3 .bago/tools/session_preflight.py \
  --objetivo "Verbo + objeto + criterio de done" \
  --roles "role_architect,role_validator" \
  --artefactos "archivo1,archivo2,archivo3"
```

**Reglas:**
- ≥ 3 artefactos pre-declarados
- ≤ 2 roles activados
- Objetivo con formato "Verbo + objeto + criterio de done"

**Flujo:** [B] preflight → [A] plan → [G] implementar → [O] cerrar → validate → CHG + EVD

### W8 · Exploración

**ID:** `w8_exploracion`  
**Cuándo usar:** Cuando no hay objetivo concreto previo pero sí área de interés — explorar, auditar, buscar qué mejorar.  
**Cuándo NO:** Si ya tienes objetivo concreto → usar W7.

| | W7 (foco) | W8 (exploración) | W0 (libre) |
|---|:---:|:---:|:---:|
| Preflight obligatorio | ✅ | ✅ mínimo | ❌ |
| Objetivo declarado | ✅ concreto | 📋 área de interés | ❌ |
| Artefactos planificados | ≥ 3 obligatorio | ≥ 1 orientativo | ❌ |
| Roles máximos | 2 | 2 | libre |

### W9 · Cosecha Contextual

**ID:** `w9_cosecha`  
**Cuándo usar:** Cuando hay pensamiento útil generado en exploración libre (modo W0/W8) que no ha sido formalizado.  
**Propósito:** Capturar valor generado durante trabajo sin estructura antes de que se pierda.

```bash
python3 bago cosecha   # o: bago cosecha
```

**Flujo interactivo:**
1. ¿Qué problema resolviste o decisión tomaste?
2. ¿Qué descartaste y por qué?
3. ¿Cuál es el siguiente paso concreto?

**Produce:** SES-HARVEST-*, CHG, EVD — todo en < 5 minutos.

---

## 6. Roles del sistema

BAGO tiene 7 roles con fronteras bien definidas. La regla global: **no más de 3 roles activos simultáneamente** salvo excepción justificada.

| Rol | Función | Activa cuándo |
|---|---|---|
| **MAESTRO_BAGO** | Coordina la sesión, identifica modo predominante, mantiene el hilo | Siempre — es el coordinador central |
| **ANALISTA_Contexto** | Aclara problema, separa hechos de supuestos, detecta restricciones y riesgo | Problema insuficientemente delimitado |
| **ARQUITECTO_Soluciones** | Diseña enfoque técnico, límites estructurales, secuencia de implementación | Se toca estructura, contratos o integración |
| **GENERADOR_Contenido** | Produce artefactos técnicos utilizables (código, docs, scripts) | Hay diseño suficiente para producir |
| **ORGANIZADOR_Entregables** | Empaqueta, resume, cierra y deja continuidad | Múltiples artefactos, handoff o cierre |
| **GUIA_VERTICE** | Metacontrol — detecta deriva, incoherencia o rediseño no controlado | Solo con evidencia de problema sistémico |
| **ADAPTADOR_PROYECTO** | Bootstrap de proyecto — adapta BAGO a un repo concreto | Primer arranque en repo desconocido |

### Matriz de activación por modo

| Modo | Obligatorio | Opcional |
|---|---|---|
| [B] Balanceado | MAESTRO_BAGO | ANALISTA_Contexto |
| [A] Adaptativo | MAESTRO_BAGO | ANALISTA, ARQUITECTO |
| [G] Generativo | MAESTRO_BAGO | GENERADOR, ARQUITECTO |
| [O] Organizativo | MAESTRO_BAGO | ORGANIZADOR |
| Revisión evolutiva | — | GUIA_VERTICE (solo con evidencia) |

### Tipos de rol normalizados (para validación)

- `government` — roles de coordinación y gobierno
- `production` — roles de generación
- `supervision` — roles de auditoría y control
- `specialist` — roles especializados

---

## 7. Artefactos de estado

### global_state.json

El estado centralizado del pack. Campos principales:

| Campo | Descripción |
|---|---|
| `bago_version` | Versión del sistema |
| `active_session_id` | Sesión actualmente en curso |
| `active_roles` | Roles activados en la sesión actual |
| `active_workflows` | Workflows activos |
| `active_scenarios` | Escenarios activos |
| `inventory.sessions` | Contador de sesiones |
| `inventory.changes` | Contador de CHGs |
| `inventory.evidences` | Contador de EVDs |
| `last_completed_*` | Datos de la última sesión completada |
| `baseline_status` | Estado del baseline (active_clean_core, etc.) |

### Sesiones (SES-*.json)

Cada sesión genera un artefacto JSON con:
- `id` — identificador único (ej: `SES-W7-2026-04-19-001`)
- `workflow` — workflow utilizado
- `objective` — objetivo declarado
- `roles` — roles activados
- `artifacts_planned` — artefactos pre-declarados
- `artifacts_produced` — artefactos producidos
- `decisions` — decisiones tomadas
- `status` — estado del ciclo de vida

**Prefijos de tipo:**
- `SES-W7-` — sesión foco (productiva)
- `SES-W8-` — sesión exploración
- `SES-HARVEST-` — cosecha W9
- `SES-ON-` / `SES-OFF-` — competición on/off (ESCENARIO-002)

### Cambios (BAGO-CHG-*.json)

Registro de mutaciones estructurales. Campos clave:
- `id` — `BAGO-CHG-NNN`
- `severity` — `patch` / `minor` / `major`
- `description` — qué cambió
- `rationale` — por qué
- `files_affected` — archivos impactados
- `session_id` — sesión que lo generó

### Evidencias (BAGO-EVD-*.json)

Registro de decisiones, validaciones y mediciones. Tipos:
- `decision` — decisión tomada con justificación
- `validation` — resultado de validación (GO/KO)
- `incident` — evento no deseado
- `closure` — cierre de sesión
- `handoff` — traspaso entre sesiones
- `measurement` — métrica medida

### pending_w2_task.json

Tarea W2 activa generada por `bago ideas --accept N`. Campos:
- `idea_title`, `idea_index`
- `objetivo`, `alcance`, `no_alcance`
- `archivos_candidatos`
- `validacion_minima`
- `metric`
- `siguiente_paso`
- `workflow`, `priority`
- `status` — `pending` / `done`
- `accepted_at`

### implemented_ideas.json

Registro de ideas ya implementadas. Cada entrada:
- `title` — título de la idea
- `idea_index` — índice en el selector
- `done_at` — timestamp ISO

---

## 8. Herramientas (tools/)

### Herramientas de validación

| Herramienta | Comando | Descripción |
|---|---|---|
| `validate_pack.py` | `bago validate` | Valida manifiesto, estado y pack completo. Salida: GO/KO en 3 líneas |
| `validate_manifest.py` | — | Valida pack.json contra schema |
| `validate_state.py` | — | Valida global_state.json contra schema |
| `reconcile_state.py` | — | Sincroniza contadores del estado con archivos reales en disco |
| `stale_detector.py` | `bago stale` | Detecta contradicciones entre global_state y disco (inventario, escenarios activos) |

### Herramientas de salud y auditoría

| Herramienta | Comando | Descripción |
|---|---|---|
| `health_score.py` | `bago health` | Score 0-100 en 5 dimensiones (ver §11) |
| `audit_v2.py` | `bago audit` | Auditoría integral: validate + reconcile + stale + health + vértice + workflow |
| `stability_summary.py` | `bago stability` | Resumen smoke/VM/soak + validadores en un solo bloque GO/WARN/KO |
| `context_detector.py` | `bago detector` | Detecta señales de madurez. Veredicto: HARVEST / WATCH / CLEAN |

### Herramientas de sesión

| Herramienta | Comando | Descripción |
|---|---|---|
| `session_preflight.py` | `bago session` (indirecto) | Valida reglas W7 antes de abrir sesión (objetivo, roles, artefactos) |
| `session_opener.py` | `bago session` | Lee pending_w2_task.json y lanza session_preflight con datos pre-rellenados |
| `show_task.py` | `bago task` | Muestra/gestiona la tarea W2 pendiente |
| `session_stats.py` | — | Estadísticas de sesiones (producción, foco, disciplina) |

### Herramientas de ideas

| Herramienta | Comando | Descripción |
|---|---|---|
| `emit_ideas.py` | `bago ideas` | Genera y filtra 5 ideas contextuales. Gate canónico integrado. |

### Herramientas de contexto y workflow

| Herramienta | Comando | Descripción |
|---|---|---|
| `workflow_selector.py` | `bago workflow` | Selector interactivo de workflows con descripción y criterios |
| `inspect_workflow.py` | — | Inspecciona un workflow por ID |
| `repo_context_guard.py` | `bago setup` | Gestiona el modo de trabajo (self / external) y sincroniza contexto |
| `cosecha.py` | `bago cosecha` | Protocolo W9 interactivo (3 preguntas → SES + CHG + EVD) |

### Herramientas de gobernanza y display

| Herramienta | Comando | Descripción |
|---|---|---|
| `bago_banner.py` | `bago` | Cartel principal con estado, inventario, task activa y comandos |
| `pack_dashboard.py` | `bago dashboard` | Dashboard visual con semáforos y KPIs del pack |
| `vertice_activator.py` | — | Evalúa si se debe activar GUIA_VERTICE |
| `personality_panel.py` | — | Gestiona el perfil de personalidad del usuario |

### Herramientas de análisis avanzado

| Herramienta | Descripción |
|---|---|
| `artifact_counter.py` | Cuenta artefactos por tipo y sesión |
| `competition_report.py` | Reporte de competición ESCENARIO-002 (on vs off) |
| `generate_bago_evolution_report.py` | Genera informe de evolución del sistema |
| `dashboard_v2.py` | Dashboard extendido V2 |
| `perf/stress_bago_agents.py` | Test de estrés de agentes |
| `perf/render_perf_charts.py` | Genera gráficas de rendimiento |

---

## 9. Sistema de ideas y handoff

El sistema de ideas es el mecanismo de **evolución continua** de BAGO — propone qué mejorar a continuación, contextualizado con el estado real del sistema.

### Flujo completo de una idea

```
bago stability          # 1. Verificar salud antes de idear
        ↓
bago ideas              # 2. Ver ideas priorizadas (gate canónico automático)
        ↓
bago ideas --detail N   # 3. Ampliar detalle de la idea elegida
        ↓
bago ideas --accept N   # 4. Generar handoff → pending_w2_task.json
        ↓
bago task               # 5. Ver la tarea generada
        ↓
bago session            # 6. Abrir sesión W2 con preflight pre-rellenado
        ↓
[implementar]
        ↓
bago task --done        # 7. Marcar como completada → registra en implemented_ideas.json
```

### Gate canónico (automático en `bago ideas`)

Antes de mostrar ideas, se ejecuta automáticamente:
1. `validate_pack.py` — si KO, **bloquea** con exit 1
2. `validate_state.py` — si KO, **bloquea** con exit 1
3. `last-report.json` (smoke) — si disponible y falla, **bloquea**

Mensaje cuando bloquea: `KO → ninguna idea avanza. Ejecuta bago stability para el detalle.`

### Cómo se generan las ideas

Las ideas son **contextuales y evolutivas**:
- Detectan qué features ya están implementadas (`detect_implemented_features()`)
- Proponen el **siguiente nivel** de cada feature, no la misma idea repetida
- Filtran ideas cuyos títulos ya están en `implemented_ideas.json`
- En `baseline_clean_mode`: solo se muestran ideas con `risk=low` y métrica declarada

**Generaciones de ideas (ejemplo línea 1):**

| Generación | Estado del sistema | Idea propuesta |
|---|---|---|
| Gen 1 | Sin handoff | "Handoff idea → W2" |
| Gen 2 | show_task.py existe | "Opener de sesión desde task" |
| Gen 3 | session_opener.py existe | "Cierre automático de sesión" |

### Handoff (pending_w2_task.json)

Al aceptar una idea con `--accept N`, se genera automáticamente un handoff que contiene todo lo necesario para abrir la sesión:
- Objetivo formulado
- Alcance y no-alcance
- Archivos candidatos
- Validación mínima
- Métrica de éxito
- Siguiente paso

El handoff persiste en disco — no se pierde entre sesiones.

---

## 10. Ciclo de sesión completo

### Sesión productiva estándar (W7)

```bash
# 1. ARRANQUE
python3 bago                # ver estado + task activa
python3 bago health         # verificar salud (opcional si bago validate GO)
python3 bago validate       # confirmar pack GO

# 2. PREFLIGHT (obligatorio en W7)
python3 bago session        # si hay pending_w2_task.json
# o manualmente:
python3 .bago/tools/session_preflight.py \
  --objetivo "Implementar X para que Y sea verificable" \
  --roles "role_architect,role_validator" \
  --artefactos ".bago/tools/archivo.py,.bago/state/global_state.json,bago"

# 3. TRABAJO
# ... implementar cambios ...

# 4. CIERRE
python3 bago validate       # pack GO
python3 bago stale          # sin contradicciones
# registrar CHG + EVD (manual o via cosecha)
```

### Sesión de exploración (W8)

```bash
python3 bago                # arranque
python3 bago ideas          # ver ideas
# explorar libremente
python3 bago cosecha        # formalizar lo generado
```

### Cierre de ideas implementadas

```bash
python3 bago task           # ver tarea activa
python3 bago task --done    # marcar completada → registra en implemented_ideas.json
# la próxima vez que se ejecute bago ideas, la idea no volverá a aparecer
```

---

## 11. Métricas de salud

`bago health` produce un score de 0-100 en 5 dimensiones:

| Dimensión | Peso | Cómo se calcula |
|---|---|---|
| **Integridad** | 25 pts | `validate_pack` GO = 25, KO = 0 |
| **Disciplina workflow** | 20 pts | `roles_medios_últimas_10` ≤ 2.0 → 20, hasta 5.0 → proporcional |
| **Captura decisiones** | 20 pts | `decisiones/sesión` últimas 10 ≥ 2.0 → 20, proporcional |
| **Estado stale** | 15 pts | `stale_detector` sin issues → 15, cada issue resta puntos |
| **Consistencia inventario** | 20 pts | Contadores global_state vs archivos reales en disco |

**Lectura del score:**

| Score | Estado | Emoji |
|---|---|---|
| 90-100 | Excelente | 🟢 |
| 70-89 | Bueno | 🟡 |
| 50-69 | Atención requerida | 🟠 |
| < 50 | Crítico | 🔴 |

---

## 12. Gates y validación

### validate_pack.py

Valida tres capas en secuencia:
1. **GO manifest** — pack.json consistente con schema
2. **GO state** — global_state.json consistente con schema
3. **GO pack** — CHECKSUMS.sha256 y TREE.txt regenerados y consistentes

Si alguna falla, **todo el sistema de ideas se bloquea**.

### validate_state.py

Valida que global_state.json tenga los campos y tipos correctos.

### reconcile_state.py

Resuelve discrepancias entre contadores del estado y archivos reales en disco. Útil cuando se detecta un KO de inventario.

```bash
python3 .bago/tools/reconcile_state.py
```

### Gates de ideas (emit_ideas.py)

El sistema de ideas tiene tres gates apilados:

| Gate | Cuándo actúa | Efecto |
|---|---|---|
| **Canónico** | Al invocar `bago ideas` | Bloquea si validate_pack o validate_state no son GO |
| **Smoke** | Al invocar `bago ideas` | WARN si no disponible; KO si disponible y falla |
| **Métrica** | Al invocar `bago ideas --accept N` | Rechaza con exit 1 si la idea no tiene campo `metric` |

### session_preflight.py

Valida tres reglas W7:
- **Regla A** — ≥ 3 artefactos pre-declarados (sin contar JSON de sesión)
- **Regla B** — ≤ 2 roles activados
- **Regla C** — objetivo con formato "Verbo + objeto + criterio de done"

---

## 13. Detectores automáticos

### context_detector.py (W9)

Detecta señales de madurez cognitiva y técnica. Busca:
- Keywords cognitivas en sesiones (`decidí`, `descarto`, `mejor opción`, `la solución`)
- Densidad de decisiones recientes
- Acumulación de trabajo sin formalizar

**Veredictos:**
- 🌾 **HARVEST** — hay valor acumulado para cosechar → ejecutar `bago cosecha`
- 👁 **WATCH** — señales presentes pero insuficientes
- ✔ **CLEAN** — estado nominal, no hay necesidad de cosecha

El banner muestra el veredicto en tiempo real.

### stale_detector.py

Detecta contradicciones entre el estado y el disco:
- Escenarios activos sin archivo correspondiente en `state/scenarios/`
- Discrepancias de inventario (contadores vs archivos reales)
- Sesiones activas huérfanas

---

## 14. Escenarios de experimentación

Los escenarios son experimentos estructurados con hipótesis, protocolo y métricas. Se declaran en `state/scenarios/`.

### ESCENARIO-001 · Foco de sesión

**Hipótesis:** Un preflight estricto (objetivo + roles + artefactos pre-declarados) mejora la producción de artefactos y el foco.  
**Protocolo:** Usar W7 con session_preflight.py en todas las sesiones productivas.  
**Métricas:** producción de artefactos, disciplina de roles, decisiones por sesión.

### ESCENARIO-002 · Competición ON vs OFF

**Hipótesis:** Las sesiones con BAGO activo producen más y mejor que las sesiones libres.  
**Protocolo:** Alternar sesiones W7 (on) con sesiones W0 (off), registrar métricas comparativas.  
**Herramienta:** `competition_report.py`

### ESCENARIO-003 · Cosecha de contexto libre (W9)

**Hipótesis:** El trabajo libre genera pensamiento útil que se pierde si no se formaliza.  
**Protocolo:** Al detectar HARVEST, ejecutar `bago cosecha` para formalizar en < 5 minutos.  
**Resultado:** W9 + `cosecha.py` + `context_detector.py` implementados.

---

## 15. Perfil de personalidad

BAGO mantiene un perfil de personalidad del usuario que adapta el estilo de interacción.

```bash
python3 .bago/tools/personality_panel.py
```

**Campos del perfil (`state/user_personality_profile.json`):**

| Campo | Descripción |
|---|---|
| `personality.style` | Estilo de comunicación preferido |
| `personality.notes` | Notas adicionales sobre preferencias |
| `language.primary` | Idioma principal (`es` / `en`) |
| `preferences.verbosity` | Nivel de detalle (`concise` / `normal` / `verbose`) |
| `preferences.tone` | Tono preferido |

---

## 16. Extensiones Copilot CLI

BAGO soporta extensiones personalizadas para GitHub Copilot CLI.

```bash
bago extensions          # lista extensiones disponibles
bago setup               # instala/reinstala extensiones
```

**Estructura:**
```
.bago/extensions/
  nombre-extension/
    extension.mjs       ← fuente
.github/extensions/
  nombre-extension/
    extension.mjs       ← destino (instalado por bago setup)
```

---

## 17. Gobernanza y canon

### Cambios sensibles

Requieren **validación humana explícita** antes de ejecutar:
- Arquitectura del sistema
- Contratos públicos o internos de `.bago/`
- Migraciones de datos
- Seguridad o permisos
- Cambios destructivos
- CI/CD base

### Principios de gobernanza

- **Claridad sobre estética** — un sistema que funciona vale más que uno que parece perfecto
- **Trazabilidad sobre velocidad ciega** — dejar rastro es más valioso que ser rápido
- **Reparar antes que castigar** — un KO es una oportunidad de mejora, no un fallo moral
- **Supervisión solo con evidencia** — GUIA_VERTICE no entra por defecto

### Canon

El canon es el conjunto de reglas y contratos que gobiernan el sistema. Vive en `.bago/core/canon/`:
- `CANON.md` — documento raíz del canon
- `TAXONOMIA.md` — vocabulario operativo normalizado
- `REGLAS_DE_ACTIVACION.md` — cuándo y cómo activar roles
- `PROTOCOLO_DE_CAMBIO.md` — cómo registrar cambios
- `CONTRATOS/` — contrato de cambio, evidencia, rol y workflow

### Regla de introducción de nuevos términos

Un término nuevo solo entra al sistema si:
1. Nombra una frontera real
2. No duplica otro término existente
3. Aporta claridad o control
4. Se documenta en TAXONOMIA.md y, si procede, en el schema

---

## 18. Glosario operativo

| Término | Definición |
|---|---|
| **BAGO** | Ciclo de trabajo: Balanceado, Adaptativo, Generativo, Organizativo |
| **Repo-first** | Leer el repositorio real antes de sobrerrepresentar metaestructura |
| **Estado estructurado** | Archivos JSON que representan el estado vivo (sesiones, cambios, evidencias) |
| **Activación mínima suficiente** | Solo activar los roles necesarios para la tarea actual |
| **Deriva** | Desplazamiento no controlado entre función declarada y uso real |
| **Gate canónico** | Bloqueo automático que impide avanzar si los validadores no son GO |
| **Handoff** | Artefacto que transfiere contexto entre fases (ideas → implementación → sesión) |
| **Cosecha** | Formalización de pensamiento generado en trabajo libre (W9) |
| **Baseline** | Estado mínimo estable del sistema que no debe degradarse |
| **Clean core** | Estado del baseline donde solo hay trabajo de bajo riesgo y con métrica |
| **Pack** | El conjunto completo de artefactos BAGO (manifiesto + estado + herramientas) |
| **Reserva** | Hallazgo que no invalida el sistema pero impide considerarlo maduro sin acotaciones |
| **GO con reservas** | Resultado de validación que acepta uso operativo pero obliga a documentar límites |
| **Fábrica de prompts** | Mecanismo para convertir una necesidad compleja en prompts reutilizables |
| **Arranque suficiente** | Carga mínima necesaria para operar con criterio sin sobredocumentar |
| **Stale** | Estado en que hay contradicción entre lo declarado y la realidad del disco |
| **Vértice** | Punto de observación metacognitiva — solo activo con evidencia de problema sistémico |

---

*Documento generado automáticamente el 2026-04-19. Para actualizar: revisar las herramientas, workflows y estado actuales del pack.*
