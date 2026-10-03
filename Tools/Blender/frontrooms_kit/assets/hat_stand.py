"""Bentwood coat / hat stand (the dark bentwood rack silhouetted in the
foreground of the A24 "Backrooms" trailer, and the "spike" of a pile).

Real-world reference: Thonet-pattern bentwood coat stand in dark-stained
beech, as made from the 1900s to the 1990s: a turned pole with a collar and
an onion finial; four large J hooks steam-bent out of the top and four
smaller hooks below them, set between the large ones; four S-curved legs
bent out from the lower pole down to the floor, tied by a bentwood ring.

Size: 0.45 m across the hooks and the feet, 1.80 m tall. Symmetric; one
pair of large hooks lies on the X axis. Budget 900 tris LOD0 / 350 LOD1;
built at ~1,220 / ~350 (1.35x): the hook curl is the piece's whole read as a
foreground silhouette and a pile spike, so the bent paths are Catmull-Rom
resampled (big hooks 10 segments, small hooks and legs 6, spaced by length
and turn so the curl gets the joints) and the ring is a 16-gon. Hidden
start caps inside the pole are left off.
Slot: WoodDark (one material, the whole stand is the same stain).
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_HatStand"
LOD1 = 0.29
SMOOTH_ANGLE = 80.0            # 5-6 sided bentwood sections (72 / 60 deg) must shade round

WOOD = "Prop_WoodDark"

POLE = [
    (0.020, 0.050),
    (0.021, 0.600),
    (0.018, 1.585),
    (0.023, 1.603),   # collar
    (0.017, 1.628),
    (0.028, 1.690),   # onion finial
    (0.027, 1.735),
    (0.020, 1.772),
    (0.011, 1.792),   # rounded cap, not a spear tip
    (0.0, 1.800),
]

# Radial (r, z) paths, rotated round the pole. They start inside the pole.
# Large hooks sweep out and up from below the collar and curl down at the
# tip (the crown silhouette); small hooks are J hooks lower down.
BIG_HOOK = [(0.004, 1.560), (0.062, 1.596), (0.122, 1.626), (0.172, 1.630), (0.204, 1.606), (0.213, 1.569),
            (0.202, 1.536)]
SMALL_HOOK = [(0.004, 1.432), (0.050, 1.408), (0.092, 1.395), (0.125, 1.405), (0.140, 1.438)]
LEG = [(0.006, 0.540), (0.088, 0.420), (0.160, 0.262), (0.200, 0.120), (0.212, 0.0)]
RING_Z = 0.300
RING_SIDES = 16                # corners every 22.5 deg from 45: every 4th sits in a leg


def _catmull(pts, dense=120, alpha=0.5):
    """Centripetal Catmull-Rom through the (r, z) control points, densely
    sampled (end tangents from mirrored phantom points)."""
    P = [(2 * pts[0][0] - pts[1][0], 2 * pts[0][1] - pts[1][1])] + list(pts) + \
        [(2 * pts[-1][0] - pts[-2][0], 2 * pts[-1][1] - pts[-2][1])]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t0 = 0.0
        t1 = t0 + math.dist(p0, p1) ** alpha
        t2 = t1 + math.dist(p1, p2) ** alpha
        t3 = t2 + math.dist(p2, p3) ** alpha
        def lerp(a, b, ta, tb, t):
            return tuple(((tb - t) * a[j] + (t - ta) * b[j]) / (tb - ta) for j in range(2))
        for k in range(dense):
            t = t1 + (t2 - t1) * k / dense
            a1, a2, a3 = lerp(p0, p1, t0, t1, t), lerp(p1, p2, t1, t2, t), lerp(p2, p3, t2, t3, t)
            b1, b2 = lerp(a1, a2, t0, t2, t), lerp(a2, a3, t1, t3, t)
            out.append(lerp(b1, b2, t1, t2, t))
    out.append(tuple(pts[-1]))
    return out


def _resample(pts, segments, turn_weight=0.5):
    """``segments`` + 1 points along the smooth curve through ``pts``, spaced
    by a blend of arc length and turning angle (the curl gets the joints)."""
    d = _catmull(pts)
    length, turn = [0.0], [0.0]
    for i in range(1, len(d)):
        length.append(length[-1] + math.dist(d[i - 1], d[i]))
        da = 0.0
        if i < len(d) - 1:
            a0 = math.atan2(d[i][1] - d[i - 1][1], d[i][0] - d[i - 1][0])
            a1 = math.atan2(d[i + 1][1] - d[i][1], d[i + 1][0] - d[i][0])
            da = abs((a1 - a0 + math.pi) % (2 * math.pi) - math.pi)
        turn.append(turn[-1] + da)
    cost = [(1 - turn_weight) * length[i] / length[-1] + turn_weight * turn[i] / max(turn[-1], 1e-9) for i in range(len(d))]
    res, j = [], 0
    for k in range(segments + 1):
        c = k / segments
        while j < len(cost) - 2 and cost[j + 1] < c:
            j += 1
        t = min(max((c - cost[j]) / max(cost[j + 1] - cost[j], 1e-12), 0.0), 1.0)
        res.append(tuple(d[j][q] + (d[j + 1][q] - d[j][q]) * t for q in range(2)))
    res[0], res[-1] = tuple(pts[0]), tuple(pts[-1])
    return res


BIG_PATH = _resample(BIG_HOOK, 10)
SMALL_PATH = _resample(SMALL_HOOK, 6)
LEG_PATH = _resample(LEG, 6)


def _radial(path, angle_deg):
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return [(r * c, r * s, z) for r, z in path]


def _leg_r_at(z):
    """Radius of the leg path at height z (linear between path points)."""
    for (r0, z0), (r1, z1) in zip(LEG_PATH, LEG_PATH[1:]):
        if z1 <= z <= z0:
            t = (z - z0) / (z1 - z0)
            return r0 + (r1 - r0) * t
    return LEG_PATH[-1][0]


def _bent(kit, pts, radius, verts, normal, name, closed=False, cap_start=True):
    """Round bentwood along a PLANAR polyline: every cross-section is framed
    by the plane's normal, so the section never twists (kit.tube re-derives
    its frame per point and flips on near-vertical runs)."""
    pts = [Vector(p) for p in pts]
    n = Vector(normal).normalized()
    m = len(pts)
    bm = bmesh.new()
    rings = []
    for k, p in enumerate(pts):
        if closed:
            t = (pts[(k + 1) % m] - pts[k - 1]).normalized()
        elif k == 0:
            t = (pts[1] - pts[0]).normalized()
        elif k == m - 1:
            t = (pts[-1] - pts[-2]).normalized()
        else:
            t = ((p - pts[k - 1]).normalized() + (pts[k + 1] - p).normalized()).normalized()
        u = t.cross(n).normalized()
        rings.append([bm.verts.new(p + (n * math.cos(2 * math.pi * i / verts) + u * math.sin(2 * math.pi * i / verts)) * radius)
                      for i in range(verts)])
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if closed else [])
    for a, b in pairs:
        for i in range(verts):
            j = (i + 1) % verts
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if not closed:
        if cap_start:
            bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, WOOD, "metres", "xz")


def build(kit):
    kit.lathe(POLE, (0, 0, 0), WOOD, verts=8, name="pole")
    def normal(angle):
        a = math.radians(angle)
        return (-math.sin(a), math.cos(a), 0.0)
    for k in range(4):
        a_big, a_leg = 90 * k, 90 * k + 45
        # Hooks and legs start inside the pole: no start cap.
        _bent(kit, _radial(BIG_PATH, a_big), 0.0118, 5, normal(a_big), "big hook", cap_start=False)
        _bent(kit, _radial(SMALL_PATH, a_leg), 0.0098, 5, normal(a_leg), "small hook", cap_start=False)
        _bent(kit, _radial(LEG_PATH, a_leg), 0.0140, 5, normal(a_leg), "leg", cap_start=False)
    # Bentwood ring through the legs (a closed 16-gon; every fourth corner
    # sits in a leg). 5-sided section like the rest: a 4-sided one shades
    # as a flat ribbon under top light (90 deg edges stay sharp at 80).
    rr = _leg_r_at(RING_Z) - 0.001
    step = 360.0 / RING_SIDES
    pts = [(rr * math.cos(math.radians(45 + step * i)), rr * math.sin(math.radians(45 + step * i)), RING_Z)
           for i in range(RING_SIDES)]
    _bent(kit, pts, 0.008, 5, (0, 0, 1), "ring", closed=True)

    kit.anchor("top", (0, 0, 1.80))
    kit.collider((0, 0, 0.90), (0.34, 0.34, 1.80))
    kit.tag("domestic", "office", "coat_stand", "pile", "pile_piece")
    kit.pile("Tall", mass=0, topper=True, palette="domestic70s")
