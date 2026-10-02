"""Freestanding 1990s systems-furniture partition panel, 60" wide x 62" tall
(the blue-grey fabric cubicle wall in Red's target office image).

Real-world reference: Steelcase Series 9000 / Haworth Unigroup-era acoustic
panels. 1.524 m wide, 1.57 m tall, 65 mm thick. Fabric-wrapped tackable core
on BOTH faces, set 4 mm inside a moulded frame: rounded top cap rail, round
vertical end trims with slotted hang-on standards beside them, and a 100 mm
base raceway cover with duplex-outlet knockouts, standing on two screw-in
levelling glides. Both faces (-Y and +Y) are identical. The frame (cap,
trims, standards, raceway) is warm putty painted steel, lighter and warmer
than the blue-grey fabric, as in the target image.

``build_panel(kit, width)`` is shared with cubicle_panel_short.py.
"""

import math

NAME = "Kit_CubiclePanel"

FABRIC = "Prop_FabricCubicle"
TRIM = "Prop_SteelPutty"    # putty frame (swap to Prop_PlasticPutty if requested)
BLACK = "Prop_PlasticBlack"
CHROME = "Prop_Chrome"

H = 1.57
T = 0.065
TRIM_W = 0.030          # vertical end trim (X)
STRIP_W = 0.016         # slotted standard beside each trim
FABRIC_INSET = 0.004    # fabric face below the trim face
RACE_Z0, RACE_H = 0.024, 0.100
CAP_TOP_H = 0.026       # cap height above the panel body
CAP_LIP = 0.008         # cap sides overlap the fabric this far


def _cap_profile():
    """Rounded top-cap section in (y, z): flat sides that lap over the
    fabric, then a flattened arch. z = 0 is the body top."""
    half = T / 2 + 0.0015
    pts = [(half, -CAP_LIP), (half, 0.006)]
    steps = 10
    for i in range(1, steps):
        a = math.pi * i / steps
        pts.append((half * math.cos(a), 0.006 + (CAP_TOP_H - 0.006) * math.sin(a)))
    pts += [(-half, 0.006), (-half, -CAP_LIP)]
    return pts


def build_panel(kit, width):
    hw = width / 2
    body_top = H - CAP_TOP_H
    race_top = RACE_Z0 + RACE_H
    face = T / 2 - FABRIC_INSET          # fabric face |y|
    inner_x = hw - TRIM_W                # inside face of the end trims

    # Top cap rail: one extrusion along X, flush with the trim ends.
    kit.extrude(_cap_profile(), width, (0, 0, body_top), TRIM, plane="yz", bevel=0.003, segments=2, name="top cap")

    # Vertical end trims (rounded on all four long edges).
    trim_h = body_top - RACE_Z0 + 0.004
    for sx in (-1, 1):
        x = sx * (hw - TRIM_W / 2)
        kit.box((TRIM_W, T, trim_h), (x, 0, RACE_Z0 + trim_h / 2 - 0.002), TRIM, bevel=0.011, segments=3, name="end trim")
        # Screw-in levelling glide under each trim.
        gx = x - sx * 0.003
        kit.cylinder(0.015, 0.010, (gx, 0, 0.005), BLACK, verts=16, bevel=0.003, segments=2, name="glide foot")
        kit.cylinder(0.0065, RACE_Z0 - 0.008, (gx, 0, 0.010 + (RACE_Z0 - 0.008) / 2), CHROME, verts=10, bevel=0.0, name="glide stem")
        kit.cylinder(0.011, 0.004, (gx, 0, RACE_Z0 - 0.003), CHROME, verts=6, bevel=0.0, name="glide nut")

    # Fabric core, both faces, its ends tucked into the trims. Soft bevel =
    # the fabric wrapping round the edge of the tackboard.
    fab_w = 2 * inner_x + 0.006
    fab_z0, fab_z1 = race_top + 0.004, body_top + 0.002
    kit.box((fab_w, 2 * face, fab_z1 - fab_z0), (0, 0, (fab_z0 + fab_z1) / 2), FABRIC, bevel=0.007, segments=3, name="fabric")

    # Slotted standards: a dark channel beside each trim on both faces with a
    # column of 25 mm slots at 50 mm pitch (hang-on shelves and binder bins).
    std_z0, std_z1 = race_top + 0.001, body_top + 0.002
    std_h = std_z1 - std_z0
    slot_z = [race_top + 0.07 + k * 0.05 for k in range(int((body_top - race_top - 0.12) / 0.05) + 1)]
    for sx in (-1, 1):
        sxc = sx * (inner_x - STRIP_W / 2 + 0.002)
        kit.box((STRIP_W + 0.004, 2 * face + 0.002, std_h), (sxc, 0, (std_z0 + std_z1) / 2), TRIM,
                bevel=0.002, segments=1, name="standard")
        # Slots are single-sided quads 0.5 mm off the standard's face (only
        # the front is ever seen), 2 tris each.
        for sy in (-1, 1):
            for z in slot_z:
                kit.quad(0.0045, 0.024, (sxc, sy * (face + 0.0015), z), BLACK,
                         facing="-y" if sy < 0 else "+y", name="standard slot")

    # Base raceway: cover (both faces), a dark reveal under the fabric, and
    # duplex-outlet knockouts on both faces.
    race_w = 2 * inner_x + 0.004
    race_t = T - 0.0035
    kit.box((race_w, race_t, RACE_H), (0, 0, RACE_Z0 + RACE_H / 2), TRIM, bevel=0.006, segments=3, name="raceway cover")
    kit.box((race_w, 2 * face - 0.006, 0.010), (0, 0, race_top + 0.002), BLACK, bevel=0.0, name="raceway reveal")
    kx = hw - min(0.22, width * 0.24)
    for sx in (-1, 1):
        for sy in (-1, 1):
            # Flush scored blank: front faces only 0.6 mm proud of the cover.
            y = sy * (race_t / 2 + 0.0002)
            kz = RACE_Z0 + RACE_H * 0.52
            # (0.8 mm deep: no bevel, it would be sub-millimetre and cost ~450 tris.)
            kit.frame((0.074, 0.044), (0.068, 0.038), 0.0008, (sx * kx, y, kz), BLACK, bevel=0.0,
                      name="knockout score")
            kit.box((0.066, 0.0008, 0.036), (sx * kx, y, kz), TRIM, bevel=0.0, name="knockout plate")
            # Two pry tabs on the knockout.
            for tx in (-0.026, 0.026):
                kit.box((0.008, 0.0010, 0.004), (sx * kx + tx, y, kz + 0.020), BLACK, bevel=0.0, name="knockout tab")
        # Cover fixing screws near each end.
        for sy in (-1, 1):
            kit.cylinder(0.0045, 0.002, (sx * (inner_x - 0.04), sy * (race_t / 2 + 0.0006), RACE_Z0 + RACE_H / 2), CHROME,
                         verts=10, rot=(90, 0, 0), bevel=0.0, name="raceway screw")

    kit.collider((0, 0, H / 2), (width, T, H))
    kit.anchor("top_centre", (0, 0, H))
    kit.tag("office", "panel")


def build(kit):
    build_panel(kit, 1.524)
