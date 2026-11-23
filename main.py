#!/usr/bin/env python3
"""The Monday Globe -- Monday 23 November 2026 in one image.

Draws a newspaper front page, pixel by pixel, with the Python 3
standard library only. No network, no photographs, no stock imagery.
Deterministic: running it twice writes byte-identical PNG bytes.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import zlib

W, H = 1024, 768
OUT = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
PATH = os.path.join(OUT, "entry.png")

PAPER = (250, 246, 235)
INK = (22, 22, 22)
RED = (178, 34, 34)
BLUE = (28, 68, 128)
GREY = (110, 108, 100)
LIGHT = (238, 232, 218)

# ---------------------------------------------------------------- canvas
buf = bytearray(PAPER[0] for _ in range(W * H * 3))
for i in range(W * H):
    buf[i * 3:i * 3 + 3] = bytes(PAPER)


def set_px(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        buf[i:i + 3] = bytes(c)


def rect(x, y, w, h, c):
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            set_px(xx, yy, c)


def hline(x, y, w, c):
    rect(x, y, w, 1, c)


def vline(x, y, h, c):
    rect(x, y, 1, h, c)


def line(x0, y0, x1, y1, c):
    dx, dy = abs(x1 - x0), abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        set_px(x0, y0, c)
        if x0 == x1 and y0 == y1:
            return
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def circle(cx, cy, r, c, fill=True):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d = (xx - cx) ** 2 + (yy - cy) ** 2
            if fill and d <= r * r:
                set_px(xx, yy, c)
            elif not fill and r * r - 2 * r <= d <= r * r:
                set_px(xx, yy, c)


def tri(x0, y0, x1, y1, x2, y2, c):
    # filled triangle via horizontal scanlines
    pts = sorted([(x0, y0), (x1, y1), (x2, y2)], key=lambda p: p[1])
    (ax, ay), (bx, by), (cx, cy) = pts
    for yy in range(ay, cy + 1):
        if yy < by:
            t1 = (yy - ay) / max(1, by - ay)
            xa = ax + (bx - ax) * t1
        else:
            t1 = (yy - by) / max(1, cy - by)
            xa = bx + (cx - bx) * t1
        t2 = (yy - ay) / max(1, cy - ay)
        xb = ax + (cx - ax) * t2
        x_lo, x_hi = int(min(xa, xb)), int(max(xa, xb))
        hline(x_lo, yy, x_hi - x_lo + 1, c)


def blend(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------- 5x7 font
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "[": ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    "]": ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
}
CHAR_W = 6  # 5 px glyph + 1 px gap


def text_w(s, scale):
    return len(s) * CHAR_W * scale - scale


def draw_text(x, y, s, scale, c):
    s = s.upper()
    for ci, ch in enumerate(s):
        g = FONT.get(ch, FONT["?"])
        ox = x + ci * CHAR_W * scale
        for r in range(7):
            for cc in range(5):
                if g[r][cc] == "1":
                    rect(ox + cc * scale, y + r * scale, scale, scale, c)
    return x + text_w(s, scale)


def draw_centered(y, s, scale, c):
    draw_text((W - text_w(s, scale)) // 2, y, s, scale, c)


def wrap(s, width_px, scale):
    words = s.split(" ")
    lines, cur = [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if text_w(t, scale) <= width_px:
            cur = t
        else:
            if cur:
                lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def para(x, y, s, width_px, scale, c, lh=None):
    lh = lh or (9 * scale)
    for ln in wrap(s, width_px, scale):
        draw_text(x, y, ln, scale, c)
        y += lh
    return y


# ---------------------------------------------------------------- masthead
hline(24, 14, W - 48, INK)
hline(24, 17, W - 48, INK)
draw_centered(28, "THE MONDAY GLOBE", 6, INK)
hline(24, 78, W - 48, INK)
draw_text(24, 86, "NO. 327", 2, GREY)
draw_centered(86, "MONDAY 23 NOVEMBER 2026", 2, RED)
draw_text(W - 24 - text_w("PRICE: ONE DAY'S NEWS", 2), 86,
          "PRICE: ONE DAY'S NEWS", 2, GREY)
hline(24, 104, W - 48, INK)
rect(24, 107, W - 48, 3, INK)

# ---------------------------------------------------------------- headline
draw_centered(122, "COP31 COLLAPSES", 5, INK)
draw_centered(160, "WITHOUT A DEAL", 5, INK)
draw_centered(206, "CLIMATE SUMMIT IN ANTALYA ENDS AFTER THE LONGEST TALKS IN HISTORY -", 2, INK)
draw_centered(224, "NO AGREEMENT ON FOSSIL FUELS OR FINANCE", 2, INK)

# ------------------------------------------------------- illustration panel
IX, IY, IW, IH = 24, 246, 976, 190
rect(IX, IY, IW, IH, (244, 214, 170))
# sunset sky bands
SKY_TOP = (226, 122, 62)
SKY_MID = (240, 170, 96)
SKY_LOW = (248, 214, 150)
for yy in range(IY, IY + 96):
    t = (yy - IY) / 96.0
    c = blend(SKY_TOP, SKY_MID, t) if t < 0.55 else blend(SKY_MID, SKY_LOW, (t - 0.55) / 0.45)
    hline(IX, yy, IW, c)
# sun, low over the sea
circle(512, IY + 88, 34, (255, 236, 170))
circle(512, IY + 88, 27, (255, 214, 120))
# distant mountains, solid ridges
tri(IX, IY + 96, IX + 150, IY + 44, IX + 300, IY + 96, (168, 104, 78))
tri(IX + 220, IY + 96, IX + 380, IY + 56, IX + 540, IY + 96, (150, 90, 70))
tri(IX + 470, IY + 96, IX + 640, IY + 40, IX + 810, IY + 96, (168, 104, 78))
tri(IX + 720, IY + 96, IX + 860, IY + 58, IX + IW, IY + 96, (150, 90, 70))
# sea
rect(IX, IY + 96, IW, 34, (52, 96, 128))
for sy in range(IY + 98, IY + 128, 6):
    for sx in range(IX + ((sy * 13) % 40), IX + IW, 40):
        hline(sx, sy, 22, (120, 170, 200))
# sun reflection on the water
for ry in range(IY + 98, IY + 128, 4):
    wdt = 24 + (ry - IY - 98) * 2
    hline(512 - wdt // 2, ry, wdt, (255, 220, 140))
# conference hall: long building with arched windows
rect(IX + 90, IY + 130, IW - 180, 44, (96, 84, 70))
rect(IX + 90, IY + 130, IW - 180, 5, (70, 60, 50))
for wx in range(IX + 116, IX + IW - 116, 44):
    rect(wx, IY + 142, 24, 22, (255, 220, 130))
    rect(wx, IY + 142, 24, 6, (200, 160, 80))
# flag poles and drooping flags on the roof
for fx in range(IX + 130, IX + IW - 130, 90):
    vline(fx, IY + 106, 24, INK)
    rect(fx, IY + 108, 30, 10, (28, 68, 128) if (fx // 90) % 2 == 0 else (178, 34, 34))
# rows of empty chairs in the foreground
for row in range(2):
    cy = IY + 178 + row * 8
    for cx in range(IX + 40, IX + IW - 40, 34):
        rect(cx, cy, 20, 3, (60, 52, 44))
        rect(cx + 2, cy + 3, 3, 6, (60, 52, 44))
        rect(cx + 15, cy + 3, 3, 6, (60, 52, 44))
# caption bar under the picture
rect(IX, IY + IH - 2, IW, 2, INK)
draw_text(IX + 4, IY + IH + 8, "THE HALL IN ANTALYA, EMPTY AS THE FINAL TEXT: DELEGATES LEFT WITHOUT A DEAL AFTER TWO DAYS OF OVERTIME.", 1, GREY)

# ---------------------------------------------------------------- columns
CY = 462
# left column: lead story
LX, LW = 24, 520
draw_text(LX, CY, "ANTALYA, TURKEY -", 2, RED)
y = para(LX, CY + 22,
          "The UN COP31 climate summit ended on Sunday without a deal to "
          "tackle climate change, after two days of overtime talks broke "
          "down over fossil fuels and money. The European Union and about "
          "130 other parties rejected a final text that did not mention "
          "fossil fuels at all.", LW, 2, INK)
y = para(LX, y + 8,
          "The talks were due to finish on Friday but ran until late "
          "Sunday, the longest UN climate conference in history. "
          "Negotiators will try again next year.", LW, 2, INK)

# right column: three side stories
RX, RW = 580, 420
vline(560, CY, 232, GREY)
ry = CY
for kicker, head, body in [
    ("UKRAINE", "SEA DRONES SINK RUSSIAN WARSHIP OFF LIBYA",
     "Ukraine said its naval drones sank the Russian corvette Merkury at "
     "Benghazi naval base. The toll from a Russian strike on flats in "
     "Dymer, near Kyiv, rose to 11."),
    ("THE GULF", "TRUMP DARES IRAN TO TEST THE BLOCKADE",
     "President Trump warned Iranian vessels testing the US naval "
     "blockade would end up \"at the bottom of the sea\", and signalled "
     "strikes could resume after the New Year."),
    ("MARKETS", "AI SELL-OFF RATTLES WORLD MARKETS",
     "Japan's Nikkei fell 5.06%; the S and P 500 dropped 3.7%."),
]:
    draw_text(RX, ry, kicker, 2, RED)
    ry = para(RX, ry + 20, head, RW, 2, INK)
    ry = para(RX, ry + 4, body, RW, 1, INK, lh=10)
    ry += 6

# ---------------------------------------------------------------- ticker
TY = 706
rect(24, TY, W - 48, 44, INK)
draw_text(36, TY + 7, "DEMOCRATS WIN 258 HOUSE SEATS - LARGEST MAJORITY SINCE 1992", 2, (250, 246, 235))
draw_text(36, TY + 25, "INDONESIA FACTORY FIRE: 24 DEAD, 30 MISSING - BOLSONARO IN INTENSIVE CARE - MARQUEZ WINS 8TH MOTOGP TITLE", 1, (200, 196, 182))
hline(24, TY + 50, W - 48, INK)
draw_centered(758, "THE MONDAY GLOBE - MONDAY 23 NOVEMBER 2026", 1, GREY)

# ---------------------------------------------------------------- write PNG
os.makedirs(OUT, exist_ok=True)


def chunk(kind, data):
    c = struct.pack(">I", len(data)) + kind + data
    return c + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


raw = b"".join(b"\x00" + bytes(buf[y * W * 3:(y + 1) * W * 3]) for y in range(H))
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(raw, 9))
       + chunk(b"IEND", b""))
with open(PATH, "wb") as f:
    f.write(png)
print("wrote", PATH, len(png), "bytes")
