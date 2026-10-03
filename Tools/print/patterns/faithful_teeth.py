#!/usr/bin/python3
"""faithful_teeth: Direction A of the crisp FrontRooms wallpaper (Backrooms chevron).

Keeps the ikat character of the CC0 reference but makes it exact. Every smeared
element (the big field chevrons and the small motif-band chevrons/diamonds) is cut
into vertical "warp strips", the way ikat warp threads are shifted before weaving.
The stack slides alternately up and down strip by strip, so every boundary between
two inks becomes a crisp square-wave interlock parallel to the chevron arm. The
outer edges carry regular flat-ended bars (spikes on top, drips below) in the places
where the reference has its dye streaks. The straight stripes are unchanged.

This file is the single source of truth for the geometry. One list of
vertical-sided trapezoids feeds both the SVG (merged into polygons, inks grouped)
and the raster frames.

Run:  /usr/bin/python3 Tools/print/patterns/faithful_teeth.py
Writes Tools/print/patterns/out/faithful_teeth/:
  faithful_teeth.svg    750 x 1125 mm vector tile, one <g id="ink-*"> per ink
  K00.png               1024 x 1536 encoded print frame (R ink density, G cream)
  preview_lobby.png     print_tool preview (2 x 2, Lobby palette)
  preview_palette.png   2 x 2 tiling in the reference palette, 1 px = 1 mm
  distance.png          Lobby-shaded strip at 2 m / 6 m / 13 m viewing distance
Units are millimetres; one tile is one roll repeat (750 wide, 1125 tall), y down.
"""
import json
import math
import os
import shutil
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

KEY = "faithful_teeth"
HERE = os.path.dirname(os.path.abspath(__file__))
PRINT_DIR = os.path.dirname(HERE)
PRINT_TOOL = os.path.join(PRINT_DIR, "print_tool.py")
ORIGINAL_K00 = os.path.join(PRINT_DIR, "frames", "chevron_test", "K00_original.png")
OUT = os.path.join(HERE, "out", KEY)

TILE_W, TILE_H = 750.0, 1125.0
UNIT_W = 375.0                 # two identical column units per tile
FIELD_DROP = 562.5             # unit 2's field chevrons are half-dropped
FRAME_W, FRAME_H = 1024, 1536  # game print slice
SS = 4                         # supersampling for the encoded frame
MIN_FEATURE = 4.0              # mm: smallest allowed feature
MIN_PERIOD = 12.0              # mm: finest allowed repeating detail

PALETTE = {                    # reference palette, sRGB
    "beige": "#EEDDCC",        # ground
    "cream": "#F4F0EC",
    "grey": "#BBBEC0",
    "pink": "#DBAFA5",
    "slate": "#9B9BAA",
    "deep": "#887799",
}
INKS = ["cream", "grey", "pink", "slate", "deep"]   # SVG group order; inks never overlap
LABEL = {"beige": 0, **{k: i + 1 for i, k in enumerate(INKS)}}

# ------------------------------------------------------------------ stripes (measured, unit 1)
# The straddling white stripe ends where unit 1's right hairline ends (369.6 - 375 = -5.4),
# so the two 375 mm units abut exactly with no overlapping shapes.
STRIPES = [
    ("cream", -5.4, 8.3),
    ("pink", 8.3, 31.3),
    ("cream", 31.3, 45.6),
    ("slate", 45.6, 49.4),     # motif band border
    # motif band 49.4 - 99.2
    ("slate", 99.2, 102.9),    # motif band border
    ("cream", 102.9, 117.7),
    ("pink", 117.7, 140.7),
    ("cream", 140.7, 155.4),
    ("pink", 155.4, 159.1),    # field hairline
    # field 159.1 - 365.8
    ("pink", 365.8, 369.6),    # field hairline
]

# ------------------------------------------------------------------ teeth vocabulary
# Every chevron is cut into vertical warp strips (index j, 0 = the apex strip).
#  * Warp slide: the whole stack shifts alternately up and down strip by strip, so every
#    edge between two inks becomes a square-wave interlock running parallel to the arm.
#    The apex strip always slides the way the chevron points, so the tip leads.
#  * Spikes: on strips that slide up, the outer top edge rises further as a flat-topped bar.
#  * Drips: on strips that slide down, the outer bottom edge hangs further as a flat bar.
# An edge is (y at the apex line, slope, offset(j), flat(j)); flat strips are level at
# the strip centre's height instead of following the arm.
def EVEN(j):
    return j % 2 == 0


def ODD(j):
    return j % 2 == 1


def NEVER(j):
    return False


def APEX(j):
    return j == 0


def offsets(slide, apex_up, spikes=None, drips=None):
    """Offset of one edge per strip. spikes/drips: extra length keyed by |j| % 4, or
    'apex' for j = 0. apex_up: the apex strip (and every even strip) slides up."""
    spikes, drips = spikes or {}, drips or {}

    def f(j):
        a = abs(j)
        key = "apex" if a == 0 else a % 4
        if (a % 2 == 0) == apex_up:
            return -slide - spikes.get(key, 0.0)
        return slide + drips.get(key, 0.0)
    return f


# ------------------------------------------------------------------ field chevrons
# A stack of two chevrons pointing up, centred in the field. 25 warp strips of
# 8.268 mm: the field edges fall exactly on strip edges, so nothing is clipped thin.
FIELD_X0, FIELD_X1 = 159.1, 365.8
FIELD_C = (FIELD_X0 + FIELD_X1) / 2          # 262.45
FIELD_N = 12                                 # strips each side of the centre strip
FIELD_U = (FIELD_X1 - FIELD_X0) / (2 * FIELD_N + 1)
FIELD_SLOPE = 1.2                            # mm of drop per mm away from the apex
FIELD_SLIDE = 7.0

FIELD_BOUNDS = {
    # upper chevron: grey / pink / slate
    "U0": (75.0, FIELD_SLOPE, offsets(FIELD_SLIDE, True, spikes={"apex": 30, 0: 20, 2: 10}), EVEN),
    "U1": (136.0, FIELD_SLOPE, offsets(FIELD_SLIDE, True), NEVER),
    "U2": (177.0, FIELD_SLOPE, offsets(FIELD_SLIDE, True), NEVER),
    "U3": (215.0, FIELD_SLOPE, offsets(FIELD_SLIDE, True, drips={1: 18, 3: 9}), ODD),
    # lower chevron: grey with cream drips beneath
    "L0": (322.0, FIELD_SLOPE, offsets(FIELD_SLIDE, True, spikes={"apex": 26, 0: 16, 2: 8}), EVEN),
    "L1": (388.0, FIELD_SLOPE, offsets(FIELD_SLIDE, True), NEVER),
    "L2": (412.0, FIELD_SLOPE, offsets(FIELD_SLIDE, True, drips={1: 22, 3: 12}), ODD),
}
FIELD_BANDS = [
    ("grey", "U0", "U1"), ("pink", "U1", "U2"), ("slate", "U2", "U3"),
    ("grey", "L0", "L1"), ("cream", "L1", "L2"),
]
FIELD_GAPS = [("U3", "L0")]                  # beige between the two chevrons

# ------------------------------------------------------------------ motif band
# Between the slate borders: a cream diamond, then a small grey / pink / slate
# chevron pointing DOWN (as in the reference), repeated 4x per tile, not half-dropped.
# 7 warp strips of 7.114 mm; local y is measured from the diamond's side points.
BAND_X0, BAND_X1 = 49.4, 99.2
BAND_C = (BAND_X0 + BAND_X1) / 2             # 74.3
BAND_N = 3
BAND_U = (BAND_X1 - BAND_X0) / (2 * BAND_N + 1)
BAND_PERIOD = TILE_H / 4                     # 281.25
BAND_Y0 = 225.0                              # first diamond's side points (measured)
V_SLOPE = -1.75                              # the small chevrons point down
D_SLOPE = 1.2                                # diamond crown
BAND_SLIDE = 5.0
# These chevrons point down, so the apex strip slides down: odd strips up, even strips down.
BAND_WARP = offsets(BAND_SLIDE, False)
BAND_HEM = offsets(BAND_SLIDE, False, drips={2: 8})
CROWN_SPIKE = 20.0                           # the diamond's centre spike (above the slide)
DEEP_TIP = 12.0                              # deep bar under the centre strip of each small chevron

BAND_BOUNDS = {
    # diamond crown: the shoulders follow the warp slide, the centre strip is a flat spike
    "M0": (-38.0, D_SLOPE, lambda j: BAND_WARP(j) - (CROWN_SPIKE if j == 0 else 0.0), APEX),
    "M1": (44.0, V_SLOPE, BAND_WARP, NEVER),       # diamond / grey
    "M2": (100.0, V_SLOPE, BAND_WARP, NEVER),      # grey / pink
    "M3": (151.0, V_SLOPE, BAND_WARP, NEVER),      # pink / slate
    "M4": (198.0, V_SLOPE, BAND_HEM, EVEN),                         # slate hem, drips flat
    # deep tip: a flat-ended bar under the centre strip only; equal to M4 everywhere else
    "M5": (198.0, V_SLOPE, lambda j: BAND_HEM(j) + (DEEP_TIP if j == 0 else 0.0), EVEN),
}
BAND_BANDS = [
    ("cream", "M0", "M1"), ("grey", "M1", "M2"), ("pink", "M2", "M3"),
    ("slate", "M3", "M4"), ("deep", "M4", "M5"),
]


# ------------------------------------------------------------------ geometry core
class Trap:
    """Vertical-sided trapezoid: x in [xa, xb], top ta->tb, bottom ba->bb (linear)."""
    __slots__ = ("ink", "shape", "xa", "xb", "ta", "tb", "ba", "bb")

    def __init__(self, ink, shape, xa, xb, ta, tb, ba, bb):
        self.ink, self.shape = ink, shape
        self.xa, self.xb, self.ta, self.tb, self.ba, self.bb = xa, xb, ta, tb, ba, bb

    def moved(self, dx, dy, tag):
        return Trap(self.ink, self.shape + tag, self.xa + dx, self.xb + dx,
                    self.ta + dy, self.tb + dy, self.ba + dy, self.bb + dy)


def strip_pieces(c, u, n):
    """Strips j = -n..n of width u centred on c. The centre strip is split at c so
    every piece is linear (the apex kink sits on the split)."""
    out = []
    for j in range(-n, n + 1):
        xa, xb = c + (j - .5) * u, c + (j + .5) * u
        if j == 0:
            out += [(j, xa, c), (j, c, xb)]
        else:
            out.append((j, xa, xb))
    return out


def edge_y(bound, c, j, x, dy, u):
    y0, slope, off, flat = bound
    if flat(j):
        x = c + j * u                      # a spike / drip end: level, at the strip centre's height
    return dy + y0 + slope * abs(x - c) + off(j)


def build_stack(bounds, bands, c, u, n, dx, dy, tag, report):
    traps = []
    for j, xa, xb in strip_pieces(c, u, n):
        for ink, up, lo in bands:
            ta, tb = edge_y(bounds[up], c, j, xa, dy, u), edge_y(bounds[up], c, j, xb, dy, u)
            ba, bb = edge_y(bounds[lo], c, j, xa, dy, u), edge_y(bounds[lo], c, j, xb, dy, u)
            ha, hb = ba - ta, bb - tb
            if ha <= 1e-9 and hb <= 1e-9:
                continue                                   # band absent in this strip
            if min(ha, hb) < MIN_FEATURE - 1e-6:
                raise SystemExit(f"{tag}:{ink} strip {j} only {min(ha, hb):.2f} mm thick")
            report["thickness"] = min(report.get("thickness", 1e9), ha, hb)
            traps.append(Trap(ink, f"{tag}:{ink}:{up}", xa + dx, xb + dx, ta, tb, ba, bb))
    return traps


def check_bounds(name, bounds, bands, c, u, n, pairs, report):
    """Steps between neighbouring strips must be 0 or >= MIN_FEATURE (no hairline jogs);
    where a band crosses a strip edge the neck must be >= MIN_FEATURE (or the two pieces
    clearly apart); beige gaps listed in pairs must stay >= MIN_FEATURE."""
    for ink, up, lo in bands:
        for j in range(-n, n):
            x = c + (j + .5) * u
            t0, b0 = edge_y(bounds[up], c, j, x, 0, u), edge_y(bounds[lo], c, j, x, 0, u)
            t1, b1 = edge_y(bounds[up], c, j + 1, x, 0, u), edge_y(bounds[lo], c, j + 1, x, 0, u)
            if b0 - t0 <= 1e-9 or b1 - t1 <= 1e-9:
                continue
            neck = min(b0, b1) - max(t0, t1)
            if abs(neck) < MIN_FEATURE - 1e-6:
                raise SystemExit(f"{name}:{ink} {neck:.2f} mm neck between strips {j} and {j + 1}")
            if neck > 0:
                report["neck"] = min(report.get("neck", 1e9), neck)
    for key, b in bounds.items():
        for j in range(-n, n):
            x = c + (j + .5) * u                       # shared edge of strips j and j + 1
            step = abs(edge_y(b, c, j + 1, x, 0, u) - edge_y(b, c, j, x, 0, u))
            if 1e-9 < step < MIN_FEATURE - 1e-6:
                raise SystemExit(f"{name}.{key}: {step:.2f} mm jog between strips {j} and {j + 1}")
            if step > 1e-9:
                report["step"] = min(report.get("step", 1e9), step)
    for up, lo in pairs:
        for j, xa, xb in strip_pieces(c, u, n):
            for x in (xa, xb):
                g = edge_y(bounds[lo], c, j, x, 0, u) - edge_y(bounds[up], c, j, x, 0, u)
                if g < MIN_FEATURE:
                    raise SystemExit(f"{name}: gap {up}-{lo} only {g:.2f} mm at strip {j}")
                report["gap"] = min(report.get("gap", 1e9), g)


def design():
    """Every shape of one tile as Traps (before wrapping)."""
    report = {}
    check_bounds("field", FIELD_BOUNDS, FIELD_BANDS, FIELD_C, FIELD_U, FIELD_N, FIELD_GAPS, report)
    # The band's gap check has to look across one period: slate hem vs the next diamond.
    nxt = dict(BAND_BOUNDS)
    y0, sl, off, flat = BAND_BOUNDS["M0"]
    nxt["M0next"] = (y0 + BAND_PERIOD, sl, off, flat)
    check_bounds("band", nxt, BAND_BANDS, BAND_C, BAND_U, BAND_N, [("M5", "M0next"), ("M4", "M0next")], report)

    traps = []
    for unit in range(2):
        dx = unit * UNIT_W
        for k, (ink, x0, x1) in enumerate(STRIPES):
            traps.append(Trap(ink, f"u{unit}:stripe{k}", x0 + dx, x1 + dx, 0, 0, TILE_H, TILE_H))
        traps += build_stack(FIELD_BOUNDS, FIELD_BANDS, FIELD_C, FIELD_U, FIELD_N,
                             dx, unit * FIELD_DROP, f"u{unit}:field", report)
        for k in range(4):
            traps += build_stack(BAND_BOUNDS, BAND_BANDS, BAND_C, BAND_U, BAND_N,
                                 dx, BAND_Y0 + k * BAND_PERIOD, f"u{unit}:band{k}", report)
    report["strip_width"] = min(FIELD_U, BAND_U)
    report["tooth_period"] = 2 * min(FIELD_U, BAND_U)
    assert report["tooth_period"] >= MIN_PERIOD
    return traps, report


# ------------------------------------------------------------------ wrap + clip
def clip_trap(t, X0=0.0, X1=TILE_W, Y0=0.0, Y1=TILE_H):
    """Clip a Trap to the tile rectangle; returns a list of Traps."""
    xa, xb = max(t.xa, X0), min(t.xb, X1)
    if xb - xa <= 1e-9:
        return []
    w = t.xb - t.xa

    def top(x):
        return t.ta + (t.tb - t.ta) * (x - t.xa) / w

    def bot(x):
        return t.ba + (t.bb - t.ba) * (x - t.xa) / w

    cuts = {xa, xb}
    for fa, fb, lvl in ((t.ta, t.tb, Y0), (t.ta, t.tb, Y1), (t.ba, t.bb, Y0), (t.ba, t.bb, Y1)):
        if (fa - lvl) * (fb - lvl) < 0:
            x = t.xa + (lvl - fa) / (fb - fa) * w
            if xa < x < xb:
                cuts.add(x)
    cuts = sorted(cuts)
    out = []
    for a, b in zip(cuts, cuts[1:]):
        m = (a + b) / 2
        if max(top(m), Y0) >= min(bot(m), Y1):
            continue
        out.append(Trap(t.ink, t.shape, a, b, max(top(a), Y0), max(top(b), Y0),
                        min(bot(a), Y1), min(bot(b), Y1)))
    return out


def wrap(traps):
    """Copies at -750/0/+750 x -1125/0/+1125, clipped to the tile: the tile repeats seamlessly
    and every shape that crosses an edge is split there."""
    out = []
    for t in traps:
        for dx in (-TILE_W, 0.0, TILE_W):
            for dy in (-TILE_H, 0.0, TILE_H):
                out += clip_trap(t.moved(dx, dy, f"@{dx:+.0f},{dy:+.0f}"))
    return out


# ------------------------------------------------------------------ polygons for the SVG
def merge(traps):
    """Group pieces by shape and join neighbours that share a vertical edge into one
    x-monotone polygon. Returns {ink: [polygon point lists]}."""
    by_shape = {}
    for t in traps:
        by_shape.setdefault((t.ink, t.shape), []).append(t)
    polys = {ink: [] for ink in INKS}
    for (ink, _), ts in by_shape.items():
        ts.sort(key=lambda t: t.xa)
        chains, cur = [], [ts[0]]
        for t in ts[1:]:
            p = cur[-1]
            joined = abs(p.xb - t.xa) < 1e-7 and min(p.bb, t.ba) - max(p.tb, t.ta) > 1e-6
            if joined:
                cur.append(t)
            else:
                chains.append(cur)
                cur = [t]
        chains.append(cur)
        for ch in chains:
            pts = []
            for t in ch:
                pts += [(t.xa, t.ta), (t.xb, t.tb)]
            for t in reversed(ch):
                pts += [(t.xb, t.bb), (t.xa, t.ba)]
            polys[ink].append(simplify(pts))
    return polys


def simplify(pts):
    out = []
    for p in pts:
        if not out or abs(p[0] - out[-1][0]) > 1e-7 or abs(p[1] - out[-1][1]) > 1e-7:
            out.append(p)
    if len(out) > 1 and abs(out[0][0] - out[-1][0]) < 1e-7 and abs(out[0][1] - out[-1][1]) < 1e-7:
        out.pop()
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            cross = (b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0])
            if abs(cross) < 1e-6:
                out.pop(i)
                changed = True
                break
    return out


def fmt(v):
    s = f"{round(v, 2):.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def write_svg(path, polys):
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(TILE_W)} {fmt(TILE_H)}" '
        f'width="{fmt(TILE_W)}mm" height="{fmt(TILE_H)}mm">',
        f'  <title>FrontRooms wallpaper, {KEY} (1 unit = 1 mm, one 750 x 1125 roll repeat)</title>',
        f'  <rect id="ground-beige" x="0" y="0" width="{fmt(TILE_W)}" height="{fmt(TILE_H)}" '
        f'fill="{PALETTE["beige"]}"/>',
    ]
    n = 0
    for ink in INKS:
        lines.append(f'  <g id="ink-{ink}" fill="{PALETTE[ink]}">')
        for p in sorted(polys[ink], key=lambda q: (min(x for x, _ in q), min(y for _, y in q))):
            xs, ys = [x for x, _ in p], [y for _, y in p]
            if len(p) == 4 and len(set(round(x, 6) for x in xs)) == 2 and len(set(round(y, 6) for y in ys)) == 2:
                x0, y0 = min(xs), min(ys)
                lines.append(f'    <rect x="{fmt(x0)}" y="{fmt(y0)}" width="{fmt(max(xs) - x0)}" '
                             f'height="{fmt(max(ys) - y0)}"/>')
            else:
                lines.append('    <polygon points="' + " ".join(f"{fmt(x)},{fmt(y)}" for x, y in p) + '"/>')
            n += 1
        lines.append("  </g>")
    lines.append("</svg>")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return n


# ------------------------------------------------------------------ raster
def rasterize(traps, px_per_mm):
    """Label map (0 = beige ground) sampled at pixel centres, half-open edges, so shapes
    that share an edge split it exactly. Returns (labels, overlap pixel count)."""
    W, H = int(round(TILE_W * px_per_mm)), int(round(TILE_H * px_per_mm))
    lab = np.zeros((H, W), np.uint8)
    hits = np.zeros((H, W), np.uint8)
    S = px_per_mm
    for t in traps:
        i0 = max(0, math.ceil(t.xa * S - .5))
        i1 = min(W, math.ceil(t.xb * S - .5))
        if i1 <= i0:
            continue
        cx = (np.arange(i0, i1) + .5) / S
        f = (cx - t.xa) / (t.xb - t.xa)
        top = t.ta + (t.tb - t.ta) * f
        bot = t.ba + (t.bb - t.ba) * f
        r0 = np.clip(np.ceil(top * S - .5), 0, H).astype(int)
        r1 = np.clip(np.ceil(bot * S - .5), 0, H).astype(int)
        lo, hi = r0.min(), r1.max()
        if hi <= lo:
            continue
        rows = np.arange(lo, hi)[:, None]
        m = (rows >= r0[None]) & (rows < r1[None])
        sub = lab[lo:hi, i0:i1]
        sub[m] = LABEL[t.ink]
        hsub = hits[lo:hi, i0:i1]
        hsub[m] += 1
    return lab, int((hits > 1).sum())


def hex01(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32) / 255


def lut():
    names = ["beige"] + INKS
    rgb = np.stack([hex01(PALETTE[k]) for k in names])
    lum = rgb @ np.array([.2126, .7152, .0722], np.float32)
    R = np.clip((0.92 - lum) / 0.35, 0, 1).astype(np.float32)
    G = np.clip((lum - 0.90) / 0.06, 0, 1).astype(np.float32)
    return rgb, R, G


def box(a, f):
    h, w = a.shape[0] // f, a.shape[1] // f
    return a.reshape(h, f, w, f, *a.shape[2:]).mean((1, 3))


def save_rgba(path, R, G):
    z = np.zeros_like(R)
    a = np.stack([R, G, z, np.ones_like(R)], -1)
    Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8), "RGBA").save(path)


def distance_sheet(path, enc):
    """Lobby-shaded strip (tile x4 wide) at 2 / 6 / 13 m. 1080p, 76 deg vertical FOV.
    The encoding is area-averaged first, then shaded, which is what the mip chain does."""
    sys.path.insert(0, PRINT_DIR)
    import print_tool
    strip = np.tile(enc, (1, 4, 1))                       # 3.0 x 1.125 m
    rows, target_w = [], None
    for d in (2.0, 6.0, 13.0):
        ppm = 1080 / (2 * d * math.tan(math.radians(38)))
        w, h = max(1, round(3.0 * ppm)), max(1, round(1.125 * ppm))
        ch = [np.asarray(Image.fromarray(np.ascontiguousarray(strip[..., c]), "F")
                         .resize((w, h), Image.BOX), np.float32) for c in range(3)]
        col = print_tool.shade(np.stack(ch, -1))
        img = Image.fromarray((np.clip(col, 0, 1) * 255 + .5).astype(np.uint8))
        if target_w is None:
            target_w = w
        k = max(1, round(target_w / w))
        rows.append((d, ppm, img.resize((w * k, h * k), Image.NEAREST)))
    pad, lab_h = 16, 26
    W = max(r[2].width for r in rows) + 2 * pad
    H = sum(r[2].height + lab_h + pad for r in rows) + pad
    sheet = Image.new("RGB", (W, H), (24, 24, 24))
    dr = ImageDraw.Draw(sheet)
    y = pad
    for d, ppm, img in rows:
        dr.text((pad, y + 6), f"{KEY}  K00 Lobby palette  {d:g} m  ({ppm:.0f} px/m, "
                f"tooth period {2 * min(FIELD_U, BAND_U) * ppm / 1000:.2f} px)", fill=(235, 235, 235))
        sheet.paste(img, (pad, y + lab_h))
        y += img.height + lab_h + pad
    sheet.save(path)


# ------------------------------------------------------------------ main
def main():
    os.makedirs(OUT, exist_ok=True)
    traps, report = design()
    pieces = wrap(traps)

    # a) SVG
    polys = merge(pieces)
    svg_path = os.path.join(OUT, f"{KEY}.svg")
    n_shapes = write_svg(svg_path, polys)

    rgb_lut, R_lut, G_lut = lut()

    # b) K00: 4x supersampled, encode per pixel at high resolution, then box down by 4
    lab, overlaps = rasterize(pieces, FRAME_W * SS / TILE_W)
    assert lab.shape == (FRAME_H * SS, FRAME_W * SS), lab.shape
    R = box(R_lut[lab], SS)
    G = box(G_lut[lab], SS)
    coverage = {k: round(float((lab == LABEL[k]).mean()), 4) for k in ["beige"] + INKS}
    del lab
    k00 = os.path.join(OUT, "K00.png")
    save_rgba(k00, R, G)

    # c) preview_lobby + validate through print_tool on a folder holding only K00.png
    tmp = os.path.join(OUT, "_k00_only")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    shutil.copy(k00, os.path.join(tmp, "K00.png"))
    py = sys.executable or "/usr/bin/python3"
    val = subprocess.run([py, PRINT_TOOL, "validate", tmp], capture_output=True, text=True)
    subprocess.run([py, PRINT_TOOL, "preview", tmp, os.path.join(OUT, "preview_lobby.png")],
                   check=True, capture_output=True, text=True)
    shutil.rmtree(tmp, ignore_errors=True)

    # d) preview_palette: 2x2 in the reference palette, 1 px = 1 mm (4x4 supersampled)
    lab4, _ = rasterize(pieces, 4.0)
    tile = np.stack([box(rgb_lut[lab4][..., c], 4) for c in range(3)], -1)
    del lab4
    Image.fromarray((np.tile(tile, (2, 2, 1)) * 255 + .5).astype(np.uint8)).save(
        os.path.join(OUT, "preview_palette.png"))

    # e) distance strip (reads the saved 8-bit frame, like the game would)
    enc = np.asarray(Image.open(k00).convert("RGB"), np.float32) / 255
    enc[..., 2] = 0
    distance_sheet(os.path.join(OUT, "distance.png"), enc)

    orig = np.asarray(Image.open(ORIGINAL_K00).convert("RGB"), np.float32) / 255
    summary = {
        "key": KEY,
        "files": sorted(os.path.join(OUT, f) for f in os.listdir(OUT)),
        "svg_shapes": n_shapes,
        "validate": val.stdout.strip(),
        "validate_pass": val.returncode == 0,
        "mean_R": round(float(enc[..., 0].mean()), 4),
        "mean_G": round(float(enc[..., 1].mean()), 4),
        "original_mean_R": round(float(orig[..., 0].mean()), 4),
        "original_mean_G": round(float(orig[..., 1].mean()), 4),
        "raster_overlap_px": overlaps,
        "coverage": coverage,
        "smallest_feature_mm": round(min(report["strip_width"], report["step"], report["neck"],
                                         report["thickness"], report["gap"]), 2),
        "checks_mm": {k: round(v, 2) for k, v in report.items()},
    }
    print(json.dumps(summary, indent=2))
    if not summary["validate_pass"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
