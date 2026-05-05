# BAGO Bootstrap — Instrucciones de inicio

Este archivo es la fuente de verdad para el arranque de cualquier agente IA
(Copilot, Codex u otro) trabajando en este repositorio.
Para cambiar el comportamiento de inicio, edita **solo este archivo**.

---

## 1. Estado del sistema

Al iniciar, ejecuta en orden:

```bash
python3 bago db status      # ideas disponibles + guardian runs
python3 bago hello --quick  # estado resumido: flujo, tarea, salud
```

Lee también:
- `.bago/state/global_state.json` → flujo activo, sprint, notas
- `.bago/state/bago.db` → fuente de verdad de ideas e historial

---

## 2. Flujo de trabajo estándar

```
bago ideas          → qué hacer ahora (priorizado por contexto)
< implementa >      → sigue el campo "siguiente paso" de la idea
bago health         → verifica que no rompiste nada (debe ser ≥ 80%)
bago task --done    → cierra la tarea y actualiza el estado
```

Repite el ciclo. No implementes sin consultar `bago ideas` primero.

---

## 3. Criterios de calidad

- Health < 80% → detente y reporta antes de continuar
- No modifiques archivos fuera del scope del flujo activo en `global_state.json`
- Cada commit debe tener mensaje descriptivo en español
- Incluye siempre el trailer: `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`

---

## 4. Comandos esenciales

| Comando | Cuándo usarlo |
|---------|--------------|
| `python3 bago hello --quick` | Al arrancar — estado en 3 líneas |
| `python3 bago ideas` | Antes de implementar cualquier cosa |
| `python3 bago status` | Para entender el contexto actual |
| `python3 bago health` | Después de cada cambio significativo |
| `python3 bago task --done` | Al terminar una tarea |
| `python3 bago db status` | Para ver el estado de bago.db |

---

## 5. Archivos clave

```
.bago/
  state/
    bago.db              ← fuente de verdad (ideas + historial guardian)
    global_state.json    ← estado del sprint y flujo activo
    config/
      ideas_catalog.json ← catálogo de mejoras disponibles
  tools/                 ← todos los comandos bago
bago                     ← script principal (python3 bago <cmd>)
```
