# CONTRATO · FRONTERA LLM EN BAGO

## Propósito

Definir el límite operativo entre `.bago/` y cualquier asistente LLM local o externo
(`llama`, `ollama`, `qwen`, etc.)
para que la mejora de UX no altere la lógica canónica del sistema.

## Principio rector

**El LLM puede explicar, resumir y acompañar.  
No puede gobernar, decidir ni mutar el comportamiento canónico de `.bago/`.**

## Fuente de verdad

La fuente de verdad sigue siendo exclusivamente:

- `pack.json`
- `.bago/state/`
- `.bago/tools/`
- workflows, prompts y validadores del pack

Ninguna salida generativa del LLM tiene autoridad por sí misma.

## Usos permitidos del LLM

- reformular resultados técnicos en lenguaje más humano;
- resumir contexto ya cargado por herramientas canónicas;
- sugerir siguientes pasos;
- mejorar la interfaz conversacional;
- etiquetar intención o tono en una capa de UX opcional;
- redactar explicaciones sobre errores, workflows o estado.

## Usos prohibidos del LLM

- decidir qué repo/directorio es el objetivo real;
- sustituir `repo_context_guard.py`, `repo_on.py` o selectores canónicos;
- activar workflows por su cuenta;
- ejecutar comandos sin pasar por tooling canónico;
- escribir o corregir `state/` por inferencia;
- redefinir reglas de validación;
- inferir “verdad operativa” cuando el estado real no la confirma.

## Componentes que NO pueden depender del LLM

Los siguientes caminos deben seguir siendo deterministas y válidos aunque no exista LLM:

- `.bago/tools/repo_context_guard.py`
- `.bago/tools/repo_on.py`
- `.bago/tools/repo_runner.py`
- `.bago/tools/bago_debug.py`
- `.bago/tools/session_preflight.py`
- `bago`

## Regla de fallo seguro

Si el LLM no responde, responde mal o no está instalado:

- `.bago/` debe seguir funcionando;
- no debe degradarse el comportamiento canónico;
- solo se pierde la capa de ayuda/explicación;
- la UX debe poder caer a texto fijo o respuestas no generativas.

## Regla de integración

Si se usa un LLM en BAGO, debe ir en una capa explícitamente opcional de UX.

Condiciones:

- apagado por defecto o claramente desacoplado;
- sin dependencia para bootstrap, validación o selección de target;
- toda acción real pasa por herramientas BAGO validadas;
- el usuario debe poder distinguir entre:
  - explicación del LLM,
  - estado real de BAGO,
  - acción ejecutada por tooling canónico.

## Patrón correcto

1. BAGO obtiene contexto real.
2. El LLM lo explica o lo resume.
3. BAGO ejecuta acciones reales si corresponde.

## Patrón incorrecto

1. El LLM interpreta el contexto por su cuenta.
2. El LLM decide qué hacer.
3. BAGO obedece esa salida como si fuera canónica.

## Fórmula operativa

**LLM = capa de presentación opcional.  
BAGO = plano de control determinista.**
