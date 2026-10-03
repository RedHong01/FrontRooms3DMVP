"""FrontRooms wallpaper, direction C: "stepped / woven grid".

A crisp, flat-ink redraw of the Backrooms chevron paper. The stripes keep the
layout measured from the CC0 reference. The smeared ikat parts (the field
chevrons and the narrow motif band) are rebuilt as stair-stepped blocks on an
exact module grid, the way a 1990 southwestern-revival paper would draw a
woven Navajo-style motif.

Single source of truth: SHAPES (built by build_shapes) is a list of
column-strip shapes. Each one is a run of x-contiguous columns, each column a
(x0, x1, y0, y1) block, so it is one rectilinear polygon. The SVG and every
raster are made from that list.

Units are mm. One tile = one roll repeat, 750 x 1125. SVG y points down.

Run:  /usr/bin/python3 Tools/print/patterns/stepped_grid.py
Writes Tools/print/patterns/out/stepped_grid/:
  stepped_grid.svg      750 x 1125 mm, one <g id="ink-*"> per ink, seamless
  K00.png               1024 x 1536 encoded game print frame (R ink, G cream)
  preview_lobby.png     print_tool.py preview (2x2, Lobby palette)
  preview_palette.png   2x2 tiling in the reference palette, 1 px = 1 mm
  distance.png          K00 in the Lobby palette at 2 m / 6 m / 13 m
"""
import math
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw

KEY = "stepped_grid"
HERE = os.path.dirname(os.path.abspath(__file__))
PRINT_DIR = os.path.dirname(HERE)
PRINT_TOOL = os.path.join(PRINT_DIR, "print_tool.py")
OUT = os.path.join(HERE, "out", KEY)
ORIGINAL = os.path.join(PRINT_DIR, "frames", "chevron_test", "K00_original.png")

TW, TH = 750.0, 1125.0                 # tile, mm
UNIT = 375.0                           # two identical column units per tile
DROP = 562.5                           # unit 2 field stack is half-dropped
FW, FH = 1024, 1536                    # game frame
SS = 4                                 # supersampling

# Reference palette (sRGB). Label 0 is the ground.
INKS = ["ground", "cream", "grey", "pink", "slate", "deep"]
HEX = {"ground": "#EEDDCC", "cream": "#F4F0EC", "grey": "#BBBEC0",
       "pink": "#DBAFA5", "slate": "#9B9BAA", "deep": "#887799"}
LABEL = {n: i for i, n in enumerate(INKS)}

# ------------------------------------------------------------------ module grid
M = 6.25                 # module: 6.25 mm divides 375 (60), 562.5 (90), 1125 (180)
STEP_W = 3 * M           # 18.75 mm tread  (> 12 mm, so no fine repeat)
STEP_H = 4 * M           # 25 mm riser     -> arm slope 1.33, as measured (1.3-1.4)
XC = 42 * M              # 262.5: apex column centre, field centre is 261.95
FIELD = (159.1, 364.8)   # beige field between the pink hairlines
BAND_X = [49.4, 55.6, 68.1, 80.5, 93.0, 99.2]   # motif band 49.8 wide: 6.2|12.5|12.4|12.5|6.2
BAND_O = [0.0, 18.75, 37.5, 18.75, 0.0]         # stepped V: edge, mid, tip, mid, edge
BAND_PERIOD = TH / 4     # 281.25, 4 motifs per tile
BAND_PHASE = 6.25        # repeat origin; with it no band edge lands on the y = 0 seam

# Stripes of unit 1 (x0, x1, ink). Unit 2 = +375. The straddling cream stripe
# [-6.4, 8.3] is the same stripe as unit 2's [368.6, 383.3]; the right hairline
# sits at 364.8-368.6 so that unit 1 closes at exactly 375 (the reference's two
# fields measure 206.6 and 205.1 wide; this one is 205.7).
STRIPES = [(-6.4, 8.3, "cream"), (8.3, 31.3, "pink"), (31.3, 45.6, "cream"),
           (45.6, 49.4, "slate"), (99.2, 102.9, "slate"), (102.9, 117.7, "cream"),
           (117.7, 140.7, "pink"), (140.7, 155.4, "cream"), (155.4, 159.1, "pink"),
           (364.8, 368.6, "pink")]


def q(v):
    return round(v * 100) / 100


class Shape:
    """A rectilinear polygon stored as x-contiguous columns (x0, x1, y0, y1)."""

    def __init__(self, name, ink, cols):
        self.name, self.ink = name, ink
        self.cols = [tuple(q(v) for v in c) for c in cols]
        for a, b in zip(self.cols, self.cols[1:]):
            assert abs(a[1] - b[0]) < 1e-9, (name, "columns not contiguous")
            assert min(a[3], b[3]) - max(a[2], b[2]) > 1e-9, (name, "columns do not overlap")

    def moved(self, dx, dy, suffix):
        return Shape(self.name + suffix, self.ink,
                     [(x0 + dx, x1 + dx, y0 + dy, y1 + dy) for x0, x1, y0, y1 in self.cols])


def outline(cols):
    """Column run -> polygon vertices (clockwise in SVG space), collinear points removed."""
    pts = []
    for x0, x1, y0, y1 in cols:                 # top edge, left to right
        pts += [(x0, y0), (x1, y0)]
    for x0, x1, y0, y1 in reversed(cols):       # bottom edge, right to left
        pts += [(x1, y1), (x0, y1)]
    out = []
    for p in pts:
        if out and abs(out[-1][0] - p[0]) < 1e-9 and abs(out[-1][1] - p[1]) < 1e-9:
            continue
        out.append(p)
    if len(out) > 1 and out[0] == out[-1]:
        out.pop()
    changed = True
    while changed and len(out) > 4:
        changed = False
        for i in range(len(out)):
            a, b, c = out[i - 1], out[i], out[(i + 1) % len(out)]
            if (abs(a[0] - b[0]) < 1e-9 and abs(b[0] - c[0]) < 1e-9) or \
               (abs(a[1] - b[1]) < 1e-9 and abs(b[1] - c[1]) < 1e-9):
                out.pop(i)
                changed = True
                break
    return out


# ------------------------------------------------------------------ geometry
def field_columns():
    """Field split into chevron columns: (x0, x1, k, is_crown). k = steps from the apex."""
    cols = [(XC - 2 * M, XC - M, 0, False), (XC - M, XC + M, 0, True), (XC + M, XC + 2 * M, 0, False)]
    k, x = 1, XC + 2 * M
    while x < FIELD[1] - 1e-9:
        cols.append((x, min(x + STEP_W, FIELD[1]), k, False))
        x, k = x + STEP_W, k + 1
    k, x = 1, XC - 2 * M
    while x > FIELD[0] + 1e-9:
        cols.insert(0, (max(x - STEP_W, FIELD[0]), x, k, False))
        x, k = x - STEP_W, k + 1
    return cols


def chevron(name, ink, top0, thick, crown=0.0):
    """A stepped chevron band pointing up: every column k steps down STEP_H."""
    cols = []
    for x0, x1, k, is_crown in field_columns():
        top = top0 + STEP_H * k - (crown if is_crown else 0.0)
        cols.append((x0, x1, top, top0 + STEP_H * k + thick))
    return Shape(name, ink, cols)


def band_layer(name, ink, spans):
    """spans: (y0, y1) per band column group (edge, mid, tip, mid, edge); None skips."""
    cols = [(BAND_X[i], BAND_X[i + 1], s[0], s[1]) for i, s in enumerate(spans) if s is not None]
    return Shape(name, ink, cols)


def build_shapes():
    unit1 = []
    # Field: two stacked chevrons pointing up (upper: grey/pink/slate, lower: grey/cream).
    unit1 += [
        # Band tops/thicknesses are multiples of M; every band is thicker than STEP_H
        # so neighbouring columns overlap and each band stays one polygon.
        chevron("field-upper-grey", "grey", 62.5, 75.0, crown=25.0),    # crown spire 37.5-62.5
        chevron("field-upper-pink", "pink", 137.5, 31.25),
        chevron("field-upper-slate", "slate", 168.75, 37.5),
        chevron("field-lower-grey", "grey", 318.75, 56.25, crown=25.0), # crown spire 293.75-318.75
        chevron("field-lower-cream", "cream", 375.0, 31.25),
    ]
    # Motif band: per repeat a stepped cream diamond, then grey / pink / slate
    # stepped V's pointing down, with a deep drip at the slate tip.
    for r in range(4):
        b = BAND_PHASE + BAND_PERIOD * r
        o = BAND_O
        unit1 += [
            band_layer(f"band-{r}-grey", "grey", [(b - 50 + v, b + 6.25 + v) for v in o]),
            band_layer(f"band-{r}-pink", "pink", [(b + 6.25 + v, b + 62.5 + v) for v in o]),
            band_layer(f"band-{r}-slate", "slate",
                       [(b + 62.5 + v, b + (131.25 if i == 2 else 106.25 + v)) for i, v in enumerate(o)]),
            band_layer(f"band-{r}-deep", "deep", [None, None, (b + 131.25, b + 150.0), None, None]),
            band_layer(f"band-{r}-cream", "cream",
                       [(b + 218.75, b + 231.25), (b + 200, b + 250), (b + 181.25, b + 268.75),
                        (b + 200, b + 250), (b + 218.75, b + 231.25)]),
        ]
    for i, (x0, x1, ink) in enumerate(STRIPES):
        unit1.append(Shape(f"stripe-{i}-{ink}", ink, [(x0, x1, 0.0, TH)]))

    shapes = []
    for s in unit1:
        shapes.append(s.moved(0, 0, "-u1"))
        dy = DROP if s.name.startswith("field") else 0.0
        shapes.append(s.moved(UNIT, dy, "-u2"))
    return shapes


OFFSETS = [(dx, dy) for dx in (-TW, 0.0, TW) for dy in (-TH, 0.0, TH)]


def clipped_runs(shape):
    """Wrap a shape into the tile: shift by every offset, clip columns to the tile,
    split into runs that are still one polygon each."""
    runs = []
    for dx, dy in OFFSETS:
        cur = []
        for x0, x1, y0, y1 in shape.cols:
            c = (max(x0 + dx, 0.0), min(x1 + dx, TW), max(y0 + dy, 0.0), min(y1 + dy, TH))
            ok = c[1] - c[0] > 1e-9 and c[3] - c[2] > 1e-9
            if ok and cur and abs(cur[-1][1] - c[0]) < 1e-9 and min(cur[-1][3], c[3]) - max(cur[-1][2], c[2]) > 1e-9:
                cur.append(c)
                continue
            if cur:
                runs.append(cur)
            cur = [c] if ok else []
        if cur:
            runs.append(cur)
    return runs


# ------------------------------------------------------------------ raster
def fill_polygon(lab, poly, s, value):
    """Even-odd scanline fill, sampling pixel centres. poly in mm, s = px per mm."""
    H, W = lab.shape
    p = np.asarray(poly, np.float64)
    ymin, ymax = p[:, 1].min(), p[:, 1].max()
    j0, j1 = max(0, math.ceil(ymin * s - 0.5)), min(H, math.ceil(ymax * s - 0.5))
    if j1 <= j0:
        return
    xmin, xmax = p[:, 0].min(), p[:, 0].max()
    i0, i1 = max(0, math.ceil(xmin * s - 0.5)), min(W, math.ceil(xmax * s - 0.5))
    if i1 <= i0:
        return
    a, b = p, np.roll(p, -1, axis=0)
    keep = a[:, 1] != b[:, 1]
    a, b = a[keep], b[keep]
    yc = (np.arange(j0, j1) + 0.5) / s
    lo, hi = np.minimum(a[:, 1], b[:, 1]), np.maximum(a[:, 1], b[:, 1])
    cross = (yc[:, None] >= lo[None]) & (yc[:, None] < hi[None])
    t = (yc[:, None] - a[None, :, 1]) / (b[None, :, 1] - a[None, :, 1])
    xs = np.where(cross, a[None, :, 0] + t * (b[None, :, 0] - a[None, :, 0]), np.inf)
    xs.sort(axis=1)
    n = xs.shape[1] // 2 * 2
    xl, xr = xs[:, 0:n:2], xs[:, 1:n:2]
    ok = np.isfinite(xl) & np.isfinite(xr)
    pl = np.clip(np.ceil(xl * s - 0.5), i0, i1).astype(np.int64)
    pr = np.clip(np.ceil(xr * s - 0.5), i0, i1).astype(np.int64)
    rows = np.broadcast_to(np.arange(j1 - j0)[:, None], pl.shape)
    diff = np.zeros((j1 - j0, i1 - i0 + 1), np.int32)
    np.add.at(diff, (rows[ok], pl[ok] - i0), 1)
    np.add.at(diff, (rows[ok], pr[ok] - i0), -1)
    inside = np.cumsum(diff, axis=1)[:, :-1] % 2 == 1
    region = lab[j0:j1, i0:i1]
    if value is None:          # overlap counter mode
        region[inside] += 1
    else:
        region[inside] = value


def rasterise(shapes, W, H, wrap=True, count=False):
    """Label image at W x H for the whole tile. wrap=True draws every source polygon
    at the 9 offsets (-750/0/+750, -1125/0/+1125)."""
    s = W / TW
    assert abs(H / TH - s) < 1e-9
    lab = np.zeros((H, W), np.uint8)
    for sh in shapes:
        polys = [outline(sh.cols)] if wrap else [outline(r) for r in clipped_runs(sh)]
        for poly in polys:
            for dx, dy in (OFFSETS if wrap else [(0.0, 0.0)]):
                pp = [(x + dx, y + dy) for x, y in poly]
                xs, ys = [v[0] for v in pp], [v[1] for v in pp]
                if max(xs) <= 0 or min(xs) >= TW or max(ys) <= 0 or min(ys) >= TH:
                    continue
                fill_polygon(lab, pp, s, None if count else LABEL[sh.ink])
    return lab


def hexc(h):
    return np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float64) / 255


PAL = np.stack([hexc(HEX[n]) for n in INKS])          # sRGB 0-1, per label
LUM = PAL @ np.array([0.2126, 0.7152, 0.0722])
ENC_R = np.clip((0.92 - LUM) / 0.35, 0, 1)            # game formula, per label
ENC_G = np.clip((LUM - 0.90) / 0.06, 0, 1)


def box_down(a, f):
    h, w = a.shape[0] // f, a.shape[1] // f
    return a.reshape(h, f, w, f, *a.shape[2:]).mean(axis=(1, 3))


# ------------------------------------------------------------------ outputs
def fmt(v):
    s = f"{q(v):.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def write_svg(shapes, path):
    groups = {n: [] for n in INKS[1:]}
    for sh in shapes:
        for ri, run in enumerate(clipped_runs(sh)):
            pid = f"{sh.name}-{ri}" if ri else sh.name
            if len(run) == 1:
                x0, x1, y0, y1 = run[0]
                groups[sh.ink].append(
                    f'<rect id="{pid}" x="{fmt(x0)}" y="{fmt(y0)}" width="{fmt(x1 - x0)}" height="{fmt(y1 - y0)}"/>')
            else:
                pts = " ".join(f"{fmt(x)},{fmt(y)}" for x, y in outline(run))
                groups[sh.ink].append(f'<polygon id="{pid}" points="{pts}"/>')
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 750 1125" width="750mm" height="1125mm">',
             f'<title>FrontRooms wallpaper, stepped grid (one 750 x 1125 mm roll repeat)</title>',
             f'<rect id="ground" x="0" y="0" width="750" height="1125" fill="{HEX["ground"]}"/>']
    for ink in INKS[1:]:
        lines.append(f'<g id="ink-{ink}" fill="{HEX[ink]}">')
        lines += ["  " + e for e in groups[ink]]
        lines.append("</g>")
    lines.append("</svg>")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    return sum(len(v) for v in groups.values())


def encode_frame(shapes):
    lab = rasterise(shapes, FW * SS, FH * SS)
    r = box_down(ENC_R[lab].astype(np.float32), SS)
    g = box_down(ENC_G[lab].astype(np.float32), SS)
    return np.stack([r, g, np.zeros_like(r)], -1), lab


def save_rgba(path, f):
    a = np.concatenate([f, np.ones_like(f[..., :1])], -1)
    Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(path)


def preview_palette(shapes, path):
    W, H = 750, 1125                                  # 1 px = 1 mm
    lab = rasterise(shapes, W * SS, H * SS)
    rgb = box_down(PAL[lab].astype(np.float32), SS)
    # cross-check: the SVG's clipped polygons rasterise to the same picture
    lab2 = rasterise(shapes, W * SS, H * SS, wrap=False)
    assert np.array_equal(lab, lab2), "SVG geometry and wrapped raster disagree"
    cnt = rasterise(shapes, W * SS, H * SS, count=True)
    assert cnt.max() <= 1, "shapes overlap"
    tile = np.tile(rgb, (2, 2, 1))
    Image.fromarray((np.clip(tile, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB").save(path)
    cov = np.bincount(lab.ravel(), minlength=len(INKS)) / lab.size
    return dict(zip(INKS, cov.round(4).tolist()))


def distance_strip(frame, path, shade):
    tan = math.tan(math.radians(38))
    tiled = np.tile(frame, (1, 4, 1))                 # 4 tiles wide = 3.0 m x 1.125 m
    rows, labels = [], []
    target_w = None
    for d in (2, 6, 13):
        ppm = 1080 / (2 * d * tan)
        w, h = max(1, round(3.0 * ppm)), max(1, round(1.125 * ppm))
        chans = [np.asarray(Image.fromarray(tiled[..., c].astype(np.float32), "F").resize((w, h), Image.BOX))
                 for c in range(3)]
        small = shade(np.clip(np.stack(chans, -1), 0, 1))
        im = Image.fromarray((np.clip(small, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")
        if target_w is None:
            target_w = w
        k = max(1, round(target_w / w))
        rows.append(im.resize((w * k, h * k), Image.NEAREST))
        labels.append(f"{d} m  ({ppm:.0f} px/m at 1080p, 76 deg vFOV; {1000 / ppm:.1f} mm/px; nearest x{k})")
    W = max(r.width for r in rows)
    H = sum(r.height + 24 for r in rows)
    out = Image.new("RGB", (W, H), (24, 24, 24))
    dr = ImageDraw.Draw(out)
    y = 0
    for r, t in zip(rows, labels):
        dr.text((6, y + 6), t, fill=(235, 235, 235))
        out.paste(r, (0, y + 24))
        y += r.height + 24
    out.save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    sys.dont_write_bytecode = True        # write nothing outside patterns/
    sys.path.insert(0, PRINT_DIR)
    import print_tool

    shapes = build_shapes()
    n = write_svg(shapes, os.path.join(OUT, KEY + ".svg"))
    frame, _ = encode_frame(shapes)
    k00 = os.path.join(OUT, "K00.png")
    save_rgba(k00, frame)
    cov = preview_palette(shapes, os.path.join(OUT, "preview_palette.png"))

    tmp = tempfile.mkdtemp(prefix=KEY + "_")
    try:
        shutil.copy(k00, os.path.join(tmp, "K00.png"))
        subprocess.run([sys.executable, PRINT_TOOL, "preview", tmp, os.path.join(OUT, "preview_lobby.png")], check=True)
        val = subprocess.run([sys.executable, PRINT_TOOL, "validate", tmp], capture_output=True, text=True)
        print(val.stdout.strip())
        print("validate:", "PASS" if val.returncode == 0 else "FAIL")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    saved = np.asarray(Image.open(k00), np.float32) / 255
    distance_strip(saved[..., :3], os.path.join(OUT, "distance.png"), print_tool.shade)

    orig = np.asarray(Image.open(ORIGINAL), np.float32) / 255
    print(f"svg elements: {n}")
    print("coverage:", cov)
    print(f"K00 mean R {saved[..., 0].mean():.4f}  G {saved[..., 1].mean():.4f}")
    print(f"original mean R {orig[..., 0].mean():.4f}  G {orig[..., 1].mean():.4f}")


if __name__ == "__main__":
    main()
