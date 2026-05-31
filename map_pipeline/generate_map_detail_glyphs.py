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


def _village():
    image = _new_canvas()
    draw = ImageDraw.Draw(image)
    _draw_shadow(draw, (18, 88, 112, 108), 52)
    outline = (61, 43, 27, 250)
    wall = (186, 139, 78, 245)
    roof = (118, 55, 38, 245)
    for x, y, w, h in [(26, 61, 28, 25), (52, 52, 34, 34), (83, 65, 25, 22)]:
        draw.rectangle((x, y, x + w, y + h), fill=wall, outline=outline, width=3)
        draw.polygon([(x - 4, y), (x + w // 2, y - 16), (x + w + 4, y)], fill=roof)
        draw.line((x - 4, y, x + w // 2, y - 16, x + w + 4, y), fill=outline, width=2)
        draw.rectangle((x + w // 2 - 3, y + h - 12, x + w // 2 + 4, y + h), fill=(77, 49, 28, 245))
    draw.line((22, 90, 108, 91), fill=(216, 187, 112, 160), width=3)
    return image


def _chapel():
    image = _new_canvas()
    draw = ImageDraw.Draw(image)
    _draw_shadow(draw, (25, 89, 103, 107), 50)
    outline = (61, 43, 28, 250)
    wall = (190, 151, 94, 245)
    roof = (117, 56, 44, 245)
    draw.rectangle((42, 51, 86, 91), fill=wall, outline=outline, width=4)
    draw.polygon([(38, 51), (64, 28), (90, 51)], fill=roof)
    draw.line((38, 51, 64, 28, 90, 51), fill=outline, width=3)
    draw.rectangle((58, 34, 70, 51), fill=wall, outline=outline, width=3)
    draw.line((64, 21, 64, 35), fill=outline, width=3)
    draw.line((58, 27, 70, 27), fill=outline, width=3)
    draw.rectangle((57, 72, 71, 91), fill=(67, 43, 28, 245))
    draw.rectangle((48, 60, 58, 70), fill=(64, 99, 111, 230), outline=outline, width=2)
    draw.rectangle((72, 60, 82, 70), fill=(64, 99, 111, 230), outline=outline, width=2)
    return image


def _ruins():
    image = _new_canvas()
    draw = ImageDraw.Draw(image)
    _draw_shadow(draw, (25, 90, 106, 108), 48)
    stone = (143, 126, 91, 240)
    outline = (66, 55, 38, 250)
    draw.rectangle((31, 58, 50, 92), fill=stone, outline=outline, width=4)
    draw.rectangle((76, 48, 97, 92), fill=stone, outline=outline, width=4)
    draw.rectangle((45, 72, 83, 92), fill=stone, outline=outline, width=4)
    for box in [(34, 64, 46, 78), (80, 55, 93, 70), (57, 78, 70, 92)]:
        draw.rectangle(box, fill=(55, 46, 34, 245))
    draw.line((27, 94, 101, 94), fill=(96, 76, 48, 210), width=4)
    return image


def _windmill():
    image = _new_canvas()
    draw = ImageDraw.Draw(image)
    _draw_shadow(draw, (31, 91, 98, 108), 48)
    outline = (61, 43, 28, 250)
    wall = (188, 148, 88, 245)
    roof = (105, 57, 42, 245)
    draw.rectangle((50, 56, 78, 93), fill=wall, outline=outline, width=4)
    draw.polygon([(46, 56), (64, 37), (82, 56)], fill=roof)
    draw.line((46, 56, 64, 37, 82, 56), fill=outline, width=3)
    hub = (64, 51)
    for end in [(64, 18), (97, 51), (64, 84), (31, 51)]:
        draw.line((hub[0], hub[1], end[0], end[1]), fill=outline, width=4)
        draw.line((hub[0], hub[1], end[0], end[1]), fill=(219, 194, 131, 240), width=2)
    draw.ellipse((58, 45, 70, 57), fill=(86, 58, 35, 250), outline=outline, width=2)
    return image


def _lighthouse():
    image = _new_canvas()
    draw = ImageDraw.Draw(image)
    _draw_shadow(draw, (34, 92, 96, 108), 45)
    outline = (60, 43, 29, 250)
    light = (237, 209, 132, 235)
    wall = (221, 196, 148, 245)
    stripe = (135, 61, 45, 245)
    draw.rectangle((51, 31, 77, 94), fill=wall, outline=outline, width=4)
    draw.rectangle((48, 24, 80, 38), fill=light, outline=outline, width=3)
    draw.polygon([(46, 24), (64, 12), (82, 24)], fill=(103, 58, 43, 245))
    draw.rectangle((51, 52, 77, 61), fill=stripe)
    draw.rectangle((51, 75, 77, 84), fill=stripe)
    for x in (30, 93):
        draw.line((64, 31, x, 18), fill=(246, 223, 139, 95), width=3)
    return image


def _watermill():
    image = _new_canvas()
    draw = ImageDraw.Draw(image)
    _draw_shadow(draw, (19, 90, 110, 108), 46)
    outline = (61, 43, 28, 250)
    wall = (177, 123, 71, 245)
    roof = (112, 54, 39, 245)
    draw.rectangle((29, 57, 69, 91), fill=wall, outline=outline, width=4)
    draw.polygon([(25, 57), (49, 36), (73, 57)], fill=roof)
    draw.line((25, 57, 49, 36, 73, 57), fill=outline, width=3)
    draw.ellipse((68, 55, 107, 94), fill=(117, 79, 43, 245), outline=outline, width=4)
    for angle in range(0, 180, 45):
        import math

        cx, cy = 87, 75
        dx = int(math.cos(math.radians(angle)) * 19)
        dy = int(math.sin(math.radians(angle)) * 19)
        draw.line((cx - dx, cy - dy, cx + dx, cy + dy), fill=(63, 43, 26, 245), width=3)
    draw.line((20, 94, 110, 94), fill=(68, 131, 143, 170), width=4)
    return image


def main():
    glyphs = {
        "detail_ship": _ship(),
        "detail_port": _port(),
        "detail_bridge": _bridge(),
        "detail_castle": _castle(),
        "detail_tower": _tower(),
        "detail_village": _village(),
        "detail_chapel": _chapel(),
        "detail_ruins": _ruins(),
        "detail_windmill": _windmill(),
        "detail_lighthouse": _lighthouse(),
        "detail_watermill": _watermill(),
    }
    for name, image in glyphs.items():
        _save(image, name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
