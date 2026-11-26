#!/usr/bin/env python3
"""News image: one 1024x1024 PNG summing up world news on 25 Nov 2026.

Python 3.13 stdlib only. No PIL: the PNG is written by hand with
zlib/struct, and text is drawn with a small built-in 5x7 bitmap font.
Deterministic: same bytes every run, no timestamps, no randomness,
no network. Paths resolve from this file's own location, never CWD.
Output: $MAKEFUN_OUTPUT_DIR/entry.png, else /output/entry.png.

All facts come from NEWS_25NOV.md (56 stories first reported 25 Nov
2026: 3 lead + 12 medium + 41 also-today). Unverified claims are
marked with * and labelled as claims. No 24 Nov story is presented
as a 25 Nov story.
"""

import os
import struct
import sys
import zlib
from pathlib import Path

W, H = 1024, 1024

# ---------------------------------------------------------------- font
# 5x7 bitmap font. Each glyph: 7 rows of 5 bits, '#' = ink, '.' = blank.
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
    'W': ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    'X': ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    'Y': ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    'Z': ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    'a': ("00000", "00000", "01110", "00001", "01111", "10001", "01111"),
    'b': ("10000", "10000", "10110", "11001", "10001", "10001", "11110"),
    'c': ("00000", "00000", "01110", "10001", "10000", "10001", "01110"),
    'd': ("00001", "00001", "01101", "10011", "10001", "10001", "01111"),
    'e': ("00000", "00000", "01110", "10001", "11111", "10000", "01110"),
    'f': ("00110", "01001", "01000", "11110", "01000", "01000", "01000"),
    'g': ("00000", "01111", "10001", "10001", "01111", "00001", "01110"),
    'h': ("10000", "10000", "10110", "11001", "10001", "10001", "10001"),
    'i': ("00100", "00000", "01100", "00100", "00100", "00100", "01110"),
    'j': ("00010", "00000", "00110", "00010", "00010", "10010", "01100"),
    'k': ("10000", "10000", "10010", "10100", "11000", "10100", "10010"),
    'l': ("01100", "00100", "00100", "00100", "00100", "00100", "01110"),
    'm': ("00000", "00000", "11010", "10101", "10101", "10101", "10101"),
    'n': ("00000", "00000", "10110", "11001", "10001", "10001", "10001"),
    'o': ("00000", "00000", "01110", "10001", "10001", "10001", "01110"),
    'p': ("00000", "00000", "11110", "10001", "11110", "10000", "10000"),
    'q': ("00000", "00000", "01101", "10011", "01111", "00001", "00001"),
    'r': ("00000", "00000", "10110", "11001", "10000", "10000", "10000"),
    's': ("00000", "00000", "01111", "10000", "01110", "00001", "11110"),
    't': ("01000", "01000", "11100", "01000", "01000", "01000", "00110"),
    'u': ("00000", "00000", "10001", "10001", "10001", "10011", "01101"),
    'v': ("00000", "00000", "10001", "10001", "10001", "01010", "00100"),
    'w': ("00000", "00000", "10001", "10101", "10101", "10101", "01010"),
    'x': ("00000", "00000", "10001", "01010", "00100", "01010", "10001"),
    'y': ("00000", "00000", "10001", "10001", "01111", "00001", "01110"),
    'z': ("00000", "00000", "11111", "00010", "00100", "01000", "11111"),
    '0': ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    '1': ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    '2': ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    '3': ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
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
    '?': ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    '-': ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    '(': ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ')': ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    '/': ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    '%': ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '$': ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    '&': ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    '+': ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    '=': ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '*': ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    '#': ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    '@': ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    '_': ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    '[': ("01110", "01000", "01000", "01000", "01000", "01000", "01110"),
    ']': ("01110", "00010", "00010", "00010", "00010", "00010", "01110"),
    '<': ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    '>': ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
    '|': ("00100", "00100", "00100", "00100", "00100", "00100", "00100"),
}

# ---------------------------------------------------------------- canvas
NAVY = (11, 31, 58)
NAVY2 = (18, 48, 86)
OCEAN = (205, 226, 242)
LAND = (139, 178, 128)
LAND_EDGE = (96, 138, 90)
INK = (22, 26, 32)
MUTED = (74, 82, 94)
WHITE = (255, 255, 255)
PAPER = (250, 249, 245)
RED = (198, 40, 40)
BLUE = (21, 101, 192)
ORANGE = (214, 110, 0)
GOLD = (255, 193, 7)
TEAL = (0, 121, 107)
GREY_LINE = (203, 210, 217)


class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x0, x1, y, color):
        if y < 0 or y >= self.h:
            return
        x0, x1 = max(0, x0), min(self.w - 1, x1)
        row = bytes(color) * (x1 - x0 + 1)
        i = (y * self.w + x0) * 3
        self.px[i:i + len(row)] = row

    def vline(self, x, y0, y1, color):
        if x < 0 or x >= self.w:
            return
        for y in range(max(0, y0), min(self.h, y1 + 1)):
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def line(self, x0, y0, x1, y1, color):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.hline(cx - dx, cx + dx, cy + dy, color)

    def ring(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.set(cx - dx, cy + dy, color)
            self.set(cx + dx, cy + dy, color)
            dx2 = int(((r - 1) * (r - 1) - dy * dy) ** 0.5) if abs(dy) < r - 1 else 0
            self.hline(cx - dx2, cx + dx2, cy + dy, color) if False else None
        # thin outline: draw circle perimeter via parametric points
        import math
        for deg in range(0, 360, 2):
            a = math.radians(deg)
            self.set(cx + int(r * math.cos(a)), cy + int(r * math.sin(a)), color)

    def fill_polygon(self, pts, color):
        # Scanline fill. pts: list of (x, y) ints, closed implicitly.
        if len(pts) < 3:
            return
        ys = [p[1] for p in pts]
        for y in range(max(0, min(ys)), min(self.h, max(ys) + 1)):
            xs = []
            n = len(pts)
            for i in range(n):
                x0, y0 = pts[i]
                x1, y1 = pts[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                    xs.append(x)
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                self.hline(int(xs[i]), int(xs[i + 1]), y, color)


def text_width(s, scale):
    return len(s) * 6 * scale


def draw_text(cv, x, y, s, scale, color):
    for ch in s:
        glyph = FONT.get(ch)
        if glyph is None:
            glyph = FONT['?']
        for row in range(7):
            bits = glyph[row]
            for col in range(5):
                if bits[col] == '1':
                    cv.fill_rect(x + col * scale, y + row * scale,
                                 scale, scale, color)
        x += 6 * scale


def draw_text_centered(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_width(s, scale) // 2, y, s, scale, color)


def wrap_text(s, scale, max_w):
    """Greedy word wrap; returns list of lines fitting max_w pixels."""
    lines, cur = [], ""
    for word in s.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            # long single word: hard-split it
            while text_width(word, scale) > max_w:
                n = max_w // (6 * scale)
                lines.append(word[:n])
                word = word[n:]
            cur = word
    if cur:
        lines.append(cur)
    return lines

# ---------------------------------------------------------------- map
# Schematic continents, equirectangular. Map area: full width,
# y MAP_Y0..MAP_Y1 (lat +90 at top, -90 at bottom).
MAP_Y0, MAP_Y1 = 76, 400


def lonlat(lon, lat):
    x = int((lon + 180.0) / 360.0 * W)
    y = int(MAP_Y0 + (90.0 - lat) / 180.0 * (MAP_Y1 - MAP_Y0))
    return (x, y)


def poly(cv, lonlat_pts, color):
    cv.fill_polygon([lonlat(lo, la) for lo, la in lonlat_pts], color)


CONTINENTS = [
    # North America
    [(-168, 66), (-158, 58), (-152, 60), (-140, 60), (-135, 57), (-130, 54),
     (-125, 49), (-124, 42), (-120, 34), (-114, 29), (-110, 24), (-105, 20),
     (-97, 16), (-90, 14), (-83, 9), (-79, 9), (-84, 13), (-87, 16),
     (-90, 21), (-96, 19), (-97, 26), (-93, 30), (-84, 30), (-81, 26),
     (-80, 32), (-76, 35), (-74, 39), (-70, 42), (-68, 45), (-65, 44),
     (-60, 47), (-60, 52), (-64, 58), (-72, 62), (-78, 62), (-85, 66),
     (-95, 69), (-110, 68), (-125, 70), (-140, 70), (-155, 71), (-168, 66)],
    # Greenland
    [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68), (-22, 70),
     (-25, 74), (-32, 76), (-45, 76), (-55, 76), (-58, 72), (-58, 64)],
    # South America
    [(-77, 7), (-72, 11), (-64, 10), (-60, 8), (-52, 5), (-50, 0),
     (-44, -3), (-35, -8), (-39, -15), (-40, -22), (-48, -27), (-57, -38),
     (-65, -41), (-68, -50), (-70, -54), (-74, -53), (-73, -44), (-72, -37),
     (-70, -30), (-70, -22), (-75, -15), (-77, -12), (-81, -6), (-81, 0),
     (-80, 4), (-77, 7)],
    # Africa
    [(-17, 15), (-17, 21), (-15, 27), (-10, 31), (-5, 35), (0, 36),
     (10, 37), (11, 34), (20, 32), (30, 31), (35, 28), (37, 22),
     (39, 18), (43, 12), (48, 11), (51, 12), (51, 10), (46, 5),
     (42, 0), (40, -5), (40, -10), (36, -18), (32, -26), (28, -33),
     (20, -35), (17, -32), (15, -27), (12, -18), (13, -12), (12, -6),
     (9, 4), (4, 6), (-8, 5), (-13, 8), (-17, 12), (-17, 15)],
    # Eurasia
    [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (0, 50), (3, 51),
     (5, 53), (8, 55), (8, 57), (10, 59), (5, 60), (5, 62), (10, 64),
     (12, 66), (18, 69), (25, 71), (30, 70), (35, 68), (40, 68),
     (45, 68), (50, 69), (55, 68), (60, 69), (65, 69), (70, 72),
     (75, 72), (80, 73), (85, 74), (90, 75), (95, 76), (100, 77),
     (105, 77), (110, 74), (115, 73), (120, 73), (125, 72), (130, 72),
     (135, 71), (140, 72), (145, 72), (150, 70), (155, 69), (160, 69),
     (165, 66), (170, 66), (178, 65), (178, 62), (170, 60), (162, 58),
     (158, 52), (155, 50), (150, 60), (142, 55), (142, 50), (140, 40),
     (135, 35), (130, 33), (127, 35), (122, 38), (120, 32), (122, 28),
     (118, 25), (110, 21), (108, 18), (105, 10), (103, 8), (100, 7),
     (98, 10), (95, 15), (92, 21), (89, 22), (86, 20), (80, 15),
     (77, 8), (75, 20), (72, 20), (70, 22), (66, 25), (62, 25),
     (58, 26), (56, 27), (52, 26), (50, 29), (48, 30), (44, 29),
     (40, 31), (36, 36), (33, 36), (30, 36), (26, 38), (23, 36),
     (19, 40), (18, 42), (14, 45), (12, 44), (8, 44), (3, 43),
     (0, 40), (-2, 37), (-6, 36), (-9, 37), (-10, 36)],
    # United Kingdom
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53), (1, 51),
     (-5, 50)],
    # Japan
    [(130, 31), (132, 33), (135, 34), (137, 35), (139, 37), (140, 39),
     (141, 41), (141, 44), (143, 43), (141, 39), (139, 36), (136, 34),
     (133, 34), (130, 31)],
    # Indonesia / SE Asia islands (schematic single chain)
    [(95, 5), (98, 3), (100, 0), (102, -3), (105, -5), (108, -6),
     (110, -7), (114, -8), (118, -9), (120, -10), (122, -8), (125, -8),
     (128, -4), (131, -2), (132, 0), (128, 1), (124, 1), (120, 0),
     (117, 1), (114, 2), (110, 1), (106, 3), (103, 1), (100, 4),
     (97, 5), (95, 5)],
    # Australia
    [(114, -22), (114, -30), (115, -34), (118, -35), (124, -33),
     (129, -32), (132, -32), (135, -35), (138, -35), (140, -38),
     (145, -38), (150, -37), (153, -32), (153, -27), (150, -22),
     (146, -19), (142, -15), (142, -11), (140, -17), (136, -15),
     (135, -12), (132, -11), (130, -13), (126, -14), (122, -17),
     (118, -20), (114, -22)],
    # New Zealand
    [(167, -45), (170, -42), (173, -40), (175, -38), (177, -38),
     (175, -41), (172, -43), (168, -46), (167, -45)],
    # Antarctica (schematic strip)
    [(-180, -70), (-120, -70), (-60, -70), (0, -70), (60, -70),
     (120, -70), (180, -70), (180, -78), (120, -78), (60, -78),
     (0, -78), (-60, -78), (-120, -78), (-180, -78)],
]

# Pins for stories 1-15: (number, lon, lat, dx, dy) — dx/dy nudge the
# drawn pin away from its true spot when two pins would collide.
PINS = [
    (1, -77, 39, 0, 0),
    (2, -74, 40.7, 0, 0),
    (3, 47, 29, 0, 0),
    (4, 100, 40, 0, 0),
    (5, 160, -9.6, 0, 0),
    (6, 35.2, 31.8, 0, 0),
    (7, 31.2, 30, 0, 0),
    (8, -75.5, 10.4, 0, 0),
    (9, 106.8, -6.6, 0, 0),
    (10, 42.3, 55.7, 0, 0),
    (11, 19, 52, 0, 0),
    (12, 34.5, 11.5, 0, 0),
    (13, 90.4, 23.8, 0, 0),
    (14, -122, 37.4, 0, 0),
    (15, -74, 40.7, 20, -18),  # shares NYC with pin 2; offset with leader
]

# ---------------------------------------------------------------- stories
# (number, headline, detail) — lead stories, from NEWS_25NOV.md.
LEAD = [
    (1, "US proposes new tariffs on 14 trading partners",
     "Trump fires a new trade salvo over excess industrial capacity. "
     "Highest rates aimed at China; EU, Japan, India, Indonesia and "
     "9 others named. Duties would not stack on July tariffs."),
    (2, "Wall Street whiplash before Thanksgiving",
     "Dow erases a 1,100-point fall to close +0.33% at 50,182.95. "
     "S&P 500 -0.25% to 7,182.78; Nasdaq -0.62% to 23,585.80. "
     "Q3 GDP revised up to 4.3%; core PCE inflation 3.3%."),
    (3, "Middle East escalation on three fronts",
     "Houthis claim a strike on Saudi Arabia's Ras Tanura refinery*. "
     "Iran's Guard claims two tankers hit mines in the Strait of "
     "Hormuz*. Israeli strike in Gaza City kills a senior Hamas "
     "security chief. US tells citizens to leave Iran. (*claims)"),
]

MEDIUM = [
    (4, "Shenzhou-24 docks: first foreign astronaut on Tiangong"),
    (5, "Solomon Islands signs security treaty with Australia"),
    (6, "Judges urge dropping key Netanyahu bribery case"),
    (7, "Cairo tanker fire kills at least 31, injures 21"),
    (8, "Cartagena supermarket hostages freed, siege ends"),
    (9, "Bogor gold-mine flood: 9 dead, 17 trapped"),
    (10, "Ukraine says it hit five Russian jets at Savasleyka*"),
    (11, "Poland to create no-fly zone near Ukraine border"),
    (12, "Sudan: RSF drone strikes kill 19 in Blue Nile"),
    (13, "Bangladesh garment wage up 36% to 17,000 taka"),
    (14, "S&P puts Nvidia on downgrade watch; shares -3.9%"),
    (15, "Macy's parade postponed to Sat 28 Nov by storm"),
]

# Also-today stories 16-56, one short line each.
ALSO = [
    (16, "N. Korea expels Swiss diplomat"),
    (17, "UK warns firms of Russian sabotage threat"),
    (18, "Two Libyan officers die in Ukraine strike"),
    (19, "Iraq court backs federal border control"),
    (20, "Saudi coalition strikes Hodeidah port"),
    (21, "Saudi coalition downs Houthi drones"),
    (22, "Houthis advance on Aden"),
    (23, "US tells citizens to leave Iran"),
    (24, "Leaked data: 490,334+ Russian war dead*"),
    (25, "Ukraine needs EUR 115bn for 2027"),
    (26, "Six dead in plane crash off Mississippi"),
    (27, "US Army detonates 4,400 kg of explosives"),
    (28, "Russian strikes kill civilians in Odesa, Kyiv"),
    (29, "Russian strikes hit Ukraine energy system"),
    (30, "Ukraine claims laser downed a drone*"),
    (31, "Eisenkot secures first coalition partner"),
    (32, "Vance: Nvidia's Huang needs no pardon"),
    (33, "Sen. Booker demands Nvidia answers"),
    (34, "Judge blocks birthright-citizenship order"),
    (35, "Abrego Garcia leaves US for Spain"),
    (36, "Microsoft 'Code Red' after worst outage"),
    (37, "CrowdStrike to buy Zscaler for $43.9bn"),
    (38, "Dell: record $132.3bn AI-server backlog"),
    (39, "Brain organoids in space: Alzheimer's clues"),
    (40, "Oil jumps: Brent $94.61 on supply fears"),
    (41, "Rupiah hits record low 18,332 per dollar"),
    (42, "Bank Indonesia sees rate at 6% in 2027"),
    (43, "Indonesia: trade deal shields it from tariffs"),
    (44, "Prabowo orders Garuda Indonesia revamp"),
    (45, "Indonesia blue-economy investment $5.1bn"),
    (46, "Nigeria: militants kill 30 in Niger State*"),
    (47, "Pope Leo XIV: concern over COP31 failure"),
    (48, "Germany's Merz accuses Russia"),
    (49, "34 nations urge Moscow: stop riot gas"),
    (50, "Man Utd held 2-2 at Sporting"),
    (51, "Liverpool win 3-0 at Club Brugge"),
    (52, "Lille stun Bayern 2-1; PSG held 2-2"),
    (53, "California king tides flood the coast"),
    (54, "East Coast storm: emergencies declared"),
    (55, "Jolie and Pitt settle winery battle"),
    (56, "Met Police: racism, misogyny persist"),
]

# ---------------------------------------------------------------- build
LEAD_COLORS = [RED, BLUE, ORANGE]


def draw_pin(cv, num, lon, lat, dx, dy):
    x, y = lonlat(lon, lat)
    px, py = x + dx, y + dy
    if dx or dy:
        cv.line(x, y, px, py, INK)
        cv.fill_circle(x, y, 3, RED)
    cv.fill_circle(px, py, 11, RED)
    cv.ring(px, py, 11, WHITE)
    label = str(num)
    draw_text(cv, px - text_width(label, 2) // 2, py - 7, label, 2, WHITE)


def build():
    cv = Canvas(W, H, PAPER)

    # ---- header
    cv.fill_rect(0, 0, W, MAP_Y0, NAVY)
    cv.fill_rect(0, MAP_Y0 - 4, W, 4, GOLD)
    draw_text_centered(cv, W // 2, 10, "25 NOVEMBER 2026", 6, WHITE)
    draw_text_centered(cv, W // 2, 56,
                       "WORLD NEWS IN ONE IMAGE - 56 STORIES - PINS 1-15 ON THE MAP",
                       1, (200, 214, 230))

    # ---- map
    cv.fill_rect(0, MAP_Y0, W, MAP_Y1 - MAP_Y0, OCEAN)
    for pts in CONTINENTS:
        poly(cv, pts, LAND)
    # graticule: equator + a few meridians, faint
    eq_y = lonlat(0, 0)[1]
    cv.hline(0, W - 1, eq_y, (170, 200, 220))
    for lon in (-120, -60, 0, 60, 120):
        x = lonlat(lon, 0)[0]
        cv.vline(x, MAP_Y0, MAP_Y1 - 1, (170, 200, 220))
    for num, lon, lat, dx, dy in PINS:
        draw_pin(cv, num, lon, lat, dx, dy)
    cv.fill_rect(0, MAP_Y1 - 2, W, 2, GREY_LINE)

    # ---- lead stories: 3 boxes
    box_y, box_h, box_w = 408, 184, 324
    for i, (num, head, detail) in enumerate(LEAD):
        x = 12 + i * (box_w + 14)
        cv.fill_rect(x, box_y, box_w, box_h, WHITE)
        cv.fill_rect(x, box_y, box_w, 8, LEAD_COLORS[i])
        for xx in (x, x + box_w - 1):
            cv.vline(xx, box_y, box_y + box_h - 1, GREY_LINE)
        cv.hline(x, x + box_w - 1, box_y + box_h - 1, GREY_LINE)
        # number badge + tag
        cv.fill_circle(x + 24, box_y + 30, 13, LEAD_COLORS[i])
        draw_text(cv, x + 24 - text_width(str(num), 2) // 2, box_y + 23,
                  str(num), 2, WHITE)
        draw_text(cv, x + 44, box_y + 24, "LEAD STORY", 2, LEAD_COLORS[i])
        # headline, scale 2, wrapped
        y = box_y + 52
        for line in wrap_text(head, 2, box_w - 24):
            draw_text(cv, x + 12, y, line, 2, INK)
            y += 16
        y += 6
        for line in wrap_text(detail, 1, box_w - 24):
            draw_text(cv, x + 12, y, line, 1, MUTED)
            y += 11

    # ---- medium stories: heading + 2 columns x 6 rows
    draw_text(cv, 12, 606, "THE DAY IN BRIEF - 12 MORE STORIES", 2, NAVY)
    cv.hline(12, W - 12, 626, GREY_LINE)
    for i, (num, text) in enumerate(MEDIUM):
        col = i % 2
        row = i // 2
        x = 12 + col * 506
        y = 636 + row * 27
        cv.fill_circle(x + 9, y + 4, 9, NAVY2)
        draw_text(cv, x + 9 - text_width(str(num), 1) // 2, y + 1,
                  str(num), 1, WHITE)
        for j, line in enumerate(wrap_text(text, 1, 462)):
            draw_text(cv, x + 24, y + j * 11, line, 1, INK)

    # ---- also today: heading + 3 columns x 14 rows
    draw_text(cv, 12, 800, "ALSO TODAY - 41 MORE  * = CLAIM, UNVERIFIED",
              2, NAVY)
    cv.hline(12, W - 12, 820, GREY_LINE)
    for i, (num, text) in enumerate(ALSO):
        col = i % 3
        row = i // 3
        x = 12 + col * 338
        y = 830 + row * 13
        draw_text(cv, x, y, "%d. %s" % (num, text), 1, INK)

    # ---- footer
    draw_text_centered(cv, W // 2, 1012,
                       "All stories first reported Tue 25 Nov 2026 - figures as reported that day",
                       1, MUTED)
    return cv


# ---------------------------------------------------------------- png
def chunk(typ, data):
    out = struct.pack(">I", len(data)) + typ + data
    out += struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)
    return out


def encode_png(cv):
    raw = bytearray()
    for y in range(cv.h):
        raw.append(0)  # filter: none
        raw += cv.px[y * cv.w * 3:(y + 1) * cv.w * 3]
    ihdr = struct.pack(">IIBBBBB", cv.w, cv.h, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    # Clear only the CONTENTS of the output dir, never the dir itself.
    for child in out_path.iterdir():
        if child.is_dir():
            import shutil
            shutil.rmtree(child)
        else:
            child.unlink()
    data = encode_png(build())
    target = out_path / "entry.png"
    target.write_bytes(data)
    print("wrote %s (%d bytes, %dx%d)" % (target, len(data), W, H))
    return 0


if __name__ == "__main__":
    sys.exit(main())
