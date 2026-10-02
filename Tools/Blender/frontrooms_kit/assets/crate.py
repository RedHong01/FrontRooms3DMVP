"""Cleated plywood shipping crate on skids (the stencilled crate sitting on a
pallet at the base of the tall pile in A24 "Backrooms" Still B).

Real-world reference: light export crate, 12 mm sheathing plywood nailed to a
pine cleat frame on every face (perimeter cleats, a mid cleat on the back and
on the lid), two chamfered pine skids underneath for forklift tines, nail
heads along every cleat, a black spray-stencilled "FRAGILE" on the front and
the ISO 780 "this way up" arrows on the right end, a packing-list pouch on
the left end. The grab cleats bridge the two vertical cleats of each end and
are nailed into them.

Stencils: until a Prop_StencilBlack decal slot exists (alpha-clipped black
spray stencil, FRAGILE + glass icon 1024x256 and THIS SIDE UP arrows 512x512,
no white field) they are modelled as thin matte-black military-stencil
glyphs (Prop_Rubber), 0.7 mm proud of the plywood; delete the 'stencil'
parts when the decal lands.
Grain follows each cleat (_pilecases_grain), each on its own patch.

Size: 0.90 m wide over the grab cleats (0.86 m body), 0.60 m deep, 0.70 m tall
(skids 60 mm, cleats 20 x 70 mm).
Front (main stencil) faces -Y.
"""

import _pilecases_grain as grain

NAME = "Kit_Crate"

PLY = "Prop_Plywood"
PINE = "Prop_PinePallet"
NAIL = "Prop_SteelBlack"
PAINT = "Prop_Rubber"           # matte black stand-in for stencil paint

W, D, H = 0.90, 0.60, 0.70
SKID_H = 0.060
T = 0.020                       # cleat thickness
B = 0.070                       # cleat width
GRAB = 0.020                    # grab cleats stand proud of the end faces
WB = W - 2 * GRAB               # body width over the cleats (0.86)
CX, CY = WB / 2 - T, D / 2 - T  # plywood box half sizes (0.41, 0.28)
Z0, Z1 = SKID_H, H - T          # plywood box bottom / top (0.06, 0.68)


def _nails_along(kit, a, b, fixed, axis, normal, step=0.15, inset=0.035):
    """A row of nail heads from a to b along `axis`, on a face whose outward
    normal is `normal` ('-y', '+y', '-x', '+x', '+z') at coordinate `fixed`."""
    length = b - a - 2 * inset
    n = max(2, int(round(length / step)) + 1)
    seed = int(abs(a * 1000 + b * 37 + fixed[0] * 53 + fixed[1] * 91)) % 997
    for i in range(n):
        # hand-nailed: spacing and line wander a few millimetres
        j = ((seed * (i + 3) * 7919) % 1000) / 1000.0 - 0.5
        t = a + inset + length * i / (n - 1) + j * 0.010
        fixed_off = j * 0.008
        if normal in ("-y", "+y"):
            sgn = -1 if normal == "-y" else 1
            x, z = (t, fixed[1] + fixed_off) if axis == "x" else (fixed[1] + fixed_off, t)
            kit.cylinder(0.0033, 0.0014, (x, fixed[0] + sgn * 0.0004, z), NAIL, verts=8, rot=(90, 0, 0),
                         bevel=0.0, name="nail head")
        elif normal in ("-x", "+x"):
            sgn = -1 if normal == "-x" else 1
            y, z = (t, fixed[1] + fixed_off) if axis == "y" else (fixed[1] + fixed_off, t)
            kit.cylinder(0.0033, 0.0014, (fixed[0] + sgn * 0.0004, y, z), NAIL, verts=8, rot=(0, 90, 0),
                         bevel=0.0, name="nail head")
        else:
            x, y = (t, fixed[1] + fixed_off) if axis == "x" else (fixed[1] + fixed_off, t)
            kit.cylinder(0.0033, 0.0014, (x, y, fixed[0] + 0.0004), NAIL, verts=8, bevel=0.0, name="nail head")


def _end_face(kit, sy, mid_cleat):
    """Front (sy=-1) or back (sy=+1) face: cleats cover the full width."""
    y = sy * (CY + T / 2)
    yo = sy * (CY + T)                         # outer face of the cleats
    nrm = "-y" if sy < 0 else "+y"
    hz = Z1 - Z0
    for sx in (-1, 1):
        x = sx * (WB / 2 - B / 2)
        kit.box((B, T, hz), (x, y, Z0 + hz / 2), PINE, bevel=0.003, segments=1, name="end cleat vertical")
        _nails_along(kit, Z0, Z1, (yo, x), "z", nrm)
    inner = WB - 2 * B
    for zc in (Z0 + B / 2, Z1 - B / 2):
        kit.box((inner, T, B), (0, y, zc), PINE, bevel=0.003, segments=1, name="end cleat horizontal")
        _nails_along(kit, -inner / 2, inner / 2, (yo, zc), "x", nrm, inset=0.05)
    if mid_cleat:
        mh = hz - 2 * B
        kit.box((B, T, mh), (0, y, Z0 + hz / 2), PINE, bevel=0.003, segments=1, name="end cleat mid")
        _nails_along(kit, Z0 + B, Z1 - B, (yo, 0.0), "z", nrm, inset=0.05)


def _side_face(kit, sx):
    """Left/right end: cleats fit between the front and back cleats."""
    x = sx * (CX + T / 2)
    xo = sx * (CX + T)
    nrm = "-x" if sx < 0 else "+x"
    hz = Z1 - Z0
    for sy in (-1, 1):
        y = sy * (CY - B / 2)
        kit.box((T, B, hz), (x, y, Z0 + hz / 2), PINE, bevel=0.003, segments=1, name="side cleat vertical")
        _nails_along(kit, Z0, Z1, (xo, y), "z", nrm)
    inner = 2 * CY - 2 * B
    for zc in (Z0 + B / 2, Z1 - B / 2):
        kit.box((T, inner, B), (x, 0, zc), PINE, bevel=0.003, segments=1, name="side cleat horizontal")
        _nails_along(kit, -inner / 2, inner / 2, (xo, zc), "y", nrm, inset=0.05)
    # Grab cleat: an extra batten nailed over the end, bottom edge eased,
    # that the crate is lifted by.
    # It spans the full 0.56 m so its ends bear on both vertical cleats, and
    # is nailed through into them (two nails at each end).
    gz = Z0 + (Z1 - Z0) * 0.80
    kit.box((T, 2 * CY, 0.050), (x + sx * T, 0, gz), PINE, bevel=0.005, segments=2, name="grab cleat")
    for ny in (-(CY - B / 2), CY - B / 2):
        for k, nz in enumerate((gz - 0.012, gz + 0.011)):
            kit.cylinder(0.0033, 0.0014, (sx * (CX + 2 * T + 0.0004), ny + (0.006 if k else -0.004), nz), NAIL,
                         verts=8, rot=(0, 90, 0), bevel=0.0, name="nail head")


# --- Stencil glyphs ------------------------------------------------------
# Military-stencil letters on a 10-unit cap height: strokes 2 units, the
# pieces separated by 0.6-unit bridges as a cut stencil leaves them.
def _rect(x0, z0, x1, z1):
    return [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]


_S, _G = 2.0, 0.6
GLYPHS = {
    "F": (6.0, [_rect(0, 0, _S, 10), _rect(_S + _G, 10 - _S, 6.0, 10), _rect(_S + _G, 4.2, 5.0, 4.2 + _S)]),
    "R": (6.4, [_rect(0, 0, _S, 10),
                [(_S + _G, 10), (4.9, 10), (6.2, 8.7), (6.2, 5.9), (4.9, 4.6), (_S + _G, 4.6), (_S + _G, 6.4),
                 (4.1, 6.4), (4.4, 6.7), (4.4, 7.9), (4.1, 8.2), (_S + _G, 8.2)],
                [(3.0, 4.0), (5.0, 4.0), (6.4, 0), (4.3, 0)]]),
    "A": (6.4, [[(0, 0), (2.0, 0), (3.0, 10), (1.5, 10)], [(6.4, 0), (4.4, 0), (3.4, 10), (4.9, 10)],
                [(2.24, 2.4), (4.16, 2.4), (3.98, 4.2), (2.42, 4.2)]]),
    "G": (6.2, [[(5.9, 10), (1.2, 10), (0, 8.8), (0, 1.2), (1.2, 0), (4.8, 0), (6.0, 1.2), (6.0, 4.8), (4.2, 4.8),
                 (4.2, 1.8), (1.8, 1.8), (1.8, 8.2), (5.9, 8.2)],
                _rect(2.8, 5.4, 6.0, 7.0)]),
    "I": (2.0, [_rect(0, 0, _S, 10)]),
    "L": (5.6, [_rect(0, 0, _S, 10), _rect(_S + _G, 0, 5.6, _S)]),
    "E": (5.8, [_rect(0, 0, _S, 10), _rect(_S + _G, 10 - _S, 5.8, 10), _rect(_S + _G, 4.1, 5.2, 4.1 + _S),
                _rect(_S + _G, 0, 5.8, _S)]),
}
# ISO 780 "this way up": two arrows over a bar (units, centred on x = 0).
_ARROW = [(-0.55, 0), (0.55, 0), (0.55, 3.6), (1.6, 3.6), (0, 6.2), (-1.6, 3.6), (-0.55, 3.6)]
WAY_UP = [[(x + 1.9, z) for x, z in _ARROW], [(x - 1.9, z) for x, z in _ARROW], _rect(-3.6, -1.7, 3.6, -0.7)]


def _stencil(kit, pieces, unit, origin, face):
    """Extrude glyph pieces 0.6 mm thick, front face 0.7 mm proud of a crate face.
    face '-y': outline (u, v) -> world (x, z) on the front; '+x': -> (y, z) on the right end."""
    ox, oy, oz = origin
    for outline in pieces:
        pts = [(u * unit, v * unit) for u, v in outline]
        if face == "-y":
            kit.extrude(pts, 0.0006, (ox, oy - 0.0004, oz), PAINT, plane="xz", bevel=0.0, name="stencil paint")
        else:
            kit.extrude(pts, 0.0006, (ox + 0.0004, oy, oz), PAINT, plane="yz", bevel=0.0, name="stencil paint")


def _stencil_word(kit, word, height, centre, face, track=1.2):
    unit = height / 10.0
    width = sum(GLYPHS[c][0] for c in word) + track * (len(word) - 1)
    cx, cy, cz = centre
    u0 = -width / 2
    for c in word:
        adv, pieces = GLYPHS[c]
        org = (cx + u0 * unit, cy, cz - height / 2) if face == "-y" else (cx, cy + u0 * unit, cz - height / 2)
        _stencil(kit, pieces, unit, org, face)
        u0 += adv + track



def build(kit):
    # Plywood carcass (sheathing on all six sides, edges hidden by cleats).
    kit.box((2 * CX, 2 * CY, Z1 - Z0), (0, 0, (Z0 + Z1) / 2), PLY, bevel=0.002, segments=1, name="plywood box")

    _end_face(kit, -1, mid_cleat=False)
    _end_face(kit, +1, mid_cleat=True)
    _side_face(kit, -1)
    _side_face(kit, +1)

    # Lid cleats: long ones over the full length, short ones between them, a
    # mid stiffener across the lid.
    zt = Z1 + T / 2
    for sy in (-1, 1):
        y = sy * (D / 2 - B / 2)
        kit.box((WB, B, T), (0, y, zt), PINE, bevel=0.003, segments=1, name="lid cleat long")
        _nails_along(kit, -WB / 2, WB / 2, (H, y), "x", "+z")
    inner = D - 2 * B
    for xc in (-(WB / 2 - B / 2), 0.0, WB / 2 - B / 2):
        kit.box((B, inner, T), (xc, 0, zt), PINE, bevel=0.003, segments=1, name="lid cleat short")
        _nails_along(kit, -inner / 2, inner / 2, (H, xc), "y", "+z", inset=0.05)

    # Skids: two runners along X with chamfered ends, nailed up into the floor.
    ch = 0.030
    outline = [(-WB / 2 + ch, 0.0), (WB / 2 - ch, 0.0), (WB / 2, ch * 0.8), (WB / 2, SKID_H), (-WB / 2, SKID_H), (-WB / 2, ch * 0.8)]
    for sy in (-1, 1):
        kit.extrude(outline, 0.075, (0, sy * 0.195, 0.0), PINE, plane="xz", bevel=0.003, segments=1, name="skid")

    # Stencils: FRAGILE across the front panel, ISO "this way up" arrows on
    # the right end below the grab cleat (geometry stand-ins, see docstring).
    _stencil_word(kit, "FRAGILE", 0.115, (0, -CY, Z0 + (Z1 - Z0) * 0.56), "-y")
    _stencil(kit, WAY_UP, 0.021, (CX, 0, Z0 + (Z1 - Z0) * 0.40), "+x")
    # Packing-list pouch stapled to the left end.
    kit.box((0.003, 0.17, 0.22), (-CX - 0.0015, 0.02, Z0 + (Z1 - Z0) * 0.5), "Prop_Paper", bevel=0.001, name="packing list pouch")

    # --- Metadata --------------------------------------------------------
    kit.support("lid", (0, 0, H), (WB - 0.02, D - 0.02))
    kit.anchor("lid", (0, 0, H))
    kit.collider((0, 0, SKID_H + (H - SKID_H) / 2), (W, D, H - SKID_H))
    kit.collider((0, 0, SKID_H / 2), (WB, 0.47, SKID_H))
    kit.tag("storage", "crate", "pile", "pile_piece")
    kit.pile("Crate", mass=2, palette="storage", states=["Upright", "Side", "Back"])

    # Grain along every cleat and skid, each on its own patch; parts longer
    # than a tile put their seam on the centre line (under the mid lid cleat).
    grain.scatter_offsets(kit, seed=9013, slots=(PINE,), tile=(0.4, 0.8), seam_at=0.0)
    grain.scatter_offsets(kit, seed=9014, slots=(PLY,), tile=(0.5, 1.0), seam_at=0.0)
    grain.install(kit)
