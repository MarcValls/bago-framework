#!/bin/zsh
set -euo pipefail

CSV="/Users/INTELIA_Manager/Desktop/BAGO_CAJAFISICA/TEST_BAGO_03(IMG)/char_girl_walk_prompts_32_from_txt.csv"
OUT_DIR="/Users/INTELIA_Manager/Desktop/BAGO_CAJAFISICA/TEST_BAGO_03(IMG)"
GEN="/Volumes/Warehouse/Bianca_The_Game/release/bianca_motor_compilado_20260226_204315/assets/sprites/generate_frames_openai.py"

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "ERROR: OPENAI_API_KEY no está configurada"
  exit 1
fi

for i in {0..31}; do
  echo "[${i}/31] Generando frame_${(l:2::0:)i}.png"
  python3 "$GEN" generate-one \
    --index "$i" \
    --csv "$CSV" \
    --frames-dir "$OUT_DIR" \
    --model gpt-image-1 \
    --size 1024x1024 \
    --quality high \
    --background transparent

done

echo "OK: 32 frames generados en $OUT_DIR"
