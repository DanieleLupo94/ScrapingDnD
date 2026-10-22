"""
Legge uno screenshot D&D con Llama 3.2 Vision via mlx-vlm (Apple Silicon nativo).

Uso:
    python read_image.py --image screenshots/Power/power6965.png
    python read_image.py --model mlx-community/Llama-3.2-11B-Vision-Instruct-4bit --image ...

Il modello viene scaricato automaticamente da HuggingFace la prima volta (~6 GB).
"""
from __future__ import annotations

import argparse

from mlx_vlm import load, generate
from mlx_vlm.prompt_utils import apply_chat_template
from mlx_vlm.utils import load_config

DEFAULT_MODEL = "mlx-community/Llama-3.2-11B-Vision-Instruct-4bit"

PROMPT = (
    "This is a D&D 4th edition compendium card. "
    "Extract all the text and return it as structured JSON with keys: "
    "name, category, flavor_text, keywords, action_type, target, attack, hit, source. "
    "Return only the JSON, no explanation."
)


def read_card(model_path: str, image_path: str) -> str:
    print(f"Caricamento modello: {model_path}")
    model, processor = load(model_path)
    config = load_config(model_path)

    formatted = apply_chat_template(
        processor,
        config,
        PROMPT,
        num_images=1,
    )

    result = generate(
        model,
        processor,
        image=image_path,
        prompt=formatted,
        max_tokens=512,
        temperature=0.1,
        verbose=False,
    )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Modello HuggingFace o path locale")
    parser.add_argument("--image", required=True, help="Path all'immagine PNG")
    args = parser.parse_args()

    result = read_card(args.model, args.image)
    print(result)
