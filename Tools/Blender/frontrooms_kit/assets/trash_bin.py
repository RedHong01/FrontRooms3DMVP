"""Rectangular office wastebasket, moulded grey polypropylene, c. 1985-2000
(the 13-quart Rubbermaid-type desk-side basket: tapered walls, generous
corner radii, a rolled lip, a stepped-out stacking/grip band under the lip,
a recessed base with a rounded heel). Empty.

Real-world reference size (10_synthesis §5.3): 0.36 m wide x 0.26 m deep x
0.38 m tall at the lip; base 0.29 x 0.19 m. Wall 3 mm. Origin = floor under
the centre. Front looks -Y (the basket is symmetric).

Budget 400 tris (this shell is ~500, 1.25x, inside the 1.4x silhouette
allowance: the lip is the brightest edge and the outline seen from 2 m, and
4-step corners showed as kinks in it). One slot (PlasticGrey), no collider
(§5.3), pile Small 0. The shell is a rounded-rectangle "lathe" built here
with bmesh (the kit's lathe only revolves circles) with 6-step corners and
nine profile rings. The stacking band is a 6 mm ledge over 2 mm of height:
near-horizontal, so its rings are split sharp and the down-facing ledge
reads as a dark line under top light. Analytic custom normals keep the long
flat sides flat-shaded and the corners round.

Placer note (FrontRoomsOfficeKit.cs, not this module): put the bin on the
desk's knee-space side only; the pedestal side intersects the pedestal.
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_TrashBin"
SMOOTH_ANGLE = 50.0      # the rolled lip shades round, the heel and ledge stay crisp

PLASTIC = "Prop_PlasticGrey"

H = 0.38
RIM_Z = 0.364          # top of the tapered wall, start of the rolled lip
BASE_HX, BASE_HY = 0.144, 0.094     # outer half sizes at z = 0
BASE_R = 0.038          # corner radius at the base (grows with the taper)
TAPER = 0.024           # outward growth per side from base to rim (envelope 0.36 x 0.26)
WALL = 0.003
FLOOR_Z = 0.009
CORNER_SEG = 6          # corner steps per 90 degrees (28 verts a ring): the lip outline reads round


def _rr_ring(bm, off, z, seg):
    """One ring of the rounded rectangle grown by ``off``; returns the verts
    and each vert's planar outward direction (exact at the arc ends, so the
    flat sides shade flat)."""
    hx, hy, r = BASE_HX + off, BASE_HY + off, BASE_R + off
    ring, dirs = [], []
    for cx, cy, a0 in ((hx - r, hy - r, 0), (-(hx - r), hy - r, 90), (-(hx - r), -(hy - r), 180), (hx - r, -(hy - r), 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90.0 * k / seg)
            ring.append(bm.verts.new((cx + r * math.cos(a), cy + r * math.sin(a), z)))
            dirs.append(Vector((math.cos(a), math.sin(a), 0.0)))
    return ring, dirs


def rr_lathe(kit, profile, slot, seg=5, smooth_angle=50.0, name="rr lathe"):
    """Sweep an (offset, z) profile round the base rounded rectangle: offset
    grows the half sizes and the corner radius together, so a linear offset
    is a uniform draft. Bottom and top rings are capped.

    With few corner steps, plain smooth shading smears the corner normals
    across the long flat sides (streaks). So the part gets analytic custom
    normals instead: planar direction of the ring x the profile normal, split
    where the profile turns more than ``smooth_angle`` (heel, ledge, floor)."""
    bm = bmesh.new()
    built = [_rr_ring(bm, off, z, seg) for off, z in profile]
    rings = [r for r, _ in built]
    dirs = built[0][1]
    n = len(rings[0])
    # Profile normal of each band, (offset, z) components: outward on the
    # outer wall going up, into the cavity on the inner wall going down.
    band_n = []
    for (o0, z0), (o1, z1) in zip(profile, profile[1:]):
        v = Vector((z1 - z0, -(o1 - o0)))
        band_n.append(v.normalized())
    cos_lim = math.cos(math.radians(smooth_angle))
    ring_of = {}
    for k, ring in enumerate(rings):
        for i, v in enumerate(ring):
            ring_of[v] = (k, i)
    band_of = {}
    for k, (ra, rb) in enumerate(zip(rings, rings[1:])):
        for i in range(n):
            j = (i + 1) % n
            band_of[bm.faces.new((ra[i], ra[j], rb[j], rb[i]))] = k
    bottom = bm.faces.new(list(reversed(rings[0])))
    top = bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cap_n = {bottom: Vector((0, 0, -1)), top: Vector((0, 0, 1))}
    if bottom.normal.z > 0:
        cap_n[bottom] = Vector((0, 0, 1))
    if top.normal.z < 0:
        cap_n[top] = Vector((0, 0, -1))

    # Faces smooth and the sharp edges marked exactly as finish() will mark
    # them, so the custom normals are encoded in the final smoothing fans
    # (shade_smooth / set_sharp_from_angle would otherwise rotate them).
    for f in bm.faces:
        f.smooth = True
    sharp_ring = set()
    for k in range(1, len(rings) - 1):
        if band_n[k - 1].dot(band_n[k]) < cos_lim:
            sharp_ring.add(k)
    if Vector((0.0, -1.0)).dot(band_n[0]) < cos_lim:
        sharp_ring.add(0)
    if Vector((0.0, 1.0)).dot(band_n[-1]) < cos_lim:
        sharp_ring.add(len(rings) - 1)
    for k in sharp_ring:
        ring = rings[k]
        for i in range(n):
            e = bm.edges.get((ring[i], ring[(i + 1) % n]))
            if e is not None:
                e.smooth = False

    def prof_normal(k, ring_k):
        """Profile normal used by band k at ring ring_k (k or k + 1)."""
        nb = band_n[k]
        other = k - 1 if ring_k == k else k + 1
        if 0 <= other < len(band_n) and nb.dot(band_n[other]) >= cos_lim:
            return (nb + band_n[other]).normalized()
        return nb

    loop_normals = []
    for f in bm.faces:
        for loop in f.loops:
            if f in cap_n:
                loop_normals.append(cap_n[f])
                continue
            rk, i = ring_of[loop.vert]
            pn = prof_normal(band_of[f], rk)
            loop_normals.append((dirs[i] * pn.x + Vector((0, 0, pn.y))).normalized())
    obj = kit._new_object(name, bm, slot, "metres", "xz")
    obj.data.normals_split_custom_set([tuple(v) for v in loop_normals])
    return obj


def _t(z):
    return TAPER * z / RIM_Z


def build(kit):
    # Profile: base heel -> tapered wall -> stacking ledge -> grip band ->
    # rolled lip -> inner wall -> floor. Offsets are outward from the base
    # rectangle. Nine rings: every one is a silhouette or a shading break
    # seen from 2 m.
    band0, band1 = 0.287, 0.289
    step = 0.006
    rim = _t(RIM_Z)
    prof = [
        (-0.006, 0.000),                    # recessed base (heel in contact shadow)
        (_t(band0), band0),                 # foot of the stacking ledge (sharp)
        (_t(band1) + step, band1),          # ledge steps out 6 mm over 2 mm (sharp, dark line)
        (rim + step, RIM_Z),                # grip band up to the lip
        (rim + 0.0122, RIM_Z + 0.0060),     # rolled lip, outer bulge
        (rim + 0.0098, RIM_Z + 0.0132),
        (rim + 0.0010, H),                  # lip top
        (rim - WALL, H - 0.0016),           # inner lip edge (a crisp edge: the inner wall shades flat)
        (_t(FLOOR_Z) - WALL - 0.006, FLOOR_Z),   # inner wall down to the floor
    ]
    rr_lathe(kit, prof, PLASTIC, seg=CORNER_SEG, smooth_angle=SMOOTH_ANGLE, name="basket shell")

    # §5.3: no collider (the pile and the room dresser treat it as clutter).
    kit.no_collider()
    kit.anchor("mouth", (0, 0, H))
    kit.tag("office")
    kit.pile("Small", mass=0)
