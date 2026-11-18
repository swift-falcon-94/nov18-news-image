#!/usr/bin/env python3
"""Draw one front page summing up the world news of 18 November 2026.

Standard library only. No network, no fonts, no randomness: the same run
always writes the same PNG bytes. The picture is drawn with a small 5x7
bitmap font and flat shapes, so every word stays crisp at small sizes.

Output: $MAKEFUN_OUTPUT_DIR/entry.png, or /output/entry.png.
"""

import math
import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (246, 241, 227)
INK = (25, 25, 25)
WHITE = (255, 255, 255)
RED = (163, 22, 33)
NAVY = (22, 50, 79)
SEA = (42, 107, 138)
SKY = (196, 222, 235)
SAND = (217, 200, 154)
GOLD = (201, 162, 39)
TEAL = (27, 107, 90)
GREY = (107, 107, 107)
LIGHT = (232, 226, 208)
DARKRED = (120, 16, 24)

# 5x7 bitmap glyphs. Each glyph is 7 rows of 5 bits, '#' on, '.' off.
FONT = {
    'A': ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    'B': ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    'C': ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    'D': ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    'E': ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    'F': ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    'G': ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    'H': ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    'I': ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    'J': ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    'K': ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    'L': ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    'M': ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    'N': ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    'O': ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    'P': ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    'Q': ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    'R': ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    'S': ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    'T': ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    'U': ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    'V': ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    'W': ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "11110", "10001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    'd': ("00001", "00001", "01111", "10001", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    'h': ("10000", "10000", "11110", "10001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "11110", "10001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    'q': ("00000", "00000", "01111", "10001", "01111", "00001", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("01000", "01000", "11100", "01000", "01000", "01001", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    '4': ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    '5': ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    '6': ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    '7': ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    '8': ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    '9': ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    ' ': ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    '.': ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ',': ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ':': ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ';': ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    '!': ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    '?': ("01110", "10001", "00001", "00010", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
}


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.buf = bytearray(w * h * 3)
        self.fill_rect(0, 0, w, h, bg)

    def set_px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        for yy in range(max(0, y), min(self.h, y + h)):
            base = (yy * self.w + max(0, x)) * 3
            row = bytes(color) * (min(self.w, x + w) - max(0, x))
            self.buf[base:base + len(row)] = row

    def rect(self, x, y, w, h, color, t=1):
        self.fill_rect(x, y, w, t, color)
        self.fill_rect(x, y + h - t, w, t, color)
        self.fill_rect(x, y, t, h, color)
        self.fill_rect(x + w - t, y, t, h, color)

    def hline(self, x, y, w, color, t=1):
        self.fill_rect(x, y, w, t, color)

    def line(self, x0, y0, x1, y1, color, t=1):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            for a in range(t):
                for b in range(t):
                    self.set_px(x0 + a, y0 + b, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                    self.set_px(xx, yy, color)

    def ring(self, cx, cy, r, color, t=2):
        for yy in range(cy - r - t, cy + r + t + 1):
            for xx in range(cx - r - t, cx + r + t + 1):
                d2 = (xx - cx) ** 2 + (yy - cy) ** 2
                if (r - t) ** 2 <= d2 <= r * r:
                    self.set_px(xx, yy, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                if ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1:
                    self.set_px(xx, yy, color)

    def polygon(self, pts, color):
        ys = [p[1] for p in pts]
        for yy in range(min(ys), max(ys) + 1):
            nodes = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    nodes.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            nodes.sort()
            for i in range(0, len(nodes) - 1, 2):
                for xx in range(int(nodes[i]), int(nodes[i + 1]) + 1):
                    self.set_px(xx, yy, color)

    def burst(self, cx, cy, r, color):
        spikes = 12
        for k in range(spikes):
            ang = 2 * math.pi * k / spikes
            x1 = int(cx + r * 1.15 * math.cos(ang))
            y1 = int(cy + r * 1.15 * math.sin(ang))
            self.line(cx, cy, x1, y1, color, 3)
        self.disc(cx, cy, int(r * 0.55), color)
        self.disc(cx, cy, int(r * 0.28), GOLD)


def text_width(s, scale):
    if not s:
        return 0
    return len(s) * 6 * scale - scale


def draw_text(cv, x, y, s, scale, color):
    cx = x
    for ch in s:
        glyph = FONT.get(ch, FONT[' '])
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    cv.fill_rect(cx + col * scale, y + row * scale,
                                 scale, scale, color)
        cx += 6 * scale
    return cx


def draw_centered(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_width(s, scale) // 2, y, s, scale, color)


def draw_right(cv, rx, y, s, scale, color):
    draw_text(cv, rx - text_width(s, scale), y, s, scale, color)


def wrap(s, scale, max_w):
    words = s.split(' ')
    lines = []
    cur = ''
    for word in words:
        trial = word if not cur else cur + ' ' + word
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def kicker(cv, x, y, s, scale, bg, fg):
    pad = 8
    w = text_width(s, scale) + pad * 2
    h = 7 * scale + pad
    cv.fill_rect(x, y, w, h, bg)
    draw_text(cv, x + pad, y + pad // 2, s, scale, fg)
    return w


def draw_gulf_map(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, SEA)
    cv.rect(x, y, w, h, INK, 2)
    # Land masses: Arabia (left/bottom) and Iran (top/right).
    cv.polygon([(x, y + h), (x, y + 168), (x + 90, y + 150),
                (x + 120, y + h)], SAND)
    cv.polygon([(x + 110, y), (x + w, y), (x + w, y + 70),
                (x + 190, y + 96), (x + 120, y + 60)], SAND)
    # Qeshm island.
    cv.ellipse(x + 175, y + 118, 52, 16, SAND)
    cv.burst(x + 175, y + 112, 16, RED)
    draw_text(cv, x + 138, y + 138, "QESHM", 2, WHITE)
    # Bahrain and Kuwait dots with labels.
    cv.disc(x + 52, y + 128, 7, WHITE)
    cv.disc(x + 52, y + 128, 4, RED)
    draw_text(cv, x + 12, y + 104, "BAHRAIN", 2, WHITE)
    cv.disc(x + 78, y + 62, 7, WHITE)
    cv.disc(x + 78, y + 62, 4, RED)
    draw_text(cv, x + 18, y + 76, "KUWAIT", 2, WHITE)
    # Dashed response arrows from the island toward the dots.
    cv.line(x + 150, y + 100, x + 96, y + 72, WHITE, 2)
    cv.line(x + 140, y + 112, x + 72, y + 122, WHITE, 2)
    draw_text(cv, x + 118, y + h - 26, "HORMUZ STRAIT", 2, WHITE)


def draw_bridge_scene(cv, x, y, w, h):
    cv.fill_rect(x, y, w, h, SKY)
    cv.fill_rect(x, y + h - 18, w, 18, SEA)
    cv.rect(x, y, w, h, INK, 2)
    deck = y + 12
    # Deck with a gap in the middle.
    cv.fill_rect(x + 8, deck, w // 2 - 34, 7, INK)
    cv.fill_rect(x + w // 2 + 26, deck, w // 2 - 34, 7, INK)
    # Small standing hump on the left, fallen arch in the water.
    cv.line(x + 40, deck, x + 80, y + 3, INK, 3)
    cv.line(x + 80, y + 3, x + 120, deck, INK, 3)
    cv.line(x + w // 2 + 16, y + h - 3, x + w // 2 + 58, y + h - 15, INK, 3)
    cv.line(x + w // 2 + 58, y + h - 15, x + w // 2 + 100, y + h - 3, INK, 3)
    # Pylons.
    cv.fill_rect(x + 24, deck + 7, 6, 10, INK)
    cv.fill_rect(x + w - 30, deck + 7, 6, 10, INK)


def draw_route(cv, x, y, w):
    draw_text(cv, x, y, "MANILA", 2, INK)
    x0 = x + text_width("MANILA", 2) + 12
    x1 = x + w - text_width("SHENZHEN", 2) - 26
    cv.line(x0, y + 7, x1, y + 7, RED, 3)
    cv.polygon([(x1, y + 1), (x1 + 14, y + 7), (x1, y + 13)], RED)
    draw_text(cv, x1 + 20, y, "SHENZHEN", 2, INK)


def draw_page():
    cv = Canvas(W, H, PAPER)
    cv.rect(10, 10, W - 20, H - 20, INK, 4)
    cv.rect(20, 20, W - 40, H - 40, INK, 1)

    # Masthead.
    draw_centered(cv, W // 2, 34, "THE WORLD TODAY", 9, INK)
    cv.hline(24, 110, W - 48, INK, 4)
    cv.hline(24, 117, W - 48, INK, 2)
    draw_text(cv, 24, 128, "Wednesday, 18 November 2026", 3, RED)
    draw_right(cv, W - 24, 128, "ONE DAY, ONE IMAGE", 3, INK)
    cv.hline(24, 156, W - 48, INK, 2)

    # Lead story: the Gulf.
    cv.fill_rect(24, 168, W - 48, 268, WHITE)
    cv.rect(24, 168, W - 48, 268, INK, 3)
    kicker(cv, 40, 184, "THE GULF", 3, RED, WHITE)
    draw_text(cv, 40, 222, "US JETS HIT IRAN", 6, INK)
    draw_text(cv, 40, 270, "SITE ON QESHM", 6, INK)
    deck = ["Iran fired drones at US sites",
            "in Bahrain and Kuwait. Gulf",
            "states say they intercepted",
            "them. Source: Reuters."]
    for i, line in enumerate(deck):
        draw_text(cv, 40, 326 + i * 26, line, 3, INK)
    draw_gulf_map(cv, 700, 184, 284, 236)

    # Second row: Kerch bridge and Manila.
    y2 = 452
    h2 = 254
    cv.fill_rect(24, y2, 476, h2, WHITE)
    cv.rect(24, y2, 476, h2, INK, 3)
    kicker(cv, 40, y2 + 16, "UKRAINE", 3, RED, WHITE)
    draw_text(cv, 40, y2 + 54, "BRIDGE ARCH", 5, INK)
    draw_text(cv, 40, y2 + 94, "FALLS INTO SEA", 5, INK)
    for i, line in enumerate(["Second strike in two days,",
                              "Ukraine says. Governor:",
                              "two killed, road shut."]):
        draw_text(cv, 40, y2 + 138 + i * 18, line, 2, INK)
    draw_bridge_scene(cv, 40, y2 + 196, 444, 46)

    cv.fill_rect(524, y2, 476, h2, WHITE)
    cv.rect(524, y2, 476, h2, INK, 3)
    kicker(cv, 540, y2 + 16, "MANILA TO SHENZHEN", 3, NAVY, WHITE)
    draw_text(cv, 540, y2 + 54, "TRUMP VOWS CLOSER", 4, INK)
    draw_text(cv, 540, y2 + 88, "DEFENCE TIES WITH", 4, INK)
    draw_text(cv, 540, y2 + 122, "THE PHILIPPINES", 4, INK)
    for i, line in enumerate(["Quad leaders met Tuesday on",
                              "minerals, security and AI.",
                              "Trilateral with Xi and Putin",
                              "due Thursday. (Reuters)"]):
        draw_text(cv, 540, y2 + 156 + i * 18, line, 2, INK)
    draw_route(cv, 540, y2 + 232, 444)

    # Third story: Ebola in DR Congo.
    y3 = 722
    cv.fill_rect(24, y3, W - 48, 156, NAVY)
    cv.rect(24, y3, W - 48, 156, INK, 3)
    kicker(cv, 40, y3 + 14, "DR CONGO - EBOLA", 3, GOLD, INK)
    draw_text(cv, 40, y3 + 54, "CASES MORE THAN DOUBLE", 4, WHITE)
    draw_text(cv, 40, y3 + 96, "7 in 10 under-5s with Ebola died.", 3, GOLD)
    draw_text(cv, 40, y3 + 124, "WHO: 67 health zones, 8 provinces.", 2, WHITE)
    # Bars on the right.
    bx = 640
    draw_text(cv, bx, y3 + 18, "CASES  11,000+", 3, WHITE)
    cv.fill_rect(bx, y3 + 46, 320, 20, RED)
    cv.rect(bx, y3 + 46, 320, 20, WHITE, 1)
    draw_text(cv, bx, y3 + 78, "DEATHS  5,400+", 3, WHITE)
    cv.fill_rect(bx, y3 + 106, 157, 20, GOLD)
    cv.rect(bx, y3 + 106, 157, 20, WHITE, 1)

    # Footer: also today.
    y4 = 890
    draw_text(cv, 24, y4, "ALSO TODAY", 3, RED)
    draw_right(cv, W - 24, y4, "DRAWN IN CODE - NO PHOTOS", 2, GREY)
    cv.hline(24, y4 + 26, W - 48, INK, 2)
    briefs = [
        "ALASKA - Peltola wins; Democrats 56-44 in the Senate.",
        "CYCLONE XAVIER - Cat 5, gusts 315 km/h, near N. Cook Islands.",
        "SIBERIA - An-12 crash: ministry says 19 dead.",
        "CRICKET - Dhoni retires as IPL player; CSK mentor in 2027.",
    ]
    for i, b in enumerate(briefs):
        bx = 24 if i % 2 == 0 else 524
        by = y4 + 36 + (i // 2) * 42
        for j, line in enumerate(wrap(b, 2, 444)):
            draw_text(cv, bx, by + j * 19, line, 2, INK)
    return cv


def write_png(path, cv):
    raw = bytearray()
    stride = cv.w * 3
    for y in range(cv.h):
        raw.append(0)
        raw += cv.buf[y * stride:(y + 1) * stride]
    data = zlib.compress(bytes(raw), 9)

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag +
                payload + struct.pack(">I", zlib.crc32(tag + payload) & 0xffffffff))

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) +
           chunk(b"IDAT", data) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    os.makedirs(outdir, exist_ok=True)
    write_png(os.path.join(outdir, "entry.png"), draw_page())


if __name__ == "__main__":
    main()
