#!/usr/bin/env python3
"""The World Today -- one-page dense summary of world news, Wednesday
18 November 2026. Pure stdlib, fully deterministic: same input always
produces byte-identical PNG output. Draws a newspaper front page at
1024x1024 with 34 verified stories, a dotted world map, and sources.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
Writes entry.png into MAKEFUN_OUTPUT_DIR (or /output, or ./out).
Set FONTTEST=1 to render a glyph test sheet instead (debug only).
"""
import math
import os
import struct
import zlib

W, H = 1024, 1024

# ---------------------------------------------------------------- palette
PAPER = (246, 241, 229)
INK = (28, 26, 23)
CARD = (255, 255, 255)
BORDER = (217, 210, 192)
NAVY = (21, 34, 56)
GOLD = (201, 155, 63)
RED = (179, 32, 44)
BLUE = (30, 78, 158)
GREEN = (30, 122, 70)
TEAL = (15, 123, 122)
AMBER = (200, 127, 10)
MAPBG = (216, 229, 233)
DOTGRAY = (138, 132, 120)
TINT = {
    "red": (249, 232, 233),
    "blue": (232, 238, 249),
    "green": (231, 242, 235),
    "teal": (230, 242, 241),
    "amber": (251, 240, 220),
}
CATCOLOR = {"red": RED, "blue": BLUE, "green": GREEN, "teal": TEAL,
            "amber": AMBER}

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 pixels, "#" = on. Hand-drawn for this page.
def _g(rows):
    return tuple(tuple(1 if c == "#" else 0 for c in r) for r in rows)

FONT = {
    " ": _g([".....", ".....", ".....", ".....", ".....", ".....", "....."]),
    "!": _g(["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."]),
    '"': _g([".#.#.", ".#.#.", ".....", ".....", ".....", ".....", "....."]),
    "$": _g(["..#..", ".####", "#.#...", ".###.", "...#.", "####.", "..#.."]),
    "%": _g(["##..#", "##.#.", "...#.", "..#..", ".#...", "#.##.", "#..##"]),
    "&": _g([".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"]),
    "'": _g(["..#..", "..#..", ".#...", ".....", ".....", ".....", "....."]),
    "(": _g(["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."]),
    ")": _g([".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."]),
    "+": _g([".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."]),
    ",": _g([".....", ".....", ".....", ".....", ".##..", "..#..", ".#..."]),
    "-": _g([".....", ".....", ".....", "#####", ".....", ".....", "....."]),
    ".": _g([".....", ".....", ".....", ".....", ".....", ".##..", ".##.."]),
    "/": _g(["....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."]),
    "0": _g([".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."]),
    "1": _g(["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."]),
    "2": _g([".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"]),
    "3": _g(["#####", "...#.", "..#..", "...#.", "....#", "#...#", ".###."]),
    "4": _g(["...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."]),
    "5": _g(["#####", "#....", "####.", "....#", "....#", "#...#", ".###."]),
    "6": _g(["..##.", ".#...", "#....", "####.", "#...#", "#...#", ".###."]),
    "7": _g(["#####", "....#", "...#.", "..#..", ".#...", ".#...", ".#..."]),
    "8": _g([".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."]),
    "9": _g([".###.", "#...#", "#...#", ".####", "....#", "...#.", ".##.."]),
    ":": _g([".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."]),
    ";": _g([".....", ".##..", ".##..", ".....", ".##..", "..#..", ".#..."]),
    "=": _g([".....", ".....", "#####", ".....", "#####", ".....", "....."]),
    "?": _g([".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."]),
    "|": _g(["..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."]),
    "A": _g([".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"]),
    "B": _g(["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."]),
    "C": _g([".###.", "#...#", "#....", "#....", "#....", "#...#", ".###."]),
    "D": _g(["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."]),
    "E": _g(["#####", "#....", "#....", "####.", "#....", "#....", "#####"]),
    "F": _g(["#####", "#....", "#....", "####.", "#....", "#....", "#...."]),
    "G": _g([".###.", "#...#", "#....", "#.###", "#...#", "#...#", ".####"]),
    "H": _g(["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"]),
    "I": _g([".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."]),
    "J": _g(["..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."]),
    "K": _g(["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"]),
    "L": _g(["#....", "#....", "#....", "#....", "#....", "#....", "#####"]),
    "M": _g(["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"]),
    "N": _g(["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"]),
    "O": _g([".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."]),
    "P": _g(["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."]),
    "Q": _g([".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"]),
    "R": _g(["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"]),
    "S": _g([".####", "#....", "#....", ".###.", "....#", "....#", "####."]),
    "T": _g(["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."]),
    "U": _g(["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."]),
    "V": _g(["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."]),
    "W": _g(["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."]),
    "X": _g(["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"]),
    "Y": _g(["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."]),
    "Z": _g(["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"]),
    "a": _g([".....", ".....", ".###.", "....#", ".####", "#...#", ".####"]),
    "b": _g(["#....", "#....", "#.##.", "##..#", "#...#", "#...#", "####."]),
    "c": _g([".....", ".....", ".###.", "#...#", "#....", "#...#", ".###."]),
    "d": _g(["....#", "....#", ".##.#", "#..##", "#...#", "#...#", ".####"]),
    "e": _g([".....", ".....", ".###.", "#...#", "#####", "#....", ".###."]),
    "f": _g(["..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."]),
    "g": _g([".....", ".####", "#...#", "#...#", ".####", "....#", ".###."]),
    "h": _g(["#....", "#....", "#.##.", "##..#", "#...#", "#...#", "#...#"]),
    "i": _g(["..#..", ".....", ".##..", "..#..", "..#..", "..#..", ".###."]),
    "j": _g(["...#.", ".....", "..##.", "...#.", "...#.", "#..#.", ".##.."]),
    "k": _g(["#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."]),
    "l": _g([".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."]),
    "m": _g([".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"]),
    "n": _g([".....", ".....", "#.##.", "##..#", "#...#", "#...#", "#...#"]),
    "o": _g([".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."]),
    "p": _g([".....", ".....", "#.##.", "##..#", "#...#", "####.", "#...."]),
    "q": _g([".....", ".....", ".##.#", "#..##", "#...#", ".####", "....#"]),
    "r": _g([".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."]),
    "s": _g([".....", ".....", ".####", "#....", ".###.", "....#", "####."]),
    "t": _g([".#...", ".#...", "####.", ".#...", ".#...", ".#..#", "..##."]),
    "u": _g([".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"]),
    "v": _g([".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."]),
    "w": _g([".....", ".....", "#...#", "#.#.#", "#.#.#", "#.#.#", ".#.#."]),
    "x": _g([".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"]),
    "y": _g([".....", "#...#", "#...#", "#...#", ".####", "....#", ".###."]),
    "z": _g([".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"]),
}

# ---------------------------------------------------------------- canvas
# Supersampling: draw at SS x resolution, then average each SS x SS block
# down to 1024. Smooths edges (anti-aliasing) while staying pure stdlib
# and fully deterministic. Logical coordinates stay 1024-based throughout.
SS = 2

class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.sw, self.sh = w * SS, h * SS
        self.buf = bytearray(bytes(bg) * (self.sw * self.sh))

    def px(self, x, y, c):
        self.rect(x, y, 1, 1, c)

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x * SS), max(0, y * SS)
        x1, y1 = min(self.sw, (x + w) * SS), min(self.sh, (y + h) * SS)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.sw + x0) * 3
            self.buf[i:i + len(row)] = row

    def hline(self, x, y, w, c, th=1):
        self.rect(x, y, w, th, c)

    def vline(self, x, y, h, c, th=1):
        self.rect(x, y, th, h, c)

    def rect_hr(self, x, y, w, h, c):
        """Filled rect in device (supersampled) coordinates."""
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.sw, x + w), min(self.sh, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.sw + x0) * 3
            self.buf[i:i + len(row)] = row

    def line(self, x0, y0, x1, y1, c, th=1):
        # Rasterize in device space so diagonals and curves anti-alias
        # when the canvas is averaged down. Accepts float coordinates.
        x0, y0, x1, y1 = (int(round(v * SS)) for v in (x0, y0, x1, y1))
        thd = max(1, int(round(th * SS)))
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx - dy
        h = thd // 2
        while True:
            self.rect_hr(x0 - h, y0 - h, thd, thd, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def circle_fill(self, cx, cy, r, c):
        cx, cy, r = cx * SS, cy * SS, r * SS
        for yy in range(int(cy - r), int(cy + r) + 1):
            dx = int(math.sqrt(max(0, r * r - (yy - cy) ** 2)))
            self.rect_hr(int(cx - dx), yy, 2 * dx + 1, 1, c)

    def circle_ring(self, cx, cy, r, c, th=1):
        cx, cy, r = cx * SS, cy * SS, r * SS
        thd = max(1, int(round(th * SS)))
        steps = max(24, int(2 * math.pi * r))
        h = thd // 2
        for i in range(steps):
            a = 2 * math.pi * i / steps
            self.rect_hr(int(round(cx + r * math.cos(a))) - h,
                         int(round(cy + r * math.sin(a))) - h, thd, thd, c)

    def arc(self, cx, cy, r, a0, a1, c, th=1):
        steps = max(8, int(abs(a1 - a0) * r * SS / 2))
        prev = None
        for i in range(steps + 1):
            a = a0 + (a1 - a0) * i / steps
            p = (cx + r * math.cos(a), cy + r * math.sin(a))
            if prev is not None:
                self.line(prev[0], prev[1], p[0], p[1], c, th)
            prev = p

    def polygon(self, pts, c):
        """Filled polygon via scanline (even-odd), rasterized in
        device space so slanted edges anti-alias."""
        if len(pts) < 3:
            return
        pts = [(x * SS, y * SS) for x, y in pts]
        ys = [p[1] for p in pts]
        for yy in range(int(min(ys)), int(max(ys)) + 1):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= yy < y1) or (y1 <= yy < y0):
                    xs.append(x0 + (yy - y0) * (x1 - x0) / (y1 - y0))
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                xa = int(math.ceil(xs[i]))
                self.rect_hr(xa, yy, max(1, int(xs[i + 1]) - xa), 1, c)

    def polyline(self, pts, c, th=1):
        for i in range(len(pts) - 1):
            self.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                      c, th)

# ---------------------------------------------------------------- text
def char_adv(scale, spacing):
    return 5 * scale + spacing

def text_w(s, scale, spacing=1):
    if not s:
        return 0
    return len(s) * char_adv(scale, spacing) - spacing

def draw_char(cv, x, y, ch, scale, color, bold=False):
    glyph = FONT.get(ch, FONT["?"])
    off = max(1, scale // 2) if bold else 0
    for ox in ((0, off) if bold else (0,)):
        for r in range(7):
            for cc in range(5):
                if glyph[r][cc]:
                    cv.rect(x + ox + cc * scale, y + r * scale,
                            scale, scale, color)

def draw_text(cv, x, y, s, scale, color, bold=False, spacing=1,
              align="left"):
    w = text_w(s, scale, spacing)
    if align == "center":
        x = x - w // 2
    elif align == "right":
        x = x - w
    cx = x
    for ch in s:
        draw_char(cv, cx, y, ch, scale, color, bold)
        cx += char_adv(scale, spacing)
    return w

def wrap_text(s, scale, spacing, max_w):
    words = s.split(" ")
    lines, cur = [], ""
    for wd in words:
        trial = wd if not cur else cur + " " + wd
        if text_w(trial, scale, spacing) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines

def draw_wrapped(cv, x, y, s, scale, color, max_w, line_h, bold=False,
                 spacing=1, max_lines=None):
    lines = wrap_text(s, scale, spacing, max_w)
    if max_lines is not None:
        lines = lines[:max_lines]
    for i, ln in enumerate(lines):
        draw_text(cv, x, y + i * line_h, ln, scale, color, bold, spacing)
    return len(lines)

# ---------------------------------------------------------------- PNG out
def write_png(path, cv):
    # Average each SS x SS block of the supersampled canvas down to one
    # output pixel. Integer math only: same input, byte-identical output.
    raw = bytearray()
    n = SS * SS
    for yy in range(cv.h):
        raw.append(0)
        for xx in range(cv.w):
            r = g = b = 0
            for dy in range(SS):
                base = ((yy * SS + dy) * cv.sw + xx * SS) * 3
                for dx in range(SS):
                    i = base + dx * 3
                    r += cv.buf[i]
                    g += cv.buf[i + 1]
                    b += cv.buf[i + 2]
            raw += bytes((r // n, g // n, b // n))
    comp = zlib.compress(bytes(raw), 9)

    def chunk(typ, data):
        c = struct.pack(">I", len(data)) + typ + data
        return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
           + chunk(b"IDAT", comp) + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)
    return len(png)

# ---------------------------------------------------------------- stories
# (number, category, kicker, headline, deck, lon, lat, nudge_x, nudge_y)
FEATURED = [
    (1, "red", "GULF / IRAN WAR",
     "Iran strikes back at Bahrain, Kuwait",
     "Bahrain says it stopped attacks a 3rd time this week. Iran says "
     "it hit a US base in Kuwait. US struck Qeshm Tue.",
     51, 26, 0, 0),
    (2, "red", "EUROPE / UKRAINE WAR",
     "Kerch Bridge road gone, rail back",
     "Road arch lies in the strait; trains run on one track. Two "
     "killed, Crimea governor says. Moscow vows a rebuild.",
     36.6, 45.3, 10, -4),
    (3, "blue", "ASIA / DIPLOMACY",
     "Trump in Manila, then Xi and Putin",
     "Meets Marcos, vows deeper defence ties. Xi greets him in "
     "Shenzhen. First trilateral with Putin set for Thu.",
     121, 14.6, 10, 8),
    (4, "green", "TECH / EARNINGS",
     "Nvidia: record $115.8bn quarter",
     "Revenue doubles; outlook $130bn next quarter. First results "
     "since Huang quit. Board will not reinstate him.",
     -122, 37.4, 0, 0),
    (5, "blue", "US / POLITICS",
     "Peltola flips Alaska Senate seat",
     "Beats Sullivan 50.12% to 45.80%, AP call. Ninth flip of the "
     "night. First Alaska Native in the Senate.",
     -150, 64, 0, 0),
    (6, "teal", "AFRICA / HEALTH",
     "Ebola: 7 in 10 small children die",
     "WHO: 11,000+ cases, 5,400 deaths in DR Congo. Children a third "
     "of deaths. 400-500 new cases a week.",
     23, -2, 0, 0),
    (7, "green", "US / TECH",
     "NSA network down in outage wave",
     "Classified NSANet degraded in maintenance, NSA says. Apple and "
     "banks also hit. No sign of cyberattack.",
     -77, 39, 0, 14),
    (8, "teal", "PACIFIC / CYCLONE",
     "Cyclone Xavier hits N. Cooks",
     "Cat 5, winds 220 km/h, gusts 315. Shelters open on Pukapuka and "
     "Nassau. Manihiki still has no grid power.",
     -160, -21, 0, 0),
    (9, "blue", "MIDDLE EAST / AID",
     "Four nations press Israel on Gaza aid",
     "150,000 tents held at border, ministers say. Floods swamp "
     "camps. WFP down to one hot meal every 2 days.",
     34.5, 31.4, 10, 24),
    (10, "teal", "US / HEALTH",
     "US loses measles-free status",
     "PAHO ends 26-year status. 5,412 cases, 10 deaths. 96% "
     "unvaccinated. Mexico and Bolivia lose it too.",
     -100, 39, 0, 0),
    (11, "red", "RUSSIA / DISASTER",
     "Military plane crash kills 19",
     "An-12 down in Kemerovo, ministry says. Criminal case opened "
     "Wed. Technical fault cited as early cause.",
     86, 55.5, 0, 0),
    (12, "teal", "ASIA / CYCLONE",
     "Cyclone Akvan heads for India",
     "Severe storm in Bay of Bengal. Landfall due Fri on Andhra "
     "coast. Fishermen warned to stay ashore.",
     88, 13, -14, -6),
]

# (number, category, one-line text, lon, lat, nudge_x, nudge_y)
ALSO = [
    (13, "red", "Hormuz: tanker crewman missing, 11 hurt", 56, 26.5, 18, -12),
    (14, "red", "Houthis hit Saudi pipeline pumps: 5 drones", 45, 24, -26, 16),
    (15, "green", "Oil falls as US crude stocks rise 5.28m", -95, 29, 0, 0),
    (16, "green", "Gulf shares fall as war fears grow", 47, 24.6, 18, 12),
    (17, "green", "Wall St: Dow -849 in Tue sell-off", -74, 40.7, 0, 0),
    (18, "blue", "Xi urges open trade; Putin hits sanctions", 114, 22.5, -4, -10),
    (19, "blue", "Thailand seals initial US trade deal", 100.5, 13.7, 0, 10),
    (20, "blue", "Kahana elected Knesset speaker, 66-52", 35.2, 31.8, -8, 10),
    (21, "blue", "Australia sanctions 3 people, 4 groups", 149, -35.3, 0, 0),
    (22, "blue", "UK sanctioned 8 settlement builders Tue", -0.1, 51.5, 0, 0),
    (23, "blue", "Latvia backs Kulbergs cabinet, 57-34", 24, 56.9, 14, -8),
    (24, "blue", "27 years for plot to kill Trump", -74, 40.7, 14, -10),
    (25, "red", "Hegseth hands Colombia a C-130", -74, 4.7, 8, -4),
    (26, "blue", "Guatemala prosecutor shot, wounded", -90.5, 14.6, 0, 0),
    (27, "teal", "Kenya Ebola-free; Nigeria reports 1 case", 37, -1.3, 0, 0),
    (28, "blue", "World Court Myanmar ruling due Thu", 4.3, 52, 0, -16),
    (29, "blue", "Grynspan leads race for UN chief", -74, 40.7, -20, 2),
    (30, "teal", "Quakes: PNG M6, Romania 5.3", 145, -6, 0, 0),
    (31, "teal", "UK warned on climate targets over EVs", -0.1, 51.5, -16, 12),
    (32, "amber", "GTA VI unlocks at midnight Thu", -118, 34, -14, 10),
    (33, "green", "Ecuador: $30m World Bank climate deal", -78.5, -0.2, -16, 6),
    (34, "teal", "COP31: warning on 'sacrifice zones'", 30.7, 36.9, -24, -6),
]

LEGEND = [("red", "WAR & SECURITY"), ("blue", "POLITICS"),
          ("green", "ECONOMY & TECH"), ("teal", "HEALTH & CLIMATE"),
          ("amber", "SPORT & CULTURE")]

# Coarse land mask in (lon_min, lat_min, lon_max, lat_max) rectangles.
LAND = [
    (-168, 58, -95, 71), (-125, 49, -66, 60), (-125, 25, -97, 49),
    (-97, 16, -86, 26), (-95, 8, -79, 17), (-80, 60, -60, 74),
    (-75, 8, -50, -10), (-70, -10, -40, -35), (-73, -35, -53, -52),
    (-10, 37, 30, 60), (5, 55, 32, 70), (30, 45, 60, 68),
    (-17, 15, 35, 32), (8, 5, 43, 15), (12, -35, 35, 5),
    (43, -25, 51, -12),
    (35, 30, 60, 42), (60, 25, 75, 37), (68, 8, 89, 28),
    (89, 20, 105, 29), (97, 5, 105, 21), (95, -10, 120, 5),
    (120, -5, 141, 5), (75, 45, 135, 75), (105, 20, 122, 40),
    (122, 30, 142, 45), (130, 42, 142, 54), (100, 42, 130, 54),
    (113, -38, 154, -22), (129, -25, 142, -10), (166, -47, 178, -34),
]

def is_land(lon, lat):
    for lo0, la0, lo1, la1 in LAND:
        if lo0 <= lon <= lo1 and la0 <= lat <= la1:
            return True
    return False

# ---------------------------------------------------------------- pictograms
def pic_ship(cv, cx, cy, col):
    cv.hline(cx - 44, cy + 18, 88, (140, 160, 175), 2)
    cv.hline(cx - 36, cy + 23, 72, (140, 160, 175), 2)
    cv.polygon([(cx - 38, cy + 6), (cx + 38, cy + 6),
                (cx + 27, cy + 17), (cx - 27, cy + 17)], INK)
    cv.rect(cx - 14, cy - 6, 28, 12, INK)
    cv.rect(cx + 16, cy - 2, 8, 8, INK)
    for dx, dy in ((-34, -20), (0, -24), (34, -20)):
        cv.line(cx + dx, cy + dy, cx + dx // 2, cy - 2, col, 2)
        cv.circle_fill(cx + dx, cy + dy, 2, col)

def pic_bridge(cv, cx, cy, col):
    cv.rect(cx - 32, cy - 14, 6, 32, INK)
    cv.rect(cx + 26, cy - 14, 6, 32, INK)
    cv.arc(cx, cy - 14, 30, 0.35, math.pi - 0.35, INK, 2)
    cv.hline(cx - 52, cy + 4, 42, INK, 3)
    cv.hline(cx + 10, cy + 4, 42, INK, 3)
    cv.polyline([(cx - 9, cy + 5), (cx, cy + 17), (cx + 9, cy + 5)], col, 3)
    cv.hline(cx - 44, cy + 22, 88, (140, 160, 175), 2)
    cv.hline(cx - 36, cy + 26, 72, (140, 160, 175), 2)

def pic_flags(cv, cx, cy, col):
    for fx, flag in ((-40, "us"), (0, "cn"), (40, "ru")):
        cv.vline(cx + fx - 14, cy - 22, 44, INK, 2)
        x0, y0 = cx + fx - 12, cy - 22
        if flag == "us":
            cv.rect(x0, y0, 26, 14, (255, 255, 255))
            for i in range(4):
                cv.hline(x0, y0 + i * 4, 26, RED, 2)
            cv.rect(x0, y0, 10, 7, BLUE)
        elif flag == "cn":
            cv.rect(x0, y0, 26, 14, RED)
            cv.circle_fill(x0 + 6, y0 + 7, 3, GOLD)
        else:
            cv.rect(x0, y0, 26, 5, (255, 255, 255))
            cv.rect(x0, y0 + 5, 26, 5, BLUE)
            cv.rect(x0, y0 + 10, 26, 4, RED)
        cv.rect(x0, y0, 26, 1, INK)
        cv.rect(x0, y0 + 13, 26, 1, INK)

def pic_chip(cv, cx, cy, col):
    cv.rect(cx - 18, cy - 18, 36, 36, INK)
    cv.rect(cx - 13, cy - 13, 26, 26, CARD)
    cv.rect(cx - 7, cy - 7, 14, 14, col)
    for dx in (-10, 0, 10):
        cv.vline(cx + dx, cy - 26, 8, INK, 2)
        cv.vline(cx + dx, cy + 18, 8, INK, 2)
        cv.hline(cx - 26, cy + dx, 8, INK, 2)
        cv.hline(cx + 18, cy + dx, 8, INK, 2)
    cv.polyline([(cx + 30, cy + 14), (cx + 38, cy + 2), (cx + 46, cy - 10)],
                col, 3)
    cv.polygon([(cx + 46, cy - 14), (cx + 52, cy - 8), (cx + 42, cy - 6)],
               col)

def pic_ballot(cv, cx, cy, col):
    cv.rect(cx - 24, cy - 2, 48, 26, INK)
    cv.rect(cx - 20, cy + 2, 40, 18, CARD)
    cv.rect(cx - 10, cy - 24, 20, 24, CARD)
    cv.rect(cx - 10, cy - 24, 20, 1, INK)
    cv.rect(cx - 10, cy - 24, 1, 24, INK)
    cv.rect(cx + 9, cy - 24, 1, 24, INK)
    cv.polyline([(cx - 6, cy - 12), (cx - 1, cy - 6), (cx + 7, cy - 18)],
                col, 3)

def pic_virus(cv, cx, cy, col):
    for i in range(8):
        a = math.pi * i / 4
        x1, y1 = cx + int(20 * math.cos(a)), cy + int(20 * math.sin(a))
        cv.line(cx, cy, x1, y1, col, 2)
        cv.circle_fill(x1, y1, 3, col)
    cv.circle_fill(cx, cy, 12, col)
    cv.circle_fill(cx - 4, cy - 3, 3, CARD)
    cv.circle_fill(cx + 4, cy + 3, 2, CARD)

def pic_monitor(cv, cx, cy, col):
    cv.rect(cx - 26, cy - 20, 52, 36, INK)
    cv.rect(cx - 22, cy - 16, 44, 28, (200, 220, 230))
    cv.rect(cx - 4, cy + 16, 8, 8, INK)
    cv.rect(cx - 14, cy + 24, 28, 3, INK)
    cv.polygon([(cx + 4, cy - 14), (cx - 6, cy + 2), (cx + 1, cy + 2),
                (cx - 4, cy + 14), (cx + 8, cy - 2), (cx + 1, cy - 2)],
               AMBER)

def pic_cyclone(cv, cx, cy, col, flip=False):
    s = -1 if flip else 1
    for r, a0 in ((20, 0.3), (14, 2.2), (8, 4.0)):
        cv.arc(cx, cy, r, a0 * s, (a0 + 4.2) * s, col, 3)
    cv.circle_fill(cx, cy, 3, col)
    for dy in (-24, 24):
        cv.line(cx - 42, cy + dy, cx - 28, cy + dy, DOTGRAY, 2)
        cv.line(cx + 28, cy + dy, cx + 42, cy + dy, DOTGRAY, 2)

def pic_tents(cv, cx, cy, col):
    cv.polygon([(cx - 46, cy + 20), (cx - 24, cy - 12), (cx - 2, cy + 20)],
               col)
    cv.polygon([(cx - 28, cy + 20), (cx - 24, cy + 8), (cx - 20, cy + 20)],
               CARD)
    cv.polygon([(cx - 6, cy + 20), (cx + 20, cy - 20), (cx + 46, cy + 20)],
               INK)
    cv.polygon([(cx + 15, cy + 20), (cx + 20, cy + 6), (cx + 25, cy + 20)],
               CARD)
    for dx in (-38, -14, 10, 34):
        cv.line(cx + dx, cy - 26, cx + dx - 5, cy - 16, BLUE, 2)

def pic_shield(cv, cx, cy, col):
    cv.polygon([(cx - 18, cy - 20), (cx + 18, cy - 20), (cx + 18, cy + 2),
                (cx, cy + 24), (cx - 18, cy + 2)], col)
    cv.polygon([(cx - 13, cy - 15), (cx + 13, cy - 15), (cx + 13, cy + 1),
                (cx, cy + 18), (cx - 13, cy + 1)], CARD)
    cv.rect(cx - 3, cy - 10, 6, 20, col)
    cv.rect(cx - 10, cy - 3, 20, 6, col)

def pic_plane(cv, cx, cy, col):
    cv.polygon([(cx - 34, cy + 2), (cx + 30, cy - 8), (cx + 44, cy - 6),
                (cx + 30, cy + 2), (cx - 20, cy + 8)], INK)
    cv.polygon([(cx - 6, cy - 2), (cx + 6, cy - 20), (cx + 14, cy - 20),
                (cx + 8, cy + 0)], INK)
    cv.polygon([(cx - 30, cy - 2), (cx - 40, cy - 14), (cx - 33, cy - 14),
                (cx - 24, cy - 4)], INK)
    for i, r in enumerate((3, 2, 2)):
        cv.circle_fill(cx - 44 - i * 8, cy + 12 + i * 3, r, DOTGRAY)

def pic_rain_storm(cv, cx, cy, col):
    cv.arc(cx, cy - 4, 18, 0.4, 4.6, col, 3)
    cv.arc(cx, cy - 4, 11, 2.4, 6.0, col, 3)
    cv.circle_fill(cx, cy - 4, 3, col)
    for dx in (-30, -15, 0, 15, 30):
        cv.line(cx + dx, cy + 14, cx + dx - 5, cy + 24, BLUE, 2)

PICTOGRAMS = {1: pic_ship, 2: pic_bridge, 3: pic_flags, 4: pic_chip,
              5: pic_ballot, 6: pic_virus, 7: pic_monitor,
              8: lambda cv, cx, cy, col: pic_cyclone(cv, cx, cy, col, False),
              9: pic_tents, 10: pic_shield, 11: pic_plane,
              12: pic_rain_storm}

# ---------------------------------------------------------------- layout
CARD_W, CARD_H, GAP = 246, 178, 6
CARD_X = [10, 262, 514, 766]
CARD_Y = [146, 330, 514]

def draw_masthead(cv):
    draw_stroke_text(cv, W // 2, 6, "THE WORLD TODAY", 2.4, 5, INK,
                     spacing=6, align="center")
    draw_text(cv, W // 2, 48, "ONE DAY OF WORLD NEWS, IN FULL", 1, INK,
              spacing=2, align="center")
    cv.hline(10, 60, 1004, INK, 2)
    cv.hline(10, 63, 1004, INK, 1)

def draw_banner(cv):
    cv.rect(10, 66, 1004, 72, NAVY)
    draw_stroke_text(cv, W // 2, 74, "WEDNESDAY 18 NOVEMBER 2026", 1.75,
                     3.5, CARD, spacing=3, align="center")
    draw_stroke_text(cv, W // 2, 110, "34 STORIES | 6 CONTINENTS | ONE DAY",
                     1.0, 2.5, GOLD, spacing=2, align="center")

def draw_card(cv, story):
    num, cat, kicker, headline, deck, _lo, _la, _nx, _ny = story
    idx = num - 1
    x, y = CARD_X[idx % 4], CARD_Y[idx // 4]
    col = CATCOLOR[cat]
    cv.rect(x, y, CARD_W, CARD_H, CARD)
    cv.rect(x, y, CARD_W, 1, BORDER)
    cv.rect(x, y + CARD_H - 1, CARD_W, 1, BORDER)
    cv.rect(x, y, 1, CARD_H, BORDER)
    cv.rect(x + CARD_W - 1, y, 1, CARD_H, BORDER)
    # pictogram strip
    cv.rect(x + 1, y + 1, CARD_W - 2, 64, TINT[cat])
    PICTOGRAMS[num](cv, x + CARD_W // 2, y + 33, col)
    # number badge
    cv.rect(x + 6, y + 6, 28, 22, col)
    draw_text(cv, x + 20, y + 11, str(num), 2, CARD, bold=True,
              spacing=1, align="center")
    # kicker, headline, deck
    draw_text(cv, x + 8, y + 74, kicker, 1, col, spacing=2)
    display = headline.upper().replace(",", "").replace(":", "")
    draw_stroke_wrapped(cv, x + 8, y + 88, display, 1.0, 2.5, INK,
                        CARD_W - 16, 18, spacing=0, max_lines=2)
    draw_wrapped(cv, x + 8, y + 126, deck, 1, INK, CARD_W - 16, 10,
                 spacing=1, max_lines=4)

def draw_map_panel(cv):
    x0, y0, w, h = 10, 698, 486, 262
    cv.rect(x0, y0, w, h, CARD)
    cv.rect(x0, y0, w, 1, BORDER)
    cv.rect(x0, y0 + h - 1, w, 1, BORDER)
    cv.rect(x0, y0, 1, h, BORDER)
    cv.rect(x0 + w - 1, y0, 1, h, BORDER)
    draw_stroke_text(cv, x0 + 10, y0 + 8, "WHERE IT HAPPENED", 1.0, 2.5,
                     INK, spacing=1)
    draw_text(cv, x0 + w - 10, y0 + 11, "34 STORIES MAPPED", 1, DOTGRAY,
              spacing=1, align="right")
    mx, my, mw, mh = x0 + 4, y0 + 30, w - 8, 190
    cv.rect(mx, my, mw, mh, MAPBG)

    def project(lon, lat):
        px = mx + (lon + 180) / 360.0 * mw
        py = my + (78 - lat) / 136.0 * mh
        return px, py

    step = 7
    yy = my + step // 2
    while yy < my + mh:
        xx = mx + step // 2
        while xx < mx + mw:
            lon = (xx - mx) / mw * 360 - 180
            lat = 78 - (yy - my) / mh * 136
            if is_land(lon, lat):
                cv.rect(xx - 1, yy - 1, 2, 2, DOTGRAY)
            xx += step
        yy += step
    # numbered dots: featured first, then also-list
    for story in FEATURED:
        num, cat = story[0], story[1]
        px, py = project(story[5], story[6])
        px, py = int(round(px)) + story[7], int(round(py)) + story[8]
        cv.circle_fill(px, py, 7, CARD)
        cv.circle_fill(px, py, 6, CATCOLOR[cat])
        draw_text(cv, px, py - 3, str(num), 1, CARD, bold=True,
                  spacing=0, align="center")
    for item in ALSO:
        num, cat = item[0], item[1]
        px, py = project(item[3], item[4])
        px, py = int(round(px)) + item[5], int(round(py)) + item[6]
        cv.circle_fill(px, py, 7, CARD)
        cv.circle_fill(px, py, 6, CATCOLOR[cat])
        draw_text(cv, px, py - 3, str(num), 1, CARD, bold=True,
                  spacing=0, align="center")
    # legend
    lx, ly = x0 + 10, y0 + 230
    for cat, label in LEGEND:
        cv.rect(lx, ly, 10, 10, CATCOLOR[cat])
        wlabel = draw_text(cv, lx + 14, ly + 2, label, 1, INK, spacing=0)
        lx += 14 + wlabel + 12

def draw_also_panel(cv):
    x0, y0, w, h = 504, 698, 510, 262
    cv.rect(x0, y0, w, h, CARD)
    cv.rect(x0, y0, w, 1, BORDER)
    cv.rect(x0, y0 + h - 1, w, 1, BORDER)
    cv.rect(x0, y0, 1, h, BORDER)
    cv.rect(x0 + w - 1, y0, 1, h, BORDER)
    draw_stroke_text(cv, x0 + 10, y0 + 8, "ALSO ON 18 NOVEMBER (13-34)",
                     1.0, 2.5, INK, spacing=1)
    cols = [x0 + 10, x0 + 266]
    for i, item in enumerate(ALSO):
        num, cat, text = item[0], item[1], item[2]
        cx = cols[i // 11]
        cy = y0 + 38 + (i % 11) * 20
        draw_text(cv, cx, cy, str(num) + ".", 1, CATCOLOR[cat], bold=True,
                  spacing=0)
        draw_text(cv, cx + 22, cy, text, 1, INK, spacing=0)

def draw_footer(cv):
    cv.hline(10, 966, 1004, INK, 2)
    draw_text(cv, W // 2, 974,
              "Every story happened or was first reported on Wednesday "
              "18 November 2026. Disputed claims are attributed.",
              1, INK, bold=True, spacing=1, align="center")
    draw_text(cv, W // 2, 986,
              "Sources: Reuters, AP, UN News, WHO, PAHO, US DOJ, IMD, "
              "Fiji Met Service, RNZ, USGS, GFZ, CNN, BBC, Al Jazeera, "
              "BusinessWorld, The Guardian.",
              1, INK, spacing=1, align="center")
    draw_text(cv, W // 2, 998,
              "All figures as reported on the day; later updates may "
              "change totals. Image drawn in code; no AI pictures.",
              1, DOTGRAY, spacing=1, align="center")

def render_page():
    cv = Canvas(W, H, PAPER)
    draw_masthead(cv)
    draw_banner(cv)
    for story in FEATURED:
        draw_card(cv, story)
    draw_map_panel(cv)
    draw_also_panel(cv)
    draw_footer(cv)
    return cv

def render_fonttest():
    cv = Canvas(W, H, CARD)
    chars = sorted(FONT.keys())
    x, y = 20, 20
    for ch in chars:
        label = ch if ch != " " else "SP"
        draw_text(cv, x, y, label + ":", 2, INK, spacing=1)
        draw_char(cv, x + 44, y - 2, ch, 3, RED)
        draw_char(cv, x + 76, y, ch, 2, BLUE)
        draw_char(cv, x + 100, y + 3, ch, 1, INK)
        x += 150
        if x > W - 160:
            x, y = 20, y + 40
    draw_text(cv, 20, y + 50, "THE QUICK BROWN FOX 0123456789 $115.8bn "
              "50.12% + - / (13-34) & 'sacrifice zones'", 2, INK,
              bold=True, spacing=2)
    draw_text(cv, 20, y + 80, "The quick brown fox jumps over the lazy "
              "dog. 11,000+ cases, 5,400 deaths.", 1, INK, spacing=1)
    return cv

# ---------------------------------------------------------------- stroke font
# Display lettering: glyphs as strokes on a 12 x 16 grid, rasterized
# through the device-space line/arc primitives so edges anti-alias.
# Used for masthead, date banner, headlines and panel headers (caps only).
# Small text keeps the crisp 5x7 bitmap font.
HALF_PI = math.pi / 2
TWO_PI = 2 * math.pi

def _S(pts):
    return ("l", tuple(pts))

def _E(cx, cy, rx, ry, a0, a1):
    return ("e", (cx, cy, rx, ry, a0, a1))

_S_SHAPE = [(9.5, 2.5), (7, 1), (4, 1.5), (2.5, 3.5), (3, 6), (5.5, 8),
            (7, 8), (9.5, 10), (9.5, 13), (7, 15), (4, 15), (2, 13)]

STROKES = {
    " ": [],
    "A": [_S([(1, 15), (6, 1), (11, 15)]), _S([(3.4, 10.5), (8.6, 10.5)])],
    "B": [_S([(1.5, 15), (1.5, 1), (7, 1)]),
          _E(7, 4.75, 3.5, 3.75, -HALF_PI, HALF_PI),
          _E(7, 11, 4, 4, -HALF_PI, HALF_PI),
          _S([(1.5, 15), (7, 15)]), _S([(1.5, 8), (6.5, 8)])],
    "C": [_E(6, 8, 5, 7, 0.65, TWO_PI - 0.65)],
    "D": [_S([(1.5, 15), (1.5, 1), (6, 1)]),
          _E(6, 8, 5, 7, -HALF_PI, HALF_PI), _S([(1.5, 15), (6, 15)])],
    "E": [_S([(10, 1), (1.5, 1), (1.5, 15), (10, 15)]),
          _S([(1.5, 8), (8, 8)])],
    "F": [_S([(1.5, 15), (1.5, 1), (10, 1)]), _S([(1.5, 8), (8, 8)])],
    "G": [_E(6, 8, 5, 7, 0.65, TWO_PI - 0.85),
          _S([(11, 7.5), (6.5, 7.5)]), _S([(11, 7.5), (11, 12)])],
    "H": [_S([(1.5, 1), (1.5, 15)]), _S([(10.5, 1), (10.5, 15)]),
          _S([(1.5, 8), (10.5, 8)])],
    "I": [_S([(6, 1), (6, 15)]), _S([(3, 1), (9, 1)]), _S([(3, 15), (9, 15)])],
    "J": [_S([(4, 1), (10, 1)]), _S([(9.5, 1), (9.5, 11)]),
          _E(6, 11, 3.5, 4, 0, math.pi)],
    "K": [_S([(1.5, 1), (1.5, 15)]), _S([(10, 1), (2.5, 8)]),
          _S([(4.5, 6), (10.5, 15)])],
    "L": [_S([(1.5, 1), (1.5, 15), (10.5, 15)])],
    "M": [_S([(1.5, 15), (1.5, 1), (6, 8.5), (10.5, 1), (10.5, 15)])],
    "N": [_S([(1.5, 15), (1.5, 1), (10.5, 15), (10.5, 1)])],
    "O": [_E(6, 8, 5, 7, 0, TWO_PI)],
    "P": [_S([(1.5, 15), (1.5, 1), (7, 1)]),
          _E(7, 4.75, 3.5, 3.75, -HALF_PI, HALF_PI),
          _S([(1.5, 8.5), (7, 8.5)])],
    "Q": [_E(6, 8, 5, 7, 0, TWO_PI), _S([(8, 12.5), (11.5, 16)])],
    "R": [_S([(1.5, 15), (1.5, 1), (7, 1)]),
          _E(7, 4.75, 3.5, 3.75, -HALF_PI, HALF_PI),
          _S([(1.5, 8.5), (7, 8.5)]), _S([(5, 8.5), (11, 15)])],
    "S": [_S(_S_SHAPE)],
    "T": [_S([(1, 1), (11, 1)]), _S([(6, 1), (6, 15)])],
    "U": [_S([(1.5, 1), (1.5, 10.5)]), _E(6, 10.5, 4.5, 4.5, 0, math.pi),
          _S([(10.5, 1), (10.5, 10.5)])],
    "V": [_S([(1, 1), (6, 15), (11, 1)])],
    "W": [_S([(1, 1), (3, 15), (6, 8), (9, 15), (11, 1)])],
    "X": [_S([(1.5, 1), (10.5, 15)]), _S([(10.5, 1), (1.5, 15)])],
    "Y": [_S([(1.5, 1), (6, 8), (10.5, 1)]), _S([(6, 8), (6, 15)])],
    "Z": [_S([(1.5, 1), (10.5, 1), (1.5, 15), (10.5, 15)])],
    "0": [_E(6, 8, 5, 7, 0, TWO_PI), _S([(3.5, 3.5), (8.5, 12.5)])],
    "1": [_S([(4, 3.5), (6.5, 1), (6.5, 15)]), _S([(3.5, 15), (9.5, 15)])],
    "2": [_S([(2, 5), (2, 3), (4, 1), (8, 1), (10, 3), (10, 5.5),
               (1.5, 15), (10.5, 15)])],
    "3": [_E(6, 4.75, 3.5, 3.75, -1.35, 1.35),
          _E(6, 11, 4, 4, -1.35, 1.35), _S([(2.5, 1.5), (5.5, 1)])],
    "4": [_S([(8, 1), (1.5, 10.5), (10.5, 10.5)]), _S([(8, 1), (8, 15)])],
    "5": [_S([(10, 1), (2, 1), (2, 8), (8.5, 8)]),
          _E(6.5, 11.5, 3.5, 3.5, -HALF_PI, HALF_PI)],
    "6": [_E(6, 10.5, 4.5, 4.5, 0.5, TWO_PI),
          _S([(10, 1.5), (6, 3), (3, 7)])],
    "7": [_S([(1.5, 1), (10.5, 1), (5, 15)])],
    "8": [_E(6, 4.5, 4, 3.5, 0, TWO_PI), _E(6, 11, 4.5, 4, 0, TWO_PI)],
    "9": [_E(6, 5.5, 4.5, 4.5, 0, TWO_PI),
          _S([(10.5, 6), (10.5, 12), (8, 15), (4, 15)])],
    "$": [_S(_S_SHAPE), _S([(6, 0), (6, 16)])],
    ".": [("d", (6, 14, 1.3))],
    "-": [_S([(2, 8), (10, 8)])],
    "/": [_S([(9, 15), (3, 1)])],
    "(": [_E(8.5, 8, 4, 7, HALF_PI, 3 * HALF_PI)],
    ")": [_E(3.5, 8, 4, 7, -HALF_PI, HALF_PI)],
    "|": [_S([(6, 1), (6, 15)])],
    "?": [_S([(2, 3), (3, 1), (6, 1), (9, 2), (9, 4), (6, 7), (6, 9)]),
          ("d", (6, 13, 1.3))],
}

STROKE_ADV = 12  # grid units per character cell

def draw_stroke_char(cv, x, y, ch, scale, weight, color):
    for stroke in STROKES.get(ch, STROKES["?"]):
        kind, data = stroke[0], stroke[1]
        if kind == "l":
            pts = [(x + px * scale, y + py * scale) for px, py in data]
            for i in range(len(pts) - 1):
                cv.line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1],
                        color, weight)
        elif kind == "e":
            cx, cy, rx, ry, a0, a1 = data
            steps = max(12, int(abs(a1 - a0) * max(rx, ry) * scale))
            prev = None
            for i in range(steps + 1):
                a = a0 + (a1 - a0) * i / steps
                p = (x + (cx + rx * math.cos(a)) * scale,
                     y + (cy + ry * math.sin(a)) * scale)
                if prev is not None:
                    cv.line(prev[0], prev[1], p[0], p[1], color, weight)
                prev = p
        elif kind == "d":
            dx, dy, r = data
            cv.circle_fill(x + dx * scale, y + dy * scale, r * scale, color)

def stroke_text_w(s, scale, spacing):
    if not s:
        return 0
    return len(s) * (STROKE_ADV * scale + spacing) - spacing

def draw_stroke_text(cv, x, y, s, scale, weight, color, spacing=1,
                     align="left"):
    w = stroke_text_w(s, scale, spacing)
    if align == "center":
        x = x - w / 2
    elif align == "right":
        x = x - w
    cx = x
    for ch in s:
        draw_stroke_char(cv, cx, y, ch, scale, weight, color)
        cx += STROKE_ADV * scale + spacing
    return w

def wrap_stroke(s, scale, spacing, max_w):
    words = s.split(" ")
    lines, cur = [], ""
    for wd in words:
        trial = wd if not cur else cur + " " + wd
        if stroke_text_w(trial, scale, spacing) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines

def draw_stroke_wrapped(cv, x, y, s, scale, weight, color, max_w, line_h,
                        spacing=1, max_lines=None):
    lines = wrap_stroke(s, scale, spacing, max_w)
    if max_lines is not None:
        lines = lines[:max_lines]
    for i, ln in enumerate(lines):
        draw_stroke_text(cv, x, y + i * line_h, ln, scale, weight, color,
                         spacing)
    return len(lines)

def render_stroketest():
    cv = Canvas(W, H, CARD)
    chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789$. -/|()?"
    x, y = 20, 30
    for ch in chars:
        draw_stroke_char(cv, x, y, ch, 2.0, 4, INK)
        x += 34
        if x > W - 60:
            x, y = 20, y + 50
    draw_stroke_text(cv, 20, y + 60, "THE WORLD TODAY", 2.4, 5, INK,
                     spacing=6)
    draw_stroke_text(cv, 20, y + 110, "WEDNESDAY 18 NOVEMBER 2026", 1.75,
                     3.5, NAVY, spacing=3)
    draw_stroke_text(cv, 20, y + 150, "IRAN STRIKES BACK AT BAHRAIN KUWAIT",
                     1.0, 2.2, INK, spacing=0)
    draw_stroke_text(cv, 20, y + 175, "NVIDIA RECORD $115.8BN QUARTER",
                     1.0, 2.2, INK, spacing=0)
    draw_stroke_text(cv, 20, y + 200, "34 STORIES | 6 CONTINENTS | ONE DAY",
                     1.0, 2.2, GOLD, spacing=2)
    return cv

def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not outdir:
        outdir = "/output" if os.path.isdir("/output") else "out"
    os.makedirs(outdir, exist_ok=True)
    if os.environ.get("FONTTEST") == "1":
        cv = render_fonttest()
    elif os.environ.get("STROKETEST") == "1":
        cv = render_stroketest()
    else:
        cv = render_page()
    path = os.path.join(outdir, "entry.png")
    size = write_png(path, cv)
    print("wrote %s (%d bytes)" % (path, size))

if __name__ == "__main__":
    main()
