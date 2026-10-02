"""FrontRooms surface library v2: Level 0, Level 4 (Office), Level ! (Run), shared.

Run: python gen_surfaces.py <outdir> <cc0 chevron png> [names...]
Repeats (world metres) divide 256 so the stream's floating-origin rebase never
shifts a pattern: wallpaper 256/373, carpet 1, ceiling/office/VCT 256/210, macro 8.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.argv = [sys.argv[0], sys.argv[1], sys.argv[2]] + sys.argv[3:]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "gen_common.py")).read())

P4 = 256 / 210  # 4 ft run (1.21905 m)


def mask(smooth, cavity, wet=None):
    z = np.zeros_like(smooth)
    return np.stack([smooth, cavity, z if wet is None else wet, np.ones_like(smooth)], -1)


def write(name, col, n=None, s=None, e=None):
    save_rgb(f"{OUT}/{name}_A.png", col)
    if n is not None: save_normal(f"{OUT}/{name}_N.png", n)
    if s is not None: save_rgba(f"{OUT}/{name}_S.png", s)
    if e is not None: save_rgb(f"{OUT}/{name}_E.png", e)


def wrap_lines(dr, N, M, pts, width, fill=255):
    for ox in (-N, 0, N):
        for oy in (-M, 0, M):
            dr.line([(a + ox, b + oy) for a, b in pts], fill=fill, width=width)


# ======================================================== Level 0 / Lobby / Shift / Exit
def wallpaper(name="Wallpaper_Chevron", ground="#D2C27C", mid="#AC9A52", deep="#766A34", cream="#E3D594", keep_hue=.16):
    src = np.asarray(Image.open(REF).convert("RGB")).astype(np.float32) / 255
    src = src[:-1, :-1]  # the CC0 file repeats its first row/column at the far edge
    W, H = 2048, 3072
    pad = np.concatenate([src, src[:, :8]], 1)
    pad = np.concatenate([pad, pad[:8]], 0)
    big = resize(pad, int(W * pad.shape[1] / src.shape[1]), int(H * pad.shape[0] / src.shape[0]))[:H, :W]
    lum = big @ np.array([.2126, .7152, .0722], np.float32)
    ink = np.clip((0.92 - lum) / 0.35, 0, 1)
    g, m, d = hexc(ground), hexc(mid), hexc(deep)
    t = ink[..., None]
    duo = np.where(t < .5, g + (m - g) * (t / .5), m + (d - m) * ((t - .5) / .5))
    col = duo + (big - lum[..., None]) * keep_hue
    cr = np.clip((lum - .90) / .06, 0, 1)[..., None]
    col = col + (hexc(cream) - col) * cr * .55
    fib = band(H, W, 180, 900, 11)
    mot = spectral(H, W, 1.6, 12)
    blot = band(H, W, 3, 14, 13)
    col *= (0.97 + 0.06 * mot[..., None]) * (0.988 + 0.024 * fib[..., None])
    tob = np.clip((blot - .64) / .25, 0, 1)[..., None] * .08
    col = col * (1 - tob) + hexc("#7A5B2A") * tob
    fox = (np.random.default_rng(5).random((H, W)) > .99993).astype(np.float32)
    fox = np.clip(blur(fox, 1.8) * 30, 0, 1)
    col *= (1 - .09 * fox[..., None])
    x = np.arange(W)[None, :]
    dd = np.minimum(x, W - x).astype(np.float32)
    seam_shadow = np.exp(-(dd / 1.6) ** 2) * .20
    seam_lift = np.exp(-((dd - 3.5) / 1.6) ** 2) * .04
    col = col * (1 - seam_shadow[..., None]) + seam_lift[..., None]
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    weave = np.sin(xx * 2 * np.pi / (W / 640)) * np.sin(yy * 2 * np.pi / (H / 960))
    weave = weave * (0.6 + 0.4 * band(H, W, 40, 200, 14))
    height = .18 * weave + .9 * blur(ink, 1.2) + .40 * fib + .6 * np.exp(-((dd - 2) / 2.2) ** 2)
    n = normal_from_height(height, 1.0)
    smooth = .20 + .07 * blur(ink, 1.0) - .04 * mot + .03 * (1 - fib)
    cav = 1 - .35 * seam_shadow / .20 - .10 * ink
    write(name, col, n, mask(smooth, cav))


def wallpaper_cold():
    # Exit / cold threshold: the same paper under a different print run.
    wallpaper("Wallpaper_Chevron_Cold", ground="#AFC0B6", mid="#87998F", deep="#56655E", cream="#C5D3C9", keep_hue=.10)


def carpet():
    N = 2048
    r = np.random.default_rng(29)
    # Scatter loop "nubs" on a jittered lattice; each nub is a soft bump with its
    # own size, height and yarn tone. Rows drift so nothing reads as a weave.
    p = 7.0
    nubs = np.zeros((N, N), np.float32)
    tones = np.zeros((N, N), np.float32)
    k = int(N / p)
    yy, xx = np.mgrid[0:7, 0:7].astype(np.float32) - 3
    for j in range(k):
        drift = r.normal(0, 1.2)
        for i in range(k):
            cx = (i + .5 + r.normal(0, .22)) * p + drift
            cy = (j + .5 + r.normal(0, .22)) * p
            rad = r.uniform(1.8, 3.2)
            hgt = r.uniform(.55, 1.0)
            ix, iy = int(cx), int(cy)
            bump = np.exp(-((xx - (cx - ix)) ** 2 + (yy - (cy - iy)) ** 2) / (rad * rad)) * hgt
            ys = (np.arange(iy - 3, iy + 4) % N)[:, None]; xs = (np.arange(ix - 3, ix + 4) % N)[None, :]
            nubs[ys, xs] = np.maximum(nubs[ys, xs], bump)
            tones[ys, xs] = np.where(bump > .25, r.random(), tones[ys, xs])
    fibre = band(N, N, 500, 1000, 24)
    tuft = band(N, N, 60, 220, 23)
    height = .62 * nubs + .25 * tuft + .18 * fibre
    tone = spectral(N, N, 1.4, 25)
    base = hexc("#9A8558")
    yarn = np.where(tones[..., None] > .88, hexc("#7C6A47"), np.where(tones[..., None] < .08, hexc("#B09C6E"), base))
    col = yarn * (0.93 + 0.09 * tone[..., None]) * (0.72 + 0.36 * height[..., None])
    n = normal_from_height(blur(height, .45), 2.2)
    write("Carpet_LoopPile", col, n, mask(.05 + .05 * (1 - height), .6 + .4 * height))


def ceiling(name="Ceiling_Fissured", layout="2x4", fissures=2400, depth=.16, face_hex="#D9D2BF", seed=31):
    N = 2048
    ppm = N / P4
    grid = 0.0238 * ppm
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    if layout == "2x4":
        dx = np.minimum.reduce([xx, np.abs(xx - N / 2), N - xx]); dy = np.minimum(yy, N - yy)
        tile_id = (xx >= N / 2).astype(np.float32)
    else:
        dx = np.minimum.reduce([xx, np.abs(xx - N / 2), N - xx]); dy = np.minimum.reduce([yy, np.abs(yy - N / 2), N - yy])
        tile_id = ((xx >= N / 2).astype(int) + 2 * (yy >= N / 2).astype(int)).astype(np.float32)
    dgrid = np.minimum(dx, dy)
    tbar = (dgrid < grid / 2).astype(np.float32)
    bevel = np.clip((dgrid - grid / 2) / (0.010 * ppm), 0, 1)
    img = Image.new("L", (N, N), 0)
    dr = ImageDraw.Draw(img)
    r = np.random.default_rng(seed)
    for _ in range(fissures):
        x, y = r.random() * N, r.random() * N
        a = r.random() * np.pi * 2
        pts = [(x, y)]
        for _ in range(int(r.integers(2, 8))):
            a += r.normal(0, .8); x += np.cos(a) * 4; y += np.sin(a) * 4
            pts.append((x, y))
        wrap_lines(dr, N, N, pts, int(r.integers(1, 3)))
    fis = blur(np.asarray(img).astype(np.float32) / 255, .7)
    pin = (r.random((N, N)) > .9955).astype(np.float32)
    pin = np.clip(blur(pin, .8) * 5, 0, 1)
    grain = band(N, N, 300, 900, seed + 1)
    tone = 1 - .02 * tile_id
    face = hexc(face_hex)[None, None, :] * tone[..., None]
    face = face * (0.95 + .05 * grain[..., None]) * (1 - depth * fis[..., None]) * (1 - .28 * pin[..., None])
    face *= (0.96 + .06 * spectral(N, N, 1.8, seed + 2)[..., None])
    col = face * (0.82 + .18 * bevel[..., None])
    col = col * (1 - tbar[..., None]) + hexc("#E3DFD3") * tbar[..., None]
    height = np.where(tbar > 0, 1.6, (.5 * grain - .8 * fis - .6 * pin) * .25 + (bevel - 1) * .9)
    n = normal_from_height(blur(height, .8), 3.0)
    smooth = np.where(tbar > 0, .42, .07 + .03 * grain)
    cav = np.where(tbar > 0, 1.0, .55 + .45 * bevel) * (1 - .25 * fis)
    write(name, col, n, mask(smooth, cav))


def lens():
    W, H = 1024, 2048
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    p = 5.0
    prism = np.abs(((xx % p) / p) - .5) + np.abs(((yy % p) / p) - .5)
    u = xx / W
    tubes = sum(np.exp(-((u - c) / .085) ** 2) for c in (.27, .5, .73))
    ends = np.clip(np.minimum(yy, H - yy) / (H * .06), 0, 1) ** .6
    emit = blur((.55 + .45 * tubes / tubes.max()) * ends * (.88 + .12 * (1 - prism)), .7)
    alb = hexc("#EDEBE3")[None, None, :] * (.94 + .06 * (1 - prism)[..., None])
    write("TrofferLens", alb, normal_from_height(prism, 1.6), None, np.repeat(emit[..., None], 3, -1))


def carpet_wet_free_macro():
    pass


# ======================================================== Level 4 / Office
def office_carpet():
    N = 2048  # 2 x 2 tiles of 24" (256/420 m), quarter-turned
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    half = N // 2
    quarter = ((xx >= half).astype(int) + (yy >= half).astype(int)) % 2
    # Cut-pile striation that changes direction tile to tile (quarter-turn install).
    sx = band(N, N * 8, 200, 900, 71); sx = resize(sx, N, N)
    sy = sx.T
    stri = np.where(quarter == 0, sx, sy)
    fibre = band(N, N, 400, 1000, 72)
    base = hexc("#5B636B")
    col = base[None, None, :] * (0.90 + .12 * stri[..., None]) * (0.92 + .10 * fibre[..., None])
    r = np.random.default_rng(73)
    flecks = r.random((N, N))
    for thr, c in ((.9975, "#3E8079"), (.9985, "#8C6A7D"), (.996, "#2E3237"), (.997, "#9AA2A8")):
        m = blur((flecks > thr).astype(np.float32), .6)
        flecks = r.random((N, N))
        col = col * (1 - np.clip(m * 2.5, 0, 1)[..., None]) + hexc(c) * np.clip(m * 2.5, 0, 1)[..., None]
    x = np.minimum.reduce([xx, np.abs(xx - half), N - xx]); y = np.minimum.reduce([yy, np.abs(yy - half), N - yy])
    seam = np.exp(-(np.minimum(x, y) / 1.2) ** 2)
    col *= (1 - .25 * seam[..., None])
    sheen = np.where(quarter == 0, 1.0, .965)
    col *= sheen[..., None]
    height = .5 * stri + .5 * fibre - .6 * seam
    write("Office_CarpetTile", col, normal_from_height(blur(height, .5), 1.8), mask(.06 + .03 * stri, .7 + .3 * fibre))


def drywall():
    N = 1024  # 256/210 m
    knock = blur(np.clip((band(N, N, 18, 70, 81) - .55) / .2, 0, 1), 1.5)  # knockdown splatter
    peel = band(N, N, 120, 400, 82)
    col = hexc("#BDB6A4")[None, None, :] * (0.97 + .03 * knock[..., None]) * (0.985 + .02 * peel[..., None])
    col *= (0.96 + .06 * spectral(N, N, 1.6, 83)[..., None])
    height = .8 * knock + .3 * peel
    write("Office_Drywall", col, normal_from_height(blur(height, .8), 1.6), mask(.30 + .06 * knock, .9 + .1 * knock))


def office_ceiling():
    ceiling("Office_Ceiling2x2", layout="2x2", fissures=1500, depth=.10, face_hex="#DCD8CC", seed=91)


def louver():
    N = 1024  # 2'x2' parabolic louver: 4 x 4 deep cells
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    c = N / 4
    lx = (xx % c) / c; ly = (yy % c) / c
    blade = np.minimum.reduce([lx, 1 - lx, ly, 1 - ly])
    cellglow = np.clip(blade / .5, 0, 1) ** 1.6
    emit = blur(cellglow * .95 + .05, 1.0)
    alb = hexc("#BFC2C4")[None, None, :] * (0.6 + .4 * (1 - cellglow[..., None]))
    height = -blade * 2
    write("Office_Louver", alb, normal_from_height(height, 4.0), mask(.82 - .3 * cellglow, 1 - .5 * cellglow), np.repeat(emit[..., None], 3, -1))


def fabric():
    N = 1024
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    weave = .5 * (np.sin(xx * 2 * np.pi / 6) ** 2) + .5 * (np.sin(yy * 2 * np.pi / 6 + np.pi * (np.floor(xx / 6) % 2)) ** 2)
    slub = band(N, N, 30, 160, 101)
    col = hexc("#6A7480")[None, None, :] * (0.88 + .10 * weave[..., None] * .5 + .12 * slub[..., None])
    write("Office_CubicleFabric", col, normal_from_height(blur(.6 * weave + .4 * slub, .5), 1.4), mask(.08 + 0 * slub, .8 + .2 * slub))


# ======================================================== Level ! / Run (hospital corridor)
def vct():
    N = 2048  # 4 x 4 tiles of 12" (256/840 m)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    t = N / 4
    tid = (np.floor(xx / t) + 4 * np.floor(yy / t)).astype(int)
    r = np.random.default_rng(111)
    tone = r.normal(0, .025, 16)[tid]
    # VCT chip pattern: directional flecks.
    chips = band(N * 4, N, 120, 500, 112); chips = resize(chips, N, N)
    chips2 = band(N, N, 300, 900, 113)
    base = hexc("#DAD7CC")
    col = base[None, None, :] * (1 + tone[..., None])
    darkf = np.clip((chips - .62) / .2, 0, 1)
    col = col * (1 - .22 * darkf[..., None]) + hexc("#8F8A7E") * .10 * darkf[..., None]
    col *= (0.97 + .04 * chips2[..., None])
    gx = np.minimum(xx % t, t - xx % t); gy = np.minimum(yy % t, t - yy % t)
    grout = np.exp(-(np.minimum(gx, gy) / 1.1) ** 2)
    col *= (1 - .30 * grout[..., None])
    # Heel scuffs (black marks) and a wax wear lane.
    img = Image.new("L", (N, N), 0); dr = ImageDraw.Draw(img)
    for _ in range(90):
        x, y = r.random() * N, r.random() * N; a = r.random() * np.pi; l = r.random() * 50 + 10
        wrap_lines(dr, N, N, [(x, y), (x + np.cos(a) * l, y + np.sin(a) * l)], int(r.integers(1, 4)))
    sc = blur(np.asarray(img).astype(np.float32) / 255, 1.2)
    col *= (1 - .35 * sc[..., None])
    wear = spectral(N, N, 1.9, 114)
    smooth = .62 - .22 * wear - .25 * sc - .3 * grout
    height = -.8 * grout + .1 * chips2
    write("Run_VCT", col, normal_from_height(blur(height, .6), 1.5), mask(smooth, 1 - .4 * grout))


def hospital_wall():
    N = 1024
    peel = band(N, N, 120, 400, 121)
    img = Image.new("L", (N, N), 0); dr = ImageDraw.Draw(img)
    r = np.random.default_rng(122)
    for _ in range(70):
        x, y = r.random() * N, r.random() * N; a = r.random() * .5 - .25; l = r.random() * 70 + 15
        wrap_lines(dr, N, N, [(x, y), (x + np.cos(a) * l, y + np.sin(a) * l)], 1)
    sc = blur(np.asarray(img).astype(np.float32) / 255, .7)
    col = hexc("#E3E1D9")[None, None, :] * (0.97 + .04 * spectral(N, N, 1.6, 123)[..., None]) * (1 - .18 * sc[..., None])
    write("Run_HospitalWall", col, normal_from_height(.6 * peel - .3 * sc, 1.0), mask(.55 + .06 * peel - .2 * sc, np.ones_like(peel)))


def exit_sign():
    W, H = 1024, 512
    img = Image.new("RGB", (W, H), (226, 224, 216))
    dr = ImageDraw.Draw(img)
    font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 300)
    text = "EXIT"
    bb = dr.textbbox((0, 0), text, font=font)
    tw, th = bb[2] - bb[0], bb[3] - bb[1]
    ox, oy = (W - tw) // 2 - bb[0], (H - th) // 2 - bb[1] - 10
    dr.text((ox, oy), text, font=font, fill=(200, 26, 22))
    for sgn, x in ((-1, 70), (1, W - 70)):  # chevrons both directions
        dr.polygon([(x, H // 2), (x - sgn * 40, H // 2 - 46), (x - sgn * 40, H // 2 + 46)], fill=(200, 26, 22))
    a = np.asarray(img).astype(np.float32) / 255
    red = (a[..., 0] > .6) & (a[..., 1] < .3)
    emit = np.zeros_like(a)
    emit[red] = (1.0, .10, .06)
    emit = np.maximum(blur(emit, 2.0) * .6, emit)
    emit += np.array([.10, .02, .015]) * 0.5  # diffused panel glow
    write("Run_ExitSign", a, None, None, np.clip(emit, 0, 1))


# ======================================================== shared
def veneer():
    W, H = 1024, 2048
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    warp = (spectral(H, W, 2.8, 41) - .5) * 26 + (band(H, W, 4, 12, 42) - .5) * 5
    rings = np.sin((xx + warp) * 2 * np.pi / 22.0 + 2.2 * np.sin(yy / H * 2 * np.pi * 2 + xx / W * 6))
    fine = band(H, W, 200, 700, 43)
    pores = blur((band(H, W, 400, 1000, 44) > .80).astype(np.float32), .6)
    g = .5 + .5 * rings
    light, dark = hexc("#BE8A4E"), hexc("#8A5A2E")
    col = dark + (light - dark) * (0.55 * g + .45 * fine)[..., None]
    col *= (1 - .16 * pores[..., None]) * (0.92 + .10 * spectral(H, W, 1.7, 45)[..., None])
    v = 1 - yy / H
    kick = np.clip((0.12 - v) / .12, 0, 1) * (0.5 + .5 * band(H, W, 30, 120, 46))
    col *= (1 - .25 * kick[..., None])
    height = .4 * g + .4 * fine - .8 * pores
    write("DoorVeneer", col, normal_from_height(blur(height, .5), 1.2), mask(.48 - .18 * kick - .10 * pores, 1 - .3 * pores))


def painted_metal():
    N = 1024
    peel = band(N, N, 60, 260, 51)
    grime = spectral(N, N, 1.5, 52)
    img = Image.new("L", (N, N), 0); dr = ImageDraw.Draw(img)
    r = np.random.default_rng(53)
    for _ in range(140):
        x, y = r.random() * N, r.random() * N; a = r.random() * np.pi; l = r.random() * 40 + 8
        wrap_lines(dr, N, N, [(x, y), (x + np.cos(a) * l, y + np.sin(a) * l)], 1)
    scr = blur(np.asarray(img).astype(np.float32) / 255, .5)
    col = hexc("#DAD4C4")[None, None, :] * (0.94 + .06 * grime[..., None]) * (1 - .10 * scr[..., None])
    write("PaintedMetal", col, normal_from_height(peel * .6 - scr * .4, 1.0), mask(.52 + .08 * peel - .25 * scr - .08 * grime, np.ones_like(peel)))


def macro():
    N = 1024
    R = spectral(N, N, 1.7, 61)
    G = band(N, N, 12, 60, 62)
    B = blur(np.clip((band(N, N, 3, 9, 63) - .66) / .16, 0, 1), 4)
    A = np.clip((resize(spectral(N, N * 8, 1.4, 64), N, N) - .55) / .35, 0, 1)
    save_rgba(f"{OUT}/MacroWear_M.png", np.stack([R, G, B, A], -1))


ALL = dict(wallpaper=wallpaper, wallpaper_cold=wallpaper_cold, carpet=carpet, ceiling=ceiling, lens=lens,
           office_carpet=office_carpet, drywall=drywall, office_ceiling=office_ceiling, louver=louver, fabric=fabric,
           vct=vct, hospital_wall=hospital_wall, exit_sign=exit_sign, veneer=veneer, metal=painted_metal, macro=macro)

if __name__ == "__main__":
    for name in (sys.argv[3:] or ALL.keys()):
        ALL[name]()
        print("done", name, flush=True)
