"""FrontRooms glow-ink content: the close-up substance of the phosphor underprint.

The ink's SHAPES (chevrons, bars) are procedural in the shader (InkShape). This tool
makes only what the shapes are filled with, read up close:

  _FR_InkType       sign type per message, in each glyph's own frame
  _FR_InkSubstance  the ground substance per run tier, in the print's roll tile

Values (linear, single channel): 1.0 = solid phosphor field, about 0.55 = knocked-out
type, so a stroke reads solid from range (mean >= 0.6 in any 100 mm square) and the
words only resolve within about 1.5 m. The substance layers carry a second channel (G)
for rare overlays (scratch-throughs, figures) that the shader gates per cell by hash.

Glyph frames (metres, produced by InkShape; layer UV = frame / 0.75, 1.365 px/mm):
  chevron arms (FLOW, pressure, forged)  u = along the arm from the apex, reading
                                         never upside down; v = across the arm from
                                         its centreline (stroke 100 mm)
  vertical bars (HERE, BREACH, pressure door)  u = from the bar's left edge (0-0.1),
                                         v = height above the floor
  horizontal bars (STOP)                 u = from the bar's left edge (0-0.6),
                                         v = from the bar's bottom edge (0-0.12)

Commands (use /usr/bin/python3, which has numpy + Pillow):
  build <spec.json> <out_dir>     render every layer, pack both arrays, write a preview
The spec holds the strings; the narrative chat owns them (30_narrative_phosphor.md).
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE_DIR = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE_DIR, "..", "..", "Assets", "Fonts", "Period1990", "TeXGyre")
FACE = {"bold": "texgyreheros-bold.otf", "cn": "texgyreheroscn-bold.otf"}
PX_PER_MM = 1024 / 750.0                      # same density as the print
TYPE_PX = 1024                                # one type layer = 0.75 x 0.75 m
SUB_W, SUB_H = 768, 1152                      # one substance layer = one 0.75 x 1.125 m roll tile
SUB_PX_PER_MM = SUB_W / 750.0
FIELD, KNOCK = 1.0, 0.55
CAP_RATIO = 0.717                             # Heros cap height / em
SS = 4                                        # supersampling for the type raster


def font(face, cap_mm, px_per_mm):
    return ImageFont.truetype(os.path.join(FONTS, FACE[face]), int(round(cap_mm * px_per_mm * SS / CAP_RATIO)))


def text_size(f, s):
    l, t, r, b = f.getbbox(s)
    return r - l, b - t, l, t


def draw_word(dr, f, s, cx, cy, jitter=None, rng=None):
    """Centres s on (cx, cy) in supersampled px. jitter imitates a hand copy."""
    if not jitter:
        w, h, l, t = text_size(f, s)
        dr.text((cx - w / 2 - l, cy - h / 2 - t), s, font=f, fill=0)
        return
    # hand-drawn imitation: one glyph at a time, rotated, scaled and shifted
    w, h, l, t = text_size(f, s)
    x = cx - w / 2
    reversed_one = False
    for ch in s:
        gw, gh, gl, gt = text_size(f, ch if ch != " " else "n")
        if ch != " ":
            tile = Image.new("L", (int(gw * 1.8) + 8, int(gh * 1.8) + 8), 255)
            td = ImageDraw.Draw(tile)
            td.text((tile.width / 2 - gw / 2 - gl, tile.height / 2 - gh / 2 - gt), ch, font=f, fill=0)
            if ch == "S" and not reversed_one and jitter.get("reverse_one_S"):
                tile = tile.transpose(Image.FLIP_LEFT_RIGHT)
                reversed_one = True
            sc = 1 + rng.uniform(-jitter["scale"], jitter["scale"])
            tile = tile.resize((max(1, int(tile.width * sc)), max(1, int(tile.height * sc))), Image.BICUBIC)
            tile = tile.rotate(rng.uniform(-jitter["rot_deg"], jitter["rot_deg"]), Image.BICUBIC, fillcolor=255)
            dy = rng.uniform(-jitter["baseline_mm"], jitter["baseline_mm"]) * PX_PER_MM * SS
            dr._image.paste(0, (int(x + gw / 2 - tile.width / 2), int(cy - tile.height / 2 + dy)),
                            Image.eval(tile, lambda p: 255 - p))
        x += f.getlength(ch) * (1 + rng.uniform(-0.04, 0.06))


def wrap_draw(img, fn):
    """Draw with x/y offsets of -1/0/+1 tile so content wraps seamlessly."""
    W, H = img.size
    dr = ImageDraw.Draw(img)
    for ox in (-W, 0, W):
        for oy in (-H, 0, H):
            fn(dr, ox, oy)


def finish(mask_ss, size):
    """mask_ss: supersampled L image, 0 = type, 255 = field -> float field/knock values."""
    m = np.asarray(mask_ss.resize(size, Image.BOX), np.float32) / 255.0
    return KNOCK + (FIELD - KNOCK) * m


def type_layer(spec, rng):
    """One _FR_InkType layer. Kinds: 'rows' (text along u, rows across v, centred on
    v = 0, for chevron arms) and 'stack' (lines centred in a bar of width bar_mm,
    repeating up v, for vertical bars) and 'lockup' (a block of lines repeated along u
    inside a horizontal bar of height bar_h_mm)."""
    N = TYPE_PX * SS
    img = Image.new("L", (N, N), 255)
    f = font(spec.get("face", "bold"), spec["cap_mm"], PX_PER_MM)
    mm = PX_PER_MM * SS
    jit = spec.get("jitter")
    kind = spec["kind"]
    if kind == "rows":
        text = spec["text"]
        w, _, _, _ = text_size(f, text)
        gap = spec.get("gap_mm", 18) * mm
        n = max(1, int(N // (w + gap)))
        period = N / n
        rows = max(1, round(750 / spec["row_pitch_mm"]))
        pitch = N / rows

        def fn(dr, ox, oy):
            for r in range(rows):
                # v = 0 is the stroke centre line: put row 0 there (image y = 0)
                cy = r * pitch + oy
                shift = (period / 2) * (r % 2)
                for k in range(n):
                    draw_word(dr, f, text, k * period + shift + period / 2 + ox, cy, jit, rng)
        wrap_draw(img, fn)
    elif kind == "stack":
        lines = spec["lines"]
        cx = spec["bar_mm"] / 2 * mm
        pitch = spec["line_pitch_mm"] * mm
        reps = max(1, int(round(N / (pitch * len(lines)))))
        pitch = N / (reps * len(lines))

        def fn(dr, ox, oy):
            for i in range(reps * len(lines)):
                draw_word(dr, f, lines[i % len(lines)], cx + ox, i * pitch + pitch / 2 + oy, jit, rng)
        wrap_draw(img, fn)
    elif kind == "lockup":
        lines = spec["lines"]
        bar_h = spec["bar_h_mm"] * mm
        lp = spec["line_pitch_mm"] * mm
        each = spec["every_mm"] * mm
        n = max(1, int(round(N / each)))
        each = N / n
        # v runs up from the bar's bottom edge, and image rows run down from the top
        # (Unity puts v = 0 at the bottom of an imported PNG), so the block sits at
        # the bottom of the image, centred bar_h / 2 above it; lines read top to bottom.
        y0 = N - bar_h / 2 - lp * (len(lines) - 1) / 2

        def fn(dr, ox, oy):
            for k in range(n):
                for j, s in enumerate(lines):
                    draw_word(dr, f, s, k * each + each / 2 + ox, y0 + j * lp + oy, jit, rng)
        wrap_draw(img, fn)
    else:
        raise ValueError(kind)
    return finish(img, (TYPE_PX, TYPE_PX))


def substance_layer(spec, rng):
    """One _FR_InkSubstance layer (one roll tile): R = ground field with register marks
    and the roll stamp; G = rare overlay (gated per cell by the shader)."""
    W, H = SUB_W * SS, SUB_H * SS
    mm = SUB_PX_PER_MM * SS
    ground = Image.new("L", (W, H), 255)
    f = font(spec.get("stamp_face", "cn"), spec["stamp_cap_mm"], SUB_PX_PER_MM)
    y_stamp = H - spec["stamp_height_m"] * 1000 * mm % H    # v measured up from the floor

    def fn(dr, ox, oy):
        draw_word(dr, f, spec["stamp"], W / 2 + ox, y_stamp + oy)
        # register crosshairs either side of the stamp
        for sx in (spec["register_inset_mm"] * mm, W - spec["register_inset_mm"] * mm):
            r = 7 * mm
            lw = int(2.6 * mm)
            dr.ellipse((sx - r + ox, y_stamp - r + oy, sx + r + ox, y_stamp + r + oy), outline=0, width=lw)
            dr.line((sx - 1.6 * r + ox, y_stamp + oy, sx + 1.6 * r + ox, y_stamp + oy), fill=0, width=lw)
            dr.line((sx + ox, y_stamp - 1.6 * r + oy, sx + ox, y_stamp + 1.6 * r + oy), fill=0, width=lw)
    wrap_draw(ground, fn)
    R = finish(ground, (SUB_W, SUB_H)) * spec.get("ground_level", 0.8)
    G = np.zeros_like(R)
    if spec.get("overlay"):
        ov = Image.new("L", (W, H), 255)
        fh = font("cn", spec["overlay"]["cap_mm"], SUB_PX_PER_MM)
        jit = {"scale": 0.12, "rot_deg": 9, "baseline_mm": 2.5}

        def fo(dr, ox, oy):
            for item in spec["overlay"]["items"]:
                x, y = item["x_mm"] * mm, H - item["height_m"] * 1000 * mm % H
                if item.get("tally"):
                    for k in range(item["tally"]):
                        xx = x + k * 9 * mm + rng.uniform(-1, 1) * mm
                        dr.line((xx + ox, y - 30 * mm + oy, xx + 3 * mm + ox, y + oy), fill=0, width=int(2.6 * mm))
                    if item["tally"] >= 5:
                        dr.line((x - 4 * mm + ox, y - 8 * mm + oy, x + item["tally"] * 9 * mm + ox, y - 24 * mm + oy), fill=0, width=int(2.6 * mm))
                else:
                    draw_word(dr, fh, item["text"], x + ox, y + oy, jit, rng)
        wrap_draw(ov, fo)
        G = 1.0 - np.asarray(ov.resize((SUB_W, SUB_H), Image.BOX), np.float32) / 255.0
    return R, G


def pack(layers, cols):
    n = len(layers)
    cols = min(cols, n)
    rows = (n + cols - 1) // cols
    h, w = layers[0].shape[:2]
    sheet = np.zeros((rows * h, cols * w) + layers[0].shape[2:], np.float32)
    for i, L in enumerate(layers):
        r, c = divmod(i, cols)
        sheet[r * h:(r + 1) * h, c * w:(c + 1) * w] = L
    return sheet, cols, rows


def save_l(path, a):
    Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8), "L").save(path)


def build(spec_path, out):
    spec = json.load(open(spec_path))
    os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(spec.get("seed", 1990))
    report = {"type": [], "substance": []}
    # ---- _FR_InkType: 16 layers (unused layers = solid field)
    types = [np.full((TYPE_PX, TYPE_PX), FIELD, np.float32) for _ in range(16)]
    for L in spec["type_layers"]:
        types[L["index"]] = type_layer(L, rng)
        a = types[L["index"]]
        report["type"].append({"index": L["index"], "name": L["name"], "mean": round(float(a.mean()), 3),
                               "min_100mm_mean": round(float(min_window_mean(a, 100 * PX_PER_MM)), 3)})
    sheet, cols, rows = pack(types, 4)
    save_l(os.path.join(out, "FR_InkType.png"), sheet)
    json.dump({"columns": cols, "rows": rows, "slices": 16, "sliceWidth": TYPE_PX, "sliceHeight": TYPE_PX,
               "frameMetres": 0.75, "encoding": "R ink field 1.0 / type 0.55, linear"},
              open(os.path.join(out, "FR_InkType.print.json"), "w"), indent=2)
    # ---- _FR_InkSubstance: one layer per run tier (RG)
    subs = []
    for S in spec["substance_layers"]:
        R, G = substance_layer(S, rng)
        subs.append(np.stack([R, G, np.zeros_like(R)], -1))
        report["substance"].append({"tier": S["tier"], "ground_mean": round(float(R.mean()), 3),
                                    "overlay_cover": round(float((G > 0.5).mean()), 4)})
    ssheet, scols, srows = pack(subs, 5)
    Image.fromarray((np.clip(ssheet, 0, 1) * 255 + .5).astype(np.uint8), "RGB").save(os.path.join(out, "FR_InkSubstance.png"))
    json.dump({"columns": scols, "rows": srows, "slices": len(subs), "sliceWidth": SUB_W, "sliceHeight": SUB_H,
               "tileMetres": [0.75, 1.125], "encoding": "R ground substance, G rare overlay (gate per cell), linear"},
              open(os.path.join(out, "FR_InkSubstance.print.json"), "w"), indent=2)
    preview(types, spec, subs, os.path.join(out, "ink_preview.png"))
    json.dump(report, open(os.path.join(out, "ink_report.json"), "w"), indent=2)
    print(json.dumps(report, indent=1))


def min_window_mean(a, win):
    """Smallest mean over any win x win square (the >= 0.6 stroke-fill rule)."""
    k = int(round(win))
    c = np.cumsum(np.cumsum(np.pad(a, ((1, 0), (1, 0))), 0), 1)
    s = c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]
    return (s / (k * k)).min()


def preview(types, spec, subs, path):
    """Glow-green rendering: each used type layer, and each tier's ground substance."""
    green = np.array([0.55, 1.0, 0.45], np.float32)
    used = [L["index"] for L in spec["type_layers"]]
    cell = 300
    tiles = []
    for i in used:
        g = np.asarray(Image.fromarray((types[i] * 255).astype(np.uint8)).resize((cell, cell), Image.BOX), np.float32) / 255
        tiles.append((g[..., None] * green * 255).astype(np.uint8))
    for s in subs:
        g = s[..., 0] / max(s[..., 0].max(), 1e-3) * 0.85 + s[..., 1] * 0.3
        g = np.asarray(Image.fromarray((np.clip(g, 0, 1) * 255).astype(np.uint8)).resize((cell, int(cell * 1.5)), Image.BOX), np.float32) / 255
        tiles.append((g[..., None] * green * 255).astype(np.uint8))
    cols = 5
    rows = (len(tiles) + cols - 1) // cols
    H = int(cell * 1.5) + 24
    img = Image.new("RGB", (cols * (cell + 12), rows * H), (12, 14, 12))
    dr = ImageDraw.Draw(img)
    names = [f"type {i}: {next(L['name'] for L in spec['type_layers'] if L['index'] == i)}" for i in used] + \
            [f"substance tier {S['tier']}" for S in spec["substance_layers"]]
    for k, (t, nm) in enumerate(zip(tiles, names)):
        r, c = divmod(k, cols)
        img.paste(Image.fromarray(t), (c * (cell + 12), r * H + 22))
        dr.text((c * (cell + 12) + 4, r * H + 4), nm, fill=(220, 230, 220))
    img.save(path)


if __name__ == "__main__":
    if len(sys.argv) < 4 or sys.argv[1] != "build":
        sys.exit(__doc__)
    build(sys.argv[2], sys.argv[3])
