"""Two-drawer oak nightstand, late 1970s (the orange-brown bedside chest
wedged on its side in A24 "Backrooms" Still A).

Real-world reference: mass-market American "colonial" oak nightstand: a
22 mm top with a rounded edge overhanging the case, two lipped drawer fronts
laid over the face (the lip throws a shadow line under flat top light), a
brass mushroom knob centred on each drawer, and a bracket-foot base: front
and side aprons cut away in a shallow arch between the feet. Hardboard back
set into the case.

Size: 0.50 m wide, 0.40 m deep, 0.60 m tall. Drawers face -Y.
Budget 900 tris LOD0 / 400 LOD1. Slots: WoodOak, Brass, Hardboard (back).
"""

import math
import random

NAME = "Kit_Nightstand2"
LOD1 = 0.44
SMOOTH_ANGLE = 40.0

OAK = "Prop_WoodOak"
BRASS = "Prop_Brass"
BACK = "Prop_Hardboard"

W, D, H = 0.50, 0.40, 0.60
TOP_T = 0.022
TOP_Z0 = H - TOP_T
BASE_H = 0.085                 # height of the bracket base
CX = 0.236                     # half width of the case
Y_FRONT = -0.183               # case front face
Y_BACK = 0.192                 # case back face
LIP = 0.019                    # drawer fronts stand this far proud of the case
GAP = 0.004                    # shut line between drawer fronts


def _bracket_outline(half, foot, rise, h, n=2, lo=None):
    """Apron outline (u along the board, v up): full height at the ends,
    cut away between the feet in a quarter-round sweep up to ``rise``."""
    lo = -half if lo is None else lo
    pts = [(lo, 0.0), (-half + foot, 0.0)]
    r = rise
    for i in range(1, n + 1):
        a = math.pi / 2 * i / n
        pts.append((-half + foot + r * math.sin(a), r * (1 - math.cos(a))))
    for i in range(n + 1):
        a = math.pi / 2 * (1 - i / n)
        pts.append((half - foot - r * math.sin(a), r * (1 - math.cos(a))))
    pts += [(half, 0.0), (half, h), (lo, h)]
    return pts


def _knob(kit, x, y, z):
    """Brass mushroom knob (28 mm) on a small collar, axis toward -Y."""
    prof = [(0.0090, 0.0), (0.0050, 0.007), (0.0090, 0.0145),
            (0.0150, 0.0205), (0.0118, 0.0255), (0.0, 0.0270)]
    kit.lathe(prof, (x, y, z), BRASS, verts=8, rot=(90, 0, 0), name="knob")


def build(kit):
    rng = random.Random(5120)
    case_h = TOP_Z0 - BASE_H
    # Case: one block (sides, face and bottom share the oak skin); the lipped
    # drawer fronts cover its face, the back is a hardboard panel set in.
    kit.box((2 * CX, Y_BACK - Y_FRONT, case_h), (0, (Y_FRONT + Y_BACK) / 2, BASE_H + case_h / 2), OAK,
            bevel=0.003, segments=1, name="case")
    kit.quad(2 * CX - 0.026, case_h - 0.024, (0, Y_BACK + 0.0006, BASE_H + case_h / 2), BACK,
             facing="+y", uv="metres", name="back panel")

    # Top: rounded front and side edges, 15 mm front overhang.
    ty0, ty1 = Y_FRONT - 0.015, Y_BACK + 0.003
    kit.box((W, ty1 - ty0, TOP_T), (0, (ty0 + ty1) / 2, TOP_Z0 + TOP_T / 2), OAK,
            bevel=0.008, segments=2, name="top")

    # Bracket base: front and side aprons, a plain rail at the back.
    ab = 0.019
    front = _bracket_outline(CX + 0.004, 0.065, 0.040, BASE_H)
    aprons = [kit.extrude(front, ab, (0, Y_FRONT + ab / 2 - 0.004, 0), OAK, plane="xz", bevel=0.003,
                          segments=1, name="front apron")]
    # Side aprons: same bracket profile, butted behind the front apron (the
    # foot is measured from the front apron's face so both feet match).
    yf, yb = Y_FRONT - 0.004, Y_BACK - 0.002
    side_half = (yb - yf) / 2
    yc = (yf + yb) / 2
    side = _bracket_outline(side_half, 0.065, 0.040, BASE_H, lo=-side_half + ab - 0.001)
    for sx in (-1, 1):
        aprons.append(kit.extrude(side, ab, (sx * (CX + 0.004 - ab / 2), yc, 0), OAK, plane="yz",
                                  bevel=0.003, segments=1, name="side apron"))
    # The 45-degree arch facets stay unbevelled (only the board's faces are eased).
    for obj in aprons:
        obj.modifiers["bevel"].angle_limit = math.radians(50)
    kit.box((2 * CX - 0.04, 0.018, BASE_H - 0.01), (0, Y_BACK - 0.03, (BASE_H - 0.01) / 2 + 0.01), OAK,
            bevel=0.002, segments=1, name="back rail")

    # Lipped drawer fronts (shallow top drawer, deeper bottom one).
    zb, zt = BASE_H + 0.012, TOP_Z0 - 0.012
    span = zt - zb - GAP
    hs = (span * 0.44, span * 0.56)               # top, bottom
    z_top_c = zt - hs[0] / 2
    z_bot_c = zb + hs[1] / 2
    fw = 2 * CX - 0.012
    for zc, h in ((z_top_c, hs[0]), (z_bot_c, hs[1])):
        kit.box((fw, LIP, h), (0, Y_FRONT - LIP / 2 + 0.001, zc), OAK, bevel=0.0055, segments=2,
                name="drawer front")
        _knob(kit, 0, Y_FRONT - LIP + 0.001, zc + 0.006)

    for obj in kit.parts:
        obj["fr_uv_offset"] = (round(rng.uniform(0, 0.6), 3), round(rng.uniform(0, 1.0), 3))

    # --- Metadata -------------------------------------------------------
    kit.support("top", (0, (ty0 + ty1) / 2, H), (W - 0.03, ty1 - ty0 - 0.03))
    kit.anchor("top", (0, (ty0 + ty1) / 2, H))
    kit.collider((0, (ty0 + ty1) / 2 - 0.002, H / 2), (W, ty1 - ty0 + 0.006, H))
    kit.tag("domestic", "case_goods", "pile", "pile_piece")
    kit.pile("Case", mass=1, states=["Upright", "Side", "Inverted"], palette="domestic70s")
