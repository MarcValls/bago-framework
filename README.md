# BAGO Framework

> Sistema operativo de trabajo técnico para programación con IA
>
> **v2.5** · 30 herramientas · 12 workflows · Gobernanza de sesión integrada

---

## 🎯 ¿Qué hace BAGO?

BAGO amplifica el trabajo con IA resolviendo:

- ❌ Pérdida de contexto entre iteraciones → ✅ Estado persistente
- ❌ Arranques improvisados → ✅ Workflows definidos
- ❌ Cambios sin trazabilidad → ✅ Protocolo de evidencias
- ❌ Deriva entre código y documentación → ✅ Sincronización automática

**BAGO = B**alanceado · **A**daptativo · **G**enerativo · **O**rganizativo

---

## ⚡ Inicio rápido (3 pasos)

```bash
# 1. Configura el entorno
./bago setup

# 2. Explora ideas priorizadas
./bago ideas

# 3. Abre una sesión de trabajo
./bago session
```

**¿Primera vez?** Ejecuta `./bago start` para menú interactivo.

---

## 📚 Comandos principales

| Comando | Descripción |
|---------|-------------|
| `./bago start` | Menú interactivo — empieza aquí |
| `./bago ideas` | Lista y acepta ideas priorizadas |
| `./bago session` | Abre sesión con contexto precargado |
| `./bago status` | Dashboard rápido del estado |
| `./bago setup` | Sincroniza contexto e instala extensiones |

Ver todos: `./bago help --all`

---

## 🌐 Interfaz web (BAGO Viewer)

Abre `menu.html` en tu navegador para acceder al panel visual:

- 📦 Explorador de proyectos BAGO
- 📈 Evolución y línea de tiempo
- 📊 Métricas y KPIs
- 🎛 Orquestador en tiempo real

```bash
# Iniciar servidor (opcional, para live data)
python3 .bago/tools/bago_chat_server.py
# Luego abre: http://localhost:5050
```

---

## 🔄 Flujos de trabajo típicos

### 🆕 Nueva idea → implementación

```bash
./bago ideas                # 1. Lista ideas
./bago ideas --accept 3     # 2. Acepta idea #3
./bago session              # 3. Abre sesión con contexto
# [haces cambios]
./bago task --done          # 4. Marca completada
```

### 🔍 Verificar salud del proyecto

```bash
./bago status               # Dashboard rápido
./bago validate             # Validación profunda
./bago stability            # Smoke + VM + soak tests
```

### 🌾 Cosechar trabajo realizado

```bash
./bago detector             # Ver si hay contexto acumulado
./bago cosecha              # Protocolo W9 de cosecha
```

---

## 📖 Documentación

- **Para usuarios:** [`.bago/README.md`](.bago/README.md) — Visión técnica del sistema
- **Para agentes IA:** [`.bago/AGENT_START.md`](.bago/AGENT_START.md) — Punto de entrada canónico
- **Workflows:** [`.bago/workflows/`](.bago/workflows/) — W1 a W9
- **Prompts reutilizables:** [`.bago/prompts/`](.bago/prompts/) — Bootstrap, análisis, tareas

---

## 🎨 Cuándo usar qué

| Situación | Herramienta recomendada |
|-----------|-------------------------|
| Proyecto nuevo con BAGO | `prompts/00_BOOTSTRAP_PROYECTO.md` |
| Trabajo día a día | `./bago start` → opción 1 |
| Inspección/debugging | `./bago status` |
| Sesión exploratoria | `./bago session` (sin idea previa) |
| Revisar progreso | BAGO Viewer (`menu.html`) |

---

## 🛠 Arquitectura (nivel alto)

```
bago-framework/
├── bago                    # Script CLI principal
├── menu.html               # Interfaz web
├── .bago/
│   ├── tools/              # 30+ herramientas Python
│   ├── workflows/          # W0-W9 workflows canónicos
│   ├── prompts/            # Prompts reutilizables
│   ├── state/              # Estado persistente (JSON)
│   ├── core/               # Contratos y cerebro
│   └── extensions/         # Extensiones Copilot CLI
└── cleanversion/           # Versiones empaquetadas
```

---

## 🤝 Integración con GitHub Copilot

BAGO funciona especialmente bien conversando con Copilot:

1. Los prompts en `.bago/prompts/` están diseñados para ser copiados en chat
2. Las extensiones CLI se instalan automáticamente con `./bago setup`
3. El estado persistente permite retomar contexto entre sesiones

---

## 📦 Cleanversions

Sistema de versiones empaquetadas para distribuir configuraciones:

```bash
./bago versions             # Lista cleanversions disponibles
```

Cada cleanversion incluye su propio pack BAGO con modo de distribución específico.

---

## ⚙️ Requisitos

- Python 3.8+
- Navegador moderno (para BAGO Viewer)
- Terminal con soporte ANSI (para colores)

---

## 🔗 Enlaces

- **Documentación técnica:** [`.bago/README.md`](.bago/README.md)
- **GitHub:** [MarcValls/bago-framework](https://github.com/MarcValls/bago-framework)
- **Versión actual:** 2.5 (2.4-v2rc en pack.json)

---

**¿No sabes por dónde empezar?** → `./bago start`
