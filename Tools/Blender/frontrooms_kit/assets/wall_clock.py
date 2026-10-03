"""1990s office wall clock: the battery quartz clock above every office door.

Real-world reference: 12.5" (0.32 m) institutional wall clock: a deep black
ABS case with a rounded front bezel, a white printed dial with bar hour
markers (heavier at 12 / 3 / 6 / 9), black hour and minute hands, a thin red
sweep second hand on a centre cap, behind a flat glass lens. Hands at 10:08,
the catalogue time.

Size: 0.32 m diameter, 0.05 m deep. ORIGIN = THE BACK CENTRE (the point that
hangs on the wall nail): the back face is the plane y = 0 and the dial faces
-Y; the dial centre is at x = z = 0, so the clock spans z -0.16 .. +0.16.
Budget 600 tris, no LOD1, no collider. Slots: PlasticBlack (case, markers,
hands), PlasticWhite (dial), PlasticRed (second hand), Glass (lens).
"""

import math

import bmesh

NAME = "Kit_WallClock"
SMOOTH_ANGLE = 40.0

BLACK = "Prop_PlasticBlack"
WHITE = "Prop_PlasticWhite"
RED = "Prop_PlasticRed"
GLASS = "Prop_Glass"

# Case profile (radius, distance in front of the wall), back to front.
CASE = [
    (0.148, 0.000),   # back edge on the wall (capped: the back face)
    (0.159, 0.008),
    (0.160, 0.034),   # side
    (0.153, 0.0495),  # rounded bezel
    (0.1435, 0.0475), # inner lip
    (0.1415, 0.037),  # down to the dial
]
DIAL_D = 0.037        # dial plane, metres in front of the wall
LENS_D = 0.0465


def _disc(kit, radius, d, slot, verts, name):
    """Flat n-gon facing -Y at ``d`` in front of the wall."""
    bm = bmesh.new()
    ring = [bm.verts.new((radius * math.cos(2 * math.pi * i / verts), -d, radius * math.sin(2 * math.pi * i / verts)))
            for i in range(verts)]
    face = bm.faces.new(ring)
    face.normal_update()
    if face.normal.y > 0:
        face.normal_flip()
    return kit._new_object(name, bm, slot, "metres", "xz")


def _hand(kit, outline, angle_deg, d, thick, slot, name):
    """A flat hand drawn pointing at 12, turned clockwise (seen from the
    front) by ``angle_deg``."""
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    pts = [(x * c + z * s, -x * s + z * c) for x, z in outline]
    return kit.extrude(pts, thick, (0, -d, 0), slot, plane="xz", bevel=0.0, name=name)


def build(kit):
    kit.lathe(CASE, (0, 0, 0), BLACK, verts=32, rot=(90, 0, 0), close_top=False, name="case")
    _disc(kit, 0.1418, DIAL_D, WHITE, 32, "dial")

    # Bar hour markers (quads 0.5 mm proud of the dial).
    for h in range(12):
        major = h % 3 == 0
        w, l = (0.0075, 0.026) if major else (0.0045, 0.017)
        r = 0.127 - l / 2
        a = math.radians(30 * h)
        q = kit.quad(w, l, (r * math.sin(a), -(DIAL_D + 0.0005), r * math.cos(a)), BLACK, facing="-y",
                     uv="metres", name="hour marker")
        q.rotation_euler = (0, a, 0)

    # Hands at 10:08:37.
    hour = [(-0.0048, -0.020), (0.0048, -0.020), (0.0042, 0.066), (0.0, 0.077), (-0.0042, 0.066)]
    minute = [(-0.0036, -0.024), (0.0036, -0.024), (0.0030, 0.104), (0.0, 0.116), (-0.0030, 0.104)]
    second = [(-0.0014, -0.034), (0.0014, -0.034), (0.0008, 0.122), (-0.0008, 0.122)]
    _hand(kit, hour, 30 * (10 + 8.6 / 60), DIAL_D + 0.0015, 0.0012, BLACK, "hour hand")
    _hand(kit, minute, 6 * (8 + 37 / 60), DIAL_D + 0.0030, 0.0012, BLACK, "minute hand")
    _hand(kit, second, 6 * 37, DIAL_D + 0.0045, 0.0008, RED, "second hand")
    kit.cylinder(0.0055, 0.004, (0, -(DIAL_D + 0.006), 0), RED, verts=8, rot=(90, 0, 0), bevel=0.0012,
                 segments=1, name="centre cap")

    # Flat glass lens seated in the bezel lip.
    _disc(kit, 0.1428, LENS_D, GLASS, 32, "lens")

    kit.no_collider()
    kit.anchor("hang", (0, 0, 0))
    kit.anchor("dial", (0, -DIAL_D, 0))
    kit.tag("office", "wall_decor")
