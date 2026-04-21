# AGENT_START

## Propósito

Punto de entrada único para cualquier agente o sesión que opere bajo BAGO.

## Regla de arranque

No ejecutar trabajo técnico relevante sin bootstrap mínimo.

## Secuencia obligatoria

1. Leer `pack.json`.
2. Leer `README.md`.
3. Leer `core/00_CEREBRO_BAGO.md`.
4. Leer `core/05_GOBERNANZA_DE_SESION.md`.
5. Leer `core/06_MATRIZ_DE_ACTIVACION.md`.
6. Leer `state/global_state.json`.
7. Ejecutar guard de contexto de repo (`tools/repo_context_guard.py check`).
8. Si el guard da `new` o `mismatch`, forzar `workflow_bootstrap_repo_first`/`W1_COLD_START` antes de cualquier otro workflow y tratar `ESTADO_BAGO_ACTUAL` previo como histórico.
9. Leer `state/ESTADO_BAGO_ACTUAL.md`.
10. Si existe `state/context_map.json`, leerlo para obtener el mapa de contextos distribuidos. Si tiene más de 30 minutos de antigüedad (campo `generated_at`), regenerarlo con `tools/context_map.py --save --depth 4`.
11. Contrastar el estado con el repositorio real.
12. Identificar modo BAGO predominante.
13. Activar solo los roles necesarios.
14. Ejecutar el bloque mínimo útil.
15. Actualizar estado tras el bloque.

## Ruta maestra de trabajo

- `workflows/WORKFLOW_MAESTRO_BAGO.md`: secuencia canónica `canon -> integracion -> entorno -> validacion_escalonada -> baseline -> regresion -> operacion_continua`.

## Repo de trabajo — regla de auto-selección

**Si `state/repo_context.json` contiene `role: "external_repo_pointer"` y `working_mode: "external"`:**
- El repo declarado en `repo_root` ES el proyecto de trabajo. No preguntar ni ofrecer alternativas.
- Leer `repo_root` y operar sobre ese directorio directamente.
- Ejecutar `tools/repo_context_guard.py check`: si devuelve `match`, continuar. Si `mismatch`, avisar al usuario pero NO bloquear.
- El siguiente paso es analizar el estado del proyecto (no del pack BAGO) y ofrecer la acción más coherente.

**Solo preguntar "¿framework o proyecto externo?"** si `working_mode` es `"self"` o si `repo_context.json` no existe.

## Resolución de directorio objetivo

Antes de editar, instalar, ejecutar o auditar:

1. Buscar primero en el contexto donde el usuario parece querer actuar:
   cwd real, `repo_context.json`, contexto reciente, handoff activo, comando o ruta citados por el usuario.
2. Si hay un único objetivo claro y coherente, operar ahí.
3. Si hay ambigüedad, no asumir por defecto el primer manifiesto encontrado.
4. Si falta contexto, ofrecer varios candidatos y dejar que el usuario elija.
5. El selector debe:
   - permitir moverse con flechas,
   - mostrar rutas completas y motivo del candidato,
   - incluir una opción final `Ruta exacta…`,
   - pedir la ruta manual si se elige esa opción.
6. Tratar `TESTS/`, `RELEASE/`, `audit/`, `cleanversion/`, snapshots, backups y zips extraídos como candidatos de baja prioridad salvo instrucción explícita del usuario.
7. Si sigue sin haber target claro, bloquear la acción y pedir precisión. Es preferible una pregunta corta a editar el repo equivocado.

## Oferta de arranque

Tras el bootstrap mínimo:

- Si hay repo externo declarado → analizar su estado y proponer el siguiente paso concreto.
- Si no hay repo externo → ofrecer dos caminos:
  1. Ejecutar una función útil del pack, como `./ideas`.
  2. Inspeccionar un workflow concreto para configuración humana, como `./workflow-info W1`.

## Regla para workflows concretos

Si el workflow elegido requiere contexto que aún no existe, primero sugerir las tareas previas necesarias y verificar que cumplen su finalidad antes de seguir.

## ESCENARIO-001 activo — Reglas W7 obligatorias

Mientras `global_state.json → active_scenarios` incluya `ESCENARIO-001`, **toda sesión productiva debe pasar el preflight antes de arrancar**:

```bash
python3 tools/session_preflight.py \
  --objetivo "Verbo + objeto + para que [done]" \
  --roles "role_principal,role_apoyo" \
  --artefactos "ruta/artefacto1.md,ruta/artefacto2.json,ruta/artefacto3.py" \
  --handoff-chain "role_analyst>role_architect>role_generator>role_validator>role_vertice" \
  --task-type system_change
```

- Resultado `GO` → abrir sesión.
- Resultado `KO` → corregir según indicaciones y repetir.
- En sesiones productivas normales usar **W7_FOCO_SESION** en lugar de W1.

### Protocolo de continuidad impoluta (obligatorio)

- Definir cadena de handoff explícita entre roles en el arranque (`--handoff-chain`).
- No cerrar tareas con `bago task --done` sin declarar al menos un `--test-cmd`; todos los tests declarados deben terminar en exit code 0.
- No cerrar tareas sin `--human-check` con mínimo 20 caracteres que describa el impacto real en experiencia humana.
- Si falla cualquier test o no hay validación humana explícita: la tarea sigue abierta.

Ver reglas completas en `state/scenarios/ESCENARIO-MEJORA-ARTEFACTOS-FOCO.md`.

## Prohibiciones

- No improvisar el arranque.
- No activar todos los roles por defecto.
- No mezclar bootstrap con ejecución principal.
- No tocar decisiones congeladas sin justificación explícita.
- **No invocar `codex` CLI ni ningún agente externo de IA** durante el arranque ni como paso automático de ningún workflow BAGO. `codex` es una herramienta opt-in; requiere invocación explícita del usuario.
- No delegar a un LLM la selección de target, la activación de workflows ni la mutación de `state/`. Ver `docs/operation/CONTRATO_FRONTERA_LLM.md`.
