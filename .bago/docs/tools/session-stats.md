# bago session-stats — Top sesiones por producción

> Muestra las sesiones más productivas con breakdown detallado por ID.

## Descripción

`bago session-stats` (alias: `bago ss`) analiza todas las sesiones registradas y las ordena por score de producción. Permite identificar qué sesiones generaron más valor (artefactos, decisiones) y qué workflows son más efectivos. También muestra el breakdown detallado de una sesión específica.

## Uso

```bash
bago session-stats             → top 10 sesiones por score
bago ss                        → alias abreviado
bago session-stats --top N     → top N sesiones
bago session-stats --id SES-ID → detalle de sesión específica
bago session-stats --json      → output JSON
bago session-stats --test      → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--top N` | Número de sesiones a mostrar (default: 10) |
| `--id SES-ID` | Muestra detalle completo de una sesión |
| `--json` | Output JSON |
| `--test` | Modo test |

## Ejemplos

```bash
# Top 10 sesiones más productivas
bago session-stats

# Top 5 (abreviado)
bago ss --top 5

# Detalle de una sesión específica
bago session-stats --id SES-SPRINT-2026-04-22-001
```

## Casos de uso

- **Cuándo usarlo:** Para entender qué tipos de sesión son más productivos, identificar patrones de trabajo efectivo, o en retrospectivas de sprint.
- **Qué produce:** Tabla de sesiones ordenadas por score con workflow, artefactos, decisiones y score calculado.
- **Integración con otros comandos:** Usa el mismo conjunto de datos que `bago metrics` y `bago velocity`, pero con enfoque por sesión individual. Complementa `bago habit` para análisis de patrones.
