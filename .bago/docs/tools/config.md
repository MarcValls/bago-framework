# bago config — Gestión de configuración del pack

> Lee y actualiza las claves de configuración en pack.json.

## Descripción

`bago config` permite inspeccionar y modificar la configuración del pack BAGO sin editar pack.json manualmente. Valida los tipos y valores antes de escribir, y soporta restaurar valores por defecto. Las claves están divididas en `writable` (modificables) y `read-only` (solo lectura).

## Uso

```bash
bago config list               → todas las claves y sus valores actuales
bago config get <clave>        → valor de una clave específica
bago config set <clave> <val>  → actualiza una clave (con validación)
bago config reset <clave>      → restaura el valor por defecto
bago config --json             → output JSON de toda la configuración
bago config --test             → valida que pack.json existe y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `list` | Lista todas las claves configurables con sus valores |
| `get <clave>` | Muestra el valor actual de una clave |
| `set <clave> <val>` | Actualiza el valor (con validación de tipo) |
| `reset <clave>` | Restaura al valor por defecto |
| `--json` | Output JSON |
| `--test` | Modo test |

## Claves configurables

| Clave | Tipo | Valores válidos | Por defecto |
|-------|------|-----------------|-------------|
| `mode` | string | `balanced`, `strict`, `lite` | `balanced` |
| `language` | string | `es`, `en` | `es` |
| `review_freq` | string | `daily`, `weekly`, `monthly` | `weekly` |
| `team_size` | int | 1-100 | `1` |
| `notifications` | bool | `true`, `false` | `true` |
| `auto_snapshot` | bool | `true`, `false` | `false` |
| `lint_level` | string | `off`, `warn`, `error` | `warn` |

## Ejemplos

```bash
# Ver toda la configuración actual
bago config list

# Cambiar el idioma a inglés
bago config set language en

# Activar snapshots automáticos
bago config set auto_snapshot true

# Restaurar lint_level al valor por defecto
bago config reset lint_level

# Verificar modo actual
bago config get mode
```

## Casos de uso

- **Cuándo usarlo:** Para adaptar el comportamiento del pack a tu flujo de trabajo o equipo.
- **Qué produce:** Modificación de pack.json con validación previa; no hay efectos secundarios en state/.
- **Integración con otros comandos:** El `mode` afecta a `bago check` (strict activa más checks). El `lint_level` afecta a `bago lint`. El `auto_snapshot` activa snapshots en `bago cosecha`.
