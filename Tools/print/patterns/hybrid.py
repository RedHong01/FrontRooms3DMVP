#!/usr/bin/env python3
"""FrontRooms wallpaper print, direction D "hybrid".

hard_edge's geometry with the ikat flame put back where the eye reads it: on the outer
silhouette of each field stack only.

  * Stripes: the exact measured layout, with hard_edge's fix for the 1 mm overlap.
  * Field: mitred, constant-thickness chevron bands, every arm at ARM_DEG, stretched to the
    CC0's extents (upper slate arm ends at y 360 on the field edges, lower cream at 520).
    The upper grey band is 15 % heavier than hard_edge's.
  * Flame: flat-ended vertical bars on a regular slot grid (SLOT_PITCH) on three outer
    edges only: spikes rising from the upper grey band, drips hanging from the upper slate
    band and from the lower cream band. Bar lengths come from LENGTH_CLASSES, which were
    measured from the CC0 (run with --measure), in a fixed seeded order. Every boundary
    between two inks stays a clean mitred line.
  * Motif band: hard_edge's down-pointing grey/pink/slate arrows, 4 per tile at the CC0's
    phase, identical in both units. Each cream block is a full-band-width cut gem, 61 mm
    tall: a crown square to the arrow arms (35 deg), 8 mm of straight sides along the slate
    borders, and the grey arrow's 55 deg notch below. One small deep diamond is folded
    into each slate tip; there are no loose specks.

Run (numpy + Pillow, nothing else):
    /usr/bin/python3 Tools/print/patterns/hybrid.py              build everything
    /usr/bin/python3 Tools/print/patterns/hybrid.py --measure    re-derive the streak lengths
    /usr/bin/python3 Tools/print/patterns/hybrid.py --find-seed  first seed passing flame_rules()

Writes Tools/print/patterns/out/hybrid/:
    hybrid.svg           750 x 1125 mm tile, one <g id="ink-*"> per ink, polygons/rects only
    K00.png              encoded game print frame, 1024x1536 RGBA (R density, G cream)
    preview_lobby.png    print_tool.py preview (2x2 in the game's Lobby palette)
    preview_palette.png  2x2 tiling in the reference palette, 1500 px wide
    distance.png         Lobby-palette strip at simulated 2 m / 6 m / 13 m viewing distance

Single source of truth: design() describes every shape once as vertical-sided trapezoids
(mm, y down). wrap() splits them at the tile edges, merge() joins each shape back into one
polygon, and clean() rounds to 0.01 mm. The SVG and every raster use that polygon list.
"""
import json
import math
import os
import random
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

KEY = "hybrid"
HERE = os.path.dirname(os.path.abspath(__file__))
PRINT_DIR = os.path.dirname(HERE)
PRINT_TOOL = os.path.join(PRINT_DIR, "print_tool.py")
OUT_DIR = os.path.join(HERE, "out", KEY)
ORIGINAL_K00 = os.path.join(PRINT_DIR, "frames", "chevron_test", "K00_original.png")
REF_PNG = os.path.join(PRINT_DIR, "..", "lookdev", "ref", "Backrooms_Chevron_CC0.png")

TW, TH = 750.0, 1125.0                  # one roll repeat, mm
FRAME_W, FRAME_H = 1024, 1536            # game print slice
SUPER = 4                                # supersampling for every raster
MIN_FEATURE = 8.0                        # mm, smallest redrawn feature allowed
MIN_PERIOD = 24.0                        # mm, finest repeating detail allowed
MAX_VERTICES = 900

PALETTE = {                              # reference palette, sRGB
    "ground": "#EEDDCC",
    "cream": "#F5F2EE",                  # the CC0's measured white (hard_edge: #F4F0EC)
    "grey": "#BBBEC0",
    "pink": "#DBAFA5",
    "slate": "#9B9BAA",
    "deep": "#887799",
}
INKS = ["cream", "grey", "pink", "slate", "deep"]   # SVG group order; inks never overlap
LABELS = ["ground"] + INKS

# ------------------------------------------------------------------ design parameters
ARM_DEG = 55.0                           # every chevron arm, from horizontal
S = math.tan(math.radians(ARM_DEG))      # rise per mm of run (1.428)
COS = math.cos(math.radians(ARM_DEG))    # vertical band thickness -> true thickness

UNIT = 375.0                             # column unit; unit 2 = unit 1 + 375 mm
UNIT2_DROP = TH / 2                      # unit 2's field stack is half-dropped (+562.5)

# Stripes, unit-1 coordinates, measured layout (hard_edge). The listed widths add up to
# 376.1 mm for a 375 mm unit, so the white stripe that follows each pink hairline is
# trimmed by the 1 mm overlap: it shows 13.7 mm, not 14.7.
STRIPES = [
    (-5.4, 8.3, "cream"),                # listed -6.4..8.3, straddles the tile edge
    (8.3, 31.3, "pink"),
    (31.3, 45.6, "cream"),
    (45.6, 49.4, "slate"),               # motif band border
    (99.2, 102.9, "slate"),              # motif band border
    (102.9, 117.7, "cream"),
    (117.7, 140.7, "pink"),
    (140.7, 155.4, "cream"),
    (155.4, 159.1, "pink"),              # field hairline
    (365.8, 369.6, "pink"),              # field hairline
]

# Field: two up-pointing chevrons, centred in the field, every band mitred at the apex.
FIELD_X0, FIELD_X1 = 159.1, 365.8
FIELD_XC = (FIELD_X0 + FIELD_X1) / 2     # 262.45
FIELD_HALF = FIELD_XC - FIELD_X0         # 103.35
# Vertical thickness, mm. Upper grey 85 = hard_edge's 74 x 1.15. The lower grey stays at 64
# (the CC0 measures 64.4 per column): that keeps 70 mm between the chevrons, room for a
# 38 mm drip with 10 mm of beige left under it.
UPPER_BANDS = [("grey", 85.0), ("pink", 42.0), ("slate", 34.0)]
LOWER_BANDS = [("grey", 64.0), ("cream", 26.0)]
UPPER_END_Y = 360.0                      # upper slate's bottom edge where it meets the field edges
LOWER_END_Y = 520.0                      # lower cream's bottom edge where it meets the field edges
UPPER_APEX = UPPER_END_Y - S * FIELD_HALF - sum(t for _, t in UPPER_BANDS)   # 51.4
LOWER_APEX = LOWER_END_Y - S * FIELD_HALF - sum(t for _, t in LOWER_BANDS)   # 282.4

# Flame bars. A bar's length L is measured on its SHORT side: the side where the sloping band
# edge comes closest to the bar's flat end (the apex spike: either side). L is the same
# quantity measure_reference() reads off the CC0 (topographic prominence of a streak tip
# above its higher flanking notch), and every jog is >= the shortest class. The long side
# is L + BAR_W * S.
BAR_W = 10.0                             # the in-range width nearest the CC0's streaks (7-9 mm)
SLOT_PITCH = 28.0                        # horizontal; 48.8 mm along the arm
SLOTS = (-3, -2, -1, 0, 1, 2, 3)         # slot 0 sits on the apex
LENGTH_CLASSES = (12.0, 23.0, 38.0, 51.0)   # mm, measured (see measure_reference)
EMPTY_P = 0.25                           # chance a slot carries no bar
SEED = 549                               # fixed: the first seed whose sequence passes flame_rules()
# (edge, stack, band index, side, class weights). The weights are the CC0's streak counts per
# class on that edge (nearest class, from measure_reference). The upper slate's 51 mm drips are
# folded into 38: a 51 mm drip would come within 8 mm of the lower chevron.
FLAME_EDGES = [
    ("upper_grey_top", "upper", 0, "top", (2, 0, 2, 8)),
    ("upper_slate_bottom", "upper", 2, "bottom", (12, 6, 6, 0)),
    ("lower_cream_bottom", "lower", 1, "bottom", (8, 2, 4, 2)),
]
APEX_RATIO = 1.5                         # apex spike <= 1.5 x the next tallest spike

# Motif band: layered arrows pointing down + a cream block, 4 repeats per tile.
BAND_X0, BAND_X1 = 49.4, 99.2
BAND_XC = (BAND_X0 + BAND_X1) / 2        # 74.3
BAND_HW = (BAND_X1 - BAND_X0) / 2        # 24.9
PERIOD = TH / 4                          # 281.25
MOTIF_EDGE_Y = 228.0                     # top of the grey arrow at the borders (the CC0's phase)
MOTIF_BANDS = [("grey", 50.0), ("pink", 54.0), ("slate", 44.0)]
# Cream block ("gem"): full band width. From the bottom up: the grey arrow's notch
# (S * BAND_HW = 35.6 mm, filled exactly), BLOCK_SIDE of straight sides along the slate
# borders (the CC0's cream touches the borders from ~215 to the grey at 226), and a crown
# whose edges are square to the arrow arms (35 deg, BAND_HW / S = 17.4 mm). 61.0 mm tall.
CROWN_H = BAND_HW / S
BLOCK_SIDE = 8.0
BLOCK_H = CROWN_H + BLOCK_SIDE + S * BAND_HW
DEEP_HW = 7.0                            # deep diamond folded into each slate tip: 14 x 20 mm

# Reference measurement (measure_reference)
REF_INKS = ["#EDDDC4", "#F5F2EE", "#D9B2A7", "#B8BDBF", "#9A9DA5", "#D8AB9F", "#847F91"]  # [0] = ground
REF_DIVIDER = 252.0                      # detrended y of the beige gap between the CC0's two chevrons
REF_WINDOW = 16.0                        # mm searched either side of a streak tip for its notches
REF_MIN_LEN = 8.0                        # shorter tip bumps are not streaks


# ------------------------------------------------------------------ flame sequence
def flame_sequence(seed=SEED):
    """Bar lengths per edge and slot (0 = no bar), one seeded stream for all edges."""
    rng = random.Random(seed)
    seq = {}
    for edge, _, _, _, weights in FLAME_EDGES:
        row = []
        for _ in SLOTS:
            if rng.random() < EMPTY_P:
                row.append(0.0)
            else:
                row.append(rng.choices(LENGTH_CLASSES, weights)[0])
        seq[edge] = row
    return seq


def flame_rules(seq):
    """Design rules for the sequence; returns the list of broken rules (empty = pass)."""
    bad = []
    mid = SLOTS.index(0)
    for edge, row in seq.items():
        bars = [L for L in row if L > 0]
        empties = len(row) - len(bars)
        if not 1 <= empties <= 2:
            bad.append(f"{edge}: {empties} empty slots (want 1-2)")
        if len(set(bars)) < 3:
            bad.append(f"{edge}: fewer than 3 different lengths")
        if any(row[i] > 0 and row[i] == row[i + 1] == row[i + 2] for i in range(len(row) - 2)):
            bad.append(f"{edge}: three equal bars in a row")
        if sum(L > 0 for L in row[:mid]) < 2 or sum(L > 0 for L in row[mid + 1:]) < 2:
            bad.append(f"{edge}: an arm with fewer than 2 bars")
    spikes = seq["upper_grey_top"]
    apex, rest = spikes[mid], sorted((L for i, L in enumerate(spikes) if i != mid), reverse=True)
    if apex <= 0 or apex < rest[0] or apex > APEX_RATIO * rest[0]:
        bad.append(f"apex spike {apex} vs next tallest {rest[0]}")
    return bad


def find_seed(limit=10000):
    for s in range(limit):
        if not flame_rules(flame_sequence(s)):
            return s
    return None


# ------------------------------------------------------------------ shapes
class Trap:
    """Vertical-sided trapezoid: x in [xa, xb], top ta->tb, bottom ba->bb (linear)."""
    __slots__ = ("ink", "shape", "xa", "xb", "ta", "tb", "ba", "bb")

    def __init__(self, ink, shape, xa, xb, ta, tb, ba, bb):
        self.ink, self.shape = ink, shape
        self.xa, self.xb, self.ta, self.tb, self.ba, self.bb = xa, xb, ta, tb, ba, bb

    def moved(self, dx, dy, tag=""):
        return Trap(self.ink, self.shape + tag, self.xa + dx, self.xb + dx,
                    self.ta + dy, self.tb + dy, self.ba + dy, self.bb + dy)


def band_traps(ink, shape, x0, x1, xc, y_top, y_bot, spikes=(), drips=()):
    """An up-pointing chevron band (top edge y_top, bottom edge y_bot on the centre line,
    arms falling at S) with flat-ended bars: spikes on the top edge, drips on the bottom.
    spikes/drips: (xa, xb, L) with L the free length on the bar's short side."""
    top = lambda x: y_top + S * abs(x - xc)
    bot = lambda x: y_bot + S * abs(x - xc)
    sp = [(a, b, min(top(a), top(b)) - L) for a, b, L in spikes]
    dr = [(a, b, max(bot(a), bot(b)) + L) for a, b, L in drips]
    xs = sorted({x0, x1, xc} | {v for a, b, _ in sp + dr for v in (a, b)})
    out = []
    for a, b in zip(xs, xs[1:]):
        m = (a + b) / 2
        ta, tb, ba, bb = top(a), top(b), bot(a), bot(b)
        for sa, sb, ye in sp:
            if sa < m < sb:
                ta = tb = ye
        for sa, sb, ye in dr:
            if sa < m < sb:
                ba = bb = ye
        out.append(Trap(ink, shape, a, b, ta, tb, ba, bb))
    return out


def slot_bars(row):
    """(xa, xb, L) for every occupied slot of one edge (unit-1 coordinates)."""
    out = []
    for k, L in zip(SLOTS, row):
        if L > 0:
            c = FIELD_XC + k * SLOT_PITCH
            out.append((c - BAR_W / 2, c + BAR_W / 2, L))
    return out


def field_traps(seq, tag):
    traps = []
    for stack, apex, bands in (("upper", UPPER_APEX, UPPER_BANDS), ("lower", LOWER_APEX, LOWER_BANDS)):
        y = apex
        for i, (ink, t) in enumerate(bands):
            sp, dr = [], []
            for edge, st, bi, side, _ in FLAME_EDGES:
                if st == stack and bi == i:
                    (sp if side == "top" else dr).extend(slot_bars(seq[edge]))
            traps += band_traps(ink, f"{tag}:{stack}{i}:{ink}", FIELD_X0, FIELD_X1, FIELD_XC, y, y + t, sp, dr)
            y += t
    return traps


def motif_traps(k, tag):
    """Repeat k of the motif band: cream block, grey / pink / slate arrows, deep tip."""
    e = MOTIF_EDGE_Y + k * PERIOD
    xc, hw = BAND_XC, BAND_HW
    vee = lambda y0: (lambda x: y0 + S * (hw - abs(x - xc)))          # down-pointing edge
    crown = lambda x: e - BLOCK_SIDE - CROWN_H * (1 - abs(x - xc) / hw)
    edges = [vee(e)]
    y = e
    for _, t in MOTIF_BANDS:
        y += t
        edges.append(vee(y))
    tip = edges[-1](xc)
    deep_top = lambda x: tip - 2 * S * DEEP_HW + S * abs(x - xc)
    slate_bot = lambda x: deep_top(x) if abs(x - xc) < DEEP_HW - 1e-9 else edges[-1](x)
    shapes = [("cream", crown, edges[0])]
    for (ink, _), up, lo in zip(MOTIF_BANDS, edges, edges[1:]):
        shapes.append((ink, up, lo))
    shapes[-1] = ("slate", edges[-2], None)                            # bottom resolved per interval
    xs = [BAND_X0, xc - DEEP_HW, xc, xc + DEEP_HW, BAND_X1]
    out = []
    for a, b in zip(xs, xs[1:]):
        inner = abs((a + b) / 2 - xc) < DEEP_HW
        for ink, up, lo in shapes:
            if lo is None:
                lo = deep_top if inner else edges[-1]
            out.append(Trap(ink, f"{tag}:{ink}", a, b, up(a), up(b), lo(a), lo(b)))
        if inner:
            out.append(Trap("deep", f"{tag}:deep", a, b, deep_top(a), deep_top(b), edges[-1](a), edges[-1](b)))
    return out


def design(seq):
    """Every shape of one tile as Traps (before wrapping)."""
    traps = []
    for u in (0, 1):
        dx = u * UNIT
        for i, (x0, x1, ink) in enumerate(STRIPES):
            traps.append(Trap(ink, f"u{u}:stripe{i}", x0 + dx, x1 + dx, 0.0, 0.0, TH, TH))
        traps += [t.moved(dx, u * UNIT2_DROP) for t in field_traps(seq, f"u{u}:field")]
        for k in range(4):
            traps += [t.moved(dx, 0.0) for t in motif_traps(k, f"u{u}:motif{k}")]
    return traps


# ------------------------------------------------------------------ wrap + clip + merge
def clip_trap(t, X0, X1, Y0, Y1):
    """Clip a Trap to a rectangle; returns a list of Traps."""
    xa, xb = max(t.xa, X0), min(t.xb, X1)
    if xb - xa <= 1e-9:
        return []
    w = t.xb - t.xa
    top = lambda x: t.ta + (t.tb - t.ta) * (x - t.xa) / w
    bot = lambda x: t.ba + (t.bb - t.ba) * (x - t.xa) / w
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


def wrap(traps, margin=0.0):
    """Copies at -1/0/+1 tile in x and y, clipped to the tile (grown by margin): the tile
    repeats seamlessly and every shape that crosses an edge is split there."""
    out = []
    for t in traps:
        for dx in (-TW, 0.0, TW):
            for dy in (-TH, 0.0, TH):
                out += clip_trap(t.moved(dx, dy, f"@{dx:+.0f},{dy:+.0f}"),
                                 -margin, TW + margin, -margin, TH + margin)
    return out


def merge(traps):
    """Join the trapezoids of each shape that share a vertical edge into one x-monotone
    polygon. Returns [(ink, shape, points)]."""
    by_shape = {}
    for t in traps:
        by_shape.setdefault((t.ink, t.shape), []).append(t)
    polys = []
    for (ink, shape), ts in sorted(by_shape.items()):
        ts.sort(key=lambda t: t.xa)
        chains, cur = [], [ts[0]]
        for t in ts[1:]:
            p = cur[-1]
            if abs(p.xb - t.xa) < 1e-7 and min(p.bb, t.ba) - max(p.tb, t.ta) > 1e-6:
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
            polys.append((ink, shape, simplify(pts)))
    return polys


def simplify(pts):
    """Drop repeated and collinear vertices BEFORE rounding, so that two inks sharing an
    edge also share its vertices (no rounded T-junctions, no hairline slivers)."""
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


def clean(poly, nd=2):
    """Round to 0.01 mm, drop repeated and collinear vertices."""
    p = [(round(float(x), nd), round(float(y), nd)) for x, y in poly]
    out = []
    for v in p:
        if not out or v != out[-1]:
            out.append(v)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    changed = True
    while changed and len(out) > 3:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            cross = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if abs(cross) < 1e-6:
                out.pop(i)
                changed = True
                break
    return out if len(out) >= 3 else None


def tile_pieces(traps, margin=0.0, keep_shape=False):
    pieces = []
    for ink, shape, poly in merge(wrap(traps, margin)):
        c = clean(poly)
        if c:
            pieces.append((ink, shape, c) if keep_shape else (ink, c))
    return pieces


# ------------------------------------------------------------------ checks
def _closest(P, A, B):
    """Closest pair between points P (n,2) and segments AB (m,2): (distance, point, foot)."""
    d = B - A
    L2 = np.maximum((d ** 2).sum(1), 1e-12)
    t = np.clip(((P[:, None, :] - A[None]) * d[None]).sum(2) / L2[None], 0, 1)
    q = A[None] + t[..., None] * d[None]
    D = np.sqrt(((P[:, None, :] - q) ** 2).sum(2))
    i, j = np.unravel_index(D.argmin(), D.shape)
    return D[i, j], P[i], q[i, j]


def shape_key(tag):
    """Shape tags are '<shape>@<dx>,<dy>' (wrap copy). A stripe runs the full tile height, so
    its copies stacked at dy = -TH/0/+TH are one stripe in the plane."""
    return tag.rsplit(",", 1)[0] if "stripe" in tag else tag


def gap_report(pieces, is_ground):
    """Smallest beige gap between two shapes that do not touch, measured on the tile grown
    by 60 mm so gaps across the tile edges are seen too. Pieces of one shape that the window
    edge or the wrap cut apart are one shape in the plane. A gap counts only if the middle
    of the shortest segment between the two shapes is bare ground (is_ground(x, y)), so a
    hairline lying between two shapes is not mistaken for a gap."""
    groups = {}
    for ink, tag, p in pieces:
        groups.setdefault(shape_key(tag), []).append(np.array(p, np.float64))
    keys = sorted(groups)
    bb = {k: (min(p[:, 0].min() for p in groups[k]), max(p[:, 0].max() for p in groups[k]),
              min(p[:, 1].min() for p in groups[k]), max(p[:, 1].max() for p in groups[k])) for k in keys}
    m = 2 * MIN_FEATURE
    best = (1e9, None)
    for i, ki in enumerate(keys):
        for kj in keys[i + 1:]:
            a, b = bb[ki], bb[kj]
            if a[0] > b[1] + m or b[0] > a[1] + m or a[2] > b[3] + m or b[2] > a[3] + m:
                continue
            c = min((_closest(pi, pj, np.roll(pj, -1, 0)) for pi in groups[ki] for pj in groups[kj]),
                    key=lambda r: r[0])
            c = min([c] + [_closest(pj, pi, np.roll(pi, -1, 0)) for pi in groups[ki] for pj in groups[kj]],
                    key=lambda r: r[0])
            d, p, q = c
            if d < 1e-6 or d >= best[0]:
                continue
            mx, my = (p + q) / 2
            if is_ground(mx % TW, my % TH):
                best = (d, (ki, kj, (round(float(mx), 1), round(float(my), 1))))
    return best


def feature_report(seq):
    """Smallest features of the redrawn parts (stripes are the measured layout, untouched).
    A band of vertical thickness t whose arms run at ARM_DEG is t*cos(ARM_DEG) thick."""
    used = sorted({L for row in seq.values() for L in row if L > 0})
    gap_v = LOWER_APEX - (UPPER_APEX + sum(t for _, t in UPPER_BANDS))
    longest_drip = max(seq["upper_slate_bottom"])
    rows = [(f"field {i} band", t * COS) for i, t in UPPER_BANDS + LOWER_BANDS]
    rows += [(f"motif {i} arrow", t * COS) for i, t in MOTIF_BANDS]
    rows += [("flame bar width", BAR_W),
             ("shortest bar side (shortest class)", min(used)),
             ("beige between neighbouring bars", SLOT_PITCH - BAR_W),
             ("beige from outer bar to field hairline", FIELD_HALF - (max(SLOTS) * SLOT_PITCH + BAR_W / 2)),
             ("field beige between chevrons", gap_v * COS),
             ("upper drip end to lower grey (true)", (gap_v - BAR_W * S - longest_drip) * COS),
             ("cream block height", BLOCK_SIDE + CROWN_H + S * BAND_HW),
             ("cream block straight full-width sides", BLOCK_SIDE),
             ("deep tip width", 2 * DEEP_HW),
             ("slate above deep tip (true)", (MOTIF_BANDS[-1][1] - 2 * S * DEEP_HW) * COS),
             ("slot pitch (finest period)", SLOT_PITCH)]
    return rows


def rasterise(pieces, w_px, h_px, count=False):
    """Label image (index into LABELS) by point-sampling pixel centres, crossing-number
    rule: two polygons that share an edge never both claim a sample."""
    sx, sy = w_px / TW, h_px / TH
    lab = np.zeros((h_px, w_px), np.uint8)
    hits = np.zeros((h_px, w_px), np.uint8) if count else None
    for ink, poly in pieces:
        P = np.array(poly, np.float64) * (sx, sy)
        i0, i1 = max(int(np.floor(P[:, 0].min())), 0), min(int(np.ceil(P[:, 0].max())), w_px)
        j0, j1 = max(int(np.floor(P[:, 1].min())), 0), min(int(np.ceil(P[:, 1].max())), h_px)
        if i1 <= i0 or j1 <= j0:
            continue
        X = (np.arange(i0, i1) + 0.5)[None, :]
        Y = (np.arange(j0, j1) + 0.5)[:, None]
        inside = np.zeros((j1 - j0, i1 - i0), bool)
        for (x1, y1), (x2, y2) in zip(P, np.roll(P, -1, 0)):
            if y1 == y2:
                continue
            cond = (y1 > Y) != (y2 > Y)
            xint = x1 + (Y - y1) * (x2 - x1) / (y2 - y1)
            inside ^= cond & (X < xint)
        lab[j0:j1, i0:i1][inside] = LABELS.index(ink)
        if count:
            hits[j0:j1, i0:i1] += inside
    return (lab, int((hits > 1).sum())) if count else lab


# ------------------------------------------------------------------ reference measurement
def _peaks(h):
    out, i, n = [], 1, len(h)
    while i < n - 1:
        if h[i] > h[i - 1]:
            j = i
            while j < n - 1 and h[j + 1] == h[i]:
                j += 1
            if j < n - 1 and h[j + 1] < h[i]:
                out.append((i + j) // 2)
            i = j + 1
        else:
            i += 1
    return out


def _prominence(h, i, w):
    """Topographic prominence of peak i, looking at most w samples to each side."""
    a, b = max(0, i - w), min(len(h) - 1, i + w)
    lm, j = h[i], i
    while j > a and h[j - 1] <= h[i]:
        j -= 1
        lm = min(lm, h[j])
    rm, k = h[i], i
    while k < b and h[k + 1] <= h[i]:
        k += 1
        rm = min(rm, h[k])
    return h[i] - max(lm, rm)


def _kmeans_1d(v, k):
    """Optimal 1-D k-means (dynamic programming over the sorted values)."""
    v = np.sort(np.asarray(v, np.float64))
    n = len(v)
    c1, c2 = np.concatenate([[0], np.cumsum(v)]), np.concatenate([[0], np.cumsum(v * v)])
    sse = lambda i, j: (c2[j] - c2[i]) - (c1[j] - c1[i]) ** 2 / (j - i)
    D = np.full((k + 1, n + 1), np.inf)
    B = np.zeros((k + 1, n + 1), int)
    D[0, 0] = 0
    for kk in range(1, k + 1):
        for j in range(kk, n + 1):
            for i in range(kk - 1, j):
                c = D[kk - 1, i] + sse(i, j)
                if c < D[kk, j]:
                    D[kk, j], B[kk, j] = c, i
    groups, j = [], n
    for kk in range(k, 0, -1):
        i = B[kk, j]
        groups.append(v[i:j])
        j = i
    return groups[::-1]


def measure_reference():
    """Streak lengths of the CC0 on the three edges that carry bars here.
    1. Classify every CC0 pixel to the nearest of its 7 flat colours; keep ink vs ground.
    2. In unit 1's field (1 mm in from the hairlines) split each pixel column into the upper
       and lower stack at REF_DIVIDER + S*|x - xc| (the beige gap between the two chevrons)
       and trace three outer edges per column: the upper stack's first ink (grey top), its
       last ink (slate bottom) and the lower stack's last ink (cream/grey bottom).
    3. A streak is a local maximum of that edge's outward height. Its length is its
       topographic prominence within +-REF_WINDOW mm: how far the tip stands free of the
       higher of its two flanking notches, i.e. the free length on the streak's short side,
       which is exactly how a bar's L is defined in this file. Tips < REF_MIN_LEN are bumps.
    4. Optimal 1-D k-means, k = 5, over all streaks of the three edges. One cluster holds only
       the two apex-zone spikes (the reason for the apex rule); the other four centroids,
       rounded, are the length classes. Per-edge counts per class give FLAME_EDGES' weights."""
    a = np.asarray(Image.open(REF_PNG).convert("RGB"), np.float64)[:-1, :-1]  # last row/col repeat the first
    H, W = a.shape[:2]
    sx, sy = W / TW, H / TH
    i0, i1 = int(np.ceil((FIELD_X0 + 1) * sx)), int(np.floor((FIELD_X1 - 1) * sx))
    sub = a[:, i0:i1]
    best = np.full(sub.shape[:2], np.inf)
    lab = np.zeros(sub.shape[:2], np.uint8)
    for k, hx in enumerate(REF_INKS):
        d = ((sub - np.array([int(hx[i:i + 2], 16) for i in (1, 3, 5)])) ** 2).sum(-1)
        lab[d < best] = k
        best = np.minimum(best, d)
    ink = lab != 0
    xs = (np.arange(i0, i1) + 0.5) / sx
    rows = np.arange(H)
    prof = {"upper_grey_top": [], "upper_slate_bottom": [], "lower_cream_bottom": []}
    for c, x in enumerate(xs):
        div = (REF_DIVIDER + S * abs(x - FIELD_XC)) * sy
        up = np.nonzero(ink[:, c] & (rows < div))[0]
        lo = np.nonzero(ink[:, c] & (rows >= div) & (rows < 600 * sy))[0]
        prof["upper_grey_top"].append(-up[0] / sy if len(up) else np.nan)        # height: up is +
        prof["upper_slate_bottom"].append((up[-1] + 1) / sy if len(up) else np.nan)
        prof["lower_cream_bottom"].append((lo[-1] + 1) / sy if len(lo) else np.nan)
    w = int(round(REF_WINDOW * sx))
    lengths = {}
    for edge, h in prof.items():
        h = np.array(h)
        ok = np.isfinite(h)
        h[~ok] = np.interp(np.nonzero(~ok)[0], np.nonzero(ok)[0], h[ok])
        lengths[edge] = [p for p in (_prominence(h, i, w) for i in _peaks(h)) if p >= REF_MIN_LEN]
    allL = [L for v in lengths.values() for L in v]
    groups = _kmeans_1d(allL, 5)
    kept = [g for g in groups if len(g) > 2]
    classes = tuple(float(round(g.mean())) for g in kept)
    counts = {e: tuple(int(sum(1 for L in v if np.argmin([abs(L - c) for c in classes]) == j))
                       for j in range(len(classes))) for e, v in lengths.items()}
    return {
        "streaks": len(allL),
        "clusters_mm": [round(float(g.mean()), 1) for g in groups],
        "cluster_sizes": [len(g) for g in groups],
        "dropped_cluster_mm": [sorted(round(float(x), 1) for x in g) for g in groups if len(g) <= 2],
        "classes_mm": classes,
        "per_edge_lengths_mm": {e: sorted(round(float(L)) for L in v) for e, v in lengths.items()},
        "per_edge_class_counts": counts,
        "per_edge_median_mm": {e: round(float(np.median(v)), 1) for e, v in lengths.items()},
    }


# ------------------------------------------------------------------ SVG
def fmt(v):
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def as_rect(poly):
    if len(poly) != 4:
        return None
    xs = sorted({p[0] for p in poly})
    ys = sorted({p[1] for p in poly})
    if len(xs) == 2 and len(ys) == 2:
        return xs[0], ys[0], xs[1] - xs[0], ys[1] - ys[0]
    return None


def write_svg(pieces, path):
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {fmt(TW)} {fmt(TH)}" '
         f'width="{fmt(TW)}mm" height="{fmt(TH)}mm">',
         f'  <title>FrontRooms wallpaper, {KEY} (1 unit = 1 mm, one roll repeat)</title>',
         f'  <rect id="ground" x="0" y="0" width="{fmt(TW)}" height="{fmt(TH)}" fill="{PALETTE["ground"]}"/>']
    n_shapes = n_vertices = 0
    for ink in INKS:
        L.append(f'  <g id="ink-{ink}" fill="{PALETTE[ink]}">')
        for pink, poly in pieces:
            if pink != ink:
                continue
            rc = as_rect(poly)
            if rc:
                x, y, w, h = rc
                L.append(f'    <rect x="{fmt(x)}" y="{fmt(y)}" width="{fmt(w)}" height="{fmt(h)}"/>')
            else:
                pts = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in poly)
                L.append(f'    <polygon points="{pts}"/>')
            n_shapes += 1
            n_vertices += len(poly)
        L.append('  </g>')
    L.append('</svg>')
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")
    return n_shapes, n_vertices


# ------------------------------------------------------------------ raster
def hexc(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float64) / 255


def encode_table():
    """Game encoding per ink, from the reference palette (0-1 sRGB values)."""
    rows = []
    for name in LABELS:
        c = hexc(PALETTE[name])
        lum = c @ np.array([0.2126, 0.7152, 0.0722])
        rows.append((np.clip((0.92 - lum) / 0.35, 0, 1), np.clip((lum - 0.90) / 0.06, 0, 1)))
    return np.array(rows, np.float64)


def box_down(a, f):
    h, w = a.shape[:2]
    return a.reshape(h // f, f, w // f, f, *a.shape[2:]).mean((1, 3))


def area_resize(f, w, h):
    """Area-averaging resize of a float HxWxC array (PIL BOX per channel)."""
    return np.stack([np.asarray(Image.fromarray(f[..., c].astype(np.float32), "F").resize((w, h), Image.BOX))
                     for c in range(f.shape[2])], -1)


def main():
    if "--measure" in sys.argv:
        print(json.dumps(measure_reference(), indent=2))
        return
    if "--find-seed" in sys.argv:
        print(find_seed())
        return

    seq = flame_sequence(SEED)
    broken = flame_rules(seq)
    if broken:
        sys.exit(f"seed {SEED} breaks the flame rules: {broken}")

    os.makedirs(OUT_DIR, exist_ok=True)
    traps = design(seq)
    pieces = tile_pieces(traps)

    svg_path = os.path.join(OUT_DIR, f"{KEY}.svg")
    n_shapes, n_vertices = write_svg(pieces, svg_path)

    # K00: encode per sample at 4x, then box-downsample by 4
    lab, overlaps = rasterise(pieces, FRAME_W * SUPER, FRAME_H * SUPER, count=True)
    enc = encode_table()
    R = box_down(enc[lab, 0].astype(np.float32), SUPER)
    G = box_down(enc[lab, 1].astype(np.float32), SUPER)
    del lab
    k00 = np.stack([R, G, np.zeros_like(R), np.ones_like(R)], -1)
    k00_path = os.path.join(OUT_DIR, "K00.png")
    Image.fromarray((np.clip(k00, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(k00_path)

    # preview_palette: 2x2 tiling in the reference palette, 750 px per tile (1 px = 1 mm)
    pal = np.array([hexc(PALETTE[n]) for n in LABELS], np.float32)
    lab_pp = rasterise(pieces, 750 * SUPER, 1125 * SUPER)
    tile_rgb = box_down(pal[lab_pp], SUPER)
    pp = np.tile(tile_rgb, (2, 2, 1))
    Image.fromarray((pp * 255 + 0.5).astype(np.uint8), "RGB").save(os.path.join(OUT_DIR, "preview_palette.png"))
    coverage = np.bincount(lab_pp.ravel(), minlength=len(LABELS)) / lab_pp.size

    # preview_lobby + validate through print_tool (a temp dir holding only K00.png)
    with tempfile.TemporaryDirectory() as td:
        shutil.copy(k00_path, os.path.join(td, "K00.png"))
        subprocess.run([sys.executable, PRINT_TOOL, "preview", td, os.path.join(OUT_DIR, "preview_lobby.png")],
                       check=True, capture_output=True, text=True)
        val = subprocess.run([sys.executable, PRINT_TOOL, "validate", td], capture_output=True, text=True)

    # distance: the encoded frame tiled 4 wide, area-averaged to the on-screen pixel
    # density at 2 / 6 / 13 m (1080p, 76 deg vertical FOV), shaded in the Lobby palette
    # (texture filtering happens before the palette in the shader), NN-upscaled.
    sys.path.insert(0, PRINT_DIR)
    import print_tool
    f = np.asarray(Image.open(k00_path).convert("RGB"), np.float32) / 255
    strip = np.tile(f, (1, 4, 1))
    rows = []
    for d in (2, 6, 13):
        ppm = 1080 / (2 * d * math.tan(math.radians(38)))
        w, h = max(1, round(4 * 0.75 * ppm)), max(1, round(1.125 * ppm))
        small = np.clip(area_resize(strip, w, h), 0, 1)
        img = (np.clip(print_tool.shade(small), 0, 1) * 255 + 0.5).astype(np.uint8)
        k = max(1, round(1040 / w))
        rows.append((d, ppm, Image.fromarray(img).resize((w * k, h * k), Image.NEAREST)))
    W = max(r[2].width for r in rows)
    Hh = sum(r[2].height + 24 for r in rows)
    canvas = Image.new("RGB", (W, Hh), (24, 24, 24))
    dr = ImageDraw.Draw(canvas)
    y = 0
    for d, ppm, im in rows:
        dr.text((6, y + 6), f"{KEY}  {d} m  ({ppm:.0f} px per m of wall, 1080p, 76 deg vFOV)", fill=(235, 235, 235))
        canvas.paste(im, (0, y + 24))
        y += im.height + 24
    canvas.save(os.path.join(OUT_DIR, "distance.png"))

    # numbers
    feats = feature_report(seq)
    gap, gap_where = gap_report(tile_pieces(traps, margin=60.0, keep_shape=True),
                                lambda x, y: lab_pp[min(int(y * SUPER), lab_pp.shape[0] - 1),
                                                    min(int(x * SUPER), lab_pp.shape[1] - 1)] == 0)
    smallest = min(min(v for _, v in feats), gap)
    orig = np.asarray(Image.open(ORIGINAL_K00).convert("RGB"), np.float32) / 255
    summary = {
        "key": KEY,
        "files": sorted(os.path.join(OUT_DIR, n) for n in os.listdir(OUT_DIR)),
        "validate": val.stdout.strip(),
        "validate_pass": val.returncode == 0,
        "mean_R": round(float(f[..., 0].mean()), 4),
        "mean_G": round(float(f[..., 1].mean()), 4),
        "target_R": round(float(orig[..., 0].mean()), 4),
        "target_G": round(float(orig[..., 1].mean()), 4),
        "svg_shapes": n_shapes,
        "svg_vertices": n_vertices,
        "raster_overlap_px": overlaps,
        "smallest_feature_mm": round(smallest, 2),
        "smallest_gap_between_shapes_mm": [round(gap, 2), gap_where],
        "features_mm": {n: round(v, 2) for n, v in feats},
        "flame": {"seed": SEED, "classes_mm": LENGTH_CLASSES, "slot_pitch_mm": SLOT_PITCH,
                  "bar_w_mm": BAR_W, "slots": SLOTS, "lengths_mm": seq},
        "field_apex_y": {"upper": round(UPPER_APEX, 2), "lower": round(LOWER_APEX, 2)},
        "coverage": {n: round(float(c), 4) for n, c in zip(LABELS, coverage)},
    }
    print(json.dumps(summary, indent=2))
    ok = (summary["validate_pass"] and overlaps == 0 and n_vertices < MAX_VERTICES
          and smallest >= MIN_FEATURE and SLOT_PITCH >= MIN_PERIOD)
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
