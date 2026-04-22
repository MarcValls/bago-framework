#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
bago_chat_server.py — Chat web BAGO con/sin roles (motor: Ollama)

Uso:
  bago chat                        → abre http://localhost:8484
  bago chat --llm-assist           → habilita asistencia LLM explícitamente
  bago chat --port 9000            → puerto alternativo
  bago chat --model mistral        → modelo Ollama
  bago chat --no-browser           → no abrir navegador automáticamente
  bago chat --no-tools             → sin ejecución de herramientas BAGO

Roles: seleccionables desde la UI (máx. 3 simultáneos, según pack.json)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import threading
import urllib.request
import urllib.error
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BAGO_ROOT    = Path(__file__).resolve().parents[2]
BAGO_SCRIPT  = BAGO_ROOT / "bago"
AGENTS_DIR   = BAGO_ROOT / ".bago" / "agents"

DEFAULT_PORT  = 8484
DEFAULT_MODEL = "qwen2.5:0.5b"
OLLAMA_BASE   = "http://localhost:11434"
BAGO_CMD_RE   = re.compile(r"\[BAGO:([a-z_-]+)\]")
MAX_ROLES     = 3  # límite canónico pack.json

ALLOWED_BAGO_CMDS = {
    "health", "ideas", "audit", "dashboard",
    "validate", "stale", "task", "detector", "stability",
    "context",
}

# Roles disponibles con descripción corta (fuente: 04_CONTRATOS_DE_ROL.md)
ROLE_META: dict[str, str] = {
    "MAESTRO_BAGO":           "Coordina la sesión, decide el modo predominante y mantiene continuidad.",
    "ANALISTA_Contexto":      "Aclara problema, restricciones y riesgos antes de decidir implementación.",
    "ARQUITECTO_Soluciones":  "Diseña límites técnicos, secuencia y contratos de implementación.",
    "GENERADOR_Contenido":    "Produce artefactos técnicos concretos con alcance delimitado.",
    "ORGANIZADOR_Entregables":"Consolida resultados, actualiza estado y deja siguiente paso claro.",
    "GUIA_VERTICE":           "Metacontrol. Solo si hay deriva o incoherencia repetida.",
    "ADAPTADOR_PROYECTO":     "Adapta el contexto del proyecto externo al marco BAGO.",
    "INICIADOR_MAESTRO":      "Convierte el contexto inicial en entrada limpia para el Maestro.",
}

SYSTEM_PROMPT_BASE = """Eres BAGO, agente de gobernanza técnica v2.5-stable. \
Responde SIEMPRE en español, conciso y directo. \
Usa los datos del contexto cuando te pregunten sobre el proyecto o estado — no digas que no tienes acceso. \
Para datos en tiempo real emite [BAGO:comando] en línea propia \
(comandos: health, ideas, audit, dashboard, validate, stale, task, detector, stability). \
No invoques 'codex' ni agentes externos."""

# ── Orquestación dinámica de roles ────────────────────────────────────────────

# Mapeo keyword → rol. Se evalúa en orden; primera coincidencia gana.
_ROLE_SIGNALS: list[tuple[list[str], str]] = [
    (["analiza", "análisis", "diagnos", "qué pasa", "problema", "restricci", "riesgo", "entiende"],
     "ANALISTA_Contexto"),
    (["diseña", "arquitect", "estructur", "enfoque", "plan técn", "cómo implement", "límite"],
     "ARQUITECTO_Soluciones"),
    (["genera", "crea", "escribe", "código", "script", "implement", "produce", "hazme", "haz un"],
     "GENERADOR_Contenido"),
    (["resume", "cierra", "siguiente paso", "empaqueta", "organiza", "qué hago", "qué falta"],
     "ORGANIZADOR_Entregables"),
]

def _detect_role(msg: str) -> str:
    """
    Detecta por keywords el rol más apropiado para este mensaje.
    Devuelve nombre del rol o 'MAESTRO_BAGO' como fallback de coordinación.
    """
    low = msg.lower()
    for keywords, role in _ROLE_SIGNALS:
        if any(kw in low for kw in keywords):
            return role
    return "MAESTRO_BAGO"

# ── BAGO Context Loader ───────────────────────────────────────────────────────

def _load_bago_context() -> tuple[str, dict]:
    """
    Lee los archivos de estado BAGO y construye un bloque de contexto COMPACTO
    para el system prompt.  Objetivo: <400 chars para minimizar prefill en CPU.
    Devuelve (context_str, summary_dict) donde summary_dict se usa en /api/context.
    """
    STATE = BAGO_ROOT / ".bago" / "state"
    summary: dict = {}

    # global_state.json --------------------------------------------------------
    gs_path = STATE / "global_state.json"
    if gs_path.exists():
        try:
            gs = json.loads(gs_path.read_text(encoding="utf-8"))
            inv = gs.get("inventory", {})
            summary.update({
                "version":       gs.get("bago_version", "?"),
                "health":        gs.get("system_health", "?"),
                "sessions":      inv.get("sessions", "?"),
                "last_session":  gs.get("last_completed_session_id", "?"),
                "last_workflow": gs.get("last_completed_workflow", "?"),
                "last_roles":    gs.get("last_completed_roles", []),
                "active_roles":  gs.get("active_roles", []),
                "active_scenarios": gs.get("active_scenarios", []),
            })
        except Exception:
            pass

    # repo_context.json --------------------------------------------------------
    rc_path = STATE / "repo_context.json"
    if rc_path.exists():
        try:
            rc = json.loads(rc_path.read_text(encoding="utf-8"))
            repo_name = Path(rc.get("repo_root", "")).name or "?"
            summary.update({
                "repo":         repo_name,
                "repo_root":    rc.get("repo_root", "?"),
                "working_mode": rc.get("working_mode", "?"),
            })
        except Exception:
            pass

    summary["context_loaded"] = bool(summary)

    # Contexto compacto para el system prompt (≤400 chars)
    ctx = (
        f"[BAGO {summary.get('version','?')} · health={summary.get('health','?')} · "
        f"ses={summary.get('sessions','?')} · última={summary.get('last_session','?')} · "
        f"wf={summary.get('last_workflow','?')} · "
        f"proyecto={summary.get('repo','?')} · modo={summary.get('working_mode','?')}]"
    )
    return (ctx, summary)

# Config mutable por argparse / endpoints
_cfg: dict = {
    "model":          DEFAULT_MODEL,
    "tools":          True,
    "port":           DEFAULT_PORT,
    "roles":          [],      # lista de nombres de rol activos (máx. MAX_ROLES)
    "llm_assist":     False,   # asistencia LLM opt-in y fuera del plano canónico
    "mock":           False,   # True → respuestas de prueba sin LLM
    "bago_context":   "",      # contexto BAGO inyectado en el system prompt
    "context_summary": {},     # resumen para /api/context
}

# ── Roles ─────────────────────────────────────────────────────────────────────

def _role_content(name: str) -> str:
    """Lee el .md del rol desde agents/. Devuelve '' si no existe."""
    path = AGENTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8").strip()
    return ""


def _build_system_prompt(last_user_msg: str = "") -> str:
    """
    Construye el system prompt.
    - Si hay roles manuales activos → los usa todos (modo manual).
    - Si no → detecta el rol apropiado para este mensaje (orquestación dinámica).
    Mantiene el prompt compacto para minimizar prefill en CPU.
    """
    ctx = _cfg.get("bago_context", "")

    manual_roles = _cfg.get("roles", [])
    if manual_roles:
        # Modo manual: el usuario activó roles explícitamente desde la UI
        roles_txt = "\n".join(
            f"- {n}: {ROLE_META.get(n, '')}" for n in manual_roles
        )
        return (
            f"{SYSTEM_PROMPT_BASE}\n\nContexto: {ctx}\n\n"
            f"Roles activos ({len(manual_roles)}/{MAX_ROLES}):\n{roles_txt}\n\n"
            f"Ejemplo: Usuario: 'qué proyecto tengo?' → "
            f"BAGO [{manual_roles[0]}]: 'Tu proyecto activo es "
            f"{_cfg.get('context_summary', {}).get('repo', '?')}. ¿En qué te ayudo?'"
        )

    # Modo orquestación: 1 rol por turno, seleccionado automáticamente
    role = _detect_role(last_user_msg) if last_user_msg else "MAESTRO_BAGO"
    role_desc = ROLE_META.get(role, "Coordina y responde.")
    repo = _cfg.get("context_summary", {}).get("repo", "el proyecto activo")

    return (
        f"{SYSTEM_PROMPT_BASE}\n\nContexto: {ctx}\n\n"
        f"Rol activo este turno: {role} — {role_desc}\n\n"
        f"Ejemplo: Usuario: 'qué proyecto tengo?' → "
        f"BAGO [{role}]: 'Tu proyecto activo es {repo}. ¿En qué te ayudo?'"
    )

# ── Ollama ────────────────────────────────────────────────────────────────────

def _ollama_available() -> bool:
    try:
        urllib.request.urlopen(f"{OLLAMA_BASE}/api/tags", timeout=2)
        return True
    except Exception:
        return False


def _available_models() -> list[str]:
    """Devuelve los nombres de modelos descargados en Ollama."""
    try:
        with urllib.request.urlopen(f"{OLLAMA_BASE}/api/tags", timeout=3) as r:
            data = json.loads(r.read())
            return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def _model_matches(target: str, available: list[str]) -> bool:
    """'llama3.2' coincide con 'llama3.2:latest' o 'llama3.2:3b', etc."""
    return any(
        m == target or m == target + ":latest" or m.startswith(target + ":")
        for m in available
    )


def _stream_ollama(messages: list[dict]):
    """Genera tokens desde Ollama en modo streaming."""
    payload = json.dumps({
        "model":    _cfg["model"],
        "messages": messages,
        "stream":   True,
    }).encode()
    req = urllib.request.Request(
        f"{OLLAMA_BASE}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        resp_cm = urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        if "not found" in body.lower() or e.code in (404, 500):
            raise RuntimeError(
                f"⚠ Modelo '{_cfg['model']}' no disponible en Ollama.\n"
                f"  Descárgalo con:  ollama pull {_cfg['model']}\n"
                f"  Modelos actuales: {', '.join(_available_models()) or 'ninguno'}"
            ) from e
        raise RuntimeError(f"⚠ Ollama HTTP {e.code}: {body[:200]}") from e
    with resp_cm as resp:
        for raw in resp:
            line = raw.decode().strip()
            if not line:
                continue
            obj   = json.loads(line)
            token = obj.get("message", {}).get("content", "")
            if token:
                yield token
            if obj.get("done"):
                break


def _stream_mock(messages: list[dict]):
    """Genera respuestas de prueba sin LLM para verificar la UI."""
    import time
    user_msg = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )
    active_roles = _cfg.get("roles", [])
    role_txt = f" [{', '.join(active_roles)}]" if active_roles else " [sin roles]"
    response = (
        f"🤖 **Modo mock**{role_txt}\n\n"
        f"Recibido: _{user_msg[:80]}_\n\n"
        "Esto es una respuesta de prueba — Ollama no está disponible o no hay modelo descargado.\n\n"
        "Para activar el LLM real:\n"
        "1. `ollama serve` — arrancar el servidor\n"
        f"2. `ollama pull {_cfg['model']}` — descargar el modelo\n"
        "3. Recargar la página"
    )
    for word in response.split(" "):
        yield word + " "
        time.sleep(0.02)


def _safe_reply(user_msg: str) -> str:
    """Respuesta determinista cuando la ayuda LLM está desactivada."""
    summary = _cfg.get("context_summary", {})
    repo = summary.get("repo", "?")
    mode = summary.get("working_mode", "?")
    health = summary.get("health", "?")
    last_session = summary.get("last_session", "?")
    last_workflow = summary.get("last_workflow", "?")
    low = user_msg.lower().strip()

    if any(token in low for token in ("proyecto", "repo", "repositorio", "directorio activo", "target")):
        return (
            "Asistencia LLM desactivada por política.\n\n"
            f"Proyecto activo: {repo}\n"
            f"Modo: {mode}\n"
            "Si necesitas cambiarlo, usa el flujo canónico de selección de target."
        )

    if any(token in low for token in ("contexto", "estado", "health", "sesión", "workflow")):
        return (
            "Asistencia LLM desactivada por política.\n\n"
            f"Health: {health}\n"
            f"Última sesión: {last_session}\n"
            f"Último workflow: {last_workflow}\n"
            "Para más detalle usa `/contexto`, `/health`, `/dashboard` o `/task`."
        )

    return (
        "Asistencia LLM desactivada por política.\n\n"
        "Este chat sigue disponible como interfaz canónica de BAGO:\n"
        "- `/contexto` recarga y muestra contexto real\n"
        "- `/health` muestra salud del pack\n"
        "- `/dashboard` resume estado\n"
        "- `/task` muestra handoff activo\n"
        "- `/ideas` lista ideas priorizadas\n\n"
        "Si quieres ayuda generativa opcional, arranca el chat con `--llm-assist`."
    )


def _stream_safe_reply(user_msg: str):
    """Streaming ligero sin LLM para mantener la misma UX del chat."""
    import time

    response = _safe_reply(user_msg)
    for chunk in response.split(" "):
        yield chunk + " "
        time.sleep(0.01)


# ── BAGO tools ────────────────────────────────────────────────────────────────

def _run_bago(cmd: str) -> str:
    if cmd == "contexto":
        cmd = "context"
    if cmd == "context":
        # Recarga el contexto desde disco y devuelve un resumen legible
        ctx_str, summary = _load_bago_context()
        _cfg["bago_context"] = ctx_str
        _cfg["context_summary"] = summary
        lines = [
            "✅ Contexto BAGO recargado.\n",
            f"• Versión:        {summary.get('version', '?')}",
            f"• Health:         {summary.get('health', '?')}",
            f"• Proyecto:       {summary.get('repo', '?')}",
            f"• Modo:           {summary.get('working_mode', '?')}",
            f"• Sesiones:       {summary.get('sessions', '?')}",
            f"• Última sesión:  {summary.get('last_session', '?')}",
            f"• Último workflow:{summary.get('last_workflow', '?')}",
        ]
        return "\n".join(lines)

    if cmd not in ALLOWED_BAGO_CMDS:
        return f"Comando '{cmd}' no permitido en modo chat."
    try:
        r = subprocess.run(
            [sys.executable, str(BAGO_SCRIPT), cmd],
            capture_output=True, text=True, timeout=30,
            cwd=str(BAGO_ROOT),
        )
        return (r.stdout + r.stderr).strip() or f"[bago {cmd}] Sin salida."
    except subprocess.TimeoutExpired:
        return f"[bago {cmd}] Timeout (>30s)."
    except Exception as e:
        return f"[bago {cmd}] Error: {e}"


# ── HTML ──────────────────────────────────────────────────────────────────────

HTML_PAGE = r"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>BAGO Chat</title>
<style>
:root {
  --bg:     #0f1117;
  --panel:  #161b22;
  --border: #30363d;
  --user:   #1c3a5e;
  --bot:    #161b22;
  --tool:   #0d2318;
  --text:   #c9d1d9;
  --dim:    #6e7681;
  --accent: #1f6feb;
  --cyan:   #39c5cf;
  --green:  #3fb950;
  --red:    #f85149;
  --mono:   "JetBrains Mono","Fira Code","Cascadia Code",monospace;
  --sans:   system-ui,-apple-system,sans-serif;
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html, body { height: 100%; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--sans);
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

/* ── Header ───────────────────────────────── */
header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
  background: var(--panel);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
}
.logo {
  font-family: var(--mono);
  font-size: 17px;
  font-weight: 700;
  color: var(--cyan);
  letter-spacing: 3px;
}
.subtitle { font-size: 11px; color: var(--dim); }
.spacer { flex: 1; }
.dot {
  width: 8px; height: 8px;
  border-radius: 50%;
  background: var(--dim);
  transition: background .3s;
}
.dot.ok  { background: var(--green); }
.dot.err { background: var(--red); }
.slabel { font-size: 11px; color: var(--dim); }

/* ── Messages ─────────────────────────────── */
#msgs {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}
.msg {
  max-width: 78%;
  border-radius: 8px;
  padding: 10px 14px;
  line-height: 1.65;
  font-size: 14px;
  word-break: break-word;
  white-space: pre-wrap;
}
.msg.user {
  background: var(--user);
  align-self: flex-end;
  border-bottom-right-radius: 2px;
  color: #ddeeff;
}
.msg.bot {
  background: var(--bot);
  align-self: flex-start;
  border-bottom-left-radius: 2px;
  border: 1px solid var(--border);
}
.msg.tool {
  background: var(--tool);
  align-self: flex-start;
  border: 1px solid #1a4a2a;
  font-family: var(--mono);
  font-size: 12px;
  width: min(1100px, 96vw);
  max-width: 96%;
  border-radius: 6px;
  padding: 12px 14px;
}
.tool-hdr {
  color: var(--green);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .5px;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 5px;
}
.tool-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}
.tool-actions {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}
.tool-btn {
  border: 1px solid #27583a;
  background: #112b1d;
  color: #9be3b0;
  border-radius: 5px;
  padding: 4px 8px;
  font-size: 11px;
  line-height: 1.2;
  cursor: pointer;
  font-family: var(--mono);
}
.tool-btn:hover {
  background: #173726;
}
.tool-btn.secondary {
  color: #c7d7ce;
  border-color: #365144;
}
.tool-body {
  overflow-x: auto;
}
.tool-pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.45;
}
.tool-pre.collapsed {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 12;
  overflow: hidden;
}
.tool-edit-banner {
  margin-bottom: 6px;
  font-size: 11px;
  color: #9be3b0;
}
.msg code {
  background: rgba(255,255,255,.07);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: var(--mono);
  font-size: 12px;
}
.cursor {
  display: inline-block;
  width: 7px; height: 14px;
  background: var(--cyan);
  animation: blink .8s step-end infinite;
  vertical-align: text-bottom;
  margin-left: 1px;
}
@keyframes blink { 50% { opacity: 0; } }

/* typing dots */
.typing { display: flex; gap: 5px; align-items: center; padding: 10px 14px; }
.typing span {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--dim);
  animation: bounce 1.2s infinite ease-in-out;
}
.typing span:nth-child(2) { animation-delay: .2s; }
.typing span:nth-child(3) { animation-delay: .4s; }
@keyframes bounce { 0%,80%,100% { transform: scale(.7); } 40% { transform: scale(1.2); } }

/* ── Input area ───────────────────────────── */
.input-wrap {
  background: var(--panel);
  border-top: 1px solid var(--border);
  padding: 10px 16px;
  flex-shrink: 0;
}
.hint-row {
  font-size: 11px;
  color: var(--dim);
  margin-bottom: 6px;
}
.hint-row code {
  background: rgba(255,255,255,.06);
  padding: 1px 5px;
  border-radius: 3px;
  font-family: var(--mono);
  font-size: 10px;
  color: var(--cyan);
}
#role-badge {
  display: inline-block;
  font-size: 10px;
  font-family: var(--mono);
  color: var(--bg);
  background: var(--cyan);
  border-radius: 3px;
  padding: 1px 6px;
  margin-left: 6px;
  transition: background .3s;
}
.row { display: flex; gap: 8px; }
textarea#inp {
  flex: 1;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 6px;
  color: var(--text);
  font-family: var(--sans);
  font-size: 14px;
  padding: 8px 12px;
  outline: none;
  resize: none;
  line-height: 1.5;
  min-height: 38px;
  max-height: 120px;
  overflow-y: auto;
}
textarea#inp:focus { border-color: var(--accent); }
textarea#inp::placeholder { color: var(--dim); }
#send {
  background: var(--accent);
  border: none;
  border-radius: 6px;
  color: #fff;
  cursor: pointer;
  font-size: 18px;
  height: 38px;
  width: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  line-height: 1;
}
#send:hover  { background: #388bfd; }
#send:disabled { background: var(--border); cursor: default; color: var(--dim); }
</style>
</head>
<body>
<header>
  <div class="logo">BAGO</div>
  <div class="subtitle">Chat · plano canónico · LLM opcional</div>
  <div class="spacer"></div>
  <div class="dot" id="dot"></div>
  <div class="slabel" id="slabel">conectando…</div>
</header>

<div id="msgs"></div>

<div class="input-wrap">
  <div class="hint-row">
    Tip: escribe libremente en español ·
    <code>/health</code> <code>/ideas</code> <code>/audit</code>
    <code>/dashboard</code> <code>/task</code> <code>/contexto</code> para comandos BAGO directos ·
    Rol activo: <span id="role-badge">MAESTRO_BAGO</span>
  </div>
  <div class="row">
    <textarea id="inp" rows="1" placeholder="Escribe un mensaje…" autofocus></textarea>
    <button id="send" title="Enviar (Enter)">↑</button>
  </div>
</div>

<script>
const msgs    = document.getElementById("msgs");
const inp     = document.getElementById("inp");
const sendBtn = document.getElementById("send");
const dot     = document.getElementById("dot");
const slabel  = document.getElementById("slabel");
const roleBadge = document.getElementById("role-badge");

// Colores por rol para identificación visual rápida
const ROLE_COLORS = {
  "MAESTRO_BAGO":          "#4fc3f7",  // cyan (default)
  "ANALISTA_Contexto":     "#81c784",  // verde
  "ARQUITECTO_Soluciones": "#ffb74d",  // naranja
  "GENERADOR_Contenido":   "#ce93d8",  // lila
  "ORGANIZADOR_Entregables":"#f48fb1", // rosa
  "GUIA_VERTICE":          "#ef5350",  // rojo
};

function setRoleBadge(name) {
  if (!roleBadge) return;
  roleBadge.textContent = name;
  roleBadge.style.background = ROLE_COLORS[name] || "#4fc3f7";
}

let history   = [];
let streaming = false;

// ── Status ────────────────────────────────────────────────────────────────
async function checkStatus() {
  try {
    const r = await fetch("/api/status");
    const d = await r.json();
    const ok = !d.llm_assist || d.mock || (d.ollama && d.model_available !== false);
    dot.className      = ok ? "dot ok" : "dot err";
    slabel.textContent = !d.llm_assist
      ? "modo canónico"
      : d.mock
        ? "🤖 mock"
        : (ok ? d.model : (d.ollama ? "sin modelo" : "Ollama no disponible"));
  } catch {
    dot.className = "dot err";
    slabel.textContent = "error";
  }
}
checkStatus();
setInterval(checkStatus, 8000);

// ── DOM helpers ───────────────────────────────────────────────────────────
function esc(s) {
  return s.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}
function scroll() { msgs.scrollTop = msgs.scrollHeight; }

function addMsg(cls, text) {
  const d = document.createElement("div");
  d.className = "msg " + cls;
  d.textContent = text;
  msgs.appendChild(d);
  scroll();
  return d;
}
function addTool(cmd, output) {
  const d = document.createElement("div");
  d.className = "msg tool";
  const text = String(output ?? "");
  const lines = text.split("\n").length;
  const collapsed = lines > 12;
  d.dataset.fullText = text;
  d.innerHTML = `
    <div class="tool-top">
      <div class="tool-hdr">⚙ bago ${esc(cmd)}</div>
      <div class="tool-actions">
        <button class="tool-btn secondary" data-action="copy">copiar</button>
        <button class="tool-btn secondary" data-action="edit">editar</button>
        ${collapsed ? '<button class="tool-btn" data-action="toggle">expandir</button>' : ''}
      </div>
    </div>
    <div class="tool-body">
      <pre class="tool-pre${collapsed ? ' collapsed' : ''}">${esc(text)}</pre>
    </div>
  `;
  msgs.appendChild(d);
  scroll();
  return d;
}

function focusInputWithText(text) {
  inp.value = text;
  inp.style.height = "auto";
  inp.style.height = Math.min(inp.scrollHeight, 120) + "px";
  inp.focus();
  inp.setSelectionRange(inp.value.length, inp.value.length);
}

function enterToolEditMode(toolEl) {
  const text = toolEl?.dataset?.fullText || "";
  if (!toolEl || toolEl.dataset.editing === "1") return;
  toolEl.dataset.editing = "1";
  toolEl.dataset.prevDraft = inp.value || "";

  const banner = document.createElement("div");
  banner.className = "tool-edit-banner";
  banner.innerHTML = `Editando salida para reenviar como mensaje tuyo. <button class="tool-btn" data-action="send-edited">enviar como mío</button> <button class="tool-btn secondary" data-action="cancel-edit">cancelar edición</button>`;
  toolEl.insertBefore(banner, toolEl.querySelector(".tool-body"));
  focusInputWithText(text);
}

function exitToolEditMode(toolEl) {
  if (!toolEl) return;
  toolEl.dataset.editing = "0";
  const banner = toolEl.querySelector(".tool-edit-banner");
  if (banner) banner.remove();
}

async function copyText(text, btn) {
  try {
    await navigator.clipboard.writeText(text);
    if (btn) {
      const old = btn.textContent;
      btn.textContent = "copiado";
      setTimeout(() => { btn.textContent = old; }, 1000);
    }
  } catch {
    if (btn) {
      const old = btn.textContent;
      btn.textContent = "falló";
      setTimeout(() => { btn.textContent = old; }, 1000);
    }
  }
}
function addTyping() {
  const d = document.createElement("div");
  d.className = "msg bot typing";
  d.innerHTML = "<span></span><span></span><span></span>";
  msgs.appendChild(d);
  scroll();
  return d;
}

// ── Render bot stream ──────────────────────────────────────────────────────
function createBotBubble() {
  const d = document.createElement("div");
  d.className = "msg bot";
  d.innerHTML = '<span class="cursor"></span>';
  msgs.appendChild(d);
  scroll();
  return d;
}
function appendToken(div, token) {
  const cur = div.querySelector(".cursor");
  div.insertBefore(document.createTextNode(token), cur);
  scroll();
}
function finalizeBubble(div) {
  const cur = div.querySelector(".cursor");
  if (cur) cur.remove();
}

// ── Direct BAGO command ────────────────────────────────────────────────────
async function runBagoCmd(cmd) {
  const indicator = addMsg("bot", `⚙ Ejecutando bago ${cmd}…`);
  try {
    const r   = await fetch("/api/bago", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cmd }),
    });
    const d   = await r.json();
    indicator.remove();
    addTool(cmd, d.output);
    history.push({ role: "user",      content: `/bago ${cmd}` });
    history.push({ role: "assistant", content: `[BAGO:${cmd}]\n${d.output}` });
  } catch (e) {
    indicator.textContent = "⚠ Error ejecutando comando: " + e.message;
  }
}

// ── Main send ─────────────────────────────────────────────────────────────
async function send() {
  const text = inp.value.trim();
  if (!text || streaming) return;
  inp.value = "";
  inp.style.height = "auto";

  // Direct BAGO command: /health, /ideas, etc.
  const directMatch = text.match(/^\/([a-z_-]+)$/i);
  if (directMatch) {
    addMsg("user", text);
    await runBagoCmd(directMatch[1].toLowerCase());
    return;
  }

  addMsg("user", text);
  history.push({ role: "user", content: text });

  streaming = true;
  sendBtn.disabled = true;
  const typing = addTyping();

  let botDiv = null;
  try {
    const resp = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ history }),
    });
    if (!resp.ok) throw new Error("HTTP " + resp.status);

    const reader    = resp.body.getReader();
    const dec       = new TextDecoder();
    let buf         = "";
    let fullText    = "";
    let toolOutputs = [];

    typing.remove();

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop();

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const data = line.slice(6).trim();
        if (data === "[DONE]") continue;
        let obj;
        try { obj = JSON.parse(data); } catch { continue; }

        if (obj.type === "token") {
          if (!botDiv) botDiv = createBotBubble();
          fullText += obj.content;
          appendToken(botDiv, obj.content);
        }
        if (obj.type === "role") {
          setRoleBadge(obj.name);
        }
        if (obj.type === "done") {
          const extra = toolOutputs.length ? "\n\n" + toolOutputs.join("\n\n") : "";
          history.push({ role: "assistant", content: obj.full_text + extra });
        }
        if (obj.type === "tool_result") {
          addTool(obj.cmd, obj.output);
          toolOutputs.push(`[BAGO:${obj.cmd}]\n${obj.output}`);
        }
      }
    }
  } catch (e) {
    typing.remove();
    history.pop();  // evitar mensaje de usuario huérfano en history
    addMsg("bot", "⚠ Error: " + e.message);
  } finally {
    if (botDiv) finalizeBubble(botDiv);  // siempre quitar cursor
  }

  streaming = false;
  sendBtn.disabled = false;
  inp.focus();
}

// ── Events ────────────────────────────────────────────────────────────────
sendBtn.addEventListener("click", send);
msgs.addEventListener("click", async (e) => {
  const btn = e.target.closest("[data-action]");
  if (!btn) return;

  const toolEl = btn.closest(".msg.tool");
  if (!toolEl) return;

  const action = btn.dataset.action;
  const fullText = toolEl.dataset.fullText || "";

  if (action === "toggle") {
    const pre = toolEl.querySelector(".tool-pre");
    if (!pre) return;
    const collapsed = pre.classList.toggle("collapsed");
    btn.textContent = collapsed ? "expandir" : "colapsar";
    scroll();
    return;
  }

  if (action === "copy") {
    await copyText(fullText, btn);
    return;
  }

  if (action === "edit") {
    enterToolEditMode(toolEl);
    return;
  }

  if (action === "cancel-edit") {
    if ((inp.value || "") === fullText) {
      focusInputWithText(toolEl.dataset.prevDraft || "");
    }
    exitToolEditMode(toolEl);
    return;
  }

  if (action === "send-edited") {
    exitToolEditMode(toolEl);
    if (!inp.value.trim()) {
      focusInputWithText(fullText);
      return;
    }
    await send();
  }
});
inp.addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
});
inp.addEventListener("input", () => {
  inp.style.height = "auto";
  inp.style.height = Math.min(inp.scrollHeight, 120) + "px";
});

// Bienvenida dinámica con contexto BAGO
(async () => {
  try {
    const r = await fetch("/api/context");
    const d = await r.json();
    const repo     = d.repo     || "BAGO_CAJAFISICA";
    const health   = d.health   || "?";
    const sessions = d.sessions || "?";
    const lastSes  = d.last_session  || "?";
    const lastWf   = d.last_workflow || "?";
    addMsg("bot",
      `¡Hola! Soy el asistente BAGO v${d.version || "2.5-stable"} con contexto cargado.\n` +
      `📂 Proyecto: ${repo}  ·  🔋 Health: ${health}  ·  Sesiones: ${sessions}\n` +
      `🕐 Última sesión: ${lastSes}  ·  Workflow: ${lastWf}\n\n` +
      `Usa /health /ideas /audit /dashboard /task /contexto para comandos directos.\n` +
      `La asistencia LLM está desactivada por defecto. Para activarla, arranca con --llm-assist.`
    );
  } catch {
    addMsg("bot",
      "¡Hola! Soy el asistente BAGO.\n" +
      "Usa /health, /ideas, /audit… para comandos BAGO directos."
    );
  }
})();
</script>
</body>
</html>"""


# ── HTTP Handler ──────────────────────────────────────────────────────────────

class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # silenciar logs HTTP

    # ── helpers ───────────────────────────────────────────────────────────────
    def _json(self, data: dict, code: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html: str):
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _sse(self, obj: dict):
        data = json.dumps(obj, ensure_ascii=False)
        self.wfile.write(f"data: {data}\n\n".encode())
        self.wfile.flush()

    def _read_body(self) -> dict | None:
        try:
            n = int(self.headers.get("Content-Length", 0))
            return json.loads(self.rfile.read(n)) if n else {}
        except (ValueError, json.JSONDecodeError):
            return None

    # ── GET ───────────────────────────────────────────────────────────────────
    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._html(HTML_PAGE)
        elif self.path == "/api/status":
            models = _available_models()
            self._json({
                "ollama":          _ollama_available(),
                "model":           _cfg["model"],
                "model_available": _model_matches(_cfg["model"], models),
                "llm_assist":      _cfg["llm_assist"],
                "tools":           _cfg["tools"],
                "roles":           _cfg["roles"],
                "mock":            _cfg["mock"],
            })
        elif self.path == "/api/context":
            self._json(_cfg.get("context_summary", {}))
        elif self.path == "/api/roles":
            available = [{"name": n, "desc": d} for n, d in ROLE_META.items()]
            self._json({"available": available, "active": _cfg["roles"]})
        else:
            self.send_response(404)
            self.end_headers()

    # ── POST ──────────────────────────────────────────────────────────────────
    def do_POST(self):
        body = self._read_body()
        if body is None:
            self._json({"error": "invalid request body"}, 400)
            return
        if self.path == "/api/chat":
            self._handle_chat(body)
        elif self.path == "/api/bago":
            cmd = body.get("cmd", "").strip()
            self._json({"output": _run_bago(cmd)})
        elif self.path == "/api/roles":
            requested = body.get("active", [])
            valid = [r for r in requested if r in ROLE_META][:MAX_ROLES]
            _cfg["roles"] = valid
            self._json({"active": _cfg["roles"]})
        else:
            self.send_response(404)
            self.end_headers()

    def _handle_chat(self, body: dict):
        raw = body.get("history", [])
        history = [
            h for h in (raw if isinstance(raw, list) else [])
            if isinstance(h, dict)
            and h.get("role") in ("user", "assistant")
            and isinstance(h.get("content"), str)
        ]
        # Detectar rol basado en el último mensaje del usuario
        last_user_msg = next(
            (h["content"] for h in reversed(history) if h.get("role") == "user"), ""
        )
        active_role = _detect_role(last_user_msg) if not _cfg.get("roles") else (
            _cfg["roles"][0] if _cfg["roles"] else "MAESTRO_BAGO"
        )
        messages = [{"role": "system", "content": _build_system_prompt(last_user_msg)}] + history

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()

        # Emitir el rol activo para que la UI lo muestre
        self._sse({"type": "role", "name": active_role})

        full_text = ""
        try:
            if not _cfg["llm_assist"]:
                gen = _stream_safe_reply(last_user_msg)
            elif _cfg["mock"]:
                gen = _stream_mock(messages)
            else:
                gen = _stream_ollama(messages)
            for token in gen:
                full_text += token
                self._sse({"type": "token", "content": token})
        except (BrokenPipeError, ConnectionResetError):
            return
        except urllib.error.URLError:
            msg = (
                "\n⚠ No se pudo conectar con Ollama. "
                "¿Está corriendo? (`ollama serve`)"
            )
            self._sse({"type": "token", "content": msg})
            full_text += msg
        except RuntimeError as e:
            msg = f"\n{e}"
            self._sse({"type": "token", "content": msg})
            full_text += msg
        except Exception as e:
            msg = f"\n⚠ Error inesperado: {e}"
            self._sse({"type": "token", "content": msg})
            full_text += msg

        self._sse({"type": "done", "full_text": full_text})

        # Ejecutar comandos BAGO que el LLM haya emitido en su respuesta
        if _cfg["tools"] and _cfg["llm_assist"]:
            seen: set[str] = set()
            for cmd in BAGO_CMD_RE.findall(full_text):
                if cmd in ALLOWED_BAGO_CMDS and cmd not in seen:
                    seen.add(cmd)
                    output = _run_bago(cmd)
                    try:
                        self._sse({"type": "tool_result", "cmd": cmd, "output": output})
                    except (BrokenPipeError, ConnectionResetError):
                        return

        try:
            self.wfile.write(b"data: [DONE]\n\n")
            self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError):
            pass



# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port",       type=int, default=DEFAULT_PORT)
    p.add_argument("--model",      default=DEFAULT_MODEL)
    p.add_argument("--llm-assist", action="store_true",
                   help="Habilita asistencia LLM opcional; desactivada por defecto")
    p.add_argument("--no-browser", action="store_true")
    p.add_argument("--no-tools",   action="store_true")
    p.add_argument("--mock",       action="store_true",
                   help="Modo demo: respuestas de prueba sin LLM")
    args, _ = p.parse_known_args()

    _cfg["model"]  = args.model
    _cfg["tools"]  = not args.no_tools
    _cfg["port"]   = args.port
    _cfg["llm_assist"] = args.llm_assist
    _cfg["mock"]   = args.mock

    # Cargar contexto BAGO al inicio
    ctx_str, ctx_summary = _load_bago_context()
    _cfg["bago_context"]    = ctx_str
    _cfg["context_summary"] = ctx_summary

    url = f"http://localhost:{args.port}"

    print()
    print("  ╔══════════════════════════════════════════╗")
    print("  ║  BAGO Chat  ·  plano canónico primero    ║")
    print("  ╚══════════════════════════════════════════╝")
    print(f"  Modelo : {args.model}")
    print(f"  Tools  : {'✅ activados' if _cfg['tools'] else '❌ desactivados'}")
    if not _cfg["llm_assist"]:
        print("  LLM    : ❌ desactivado (modo canónico por defecto)")
    else:
        print(f"  LLM    : {'🤖 MOCK (sin Ollama real)' if _cfg['mock'] else '🧠 habilitado por --llm-assist'}")
    if ctx_summary.get("context_loaded"):
        print(f"  Proyecto: {ctx_summary.get('repo', '?')}  ·  "
              f"Health: {ctx_summary.get('health', '?')}  ·  "
              f"Sesiones: {ctx_summary.get('sessions', '?')}")
    print(f"  URL    : {url}")
    print()

    if _cfg["llm_assist"] and not args.mock:
        if not _ollama_available():
            print("  ⚠  Ollama no responde en localhost:11434")
            print("     Inícialo con:  ollama serve")
            print("     O usa --mock para modo demo sin LLM.")
            print()
        else:
            models = _available_models()
            if not models:
                print(f"  ⚠  Ollama activo pero sin modelos descargados.")
                print(f"     Descarga uno:  ollama pull {args.model}")
                print(f"     O usa --mock para modo demo sin LLM.")
                print()
            elif not _model_matches(args.model, models):
                print(f"  ⚠  Modelo '{args.model}' no encontrado.")
                print(f"     Modelos disponibles: {', '.join(models)}")
                print(f"     Descárgalo:  ollama pull {args.model}")
                print()
            else:
                print(f"  ✅ Ollama listo · modelo: {args.model}")
                print()
    elif not _cfg["llm_assist"]:
        print("  Política: el chat no usa LLM salvo opt-in explícito con --llm-assist")
        print()

    server = ThreadingHTTPServer(("localhost", args.port), Handler)

    if not args.no_browser:
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()

    print("  Ctrl+C para detener\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  BAGO Chat detenido.")


if __name__ == "__main__":
    main()
