# ESCENARIO DE MEJORA · Producción de artefactos y Foco de sesión

**ID:** ESCENARIO-001  
**Creado:** 2026-04-18  
**Estado:** CERRADO ✅  
**Alcance:** pack BAGO + proyectos externos que usen BAGO  

---

## 1. Diagnóstico de partida

| Métrica | Valor early | Valor late | Δ | Problema |
|---------|:-----------:|:----------:|:---:|---------|
| 📦 Producción artefactos | 4.8 | 4.0 | ▼ -0.8 | Sesiones recientes generan menos artefactos tangibles |
| 🎯 Foco sesión | 3.0 | 6.9 | ▲ +3.9 | Mejora, pero aún se activan demasiados roles por sesión (media 4.0) |

**Causa raíz identificada:**

- **Artefactos**: las sesiones de cierre/consolidación no declaran artefactos obligatorios antes de empezar. Se termina sin output concreto o con solo el JSON de sesión.
- **Foco**: se activan roles por defecto o por precaución, no por necesidad real. Una sesión de `system_change` simple no necesita 6 roles.

---

## 2. Objetivos del escenario

| Métrica | Baseline (now) | Target | Criterio de éxito |
|---------|:--------------:|:------:|-------------------|
| Producción artefactos | 4.0/10 | **≥ 6.0/10** | media ≥ 4 artefactos útiles por sesión en las próximas 5 |
| Foco sesión | 6.9/10 | **≥ 8.5/10** | media ≤ 2 roles por sesión en las próximas 5 |

---

## 3. Protocolo de sesión — reglas obligatorias

Estas reglas se aplican a **toda sesión abierta mientras el escenario esté ACTIVO**.

### Regla A — Declaración previa de artefactos (ANTES de ejecutar)

Al abrir una sesión, declarar en el campo `artifacts_planned` **mínimo 3 artefactos concretos**:

```json
"artifacts_planned": [
  "docs/operation/NOMBRE_DOC.md",
  "state/changes/BAGO-CHG-XXX.json",
  "state/sessions/SES-XXX.json"
]
```

- Los artefactos deben ser archivos reales que se van a crear o modificar.
- El JSON de sesión no cuenta como artefacto útil (es overhead de protocolo).
- Si al cerrar hay menos de 3 artefactos reales: **anotar en `decisions` por qué** y reducir el scope la próxima sesión.

### Regla B — Máximo 2 roles activos por sesión

Seleccionar el rol **principal** y como máximo **1 rol de apoyo**.

| Tipo de tarea | Rol principal | Rol de apoyo (opcional) |
|---------------|--------------|------------------------|
| `system_change` | `role_architect` | `role_validator` |
| `analysis` | `role_auditor` | `role_organizer` |
| `execution` | `role_executor` | `role_validator` |
| `sprint` | `role_organizer` | `role_vertice` |
| `project_bootstrap` | `role_architect` | `role_organizer` |

- Si se necesita un tercer rol, **documentar la excepción** en `decisions`.
- `role_master_bago` y `role_orchestrator` solo se activan en sesiones de coordinación explícita.

### Regla C — Objetivo único por sesión

Cada sesión declara **un objetivo principal** en `user_goal`. Formato:

> **Verbo + objeto + criterio de done**  
> ✅ "Crear guía de mantenimiento del pack con secciones de ciclo de vida y regeneración TREE"  
> ❌ "Trabajar en mejoras del pack y revisar estado y actualizar cosas"

Si emergen más objetivos durante la sesión: **abrir sesión nueva**, no ampliar la actual.

---

## 4. Experimento — 5 sesiones de prueba

Ejecutar **5 sesiones consecutivas** aplicando las 3 reglas. Registrar en cada una:

| Sesión | Artefactos planificados | Artefactos entregados | Roles activados | Objetivo cumplido |
|--------|:-----------------------:|:---------------------:|:---------------:|:-----------------:|
| SES-1 `SES-W7-2026-04-18-001` | 3 | 3 útiles | 2 | ✅ |
| SES-2 `SES-W7-2026-04-18-002` | 6 | 6 útiles | 2 | ✅ |
| SES-3 `SES-W7-2026-04-18-003` | 4 | 4 útiles | 2 | ✅ |
| SES-4 `SES-W7-2026-04-18-004` | ≥3 | 4 útiles | 2 | ✅ |
| SES-5 `SES-W7-2026-04-18-005` | ≥3 | 4 útiles | 2 | ✅ |

**Al finalizar las 5 sesiones:** ejecutar `validate_pack.py` y leer el radar bago-viewer.  
Si las métricas alcanzan los targets → **escenario COMPLETADO**.  
Si no → analizar qué regla se incumplió más y ajustar.

---

## 5. Workflow asociado — W7_FOCO_SESION

Ver `workflows/W7_FOCO_SESION.md` para la secuencia de arranque guiado.  
Usar W7 en lugar de W1 cuando el objetivo de la sesión sea concreto y acotado (no bootstrap).

---

## 6. Cómo medir el resultado

```bash
# Desde BAGO_CAJAFISICA/
python3 -c "
import json
from pathlib import Path
from collections import Counter

root = Path('.bago')
sessions = sorted([json.loads(p.read_text()) for p in (root/'state/sessions').glob('*.json')],
                  key=lambda s: s.get('created_at',''))

# Últimas 5 sesiones (post-escenario)
last5 = sessions[-5:]
roles = [len(s.get('roles_activated',[])) for s in last5]
arts  = [len(s.get('artifacts',[])) for s in last5]
print('Últimas 5 sesiones:')
print(f'  Roles/sesión:      {[r for r in roles]} → media {sum(roles)/len(roles):.1f}')
print(f'  Artefactos/sesión: {[a for a in arts]} → media {sum(arts)/len(arts):.1f}')
print(f'  Foco target (≤2 roles): {\"OK\" if sum(roles)/len(roles) <= 2 else \"FALLA\"}')
print(f'  Producción target (≥4 artefactos): {\"OK\" if sum(arts)/len(arts) >= 4 else \"FALLA\"}')
"
```

---

## 7. Historial de revisiones

| Fecha | Acción | Resultado |
|-------|--------|-----------|
| 2026-04-18 | Escenario creado | ACTIVO |
| 2026-04-18 | SES-1: session_preflight.py creado | 3 art útiles, 2 roles, GO preflight ✅ |
| 2026-04-18 | SES-2: sistema producción máxima (counter + guía + 3 plantillas) | 6 art útiles, 2 roles, score 7.8/10 ✅ |
| 2026-04-18 | SES-3: competition_report.py + W0 + ESCENARIO-002 setup | 4 art útiles, 2 roles ✅ |
| 2026-04-18 | SES-4: W8_EXPLORACION + tpl_exploration | 4 art útiles, 2 roles ✅ |
| 2026-04-18 | SES-5: BAGO_EVOLUCION_v2 + EVAL-E001-FINAL | 4 art útiles, 2 roles ✅ |
| 2026-04-18 | 5 sesiones completadas — media 4.2 útiles, 2.0 roles | ✅ COMPLETADO |
| 2026-04-18 | EVAL-ESCENARIO001-FINAL creado | ✅ CERRADO |
