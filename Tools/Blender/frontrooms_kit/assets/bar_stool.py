"""Wooden kitchen bar stool, 1970s domestic (the lone stool parked beside
the piles in Red's stills, A14 / B17). Solid walnut (§5.3 Kit_BarStool).

Construction:
* Round seat 0.38 m across, 42 mm thick: chamfered underside edge,
  bullnosed rim and a shallow dish (10 mm) where you sit. The four legs
  socket straight into the seat underside (no apron ring).
* Four turned legs on the diagonals, splayed ~12.5 degrees (feet on a 0.56 m
  circle): foot, long swell, bead at the foot ring, neck and shoulder under
  the seat.
* Steam-bent foot ring at 0.28 m (0.52 m outside diameter) on the outside
  of the legs.
* Feet cut level (the ends of splayed legs are trimmed flat to sit on the
  floor) with nail-on chrome glides under them; a paper maker's label
  under the seat (Prop_Label atlas cell 11, seen whenever a pile turns the
  stool over).

Real-world reference size: 0.52 W x 0.52 D (foot ring) x 0.76 H, seat 0.38
dia. Front faces -Y (two legs either side of the front; a stool reads the
same from every side).

Budget (§5.3 1,600 / 700): 1,600 tris LOD0, LOD1 0.43 (~690).
* Seat and foot ring 28 sides (the two big round silhouettes; 1.2-1.6 mm
  chord error), an 8-point ring section, legs 10 sides with only the
  silhouette points of the turning, glides 8 sides; buried ends (leg
  tops, glide tops) left open. A glide's open top must stay inside the
  leg: the leg's foot is levelled (zero tris) so the vertical glide seats
  flush instead of leaving a wedge-shaped sliver under the splayed foot
  (Unity culls back faces, so the sliver showed through the open glide).
* The ring's brass screws (8 mm heads) are gone: below the 5 mm-at-2 m
  rule and they cost a slot. Three slots: Prop_WoodWalnut, Prop_Chrome
  (glides), Prop_Label.

Grain (assets/_seating_grain.py): the seat sets fr_grain "x" (kitlib's
grain-aware metre UVs run the top along X and the rim round horizontally),
the foot ring is "metres_ring" (grain follows the bend, seam at the back) and
the splayed legs "metres_axis" (grain straight down each leg, seam inside).
SMOOTH_ANGLE 50 lets the 10-sided legs and 8-sided glides shade round.
"""

import math

from mathutils import Euler, Vector

import _seating_grain as grain

NAME = "Kit_BarStool"
LOD1 = 0.43            # ~690 of 1,600: §5.3 LOD1 budget 700
SMOOTH_ANGLE = 50.0

WOOD = "Prop_WoodWalnut"
GLIDE = "Prop_Chrome"

SEAT_TOP = 0.760
SEAT_BOTTOM = 0.718
SEAT_R = 0.190
DISH = 0.0104        # dish depth at the seat centre
FOOT_R = 0.280       # leg centre radius at the floor (12.5 deg splay)
TOP_R = 0.122        # leg centre radius at the seat underside
GLIDE_H = 0.005
RING_Z = 0.280

# (radius, fraction of length) from foot to seat; silhouette points only.
LEG = [(0.0160, 0.0), (0.0212, 0.30), (0.0200, 0.352), (0.0245, 0.38), (0.0200, 0.41), (0.0238, 0.77),
       (0.0190, 0.815), (0.0228, 0.95), (0.0180, 1.0)]


def _rot_to(d):
    """Euler (degrees) turning +Z onto direction d."""
    e = Vector((0, 0, 1)).rotation_difference(Vector(d).normalized()).to_euler("XYZ")
    return tuple(math.degrees(a) for a in e)


def _leg_point(a, z):
    """Leg centre at height z on the diagonal at angle a (radians)."""
    r = FOOT_R + (TOP_R - FOOT_R) * (z - GLIDE_H) / (SEAT_BOTTOM - GLIDE_H)
    return Vector((r * math.cos(a), r * math.sin(a), z))


def _level_foot(obj, rot):
    """Slide the lathe's first ring (local z = 0) along the turning axis
    onto the world plane through its centre: a level-cut foot."""
    m = Euler([math.radians(a) for a in rot], "XYZ").to_matrix()
    az = (m @ Vector((0, 0, 1))).z
    for v in obj.data.vertices:
        if abs(v.co.z) < 1e-7:
            v.co.z -= (m @ v.co).z / az
    obj.data.update()
    return obj


def build(kit):
    grain.install(kit)

    # Seat: solid, dished, bullnosed rim, chamfered underside.
    b, t, R = SEAT_BOTTOM, SEAT_TOP, SEAT_R
    # (flat underside closed by one n-gon: 2 tris fewer than a centre fan)
    seat = [(R - 0.044, b), (R - 0.009, b + 0.0025), (R - 0.0005, b + 0.013), (R - 0.0005, b + 0.026),
            (R - 0.006, b + 0.037), (R - 0.020, t), (R - 0.080, t - 0.0058), (0.0, t - DISH)]
    grain.horizontal(kit.lathe(seat, (0, 0, 0), WOOD, verts=28, name="seat"), "x")

    angles = [math.radians(45 + 90 * k) for k in range(4)]
    for k, a in enumerate(angles):
        foot = _leg_point(a, GLIDE_H)
        top = _leg_point(a, SEAT_BOTTOM + 0.006)
        length = (top - foot).length
        rot = _rot_to(top - foot)
        leg = _level_foot(kit.lathe([(r, f * length) for r, f in LEG], tuple(foot), WOOD, verts=10,
                                    rot=rot, name="leg", close_top=False), rot)
        grain.axial(leg, foot, top, out=(math.cos(a), math.sin(a), 0.0))["fr_uv_offset"] = (0.13 * k, 0.29 * k)
        # Nail-on glide: a shallow chrome dome under the level foot, its open
        # top 1 mm up inside the leg (0.0146 < the decagon's 0.0152 flats).
        kit.lathe([(0.0132, 0.0), (0.0146, GLIDE_H + 0.0010)], (foot.x, foot.y, 0.0), GLIDE,
                  verts=8, close_top=False, name="glide")

    # Steam-bent foot ring on the outside of the legs.
    leg_rad, hw, hh = 0.0215, 0.009, 0.013
    rc = _leg_point(angles[0], RING_Z).xy.length + leg_rad + hw - 0.001
    z, c = RING_Z, 0.004
    section = [(rc - hw + c, z - hh), (rc + hw - c, z - hh), (rc + hw, z - hh + c), (rc + hw, z + hh - c),
               (rc + hw - c, z + hh), (rc - hw + c, z + hh), (rc - hw, z + hh - c), (rc - hw, z - hh + c),
               (rc - hw + c, z - hh)]
    grain.ring(kit.lathe(section, (0, 0, 0), WOOD, verts=28, name="foot ring", close_top=False,
                         close_bottom=False), rc)
    r_out = rc + hw

    # Maker's label under the seat (atlas cell 11: furniture maker's label).
    label = kit.quad(0.07, 0.045, (0.0, 0.0, 0.0), "Prop_Label", facing="+z", name="maker label",
                     uv_rect=kit.atlas_cell(11, 4, 4))
    kit._place(label, (0.0, -0.03, SEAT_BOTTOM - 0.0005), (180, 0, 0))

    # ------------------------------------------------------------ metadata
    # Support sits 8 mm into the 10 mm dish so small props rest, not float.
    kit.support("seat", (0, 0, SEAT_TOP - 0.008), (0.26, 0.26))
    kit.anchor("sit", (0, 0, SEAT_TOP - DISH))
    # §5.3: one box, the foot ring's square (seat and legs sit inside it).
    kit.collider((0, 0, SEAT_TOP / 2), (2 * r_out, 2 * r_out, SEAT_TOP))
    kit.tag("pile")
    kit.pile("Seat", mass=0, palette="domestic70s", states=["Upright", "Inverted", "Side"])
