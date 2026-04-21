#!/bin/bash
# ── BAGO·Viewer Launcher ──────────────────────────────
# Doble clic en Finder para iniciar el servidor y abrir el menu

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PORT=5050

echo ""
echo "  ╔══════════════════════════════════╗"
echo "  ║       BAGO·Viewer Launcher       ║"
echo "  ╚══════════════════════════════════╝"
echo ""

# Check if port is already in use
if lsof -i :$PORT -sTCP:LISTEN -t &>/dev/null 2>&1; then
  echo "  ✅ Servidor ya activo en http://localhost:$PORT"
  echo "  → Abriendo menú en el navegador…"
  open "http://localhost:$PORT/"
  exit 0
fi

echo "  ▶  Iniciando servidor en puerto $PORT…"
echo "  📂 Directorio: $SCRIPT_DIR"
echo ""

# Start server in background
cd "$SCRIPT_DIR"
python3 bago-viewer/app.py &
SERVER_PID=$!

# Wait for server to be ready
echo "  ⏳ Esperando que el servidor arranque…"
for i in {1..20}; do
  sleep 0.5
  if curl -s "http://localhost:$PORT/" &>/dev/null; then
    echo "  ✅ Servidor listo en http://localhost:$PORT (PID: $SERVER_PID)"
    echo ""
    echo "  → Abriendo menú en el navegador…"
    open "http://localhost:$PORT/"
    echo ""
    echo "  [Cierra esta ventana para detener el servidor]"
    wait $SERVER_PID
    exit 0
  fi
done

echo "  ❌ No se pudo conectar al servidor. Revisa la consola."
wait $SERVER_PID
