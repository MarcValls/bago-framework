# bago watch — Monitor en tiempo real

> Monitoriza en tiempo real el estado del pack BAGO, actualizando automáticamente.

## Descripción

`bago watch` ejecuta un bucle de monitorización que actualiza el estado del pack en pantalla cada N segundos. Muestra health score, sesión activa, cambios recientes y alertas. Útil para tener visibilidad continua del estado mientras se trabaja en otra ventana.

## Uso

```bash
bago watch                     → monitor con actualización cada 5 segundos
bago watch --interval N        → actualiza cada N segundos
bago watch --compact           → vista compacta (una línea)
bago watch --test              → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--interval N` | Intervalo de actualización en segundos (default: 5) |
| `--compact` | Vista compacta de una línea |
| `--test` | Modo test |

## Salida

Refresca la pantalla mostrando:
- Health score actual con semáforo
- Sesión activa (si la hay)
- Último cambio registrado
- Alertas activas (stale, health bajo)
- Hora de la última actualización

## Ejemplos

```bash
# Monitor estándar
bago watch

# Actualización cada 30 segundos (menos intrusivo)
bago watch --interval 30

# Vista compacta para terminal pequeña
bago watch --compact
```

## Casos de uso

- **Cuándo usarlo:** Abre `bago watch` en una ventana de terminal separada mientras trabajas para tener visibilidad continua del estado del pack.
- **Qué produce:** Output de terminal que se refresca automáticamente. Sale con Ctrl+C.
- **Integración con otros comandos:** Es la contraparte en tiempo real de `bago status`. Para el servidor web usar `bago chat`.
