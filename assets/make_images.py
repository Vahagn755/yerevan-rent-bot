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
SNOW = (252, 248, 246)

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


def avatar() -> None:
    W = 640 * S
    img = tuff_wall(W, W, block_w=W // 4, block_h=W // 8)
    d = ImageDraw.Draw(img)
    cx, top, bottom, half = W // 2, int(W * 0.17), int(W * 0.92), int(W * 0.25)

    # carved frame stone around the doorway
    frame = arch_path(cx, top - W * 0.05, bottom, half + W * 0.05)
    shadow = Image.new("L", (W, W), 0)
    ImageDraw.Draw(shadow).polygon([(x + W * 0.012, y + W * 0.018) for x, y in frame], fill=120)
    img.paste((70, 40, 34), mask=shadow.filter(ImageFilter.GaussianBlur(W * 0.02)))
    d.polygon(frame, fill=mix(TUFF, (255, 240, 232), 0.35))

    # the doorway: dark basalt reveal, then warm apricot light from inside
    d.polygon(arch_path(cx, top, bottom, half), fill=BASALT)
    inner = arch_path(cx, top + W * 0.03, bottom, half - W * 0.03)
    light = glow((W, W), APRICOT_LIGHT, APRICOT, (cx, int(W * 0.62)), W * 0.42)
    mask = Image.new("L", (W, W), 0)
    ImageDraw.Draw(mask).polygon(inner, fill=255)
    img.paste(light, mask=mask)

    key_shape(d, cx, int(W * 0.58), W * 0.36, INK)
    img.resize((640, 640), Image.LANCZOS).save(OUT / "avatar.png", optimize=True)


def description() -> None:
    W, H = 640 * S, 360 * S
    # dawn sky over Yerevan
    sky = Image.new("RGB", (W, H))
    sd = ImageDraw.Draw(sky)
    for y in range(H):
        sd.line([(0, y), (W, y)], fill=mix((255, 226, 196), (196, 216, 236), (1 - y / H) ** 1.3))
    img = sky
    d = ImageDraw.Draw(img)

    # Ararat: Masis (big) and Sis (small), with snow caps
    base = int(H * 0.74)
    masis = [(W * 0.42, base), (W * 0.72, H * 0.24), (W * 0.77, H * 0.235), (W * 1.08, base)]
    sis = [(W * 0.70, base), (W * 0.88, H * 0.46), (W * 1.02, base)]
    far = (150, 158, 188)
    d.polygon(sis, fill=mix(far, (200, 206, 224), 0.35))
    d.polygon(masis, fill=far)
    snow = [(W * 0.645, H * 0.33), (W * 0.72, H * 0.24), (W * 0.77, H * 0.235), (W * 0.84, H * 0.34),
            (W * 0.80, H * 0.36), (W * 0.775, H * 0.33), (W * 0.74, H * 0.37), (W * 0.70, H * 0.335), (W * 0.67, H * 0.355)]
    d.polygon(snow, fill=SNOW)
    d.polygon([(W * 0.86, H * 0.49), (W * 0.88, H * 0.46), (W * 0.90, H * 0.49), (W * 0.885, H * 0.50)], fill=SNOW)

    # row of tuff buildings with arched windows, some lit
    rnd = random.Random(3)
    wall = tuff_wall(W, H, block_w=W // 16, block_h=H // 22, seed=11)
    x = 0
    while x < W:
        bw = rnd.choice([int(W * 0.16), int(W * 0.2), int(W * 0.13)])
        bh = rnd.choice([int(H * 0.25), int(H * 0.30), int(H * 0.21)])
        top = H - bh
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).rectangle([x, top, x + bw - S * 3, H], fill=255)
        img.paste(wall, mask=m)
        d.rectangle([x, top, x + bw - S * 3, top + S * 6], fill=mix(TUFF_DARK, BASALT, 0.25))  # cornice
        cols = max(2, bw // int(W * 0.055))
        ww = int(bw / cols * 0.48)
        for c in range(cols):
            wx = x + int((c + 0.5) * bw / cols)
            for r in range(2):
                wy = top + int(bh * (0.22 + r * 0.38))
                lit = rnd.random() < 0.45
                color = APRICOT_LIGHT if lit else (92, 70, 68)
                d.polygon(arch_path(wx, wy, wy + int(bh * 0.22), ww // 2, 24), fill=color)
        x += bw

    # text panel
    title = font(FONT_SERIF_BOLD, 34 * S)
    sub = font(FONT_SANS, 15 * S)
    tx, ty = 26 * S, 26 * S
    d.text((tx, ty), "Վարձով տուն", font=title, fill=INK)
    d.text((tx, ty + 42 * S), "Երևանում", font=title, fill=INK)
    lines = ["Նոր հայտարարություններ՝ ըստ քո ֆիլտրի,", "առանց միջնորդների և խաբեբաների"]
    for i, line in enumerate(lines):
        d.text((tx, ty + 94 * S + i * 21 * S), line, font=sub, fill=mix(INK, (120, 100, 92), 0.35))
    img.resize((640, 360), Image.LANCZOS).save(OUT / "description.png", optimize=True)


if __name__ == "__main__":
    avatar()
    description()
    print("saved", OUT / "avatar.png", OUT / "description.png")
