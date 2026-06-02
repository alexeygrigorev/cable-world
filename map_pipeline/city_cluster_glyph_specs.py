import argparse
import json
from pathlib import Path


DEFAULT_SPECS_FILE = Path("map_pipeline/data/city_cluster_glyph_specs.json")
APPROVED_REFERENCE_SHEET = Path("assets/map/references/city-glyph-style-reference-5x3.png")
FULL_REGEN_BATCH_SIZE = 15
BATCH_GRID_CELLS = 15

FORBIDDEN_HINT_TERMS = (
    "river",
    "harbor",
    "hill",
    "mountain",
    "water",
    "canal",
    "sea",
    "boat",
    "ship",
    "pier",
    "dock",
    "waterfront",
    "bridge",
    "promenade",
    "quay",
    "cascade",
    "skyline",
    "mound",
)


def load_specs(path: Path = DEFAULT_SPECS_FILE) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def city_ids(specs: dict, status: str | None = None) -> list[str]:
    cities = specs["cities"]
    if status:
        cities = [city for city in cities if city["status"] == status]
    return [city["id"] for city in cities]


def planned_city_ids(specs: dict) -> list[str]:
    return city_ids(specs, "planned_cluster")


def _city_by_id(specs: dict, city_id: str) -> dict:
    return next(city for city in specs["cities"] if city["id"] == city_id)


def _safe_city_hint(city: dict) -> str:
    elements = [
        element
        for element in city["cluster_elements"]
        if not any(term in element.lower() for term in FORBIDDEN_HINT_TERMS)
    ]
    if not elements:
        elements = [
            "compact old-town architecture",
            "civic buildings, churches, palaces, domes, roofs, and modest tower accents",
            "dense urban base with small courtyards and trees",
        ]
    return f"{city['display_name']}: " + "; ".join(elements) + "."


def prompt_for_city(specs: dict, city_id: str) -> str:
    style_reference = specs["style_reference"]
    city = _city_by_id(specs, city_id)
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
            "Avoid terrain and water layers inside the city glyph: no mountain backdrops, snowy peaks, broad hills, terrain massifs, river strips, lakes, sea, harbor water, boats, ships, piers.",
        ]
    )


def batched_city_ids(ids: list[str], batch_size: int = FULL_REGEN_BATCH_SIZE) -> list[list[str]]:
    return [ids[index : index + batch_size] for index in range(0, len(ids), batch_size)]


def sharded_city_ids(ids: list[str], shard_count: int, shard_index: int) -> list[str]:
    if shard_count < 1:
        raise ValueError("shard_count must be >= 1")
    if shard_index < 1 or shard_index > shard_count:
        raise ValueError("shard_index must be between 1 and shard_count")
    chunk_size = (len(ids) + shard_count - 1) // shard_count
    start = (shard_index - 1) * chunk_size
    return ids[start : start + chunk_size]


def prompt_for_city_batch(specs: dict, ids: list[str], batch_number: int | None = None) -> str:
    cities = [_city_by_id(specs, city_id) for city_id in ids]
    filler_count = max(0, BATCH_GRID_CELLS - len(cities))
    cells = [
        (city["id"], city["display_name"], _safe_city_hint(city), False)
        for city in cities
    ]
    for index in range(filler_count):
        filler_id = f"style_filler_{index + 1}"
        cells.append(
            (
                filler_id,
                "Style filler",
                "Style filler: compact generic old-town token matching the reference sheet; this cell is a spacing/style pad and will be discarded.",
                True,
            )
        )
    batch_label = f" batch {batch_number}" if batch_number is not None else ""
    return "\n".join(
        [
            "Use case: stylized-concept",
            "Asset type: pre-slice high-resolution city glyph sheet for a Godot atlas map UI",
            f"Input image: {APPROVED_REFERENCE_SHEET} is the approved visual style reference.",
            f"Primary request: Create one coherent 5 columns x 3 rows city glyph sheet{batch_label} for these {len(cells)} cells, in this exact order:",
            ",".join(cell[0] for cell in cells) + ".",
            "",
            "Cell order:",
            "\n".join(f"{index + 1}. {display_name} ({city_id})" for index, (city_id, display_name, _hint, _filler) in enumerate(cells)),
            "",
            "Match the reference sheet exactly in visual language: compact European RPG map city-token, single artist, painterly pixel-art / 2.5D atlas miniature, warm stone and terracotta palette, crisp dark outline, consistent camera angle, consistent lighting, shared bottom baseline, medium-small controlled tokens, comparable visual mass.",
            "Each city should be a compact multi-symbol cluster, not one giant monument and not a flat side-view architectural row. Keep tall accents modest and do not let any token fill the whole cell height.",
            "",
            "Use only positive city hints:",
            "\n".join(f"- {hint}" for _city_id, _display_name, hint, _filler in cells),
            "",
            "Hard constraints: no water/canals/rivers/sea/harbor water/boats/ships/piers/docks/waterfront bases, no terrain/mountain backdrops/snowy peaks/broad hills/scenic bases, no flags, no readable text/labels, no frame, no watermark, no photorealism, no flat vector app-icon style.",
            "Background: perfectly flat solid #ff00ff chroma-key background only, with clean #ff00ff gutters. Do not leave partial-batch cells empty; use the listed style filler cells so every grid slot has one separable token.",
            "Integration note: discard any style_filler_* outputs after slicing; they exist only to keep the sheet geometry stable.",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect planned multi-symbol city cluster glyph specs.")
    parser.add_argument("--specs-file", type=Path, default=DEFAULT_SPECS_FILE)
    parser.add_argument("--status", choices=["existing_cluster", "planned_cluster"], default=None)
    parser.add_argument("--prompts", action="store_true", help="Print image-generation prompts instead of ids.")
    parser.add_argument("--batch-prompts", action="store_true", help="Print approved-reference 5x3 batch prompts.")
    parser.add_argument("--batch-size", type=int, default=FULL_REGEN_BATCH_SIZE)
    parser.add_argument("--shard-count", type=int, default=None)
    parser.add_argument("--shard-index", type=int, default=None)
    args = parser.parse_args()

    specs = load_specs(args.specs_file)
    ids = city_ids(specs, args.status)
    if args.shard_count is not None or args.shard_index is not None:
        if args.shard_count is None or args.shard_index is None:
            parser.error("--shard-count and --shard-index must be used together")
        ids = sharded_city_ids(ids, args.shard_count, args.shard_index)
    if args.batch_prompts:
        for batch_number, batch in enumerate(batched_city_ids(ids, args.batch_size), start=1):
            print(f"--- batch {batch_number} ---")
            print(prompt_for_city_batch(specs, batch, batch_number))
            print()
    elif args.prompts:
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
