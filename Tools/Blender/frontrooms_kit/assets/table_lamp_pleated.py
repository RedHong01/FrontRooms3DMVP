"""Ginger-jar table lamp with a pleated empire shade, c. 1985-95 (the
Sears / JCPenney living-room lamp: glazed ceramic jar on a turned brass
foot, brass neck, harp and finial, a cream knife-pleated paper/fabric shade
on a three-arm spider).

Real-world reference size: 0.62 m tall to the finial. Jar 0.22 m diameter,
0.29 m tall on a 0.15 m brass foot (jar + foot 0.31 m, about half the lamp),
a 20 mm brass neck between the jar cap and the shade. Shade: empire (tapered
drum) 0.20 m top / 0.38 m bottom diameter, 0.26 m tall, 40 knife pleats
built as real zig-zag geometry. Bulb: frosted A19 in a brass turn-key socket.
Front faces -Y (turn key on +X, cord leaves the back). Origin = underside
of the foot. Film: Still A, the pleated lamp on top of the pile.

Budget (§5.3): 1,600 LOD0 tris, <= 4 slots, no collider. Optimised
2026-10-02 from 3.0k / 5 slots: the shade keeps all 40 pleats but is two
open zig-zag skins (outer, inner) without the 1.6 mm rim bands; jar, foot
and cap keep 24 sides with fewer profile rings; wire rings, washer, key
shaft, grommet and plug blades (all under ~5 mm at 2 m) are gone. The
frosted bulb shares the shade slot, so an "on" variant that swaps
Prop_LampShade for Prop_LampShadeLit lights both.
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_TableLampPleated"
LOD1 = 0.42
SMOOTH_ANGLE = 40.0

CERAMIC = "Prop_CeramicGlaze"
BRASS = "Prop_Brass"
SHADE = "Prop_LampShade"
BLACK = "Prop_PlasticBlack"

PLEATS = 40
SHADE_BOTTOM = 0.345
SHADE_H = 0.26
R_BOTTOM = 0.19
R_TOP = 0.10
PLEAT_K = 0.048      # pleat depth as a fraction of the radius
JAR_SR, JAR_SZ = 1.1, 1.2   # jar profile scale (radius, height above the foot)
CAP_UP = 0.048              # jar cap raised to the scaled jar's lip


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
    # Turned brass foot: a rounded bead over a flat bottom (open at the top,
    # where the jar's foot ring sits inside it).
    foot = [(0.0750, 0.0), (0.0764, 0.0110), (0.0675, 0.0190), (0.0625, 0.0265)]
    kit.lathe(foot, (0, 0, 0), BRASS, verts=24, name="brass foot", close_top=False)

    # -------------------------------------------------------- ginger jar
    # High-shouldered jar: narrow foot ring, swelling to a broad shoulder at
    # three quarters of its height, rolling over into a short neck. Drawn at
    # the old 0.24 m size, then scaled 1.2 tall / 1.1 wide so jar + foot is
    # about half the lamp (0.31 m). Nine rings carry the S-curve.
    jar = [
        (0.0560, 0.0255), (0.0585, 0.0330),               # foot ring, seated in the brass foot
        (0.0800, 0.0850), (0.0985, 0.1500), (0.0965, 0.1960),
        (0.0835, 0.2200), (0.0560, 0.2400),               # shoulder
        (0.0478, 0.2520), (0.0505, 0.2650),               # neck + lip
    ]
    jar = [(r * JAR_SR, 0.0255 + (z - 0.0255) * JAR_SZ) for r, z in jar]
    kit.lathe(jar, (0, 0, 0), CERAMIC, verts=24, name="ginger jar", close_top=False, close_bottom=False)

    # ------------------------------------------------- brass cap and neck
    cap = [(0.0532, 0.2650), (0.0460, 0.2715), (0.0220, 0.2790), (0.0, 0.2810)]
    cap = [(r * JAR_SR, z + CAP_UP) for r, z in cap]
    kit.lathe(cap, (0, 0, 0), BRASS, verts=24, name="jar cap", close_bottom=False)
    neck0 = 0.281 + CAP_UP
    kit.cylinder(0.0095, 0.355 - neck0, (0, 0, (neck0 + 0.355) / 2), BRASS, verts=8, bevel=0.0,
                 name="neck tube")

    # Harp saddle: flat bar the harp legs drop into.
    sz = 0.351
    kit.box((0.080, 0.012, 0.004), (0, 0, sz), BRASS, bevel=0.0, name="harp saddle")

    # ------------------------------------------------- socket and bulb
    sock = [(0.0, 0.353), (0.0165, 0.357), (0.0172, 0.392), (0.0182, 0.396),
            (0.0172, 0.414), (0.0, 0.417)]
    kit.lathe(sock, (0, 0, 0), BRASS, verts=12, name="socket shell")
    # Turn-key switch on the +X side.
    kit.box((0.004, 0.016, 0.011), (0.0255, 0, 0.383), BRASS, bevel=0.0, name="turn key")
    bulb = [(0.0130, 0.414), (0.0235, 0.455), (0.0298, 0.482), (0.0240, 0.512), (0.0, 0.528)]
    kit.lathe(bulb, (0, 0, 0), SHADE, verts=12, name="frosted bulb", close_bottom=False)

    # ----------------------------------------------------- harp + finial
    hz = 0.584
    for side in (-1, 1):
        kit.tube(smooth_path([(side * 0.034, 0, sz + 0.002), (side * 0.050, 0, 0.425), (side * 0.063, 0, 0.500),
                              (side * 0.044, 0, 0.558), (side * 0.006, 0, hz - 0.002)], 2),
                 0.0020, BRASS, verts=3, name="harp leg")

    # ------------------------------------------------------ pleated shade
    # Two open skins 1.6 mm apart, both pleated: the outside faces out, the
    # inside faces the bulb (seen through the top and from below).
    t = 0.0016
    z0, z1 = SHADE_BOTTOM, SHADE_BOTTOM + SHADE_H
    outer = kit.lathe([(R_BOTTOM, z0), (R_TOP, z1)], (0, 0, 0), SHADE, verts=2 * PLEATS,
                      name="pleated shade", close_top=False, close_bottom=False)
    pleat(outer, 2 * PLEATS, PLEAT_K)
    face_towards(outer, lambda c: Vector((c.x, c.y, 0.0)))
    inner = kit.lathe([(R_BOTTOM - t, z0), (R_TOP - t, z1)], (0, 0, 0), SHADE, verts=2 * PLEATS,
                      name="pleated shade inside", close_top=False, close_bottom=False)
    pleat(inner, 2 * PLEATS, PLEAT_K)
    face_towards(inner, lambda c: Vector((-c.x, -c.y, 0.0)))
    # Three-arm spider from the top ring (in the pleat valleys) to the finial.
    rt = R_TOP * (1 - PLEAT_K) - t - 0.0014
    for k in range(3):
        a = math.radians(90 + 120 * k)
        c, s = math.cos(a), math.sin(a)
        kit.tube([(c * rt, s * rt, z1 - 0.004), (c * 0.045, s * 0.045, z1 - 0.010), (c * 0.008, s * 0.008, hz + 0.006)],
                 0.0016, BRASS, verts=3, name="spider arm")
    finial = [(0.0, hz + 0.004), (0.0110, hz + 0.008), (0.0050, hz + 0.0165),
              (0.0100, hz + 0.0270), (0.0, hz + 0.0370)]
    kit.lathe(finial, (0, 0, 0), BRASS, verts=8, name="finial")

    # ------------------------------------------------------------ cord
    # Leaves the back of the foot, curls round inside the shade footprint,
    # ends in a plug.
    kit.tube(smooth_path([(0, 0.070, 0.006), (0.003, 0.094, 0.0029), (0.030, 0.132, 0.0029),
                          (0.090, 0.144, 0.0029), (0.130, 0.128, 0.0029)], 2),
             0.0028, BLACK, verts=4, name="lamp cord")
    d = Vector((0.025, -0.012)).normalized()
    rz = math.degrees(math.atan2(-d.x, d.y))
    c = (0.130 + d.x * 0.015, 0.128 + d.y * 0.015)
    kit.box((0.022, 0.030, 0.014), (c[0], c[1], 0.007), BLACK, bevel=0.0, rot=(0, 0, rz), name="plug body")

    kit.anchor("light", (0, 0, 0.47))
    kit.no_collider()
    kit.tag("pile", "lamp", "domestic", "table_top")
    kit.pile("Tall", mass=0, palette="domestic70s", topper=True)
