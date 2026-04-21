# bago lint — Linter de calidad del pack

> Ejecuta validaciones de calidad sobre el pack y reporta errores y avisos.

## Descripción

`bago lint` verifica la calidad y coherencia del pack BAGO más allá de la validación estructural. Detecta problemas semánticos como campos inconsistentes, valores obsoletos, referencias rotas y patrones de datos que sugieren problemas. Reporta errores (deben corregirse) y avisos (recomendable corregir).

## Uso

```bash
bago lint                      → lint completo
bago lint --json               → output JSON con errores y avisos
bago lint --errors-only        → solo muestra errores (sin avisos)
bago lint --test               → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--json` | Output JSON con arrays `errors` y `warnings` |
| `--errors-only` | Muestra solo errores, omite avisos |
| `--test` | Modo test |

## Estado esperado

```
0 errores, N avisos
```

Los 11 avisos del estado base son conocidos y aceptados. Los errores deben ser 0 antes de hacer commit.

## Ejemplos

```bash
# Lint completo
bago lint

# Solo errores para CI
bago lint --errors-only

# Ver todos los problemas en JSON
bago lint --json | jq '.errors[]'
```

## Casos de uso

- **Cuándo usarlo:** En el flujo de CI local (`bago validate && bago health && bago test`) antes de commits importantes, o cuando `bago check` detecta problemas de calidad.
- **Qué produce:** Lista de errores y avisos con archivo afectado, campo problemático y descripción.
- **Integración con otros comandos:** `bago patch` puede corregir automáticamente algunos de los errores que `bago lint` detecta. `bago doctor` incluye una versión simplificada de los checks de lint.
