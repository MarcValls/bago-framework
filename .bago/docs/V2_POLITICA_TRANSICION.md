# BAGO V2 — Política de Transición de Workflows

> Versión: V2.0 | Pack: 2.4-v2rc | Fecha: 2026-04-18

---

## 1. Propósito

Este documento define las **reglas formales de transición** entre los workflows operativos de BAGO V2. Su objetivo es eliminar la ambigüedad en la elección de workflow al inicio de una sesión y proporcionar criterios explícitos para cambiar de modo durante el trabajo.

---

## 2. Tabla de workflows operativos

| ID | Nombre | Uso principal | Artefactos típicos | Roles típicos |
|---|---|---|---|---|
| **W7** | FOCO_SESION | Tarea técnica definida y acotada | 3–6 (código, tests, CHG, EVD) | 2 |
| **W8** | EXPLORACION | Análisis sin entregable fijo | 0–3 (notas, decisiones) | 2–3 |
| **W9** | COSECHA | Formalizar contexto acumulado | 2–4 (EVD, CHG, estado) | 1 |
| **W0** | FREE_SESSION | Libre, experimental, bajo ruido | 0–4 | 2–4 |
| **W2** | IMPL_CONTROLADA | Implementación con gate de calidad | 5–12 | 2–3 |
| **W1** | COLD_START | Bootstrap de repo/proyecto nuevo | 6–15 | 3–4 |
| **WSC** | SYSTEM_CHANGE | Cambio al pack BAGO mismo | 8–15 | 3–5 |

---

## 3. Tabla de transiciones

```
        ┌─────────────────────────────────────────────────────────────┐
        │                DISPARADORES DE ENTRADA                      │
        ├──────────┬──────────────────────────────────────────────────┤
        │ W7       │ Existe tarea técnica definida con criterio de done│
        │ W8       │ Pregunta sin respuesta, análisis exploratorio     │
        │ W9       │ ≥3 sesiones sin EVD formal o decisiones sueltas   │
        │ W0       │ Sesión sin objetivo fijo, experimento, warm-up   │
        │ W2       │ Implementación con contrato de calidad estricto   │
        │ W1       │ Repo nuevo, sin .bago/ o sin estado válido        │
        │ WSC      │ El objeto de trabajo es .bago/ mismo              │
        └──────────┴──────────────────────────────────────────────────┘
```

### 3.1 Transiciones entre modos

| Desde → Hacia | Condición de transición | Acción |
|---|---|---|
| **W0 → W7** | La sesión libre genera una tarea concreta | Registrar como nuevo W7 en siguiente sesión |
| **W0 → W9** | La sesión libre acumula 3+ decisiones informales | Convertir a cosecha (W9) antes de cerrar |
| **W7 → W8** | La tarea requiere investigación previa indefinida | Pausar W7, abrir W8, retomar W7 |
| **W7 → W2** | La tarea requiere contrato de calidad formal | Elevar a W2 desde el inicio de siguiente sesión |
| **W8 → W7** | La exploración define una tarea técnica clara | Cerrar W8, abrir W7 con el output de W8 |
| **W8 → W9** | La exploración produce contexto maduro | Cosechar resultados antes de nueva exploración |
| **W9 → W7** | La cosecha identifica tareas pendientes | Agendar W7 para cada tarea identificada |
| **Cualquiera → WSC** | El trabajo afecta .bago/ mismo | Siempre usar WSC para cambios al pack |
| **Cualquiera → Vértice** | Ver sección 5 | Activar role_vertice |

---

## 4. Disparadores de salida

| Workflow | Señal de salida limpia | Señal de salida anticipada |
|---|---|---|
| **W7** | Criterio de done cumplido, CHG+EVD registrados | Bloqueante externo, scope creep |
| **W8** | Pregunta respondida, output documentado | Sin señal — exploración puede cerrarse en cualquier momento |
| **W9** | Estado formalizado, artefactos archivados | N/A (siempre es corta) |
| **W0** | Sesión completada, 0-N decisiones opcionales | — |
| **W2** | Gate de calidad superado | Fallo de gate → reabrir como W2 o degradar a W7 |
| **WSC** | validate_pack = GO, TREE+CHECKSUMS regenerados | KO → no cerrar hasta GO |

---

## 5. Cuándo activar Vértice

El role_vertice es la revisión estructural del sistema. No es un workflow regular — es una sesión de gobierno.

**Señales de activación:**

| Señal | Umbral | Severidad |
|---|---|---|
| Sesiones W0 consecutivas sin decisiones | ≥ 3 | WARN |
| Health Score | < 60/100 | WARN |
| Escenario activo sin actividad | > 14 días | WARN |
| validate_pack KO recurrente | ≥ 2 sesiones seguidas | ERROR → ACTIVATE |
| Discrepancia inventario/disco | diff > 5 | ERROR |

**Qué hace Vértice:**
- Revisa coherencia del estado global
- Cierra o reencausa escenarios estancados
- Decide si es necesario abrir un nuevo sprint de consolidación
- Documenta decisiones en EVD tipo `governance`

**Cuándo NO activar Vértice:**
- Por warn individual aislado
- Como respuesta a una sesión W0 normal
- Antes de completar el cierre de la tarea actual

---

## 6. Cuándo una sesión W0 debe convertirse en W9

Una sesión W0 debe ser **promovida a W9** cuando se cumpla cualquiera de:

1. Se han capturado ≥ 3 decisiones durante la sesión
2. Se ha generado contexto que cambia el entendimiento del sistema
3. Hay artefactos producidos que merecen ser registrados como evidencias formales
4. La sesión ha durado > 2h o tiene > 6 artefactos

**Mecanismo:** antes de cerrar la sesión W0, re-etiquetar el workflow como `w9_cosecha` y registrar EVD + CHG apropiados.

---

## 7. Métricas observadas (base de datos real)

Distribución histórica de workflows en BAGO (base: 39 sesiones):

| Workflow | Sesiones | % | Artefactos/ses | Decisiones/ses |
|---|---:|---:|---:|---:|
| workflow_system_change | 15 | 38% | 10.47 | 3.53 |
| w7_foco_sesion | 11 | 28% | 5.64 | 3.36 |
| w0_free_session | 5 | 13% | 4.00 | 0.00 |
| w9_cosecha | 3 | 8% | 2.33 | 2.00 |
| workflow_analysis | 2 | 5% | 1.50 | 4.00 |
| workflow_bootstrap_repo_first | 2 | 5% | 7.00 | 3.50 |
| workflow_execution | 1 | 3% | 0.00 | 4.00 |

**Observación clave:** W0 tiene 0.00 decisiones/sesión de media. Es el único workflow que sistemáticamente no captura valor formal. Esto justifica la regla de conversión W0→W9 cuando hay decisiones acumuladas.

---

*Documento parte del ecosistema BAGO V2 — ver también: `V2_CONTRATO_CIERRE_ESCENARIO.md`, `V2_PLAYBOOK_OPERATIVO.md`*
