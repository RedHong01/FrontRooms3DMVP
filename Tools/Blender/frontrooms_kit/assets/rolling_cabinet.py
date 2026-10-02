"""Small cherry rolling cabinet / mini-bar cube on casters (the satellite piece
standing alone at the right of A24 "Backrooms" Still A).

Real-world reference: late-1970s/80s mass-market bedroom or den cabinet,
cherry veneer, one overlay drawer over one five-piece raised-panel door hung
on small brass butt hinges, brass mushroom knobs, base moulding, hardboard
back, four plate casters (brass swivel plate and fork, 50 mm black plastic
wheel) set right at the corners so the wheels show past the moulding.

Size: 0.45 m wide, 0.40 m deep (body; the trailing wheels reach 7 mm past
front and back), 0.62 m tall including 65 mm casters.
Front (drawer + door) looks -Y. Wood grain follows each board's length via
_pilecases_grain (horizontal on the drawer front and top).
"""

import _pilecases_grain as grain

NAME = "Kit_RollingCabinet"
SMOOTH_ANGLE = 40.0        # 10-vert hinge knuckles render smooth

CHERRY = "Prop_WoodCherry"
DARK = "Prop_WoodDark"
BRASS = "Prop_Brass"
BLACK = "Prop_PlasticBlack"
BACK = "Prop_WoodDark"     # tempered hardboard; move to Prop_Hardboard when that slot exists
RAW = "Prop_Chipboard"     # raw particleboard underside

W, D, H = 0.45, 0.40, 0.62
CASTER_H = 0.065
SIDE_T = 0.018
CX = 0.219                 # outer half-width of the carcass sides
Y_CAR = -0.180             # carcass front edge (fronts lie on it)
Y_BACK = 0.198
FRONT_T = 0.020
Y_FACE = Y_CAR - FRONT_T   # -0.200
TOP_T = 0.022
BASE_H = 0.025


def _knob(kit, x, y, z, scale=1.0):
    """Brass mushroom knob, axis along -Y, base on the face at y."""
    s = scale
    prof = [(0.0125 * s, 0.0), (0.0125 * s, 0.002 * s), (0.008 * s, 0.004 * s), (0.0055 * s, 0.010 * s),
            (0.0060 * s, 0.015 * s), (0.0120 * s, 0.019 * s), (0.0150 * s, 0.023 * s),
            (0.0145 * s, 0.027 * s), (0.0100 * s, 0.0305 * s), (0.0, 0.0315 * s)]
    kit.lathe(prof, (x, y, z), BRASS, verts=16, rot=(90, 0, 0), name="knob")


def _caster(kit, x, y, trail):
    """Plate caster: brass top plate + swivel race + fork, 50 mm black wheel.
    trail: wheel axle offset along Y from the swivel axis (points outward)."""
    top = CASTER_H
    r = 0.025                                   # wheel radius
    kit.box((0.046, 0.046, 0.003), (x, y, top - 0.0015), BRASS, bevel=0.0012, segments=1, name="caster plate")
    kit.cylinder(0.0165, 0.006, (x, y, top - 0.006), BRASS, verts=16, bevel=0.0015, segments=1, name="swivel race")
    # Fork: crown under the race, two cheek plates down to the trailing axle.
    kit.box((0.030, 0.030, 0.004), (x, y + trail * 0.5, top - 0.0105), BRASS, bevel=0.0015, segments=1, name="fork crown")
    cheek_z0 = r - 0.012
    ch = top - 0.0125 - cheek_z0
    for sx in (-1, 1):
        kit.extrude([(-0.0135, 0.0), (0.0135, 0.0), (0.0135, 0.016), (0.008, ch), (-0.008, ch), (-0.0135, 0.016)],
                    0.0022, (x + sx * 0.0115, y + trail, cheek_z0), BRASS, plane="yz", bevel=0.0007, segments=1,
                    name="fork cheek")
    # Wheel, hub, axle rivets.
    kit.cylinder(r, 0.018, (x, y + trail, r), BLACK, verts=20, rot=(0, 90, 0), bevel=0.005, segments=2, name="wheel")
    kit.cylinder(0.010, 0.0195, (x, y + trail, r), BRASS, verts=12, rot=(0, 90, 0), bevel=0.001, segments=1, name="wheel hub")
    for sx in (-1, 1):
        kit.cylinder(0.0035, 0.004, (x + sx * 0.0146, y + trail, r), BRASS, verts=8, rot=(0, 90, 0), bevel=0.001,
                     segments=1, name="axle rivet")


def build(kit):
    body_z0 = CASTER_H
    top_z0 = H - TOP_T
    car_d = Y_BACK - Y_CAR
    car_yc = (Y_BACK + Y_CAR) / 2

    # --- Carcass ---------------------------------------------------------
    side_h = top_z0 - (body_z0 + BASE_H)
    for sx in (-1, 1):
        kit.box((SIDE_T, car_d, side_h), (sx * (CX - SIDE_T / 2), car_yc, body_z0 + BASE_H + side_h / 2), CHERRY,
                bevel=0.002, segments=2, name="side panel")
    # Base moulding: a slightly proud, rounded skirt the casters screw into.
    kit.box((2 * CX + 0.008, Y_BACK - Y_FACE + 0.004, BASE_H), (0, (Y_BACK + Y_FACE - 0.004) / 2, body_z0 + BASE_H / 2),
            CHERRY, bevel=0.007, segments=3, name="base moulding")
    # Raw particleboard underside showing inside the moulding (caster plates hide its edge).
    kit.box((2 * CX - 0.03, Y_BACK - Y_FACE - 0.03, 0.0008), (0, (Y_BACK + Y_FACE) / 2, body_z0 - 0.0006), RAW,
            bevel=0.0, name="underside")
    # Top: overhangs 6 mm, rounded edge.
    kit.box((W, Y_BACK - Y_FACE + 0.006, TOP_T), (0, (Y_BACK + Y_FACE - 0.006) / 2 + 0.001, top_z0 + TOP_T / 2), CHERRY,
            bevel=0.007, segments=3, name="top")
    # Hardboard back in a rabbet, with a small maker's label.
    kit.box((2 * CX - 0.012, 0.005, side_h - 0.006), (0, Y_BACK - 0.0045, body_z0 + BASE_H + side_h / 2), BACK,
            bevel=0.001, name="back panel")
    # Back panel's outer face is at Y_BACK - 0.002; the paper label sits 0.6 mm proud of it.
    kit.quad(0.08, 0.05, (-0.09, Y_BACK - 0.0014, 0.47), "Prop_Paper", facing="+y", name="maker label")
    # Dark carcass interior behind the shut lines.
    kit.box((2 * (CX - SIDE_T) - 0.002, 0.02, side_h - 0.004), (0, Y_CAR + 0.012, body_z0 + BASE_H + side_h / 2), DARK,
            bevel=0.0, name="interior shadow")

    # --- Fronts ------------------------------------------------------------
    gap = 0.003
    fw = 2 * CX - 0.003
    z_lo = body_z0 + BASE_H + gap
    z_hi = top_z0 - gap
    drawer_h = 0.118
    door_h = z_hi - z_lo - drawer_h - gap
    y_mid = Y_CAR - FRONT_T / 2
    # Drawer: slab with a routed edge.
    dz = z_hi - drawer_h / 2
    kit.box((fw, FRONT_T, drawer_h), (0, y_mid, dz), CHERRY, bevel=0.005, segments=3, name="drawer front")
    _knob(kit, 0, Y_FACE, dz, scale=1.0)
    # Door: five-piece frame with a raised centre panel.
    cz = z_lo + door_h / 2
    rail = 0.058
    # Stiles run full height (vertical grain); rails run between them
    # (horizontal grain), their ends buried in the stiles and their faces
    # 0.6 mm shy, so each joint reads as a fine line against the stile's eased edge.
    for sx in (-1, 1):
        kit.box((rail, FRONT_T, door_h), (sx * (fw / 2 - rail / 2), y_mid, cz), CHERRY,
                bevel=0.005, segments=2, name="door stile")
    for sz in (-1, 1):
        kit.box((fw - rail, FRONT_T - 0.0012, rail), (0, y_mid, cz + sz * (door_h / 2 - rail / 2)), CHERRY,
                bevel=0.005, segments=2, name="door rail")
    iw, ih = fw - 2 * rail, door_h - 2 * rail
    panel = kit.loft_box((iw - 0.05, ih - 0.05), (iw + 0.006, ih + 0.006), 0.010, (0, Y_FACE + 0.010, cz), CHERRY,
                         bevel=0.002, segments=1, name="raised panel")
    panel["fr_grain"] = "z"          # glued-up panel, grain vertical like the stiles
    _knob(kit, fw / 2 - 0.035, Y_FACE, z_lo + door_h - 0.05, scale=0.92)
    # Brass butt hinge knuckles on the left edge of the door.
    for hz in (z_lo + 0.06, z_lo + door_h - 0.06):
        kit.cylinder(0.0042, 0.048, (-fw / 2 - 0.0012, Y_CAR - 0.002, hz), BRASS, verts=10, bevel=0.001, segments=1,
                     name="hinge knuckle")

    # --- Casters ---------------------------------------------------------
    # Plates flush with the carcass sides; wheels trail outward so the front
    # pair shows ~7 mm past the base moulding.
    for sx in (-1, 1):
        _caster(kit, sx * (CX - 0.023), -0.178, trail=-0.008)
        _caster(kit, sx * (CX - 0.023), 0.172, trail=0.008)

    # --- Metadata --------------------------------------------------------
    kit.support("top", (0, 0, H), (0.43, 0.38))
    kit.anchor("top", (0, 0, H))
    kit.collider((0, 0, body_z0 + (H - body_z0) / 2), (W, D, H - body_z0))
    kit.collider((0, -0.003, CASTER_H / 2), (0.44, 0.40, CASTER_H))
    kit.tag("domestic", "case_goods", "pile", "pile_piece")
    kit.pile("Case", mass=1, palette="domestic70s")

    # Grain along each board, each board on its own patch of veneer.
    grain.scatter_offsets(kit, seed=5112, slots=(CHERRY,))
    grain.install(kit)
