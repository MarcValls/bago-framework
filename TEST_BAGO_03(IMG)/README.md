# Sprite Pipeline — char_girl_walk (32 frames)

> Proyecto de game art para **Bianca The Game** — gobernado por BAGO v3.0

![bago](https://img.shields.io/badge/BAGO-v3.0-blue) ![status](https://img.shields.io/badge/status-activo-brightgreen) ![frames](https://img.shields.io/badge/frames-32-orange) ![version](https://img.shields.io/badge/pipeline-v1.1-green)

## ¿Qué hace este proyecto?

Genera **32 frames de animación walk** para el personaje `char_girl` mediante dos pipelines complementarios:

| Pipeline | Herramienta | Descripción |
|----------|-------------|-------------|
| `run_generate_32.sh` | OpenAI `gpt-image-1` | Genera frames via API — batch automático, 1024×1024, fondo transparente |
| `perchance_keyboard_submit.sh` | Perchance + AppleScript | Envía prompts al generador web de Perchance vía automatización de teclado |

---

## Requisitos

```bash
# Python 3.9+
pip install openai

# Variables de entorno (para pipeline OpenAI)
export OPENAI_API_KEY="sk-..."
```

> **Nota:** El pipeline Perchance requiere macOS (AppleScript) y permisos de **Accesibilidad** en Ajustes del Sistema.

---

## Uso rápido

### Pipeline OpenAI (recomendado para batch)

```bash
# Genera los 32 frames secuencialmente
./run_generate_32.sh

# Modo batch (un solo comando Python, más eficiente)
./run_generate_32.sh --batch

# Personalizar modelo, calidad y destino
./run_generate_32.sh --model gpt-image-1 --quality high --out-dir ./output

# Ver todas las opciones
./run_generate_32.sh --help
```

### Validar frames generados

```bash
python3 generate_frames_openai.py validate --frames-dir .
# → muestra frame_00.png ... frame_31.png presentes / faltantes
```

### Pipeline Perchance (alternativo, interactivo)

```bash
# Con espera manual entre envíos
./perchance_keyboard_submit.sh

# Modo automático (12s entre frames)
./perchance_keyboard_submit.sh --auto --wait 15

# Continuar desde un frame específico
./perchance_keyboard_submit.sh --from 10

# Ver todas las opciones
./perchance_keyboard_submit.sh --help
```

---

## Archivos

| Archivo | Descripción |
|---------|-------------|
| `generate_frames_openai.py` | Generador principal — subcomandos: `generate-one`, `generate-all`, `validate` |
| `run_generate_32.sh` | Wrapper shell — itera sobre los 32 frames usando el generador local |
| `perchance_keyboard_submit.sh` | Automatización AppleScript para Perchance (alternativo) |
| `char_girl_walk_prompts_32_from_txt.csv` | 32 prompts con `frame_index` y `prompt` |
| `.bago/pack.json` | Configuración BAGO del proyecto |

---

## generate_frames_openai.py — Referencia

```bash
# Genera un frame individual
python3 generate_frames_openai.py generate-one \
  --index 5 --csv char_girl_walk_prompts_32_from_txt.csv \
  --frames-dir . --model gpt-image-1 --size 1024x1024 \
  --quality high --background transparent

# Genera todos (con retry automático)
python3 generate_frames_openai.py generate-all \
  --csv char_girl_walk_prompts_32_from_txt.csv \
  --frames-dir ./output --retry 3

# Valida que los 32 frames existan
python3 generate_frames_openai.py validate --frames-dir .
```

---

## Problemas conocidos

| # | Problema | Estado |
|---|----------|--------|
| 1 | ~~`generate_frames_openai.py` dependía de `/Volumes/Warehouse/...`~~ | ✅ Corregido v1.1 — ahora es local |
| 2 | `OPENAI_API_KEY` debe estar exportada | ⚠️ Manual — sin key el script termina con error claro |
| 3 | Perchance requiere foco en el navegador y permisos Accesibilidad | ⚠️ Limitación AppleScript en macOS |
| 4 | `gpt-image-1` con `background: transparent` requiere `openai>=1.35` | ⚠️ Actualiza con `pip install -U openai` si falla |

---

## Estado BAGO

```bash
# Desde BAGO_CAJAFISICA (framework padre)
./bago health
./bago dashboard
```

---

*Gobernado por [BAGO Framework v3.0](https://github.com/MarcValls/bago-framework)*
