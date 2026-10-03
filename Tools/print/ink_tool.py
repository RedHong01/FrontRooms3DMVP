"""FrontRooms glow-ink content: the close-up substance of the phosphor underprint.

The ink's SHAPES (chevrons, bars) are procedural in the shader (InkShape). This tool
renders only what the shapes are filled with, read up close, from the narrative
chat's frozen content spec (30_narrative_phosphor.md A.11, a JSON block):

  _FR_InkType       16 layers, 1024 x 1024 = one 0.75 x 0.75 m tile each,
                    sampled with an UNMIRRORED face u (text reads left to right)
                    and v = height above the floor
  _FR_InkSubstance  one layer per run tier, 768 x 1152 = one 0.75 x 1.125 m roll
                    tile, sampled with the (warped) print UV

Type layers (0-8): field 1.0, type knocked out to 0.55, so a stroke reads solid from
range and the words resolve only within about 1.5 m. Layer 9 (scratches) is the
opposite: background 0, marks 1.0, composited in the shader as max(substance, mark).
Substance: field 0.7, marks 0.4. Everything tiles seamlessly.

Run with a Python that has numpy + Pillow (/usr/bin/python3 on this Mac):
  build <spec.json> <out_dir>      render, pack both arrays, write report + preview
The spec file is the A.11 JSON block saved as-is (see ink/egress_v1.json).
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE_DIR = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE_DIR, "..", "..", "Assets", "Fonts", "Period1990")
TILE_MM = 750.0
TYPE_PX = 1024
PX_MM = TYPE_PX / TILE_MM                     # 1.3653 px/mm, the same density as the print
SUB_W, SUB_H = 768, 1152                      # one roll tile, 750 x 1125 mm
SUB_PX_MM = SUB_W / TILE_MM
SS = 4                                        # supersampling
CAP_RATIO = 0.717                             # TeX Gyre Heros cap height / em


# ---------------------------------------------------------------- canvas helpers
class Canvas:
    """A supersampled single-channel tile that wraps: anything drawn across an edge
    reappears on the opposite edge, so the tile is seamless."""

    def __init__(self, w_mm, h_mm, px_mm, bg):
        self.s = px_mm * SS                    # supersampled px per mm
        self.W, self.H = int(round(w_mm * px_mm)) * SS, int(round(h_mm * px_mm)) * SS
        self.img = Image.new("L", (self.W, self.H), bg)
        self.dr = ImageDraw.Draw(self.img)

    def offsets(self, bbox):
        x0, y0, x1, y1 = bbox
        xs = [0] + ([self.W] if x0 < 0 else []) + ([-self.W] if x1 > self.W else [])
        ys = [0] + ([self.H] if y0 < 0 else []) + ([-self.H] if y1 > self.H else [])
        return [(ox, oy) for ox in xs for oy in ys]

    def paste_mask(self, mask, x, y, value):
        """mask: L image (255 = mark). Paints `value` where the mask is set, wrapped."""
        x, y = x % self.W, y % self.H
        for ox, oy in self.offsets((x, y, x + mask.width, y + mask.height)):
            self.img.paste(value, (int(round(x + ox)), int(round(y + oy))), mask)

    def result(self, out_w, out_h):
        return np.asarray(self.img.resize((out_w, out_h), Image.BOX), np.float32) / 255.0


def font(name, cap_mm, s):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), max(4, int(round(cap_mm * s / CAP_RATIO))))


def glyph_run_mask(f, text, tracking_px):
    """Set `text` one character at a time with extra tracking. Returns an L mask
    (255 = ink), its advance, and the y of the cap line and baseline inside it."""
    return glyph_run_mask_spaced(f, text, tracking_px, 0.0)


def glyph_run_mask_spaced(f, text, tracking_px, word_px):
    """As glyph_run_mask, with `word_px` added to every space (word spacing)."""
    adv = [f.getlength(ch) + tracking_px + (word_px if ch == " " else 0.0) for ch in text]
    asc, desc = f.getmetrics()
    # wide enough for the last glyph even when tracking is negative
    m = Image.new("L", (int(math.ceil(sum(adv) + f.size)) + 4, asc + desc + 4), 0)
    d = ImageDraw.Draw(m)
    x = 0.0
    for ch, a in zip(text, adv):
        d.text((x, 0), ch, font=f, fill=255)
        x += a
    hb = f.getbbox("H")
    return m, sum(adv), hb[1], hb[3]


# ---------------------------------------------------------------- monoline hand
# Single-stroke capitals and digits in a 1-unit cap box (y up), for the forged
# layer's marker lettering and the scratch cluster: (strokes, advance width).
def _ellipse(cx, cy, rx, ry, n=20):
    return [(cx + rx * math.cos(2 * math.pi * k / n), cy + ry * math.sin(2 * math.pi * k / n)) for k in range(n + 1)]


_S = [(0.6, 0.88), (0.46, 0.99), (0.24, 1.0), (0.06, 0.9), (0.03, 0.72), (0.14, 0.58), (0.46, 0.46),
      (0.6, 0.32), (0.6, 0.14), (0.44, 0.01), (0.2, 0.0), (0.02, 0.12)]
_SIX = [(0.52, 0.95), (0.32, 1.0), (0.12, 0.88), (0.02, 0.6), (0.02, 0.3), (0.12, 0.08), (0.3, 0.0),
        (0.48, 0.06), (0.56, 0.22), (0.52, 0.42), (0.32, 0.52), (0.12, 0.45), (0.03, 0.32)]
HAND = {
    "A": ([[(0, 0), (0.35, 1), (0.7, 0)], [(0.14, 0.4), (0.56, 0.4)]], 0.7),
    "C": ([[(0.62, 0.82), (0.5, 0.97), (0.32, 1.0), (0.12, 0.9), (0.02, 0.68), (0.02, 0.32), (0.12, 0.1),
            (0.32, 0.0), (0.5, 0.03), (0.62, 0.18)]], 0.65),
    "D": ([[(0, 0), (0, 1), (0.3, 1), (0.52, 0.9), (0.64, 0.68), (0.64, 0.32), (0.52, 0.1), (0.3, 0), (0, 0)]], 0.66),
    "E": ([[(0.6, 1), (0, 1), (0, 0), (0.6, 0)], [(0, 0.52), (0.48, 0.52)]], 0.6),
    "G": ([[(0.62, 0.82), (0.5, 0.97), (0.32, 1.0), (0.12, 0.9), (0.02, 0.68), (0.02, 0.32), (0.12, 0.1),
            (0.32, 0.0), (0.52, 0.03), (0.64, 0.15), (0.64, 0.45), (0.38, 0.45)]], 0.66),
    "H": ([[(0, 0), (0, 1)], [(0.62, 0), (0.62, 1)], [(0, 0.52), (0.62, 0.52)]], 0.62),
    "I": ([[(0.08, 0), (0.08, 1)]], 0.16),
    "K": ([[(0, 0), (0, 1)], [(0.6, 1), (0, 0.4)], [(0.18, 0.58), (0.62, 0)]], 0.62),
    "L": ([[(0, 1), (0, 0), (0.55, 0)]], 0.55),
    "M": ([[(0, 0), (0, 1), (0.38, 0.3), (0.76, 1), (0.76, 0)]], 0.76),
    "N": ([[(0, 0), (0, 1), (0.62, 0), (0.62, 1)]], 0.62),
    "O": ([_ellipse(0.36, 0.5, 0.36, 0.5)], 0.72),
    "R": ([[(0, 0), (0, 1), (0.38, 1), (0.56, 0.92), (0.62, 0.76), (0.56, 0.6), (0.38, 0.52), (0, 0.52)],
           [(0.3, 0.52), (0.62, 0)]], 0.62),
    "S": ([_S], 0.62),
    "Ƨ": ([[(0.62 - x, y) for x, y in _S]], 0.62),
    "T": ([[(0, 1), (0.66, 1)], [(0.33, 1), (0.33, 0)]], 0.66),
    "U": ([[(0, 1), (0, 0.3), (0.06, 0.1), (0.2, 0.0), (0.42, 0.0), (0.56, 0.1), (0.62, 0.3), (0.62, 1)]], 0.62),
    "W": ([[(0, 1), (0.2, 0), (0.4, 0.7), (0.6, 0), (0.8, 1)]], 0.8),
    "Y": ([[(0, 1), (0.33, 0.5), (0.66, 1)], [(0.33, 0.5), (0.33, 0)]], 0.66),
    "0": ([_ellipse(0.3, 0.5, 0.3, 0.5)], 0.6),
    "1": ([[(0.08, 0.8), (0.3, 1), (0.3, 0)]], 0.4),
    "4": ([[(0.45, 0), (0.45, 1), (0, 0.3), (0.62, 0.3)]], 0.62),
    "6": ([_SIX], 0.58),
    "9": ([[(0.58 - x, 1 - y) for x, y in _SIX]], 0.58),
    ".": ([[(0.05, 0.0), (0.08, 0.03)]], 0.2),
    "/": ([[(0, 0), (0.4, 1)]], 0.42),
    "·": ([[(0.1, 0.48), (0.13, 0.51)]], 0.26),
    " ": ([], 0.38),
}
HAND_GAP = 0.18                               # extra space between hand glyphs, in caps


def hand_line(text, cap_px, stroke_px_range, rng, rot_deg, baseline_px, scale, spacing_px, ragged=False):
    """A hand-lettered line as an L mask (255 = ink). Every glyph gets its own size,
    rotation, baseline and gap. Returns (mask, advance, pad); the cap line is at y = pad."""
    pad = int(cap_px * 0.8 + baseline_px * 2 + 8)
    items, x = [], 0.0
    for ch in text:
        strokes, w = HAND[ch]
        sc = cap_px * (1 + rng.uniform(-scale, scale))
        items.append((strokes, x, sc, math.radians(rng.uniform(-rot_deg, rot_deg)),
                      rng.uniform(-baseline_px, baseline_px), rng.uniform(*stroke_px_range)))
        x += w * sc + cap_px * HAND_GAP + rng.uniform(-spacing_px, spacing_px)
    m = Image.new("L", (int(math.ceil(x)) + 2 * pad, int(cap_px + 2 * pad)), 0)
    d = ImageDraw.Draw(m)
    for strokes, gx, sc, rot, dy, sw in items:
        cx, cy = 0.35, 0.5
        for st in strokes:
            pts = []
            for px_, py_ in st:
                X, Y = (px_ - cx) * sc, (py_ - cy) * sc
                X, Y = X * math.cos(rot) - Y * math.sin(rot), X * math.sin(rot) + Y * math.cos(rot)
                pts.append((pad + gx + cx * sc + X, pad + cap_px - (cy * sc + Y) + dy))
            if ragged and len(pts) >= 2:          # scratched: ends overshoot or stop short
                for end in (0, -1):
                    a, b = (pts[0], pts[1]) if end == 0 else (pts[-1], pts[-2])
                    k = rng.uniform(-0.05, 0.12) * sc
                    L = math.hypot(a[0] - b[0], a[1] - b[1]) or 1
                    pts[end] = (a[0] + (a[0] - b[0]) / L * k, a[1] + (a[1] - b[1]) / L * k)
            d.line(pts, fill=255, width=max(1, int(round(sw))), joint="curve")
            r = sw / 2
            for p in (pts[0], pts[-1]):
                d.ellipse((p[0] - r, p[1] - r, p[0] + r, p[1] + r), fill=255)
    return m, x, pad


# ---------------------------------------------------------------- layer builders
def fit_cycle(widths_mm, n_chars):
    """Repeat count n and per-character tracking (mm) so that n cycles are exactly
    750 mm, choosing the n that needs the least tracking within -1..+4 mm/char."""
    best = None
    for n in range(1, 16):
        t = (TILE_MM / n - widths_mm) / n_chars
        if -1.0 <= t <= 4.0 and (best is None or abs(t) < abs(best[1])):
            best = (n, t)
    if best is None:                              # nothing in range: closest, flagged in the report
        n = max(1, int(round(TILE_MM / widths_mm)))
        best = (n, (TILE_MM / n - widths_mm) / n_chars)
    return best


def type_lines(L, common, rng):
    """Horizontal layers (and rotated ones, before rotation): lines at a 37.5 mm pitch,
    each repeating `phrase + separator` in a cycle fitted to exactly 750 mm, brick-offset
    by half a phrase from the line above."""
    cv = Canvas(TILE_MM, TILE_MM, PX_MM, 255)
    s = cv.s
    pitch = common["pitch_mm"]
    lines = int(round(TILE_MM / pitch))
    cap = L["cap_mm"]
    cyc = L["phrase"] + common["separator"]
    hand = L.get("hand")
    if hand is None:
        info_fit = {}
        while True:
            f = font(common["font"], cap, s)
            w0 = sum(f.getlength(ch) for ch in cyc) / s
            n, t = fit_cycle(w0, len(cyc))
            word = 0.0
            if t > 4.0:
                # too loose: keep tracking at +4 and open the word spaces (never close them)
                spaces = cyc.count(" ")
                word = (TILE_MM / n - w0 - 4.0 * len(cyc)) / max(1, spaces)
                info_fit = {"tracking_limited_to_mm": 4.0, "word_space_mm": round(word, 2), "cap_mm_used": cap}
                t = 4.0
                break
            if t < -1.0 and cap > L["cap_mm"] - 4:
                cap -= 0.5                        # too tight: a slightly smaller cap height, words keep their spaces
                continue
            info_fit = {"cap_mm_used": cap}
            break
        mask, adv, top, _ = glyph_run_mask_spaced(f, cyc, t * s, word * s)
        period = TILE_MM / n * s
        for k in range(lines):
            y_cap = (k * pitch + (pitch - cap) / 2) * s
            shift = (period / 2) * (k % 2)
            for r in range(n):
                cv.paste_mask(mask, r * period + shift, y_cap - top, 0)
        return cv, {"repeats": n, "tracking_mm": round(t, 2), **info_fit}
    # hand-lettered (forged): drifting pitch, random line offsets, still seamless
    cap_px = cap * s
    n, t = fit_cycle(sum(HAND[ch][1] * cap + cap * HAND_GAP for ch in cyc), len(cyc))
    drift = np.array([rng.uniform(-hand["pitch_drift_mm"], hand["pitch_drift_mm"]) for _ in range(lines)])
    drift -= drift.mean()                         # the pitches still sum to 750 mm
    ys = np.cumsum(np.r_[0.0, pitch + drift[:-1]])
    for k in range(lines):
        segs = [hand_line(cyc, cap_px, [v * s for v in hand["stroke_mm"]], rng, hand["rot_deg"],
                          hand["baseline_mm"] * s, hand["scale"], hand["spacing_mm"] * s) for _ in range(n)]
        total = sum(a for _, a, _ in segs)
        squeeze = TILE_MM * s / total             # land the line's cycle on exactly 750 mm
        x0 = rng.uniform(0, TILE_MM * s)          # random per-line offset (no brick)
        x = 0.0
        for m, adv, pad in segs:
            cv.paste_mask(m, x0 + x - pad, (ys[k] + (pitch - cap) / 2) * s - pad, 0)
            x += adv * squeeze
    return cv, {"repeats": n, "tracking_mm": round(t, 2), "hand": True}


def type_pairs(L, common):
    """STOP: NO over EXIT in 125 x 62.5 mm cells, alternate rows offset half a cell."""
    cv = Canvas(TILE_MM, TILE_MM, PX_MM, 255)
    s = cv.s
    cw, ch = L["cell_mm"]
    mt, at, tt, _ = glyph_run_mask(font(common["font"], L["top"]["cap_mm"], s), L["top"]["text"], 0)
    mb, ab, tb, _ = glyph_run_mask(font(common["font"], L["bottom"]["cap_mm"], s), L["bottom"]["text"], 0)
    pair_h = L["top"]["cap_mm"] + L["gap_mm"] + L["bottom"]["cap_mm"]
    cols, rows = int(round(TILE_MM / cw)), int(round(TILE_MM / ch))
    for r in range(rows):
        for c in range(cols):
            cx = (c * cw + cw / 2 + (cw / 2) * (r % 2)) * s
            y_top = (r * ch + (ch - pair_h) / 2) * s
            cv.paste_mask(mt, cx - at / 2, y_top - tt, 0)
            cv.paste_mask(mb, cx - ab / 2, y_top + (L["top"]["cap_mm"] + L["gap_mm"]) * s - tb, 0)
    return cv, {"pair_mm": pair_h, "cells": [cols, rows], "fits_120mm_bar": ch + pair_h <= 120}


def type_scratch(L, rng):
    """Layer 9: one scratched cluster (background 0, marks 1.0) inside v 0.1-0.9 and
    never across the tile edge. v runs up from the bottom; image rows run down."""
    cv = Canvas(TILE_MM, TILE_MM, PX_MM, 0)
    s = cv.s
    v0, v1 = L["v_range"]
    y_lo = (1 - v1) * TILE_MM                     # top of the allowed band, image mm
    sw = [v * s for v in L["stroke_mm"]]
    placed = []
    plan = [("IT ONLY GOES IN", 34, 60, y_lo + 40), ("SAME ROLL AGAIN", 30, 95, y_lo + 125),
            ("COUNTED 41 DOORS", 28, 70, y_lo + 205), ("R.M. 6/90", 25, 450, y_lo + 290),
            ("D.K. 11/90", 26, 110, y_lo + 365)]
    for text, cap, x, y in plan:
        m, adv, pad = hand_line(text, cap * s, sw, rng, L["rot_deg"], 2.0 * s, 0.07, 2.5 * s, ragged=True)
        m = m.rotate(rng.uniform(-L["rot_deg"], L["rot_deg"]) * 0.5, Image.BICUBIC, expand=True)
        bb = m.getbbox()
        px, py = int(x * s - pad), int(y * s - pad)
        cv.img.paste(255, (px, py), m)
        placed.append([text, round((px + bb[0]) / s), round((py + bb[1]) / s), round((px + bb[2]) / s), round((py + bb[3]) / s)])
    # tally: 4 gates (four uprights crossed by a diagonal) and 3 strokes, 40 mm tall
    tx, ty, h = 470.0, y_lo + 60, 40.0
    x = tx
    for g in range(5):
        n = 4 if g < 4 else 3
        for k in range(n):
            xx = (x + k * 8 + rng.uniform(-1, 1)) * s
            cv.dr.line(((xx, (ty + rng.uniform(-2, 2)) * s), (xx + rng.uniform(-3, 3) * s, (ty + h) * s)),
                       fill=255, width=int(round(rng.uniform(*sw))))
        if g < 4:
            cv.dr.line(((x - 4) * s, (ty + h - 6) * s, (x + 30) * s, (ty + 6) * s), fill=255, width=int(round(rng.uniform(*sw))))
            x += 42
    placed.append(["TALLY 4x5+3", round(tx - 5), round(ty - 3), round(x + 22), round(ty + h + 3)])
    return cv, {"items_bbox_mm": placed, "allowed_image_y_mm": [round(y_lo), round((1 - v0) * TILE_MM)]}


def substance(T, sub, common):
    cv = Canvas(sub["tile_mm"][0], sub["tile_mm"][1], SUB_PX_MM, 255)
    s = cv.s
    lw = int(round(2.5 * s))
    for reg in sub["register"]:
        x, y = reg["xy_mm"]
        r = 8 * s
        cv.dr.ellipse((x * s - r, y * s - r, x * s + r, y * s + r), outline=0, width=lw)
        cv.dr.line((x * s - 15 * s, y * s, x * s + 15 * s, y * s), fill=0, width=lw)
        cv.dr.line((x * s, y * s - 15 * s, x * s, y * s + 15 * s), fill=0, width=lw)
    st = sub["stamp"]
    f = font(common["font"], st["cap_mm"], s)
    ends = []
    for line, base in zip(T["lines"], st["baselines_mm"]):
        m, adv, top, bot = glyph_run_mask(f, line, st["tracking_mm"] * s)
        cv.img.paste(0, (int(st["x_mm"] * s), int(base * s - bot)), m)
        ends.append(round(st["x_mm"] + adv / s, 1))
    a = cv.result(SUB_W, SUB_H)                   # 1 = field, 0 = mark
    return sub["marks"] + (sub["field"] - sub["marks"]) * a, {"stamp_right_edge_mm": ends,
                                                              "stamp_fits": max(ends) <= sub["tile_mm"][0] - 20}


def min_window_mean(a, win_px):
    k = int(round(win_px))
    c = np.cumsum(np.cumsum(np.pad(a.astype(np.float64), ((1, 0), (1, 0))), 0), 1)
    sm = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    return float((sm / (k * k)).min())


def seam_ratio(a):
    col = np.abs(np.diff(a, axis=1)).mean(0)
    row = np.abs(np.diff(a, axis=0)).mean(1)
    return (float(np.abs(a[:, 0] - a[:, -1]).mean() / (np.percentile(col, 90) + 1 / 255)),
            float(np.abs(a[0, :] - a[-1, :]).mean() / (np.percentile(row, 90) + 1 / 255)))


# ---------------------------------------------------------------- build
def save_l(path, a):
    Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8), "L").save(path)


def build(spec_path, out):
    spec = json.load(open(spec_path))
    common = spec["type_common"]
    common.setdefault("font", "TeXGyre/texgyreheros-bold.otf")
    os.makedirs(out, exist_ok=True)
    layers = [np.ones((TYPE_PX, TYPE_PX), np.float32) for _ in range(16)]
    report = {"spec": spec.get("spec"), "type": [], "substance": []}
    for L in spec["ink_type"]:
        o = L["orient"]
        if o in ("horizontal", "rotated"):
            cv, info = type_lines(L, common, np.random.default_rng(L.get("hand", {}).get("seed", 1990)))
            a = cv.result(TYPE_PX, TYPE_PX)
            if o == "rotated":                    # 90 deg clockwise: reads top to bottom
                a = np.rot90(a, k=-1).copy()
        elif o == "pairs":
            cv, info = type_pairs(L, common)
            a = cv.result(TYPE_PX, TYPE_PX)
        elif o == "cluster":
            cv, info = type_scratch(L, np.random.default_rng(1990))
            a = cv.result(TYPE_PX, TYPE_PX)
        else:
            raise ValueError(o)
        if o != "cluster":
            a = common["knockout"] + (common["field"] - common["knockout"]) * a
        layers[L["layer"]] = a
        entry = {"layer": L["layer"], "mark": L["mark"], "orient": o, **info, "mean": round(float(a.mean()), 3),
                 "seam_xy": [round(v, 2) for v in seam_ratio(a)]}
        if o != "cluster":
            entry["min_mean_100mm"] = round(min_window_mean(a, 100 * PX_MM), 3)
        report["type"].append(entry)
    sheet = np.zeros((4 * TYPE_PX, 4 * TYPE_PX), np.float32)
    for i, a in enumerate(layers):
        r, c = divmod(i, 4)
        sheet[r * TYPE_PX:(r + 1) * TYPE_PX, c * TYPE_PX:(c + 1) * TYPE_PX] = a
    save_l(os.path.join(out, "FR_InkType.png"), sheet)
    json.dump({"columns": 4, "rows": 4, "slices": 16, "sliceWidth": TYPE_PX, "sliceHeight": TYPE_PX,
               "singleChannel": True, "frameMetres": TILE_MM / 1000,
               "encoding": "R: layers 0-8 field 1.0 / type 0.55; layer 9 marks 1.0 on 0; 10-15 unused (1.0); linear"},
              open(os.path.join(out, "FR_InkType.print.json"), "w"), indent=2)
    sub = spec["ink_substance"]
    subs = []
    for T in sub["tiers"]:
        a, info = substance(T, sub, common)
        subs.append(a)
        report["substance"].append({"layer": T["layer"], "ld": T["ld"], **info, "mean": round(float(a.mean()), 3),
                                    "seam_xy": [round(v, 2) for v in seam_ratio(a)]})
    save_l(os.path.join(out, "FR_InkSubstance.png"), np.concatenate(subs, 1))
    json.dump({"columns": len(subs), "rows": 1, "slices": len(subs), "sliceWidth": SUB_W, "sliceHeight": SUB_H,
               "singleChannel": True, "tileMetres": [0.75, 1.125],
               "encoding": "R: field 0.7, marks 0.4; layer = run tier - 1; linear"},
              open(os.path.join(out, "FR_InkSubstance.print.json"), "w"), indent=2)
    json.dump(report, open(os.path.join(out, "ink_report.json"), "w"), indent=2, ensure_ascii=False)
    preview(layers, spec, subs, os.path.join(out, "ink_preview.png"))
    print(json.dumps(report, indent=1, ensure_ascii=False))


def preview(layers, spec, subs, path):
    green = np.array([0.55, 1.0, 0.45], np.float32)
    cell = 320
    tiles, names = [], []
    for L in spec["ink_type"]:
        a = layers[L["layer"]]
        tiles.append(np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((cell, cell), Image.BOX), np.float32) / 255)
        names.append(f"{L['layer']} {L['mark']}")
    for T, a in zip(spec["ink_substance"]["tiers"], subs):
        tiles.append(np.asarray(Image.fromarray((a * 255).astype(np.uint8)).resize((cell, int(cell * 1.5)), Image.BOX), np.float32) / 255)
        names.append(f"substance {T['ld']}")
    cols = 5
    rows = (len(tiles) + cols - 1) // cols
    H = int(cell * 1.5) + 24
    img = Image.new("RGB", (cols * (cell + 12), rows * H), (12, 14, 12))
    dr = ImageDraw.Draw(img)
    for k, (g, nm) in enumerate(zip(tiles, names)):
        r, c = divmod(k, cols)
        img.paste(Image.fromarray((g[..., None] * green * 255).astype(np.uint8)), (c * (cell + 12), r * H + 22))
        dr.text((c * (cell + 12) + 4, r * H + 4), nm, fill=(220, 230, 220))
    img.save(path)


if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[1] != "build":
        sys.exit(__doc__)
    build(sys.argv[2], sys.argv[3])
