"""Wooden kitchen bar stool, 1970s domestic (the lone stool parked beside
the piles in Red's stills). Solid oak.

Construction:
* Round seat 0.40 m across, 42 mm thick: bevelled underside edge, bullnosed
  rim and a shallow dish (10 mm) where you sit. The four legs socket
  straight into the seat underside (no apron ring).
* Four turned legs on the diagonals, splayed ~12.5 degrees (feet on a 0.56 m
  circle, a 0.43 m square to the outside of the feet): foot, long swell,
  beads at the foot-ring, neck and shoulder under the seat.
* Steam-bent oak foot ring at 0.28 m (0.52 m outside diameter), screwed
  (brass) to the outside of each leg.
* Nail-on glides under the feet; a paper maker's label under the seat
  (seen whenever a pile turns the stool over).

Real-world reference size: 0.52 W x 0.52 D (foot ring) x 0.76 H, seat 0.40
dia. Front faces -Y (two legs either side of the front; a stool reads the
same from every side).

Grain (assets/_seating_grain.py): the seat is fr_uv = "metres_h" (top grain
along X, rim grain horizontal) and the foot ring "metres_ring" (grain follows
the bend, seam at the back), so Prop_WoodOak's DoorVeneer grain no longer
runs across them; the splayed legs are "metres_axis" (grain straight down
each leg, one seam on its inner side). SMOOTH_ANGLE 50 lets
the 12-sided legs and 8-sided glides shade round. ~2.7k tris LOD0, LOD1 = 0.45.
"""

import math

from mathutils import Vector

import _seating_grain as grain

NAME = "Kit_BarStool"
LOD1 = 0.45            # kit-decimated ~1.2k LOD1
SMOOTH_ANGLE = 50.0

OAK = "Prop_WoodOak"

SEAT_TOP = 0.760
SEAT_BOTTOM = 0.718
DISH = 0.0104        # dish depth at the seat centre
FOOT_R = 0.280       # leg centre radius at the floor (12.5 deg splay)
TOP_R = 0.122        # leg centre radius at the seat underside
GLIDE_H = 0.005
RING_Z = 0.280

# (radius, fraction of length) from foot to seat.
LEG = [(0.0160, 0.0), (0.0178, 0.012), (0.0212, 0.30), (0.0202, 0.355), (0.0242, 0.372), (0.0245, 0.392),
       (0.0202, 0.410), (0.0208, 0.66), (0.0238, 0.765), (0.0238, 0.785), (0.0190, 0.815), (0.0230, 0.95),
       (0.0180, 1.0)]


def _rot_to(d):
    """Euler (degrees) turning +Z onto direction d."""
    e = Vector((0, 0, 1)).rotation_difference(Vector(d).normalized()).to_euler("XYZ")
    return tuple(math.degrees(a) for a in e)


def _leg_point(a, z):
    """Leg centre at height z on the diagonal at angle a (radians)."""
    r = FOOT_R + (TOP_R - FOOT_R) * (z - GLIDE_H) / (SEAT_BOTTOM - GLIDE_H)
    return Vector((r * math.cos(a), r * math.sin(a), z))


def build(kit):
    grain.install(kit)

    # Seat: solid, dished, bullnosed rim, chamfered underside.
    b, t = SEAT_BOTTOM, SEAT_TOP
    seat = [(0.0, b), (0.150, b), (0.188, b + 0.0015), (0.196, b + 0.006), (0.1995, b + 0.014),
            (0.2000, b + 0.024), (0.1985, b + 0.033), (0.1945, b + 0.0395), (0.188, t - 0.0005),
            (0.178, t), (0.135, t - 0.0050), (0.075, t - 0.0092), (0.0, t - DISH)]
    grain.horizontal(kit.lathe(seat, (0, 0, 0), OAK, verts=32, name="seat"), "x")

    angles = [math.radians(45 + 90 * k) for k in range(4)]
    for a in angles:
        foot = _leg_point(a, GLIDE_H)
        top = _leg_point(a, SEAT_BOTTOM + 0.006)
        length = (top - foot).length
        grain.axial(kit.lathe([(r, f * length) for r, f in LEG], tuple(foot), OAK, verts=12,
                              rot=_rot_to(top - foot), name="leg"),
                    foot, top, out=(math.cos(a), math.sin(a), 0.0))
        # Nail-on glide: a shallow dome under the foot.
        kit.lathe([(0.0, 0.0), (0.0145, 0.0), (0.0155, 0.002), (0.0140, 0.0042), (0.0, GLIDE_H + 0.0012)],
                  (foot.x, foot.y, 0.0), "Prop_SteelPutty", verts=8, name="glide")

    # Steam-bent oak foot ring on the outside of the legs, one brass screw
    # per leg.
    leg_rad, hw, hh = 0.0215, 0.009, 0.013
    rc = _leg_point(angles[0], RING_Z).xy.length + leg_rad + hw - 0.001
    r_out = rc + hw
    z, c = RING_Z, 0.004
    section = [(rc - hw + c, z - hh), (rc + hw - c, z - hh), (rc + hw, z - hh + c), (rc + hw, z + hh - c),
               (rc + hw - c, z + hh), (rc - hw + c, z + hh), (rc - hw, z + hh - c), (rc - hw, z - hh + c),
               (rc - hw + c, z - hh)]
    grain.ring(kit.lathe(section, (0, 0, 0), OAK, verts=32, name="foot ring", close_top=False,
                         close_bottom=False), rc)
    for a in angles:
        p = Vector((math.cos(a), math.sin(a), 0)) * r_out
        kit.cylinder(0.0042, 0.003, (p.x, p.y, z), "Prop_Brass", verts=6, bevel=0.0,
                     rot=_rot_to((math.cos(a), math.sin(a), 0)), name="ring screw")

    # Maker's label under the seat.
    label = kit.quad(0.07, 0.045, (0.0, 0.0, 0.0), "Prop_Label", facing="+z", name="maker label")
    kit._place(label, (0.0, -0.03, SEAT_BOTTOM - 0.0005), (180, 0, 0))

    # ------------------------------------------------------------ metadata
    # Support sits 8 mm into the 10 mm dish so small props rest, not float.
    kit.support("seat", (0, 0, SEAT_TOP - 0.008), (0.26, 0.26))
    kit.anchor("sit", (0, 0, SEAT_TOP - DISH))
    kit.collider((0, 0, (SEAT_BOTTOM + SEAT_TOP) / 2), (0.40, 0.40, SEAT_TOP - SEAT_BOTTOM))
    kit.collider((0, 0, SEAT_BOTTOM / 2), (2 * r_out, 2 * r_out, SEAT_BOTTOM))
    kit.tag("pile")
    kit.pile("Seat", mass=0, palette="domestic70s", states=["Upright", "Inverted", "Side"])
