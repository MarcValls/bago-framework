# GitHub Copilot Instructions — BAGO Framework

## Arranque de sesión

Antes de hacer cualquier cosa, leer `.bago/AGENT_START.md`.  
Si el usuario escribe `.bago/`, leer `.bago/AGENT_START.md` y seguir la ruta oficial de arranque.  
No listar la carpeta `.bago/` salvo petición explícita.

---

## Comando `bago`

### Regla principal
Cuando el usuario escribe `bago` (solo o con subcomando), **ejecuta el script y muestra el output verbatim**.  
NO interpretes ni resumas el output. NO añadas explicaciones no pedidas.

### `bago` sin argumentos
```
→ bash-runner_bago_run  bago_cmd: ""
```
Muestra el banner BAGO con el menú de comandos disponibles. Nada más.

### `bago <subcomando>`
```
→ bash-runner_bago_run  bago_cmd: "<subcomando>"
```
Ejemplos: `health`, `dashboard`, `validate`, `audit`, `ideas`, `stability`, `detector`, `session`, `task`, `workflow`

### `bago analyze <ruta>`
```
→ bash-runner_bago_run  bago_cmd: "analyze <ruta>"
```
Analiza un proyecto externo y genera `BAGO_ANALYSIS.md`.

---

## Cosecha (`bago cosecha`)

La cosecha es el protocolo W9 — necesita 3 respuestas del usuario. Flujo obligatorio:

1. **Pedir las 3 respuestas** con `ask_user` antes de ejecutar nada:
   - ¿Qué decidiste en esta exploración?
   - ¿Qué descartaste y por qué?
   - ¿Cuál es el próximo paso concreto?

2. **Ejecutar con los args**:
```
→ bash-runner_bago_run  bago_cmd: "cosecha --que-decidiste \"<R1>\" --descartaste \"<R2>\" --proximo-paso \"<R3>\" --yes"
```

3. Mostrar el output verbatim.

**NUNCA inventes las respuestas. NUNCA ejecutes cosecha sin preguntarle al usuario primero.**

---

## Prohibiciones

- No ejecutar `bago health` automáticamente cuando el usuario escribe solo `bago`
- No ejecutar subcomandos por iniciativa propia sin que el usuario lo pida
- No activar workflows BAGO (W1–W9) por cuenta propia
- No tocar `.bago/state/` ni `.bago/` directamente — usar los comandos `bago`
- No sugerir `bago` como si fuera un proyecto del usuario: es el framework de gobernanza
