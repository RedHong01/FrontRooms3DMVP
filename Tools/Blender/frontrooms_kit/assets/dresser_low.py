"""Low cherry six-drawer dresser, c. 1975-88 (the cherry sideboard standing
upright at the back of the low pile in A24 "Backrooms" Still A).

Real-world reference: mass-market Chippendale-style double dresser in
lacquered cherry: an ogee-edged top overhanging 20 mm, a flat face frame
(end stiles, centre stile, rails) with six lipped drawers in two columns,
graduated top to bottom, each with a thumbnail edge and two brass bail
pulls; an ovolo base moulding over four ogee bracket feet (the case floats
75 mm off the floor between them), tempered hardboard back with the maker's
paper label.

Size: 1.40 m wide, 0.48 m deep, 0.78 m tall. Front looks -Y.
"""

import random

import _newcase as nc

NAME = "Kit_DresserLow"
LOD1 = 0.4
SMOOTH_ANGLE = 40.0

WOOD = "Prop_WoodCherry"
BRASS = "Prop_Brass"
BACK = "Prop_Hardboard"

W, D, H = 1.40, 0.48, 0.78
OVER = 0.020
CX = W / 2 - OVER               # carcass half-width 0.68
FRONT_T = 0.020
YF = -D / 2 + 0.016 + FRONT_T   # face frame -0.204; the top overhangs the drawers 16 mm
YM = YF - FRONT_T + 0.004       # base moulding line (10 mm proud of the drawers)
YB = D / 2                      # 0.24
T = 0.019
TOP_T = 0.025
FOOT_H = 0.075
BASE_H = 0.032                  # ovolo base moulding above the feet
CASE_Z0 = FOOT_H + BASE_H       # 0.107
CASE_Z1 = H - TOP_T             # 0.755
LIP = 0.008                     # drawer lips overlap the face frame


def _bracket(kit, u_sign, corner, facing):
    """One ogee bracket-foot board: profile in its own plane, outer edge at
    the corner. facing '-y' (front) or '+x'/'-x' (sides)."""
    L = 0.135
    prof = [(0.0, 0.0), (0.050, 0.0), (0.056, 0.010), (0.068, 0.022), (0.088, 0.030), (0.112, 0.036),
            (L, 0.050), (L, FOOT_H), (0.0, FOOT_H)]
    t = 0.020
    cx, cy = corner
    if facing == "-y":
        pts = [(cx + u_sign * u, v) for u, v in prof]
        obj = kit.extrude(pts, t, (0, cy + t / 2, 0), WOOD, plane="xz", bevel=0.0, name="bracket foot")
        obj["fr_grain"] = "x"
    else:
        pts = [(cy + u_sign * u, v) for u, v in prof]
        sx = 1 if facing == "+x" else -1
        obj = kit.extrude(pts, t, (cx - sx * t / 2, 0, 0), WOOD, plane="yz", bevel=0.0, name="bracket foot")
        obj["fr_grain"] = "y"
    nc.tri(obj)
    return obj


def build(kit):
    # --- Case -----------------------------------------------------------------
    side_h = CASE_Z1 - CASE_Z0
    for sx in (-1, 1):
        nc.plate(kit, YB - YF, side_h, nc.chamfer(T, 0.002), (sx * (CX - T), (YF + YB) / 2, CASE_Z0 + side_h / 2),
                 WOOD, facing="+x" if sx > 0 else "-x", name="side", grain="z")
    # Face frame: one cherry plane behind the lipped drawers (stiles and rails
    # show between them), its outer edges on the side panels.
    kit.quad(2 * (CX - T), side_h, (0, YF, CASE_Z0 + side_h / 2), WOOD, facing="-y", uv="metres", name="face frame")
    nc.plate(kit, W, D, nc.ogee(TOP_T, 0.011), (0, 0, CASE_Z1), WOOD, facing="+z", name="top", grain="x")
    kit.box((2 * (CX - T), 0.005, H - TOP_T - FOOT_H - 0.004), (0, YB - 0.0025, (H - TOP_T + FOOT_H + 0.004) / 2),
            BACK, bevel=0.0, name="back panel")
    nc.label(kit, *nc.MAKER_LABEL, 0.105, 0.084, (0.36, YB + 0.0003, 0.55), facing="+y", name="maker label")

    # --- Base moulding and bracket feet ---------------------------------------
    ovolo = [(-0.026, 0.0), (0.014, 0.0), (0.014, 0.010), (0.0125, 0.018), (0.0085, 0.025), (0.003, 0.0295),
             (0.0, BASE_H), (-0.026, BASE_H)]
    nc.sweep(kit, nc.three_sides(CX, YM, YB), ovolo, WOOD, origin=(0, 0, FOOT_H), name="base moulding")
    # Dust board under the case (seen between the feet).
    kit.box((2 * CX - 0.03, YB - YF - 0.03, 0.008), (0, (YF + YB) / 2, FOOT_H + 0.004), WOOD, bevel=0.0,
            name="bottom board")
    fy = YM - 0.004                 # feet sit under the moulding, 10 mm behind its nose
    fx = CX + 0.004
    for sx in (-1, 1):
        _bracket(kit, -sx, (sx * fx, fy), "-y")                       # front, runs inward
        _bracket(kit, 1, (sx * fx, fy + 0.020), "+x" if sx > 0 else "-x")   # side, butts behind the front
        _bracket(kit, -1, (sx * fx, YB), "+x" if sx > 0 else "-x")    # rear side bracket, runs forward
        kit.box((0.10, 0.020, FOOT_H), (sx * (fx - 0.07), YB - 0.010, FOOT_H / 2), WOOD, bevel=0.0,
                name="rear foot block")

    # --- Drawers: 2 columns x 3 graduated rows --------------------------------
    stile, centre = 0.035, 0.040
    top_rail, bot_rail, rail = 0.030, 0.030, 0.030
    rows = [0.200, 0.175, 0.153]                       # bottom to top
    open_w = (2 * CX - 2 * stile - centre) / 2
    z = CASE_Z0 + bot_rail
    thumb = [(0, 0), (0, FRONT_T - 0.008), (0.003, FRONT_T - 0.003), (0.0075, FRONT_T)]
    for k, h in enumerate(rows):
        zc = z + h / 2
        for sx in (-1, 1):
            cx = sx * (centre / 2 + open_w / 2)
            nc.plate(kit, open_w + 2 * LIP, h + 2 * LIP, thumb, (cx, YF, zc), WOOD, facing="-y",
                     name="drawer front", grain="x")
            for px in (-0.165, 0.165):
                nc.bail_pull(kit, cx + px, zc + 0.006, YF - FRONT_T, BRASS, span=0.072, drop=0.022, plate_h=0.030,
                             post_verts=4)
        z += h + rail
    assert abs((z - rail + top_rail) - CASE_Z1) < 0.01, z

    # --- Metadata ----------------------------------------------------------------
    kit.support("top", (0, 0, H), (W - 0.04, D - 0.04))
    kit.anchor("top", (0, 0, H))
    kit.collider((0, 0, H / 2), (W, D, H))
    kit.tag("domestic", "case_goods", "pile", "pile_piece")
    kit.pile("Case", mass=3, states=["Upright", "Back", "EdgeLean"], palette="domestic70s")

    nc.scatter(kit, 7801, (WOOD, BACK))
    nc.lod1_sharp(kit, SMOOTH_ANGLE)
