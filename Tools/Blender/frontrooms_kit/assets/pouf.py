"""Round upholstered pouf / drum ottoman, 1980s-90s (Still B: the navy pouf
on the top surface of the tower; the colour accent of the pile).

One soft lathe: a stuffed barrel whose sides bulge and roll softly into a
domed top panel, a piped top seam (a shallow bead in the profile), the
centre pulled down by a single tufting button, and a recessed base so it
sits on a shadow line. One closed mesh inside the 800-tri budget.

Real-world reference size: diameter 0.50 m, height 0.40 m.
Front faces -Y (it is round; the lathe seam and the slight lean sit at the back).
Slot: Prop_FabricNavy. No collider (pile "Small" piece / soft clutter).
"""

import math

NAME = "Kit_Pouf"
LOD1 = 0.39
SMOOTH_ANGLE = 85.0

FABRIC = "Prop_FabricNavy"

# (radius, z) bottom to top: a stuffed barrel rolling softly into a domed
# top panel; the top seam's piping is a shallow bead on that roll, and the
# centre is pulled down by a button tuft. SMOOTH_ANGLE 85 keeps it all soft.
PROFILE = [
    (0.205, 0.000),                                   # recessed base
    (0.233, 0.014),                                   # bottom roll
    (0.2475, 0.060),
    (0.2515, 0.170), (0.2490, 0.280),                 # stuffed, bulging side
    (0.2400, 0.338),                                  # shoulder
    (0.2425, 0.352),                                  # top seam piping
    (0.2270, 0.372),                                  # top roll
    (0.1850, 0.392), (0.1050, 0.403),                 # domed top panel
    (0.0400, 0.396),
    (0.0130, 0.384),                                  # pulled into the tuft
    (0.0, 0.387),                                     # button
]


def build(kit):
    obj = kit.lathe(PROFILE, (0, 0, 0), FABRIC, verts=32, rot=(0, 0, 90), name="pouf")
    # Hand-stuffed, not turned: a faint lean of the crown and a soft squash.
    for v in obj.data.vertices:
        t = v.co.z / 0.40
        v.co.x *= 1.0 + 0.006 * t
        v.co.y *= 0.994
        v.co.x += 0.004 * t * t
    kit.no_collider()
    kit.support("top", (0, 0, 0.400), (0.30, 0.30))
    kit.anchor("sit", (0, 0, 0.400))
    kit.tag("domestic", "upholstery", "pile_piece")
    kit.pile("Small", mass=0, palette="domestic70s")
