# Manual de usuario · BAGO 2.5-stable

> Para quien instala BAGO por primera vez y quiere entender cómo usarlo en su día a día.

---

## 1. ¿Qué es BAGO?

**BAGO** (Balanceado · Adaptativo · Generativo · Organizativo) es una capa de operación que vive dentro de tu repositorio y trabaja junto a cualquier agente de IA (GitHub Copilot, Claude, GPT…).

Resuelve cuatro problemas concretos:

| Problema | Sin BAGO | Con BAGO |
|---|---|---|
| Pérdida de contexto entre sesiones | El agente no recuerda qué hiciste | Estado persistente en `.bago/state/` |
| Arranques improvisados | El agente empieza sin rol ni protocolo | Bootstrap estructurado antes de cada sesión |
| Cambios sin rastro | Las decisiones se pierden | Cada cambio genera un artefacto `BAGO-CHG` |
| Ideas sin gestión | Las mejoras se quedan en el aire | `bago ideas` con puntuación y registro |

BAGO **no es** un agente. Es el sistema operativo debajo de cualquier agente.

---

## 2. Instalación rápida

### Requisitos
- Python 3.9 o superior
- Sin dependencias externas (usa solo la librería estándar)

### Pasos

```bash
# 1. Clona el repositorio (o descarga el ZIP)
git clone https://github.com/MarcValls/bago-framework.git
cd bago-framework

# 2. Verifica que el sistema está bien
python3 bago validate

# Salida esperada:
# GO manifest
# GO state
# GO pack

# 3. Comprueba el estado inicial
python3 bago health

# Salida esperada en instalación limpia:
# BAGO Health: initializing ⚪
# No closed sessions yet...
```

> **Nota:** El estado `initializing` es **correcto** en una instalación nueva. El score de salud solo sube con el uso real del sistema.

### Primer arranque interactivo

Cuando ejecutas `python3 bago` **sin argumentos** por primera vez, BAGO detecta que está en modo `template_seed` y muestra un menú de configuración:

```
  ┌─────────────────────────────────────────────┐
  │  BAGO · Primera ejecución                   │
  ├─────────────────────────────────────────────┤
  │  [1] Evolucionar el framework BAGO          │
  │  [2] Iniciar un proyecto nuevo              │
  └─────────────────────────────────────────────┘
```

**Elige según tu objetivo:**

| Opción | Cuándo usarla |
|---|---|
| `[1] Evolucionar el framework` | Quieres contribuir o mejorar BAGO en sí mismo |
| `[2] Iniciar un proyecto nuevo` | Quieres usar BAGO **en tu propio proyecto** |

Si eliges `[2]`, BAGO muestra un menú de directorios sugeridos — **nunca asume que el directorio del framework es tu proyecto**:

```
  BAGO trabaja SOBRE tu proyecto, no dentro del framework.
  ¿Dónde está (o estará) tu proyecto?

  [1] /ruta/a/tu/proyecto          ← directorio actual del terminal
  [2] /ruta/al/directorio/padre
  [3] /ruta/dos/niveles/arriba
  [M] Otra ruta (escribirla)
```

BAGO copiará su pack al directorio elegido y lo dejará listo con `setup`.

> **Nota:** Los subcomandos `validate`, `health`, `audit`… funcionan directamente sin pasar por este menú.

### Instalar el alias `bago` (opcional pero recomendado)

```bash
make install
# o manualmente:
echo 'alias bago="python3 /ruta/a/bago-framework/bago"' >> ~/.zshrc
source ~/.zshrc
```

Con el alias instalado puedes escribir `bago health` en lugar de `python3 bago health`.

---

## 3. Los 15 comandos CLI explicados

### Comandos de diagnóstico

#### `bago health`
Muestra el estado de salud del sistema (0–100).

```bash
python3 bago health
```

- En instalación limpia: `initializing ⚪` (normal, sin historial todavía)
- Con sesiones reales: `🟢 80/100` o similar

---

#### `bago validate`
Verifica la integridad del sistema: manifiesto, estado y checksums. **Solo lectura — no modifica ningún archivo.**

```bash
python3 bago validate
```

Ejecuta este comando **antes y después** de cada sesión de trabajo. Si algo está mal, lo indica aquí.
Si los checksums están desactualizados, usa `bago sync` para regenerarlos.

---

#### `bago audit`
Auditoría completa: integridad, inventario, reportes, health score y workflow recomendado.

```bash
python3 bago audit
```

Ejemplo de salida:
```
[1] INTEGRIDAD    ✅  GO pack
[2] INVENTARIO    ✅  ses=0/chg=0/evd=0
[3] REPORTING     ✅  Sin artefactos stale
[4] HEALTH SCORE  ✅  🟢 80/100
[5] VÉRTICE       ✅  CLEAN
[6] WORKFLOW      →  W0_FREE_SESSION
```

---

#### `bago stability`
Resumen de estabilidad: validadores canónicos + sandbox (smoke, VM, soak, matrix).

```bash
python3 bago stability
```

En instalación sin entorno sandbox obtendrás `WARN` para smoke/vm/soak/matrix — **es normal**. Los validadores canónicos deben estar en verde.

---

#### `bago stale`
Detecta artefactos o tareas que llevan demasiado tiempo sin cerrarse.

```bash
python3 bago stale
```

---

### Comandos de trabajo

#### `bago ideas`
Lista las ideas priorizadas (0–100) para el siguiente paso de mejora del sistema.

```bash
python3 bago ideas

# Aceptar una idea para trabajarla (la convierte en tarea W2):
python3 bago ideas --accept 1

# Ver detalle de una idea concreta:
python3 bago ideas --detail 2
```

---

#### `bago task`
Muestra la tarea W2 activa (si existe).

```bash
python3 bago task
```

Las tareas se crean al aceptar una idea con `bago ideas --accept N`.

---

#### `bago session`
Abre una sesión de trabajo desde el handoff de la sesión anterior.

```bash
python3 bago session
```

---

#### `bago workflow`
Inspecciona los workflows disponibles o un workflow concreto.

```bash
# Ver todos los workflows
python3 bago workflow

# Inspeccionar uno concreto
python3 bago workflow W2
```

---

#### `bago cosecha`
Protocolo W9 de cierre de sesión: 3 preguntas rápidas que generan el artefacto de cierre.

```bash
python3 bago cosecha
```

Úsalo **al final de cada sesión** para que el contexto quede guardado y la siguiente sesión pueda retomarlo.

---

### Comandos de visión

#### `bago dashboard`
Vista general del sistema: estado del pack, inventario y detector W9.

```bash
python3 bago dashboard
```

---

#### `bago efficiency`
Métricas de eficiencia comparadas entre versiones del sistema.

```bash
python3 bago efficiency
```

---

#### `bago detector`
Detecta si el contexto del repositorio ha cambiado desde la última sesión.

```bash
python3 bago detector
```

---

#### `bago sync`
Regenera los artefactos derivados: `TREE.txt` y `CHECKSUMS.sha256`. Ejecutar después de añadir o eliminar archivos.

```bash
python3 bago sync
```

Commitea los cambios de `TREE.txt` y `CHECKSUMS.sha256` junto con el resto de la sesión.

---

#### `bago check`
Verificación estática de pureza: comprueba que ningún `validate_*.py` contiene operaciones de escritura.

```bash
python3 bago check
```

---

## 4. Los 10 workflows operativos

Los workflows son los "modos de trabajo" de BAGO. El sistema los recomienda automáticamente según el contexto, pero puedes elegir el tuyo.

| Workflow | Cuándo usarlo |
|---|---|
| **W0 · Sesión Libre** | Exploración sin estructura, modo off |
| **W1 · Cold Start** | Primera vez en un repositorio desconocido |
| **W2 · Implementación Controlada** | Tienes una tarea concreta y quieres hacerla bien |
| **W3 · Refactor Sensible** | Cambios estructurales de alto riesgo |
| **W4 · Debug Multicausa** | Un bug con varias causas posibles |
| **W5 · Cierre y Continuidad** | Cerrar la sesión con handoff completo |
| **W6 · Ideación Aplicada** | Generar y priorizar ideas de mejora |
| **W7 · Foco de Sesión** | Sesión con objetivo único y bien delimitado *(recomendado para uso diario)* |
| **W8 · Exploración** | Explorar el pack sin objetivo concreto previo |
| **W9 · Cosecha** | Formalizar valor generado en sesión libre |

### ¿Cuál usar en el día a día?

```
¿Tienes un objetivo concreto?
  → Sí → W7 (Foco de Sesión)
  → No, quiero explorar → W8 (Exploración)
  → Hay un bug → W4 (Debug Multicausa)
  → Quiero ideas → W6 (Ideación) → luego W2 para implementar
  → Fin de sesión → W9 (Cosecha) o W5 (Cierre y Continuidad)
```

---

## 5. Flujo de sesión típico

### Sesión estándar (30–90 min)

```bash
# 1. ANTES DE EMPEZAR — verifica el sistema
python3 bago validate
python3 bago stability

# 2. DECIDE QUÉ HACER
python3 bago ideas          # ver qué hay priorizado
python3 bago task           # o retomar tarea activa

# 3. TRABAJA
# Abre .bago/AGENT_START.md en tu agente de IA
# El agente cargará el estado y sabrá dónde estás

# 4. AL TERMINAR — registra el trabajo
python3 bago cosecha        # 3 preguntas rápidas (≤5 min)
python3 bago validate       # verifica que todo sigue bien
```

### Flujo de una idea nueva → implementación

```bash
# Ver ideas disponibles
python3 bago ideas

# Aceptar la idea #1
python3 bago ideas --accept 1

# Ver la tarea creada
python3 bago task

# Trabajar con tu agente de IA (señalar AGENT_START.md como contexto)

# Al terminar, cosechar
python3 bago cosecha
```

---

## 6. Integrar BAGO con tu agente de IA

### GitHub Copilot / Claude / GPT

El punto de entrada para el agente es `.bago/AGENT_START.md`. Añade esta instrucción al inicio de tu sesión:

```
Lee .bago/AGENT_START.md antes de hacer nada. Luego procede.
```

### Con GitHub Copilot CLI

Si tienes instalada la extensión BAGO para Copilot CLI:

```bash
# Instalar extensiones
python3 bago extensions
python3 bago setup
```

### Disparador automático `.bago/`

Para que el agente arranque BAGO automáticamente cuando escribes `.bago/`, crea un archivo `AGENTS.md` en la raíz del repo:

```markdown
# AGENTS

## BAGO Trigger

Si el usuario escribe `.bago/`, lee `.bago/AGENT_START.md` y sigue la ruta oficial de arranque.
No listar la carpeta `.bago/` salvo petición explícita.
```

---

## 7. Conceptos clave

### Estado (`state/`)
BAGO mantiene su estado en `.bago/state/`:
- `global_state.json` — estado global (versión, health, inventario)
- `ESTADO_BAGO_ACTUAL.md` — resumen en lenguaje natural del estado actual
- `pending_w2_task.json` — tarea W2 activa (si existe)

### Artefactos BAGO-CHG
Cada cambio significativo genera un artefacto en `.bago/state/changes/`:
```
BAGO-CHG-001-descripcion.json
```
Estos artefactos son la trazabilidad del sistema.

### Roles
BAGO tiene 13 roles especializados organizados en 4 categorías:

| Categoría | Roles |
|---|---|
| **Gobierno** | MAESTRO_BAGO, ORQUESTADOR_CENTRAL |
| **Supervisión** | VÉRTICE, AUDITOR_CANÓNICO |
| **Producción** | ANALISTA, ARQUITECTO, GENERADOR, ORGANIZADOR, VALIDADOR |
| **Especialistas** | REVISOR_UX, REVISOR_PERFORMANCE, REVISOR_SEGURIDAD, INTEGRADOR_REPO |

El agente activa solo los roles necesarios para cada sesión (máximo 3 activos a la vez).

### Pack (`pack.json`)
El manifiesto central del sistema. Define versión, rutas canónicas, contratos y workflows registrados. **No editar manualmente.**

---

## 8. Preguntas frecuentes

**¿Por qué `bago health` dice "initializing" pero `bago audit` muestra 80/100?**
Son dos modos distintos de la misma herramienta. `bago health` es contextual: si no hay sesiones cerradas, muestra "initializing" para indicar que aún no hay historial. `bago audit` usa `--score-only` y calcula el score técnico del pack independientemente del historial. Ambos son correctos.

**¿Qué son los 4 WARN de `bago stability`?**
Son avisos de que el sandbox (smoke, vm, soak, matrix) no está disponible. Esto es **normal** en instalación pública o sin entorno de pruebas. Los validadores canónicos (manifest + state) deben estar en verde — si lo están, puedes trabajar con normalidad.

**¿Debo ejecutar `bago validate` siempre?**
Sí, es una buena práctica. `bago validate` es **solo lectura** — verifica integridad sin modificar nada. Si detecta que los metadatos están desactualizados, ejecuta `bago sync` para regenerar `CHECKSUMS.sha256` y `TREE.txt`, y luego incluye esos cambios en el commit.

**¿Cómo se usa el comando `bago versions`?**
Requiere un directorio `cleanversion/` con snapshots históricos del sistema. No está incluido en el repositorio público. Se usa internamente para comparar versiones anteriores del framework.

**¿Puedo usar BAGO en cualquier repositorio?**
Sí. Copia la carpeta `.bago/` y el script `bago` a la raíz de tu repo. Ejecuta `python3 bago validate` para verificar que todo funciona. Para que el agente de IA lo detecte automáticamente, añade el `AGENTS.md` descrito en la sección 6.

---

## 9. Referencia rápida

```bash
# DIAGNÓSTICO
python3 bago health       → estado de salud (0–100)
python3 bago validate     → integridad del sistema
python3 bago audit        → auditoría completa
python3 bago stability    → resumen de estabilidad
python3 bago stale        → artefactos caducados

# TRABAJO
python3 bago ideas        → ideas priorizadas
python3 bago task         → tarea activa W2
python3 bago session      → abrir sesión desde handoff
python3 bago workflow     → inspeccionar workflows

# CIERRE
python3 bago cosecha      → cosechar sesión (W9)

# VISIÓN
python3 bago dashboard    → vista general
python3 bago efficiency   → métricas por versión
python3 bago detector     → detector de drift
```

---

*BAGO 2.5-stable · Manual de nuevo usuario · Abril 2026*
