"""G10 run 2 sheets. Usage: /usr/bin/python3 sheets2.py <capture dir> <out dir>
Every output is JPEG quality 85. Full frames are copied byte-for-byte (Unity already wrote them at q85)."""
import os, re, sys, shutil
from PIL import Image, ImageDraw, ImageFont

src, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
W, H = 1920, 1080
FONT = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 26)
SMALL = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 19)
BG = (24, 24, 24)

def load(name):
    p = os.path.join(src, name)
    return Image.open(p).convert("RGB") if os.path.exists(p) else None

def label(img, text, font=SMALL):
    d = ImageDraw.Draw(img)
    b = d.textbbox((8, 6), text, font=font)
    d.rectangle((b[0] - 5, b[1] - 3, b[2] + 5, b[3] + 3), fill=(0, 0, 0))
    d.text((8, 6), text, fill=(255, 255, 255), font=font)
    return img

def save(img, name):
    img.save(os.path.join(out, name), "JPEG", quality=85)
    print("wrote", name, img.size)

boxes, last = {}, None
for line in open(os.path.join(src, "g10_frames.txt"), encoding="utf-8"):
    m = re.match(r"^(\S+) \| frame", line)
    if m:
        last = m.group(1); continue
    m = re.search(r"pane box \(bottom-left origin\) (\d+),(\d+) (\d+)x(\d+)", line)
    if m and last:
        x, y, w, h = map(int, m.groups())
        boxes[last] = (x, H - (y + h), x + w, H - y)

def grid(title, rows, cols, tw=640, th=360, name=None):
    """rows: list of (row id, row label); cols: list of (suffix, col label)."""
    gap = 6
    present = [(rid, rl) for rid, rl in rows if any(load(f"{rid}_{s}.jpg") for s, _ in cols)]
    sheet = Image.new("RGB", (len(cols) * tw + (len(cols) - 1) * gap, len(present) * (th + gap) + 48), BG)
    ImageDraw.Draw(sheet).text((10, 10), title, fill=(255, 255, 255), font=FONT)
    for r, (rid, rl) in enumerate(present):
        for c, (suffix, cl) in enumerate(cols):
            im = load(f"{rid}_{suffix}.jpg")
            if im is None: continue
            sheet.paste(label(im.resize((tw, th), Image.LANCZOS), f"{rl} · {cl}"), (c * (tw + gap), 48 + r * (th + gap)))
    save(sheet, name)

ABC = [("A_before", "BEFORE (shipped)"), ("B_glass_sceneambient", "AFTER-glass, scene ambient"), ("C_after", "AFTER (+ ApplyAmbient)")]
ACN = [("A_before", "BEFORE (shipped)"), ("C_after", "AFTER"), ("N_nopane_after", "no pane (AFTER light)")]

grid("G10 · audit frames 01 / 34 / 35 / 37, seed 4242 · BEFORE | AFTER-glass with the scene's ambient | AFTER",
     [("01_rep_L0", "01 Level 0"), ("34_rep_Office", "34 Office"), ("35_rep_Office_b", "35 Office"), ("37_rep_Dark", "37 dead lamp")], ABC,
     name="g10_01_representative.jpg")
grid("G10 · Level 0 window (282,206), seed 4242 · BEFORE | AFTER | no pane",
     [("window_L0_1.5m", "1.5 m (audit 02)"), ("window_L0_oblique50", "~50° (audit 04)"), ("window_L0_0.7m", "0.7 m (audit 05)"), ("window_L0_steep", "61° (audit 06)")], ACN,
     name="g10_02_window_L0.jpg")
grid("G10 · Office window (281,206), seed 4242 · BEFORE | AFTER | no pane",
     [("window_Office_1.5m", "1.5 m (audit 21)"), ("window_Office_oblique50", "~50° (audit 23)"), ("window_Office_0.7m", "0.7 m"), ("window_Office_steep", "61° (audit 25)")], ACN,
     name="g10_03_window_Office.jpg")
grid("G10 · dead lamp · 37: audit frame (no glass in view) · 38: window seen from under a dead lamp · 39: same window from the lit side",
     [("38_deadlamp_window_1.5m", "38 1.5 m"), ("38_deadlamp_window_oblique50", "38 ~50°"), ("39_dark_beyond_window_1.5m", "39 1.5 m")], ACN,
     name="g10_06_deadlamp_windows.jpg")

# 1:1 crops at the pane centre: BEFORE | AFTER | no pane
def crops_1to1(ids, name, cw=600, ch=380):
    gap = 6
    rows = [i for i in ids if i in boxes and load(f"{i}_A_before.jpg")]
    sheet = Image.new("RGB", (3 * cw + 2 * gap, len(rows) * (ch + gap) + 48), BG)
    ImageDraw.Draw(sheet).text((10, 10), "G10 · 1:1 pixel crops at the pane centre · BEFORE | AFTER | no pane", fill=(255, 255, 255), font=FONT)
    for r, i in enumerate(rows):
        x0, y0, x1, y1 = boxes[i]
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        box = (max(0, cx - cw // 2), max(0, cy - ch // 2), max(0, cx - cw // 2) + cw, max(0, cy - ch // 2) + ch)
        for c, (s, cl) in enumerate(ACN):
            sheet.paste(label(load(f"{i}_{s}.jpg").crop(box), f"{i} · {cl} · 1:1"), (c * (cw + gap), 48 + r * (ch + gap)))
    save(sheet, name)

crops_1to1(["window_L0_1.5m", "window_L0_0.7m", "window_Office_1.5m", "window_Office_0.7m"], "g10_04_window_crops_1to1.jpg")

# diagnostics: per view, the pane region (scaled) for N, C, diff x6, VR0, VS0, VG0, VR2, A
DIAG = [("N_nopane_after", "no pane"), ("C_after", "AFTER (as shipped in the clone)"), ("D_diff_x6", "difference AFTER vs no pane, x6"), ("VR2", "_ReflectionMin 1.0 (full cube)"),
        ("VR0", "_ReflectionMin 0"), ("VS0", "_Scatter 0"), ("VG0", "grime off (audit clear values)"), ("A_before", "BEFORE")]
def diag(ids, name):
    tw, th, gap = 470, 360, 6
    sheet = Image.new("RGB", (4 * tw + 3 * gap, len(ids) * 2 * (th + gap) + 48), BG)
    ImageDraw.Draw(sheet).text((10, 10), "G10 · what makes the pane visible: one knob changed at a time (temporary material copy, state C)", fill=(255, 255, 255), font=FONT)
    y = 48
    for i in ids:
        x0, y0, x1, y1 = boxes[i]
        pad = 30
        box = (max(0, x0 - pad), max(0, y0 - pad), min(W, x1 + pad), min(H, y1 + pad))
        bw, bh = box[2] - box[0], box[3] - box[1]
        s = min(tw / bw, th / bh)
        for k, (suffix, cl) in enumerate(DIAG):
            im = load(f"{i}_{suffix}.jpg")
            if im is None: continue
            t = Image.new("RGB", (tw, th), BG)
            c = im.crop(box).resize((max(1, int(bw * s)), max(1, int(bh * s))), Image.LANCZOS)
            t.paste(c, ((tw - c.width) // 2, (th - c.height) // 2))
            sheet.paste(label(t, f"{i.replace('window_', '')} · {cl}"), ((k % 4) * (tw + gap), y + (k // 4) * (th + gap)))
        y += 2 * (th + gap)
    save(sheet, name)

diag(["window_L0_1.5m", "window_L0_0.7m", "window_L0_oblique50"], "g10_05_diagnostics_L0.jpg")
diag(["window_Office_1.5m", "38_deadlamp_window_1.5m", "39_dark_beyond_window_1.5m"], "g10_05b_diagnostics_Office_deadlamp.jpg")

# props: full frame BEFORE | AFTER (half size), then a 1:1 crop around the glass
PROPS = [("40_prop_bottle_WaterCooler", "water-cooler bottle (Prop_BottleBlue)", (700, 150, 1280, 560)),
         ("40_prop_vending_front", "vending front (Prop_Glass)", None),
         ("40_prop_vending_oblique", "vending ~53° (Prop_Glass)", None),
         ("41_desk_glass_STAGED", "STAGED desk: stand-in tumbler + bottle", (900, 420, 1440, 700)),
         ("42_hutch_cabinet_STAGED", "STAGED hutch + display cabinet", (540, 220, 1260, 760))]
def props(name):
    tw, th, gap = 960, 540, 6
    rows = [p for p in PROPS if load(f"{p[0]}_A_before.jpg")]
    hgt = 48
    for pid, _, crop in rows:
        hgt += th + gap
        if crop: hgt += th + gap
    sheet = Image.new("RGB", (2 * tw + gap, hgt), BG)
    ImageDraw.Draw(sheet).text((10, 10), "G10 · glass props · BEFORE | AFTER (full frame, then a crop where marked)", fill=(255, 255, 255), font=FONT)
    y = 48
    for pid, what, crop in rows:
        a, c = load(f"{pid}_A_before.jpg"), load(f"{pid}_C_after.jpg")
        sheet.paste(label(a.resize((tw, th), Image.LANCZOS), f"{what} · BEFORE"), (0, y))
        sheet.paste(label(c.resize((tw, th), Image.LANCZOS), f"{what} · AFTER"), (tw + gap, y))
        y += th + gap
        if crop:
            s = min(tw / (crop[2] - crop[0]), th / (crop[3] - crop[1]))
            size = (int((crop[2] - crop[0]) * s), int((crop[3] - crop[1]) * s))
            for k, im in enumerate((a, c)):
                t = Image.new("RGB", (tw, th), BG)
                t.paste(im.crop(crop).resize(size, Image.LANCZOS), ((tw - size[0]) // 2, (th - size[1]) // 2))
                sheet.paste(label(t, f"crop x{s:.1f} · {'BEFORE' if k == 0 else 'AFTER'}"), (k * (tw + gap), y))
            y += th + gap
    save(sheet, name)

props("g10_07_props.jpg")

# full-resolution frames for judging (copied, not re-encoded)
FULL = ["01_rep_L0", "window_L0_oblique50", "window_Office_oblique50", "34_rep_Office", "35_rep_Office_b", "37_rep_Dark",
        "38_deadlamp_window_1.5m", "window_L0_1.5m", "window_L0_0.7m", "window_Office_1.5m", "41_desk_glass_STAGED", "42_hutch_cabinet_STAGED"]
for i in FULL:
    for s in ("A_before", "C_after", "N_nopane_after"):
        p = os.path.join(src, f"{i}_{s}.jpg")
        if os.path.exists(p) and (s != "N_nopane_after" or i in ("window_L0_1.5m", "window_L0_0.7m")):
            shutil.copyfile(p, os.path.join(out, f"g10_full_{i}_{s}.jpg"))
print("copied full frames")
