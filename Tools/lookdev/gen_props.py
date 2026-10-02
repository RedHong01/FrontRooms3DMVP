"""FrontRooms prop kit: unique (decal-mapped) textures.

Run: python gen_props.py <outdir> [names...]
Each map covers one part 0..1 (kit parts with uv="decal"):
  Prop_ScreenCRT     4:3 CRT face: dead phosphor glass, dust, vignette (+ _E for the
                     rare monitor left on: a dim DOS prompt)
  Prop_VendingFront  1:2 snack machine glass: 6 rows of fictional snacks on coils,
                     price strips, the lit cabinet behind (+ _E)
  Prop_CopierPanel   4:1 copier control strip: keypad, LCD, start button
  Prop_KeyboardKeys  8:3 top of a beige 101-key keyboard
  Prop_Label         label sheet (filing-cabinet card holders, asset tags)
All brand names are invented; nothing reproduces a real trademark.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.argv = [sys.argv[0], sys.argv[1], ""] + sys.argv[2:]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_common.py")).read())

FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_MONO = "/System/Library/Fonts/Supplemental/Courier New Bold.ttf"


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def mask(smooth, cavity):
    z = np.zeros_like(smooth)
    return np.stack([smooth, cavity, z, np.ones_like(smooth)], -1)


def write(name, col, n=None, s=None, e=None):
    save_rgb(f"{OUT}/{name}_A.png", col)
    if n is not None: save_normal(f"{OUT}/{name}_N.png", n)
    if s is not None: save_rgba(f"{OUT}/{name}_S.png", s)
    if e is not None: save_rgb(f"{OUT}/{name}_E.png", e)


def arr(img):
    return np.asarray(img).astype(np.float32) / 255


# ------------------------------------------------------------------ CRT screen
def screen_crt():
    W, H = 1024, 768
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    u, v = xx / W * 2 - 1, yy / H * 2 - 1
    r2 = (u * u * .9 + v * v)
    # Dead phosphor: a dark grey-green glass, lighter toward the bulge centre.
    base = hexc("#1F2622") * (1.0 + .35 * np.clip(1 - r2, 0, 1))[..., None]
    dust = blur(spectral(H, W, 1.2, 101), 1.0)
    specks = (band(H, W, 300, 700, 102) > .86).astype(np.float32)
    smudge = blur(np.clip((spectral(H, W, 2.2, 103) - .58) * 4, 0, 1), 6)
    col = base + (hexc("#5A5C55") - base) * (0.10 * dust + .25 * specks + .22 * smudge)[..., None]
    # Inner bezel shadow: the tube face sinks into the casing.
    edge = np.clip(np.maximum(np.abs(u), np.abs(v)) * 1.0 - .86, 0, 1) / .14
    col *= (1 - .55 * edge ** 1.5)[..., None]
    smooth = .86 - .5 * smudge - .3 * specks
    write("Prop_ScreenCRT", col, None, mask(smooth, np.ones_like(smooth)))
    # Emission for the rare live monitor: dim amber DOS text and scanlines.
    img = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(img)
    f = font(FONT_MONO, 34)
    lines = ["C:\\>DIR /W", " Volume in drive C has no label", " Directory of C:\\LEVEL4",
             "", "[.]      [..]     FLOOR.DAT  EXIT.BAT", "        4 file(s)  0 bytes free", "", "C:\\>EXIT.BAT",
             "Bad command or file name", "", "C:\\>_"]
    for i, line in enumerate(lines):
        dr.text((70, 60 + i * 52), line, font=f, fill=255)
    text = blur(arr(img), 1.1) * 1.4
    scan = .75 + .25 * (np.sin(yy * np.pi / 2.0) ** 2)
    glow = np.clip(text * scan, 0, 1)[..., None] * hexc("#FFB347")[None, None, :]
    glow += hexc("#1A1206")[None, None, :] * np.clip(1 - r2, 0, 1)[..., None] * .6
    glow *= (1 - edge ** 1.5)[..., None]
    save_rgb(f"{OUT}/Prop_ScreenCRT_E.png", np.clip(glow, 0, 1))


# ------------------------------------------------------------- vending machine
SNACKS = [
    ("CRUNCHOS", "#C8352A", "#F2C230"), ("Mallo", "#F1E3C8", "#7A3B1F"), ("PRETZL", "#2B4F9E", "#F4F1E8"),
    ("Cheezy", "#F08A1C", "#3B1E0E"), ("NUTBAR", "#5B3A22", "#E8D7B0"), ("Fizz", "#1E8A4C", "#F7F3E4"),
    ("ZESTO", "#E6D02A", "#B2261C"), ("Choco", "#3A1D12", "#D9A441"), ("SALTS", "#8BB3D9", "#1F3550"),
    ("Gummo", "#D2477C", "#FFF2B8"), ("POPPS", "#F6EAD0", "#C0392B"), ("Tater", "#B9772E", "#FFF4D6"),
]


def vending_front():
    W, H = 1024, 2048
    img = Image.new("RGB", (W, H), (34, 30, 26))
    dr = ImageDraw.Draw(img)
    emit = Image.new("RGB", (W, H), (0, 0, 0))
    de = ImageDraw.Draw(emit)
    rng = np.random.default_rng(111)
    rows, cols = 6, 6
    top, bottom = 90, 1720
    rh = (bottom - top) / rows
    cw = (W - 120) / cols
    f_brand = font(FONT_BOLD, 30)
    f_price = font(FONT_BOLD, 26)
    # Lit cabinet: a warm fluorescent wash, brightest at the top.
    for y in range(top - 60, bottom + 30, 4):
        k = 1 - (y - top) / (bottom - top) * .45
        de.rectangle([40, y, W - 40, y + 4], fill=(int(70 * k), int(66 * k), int(52 * k)))
    for r in range(rows):
        y0 = top + r * rh
        shelf_y = y0 + rh - 34
        for c in range(cols):
            x0 = 60 + c * cw
            # Some slots are sold out; some packs hang crooked.
            if rng.random() < .16:
                continue
            name, a, b = SNACKS[rng.integers(len(SNACKS))]
            bw, bh = cw * .78, rh * .70
            bx = x0 + (cw - bw) / 2 + rng.normal(0, 3)
            by = shelf_y - bh - 6 + rng.normal(0, 4)
            tilt = rng.normal(0, 4)
            pack = Image.new("RGBA", (int(bw), int(bh)), a)
            pd = ImageDraw.Draw(pack)
            pd.rectangle([0, bh * .34, bw, bh * .62], fill=b)
            size = 30
            while size > 14:
                fb = font(FONT_BOLD, size)
                tb = pd.textbbox((0, 0), name, font=fb)
                if tb[2] - tb[0] <= bw - 10: break
                size -= 2
            pd.text(((bw - (tb[2] - tb[0])) / 2, bh * .36), name, font=fb, fill=a)
            pd.rectangle([0, 0, bw, 10], fill=(220, 220, 214))  # crimp
            pd.rectangle([0, bh - 10, bw, bh], fill=(220, 220, 214))
            pack = pack.rotate(tilt, expand=True, resample=Image.BICUBIC)
            img.paste(pack, (int(bx), int(by)), pack)
            # Coil in front of the pack.
            for k in range(5):
                cx = x0 + cw * (.18 + k * .16)
                dr.arc([cx - 16, shelf_y - 56, cx + 16, shelf_y - 4], 200, 340, fill=(170, 170, 165), width=4)
        # Shelf lip and price strip.
        dr.rectangle([40, shelf_y, W - 40, shelf_y + 30], fill=(56, 54, 50))
        for c in range(cols):
            x0 = 60 + c * cw
            label = "%d%d  $%.2f" % (r + 1, c + 1, .65 + .1 * ((r * 7 + c * 3) % 9))
            dr.rectangle([x0 + 8, shelf_y + 4, x0 + cw - 8, shelf_y + 26], fill=(236, 232, 214))
            dr.text((x0 + 14, shelf_y + 2), label, font=f_price, fill=(30, 30, 30))
    # Delivery bin and the dark lower panel.
    dr.rectangle([40, 1760, W - 40, 2010], fill=(18, 17, 16))
    dr.rectangle([120, 1810, W - 120, 1960], fill=(8, 8, 8))
    dr.text((140, 1830), "PUSH", font=font(FONT_BOLD, 40), fill=(120, 116, 104))
    col = arr(img)
    lit = arr(emit)
    # Glass: dust and finger smudges lower down, a faint reflection band.
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dust = blur(spectral(H, W, 1.3, 112), 1.0)
    smudge = blur(np.clip((spectral(H, W, 2.0, 113) - .55) * 3.5, 0, 1), 8) * np.clip((yy / H - .35) * 2, 0, 1)
    col = col * (0.85 + .25 * lit.mean(-1, keepdims=True) * 3) + .06 * dust[..., None] + .10 * smudge[..., None]
    emission = np.clip(col * lit.mean(-1, keepdims=True) * 4.0, 0, 1) * .9
    emission[1740:] = 0
    smooth = .9 - .45 * smudge - .2 * dust
    write("Prop_VendingFront", np.clip(col, 0, 1), None, mask(smooth, np.ones_like(smooth)), emission)


# ----------------------------------------------------------------- copier panel
def copier_panel():
    W, H = 1024, 256
    img = Image.new("RGB", (W, H), (196, 192, 180))
    dr = ImageDraw.Draw(img)
    dr.rectangle([0, 0, W, 18], fill=(150, 146, 136))
    # LCD.
    dr.rectangle([40, 50, 330, 150], fill=(60, 74, 52))
    dr.rectangle([48, 58, 322, 142], fill=(122, 140, 98))
    dr.text((62, 76), "READY   001", font=font(FONT_MONO, 34), fill=(40, 52, 34))
    # Keypad 4x3.
    f = font(FONT_BOLD, 26)
    keys = "123456789*0#"
    for i, k in enumerate(keys):
        x = 400 + (i % 3) * 64
        y = 30 + (i // 3) * 52
        dr.rounded_rectangle([x, y, x + 52, y + 42], 6, fill=(222, 220, 212), outline=(120, 118, 110), width=2)
        dr.text((x + 17, y + 7), k, font=f, fill=(40, 40, 40))
    # Function buttons and the big green start.
    for i, label in enumerate(("RESET", "STOP", "DARKER", "LIGHTER")):
        x = 640 + (i % 2) * 110
        y = 40 + (i // 2) * 80
        dr.rounded_rectangle([x, y, x + 96, y + 52], 8, fill=(210, 206, 196), outline=(110, 106, 98), width=2)
        dr.text((x + 10, y + 14), label, font=font(FONT_BOLD, 18), fill=(50, 50, 50))
    dr.rounded_rectangle([880, 60, 990, 190], 14, fill=(46, 140, 72), outline=(30, 80, 40), width=3)
    dr.text((900, 110), "START", font=font(FONT_BOLD, 24), fill=(230, 240, 230))
    col = arr(img)
    grime = blur(spectral(H, W, 1.6, 121), 1.0)
    col *= (0.92 + .08 * grime)[..., None]
    hgt = blur(arr(img.convert("L")), 1.5)
    write("Prop_CopierPanel", col, normal_from_height(hgt, 2.5), mask(.45 + .1 * grime, np.ones_like(grime)))


# --------------------------------------------------------------------- keyboard
def keyboard_keys():
    W, H = 2048, 768
    img = Image.new("RGB", (W, H), (150, 144, 128))
    hmap = Image.new("L", (W, H), 0)
    dr = ImageDraw.Draw(img)
    dh = ImageDraw.Draw(hmap)
    f = font(FONT, 26)
    unit = W / 23.0
    unit_y = (H - 60) / 6.2  # rows fill the map height (keys are slightly tall)
    rows = [
        ["Esc", None, "F1", "F2", "F3", "F4", None, "F5", "F6", "F7", "F8", None, "F9", "F10", "F11", "F12"],
        ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", ("Bksp", 2)],
        [("Tab", 1.5), "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", ("\\", 1.5)],
        [("Caps", 1.75), "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", ("Enter", 2.25)],
        [("Shift", 2.25), "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", ("Shift", 2.75)],
        [("Ctrl", 1.5), None, ("Alt", 1.5), ("", 7), ("Alt", 1.5), None, ("Ctrl", 1.5)],
    ]
    y = 30
    for ri, row in enumerate(rows):
        x = 40
        for key in row:
            if key is None:
                x += unit * .5; continue
            label, w = (key, 1) if isinstance(key, str) else key
            x0, x1 = x + 4, x + unit * w - 4
            y0, y1 = y + 4, y + unit_y - 4
            shade = 214 if ri else 200
            dr.rounded_rectangle([x0, y0, x1, y1], 9, fill=(shade, shade - 6, shade - 22), outline=(120, 114, 98), width=2)
            dh.rounded_rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], 9, fill=255)
            dr.text((x0 + 12, y0 + 8), label, font=f, fill=(60, 58, 52))
            x += unit * w
        y += unit_y + (18 if ri == 0 else 0)
    # Numeric pad and arrows on the right.
    for i, label in enumerate(["7", "8", "9", "4", "5", "6", "1", "2", "3", "0", ".", "+"]):
        x = W - 4 * unit + (i % 3) * unit
        yk = 30 + unit_y + 18 + (i // 3) * unit_y
        dr.rounded_rectangle([x + 4, yk + 4, x + unit - 4, yk + unit_y - 4], 9, fill=(212, 206, 190), outline=(120, 114, 98), width=2)
        dh.rounded_rectangle([x + 10, yk + 10, x + unit - 10, yk + unit_y - 10], 9, fill=255)
        dr.text((x + 16, yk + 10), label, font=f, fill=(60, 58, 52))
    col = arr(img)
    grime = blur(spectral(H, W, 1.5, 131), 1.0)
    col *= (0.86 + .14 * grime)[..., None]
    hgt = blur(arr(hmap), 3)
    write("Prop_KeyboardKeys", col, normal_from_height(hgt, 6), mask(.42 + .12 * hgt, .7 + .3 * hgt))


# ----------------------------------------------------------------------- labels
def labels():
    W, H = 1024, 512
    img = Image.new("RGB", (W, H), (226, 220, 200))
    dr = ImageDraw.Draw(img)
    f = font(FONT_MONO, 34)
    texts = ["A - C", "D - F", "G - K", "L - P", "Q - S", "T - Z", "1994", "1995", "PAYROLL", "MISC", "OLD", "LEVEL 4"]
    for i, t in enumerate(texts):
        x = (i % 4) * 256 + 18
        y = (i // 4) * 170 + 30
        dr.rectangle([x, y, x + 220, y + 110], fill=(240, 236, 220), outline=(150, 140, 120), width=3)
        dr.text((x + 20, y + 34), t, font=f, fill=(40, 40, 60))
    col = arr(img) * (0.9 + .1 * blur(spectral(H, W, 1.5, 141), 1.0))[..., None]
    write("Prop_Label", col, None, mask(np.full((H, W), .3, np.float32), np.ones((H, W), np.float32)))


ALL = dict(screen_crt=screen_crt, vending_front=vending_front, copier_panel=copier_panel,
           keyboard_keys=keyboard_keys, labels=labels)

if __name__ == "__main__":
    for name in (sys.argv[3:] or ALL.keys()):
        ALL[name]()
        print("done", name, flush=True)
