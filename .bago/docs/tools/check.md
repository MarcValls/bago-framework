# bago check — Checklist pre-sesión personalizable

> Ejecuta una lista de verificaciones antes de abrir una sesión de trabajo.

## Descripción

`bago check` evalúa una serie de condiciones del pack antes de comenzar a trabajar. Ayuda a detectar problemas (health bajo, validación fallida, sprint sin abrir) antes de que afecten al trabajo. El checklist es personalizable mediante `.bago/config/checklist.json`.

## Uso

```bash
bago check                     → checklist completo (todos los checks)
bago check --quick             → solo los checks críticos
bago check --json              → output JSON con resultado por check
bago check init                → crea checklist.json personalizable en .bago/config/
bago check --test              → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--quick` | Solo ejecuta los checks marcados como críticos |
| `--json` | Output JSON con status por check |
| `init` | Crea el archivo de configuración del checklist |
| `--test` | Modo test |

## Checks por defecto

| Check | Crítico | Condición |
|-------|---------|-----------|
| Health mínimo | ✅ Sí | `bago health` score ≥ 80 |
| Sin errores de validación | ✅ Sí | `bago validate` → GO sin errores |
| Sprint activo | No | Existe SPRINT-*.json en estado `open` |
| Sin legacy status | No | No hay sesiones con status `completed` (usar `closed`) |
| Snapshot reciente | No | Existe SNAP-*.zip de los últimos 7 días |

## Ejemplos

```bash
# Verificación completa antes de empezar a trabajar
bago check

# Solo los críticos (rápido)
bago check --quick

# Crear checklist personalizado
bago check init
# Luego editar .bago/config/checklist.json

# Usar en scripts
bago check --json | jq '.summary.failed'
```

## Casos de uso

- **Cuándo usarlo:** Justo antes de `bago session` para asegurarse de que el pack está en buen estado.
- **Qué produce:** Lista de checks con ✅/❌ y resumen de pasados/fallados. Con `--json`, objeto con campo `summary` y array `checks`.
- **Integración con otros comandos:** Complementa `bago health` y `bago doctor`. Si falla, usar `bago patch` para correcciones automáticas o `bago validate` para diagnóstico.
