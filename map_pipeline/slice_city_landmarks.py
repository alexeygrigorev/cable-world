import argparse
from pathlib import Path

from PIL import Image


ICON_SIZE = 192
PADDING = 16

CITY_ICON_NAMES = [
    "berlin", "hamburg", "rostock", "munich", "cologne", "frankfurt", "stuttgart", "dresden",
    "heidelberg", "duesseldorf", "dortmund", "wuppertal", "baden_baden", "koblenz", "zugspitze", "harz",
    "paris", "london", "madrid", "barcelona", "rome", "milan", "venice", "amsterdam",
    "brussels", "prague", "vienna", "budapest", "warsaw", "krakow", "copenhagen", "stockholm",
    "oslo", "helsinki", "tallinn", "riga", "vilnius", "minsk", "kyiv", "lviv",
    "istanbul", "ankara", "lisbon", "porto", "athens", "sofia", "bucharest", "belgrade",
    "zagreb", "ljubljana", "bratislava", "sarajevo", "skopje", "tirana", "reykjavik", "dublin",
    "zurich", "geneva", "luxembourg", "monaco", "andorra", "san_marino", "valletta", "strasbourg",
]


def _cell_bounds(width: int, height: int, index: int) -> tuple[int, int, int, int]:
    col = index % 8
    row = index // 8
    return (
        round(width * col / 8),
        round(height * row / 8),
        round(width * (col + 1) / 8),
        round(height * (row + 1) / 8),
    )


def _trim_alpha(image: Image.Image) -> Image.Image:
    bbox = image.getchannel("A").getbbox()
    return image.crop(bbox) if bbox else image


def _fit_icon(image: Image.Image) -> Image.Image:
    icon = Image.new("RGBA", (ICON_SIZE, ICON_SIZE), (0, 0, 0, 0))
    max_side = ICON_SIZE - PADDING * 2
    scale = min(max_side / image.width, max_side / image.height)
    resized = image.resize(
        (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
        Image.Resampling.LANCZOS,
    )
    icon.alpha_composite(resized, ((ICON_SIZE - resized.width) // 2, (ICON_SIZE - resized.height) // 2))
    return icon


def main() -> int:
    parser = argparse.ArgumentParser(description="Slice an 8x8 city landmark sprite sheet.")
    parser.add_argument("--sheet", required=True)
    parser.add_argument("--out-dir", default="assets/sprites/city_landmarks")
    args = parser.parse_args()

    sheet = Image.open(args.sheet).convert("RGBA")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for index, name in enumerate(CITY_ICON_NAMES):
        icon = _fit_icon(_trim_alpha(sheet.crop(_cell_bounds(sheet.width, sheet.height, index))))
        out = out_dir / f"city_{name}.png"
        icon.save(out, "PNG", optimize=True)
        print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
