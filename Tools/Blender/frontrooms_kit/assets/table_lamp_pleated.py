"""Ginger-jar table lamp with a pleated empire shade, c. 1985-95 (the
Sears / JCPenney living-room lamp: glazed ceramic jar on a turned brass
foot, brass neck, harp and finial, a cream knife-pleated paper/fabric shade
on wire rings with a three-arm spider).

Real-world reference size: 0.62 m tall to the finial. Jar 0.22 m diameter,
0.29 m tall on a 0.15 m brass foot (jar + foot 0.31 m, about half the lamp),
a 20 mm brass neck between the jar cap and the shade. Shade: empire (tapered drum) 0.20 m
top / 0.38 m bottom diameter, 0.26 m tall, 40 knife pleats built as real
zig-zag geometry. Budget: under the 3k small-item cap. Bulb: frosted A19 in a brass turn-key socket.
Front faces -Y (turn key on +X, cord leaves the back). Origin = underside
of the foot. Film: Still A, the pleated lamp on top of the pile.
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_TableLampPleated"
SMOOTH_ANGLE = 40.0

CERAMIC = "Prop_PlasticWhite"
BRASS = "Prop_Brass"
SHADE = "Prop_LampShade"
FELT = "Prop_FabricChair"
BLACK = "Prop_PlasticBlack"

PLEATS = 40
SHADE_BOTTOM = 0.345
SHADE_H = 0.26
R_BOTTOM = 0.19
R_TOP = 0.10
PLEAT_K = 0.048      # pleat depth as a fraction of the radius
JAR_SR, JAR_SZ = 1.1, 1.2   # jar profile scale (radius, height above the foot)
CAP_UP = 0.048              # jar cap raised to the scaled jar's lip


def ring_profile(kit, profile, loc, slot, verts=32, name="ring"):
    """Lathe a CLOSED (r, z) loop (first point repeated) -> watertight shell."""
    pts = list(profile) + [profile[0]]
    return kit.lathe(pts, loc, slot, verts=verts, name=name, close_top=False, close_bottom=False)


def pleat(obj, verts, k):
    """Knife pleats: pull every other angular column of a lathe inward by
    the fraction k of its radius, so the surface zig-zags around Z."""
    step = 2 * math.pi / verts
    for v in obj.data.vertices:
        r = math.hypot(v.co.x, v.co.y)
        if r < 1e-6:
            continue
        i = int(round(math.atan2(v.co.y, v.co.x) / step)) % verts
        if i % 2:
            v.co.x *= 1 - k
            v.co.y *= 1 - k
    return obj


def smooth_path(points, sub=4):
    """Catmull-Rom through the control points (cords that sag, not kink)."""
    pts = [Vector(p) for p in points]
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(sub):
            t = s / sub
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-1])
    return [tuple(v) for v in out]


def build(kit):
    # ---------------------------------------------------------- brass foot
    # Felt-lined underside (dark disc) inside a turned brass foot.
    # (Open at the top: that disc is buried 1 mm inside the jar's foot ring.)
    foot = [(0.0, 0.0), (0.0750, 0.0), (0.0762, 0.0115), (0.0680, 0.0180),
            (0.0640, 0.0225), (0.0625, 0.0265)]
    kit.lathe(foot, (0, 0, 0), BRASS, verts=24, name="brass foot", close_top=False)

    # -------------------------------------------------------- ginger jar
    # High-shouldered jar: narrow foot ring, swelling to a broad shoulder at
    # three quarters of its height, rolling over into a short neck. Drawn at
    # the old 0.24 m size, then scaled 1.2 tall / 1.1 wide so jar + foot is
    # about half the lamp (0.31 m) and the jar ~0.58x the shade bottom.
    jar = [
        (0.0, 0.0255), (0.0560, 0.0255), (0.0585, 0.0300), (0.0563, 0.0370),   # foot ring
        (0.0800, 0.0850), (0.0990, 0.1580), (0.0972, 0.1960), (0.0835, 0.2200),
        (0.0510, 0.2430),                                                         # shoulder
        (0.0478, 0.2520), (0.0505, 0.2650),                                       # neck + lip
    ]
    jar = [(r * JAR_SR, 0.0255 + (z - 0.0255) * JAR_SZ) for r, z in jar]
    # Open ends: the bottom sits inside the brass foot, the lip under the cap.
    kit.lathe(jar[1:], (0, 0, 0), CERAMIC, verts=24, name="ginger jar", close_top=False, close_bottom=False)

    # ------------------------------------------------- brass cap and neck
    cap = [(0.0528, 0.2635), (0.0532, 0.2672), (0.0460, 0.2715),
           (0.0280, 0.2770), (0.0150, 0.2810), (0.0, 0.2810)]
    cap = [(r * JAR_SR, z + CAP_UP) for r, z in cap]
    kit.lathe(cap, (0, 0, 0), BRASS, verts=24, name="jar cap", close_bottom=False)
    neck0 = 0.281 + CAP_UP
    kit.cylinder(0.0095, 0.349 - neck0, (0, 0, (neck0 + 0.349) / 2), BRASS, verts=16, bevel=0.0,
                 name="neck tube")

    # Harp saddle: flat bar the harp legs drop into.
    sz = 0.351
    kit.box((0.080, 0.012, 0.004), (0, 0, sz), BRASS, bevel=0.0015, segments=1, name="harp saddle")

    # ------------------------------------------------- socket and bulb
    sock = [(0.0, 0.353), (0.0120, 0.353), (0.0165, 0.357), (0.0172, 0.392),
            (0.0182, 0.395), (0.0172, 0.399), (0.0172, 0.414), (0.0150, 0.417), (0.0, 0.417)]
    kit.lathe(sock, (0, 0, 0), BRASS, verts=16, name="socket shell")
    # Turn-key switch on the +X side.
    kit.cylinder(0.0022, 0.012, (0.0225, 0, 0.383), BRASS, verts=6, rot=(0, 90, 0), bevel=0.0, name="key shaft")
    kit.box((0.004, 0.016, 0.011), (0.0300, 0, 0.383), BRASS, bevel=0.0018, segments=1, name="turn key")
    bulb = [(0.0130, 0.414), (0.0130, 0.432), (0.0235, 0.455), (0.0298, 0.480),
            (0.0270, 0.507), (0.0150, 0.523), (0.0, 0.528)]
    kit.lathe(bulb, (0, 0, 0), CERAMIC, verts=14, name="frosted bulb")

    # ----------------------------------------------------- harp + finial
    hz = 0.584
    for side in (-1, 1):
        kit.tube(smooth_path([(side * 0.034, 0, sz + 0.016), (side * 0.050, 0, 0.425), (side * 0.063, 0, 0.500),
                              (side * 0.044, 0, 0.558), (side * 0.006, 0, hz - 0.002)], 3),
                 0.0019, BRASS, verts=5, name="harp leg")
    kit.cylinder(0.0042, 0.012, (0, 0, hz + 0.001), BRASS, verts=6, bevel=0.0, name="harp stud")

    # ------------------------------------------------------ pleated shade
    t = 0.0016
    z0, z1 = SHADE_BOTTOM, SHADE_BOTTOM + SHADE_H
    shade = ring_profile(kit, [(R_BOTTOM, z0), (R_TOP, z1), (R_TOP - t, z1), (R_BOTTOM - t, z0)],
                         (0, 0, 0), SHADE, verts=2 * PLEATS, name="pleated shade")
    pleat(shade, 2 * PLEATS, PLEAT_K)
    # Wire rings inside the pleat valleys and the three-arm spider.
    rb = R_BOTTOM * (1 - PLEAT_K) - t - 0.0016
    rt = R_TOP * (1 - PLEAT_K) - t - 0.0014
    ring_profile(kit, [(rb - 0.0012, z0 + 0.0030), (rb + 0.0010, z0 + 0.0030), (rb - 0.0001, z0 + 0.0052)],
                 (0, 0, 0), BRASS, verts=PLEATS // 2, name="bottom wire ring")
    ring_profile(kit, [(rt - 0.0012, z1 - 0.0030), (rt - 0.0001, z1 - 0.0052), (rt + 0.0010, z1 - 0.0030)],
                 (0, 0, 0), BRASS, verts=PLEATS // 2, name="top wire ring")
    for k in range(3):
        a = math.radians(90 + 120 * k)
        c, s = math.cos(a), math.sin(a)
        kit.tube([(c * rt, s * rt, z1 - 0.004), (c * 0.045, s * 0.045, z1 - 0.010), (c * 0.010, s * 0.010, hz + 0.006)],
                 0.0013, BRASS, verts=5, name="spider arm")
    kit.cylinder(0.012, 0.0025, (0, 0, hz + 0.0075), BRASS, verts=10, bevel=0.0, name="spider washer")
    finial = [(0.0, hz + 0.009), (0.0088, hz + 0.0105), (0.0050, hz + 0.0165), (0.0045, hz + 0.020),
              (0.0092, hz + 0.0245), (0.0105, hz + 0.0290), (0.0080, hz + 0.0335), (0.0, hz + 0.0370)]
    kit.lathe(finial, (0, 0, 0), BRASS, verts=10, name="finial")

    # ------------------------------------------------------------ cord
    kit.cylinder(0.0045, 0.012, (0, 0.074, 0.009), BLACK, verts=8, rot=(90, 0, 0), bevel=0.0,
                 name="cord grommet")
    # Cord curls round to the side inside the shade footprint, ends in a plug.
    kit.tube(smooth_path([(0, 0.078, 0.009), (0.003, 0.094, 0.0029), (0.030, 0.132, 0.0029),
                          (0.090, 0.144, 0.0029), (0.130, 0.128, 0.0029)], 2),
             0.0026, BLACK, verts=5, name="lamp cord")
    d = Vector((0.025, -0.012)).normalized()
    rz = math.degrees(math.atan2(-d.x, d.y))
    c = (0.130 + d.x * 0.015, 0.128 + d.y * 0.015)
    kit.box((0.022, 0.030, 0.014), (c[0], c[1], 0.007), BLACK, bevel=0.004, segments=1, rot=(0, 0, rz),
            name="plug body")
    for o in (-0.0055, 0.0055):
        kit.box((0.0016, 0.014, 0.006), (c[0] + d.x * 0.021 + d.y * o, c[1] + d.y * 0.021 - d.x * o, 0.0075),
                "Prop_Chrome", bevel=0.0, rot=(0, 0, rz), name="plug blade")

    kit.anchor("light", (0, 0, 0.47))
    kit.collider((0, 0, 0.175), (0.22, 0.22, 0.345))
    kit.collider((0, 0, SHADE_BOTTOM + SHADE_H / 2 + 0.008), (2 * R_BOTTOM, 2 * R_BOTTOM, SHADE_H + 0.016))
    kit.tag("pile", "lamp", "domestic", "table_top")
    kit.pile("Tall", mass=0, palette="domestic70s", topper=True)
