"""Rectangular office wastebasket, moulded grey polypropylene, c. 1985-2000
(the 13-quart Rubbermaid-type desk-side basket: tapered walls, generous
corner radii, a rolled lip, a raised grip band under the lip, a recessed
base with a rounded heel). Two crumpled letter sheets on its floor.

Real-world reference size: 0.28 m wide x 0.20 m deep x 0.30 m tall at the
rim; base 0.22 x 0.14 m. Wall 3 mm. Origin = floor under the centre.
Front looks -Y (the basket is symmetric; the paper is arranged for a -Y
viewer).

The shell is a rounded-rectangle "lathe" built here with bmesh because the
kit's lathe only revolves circles; it is registered through kit._new_object
like every other part, so it goes through the same UV/export path.
"""

import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise

NAME = "Kit_TrashBin"
SMOOTH_ANGLE = 40.0

PLASTIC = "Prop_PlasticGrey"
PAPER = "Prop_Paper"

H = 0.30
RIM_Z = 0.284          # top of the tapered wall, start of the rolled lip
BASE_HX, BASE_HY = 0.1095, 0.0695   # outer half sizes at z = 0
BASE_R = 0.030          # corner radius at the base (grows with the taper)
TAPER = 0.0215          # outward growth per side from base to rim
WALL = 0.003
FLOOR_Z = 0.008


def _rr_ring(bm, off, z, seg):
    hx, hy, r = BASE_HX + off, BASE_HY + off, BASE_R + off
    ring = []
    for cx, cy, a0 in ((hx - r, hy - r, 0), (-(hx - r), hy - r, 90), (-(hx - r), -(hy - r), 180), (hx - r, -(hy - r), 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90.0 * k / seg)
            ring.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z)))
    return ring


def rr_lathe(kit, profile, slot, seg=5, name="rr lathe"):
    """Sweep an (offset, z) profile round the base rounded rectangle: offset
    grows the half sizes and the corner radius together, so a linear offset
    is a uniform draft. Bottom and top rings are capped."""
    bm = bmesh.new()
    rings = [_rr_ring(bm, off, z, seg) for off, z in profile]
    n = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _decimate(bm, target_tris):
    """Collapse-decimate a bmesh to about ``target_tris`` triangles (through a
    temporary object and its evaluated mesh); returns a new bmesh. The folds
    are cut at high resolution first, so the collapse keeps their ridges."""
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    me = bpy.data.meshes.new("_dec")
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new("_dec", me)
    bpy.context.scene.collection.objects.link(ob)
    mod = ob.modifiers.new("dec", "DECIMATE")
    mod.ratio = min(1.0, target_tris / float(tris))
    mod.use_collapse_triangulate = True
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    out = bmesh.new()
    out.from_mesh(ev.to_mesh())
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.meshes.remove(me)
    return out


def paper_ball(kit, xy, floor_z, radius, seed, target_tris=880, name="crumpled paper"):
    """A crumpled letter sheet. An icosphere is made lumpy with low-frequency
    noise, cut flat across 30 random crease planes (flats meeting in ridges),
    scored with V-shaped fold lines, punched with 3-4 dents that fold past
    their plane (the concave pockets real paper balls have), squashed
    anisotropically, given two sheet corners poking out, then decimated and
    edge-split so every facet stays a crisp flat plane whatever the smoothing
    angle. It is turned, then dropped until its lowest point rests on
    ``floor_z``."""
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=5, radius=radius)
    off = Vector((rng.uniform(-50, 50), rng.uniform(-50, 50), rng.uniform(-50, 50)))
    for v in bm.verts:
        n = v.co.normalized()
        k = 1.0 + 0.12 * max(-1.0, min(1.0, 1.6 * noise.noise(n * 1.7 + off)))
        v.co = n * radius * k

    def rand_dir():
        return Vector((rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1))).normalized()

    # Crease planes: each flattens a cap of the ball toward a plane. The 30
    # normals are spread over the sphere (jittered Fibonacci points), so no
    # lobe escapes the crush and ends up as a spike.
    dirs = []
    for i in range(30):
        zf = 1.0 - (i + 0.5) * 2.0 / 30
        rf = math.sqrt(max(0.0, 1.0 - zf * zf))
        a = i * 2.39996
        dirs.append((Vector((rf * math.cos(a), rf * math.sin(a), zf)) + rand_dir() * 0.25).normalized())
    rng.shuffle(dirs)
    for n in dirs:
        d = rng.uniform(0.15, 0.55) * radius
        push = rng.uniform(0.5, 0.9)
        for v in bm.verts:
            s = v.co.dot(n)
            if s > d:
                v.co -= n * (s - d) * push
    # Fold lines: a V valley (or ridge) scored along a plane through the ball.
    for i in range(14):
        n = rand_dir()
        o = rng.uniform(-0.35, 0.35) * radius
        wdt = rng.uniform(0.10, 0.18) * radius
        depth = rng.uniform(0.05, 0.10) * radius * (1 if i % 3 else -0.6)
        for v in bm.verts:
            t = abs(v.co.dot(n) - o)
            if t < wdt:
                v.co -= v.co.normalized() * depth * (1.0 - t / wdt)
    # Dents: the cap past the plane is pushed through it (concave pocket).
    for _ in range(rng.choice((3, 4))):
        n = rand_dir()
        d = rng.uniform(0.38, 0.62) * radius
        for v in bm.verts:
            s = v.co.dot(n)
            if s > d:
                v.co -= n * (s - d) * 1.4
    # The creases crush the sphere well inside its radius: bring the mean
    # radius back to ``radius`` before the squash.
    mean = sum(v.co.length for v in bm.verts) / len(bm.verts)
    bmesh.ops.scale(bm, vec=(radius / mean,) * 3, verts=bm.verts)
    # Two sheet corners poking out of the ball (short, blunt tips).
    for _ in range(2):
        n = rand_dir()
        for v in bm.verts:
            c = v.co.normalized().dot(n)
            if c > 0.96:
                v.co += n * radius * 0.12 * ((c - 0.96) / 0.04) ** 1.3
    sy, sz = rng.uniform(0.75, 0.9), rng.uniform(0.6, 0.75)
    bmesh.ops.scale(bm, vec=(1.0, sy, sz), verts=bm.verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm = _decimate(bm, target_tris)
    # Settled, so mostly lying on its flat side: free yaw, small tilt.
    rot = (Matrix.Rotation(rng.uniform(0, 2 * math.pi), 3, "Z") @ Matrix.Rotation(math.radians(rng.uniform(-18, 18)), 3, "X")
           @ Matrix.Rotation(math.radians(rng.uniform(-18, 18)), 3, "Y"))
    bmesh.ops.rotate(bm, cent=(0, 0, 0), matrix=rot, verts=bm.verts)
    zmin = min(v.co.z for v in bm.verts)
    bmesh.ops.translate(bm, vec=(xy[0], xy[1], floor_z - zmin - 0.0008), verts=bm.verts)
    bmesh.ops.split_edges(bm, edges=bm.edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, PAPER, "metres", "xz")


def _t(z):
    return TAPER * z / RIM_Z


def build(kit):
    # Profile: base heel -> tapered wall -> grip band -> rolled lip -> inner
    # wall -> floor. Offsets are outward from the base rectangle.
    band0, band1 = 0.226, 0.2295
    step = 0.0028
    prof = [
        (-0.006, 0.000),
        (-0.0025, 0.0012),
        (-0.0006, 0.0040),
        (_t(0.012), 0.012),
        (_t(band0), band0),
        (_t(band0) + step * 0.55, band0 + 0.0012),
        (_t(band1) + step, band1),         # grip band steps out 2.8 mm
        (_t(RIM_Z) + step, RIM_Z),
        (_t(RIM_Z) + 0.0058, RIM_Z + 0.0008),
        (_t(RIM_Z) + 0.0082, RIM_Z + 0.0040),
        (_t(RIM_Z) + 0.0090, RIM_Z + 0.0085),
        (_t(RIM_Z) + 0.0080, RIM_Z + 0.0125),
        (_t(RIM_Z) + 0.0055, RIM_Z + 0.0152),
        (_t(RIM_Z) + 0.0018, H),
        (_t(RIM_Z) - 0.0016, H - 0.0006),
        (_t(RIM_Z) - WALL, H - 0.0030),     # inner lip edge
        (_t(RIM_Z) - WALL, RIM_Z - 0.002),
        (_t(band1) - WALL + 0.0012, band1 - 0.002),
        (_t(band0) - WALL, band0 - 0.004),
        (_t(0.04) - WALL, 0.04),
        (_t(FLOOR_Z + 0.006) - WALL - 0.002, FLOOR_Z + 0.002),
        (_t(FLOOR_Z) - WALL - 0.007, FLOOR_Z),
    ]
    rr_lathe(kit, prof, PLASTIC, seg=6, name="basket shell")

    # Two crumpled sheets lying on the floor of the basket, visible down the
    # mouth from eye height; the bin is otherwise empty.
    paper_ball(kit, (-0.050, 0.018), FLOOR_Z, 0.038, seed=31, name="paper ball")
    paper_ball(kit, (0.052, 0.006), FLOOR_Z, 0.036, seed=17, name="paper ball")

    kit.collider((0, 0, H / 2), (0.28, 0.20, H))
    kit.anchor("mouth", (0, 0, H))
    kit.tag("office")
    kit.pile("Small")
