#!/bin/zsh
# perchance_keyboard_submit.sh — Envia 32 prompts al generador web de Perchance
# via automatización de teclado (AppleScript + osascript)
# BAGO v3.0 · Bianca The Game · char_girl_walk pipeline
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
CSV_DEFAULT="${SCRIPT_DIR}/char_girl_walk_prompts_32_from_txt.csv"
TXT_DEFAULT="/Volumes/Warehouse/Bianca_The_Game/release/bianca_motor_compilado_20260226_204315/assets/sprites/char_girl_walk_prompts_32.txt"
SCRIPT_NAME="${0:t}"
PERCHANCE_URL="https://perchance.org/y06fzf5rev"
AUTO_MODE=0
WAIT_SECONDS=12
FROM_FRAME=0
OVERRIDE_INPUT=""

print_help() {
  echo "Uso: $SCRIPT_NAME [opciones]"
  echo ""
  echo "Opciones:"
  echo "  --auto            Modo automático (no espera ENTER entre frames)"
  echo "  --wait N          Segundos entre envíos en modo auto (default: 12)"
  echo "  --from N          Empezar desde frame N (default: 0)"
  echo "  --input PATH      Ruta al archivo de prompts (.csv o .txt)"
  echo "  --url URL         URL de Perchance (default: $PERCHANCE_URL)"
  echo "  --help, -h        Muestra esta ayuda"
  echo ""
  echo "Fuentes de prompts (por prioridad):"
  echo "  1. --input especificado explícitamente"
  echo "  2. CSV local: $CSV_DEFAULT"
  echo "  3. TXT en volumen: $TXT_DEFAULT"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --auto)         AUTO_MODE=1 ;;
    --wait)         shift; WAIT_SECONDS="${1:?--wait requiere un número}" ;;
    --from)         shift; FROM_FRAME="${1:?--from requiere un número}" ;;
    --input)        shift; OVERRIDE_INPUT="${1:?--input requiere una ruta}" ;;
    --url)          shift; PERCHANCE_URL="${1:?--url requiere una URL}" ;;
    --help|-h)      print_help; exit 0 ;;
    *)              echo "ERROR: Opción desconocida: $1" >&2; print_help; exit 1 ;;
  esac
  shift
done

# Selección de fuente de prompts
if [[ -n "$OVERRIDE_INPUT" ]]; then
  INPUT_PATH="$OVERRIDE_INPUT"
elif [[ -f "$CSV_DEFAULT" ]]; then
  INPUT_PATH="$CSV_DEFAULT"
elif [[ -f "$TXT_DEFAULT" ]]; then
  INPUT_PATH="$TXT_DEFAULT"
else
  echo "ERROR: No se encontró archivo de prompts." >&2
  echo "  CSV local: $CSV_DEFAULT (no existe)" >&2
  echo "  TXT volumen: $TXT_DEFAULT (no existe)" >&2
  echo "  Usa --input para especificar la ruta." >&2
  exit 1
fi

if ! command -v osascript >/dev/null 2>&1; then
  echo "ERROR: osascript no disponible (¿estás en macOS?)" >&2; exit 1
fi
if ! command -v pbcopy >/dev/null 2>&1; then
  echo "ERROR: pbcopy no disponible (¿estás en macOS?)" >&2; exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 no disponible" >&2; exit 1
fi

echo "Fuente: $INPUT_PATH"
echo "URL: $PERCHANCE_URL"
[[ "$FROM_FRAME" -gt 0 ]] && echo "Comenzando desde frame $FROM_FRAME"

TMP_PROMPTS="$(mktemp /tmp/bago_perchance_XXXXXX.tsv)"
trap 'rm -f "$TMP_PROMPTS"' EXIT

# Normaliza CSV o TXT a TSV interno: idx\tprompt (una línea por frame)
python3 - "$INPUT_PATH" "$TMP_PROMPTS" "$FROM_FRAME" <<'PY'
import csv, re, sys
from pathlib import Path

src = Path(sys.argv[1])
out = Path(sys.argv[2])
skip_before = int(sys.argv[3]) if len(sys.argv) > 3 else 0
text = src.read_text(encoding='utf-8')
rows = []

# Detecta formato por extensión o contenido
if src.suffix.lower() == '.csv' or 'frame_index' in text[:200]:
    reader = csv.DictReader(text.splitlines())
    for row in reader:
        idx = int(row['frame_index'])
        prompt = row['prompt'].strip().replace('\r\n', '\n').replace('\r', '\n')
        rows.append((idx, prompt))
else:
    # Formato .txt con bloques [frame_XX]
    parts = re.split(r'(?=\[frame_\d{2}\])', text)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        m = re.match(r'\[frame_(\d{2})\][^\n]*\n(.*)', part, flags=re.S)
        if not m:
            continue
        idx = int(m.group(1))
        prompt = m.group(2).strip().replace('\r\n', '\n').replace('\r', '\n')
        rows.append((idx, prompt))

rows.sort(key=lambda x: x[0])
if not rows:
    raise SystemExit('ERROR: No se encontraron prompts en el archivo')

filtered = [(i, p) for i, p in rows if i >= skip_before]
with out.open('w', encoding='utf-8') as f:
    for idx, p in filtered:
        f.write(f"{idx:02d}\t{p.replace(chr(10), chr(92) + 'n')}\n")

total = len(filtered)
print(f'OK: {total} prompts listos (de {len(rows)} total, skip_before={skip_before})')
PY

TOTAL=$(wc -l < "$TMP_PROMPTS" | tr -d ' ')
echo ""
echo "═══════════════════════════════════════════════"
echo "  Perchance Keyboard Submit — $TOTAL frames"
echo "═══════════════════════════════════════════════"
echo ""
echo "1. Abre esta URL en Chrome o Safari:"
echo "   $PERCHANCE_URL"
echo "2. Haz click dentro del campo de texto del generador."
echo ""
if [[ "$AUTO_MODE" -eq 1 ]]; then
  echo "Modo AUTO: comenzando en 5 segundos. Cambia al navegador ahora."
  sleep 5
else
  echo "Cuando estés listo en el navegador, vuelve aquí y presiona ENTER."
  read -r _ </dev/tty
fi

count=0
failed=()

exec 3< "$TMP_PROMPTS"
while IFS=$'\t' read -r idx prompt_escaped <&3; do
  prompt="${prompt_escaped//\\n/$'\n'}"
  count=$((count + 1))

  # Copia al clipboard
  printf "%s" "$prompt" | pbcopy

  # Activa el navegador (Chrome primero, luego Safari, luego primer navegador disponible)
  osascript 2>/dev/null <<'OSA' || true
try
  tell application "Google Chrome" to activate
on error
  try
    tell application "Safari" to activate
  on error
    try
      tell application "Firefox" to activate
    end try
  end try
end try
OSA

  sleep 0.3

  # Selecciona todo, pega el prompt y pulsa Enter
  if ! osascript 2>/dev/null <<'OSA'; then
tell application "System Events"
  key code 0 using {command down}
  delay 0.05
  keystroke "v" using {command down}
  delay 0.1
  key code 36
end tell
OSA
    echo "  [WARN] Error de AppleScript en frame_${idx} — continuando" >&2
    failed+=("$idx")
  fi

  echo "[$count/$TOTAL] frame_${idx} enviado."

  if [[ "$AUTO_MODE" -eq 1 ]]; then
    if [[ "$count" -lt "$TOTAL" ]]; then
      echo "  Esperando ${WAIT_SECONDS}s..."
      sleep "$WAIT_SECONDS"
    fi
  else
    echo "  Guarda la imagen. ENTER = siguiente | q = salir | s = saltar"
    read -r ans </dev/tty
    case "${ans:l}" in
      q|quit|exit) echo "Parado por usuario en frame_${idx}."; exec 3<&-; exit 0 ;;
      s|skip)      echo "  [SKIP] frame_${idx} omitido por usuario." ;;
      *)           ;;
    esac
  fi

done
exec 3<&-

echo ""
echo "═══════════════════════════════════════════════"
if [[ ${#failed[@]} -eq 0 ]]; then
  echo "  ✓ Completado: $count/$TOTAL prompts enviados."
else
  echo "  ⚠ Completado con advertencias: ${#failed[@]} frames con error AppleScript."
  echo "  Frames con error: ${failed[*]}"
fi
echo "═══════════════════════════════════════════════"
