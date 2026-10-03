"""Giant B "Night Shift": the squeezed-giant version of Hunter concept B
(Documentation/research/hunter/11_squeezed_giant.md; base: creatures/hunter_b_night_shift.py,
10_hunter_directions.md §4).

The building's night electrician, blown up to ~1.75 x a person and never fitting the rooms:
a faded spruce coverall, hood drawn tight round a narrow strip of opal troffer lens
(0.20 x 0.40 m, the ceiling lens's 1 : 2) where his face should be. In every room the
shrugged shoulders are jammed against the ceiling tiles (the cloth flattens on them), the
neck cranes out of the front of the shrug and the hooded lens hangs down to the player's
eye line. Elbows splay, the knees fold, the coverall strains across the back and bunches
at the elbows, the collar is shoved up round the neck.

One body, four poses (POSES): `low` (2.4 m ceiling), `std` (2.9 m), `door` (half through a
1.0 x 2.1 m door, sideways), `tall` (the reveal in a 5.4 m zone). Every pose is one parameter
set (POSE[pose]) feeding the same skeleton: fixed bone lengths (spine, thigh/shin, upper arm/
forearm), IK for the limbs, and the costume parts placed from the body (frames, ray casts,
strips cut from the garments), so they follow it into every pose.

Helpers are copied from the base module (not imported) and take a scale `k`, so the gloves,
boots, hood, tape, belt, pouch, keys and name patch are a person's things blown up.
"""

import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

NAME = "Giant_B_NightShift"
TITLE = "Night Shift (giant)"
PITCH = ("The building's night electrician, grown too big for the building: a giant in a faded work "
         "coverall jammed under the ceiling tiles, its hood hanging down on a craned neck so the strip "
         "of lit ceiling lens where its face should be comes level with yours.")
SMOOTH_ANGLE = 60.0
POSES = {"low": {"top": 2.37, "halfWidth": 0.80}, "std": {"top": 2.86, "halfWidth": 0.80},
         "door": {"top": 2.9, "door": True}, "tall": {"top": 3.30, "halfWidth": 0.85}}
SIL_FRAME = (2.4, 3.6)
EYE = {"low": 1.45, "std": 1.72, "door": 1.45, "tall": 2.95}   # lens centre; build() writes the measured value
LENS_GLOW = 3.0       # preview emission strength (Hunt: dim, steady); 0 = Listen (off)

TWILL = "Creature_TwillSpruce"
LENS = "Creature_LensOpal"
PAPER = "Prop_Paper"
TAPE = "Creature_TapeSilver"
GLOVE = "Prop_FabricChair"
VINYL = "Prop_Vinyl"

# ---- one skeleton (metres). Base figure ~2.0 m standing; the giant stands ~3.25 m.
SPINE = (0.42, 0.42, 0.36, 0.22)   # pelvis -> belly -> chest -> shoulders -> shrug (trapezius, neck root)
THIGH, SHIN = 0.76, 0.68           # hip -> knee -> ankle (ankle ~0.16 above the floor): stocky
UPPER, FORE = 0.60, 0.64           # shoulder -> elbow -> wrist (Night Shift's long forearm)
HIP_HALF = 0.19
SOCKET_HALF = 0.31                 # arm sockets inside the shoulder ends
KH = 1.45                          # hood details (opening, hem, band, tunnel)
KG = 1.65                          # gloves: ~0.32 m hand
KF = 1.45                          # boots: ~0.45 m shoe
KC = 1.6                           # costume hardware: belt, pouch, tools, keys, patch, cords, tape bands
LENS_W, LENS_H = 0.20, 0.40        # the ceiling lens's 1 : 2, long axis vertical
HOOD_HALF = (0.198, 0.228, 0.275)  # hood shell half sizes (x, depth, z): ~0.40 x 0.55 m

# Per-pose parameters. Body frame: faces -Y, X = the figure's left, feet on z = 0.
#   pelvis          pelvis joint (x, y, z)
#   spine           (pitch, roll) deg per SPINE segment: pitch forward (-Y), roll toward +X
#   feet            ball-of-foot (x, y), yaw deg (toe out = +l / -r), heel lift deg
#   knee            knee pole (x, y, z) hint
#   lens, hood      lens centre (x, y, z) and hood (pitch, roll, yaw) deg; pitch = face down
#   wrist, elbow    wrist target and elbow pole hint per side
#   hand            (direction hint, mix toward it, palm hint, thumb hint)
#   ceiling         press the cloth flat under this height (None = free)
#   xform           (yaw deg, tx, ty): whole figure turned/moved after the build (door)
POSE = {
    "std": dict(
        pelvis=(0.0, 0.16, 1.56),
        spine=((8, 0), (22, 0), (38, 0), (72, 0)),
        feet=dict(l=((0.50, -0.34), 24.0, 0.0), r=((-0.48, 0.26), -20.0, 10.0)),
        knee=dict(l=(1.3, -1.0, 0.0), r=(-1.3, -1.0, 0.0)),
        lens=(0.0, -0.78, 1.78), hood=(26.0, 0.0, 0.0),
        wrist=dict(l=(0.47, -0.56, 1.58), r=(-0.38, -0.86, 2.765)),
        elbow=dict(l=(1.0, 0.25, 0.1), r=(-0.5, -0.1, -0.85)),
        hand=dict(l=((0.05, -0.25, -1.0), 0.55, (-1.0, 0.3, 0.0), (0.0, -1.0, 0.0)),
                  r=((-0.35, -1.0, 0.0), 1.0, (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), 0.15, 1.35)),
        ceiling=2.845,
        xform=None,
    ),
    "low": dict(
        pelvis=(0.0, 0.18, 1.12),
        spine=((12, 0), (24, 0), (40, 0), (75, 0)),
        feet=dict(l=((0.47, -0.34), 28.0, 0.0), r=((-0.46, 0.10), -26.0, 14.0)),
        knee=dict(l=(0.9, -1.0, 0.2), r=(-0.9, -1.0, 0.2)),
        lens=(0.0, -0.80, 1.42), hood=(20.0, 9.0, 0.0),
        wrist=dict(l=(0.36, -0.72, 1.14), r=(-0.33, -0.78, 1.18)),
        elbow=dict(l=(1.0, 0.3, 0.0), r=(-1.0, 0.3, 0.0)),
        hand=dict(l=((0.1, -0.3, -1.0), 0.6, (-1.0, 0.3, 0.0), (0.0, -1.0, 0.0), 1.3),
                  r=((-0.1, -0.3, -1.0), 0.6, (1.0, 0.3, 0.0), (0.0, -1.0, 0.0), 1.3)),
        ceiling=2.355,
        xform=None,
    ),
    "tall": dict(
        pelvis=(0.0, 0.06, 1.57),
        spine=((4, 0), (9, 0), (16, 0), (40, 0)),
        feet=dict(l=((0.24, -0.22), 12.0, 0.0), r=((-0.24, 0.16), -10.0, 8.0)),
        knee=dict(l=(0.3, -1.0, 0.0), r=(-0.3, -1.0, 0.0)),
        lens=(0.0, -0.60, 2.92), hood=(14.0, 0.0, 0.0),
        wrist=dict(l=(0.50, -0.20, 1.56), r=(-0.49, -0.12, 1.58)),
        elbow=dict(l=(0.5, 1.0, 0.0), r=(-0.5, 1.0, 0.0)),
        hand=dict(l=((0.05, -0.1, -1.0), 0.6, (-1.0, 0.25, 0.0), (0.0, -1.0, 0.0)),
                  r=((-0.05, -0.1, -1.0), 0.6, (1.0, 0.25, 0.0), (0.0, -1.0, 0.0))),
        ceiling=None,
        xform=None,
    ),
    "door": dict(          # body-frame pelvis/spine; everything else in WORLD space (door plane y = 0)
        world=True,
        pelvis=(0.0, 0.0, 0.74),
        spine=((12, -12), (16, -26), (20, -38), (50, -70)),
        feet=dict(l=((-0.05, 0.95), 95.0, 16.0), r=((0.08, -0.42), 40.0, 0.0)),   # ball (x, y), yaw, heel lift
        knee=dict(l=(1.0, 0.2, 0.2), r=(0.7, -0.7, 0.3)),
        lens=(0.04, -0.46, 1.45), hood=(10.0, -12.0, 15.0),
        wrist=dict(l=(0.78, 0.31, 1.30), r=(0.84, -0.37, 1.52)),
        elbow=dict(l=(0.6, 0.3, -0.4), r=(0.3, -0.4, 1.0)),
        hand=dict(l=((0.0, 0.0, 1.0), 0.9, (0.0, -1.0, 0.0), (-1.0, 0.0, 0.0), 0.5, 1.3),
                  r=((-1.0, 0.0, 0.0), 0.95, (0.0, 1.0, 0.0), (0.0, 0.0, 1.0), 0.8)),
        ceiling=None,
        xform=(80.0, -0.15, 0.62),
    ),
}


# ------------------------------------------------------------------ small maths helpers
def V(x, y, z):
    return Vector((x, y, z))


def deg(m3):
    e = m3.to_euler("XYZ")
    return (math.degrees(e.x), math.degrees(e.y), math.degrees(e.z))


def basis(x, y, z):
    """Rotation whose local X/Y/Z axes are the given world vectors."""
    return Matrix((x, y, z)).transposed()


def frame_z(direction, hint=None):
    """Rotation taking local +Z to `direction` (local X kept close to `hint`, default world X)."""
    z = direction.normalized()
    hint = hint or V(1, 0, 0)
    y = z.cross(hint)
    if y.length < 1e-4:
        y = z.cross(V(0, 1, 0))
    y.normalize()
    x = y.cross(z).normalized()
    return basis(x, y, z)


def ik(root, end, l1, l2, pole):
    """Two-bone IK: the middle joint for segment lengths l1, l2, bent toward `pole`."""
    d = end - root
    L = min(d.length, l1 + l2 - 1e-4)
    n = d.normalized()
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    p = pole - n * pole.dot(n)
    p.normalize()
    return root + n * a + p * h


def lerp(a, b, t):
    return a.lerp(b, t)


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def rot(pitch, roll, yaw):
    return Euler((math.radians(pitch), math.radians(roll), math.radians(yaw)), "XYZ").to_matrix()


# ------------------------------------------------------------------ mesh helpers (from the base)
def resample_loop(pts, count):
    """Even arc-length resampling of a closed polyline."""
    segs = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    lens = [(b - a).length for a, b in segs]
    total = sum(lens)
    out, k, acc = [], 0, 0.0
    for i in range(count):
        target = total * i / count
        while acc + lens[k] < target:
            acc += lens[k]
            k += 1
        a, b = segs[k]
        out.append(a.lerp(b, (target - acc) / max(lens[k], 1e-9)))
    return out


def loop_tube(kit, pts, radius, slot, normal, verts=10, name="loop"):
    """Closed round tube along a planar loop (ring frame from the loop's plane normal, so it
    never twists). `radius` is one number or one per point (a gathered hem)."""
    bm = bmesh.new()
    n = len(pts)
    radii = radius if isinstance(radius, (list, tuple)) else [radius] * n
    rings = []
    for k in range(n):
        p = pts[k]
        t = (pts[(k + 1) % n] - pts[k - 1]).normalized()
        side = t.cross(normal).normalized()
        up = side.cross(t).normalized()
        rings.append([bm.verts.new(p + (side * math.cos(2 * math.pi * i / verts) +
                                        up * math.sin(2 * math.pi * i / verts)) * radii[k])
                      for i in range(verts)])
    for k in range(n):
        a, b = rings[k], rings[(k + 1) % n]
        for i in range(verts):
            j = (i + 1) % verts
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def strip(kit, src, planes, keep, offset, thickness, slot, name="strip"):
    """Cut a strip out of a finished garment mesh between `planes` [(co, outward normal)],
    keep the vertices `keep(co)` accepts, push it out along the normals by `offset` and give
    it `thickness` (outward). Tape, belts, seams, creases: they hug the cloth they wrap."""
    bm = bmesh.new()
    bm.from_mesh(src.data)
    bm.transform(src.matrix_world.copy())
    for co, no in planes:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no, clear_outer=True)
    doomed = [v for v in bm.verts if not keep(v.co)]
    if doomed:
        bmesh.ops.delete(bm, geom=doomed, context="VERTS")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * offset
    obj = kit._new_object(name, bm, slot, "metres", "xz")
    if thickness:
        mod = obj.modifiers.new("solid", "SOLIDIFY")
        mod.thickness = thickness
        mod.offset = 1.0
        mod.use_even_offset = True
    return obj


def ray(objs, origin, direction, fallback=None):
    """Nearest hit on any of objs (applied meshes, identity transforms): (point, normal)."""
    best = None
    for o in objs:
        ok, loc, nor, _ = o.ray_cast(origin, direction)
        if ok:
            d = (loc - origin).length
            if best is None or d < best[0]:
                best = (d, loc.copy(), nor.normalized())
    if best is None:
        if fallback is not None:
            return fallback
        raise RuntimeError("ray missed at %s" % (tuple(origin),))
    return best[1], best[2]


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def bake(obj):
    """Apply an object's modifiers and transform (so its vertices are world positions)."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def press_parts(kit, ceiling, soft=0.10, spread=0.35):
    """The ceiling pushes back: every vertex above `ceiling - soft` is squashed smoothly
    toward the plane z = ceiling (tanh), and spread sideways a little where it is pressed,
    so the cloth flattens on the tiles instead of stopping short of them. Returns the
    number of vertices pressed. The decal lens is never touched (its UVs are local)."""
    bpy.context.view_layer.update()
    z0 = ceiling - soft
    count = 0
    for obj in list(kit.parts):
        if obj.get("fr_uv") == "decal" or not obj.data.vertices:
            continue
        mw = obj.matrix_world
        if max((mw @ v.co).z for v in obj.data.vertices) < z0 - 0.03:
            continue
        bake(obj)
        hot = [v for v in obj.data.vertices if v.co.z > z0]
        if not hot:
            continue
        cx = sum(v.co.x for v in hot) / len(hot)
        cy = sum(v.co.y for v in hot) / len(hot)
        for v in hot:
            t = v.co.z - z0
            new = soft * math.tanh(t / soft)
            dz = t - new
            h = V(v.co.x - cx, v.co.y - cy, 0.0)
            v.co.z = z0 + new
            if h.length > 1e-6:
                v.co += h.normalized() * dz * spread
        obj.data.update()
        count += len(hot)
    return count


# ------------------------------------------------------------------ body frames
def spine_points(pelvis, angles):
    pts = [pelvis]
    for length, (pitch, roll) in zip(SPINE, angles):
        p, r = math.radians(pitch), math.radians(roll)
        d = V(math.sin(r), -math.sin(p) * math.cos(r), math.cos(p) * math.cos(r))
        pts.append(pts[-1] + d * length)
    return pts


def seg_frames(pts):
    """Per spine segment: (a, b, x lateral (+ = figure's left), y back, z up the spine, s0, L)."""
    out, s = [], 0.0
    for a, b in zip(pts, pts[1:]):
        z = (b - a).normalized()
        x = (V(1, 0, 0) - z * z.x).normalized()
        y = z.cross(x).normalized()
        L = (b - a).length
        out.append((a, b, x, y, z, s, L))
        s += L
    return out


def torso_local(frames, co):
    """(lateral, back, arc length up the spine) of a point, from the nearest spine segment."""
    best = None
    for a, b, x, y, z, s0, L in frames:
        t = max(0.0, min(L, (co - a).dot(z)))
        q = co - (a + z * t)
        d = q.length
        if best is None or d < best[0]:
            best = (d, V(q.dot(x), q.dot(y), s0 + t))
    return best[1]


def at(frames, s):
    """Point and frame (x, y, z) on the spine at arc length s."""
    for a, b, x, y, z, s0, L in frames:
        if s <= s0 + L or (a, b) == frames[-1][:2]:
            return a + z * (s - s0), x, y, z
    raise ValueError(s)


# ------------------------------------------------------------------ body parts (from the base, scaled)
def rounded_rect(a, b, rc, count):
    """`count` evenly spaced points round a rounded rectangle (half sizes a x b, corner radius
    rc) in the head frame's x-z plane (y = 0), counter-clockwise seen from the front."""
    pts = []
    for cx, cz, a0 in ((a - rc, b - rc, 0.0), (rc - a, b - rc, 90.0), (rc - a, rc - b, 180.0), (a - rc, rc - b, 270.0)):
        for k in range(13):
            t = math.radians(a0 + 90.0 * k / 12)
            pts.append(V(cx + rc * math.cos(t), 0.0, cz + rc * math.sin(t)))
    return resample_loop(pts, count)


def se_radius(theta, ax, az, m):
    """Polar radius of the superellipse |x/ax|^m + |z/az|^m = 1 at angle theta."""
    c, s = abs(math.cos(theta)) / ax, abs(math.sin(theta)) / az
    return (c ** m + s ** m) ** (-1.0 / m)


def build_hood(kit, H, R, half, lens, k, m=2.4, n=48, shell_rings=12, band_rings=5, pleats=9):
    """Work hood drawn tight round the lens (base build_hood, every detail size x k).
    Head frame: origin H on the face plane at the lens centre, +y back into the head, R its
    rotation (face toward R @ -y). Shell = superellipsoid in rings round the face axis; a
    pleated, puffed band runs in to a rounded-rectangle drawcord opening on a flat plane with a
    gathered rolled hem that overlaps the lens border; a short tunnel buries the lens edges.
    The flat opal lens sits `lens_depth` behind the opening plane: no rim, no bezel.
    Returns a dict: lens, shell, centre, R, H, hem (world points)."""
    A, B, rc = 0.073 * k, 0.138 * k, 0.022 * k
    cy, zc, y_rim = 0.062 * k, 0.01 * k, 0.015 * k
    puff, brim, pleat_amp = 0.008 * k, 0.008 * k, 0.007 * k
    lens_depth, lens_drop, recess, hem_r, peak = 0.012 * k, 0.004 * k, 0.024 * k, 0.013 * k, 0.03 * k
    hx, hy, hz = half
    O = rounded_rect(A, B, rc, n)
    th = [math.atan2(o.z, o.x) for o in O]
    rad = [se_radius(t, hx, hz, m) for t in th]
    C = V(0, cy, zc)

    def shell_pt(i, alpha):
        ca, sa = math.cos(alpha), math.sin(alpha)
        s = abs(sa) ** (2.0 / m)
        return V(rad[i] * math.cos(th[i]) * s, cy - hy * math.copysign(abs(ca) ** (2.0 / m), ca),
                 zc + rad[i] * math.sin(th[i]) * s)

    def deform(p):
        """Fabric, not a helmet: a soft parka peak along the centre seam behind the crown,
        and the lower back drawn into the neck."""
        q = p - C
        fy, fz = q.y / hy, q.z / hz
        if fy > -0.3 and fz > 0:
            f = smooth((fy + 0.3) * 0.9) * smooth(fz * 1.2) * max(0.0, 1 - abs(q.x / hx)) ** 1.5
            q.y += peak * 0.7 * f
            q.z += peak * f
        if fy > 0 and fz < 0:
            q.z -= 0.04 * k * smooth(fy) * smooth(-fz)
        return C + q

    a_rim = math.acos(((cy - y_rim) / hy) ** (m / 2.0))
    rings = []
    for j in range(1, shell_rings + 1):                      # from the back pole to the rim
        alpha = math.pi - (math.pi - a_rim) * j / shell_rings
        rings.append([deform(shell_pt(i, alpha)) for i in range(n)])
    S = rings[-1]
    for j in range(1, band_rings + 1):                       # gathered band: rim -> opening
        g = 1 - (1 - j / band_rings) ** 1.6
        w = smooth(g / 0.45) * smooth((1 - g) / 0.25)
        ring = []
        for i in range(n):
            p = S[i].lerp(O[i], g)
            top = max(0.0, math.sin(th[i]))
            bulge = (puff + brim * top * top) * math.sin(math.pi * g) ** 0.8
            p.y = S[i].y * (1 - g) - bulge - pleat_amp * w * math.cos(2 * math.pi * pleats * i / n)
            ring.append(p)
        rings.append(ring)
    for d, yy in ((0.006 * k, 0.008 * k), (0.020 * k, recess)):   # tunnel behind the hem
        rings.append([V(o.x * (1 - d / o.length), yy, o.z * (1 - d / o.length)) for o in O])

    def W(p):
        return H + R @ p
    bm = bmesh.new()
    pole = bm.verts.new(W(deform(V(0, cy + hy, zc))))
    vr = [[bm.verts.new(W(p)) for p in ring] for ring in rings]
    floor = bm.verts.new(W(V(0, recess, 0)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((pole, vr[0][j], vr[0][i]))
        for r0, r1 in zip(vr, vr[1:]):
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
        bm.faces.new((vr[-1][i], vr[-1][j], floor))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    shell = kit._new_object("hood shell", bm, TWILL, "metres", "xz")
    hn = 40
    hem_o = rounded_rect(A, B, rc, hn)
    pts, radii = [], []
    for j, o in enumerate(hem_o):
        wave = math.cos(2 * math.pi * pleats * j / hn)
        bunch = max(math.exp(-((o - V(sx * A, 0, -B)).length / (0.03 * k)) ** 2) for sx in (1, -1))
        pts.append(W(V(o.x, -0.003 * k - 0.002 * k * wave, o.z)))
        radii.append(hem_r * (1.0 + 0.2 * wave + 0.3 * bunch))
    loop_tube(kit, pts, radii, TWILL, R @ V(0, -1, 0), verts=6, name="hood hem")
    lw, lh = lens
    # Decal UVs: the lens is a local x-z panel placed by its own rotation, so the Unity
    # material maps the whole troffer lens once across it (u across, v up).
    lens_obj = kit.bulged_panel(lw, lh, 0.006 * k, W(V(0, lens_depth, -lens_drop)), LENS, segments=8,
                                rot=deg(R), name="opal lens")
    return {"lens": lens_obj, "shell": shell, "centre": W(C), "R": R, "H": H, "hem": pts}


def build_glove(kit, cl, wrist_in, wrist, d, palm, thumb_hint, name, k=KG, curl=1.0, spread=1.0):
    """Black canvas work glove (base build_glove x k): cuff tube, palm block, four curled
    fingers and a thumb. `palm` hints the palm normal, `thumb_hint` which side the thumb is."""
    d = d.normalized()
    n = (palm - d * palm.dot(d)).normalized()
    s = n.cross(d).normalized()
    thumb = s if s.dot(thumb_hint) > 0 else -s
    cl.skin_body(kit, {"in": (tuple(wrist_in), 0.042 * k), "w": (tuple(wrist), 0.046 * k),
                       "p": (tuple(wrist + d * 0.04 * k), 0.044 * k)},
                 [("in", "w"), ("w", "p")], GLOVE, subdiv=1, name=name + " cuff")
    kit.soft_box((0.098 * k, 0.048 * k, 0.112 * k), wrist + d * 0.068 * k - n * 0.002 * k, GLOVE,
                 radius=0.014 * k, segments=16, rings=10, rot=deg(basis(s, n, d)), name=name + " palm")
    joints, bones = {}, []
    for i, (off, ls) in enumerate(((0.034, 0.93), (0.0115, 1.0), (-0.0115, 0.95), (-0.033, 0.80))):
        k0 = wrist + (d * 0.106 + thumb * off * spread - n * 0.004) * k
        fan = thumb * off * (spread - 1.0) * 0.8
        k1 = k0 + (d * (0.044 + 0.010 * (1 - curl)) + n * 0.012 * curl + fan) * ls * k
        k2 = k1 + (d * (0.024 + 0.024 * (1 - curl)) + n * 0.024 * curl + fan) * ls * k
        k3 = k2 + (d * (0.006 + 0.020 * (1 - curl)) + n * 0.022 * curl + fan * 0.5) * ls * k
        for j, (p, r) in enumerate(((k0, 0.0138), (k1, 0.0134), (k2, 0.0126), (k3, 0.0115))):
            joints["f%d%d" % (i, j)] = (tuple(p), r * k)
        bones += [("f%d0" % i, "f%d1" % i), ("f%d1" % i, "f%d2" % i), ("f%d2" % i, "f%d3" % i)]
    t0 = wrist + (d * 0.035 + thumb * 0.032 + n * 0.010) * k
    t1 = t0 + (d * 0.035 + thumb * 0.020 + n * 0.020) * k
    t2 = t1 + (d * 0.026 + thumb * 0.002 + n * 0.020) * k
    joints.update({"t0": (tuple(t0), 0.019 * k), "t1": (tuple(t1), 0.017 * k), "t2": (tuple(t2), 0.0145 * k)})
    bones += [("t0", "t1"), ("t1", "t2")]
    cl.decimate_to(cl.skin_body(kit, joints, bones, GLOVE, subdiv=1, name=name + " fingers"), 620)
    return wrist + (d * 0.20 + n * 0.03) * k        # ~fingertips


def foot_points(ball, yaw, pitch, k=KF):
    """Boot points from the ball-of-foot contact on the floor (base x k). Local +Y = back;
    `pitch` lifts everything behind the ball (heel raised), the toe stays flat."""
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    rz = Euler((0, 0, math.radians(yaw))).to_matrix()

    def P(x, y, z, flex=True):
        x, y, z = x * k, y * k, z * k
        if flex and y > 0:
            y, z = y * cp - z * sp, y * sp + z * cp
        return ball + rz @ V(x, y, z)
    return {
        "ankle": P(0, 0.150, 0.112), "instep": P(0, 0.070, 0.086),
        "heel": P(0, 0.205, 0.064), "mid": P(0, 0.100, 0.064),
        "ball": P(0, 0.0, 0.058, False), "toe": P(0, -0.098, 0.050, False),
        "_P": P,
    }


def build_boot(kit, cl, fp, shaft_top, yaw, pitch, name, k=KF):
    """Rubber-soled work boot (base x k): shaft chain into the instep, heel-to-toe foot chain, sole."""
    P = fp["_P"]
    j = {"s": (tuple(shaft_top), 0.056 * k), "a": (tuple(fp["ankle"]), 0.064 * k), "i": (tuple(fp["instep"]), 0.058 * k),
         "h": (tuple(fp["heel"]), 0.056 * k), "m": (tuple(fp["mid"]), 0.060 * k), "b": (tuple(fp["ball"]), 0.059 * k),
         "t": (tuple(fp["toe"]), 0.052 * k)}
    upper = cl.skin_body(kit, j, [("s", "a"), ("a", "i"), ("h", "m"), ("m", "b"), ("b", "t")], VINYL,
                         subdiv=2, name=name)
    rz = Euler((0, 0, math.radians(yaw))).to_matrix().inverted()
    base = V(fp["ball"].x, fp["ball"].y, 0.0)
    loc = [rz @ (v.co - base) for v in upper.data.vertices]
    low = [c for c in loc if c.z < 0.05 * k]
    front = min(c.y for c in loc if c.y < 0.02 * k)
    back = max(c.y for c in low) if pitch <= 0.5 else 0.195 * k
    half_w = max(abs(c.x) for c in low)
    y0, y1 = front + 0.006 * k, back - 0.006 * k
    w = 2 * half_w + 0.004 * k
    h = 0.03 * k

    def Pm(y, flex=True):          # P() takes base units
        return P(0, y / k, h / 2 / k, flex)
    if pitch > 0.5:
        kit.soft_box((w, y1, h), Pm(y1 / 2), VINYL, radius=0.012 * k, segments=16, rings=8,
                     rot=(pitch, 0, yaw), name=name + " sole heel")
        kit.soft_box((w - 0.002 * k, 0.01 * k - y0, h), Pm((y0 + 0.01 * k) / 2, False), VINYL, radius=0.012 * k,
                     segments=16, rings=8, rot=(0, 0, yaw), name=name + " sole toe")
    else:
        kit.soft_box((w, y1 - y0, h), Pm((y0 + y1) / 2), VINYL, radius=0.012 * k, segments=16, rings=8,
                     rot=(0, 0, yaw), name=name + " sole")
    cl.decimate_to(upper, 560)
    return front, back


def lens_glow(kit, strength):
    """Preview-only: opal lens emission, two lamp bands behind the diffuser and ONE soft shadow
    over one of them: a strip of a face pressed against the opal from inside (the tell)."""
    mat = kit._material(LENS)
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    bsdf = N.get("Principled BSDF")
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["UV"], sep.inputs[0])
    u, v = sep.outputs[0], sep.outputs[1]

    def m(op, a, b=None, clamp=False):
        node = N.new("ShaderNodeMath")
        node.operation = op
        node.use_clamp = clamp
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                node.inputs[i].default_value = x
            else:
                L.new(x, node.inputs[i])
        return node.outputs[0]

    def blob(cx, cy, rx, ry, soft):
        dx = m("DIVIDE", m("SUBTRACT", u, cx), rx)
        dy = m("DIVIDE", m("SUBTRACT", v, cy), ry)
        d = m("ADD", m("MULTIPLY", dx, dx), m("MULTIPLY", dy, dy))
        mr = N.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        L.new(d, mr.inputs["Value"])
        mr.inputs["From Min"].default_value = max(0.0, 1.0 - soft)
        mr.inputs["From Max"].default_value = 1.0
        mr.inputs["To Min"].default_value = 1.0
        mr.inputs["To Max"].default_value = 0.0
        return mr.outputs["Result"]

    terms = [(blob(0.76, 0.55, 0.42, 0.30, 0.9), 0.48),
             (blob(0.66, 0.53, 0.07, 0.15, 0.6), 0.26)]
    shadow = None
    for sock, w in terms:
        s = m("MULTIPLY", sock, w)
        shadow = s if shadow is None else m("ADD", shadow, s)
    lit = m("SUBTRACT", 1.0, m("MINIMUM", shadow, 0.75))
    band = None
    for c in (0.27, 0.73):
        b = m("SUBTRACT", 1.0, m("DIVIDE", m("ABSOLUTE", m("SUBTRACT", u, c)), 0.14), clamp=True)
        b = m("POWER", b, 0.6)
        band = b if band is None else m("ADD", band, b)
    glow = m("MULTIPLY", lit, m("ADD", 0.15, m("MULTIPLY", band, 1.8)))
    L.new(m("MULTIPLY", glow, strength), bsdf.inputs["Emission Strength"])
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.92, 0.78, 1.0)
    base = N.new("ShaderNodeMixRGB")
    base.blend_type = "MIX"
    L.new(lit, base.inputs["Fac"])
    base.inputs["Color1"].default_value = (0.45, 0.44, 0.41, 1)
    base.inputs["Color2"].default_value = (0.91, 0.894, 0.847, 1)
    L.new(base.outputs["Color"], bsdf.inputs["Base Color"])


def bezier(p0, p1, p2, t):
    return p0 * (1 - t) ** 2 + p1 * 2 * t * (1 - t) + p2 * t * t


# ------------------------------------------------------------------ the figure
def build(kit, cl, pose="std"):
    P = dict(POSE[pose])
    log = lambda *a: print("[giant_b/%s]" % pose, *a)
    if P.get("world"):
        # Door: targets (lens, wrists, hand vectors, foot balls/yaws) are given in WORLD space,
        # where the door plane is y = 0; bring them into the body frame the figure is built in.
        yaw0, tx, ty = P["xform"]
        Ri = Euler((0, 0, math.radians(-yaw0))).to_matrix()

        def Lp(p):
            return tuple(Ri @ (V(*p) - V(tx, ty, 0.0)))

        def Ld(v):
            return tuple(Ri @ V(*v))
        P["lens"] = Lp(P["lens"])
        P["hood"] = (P["hood"][0], P["hood"][1], P["hood"][2] - yaw0)
        P["wrist"] = {s: Lp(w) for s, w in P["wrist"].items()}
        P["elbow"] = {s: Ld(w) for s, w in P["elbow"].items()}
        P["knee"] = {s: Ld(w) for s, w in P["knee"].items()}
        P["hand"] = {s: (Ld(h[0]), h[1], Ld(h[2]), Ld(h[3])) + tuple(h[4:]) for s, h in P["hand"].items()}
        P["feet"] = {s: (Lp((f[0][0], f[0][1], 0.0))[:2], f[1] - yaw0, f[2]) for s, f in P["feet"].items()}

    # ---- spine and frames
    pts = spine_points(V(*P["pelvis"]), P["spine"])
    pelvis, belly, chest, shoulders, shrug = pts
    F = seg_frames(pts)
    fx_p, fy_p, fz_p = F[0][2], F[0][3], F[0][4]          # pelvis segment frame
    fx_s, fy_s, fz_s = F[2][2], F[2][3], F[2][4]          # chest -> shoulders frame

    # ---- feet first: the legs are solved down to them
    feet, ball = {}, {}
    for s in ("l", "r"):
        (bx, by), yaw, lift = P["feet"][s]
        feet[s] = foot_points(V(bx, by, 0.0), yaw, lift)

    # ---- legs (coverall), one chain each from inside the seat
    legs, leg_bones, knees, hips = {}, [], {}, {}
    for s, sx in (("l", 1), ("r", -1)):
        hip = pelvis + fx_p * (sx * HIP_HALF) - fz_p * 0.07 + fy_p * 0.01
        knee = ik(hip, feet[s]["ankle"], THIGH, SHIN, V(*P["knee"][s]))
        hips[s], knees[s] = hip, knee
        a = feet[s]["ankle"]
        legs["seat_" + s] = (tuple(pelvis + fx_p * (sx * 0.09) + fz_p * 0.08), 0.20)
        legs["hip_" + s] = (tuple(hip), 0.225)
        legs["thigh_" + s] = (tuple(lerp(hip, knee, 0.5)), 0.20)
        legs["knee_" + s] = (tuple(knee), 0.155)
        legs["calf_" + s] = (tuple(lerp(knee, a, 0.35)), 0.150)
        legs["tape_" + s] = (tuple(lerp(knee, a, 0.80)), 0.118)
        legs["hem_" + s] = (tuple(lerp(knee, a, 0.93)), 0.142)
        leg_bones += [("seat_" + s, "hip_" + s), ("hip_" + s, "thigh_" + s), ("thigh_" + s, "knee_" + s),
                      ("knee_" + s, "calf_" + s), ("calf_" + s, "tape_" + s), ("tape_" + s, "hem_" + s)]
    legs_obj = cl.skin_body(kit, legs, leg_bones, TWILL, subdiv=2, name="coverall legs")
    cl.decimate_to(legs_obj, 1700)

    # ---- torso (coverall): pelvis to the shrug. The shrug is the torso's own top (base §DESIGN):
    # a wide flat shoulder section tapering to a high trapezius that the ceiling flattens.
    crotch = pelvis - fz_p * 0.12 + fy_p * 0.02
    torso = {
        "crotch": (tuple(crotch), (0.14, 0.14)),
        "pelvis": (tuple(pelvis), (0.31, 0.25)),
        "belly": (tuple(belly), (0.32, 0.275)),
        "chest": (tuple(chest), (0.43, 0.30)),
        "shoulders": (tuple(shoulders), (0.44, 0.36)),
        "shrug": (tuple(shrug), (0.33, 0.27)),
    }
    torso_obj = cl.skin_body(kit, torso, [("crotch", "pelvis"), ("pelvis", "belly"), ("belly", "chest"),
                                          ("chest", "shoulders"), ("shoulders", "shrug")],
                             TWILL, subdiv=2, name="coverall torso")

    # ---- arms (sleeves) from inside the shoulder ends; elbows by IK toward the splay pole
    arm, arm_bones, wrists, elbows, sockets = {}, [], {}, {}, {}
    for s, sx in (("l", 1), ("r", -1)):
        sock = shoulders + fx_s * (sx * SOCKET_HALF) + fy_s * 0.03 + fz_s * 0.02
        wrist = V(*P["wrist"][s])
        elbow = ik(sock, wrist, UPPER, FORE, V(*P["elbow"][s]))
        sockets[s], wrists[s], elbows[s] = sock, wrist, elbow
        # Sleeve bunched at the elbow: a fat roll above and below the crook, pinched at it.
        ua, fa = (elbow - sock).normalized(), (wrist - elbow).normalized()
        arm.update({"sh_" + s: (tuple(sock), 0.155), "upper_" + s: (tuple(lerp(sock, elbow, 0.5)), 0.135),
                    "bunch_a_" + s: (tuple(elbow - ua * 0.11), 0.138), "elbow_" + s: (tuple(elbow), 0.112),
                    "bunch_b_" + s: (tuple(elbow + fa * 0.10), 0.128),
                    "fore_" + s: (tuple(lerp(elbow, wrist, 0.45)), 0.110),
                    "cinch_" + s: (tuple(lerp(elbow, wrist, 0.83)), 0.090),
                    "sleeve_" + s: (tuple(lerp(elbow, wrist, 0.93)), 0.100)})
        arm_bones += [("sh_" + s, "upper_" + s), ("upper_" + s, "bunch_a_" + s), ("bunch_a_" + s, "elbow_" + s),
                      ("elbow_" + s, "bunch_b_" + s), ("bunch_b_" + s, "fore_" + s), ("fore_" + s, "cinch_" + s),
                      ("cinch_" + s, "sleeve_" + s)]
    arms_obj = cl.skin_body(kit, arm, arm_bones, TWILL, subdiv=2, name="coverall arms")
    cl.decimate_to(arms_obj, 1700)

    # ---- gloves
    tips = {}
    for s in ("l", "r"):
        e, w = elbows[s], wrists[s]
        hd, mix, palm, thumb = P["hand"][s][:4]
        curl, spread = (P["hand"][s][4:] + (1.0, 1.0))[:2]
        d = (w - e).normalized().lerp(V(*hd).normalized(), mix)
        tips[s] = build_glove(kit, cl, lerp(e, w, 0.84), w, d, V(*palm), V(*thumb), "glove " + s,
                              curl=curl, spread=spread)

    # ---- boots
    for s in ("l", "r"):
        (bx, by), yaw, lift = P["feet"][s]
        build_boot(kit, cl, feet[s], lerp(knees[s], feet[s]["ankle"], 0.78), yaw, lift, "boot " + s)

    # ---- hood drawn tight round the lens, hanging on the craned neck
    H = V(*P["lens"])
    HR = rot(*P["hood"])
    hd = build_hood(kit, H, HR, HOOD_HALF, (LENS_W, LENS_H), KH)
    lens_obj, hood, hood_c = hd["lens"], hd["shell"], hd["centre"]
    HT = HR.transposed()

    # ---- neck: carries on out of the front of the shrug, then bows down into the back of the
    # hood. Wide where it leaves the trapezius and tapering into the hood (it is the hood's own
    # twill stretched over it), so it reads as a bowed bull neck, not a stalk or a hose.
    sdir = F[3][4]
    root = shrug - sdir * 0.06
    end = hood_c + HR @ V(0, 0.08, 0.05)
    reach = (end - root).length
    ctrl = root + sdir * reach * 0.42
    neck = {}
    for i in range(5):
        t = i / 4
        neck["n%d" % i] = (tuple(bezier(root, ctrl, end, t)), (0.38 - 0.23 * smooth(t * 1.15), 0.29 - 0.14 * smooth(t * 1.15)))
    neck_obj = cl.skin_body(kit, neck, [("n%d" % i, "n%d" % (i + 1)) for i in range(4)], TWILL, subdiv=2,
                            name="hood neck")
    cl.decimate_to(neck_obj, 900)
    neck_len = sum((V(*neck["n%d" % (i + 1)][0]) - V(*neck["n%d" % i][0])).length for i in range(4))

    bpy.context.view_layer.update()

    # ---- the coverall collar, shoved up round the neck where it leaves the shrug: a rolled,
    # bunched ring of twill, fattest at the back where the ceiling pushes it up.
    probe = bezier(root, ctrl, end, 0.75)
    hit, _ = ray([torso_obj], probe, (root - probe).normalized(), fallback=(bezier(root, ctrl, end, 0.3), None))
    tc = 0.3
    for j in range(20):                       # the curve parameter nearest the exit point
        t = j / 20
        if (bezier(root, ctrl, end, t) - hit).length < (bezier(root, ctrl, end, tc) - hit).length:
            tc = t
    tc = min(0.8, tc + 0.06)
    cc = bezier(root, ctrl, end, tc)
    ndir = (bezier(root, ctrl, end, tc + 0.05) - bezier(root, ctrl, end, tc - 0.05)).normalized()
    nr = 0.32 - 0.17 * smooth(tc * 1.15)
    e1 = (V(1, 0, 0) - ndir * ndir.x).normalized()
    e2 = ndir.cross(e1).normalized()
    cpts, crad = [], []
    for j in range(24):
        a = 2 * math.pi * j / 24
        dirv = e1 * math.cos(a) + e2 * math.sin(a)
        back = max(0.0, dirv.z)                # the top/back of the ring rides up
        cpts.append(cc + dirv * (nr * 0.86 + 0.025) + ndir * (0.03 * back))
        crad.append(0.034 * (1.0 + 0.45 * back + 0.18 * math.cos(5 * a)))
    loop_tube(kit, cpts, crad, TWILL, ndir, verts=8, name="collar")

    # ---- tape cuffs (wrists, ankles): strips of the sleeve / trouser leg, pushed out
    tb = 0.026 * KC
    for s in ("l", "r"):
        e, w = elbows[s], wrists[s]
        ax = (w - e).normalized()
        c = lerp(e, w, 0.83)
        strip(kit, arms_obj, [(c + ax * tb, ax), (c - ax * tb, -ax)],
              lambda co, c=c, ax=ax: ((co - c) - ax * (co - c).dot(ax)).length < 0.18,
              0.004, 0.005, TAPE, name="tape wrist " + s)
        k_, a = knees[s], feet[s]["ankle"]
        ax = (a - k_).normalized()
        c = lerp(k_, a, 0.80)
        strip(kit, legs_obj, [(c + ax * tb, ax), (c - ax * tb, -ax)],
              lambda co, c=c, ax=ax: ((co - c) - ax * (co - c).dot(ax)).length < 0.22,
              0.004, 0.005, TAPE, name="tape ankle " + s)


    # ---- drawcords: leave the hem at the opening's lower corners and hang straight down
    # (gravity sells the bowed hood), each ending in a metal aglet.
    for sx in (1, -1):
        corner = min(hd["hem"], key=lambda q: (HT @ (q - H) - V(sx * 0.07 * KH, 0, -0.135 * KH)).length)
        start = corner + HR @ V(-sx * 0.002, -0.014, 0)
        p1 = start + HR @ V(sx * 0.008, -0.016, -0.05)
        p2 = p1 + V(sx * 0.006, -0.004, -0.16)
        p3 = p2 + V(sx * 0.004, 0.006, -0.15)
        kit.tube([start, p1, p2, p3], 0.0055 * KC, VINYL, verts=8, name="drawcord")
        kit.cylinder(0.0075 * KC, 0.026 * KC, p3 + V(0, 0, -0.012 * KC), TAPE, verts=8, rot=(0, 0, 0),
                     bevel=0.002, segments=1, name="aglet")

    # ---- hood centre seam (raised strip of the shell along its centre plane, crown to nape),
    # carried on up the back of the neck to the collar: the neck is the hood's own twill.
    hx_ = HR @ V(1, 0, 0)
    strip(kit, hood, [(hood_c + hx_ * 0.0065, hx_), (hood_c - hx_ * 0.0065, -hx_)],
          lambda co: (HT @ (co - hood_c)).z > -0.03 and (HT @ (co - hood_c)).y > -0.03,
          0.0, 0.003, TWILL, name="hood seam")
    nb = (ctrl - root).cross(end - root)
    if nb.length > 1e-4:
        nb.normalize()
        convex = -(root - ctrl * 2 + end)              # B'' points into the bend; the seam runs outside it
        samples = [(bezier(root, ctrl, end, j / 24), j / 24) for j in range(25)]

        def on_top(co):
            q, t = min(samples, key=lambda st: (st[0] - co).length)
            tan = (bezier(root, ctrl, end, min(1, t + 0.02)) - bezier(root, ctrl, end, max(0, t - 0.02))).normalized()
            n_loc = (convex - tan * convex.dot(tan)).normalized()
            return (co - q).dot(n_loc) > 0.0
        strip(kit, neck_obj, [(root + nb * 0.0065, nb), (root - nb * 0.0065, -nb)], on_top,
              0.0, 0.003, TWILL, name="neck seam")

    # ---- action back: yoke seam across the shoulder blades, two pleats pulled open below it,
    # and strain creases fanning across the back where the ceiling holds the shrug down.
    s_yoke = F[2][5] + 0.06
    py, px_, pyb, pz_ = at(F, s_yoke)
    strip(kit, torso_obj, [(py + pz_ * 0.009, pz_), (py - pz_ * 0.009, -pz_), (py, -pyb)],
          lambda co: True, 0.0, 0.007, TWILL, name="back yoke seam")
    lo_s, hi_s = F[1][5] + 0.06, s_yoke - 0.03
    for lx in (0.15, -0.15):
        po, ax_, ay_, az_ = at(F, (lo_s + hi_s) / 2)
        p_lo, _, _, z_lo = at(F, lo_s)
        p_hi, _, _, z_hi = at(F, hi_s)
        strip(kit, torso_obj, [(po + ax_ * (lx + 0.011), ax_), (po + ax_ * (lx - 0.011), -ax_), (po, -ay_),
                               (p_lo, -z_lo), (p_hi, z_hi)],
              lambda co: True, 0.0, 0.009, TWILL, name="action pleat")
    # Strain creases: the cloth pulled taut over the shoulder blades where the tiles hold the
    # shrug down; soft ridges with clean ends, slightly fanned.
    for i, (ds, tilt, half) in enumerate(((0.10, 7.0, 0.30), (0.19, -5.0, 0.34), (0.28, 3.0, 0.30))):
        po, ax_, ay_, az_ = at(F, s_yoke + ds)
        nrm = (az_ * math.cos(math.radians(tilt)) + ax_ * math.sin(math.radians(tilt))).normalized()
        strip(kit, torso_obj, [(po + nrm * 0.016, nrm), (po - nrm * 0.016, -nrm), (po, -ay_),
                               (po + ax_ * half, ax_), (po - ax_ * half, -ax_)],
              lambda co: True, 0.0, 0.008, TWILL, name="strain crease %d" % i)

    # ---- coverall front: zip placket, two chest pocket flaps
    po, ax_, ay_, az_ = at(F, F[2][5] - 0.10)
    strip(kit, torso_obj, [(po + ax_ * 0.022, ax_), (po - ax_ * 0.022, -ax_)],
          lambda co: torso_local(F, co).y < -0.08 and 0.12 < torso_local(F, co).z < F[3][5] + 0.05,
          0.0, 0.007, TWILL, name="zip placket")
    s_pk = F[1][5] + 0.22
    for sx in (1, -1):
        po, ax_, ay_, az_ = at(F, s_pk)
        x0, x1 = sorted((sx * 0.07, sx * 0.29))
        strip(kit, torso_obj, [(po + ax_ * x1, ax_), (po + ax_ * x0, -ax_),
                               (po + az_ * 0.045, az_), (po - az_ * 0.045, -az_), (po, ay_)],
              lambda co: True, 0.003, 0.012, TWILL, name="pocket flap")

    # ---- tool belt: a strip of the coverall round the waist, square to the torso axis
    c = pelvis + fz_p * 0.19
    strip(kit, torso_obj, [(c + fz_p * 0.05, fz_p), (c - fz_p * 0.05, -fz_p)], lambda co: True,
          0.006, 0.018, VINYL, name="tool belt")

    # ---- tool pouch on the right hip (hangs from the belt), two tool handles
    hit, nor = ray([torso_obj, legs_obj], c - fx_p * 1.5 - fz_p * 0.08, fx_p)
    out = V(nor.x, nor.y, 0).normalized()
    up = V(0, 0, 1)
    side = up.cross(out).normalized()
    pc = hit + out * 0.045 * KC - up * 0.045 * KC
    M = basis(out, side, up)
    kit.soft_box((0.08 * KC, 0.15 * KC, 0.19 * KC), pc, VINYL, radius=0.02 * KC, segments=16, rings=10,
                 rot=deg(M), name="pouch")
    kit.soft_box((0.09 * KC, 0.158 * KC, 0.055 * KC), pc + (out * 0.006 + up * 0.08) * KC, VINYL,
                 radius=0.012 * KC, segments=12, rings=8, rot=deg(M), name="pouch flap")
    for j, (o, tilt, r, ln) in enumerate(((-0.035, 8, 0.013, 0.10), (0.036, -12, 0.010, 0.09))):
        tp = pc + (side * o + up * 0.125 + out * 0.005) * KC
        dirn = (up + side * math.tan(math.radians(tilt))).normalized()
        kit.cylinder(r * KC, ln * KC, tp, VINYL, verts=8, rot=deg(frame_z(dirn)), segments=1,
                     name="tool handle %d" % j)

    # ---- key ring on the left hip
    hit, nor = ray([torso_obj, legs_obj], c + fx_p * 1.5 - fz_p * 0.03 - fy_p * 0.06, -fx_p)
    out = V(nor.x, nor.y, 0).normalized()
    kc = hit + out * 0.012 * KC - V(0, 0, 0.055 * KC)
    kit.box((0.012 * KC, 0.02 * KC, 0.05 * KC), hit + out * 0.006 * KC - V(0, 0, 0.015 * KC), TAPE,
            rot=deg(frame_z(V(0, 0, 1), out)), name="key clip")
    tang = out.cross(V(0, 0, 1)).normalized()
    ring_pts = [kc + (V(0, 0, 1) * math.cos(a) + tang * math.sin(a)) * 0.024 * KC
                for a in [2 * math.pi * i / 16 for i in range(16)]]
    loop_tube(kit, ring_pts, 0.0028 * KC, TAPE, out, verts=4, name="key ring")
    for j, ang in enumerate((-25, 0, 20)):
        dirn = (V(0, 0, -1) + tang * math.tan(math.radians(ang))).normalized()
        kit.box((0.016 * KC, 0.003 * KC, 0.05 * KC), kc + dirn * 0.045 * KC, TAPE, bevel=0.0015, segments=1,
                rot=deg(frame_z(-dirn, tang)), name="key %d" % j)

    # ---- blank oval name patch (Prop_Paper) on the left chest, above the pocket
    po, ax_, ay_, az_ = at(F, s_pk + 0.15)
    o = po + ax_ * 0.20 - ay_ * 1.2
    hit, nor = ray([torso_obj], o, ay_)
    patch = kit.cylinder(0.044 * KC, 0.005, hit + nor * 0.003, PAPER, verts=16,
                         rot=deg(frame_z(nor, ax_)), bevel=0.0015, segments=1, name="name patch")
    patch.scale = (1.0, 0.58, 1.0)

    # ---- door: turn the whole figure sideways and set it in the doorway
    if P["xform"]:
        yaw, tx, ty = P["xform"]
        Mx = Matrix.Translation(V(tx, ty, 0.0)) @ Euler((0, 0, math.radians(yaw))).to_matrix().to_4x4()
        bpy.context.view_layer.update()
        for obj in kit.parts:
            obj.matrix_world = Mx @ obj.matrix_world
        bpy.context.view_layer.update()

    # ---- the ceiling pushes back
    bpy.context.view_layer.update()
    lo = min((o.matrix_world @ v.co).z for o in kit.parts for v in o.data.vertices)
    log("unpressed top %.3f" % (max((o.matrix_world @ v.co).z for o in kit.parts for v in o.data.vertices) - lo))
    pressed = press_parts(kit, P["ceiling"] + lo) if P["ceiling"] else 0

    # ---- finish
    lo = cl.floor_parts(kit)
    kit.no_collider()
    if LENS_GLOW > 0:
        lens_glow(kit, LENS_GLOW)
    bpy.context.view_layer.update()
    eye = (lens_obj.matrix_world @ V(0, 0, 0)).z
    EYE[pose] = round(eye, 3)

    # ---- diagnostics
    ws = [(o, o.matrix_world @ v.co) for o in kit.parts for v in o.data.vertices]
    top = max(w.z for _, w in ws)
    topname = max(ws, key=lambda t: t[1].z)[0].name
    hw = max(abs(w.x) for _, w in ws)
    hwname = max(ws, key=lambda t: abs(t[1].x))[0].name
    band = [w for o, w in ws if o.name.startswith(("coverall torso", "coverall arms")) and
            abs(w.z - (sockets["l"].z - lo)) < 0.06 and abs(w.y - sockets["l"].y) < 0.25]
    shoulder_w = (max(w.x for w in band) - min(w.x for w in band)) if band else 0.0
    crown = max((w for o, w in ws if o is hood), key=lambda w: w.z)
    log("top %.3f (%s), half-width %.3f (%s), lens centre %.3f, hood crown %.3f" % (top, topname, hw, hwname, eye, crown.z))
    log("neck length %.3f, shoulders across %.3f, pressed verts %d, floor shift %.3f" % (neck_len, shoulder_w, pressed, lo))
    log("fingertips z l %.2f r %.2f; mid-thigh l %.2f; knees z l %.2f r %.2f; hips z %.2f" % (
        tips["l"].z - lo, tips["r"].z - lo, (lerp(hips["l"], knees["l"], 0.5)).z - lo, knees["l"].z - lo,
        knees["r"].z - lo, pelvis.z - lo))
    if P["xform"]:
        slab = [(o, w) for o, w in ws if abs(w.y) < 0.15]
        dz = max(slab, key=lambda t: t[1].z) if slab else None
        dx = max(slab, key=lambda t: abs(t[1].x)) if slab else None
        if slab:
            log("door slab: top %.3f (%s), |x| %.3f (%s)" % (dz[1].z, dz[0].name, abs(dx[1].x), dx[0].name))
            bad = {}
            for o, w in slab:
                if w.z > 2.08 or abs(w.x) > 0.48:
                    bad.setdefault(o.name, []).append(w)
            for nme, wl in bad.items():
                log("  slab violation %s: %d verts, max z %.3f, max |x| %.3f, y %.3f..%.3f" % (
                    nme, len(wl), max(w.z for w in wl), max(abs(w.x) for w in wl), min(w.y for w in wl), max(w.y for w in wl)))
        log("lens world (%.2f, %.2f, %.2f)" % tuple(lens_obj.matrix_world @ V(0, 0, 0)))
    total = sum(tris(o) for o in kit.parts)
    log("parts %d, tris (pre-modifier) %d, eye %.3f" % (len(kit.parts), total, eye))


# DESIGN (giant pass, 2026-10-02; see the hand-off notes)
# * Kept from the base: the hood (superellipsoid shell, pleated drawn band, gathered hem, cords
#   from the lower corners, centre seam, parka peak), the flat rimless opal lens with decal UVs
#   and the one-shadow tell, tape cuffs at wrists and ankles, tool belt + pouch + tool handles,
#   key ring, Prop_Paper name patch, black gloves, rubber-soled boots, zip placket, pocket
#   flaps, action-back yoke and pleats, the shrug as the torso's own top, 6 slots.
# * New for the squeeze: the shrug is pressed flat on the ceiling (press_parts), the neck
#   cranes out of the front of the shrug inside a sleeve of hood twill, the coverall collar is
#   shoved up round it, strain creases fan across the back, the sleeves bunch at the elbows,
#   the cords hang plumb from the bowed hood.
