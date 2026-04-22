# bago timeline — Timeline ASCII semanal

> Muestra una línea de tiempo ASCII de sesiones y cambios organizados por semana.

## Descripción

`bago timeline` genera una visualización temporal de las sesiones de trabajo registradas. Organiza la actividad por semanas y muestra el workflow utilizado en cada sesión. Ayuda a ver de un vistazo cuándo se trabajó y con qué intensidad.

## Uso

```bash
bago timeline                  → últimas 4 semanas
bago timeline --weeks N        → últimas N semanas
bago timeline --json           → output JSON con actividad por semana
bago timeline --test           → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--weeks N` | Número de semanas a mostrar (default: 4) |
| `--json` | Output JSON |
| `--test` | Modo test |

## Ejemplos

```bash
# Timeline de las últimas 4 semanas
bago timeline

# Timeline del último mes y medio
bago timeline --weeks 6
```

## Casos de uso

- **Cuándo usarlo:** Para visualizar la distribución temporal del trabajo, detectar semanas sin actividad, o preparar un informe de progreso.
- **Qué produce:** Diagrama ASCII con una columna por día y filas por semana, marcando días con actividad.
- **Integración con otros comandos:** Complementa `bago velocity` (ritmo) y `bago review` (informe). Para buscar en el contenido de sesiones usar `bago search`.
