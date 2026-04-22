# BAGO 2.5-stable · Guía para el Tester

Gracias por probar BAGO. Este paquete contiene el framework listo para usar.

---

## Requisitos

- Python 3.9+
- Terminal con color (iTerm2, Terminal.app, Windows Terminal, etc.)

---

## Primer arranque

```bash
# 1. Descomprime el paquete en cualquier directorio
unzip BAGO_v03-template-seed_tester.zip
cd v03-template-seed

# 2. Da permiso de ejecución (solo la primera vez en macOS/Linux)
chmod +x bago

# 3. Arranca
python3 bago
```

Al ejecutar por primera vez verás:

```
  ┌─────────────────────────────────────────────┐
  │  BAGO · Primera ejecución                   │
  ├─────────────────────────────────────────────┤
  │  [1] Evolucionar el framework BAGO          │
  │  [2] Iniciar un proyecto nuevo              │
  └─────────────────────────────────────────────┘
```

- **[1]** → modo framework: BAGO se activa en el directorio actual para ser desarrollado
- **[2]** → modo proyecto: copia el pack a otra ruta e inicializa un proyecto nuevo

---

## Comandos principales

| Comando | Descripción |
|---|---|
| `python3 bago` | Banner + estado |
| `python3 bago health` | Score de salud (0–100) |
| `python3 bago ideas` | Selector de ideas con scoring |
| `python3 bago ideas --accept N` | Acepta idea N y genera tarea W2 |
| `python3 bago task` | Muestra la tarea W2 pendiente |
| `python3 bago task --done` | Marca tarea completada + registra en ideas registry |
| `python3 bago session` | Abre sesión W2 con preflight pre-rellenado |
| `python3 bago session --dry` | Muestra args sin ejecutar |
| `python3 bago stability` | Resumen único de estabilidad |
| `python3 bago dashboard` | Dashboard del pack |
| `python3 bago validate` | Valida integridad del pack |
| `python3 bago workflow` | Selector interactivo de workflow |
| `python3 bago audit` | Auditoría de artefactos |
| `python3 bago stale` | Detecta artefactos obsoletos |
| `python3 bago cosecha` | Cosecha de sesión |
| `python3 bago versions` | Lista cleanversions disponibles |

---

## Novedades en v03 (2.5-stable)

- **Ciclo de tareas completo**: `ideas --accept` → `task` → `session` → `task --done`
- **Ideas evolution chain**: el selector de ideas evoluciona en 3 generaciones según lo implementado
- **Registry de ideas**: `bago task --done` registra automáticamente en `implemented_ideas.json`
- **Banner dinámico**: muestra la task W2 activa con icono ⏳/✅
- **`bago stability`**: resumen único de validadores, smoke tests y VM status
- **BAGO_REFERENCIA_COMPLETA.md**: documento de referencia de 18 secciones

---

## Instalar alias global (opcional)

```bash
echo 'alias bago="python3 $(pwd)/bago"' >> ~/.zshrc
source ~/.zshrc
bago health
```
