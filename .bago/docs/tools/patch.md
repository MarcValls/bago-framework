# bago patch — Corrección automática de inconsistencias

> Detecta y corrige inconsistencias conocidas en el state/ del pack BAGO.

## Descripción

`bago patch` aplica correcciones automáticas a problemas conocidos en los datos de state/. Opera en modo dry-run por defecto (muestra qué cambiaría sin modificar nada) y requiere `--apply` para ejecutar los cambios. Hay tres parches predefinidos que abordan los problemas más comunes detectados por `bago lint`.

## Uso

```bash
bago patch --list              → lista parches disponibles y archivos afectados
bago patch <nombre>            → dry-run: muestra qué cambiaría
bago patch <nombre> --apply    → aplica el parche realmente
bago patch --all --apply       → aplica todos los parches disponibles
bago patch --test              → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--list` | Lista parches y número de archivos afectados |
| `<nombre>` | Nombre del parche a aplicar (dry-run por defecto) |
| `--apply` | Aplica el parche (sin esta flag, solo dry-run) |
| `--all` | Aplica todos los parches disponibles |
| `--test` | Modo test |

## Parches disponibles

| Nombre | Descripción | Afecta a |
|--------|-------------|----------|
| `legacy-status` | Cambia `status: completed` → `status: closed` en SES-*.json | state/sessions/ |
| `missing-tests` | Añade campo `tests` faltante en SES-*.json | state/sessions/ |
| `missing-goal` | Añade campo `goal` faltante en SES-*.json | state/sessions/ |

## Ejemplos

```bash
# Ver qué parches hay y cuántos archivos afectan
bago patch --list

# Ver qué cambiaría el parche legacy-status (sin modificar)
bago patch legacy-status

# Aplicar corrección de status legado
bago patch legacy-status --apply

# Aplicar todos los parches de una vez
bago patch --all --apply
```

## Casos de uso

- **Cuándo usarlo:** Después de `bago lint` detecta errores relacionados con campos faltantes o valores obsoletos, o después de migrar de una versión anterior del pack.
- **Qué produce:** Modifica archivos SES-*.json directamente en state/sessions/. En dry-run muestra el diff de lo que cambiaría.
- **Integración con otros comandos:** Ejecutar `bago validate` después de aplicar parches para confirmar que el estado es correcto. `bago check` detecta problemas que `bago patch` puede resolver.
