# Guía de producción de artefactos — BAGO

**Versión:** 1.0  
**Actualizado:** 2026-04-18  
**Audiencia:** agentes y operadores del pack BAGO

---

## ¿Qué cuenta como artefacto útil?

Un **artefacto útil** es cualquier archivo que aporte valor permanente al pack o al proyecto, más allá del overhead de protocolo.

| ✅ Cuenta como útil | ❌ NO cuenta (protocolo) |
|---------------------|--------------------------|
| Scripts y herramientas (`tools/*.py`) | `state/sessions/*.json` |
| Documentación (`docs/**/*.md`, `*.html`) | `state/changes/*.json` |
| Plantillas (`docs/operation/templates/*`) | `state/evidences/*.json` |
| Workflows (`workflows/W*.md`) | `TREE.txt` |
| Informes y análisis (`state/evaluations/*`) | `CHECKSUMS.sha256` |
| Configuración (`pack.json`, roles, prompts) | |
| Cualquier archivo en `dist/`, `examples/` | |

**Regla práctica:** si el archivo existiría aunque BAGO no tuviera protocolo de sesión, es útil.

---

## Mínimo por sesión (ESCENARIO-001)

| Umbral | Significado |
|--------|-------------|
| ≥ 4 útiles | ✅ Sesión productiva — contribuye al target |
| 2–3 útiles | ⚠️ Sesión marginal — justificar por qué el scope era pequeño |
| 0–1 útil  | ❌ Sesión vacía — no debería suceder con preflight activo |

---

## Artefactos por tipo de tarea

### `system_change` (cambio en el pack)

Declarar al menos estos en `artifacts_planned`:

```
tools/<nombre>.py               # la herramienta creada/modificada
docs/operation/<GUIA>.md        # documentación de la herramienta
workflows/<W_modificado>.md     # si el workflow cambia
core/<archivo>.md               # si afecta al core
```

### `analysis` (evaluación, auditoría, diagnóstico)

```
docs/analysis/<INFORME>.md        # informe principal
state/evaluations/<EVAL>.md       # registro de evaluación
state/metrics/metrics_snapshot.json  # si actualiza métricas
docs/analysis/<HTML>.html         # si hay visualización
```

### `sprint`

```
state/sessions/SES-S<N>-*.json     # sesión de sprint (protocolo, no cuenta)
docs/operation/<RESULTADO>.md      # entregable del sprint
state/changes/BAGO-CHG-*.json      # al menos 1 cambio
<todos los artefactos del sprint>
```

### `execution` (implementación de feature o fix)

```
<archivo_modificado_1>
<archivo_modificado_2>
tests/<prueba>.py   # si hay test
docs/<referencia>.md
```

### `project_bootstrap`

```
.bago/state/repo_context.json
docs/operation/PROYECTO_<NOMBRE>.md
state/sessions/SES-BOOT-*.json
```

---

## Cómo medir la producción de una sesión

```bash
# Desde BAGO_CAJAFISICA/
python3 .bago/tools/artifact_counter.py            # todas las sesiones
python3 .bago/tools/artifact_counter.py -n 5       # últimas 5
python3 .bago/tools/artifact_counter.py --escenario # resumen ESCENARIO-001
python3 .bago/tools/artifact_counter.py -v          # detalle por sesión
```

---

## Estrategias para maximizar producción útil

### 1. Declarar más artefactos que los mínimos

La regla dice ≥3. La meta real es ≥5 cuando el scope lo permite. Antes de abrir la sesión, pregunta:

- ¿Hay un script que podría automatizar algo de lo que voy a hacer?
- ¿Hay documentación que debería existir y no existe?
- ¿Hay una plantilla que evitaría trabajo repetitivo en el futuro?
- ¿El resultado de esta sesión debería quedar como guía?

### 2. Convertir decisiones en artefactos

Cada decisión tomada en `decisions[]` debería tener un artefacto asociado:

| Decisión | Artefacto derivado |
|----------|-------------------|
| "Usamos X porque Y" | `docs/decisions/ADR-<N>.md` |
| "El proceso correcto es A→B→C" | `docs/operation/<PROCESO>.md` |
| "Esta herramienta hace X" | `tools/<herramienta>.py` + sección en GUIA |

### 3. Plantillas → producción rápida

Usar las plantillas de `docs/operation/templates/` para que el tiempo de escritura no sea el cuello de botella. Ver las plantillas disponibles en esa carpeta.

### 4. No esperar al cierre para producir

Los artefactos se crean DURANTE la sesión, no al final. Al cerrar solo se actualiza el campo `artifacts` con lo que ya existe en disco.

### 5. El test del borrado

Antes de cerrar la sesión, pregunta: *"si borrara el JSON de sesión, ¿quedaría algo útil en el repo?"*  
Si la respuesta es NO → la sesión no fue productiva, independientemente de lo que digan los JSONs de protocolo.

---

## Categorías de artefactos disponibles en BAGO

| Categoría | Directorio | Ejemplos |
|-----------|-----------|---------|
| Herramientas | `tools/` | `artifact_counter.py`, `session_preflight.py` |
| Workflows | `workflows/` | `W7_FOCO_SESION.md` |
| Core | `core/` | cerebro, principios, roles |
| Operación | `docs/operation/` | guías, checklists, plantillas |
| Análisis | `docs/analysis/` | informes HTML/MD |
| Evaluaciones | `state/evaluations/` | registros de auditoría |
| Plantillas | `docs/operation/templates/` | tpl_*.md |
| Distribución | `dist/source/` | ZIPs de versión |
| Métricas | `state/metrics/` | snapshots, CSV |
| Escenarios | `state/scenarios/` | ESCENARIO-*.md |

---

## Referencia cruzada

- `tools/session_preflight.py` — valida ≥3 artefactos antes de abrir sesión
- `tools/artifact_counter.py` — mide producción histórica
- `workflows/W7_FOCO_SESION.md` — workflow que aplica estas reglas
- `state/scenarios/ESCENARIO-MEJORA-ARTEFACTOS-FOCO.md` — experimento activo
