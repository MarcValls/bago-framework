# ESCENARIO-002 · Competición `.bago/on` vs `.bago/off`

**ID:** ESCENARIO-002  
**Creado:** 2026-04-18  
**Estado:** ACTIVO  
**Depende de:** ESCENARIO-001 (reglas W7 activas en el grupo `on`)

---

## 1. Pregunta del experimento

> **¿Cuánto valor añade el protocolo BAGO (preflight + W7 + roles declarados + artefactos pre-planificados) respecto a trabajo libre sin estructura?**

---

## 2. Grupos del experimento

| Grupo | Nombre | Workflow | Preflight | Roles | Artefactos pre-declarados |
|-------|--------|----------|-----------|-------|--------------------------|
| A | `.bago/on` | `W7_FOCO_SESION` | ✅ obligatorio | ≤ 2 | ✅ mínimo 3 |
| B | `.bago/off` | `W0_FREE_SESSION` | ❌ no ejecutar | libre | ❌ no pre-declarar |

Cada grupo ejecuta **5 sesiones** del mismo tipo de tarea.  
Al finalizar, se comparan los resultados con `competition_report.py`.

---

## 3. Tipos de tarea elegidos para el experimento

Para que la comparación sea justa, ambos grupos trabajan tareas **equivalentes**:

| Ronda | Tipo | Descripción de la tarea equivalente |
|-------|------|-------------------------------------|
| 1 | `system_change` | Crear/mejorar una herramienta del pack |
| 2 | `analysis` | Analizar el estado de algún componente del pack |
| 3 | `system_change` | Crear documentación operativa |
| 4 | `execution` | Actualizar o corregir un artefacto existente |
| 5 | `system_change` | Libre — cualquier mejora al pack |

---

## 4. Métricas comparadas

| Métrica | Descripción | Mejor resultado |
|---------|-------------|-----------------|
| `useful_artifacts` | Artefactos útiles por sesión (excluyendo protocolo) | Más alto |
| `roles_count` | Roles activados por sesión | Más bajo |
| `objective_met` | ¿Se cumplió el objetivo declarado? | 1 = sí |
| `pack_go` | ¿validate_pack GO al cierre? | 1 = sí |
| `planned_vs_delivered` | Ratio artefactos entregados / planificados | Más cercano a 1 |
| `decisions_count` | Decisiones documentadas por sesión | Informativo |

---

## 5. Protocolo de sesión `.bago/off`

Una sesión `.bago/off` **debe** incluir en su JSON:

```json
{
  "session_id": "SES-OFF-YYYY-MM-DD-00N",
  "bago_mode": "off",
  "selected_workflow": "w0_free_session",
  "task_type": "<mismo tipo que la ronda>",
  "roles_activated": ["<los que surjan>"],
  "user_goal": "<puede quedar vago o cambiar>",
  "artifacts": ["<lo que se haya creado>"],
  "status": "closed"
}
```

No ejecutar preflight. No pre-declarar `artifacts_planned`. Trabajar libremente.

---

## 6. Tabla de seguimiento

### Grupo A — `.bago/on` (W7)

| Ronda | Sesión | Útiles | Roles | Objetivo ✅ | Pack GO |
|-------|--------|:------:|:-----:|:-----------:|:-------:|
| 1 | SES-ON-2026-04-18-001 | 2 | 2 | ✅ | ✅ |
| 2 | SES-ON-2026-04-18-002 | 3 | 2 | ✅ | ✅ |
| 3 | SES-ON-2026-04-18-003 | 3 | 2 | ✅ | ✅ |
| 4 | SES-ON-2026-04-18-004 | 3 | 2 | ✅ | ✅ |
| 5 | SES-ON-2026-04-18-005 | 4 | 2 | ✅ | ✅ |

### Grupo B — `.bago/off` (W0)

| Ronda | Sesión | Útiles | Roles | Objetivo ✅ | Pack GO |
|-------|--------|:------:|:-----:|:-----------:|:-------:|
| 1 | SES-OFF-2026-04-18-001 | 1 | 3 | ✅ | ✅ |
| 2 | SES-OFF-2026-04-18-002 | 1 | 4 | ✅ | ✅ |
| 3 | SES-OFF-2026-04-18-003 | 1 | 4 | ✅ | ✅ |
| 4 | SES-OFF-2026-04-18-004 | 1 | 4 | ✅ | ✅ |
| 5 | SES-OFF-2026-04-18-005 | 1 | 4 | ✅ | ✅ |

---

## 7. Cómo ejecutar el reporte

```bash
# Desde BAGO_CAJAFISICA/
python3 .bago/tools/competition_report.py

# Con detalle por sesión
python3 .bago/tools/competition_report.py -v

# Solo las rondas completadas
python3 .bago/tools/competition_report.py --completed
```

---

## 8. Criterio de victoria

| Ganador | Condición |
|---------|-----------|
| `.bago/on` gana | Media útiles ON > OFF y/o media roles ON < OFF |
| `.bago/off` sorprende | Media útiles OFF ≥ ON (revisión de protocolo necesaria) |
| Empate técnico | Δ < 0.5 en útiles y Δ < 0.5 en roles |

Si `.bago/off` produce ≥ útiles que `.bago/on` → **el protocolo añade burocracia sin valor y debe simplificarse**.

---

## 9. Historial de revisiones

| Fecha | Acción | Resultado |
|-------|--------|-----------|
| 2026-04-18 | Escenario creado | ACTIVO |
| 2026-04-18 | R1 completada: ON=2, OFF=1 | EN PROGRESO |
| 2026-04-18 | R2 completada: ON=3, OFF=1 | EN PROGRESO |
| 2026-04-18 | R3 completada: ON=3, OFF=1 | EN PROGRESO |
| 2026-04-18 | R4 completada: ON=3, OFF=1 | EN PROGRESO |
| 2026-04-18 | R5 completada: ON=4, OFF=1. EXPERIMENTO CERRADO. | CERRADO |
| 2026-04-18 | Veredicto: ON gana Δ=+2.0 útiles, −1.8 roles, +3.0 decisiones | CERRADO |
