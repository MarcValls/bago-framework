# bago habit — Detector de hábitos de trabajo

> Analiza patrones en las sesiones para identificar hábitos positivos y áreas de mejora.

## Descripción

`bago habit` procesa el historial de sesiones registradas en state/sessions/ y detecta patrones recurrentes de comportamiento. Clasifica los hallazgos en tres tipos: hábitos positivos (hacer más), áreas de mejora (hacer menos o diferente), y patrones de actividad (observaciones neutras). Cada hábito detectado recibe un score de 0 a 100.

## Uso

```bash
bago habit                     → análisis completo (todos los tipos)
bago habit --positive          → solo hábitos positivos detectados
bago habit --improve           → solo áreas de mejora
bago habit --pattern           → solo patrones de actividad temporal
bago habit --json              → output JSON con scores y detalle
bago habit --test              → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--positive` | Muestra solo los hábitos positivos |
| `--improve` | Muestra solo las áreas de mejora |
| `--pattern` | Muestra solo los patrones de actividad (días/horas) |
| `--json` | Output JSON con campo `habits` array |
| `--test` | Modo test |

## Tipos de hábitos

| Tipo | Descripción | Ejemplo |
|------|-------------|---------|
| `POSITIVE` | Comportamiento beneficioso con frecuencia alta | Decisiones registradas en >80% de sesiones |
| `IMPROVE` | Comportamiento que reduce calidad o velocidad | Sesiones sin artefactos en >40% de los casos |
| `PATTERN` | Observación de actividad sin juicio de valor | Pico de actividad los martes |

## Ejemplos

```bash
# Análisis completo
bago habit

# Solo áreas de mejora para sprint retrospectiva
bago habit --improve

# Patrones de actividad temporal
bago habit --pattern

# Exportar para análisis externo
bago habit --json | jq '.habits[] | select(.type == "POSITIVE")'
```

## Casos de uso

- **Cuándo usarlo:** En retrospectivas de sprint, revisiones periódicas, o cuando la velocidad ha bajado inesperadamente.
- **Qué produce:** Lista de hábitos con tipo, descripción, score y frecuencia observada.
- **Integración con otros comandos:** `bago review` incluye el resumen de hábitos. Combinar con `bago velocity` para correlacionar hábitos con velocidad.
