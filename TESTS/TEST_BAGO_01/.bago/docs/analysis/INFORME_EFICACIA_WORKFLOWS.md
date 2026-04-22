# Informe de eficacia de workflows BAGO

**Fecha actualización:** 2026-04-18 (R4 ESCENARIO-002)  
**Sesión:** SES-ON-2026-04-18-004 (ejecución sobre artefacto existente)  
**Metodología:** análisis de 19 sesiones cerradas — media de artefactos útiles, roles activados y decisiones documentadas por workflow. Excluye artefactos de protocolo.

---

## 1. Ranking de eficacia (por artefactos útiles/sesión)

| Workflow | N | Útiles/ses | Roles/ses | Decisiones/ses | Tipos de tarea |
|----------|:---:|:----------:|:---------:|:--------------:|----------------|
| `workflow_system_change` | 5 | **9.8** | 2.4 | 3.4 | system_change |
| `workflow_bootstrap_repo_first` | 2 | **7.0** | 3.0 | 3.5 | project_bootstrap |
| `w7_foco_sesion` | 6 | **3.5** | **2.0** | **3.5** | system_change, analysis, execution |
| `workflow_analysis` | 2 | 1.5 | 2.5 | 4.0 | analysis, audit |
| `w0_free_session` | 3 | 1.0 | 3.7 | 0.0 | system_change (libre) |
| `workflow_execution` | 1 | 0.0 | 2.0 | 4.0 | execution |

---

## 2. Interpretación

### `workflow_system_change` — máxima producción bruta (9.8)
Las sesiones de cambio sistémico usan este workflow cuando el scope es grande y bien definido. Alta producción refleja que estas sesiones suelen incluir múltiples componentes relacionados (scripts + docs + validadores). No requiere preflight: el scope grande viene dado por el tipo de tarea.

### `workflow_bootstrap_repo_first` — alta producción por naturaleza (7.0)
El bootstrap de un repo nuevo produce muchos artefactos casi automáticamente (app, templates, scripts). No es replicable en sesiones de mantenimiento.

### `w7_foco_sesion` — mejor balance foco/producción (3.5 útiles, 2.0 roles)
Con solo 2 roles medios y buenas decisiones documentadas (3.5/sesión), es el workflow más **sostenible** para el trabajo rutinario. La producción bruta es menor pero la calidad del artefacto y el foco son superiores.

### `w0_free_session` — control negativo (1.0 útil, 0.0 decisiones)
Sin estructura, las sesiones producen 1 útil de promedio (generalmente notas genéricas) con 3.7 roles y 0 decisiones. La brecha con w7 es +2.5 útiles y +1.7 roles menos.

### `workflow_analysis` y `workflow_execution` — nichos específicos
Análisis: alto número de decisiones (4.0) aunque pocos artefactos. Útil para sesiones de auditoría. Execution: sin útiles pero 4 decisiones — sugiere que estas sesiones detectan más que producen.

---

## 3. Métricas ESCENARIO-002 (actualización R4)

| Grupo | N sesiones | Útiles/ses | Roles/ses | Decisiones/ses |
|-------|:---:|:---:|:---:|:---:|
| `.bago/ON` (W7) | 4 | 2.75 | 2.0 | 2.75 |
| `.bago/OFF` (W0) | 3 | 1.0 | 3.67 | 0.0 |
| **Δ** | — | **+1.75** | **−1.67** | **+2.75** |

---

## 4. Recomendaciones por tipo de tarea

| Tipo de tarea | Workflow recomendado | Razón |
|---------------|---------------------|-------|
| Cambio grande (nuevo módulo, herramienta nueva) | `workflow_system_change` | Máxima producción bruta |
| Cambio mediano con control de calidad | `w7_foco_sesion` | Balance foco/producción |
| Análisis o auditoría | `workflow_analysis` | Orientado a decisiones |
| Corrección de artefacto existente | `w7_foco_sesion` | Preflight evita regresiones |
| Sesión exploratoria sin objetivo claro | No recomendado | Usar ESCENARIO-002 off solo para experimento |

---

## 5. Señal de alerta

El workflow `w0_free_session` (OFF) produce **0 decisiones documentadas** en todas las sesiones observadas. Esto indica que las sesiones sin estructura **no generan conocimiento persistente**, solo artefactos de relleno.

Criterio de revisión: si alguna sesión OFF supera 2 útiles o documenta ≥1 decisión real, el protocolo W7 debería revisarse para evaluar si añade burocracia.

---

*Actualizado: 2026-04-18 · Basado en 19 sesiones cerradas*


---

## 1. Ranking de eficacia (por artefactos útiles/sesión)

| Workflow | N | Útiles/ses | Roles/ses | Decisiones/ses | Tipos de tarea |
|----------|:---:|:----------:|:---------:|:--------------:|----------------|
| `workflow_system_change` | 5 | **9.8** | 2.4 | 3.4 | system_change |
| `workflow_bootstrap_repo_first` | 2 | **7.0** | 3.0 | 3.5 | project_bootstrap |
| `w7_foco_sesion` | 4 | 3.8 | **2.0** | **3.8** | system_change |
| `workflow_analysis` | 2 | 1.5 | 2.5 | 4.0 | analysis, audit |
| `w0_free_session` | 1 | 1.0 | 3.0 | 0.0 | system_change |
| `workflow_execution` | 1 | 0.0 | 2.0 | 4.0 | execution |

---

## 2. Interpretación

### `workflow_system_change` — máxima producción bruta (9.8)
Las sesiones de cambio sistémico usan este workflow cuando el scope es grande y bien definido. Alta producción refleja que estas sesiones suelen incluir múltiples componentes relacionados (scripts + docs + validadores). No requiere preflight: el scope grande viene dado por el tipo de tarea.

### `workflow_bootstrap_repo_first` — alta producción por naturaleza (7.0)
El bootstrap de un repo nuevo produce muchos artefactos casi automáticamente (app, templates, scripts). No es replicable en sesiones de mantenimiento.

### `w7_foco_sesion` — mejor balance foco/producción (3.8 útiles, 2.0 roles)
W7 no produce más artefactos brutos que `workflow_system_change`, pero **garantiza foco**: 2.0 roles exactos, 0 deriva de scope, 3.8 decisiones documentadas. Es el workflow más predecible y reproducible. Adecuado para sesiones de mantenimiento incremental.

### `workflow_analysis` — producción baja, decisiones altas (4.0)
Las sesiones de análisis producen pocos archivos pero documentan muchas decisiones. El problema: los informes resultantes no siempre se materializan en artefactos concretos. Mejorable con la plantilla `tpl_analysis.md`.

### `w0_free_session` — peor ratio (1.0 útil, 3.0 roles, 0 decisiones)
Sin estructura, la sesión activa más roles por inercia y produce menos artefactos útiles. Las decisiones no se documentan. Resultado esperado del grupo de control ESCENARIO-002.

### `workflow_execution` — 0 útiles (muestra pequeña)
1 sola sesión, contexto de ejecución pura sin artefactos de output. N insuficiente para conclusiones.

---

## 3. Recomendaciones por tipo de tarea

| Tipo de tarea | Workflow recomendado | Alternativa |
|---------------|---------------------|-------------|
| `system_change` (scope grande) | `workflow_system_change` | `w7_foco_sesion` si el scope es acotado |
| `system_change` (scope pequeño) | `w7_foco_sesion` | — |
| `project_bootstrap` | `workflow_bootstrap_repo_first` | — |
| `analysis` | `w7_foco_sesion` + `tpl_analysis.md` | `workflow_analysis` |
| `sprint` | `w7_foco_sesion` | `workflow_system_change` |
| `execution` | `w7_foco_sesion` | `workflow_execution` |

---

## 4. Conclusión

> **W7 no produce el mayor número bruto de artefactos, pero es el workflow más focalizado y predecible.** Para sesiones incrementales y de mantenimiento, es la mejor opción. Para sesiones de cambio sistémico de gran alcance, `workflow_system_change` sigue siendo más productivo en términos absolutos.

La diferencia clave: `w7_foco_sesion` tiene **0 sesiones con deriva de scope** y **todas las decisiones documentadas**, mientras que los workflows sin preflight presentan variabilidad mayor.

---

## 5. Próximos pasos

- [ ] Ampliar muestra de `workflow_analysis` (solo 2 sesiones) para confirmar tendencia
- [ ] Testear `tpl_analysis.md` en próximas sesiones de análisis para subir producción útil
- [ ] Completar ESCENARIO-002 (4 rondas restantes) para comparación on/off estadísticamente más robusta
