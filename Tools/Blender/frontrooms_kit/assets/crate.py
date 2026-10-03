"""Cleated plywood shipping crate on skids (the stencilled crate sitting on a
pallet at the base of the tall pile in A24 "Backrooms" Still B).

Real-world reference: light export crate, 12 mm sheathing plywood nailed to a
pine cleat frame on every face (perimeter cleats, a mid cleat on the back and
on the lid), two chamfered pine skids underneath for forklift tines, nail
heads along every cleat, black spray stencils: FRAGILE on the front, the
ISO 780 "this way up" arrows on the right end and the back, KEEP DRY on the
left end. The grab cleats bridge the two vertical cleats of each end and are
nailed into them.

Budget pass (2026-10-02, §5.3: 1.00 x 0.80 x 0.75 m, 600 LOD0 / 250 LOD1,
Crate 2; U, S, one collider; live ~700 / ~290, 1.16x):
* slots: Prop_Plywood, Prop_PinePallet (cleats, skids), Prop_SteelBlack
  (nail heads), Prop_StencilBlack (alpha-clipped spray stencil atlas, quads
  0.7 mm off the plywood). The packing-list pouch is gone (5th slot).
* cleats are 6-sided extrusions (20 tris): the two outer long edges carry a
  4 mm chamfer that catches the light, the ends and the face against the
  plywood stay square (butt joints, as nailed up). Nail heads are 7 mm quads.
* +X / +Y facing decals are mapped with U swapped so they read correctly.
* fix pass: _pilecases_grain.install transposes the Plywood / PinePallet UVs
  (both albedos have their grain on U), snaps every cleat and skid into one
  plank of the Planks021 sheet with no painted nail dot on cleats under
  0.7 m, keeps LOD1's sharp edges and alpha-clips the stencils in the
  preview stills. TODO when Prop_Atlas exists: move the stencil cells into
  it and drop Prop_StencilBlack (URP/Lit alpha test, a second shader).

Size: 1.00 m wide over the grab cleats (0.96 m body), 0.80 m deep, 0.75 m
tall (skids 60 mm, cleats 20 x 80 mm). Front (FRAGILE) faces -Y.
Grain follows each cleat (kitlib), each cleat on its own patch.
"""

import math

import _pilecases_grain as grain

NAME = "Kit_Crate"
LOD1 = 0.42

PLY = "Prop_Plywood"
PINE = "Prop_PinePallet"
NAIL = "Prop_SteelBlack"
STENCIL = "Prop_StencilBlack"

W, D, H = 1.00, 0.80, 0.75
SKID_H = 0.060
T = 0.020                       # cleat thickness
B = 0.080                       # cleat width
CH = 0.004                      # chamfer on a cleat's outer long edges
GRAB = 0.020                    # grab cleats stand proud of the end faces
WB = W - 2 * GRAB               # body width over the cleats (0.96)
CX, CY = WB / 2 - T, D / 2 - T  # plywood box half sizes (0.46, 0.38)
Z0, Z1 = SKID_H, H - T          # plywood box bottom / top (0.06, 0.73)
NAIL_STEP = 0.25

# Prop_StencilBlack atlas (1024 x 512): FRAGILE + glass (0, .5, 1, 1), its
# bottom rows catch the top of the KEEP DRY umbrella, so it is cropped to
# v .56 - .98; THIS SIDE UP (0, 0, .5, .5) with the art in its left 76 %;
# KEEP DRY (.5, 0, 1, .5) with the art in u .60 - .88.
UV_FRAGILE = (0.02, 0.56, 0.92, 0.98)      # 4.29 : 1
UV_SIDE_UP = (0.0, 0.0, 0.38, 0.5)         # 1.52 : 1
UV_KEEP_DRY = (0.60, 0.0, 0.88, 0.5)       # 1.12 : 1


def _mirror(rect):
    """For a +X / +Y facing decal: kitlib maps those seen from behind."""
    u0, v0, u1, v1 = rect
    return (u1, v0, u0, v1)


_PLANE = {"z": "xy", "x": "yz", "y": "xz"}
_PLANE_AXES = {"xy": ("x", "y"), "yz": ("y", "z"), "xz": ("x", "z")}


def _cleat(kit, axis, outward, length, width, centre, slot=PINE, name="cleat", thick=T):
    """A board of `thick` x `width` running along `axis`, lying on a face whose
    outward normal is `outward` ('+x', '-y', '+z', ...): the two long edges
    away from the face are chamfered, everything else is square."""
    plane = _PLANE[axis]
    u_ax, v_ax = _PLANE_AXES[plane]
    n_ax, s = outward[1], (1 if outward[0] == "+" else -1)
    w, t, c = width / 2, thick / 2, CH
    bn = [(-w, -s * t), (w, -s * t), (w, s * (t - c)), (w - c, s * t), (-w + c, s * t), (-w, s * (t - c))]
    outline = [(b, n) if v_ax == n_ax else (n, b) for b, n in bn]
    obj = kit.extrude(outline, length, centre, slot, plane=plane, bevel=0.0, name=name)
    obj["fr_grain"] = axis
    obj["fr_face"] = tuple(float(s) if a == n_ax else 0.0 for a in "xyz")    # plank-snap the outer face
    return obj


def _nail(kit, pos, normal, k):
    q = kit.quad(0.007, 0.007, pos, NAIL, facing=normal, uv="metres", name="nail head")
    a = math.radians((k * 37) % 90)
    q.rotation_euler = {"-y": (0, a, 0), "+y": (0, a, 0), "-x": (a, 0, 0), "+x": (a, 0, 0), "+z": (0, 0, a)}[normal]


def _nails_along(kit, a, b, fixed, axis, normal, step=NAIL_STEP, inset=0.04):
    """A row of nail heads from a to b along `axis`, on a face whose outward
    normal is `normal` ('-y', '+y', '-x', '+x', '+z') at coordinate `fixed`."""
    length = b - a - 2 * inset
    n = max(2, int(round(length / step)) + 1)
    seed = int(abs(a * 1000 + b * 37 + fixed[0] * 53 + fixed[1] * 91)) % 997
    for i in range(n):
        # hand-nailed: spacing and line wander a few millimetres
        j = ((seed * (i + 3) * 7919) % 1000) / 1000.0 - 0.5
        t = a + inset + length * i / (n - 1) + j * 0.010
        off = j * 0.008
        sgn = -1 if normal[0] == "-" else 1
        f = fixed[0] + sgn * 0.0004
        if normal in ("-y", "+y"):
            x, z = (t, fixed[1] + off) if axis == "x" else (fixed[1] + off, t)
            pos = (x, f, z)
        elif normal in ("-x", "+x"):
            y, z = (t, fixed[1] + off) if axis == "y" else (fixed[1] + off, t)
            pos = (f, y, z)
        else:
            x, y = (t, fixed[1] + off) if axis == "x" else (fixed[1] + off, t)
            pos = (x, y, f)
        _nail(kit, pos, normal, seed + i)


def _end_face(kit, sy, mid_cleat):
    """Front (sy=-1) or back (sy=+1) face: cleats cover the full width."""
    y = sy * (CY + T / 2)
    yo = sy * (CY + T)                         # outer face of the cleats
    nrm = "-y" if sy < 0 else "+y"
    hz = Z1 - Z0
    for sx in (-1, 1):
        x = sx * (WB / 2 - B / 2)
        _cleat(kit, "z", nrm, hz, B, (x, y, Z0 + hz / 2), name="end cleat vertical")
        _nails_along(kit, Z0, Z1, (yo, x), "z", nrm)
    inner = WB - 2 * B
    for zc in (Z0 + B / 2, Z1 - B / 2):
        _cleat(kit, "x", nrm, inner, B, (0, y, zc), name="end cleat horizontal")
        _nails_along(kit, -inner / 2, inner / 2, (yo, zc), "x", nrm, inset=0.05)
    if mid_cleat:
        mh = hz - 2 * B
        _cleat(kit, "z", nrm, mh, B, (0, y, Z0 + hz / 2), name="end cleat mid")
        _nails_along(kit, Z0 + B, Z1 - B, (yo, 0.0), "z", nrm, inset=0.05)


def _side_face(kit, sx):
    """Left/right end: cleats fit between the front and back cleats."""
    x = sx * (CX + T / 2)
    xo = sx * (CX + T)
    nrm = "-x" if sx < 0 else "+x"
    hz = Z1 - Z0
    for sy in (-1, 1):
        y = sy * (CY - B / 2)
        _cleat(kit, "z", nrm, hz, B, (x, y, Z0 + hz / 2), name="side cleat vertical")
        _nails_along(kit, Z0, Z1, (xo, y), "z", nrm)
    inner = 2 * CY - 2 * B
    for zc in (Z0 + B / 2, Z1 - B / 2):
        _cleat(kit, "y", nrm, inner, B, (x, 0, zc), name="side cleat horizontal")
        _nails_along(kit, -inner / 2, inner / 2, (xo, zc), "y", nrm, inset=0.05)
    # Grab cleat: an extra batten over the end that the crate is lifted by,
    # spanning the full 0.76 m so its ends bear on both vertical cleats, and
    # nailed through into them (one nail at each end).
    gz = Z0 + (Z1 - Z0) * 0.80
    _cleat(kit, "y", nrm, 2 * CY, 0.050, (x + sx * T, 0, gz), name="grab cleat")
    for k, ny in enumerate((-(CY - B / 2), CY - B / 2)):
        _nail(kit, (sx * (CX + 2 * T + 0.0004), ny + (0.006 if k else -0.004), gz + 0.003 * sx), nrm, 11 + k)


def build(kit):
    # Plywood carcass (sheathing on all six sides, edges hidden by cleats).
    kit.box((2 * CX, 2 * CY, Z1 - Z0), (0, 0, (Z0 + Z1) / 2), PLY, bevel=0.0, name="plywood box")

    _end_face(kit, -1, mid_cleat=False)
    _end_face(kit, +1, mid_cleat=True)
    _side_face(kit, -1)
    _side_face(kit, +1)

    # Lid cleats: long ones over the full length, short ones between them, a
    # mid stiffener across the lid.
    zt = Z1 + T / 2
    for sy in (-1, 1):
        y = sy * (D / 2 - B / 2)
        _cleat(kit, "x", "+z", WB, B, (0, y, zt), name="lid cleat long")
        _nails_along(kit, -WB / 2, WB / 2, (H, y), "x", "+z")
    inner = D - 2 * B
    for xc in (-(WB / 2 - B / 2), 0.0, WB / 2 - B / 2):
        _cleat(kit, "y", "+z", inner, B, (xc, 0, zt), name="lid cleat short")
        _nails_along(kit, -inner / 2, inner / 2, (H, xc), "y", "+z", inset=0.05)

    # Skids: two 90 mm runners along X with chamfered ends, nailed up into
    # the floor of the crate.
    ch = 0.030
    outline = [(-WB / 2 + ch, 0.0), (WB / 2 - ch, 0.0), (WB / 2, ch * 0.8), (WB / 2, SKID_H), (-WB / 2, SKID_H),
               (-WB / 2, ch * 0.8)]
    for sy in (-1, 1):
        sk = kit.extrude(outline, 0.090, (0, sy * 0.265, 0.0), PINE, plane="xz", bevel=0.0, name="skid")
        sk["fr_grain"] = "x"
        sk["fr_face"] = (0.0, float(sy), 0.0)

    # Spray stencils (Prop_StencilBlack, alpha-clipped), 0.7 mm off the
    # plywood inside the cleat frames.
    zf = Z0 + (Z1 - Z0) * 0.55
    kit.quad(0.74, 0.1725, (0.0, -CY - 0.0007, zf), STENCIL, facing="-y", uv_rect=UV_FRAGILE, name="stencil fragile")
    kit.quad(0.38, 0.25, (CX + 0.0007, 0.0, Z0 + (Z1 - Z0) * 0.40), STENCIL, facing="+x",
             uv_rect=_mirror(UV_SIDE_UP), name="stencil this side up")
    kit.quad(0.27, 0.24, (-CX - 0.0007, -0.02, Z0 + (Z1 - Z0) * 0.42), STENCIL, facing="-x",
             uv_rect=UV_KEEP_DRY, name="stencil keep dry")
    kit.quad(0.30, 0.197, (-0.20, CY + 0.0007, Z0 + (Z1 - Z0) * 0.58), STENCIL, facing="+y",
             uv_rect=_mirror(UV_SIDE_UP), name="stencil this side up back")

    # --- Metadata --------------------------------------------------------
    kit.support("lid", (0, 0, H), (WB - 0.02, D - 0.02))
    kit.anchor("lid", (0, 0, H))
    kit.collider((0, 0, H / 2), (W, D, H))
    kit.tag("storage", "crate", "pile", "pile_piece")
    kit.pile("Crate", mass=2, palette="storage", states=["Upright", "Side"])

    # Each cleat / sheet on its own patch of the (seamless) textures:
    # PinePallet TileSize 1.4 m, Plywood 0.5 m. Grain direction: kitlib.
    grain.scatter_offsets(kit, seed=9013, slots=(PINE,), tile=(1.4, 1.4))
    grain.scatter_offsets(kit, seed=9014, slots=(PLY,), tile=(0.5, 0.5))
    grain.install(kit, 35.0, planks={PINE: grain.PINE_PLANKS})
