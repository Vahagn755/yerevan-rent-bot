"""Draws the bot's profile picture (640x640) and description picture (640x360).

Run: python assets/make_images.py   (needs Pillow and the DejaVu fonts, which include Armenian)
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = Path(__file__).parent
S = 2  # draw at 2x and scale down for smooth edges

TUFF = (226, 181, 165)
TUFF_DARK = (196, 140, 124)
MORTAR = (242, 214, 203)
BASALT = (58, 44, 42)
APRICOT = (240, 162, 59)
APRICOT_LIGHT = (255, 214, 150)
INK = (42, 37, 34)
PLUM = (46, 36, 48)
CREAM = (250, 242, 236)

FONT_SERIF_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
FONT_SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    for p in (path, path.replace("truetype/dejavu", "dejavu")):
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.truetype(path.rsplit("/", 1)[1], size)


def mix(a, b, t):
    return tuple(round(x + (y - x) * t) for x, y in zip(a, b))


def tuff_wall(w: int, h: int, block_w: int, block_h: int, seed: int = 7) -> Image.Image:
    """Yerevan pink tuff masonry: staggered blocks with slight tone changes."""
    rnd = random.Random(seed)
    img = Image.new("RGB", (w, h), MORTAR)
    d = ImageDraw.Draw(img)
    gap = max(3, block_h // 14)
    for row, y in enumerate(range(0, h + block_h, block_h)):
        offset = (block_w // 2) if row % 2 else 0
        for x in range(-offset, w + block_w, block_w):
            tone = mix(TUFF, TUFF_DARK, rnd.uniform(0, 0.55))
            tone = mix(tone, (255, 236, 228), rnd.uniform(0, 0.18))
            d.rounded_rectangle([x + gap, y + gap, x + block_w - gap, y + block_h - gap],
                                radius=gap * 2, fill=tone)
    # porous stone grain
    grain = Image.effect_noise((w, h), 22).convert("L")
    img = Image.composite(img, mix_img(img, (120, 70, 60)), grain.point(lambda v: 255 if v > 70 else 235))
    return img


def mix_img(img: Image.Image, color) -> Image.Image:
    return Image.blend(img, Image.new("RGB", img.size, color), 0.12)


def arch_path(cx, top, bottom, half_w, steps=64):
    """Points of a round-topped Armenian doorway arch."""
    pts = [(cx - half_w, bottom)]
    for i in range(steps + 1):
        a = math.pi + math.pi * i / steps
        pts.append((cx + half_w * math.cos(a), top + half_w + half_w * math.sin(a)))
    pts.append((cx + half_w, bottom))
    return pts


def glow(size, inner, outer, center, radius):
    w, h = size
    img = Image.new("RGB", size, outer)
    px = img.load()
    cx, cy = center
    for y in range(h):
        for x in range(0, w):
            t = min(1.0, math.hypot(x - cx, y - cy) / radius)
            px[x, y] = mix(inner, outer, t ** 1.4)
    return img


def key_shape(d: ImageDraw.ImageDraw, cx, cy, s, color):
    """Simple key: ring bow, shaft and two teeth."""
    r = s * 0.22
    d.ellipse([cx - r, cy - s * 0.42 - r, cx + r, cy - s * 0.42 + r], outline=color, width=int(s * 0.09))
    d.rounded_rectangle([cx - s * 0.045, cy - s * 0.2, cx + s * 0.045, cy + s * 0.5], radius=int(s * 0.03), fill=color)
    d.rectangle([cx, cy + s * 0.28, cx + s * 0.17, cy + s * 0.35], fill=color)
    d.rectangle([cx, cy + s * 0.41, cx + s * 0.13, cy + s * 0.48], fill=color)


def pin_path(cx, cy, r, tip_y, steps=80):
    """Map pin: a circle that narrows to a point at the bottom."""
    a0 = math.asin(r / (tip_y - cy))  # tangent angle from the tip
    pts = [(cx, tip_y)]
    start, end = math.pi / 2 + a0, math.pi / 2 - a0 + 2 * math.pi
    for i in range(steps + 1):
        a = start + (end - start) * i / steps
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def avatar() -> None:
    """Map pin built from pink tuff blocks, with a lit arched door: home, in Yerevan."""
    W = 640 * S
    bg = glow((W, W), (74, 58, 78), PLUM, (W // 2, int(W * 0.35)), W * 0.75)
    img = bg
    cx, cy, r, tip = W // 2, int(W * 0.42), int(W * 0.30), int(W * 0.90)
    pin = pin_path(cx, cy, r, tip)

    shadow = Image.new("L", (W, W), 0)
    ImageDraw.Draw(shadow).polygon([(x, y + W * 0.02) for x, y in pin], fill=150)
    img.paste((20, 14, 22), mask=shadow.filter(ImageFilter.GaussianBlur(W * 0.025)))

    wall = tuff_wall(W, W, block_w=W // 7, block_h=W // 14, seed=5)
    mask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(mask).polygon(pin, fill=255)
    img.paste(wall, mask=mask)
    d = ImageDraw.Draw(img)

    # arched door in the middle of the pin, warm light inside
    half, top, bottom = int(r * 0.42), cy - int(r * 0.55), cy + int(r * 0.62)
    d.polygon(arch_path(cx, top - S * 10, bottom + S * 4, half + S * 10), fill=mix(TUFF, CREAM, 0.5))
    d.polygon(arch_path(cx, top, bottom, half), fill=BASALT)
    door = arch_path(cx, top + S * 9, bottom, half - S * 9)
    light = glow((W, W), APRICOT_LIGHT, APRICOT, (cx, bottom), r * 0.9)
    m = Image.new("L", (W, W), 0)
    ImageDraw.Draw(m).polygon(door, fill=255)
    img.paste(light, mask=m)
    d.ellipse([cx + half * 0.35, cy + r * 0.05, cx + half * 0.35 + S * 14, cy + r * 0.05 + S * 14], fill=INK)  # knob
    img.resize((640, 640), Image.LANCZOS).save(OUT / "avatar.png", optimize=True)


def window(img, d, x, y, w, h, lit, rnd):
    frame = mix(TUFF, CREAM, 0.45)
    d.polygon(arch_path(x, y - S * 5, y + h + S * 4, w // 2 + S * 5, 32), fill=frame)
    if lit:
        g = glow((w + S * 2, h + S * 2), APRICOT_LIGHT, APRICOT, (w // 2, int(h * 0.75)), h)
        m = Image.new("L", g.size, 0)
        ImageDraw.Draw(m).polygon(arch_path(w // 2 + S, 0, h, w // 2, 32), fill=255)
        img.paste(g, (x - w // 2 - S, y), m)
    else:
        d.polygon(arch_path(x, y, y + h, w // 2, 32), fill=(86, 66, 72))
    # mullion and transom
    d.line([(x, y + w // 2), (x, y + h)], fill=frame, width=S * 3)
    d.line([(x - w // 2, y + int(h * 0.42)), (x + w // 2, y + int(h * 0.42))], fill=frame, width=S * 3)


def description() -> None:
    """Evening facade of a tuff apartment house; one balcony has a "for rent" tag."""
    W, H = 640 * S, 360 * S
    img = glow((W, H), (70, 54, 74), PLUM, (int(W * 0.25), int(H * 0.3)), W * 0.8)
    d = ImageDraw.Draw(img)

    # facade on the right
    fx = int(W * 0.50)
    wall = tuff_wall(W - fx, H, block_w=W // 14, block_h=H // 16, seed=21)
    img.paste(wall, (fx, 0))
    d.rectangle([fx, 0, fx + S * 6, H], fill=mix(TUFF_DARK, BASALT, 0.35))  # building edge shadow

    rnd = random.Random(8)
    cols, floors = 3, 3
    fw = W - fx
    ww, wh = int(fw / cols * 0.42), int(H / floors * 0.58)
    lit_map = [[1, 0, 1], [0, 1, 0], [1, 1, 0]]
    for f in range(floors):
        y0 = int(H * 0.06) + f * int(H / floors)
        # cornice under each floor
        d.rectangle([fx, y0 + wh + S * 14, W, y0 + wh + S * 20], fill=mix(TUFF_DARK, BASALT, 0.2))
        for c in range(cols):
            x = fx + int((c + 0.5) * fw / cols)
            window(img, d, x, y0, ww, wh, lit_map[f][c], rnd)
        if f == 1:  # balcony with a railing across the middle window
            bx0, bx1 = fx + int(0.5 * fw / cols) + ww, fx + int(2.5 * fw / cols) - ww
            mid = fx + int(1.5 * fw / cols)
            by = y0 + wh + S * 2
            bx0, bx1 = mid - int(ww * 0.95), mid + int(ww * 0.95)
            d.rectangle([bx0, by, bx1, by + S * 6], fill=BASALT)
            for bx in range(bx0, bx1 + 1, S * 9):
                d.line([(bx, by - int(wh * 0.28)), (bx, by)], fill=BASALT, width=S * 2)
            d.rectangle([bx0, by - int(wh * 0.28), bx1, by - int(wh * 0.28) + S * 3], fill=BASALT)
            # hanging tag
            tag_font = font(FONT_SANS.replace("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"), 12 * S)
            label = "Վարձով"
            tw = d.textlength(label, font=tag_font)
            tx0, ty0 = mid - tw / 2 - S * 10, by + S * 22
            d.line([(mid - tw / 3, by + S * 6), (mid - tw / 3, ty0)], fill=CREAM, width=S * 2)
            d.line([(mid + tw / 3, by + S * 6), (mid + tw / 3, ty0)], fill=CREAM, width=S * 2)
            d.rounded_rectangle([tx0, ty0, mid + tw / 2 + S * 10, ty0 + S * 26], radius=S * 6, fill=APRICOT)
            d.text((mid - tw / 2, ty0 + S * 5), label, font=tag_font, fill=INK)

    # text
    title = font(FONT_SERIF_BOLD, 33 * S)
    sub = font(FONT_SANS, 14 * S)
    tx, ty = 28 * S, 44 * S
    d.text((tx, ty), "Վարձով տուն", font=title, fill=CREAM)
    d.text((tx, ty + 42 * S), "Երևանում", font=title, fill=CREAM)
    d.rounded_rectangle([tx, ty + 98 * S, tx + 44 * S, ty + 102 * S], radius=S * 2, fill=APRICOT)
    lines = ["Նոր հայտարարություններ՝", "ըստ քո ֆիլտրի, առանց", "միջնորդների և խաբեբաների"]
    for i, line in enumerate(lines):
        d.text((tx, ty + 116 * S + i * 21 * S), line, font=sub, fill=mix(CREAM, PLUM, 0.28))
    img.resize((640, 360), Image.LANCZOS).save(OUT / "description.png", optimize=True)


if __name__ == "__main__":
    avatar()
    description()
    print("saved", OUT / "avatar.png", OUT / "description.png")
