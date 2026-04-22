#!/bin/zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
CSV="${SCRIPT_DIR}/char_girl_walk_prompts_32_from_txt.csv"
OUT_DIR="${SCRIPT_DIR}"
GEN="${SCRIPT_DIR}/generate_frames_openai.py"
MODEL="${MODEL:-gpt-image-1}"
SIZE="${SIZE:-1024x1024}"
QUALITY="${QUALITY:-high}"
RETRY="${RETRY:-3}"
BATCH=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --batch)       BATCH=1 ;;
    --model)       shift; MODEL="$1" ;;
    --size)        shift; SIZE="$1" ;;
    --quality)     shift; QUALITY="$1" ;;
    --out-dir)     shift; OUT_DIR="$1" ;;
    --retry)       shift; RETRY="$1" ;;
    --help|-h)
      echo "Uso: $0 [--batch] [--model MODEL] [--size SIZExSIZE] [--quality QUALITY] [--out-dir DIR] [--retry N]"
      echo ""
      echo "  --batch    Usa generate-all (un solo llamado, más eficiente)"
      echo "  --model    Modelo OpenAI (default: gpt-image-1)"
      echo "  --size     Tamaño imagen (default: 1024x1024)"
      echo "  --quality  Calidad (default: high)"
      echo "  --out-dir  Directorio de salida (default: directorio del script)"
      echo "  --retry    Reintentos por frame (default: 3)"
      exit 0
      ;;
    *) echo "Opción desconocida: $1" >&2; exit 1 ;;
  esac
  shift
done

if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "ERROR: OPENAI_API_KEY no está configurada."
  echo "       Exporta con: export OPENAI_API_KEY='sk-...'"
  exit 1
fi

if [[ ! -f "$GEN" ]]; then
  echo "ERROR: generate_frames_openai.py no encontrado en $SCRIPT_DIR"
  exit 1
fi

if [[ ! -f "$CSV" ]]; then
  echo "ERROR: CSV no encontrado: $CSV"
  exit 1
fi

mkdir -p "$OUT_DIR"

if [[ "$BATCH" -eq 1 ]]; then
  echo "Modo batch — generando todos los frames en un solo comando..."
  python3 "$GEN" generate-all \
    --csv "$CSV" \
    --frames-dir "$OUT_DIR" \
    --model "$MODEL" \
    --size "$SIZE" \
    --quality "$QUALITY" \
    --background transparent \
    --retry "$RETRY"
else
  for i in {0..31}; do
    echo "[${i}/31] Generando frame_${(l:2::0:)i}.png"
    python3 "$GEN" generate-one \
      --index "$i" \
      --csv "$CSV" \
      --frames-dir "$OUT_DIR" \
      --model "$MODEL" \
      --size "$SIZE" \
      --quality "$QUALITY" \
      --background transparent \
      --retry "$RETRY"
  done
fi

echo ""
echo "Validando frames generados..."
python3 "$GEN" validate --frames-dir "$OUT_DIR"
echo "OK: Pipeline completado. Frames en: $OUT_DIR"
