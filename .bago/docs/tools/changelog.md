# bago changelog — CHANGELOG desde registros CHG

> Genera un CHANGELOG en formato Keep a Changelog desde los archivos BAGO-CHG-*.json.

## Descripción

`bago changelog` lee todos los archivos BAGO-CHG-*.json de state/changes/ y los formatea en un CHANGELOG estándar siguiendo la especificación [Keep a Changelog](https://keepachangelog.com/en/1.0.0/). Agrupa los cambios por fecha y tipo, y puede actualizar el archivo `.bago/docs/CHANGELOG.md` automáticamente.

## Uso

```bash
bago changelog                 → muestra CHANGELOG en terminal
bago changelog --update        → actualiza docs/CHANGELOG.md
bago changelog --period N      → solo últimos N días
bago changelog --json          → output JSON agrupado por fecha
bago changelog --test          → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--update` | Escribe el resultado en `.bago/docs/CHANGELOG.md` |
| `--period N` | Limita a los últimos N días de cambios |
| `--json` | Output JSON con cambios agrupados |
| `--test` | Modo test |

## Ejemplos

```bash
# Ver CHANGELOG generado en terminal
bago changelog

# Actualizar el archivo CHANGELOG.md
bago changelog --update

# Solo cambios del último mes
bago changelog --period 30
```

## Casos de uso

- **Cuándo usarlo:** Al cerrar un sprint o versión, para generar el CHANGELOG actualizado, o para revisar qué ha cambiado en un período.
- **Qué produce:** Texto Markdown formateado con Keep a Changelog o actualización del archivo docs/CHANGELOG.md.
- **Integración con otros comandos:** Lee los CHGs creados por `bago cosecha`. Complementa `bago report` (más detallado) y `bago summary` (más ejecutivo).
