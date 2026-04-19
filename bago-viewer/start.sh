#!/bin/bash
cd "$(dirname "$0")"
echo ""
echo "  BAGO Viewer → http://localhost:5050"
echo "  Ctrl+C para detener"
echo ""
# < /dev/null evita "Bad file descriptor" en sys.stdin cuando se llama sin terminal
exec python3 app.py < /dev/null
