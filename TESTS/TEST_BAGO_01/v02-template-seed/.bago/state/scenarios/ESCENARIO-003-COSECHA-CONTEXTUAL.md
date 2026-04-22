# ESCENARIO DE MEJORA · Cosecha contextual (standby activo)

**ID:** ESCENARIO-003  
**Creado:** 2026-04-18  
**Estado:** CERRADO ✅  
**Alcance:** pack BAGO — mecanismo de captura de valor en modo exploración libre  

---

## 1. Problema que resuelve

Del ESCENARIO-002 aprendimos que el modo OFF produce:
- **0 decisiones** por sesión (aunque el trabajo cognitivo exista)
- **1 útil** en promedio (el mínimo accidental)
- **≥3 roles** activados (dispersión sin foco)

La causa no es que el pensamiento libre sea malo.  
La causa es que **el valor generado no se captura**.

> El modo OFF no es el enemigo. El verdadero problema es no tener
> un mecanismo que formalice lo útil cuando el pensamiento ha madurado.

---

## 2. Concepto: Cosecha contextual

```
 trabajo libre (.bago/off o exploración sin estructura)
      │
      ▼
 BAGO en standby — observa señales, NO interrumpe
      │
      ▼ ← disparador por CONTEXTO (no por tiempo)
      │
 BAGO sugiere: "hay material suficiente — ¿cosechamos?"
      │
      ▼
 cosecha.py — 3 preguntas, 3 minutos, 1 sesión BAGO cerrada
      │
      ▼
 artefactos formalizados + decisiones registradas + CHG/EVD creados
```

---

## 3. Disparadores de contexto (señales de madurez)

El disparador NO es temporal. Es una señal compuesta:

| Señal | Tipo | Peso |
|-------|------|------|
| ≥3 ficheros modificados sin CHG asociado | técnica | alto |
| ≥1 commit sin sesión BAGO | técnica | medio |
| aparece "decidí / descarto / mejor opción / solución" en texto reciente | cognitiva | alto |
| hay al menos 1 alternativa comparada en el trabajo | cognitiva | muy alto |
| hay al menos 1 descarte explícito | cognitiva | muy alto |

**Umbral de activación:** ≥2 señales de peso alto/muy alto  
→ BAGO muestra: *"Detecto contexto suficiente. ¿Cosechamos?"*

---

## 4. Protocolo de cosecha (W9)

La cosecha es mínima e intencionada. Solo 3 preguntas:

```
1. ¿Qué decidiste en esta exploración?
   (captura la decisión principal — máx. 2 líneas)

2. ¿Qué descartaste y por qué?
   (captura el razonamiento — máx. 2 líneas)

3. ¿Cuál es el próximo paso concreto?
   (define el siguiente artefacto a producir)
```

Con esas 3 respuestas BAGO genera:
- 1 sesión cerrada con `task_type: "harvest"`
- 1 CHG con los artefactos modificados detectados
- 1 EVD con las 3 respuestas como `details`
- `decisions[]` con la respuesta 1 + la respuesta 2

---

## 5. Métricas del escenario

| Métrica | Baseline (modo OFF) | Target W9 | Criterio de éxito |
|---------|:-------------------:|:---------:|-------------------|
| Decisiones capturadas | 0.0/ses | **≥ 2.0/ses** | media ≥2 en 5 cosechas |
| Útiles formalizados | 1.0/ses | **≥ 2.5/ses** | media ≥2.5 en 5 cosechas |
| Tiempo de cosecha | — | **≤ 5 min** | medido desde inicio hasta EVD creada |
| Artefactos que habrían perdido valor | — | **0** | ninguna exploración útil sin cosechar |

---

## 6. Fases del escenario

| Fase | Tarea | Artefactos esperados |
|------|-------|----------------------|
| **F1 — Diseño** | Diseñar `context_detector.py` + `cosecha.py` + W9 | 3 útiles |
| **F2 — Integración** | Conectar detector con `pack_dashboard.py` | 1 útil |
| **F3 — Cosecha real x3** | 3 cosechas reales desde exploración libre | 3 sesiones harvest |
| **F4 — Evaluación** | Comparar harvest vs OFF en métricas | EVAL-E003-FINAL |

---

## 7. Artefactos a crear

```
 tools/context_detector.py     — detecta señales de madurez en el workspace
 tools/cosecha.py              — 3 preguntas → sesión harvest cerrada
 workflows/W9_COSECHA.md       — protocolo formal del workflow harvest
 docs/operation/templates/tpl_harvest.md  — plantilla de sesión harvest
```

---

## 8. Tabla de seguimiento

| Fase | Target útiles | Producido | Roles | ✅ |
|------|:-------------:|-----------|:-----:|:--:|
| F1 — Diseño tools + W9 | ≥3 | 4 | ≤2 | ✅ |
| F2 — Integración dashboard | ≥1 | 1 | ≤2 | ✅ |
| F3a — Cosecha real 1 | ≥2 dec | 2 | ≤2 | ✅ |
| F3b — Cosecha real 2 | ≥2 dec | 2 | ≤2 | ✅ |
| F3c — Cosecha real 3 | ≥2 dec | 2 | ≤2 | ✅ |
| F4 — Evaluación | ≥1 eval | 1 | ≤2 | ✅ |

---

## 9. Hipótesis a validar

> **H1:** Un disparador basado en contexto captura más valor útil que
> un disparador temporal fijo (cada X minutos).

> **H2:** 3 preguntas estructuradas tras exploración libre producen
> tantas decisiones formalizadas como una sesión W7 completa.

> **H3:** La cosecha no penaliza el flujo creativo porque ocurre
> *después* de que el pensamiento haya concluido naturalmente.

---

## 10. Historial de revisiones

| Fecha | Acción | Resultado |
|-------|--------|-----------|
| 2026-04-18 | Escenario diseñado desde conclusiones E001+E002 | ACTIVO |
| 2026-04-18 | F1-F4 completadas — 3/3 hipótesis confirmadas | CERRADO ✅ |
