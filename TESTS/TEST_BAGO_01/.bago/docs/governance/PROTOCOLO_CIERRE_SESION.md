# Protocolo de Cierre de Sesión BAGO

**ID:** governance-cierre-v1  
**Propósito:** Checklist formal para cerrar cualquier sesión dejando el pack en estado GO.

---

## Checklist de cierre

### Paso 1 — Completar el JSON de sesión

```
✅ artifacts[] contiene todos los artefactos realmente creados/modificados
   (excluir: state/sessions/, state/changes/, state/evidences/, TREE.txt, CHECKSUMS.sha256)
✅ decisions[] tiene ≥1 decisión documentada (formato: frase que explica el porqué)
✅ summary completado (1-2 líneas: qué se hizo, cuántos útiles, roles, preflight)
✅ status: "closed"
✅ updated_at: ISO8601 actual
```

### Paso 2 — Obtener siguiente ID disponible

```bash
python3 -c "
from pathlib import Path
c = len(list(Path('.bago/state/changes').glob('*.json')))
e = len(list(Path('.bago/state/evidences').glob('*.json')))
print(f'Siguiente CHG: BAGO-CHG-{c+1:03d}')
print(f'Siguiente EVD: BAGO-EVD-{e+1:03d}')
"
```

### Paso 3 — Crear BAGO-CHG-XXX.json

```json
{
  "change_id": "BAGO-CHG-XXX",
  "type": "governance",
  "severity": "minor",
  "title": "<acción principal de la sesión>",
  "motivation": "<por qué se hizo, qué problema resuelve>",
  "status": "applied",
  "affected_components": ["<ruta/artefacto1>", "<ruta/artefacto2>"],
  "related_evidence": "BAGO-EVD-XXX",
  "created_at": "<ISO8601>",
  "updated_at": "<ISO8601>",
  "author": "<rol-principal>"
}
```

Ubicación: `.bago/state/changes/BAGO-CHG-XXX.json`

### Paso 4 — Crear BAGO-EVD-XXX.json

```json
{
  "evidence_id": "BAGO-EVD-XXX",
  "type": "closure",
  "related_to": ["BAGO-CHG-XXX", "<session_id>"],
  "summary": "<1 línea concreta>",
  "details": "<descripción real de lo entregado; NO dejar vacío>",
  "status": "recorded",
  "recorded_at": "<ISO8601>"
}
```

Ubicación: `.bago/state/evidences/BAGO-EVD-XXX.json`

### Paso 5 — Actualizar global_state.json

```bash
python3 -c "
import json
from pathlib import Path

p = '.bago/state/global_state.json'
d = json.loads(open(p).read())

# Actualizar con datos de la sesión cerrada
d['last_completed_session_id']  = '<SES-ID>'
d['last_completed_workflow']    = '<selected_workflow>'
d['last_completed_task_type']   = '<task_type>'
d['last_completed_roles']       = ['<rol1>', '<rol2>']
d['last_completed_change_id']   = 'BAGO-CHG-XXX'
d['last_completed_evidence_id'] = 'BAGO-EVD-XXX'
d['updated_at']                 = '<ISO8601>'

base = Path('.bago/state')
d['inventory'] = {
    'sessions':  len(list((base/'sessions').glob('*.json'))),
    'changes':   len(list((base/'changes').glob('*.json'))),
    'evidences': len(list((base/'evidences').glob('*.json')))
}

open(p,'w').write(json.dumps(d, indent=2, ensure_ascii=False))
print('global_state actualizado:', d['inventory'])
"
```

### Paso 6 — Regenerar TREE+CHECKSUMS y validar

```bash
cd ~/Desktop/BAGO_CAJAFISICA

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
# → debe terminar en "GO pack"
```

---

## Tiempo estimado de cierre

| Tipo de sesión | Tiempo |
|----------------|--------|
| `system_change` simple | ~5 min |
| `analysis` | ~5 min |
| `execution` | ~3 min |
| `sprint` multi-artefacto | ~10 min |

---

## Señales de alerta en el cierre

⚠️ `details` vacío en EVD → validate_state KO  
⚠️ `active_workflows != []` con `active_session_id: null` → KO  
⚠️ `last_completed_task_type` no coincide con `task_type` de la sesión → KO  
⚠️ Archivos creados sin regenerar TREE → KO checksum  

Ver diagnóstico completo en: `docs/operation/TROUBLESHOOTING.md`
