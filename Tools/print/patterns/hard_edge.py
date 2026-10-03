#!/usr/bin/env python3
"""FrontRooms wallpaper print, direction B "hard_edge".

The Backrooms chevron paper redrawn as a hard-edge flat print: the stripes are kept
exactly as measured from the CC0 ikat recreation, and only the smeared parts (the big
field chevrons and the small motif-band arrows) are redrawn as clean polygons. Every
diagonal in the design runs at one angle (ARM_DEG), every band keeps a constant
thickness, and band corners are straight mitres.

Run (numpy + Pillow, nothing else):
    /usr/bin/python3 Tools/print/patterns/hard_edge.py

Writes Tools/print/patterns/out/hard_edge/:
    hard_edge.svg        750 x 1125 mm tile, one <g id="ink-*"> per ink, polygons/rects only
    K00.png              encoded game print frame, 1024x1536 RGBA (R density, G cream)
    preview_lobby.png    print_tool.py preview (2x2 in the game's Lobby palette)
    preview_palette.png  2x2 tiling in the reference palette, 1500 px wide
    distance.png         Lobby-palette strip at simulated 2 m / 6 m / 13 m viewing distance

Single source of truth: build_regions() describes every shape once (mm, y down);
tile_pieces() wraps and splits them at the tile edges and rounds to 0.01 mm. The SVG
and every raster are made from that one polygon list.
"""
import math
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

KEY = "hard_edge"
HERE = os.path.dirname(os.path.abspath(__file__))
PRINT_DIR = os.path.dirname(HERE)
PRINT_TOOL = os.path.join(PRINT_DIR, "print_tool.py")
OUT_DIR = os.path.join(HERE, "out", KEY)

TW, TH = 750.0, 1125.0                  # one roll repeat, mm
FRAME_W, FRAME_H = 1024, 1536            # game print slice
SUPER = 4                                # supersampling for every raster

PALETTE = {                              # reference palette, sRGB
    "ground": "#EEDDCC",
    "cream": "#F4F0EC",
    "grey": "#BBBEC0",
    "pink": "#DBAFA5",
    "slate": "#9B9BAA",
    "deep": "#887799",
}
INKS = ["cream", "grey", "pink", "slate", "deep"]   # SVG group order, bottom to top

# ------------------------------------------------------------------ design parameters
ARM_DEG = 55.0                           # every diagonal in the print, from horizontal
S = math.tan(math.radians(ARM_DEG))      # rise per mm of run

UNIT = 375.0                             # column unit; unit 2 = unit 1 + 375 mm
UNIT2_DROP = TH / 2                      # unit 2's field stack is half-dropped

# Stripes, unit-1 coordinates, measured layout. The listed widths add up to 376.1 mm
# for a 375 mm unit, so the white stripe that follows each pink hairline is trimmed
# by the 1 mm overlap (hairlines are painted over it): it shows 13.7 mm, not 14.7.
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

# Field: a stack of two chevrons pointing up, centred in the field.
FIELD_X0, FIELD_X1 = 159.1, 365.8
FIELD_XC = (FIELD_X0 + FIELD_X1) / 2     # 262.45
UPPER_APEX = 46.0                        # top of the upper chevron at the centre line
UPPER_BANDS = [("grey", 74.0), ("pink", 42.0), ("slate", 34.0)]   # vertical thickness, mm
LOWER_APEX = 294.0
LOWER_BANDS = [("grey", 64.0), ("cream", 26.0)]

# Motif band: small layered arrows pointing down + a cream diamond, 4 repeats per tile.
BAND_X0, BAND_X1 = 49.4, 99.2
BAND_XC = (BAND_X0 + BAND_X1) / 2        # 74.3
BAND_HW = (BAND_X1 - BAND_X0) / 2        # 24.9
PERIOD = TH / 4                          # 281.25
MOTIF_EDGE_Y = 228.0                     # top of the grey arrow where it meets the borders
MOTIF_BANDS = [("grey", 50.0), ("pink", 54.0), ("slate", 44.0)]
# The cream diamond spans the band and its lower half fills the notch of the grey arrow
# exactly, so it is the top layer of the arrow stack (as the ikat cream sits on its grey).
DROP_HW = 6.0                            # deep pendant under each arrow tip (the ikat drip)
DROP_GAP = 6.0                           # beige between the slate tip and the pendant


# ------------------------------------------------------------------ shapes
# Every shape is an x-monotone region: an x range plus a piecewise-linear top edge and
# bottom edge (lists of (x, y) breakpoints). That makes clipping at the tile edges exact
# and lets one band stay one polygon.
class Region:
    def __init__(self, ink, top, bot):
        self.ink, self.top, self.bot = ink, top, bot

    def moved(self, dx, dy):
        mv = lambda pts: [(x + dx, y + dy) for x, y in pts]
        return Region(self.ink, mv(self.top), mv(self.bot))

    def bbox(self):
        xs = [p[0] for p in self.top]
        ys = [p[1] for p in self.top + self.bot]
        return min(xs), max(xs), min(ys), max(ys)


def rect(ink, x0, x1, y0, y1):
    return Region(ink, [(x0, y0), (x1, y0)], [(x0, y1), (x1, y1)])


def chevron(ink, x0, x1, xc, y_apex, thick, up=True):
    """Constant-thickness band with a mitred apex at xc. up=True points up (^): y_apex
    is the top edge at the centre line, the arms fall at S towards x0 and x1."""
    sgn = 1 if up else -1
    top = [(x0, y_apex + sgn * S * (xc - x0)), (xc, y_apex), (x1, y_apex + sgn * S * (x1 - xc))]
    bot = [(x, y + thick) for x, y in top]
    return Region(ink, top, bot)


def diamond(ink, cx, cy, hw):
    hh = S * hw
    return Region(ink, [(cx - hw, cy), (cx, cy - hh), (cx + hw, cy)],
                  [(cx - hw, cy), (cx, cy + hh), (cx + hw, cy)])


def build_regions():
    regs = []
    for u in (0, 1):
        dx = u * UNIT
        for x0, x1, ink in STRIPES:
            regs.append(rect(ink, x0 + dx, x1 + dx, 0.0, TH))

        # field chevron stack (unit 2 half-dropped)
        dy = u * UNIT2_DROP
        for apex, bands in ((UPPER_APEX, UPPER_BANDS), (LOWER_APEX, LOWER_BANDS)):
            y = apex
            for ink, t in bands:
                regs.append(chevron(ink, FIELD_X0 + dx, FIELD_X1 + dx, FIELD_XC + dx, y + dy, t, up=True))
                y += t

        # motif band (identical in both units, not dropped)
        T = sum(t for _, t in MOTIF_BANDS)
        depth = S * BAND_HW                                  # how far the arrow tip hangs
        for k in range(4):
            tip = MOTIF_EDGE_Y + k * PERIOD + depth          # centre of the grey top edge
            y = tip
            for ink, t in MOTIF_BANDS:
                regs.append(chevron(ink, BAND_X0 + dx, BAND_X1 + dx, BAND_XC + dx, y, t, up=False))
                y += t
            # cream diamond sitting in this arrow's notch: side corners on the borders
            regs.append(diamond("cream", BAND_XC + dx, tip - depth, BAND_HW))
            # deep pendant hanging under the slate tip
            slate_tip = tip + T
            regs.append(diamond("deep", BAND_XC + dx, slate_tip + DROP_GAP + S * DROP_HW, DROP_HW))
    return regs


# ------------------------------------------------------------------ clip + wrap
def _interp(pts, x):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return np.interp(x, xs, ys)


def clip_region(r, X0, X1, Y0, Y1):
    """Exact clip of an x-monotone region to a rectangle -> list of polygons."""
    xa, xb = max(r.top[0][0], X0), min(r.top[-1][0], X1)
    if xb - xa < 1e-9:
        return []
    xs = {xa, xb}
    for pts in (r.top, r.bot):
        xs.update(p[0] for p in pts if xa < p[0] < xb)
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            for Y in (Y0, Y1):
                if (y1 - Y) * (y2 - Y) < 0:
                    x = x1 + (Y - y1) * (x2 - x1) / (y2 - y1)
                    if xa < x < xb:
                        xs.add(x)
    xs = sorted(xs)
    g1 = np.clip(_interp(r.top, xs), Y0, Y1)
    g2 = np.clip(_interp(r.bot, xs), Y0, Y1)
    runs, cur = [], None
    for i in range(len(xs) - 1):
        xm = (xs[i] + xs[i + 1]) / 2
        h = np.clip(_interp(r.bot, xm), Y0, Y1) - np.clip(_interp(r.top, xm), Y0, Y1)
        if h > 1e-6:
            cur = [i, i + 1] if cur is None else [cur[0], i + 1]
        elif cur is not None:
            runs.append(cur)
            cur = None
    if cur is not None:
        runs.append(cur)
    polys = []
    for i, j in runs:
        poly = [(xs[k], g1[k]) for k in range(i, j + 1)] + [(xs[k], g2[k]) for k in range(j, i - 1, -1)]
        polys.append(poly)
    return polys


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


def tile_pieces(regs):
    """Wrap every region by -1/0/+1 tile in x and y, split at the tile edges."""
    pieces = []
    for r in regs:
        for ox in (-TW, 0.0, TW):
            for oy in (-TH, 0.0, TH):
                m = r.moved(ox, oy)
                x0, x1, y0, y1 = m.bbox()
                if x1 <= 0 or x0 >= TW or y1 <= 0 or y0 >= TH:
                    continue
                for poly in clip_region(m, 0.0, TW, 0.0, TH):
                    c = clean(poly)
                    if c:
                        pieces.append((r.ink, c))
    return pieces


def feature_report():
    """Smallest features of the redrawn parts (stripes are the measured layout, untouched).
    A band of vertical thickness t whose arms run at ARM_DEG is t*cos(ARM_DEG) thick."""
    c = math.cos(math.radians(ARM_DEG))
    rows = [(f"field {i} band", t * c) for i, t in UPPER_BANDS + LOWER_BANDS]
    rows += [(f"motif {i} arrow", t * c) for i, t in MOTIF_BANDS]
    rows += [("cream diamond width", 2 * BAND_HW), ("deep pendant width", 2 * DROP_HW),
             ("pendant gap under arrow tip", DROP_GAP),
             ("motif beige gap (edge)", PERIOD - sum(t for _, t in MOTIF_BANDS)),
             ("field beige between chevrons", (LOWER_APEX - UPPER_APEX - sum(t for _, t in UPPER_BANDS)) * c)]
    out = [f"arms {ARM_DEG:.0f} deg; smallest redrawn feature {min(v for _, v in rows):.1f} mm"]
    out += [f"  {n:30s} {v:6.1f} mm" for n, v in rows]
    return out


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
        L.append('  </g>')
    L.append('</svg>')
    with open(path, "w") as fh:
        fh.write("\n".join(L) + "\n")


# ------------------------------------------------------------------ raster
def hexc(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float64) / 255


LABELS = ["ground"] + INKS


def rasterise(pieces, w_px, h_px):
    """Label image (index into LABELS) by point-sampling pixel centres, crossing-number
    rule: two polygons that share an edge never both claim a sample."""
    sx, sy = w_px / TW, h_px / TH
    lab = np.zeros((h_px, w_px), np.uint8)
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
    return lab


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
    os.makedirs(OUT_DIR, exist_ok=True)
    regs = build_regions()
    pieces = tile_pieces(regs)

    svg_path = os.path.join(OUT_DIR, f"{KEY}.svg")
    write_svg(pieces, svg_path)

    # K00: encode per sample at 4x, then box-downsample by 4
    lab = rasterise(pieces, FRAME_W * SUPER, FRAME_H * SUPER)
    enc = encode_table()
    R = box_down(enc[lab, 0].astype(np.float32), SUPER)
    G = box_down(enc[lab, 1].astype(np.float32), SUPER)
    k00 = np.stack([R, G, np.zeros_like(R), np.ones_like(R)], -1)
    k00_path = os.path.join(OUT_DIR, "K00.png")
    Image.fromarray((np.clip(k00, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(k00_path)

    # preview_palette: 2x2 tiling in the reference palette, 750 px per tile (1 px = 1 mm)
    pal = np.array([hexc(PALETTE[n]) for n in LABELS], np.float32)
    lab_pp = rasterise(pieces, 750 * SUPER, 1125 * SUPER)
    tile_rgb = box_down(pal[lab_pp], SUPER)
    pp = np.tile(tile_rgb, (2, 2, 1))
    Image.fromarray((pp * 255 + 0.5).astype(np.uint8), "RGB").save(os.path.join(OUT_DIR, "preview_palette.png"))

    # preview_lobby via print_tool (a temp dir holding only K00.png)
    with tempfile.TemporaryDirectory() as td:
        shutil.copy(k00_path, os.path.join(td, "K00.png"))
        subprocess.run([sys.executable, PRINT_TOOL, "preview", td, os.path.join(OUT_DIR, "preview_lobby.png")],
                       check=True)

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

    # seam check through print_tool (a temp dir holding only K00.png)
    with tempfile.TemporaryDirectory() as td:
        shutil.copy(k00_path, os.path.join(td, "K00.png"))
        subprocess.run([sys.executable, PRINT_TOOL, "validate", td], check=True)

    # numbers
    for line in feature_report():
        print(line)
    print(f"pieces: {len(pieces)}  ({', '.join(f'{i}: {sum(1 for p in pieces if p[0] == i)}' for i in INKS)})")
    print(f"K00 mean R {R.mean():.4f}  mean G {G.mean():.4f}")
    cov = np.bincount(lab_pp.ravel(), minlength=len(LABELS)) / lab_pp.size
    print("coverage " + "  ".join(f"{n} {c:.3f}" for n, c in zip(LABELS, cov)))
    print(f"wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
