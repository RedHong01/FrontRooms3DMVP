"""Cherry office credenza, c. 1988-97 (the cherry sideboard standing behind
the pedestal desk in the low pile of A24 "Backrooms" Still A; also the
executive-office wall unit of the Office level).

Real-world reference: "transitional" executive credenza in lacquered cherry
veneer: a 30 mm top with an ogee edge overhanging 20 mm, a pedestal at each
end (a locking box drawer over a lateral-file drawer), a pair of hinged doors
on concealed hinges between them, fronts set between the case sides, an eased edge
and a routed V-groove border, brass bail pulls, a brass lock core in each box
drawer, a recessed toe-kick plinth, tempered hardboard back with the maker's
label.

Size: 1.52 m wide, 0.46 m deep, 0.76 m tall. Front looks -Y.
"""

import random

import _newcase as nc

NAME = "Kit_Credenza"
LOD1 = 0.4
SMOOTH_ANGLE = 40.0

WOOD = "Prop_WoodCherry"
BRASS = "Prop_Brass"
BACK = "Prop_Hardboard"

W, D, H = 1.52, 0.46, 0.76
OVER = 0.020
CX = W / 2 - OVER               # 0.74
YF = -D / 2 + OVER + 0.022      # carcass face (fronts 22 mm in front of it) -0.188
YB = D / 2                      # 0.23
T = 0.019
TOP_T = 0.030
KICK_H = 0.070
KICK_IN = 0.035
FRONT_T = 0.022
GAP = 0.004
PED_W = 0.40


def build(kit):
    case_z0, case_z1 = KICK_H, H - TOP_T
    side_h = case_z1 - case_z0
    # --- Case --------------------------------------------------------------------
    for sx in (-1, 1):
        nc.plate(kit, YB - (YF - FRONT_T), side_h, nc.chamfer(T, 0.002),
                 (sx * (CX - T), (YB + YF - FRONT_T) / 2, case_z0 + side_h / 2), WOOD,
                 facing="+x" if sx > 0 else "-x", name="side", grain="z")
    kit.quad(2 * (CX - T), side_h, (0, YF, case_z0 + side_h / 2), WOOD, facing="-y", uv="metres", name="case face")
    nc.plate(kit, W, D, nc.ogee(TOP_T, 0.012), (0, 0, case_z1), WOOD, facing="+z", name="top", grain="x")
    kit.box((2 * (CX - T), 0.005, H - TOP_T - 0.004), (0, YB - 0.0025, (H - TOP_T + 0.004) / 2), BACK, bevel=0.0,
            name="back panel")
    nc.label(kit, *nc.MAKER_LABEL, 0.105, 0.084, (-0.45, YB + 0.0003, 0.52), facing="+y", name="maker label")
    # Recessed toe kick: front board and two returns, 35 mm in.
    ky = YF - FRONT_T + KICK_IN
    kx = CX - 0.020
    kit.box((2 * kx, 0.018, KICK_H), (0, ky + 0.009, KICK_H / 2), WOOD, bevel=0.0, name="toe kick")
    for sx in (-1, 1):
        kit.box((0.018, YB - ky - 0.006, KICK_H), (sx * (kx - 0.009), (ky + YB - 0.006) / 2, KICK_H / 2), WOOD,
                bevel=0.0, name="kick return")
    kit.box((2 * CX - 0.002, YB - YF + FRONT_T - 0.004, 0.012), (0, (YB + YF - FRONT_T) / 2, KICK_H + 0.006), WOOD,
            bevel=0.0, name="bottom")

    # --- Fronts ------------------------------------------------------------------
    prof = nc.routed(FRONT_T, border=0.042, edge=0.004, groove=0.006, depth=0.003)
    z0, z1 = case_z0 + GAP, case_z1 - GAP
    box_h = 0.165
    for sx in (-1, 1):
        # Pedestal: box drawer over a lateral-file drawer.
        x_out = sx * (CX - T - 0.003)          # fronts sit between the sides, 3 mm shy
        x_in = sx * (CX - PED_W)
        pcx, pw = (x_out + x_in) / 2, abs(x_out - x_in) - GAP / 2
        bz = z1 - box_h / 2
        nc.plate(kit, pw, box_h, prof, (pcx, YF, bz), WOOD, facing="-y", name="box drawer", grain="x")
        nc.bail_pull(kit, pcx, bz - 0.010, YF - FRONT_T, BRASS, span=0.076, drop=0.022, plate_h=0.032)
        lock = kit.cylinder(0.0085, 0.006, (pcx, YF - FRONT_T - 0.001, bz + 0.048), BRASS, verts=10, rot=(90, 0, 0),
                            bevel=0.0, name="lock core")
        fh = (z1 - box_h - GAP) - z0
        fz = z0 + fh / 2
        nc.plate(kit, pw, fh, prof, (pcx, YF, fz), WOOD, facing="-y", name="file drawer", grain="x")
        nc.bail_pull(kit, pcx, z0 + fh - 0.075, YF - FRONT_T, BRASS, span=0.076, drop=0.022, plate_h=0.032)
        # Door between the pedestals (one each side of centre).
        dx0, dx1 = sx * (GAP / 2), sx * (CX - PED_W - GAP / 2)
        dcx, dw = (dx0 + dx1) / 2, abs(dx1 - dx0)
        nc.plate(kit, dw, z1 - z0, prof, (dcx, YF, (z0 + z1) / 2), WOOD, facing="-y", name="door", grain="z")
        nc.bail_pull(kit, sx * (GAP / 2 + 0.055), z1 - 0.20, YF - FRONT_T, BRASS, span=0.076, drop=0.022,
                     plate_h=0.032, vertical=True)

    # --- Metadata ------------------------------------------------------------------
    kit.support("top", (0, 0, H), (W - 0.04, D - 0.04))
    kit.anchor("top", (0, 0, H))
    kit.collider((0, 0, H / 2), (W, D, H))
    kit.tag("office", "domestic", "case_goods", "pile", "pile_piece", "wall_unit")
    kit.pile("Case", mass=3, states=["Upright", "Back"], palette="office90s")

    nc.scatter(kit, 1529, (WOOD, BACK))
    nc.lod1_sharp(kit, SMOOTH_ANGLE)
