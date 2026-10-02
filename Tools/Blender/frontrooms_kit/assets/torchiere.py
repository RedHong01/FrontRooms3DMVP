"""Black halogen torchiere floor lamp, c. 1992-98 (the 300 W "uplight" every
dorm room and furniture showroom had: weighted steel disc base, slim
three-section steel pole with threaded couplings, a rotary dimmer pod at
hand height, a wide shallow bowl with a rolled lip, white enamel inside and
a linear R7s halogen tube between ceramic clips under a wire guard).

Real-world reference size: 1.85 m tall, base 0.28 m diameter (42 mm high,
cast-iron weight under a domed steel cover, rubber foot ring), pole 19 mm
diameter, bowl 0.36 m diameter x 85 mm deep. Cord leaves the back of the
base through a strain relief and ends in a two-pin plug.
Front (dimmer knob) faces -Y. Origin = floor under the base centre.
Film: Still B, the black pole / white bowl spike on top of the pile (it
leans out of the pile, hence the EdgeLean state as well as Upright).

Budget: ~4.5k tris, an agreed exception to the 3k small-item cap (a 1.85 m
silhouette seen from across a room, whose bowl rim and rolled base need the
segments); LOD1 at 0.45 carries it at distance.
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_Torchiere"
LOD1 = 0.45
# Rolled bowl lip and base rim turn 40 deg per step: keep them one smooth bead.
SMOOTH_ANGLE = 45.0

STEEL = "Prop_SteelBlack"
WHITE = "Prop_PlasticWhite"
BLACK = "Prop_PlasticBlack"
RUBBER = "Prop_Rubber"
CHROME = "Prop_Chrome"

POLE_R = 0.0095
BOWL_R = 0.1805
BOWL_BOTTOM = 1.766
BOWL_VERTS = 36
TOP = 1.85


def ring_profile(kit, profile, loc, slot, verts=32, name="ring"):
    """Lathe a CLOSED (r, z) loop (first point repeated at the end) so the
    result is a watertight shell with real wall thickness."""
    pts = list(profile) + [profile[0]]
    return kit.lathe(pts, loc, slot, verts=verts, name=name, close_top=False, close_bottom=False)


def face_towards(obj, direction):
    """Open lathes have no inside/outside: flip the winding so most faces
    point along ``direction`` (a function of the face centre)."""
    mesh = obj.data
    score = sum(p.normal.dot(direction(Vector(p.center))) * p.area for p in mesh.polygons)
    if score < 0:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
    return obj


def scallop(obj, verts, depth):
    """Pull every other angular column of a Z-axis mesh inward: knurls, ribs."""
    step = 2 * math.pi / verts
    for v in obj.data.vertices:
        r = math.hypot(v.co.x, v.co.y)
        if r < 1e-6:
            continue
        k = int(round(math.atan2(v.co.y, v.co.x) / step)) % verts
        if k % 2:
            f = (r - depth) / r
            v.co.x *= f
            v.co.y *= f
    return obj


def smooth_path(points, sub=4):
    """Catmull-Rom through the control points: cables that sag instead of kink."""
    pts = [Vector(p) for p in points]
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for k in range(sub):
            t = k / sub
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-1])
    return [tuple(v) for v in out]


def plug(kit, end, d, body, blade):
    """Two-pin plug whose back sits on the cord ``end`` and whose blades
    point along the floor direction ``d``."""
    dx, dy = d
    rz = math.degrees(math.atan2(-dx, dy))
    sx, sy = dy, -dx                        # plug's local +X in world
    c = (end[0] + dx * 0.017, end[1] + dy * 0.017)
    kit.box((0.026, 0.034, 0.016), (c[0], c[1], 0.008), body, bevel=0.004, segments=1, rot=(0, 0, rz),
            name="plug body")
    for o in (-0.0062, 0.0062):
        kit.box((0.0018, 0.016, 0.0065), (c[0] + dx * 0.024 + sx * o, c[1] + dy * 0.024 + sy * o, 0.009),
                blade, bevel=0.0, rot=(0, 0, rz), name="plug blade")


def bowl_z(r):
    """Outer surface of the bowl: shallow dish that turns up near the lip."""
    t = r / 0.172
    return BOWL_BOTTOM + 0.010 * t + 0.064 * t ** 2.4


def build(kit):
    # ---------------------------------------------------------------- base
    # Domed steel cover over the weight: crisp rolled edge, gentle dome.
    base = [
        (0.0, 0.005), (0.131, 0.005), (0.1385, 0.0080), (0.1396, 0.0100), (0.1400, 0.0125),
        (0.1395, 0.0190), (0.1360, 0.0240), (0.1280, 0.0264),
        (0.0950, 0.0305), (0.0620, 0.0362), (0.0380, 0.0405), (0.0, 0.0420),
    ]
    kit.lathe(base, (0, 0, 0), STEEL, verts=36, name="base cover")
    ring_profile(kit, [(0.118, 0.0), (0.132, 0.0), (0.132, 0.0055), (0.118, 0.0055)],
                 (0, 0, 0), RUBBER, verts=16, name="foot ring")
    # Pole socket boss and a hex lock nut.
    boss = [(0.0275, 0.038), (0.0275, 0.051), (0.0255, 0.056), (0.0190, 0.061),
            (0.0135, 0.068), (0.0125, 0.080), (0.0, 0.080)]
    kit.lathe(boss, (0, 0, 0), STEEL, verts=16, name="pole boss")
    kit.cylinder(0.0148, 0.009, (0, 0, 0.0845), STEEL, verts=6, bevel=0.0012, segments=1, name="lock nut")

    # ---------------------------------------------------------------- pole
    # Three sections joined by threaded couplings (the mid collar).
    kit.cylinder(POLE_R, 0.585, (0, 0, 0.089 + 0.2925), STEEL, verts=14, bevel=0.0, name="pole lower")
    kit.cylinder(POLE_R, 0.50, (0, 0, 0.672 + 0.25), STEEL, verts=14, bevel=0.0, name="pole middle")
    kit.cylinder(POLE_R, 0.58, (0, 0, 1.172 + 0.29), STEEL, verts=14, bevel=0.0, name="pole upper")
    for z in (0.672, 1.172):
        coupling = [(0.0, z - 0.017), (0.0100, z - 0.017), (0.0129, z - 0.009),
                    (0.0129, z + 0.009), (0.0100, z + 0.017), (0.0, z + 0.017)]
        kit.lathe(coupling, (0, 0, 0), STEEL, verts=12, name="pole coupling")

    # ---------------------------------------------------------- rotary dimmer
    # Pod moulded round the pole at hand height, knurled knob facing -Y.
    dz = 1.05
    kit.box((0.040, 0.046, 0.094), (0, -0.010, dz), BLACK, bevel=0.012, segments=3, name="dimmer pod")
    for zz in (dz - 0.0475, dz + 0.0475):
        kit.cylinder(0.0118, 0.006, (0, 0, zz), BLACK, verts=12, bevel=0.0, name="pod grommet")
    kit.box((0.029, 0.004, 0.074), (0, -0.0335, dz), BLACK, bevel=0.0015, segments=1, name="dimmer face plate")
    knob = kit.cylinder(0.0140, 0.016, (0, -0.0430, dz + 0.010), BLACK, verts=20, rot=(90, 0, 0),
                        bevel=0.0016, segments=1, name="dimmer knob")
    scallop(knob, 20, 0.0010)
    kit.cylinder(0.0105, 0.003, (0, -0.0517, dz + 0.010), BLACK, verts=16, rot=(90, 0, 0),
                 bevel=0.0010, segments=1, name="knob cap")
    kit.box((0.0018, 0.0012, 0.0075), (0, -0.0534, dz + 0.0185), WHITE, bevel=0.0, name="knob pointer")
    # MIN..MAX wedge of tick marks printed under the knob.
    for k in range(5):
        h = 0.0018 + 0.0011 * k
        kit.box((0.0014, 0.001, h), (-0.0088 + k * 0.0044, -0.0358, dz - 0.027 + h / 2), WHITE,
                bevel=0.0, name="dimmer scale")

    # ---------------------------------------------------------------- bowl
    b = BOWL_BOTTOM
    neck = [(0.0, b - 0.066), (0.0118, b - 0.066), (0.0131, b - 0.062), (0.0131, b - 0.050),
            (0.0118, b - 0.046), (0.0150, b - 0.038), (0.0240, b - 0.022), (0.0330, b - 0.010),
            (0.0400, b - 0.002), (0.0400, b + 0.002), (0.0, b + 0.002)]
    kit.lathe(neck, (0, 0, 0), STEEL, verts=16, name="bowl neck")
    # Black spun-steel outside with a rolled lip (open surface, faces down/out).
    outer = []
    for i in range(6):
        r = 0.028 + (0.172 - 0.028) * (i / 5.0) ** 0.75
        outer.append((r, bowl_z(r)))
    lip_c = (0.1755, bowl_z(0.172) + 0.0045)
    lip = []
    for deg in (-105, -65, -25, 15, 55, 95, 135):
        a = math.radians(deg)
        lip.append((lip_c[0] + 0.0055 * math.cos(a), lip_c[1] + 0.0055 * math.sin(a)))
    lip_end = lip[-1]
    shell = kit.lathe(outer + lip, (0, 0, 0), STEEL, verts=BOWL_VERTS, name="bowl outside",
                      close_top=False, close_bottom=False)
    face_towards(shell, lambda c: Vector((c.x, c.y, -0.6 * math.hypot(c.x, c.y) - 0.02)))
    # White enamel inside, 2.5 mm above, meeting the inner edge of the lip.
    inside = [(r, z + 0.0028) for r, z in outer[:-1]] + [(lip_end[0] - 0.0012, lip_end[1] - 0.0045), lip_end]
    liner = kit.lathe(inside, (0, 0, 0), WHITE, verts=BOWL_VERTS, name="bowl inside",
                      close_top=False, close_bottom=False)
    face_towards(liner, lambda c: Vector((-c.x, -c.y, 1.0)))

    # Lamp holder: cup, stamped bracket, two ceramic end clips, linear
    # halogen tube, three-wire guard.
    hz = bowl_z(0.0) + 0.006
    kit.cylinder(0.034, 0.010, (0, 0, hz + 0.004), STEEL, verts=16, bevel=0.002, segments=1, name="holder cup")
    kit.box((0.124, 0.022, 0.004), (0, 0, hz + 0.010), STEEL, bevel=0.0015, segments=1, name="holder bracket")
    for x in (-0.058, 0.058):
        kit.box((0.012, 0.020, 0.024), (x, 0, hz + 0.024), WHITE, bevel=0.003, segments=1, name="ceramic clip")
    kit.cylinder(0.0050, 0.106, (0, 0, hz + 0.030), "Prop_Glass", verts=10, rot=(0, 90, 0),
                 bevel=0.002, segments=1, name="halogen tube")
    kit.cylinder(0.0014, 0.084, (0, 0, hz + 0.030), CHROME, verts=5, rot=(0, 90, 0), bevel=0.0, name="filament")
    gz = bowl_z(0.082) + 0.0032
    for y in (-0.026, 0.0, 0.026):
        kit.tube([(-0.082, y, gz), (-0.072, y, hz + 0.048), (0.072, y, hz + 0.048),
                  (0.082, y, gz)], 0.0013, CHROME, verts=6, name="wire guard")

    # ---------------------------------------------------------------- cord
    kit.cylinder(0.0055, 0.016, (0, 0.144, 0.013), RUBBER, verts=10, rot=(90, 0, 0), bevel=0.0015,
                 segments=1, name="strain relief")
    # The cord curls round the back of the base and ends in a two-pin plug
    # (kept inside the bowl footprint so the lamp packs into a pile).
    kit.tube(smooth_path([(0, 0.150, 0.013), (0.003, 0.162, 0.008), (0.018, 0.175, 0.0034), (0.065, 0.172, 0.0034),
                          (0.115, 0.155, 0.0034), (0.150, 0.125, 0.0034), (0.163, 0.095, 0.0034),
                          (0.165, 0.074, 0.0034)], 2), 0.0030, BLACK, verts=6, name="power cord")
    plug(kit, (0.165, 0.074), (0.0, -1.0), BLACK, CHROME)

    kit.anchor("light", (0, 0, TOP - 0.04))
    kit.anchor("dimmer", (0, -0.054, dz + 0.010))
    kit.collider((0, 0, 0.022), (0.28, 0.28, 0.044))
    kit.collider((0, 0, 0.90), (0.06, 0.06, 1.72))
    kit.collider((0, 0, (BOWL_BOTTOM + TOP) / 2), (2 * BOWL_R, 2 * BOWL_R, TOP - BOWL_BOTTOM))
    kit.tag("pile", "lamp", "domestic")
    kit.pile("Tall", mass=0, palette="domestic70s", topper=True, states=["Upright", "EdgeLean"])
