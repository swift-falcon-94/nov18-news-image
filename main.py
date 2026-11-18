# Nov 18 News Image: renders one 1024x1024 PNG summing up the world news
# of Wednesday 18 November 2026. Pure Python 3 standard library, no
# network, no input files, no clock, no randomness: repeated runs write
# identical bytes. Layout: front page. A masthead names the day, four
# story rows each carry a pictogram, a tag, a headline and three factual
# lines, and a footer strip lists more stories reported on the day.
# Text uses a hand-authored 5x7 bitmap font stored as integer bitmasks,
# uppercase only, drawn at integer scales.

import os
import struct
import zlib

W = 1024
H = 1024

PAPER = (252, 250, 243)
INK = (24, 30, 40)
TEAL = (12, 74, 78)
TEAL_DK = (8, 52, 55)
RUST = (198, 72, 38)
GOLD = (222, 164, 52)
SKY = (178, 208, 224)
SEA = (64, 116, 148)
SEA_DK = (42, 88, 118)
SAND = (233, 220, 196)
GREY = (120, 126, 134)
GREY_LT = (196, 202, 208)
SMOKE = (176, 180, 186)
FLAME = (232, 90, 40)
LEAF = (74, 140, 92)
WHITE = (255, 255, 255)
CREAM = (244, 238, 224)
PANEL_A = (214, 232, 238)
PANEL_B = (238, 228, 205)
PANEL_C = (222, 228, 232)
PANEL_D = (232, 222, 226)
STEEL = (58, 68, 82)

# 5x7 glyphs: seven rows, each a 5-bit mask, bit 4 is the left pixel.
GLYPHS = {
    'A': [14, 17, 17, 31, 17, 17, 17],
    'B': [30, 17, 17, 30, 17, 17, 30],
    'C': [14, 17, 16, 16, 16, 17, 14],
    'D': [28, 18, 17, 17, 17, 18, 28],
    'E': [31, 16, 16, 30, 16, 16, 31],
    'F': [31, 16, 16, 30, 16, 16, 16],
    'G': [14, 17, 16, 23, 17, 17, 15],
    'H': [17, 17, 17, 31, 17, 17, 17],
    'I': [14, 4, 4, 4, 4, 4, 14],
    'J': [7, 2, 2, 2, 2, 18, 12],
    'K': [17, 18, 20, 24, 20, 18, 17],
    'L': [16, 16, 16, 16, 16, 16, 31],
    'M': [17, 27, 21, 21, 17, 17, 17],
    'N': [17, 25, 25, 21, 19, 19, 17],
    'O': [14, 17, 17, 17, 17, 17, 14],
    'P': [30, 17, 17, 30, 16, 16, 16],
    'Q': [14, 17, 17, 17, 21, 18, 13],
    'R': [30, 17, 17, 30, 20, 18, 17],
    'S': [15, 16, 16, 14, 1, 1, 30],
    'T': [31, 4, 4, 4, 4, 4, 4],
    'U': [17, 17, 17, 17, 17, 17, 14],
    'V': [17, 17, 17, 17, 17, 10, 4],
    'W': [17, 17, 17, 21, 21, 27, 17],
    'X': [17, 10, 4, 4, 4, 10, 17],
    'Y': [17, 17, 10, 4, 4, 4, 4],
    'Z': [31, 1, 2, 4, 8, 16, 31],
    '0': [14, 17, 19, 21, 25, 17, 14],
    '1': [4, 12, 20, 4, 4, 4, 31],
    '2': [14, 17, 1, 2, 4, 8, 31],
    '3': [30, 1, 1, 14, 1, 1, 30],
    '4': [2, 6, 10, 18, 31, 2, 2],
    '5': [31, 16, 30, 1, 1, 17, 14],
    '6': [14, 16, 16, 30, 17, 17, 14],
    '7': [31, 1, 2, 2, 4, 4, 4],
    '8': [14, 17, 17, 14, 17, 17, 14],
    '9': [14, 17, 17, 15, 1, 1, 14],
    ' ': [0, 0, 0, 0, 0, 0, 0],
    ',': [0, 0, 0, 0, 6, 6, 4],
    '.': [0, 0, 0, 0, 0, 6, 6],
    '-': [0, 0, 0, 31, 0, 0, 0],
    ':': [0, 6, 6, 0, 6, 6, 0],
    '/': [1, 1, 2, 4, 8, 16, 16],
}

CANVAS = bytearray(W * H * 3)


def set_px(x, y, colour):
    if 0 <= x < W and 0 <= y < H:
        i = (y * W + x) * 3
        CANVAS[i] = colour[0]
        CANVAS[i + 1] = colour[1]
        CANVAS[i + 2] = colour[2]


def fill(x, y, w, h, colour):
    x0 = max(x, 0)
    y0 = max(y, 0)
    x1 = min(x + w, W)
    y1 = min(y + h, H)
    if x1 <= x0 or y1 <= y0:
        return
    row = bytes(colour) * (x1 - x0)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        CANVAS[base:base + len(row)] = row


def disc(cx, cy, r, colour):
    for yy in range(cy - r, cy + r + 1):
        rem = r * r - (yy - cy) * (yy - cy)
        if rem < 0:
            continue
        dx = int(rem ** 0.5)
        fill(cx - dx, yy, 2 * dx + 1, 1, colour)


def ring(cx, cy, r, colour, thick=3):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            d2 = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
            if (r - thick) * (r - thick) <= d2 <= r * r:
                set_px(xx, yy, colour)


def stroke(x0, y0, x1, y1, colour, thick=1):
    # Integer Bresenham line with a square brush.
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    x, y = x0, y0
    half = thick // 2
    while True:
        fill(x - half, y - half, thick, thick, colour)
        if x == x1 and y == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x += sx
        if e2 < dx:
            err += dx
            y += sy


def text_w(s, scale):
    if not s:
        return 0
    return len(s) * 6 * scale - scale


def draw_text(x, y, s, scale, colour):
    cx = x
    for ch in s:
        rows = GLYPHS.get(ch, GLYPHS[' '])
        for ry in range(7):
            mask = rows[ry]
            for rx in range(5):
                if mask & (1 << (4 - rx)):
                    fill(cx + rx * scale, y + ry * scale, scale, scale, colour)
        cx += 6 * scale


def draw_centred(y, s, scale, colour):
    draw_text((W - text_w(s, scale)) // 2, y, s, scale, colour)


def frame(px, py, pw, ph, colour):
    fill(px, py, pw, ph, colour)
    fill(px, py, pw, 3, INK)
    fill(px, py + ph - 3, pw, 3, INK)
    fill(px, py, 3, ph, INK)
    fill(px + pw - 3, py, 3, ph, INK)


def pic_gulf(px, py):
    # Island launch site, jets overhead, drones, intercepted burst.
    frame(px, py, 272, 162, PANEL_A)
    fill(px + 3, py + 108, 266, 51, SEA)
    fill(px + 3, py + 108, 266, 4, SEA_DK)
    fill(px + 30, py + 118, 200, 8, SEA_DK)
    fill(px + 60, py + 132, 150, 6, SEA_DK)
    fill(px + 96, py + 84, 80, 24, SAND)
    fill(px + 110, py + 72, 52, 12, SAND)
    fill(px + 118, py + 58, 10, 16, STEEL)
    stroke(px + 123, py + 58, px + 138, py + 38, STEEL, 5)
    disc(px + 138, py + 36, 4, FLAME)
    fill(px + 28, py + 31, 38, 7, INK)
    fill(px + 42, py + 26, 9, 17, INK)
    fill(px + 60, py + 28, 6, 13, INK)
    fill(px + 176, py + 23, 34, 6, INK)
    fill(px + 189, py + 18, 8, 15, INK)
    for ox, oy in ((200, 52), (224, 66), (188, 78)):
        stroke(px + ox - 7, py + oy - 7, px + ox + 7, py + oy + 7, RUST, 3)
        stroke(px + ox - 7, py + oy + 7, px + ox + 7, py + oy - 7, RUST, 3)
        disc(px + ox, py + oy, 3, INK)
    disc(px + 66, py + 62, 10, GOLD)
    ring(px + 66, py + 62, 17, GOLD, 3)
    stroke(px + 66, py + 40, px + 66, py + 30, GOLD, 3)
    stroke(px + 88, py + 62, px + 98, py + 62, GOLD, 3)


def pic_manila(px, py):
    # Skyline, sun, and a plane on its way over the city.
    frame(px, py, 272, 162, PANEL_B)
    disc(px + 222, py + 34, 18, GOLD)
    fill(px + 3, py + 128, 266, 31, GREY_LT)
    for bx, bw, bh in ((18, 34, 62), (58, 28, 84), (92, 40, 54),
                       (138, 30, 92), (174, 36, 66), (216, 32, 48)):
        fill(px + bx, py + 128 - bh, bw, bh, STEEL)
        fill(px + bx + 5, py + 128 - bh + 8, 6, 6, GOLD)
        fill(px + bx + 5, py + 128 - bh + 22, 6, 6, GOLD)
        fill(px + bx + 16, py + 128 - bh + 14, 6, 6, PAPER)
    stroke(px + 138, py + 36, px + 138, py + 10, INK, 3)
    fill(px + 138, py + 10, 26, 14, RUST)
    fill(px + 38, py + 53, 56, 9, INK)
    fill(px + 58, py + 46, 14, 23, INK)
    fill(px + 86, py + 50, 7, 15, INK)
    for i in range(6):
        disc(px + 108 + i * 14, py + 44 - i * 2, 2, INK)


def pic_crimea(px, py):
    # Road deck broken in the middle, rail line below, debris in water.
    frame(px, py, 272, 162, PANEL_C)
    fill(px + 3, py + 104, 266, 55, SEA)
    fill(px + 3, py + 104, 266, 4, SEA_DK)
    fill(px + 24, py + 118, 60, 5, SEA_DK)
    fill(px + 180, py + 126, 70, 5, SEA_DK)
    fill(px + 30, py + 52, 12, 52, STEEL)
    fill(px + 228, py + 52, 12, 52, STEEL)
    fill(px + 3, py + 44, 112, 10, INK)
    fill(px + 157, py + 44, 112, 10, INK)
    stroke(px + 42, py + 44, px + 84, py + 22, STEEL, 4)
    stroke(px + 84, py + 22, px + 115, py + 44, STEEL, 4)
    stroke(px + 157, py + 44, px + 188, py + 22, STEEL, 4)
    stroke(px + 188, py + 22, px + 228, py + 44, STEEL, 4)
    fill(px + 3, py + 66, 266, 5, GREY)
    fill(px + 118, py + 58, 10, 12, STEEL)
    fill(px + 132, py + 72, 12, 10, STEEL)
    fill(px + 146, py + 86, 10, 12, STEEL)
    disc(px + 136, py + 108, 8, WHITE)
    disc(px + 136, py + 108, 4, SEA)
    fill(px + 118, py + 18, 8, 18, SMOKE)
    fill(px + 128, py + 12, 10, 24, SMOKE)
    disc(px + 60, py + 26, 9, GOLD)


def pic_ebola(px, py):
    # Medical cross badge, virus marks, and bars rising steeply.
    frame(px, py, 272, 162, PANEL_D)
    disc(px + 62, py + 62, 34, TEAL)
    fill(px + 54, py + 38, 16, 48, WHITE)
    fill(px + 38, py + 54, 48, 16, WHITE)
    disc(px + 196, py + 42, 14, RUST)
    for ang in range(8):
        ex = 196 + int(22 * [1, 0, -1, 0, 1, -1, 1, -1][ang])
        ey = 42 + int(22 * [0, 1, 0, -1, 1, 1, -1, -1][ang])
        stroke(px + 196, py + 42, px + ex, py + ey, RUST, 3)
        disc(px + ex, py + ey, 3, RUST)
    disc(px + 236, py + 78, 8, RUST)
    disc(px + 30, py + 118, 6, RUST)
    fill(px + 3, py + 128, 266, 3, INK)
    for bx, bh in ((110, 28), (150, 52), (190, 84), (228, 104)):
        fill(px + bx, py + 128 - bh, 26, bh, RUST)
    stroke(px + 104, py + 112, px + 254, py + 22, INK, 3)
    disc(px + 254, py + 22, 4, INK)


STORIES = [
    {
        'tag': 'THE GULF', 'pic': pic_gulf,
        'head': ['US HITS QESHM, IRAN', 'STRIKES BACK IN GULF'],
        'body': ['US JETS HIT A MISSILE SITE ON QESHM',
                 'ISLAND, A US OFFICIAL SAID. IRAN',
                 'FIRED DRONES AT BAHRAIN, KUWAIT'],
    },
    {
        'tag': 'MANILA', 'pic': pic_manila,
        'head': ['TRUMP MEETS MARCOS IN', 'MANILA, SHENZHEN NEXT'],
        'body': ['US TO EXPAND DEFENCE TIES, ARMS',
                 'SALES OVER 5 BILLION DOLLARS.',
                 'TRILATERAL WITH XI, PUTIN THURSDAY'],
    },
    {
        'tag': 'CRIMEA', 'pic': pic_crimea,
        'head': ['CRIMEA BRIDGE ROAD SPAN', 'COLLAPSES INTO SEA'],
        'body': ['UKRAINE HIT THE BRIDGE A SECOND',
                 'DAY. ROAD ARCH FELL, TRAFFIC SHUT.',
                 'TWO KILLED, CRIMEA OFFICIALS SAID.'],
    },
    {
        'tag': 'CONGO', 'pic': pic_ebola,
        'head': ['EBOLA CASES DOUBLE', 'IN CONGO, WHO SAYS'],
        'body': ['CASES TOP 11,000, DEATHS 5,400.',
                 'WHO SAID CHILDREN ARE A THIRD OF',
                 'DEATHS. SEVEN IN TEN UNDER 5 DIED'],
    },
]

FOOTER = [
    'ALSO: PELTOLA WINS ALASKA, DEMOCRATS 56-44 IN SENATE',
    'CYCLONE XAVIER, CATEGORY 5, NEARS NORTH COOK ISLANDS',
    'AN-12 CRASH IN SIBERIA KILLS 19. DHONI RETIRES FROM IPL.',
]


def draw_row(y, story):
    story['pic'](16, y + 14)
    tag = story['tag']
    tw = text_w(tag, 3) + 24
    fill(322, y + 16, tw, 28, RUST)
    draw_text(334, y + 19, tag, 3, WHITE)
    draw_text(322, y + 54, story['head'][0], 4, INK)
    draw_text(322, y + 86, story['head'][1], 4, INK)
    draw_text(322, y + 118, story['body'][0], 3, INK)
    draw_text(322, y + 142, story['body'][1], 3, INK)
    draw_text(322, y + 164, story['body'][2], 3, INK)
    # Body scale 3 is 21 px tall; the third line ends at y+185.
    fill(0, y + 190, W, 2, GREY_LT)


def render():
    fill(0, 0, W, H, PAPER)
    fill(0, 0, W, 170, TEAL)
    fill(0, 164, W, 6, GOLD)
    draw_centred(20, 'THE WORLD IN ONE IMAGE', 3, GOLD)
    draw_centred(54, 'WEDNESDAY 18 NOVEMBER 2026', 6, WHITE)
    draw_centred(116, 'FOUR STORIES THAT DEFINED THE DAY, AS REPORTED', 3, CREAM)
    y = 170
    for story in STORIES:
        draw_row(y, story)
        y += 190
    fill(0, 930, W, 94, INK)
    fill(0, 930, W, 4, GOLD)
    draw_text(24, 944, FOOTER[0], 2, WHITE)
    draw_text(24, 966, FOOTER[1], 2, WHITE)
    draw_text(24, 988, FOOTER[2], 2, WHITE)


def chunk(kind, data):
    return struct.pack('>I', len(data)) + kind + data + struct.pack(
        '>I', zlib.crc32(kind + data) & 0xFFFFFFFF)


def encode_png():
    raw = bytearray()
    stride = W * 3
    for yy in range(H):
        raw.append(0)
        raw.extend(CANVAS[yy * stride:(yy + 1) * stride])
    header = struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0)
    out = bytearray(b'\x89PNG\r\n\x1a\n')
    out.extend(chunk(b'IHDR', header))
    out.extend(chunk(b'IDAT', zlib.compress(bytes(raw), 9)))
    out.extend(chunk(b'IEND', b''))
    return bytes(out)


def main():
    render()
    out_dir = os.environ.get('MAKEFUN_OUTPUT_DIR') or '/output'
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, 'entry.png')
    with open(path, 'wb') as fh:
        fh.write(encode_png())


if __name__ == '__main__':
    main()
