"""Dark 1980s china hutch (the ebonised cabinet leaning 45 degrees, back to
the camera, in the low pile of A24 "Backrooms" Still A: "dark triangular
silhouette peak").

Real-world reference: mass-market Queen Anne-style dining hutch, c. 1980-88,
black-brown ebonised finish with brass hardware. Lower buffet: moulded
plinth, two overlay drawers over two frame-and-raised-panel doors, an ogee
top that overhangs 20 mm. Upper hutch set back on the buffet top: oak-framed
face frame (ebonised) with two inset glazed doors whose glass has an arched
head (a shaped spandrel in each door), two plate shelves inside, a cove
crown under a rounded top board, brass knobs and butt hinges, brass bail
pulls on the drawers, tempered hardboard back.

Size: 1.00 m wide, 0.50 m deep (buffet), 1.90 m tall; buffet top at 0.80 m.
Front looks -Y. Variant Kit_Hutch_Cherry swaps the finish to cherry.
"""

import math
import random

import _newcase as nc

NAME = "Kit_Hutch"
LOD1 = 0.4
SMOOTH_ANGLE = 40.0
VARIANTS = {"Kit_Hutch_Cherry": {"Prop_WoodEbony": "Prop_WoodCherry"}}

WOOD = "Prop_WoodEbony"
BRASS = "Prop_Brass"
GLASS = "Prop_Glass"
BACK = "Prop_Hardboard"

W, D, H = 1.00, 0.50, 1.90
T = 0.019                       # carcass board
YB = D / 2                      # back plane 0.25
# Buffet
CXL = 0.48                      # carcass half-width (top overhangs 20 mm)
FRONT_T = 0.022
YFL = -D / 2 + 0.015 + FRONT_T  # carcass face -0.213; the top overhangs the fronts 15 mm
PLINTH_H = 0.100
TOPL_T = 0.025
TOPL_Z = 0.80                   # buffet top surface
GAP = 0.004
# Hutch
CXU = 0.46
YFU = -0.060                    # face frame front
CROWN_O = 0.037
CROWN_Z = 1.800
TOPU_T = 0.022
STILE = 0.050
U_OPEN_Z0, U_OPEN_Z1 = 0.850, 1.700
MEMBER = 0.045
FRAME_PROFILE = [(0.0, 0.0), (MEMBER, 0.0), (MEMBER, 0.017), (MEMBER - 0.0025, 0.020), (0.010, 0.020),
                 (0.0055, 0.0188), (0.0025, 0.0158), (0.0, 0.012)]


def build(kit):
    rng = random.Random(1983)
    # =============================== buffet ===============================
    base = [(-0.030, 0.0), (0.016, 0.0), (0.016, 0.058), (0.0145, 0.066), (0.0105, 0.073), (0.0065, 0.080),
            (0.0045, 0.089), (0.0, PLINTH_H), (-0.030, PLINTH_H)]
    # Run on the door-face line, so the moulding stands 16 mm proud of the doors.
    nc.sweep(kit, nc.three_sides(CXL, YFL - FRONT_T, YB), base, WOOD, origin=(0, 0, 0), name="plinth moulding")
    kit.box((2 * CXL - 0.024, YB - YFL - 0.012, 0.012), (0, (YFL + YB) / 2 + 0.006, PLINTH_H - 0.006), WOOD,
            bevel=0.0, name="plinth deck")
    side_h = TOPL_Z - TOPL_T - PLINTH_H
    for sx in (-1, 1):
        nc.plate(kit, YB - YFL, side_h, nc.chamfer(T, 0.002), (sx * (CXL - T), (YFL + YB) / 2, PLINTH_H + side_h / 2),
                 WOOD, facing="+x" if sx > 0 else "-x", name="buffet side", grain="z")
    # Carcass face behind the fronts (seen in the shut lines).
    kit.quad(2 * CXL - 0.002, side_h, (0, YFL + 0.0005, PLINTH_H + side_h / 2), WOOD, facing="-y", uv="metres",
             name="buffet face")
    # Ogee top, overhanging front and sides.
    nc.plate(kit, W, D, nc.ogee(TOPL_T, 0.011), (0, 0, TOPL_Z - TOPL_T), WOOD, facing="+z", name="buffet top",
             grain="x")
    # Fronts: two drawers over two raised-panel doors.
    fw = (2 * CXL - 3 * GAP) / 2
    z_top = TOPL_Z - TOPL_T - GAP
    dr_h = 0.130
    dr_z = z_top - dr_h / 2
    door_z0 = PLINTH_H + GAP
    door_z1 = z_top - dr_h - GAP
    door_h = door_z1 - door_z0
    for sx in (-1, 1):
        cx = sx * (GAP / 2 + fw / 2)
        nc.plate(kit, fw, dr_h, nc.ogee(FRONT_T, 0.009), (cx, YFL, dr_z), WOOD, facing="-y", name="drawer front",
                 grain="x")
        nc.bail_pull(kit, cx, dr_z + 0.004, YFL - FRONT_T, BRASS, span=0.084, drop=0.024, plate_h=0.038)
        nc.plate(kit, fw, door_h, nc.raised_panel(FRONT_T, rail=0.062, field=0.034),
                 (cx, YFL, door_z0 + door_h / 2), WOOD, facing="-y", name="buffet door", grain="z")
        nc.knob(kit, sx * (GAP / 2 + 0.034), door_z1 - 0.075, YFL - FRONT_T, BRASS)
        for hz in (door_z0 + 0.07, door_z1 - 0.07):
            nc.knuckle(kit, sx * (CXL - 0.0005), YFL - 0.003, hz, 0.050, BRASS, radius=0.0038)
    kit.box((2 * (CXL - T), 0.005, TOPL_Z - TOPL_T - 0.004), (0, YB - 0.0025, (TOPL_Z - TOPL_T + 0.004) / 2), BACK,
            bevel=0.0, name="buffet back")

    # =============================== hutch ================================
    ff_y = YFU + 0.020
    u_side_h = CROWN_Z - TOPL_Z
    for sx in (-1, 1):
        nc.plate(kit, YB - YFU, u_side_h, nc.chamfer(T, 0.002), (sx * (CXU - T), (YFU + YB) / 2, TOPL_Z + u_side_h / 2),
                 WOOD, facing="+x" if sx > 0 else "-x", name="hutch side", grain="z")
        nc.plate(kit, STILE, u_side_h, nc.chamfer(0.020, 0.002), (sx * (CXU - STILE / 2), ff_y, TOPL_Z + u_side_h / 2),
                 WOOD, facing="-y", name="hutch stile", grain="z")
    rail_w = 2 * (CXU - STILE) + 0.004
    nc.plate(kit, rail_w, CROWN_Z - U_OPEN_Z1, nc.chamfer(0.019, 0.002), (0, ff_y, (CROWN_Z + U_OPEN_Z1) / 2), WOOD,
             facing="-y", name="frieze rail", grain="x")
    nc.plate(kit, rail_w, U_OPEN_Z0 - TOPL_Z, nc.chamfer(0.019, 0.002), (0, ff_y, (U_OPEN_Z0 + TOPL_Z) / 2), WOOD,
             facing="-y", name="hutch bottom rail", grain="x")
    # Interior: back veneer, two plate shelves, ceiling.
    ix = CXU - T
    kit.box((2 * ix, 0.005, H - TOPU_T - TOPL_Z), (0, YB - 0.0025, (H - TOPU_T + TOPL_Z) / 2), BACK, bevel=0.0,
            name="hutch back")
    kit.quad(2 * ix, U_OPEN_Z1 - TOPL_Z, (0, YB - 0.0052, (U_OPEN_Z1 + TOPL_Z) / 2), WOOD, facing="-y", uv="metres",
             name="hutch back veneer")
    for z in (1.115, 1.405):
        sy0, sy1 = ff_y + 0.012, YB - 0.006
        nc.plate(kit, 2 * ix - 0.002, sy1 - sy0, nc.chamfer(T, 0.002), (0, (sy0 + sy1) / 2, z), WOOD, facing="+z",
                 name="plate shelf", grain="x")
    ceil = kit.quad(2 * ix, YB - 0.006 - ff_y, (0, (ff_y + YB - 0.006) / 2, U_OPEN_Z1), WOOD, facing="+z",
                    uv="metres", name="ceiling")
    ceil.rotation_euler = (math.pi, 0, 0)
    # Doors: inset, mitred frames, arched glass heads.
    rv = 0.0025
    ox = CXU - STILE
    dz0, dz1 = U_OPEN_Z0 + rv, U_OPEN_Z1 - rv
    for sx in (-1, 1):
        x_out, x_in = sx * (ox - rv), sx * (rv / 2)
        dx0, dx1 = min(x_out, x_in), max(x_out, x_in)
        gx0, gx1 = dx0 + MEMBER, dx1 - MEMBER
        gz0, gz1 = dz0 + MEMBER, dz1 - MEMBER
        nc.sweep(kit, nc.rect_path(gx0, gx1, gz0, gz1), FRAME_PROFILE, WOOD, facing="-y", origin=(0, ff_y, 0),
                 closed=True, split=True, name="door frame")
        kit.box((gx1 - gx0 + 0.012, 0.003, gz1 - gz0 + 0.012), ((gx0 + gx1) / 2, ff_y - 0.0045, (gz0 + gz1) / 2),
                GLASS, bevel=0.0, name="door glass")
        # Spandrel: fills the top corners so the glass reads as an arch.
        mid, hw = (gx0 + gx1) / 2, (gx1 - gx0) / 2
        spring, rise = gz1 - 0.115, 0.085
        arc = [(mid + hw * math.cos(math.pi * k / 12), spring + rise * math.sin(math.pi * k / 12)) for k in range(13)]
        outline = [(gx0, gz1 + 0.003), (gx1, gz1 + 0.003)] + arc[:-1] + [(gx0, spring)]
        # arc runs right -> left: (gx1, spring) ... apex ... (gx0, spring)
        sp = kit.extrude(outline, 0.008, (0, ff_y - 0.010, 0), WOOD, plane="xz", bevel=0.0, name="spandrel")
        sp["fr_grain"] = "x"
        nc.tri(sp)
        nc.knob(kit, sx * (rv / 2 + MEMBER / 2), 1.08, YFU, BRASS, scale=0.85)
        for hz in (dz0 + 0.12, dz1 - 0.12):
            nc.knuckle(kit, x_out + sx * 0.0005, YFU - 0.0025, hz, 0.050, BRASS, radius=0.0038)

    # Crown and top board.
    crown = [(-0.012, 0.0), (0.0, 0.0), (0.004, 0.004), (0.0052, 0.0095), (0.0085, 0.0125), (0.0125, 0.0155),
             (0.0205, 0.0235), (0.0285, 0.0335), (0.0345, 0.0455), (0.0372, 0.0575), (0.0400, 0.0600),
             (0.0400, H - TOPU_T - CROWN_Z), (-0.012, H - TOPU_T - CROWN_Z)]
    nc.sweep(kit, nc.three_sides(CXU, YFU, YB), crown, WOOD, origin=(0, 0, CROWN_Z), name="crown")
    core_y0, core_y1 = ff_y, YB - 0.006
    kit.box((2 * CXU - 0.02, core_y1 - core_y0, H - TOPU_T - (U_OPEN_Z1 + 0.01)),
            (0, (core_y0 + core_y1) / 2, (H - TOPU_T + U_OPEN_Z1 + 0.01) / 2), WOOD, bevel=0.0, name="crown core")
    ty0 = YFU - CROWN_O - 0.003
    nc.plate(kit, 2 * (CXU + CROWN_O + 0.003), YB - ty0, nc.rounded(TOPU_T, 0.007), (0, (ty0 + YB) / 2, H - TOPU_T),
             WOOD, facing="+z", name="top", grain="x")

    # ============================== metadata ==============================
    kit.support("top", (0, (ty0 + YB) / 2, H), (2 * CXU, YB - ty0 - 0.03))
    kit.support("buffet ledge", (0, (-D / 2 + YFU) / 2, TOPL_Z), (W - 0.04, YFU + D / 2 - 0.02))
    kit.anchor("top", (0, (ty0 + YB) / 2, H))
    kit.collider((0, 0, TOPL_Z / 2), (W, D, TOPL_Z))
    kit.collider((0, (ty0 + YB) / 2, (TOPL_Z + H) / 2), (2 * (CXU + CROWN_O + 0.003), YB - ty0, H - TOPL_Z))
    kit.tag("domestic", "case_goods", "pile", "pile_piece", "glass")
    kit.pile("Case", mass=3, states=["Upright", "Back", "EdgeLean"], palette="domestic70s")

    nc.scatter(kit, 1983, (WOOD, BACK))
    nc.lod1_sharp(kit, SMOOTH_ANGLE)
