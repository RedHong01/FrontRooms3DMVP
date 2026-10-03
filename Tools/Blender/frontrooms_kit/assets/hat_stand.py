"""Bentwood coat / hat stand (the dark bentwood rack silhouetted in the
foreground of the A24 "Backrooms" trailer, and the "spike" of a pile).

Real-world reference: Thonet-pattern bentwood coat stand in dark-stained
beech, as made from the 1900s to the 1990s: a turned pole with a collar and
an onion finial; four large J hooks steam-bent out of the top and four
smaller hooks below them, set between the large ones; four S-curved legs
bent out from the lower pole down to the floor, tied by a bentwood ring.

Size: 0.45 m across the hooks and the feet, 1.80 m tall. Symmetric; one
pair of large hooks lies on the X axis. Budget 900 tris LOD0 / 350 LOD1.
Slot: WoodDark (one material, the whole stand is the same stain).
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_HatStand"
LOD1 = 0.39
SMOOTH_ANGLE = 80.0            # 5-6 sided bentwood sections (72 / 60 deg) must shade round

WOOD = "Prop_WoodDark"

POLE = [
    (0.020, 0.050),
    (0.021, 0.600),
    (0.018, 1.585),
    (0.023, 1.603),   # collar
    (0.017, 1.628),
    (0.028, 1.690),   # onion finial
    (0.024, 1.752),
    (0.010, 1.791),   # rounded top
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


def _radial(path, angle_deg):
    a = math.radians(angle_deg)
    c, s = math.cos(a), math.sin(a)
    return [(r * c, r * s, z) for r, z in path]


def _leg_r_at(z):
    """Radius of the leg path at height z (linear between path points)."""
    for (r0, z0), (r1, z1) in zip(LEG, LEG[1:]):
        if z1 <= z <= z0:
            t = (z - z0) / (z1 - z0)
            return r0 + (r1 - r0) * t
    return LEG[-1][0]


def _bent(kit, pts, radius, verts, normal, name, closed=False):
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
        _bent(kit, _radial(BIG_HOOK, a_big), 0.0118, 5, normal(a_big), "big hook")
        _bent(kit, _radial(SMALL_HOOK, a_leg), 0.0098, 5, normal(a_leg), "small hook")
        _bent(kit, _radial(LEG, a_leg), 0.0140, 5, normal(a_leg), "leg")
    # Bentwood ring through the legs (a closed 12-gon; every third corner
    # sits in a leg).
    rr = _leg_r_at(RING_Z) - 0.001
    pts = [(rr * math.cos(math.radians(45 + 30 * i)), rr * math.sin(math.radians(45 + 30 * i)), RING_Z) for i in range(12)]
    _bent(kit, pts, 0.008, 5, (0, 0, 1), "ring", closed=True)

    kit.anchor("top", (0, 0, 1.80))
    kit.collider((0, 0, 0.90), (0.34, 0.34, 1.80))
    kit.tag("domestic", "office", "coat_stand", "pile", "pile_piece")
    kit.pile("Tall", mass=0, topper=True, palette="domestic70s")
