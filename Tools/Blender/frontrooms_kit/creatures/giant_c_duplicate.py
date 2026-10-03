"""Giant C — "Duplicate (giant)": the photocopied office worker as a squeezed giant
(Documentation/research/hunter/11_squeezed_giant.md, built on 10_hunter_directions.md §5 and the
human-scale module creatures/hunter_c_duplicate.py, whose helpers are copied here, not imported).

The copy is an ENLARGEMENT: the same black-and-white print of an employee (paper shirt, toner head,
tie, trousers and shoes, a flat printed sad face, the drum streak, the baked toner edge) blown up
~1.75x past the page, so the printed face, the streak and the pocket scale with it. It never fits
the rooms it hunts in: the long "page" trunk is pressed up into the ceiling tiles and folds over
forward like a sheet too tall for its frame, the back of the shirt stretched round the fold (printed
tension creases across it, the contact patch flattened), the head hanging down out of the front of
the fold to the player's eye line, the elbows splayed, the sleeves bunched, the collar shoved up.
Where the enlargement ran off the page, the outer edge of one elbow is simply cut off flat, its cut
face toner-black like the margin of a copy made with the lid up.

Rig: one rest body (the upright print) and one parameter set per pose (POSE below):
- the trunk is built upright in its rest frame and bent along a posed spine (pitch/roll/yaw rates
  per spine section, about a bend axis that runs near the chest front, so the back stretches and
  the chest creases); every shirt detail (belt, tie, pocket, pen, streak, creases) is built on the
  rest shirt and bent with it;
- arms and legs are two-bone IK chains of fixed length from the bent trunk's shoulders/hips to
  per-pose wrist/ankle targets with pole vectors; hands, shoes and head follow those frames;
- a soft ceiling clamp flattens whatever the pose pushes into the tiles.

Conventions: metres, Z up, facing -Y, left = +X; rotations X pitch, Y roll, Z yaw (Blender XYZ
Euler); feet on z = 0 after cl.floor_parts(); centred on the nav axis x = y = 0, except the door
pose, whose origin is the door centre (the door plane is y = 0).
"""

import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

NAME = "Giant_C_Duplicate"
TITLE = "Duplicate (giant)"
PITCH = ("The photocopied office worker blown up past the page: a 3.3 m black-and-white print whose long "
         "paper shirt is folded over under the ceiling tiles, its toner head with the flat printed sad face "
         "hanging down out of the fold to your eye line.")
SMOOTH_ANGLE = 60.0

POSES = {"low": {"top": 2.37, "halfWidth": 0.80}, "std": {"top": 2.86, "halfWidth": 0.80},
         "door": {"top": 2.9, "door": True}, "tall": {"top": 3.30, "halfWidth": 0.85}}
SIL_FRAME = (2.4, 3.6)
EYE = {"low": 1.45, "std": 1.80, "door": 1.45, "tall": 2.95}   # replaced in build() by the measured face centre

DEBUG = {}
PAPER = "Prop_Paper"          # shirt, collar, cuffs, face, hands, neck, ears (with the baked toner-edge term)
TONER = "Creature_Toner"      # head and hair, print ink, tie, trousers, belt, shoes, pen, creases, cut faces

# ------------------------------------------------------------------ rest body (the upright print, giant metres)
TRUNK_STRETCH = 1.12                   # the page slipped: the trunk above the belly is drawn out 12 % more


def _rz(z):
    """Design height on the trunk -> rest height after the page-slip stretch."""
    return z if z <= 0.42 else 0.42 + (z - 0.42) * TRUNK_STRETCH


# Trunk rows above the hip joint: (z, half-width, front y, back y). The base page shirt scaled ~1.75x in
# length, ~1.45x in width (shoulders 0.93 m across the cloth), ~1.6x in depth: a heavy, deep trunk,
# straight-sided from the belt, opening under the sleeves into the level, square-cornered shoulder block.
TRUNK = [
    (0.180, 0.300, -0.200, 0.230),     # hem, tucked inside the belt
    (0.210, 0.330, -0.250, 0.255),
    (0.280, 0.345, -0.300, 0.272),
    (0.380, 0.352, -0.340, 0.280),
    (0.500, 0.355, -0.360, 0.286),     # paunch
    (0.620, 0.356, -0.362, 0.296),
    (0.740, 0.358, -0.352, 0.316),
    (0.860, 0.362, -0.335, 0.346),     # a heavy, rounded upper back
    (0.960, 0.368, -0.318, 0.370),     # shoulder blades
    (1.020, 0.385, -0.310, 0.378),     # armpit: the block opens out behind the sleeve tops
    (1.060, 0.436, -0.304, 0.375),
    (1.090, 0.461, -0.300, 0.368),
    (1.120, 0.468, -0.296, 0.355),     # from here up the flank is plumb, flush with the sleeve
    (1.220, 0.470, -0.285, 0.315),
    (1.320, 0.470, -0.272, 0.255),
    (1.380, 0.470, -0.262, 0.215),     # start of the shoulder corner
]
TRUNK = [(_rz(r[0]),) + r[1:] for r in TRUNK]
SHOULDER_R = 0.050                     # corner radius seen from the front
SHOULDER_TOP = _rz(1.430)                  # the level shoulder line
COLLAR_RING = (0.165, _rz(1.455), -0.255, -0.020)   # half-width, z, front y, back y
SECTION_N = 2.6                        # superellipse exponent of the trunk sections (2 = ellipse)
ROW_STEP = 0.021                       # rest spacing of the lofted rows (the folded back stretches 3-4x)
# The line the trunk bends about, (rest z, rest y): centred in the pelvis, near the chest front higher up,
# so a forward fold creases the chest and stretches the back round the fold.
BEND_AXIS = [(-0.6, 0.0), (0.42, 0.0), (0.95, -0.06), (2.0, -0.06)]

HIP_REST = (0.165, 0.060, 0.0)         # hip joints in the trunk's rest frame (mirrored for the right)
WAIST_REST = (0.125, 0.090, 0.215)     # trouser roots, behind the belt
SHOULDER_REST = (0.392, -0.030, _rz(1.290)) # shoulder joints, inside the shoulder block
NECK_REST = (0.0, -0.135, _rz(1.385))      # neck base, inside the collar
THIGH, SHIN = 0.660, 0.620
ANKLE_H = 0.220                        # ankle joint above the sole (flat shoe)
UPPER_ARM, FOREARM = 0.600, 0.580      # fingertips at mid-thigh when it stands
NECK_LEN = (0.160, 0.150)
HEAD_S = 1.55                          # the base head and its printed face, enlarged (0.42 m tall)
HEAD_NECK = Vector((0.0, -0.075, 0.075))   # head centre from the neck end, head-local (the neck enters the nape)

# ------------------------------------------------------------------ the poses (one parameter set each)
# root: pelvis centre (world); yaw: body yaw; pelvis: (pitch, roll); spine: (z0, z1, pitch, roll, yaw)
# bends spread evenly over each rest section; neck: absolute (pitch, roll, yaw) of its two segments;
# head: absolute (pitch, roll, yaw); arm: wrist target, elbow pole, finger direction, palm normal, curl;
# leg: ankle target, knee pole, foot yaw, heel lift; ceiling: the tiles the pose presses (None = free).
POSE = {
    "std": {
        "root": (0.0, 0.22, 1.37), "yaw": 0.0, "pelvis": (-2.0, 0.0),
        "spine": [(0.00, 0.42, 4.0, 0.0, 0.0), (0.42, 0.95, 22.0, 0.0, 0.0),
                  (0.95, 1.32, 62.0, 0.0, 0.0), (1.32, 1.62, 68.0, 0.0, 0.0)],
        "shoulder": (0.395, 0.0, _rz(1.27)),
        "neck": ((168.0, 0.0, 0.0), (140.0, 0.0, 0.0)), "head": (20.0, 6.0, 0.0),
        "arm_l": {"wrist": (0.50, -0.66, 1.74), "pole": (1.0, 0.45, 0.25), "down": (-0.30, -0.45, -1.0),
                  "palm": (-1.0, 0.3, 0.0), "curl": 40.0},
        "arm_r": {"wrist": (-0.53, -0.58, 1.66), "pole": (-1.0, 0.45, 0.20), "down": (0.25, -0.40, -1.0),
                  "palm": (1.0, 0.3, 0.0), "curl": 55.0},
        "leg_l": {"ankle": (0.46, 0.02, ANKLE_H), "pole": (0.65, -1.0, 0.0), "yaw": 20.0, "heel": 0.0},
        "leg_r": {"ankle": (-0.44, 0.46, ANKLE_H + 0.03), "pole": (-0.60, -1.0, 0.0), "yaw": -18.0, "heel": 12.0},
        "ceiling": 2.90, "tie": "hang", "crop": 0.10,
    },
}


# ------------------------------------------------------------------ helpers (copied from hunter_c_duplicate)
def _bvh(objs):
    verts, polys = [], []
    for obj in objs:
        mw = obj.matrix_world
        base = len(verts)
        verts += [mw @ v.co for v in obj.data.vertices]
        polys += [tuple(base + i for i in p.vertices) for p in obj.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


def _front(tree, x, z):
    """First surface hit looking from the front (-Y) toward +Y at (x, z): (location, normal) or None."""
    loc, nrm, _i, _d = tree.ray_cast(Vector((x, -2.0, z)), Vector((0, 1, 0)))
    return (loc, nrm) if loc is not None else None


def _back(tree, x, z):
    """First surface hit looking from behind (+Y) toward -Y at (x, z)."""
    loc, nrm, _i, _d = tree.ray_cast(Vector((x, 2.0, z)), Vector((0, -1, 0)))
    return (loc, nrm) if loc is not None else None


def _smooth(a, b, x):
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _ellipse(cx, cz, w, h, n=14, tilt=0.0, droop=0.0, power=1.0):
    """Closed outline (u, v) of an ellipse-ish blob; droop pulls the +u end down."""
    pts = []
    ct, st = math.cos(math.radians(tilt)), math.sin(math.radians(tilt))
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        u = math.copysign(abs(c) ** power, c) * w / 2
        v = math.copysign(abs(s) ** power, s) * h / 2
        v -= droop * max(0.0, u / (w / 2)) ** 2
        pts.append((cx + u * ct - v * st, cz + u * st + v * ct))
    return pts


def _mirror(outline):
    return [(-u, v) for (u, v) in reversed(outline)]


def _stroke(points, width, taper=0.5):
    """Closed outline around a polyline [(u, v)...]: a brush stroke, thinner at the ends."""
    pts = [Vector((p[0], p[1])) for p in points]
    up, down = [], []
    for k, p in enumerate(pts):
        a = pts[max(k - 1, 0)]
        b = pts[min(k + 1, len(pts) - 1)]
        d = (b - a).normalized()
        nrm = Vector((-d.y, d.x))
        f = k / (len(pts) - 1)
        w = width / 2 * (1 - taper * (2 * f - 1) ** 2)
        up.append(tuple(p + nrm * w))
        down.append(tuple(p - nrm * w))
    return up + list(reversed(down))


# Head-local face art (the base head's own units; the whole head is enlarged by HEAD_S afterwards).
HEAD_HX = 0.095
HEAD_HY_FRONT, HEAD_HY_BACK = 0.130, 0.118
HEAD_HZ_TOP, HEAD_HZ_BOT = 0.145, 0.125
HEAD_FRONT = 0.060                    # the skull is cut flat this far in front of its centre
FACE_W, FACE_H, FACE_Z = 0.148, 0.190, -0.006
STREAK_X = -0.054                     # the drum streak, face and shirt (the lit side)
STREAK_W = 0.010                      # enlarged with the print: 2.5x the base streak before HEAD_S
HAIR_BAND = Vector((0, -0.024, 0))
HAIRLINE = [((0, -0.024, 0.034), (0, 0.070, 0.014)),
            ((0, 0.040, 0.030), (0, 0.125, -0.080))]


def _face_outline(n=64):
    """The printed face, head-local (u, v): what a copier keeps of a face lit from its right."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        e = 0.74 if s > 0 else 0.92
        u = math.copysign(abs(c) ** e, c) * FACE_W / 2
        v = math.copysign(abs(s) ** e, s) * FACE_H / 2
        if s < 0:
            u *= 1 - 0.36 * (-s) ** 1.6
        top = FACE_H / 2 - 0.004 - 0.030 * _smooth(-0.030, 0.075, u) - 0.010 * _smooth(-0.030, -0.080, u)
        v = min(v, top)
        if u > 0 and v < 0.004:
            lim = 0.066 - 0.030 * _smooth(0.004, -0.060, v)
            u = min(u, lim)
        pts.append((u, FACE_Z + v))
    return pts


def _v_range(outline, u):
    vs = []
    for (u0, v0), (u1, v1) in zip(outline, outline[1:] + outline[:1]):
        if (u0 - u) * (u1 - u) <= 0 and u0 != u1:
            vs.append(v0 + (v1 - v0) * (u - u0) / (u1 - u0))
    return min(vs), max(vs)


def _reshape(obj, fn):
    for v in obj.data.vertices:
        v.co = fn(Vector(v.co))


def _new_mesh(kit, bm, slot, name):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _bake(obj):
    """Fold the object transform into the mesh (so vertex positions and normals are world)."""
    obj.data.transform(obj.matrix_basis)
    obj.matrix_basis = Matrix.Identity(4)
    obj.data.update()
    return obj


def _band(kit, rings, slot, name):
    """Closed tube through a list of rings (each a list of Vectors, same count), capped."""
    bm = bmesh.new()
    vr = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for a, b in zip(vr, vr[1:]):
        for i in range(n):
            k = (i + 1) % n
            bm.faces.new((a[i], a[k], b[k], b[i]))
    bm.faces.new(list(reversed(vr[0])))
    bm.faces.new(vr[-1])
    return _new_mesh(kit, bm, slot, name)


def _pocket(kit, tree, cx, w, z_top, z_bot, nu=6, nv=9, front=0.006, back=0.003):
    """A patch pocket lying on the (rest) shirt, thickened along the normal, pointed bottom."""
    grid = []
    for jv in range(nv):
        f = jv / (nv - 1)
        z = z_top + (z_bot - z_top) * f
        row = []
        for iu in range(nu):
            g = iu / (nu - 1)
            x = cx - w / 2 + w * g
            zz = z + (0.024 * abs(2 * g - 1) ** 2 if f == 1.0 else 0.0)
            hit = _front(tree, x, zz)
            row.append(hit if hit else (Vector((x, -0.3, zz)), Vector((0, -1, 0))))
        grid.append(row)
    bm = bmesh.new()
    F = [[bm.verts.new(p + n * front) for p, n in row] for row in grid]
    K = [[bm.verts.new(p - n * back) for p, n in row] for row in grid]
    for jv in range(nv - 1):
        for iu in range(nu - 1):
            bm.faces.new((F[jv][iu], F[jv + 1][iu], F[jv + 1][iu + 1], F[jv][iu + 1]))
            bm.faces.new((K[jv][iu], K[jv][iu + 1], K[jv + 1][iu + 1], K[jv + 1][iu]))
    ring = [(0, iu) for iu in range(nu)] + [(jv, nu - 1) for jv in range(1, nv)] + \
           [(nv - 1, iu) for iu in range(nu - 2, -1, -1)] + [(jv, 0) for jv in range(nv - 2, 0, -1)]
    for (a1, b1), (a2, b2) in zip(ring, ring[1:] + ring[:1]):
        bm.faces.new((F[a1][b1], F[a2][b2], K[a2][b2], K[a1][b1]))
    return _new_mesh(kit, bm, PAPER, "pocket")


def _strip(kit, pts, widths, normals, thick, slot, name, tip=0.0, side=None):
    """A flat strip lying on a surface: pts top to bottom, offset along the normals, optional pointed tip.
    side: the strip's width direction (one vector, or one per point); default world X."""
    bm = bmesh.new()
    rows = []
    for k, (p, w, nrm) in enumerate(zip(pts, widths, normals)):
        sd = side[k] if isinstance(side, list) else (side or Vector((1, 0, 0)))
        rows.append([bm.verts.new(p + sd * sx * w / 2 + nrm * off) for sx, off in
                     ((-1, thick), (1, thick), (1, 0.0), (-1, 0.0))])
    for a, b in zip(rows, rows[1:]):
        for i in range(4):
            k = (i + 1) % 4
            bm.faces.new((a[i], a[k], b[k], b[i]))
    bm.faces.new(list(reversed(rows[0])))
    last = rows[-1]
    if tip > 0:
        d = (pts[-1] - pts[-2]).normalized()
        tf = bm.verts.new(pts[-1] + d * tip + normals[-1] * thick)
        tb = bm.verts.new(pts[-1] + d * tip)
        bm.faces.new((last[0], last[1], tf))
        bm.faces.new((last[2], last[3], tb))
        bm.faces.new((last[1], last[2], tb, tf))
        bm.faces.new((last[3], last[0], tf, tb))
    else:
        bm.faces.new(last)
    return _new_mesh(kit, bm, slot, name)


def _catmull(rows, steps=2):
    out = []
    n = len(rows)
    for i in range(n - 1):
        p0, p1, p2, p3 = rows[max(i - 1, 0)], rows[i], rows[i + 1], rows[min(i + 2, n - 1)]
        for k in range(steps):
            t = k / steps
            out.append(tuple(0.5 * (2 * b + (c - a) * t + (2 * a - 5 * b + 4 * c - d) * t * t +
                                    (3 * b - a - 3 * c + d) * t ** 3) for a, b, c, d in zip(p0, p1, p2, p3)))
    out.append(rows[-1])
    return out


def _tube_radius(obj, point, axis, slab=0.012, reach=0.25):
    ds = []
    for v in obj.data.vertices:
        d = v.co - point
        h = d.dot(axis)
        if abs(h) < slab:
            r = (d - axis * h).length
            if r < reach:
                ds.append(r)
    return sum(ds) / len(ds) if ds else 0.09


def _skin(kit, cl, j, bones, slot, name, max_tris=None):
    names = []
    for a, b in bones:
        for n in (a, b):
            if n not in names:
                names.append(n)
    obj = cl.skin_body(kit, {n: j[n] for n in names}, bones, slot, subdiv=2, name=name)
    if max_tris:
        cl.decimate_to(obj, max_tris)
    return obj


# ------------------------------------------------------------------ the posed body
def _rot(p, r=0.0, y=0.0):
    return Euler((math.radians(p), math.radians(r), math.radians(y)), "XYZ").to_matrix()


def _axis_y(z):
    pts = BEND_AXIS
    if z <= pts[0][0]:
        return pts[0][1]
    for (z0, y0), (z1, y1) in zip(pts, pts[1:]):
        if z <= z1:
            return y0 + (y1 - y0) * _smooth(z0, z1, z)
    return pts[-1][1]


class Body:
    """The rest trunk frame bent along the posed spine: map(rest point) -> world point."""
    DZ = 0.005
    Z0, Z1 = -0.6, 2.0

    def __init__(self, P):
        self.P = P
        yaw = P.get("yaw", 0.0)
        pp, pr = P.get("pelvis", (0.0, 0.0))
        self.Ryaw = _rot(0, 0, yaw)
        R0 = self.Ryaw @ _rot(pp, pr, 0)
        root = Vector(P["root"])
        n = int(round((self.Z1 - self.Z0) / self.DZ)) + 1
        i0 = int(round(-self.Z0 / self.DZ))
        Ps, Rs = [None] * n, [None] * n
        Ps[i0], Rs[i0] = root.copy(), R0.copy()
        for i in range(i0 - 1, -1, -1):
            z = self.Z0 + i * self.DZ
            Ps[i] = root + R0 @ Vector((0, _axis_y(z) - _axis_y(0), z))
            Rs[i] = R0.copy()
        for i in range(i0, n - 1):
            z = self.Z0 + i * self.DZ
            p, r, y = self._rates(z + self.DZ / 2)
            half = _rot(p * self.DZ / 2, r * self.DZ / 2, y * self.DZ / 2)
            dy = (_axis_y(z + self.DZ) - _axis_y(z)) / self.DZ
            Ps[i + 1] = Ps[i] + (Rs[i] @ half) @ Vector((0, dy, 1)) * self.DZ
            Rs[i + 1] = Rs[i] @ half @ half
        self.Ps = Ps
        self.Qs = [R.to_quaternion() for R in Rs]

    def _rates(self, z):
        p = r = y = 0.0
        for z0, z1, dp, dr, dyw in self.P["spine"]:
            if z0 <= z < z1:
                k = 1.0 / (z1 - z0)
                p += dp * k
                r += dr * k
                y += dyw * k
        return p, r, y

    def frame(self, z):
        if z >= self.Z1:
            R = self.Qs[-1].to_matrix()
            return self.Ps[-1] + R @ Vector((0, 0, z - self.Z1)), R
        f = (z - self.Z0) / self.DZ
        i = max(0, min(len(self.Ps) - 2, int(math.floor(f))))
        t = max(0.0, min(1.0, f - i))
        return self.Ps[i].lerp(self.Ps[i + 1], t), self.Qs[i].slerp(self.Qs[i + 1], t).to_matrix()

    def map(self, p):
        p = Vector(p)
        P, R = self.frame(p.z)
        return P + R @ Vector((p.x, p.y - _axis_y(p.z), 0.0))

    def follow(self, obj, squash=None):
        """Bend a rest-space part with the trunk (then press it under the ceiling)."""
        _bake(obj)
        for v in obj.data.vertices:
            q = self.map(v.co)
            self.raw_top = max(getattr(self, "raw_top", -9.0), q.z)
            v.co = squash(q) if squash else q
        obj.data.update()
        return obj


def _squasher(body, ceiling, w=0.07, gap=0.042, bulge=0.08):
    """Soft ceiling: points pushed into the tiles are pressed into a flat band just under them,
    and spread sideways a little (the body would be bigger if the room let it)."""
    if ceiling is None:
        return None
    zc = ceiling - gap
    lat = body.Ryaw @ Vector((1, 0, 0))
    root = Vector(body.P["root"])

    def f(q):
        t = q.z - (zc - w)
        if t <= 0:
            return q
        z = zc - w + w * (1 - math.exp(-t / w))
        off = (q - root).dot(lat)
        k = bulge * min(1.0, t / (2 * w))
        return Vector((q.x + lat.x * off * k, q.y + lat.y * off * k, z))
    return f


def _ik(a, target, l1, l2, pole):
    """Two-bone IK: the middle joint for a chain a -> (l1) -> mid -> (l2) -> end, bent toward pole."""
    a, target, pole = Vector(a), Vector(target), Vector(pole)
    d = target - a
    dist = max(abs(l1 - l2) + 1e-3, min(l1 + l2 - 1e-3, d.length))
    u = d.normalized()
    end = a + u * dist
    cos_a = (l1 * l1 + dist * dist - l2 * l2) / (2 * l1 * dist)
    sin_a = math.sqrt(max(0.0, 1 - cos_a * cos_a))
    perp = (pole - u * pole.dot(u)).normalized()
    return a + (u * cos_a + perp * sin_a) * l1, end


def _frame_from(down, palm, mirror):
    """Hand frame: template -Z along the fingers, palm normal -X (left) / +X (right template)."""
    ez = -Vector(down).normalized()
    pn = Vector(palm)
    pn = (pn - ez * pn.dot(ez)).normalized()
    ex = pn if mirror else -pn
    ey = ez.cross(ex)
    return Matrix((ex, ey, ez)).transposed()


# Left hand template (wrist at the origin; base hand x1.75): name -> (offset, radius).
HAND = {
    "handin": ((0.0, 0.010, 0.050), 0.052),
    "wrist": ((0.0, 0.0, 0.0), 0.058),
    "knuckle": ((0.011, -0.032, -0.163), (0.038, 0.082)),
    "fing": ((-0.004, -0.049, -0.254), (0.033, 0.072)),
    "tip": ((-0.025, -0.038, -0.313), (0.025, 0.054)),
    "thumb0": ((-0.007, -0.046, -0.058), 0.030),
    "thumb1": ((-0.021, -0.093, -0.135), 0.027),
    "thumb2": ((-0.035, -0.109, -0.191), 0.021),
}


def _hand_joints(wrist, M, curl, mirror):
    sx = -1 if mirror else 1
    loc = {k: Vector((v[0][0] * sx, v[0][1], v[0][2])) for k, v in HAND.items()}
    if curl:
        rc = Matrix.Rotation(math.radians(curl) * (-1 if mirror else 1), 3, "Y")
        kn = loc["knuckle"]
        f1 = kn + rc @ (loc["fing"] - kn)
        loc["tip"] = f1 + rc @ rc @ (loc["tip"] - loc["fing"])
        loc["fing"] = f1
    return {k: (tuple(Vector(wrist) + M @ p), HAND[k][1]) for k, p in loc.items()}


# ------------------------------------------------------------------ parts
def _trunk_rows():
    """Dense rest rows of the shirt: the Catmull-Rom loft resampled every ROW_STEP, then the square
    shoulder corner and the level top closing in to the collar ring."""
    dense = _catmull(TRUNK, steps=6)
    rows = []
    z = TRUNK[0][0]
    k = 0
    while z < TRUNK[-1][0] - 1e-6:
        while k < len(dense) - 2 and dense[k + 1][0] < z:
            k += 1
        a, b = dense[k], dense[k + 1]
        t = (z - a[0]) / max(b[0] - a[0], 1e-6)
        rows.append(tuple(a[i] + (b[i] - a[i]) * t for i in range(4)))
        z += ROW_STEP
    rows.append(TRUNK[-1])
    z_c, w_c, f_c, b_c = TRUNK[-1]
    yc, hd = (f_c + b_c) / 2, (b_c - f_c) / 2
    for k in range(1, 7):
        th = math.radians(15 * k)
        w = w_c - SHOULDER_R + SHOULDER_R * math.cos(th)
        z = z_c + (SHOULDER_TOP - z_c) * math.sin(th)
        h = hd * (1 - 0.30 * (1 - math.cos(th)))
        rows.append((z, w, yc - h, yc + h))
    w0, z0, f0, b0 = rows[-1][1], rows[-1][0], rows[-1][2], rows[-1][3]
    wt, zt, ft, bt = COLLAR_RING
    for t in (0.3, 0.6, 0.85, 1.0):
        rows.append((z0 + (zt - z0) * t * t, w0 + (wt - w0) * t, f0 + (ft - f0) * t, b0 + (bt - b0) * t))
    return rows


def _trunk(kit, n_around=28):
    rows = _trunk_rows()
    e = 2.0 / SECTION_N
    bm = bmesh.new()
    rings = []
    for z, w, f, b in rows:
        yc, hd = (f + b) / 2, (b - f) / 2
        ring = []
        for i in range(n_around):
            a = 2 * math.pi * i / n_around
            c, s = math.cos(a), math.sin(a)
            ring.append(bm.verts.new((w * math.copysign(abs(c) ** e, c), yc + hd * math.copysign(abs(s) ** e, s), z)))
        rings.append(ring)
    for ra, rb in zip(rings, rings[1:]):
        for i in range(n_around):
            k = (i + 1) % n_around
            bm.faces.new((ra[i], ra[k], rb[k], rb[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    return _new_mesh(kit, bm, PAPER, "shirt")


def _head_parts(kit):
    """The base head, head-local and at the base's scale: toner skull + hair, paper ears, the paper face
    and its print, the drum streak. Returns (parts, face point)."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=34, v_segments=20, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        x *= HEAD_HX
        y *= HEAD_HY_FRONT if y < 0 else HEAD_HY_BACK
        z *= HEAD_HZ_TOP if z > 0 else HEAD_HZ_BOT
        if z < 0:
            k = -z / HEAD_HZ_BOT
            x *= 1 - 0.22 * k ** 2
            if y > 0:
                y *= 1 - 0.40 * k ** 1.5
                z *= 1 - 0.30 * min(1.0, y / HEAD_HY_BACK)
        if y < -HEAD_FRONT:
            y = -HEAD_FRONT
        v.co = (x, y, z)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    cuts = [(HAIR_BAND, Vector((0, 1, 0)))]
    for a, b in HAIRLINE:
        d = Vector(b) - Vector(a)
        cuts.append((Vector(a), Vector((0, -d.z, d.y)).normalized()))
    for co, no in cuts:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=co, plane_no=no)
    head = _new_mesh(kit, bm, TONER, "head")
    head.data.materials.append(kit._material(PAPER))
    for poly in head.data.polygons:
        c = poly.center
        if all((c - co).dot(no) > 0 for co, no in cuts[:1]) and all((c - co).dot(no) < 0 for co, no in cuts[1:]):
            poly.material_index = 1
    parts = {"head": head, "ears": [], "print": []}
    for sx in (1, -1):
        e = kit.soft_box((0.024, 0.046, 0.062), (sx * 0.090, 0.016, -0.016), PAPER, radius=0.0372, segments=12,
                         rings=8, rot=(0, 0, sx * 8.0), name="ear")
        parts["ears"].append(e)
    face = _face_outline()
    paper_y = -HEAD_FRONT - 0.0001
    parts["face"] = kit.extrude(face, 0.0024, (0, paper_y, 0), PAPER, plane="xz", name="face_paper")
    ink_y = -HEAD_FRONT - 0.0018
    fz = FACE_Z
    ink = []
    eye = _ellipse(0.034, fz + 0.022, 0.040, 0.022, n=16, droop=0.004, power=0.85)
    brow = _stroke([(0.015, fz + 0.050), (0.037, fz + 0.046), (0.060, fz + 0.036)], 0.010, 0.6)
    nostril = _ellipse(0.010, fz - 0.032, 0.011, 0.007, n=10)
    for shape in (eye, brow, nostril):
        ink += [shape, _mirror(shape)]
    ink.append(_stroke([(-0.010, fz + 0.016), (-0.012, fz - 0.006), (-0.016, fz - 0.024)], 0.005, 0.6))
    ink.append(_stroke([(-0.026, fz - 0.064), (-0.012, fz - 0.058), (0.0, fz - 0.057), (0.012, fz - 0.058),
                        (0.026, fz - 0.064)], 0.006, 0.5))
    ink.append(_ellipse(0.0, fz - 0.073, 0.022, 0.006, n=10))
    for k, outline in enumerate(ink):
        parts["print"].append(kit.extrude(outline, 0.0010, (0, ink_y, 0), TONER, plane="xz", bevel=0.0003,
                                          name="print_%d" % k))
    v0, v1 = _v_range(face, STREAK_X)
    sw = STREAK_W / 2
    parts["print"].append(kit.extrude([(STREAK_X - sw, v0 + 0.002), (STREAK_X + sw, v0 + 0.002),
                                       (STREAK_X + sw, v1 - 0.002), (STREAK_X - sw, v1 - 0.002)],
                                      0.0010, (0, ink_y, 0), TONER, plane="xz", bevel=0.0003, name="streak_face"))
    return parts, Vector((0, paper_y, FACE_Z))


def _shoe(kit, loc, rot, name):
    s = 1.75

    def shape(p):
        hl = 0.1275 * s
        f = max(0.0, -p.y / hl)
        b = max(0.0, p.y / hl)
        if p.z > 0:
            p.z *= 1 - 0.40 * f ** 1.3
        else:
            p.z += 0.010 * s * max(0.0, f - 0.6) ** 2 / 0.16
        p.x *= (1 - 0.18 * f ** 2.5) * (1 - 0.12 * b ** 2)
        return p
    shoe = kit.soft_box((0.096 * s, 0.255 * s, 0.094 * s), (0, 0, 0), TONER, radius=0.026 * s, segments=20, rings=10,
                        name=name)
    _reshape(shoe, shape)
    shoe.data.transform(Matrix.Translation(Vector(loc)) @ rot.to_4x4())
    shoe.data.update()
    return shoe


def _belt(kit, objs, z, centre_y, n=48):
    """An elliptical band fitted to the measured (rest) waist, rays cast inward."""
    tree = _bvh(objs)
    c = Vector((0.0, centre_y, z))
    rad = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = Vector((math.cos(a), math.sin(a), 0.0))
        r = 0.0
        for dz in (-0.04, -0.02, 0.0, 0.02, 0.04):
            loc, _n, _i, _d = tree.ray_cast(c + d * 1.0 + Vector((0, 0, dz)), -d)
            if loc is not None:
                r = max(r, (loc - c - Vector((0, 0, dz))).length)
        rad.append((r or 0.3) + 0.010)
    rings = []
    for dz, grow in ((-0.042, -0.016), (-0.035, 0.0), (0.035, 0.0), (0.042, -0.016)):
        rings.append([c + Vector((math.cos(2 * math.pi * i / n) * (r + grow), math.sin(2 * math.pi * i / n) * (r + grow), dz))
                      for i, r in enumerate(rad)])
    return _band(kit, rings, TONER, "belt")


def _cuff(kit, end, axis, radius, name):
    """A buttoned shirt cuff round the end of a long sleeve (base cuff x1.75), one toner stitch ring."""
    q = Vector((0, 0, -1)).rotation_difference(axis)
    rot = [math.degrees(a) for a in q.to_euler("XYZ")]
    s = 1.75
    ro = radius + 0.009
    band = kit.lathe([(0.042, 0.0), (ro - 0.005, 0.0), (ro, 0.007), (ro, 0.087), (ro - 0.007, 0.096),
                      (radius - 0.014, 0.101)], tuple(end), PAPER, verts=24, rot=rot, name="cuff_" + name,
                     close_top=False, close_bottom=False)
    seam = kit.lathe([(ro + 0.0004, 0.041 * s), (ro + 0.003, 0.042 * s), (ro + 0.003, 0.046 * s), (ro + 0.0004, 0.047 * s)],
                     tuple(end), TONER, verts=16, rot=rot, name="cuff_seam_" + name, close_top=False, close_bottom=False)
    return _bake(band), _bake(seam)


def _collar(kit, base, axis, lat, r=0.118, h_front=0.060, h_back=0.150, n=28):
    """The shirt collar round the neck base, shoved up at the back by the folded trunk: a band whose
    top edge rises from h_front at the throat to h_back at the nape, flaring a little."""
    axis = Vector(axis).normalized()
    lat = (Vector(lat) - axis * Vector(lat).dot(axis)).normalized()
    fwd = lat.cross(axis)            # toward the throat
    rings = [[], [], [], []]
    for i in range(n):
        a = 2 * math.pi * i / n
        d = lat * math.cos(a) + fwd * math.sin(a)
        back = 0.5 - 0.5 * math.sin(a)        # 0 at the throat, 1 at the nape
        h = h_front + (h_back - h_front) * back ** 1.5
        flare = 1.0 + 0.10 * back
        rings[0].append(base + d * (r - 0.012))
        rings[1].append(base + d * r)
        rings[2].append(base + d * r * flare + axis * h)
        rings[3].append(base + d * (r * flare - 0.014) + axis * (h - 0.006))
    return _band(kit, rings, PAPER, "collar")


def _cut(obj, co, no, toner_index):
    """Crop a part with a plane (keep the side behind no) and cap the cut with toner: the page edge."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no, clear_outer=True)
    edges = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if edges:
        filled = bmesh.ops.holes_fill(bm, edges=edges, sides=0)
        for f in filled["faces"]:
            f.material_index = toner_index
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


# ------------------------------------------------------------------ build
def build(kit, cl, pose="std"):
    P = POSE[pose]
    body = Body(P)
    squash = _squasher(body, P.get("ceiling"))
    fwd = body.Ryaw @ Vector((0, -1, 0))
    lat = body.Ryaw @ Vector((1, 0, 0))

    # --- shirt (paper), built upright as the print, then bent with the body and pressed under the tiles
    shirt = _trunk(kit)
    tree = _bvh([shirt])                       # rest shirt: details are placed on the print, then bent
    rest_parts = []
    # belt (toner) round the hem
    rest_parts.append(_belt(kit, [shirt], 0.205, 0.03))
    # pocket on the left breast, and a pen in it
    pocket = _pocket(kit, tree, 0.158, 0.150, _rz(0.96), _rz(0.69))
    rest_parts.append(pocket)
    pa, pb = _front(tree, 0.130, _rz(0.88)), _front(tree, 0.130, _rz(0.98))
    if pa and pb:
        d = (pb[0] - pa[0]).normalized()
        mid = (pa[0] + pb[0]) / 2 + pa[1] * 0.012 + d * 0.022
        rest_parts.append(_bake(kit.cylinder(0.0095, 0.150, tuple(mid), TONER, verts=10,
                                             rot=(math.degrees(math.atan2(-d.y, d.z)), 0, 0), name="pen")))
    # the drum streak down the shirt front, enlarged with the print (3 cm wide)
    sx = STREAK_X * 1.6
    sh = [_front(tree, sx, _rz(1.40) - 0.03 * i) for i in range(50)]
    sh = [h for h in sh if h and 0.25 <= h[0].z <= _rz(1.40)]
    if len(sh) >= 3:
        rest_parts.append(_strip(kit, [h[0] + h[1] * 0.0012 for h in sh], [0.030] * len(sh), [h[1] for h in sh],
                                 0.0016, TONER, "streak_shirt"))
    # printed tension creases across the back: armpit to armpit, arching over the shoulder blades
    for k, (zc, arch) in enumerate(((0.84, 0.05), (0.93, 0.07), (1.02, 0.08), (1.10, 0.06))):
        pts, nrm = [], []
        for i in range(17):
            x = -0.36 + 0.72 * i / 16
            z = zc + arch * (1 - (abs(x) / 0.36) ** 1.6) + 0.012 * k * (x / 0.36)
            hit = _back(tree, x, _rz(z))
            if hit:
                pts.append(hit[0] + hit[1] * 0.0012)
                nrm.append(hit[1])
        if len(pts) >= 3:
            sides = [Vector((0, 0, 1))] * len(pts)
            rest_parts.append(_strip(kit, pts, [0.016 - 0.003 * abs(k - 1.5)] * len(pts), nrm, 0.0016, TONER,
                                     "crease_%d" % k, side=sides))
    # the tie knot sits at the throat of the print
    kn = _front(tree, 0.0, _rz(1.40))
    knot = None
    if kn:
        knot = kit.soft_box((0.082, 0.054, 0.076), tuple(kn[0] + Vector((0, -0.018, 0))), TONER, radius=0.021,
                            segments=12, rings=8, rot=(-12, 0, 0), name="knot")
        rest_parts.append(_bake(knot))
    tie_rest = None
    if P.get("tie") == "lie":
        hits = [_front(tree, 0.0, _rz(1.37) - 0.035 * i) for i in range(22)]
        hits = [h for h in hits if h and _rz(0.72) <= h[0].z <= _rz(1.37)]
        if len(hits) >= 3:
            top, end = hits[0][0].z, hits[-1][0].z
            widths = [0.066 + (0.140 - 0.066) * (top - h[0].z) / (top - end) for h in hits]
            tie_rest = _strip(kit, [h[0] + Vector((0, 0.003, 0)) for h in hits], widths, [Vector((0, -1, 0))] * len(hits),
                              0.019, TONER, "tie", tip=0.074)
            rest_parts.append(tie_rest)
    body.follow(shirt, squash)
    for obj in rest_parts:
        body.follow(obj, squash)

    # --- the hanging tie: from the knot straight down under gravity, its face to the front
    if P.get("tie") == "hang" and knot is not None:
        kb = Vector(knot.matrix_world.translation)
        top = Vector(sum((v.co for v in knot.data.vertices), Vector())) / len(knot.data.vertices)
        swing = Vector(P.get("tie_swing", (0.0, 0.0)))
        pts = []
        for i in range(12):
            t = i / 11
            pts.append(top + Vector((0, 0, -0.03 - 0.60 * t)) + fwd * (swing.y * t * t) + lat * (swing.x * t * t))
        widths = [0.066 + (0.140 - 0.066) * i / 11 for i in range(12)]
        _strip(kit, pts, widths, [fwd] * 12, 0.019, TONER, "tie", tip=0.074, side=[lat] * 12)

    # --- arms: long sleeves (paper) bunched at the elbow, buttoned cuffs, bare paper hands
    sleeves, cuffs, hands = [], [], []
    for s, sxn in (("l", 1), ("r", -1)):
        A = P["arm_" + s]
        SR = P.get("shoulder", SHOULDER_REST)
        S = body.map((sxn * SR[0], SR[1], SR[2]))
        DEBUG.setdefault("_joints", {})[s] = (tuple(round(c, 2) for c in S), A["wrist"])
        E, W = _ik(S, A["wrist"], UPPER_ARM, FOREARM, A["pole"])
        up, fo = (E - S).normalized(), (W - E).normalized()
        j = {
            "sh": (tuple(S), 0.112), "u1": (tuple(S.lerp(E, 0.45)), 0.104),
            "b1": (tuple(S.lerp(E, 0.80)), 0.112), "b2": (tuple(S.lerp(E, 0.92)), 0.104),
            "el": (tuple(E), 0.106), "b3": (tuple(E.lerp(W, 0.12)), 0.110), "b4": (tuple(E.lerp(W, 0.26)), 0.099),
            "f1": (tuple(E.lerp(W, 0.55)), 0.092), "sl": (tuple(E.lerp(W, 0.86)), 0.084),
        }
        sleeve = _skin(kit, cl, j, [("sh", "u1"), ("u1", "b1"), ("b1", "b2"), ("b2", "el"), ("el", "b3"), ("b3", "b4"),
                                    ("b4", "f1"), ("f1", "sl")], PAPER, "sleeve_" + s, max_tris=900)
        sleeves.append(sleeve)
        sl = E.lerp(W, 0.86)
        r_meas = _tube_radius(sleeve, sl - fo * 0.06, fo)
        band, _seam = _cuff(kit, sl + fo * 0.052, fo, r_meas, s)
        cuffs.append(band)
        M = _frame_from(A["down"], A["palm"], s == "r")
        hj = _hand_joints(W, M, A.get("curl", 0.0), s == "r")
        hj["handin"] = (tuple(E.lerp(W, 0.80)), 0.054)
        hands.append(_skin(kit, cl, hj, [("handin", "wrist"), ("wrist", "knuckle"), ("knuckle", "fing"), ("fing", "tip"),
                                         ("thumb0", "thumb1"), ("thumb1", "thumb2")], PAPER, "hand_" + s, max_tris=900))
        crop = P.get("crop")
        if crop and s == "l":
            # the page ended here: the outer point of the left elbow is cut off flat
            out = (E - S.lerp(W, 0.5))
            out = (out - fo * out.dot(fo)).normalized()
            out = Vector((out.x, out.y, 0.0)).normalized()
            co = E + out * (0.106 - crop)
            sleeve.data.materials.append(kit._material(TONER))
            _cut(sleeve, co, out, 1)

    # --- legs: toner trousers (two chains from behind the belt), soft office shoes
    leg_j = {}
    shoes = []
    for s, sxn in (("l", 1), ("r", -1)):
        L = P["leg_" + s]
        Hj = body.map((sxn * HIP_REST[0], HIP_REST[1], HIP_REST[2]))
        Wj = body.map((sxn * WAIST_REST[0], WAIST_REST[1], WAIST_REST[2]))
        K, A = _ik(Hj, L["ankle"], THIGH, SHIN, L["pole"])
        down = (A - K).normalized()
        leg_j.update({
            "waist_" + s: (tuple(Wj), (0.215, 0.200)), "hip_" + s: (tuple(Hj), 0.212),
            "thigh_" + s: (tuple(Hj.lerp(K, 0.55)), 0.182), "knee_" + s: (tuple(K), 0.148),
            "calf_" + s: (tuple(K.lerp(A, 0.40)), 0.138), "ankle_" + s: (tuple(A), 0.104),
            "cuff_" + s: (tuple(A + down * 0.068), 0.108),
        })
        Rs = _rot(L.get("heel", 0.0), 0, L.get("yaw", 0.0) + P.get("yaw", 0.0))
        shoe_c = A + Rs @ Vector((0, -0.105, -0.137))
        shoes.append(_shoe(kit, shoe_c, Rs, "shoe_" + s))
        sock = A + Rs @ Vector((0, -0.018, -0.120))
        _skin(kit, cl, {"shin": (tuple(K.lerp(A, 0.72)), 0.077), "sock": (tuple(sock), 0.084)}, [("shin", "sock")],
              TONER, "upper_" + s)
    trousers = _skin(kit, cl, leg_j, [("waist_l", "hip_l"), ("hip_l", "thigh_l"), ("thigh_l", "knee_l"), ("knee_l", "calf_l"),
                                      ("calf_l", "ankle_l"), ("ankle_l", "cuff_l"),
                                      ("waist_r", "hip_r"), ("hip_r", "thigh_r"), ("thigh_r", "knee_r"), ("knee_r", "calf_r"),
                                      ("calf_r", "ankle_r"), ("ankle_r", "cuff_r")], TONER, "trousers", max_tris=2400)

    # --- neck (paper) out of the collar, craned down; the head hung on it
    nb = body.map(NECK_REST)
    d1 = body.Ryaw @ _rot(*P["neck"][0]) @ Vector((0, 0, 1))
    d2 = body.Ryaw @ _rot(*P["neck"][1]) @ Vector((0, 0, 1))
    n1 = nb + d1 * NECK_LEN[0]
    n2 = n1 + d2 * NECK_LEN[1]
    neck = _skin(kit, cl, {"nb": (tuple(nb), 0.104), "n1": (tuple(n1), 0.100), "n2": (tuple(n2), 0.092)},
                 [("nb", "n1"), ("n1", "n2")], PAPER, "neck")
    Rh = body.Ryaw @ _rot(*P["head"])
    hc = n2 + Rh @ HEAD_NECK
    Mh = Matrix.Translation(hc) @ Rh.to_4x4() @ Matrix.Scale(HEAD_S, 4)
    hp, face_pt = _head_parts(kit)
    head_objs = [hp["head"], hp["face"]] + hp["ears"] + hp["print"]
    for obj in head_objs:
        _bake(obj)
        obj.data.transform(Mh)
        obj.data.update()

    # --- collar (paper) round the neck base, shoved up at the back
    top_axis = (body.frame(SHOULDER_TOP)[1] @ Vector((0, 0, 1)))
    c_axis = (top_axis + d1).normalized()
    cb = body.map((0.0, (COLLAR_RING[2] + COLLAR_RING[3]) / 2, COLLAR_RING[1] - 0.03))
    collar = _collar(kit, cb, c_axis, lat)

    for obj in kit.parts:
        _bake(obj)
    lo = cl.floor_parts(kit)
    global EYE
    eye = (Mh @ face_pt).z - lo
    EYE = dict(EYE) if isinstance(EYE, dict) else {}
    EYE[pose] = round(eye, 3)
    DEBUG[pose] = {"rawTop": round(body.raw_top - lo, 3), "neckEnd": tuple(round(c, 3) for c in n2),
                   "collar": tuple(round(c, 3) for c in nb)}
    weights = {shirt: 1.0, pocket: 1.0, collar: 0.6, neck: 0.8, hp["head"]: 0.55,
               hp["ears"][0]: 0.55, hp["ears"][1]: 0.55}
    for o in sleeves:
        weights[o] = 1.0
    for o in cuffs:
        weights[o] = 0.8
    for o in hands:
        weights[o] = 0.6
    _toner_edges(kit, weights)
    kit.no_collider()


def _toner_edges(kit, weights):
    """The 'printed' paper: up- and front-facing planes stay paper-white, flanks and undersides go
    toner-grey (a baked darkening toward the silhouette edge, doc 10 §5). Stored as a colour attribute
    'toner' on every part (1 = no change) and multiplied into the Paper slot."""
    for obj in kit.parts:
        me = obj.data
        attr = me.color_attributes.get("toner") or me.color_attributes.new("toner", "FLOAT_COLOR", "POINT")
        w = weights.get(obj, 0.0)
        for i, v in enumerate(me.vertices):
            val = 1.0
            if w:
                n = v.normal
                side = _smooth(0.35, 0.90, abs(n.x))
                down = _smooth(0.15, 0.75, -n.z)
                back = _smooth(0.30, 0.95, n.y)
                val = max(0.34, 1.0 - w * (0.60 * side + 0.42 * down + 0.08 * back))
            attr.data[i].color = (val, val, val, 1.0)
    mat = bpy.data.materials.get(PAPER)
    if mat is None or not mat.use_nodes:
        return
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    base = tuple(bsdf.inputs["Base Color"].default_value)
    at = nodes.new("ShaderNodeAttribute")
    at.attribute_name = "toner"
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs[0].default_value = 1.0
    a_in, b_in = [s for s in mix.inputs if s.type == "RGBA"][:2]
    a_in.default_value = base
    links.new(at.outputs["Color"], b_in)
    links.new([s for s in mix.outputs if s.type == "RGBA"][0], bsdf.inputs["Base Color"])
