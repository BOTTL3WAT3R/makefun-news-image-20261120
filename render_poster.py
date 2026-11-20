#!/usr/bin/env python3
"""news-image-20261120 — one front page for Friday 20 November 2026 (v3).

Deterministic, offline Pillow program. Draws a cream broadsheet front page:
masthead naming the day, stat strip, one dominant illustrated lead scene
(the Shenzhen trilateral summit), 3 large panels, 12 small panels, a brief
list and a DATE CHECK footer. 33 verified stories (v2 carried 25; v3 adds
8 more from research/FACTS-V3-20261120.md plus Friday updates to the lead,
Akvan, Anthropic and COP31 stories). Every fact verified against at
least two independent sources (see research/FACTS-20261120.md and
research/FACTS-V3-20261120.md in the build folder; no leader numbers are
copied).

Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png).
"""
import os
from PIL import Image, ImageDraw, ImageFont

W = H = 1024
M = 20                      # outer margin
CW = W - 2 * M              # content width = 984

PAPER = (247, 241, 222)
INK = (26, 26, 26)
RED = (164, 30, 34)
BLUE = (31, 78, 121)
MUTED = (107, 101, 88)
SKY = (188, 211, 228)
SKY_D = (140, 175, 205)
DUSK = (46, 64, 83)
SAND = (232, 222, 196)
PANEL_BG = (250, 246, 232)
SEA = (178, 205, 222)
GOLD = (176, 141, 60)

FONT_PATHS = {
    "serif_b": [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    ],
    "serif": [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ],
    "serif_i": [
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
    ],
    "sans_b": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "sans": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
}


def font(role, size):
    for p in FONT_PATHS[role]:
        try:
            return ImageFont.truetype(p, size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap(draw, text, fnt, width):
    """Greedy word wrap; returns list of lines."""
    lines, cur = [], ""
    for word in text.split():
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=fnt) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text_block(draw, x, y, text, fnt, width, fill=INK, leading=None, max_lines=None):
    lines = wrap(draw, text, fnt, width)
    if max_lines:
        lines = lines[:max_lines]
    lh = leading or int(fnt.size * 1.18)
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def hline(draw, x0, x1, y, width=2, fill=INK):
    draw.line([(x0, y), (x1, y)], fill=fill, width=width)


def vline(draw, x, y0, y1, width=1, fill=INK):
    draw.line([(x, y0), (x, y1)], fill=fill, width=width)


# ---------------------------------------------------------------- flags
def flag_us(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=INK)
    for i in range(7):
        if i % 2 == 0:
            draw.rectangle([x, y + i * h / 7, x + w, y + (i + 1) * h / 7],
                           fill=(178, 34, 52))
    draw.rectangle([x, y, x + w * 0.4, y + h * 4 / 7], fill=(60, 59, 110))
    for r in range(3):
        for c in range(4):
            draw.ellipse([x + 3 + c * w * 0.09, y + 2 + r * h * 0.17,
                          x + 6 + c * w * 0.09, y + 5 + r * h * 0.17],
                         fill=(255, 255, 255))


def flag_cn(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(222, 41, 16), outline=INK)
    def star(cx, cy, r):
        pts = []
        import math
        for k in range(10):
            ang = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.45
            pts.append((cx + rr * math.cos(ang), cy + rr * math.sin(ang)))
        draw.polygon(pts, fill=(255, 222, 0))
    star(x + w * 0.18, y + h * 0.28, h * 0.22)
    for sx, sy in [(0.42, 0.18), (0.52, 0.32), (0.5, 0.5), (0.4, 0.6)]:
        star(x + w * sx, y + h * sy, h * 0.09)


def flag_ru(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=INK)
    draw.rectangle([x, y + h / 3, x + w, y + 2 * h / 3], fill=(0, 57, 166))
    draw.rectangle([x, y + 2 * h / 3, x + w, y + h], fill=(213, 0, 50))


def flag_pole(draw, x, y, h, flag_fn, fw=34):
    draw.line([(x, y), (x, y + h)], fill=INK, width=3)
    draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=GOLD)
    flag_fn(draw, x + 2, y + 2, fw, int(fw * 0.62))


# ---------------------------------------------------------------- scenes
def draw_lead_scene(draw, x, y, w, h):
    """Shenzhen skyline at dusk, three flags, three leaders at a table."""
    # sky
    for i in range(h):
        t = i / max(h - 1, 1)
        c = tuple(int(SKY[i2] + (DUSK[i2] - SKY[i2]) * t) for i2 in range(3))
        draw.line([(x, y + i), (x + w, y + i)], fill=c)
    # sun disc (clear of the flags at left and right)
    draw.ellipse([x + 300, y + 10, x + 346, y + 56], fill=(240, 200, 120))
    # skyline (two depths)
    import random
    rnd = random.Random(20261120)
    base = y + h - 58
    s = h / 158.0                     # v3 scene is shorter than v2's 158px
    for bx in range(x, x + w, 26):
        bh = rnd.randint(8, max(10, int(52 * s)))
        draw.rectangle([bx + 2, base - bh, bx + 24, base], fill=(58, 80, 104))
    for bx in range(x + 8, x + w, 40):
        bh = rnd.randint(12, max(14, int(74 * s)))
        draw.rectangle([bx + 2, base - bh, bx + 36, base], fill=(38, 56, 76))
        for wy in range(base - bh + 6, base - 6, 12):
            for wx in range(bx + 8, bx + 30, 10):
                if rnd.random() < 0.5:
                    draw.rectangle([wx, wy, wx + 4, wy + 6], fill=(240, 210, 130))
    # tower with spire (centre-right, Shenzhen-like) — kept inside the scene
    tx = x + w - 210
    th = int(88 * s)
    draw.rectangle([tx, base - th, tx + 26, base], fill=(30, 46, 64))
    draw.polygon([(tx + 13, base - int(96 * s)), (tx + 4, base - th),
                  (tx + 22, base - th)], fill=(30, 46, 64))
    # table
    draw.rectangle([x + 40, base + 6, x + w - 40, base + 34], fill=(58, 44, 34))
    draw.rectangle([x + 40, base + 6, x + w - 40, base + 12], fill=(96, 74, 54))
    # three leaders: simple seated figures (head + shoulders), no faces
    spots = [(0.24, (52, 52, 58), (200, 200, 205)),   # dark hair, grey suit
             (0.50, (30, 30, 30), (24, 24, 24)),      # black hair, black suit
             (0.76, (210, 210, 210), (70, 90, 120))]  # grey hair, blue suit
    for fx, hair, suit in spots:
        cx = x + int(w * fx)
        draw.ellipse([cx - 15, base - 34, cx + 15, base - 4], fill=(222, 184, 150))
        draw.pieslice([cx - 15, base - 34, cx + 15, base - 12], 180, 360, fill=hair)
        draw.polygon([(cx - 26, base + 6), (cx - 18, base - 10),
                      (cx + 18, base - 10), (cx + 26, base + 6)], fill=suit)
        draw.polygon([(cx - 6, base - 8), (cx + 6, base - 8),
                      (cx + 3, base + 6), (cx - 3, base + 6)], fill=(255, 255, 255))
        draw.polygon([(cx - 3, base - 8), (cx + 3, base - 8),
                      (cx, base + 2)], fill=RED)
    # name plates on the table
    for fx, name in [(0.24, "TRUMP"), (0.50, "XI"), (0.76, "PUTIN")]:
        cx = x + int(w * fx)
        draw.rectangle([cx - 30, base + 16, cx + 30, base + 32],
                       fill=(250, 246, 232), outline=INK)
        f = font("sans_b", 11)
        tw = draw.textlength(name, font=f)
        draw.text((cx - tw / 2, base + 18), name, font=f, fill=INK)
    # flags on poles behind the table, left and right
    flag_pole(draw, x + 60, y + 10, int(56 * s), flag_us)
    flag_pole(draw, x + 118, y + 10, int(56 * s), flag_cn)
    flag_pole(draw, x + w - 84, y + 10, int(56 * s), flag_ru)


def draw_cyclone(draw, x, y, w, h):
    """Akvan: spiral storm over a blue sea, coastline at the bottom."""
    draw.rectangle([x, y, x + w, y + h], fill=(206, 222, 232))
    cx, cy = x + w // 2, y + h // 2 + 2
    for r in range(min(40, h // 2 - 3), 6, -6):
        draw.arc([cx - r, cy - r, cx + r, cy + r], 20, 300,
                 fill=(255, 255, 255), width=5)
    draw.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], fill=(255, 255, 255),
                 outline=INK)
    for i in range(14):
        rx = x + (i * 37) % w
        ry = y + 8 + (i * 53) % (h - 20)
        draw.line([(rx, ry), (rx - 4, ry + 10)], fill=(90, 130, 170), width=2)
    # coastline + land
    draw.polygon([(x, y + h), (x + w * 0.55, y + h - 18), (x + w, y + h - 8),
                  (x + w, y + h), (x, y + h)], fill=(214, 196, 150))
    draw.line([(x, y + h - 2), (x + w * 0.55, y + h - 20),
               (x + w, y + h - 10)], fill=INK, width=2)


def draw_calendar(draw, x, y, w, h):
    """Iran: a calendar page reading 2027 with a red arrow pointing on."""
    draw.rectangle([x, y, x + w, y + h], fill=(250, 246, 232))
    band = int(h * 0.28)
    draw.rectangle([x + 14, y + 6, x + w - 14, y + h - 6], fill=(255, 255, 255),
                   outline=INK, width=2)
    draw.rectangle([x + 14, y + 6, x + w - 14, y + 6 + band], fill=RED)
    f = font("sans_b", 12)
    t = "DECISION"
    draw.text((x + w / 2 - draw.textlength(t, font=f) / 2, y + 8), t,
              font=f, fill=(255, 255, 255))
    f2 = font("serif_b", int(h * 0.40))
    t2 = "2027"
    draw.text((x + w / 2 - draw.textlength(t2, font=f2) / 2, y + 7 + band), t2,
              font=f2, fill=INK)
    draw.line([(x + 18, y + h - 7), (x + w - 34, y + h - 7)], fill=RED, width=3)
    draw.polygon([(x + w - 34, y + h - 12), (x + w - 34, y + h - 2),
                  (x + w - 20, y + h - 7)], fill=RED)


def draw_court(draw, x, y, w, h):
    """ICJ: courthouse pediment, columns, scales (compact for short art)."""
    draw.rectangle([x, y, x + w, y + h], fill=(232, 222, 196))
    draw.polygon([(x + 8, y + 18), (x + w / 2, y + 4), (x + w - 8, y + 18)],
                 fill=(120, 100, 70), outline=INK)
    for i in range(5):
        cx = x + 22 + i * (w - 44) / 4
        draw.rectangle([cx - 7, y + 20, cx + 7, y + h - 10], fill=(250, 246, 232),
                       outline=INK)
    draw.rectangle([x + 8, y + h - 10, x + w - 8, y + h - 4], fill=(120, 100, 70))
    # scales of justice, centre, drawn over the columns
    cx, cy = x + w / 2, y + int(h * 0.55)
    draw.line([(cx, cy - 12), (cx, cy + 2)], fill=INK, width=3)
    draw.line([(cx - 15, cy - 12), (cx + 15, cy - 12)], fill=INK, width=3)
    draw.line([(cx - 15, cy - 12), (cx - 18, cy)], fill=INK, width=2)
    draw.line([(cx - 15, cy - 12), (cx - 12, cy)], fill=INK, width=2)
    draw.line([(cx + 15, cy - 12), (cx + 18, cy)], fill=INK, width=2)
    draw.line([(cx + 15, cy - 12), (cx + 12, cy)], fill=INK, width=2)
    draw.arc([cx - 21, cy - 2, cx - 9, cy + 8], 0, 180, fill=INK, width=2)
    draw.arc([cx + 9, cy - 2, cx + 21, cy + 8], 0, 180, fill=INK, width=2)


def draw_globe_doc(draw, x, y, w, h):
    """COP31: globe with a struck-through fossil-fuel document."""
    draw.rectangle([x, y, x + w, y + h], fill=(222, 232, 222))
    r = min(24, int(w * 0.36))
    cx, cy = x + r + 4, y + h / 2
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(120, 180, 210),
                 outline=INK, width=2)
    draw.ellipse([cx - r // 2, cy - r, cx + r // 2, cy + r],
                 outline=(255, 255, 255), width=2)
    draw.line([(cx - r, cy), (cx + r, cy)], fill=(255, 255, 255), width=2)
    draw.arc([cx - r + 2, cy - r // 2, cx + r - 2, cy + r // 2], 200, 340,
             fill=(255, 255, 255), width=2)
    # document
    dx, dy = x + w - 24, y + 8
    draw.rectangle([dx, dy, dx + 20, dy + h - 16], fill=(255, 255, 255),
                   outline=INK, width=2)
    for i in range(4):
        draw.line([(dx + 4, dy + 8 + i * 9), (dx + 16, dy + 8 + i * 9)],
                  fill=MUTED, width=2)
    draw.line([(dx + 1, dy + 3), (dx + 19, dy + h - 19)], fill=RED, width=3)


def draw_embassy(draw, x, y, w, h):
    """Kyiv: embassy building, cracked facade, EU stars (narrow art)."""
    draw.rectangle([x, y, x + w, y + h], fill=(214, 222, 232))
    draw.rectangle([x + 10, y + 20, x + w - 10, y + h - 8], fill=(232, 222, 196),
                   outline=INK, width=2)
    draw.polygon([(x + 4, y + 20), (x + w / 2, y + 5), (x + w - 4, y + 20)],
                 fill=(120, 100, 70))
    for i in range(3):
        wx = x + 15 + i * 11
        draw.rectangle([wx, y + 30, wx + 8, y + 44], fill=(90, 120, 150),
                       outline=INK)
    # crack
    draw.line([(x + w - 14, y + 26), (x + w - 19, y + 38), (x + w - 13, y + 48),
               (x + w - 17, y + h - 10)], fill=INK, width=2)
    # EU stars ring, top right
    import math
    sx, sy = x + w - 9, y + 9
    for k in range(6):
        ang = -math.pi / 2 + k * math.pi / 3
        draw.ellipse([sx + 5 * math.cos(ang) - 1, sy + 5 * math.sin(ang) - 1,
                      sx + 5 * math.cos(ang) + 1, sy + 5 * math.sin(ang) + 1],
                     fill=GOLD)


def draw_gta(draw, x, y, w, h):
    """GTA VI: neon sunset, skyline, big VI."""
    for i in range(h):
        t = i / max(h - 1, 1)
        top = (250, 120, 90)
        bot = (120, 40, 90)
        c = tuple(int(top[j] + (bot[j] - top[j]) * t) for j in range(3))
        draw.line([(x, y + i), (x + w, y + i)], fill=c)
    draw.ellipse([x + w / 2 - 16, y + 8, x + w / 2 + 16, y + 40],
                 fill=(255, 220, 130))
    base = y + h - 14
    for bx in range(x, x + w, 18):
        bh = 10 + ((bx * 7) % 26)
        draw.rectangle([bx + 2, base - bh, min(bx + 16, x + w), base],
                       fill=(40, 20, 50))
    f = font("serif_b", 34)
    t = "VI"
    draw.text((x + w / 2 - draw.textlength(t, font=f) / 2, y + h - 44), t,
              font=f, fill=(255, 255, 255))


def draw_chart(draw, x, y, w, h):
    """Anthropic: rising chart, $83 tag."""
    draw.rectangle([x, y, x + w, y + h], fill=(222, 232, 222))
    pts = [(x + 8, y + h - 18), (x + w * 0.3, y + h - 34),
           (x + w * 0.5, y + h - 26), (x + w * 0.72, y + h - 46),
           (x + w - 10, y + 14)]
    draw.line(pts, fill=(30, 120, 60), width=4, joint="curve")
    draw.polygon([(x + w - 10, y + 14), (x + w - 22, y + 16),
                  (x + w - 12, y + 26)], fill=(30, 120, 60))
    for gy in range(y + 16, y + h - 8, 14):
        draw.line([(x + 6, gy), (x + w - 6, gy)], fill=(200, 212, 200), width=1)
    f = font("sans_b", 15)
    draw.text((x + 8, y + 6), "$83", font=f, fill=INK)


def draw_spark(draw, x, y, w, h):
    """Gemini 4: four-point sparkle on deep blue."""
    draw.rectangle([x, y, x + w, y + h], fill=(24, 44, 90))
    cx, cy = x + w / 2, y + h / 2 - 4
    rr = min(26, int(w * 0.40))
    draw.polygon([(cx, cy - rr), (cx + 8, cy - 8), (cx + rr, cy),
                  (cx + 8, cy + 8), (cx, cy + rr), (cx - 8, cy + 8),
                  (cx - rr, cy), (cx - 8, cy - 8)], fill=(140, 190, 255))
    draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 255, 255))
    f = font("serif_b", 22)
    t = "4"
    draw.text((x + w / 2 - draw.textlength(t, font=f) / 2, y + h - 26), t,
              font=f, fill=(255, 255, 255))


def draw_gavel(draw, x, y, w, h):
    """Seoul: gavel and sound block."""
    draw.rectangle([x, y, x + w, y + h], fill=(232, 222, 196))
    draw.line([(x + 12, y + 14), (x + w - 12, y + h - 28)], fill=(90, 60, 30),
              width=7)
    draw.rectangle([x + w - 30, y + 10, x + w - 10, y + 26], fill=(90, 60, 30),
                   outline=INK)
    draw.rectangle([x + 10, y + h - 22, x + 44, y + h - 10], fill=(120, 90, 50),
                   outline=INK)


def draw_bridge(draw, x, y, w, h):
    """Crimean Bridge: deck, arch, a broken span, smoke."""
    draw.rectangle([x, y, x + w, y + h], fill=(206, 222, 232))
    draw.rectangle([x + 6, y + h - 30, x + w - 6, y + h - 22], fill=(120, 100, 70))
    draw.arc([x + w * 0.28, y + 22, x + w * 0.72, y + h - 20], 180, 360,
             fill=(90, 80, 60), width=4)
    for px in (0.2, 0.42, 0.62, 0.82):
        draw.rectangle([x + w * px - 3, y + h - 44, x + w * px + 3, y + h - 22],
                       fill=(90, 80, 60))
    # broken span + smoke, centre
    draw.line([(x + w * 0.48, y + h - 30), (x + w * 0.52, y + h - 40)],
              fill=INK, width=3)
    for sx, sy, sr in [(0.5, 0.28, 9), (0.54, 0.2, 7), (0.46, 0.18, 6)]:
        draw.ellipse([x + w * sx - sr, y + h * sy - sr, x + w * sx + sr,
                      y + h * sy + sr], fill=(120, 120, 120))


def draw_drought(draw, x, y, w, h):
    """Fiji: sun over cracked dry earth, one water drop."""
    draw.rectangle([x, y, x + w, y + h], fill=(250, 230, 180))
    draw.ellipse([x + w - 30, y + 6, x + w - 8, y + 28], fill=(240, 180, 60))
    draw.polygon([(x, y + h * 0.55), (x + w, y + h * 0.55), (x + w, y + h),
                  (x, y + h)], fill=(214, 178, 130))
    draw.line([(x + 8, y + h * 0.62), (x + w * 0.4, y + h * 0.7),
               (x + w * 0.35, y + h * 0.85)], fill=(120, 90, 60), width=2)
    draw.line([(x + w * 0.6, y + h * 0.6), (x + w * 0.75, y + h * 0.78),
               (x + w * 0.9, y + h * 0.7)], fill=(120, 90, 60), width=2)
    draw.ellipse([x + w / 2 - 6, y + 12, x + w / 2 + 6, y + 30],
                 fill=(60, 130, 200))
    draw.polygon([(x + w / 2 - 6, y + 22), (x + w / 2 + 6, y + 22),
                  (x + w / 2, y + 8)], fill=(60, 130, 200))


def draw_cricket(draw, x, y, w, h):
    """Wellington: stumps, ball, bat."""
    draw.rectangle([x, y, x + w, y + h], fill=(150, 190, 120))
    draw.rectangle([x, y + h - 16, x + w, y + h], fill=(110, 150, 80))
    for i in range(3):
        sx = x + w / 2 - 14 + i * 12
        draw.rectangle([sx, y + h - 52, sx + 6, y + h - 16], fill=(240, 210, 90),
                       outline=INK)
    draw.ellipse([x + 12, y + 12, x + 28, y + 28], fill=(178, 34, 34),
                 outline=(255, 255, 255))
    draw.line([(x + w - 26, y + 10), (x + w - 44, y + h - 40)], fill=(210, 180,
              140), width=8)
    f = font("serif_b", 20)
    draw.text((x + 8, y + h - 24), "113*", font=f, fill=(255, 255, 255))


def draw_downchart(draw, x, y, w, h):
    """Wall Street: a falling red line on a dark trading screen."""
    draw.rectangle([x, y, x + w, y + h], fill=(24, 40, 56))
    for gy in range(y + 12, y + h - 8, 12):
        draw.line([(x + 4, gy), (x + w - 4, gy)], fill=(52, 74, 92), width=1)
    pts = [(x + 5, y + 12), (x + w * 0.28, y + 20), (x + w * 0.45, y + 16),
           (x + w * 0.66, y + h - 26), (x + w - 6, y + h - 12)]
    draw.line(pts, fill=(230, 70, 60), width=3, joint="curve")
    draw.polygon([(x + w - 6, y + h - 12), (x + w - 16, y + h - 14),
                  (x + w - 8, y + h - 22)], fill=(230, 70, 60))
    f = font("sans_b", 11)
    draw.text((x + 5, y + 3), "S&P", font=f, fill=(255, 255, 255))


def draw_tower(draw, x, y, w, h):
    """Riyadh: a tall tower at night, smoke and flame at its crown."""
    draw.rectangle([x, y, x + w, y + h], fill=(28, 38, 58))
    cx = x + w / 2
    draw.polygon([(cx - 13, y + h - 4), (cx - 6, y + 16), (cx + 6, y + 16),
                  (cx + 13, y + h - 4)], fill=(52, 70, 96), outline=INK)
    # lit windows
    for wy in range(y + 22, y + h - 10, 8):
        for wx in (cx - 8, cx, cx + 6):
            if (wy * 7 + int(wx)) % 3:
                draw.point((int(wx), wy), fill=(240, 210, 130))
    # flame + smoke at the crown
    draw.ellipse([cx - 7, y + 8, cx + 7, y + 20], fill=(235, 130, 40))
    draw.ellipse([cx - 4, y + 11, cx + 4, y + 19], fill=(250, 200, 90))
    for sx, sy, sr in [(cx + 8, y + 6, 5), (cx + 14, y + 3, 4), (cx - 10, y + 4, 4)]:
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(130, 130, 135))


def draw_missiles(draw, x, y, w, h):
    """Kyiv at night: missile trails arcing over a dark skyline."""
    draw.rectangle([x, y, x + w, y + h], fill=(18, 28, 48))
    base = y + h - 10
    for bx in range(x, x + w, 14):
        bh = 8 + ((bx * 11) % 16)
        draw.rectangle([bx + 1, base - bh, min(bx + 12, x + w), base],
                       fill=(8, 14, 26))
    draw.rectangle([x, base, x + w, y + h], fill=(8, 14, 26))
    import math
    for (sx, ex, peak) in [(0.06, 0.52, 0.30), (0.30, 0.78, 0.16),
                           (0.55, 0.97, 0.38)]:
        pts = []
        for t in range(21):
            tt = t / 20
            px = x + w * (sx + (ex - sx) * tt)
            py = y + h * (0.06 + (0.72 - 0.06) * tt) - math.sin(tt * math.pi) * h * peak
            pts.append((px, py))
        for px, py in pts[::2]:
            draw.ellipse([px - 1, py - 1, px + 1, py + 1], fill=(240, 200, 130))
        hx, hy = pts[-1]
        draw.ellipse([hx - 3, hy - 3, hx + 3, hy + 3], fill=(255, 240, 200))
    # one burst low over the rooftops
    bx, by = x + w * 0.78, base - 12
    for ang in range(0, 360, 45):
        import math as _m
        draw.line([(bx, by), (bx + 7 * _m.cos(_m.radians(ang)),
                              by + 7 * _m.sin(_m.radians(ang)))],
                  fill=(245, 160, 60), width=2)
    draw.ellipse([bx - 3, by - 3, bx + 3, by + 3], fill=(250, 200, 90))


# ---------------------------------------------------------------- build
def build():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # outer frame
    d.rectangle([M - 6, M - 6, W - M + 6, H - M + 6], outline=INK, width=3)
    d.rectangle([M, M, W - M, H - M], outline=INK, width=1)

    # kicker
    f_kick = font("sans_b", 15)
    f_kick_r = font("sans", 11)
    d.text((M + 8, 24), "THE WORLD IN ONE DAY", font=f_kick, fill=RED)
    rt = "33 STORIES · 6 REGIONS · EVERY ONE CHECKED"
    d.text((W - M - 8 - d.textlength(rt, font=f_kick_r), 27), rt,
           font=f_kick_r, fill=MUTED)
    hline(d, M + 8, W - M - 8, 46, 2)

    # masthead
    f_mast = font("serif_b", 56)
    mast = "Friday 20 November 2026"
    d.text(((W - d.textlength(mast, font=f_mast)) / 2, 50), mast,
           font=f_mast, fill=INK)
    f_sub = font("serif_i", 18)
    sub = "Akvan comes ashore · Three leaders meet in Shenzhen · Wall Street slides 2%"
    d.text(((W - d.textlength(sub, font=f_sub)) / 2, 112), sub,
           font=f_sub, fill=RED)
    hline(d, M + 8, W - M - 8, 134, 2)

    # stat strip
    stats = [
        ("300,000", "moved to shelters\nbefore Akvan"),
        ("70–80", "kmph winds\nat landfall"),
        ("9–6", "ICJ genocide\nverdict"),
        ("$1.84bn", "GTA VI launch\nsales"),
        ("$97.17", "ANT first-day\nclose, +17%"),
        ("589m", "children in\nwar zones"),
    ]
    f_num = font("sans_b", 22)
    f_lab = font("sans", 9)
    cell = CW / 6
    y0, y1 = 140, 178
    for i, (num, lab) in enumerate(stats):
        cx = M + cell * i
        nw = d.textlength(num, font=f_num)
        d.text((cx + (cell - nw) / 2, y0), num, font=f_num,
               fill=RED if i % 2 == 0 else INK)
        for j, ll in enumerate(lab.split("\n")):
            lw = d.textlength(ll, font=f_lab)
            d.text((cx + (cell - lw) / 2, y0 + 25 + j * 11), ll,
                   font=f_lab, fill=MUTED)
        if i:
            vline(d, cx, y0 + 2, y1 - 4, 1, MUTED)
    hline(d, M + 8, W - M - 8, 192, 2)

    # lead scene
    draw_lead_scene(d, M + 8, 198, CW - 16, 100)
    y = 304
    f_tag = font("sans_b", 12)
    d.text((M + 8, y), "1 · SHENZHEN — DIPLOMACY", font=f_tag, fill=RED)
    f_head = font("serif_b", 25)
    d.text((M + 8, y + 16), "Trump, Xi and Putin meet three-way for the first time",
           font=f_head, fill=INK)
    f_deck = font("serif", 13)
    deck = ("The three leaders issue a four-point declaration toward peace — Ukraine "
            "first on the agenda — as APEC adopts its Shenzhen Outlook beside them.")
    text_block(d, M + 8, y + 44, deck, f_deck, CW - 16, leading=16, max_lines=2)
    hline(d, M + 8, W - M - 8, 384, 2)

    # 3 large panels
    big = [
        (2, "ODISHA — STORM", "Cyclone Akvan comes ashore",
         "Crossed the coast near Gopalpur on Friday morning, weaker than feared "
         "at 70–80 kmph gusting 90. Some 300,000 people were moved to shelters; "
         "69 trains cancelled.",
         draw_cyclone),
        (3, "WASHINGTON — IRAN", "Trump puts the Iran decision off to 2027",
         "“I am not rushing into any decision,” he tells Axios on Air Force One. "
         "“We will see what happens after the beginning of the year.”",
         draw_calendar),
        (4, "THE HAGUE — LAW", "Myanmar guilty of genocide",
         "The world court rules 9–6 — the first state ever held liable for genocide. "
         "Some 10,000 Rohingya were killed; 700,000 fled in 2017.",
         draw_court),
    ]
    pw = (CW - 16 - 24) / 3
    f_ptag = font("sans_b", 11)
    f_phead = font("serif_b", 16)
    f_pbody = font("serif", 11)
    for i, (n, tag, head, body, art) in enumerate(big):
        px = int(M + 8 + i * (pw + 12))
        py = 390
        art(d, px, py, pw, 56)
        d.text((px, py + 62), f"{n} · {tag}", font=f_ptag, fill=RED)
        yy = text_block(d, px, py + 78, head, f_phead, pw, leading=18, max_lines=2)
        text_block(d, px, yy + 4, body, f_pbody, pw, leading=14, max_lines=3)
    hline(d, M + 8, W - M - 8, 554, 2)

    # 12 small panels
    small = [
        (5, "ANTALYA — CLIMATE", "COP31 drags past its close, no deal",
         "The final day opens with fossil fuels still cut from the draft; talks run into the night.",
         draw_globe_doc),
        (6, "NEW YORK — MARKETS", "S&P 500 falls 2% in fifth straight loss",
         "Indexes drop over 2% despite Anthropic's record debut as AI-valuation worries bite.",
         draw_downchart),
        (7, "RIYADH — GULF", "Missile damages Riyadh's tallest tower",
         "The Houthis claim strikes on four Saudi targets as the Gulf attacks widen.",
         draw_tower),
        (8, "KYIV — WAR", "Ballistic missiles strike Kyiv overnight",
         "Explosions and fires in several districts, hours after the barrage that hit two embassies.",
         draw_missiles),
        (9, "KYIV — WAR", "Strikes damage two embassies",
         "Austrian and Dutch missions hit; the EU summons Russian envoys in protest.",
         draw_embassy),
        (10, "GAMES", "GTA VI launches to record sales",
         "Sensor Tower: 19m copies, $1.84bn by launch morning — the biggest launch ever.",
         draw_gta),
        (11, "NEW YORK — MARKETS", "Anthropic's $81.3bn IPO at $83",
         "ANT opens +34%, then closes its first day at $97.17 — up 17% on the offer price.",
         draw_chart),
        (12, "TECH", "Google ships Gemini 4 Neon",
         "A 1M-token window at $3/$15 — and the top score on the Artificial Analysis index.",
         draw_spark),
        (13, "SEOUL — LAW", "Han's 15-year term overturned",
         "The 15-year term over the 2024 martial-law case is quashed; a retrial is ordered.",
         draw_gavel),
        (14, "CRIMEA — WAR", "Crimean Bridge hit again",
         "A Ukrainian attack halts rail traffic; Putin vows retaliation.",
         draw_bridge),
        (15, "SUVA — CLIMATE", "Fiji declares a disaster",
         "El Niño drought: a one-month emergency; FJ$20m for water as rain stays away.",
         draw_drought),
        (16, "WELLINGTON — CRICKET", "Nicholls 113* leads NZ to 243/5",
         "New Zealand fight back on day one of the first Test at the Basin Reserve.",
         draw_cricket),
    ]
    spw = (CW - 16 - 24) / 3
    f_stag = font("sans_b", 9)
    f_shead = font("serif_b", 13)
    f_sbody = font("serif", 10)
    for i, (n, tag, head, body, art) in enumerate(small):
        row, col = divmod(i, 3)
        px = int(M + 8 + col * (spw + 12))
        py = 560 + row * 76
        art(d, px, py, 58, 68)
        tx = px + 66
        tw = spw - 66
        d.text((tx, py), f"{n} · {tag}", font=f_stag, fill=RED)
        yy = text_block(d, tx, py + 12, head, f_shead, tw, leading=15, max_lines=2)
        text_block(d, tx, yy + 3, body, f_sbody, tw, leading=12, max_lines=2)
    hline(d, M + 8, W - M - 8, 861, 2)

    # brief list (2 columns, one line each)
    f_bhead = font("sans_b", 12)
    d.text((M + 8, 867), "ALSO ON FRIDAY 20 NOVEMBER — 17 MORE STORIES",
           font=f_bhead, fill=RED)
    f_src = font("sans", 9)
    src = "Sources: Reuters, AP, BBC, AFP, IMD, IAEA, UN"
    d.text((W - M - 8 - d.textlength(src, font=f_src), 869), src,
           font=f_src, fill=MUTED)
    briefs = [
        "17 RIYADH — Missiles intercepted over Riyadh again; Gulf attacks widen.",
        "18 NEW DELHI — Modi meets the Prince and Princess of Wales.",
        "19 DHAKA — Fire at Muhammad Yunus's ancestral home; arson suspected.",
        "20 MUMBAI — Sensex +1.21%, Nifty +1.14%; Nifty crosses 25,400.",
        "21 CANBERRA — Australia sanctions 3 settlers, 4 groups over the West Bank.",
        "22 WASHINGTON — Senate rejects Iran war-powers resolution, 51–48.",
        "23 VIENNA — IAEA: North Korea is expanding Yongbyon enrichment.",
        "24 SHENZHEN — Trump: Iran's arsenal “down to 12–13%”; US holds Hormuz.",
        "25 NEW DELHI — Modi opens FICCI's centenary; growth to 2047 in focus.",
        "26 BEIJING — Xi urges APEC to back open trade and new technology.",
        "27 WASHINGTON — Iran war has cost US taxpayers about $48.3bn so far.",
        "28 MANAMA — Iran claims drone strikes on a US base; Bahrain says no.",
        "29 HORMUZ — Tanker catches fire after hitting a mine east of the strait.",
        "30 WASHINGTON — White House names Kirsten Davies national cyber director.",
        "31 GENEVA — 589m children, nearly 1 in 4, live in war zones — a record.",
        "32 GENOA — Drones shut Genoa airport for two hours on Thursday evening.",
        "33 TBILISI — Gas blast toll reaches six; a girl of three pulled out alive.",
    ]
    f_brief = font("serif", 9)
    bx, by = M + 8, 885
    colw = 476
    for i, b in enumerate(briefs):
        col, row = divmod(i, 9)
        x = bx + col * (colw + 8)
        y = by + row * 10.5
        d.text((x, y), b, font=f_brief, fill=INK)

    # DATE CHECK strip (one line)
    hline(d, M + 8, W - M - 8, 982, 1, RED)
    f_dc = font("sans_b", 9)
    d.text((M + 8, 986), "DATE CHECK", font=f_dc, fill=RED)
    f_dct = font("serif", 9)
    dc = ("The Shenzhen summit, the ICJ verdict, GTA VI's launch and Anthropic's "
          "debut broke Thu 19 Nov (Friday in Asia-Pacific time). Friday's own news: "
          "Akvan's landfall, Wall Street's slide, COP31's final day.")
    text_block(d, M + 8 + d.textlength("DATE CHECK  ", font=f_dc), 986, dc,
               f_dct, CW - 16 - d.textlength("DATE CHECK  ", font=f_dc),
               leading=11, max_lines=1)
    return img


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    img = build()
    img.save(os.path.join(out_dir, "entry.png"), format="PNG",
             optimize=True)
    print("wrote", os.path.join(out_dir, "entry.png"), img.size)


if __name__ == "__main__":
    main()
