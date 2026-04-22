#!/usr/bin/env python3
"""
generate_frames_openai.py — Sprite frame generator via OpenAI Images API
Bianca The Game · char_girl_walk pipeline · BAGO v3.0

Usage:
  python3 generate_frames_openai.py generate-one \\
    --index 0 --csv prompts.csv --frames-dir ./out \\
    --model gpt-image-1 --size 1024x1024 --quality high --background transparent

  python3 generate_frames_openai.py generate-all \\
    --csv prompts.csv --frames-dir ./out \\
    --model gpt-image-1 --size 1024x1024 --quality high --background transparent \\
    [--retry 3] [--delay 2]

  python3 generate_frames_openai.py validate --frames-dir ./out
"""

import argparse
import base64
import csv
import os
import sys
import time
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package no instalado. Ejecuta: pip install openai", file=sys.stderr)
    sys.exit(1)


def load_prompts(csv_path: str) -> dict[int, str]:
    """Carga el CSV de prompts → {frame_index: prompt_text}"""
    path = Path(csv_path)
    if not path.exists():
        print(f"ERROR: CSV no encontrado: {csv_path}", file=sys.stderr)
        sys.exit(1)
    prompts = {}
    with path.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            idx = int(row["frame_index"])
            prompts[idx] = row["prompt"]
    return prompts


def generate_one(
    client: OpenAI,
    index: int,
    prompt: str,
    frames_dir: Path,
    model: str,
    size: str,
    quality: str,
    background: str,
    retry: int = 3,
    delay: float = 2.0,
) -> Path:
    """Genera un frame y lo guarda como PNG. Retorna la ruta del archivo."""
    out_path = frames_dir / f"frame_{index:02d}.png"
    if out_path.exists():
        print(f"  [SKIP] {out_path.name} ya existe.")
        return out_path

    kwargs = dict(
        model=model,
        prompt=prompt,
        n=1,
        size=size,
    )
    if model == "gpt-image-1":
        kwargs["quality"] = quality
        kwargs["output_format"] = "png"
        if background == "transparent":
            kwargs["background"] = "transparent"
    else:
        kwargs["response_format"] = "b64_json"

    for attempt in range(1, retry + 1):
        try:
            response = client.images.generate(**kwargs)
            image_data = response.data[0]

            if hasattr(image_data, "b64_json") and image_data.b64_json:
                png_bytes = base64.b64decode(image_data.b64_json)
            elif hasattr(image_data, "url") and image_data.url:
                import urllib.request
                with urllib.request.urlopen(image_data.url) as r:
                    png_bytes = r.read()
            else:
                raise ValueError("Respuesta API sin imagen válida")

            frames_dir.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(png_bytes)
            print(f"  [OK] {out_path.name} guardado ({len(png_bytes):,} bytes)")
            return out_path

        except Exception as e:
            print(f"  [WARN] Intento {attempt}/{retry} fallido: {e}", file=sys.stderr)
            if attempt < retry:
                time.sleep(delay * attempt)
            else:
                print(f"  [ERROR] frame_{index:02d} fallido después de {retry} intentos.", file=sys.stderr)
                raise

    return out_path


def cmd_generate_one(args: argparse.Namespace) -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY no está configurada.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    prompts = load_prompts(args.csv)

    if args.index not in prompts:
        print(f"ERROR: frame_index {args.index} no encontrado en CSV (disponibles: {sorted(prompts.keys())})", file=sys.stderr)
        sys.exit(1)

    frames_dir = Path(args.frames_dir)
    generate_one(
        client=client,
        index=args.index,
        prompt=prompts[args.index],
        frames_dir=frames_dir,
        model=args.model,
        size=args.size,
        quality=args.quality,
        background=args.background,
        retry=args.retry,
        delay=args.delay,
    )


def cmd_generate_all(args: argparse.Namespace) -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY no está configurada.", file=sys.stderr)
        sys.exit(1)

    client = OpenAI(api_key=api_key)
    prompts = load_prompts(args.csv)
    frames_dir = Path(args.frames_dir)
    total = len(prompts)
    failed = []

    print(f"Generando {total} frames en {frames_dir}/")
    for i, (idx, prompt) in enumerate(sorted(prompts.items()), 1):
        print(f"[{i}/{total}] frame_{idx:02d}...")
        try:
            generate_one(
                client=client,
                index=idx,
                prompt=prompt,
                frames_dir=frames_dir,
                model=args.model,
                size=args.size,
                quality=args.quality,
                background=args.background,
                retry=args.retry,
                delay=args.delay,
            )
        except Exception:
            failed.append(idx)

    print(f"\n{'OK' if not failed else 'PARTIAL'}: {total - len(failed)}/{total} frames generados.")
    if failed:
        print(f"  Fallidos: {[f'frame_{i:02d}' for i in failed]}", file=sys.stderr)
        sys.exit(1)


def cmd_validate(args: argparse.Namespace) -> None:
    frames_dir = Path(args.frames_dir)
    missing = []
    present = []
    for i in range(32):
        p = frames_dir / f"frame_{i:02d}.png"
        if p.exists():
            size = p.stat().st_size
            present.append(f"frame_{i:02d}.png ({size:,}B)")
        else:
            missing.append(f"frame_{i:02d}.png")

    print(f"Validación en {frames_dir}/")
    print(f"  Presentes : {len(present)}/32")
    if missing:
        print(f"  Faltantes : {len(missing)}/32")
        for m in missing:
            print(f"    - {m}")
        sys.exit(1)
    else:
        print("  ✓ Los 32 frames están presentes.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generador de sprite frames via OpenAI Images API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--csv", required=True, help="Ruta al CSV de prompts")
    shared.add_argument("--frames-dir", required=True, help="Directorio de salida para PNGs")
    shared.add_argument("--model", default="gpt-image-1", help="Modelo OpenAI (default: gpt-image-1)")
    shared.add_argument("--size", default="1024x1024", help="Tamaño imagen (default: 1024x1024)")
    shared.add_argument("--quality", default="high", help="Calidad imagen (default: high)")
    shared.add_argument("--background", default="transparent", help="Fondo (default: transparent)")
    shared.add_argument("--retry", type=int, default=3, help="Reintentos por frame (default: 3)")
    shared.add_argument("--delay", type=float, default=2.0, help="Delay base entre reintentos en s (default: 2.0)")

    p_one = sub.add_parser("generate-one", parents=[shared], help="Genera un único frame")
    p_one.add_argument("--index", type=int, required=True, help="Índice del frame (0-31)")

    sub.add_parser("generate-all", parents=[shared], help="Genera todos los frames del CSV")

    p_val = sub.add_parser("validate", help="Valida que los 32 frames existan")
    p_val.add_argument("--frames-dir", required=True, help="Directorio con los PNGs")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    dispatch = {
        "generate-one": cmd_generate_one,
        "generate-all": cmd_generate_all,
        "validate": cmd_validate,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
