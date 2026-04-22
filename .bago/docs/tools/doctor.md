# bago doctor — Diagnóstico integral del pack

> Ejecuta un diagnóstico completo y detecta problemas en el pack BAGO.

## Descripción

`bago doctor` combina múltiples validaciones en un único diagnóstico integral. Verifica la integridad del pack, detecta problemas de configuración, identifica archivos corruptos o faltantes, y sugiere correcciones. Es el punto de partida cuando algo no funciona correctamente.

## Uso

```bash
bago doctor                    → diagnóstico completo
bago doctor --json             → output JSON con resultado de cada check
bago doctor --test             → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--json` | Output JSON con campo `checks` y `summary` |
| `--test` | Modo test |

## Checks realizados

1. Estructura de directorios (tools/, state/, docs/, workflows/)
2. Integridad del manifest (TREE.txt, CHECKSUMS.sha256)
3. Validación de pack.json
4. global_state.json legible y coherente
5. Sesiones con formato correcto
6. Cambios con formato correcto
7. Health score calculable
8. Herramientas Python sin errores de importación

## Ejemplos

```bash
# Diagnóstico completo
bago doctor

# Diagnóstico en JSON para procesado
bago doctor --json | jq '.checks[] | select(.status == "FAIL")'
```

## Casos de uso

- **Cuándo usarlo:** Cuando `bago health` da un score inesperadamente bajo, cuando un comando falla, o después de migrar o actualizar el pack.
- **Qué produce:** Listado de checks con ✅/❌/⚠️ y descripción del problema si lo hay.
- **Integración con otros comandos:** Después de `bago doctor` usar `bago patch` para correcciones automáticas, `bago validate` para verificación formal, y `bago lint` para problemas de calidad.
