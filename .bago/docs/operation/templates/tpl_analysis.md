# Plantilla de sesión — `analysis`

> Para sesiones de evaluación, auditoría, diagnóstico o investigación.  
> La producción mínima es un informe + un registro de evaluación.

---

## Preflight checklist

```bash
python3 .bago/tools/session_preflight.py \
  --objetivo "TODO: Analizar/Evaluar [objeto] para que [resultado accionable]" \
  --roles "role_auditor,role_organizer" \
  --artefactos "docs/analysis/INFORME.md,state/evaluations/EVAL.md,state/metrics/metrics_snapshot.json" \
  --task-type analysis
```

> `state/evaluations/` y `state/metrics/` se crean automáticamente en primer uso. No es necesario crearlos manualmente.

---

## Datos de sesión

| Campo | Valor |
|-------|-------|
| **session_id** | `SES-EVAL-YYYY-MM-DD-00N` |
| **task_type** | `analysis` |
| **selected_workflow** | `w7_foco_sesion` o `workflow_analisis` |
| **roles** | `role_auditor` + `role_organizer` |
| **objetivo** | TODO |

---

## Artefactos planificados

### Obligatorios
```
docs/analysis/<NOMBRE>_INFORME.md       # informe principal con hallazgos
state/evaluations/<NOMBRE>_EVAL.md      # registro estructurado
```

### Opcionales según alcance
```
state/metrics/metrics_snapshot.json     # si actualiza métricas globales
docs/analysis/<NOMBRE>.html             # si hay visualización Chart.js
state/scenarios/ESCENARIO-*.md          # si propone escenario de mejora
```

---

## Estructura del informe (docs/analysis/)

```markdown
# [Título del análisis]

**Fecha:** YYYY-MM-DD  
**Scope:** [qué se analizó]  
**Metodología:** [cómo]

## Hallazgos principales
1. …
2. …

## Métricas
| Métrica | Valor | Comparación |
|---------|-------|-------------|
| …       | …     | …           |

## Recomendaciones
- …

## Acciones derivadas
- [ ] …
```

---

## Estructura del registro de evaluación (state/evaluations/)

```markdown
# [ID-EVAL] — [Título]

**Estado:** ACTIVO | ARCHIVADO  
**Sesión origen:** SES-EVAL-*  
**Fecha:** YYYY-MM-DD

## Resultado
[GO | KO | PARCIAL]

## Evidencias
- [referencia a artefactos]

## Notas
```

---

## Checklist de cierre

- [ ] Informe generado con hallazgos y recomendaciones concretas
- [ ] `metrics_snapshot.json` actualizado si aplica
- [ ] CHG + EVD creados
- [ ] `global_state.json` inventario actualizado
- [ ] TREE + CHECKSUMS → validate_pack GO
