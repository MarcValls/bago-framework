# bago git — Contexto git integrado

> Obtiene contexto del repositorio git activo e inyecta información en el estado BAGO.

## Descripción

`bago git` extrae información del repositorio git donde está trabajando: branch activa, últimos commits, autores recientes y archivos modificados. Puede inyectar este contexto en la sesión BAGO activa para que el historial quede vinculado con los cambios en el repositorio.

## Uso

```bash
bago git                       → resumen del contexto git actual
bago git --log N               → últimos N commits
bago git --branch              → solo info de la branch activa
bago git --authors             → autores recientes y actividad
bago git --inject              → inyecta contexto en la sesión BAGO activa
bago git --json                → output JSON
bago git --test                → valida dependencias y sale con "OK"
```

## Opciones

| Opción | Descripción |
|--------|-------------|
| `--log N` | Muestra los últimos N commits (default: 10) |
| `--branch` | Solo información de la branch activa |
| `--authors` | Lista de autores con número de commits recientes |
| `--inject` | Inyecta el contexto en la sesión BAGO activa |
| `--json` | Output JSON |
| `--test` | Modo test |

## Ejemplos

```bash
# Ver contexto git completo
bago git

# Últimos 5 commits
bago git --log 5

# Vincular commits recientes a la sesión activa
bago git --inject
```

## Casos de uso

- **Cuándo usarlo:** Al iniciar una sesión para cargar contexto del repositorio, o al cerrar para vincular los commits con la sesión BAGO.
- **Qué produce:** Resumen del estado git (branch, commits, autores). Con `--inject`, actualiza la sesión activa en state/ con los datos git.
- **Integración con otros comandos:** Usar antes de `bago session` para contexto completo. Los datos inyectados aparecen en `bago session-stats` y `bago review`.
