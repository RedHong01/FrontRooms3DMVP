"""Golden-oak open bookcase, c. 1978-90 (the bookcase lying on its side in
the tall pile of A24 "Backrooms" Still B).

Real-world reference: mass-market solid-oak / oak-veneer bookcase: 19 mm
sides running to the floor with eased front edges, a 22 mm top overhanging
15 mm on three sides with a thumbnail edge and a small cove moulding under
it, four adjustable shelves set back 10 mm on pins, a fixed bottom shelf over
an arched front apron, and a 6 mm particleboard back nailed into rabbets
(raw both faces) with the maker's paper label.

Size: 0.90 m wide (top), 0.30 m deep, 1.80 m tall; five 32 cm openings.
Front (open shelves) looks -Y. Grain runs along each board (kitlib fr_grain).
"""

import math
import random

import _newcase as nc

NAME = "Kit_Bookcase"
LOD1 = 0.45
SMOOTH_ANGLE = 40.0

OAK = "Prop_WoodOak"
BACK = "Prop_Chipboard"

W, D, H = 0.90, 0.30, 1.80
TOP_T = 0.024
OVER = 0.018                    # top overhang (front and sides)
CX = W / 2 - OVER               # carcass outer half-width 0.435
YF = -D / 2 + OVER              # carcass front -0.135
YB = D / 2                      # back face 0.15
ST = 0.019                      # side / shelf thickness
XI = CX - ST                    # inner face of the sides 0.416
TOP_Z0 = H - TOP_T              # underside of the top 1.778
COVE_H = 0.020
BOT_Z = 0.075                   # underside of the fixed bottom shelf
BACK_T = 0.006
BACK_Y = YB - BACK_T            # inner face of the back 0.144


def _side(kit, sx):
    """Side panel: profile (Y, Z) with an arched cut-out between the front
    and back feet, run 19 mm along X; kitlib bevels its arrises 2 mm."""
    foot = 0.050
    y0, y1 = YF + foot, YB - foot
    mid, hw, rise = (y0 + y1) / 2, (y1 - y0) / 2, 0.052
    arch = [(mid + hw * math.cos(math.pi * k / 8), rise * math.sin(math.pi * k / 8)) for k in range(9)]
    outline = [(YF, 0.0)] + list(reversed(arch)) + [(YB, 0.0), (YB, TOP_Z0), (YF, TOP_Z0)]
    obj = kit.extrude(outline, ST, (sx * (CX - ST / 2), 0, 0), OAK, plane="yz", bevel=0.002, segments=1,
                      name="side")
    obj["fr_grain"] = "z"
    nc.tri(obj)
    return obj


def _shelf(kit, z0, y0, x_half, t=ST, name="shelf"):
    """Shelf board: YZ section (front arrises chamfered) run along X."""
    c = 0.0025
    y1 = BACK_Y - 0.002
    outline = [(y1, z0), (y0 + c, z0), (y0, z0 + c), (y0, z0 + t - c), (y0 + c, z0 + t), (y1, z0 + t)]
    obj = kit.extrude(outline, 2 * x_half, (0, 0, 0), OAK, plane="yz", bevel=0.0, name=name)
    obj["fr_grain"] = "x"
    return obj


def build(kit):
    rng = random.Random(4471)
    # --- Carcass -----------------------------------------------------------
    _side(kit, -1)
    _side(kit, 1)
    # Top: thumbnail edge on all four sides of its upper face.
    nc.plate(kit, W, D, [(0, 0), (0, 0.010), (0.0035, 0.0175), (0.008, 0.0208), (0.013, TOP_T)],
             (0, 0, TOP_Z0), OAK, facing="+z", name="top", grain="x")
    # Cove moulding under the overhang, round the front and both sides.
    nc.sweep(kit, nc.three_sides(CX, YF, YB), nc.cove(OVER - 0.001, COVE_H, n=3), OAK, facing="+z",
             origin=(0, 0, TOP_Z0 - COVE_H), name="cove moulding")
    # Fixed bottom shelf and the arched apron below it.
    _shelf(kit, BOT_Z, YF, XI, name="bottom shelf")
    arch = []
    n = 8
    for k in range(n + 1):
        t = k / n
        x = -0.34 + 0.68 * t
        arch.append((x, 0.016 + 0.030 * (1 - (2 * t - 1) ** 2) ** 0.8))
    outline = [(-XI, 0.004), (-0.38, 0.004)] + arch + [(0.38, 0.004), (XI, 0.004), (XI, BOT_Z), (-XI, BOT_Z)]
    ap = kit.extrude(outline, 0.019, (0, YF + 0.0095 + 0.004, 0), OAK, plane="xz", bevel=0.0, name="apron")
    ap["fr_grain"] = "x"
    nc.tri(ap)
    # Raw particleboard back in rabbets, floor to top.
    kit.box((2 * XI + 0.018, BACK_T, TOP_Z0 - 0.002), (0, YB - 0.0005 - BACK_T / 2, (TOP_Z0 - 0.002) / 2), BACK,
            bevel=0.0, name="back panel")
    nc.label(kit, *nc.MAKER_LABEL, 0.105, 0.084, (-0.21, YB - 0.0001, 1.52), facing="+y", name="maker label")
    # Arched valance under the top, matching the apron (frames the top opening).
    val_h = 0.058
    arch_top = []
    for k in range(n + 1):
        t = k / n
        arch_top.append((0.34 - 0.68 * t, TOP_Z0 - 0.050 + 0.030 * (1 - (2 * t - 1) ** 2) ** 0.8))
    outline = [(-XI, TOP_Z0 - val_h), (-0.38, TOP_Z0 - val_h)] + \
        list(reversed(arch_top)) + [(0.38, TOP_Z0 - val_h), (XI, TOP_Z0 - val_h), (XI, TOP_Z0), (-XI, TOP_Z0)]
    va = kit.extrude(outline, 0.019, (0, YF + 0.0095 + 0.004, 0), OAK, plane="xz", bevel=0.0, name="valance")
    va["fr_grain"] = "x"
    nc.tri(va)

    # --- Shelves ------------------------------------------------------------
    open_h = (TOP_Z0 - (BOT_Z + ST) - 4 * ST) / 5
    z = BOT_Z + ST
    shelf_zs = []
    for k in range(4):
        z += open_h
        _shelf(kit, z, YF + 0.010, XI - 0.0015)
        shelf_zs.append(z + ST)
        z += ST

    # --- Metadata -----------------------------------------------------------
    kit.support("top", (0, 0, H), (W - 0.03, D - 0.03))
    kit.support("bottom shelf", (0, (YF + BACK_Y) / 2, BOT_Z + ST), (2 * XI - 0.02, BACK_Y - YF - 0.02))
    for k, sz in enumerate(shelf_zs):
        kit.support("shelf %d" % (k + 1), (0, (YF + 0.01 + BACK_Y) / 2, sz), (2 * XI - 0.02, BACK_Y - YF - 0.03))
    kit.anchor("top", (0, 0, H))
    kit.collider((0, 0, H / 2), (W, D, H))
    kit.tag("domestic", "case_goods", "pile", "pile_piece", "shelving")
    kit.pile("Case", mass=2, states=["Upright", "Back", "Side", "EdgeLean"], palette="domestic70s")

    nc.scatter(kit, 4471, (OAK, BACK))
    nc.lod1_sharp(kit, SMOOTH_ANGLE)
