# bago export — Exportación HTML y CSV

> Exporta datos del pack en formato HTML dark-theme o CSV con gráfico SVG.

## Descripción

`bago export` genera archivos de exportación para compartir o visualizar fuera del terminal. Produce páginas HTML con tema oscuro que incluyen métricas y gráficos SVG, o archivos CSV para análisis en hojas de cálculo. Ideal para presentaciones o para compartir el estado del proyecto con personas que no tienen acceso al pack.

## Uso

```bash
bago export                    → HTML dark-theme con todas las métricas
bago export --format csv       → CSV con datos de sesiones y cambios
bago export --out FILE         → guarda en el archivo indicado
bago export --period N         → limita a los últimos N días
bago export --test             → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--format csv` | Exporta en CSV en lugar de HTML |
| `--out FILE` | Archivo de destino (default: bago_export.html / .csv) |
| `--period N` | Limita la exportación a los últimos N días |
| `--test` | Modo test |

## Ejemplos

```bash
# Exportar HTML completo
bago export

# Exportar CSV del último mes
bago export --format csv --period 30 --out datos-abril.csv

# HTML guardado en ruta específica
bago export --out REPORTS/estado-bago.html
```

## Casos de uso

- **Cuándo usarlo:** Para compartir el estado del proyecto con stakeholders que no usan BAGO, para archivar una versión visual del estado, o para análisis en Excel/Sheets.
- **Qué produce:** Archivo HTML autocontenido con estilos dark-theme y gráficos SVG, o CSV tabular.
- **Integración con otros comandos:** Combina datos de `bago stats`, `bago metrics` y `bago velocity`. Para documentación interna usar `bago review` o `bago report`.
