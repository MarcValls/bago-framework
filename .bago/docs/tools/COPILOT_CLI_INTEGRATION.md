# GitHub Copilot CLI Integration — New BAGO Tools

## Overview

BAGO now integrates with GitHub Copilot CLI capabilities through three new tools:
- **Research Mode** (`/research`) 
- **Session Chronicle** (`/chronicle`)
- **LSP Manager** (Language Server Protocol support)

These tools enhance BAGO workflows with Copilot CLI's research, persistence, and code intelligence features.

---

## 1. Research Orchestrator

**Command:** `bago research <tema>`

### Purpose
Implements Copilot CLI's `/research` mode for BAGO. Provides structured investigation into repository themes.

### Features
- Collects repository structure and dependencies
- Generates investigation reports by topic
- Integrates with W6 (Ideación) and W8 (Exploración) workflows
- Persistent research history in `.bago/state/research/`

### Usage

```bash
# Start investigation on a topic
bago research "API security architecture"

# List previous investigations
bago research --list

# Example output
# ID:        RES-2026-04-28-042546
# Tema:      API security architecture
# Áreas:
#   • Arquitectura y estructura
#   • Dependencias y integraciones
#   • Estado operativo BAGO
```

### Integration Points
- **W6 (Ideación Aplicada)**: Use research reports to prioritize ideas
- **W8 (Exploración)**: Launch research with exploratory workflows
- **AGENT_START.md**: Agentes can trigger `bago research` for context gathering

---

## 2. Chronicle Reporter

**Command:** `bago chronicle [--summary|--detailed]`

### Purpose
Implements Copilot CLI's `/chronicle` mode for BAGO. Provides session history and continuity across sessions.

### Features
- Displays status summary (version, health, session count)
- Shows recent sessions and changes (last 10 sessions, 5 changes)
- Lists pending tasks
- Recommends next steps based on history
- Session persistence in `.bago/state/sessions/`

### Usage

```bash
# Full report
bago chronicle

# Brief summary (no session history)
bago chronicle --summary

# Detailed analysis
bago chronicle --detailed

# Example output
# STATUS
#   Version:        2.5-stable
#   Health:         80/100
#   Total Sessions: 24
#
# RECOMMENDATIONS FOR NEXT SESSION
#   1. Complete pending W2 Implementation task
#   2. Continue with workflow type similar to: W7_FOCO_SESION
#   3. Run: bago audit (before starting work)
#   4. Run: bago cosecha (after closing session)
```

### Integration Points
- **W5 (Cierre y Continuidad)**: Automatically run before closing sessions
- **AGENT_START.md**: Agentes load chronicle context at session start
- **Continuity**: Bridge between sessions via persistent state

---

## 3. LSP Manager

**Command:** `bago lsp [--status|--list|--detect|--integrate]`

### Purpose
Manages Language Server Protocol (LSP) configuration for BAGO. Provides code intelligence to tools and workflows.

### Features
- Auto-detects available LSP servers (TypeScript, Python, Go, Rust)
- Registers and manages LSP configurations
- Integrates with code analysis tools
- Persists configuration in `.bago/state/lsp_registry.json`

### Usage

```bash
# Check LSP status
bago lsp --status
# Output:
# 🟢 Active:   2/4
# ⏳ Total:    4

# List registered servers
bago lsp --list
# Output:
# 🟢 typescript | typescript-language-server
# 🟢 python     | pylsp

# Auto-detect and register servers
bago lsp --detect
# Scans system for: typescript-language-server, pylsp, gopls, rust-analyzer

# Integrate with pack.json (advisory)
bago lsp --integrate
# Shows suggested pack.json configuration

# Manual registration
bago lsp --register go gopls
```

### Supported Languages
- **TypeScript/JavaScript**: `typescript-language-server`
- **Python**: `pylsp` (python-lsp-server)
- **Go**: `gopls`
- **Rust**: `rust-analyzer`

### Integration Points
- **W2 (Implementación Controlada)**: Code intelligence for refactoring
- **W3 (Refactor Sensible)**: Precise symbol navigation and renaming
- **Code Analysis Tools**: `type_check.py`, `naming_check.py` use LSP context

---

## Architecture & Data Flow

```
┌─ GitHub Copilot CLI ─────────────────────────────┐
│  /research  /chronicle  LSP Servers                │
└─────────────────┬───────────────────────────────┘
                  │
        ┌─────────▼──────────┐
        │  BAGO Orchestration │
        └─────────┬──────────┘
                  │
      ┌───────────┼───────────┐
      │           │           │
   ┌──▼──┐   ┌──▼──┐   ┌────▼───┐
   │ W6  │   │ W8  │   │  W2/W3 │
   │     │   │     │   │        │
   └─────┘   └─────┘   └────────┘
      │        │           │
   Research  Explorer     Code
   Reports   Findings   Intelligence
```

---

## Shared Utilities

All three tools use `bago_utils.py` for common operations:
- Path resolution (`get_bago_root`, `get_repo_root`)
- State management (`load_json`, `save_json`)
- Timestamps (`timestamp_iso`, `timestamp_readable`)
- Health status queries

---

## Testing

All three tools are covered by integration tests:

```bash
# Run all Copilot integration tests
python3 .bago/tools/integration_tests.py --test 107  # research_orchestrator
python3 .bago/tools/integration_tests.py --test 108  # chronicle_reporter
python3 .bago/tools/integration_tests.py --test 109  # lsp_manager

# Or run all tests
python3 .bago/tools/integration_tests.py
```

---

## Configuration

### Automatic Registration

When tools are first used, they auto-register in `tool_registry.py` with preflight checks.

### State Directory

All tools persist data in `.bago/state/`:
```
.bago/state/
├── research/           # Research reports (RES-*.json)
├── sessions/           # Session history (*.json)
├── lsp_registry.json   # LSP server configuration
└── global_state.json   # Overall BAGO state
```

### pack.json Integration

Optional LSP configuration in `pack.json`:

```json
{
  "lsp": {
    "enabled": true,
    "registry_file": "state/lsp_registry.json",
    "auto_detect": true
  }
}
```

---

## Examples

### Scenario 1: Research-driven Implementation

```bash
# 1. Investigate architecture
bago research "microservices transition"

# 2. Review chronicle for context
bago chronicle --summary

# 3. Accept a generated idea
bago ideas --accept 3

# 4. Implement with code intelligence
bago lsp --status  # Ensure LSP is available
# ... start W2 workflow
```

### Scenario 2: Session Continuity

```bash
# Session 1: End-of-day harvest
bago cosecha

# Next day: Load context
bago chronicle --detailed
# See pending tasks and recommendations

# Run preflight
bago audit

# Continue work
```

### Scenario 3: Code Refactoring with Intelligence

```bash
# Setup code intelligence
bago lsp --detect
bago lsp --status

# Start sensitive refactor
python3 bago W3

# Tools use LSP for:
# - Precise symbol navigation (type_check.py)
# - Consistent naming (naming_check.py)
# - Safe refactoring recommendations
```

---

## Troubleshooting

### Research Reports Not Appearing

```bash
# Check state directory
ls -la .bago/state/research/

# Verify bago_utils can access paths
python3 -c "from bago_utils import get_state_dir; print(get_state_dir())"
```

### Chronicle Shows No Sessions

```bash
# Create a session first
bago session

# Then review chronicle
bago chronicle
```

### LSP Servers Not Detected

```bash
# Check system PATH
which typescript-language-server  # or pylsp, gopls, rust-analyzer

# Manual registration
bago lsp --register typescript /usr/local/bin/typescript-language-server

# Verify
bago lsp --list
```

---

## See Also

- `W6_IDEACION_APLICADA.md` — Workflow for prioritized idea generation
- `W8_EXPLORACION.md` — Exploration workflow (uses research)
- `W5_CIERRE_Y_CONTINUIDAD.md` — Session closure (uses chronicle)
- `tool_registry.py` — Full registry of all BAGO tools
- `bago_utils.py` — Shared utilities documentation

