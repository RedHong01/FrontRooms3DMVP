"""Small cherry rolling cabinet / mini-bar cube on casters (the satellite piece
standing alone at the right of A24 "Backrooms" Still A).

Real-world reference: late-1970s/80s mass-market bedroom or den cabinet,
cherry veneer, one overlay drawer over one five-piece raised-panel door hung
on small brass butt hinges, brass mushroom knobs, base moulding, hardboard
back, four plate casters (brass swivel plate and fork, 50 mm black wheel) set
right at the corners so the wheels show past the moulding.

Budget pass (2026-10-02, §5.3: 900 LOD0 / 400 LOD1; fix pass: resized to the
§5.3 0.50 x 0.45 x 0.62):
* slots: Prop_WoodCherry, Prop_Brass, Prop_Rubber (wheels), Prop_Hardboard
  (back panel, the dark carcass face seen through the shut lines, the raw
  underside). The paper maker's label is gone (it was a 5th slot).
* the carcass is one cherry box; the hardboard back and the dark front are
  quads on its faces. Fronts keep their 1-segment eased edges and the door
  keeps its separate stiles, rails and raised panel (the joint lines).
* casters: plate, one tapered fork yoke and a 10-sided wheel (~68 tris).

Size (§5.3): 0.50 m wide, 0.45 m deep (body; the knobs stand 26 mm proud and
the trailing wheels reach 7 mm past front and back), 0.62 m tall including
65 mm casters. Front (drawer + door) looks -Y. Wood grain follows each
board's length (kitlib; _pilecases_grain.install transposes it for the
cherry albedo, grain on U, and fixes the LOD1 sharp edges), each board on its
own patch of veneer.
"""

import math

import _pilecases_grain as grain

NAME = "Kit_RollingCabinet"
LOD1 = 0.42
SMOOTH_ANGLE = 40.0        # 8/10-sided knobs and wheels shade round; 45-degree chamfers stay crisp

CHERRY = "Prop_WoodCherry"
BRASS = "Prop_Brass"
RUBBER = "Prop_Rubber"
BACK = "Prop_Hardboard"    # tempered hardboard back, dark interior, raw underside

W, D, H = 0.50, 0.45, 0.62
CASTER_H = 0.065
SIDE_T = 0.018
CX = 0.244                 # outer half-width of the carcass
Y_CAR = -0.205             # carcass front edge (fronts lie on it)
Y_BACK = 0.223
FRONT_T = 0.020
Y_FACE = Y_CAR - FRONT_T   # -0.225
TOP_T = 0.022
BASE_H = 0.025
Y_LO = Y_FACE - 0.0315     # knob tips
Y_DEPTH = 0.2300 - Y_LO    # to the back wheels' trailing edge (sidecar bounds)


def _knob(kit, x, y, z, scale=1.0):
    """Brass mushroom knob, axis along -Y, base on the face at y."""
    s = scale
    prof = [(0.0115 * s, 0.0), (0.0055 * s, 0.008 * s), (0.0145 * s, 0.020 * s),
            (0.0120 * s, 0.028 * s), (0.0, 0.0315 * s)]
    kit.lathe(prof, (x, y, z), BRASS, verts=8, rot=(90, 0, 0), close_bottom=False, name="knob")


def _caster(kit, x, y, trail):
    """Plate caster: brass top plate, swivel fork, 50 mm black wheel.
    trail: wheel axle offset along Y from the swivel axis (points outward)."""
    top = CASTER_H
    r = 0.025                                   # wheel radius
    wz = r * math.cos(math.pi / 10)             # 10-gon: a flat, not a corner, rests on the floor
    kit.box((0.046, 0.046, 0.003), (x, y, top - 0.0015), BRASS, bevel=0.0, name="caster plate")
    # Fork seen side-on: wide at the axle, narrowing up to the swivel under
    # the plate (which sits `trail` back from the axle).
    z0 = wz - 0.010
    ch = top - 0.003 - z0
    t = -trail
    outline = [(-0.0135, 0.0), (0.0135, 0.0), (0.0135, 0.012), (t + 0.009, ch), (t - 0.009, ch), (-0.0135, 0.012)]
    kit.extrude(outline, 0.024, (x, y + trail, z0), BRASS, plane="yz", bevel=0.0, name="caster fork")
    kit.cylinder(r, 0.018, (x, y + trail, wz), RUBBER, verts=10, rot=(0, 90, 0), bevel=0.0, name="wheel")


def build(kit):
    body_z0 = CASTER_H
    top_z0 = H - TOP_T
    car_d = Y_BACK - Y_CAR
    car_yc = (Y_BACK + Y_CAR) / 2
    side_z0 = body_z0 + BASE_H
    side_h = top_z0 - side_z0
    car_zc = side_z0 + side_h / 2

    # --- Carcass ---------------------------------------------------------
    kit.box((2 * CX, car_d, side_h), (0, car_yc, car_zc), CHERRY, bevel=0.002, segments=1, name="carcass")
    # Hardboard back (the cherry side edges frame it) and the dark carcass
    # face behind the fronts, read through the 3 mm shut lines.
    kit.quad(2 * CX - 0.020, side_h - 0.012, (0, Y_BACK + 0.0006, car_zc), BACK, facing="+y", uv="metres",
             name="back panel")
    kit.quad(2 * CX - 0.006, side_h - 0.006, (0, Y_CAR - 0.0006, car_zc), BACK, facing="-y", uv="metres",
             name="interior shadow")
    # Base moulding: a slightly proud skirt the casters screw into, and the
    # raw underside inside it.
    kit.box((2 * CX + 0.008, Y_BACK - Y_FACE + 0.004, BASE_H), (0, (Y_BACK + Y_FACE - 0.004) / 2, body_z0 + BASE_H / 2),
            CHERRY, bevel=0.005, segments=1, name="base moulding")
    kit.box((2 * CX - 0.03, Y_BACK - Y_FACE - 0.03, 0.001), (0, (Y_BACK + Y_FACE) / 2, body_z0 - 0.0006), BACK,
            bevel=0.0, name="underside")
    # Top: overhangs 6 mm, rounded edge.
    kit.box((W, Y_BACK - Y_FACE + 0.006, TOP_T), (0, (Y_BACK + Y_FACE - 0.006) / 2 + 0.001, top_z0 + TOP_T / 2), CHERRY,
            bevel=0.007, segments=2, name="top")

    # --- Fronts ------------------------------------------------------------
    gap = 0.003
    fw = 2 * CX - 0.003
    z_lo = side_z0 + gap
    z_hi = top_z0 - gap
    drawer_h = 0.118
    door_h = z_hi - z_lo - drawer_h - gap
    y_mid = Y_CAR - FRONT_T / 2
    # Drawer: slab with an eased edge.
    dz = z_hi - drawer_h / 2
    kit.box((fw, FRONT_T, drawer_h), (0, y_mid, dz), CHERRY, bevel=0.005, segments=1, name="drawer front")
    _knob(kit, 0, Y_FACE, dz, scale=1.0)
    # Door: five-piece frame with a raised centre panel. Stiles run full
    # height (vertical grain); rails run between them (horizontal grain),
    # their ends buried in the stiles and their faces 0.6 mm shy, so each
    # joint reads as a fine line against the stile's eased edge.
    cz = z_lo + door_h / 2
    rail = 0.058
    for sx in (-1, 1):
        kit.box((rail, FRONT_T, door_h), (sx * (fw / 2 - rail / 2), y_mid, cz), CHERRY,
                bevel=0.004, segments=1, name="door stile")
    for sz in (-1, 1):
        kit.box((fw - rail, FRONT_T - 0.0012, rail), (0, y_mid, cz + sz * (door_h / 2 - rail / 2)), CHERRY,
                bevel=0.004, segments=1, name="door rail")
    iw, ih = fw - 2 * rail, door_h - 2 * rail
    panel = kit.loft_box((iw - 0.05, ih - 0.05), (iw + 0.006, ih + 0.006), 0.010, (0, Y_FACE + 0.010, cz), CHERRY,
                         bevel=0.002, segments=1, name="raised panel")
    panel["fr_grain"] = "z"          # glued-up panel, grain vertical like the stiles
    _knob(kit, fw / 2 - 0.035, Y_FACE, z_lo + door_h - 0.05, scale=0.92)
    # Brass butt hinge knuckles on the left edge of the door.
    for hz in (z_lo + 0.06, z_lo + door_h - 0.06):
        kit.cylinder(0.0042, 0.048, (-fw / 2 - 0.0012, Y_CAR - 0.002, hz), BRASS, verts=6, bevel=0.0,
                     name="hinge knuckle")

    # --- Casters ---------------------------------------------------------
    # Plates flush with the carcass sides; wheels trail outward so the front
    # pair shows ~7 mm past the base moulding.
    for sx in (-1, 1):
        _caster(kit, sx * (CX - 0.023), Y_CAR + 0.002, trail=-0.008)
        _caster(kit, sx * (CX - 0.023), Y_BACK - 0.026, trail=0.008)

    # --- Metadata --------------------------------------------------------
    kit.support("top", (0, 0, H), (W - 0.02, D - 0.02))
    kit.anchor("top", (0, 0, H))
    kit.collider((0, Y_LO + Y_DEPTH / 2, H / 2), (W, Y_DEPTH, H))   # body, knobs, wheels: one box (§5.3)
    kit.tag("domestic", "case_goods", "pile", "pile_piece")
    kit.pile("Case", mass=1, palette="domestic70s", states=["Upright", "Side"])

    # Each board on its own patch of veneer (grain direction: kitlib).
    grain.scatter_offsets(kit, seed=5112, slots=(CHERRY,), tile=(1.0, 1.0))  # Cherry TileSize 1.0 m
    grain.install(kit, SMOOTH_ANGLE)
