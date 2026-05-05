#!/bin/bash
# ─────────────────────────────────────────────────────────────────
#  BAGO.command — macOS: doble clic en Finder para abrir BAGO Shell
#  El archivo .command hace que Terminal.app lo abra automáticamente.
# ─────────────────────────────────────────────────────────────────
cd "$(dirname "$0")"

# Verificar Python
if ! command -v python3 &>/dev/null; then
    echo "❌  Python3 no encontrado. Instálalo desde https://python.org"
    read -p "Pulsa Enter para salir..."
    exit 1
fi

clear
python3 bago
