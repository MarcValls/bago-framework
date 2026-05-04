# Guía del Operador BAGO

**Versión:** 1.0 · **Pack:** 2.3-clean  
**Propósito:** Arrancar, ejecutar y cerrar cualquier sesión BAGO sin depender de memoria.

---

## 1. Bootstrap — lo primero siempre

```bash
cd ~/Desktop/BAGO_CAJAFISICA   # o la carpeta donde esté el pack

# Verificar integridad antes de tocar nada
python3 .bago/tools/validate_pack.py
# → debe responder "GO pack"
```

Si responde KO:
- `GO manifest / KO state` → revisar `global_state.json` (campos last_completed)
- `KO pack` → regenerar TREE+CHECKSUMS (ver sección 6)

Leer estado:
```bash
cat .bago/state/global_state.json | python3 -m json.tool | grep -E "last_|inventory|active_"
```

---

## 2. Árbol de decisión — ¿qué sesión arranco?

```
¿Objetivo concreto?
│
├── SÍ → ¿Implica cambiar el pack?
│         ├── SÍ (crear/modificar) → task_type: system_change   → W7
│         ├── SÍ (analizar datos)  → task_type: analysis        → W7
│         ├── SÍ (corregir algo)   → task_type: execution       → W7
│         └── SÍ (ciclo múltiple)  → task_type: sprint          → W7
│
└── NO / explorar libre → ESCENARIO-002 grupo off → W0
```

**Regla de oro:** si dudas entre tipos, elige `system_change`. Es el más productivo.

---

## 3. Abrir sesión (modo ON — W7)

### 3.1 Preflight — paso obligatorio

```bash
python3 .bago/tools/validate_pack.py   # debe ser GO
```

Si KO → no continuar hasta resolver.

### 3.2 Crear JSON de sesión

```bash
python3 -c "
import json, datetime
ses = {
  'session_id': 'SES-YYYY-MM-DD-001',        # ← ajustar
  'task_type': 'system_change',               # ← system_change | analysis | execution | sprint
  'selected_workflow': 'w7_foco_sesion',
  'roles_activated': ['role_architect', 'role_executor'],  # ≤ 2 roles
  'user_goal': '<objetivo concreto en una frase>',
  'status': 'open',
  'bago_mode': 'on',
  'created_at': datetime.datetime.utcnow().isoformat()+'Z',
  'updated_at': datetime.datetime.utcnow().isoformat()+'Z',
  'artifacts_planned': ['<artefacto-1>', '<artefacto-2>', '<artefacto-3>'],  # mínimo 3
  'preflight_resultado': 'GO',
  'artifacts': [],
  'decisions': [],
  'summary': ''
}
open('.bago/state/sessions/SES-YYYY-MM-DD-001.json','w').write(json.dumps(ses,indent=2,ensure_ascii=False))
print('Sesión creada')
"
```

### 3.3 Límites de la sesión ON

| Restricción | Valor |
|-------------|-------|
| Roles máximos | 2 |
| Artefactos planificados mínimos | 3 |
| Preflight | Obligatorio (GO antes de empezar) |
| Artefactos de protocolo excluidos | sessions/, changes/, evidences/, TREE, CHECKSUMS |

---

## 4. Producir artefactos

Orden de prioridad por impacto:

1. **Herramientas** (`tools/*.py`) — máxima reutilización
2. **Análisis/informes** (`docs/analysis/`) — documentan estado real
3. **Documentación operativa** (`docs/operation/`) — guías accionables
4. **Evaluaciones** (`state/evaluations/`) — decisiones con criterio
5. **Actualizaciones de workflows** (`workflows/`) — mejoran el proceso
6. **Notas y snapshots** — solo si hay algo nuevo que decir

Ver criterios completos: `docs/operation/GUIA_ARTEFACTOS.md`

---

## 5. Cerrar sesión

### 5.1 Checklist de cierre

- [ ] Todos los artefactos planificados creados (o documentar por qué no)
- [ ] Campo `artifacts` en la sesión JSON actualizado
- [ ] Campo `decisions` con ≥1 decisión documentada
- [ ] `summary` completado (1-2 líneas: qué, cuántos útiles, roles, preflight)
- [ ] `status: "closed"`

### 5.2 Crear CHG y EVD

```bash
# Siguiente ID disponible:
python3 -c "
from pathlib import Path
c = len(list(Path('.bago/state/changes').glob('*.json')))
e = len(list(Path('.bago/state/evidences').glob('*.json')))
print(f'Siguiente CHG: BAGO-CHG-{c+1:03d}')
print(f'Siguiente EVD: BAGO-EVD-{e+1:03d}')
"
```

Plantilla CHG:
```json
{
  "change_id": "BAGO-CHG-XXX",
  "type": "governance",
  "severity": "minor",
  "title": "<título descriptivo>",
  "motivation": "<por qué se hizo>",
  "status": "applied",
  "affected_components": ["<artefacto-1>", "<artefacto-2>"],
  "related_evidence": "BAGO-EVD-XXX",
  "created_at": "<ISO8601>",
  "updated_at": "<ISO8601>",
  "author": "<rol>"
}
```

Plantilla EVD:
```json
{
  "evidence_id": "BAGO-EVD-XXX",
  "type": "closure",
  "related_to": ["BAGO-CHG-XXX", "SES-YYYY-MM-DD-001"],
  "summary": "<1 línea>",
  "details": "<mínimo una frase de contenido real, no vacío>",
  "status": "recorded",
  "recorded_at": "<ISO8601>"
}
```

### 5.3 Actualizar global_state.json

Campos a actualizar en cada cierre:
```
last_completed_session_id  ← ID de la sesión
last_completed_workflow    ← selected_workflow de la sesión
last_completed_roles       ← roles_activated de la sesión
last_completed_task_type   ← task_type de la sesión
last_completed_change_id   ← ID del CHG creado
last_completed_evidence_id ← ID del EVD creado
inventory.sessions         ← contar archivos en state/sessions/
inventory.changes          ← contar archivos en state/changes/
inventory.evidences        ← contar archivos en state/evidences/
updated_at                 ← ISO8601 actual
```

### 5.4 Regenerar TREE+CHECKSUMS y validar

```bash
cd ~/Desktop/BAGO_CAJAFISICA   # siempre desde aquí, no desde dentro de .bago

python3 -c "
from pathlib import Path; import hashlib
root = Path('.bago')
entries = sorted(str(p.relative_to(root))+('/' if p.is_dir() else '') for p in root.rglob('*'))
(root/'TREE.txt').write_text('\n'.join(entries)+'\n')
lines = []
for p in sorted(root.rglob('*')):
    if p.is_file() and p.name != 'CHECKSUMS.sha256':
        lines.append(f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(root)}')
(root/'CHECKSUMS.sha256').write_text('\n'.join(lines)+'\n')
"
python3 .bago/tools/validate_pack.py
```

Debe terminar en `GO pack`.

---

## 6. Comandos de diagnóstico rápido

### Dashboard rápido (una sola pantalla)

```bash
# Estado completo del pack en una pantalla
python3 .bago/tools/pack_dashboard.py

# Con detalle del ESCENARIO-002 por ronda
python3 .bago/tools/pack_dashboard.py --full
```

### Comandos individuales

```bash
# Score de producción de artefactos (últimas 5 sesiones)
python3 .bago/tools/artifact_counter.py --escenario

# Estadísticas por tipo/workflow/rol
python3 .bago/tools/session_stats.py

# Marcador experimento on/off
python3 .bago/tools/competition_report.py -v

# Inventario real vs declarado
python3 -c "
from pathlib import Path
base = Path('.bago/state')
for d in ['sessions','changes','evidences']:
    n = len(list((base/d).glob('*.json')))
    print(f'{d}: {n}')
"
```

---

## 7. Errores frecuentes → ver `TROUBLESHOOTING.md`
