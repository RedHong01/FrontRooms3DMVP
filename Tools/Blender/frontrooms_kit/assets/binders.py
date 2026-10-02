"""A row of five 3-ring binders standing spine-out, c. 1985-2000: vinyl-
over-board and cloth-covered D-ring binders with rolled hinge edges, a
hinge crease pressed into each cover, a spine label window (a welded vinyl
pocket or a riveted chrome holder) with a paper insert, the page block
showing between the covers, index tabs on some, and the last binder leaning
on its neighbour.

Real-world reference size per binder: 0.29 m tall x 0.27 m deep, spines
40-60 mm (1"-2" rings). Row about 0.33 m long. Origin = shelf / desk
surface under the middle of the row. Spines (front) look -Y.
"""

import math
import random

from mathutils import Matrix, Vector

import _storage_labels as labels

NAME = "Kit_Binders"

PAPER = "Prop_Paper"
LABEL = "Prop_Label"
CHROME = "Prop_Chrome"
TAB = "Prop_PlasticWhite"

H, D = 0.29, 0.27
COVER_T = 0.0032

# (spine width, cover slot, label style, page fill, index tabs, spine card)
# Spine cards are tiles of the Prop_Label atlas (see _storage_labels.py).
ROW = [
    (0.050, "Prop_PlasticBlack", "pocket", 0.92, 0, "1994"),
    (0.045, "Prop_FabricTeal", "chrome", 0.80, 3, "PAYROLL"),
    (0.060, "Prop_Vinyl", "pocket", 0.95, 0, "1995"),
    (0.040, "Prop_PlasticGrey", "pocket", 0.70, 2, "MISC"),
]
LEANER = (0.050, "Prop_FabricTeal", "chrome", 0.85, 0, "OLD")
LEAN_DEG = 9.0
GAP = 0.004          # between upright binders (their yaw jitter is +/-0.5 deg)


def _xform(parts, m):
    for obj in parts:
        obj.matrix_basis = m @ obj.matrix_basis


def binder(kit, w, slot, label, fill, tabs, card, seed):
    """One binder in local space: spine on the -Y face, x centred, z from 0.
    Returns the parts so the caller can place / lean it."""
    first = len(kit.parts)
    rng = random.Random(seed)
    hw = w / 2
    y0 = -D / 2
    # Covers (board in vinyl or cloth), hinge creases pressed 13 mm in.
    for s in (-1, 1):
        kit.box((COVER_T, D - 0.004, H), (s * (hw - COVER_T / 2), 0.002, H / 2), slot, bevel=0.0012, segments=1, name="cover")
        kit.box((0.0008, 0.0035, H - 0.010), (s * (hw + 0.0002), y0 + 0.014, H / 2), slot, bevel=0.0, name="hinge crease")
        if slot != "Prop_FabricTeal":
            # RF-welded vinyl seam 4 mm in from the cover edge.
            kit.frame((D - 0.012, H - 0.008), (D - 0.020, H - 0.016), 0.0006, (s * (hw + 0.0001), 0.006, H / 2), slot,
                      bevel=0.0, rot=(0, 0, 90 * s), name="cover weld")
    # Spine panel and its rolled hinge edges.
    kit.box((w - 0.004, 0.0034, H), (0, y0 + 0.0017, H / 2), slot, bevel=0.0012, segments=1, name="spine")
    for s in (-1, 1):
        kit.cylinder(0.0026, H, (s * (hw - 0.0024), y0 + 0.0026, H / 2), slot, verts=12, bevel=0.0, name="spine hinge")
    # Page block leaning on the left cover, ring mechanism plate by the spine.
    inner = w - 2 * COVER_T - 0.001
    pw = inner * fill
    px = -hw + COVER_T + 0.0005 + pw / 2
    # Page block: punched letter sheets plus a few sheet protectors, which
    # are wider and taller, so they stand proud of the paper.
    bx = -hw + COVER_T + 0.0005
    sheets_w = pw * 0.72
    kit.box((sheets_w, 0.216 + 0.010, 0.279), (bx + sheets_w / 2, y0 + 0.024 + 0.113 + rng.uniform(-0.002, 0.002), 0.0045 + 0.1395),
            PAPER, bevel=0.0008, segments=1, name="punched sheets")
    prot_w = pw - sheets_w
    kit.box((prot_w * 0.95, 0.232, 0.284), (bx + sheets_w + prot_w / 2, y0 + 0.022 + 0.116, 0.0035 + 0.142),
            PAPER, bevel=0.0006, segments=1, name="sheet protectors")
    # D-ring mechanism on the inner (right) cover, booster lever on top.
    mx = hw - COVER_T - 0.0012
    kit.box((0.0016, 0.024, H * 0.80), (mx, y0 + 0.017, H / 2), CHROME, bevel=0.0, name="ring mechanism")
    kit.box((0.0055, 0.016, 0.009), (mx - 0.002, y0 + 0.017, H * 0.9 + 0.004), CHROME, bevel=0.001, segments=1, name="booster")
    # Index tabs: on dividers inside the punched sheets, standing 12 mm proud
    # of their fore-edge (y0 + 0.250) and 8 mm inside the covers' edge.
    for k in range(tabs):
        tz = 0.06 + k * 0.07 + rng.uniform(-0.01, 0.01)
        kit.box((0.0012, 0.014, 0.038), (bx + rng.uniform(0.15, 0.85) * sheets_w, y0 + 0.255, tz), TAB, bevel=0.0004, segments=1,
                name="index tab")
    # Spine label window, upper third.
    lz, lh = 0.205, 0.085
    lw = w - 0.016
    if label == "chrome":
        kit.frame((lw + 0.006, lh + 0.006), (lw, lh), 0.0012, (0, y0 - 0.0006, lz), CHROME, bevel=0.0004, segments=1,
                  name="label holder")
        for zz in (lz - lh / 2 - 0.0012, lz + lh / 2 + 0.0012):
            kit.cylinder(0.0014, 0.0016, (0, y0 - 0.0012, zz), CHROME, verts=6, rot=(90, 0, 0), bevel=0.0,
                         name="rivet")
    else:
        kit.frame((lw + 0.006, lh + 0.006), (lw, lh), 0.0010, (0, y0 - 0.0005, lz), slot, bevel=0.0,
                  name="label pocket weld")
    # Typed spine card, text running down the spine (US style).
    card_obj = labels.label(kit, card, lh, lw, (0, 0, -1), (1, 0, 0), name="spine label")
    card_obj.location = (0, y0 - 0.0003, lz)
    return kit.parts[first:]


def build(kit):
    rng = random.Random(4)
    x = 0.0
    placed = []
    for i, (w, slot, label, fill, tabs, card) in enumerate(ROW):
        parts = binder(kit, w, slot, label, fill, tabs, card, seed=10 + i)
        cx = x + w / 2
        yaw = rng.uniform(-0.5, 0.5)
        if i == len(ROW) - 1:
            yaw = 0.0                     # the leaner rests on this one's cover
        m = Matrix.Translation((cx, rng.uniform(-0.006, 0.006), 0)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
        placed.append((parts, m))
        x += w + GAP
    # The last binder has slipped over: it stands on its inner bottom edge
    # (the outer one lifted) with its top corner resting on the neighbour.
    w, slot, label, fill, tabs, card = LEANER
    t = math.radians(LEAN_DEG)
    row_end = x - GAP
    # 2.5 mm clears the two covers' weld seams and creases (0.6 mm each) at
    # the top contact, so the leaner touches without cutting in.
    pivot_x = row_end + H * math.sin(t) + 0.0025
    parts = binder(kit, w, slot, label, fill, tabs, card, seed=20)
    m = (Matrix.Translation((pivot_x, 0.004, 0)) @ Matrix.Rotation(-t, 4, "Y") @ Matrix.Translation((w / 2, 0, 0)))
    placed.append((parts, m))
    # Centre the row on x = 0.
    length = pivot_x + w * math.cos(t)
    shift = Matrix.Translation((-length / 2, 0, 0))
    for parts, m in placed:
        _xform(parts, shift @ m)

    kit.anchor("row_start", (-length / 2, -D / 2, 0))
    kit.tag("office", "desk_top")
    # Upright only: laid on its side the leaning binder would hang in the air.
    kit.pile("Small", states=["Upright"])
