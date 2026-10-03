"""Raw plywood utility cabinet (the unfinished ply cabinets at the base of
the tall pile in A24 "Backrooms" Still B).

Real-world reference: a job-built storeroom / workshop cabinet, c. 1975-95:
18 mm unfinished plywood box (sides notched for a 75 mm toe kick, top laid
over the sides and run forward flush with the doors), two full-overlay
18 mm ply doors on surface butt hinges with exposed knuckles, square-bar
chrome D-pulls, a 6 mm particleboard back let in between the sides, and an
inventory asset tag on the right door. Every cut edge shows its plies (see
_newcase.ply_edge: one quad per edge, the scan squeezed across 18 mm).

Size: 0.90 m wide, 0.45 m deep (incl. doors), 1.20 m tall.
Front (doors) looks -Y.
"""

import random

import _newcase as nc

NAME = "Kit_PlyCabinet"
SMOOTH_ANGLE = 40.0

PLY = "Prop_Plywood"
BACK = "Prop_Chipboard"
METAL = "Prop_Chrome"

W, D, H = 0.90, 0.45, 1.20
T = 0.018                       # ply thickness
BACK_T = 0.006
DOOR_Y1 = -D / 2 + 0.002        # door faces (top runs 2 mm proud of them)
YF = DOOR_Y1 + T                # carcass front edge (door backs)
YB = D / 2                      # carcass back edge (back panel let in flush)
TOP_Z0 = H - T
KICK_H, KICK_D = 0.075, 0.060
GAP = 0.003


def build(kit):
    rng = random.Random(9917)
    # --- Carcass ------------------------------------------------------------
    for sx in (-1, 1):
        outline = [(YB, 0.0), (YF + KICK_D, 0.0), (YF + KICK_D, KICK_H), (YF, KICK_H), (YF, TOP_Z0), (YB, TOP_Z0)]
        side = kit.extrude(outline, T, (sx * (W / 2 - T / 2), 0, 0), PLY, plane="yz", bevel=0.0, name="side")
        side["fr_grain"] = "z"
        nc.tri(side)
    # Top laid over the sides, run forward over the doors; edges just eased.
    top_y0, top_y1 = -D / 2, D / 2
    nc.plate(kit, W, top_y1 - top_y0, nc.chamfer(T, 0.0012), (0, (top_y0 + top_y1) / 2, TOP_Z0), PLY,
             facing="+z", name="top", grain="x")
    kit.box((W - 2 * T, YB - BACK_T - YF, T), (0, (YF + YB - BACK_T) / 2, KICK_H + T / 2), PLY, bevel=0.0,
            name="bottom")
    kit.box((W - 2 * T, T, KICK_H), (0, YF + KICK_D + T / 2, KICK_H / 2), PLY, bevel=0.0, name="toe kick")
    # Particleboard back let in between the sides, 1 mm shy of their back
    # edges, which show their plies from behind.
    kit.box((W - 2 * T, BACK_T, TOP_Z0), (0, YB - 0.001 - BACK_T / 2, TOP_Z0 / 2), BACK, bevel=0.0,
            name="back panel")
    for sx in (-1, 1):
        nc.ply_edge(kit, (sx * (W / 2 - T / 2), YB, TOP_Z0 / 2), (0, 1, 0), (0, 0, 1), TOP_Z0, T, PLY,
                    random.Random(77 + sx))

    # --- Doors ----------------------------------------------------------------
    dz0, dz1 = KICK_H + GAP, TOP_Z0 - GAP
    dh = dz1 - dz0
    dw = (W - 3 * GAP) / 2 + GAP / 2      # full overlay, 3 mm meeting gap
    dyc = DOOR_Y1 + T / 2
    for sx in (-1, 1):
        cx = sx * (GAP / 2 + dw / 2)
        sag = -0.0016 if sx > 0 else 0.0          # job-built: the right door hangs 1.6 mm low
        dz0, dz1 = KICK_H + GAP + sag, TOP_Z0 - GAP + sag
        nc.plate(kit, dw, dh, nc.chamfer(T, 0.0012), (cx, YF, dz0 + dh / 2), PLY, facing="-y",
                 name="door", grain="z")
        # Cut edges: outer, meeting, top, bottom.
        for ex in (-1, 1):
            nc.ply_edge(kit, (cx + ex * dw / 2, dyc, dz0 + dh / 2), (ex, 0, 0), (0, 0, 1), dh, T, PLY, rng)
        for ez in (-1, 1):
            nc.ply_edge(kit, (cx, dyc, dz0 + dh / 2 + ez * dh / 2), (0, 0, ez), (1, 0, 0), dw, T, PLY, rng)
        # Square-bar chrome D-pull, vertical, near the meeting edge.
        px = cx - sx * (dw / 2 - 0.045)
        pz = dz1 - 0.16
        yd = DOOR_Y1
        c = 0.006
        u = [(yd, pz - 0.052), (yd - 0.028 + c, pz - 0.052), (yd - 0.028, pz - 0.052 + c), (yd - 0.028, pz + 0.052 - c),
             (yd - 0.028 + c, pz + 0.052), (yd, pz + 0.052), (yd, pz + 0.044), (yd - 0.020, pz + 0.044),
             (yd - 0.020, pz - 0.044), (yd, pz - 0.044)]
        pull = kit.extrude(u, 0.009, (px, 0, 0), METAL, plane="yz", bevel=0.0, name="d pull")
        nc.tri(pull)
        # Surface-mounted wrap hinges (the job-built look): a leaf screwed
        # to the door face, the knuckle on the outer corner, a leaf on the side.
        for hz in (dz0 + 0.11, dz1 - 0.11):
            hl = 0.064
            kit.box((0.020, 0.0015, hl), (sx * (W / 2 - 0.004 - 0.010), DOOR_Y1 - 0.00075, hz), METAL,
                    bevel=0.0, name="hinge leaf front")
            nc.knuckle(kit, sx * (W / 2 - 0.0005), DOOR_Y1 - 0.0005, hz, hl, METAL, radius=0.0042)
            kit.box((0.0015, 0.024, hl), (sx * (W / 2 + 0.00075), DOOR_Y1 + 0.004 + 0.012, hz), METAL,
                    bevel=0.0, name="hinge leaf side")

    # Top: front and side edges show their plies (the back one is seen in piles).
    tyc = TOP_Z0 + T / 2
    nc.ply_edge(kit, (0, top_y0, tyc), (0, -1, 0), (1, 0, 0), W, T, PLY, rng)
    nc.ply_edge(kit, (0, top_y1, tyc), (0, 1, 0), (1, 0, 0), W, T, PLY, rng)
    for sx in (-1, 1):
        nc.ply_edge(kit, (sx * W / 2, 0, tyc), (sx, 0, 0), (0, 1, 0), D, T, PLY, rng)

    # Inventory asset tag, top corner of the right door.
    nc.label(kit, *nc.ASSET_TAG, 0.056, 0.029, (dw - 0.06, DOOR_Y1 - 0.0004, dz1 - 0.045), facing="-y",
             name="asset tag")

    # --- Metadata -------------------------------------------------------------
    kit.support("top", (0, 0, H), (W - 0.03, D - 0.03))
    kit.anchor("top", (0, 0, H))
    kit.collider((0, 0, H / 2), (W, D, H))
    kit.tag("storage", "case_goods", "pile", "pile_piece")
    kit.pile("Case", mass=2, states=["Upright", "Side", "Back"], palette="storage")

    nc.scatter(kit, 9917, (PLY, BACK))
    nc.grain_on_u(kit)
