import argparse
import json
from pathlib import Path


DEFAULT_SPECS_FILE = Path("map_pipeline/data/city_cluster_glyph_specs.json")


def load_specs(path: Path = DEFAULT_SPECS_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def city_ids(specs: dict, status: str | None = None) -> list[str]:
    cities = specs["cities"]
    if status:
        cities = [city for city in cities if city["status"] == status]
    return [city["id"] for city in cities]


def planned_city_ids(specs: dict) -> list[str]:
    return city_ids(specs, "planned_cluster")


def prompt_for_city(specs: dict, city_id: str) -> str:
    style_reference = specs["style_reference"]
    city = next(city for city in specs["cities"] if city["id"] == city_id)
    elements = "; ".join(city["cluster_elements"])
    return "\n".join(
        [
            "Use case: stylized-concept",
            "Asset type: high-resolution transparent-source city cluster glyph for a Godot 16-bit RPG atlas map UI",
            f"Primary request: Create one {city['display_name']} multi-symbol city cluster glyph. {city['prompt_spec']}",
            f"Landmark elements: {elements}.",
            f"Style reference: {style_reference}",
            "Composition/framing: one centered compact cluster, generous transparent-ready padding, stable visual mass, no frame, no labels.",
            "Background: perfectly flat solid #ff00ff chroma-key background for background removal. The background must be one uniform color with no shadows, gradients, texture, reflections, floor plane, or lighting variation. Do not use #ff00ff anywhere in the icon.",
            "Constraints: 2-4 recognizable city elements, simplified readable silhouettes, avoid ultra-fine detail and tiny texture noise, clean at user zoom 300%, icon must not be cropped.",
            "Avoid: text, letters, city names, flags, watermark, photorealism, flat vector app icon style, mixed styles, large drop shadows, map background, decorative frame, one-symbol-only city.",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect planned multi-symbol city cluster glyph specs.")
    parser.add_argument("--specs-file", type=Path, default=DEFAULT_SPECS_FILE)
    parser.add_argument("--status", choices=["existing_cluster", "planned_cluster"], default=None)
    parser.add_argument("--prompts", action="store_true", help="Print image-generation prompts instead of ids.")
    args = parser.parse_args()

    specs = load_specs(args.specs_file)
    ids = city_ids(specs, args.status)
    if args.prompts:
        for city_id in ids:
            print(f"--- {city_id} ---")
            print(prompt_for_city(specs, city_id))
            print()
    else:
        for city_id in ids:
            print(city_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
