# BAGO V2 — Playbook Operativo

> Versión: 2.5-stable | Fecha: 2026-04-20  
> Audiencia: Operador técnico que ya conoce BAGO

---

## 1. Cómo arrancar BAGO V2 (bootstrap)

### Primera vez en un repo nuevo

```bash
# 1. Copiar el pack al repo
cp -r .bago/ /tu/repo/.bago/

# 2. Verificar que el pack es válido
cd /tu/repo
python3 .bago/tools/validate_pack.py
# → debe decir: GO pack

# 3. Inicializar el estado para el nuevo repo
# Editar .bago/state/global_state.json:
#   - Cambiar active_session_id, active_task_type
#   - Limpiar inventory a 0/0/0
#   - Limpiar last_completed_* si es repo nuevo

# 4. Ejecutar preflight
python3 .bago/tools/session_preflight.py
```

### Bootstrap con script bago

```bash
# Desde el directorio del proyecto BAGO_CAJAFISICA:
./bago                    # banner + estado
./bago validate           # validar pack
./bago audit              # auditoría V2 completa
./bago health             # solo health score
```

---

## 2. Cómo elegir workflow al inicio de sesión

### Opción A: Selector interactivo

```bash
./bago workflow
# → Responde 4-5 preguntas → recibe recomendación
```

### Opción B: Selector automático (usa global_state)

```bash
python3 .bago/tools/workflow_selector.py --auto
# → Recomienda basándose en estado actual
```

### Opción C: Decisión manual (referencia rápida)

| Situación | Workflow |
|---|---|
| Hay una tarea técnica definida | **W7_FOCO_SESION** |
| La tarea necesita contrato de calidad | **W2_IMPLEMENTACION_CONTROLADA** |
| Exploración, análisis, investigación | **W8_EXPLORACION** |
| Formalizar decisiones/contexto acumulado | **W9_COSECHA** |
| Sin objetivo fijo, experimental | **W0_FREE_SESSION** |
| Bootstrap de repo nuevo | **W1_COLD_START** |
| Modificar el pack .bago/ mismo | **workflow_system_change** |

---

## 3. Cómo cerrar una sesión correctamente

### Checklist de cierre mínimo

```
□ CHG registrado en state/changes/ con tipo correcto
  (architecture | governance | migration)
  
□ EVD registrado en state/evidences/ con tipo correcto
  (decision | validation | incident | closure | handoff | measurement | migration_trace)
  
□ global_state.json actualizado:
  □ last_completed_session_id
  □ last_completed_change_id
  □ last_completed_evidence_id
  □ inventory.sessions / changes / evidences
  □ updated_at

□ Archivo de sesión cerrado en state/sessions/
  con status: "closed" y closed_at

□ TREE.txt + CHECKSUMS sincronizados:
  python3 bago sync   ← regenera TREE+CHECKSUMS
  python3 bago validate  ← verifica (solo lectura)
  → debe decir: GO pack
```

### Cierre rápido con script

```bash
./bago sync          # sincroniza TREE+CHECKSUMS
./bago validate      # verifica integridad (solo lectura)
./bago stale         # verifica sin artefactos stale
```

---

## 4. Cómo cerrar un escenario

Ver contrato completo en `docs/V2_CONTRATO_CIERRE_ESCENARIO.md`.

### Resumen de 5 pasos:

```bash
# 1. Crear EVAL-{ID}-FINAL.md en state/scenarios/
# 2. Actualizar ESCENARIO-{ID}.md → Estado: CERRADO ✅
# 3. Crear EVD tipo "closure" en state/evidences/
# 4. Crear CHG tipo "governance" en state/changes/
# 5. Eliminar escenario de active_scenarios en global_state.json

# Verificar:
./bago stale
# → debe pasar sin ERRORs relacionados con ese escenario
```

---

## 5. Cómo auditar el pack en ≤ 5 minutos

```bash
# Auditoría completa automática:
./bago audit

# Output esperado:
# ═══ BAGO V2 AUDITORÍA ═══
# [1] INTEGRIDAD         ✅ GO pack
# [2] INVENTARIO         ✅ reconciliado
# [3] REPORTING          ✅ Sin artefactos stale
# [4] HEALTH SCORE       🟢 87/100
# [5] VÉRTICE            ✅ CLEAN
# [6] WORKFLOW SUGERIDO  → W7_FOCO_SESION
# ═══ VEREDICTO: ✅ GO V2 ═══

# Auditoría por partes:
./bago validate           # integridad del pack
./bago health             # health score detallado
./bago stale              # artefactos stale
python3 .bago/tools/reconcile_state.py         # inventario
python3 .bago/tools/vertice_activator.py       # señales Vértice
python3 .bago/tools/v2_close_checklist.py      # checklist GO V2
```

---

## 6. Comandos `bago` — referencia rápida

| Comando | Script | Función |
|---|---|---|
| `./bago` | bago_banner.py | Banner + estado del pack |
| `./bago dashboard` | pack_dashboard.py | Dashboard clásico |
| `./bago dashboard --full` | pack_dashboard.py | Dashboard con distribución de workflows |
| `./bago validate` | validate_pack.py | Validar integridad del pack |
| `./bago health` | health_score.py | Health score 0-100 |
| `./bago audit` | audit_v2.py | Auditoría completa V2 |
| `./bago workflow` | workflow_selector.py | Selector interactivo de workflow |
| `./bago stale` | stale_detector.py | Detector de artefactos stale |
| `./bago v2` | v2_close_checklist.py | Checklist GO/KO V2 |
| `./bago cosecha` | cosecha.py | Herramienta de cosecha |
| `./bago detector` | context_detector.py | Detector de contexto |
| `./bago ideas` | emit_ideas.py | Emisor de ideas |

---

## 7. Troubleshooting frecuente

### validate_pack → KO por TREE desactualizado
```bash
# validate es solo lectura. Para sincronizar metadatos:
python3 bago sync
python3 bago validate
```

### Inventario desincronizado
```bash
# Ver diferencias:
python3 .bago/tools/reconcile_state.py

# Aplicar corrección:
python3 .bago/tools/reconcile_state.py --fix
```

### Escenario en estado contradictorio
```bash
# Detectar contradicciones:
./bago stale

# Resolver manualmente:
# 1. Si EVAL existe + escenario en active → cerrar escenario (ver protocolo cierre)
# 2. Si CERRADO en MD + en active → eliminar de active_scenarios en global_state.json
```

### Health Score bajo (< 60)
```bash
# Ver detalle por dimensión:
./bago health

# Cada dimensión indica qué ajustar:
# - Integridad baja → validate_pack KO
# - Disciplina baja → muchos roles por sesión
# - Decisiones bajas → sesiones W0 sin captura formal
# - Stale alto → artefactos contradictorios
# - Inventario bajo → reconcile_state con diff
```

---

*Documento parte del ecosistema BAGO V2 — ver también: `V2_GUIA_EJECUTIVA.md`, `V2_POLITICA_TRANSICION.md`*
