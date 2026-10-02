"""Pack the approved CC0 scans into the prop kit's slot textures.

  python Tools/lookdev/import_cc0_textures.py <out textures dir> [slot ...]

Sources: Tools/lookdev/cc0_src (fetch_cc0.py). For every Prop_* slot the scan
keeps its own detail (grain, weave, pores, scratches) but is regraded to the
slot's measured albedo target (research/10_synthesis.md §5.2): per-channel
ratio to the scan's mean, so hue variation survives. Roughness is
percentile-normalised into the slot's smoothness range.
Outputs <slot>_A.png (sRGB albedo), _N.png (OpenGL normal), _S.png (linear:
R smoothness, G AO/cavity) — the FrontRooms/Surface convention.
"""
import io, os, sys, zipfile
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "cc0_src")
OUT = sys.argv[1]
ONLY = set(sys.argv[2:])
os.makedirs(OUT, exist_ok=True)


def hexc(s):
    return np.array([int(s[i:i + 2], 16) / 255 for i in (1, 3, 5)], np.float32)


def to_lin(c):
    return np.where(c <= .04045, c / 12.92, ((c + .055) / 1.055) ** 2.4)


def to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= .0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - .055)


def load_ph(asset, mapname):
    d = os.path.join(SRC, "polyhaven", asset)
    for f in os.listdir(d):
        if f.startswith(asset + "_" + mapname + "_"):
            return Image.open(os.path.join(d, f))
    return None


def load_acg(name, mapname):
    asset = name.rsplit("_", 1)[0]
    z = zipfile.ZipFile(os.path.join(SRC, "ambientcg", asset, name + "-JPG.zip"))
    for n in z.namelist():
        if n.endswith("_" + mapname + ".jpg"):
            return Image.open(io.BytesIO(z.read(n)))
    return None


def maps(src):
    """-> dict(albedo, normal, rough, ao, height) as PIL images (or None)."""
    kind, name = src
    if kind == "ph":
        arm = load_ph(name, "arm")
        ao = rough = None
        if arm is not None:
            r, g, b = arm.convert("RGB").split()
            ao, rough = r, g
        return dict(albedo=load_ph(name, "diff"), normal=load_ph(name, "nor_gl"), rough=rough, ao=ao, height=load_ph(name, "disp"))
    return dict(albedo=load_acg(name, "Color"), normal=load_acg(name, "NormalGL"), rough=load_acg(name, "Roughness"),
                ao=load_acg(name, "AmbientOcclusion"), height=load_acg(name, "Displacement"))


def arr(img, size, mode="RGB"):
    img = img.convert(mode)
    if img.size != (size, size):
        img = img.resize((size, size), Image.LANCZOS)
    return np.asarray(img).astype(np.float32) / 255


def regrade(albedo, target, detail=1.0):
    """Per-channel ratio to the scan mean in linear light, re-centred on target."""
    lin = to_lin(albedo)
    mean = lin.reshape(-1, 3).mean(0) + 1e-4
    ratio = (lin / mean) ** detail
    out = to_lin(hexc(target))[None, None, :] * ratio
    lo, hi = to_lin(np.float32(0x10 / 255)), to_lin(np.float32(0xE6 / 255))
    return to_srgb(np.clip(out, lo, hi))


def smooth_range(rough, lo, hi):
    s = 1 - rough
    p2, p98 = np.percentile(s, 2), np.percentile(s, 98)
    s = np.clip((s - p2) / max(p98 - p2, 1e-3), 0, 1)
    return lo + (hi - lo) * s


def save(slot, a, n, s_r, s_g):
    Image.fromarray((np.clip(a, 0, 1) * 255 + .5).astype(np.uint8), "RGB").save(os.path.join(OUT, slot + "_A.png"), optimize=True)
    if n is not None:
        Image.fromarray((np.clip(n, 0, 1) * 255 + .5).astype(np.uint8), "RGB").save(os.path.join(OUT, slot + "_N.png"), optimize=True)
    rgba = np.stack([s_r, s_g, np.zeros_like(s_r), np.ones_like(s_r)], -1)
    Image.fromarray((np.clip(rgba, 0, 1) * 255 + .5).astype(np.uint8), "RGBA").save(os.path.join(OUT, slot + "_S.png"), optimize=True)


def flatten_normal(n, keep):
    """Blend an OpenGL normal map toward flat (pores removed / milder bumps)."""
    v = n * 2 - 1
    v[..., 0:2] *= keep
    v /= np.linalg.norm(v, axis=-1, keepdims=True) + 1e-6
    return v * .5 + .5


def noise(size, seed, sigma):
    r = np.random.default_rng(seed).standard_normal((size, size)).astype(np.float32)
    img = Image.fromarray(((r - r.min()) / (r.max() - r.min()) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(sigma))
    return np.asarray(img).astype(np.float32) / 255


# slot: source, size, albedo target, smoothness range, extras
SLOTS = {
    "Prop_WoodCherry": (("ph", "lacquered_cherry_wood"), 2048, "#5A2A18", (.65, .75), {}),
    "Prop_WoodOak": (("ph", "red_oak_veneer"), 2048, "#9A6A3A", (.50, .58), {}),
    "Prop_WoodTeak": (("ph", "teak_veneer"), 2048, "#A0582A", (.48, .55), {}),
    "Prop_WoodDark": (("ph", "dark_wood"), 2048, "#2E1C14", (.55, .62), {}),
    "Prop_WoodEbony": (("ph", "dark_wood"), 2048, "#1C1410", (.62, .70), {}),
    "Prop_WoodWalnut": (("ph", "walnut_veneer"), 2048, "#4A3020", (.48, .55), {}),
    "Prop_WoodLaminate": (("ph", "red_oak_veneer"), 2048, "#8E6E4C", (.58, .64), {"normal_keep": .25, "detail": .7}),
    "Prop_Plywood": (("ph", "plywood"), 2048, "#B8936A", (.25, .32), {}),
    "Prop_Chipboard": (("acg", "Chipboard004_1K"), 1024, "#9C8466", (.20, .28), {}),
    "Prop_PinePallet": (("acg", "Planks021_1K"), 1024, "#A88A62", (.15, .22), {}),
    "Prop_Studs": (("acg", "Wood096_1K"), 1024, "#C9AE84", (.18, .25), {}),
    "Prop_PlasticBeige": (("acg", "Plastic013B_1K"), 1024, "#D3C9AE", (.45, .55), {"gen_albedo": 2}),
    "Prop_PlasticWhite": (("acg", "Plastic013B_1K"), 1024, "#D9D5C8", (.45, .55), {"gen_albedo": 3}),
    "Prop_PlasticBlack": (("acg", "Plastic012B_1K"), 1024, "#1A1A1A", (.40, .48), {"detail": .5}),
    "Prop_PlasticGrey": (("acg", "Plastic018B_1K"), 1024, "#5E5E5A", (.40, .48), {"detail": .5}),
    "Prop_SteelPutty": (("acg", "Metal028_1K"), 1024, "#A8A08A", (.38, .48), {"detail": .6}),
    "Prop_SteelBrown": (("acg", "Metal028_1K"), 1024, "#3B2E25", (.38, .48), {"detail": .6}),
    "Prop_SteelBlack": (("acg", "Metal028_1K"), 1024, "#1E1E1E", (.38, .48), {"detail": .6}),
    "Prop_Aluminium": (("acg", "Metal050C_1K"), 1024, "#B8B8B4", (.50, .60), {"detail": .6}),
    "Prop_FabricCubicle": (("ph", "poly_wool_herringbone"), 1024, "#5A646E", (.10, .18), {}),
    "Prop_FabricBeige": (("ph", "poly_wool_herringbone"), 1024, "#B9A88A", (.10, .18), {}),
    "Prop_FabricChair": (("ph", "rough_linen"), 1024, "#1C1C1E", (.12, .18), {}),
    "Prop_FabricTeal": (("ph", "rough_linen"), 1024, "#2F6B6A", (.12, .20), {}),
    "Prop_FabricCharcoal": (("ph", "rough_linen"), 1024, "#3A3A3C", (.12, .18), {}),
    "Prop_FabricNavy": (("ph", "rough_linen"), 1024, "#23304A", (.12, .18), {}),
    "Prop_VelvetPink": (("ph", "velour_velvet"), 1024, "#B88986", (.20, .30), {"detail": .45}),
    # The jacquard's own woven motif, regraded to the faded 90s ground colour.
    "Prop_FabricFloral": (("ph", "floral_jacquard"), 2048, "#C4B596", (.10, .16), {"detail": 1.15}),
    "Prop_Vinyl": (("acg", "Leather027_1K"), 1024, "#151413", (.35, .45), {}),
    # CardboardSet001 / Tape005 are cut-out sheets (opacity), not tiles: their
    # roughness/normal crops drive a generated surface instead.
    "Prop_Cardboard": (("acg", "Chipboard004_1K"), 1024, "#A07E55", (.15, .22), {"gen_albedo": 11, "normal_keep": .15}),
    "Prop_TapeBlue": (("acg", "Leather027_1K"), 512, "#2E86C1", (.28, .32), {"gen_albedo": 12, "normal_keep": .2}),
}

for slot, (src, size, target, (lo, hi), extra) in SLOTS.items():
    if ONLY and slot not in ONLY:
        continue
    m = maps(src)
    alb = arr(m["albedo"], size) if m["albedo"] is not None else np.full((size, size, 3), .5, np.float32)
    nrm = arr(m["normal"], size) if m["normal"] is not None else None
    rough = arr(m["rough"], size, "L") if m["rough"] is not None else np.full((size, size), .5, np.float32)
    ao = arr(m["ao"], size, "L") if m["ao"] is not None else np.ones((size, size), np.float32)
    if extra.get("floral"):
        # Woven motif from the height map: ground, motif, faded rose/sage accents.
        h = arr(m["height"], size, "L") if m["height"] is not None else alb.mean(-1)
        hb = np.asarray(Image.fromarray((h * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2))).astype(np.float32) / 255
        motif = np.clip((hb - np.percentile(hb, 55)) / max(np.percentile(hb, 85) - np.percentile(hb, 55), 1e-3), 0, 1)
        ground, mot = to_lin(hexc("#CDBFA3")), to_lin(hexc("#A89679"))
        rose, sage = to_lin(hexc("#B08A88")), to_lin(hexc("#8E9A80"))
        tint = noise(size, 7, 60)
        accent = np.where(tint[..., None] > .55, rose, sage)
        mix = np.clip((np.abs(tint - .5) - .08) * 6, 0, 1)[..., None]
        motif_col = mot * (1 - mix * .7) + accent * (mix * .7)
        lin = ground * (1 - motif[..., None]) + motif_col * motif[..., None]
        weave = (alb.mean(-1) / (alb.mean() + 1e-4))[..., None] ** .35
        a = to_srgb(lin * weave)
    elif "gen_albedo" in extra:
        # Plastics: flat target colour with faint mottling from the scan's luminance.
        lum = alb.mean(-1)
        a = to_srgb(to_lin(hexc(target))[None, None, :] * ((lum / (lum.mean() + 1e-4)) ** .12)[..., None]
                    * (1 + .03 * (noise(size, extra["gen_albedo"], 40) - .5))[..., None])
    else:
        a = regrade(alb, target, extra.get("detail", 1.0))
    if nrm is not None and "normal_keep" in extra:
        nrm = flatten_normal(nrm, extra["normal_keep"])
    save(slot, a, nrm, smooth_range(rough, lo, hi), np.clip(ao, 0, 1))
    print("packed", slot, size, flush=True)
