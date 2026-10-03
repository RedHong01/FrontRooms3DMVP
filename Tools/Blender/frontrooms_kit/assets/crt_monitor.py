"""Beige 15" CRT monitor, c. 1987-96 (the generic office VGA tube: tilt/swivel
plinth, thick lower bezel with thumbwheels, tapered tube housing, rear vents).

Real-world reference size: 0.37 m wide, 0.40 m tall on its plinth, 0.40 m
deep. Sits on a desk or on a desktop PC case (origin = underside of plinth).
Front (screen) faces -Y. Exemplar module for the kit: read it before writing
another asset.
"""

NAME = "Kit_CRTMonitor"
LOD1 = 0.42

BEIGE = "Prop_PlasticBeige"
DARK = "Prop_PlasticGrey"
BLACK = "Prop_PlasticBlack"


def build(kit):
    # Tilt/swivel plinth: a rounded slab and a short neck.
    kit.box((0.25, 0.23, 0.024), (0, 0.02, 0.012), BEIGE, bevel=0.03, segments=4, name="plinth")
    kit.box((0.13, 0.11, 0.04), (0, 0.03, 0.044), BEIGE, bevel=0.012, segments=3, name="swivel neck")

    casing_bottom = 0.062
    casing_h = 0.345
    zc = casing_bottom + casing_h / 2
    # Bezel: one frame with the screen opening set high (thick chin for buttons).
    opening_w, opening_h = 0.300, 0.228
    chin = 0.072
    opening_cz = casing_bottom + chin + opening_h / 2
    kit.frame((0.372, casing_h), (opening_w, opening_h), 0.036, (0, -0.187, zc), BEIGE,
              inner_offset=(0, opening_cz - zc), bevel=0.012, segments=3, name="bezel")
    # Casing block behind the bezel and the tapered tube housing.
    kit.box((0.362, 0.10, 0.337), (0, -0.12, zc), BEIGE, bevel=0.01, segments=2, name="front casing")
    kit.loft_box((0.345, 0.315), (0.215, 0.175), 0.25, (0, 0.05, zc - 0.005), BEIGE,
                 back_offset=(0, 0.035), bevel=0.012, segments=3, name="tube housing")
    kit.box((0.205, 0.035, 0.16), (0, 0.185, zc + 0.03), BEIGE, bevel=0.01, segments=2, name="rear cap")
    # Rear vents: dark slots on the cap.
    for i in range(7):
        kit.box((0.15, 0.004, 0.006), (0, 0.2035, zc - 0.03 + i * 0.016), BLACK, bevel=0.0, name="rear vent")

    # Glass: a slightly convex face recessed 22 mm behind the bezel front.
    kit.box((opening_w + 0.004, 0.02, opening_h + 0.004), (0, -0.168, opening_cz), BLACK, bevel=0.0, name="tube surround")
    kit.bulged_panel(opening_w - 0.002, opening_h - 0.002, 0.012, (0, -0.183, opening_cz), "Prop_ScreenCRT", name="screen glass")

    # Chin details: power button with its recess, two knurled brightness/contrast
    # thumbwheels (push-button OSDs are c. 1993+; era lock = 1990), badge.
    chin_z = casing_bottom + chin * 0.5
    kit.box((0.034, 0.006, 0.020), (0.135, -0.2055, chin_z), DARK, bevel=0.002, name="power recess")
    kit.box((0.026, 0.008, 0.013), (0.135, -0.209, chin_z), BEIGE, bevel=0.003, name="power button")
    for k in range(2):
        wx = -0.135 + k * 0.030
        kit.box((0.022, 0.008, 0.024), (wx, -0.2050, chin_z), DARK, bevel=0.002, name="thumbwheel slot")
        kit.cylinder(0.0105, 0.007, (wx, -0.2025, chin_z), DARK, verts=18, rot=(0, 90, 0), bevel=0.001, segments=1, name="thumbwheel")
    kit.box((0.06, 0.003, 0.010), (0, -0.2065, chin_z + 0.004), DARK, bevel=0.001, name="badge")

    # Power and video cables drooping off the back to the desk.
    # They leave the underside of the rear cap, sag and lie on the desk.
    kit.tube([(0.035, 0.175, zc - 0.045), (0.038, 0.196, zc - 0.075), (0.042, 0.212, 0.10), (0.046, 0.222, 0.03),
              (0.05, 0.236, 0.0045), (0.058, 0.275, 0.0035), (0.07, 0.31, 0.0035)], 0.0032, BLACK, name="power cable")
    kit.tube([(-0.035, 0.175, zc - 0.05), (-0.04, 0.194, zc - 0.085), (-0.046, 0.208, 0.09), (-0.05, 0.218, 0.025),
              (-0.054, 0.232, 0.005), (-0.064, 0.27, 0.004), (-0.08, 0.30, 0.004)], 0.0038, BLACK, name="video cable")

    top = casing_bottom + casing_h
    kit.support("top", (0, -0.14, top), (0.33, 0.09))
    kit.anchor("screen", (0, -0.19, opening_cz))
    kit.collider((0, 0.0, 0.22), (0.372, 0.41, 0.44))
    kit.tag("office", "electronics", "desk_top", "pile_piece")
    kit.pile("Screen", mass=1, palette="office90s", topper=True)
