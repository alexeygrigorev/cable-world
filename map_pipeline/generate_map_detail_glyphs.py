import os
import sys

from PIL import Image, ImageDraw


MAP_DIR = os.path.join(os.path.dirname(__file__), "..", "assets", "map")
GLYPH_DIR = os.path.join(MAP_DIR, "glyphs")
SIZE = 128


def _new_canvas():
    return Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))


def _save(image, name):
    os.makedirs(GLYPH_DIR, exist_ok=True)
    path = os.path.join(GLYPH_DIR, f"{name}.png")
    image.save(path, "PNG", optimize=True)
    print(f"Wrote {path}")


def _draw_shadow(draw, box, alpha=72):
    draw.ellipse(box, fill=(42, 31, 20, alpha))


def _ship():
    image = _new_canvas()
    draw = ImageDraw.Draw(image)
    _draw_shadow(draw, (26, 82, 106, 104), 58)
    hull = [(23, 72), (99, 72), (87, 91), (37, 91)]
    draw.polygon(hull, fill=(111, 64, 42, 245))
    draw.line(hull + [hull[0]], fill=(49, 34, 25, 245), width=4)
    draw.rectangle((43, 60, 78, 73), fill=(191, 151, 89, 245), outline=(57, 40, 27), width=3)
    draw.line((61, 25, 61, 72), fill=(48, 37, 27, 245), width=4)
    draw.polygon([(64, 30), (91, 55), (64, 59)], fill=(232, 216, 168, 240))
    draw.line((64, 30, 91, 55, 64, 59), fill=(82, 62, 39, 220), width=3)
    draw.polygon([(58, 36), (35, 60), (58, 63)], fill=(213, 193, 139, 235))
    draw.line((58, 36, 35, 60, 58, 63), fill=(82, 62, 39, 220), width=3)
    for x in (48, 62, 76):
        draw.rectangle((x, 65, x + 6, 70), fill=(65, 101, 111, 230), outline=(43, 50, 45))
    return image


def _port():
    image = _new_canvas()
    draw = ImageDraw.Draw(image)
    _draw_shadow(draw, (22, 86, 110, 105), 54)
    draw.rectangle((24, 78, 107, 87), fill=(92, 61, 38, 245), outline=(42, 31, 22), width=3)
    for x in range(30, 104, 14):
        draw.line((x, 50, x, 94), fill=(67, 45, 30, 245), width=4)
    draw.rectangle((34, 56, 78, 80), fill=(164, 115, 70, 245), outline=(53, 37, 24), width=3)
    draw.line((84, 76, 84, 36), fill=(55, 40, 27, 245), width=4)
    draw.line((84, 38, 106, 51), fill=(55, 40, 27, 245), width=4)
    draw.line((102, 51, 96, 63), fill=(55, 40, 27, 245), width=3)
    draw.rectangle((41, 63, 51, 74), fill=(55, 93, 103, 235), outline=(42, 31, 22))
    draw.rectangle((57, 63, 67, 74), fill=(55, 93, 103, 235), outline=(42, 31, 22))
    return image


def _bridge():
    image = _new_canvas()
    draw = ImageDraw.Draw(image)
    _draw_shadow(draw, (18, 79, 112, 105), 48)
    draw.arc((20, 44, 108, 118), 198, 342, fill=(65, 47, 32, 245), width=9)
    draw.arc((28, 54, 100, 108), 200, 340, fill=(189, 145, 82, 245), width=9)
    draw.line((23, 78, 107, 78), fill=(72, 50, 31, 245), width=6)
    draw.line((25, 70, 105, 70), fill=(219, 181, 111, 230), width=4)
    for x in (36, 52, 76, 92):
        draw.line((x, 70, x, 84), fill=(65, 47, 32, 230), width=3)
    return image


def _castle():
    image = _new_canvas()
    draw = ImageDraw.Draw(image)
    _draw_shadow(draw, (22, 88, 108, 108), 62)
    wall = (181, 137, 82, 245)
    outline = (68, 48, 31, 250)
    roof = (117, 56, 43, 245)
    draw.rectangle((38, 53, 90, 88), fill=wall, outline=outline, width=4)
    for cx in (35, 93):
        draw.rectangle((cx - 13, 38, cx + 13, 88), fill=wall, outline=outline, width=4)
        draw.polygon([(cx - 17, 38), (cx, 19), (cx + 17, 38)], fill=roof)
        draw.line((cx - 17, 38, cx, 19, cx + 17, 38), fill=outline, width=3)
    draw.polygon([(34, 53), (64, 30), (94, 53)], fill=roof)
    draw.line((34, 53, 64, 30, 94, 53), fill=outline, width=3)
    draw.rectangle((59, 69, 70, 88), fill=(68, 48, 31, 245))
    return image


def _tower():
    image = _new_canvas()
    draw = ImageDraw.Draw(image)
    _draw_shadow(draw, (34, 91, 96, 108), 54)
    stone = (175, 145, 95, 245)
    outline = (67, 49, 32, 250)
    roof = (105, 55, 46, 245)
    draw.rectangle((51, 37, 77, 93), fill=stone, outline=outline, width=4)
    draw.polygon([(47, 37), (64, 18), (81, 37)], fill=roof)
    draw.line((47, 37, 64, 18, 81, 37), fill=outline, width=3)
    draw.rectangle((58, 50, 70, 63), fill=(58, 93, 102, 235), outline=outline, width=2)
    draw.rectangle((58, 75, 70, 93), fill=(68, 48, 31, 245))
    for x in (44, 84):
        draw.line((x, 82, 64, 62), fill=outline, width=3)
    return image


def main():
    glyphs = {
        "detail_ship": _ship(),
        "detail_port": _port(),
        "detail_bridge": _bridge(),
        "detail_castle": _castle(),
        "detail_tower": _tower(),
    }
    for name, image in glyphs.items():
        _save(image, name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
