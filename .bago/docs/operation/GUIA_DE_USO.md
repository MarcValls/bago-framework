# Guía de uso · BAGO 2.5-stable

## Ruta recomendada sobre repositorio real

1. Abrir `AGENT_START.md`.
2. Seguir la Ruta A.
3. Ejecutar `workflow_bootstrap_repo_first`.
4. Dejar que el Orquestador elija el workflow siguiente.
5. Validar antes de cerrar.
6. Registrar cambios solo si realmente mutaste el sistema.

## Ruta recomendada para evolución de BAGO

1. Ruta B de `AGENT_START.md`.
2. Cargar canon, orquestación y protocolo.
3. Si procede, activar `workflow_system_change`.

## Uso de ejemplos

- Prompt de arquitectura: `examples/prompts/ejemplo_prompt_arquitectura.md`
- Sesión de supervisión: `examples/sesiones/ejemplo_sesion_supervision.md`

## Regla de sobriedad

- usa la fábrica de prompts cuando reduce ambigüedad,
- no promptifiques tareas triviales,
- no conviertas bootstrap en rediseño si solo faltaba leer el repo.
