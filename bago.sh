#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────
#  bago.sh — Linux / Android (Termux) / sistemas Unix generales
#  Ejecuta: bash bago.sh   o   ./bago.sh   o doble clic en gestor
# ─────────────────────────────────────────────────────────────────
set -euo pipefail
DRIVE="$(cd "$(dirname "$0")" && pwd)"
cd "$DRIVE"

# Verificar Python
PY=""
for cmd in python3 python; do
    command -v "$cmd" &>/dev/null && PY="$cmd" && break
done
if [ -z "$PY" ]; then
    echo "❌  Python3 no encontrado. Instálalo con tu gestor de paquetes."
    exit 1
fi

# ── Android / Termux ─────────────────────────────────────────────
if [ -n "${TERMUX_VERSION:-}" ]; then
    # Ya estamos en el terminal correcto
    exec "$PY" bago "$@"
fi

# ── macOS ─────────────────────────────────────────────────────────
if [ "$(uname)" = "Darwin" ]; then
    # Prefiere abrir en terminal si no hay TTY
    if [ ! -t 0 ]; then
        open -a Terminal "$DRIVE/BAGO.command"
        exit 0
    fi
    exec "$PY" bago "$@"
fi

# ── Linux — busca emulador de terminal disponible ─────────────────
if [ ! -t 0 ]; then
    for term in gnome-terminal kitty alacritty xterm konsole xfce4-terminal; do
        if command -v "$term" &>/dev/null; then
            case "$term" in
                gnome-terminal) $term -- bash -c "cd '$DRIVE' && $PY bago; exec bash" & ;;
                kitty|alacritty) $term bash -c "cd '$DRIVE' && $PY bago; exec bash" & ;;
                *)               $term -e bash -c "cd '$DRIVE' && $PY bago; exec bash" & ;;
            esac
            exit 0
        fi
    done
    echo "Ningún emulador de terminal detectado. Ejecuta manualmente: cd '$DRIVE' && $PY bago"
    exit 1
fi

exec "$PY" bago "$@"
