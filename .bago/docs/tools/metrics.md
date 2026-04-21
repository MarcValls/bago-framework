# bago metrics — Tendencias y métricas rolling

> Calcula tendencias rolling de métricas clave con sparklines ASCII.

## Descripción

`bago metrics` analiza la evolución temporal de las métricas del pack usando ventanas rolling configurable. Muestra sparklines ASCII para visualizar tendencias sin necesidad de herramientas externas. Complementa `bago velocity` con un enfoque más amplio sobre múltiples dimensiones.

## Uso

```bash
bago metrics                   → métricas rolling estándar (últimas 4 semanas)
bago metrics --window N        → ventana rolling de N días
bago metrics --json            → output JSON con series temporales
bago metrics --test            → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--window N` | Tamaño de la ventana rolling en días (default: 7) |
| `--json` | Output JSON con series temporales de cada métrica |
| `--test` | Modo test |

## Métricas incluidas

- Sesiones por semana (sparkline)
- Artefactos por semana (sparkline)
- Decisiones por semana (sparkline)
- Health score histórico
- Workflows más usados por período

## Ejemplos

```bash
# Métricas estándar con ventana de 7 días
bago metrics

# Ventana de 14 días para suavizar fluctuaciones
bago metrics --window 14
```

## Casos de uso

- **Cuándo usarlo:** Para identificar tendencias a largo plazo, detectar degradación o mejora continua, o preparar informe de sprint.
- **Qué produce:** Tabla de métricas con sparklines ASCII y valores de tendencia (▲/▼/→).
- **Integración con otros comandos:** Complementa `bago velocity` (ritmo puntual) y `bago stats` (snapshot agregado). Para detalle de sesiones específicas usar `bago session-stats`.
