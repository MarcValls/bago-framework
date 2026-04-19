# Plantilla de sesión — `system_change`

> Copia este archivo, rellena los campos marcados con `TODO` y úsalo para arrancar la sesión.  
> Al cerrar, copia los valores al JSON de sesión correspondiente.

---

## Preflight checklist

```bash
python3 .bago/tools/session_preflight.py \
  --objetivo "TODO: verbo + objeto + para que [done]" \
  --roles "role_architect,role_validator" \
  --artefactos "TODO: lista,de,artefactos,separados,por,comas" \
  --task-type system_change
```

---

## Datos de sesión

| Campo | Valor |
|-------|-------|
| **session_id** | `SES-W7-YYYY-MM-DD-00N` |
| **task_type** | `system_change` |
| **selected_workflow** | `w7_foco_sesion` |
| **roles** | `role_architect` + `role_validator` (o `role_executor`) |
| **objetivo** | TODO |

---

## Artefactos planificados (mínimo 3 útiles)

```
tools/<herramienta>.py
docs/operation/<GUIA>.md
workflows/<W_afectado>.md
```

Añade más si el scope lo justifica. Más artefactos = sesión más productiva.

---

## Decisiones que deben quedar documentadas

- Por qué se eligió este enfoque vs. alternativas
- Qué cambió en la arquitectura/gobernanza
- Qué impacto tiene en sesiones futuras

---

## Artefactos de cierre (protocolo — no cuentan en útiles)

```
state/changes/BAGO-CHG-XXX.json    # type: governance|architecture|migration
state/evidences/BAGO-EVD-XXX.json  # type: closure
state/sessions/SES-W7-*.json        # actualizar status: closed
```

---

## Medición post-sesión

```bash
python3 .bago/tools/artifact_counter.py -n 1 -v
```

¿Resultado útil ≥ 4? Si no, ¿qué documentación o herramienta adicional podría haberse creado?

---

## Checklist de cierre

- [ ] Todos los artefactos planificados existen en disco
- [ ] CHG + EVD creados
- [ ] `global_state.json` inventario actualizado
- [ ] TREE + CHECKSUMS regenerados
- [ ] `validate_pack.py` → GO
