"""Golden-oak glass curio / display cabinet, c. 1982-95 (the glass cabinet
standing upright at the lower centre-right of the tall pile in A24
"Backrooms" Still B: "glass reflection plus shelf lines").

Real-world reference: mass-market oak curio: a moulded plinth, an oak face
frame with a deep frieze rail under a cove-and-fascia crown and a rounded
top board, two inset glazed doors whose stiles and rails carry an ovolo
sticking round the glass (mitred), glazed side panels in oak frames, three
6 mm glass shelves, an oak-veneered back inside (tempered hardboard outside),
a halogen puck light in the ceiling, brass knobs and brass butt hinges.

Size: 0.90 m wide (crown), 0.40 m deep, 1.80 m tall. Front looks -Y.
"""

import math
import random

import _newcase as nc

NAME = "Kit_DisplayCabinet"
LOD1 = 0.4
SMOOTH_ANGLE = 40.0

OAK = "Prop_WoodOak"
GLASS = "Prop_Glass"
BRASS = "Prop_Brass"
BACK = "Prop_Hardboard"

W, D, H = 0.90, 0.40, 1.80
CROWN_O = 0.035                 # crown projection past the carcass
CX = W / 2 - CROWN_O            # carcass outer half-width 0.415
YF = -D / 2 + CROWN_O           # face-frame front -0.165
YB = D / 2                      # back 0.20
FF_T = 0.020                    # face frame / door / side frame thickness
PLINTH_H = 0.090
CROWN_Z = 1.720                 # crown starts (top of the frieze rail)
TOP_T = 0.022
STILE = 0.050
OPEN_Z0, OPEN_Z1 = 0.140, 1.620  # face-frame opening
MEMBER = 0.045                  # door / side frame member width

# Door / side-frame member section (o out from the glass, h toward the
# viewer): square back, chamfered outer arris, ovolo sticking at the glass.
FRAME_PROFILE = [(0.0, 0.0), (MEMBER, 0.0), (MEMBER, FF_T - 0.003), (MEMBER - 0.0025, FF_T),
                 (0.010, FF_T), (0.0055, FF_T - 0.0012), (0.0025, FF_T - 0.0042), (0.0, FF_T - 0.008)]


def build(kit):
    rng = random.Random(1806)
    # --- Plinth: base moulding round three sides -----------------------------
    base = [(-0.012, 0.0), (0.020, 0.0), (0.020, 0.056), (0.0185, 0.063), (0.0135, 0.069), (0.0085, 0.074),
            (0.0060, 0.081), (0.0035, 0.087), (0.0, PLINTH_H), (-0.012, PLINTH_H)]
    nc.sweep(kit, nc.three_sides(CX, YF, YB), base, OAK, facing="+z", origin=(0, 0, 0), name="base moulding")
    kit.box((2 * CX - 0.024, YB - YF - 0.012, 0.012), (0, (YF + YB) / 2 + 0.006, PLINTH_H - 0.006), OAK,
            bevel=0.0, name="plinth deck")

    # --- Face frame -------------------------------------------------------------
    ff_y = YF + FF_T                     # back plane of the face frame
    h_st = CROWN_Z - PLINTH_H
    for sx in (-1, 1):
        nc.plate(kit, STILE, h_st, nc.chamfer(FF_T, 0.002), (sx * (CX - STILE / 2), ff_y, PLINTH_H + h_st / 2), OAK,
                 facing="-y", name="face stile", grain="z")
    rail_w = 2 * (CX - STILE)
    nc.plate(kit, rail_w + 0.004, CROWN_Z - OPEN_Z1, nc.chamfer(FF_T - 0.001, 0.002),
             (0, ff_y, (CROWN_Z + OPEN_Z1) / 2), OAK, facing="-y", name="frieze rail", grain="x")
    nc.plate(kit, rail_w + 0.004, OPEN_Z0 - PLINTH_H, nc.chamfer(FF_T - 0.001, 0.002),
             (0, ff_y, (OPEN_Z0 + PLINTH_H) / 2), OAK, facing="-y", name="bottom rail", grain="x")

    # --- Side frames (glazed) ---------------------------------------------------
    sy0, sy1 = YF + FF_T, YB
    sz0, sz1 = PLINTH_H, CROWN_Z
    for sx in (-1, 1):
        facing = "+x" if sx > 0 else "-x"
        origin = (sx * (CX - FF_T), 0, 0)
        oy0, oy1 = sy0 + MEMBER, sy1 - MEMBER
        oz0, oz1 = sz0 + MEMBER, sz1 - MEMBER
        path = nc.rect_path(oy0, oy1, oz0, oz1) if sx > 0 else nc.rect_path(-oy1, -oy0, oz0, oz1)
        nc.sweep(kit, path, FRAME_PROFILE, OAK, facing=facing, origin=origin, closed=True, split=True,
                 name="side frame")
        kit.box((0.003, oy1 - oy0 + 0.012, oz1 - oz0 + 0.012), (sx * (CX - FF_T + 0.006), (oy0 + oy1) / 2,
                (oz0 + oz1) / 2), GLASS, bevel=0.0, name="side glass")

    # --- Back: oak-veneered inside, tempered hardboard outside ---------------------
    bx = CX - FF_T
    top_z0 = H - TOP_T
    kit.box((2 * bx, 0.004, top_z0 - 0.004), (0, YB - 0.002, (top_z0 + 0.004) / 2), BACK, bevel=0.0,
            name="back panel")
    kit.quad(2 * bx, CROWN_Z - PLINTH_H, (0, YB - 0.0042, (CROWN_Z + PLINTH_H) / 2), OAK, facing="-y", uv="metres",
             name="back veneer")

    # --- Interior: deck, ceiling, puck light, glass shelves ----------------------
    deck_z = OPEN_Z0 - 0.005
    kit.box((2 * bx, YB - 0.004 - ff_y, 0.020), (0, (ff_y + YB - 0.004) / 2, deck_z - 0.010), OAK, bevel=0.0,
            name="deck")
    ceil_z = sz1 - MEMBER
    ceil = kit.quad(2 * bx, YB - 0.004 - ff_y, (0, (ff_y + YB - 0.004) / 2, ceil_z), OAK, facing="+z", uv="metres",
                    name="ceiling")
    ceil.rotation_euler = (3.14159265, 0, 0)        # face down, seen through the glass
    kit.cylinder(0.034, 0.012, (0, 0.03, ceil_z - 0.006), BRASS, verts=12, bevel=0.0, name="puck light")
    gap = (ceil_z - deck_z) / 4
    shelf_y0, shelf_y1 = ff_y + 0.012, YB - 0.012
    for k in range(1, 4):
        z = deck_z + gap * k
        kit.box((2 * bx - 0.004, shelf_y1 - shelf_y0, 0.008), (0, (shelf_y0 + shelf_y1) / 2, z), GLASS, bevel=0.0,
                name="glass shelf")

    # --- Doors: inset, mitred frames round the glass --------------------------------
    rv = 0.0025
    door_z0, door_z1 = OPEN_Z0 + rv, OPEN_Z1 - rv
    ox = CX - STILE
    for sx in (-1, 1):
        x_out, x_in = sx * (ox - rv), sx * (rv / 2)
        dx0, dx1 = min(x_out, x_in), max(x_out, x_in)
        gx0, gx1 = dx0 + MEMBER, dx1 - MEMBER
        gz0, gz1 = door_z0 + MEMBER, door_z1 - MEMBER
        nc.sweep(kit, nc.rect_path(gx0, gx1, gz0, gz1), FRAME_PROFILE, OAK, facing="-y", origin=(0, ff_y, 0),
                 closed=True, split=True, name="door frame")
        kit.box((gx1 - gx0 + 0.012, 0.003, gz1 - gz0 + 0.012), ((gx0 + gx1) / 2, ff_y - 0.0055, (gz0 + gz1) / 2),
                GLASS, bevel=0.0, name="door glass")
        nc.knob(kit, sx * (rv / 2 + MEMBER / 2), 0.98, YF, BRASS, scale=0.8)
        if sx > 0:
            # Keyhole escutcheon under the knob (the doors lock).
            esc = [(rv / 2 + MEMBER / 2 + 0.0075 * math.cos(2 * math.pi * k / 8),
                    0.925 + 0.012 * math.sin(2 * math.pi * k / 8)) for k in range(8)]
            nc._flat(kit, esc, YF - 0.0006, BRASS, "escutcheon")
        for hz in (door_z0 + 0.16, door_z1 - 0.16):
            nc.knuckle(kit, x_out + sx * 0.0005, YF - 0.0025, hz, 0.050, BRASS, radius=0.0038)

    # --- Crown and top --------------------------------------------------------------
    crown = [(-0.012, 0.0), (0.0, 0.0), (0.0035, 0.003), (0.0045, 0.0075), (0.0065, 0.0115), (0.0125, 0.017),
             (0.0205, 0.0235), (0.0275, 0.0315), (0.0315, 0.042), (0.0325, 0.058), (-0.012, 0.058)]
    nc.sweep(kit, nc.three_sides(CX, YF, YB), crown, OAK, facing="+z", origin=(0, 0, CROWN_Z), name="crown")
    core_y0, core_y1 = YF + FF_T, YB - 0.005
    kit.box((2 * CX - 0.02, core_y1 - core_y0, top_z0 - (CROWN_Z - 0.04)),
            (0, (core_y0 + core_y1) / 2, (top_z0 + CROWN_Z - 0.04) / 2), OAK, bevel=0.0, name="crown core")
    nc.plate(kit, W, D, nc.rounded(TOP_T, 0.007), (0, 0, top_z0), OAK, facing="+z", name="top", grain="x")

    # --- Metadata -------------------------------------------------------------------
    kit.support("top", (0, 0, H), (W - 0.04, D - 0.04))
    kit.anchor("top", (0, 0, H))
    for k in range(1, 4):
        kit.anchor("shelf %d" % k, (0, (shelf_y0 + shelf_y1) / 2, deck_z + gap * k + 0.003))
    kit.collider((0, 0, H / 2), (W, D, H))
    kit.tag("domestic", "case_goods", "pile", "pile_piece", "glass")
    kit.pile("Case", mass=2, states=["Upright", "Back", "Side", "EdgeLean"], palette="domestic70s")

    nc.scatter(kit, 1806, (OAK, BACK))
    nc.lod1_sharp(kit, SMOOTH_ANGLE)
