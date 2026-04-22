#!/bin/zsh
set -euo pipefail

TXT_DEFAULT="/Volumes/Warehouse/Bianca_The_Game/release/bianca_motor_compilado_20260226_204315/assets/sprites/char_girl_walk_prompts_32.txt"
TXT_PATH="$TXT_DEFAULT"
AUTO_MODE=0
WAIT_SECONDS=12

while [[ $# -gt 0 ]]; do
  case "$1" in
    --auto) AUTO_MODE=1 ;;
    --wait) shift; WAIT_SECONDS="${1:-12}" ;;
    *) TXT_PATH="$1" ;;
  esac
  shift
done

if [[ ! -f "$TXT_PATH" ]]; then
  echo "ERROR: no existe archivo de prompts: $TXT_PATH"
  exit 1
fi

if ! command -v osascript >/dev/null 2>&1; then
  echo "ERROR: osascript no disponible"
  exit 1
fi

if ! command -v pbcopy >/dev/null 2>&1; then
  echo "ERROR: pbcopy no disponible"
  exit 1
fi

TMP_PROMPTS="$(mktemp)"
trap 'rm -f "$TMP_PROMPTS"' EXIT

python3 - "$TXT_PATH" "$TMP_PROMPTS" <<'PY'
from pathlib import Path
import re,sys
src=Path(sys.argv[1])
out=Path(sys.argv[2])
text=src.read_text(encoding='utf-8')
parts=re.split(r'(?=\[frame_\d{2}\])', text)
rows=[]
for part in parts:
    part=part.strip()
    if not part:
        continue
    m=re.match(r'\[frame_(\d{2})\][^\n]*\n(.*)', part, flags=re.S)
    if not m:
        continue
    idx=int(m.group(1))
    prompt=m.group(2).strip().replace('\r\n','\n').replace('\r','\n')
    rows.append((idx,prompt))
rows.sort(key=lambda x:x[0])
if len(rows)!=32:
    raise SystemExit(f'Expected 32 prompts, got {len(rows)}')
with out.open('w',encoding='utf-8') as f:
    for idx,p in rows:
        f.write(f"{idx:02d}\t{p.replace(chr(10),'\\n')}\n")
print('OK', len(rows))
PY

echo
echo "Abre Perchance en tu navegador y haz click dentro del campo de prompt."
echo "URL sugerida: https://perchance.org/y06fzf5rev"
if [[ "$AUTO_MODE" -eq 1 ]]; then
  echo "Modo AUTO activo: inicio en 3 segundos..."
  sleep 3
else
  echo "Luego vuelve aquí y presiona ENTER para comenzar."
  read -r _ </dev/tty
fi

count=0
exec 3< "$TMP_PROMPTS"
while IFS=$'\t' read -r idx prompt_escaped <&3; do
  prompt="${prompt_escaped//\\n/$'\n'}"
  printf "%s" "$prompt" | pbcopy

  osascript <<'OSA'
try
  tell application "Google Chrome" to activate
on error
  try
    tell application "Safari" to activate
  end try
end try
OSA

  sleep 0.2
  osascript <<'OSA'
tell application "System Events"
  keystroke "a" using {command down}
  keystroke "v" using {command down}
  key code 36
end tell
OSA

  count=$((count+1))
  echo "[$count/32] frame_$idx enviado."
  if [[ "$AUTO_MODE" -eq 1 ]]; then
    echo "AUTO: esperando ${WAIT_SECONDS}s antes del siguiente..."
    sleep "$WAIT_SECONDS"
  else
    echo "Guarda la imagen y vuelve aquí. ENTER = siguiente | q = salir"
    read -r ans </dev/tty
    if [[ "${ans:l}" == "q" ]]; then
      echo "Parado por usuario en frame_$idx"
      exit 0
    fi
  fi

done
exec 3<&-

echo "Completado: 32 prompts enviados al navegador."
