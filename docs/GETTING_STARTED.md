# Getting Started with BAGO

This guide walks you through your first BAGO-powered work session.

---

## Prerequisites

- **Python 3.9+** (no pip dependencies required for core BAGO)
- **Git** (optional, but recommended)
- An AI agent: GitHub Copilot CLI, Claude Code, or any LLM with file access

---

## Step 1 — Verify the installation

```bash
python3 bago validate
```

Expected output:
```
GO manifest
GO state
GO pack
```

If you see `KO`, run `python3 bago health` for diagnostics.

### First-run setup (optional interactive menu)

Running `python3 bago` with **no arguments** opens a setup menu. Options adapt to your environment:

```
  [1] Seguir con esta versión          → continue with the current version
  [2] Actualizar framework (git pull)  → pull latest from GitHub (git clones only)
  [3] Iniciar un proyecto nuevo        → copy BAGO to your own project
  [4] Evolucionar el framework BAGO    → develop BAGO itself
```

Choosing "Iniciar un proyecto nuevo" shows a numbered list of candidate directories — BAGO never silently operates inside the framework directory itself.

> You can skip this menu entirely and use subcommands directly (`validate`, `health`, etc.).

---

## Step 2 — Check system health

```bash
python3 bago health
```

BAGO health measures 5 dimensions:

| Dimension | What it measures |
|---|---|
| Integridad | pack.json + validator consistency |
| Disciplina workflow | Workflow usage per session |
| Captura decisiones | Average decisions per session |
| Estado stale | No stale tasks or outdated state |
| Consistencia inventario | Declared inventory matches reality |

A fresh installation shows `initializing`. After a few sessions, you'll see a score like `87/100 🟢`.

---

## Step 3 — Bootstrap your AI agent

Open `.bago/AGENT_START.md` — this is the entry point for any AI agent. It bootstraps the agent with:
- The active workflow context
- Current task and sprint status
- Operational protocols

**Example prompt to your AI agent:**
```
Read .bago/AGENT_START.md first, then help me implement [feature].
```

---

## Step 4 — Choose a workflow

```bash
python3 bago workflow
```

Or manually pick based on your task type:

| If you want to... | Use |
|---|---|
| Start a new project | `W1 · Cold Start` |
| Implement a feature | `W2 · Controlled Implementation` |
| Refactor existing code | `W3 · Sensitive Refactor` |
| Debug a complex issue | `W4 · Multi-cause Debug` |
| Wrap up a session | `W5 · Closure & Continuity` |
| Generate new ideas | `W6 · Applied Ideation` |
| Stay focused on one goal | `W7 · Session Focus` |
| Explore something new | `W8 · Exploration` |
| Harvest artifacts | `W9 · Cosecha` |

---

## Step 5 — Work with BAGO discipline

During a session:

1. **Start**: `python3 bago session` → logs session start with context
2. **Work**: Make changes, the agent records decisions and artifacts
3. **Check**: `python3 bago stability` → full system check mid-session
4. **Ideas**: `python3 bago ideas` → prioritized improvements to implement

---

## Step 6 — Close the session properly

```bash
# Harvest artifacts and decisions
python3 bago cosecha

# Full audit of the session
python3 bago audit

# Validate everything is consistent
python3 bago validate
```

---

## Step 7 — Track your evolution

After several sessions:

```bash
python3 bago efficiency
```

This shows how your BAGO instance has grown across versions — commands, tools, docs, and a weighted efficiency index.

---

## Common patterns

### Daily work routine
```bash
python3 bago stability      # Morning check
python3 bago ideas          # Pick today's focus
# ... work with AI agent ...
python3 bago validate       # End-of-session check
```

### When something feels wrong
```bash
python3 bago stale          # Check for stale tasks
python3 bago detector       # Context drift detection
python3 bago audit          # Full session audit
```

### When you want to evolve BAGO
```bash
python3 bago ideas          # See scored improvement ideas
# Implement an idea
python3 bago efficiency     # Measure the improvement
```

---

## File structure reference

```
.bago/
├── AGENT_START.md          ← Start here (for AI agent)
├── pack.json               ← System manifest
├── state/
│   ├── global_state.json   ← Current system state
│   ├── sessions/           ← Session records
│   ├── changes/            ← BAGO-CHG artifacts
│   └── evidences/          ← Evidence files
├── tools/                  ← 30 Python utilities
├── workflows/              ← 12 workflow protocols
└── core/                   ← Protocols and constitution
```

---

## Troubleshooting

**`KO version mismatch`**: `pack.json` version and `global_state.json` `bago_version` must match.

**`Health: initializing`**: Normal for a fresh install. After the first full session it transitions to `stable`.

**`Stale task detected`**: A task in `pending_w2_task.json` is older than 3 days. Clear with `python3 bago task --clear`.

---

*More documentation in `.bago/docs/` — 74 reference files covering every aspect of BAGO.*
