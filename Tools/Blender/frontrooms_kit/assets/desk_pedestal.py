"""Cherry executive double-pedestal desk, early 1990s (the lacquered cherry
desk anchoring the low pile in A24 "Backrooms" Still A).

Real-world reference: a "traditional" executive desk from an office-furniture
catalogue: a 32 mm top with a thumbnail edge overhanging two pedestals, each
pedestal with two box drawers over a file drawer, a pencil drawer over the
kneehole, fielded (bevel-raised) drawer fronts, brass bail pulls on
backplates, moulded plinths, and finished panelled ends and back (the desk
stands free in a manager's office, so the visitor side is panelled too: the
modesty panel and the pedestal backs carry raised panels).

Size: 1.37 m wide, 0.71 m deep, 0.76 m tall. The drawers (the user's side)
face -Y; the visitor's side (+Y) shows the modesty panel.
Budget 1,800 tris LOD0 / ~700 LOD1. Slots: WoodCherry, Brass, Backer
(kraft backer under the top).
"""

import math
import random

NAME = "Kit_DeskPedestal"
LOD1 = 0.4
SMOOTH_ANGLE = 40.0

CHERRY = "Prop_WoodCherry"
BRASS = "Prop_Brass"
BACKER = "Prop_Backer"

W, D, H = 1.37, 0.71, 0.76
TOP_T = 0.032
TOP_Z0 = H - TOP_T
Y_FRONT = -D / 2 + 0.025       # carcass front (drawer side) under a 25 mm overhang
Y_BACK = D / 2 - 0.018         # carcass back (visitor side)
PW = 0.38                      # pedestal width
PX = W / 2 - 0.020 - PW / 2    # pedestal centre x
PLINTH_H = 0.072
FRONT_T = 0.020                # drawer front thickness (overlay)
GAP = 0.004
KNEE_APRON = 0.118             # apron (pencil drawer zone) above the kneehole


def _fielded(kit, size_w, size_h, depth, field, loc, rot=(0, 0, 0), name="fielded panel"):
    """A fielded (bevel-raised) board: the face is ``field`` smaller each
    side than the back, so the raise reads as a lit upper bevel and a dark
    lower one under top light. Faces -Y unless rotated."""
    return kit.loft_box((size_w - 2 * field, size_h - 2 * field), (size_w, size_h), depth, loc, CHERRY,
                        bevel=0.0015, segments=1, rot=rot, name=name)


def _bail_pull(kit, x, y, z, span=0.074):
    """Brass bail pull: an elongated-octagon backplate and a hanging bail
    whose ends turn into the plate."""
    hw, hh, c = span / 2 + 0.010, 0.016, 0.008
    plate = [(-hw + c, -hh), (hw - c, -hh), (hw, -hh + c), (hw, hh - c), (hw - c, hh), (-hw + c, hh),
             (-hw, hh - c), (-hw, -hh + c)]
    kit.extrude(plate, 0.002, (x, y - 0.001, z), BRASS, plane="xz", bevel=0.0, name="pull plate")
    # The bail swings from the plate's upper corners and hangs in a shallow arc.
    a = span / 2
    pts = []
    for i in range(6):
        t = math.pi * i / 5
        s = math.sin(t)
        pts.append((x - a * math.cos(t), y - 0.0015 - 0.009 * s, z + 0.007 - 0.019 * s))
    kit.tube(pts, 0.0032, BRASS, verts=6, name="pull bail")


def build(kit):
    rng = random.Random(1370)
    # --- Top: thumbnail edge, kraft backer underneath ---------------------
    kit.box((W, D, TOP_T), (0, 0, TOP_Z0 + TOP_T / 2), CHERRY, bevel=0.010, segments=3, name="top")
    kit.quad(W - 0.06, D - 0.06, (0, 0, TOP_Z0 - 0.0006), BACKER, facing="+z", uv="metres", name="top backer")
    kit.parts[-1].rotation_euler = (3.14159265, 0, 0)       # face down

    depth = Y_BACK - Y_FRONT
    yc = (Y_FRONT + Y_BACK) / 2
    car_h = TOP_Z0 - PLINTH_H
    for sx in (-1, 1):
        x = sx * PX
        # Pedestal carcass and moulded plinth.
        kit.box((PW, depth, car_h), (x, yc, PLINTH_H + car_h / 2), CHERRY, bevel=0.003, segments=1,
                name="pedestal")
        kit.box((PW + 0.016, depth + 0.010, PLINTH_H), (x, yc - 0.003, PLINTH_H / 2), CHERRY,
                bevel=0.008, segments=2, name="plinth")
        # Panelled end (outer side) and back.
        pz = PLINTH_H + 0.03 + (car_h - 0.06) / 2
        _fielded(kit, depth - 0.07, car_h - 0.07, 0.010, 0.022,
                 (x + sx * (PW / 2 + 0.004), yc, pz), rot=(0, 0, 90 * sx), name="end panel")
        _fielded(kit, PW - 0.07, car_h - 0.07, 0.010, 0.022,
                 (x, Y_BACK + 0.004, pz), rot=(0, 0, 180), name="back panel")

        # Drawer fronts: two box drawers over a file drawer.
        zt = TOP_Z0 - 0.010
        fw = PW - 0.010
        for h in (0.128, 0.160, 0.330):
            zc = zt - h / 2
            fy = Y_FRONT - FRONT_T / 2 + 0.001
            _fielded(kit, fw, h, FRONT_T, 0.016, (x, fy, zc), name="drawer front")
            _bail_pull(kit, x, Y_FRONT - FRONT_T + 0.001, zc + (0.0 if h < 0.2 else h * 0.22))
            zt -= h + GAP

    # --- Kneehole: apron with the pencil drawer, recessed modesty panel ----
    kx = PX - PW / 2                                    # half width of the kneehole
    kit.box((2 * kx + 0.004, depth, KNEE_APRON), (0, yc, TOP_Z0 - KNEE_APRON / 2), CHERRY,
            bevel=0.003, segments=1, name="kneehole apron")
    ph = KNEE_APRON - 0.022
    _fielded(kit, 2 * kx - 0.012, ph, FRONT_T, 0.014, (0, Y_FRONT - FRONT_T / 2 + 0.001, TOP_Z0 - 0.010 - ph / 2),
             name="pencil drawer")
    _bail_pull(kit, 0, Y_FRONT - FRONT_T + 0.001, TOP_Z0 - 0.010 - ph / 2)
    mz0, mz1 = 0.17, TOP_Z0 - KNEE_APRON
    my = Y_BACK - 0.030
    kit.box((2 * kx + 0.004, 0.018, mz1 - mz0 + 0.004), (0, my, (mz0 + mz1) / 2), CHERRY,
            bevel=0.003, segments=1, name="modesty panel")
    _fielded(kit, 2 * kx - 0.08, mz1 - mz0 - 0.07, 0.008, 0.020, (0, my + 0.009 + 0.003, (mz0 + mz1) / 2),
             rot=(0, 0, 180), name="modesty field")

    for obj in kit.parts:
        obj["fr_uv_offset"] = (round(rng.uniform(0, 0.6), 3), round(rng.uniform(0, 1.0), 3))

    # --- Metadata -------------------------------------------------------
    kit.support("top", (0, 0, H), (W - 0.04, D - 0.04))
    kit.anchor("top", (0, 0, H))
    kit.collider((0, 0, H / 2), (W, D, H))
    kit.tag("office", "desk", "case_goods", "pile", "pile_piece")
    kit.pile("Table", mass=3, states=["Upright", "Back"], palette="office90s")
