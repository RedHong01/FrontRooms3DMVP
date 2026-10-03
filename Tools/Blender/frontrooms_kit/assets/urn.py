"""Brown-glazed ceramic urn / bulb vase, 1970s (the vase lying on its side
in the low pile of A24 "Backrooms" Still A).

Real-world reference: a thrown stoneware floor/table vase in a glossy
treacle-brown glaze: a turned foot ring, a full bulb that peaks a little
below mid-height, a steep shoulder, a short neck and a rolled, flared lip.
The mouth is open: the profile turns over the lip and runs straight down a
vertical bore to a dark well floor. The bore walls face sideways, so flat
top light never reaches them, and the floor is a separate black disc: the
opening reads as a hole (not a lid) upright and when the vase lies on its
side (Still A).

Size: 0.28 m diameter, 0.38 m tall. Rotationally symmetric (front = -Y by
convention only). Budget 600 / 250 tris (~640 LOD0: the 18-sided bulb needs
9 profile points to hold the glaze highlight without banding), no collider
(rolls loose in piles). Slots: Ceramic, Rubber (matte black well floor).
"""

import math

import bmesh

NAME = "Kit_Urn"
LOD1 = 0.42
SMOOTH_ANGLE = 42.0
VERTS = 18

CERAMIC = "Prop_Ceramic"
WELL = "Prop_Rubber"           # matte (smoothness 0.15), so top light leaves no highlight in the well

# The bulb: an ellipse (r 0.140, half-height 0.125) centred at z 0.158,
# sampled every ~14 deg from -58 deg (z 0.052) to +54.7 deg (z 0.260).
BULB_R, BULB_H, BULB_Z = 0.140, 0.125, 0.158
BULB = [(BULB_R * math.cos(math.radians(a)), BULB_Z + BULB_H * math.sin(math.radians(a)))
        for a in (-58.0 + (54.7 + 58.0) * i / 8 for i in range(9))]

WELL_R, WELL_Z = 0.046, 0.300

PROFILE = [
    (0.058, 0.000),   # foot ring, underside
    (0.066, 0.009),
    (0.061, 0.022),   # groove above the foot
] + BULB + [
    (0.064, 0.298),   # shoulder
    (0.055, 0.336),   # neck
    (0.070, 0.372),   # flared, rolled lip
    (0.062, 0.380),
    (0.050, 0.366),   # over the lip and into the mouth
    (WELL_R, WELL_Z), # straight bore: vertical walls stay unlit
]


def _well_floor(kit):
    """The bore's floor: one flat VERTS-gon on exactly the bore's bottom
    ring (same angles as kit.lathe), facing +Z, in the dark slot."""
    bm = bmesh.new()
    ring = [bm.verts.new((WELL_R * math.cos(2 * math.pi * i / VERTS), WELL_R * math.sin(2 * math.pi * i / VERTS), WELL_Z))
            for i in range(VERTS)]
    face = bm.faces.new(ring)
    face.normal_update()
    if face.normal.z < 0:
        face.normal_flip()
    return kit._new_object("well floor", bm, WELL, "metres", "xy")


def build(kit):
    kit.lathe(PROFILE, (0, 0, 0), CERAMIC, verts=VERTS, close_top=False, name="urn body")
    _well_floor(kit)

    kit.no_collider()
    kit.anchor("mouth", (0, 0, 0.38))
    kit.tag("domestic", "decor", "pile_piece")
    kit.pile("Small", mass=0, palette="domestic70s")
