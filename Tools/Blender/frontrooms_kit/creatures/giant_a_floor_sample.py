"""Giant A, "Floor Sample" as a squeezed giant (Documentation/research/hunter/11_squeezed_giant.md;
direction A in 10_hunter_directions.md §3). Early concept blockout, not production.

The furniture store's display figure in its padded-yoke power suit, blown up to a
~3.2 m giant that never fits the room: the yoke presses the ceiling tiles, the pale
CRT-faced shell head hangs below it down to the player's eye line, and the clasped
mannequin hands are huge. Four poses from one parameter set each (POSE_PARAMS).

Build (headless, from the Unity project root):
  Blender -b --factory-startup --python Tools/Blender/frontrooms_kit/build_creature.py -- giant_a_floor_sample [--pose std]

Envelope after flooring (2026-10-02 build; 17.4 k tris and 6 slots in every pose):
  low   top 2.355 (yoke 4 cm under the 2.4 m tiles), face 1.46, half-width 0.77
  std   top 2.840 (6 cm under 2.9), face 1.72, half-width 0.68
  door  door-plane top 2.02, |x| 0.42 at the plane, face 1.32, figure top 2.33
  tall  top 3.18, face 2.83, half-width 0.73

Construction
* The costume is the human-scale module's (hunter_a_floor_sample.py, copied, not
  imported): one lofted jacket shell with the padded yoke, lapels, collar band, shirt V,
  buttons, pocket flaps, back seam/vent, badge and lanyard. All of it is still written in
  the base figure's coordinates and passes through one map per pose:
    base space --G--> giant torso space (x, y, s) --T--> world
  G scales the base torso up (length x1.80, depth x1.80, width x1.62, the pads
  compressed so the yoke is 0.95 m across). T bends the torso along a spine curve: roll
  (lateral) and pitch (forward) accumulate along s like a real spine, applied roll-first
  so the shoulder line stays lateral. T also soft-clamps the torso under the ceiling, so
  the yoke and upper back flatten and spread where they press the tiles. Every jacket
  detail follows the body because it goes through the same map.
* Limbs are Skin-modifier chains between joints solved per pose with two-bone IK and
  fixed bone lengths (upper arm 0.66, forearm 0.70 (A's long forearm), thigh 0.72,
  shin 0.68), so the four poses are targets for one rig.
* Rigid parts scale with the body, so they read as a person's things blown up: head
  x1.50 (0.405 m tall), hands x1.70 (0.335 m), oxfords x1.40 (0.46 m), swing tag x1.6.
* The craned neck is sleeved by the navy jacket collar, pushed up it in accordion folds,
  then the white shirt collar, then a short mannequin neck peg with a black seam at
  each end. A bare long neck read as a pipe, or as the Coil-head's spring.
* Strain: the yoke flattens and spreads against the ceiling, folds bunch in the crook
  of each elbow, creases pull across the upper back, and folds fan out from the top
  button.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

NAME = "Giant_A_FloorSample"
TITLE = "Floor Sample (giant)"
PITCH = ("The furniture store's display figure, blown up to three metres and crammed under "
         "the ceiling tiles: its padded yoke flattens on the ceiling, its pale CRT-faced head "
         "hangs down to your eye level, and its huge mannequin hands stay politely clasped.")
SMOOTH_ANGLE = 70.0

POSES = {
    "low": {"top": 2.37, "halfWidth": 0.80},
    "std": {"top": 2.86, "halfWidth": 0.80},
    "door": {"top": 2.9, "door": True},
    "tall": {"top": 3.30, "halfWidth": 0.85},
}
SIL_FRAME = (2.4, 3.6)
EYE = {"low": 1.459, "std": 1.724, "door": 1.32, "tall": 2.831}   # CRT face centre; re-measured in build()

SUIT = "Prop_FabricNavy"
SHELL = "Creature_ShellSatin"
GLASS = "Prop_GlassCRT"
WHITE = "Prop_PlasticWhite"
BLACK = "Prop_PlasticBlack"
TAG = "Prop_Paper"

# base figure -> giant torso space
HIP0 = 0.97           # base hip line (z), the giant torso's s = 0
SV = 1.80             # torso length scale
SD = 1.80             # torso depth scale
SW = 1.62             # torso width scale (below the pads)
HEAD_K = 1.50         # head 0.27 -> 0.405 m
HAND_K = 1.70         # hand ~0.20 -> 0.335 m
SHOE_K = 1.40         # oxford 0.33 -> 0.46 m
TAG_K = 1.60

UPPER_ARM, FOREARM = 0.66, 0.70
THIGH, SHIN = 0.72, 0.68


# ------------------------------------------------------------------ helpers (from the base module)
def _pchip(xs, ys):
    """Monotone cubic (Fritsch-Carlson) through (xs, ys): smooth, no overshoot."""
    n = len(xs)
    h = [xs[i + 1] - xs[i] for i in range(n - 1)]
    d = [(ys[i + 1] - ys[i]) / h[i] for i in range(n - 1)]
    m = [0.0] * n
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, n - 1):
        if d[i - 1] * d[i] <= 0:
            m[i] = 0.0
        else:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])

    def f(x):
        if x <= xs[0]:
            return ys[0]
        if x >= xs[-1]:
            return ys[-1]
        i = 0
        while xs[i + 1] < x:
            i += 1
        t = (x - xs[i]) / h[i]
        t2, t3 = t * t, t * t * t
        return ((2 * t3 - 3 * t2 + 1) * ys[i] + (t3 - 2 * t2 + t) * h[i] * m[i]
                + (-2 * t3 + 3 * t2) * ys[i + 1] + (t3 - t2) * h[i] * m[i + 1])
    return f


def _se(a, e):
    """Unit superellipse point at parameter angle a; |x|^e + |y|^e = 1."""
    c, s = math.cos(a), math.sin(a)
    p = 2.0 / e
    return math.copysign(abs(c) ** p, c), math.copysign(abs(s) ** p, s)


def _smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _ring_mesh(kit, rings, slot, name, cap0=True, cap1=True):
    """Closed tube through rings of equal length; fan caps at both ends."""
    bm = bmesh.new()
    vr = [[bm.verts.new(Vector(p)) for p in ring] for ring in rings]
    n = len(rings[0])
    for a, b in zip(vr, vr[1:]):
        for j in range(n):
            k = (j + 1) % n
            bm.faces.new((a[j], a[k], b[k], b[j]))
    for ring, cap in ((vr[0], cap0), (vr[-1], cap1)):
        if not cap:
            continue
        c = sum((v.co for v in ring), Vector()) / n
        cv = bm.verts.new(c)
        for j in range(n):
            bm.faces.new((ring[j], ring[(j + 1) % n], cv))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _perp(d):
    d = d.normalized()
    ref = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    u = d.cross(ref).normalized()
    return u, d.cross(u).normalized()


def _loft(kit, stations, slot, name, n=20, steps=3):
    """stations: [(centre, U, V, a, b, e)] - section = centre + U*a*x + V*b*y over a
    superellipse. Centres, sizes and exponents are interpolated (monotone cubic)."""
    k = len(stations)
    ts = list(range(k))
    comps = []
    for idx in range(3):
        comps.append(_pchip(ts, [s[0][idx] for s in stations]))
    fa = _pchip(ts, [s[3] for s in stations])
    fb = _pchip(ts, [s[4] for s in stations])
    fe = _pchip(ts, [s[5] for s in stations])
    rings = []
    total = (k - 1) * steps
    for i in range(total + 1):
        t = i / steps
        j = min(int(t), k - 2)
        w = t - j
        U = stations[j][1].lerp(stations[j + 1][1], w).normalized()
        V = stations[j][2].lerp(stations[j + 1][2], w).normalized()
        c = Vector([comps[q](t) for q in range(3)])
        a, b, e = fa(t), fb(t), fe(t)
        ring = []
        for s in range(n):
            x, y = _se(2 * math.pi * s / n, e)
            ring.append(c + U * (a * x) + V * (b * y))
        rings.append(ring)
    return _ring_mesh(kit, rings, slot, name)


def _loop_tube(kit, centre, U, V, ra, rb, r, slot, name, n=14):
    """A thin closed ring (seam lines, bezels) round an ellipse in the U-V plane."""
    pts = [centre + U * (ra * math.cos(2 * math.pi * i / n)) + V * (rb * math.sin(2 * math.pi * i / n))
           for i in range(n)]
    pts += pts[:2]
    return kit.tube(pts, r, slot, verts=6, name=name, caps=False)


def _ik(root, target, a, b, pole):
    """Two-bone IK: the middle joint for bones a, b from root toward target, bent toward
    the pole direction. Returns (mid, reached_target, clamped)."""
    root, target, pole = Vector(root), Vector(target), Vector(pole)
    d = target - root
    L = d.length
    u = d.normalized()
    L2 = min(max(L, abs(a - b) + 1e-3), a + b - 1e-3)
    clamped = abs(L2 - L) > 1e-4
    target = root + u * L2
    x = (a * a - b * b + L2 * L2) / (2 * L2)
    h = math.sqrt(max(0.0, a * a - x * x))
    v = pole - u * pole.dot(u)
    v.normalize()
    return root + u * x + v * h, target, clamped


# ------------------------------------------------------------------ the jacket shell (base space)
_TORSO_SIDE = [  # z, front y, back y, half-width x, superellipse exponent
    (0.855, -0.080, 0.178, 0.170, 2.4),
    (0.870, -0.092, 0.192, 0.188, 2.4),
    (0.950, -0.094, 0.186, 0.186, 2.4),
    (1.040, -0.097, 0.160, 0.176, 2.3),
    (1.150, -0.106, 0.125, 0.163, 2.3),     # waist
    (1.280, -0.142, 0.130, 0.168, 2.4),
    (1.420, -0.178, 0.144, 0.168, 2.5),     # chest swell / shoulder-blade hunch
    (1.520, -0.186, 0.146, 0.184, 2.6),
    (1.620, -0.170, 0.132, 0.214, 2.9),     # recess under the head
    (1.700, -0.178, 0.108, 0.275, 3.4),
    (1.745, -0.198, 0.092, 0.392, 4.4),     # underside of the pads (quick flare)
    (1.790, -0.205, 0.078, 0.420, 5.0),     # yoke: squared pads
    (1.850, -0.207, 0.066, 0.421, 5.0),
    (1.880, -0.200, 0.055, 0.414, 4.6),
    (1.900, -0.185, 0.036, 0.396, 4.0),     # crowned top
    (1.912, -0.155, 0.006, 0.350, 3.4),
    (1.917, -0.120, -0.020, 0.280, 3.0),
]
TORSO = [(z, (f + bk) / 2, hx, (bk - f) / 2, e) for z, f, bk, hx, e in _TORSO_SIDE]


class _Shell:
    def __init__(self, stations):
        zs = [s[0] for s in stations]
        self.zs = zs
        self.f = [_pchip(zs, [s[k] for s in stations]) for k in range(1, 5)]

    def section(self, z):
        return tuple(f(z) for f in self.f)

    def front_y(self, x, z, back=False):
        yc, hx, hy, e = self.section(z)
        q = max(0.0, 1.0 - min(1.0, abs(x / hx)) ** e)
        return yc + (1 if back else -1) * hy * q ** (1.0 / e)


SLEEVE_Y = -0.080     # base y of the sleeve heads under the pad tips


def gx(x):
    """Base width -> giant width: x1.55 up to the chest, the pads compressed so the
    0.84 m base yoke becomes 0.95 m."""
    t = abs(x)
    v = SW * t if t <= 0.19 else SW * 0.19 + 0.72 * (t - 0.19)
    return math.copysign(v, x)


def G(p):
    return Vector((gx(p[0]), p[1] * SD, (p[2] - HIP0) * SV))


# ------------------------------------------------------------------ the posed body
def _rx(a):
    return Matrix.Rotation(math.radians(a), 3, "X")


def _ry(a):
    return Matrix.Rotation(math.radians(a), 3, "Y")


def _rz(a):
    return Matrix.Rotation(math.radians(a), 3, "Z")


class Body:
    """One pose of the giant. Torso space (x, y, s): x to the figure's left, y back,
    s up the spine from the hip line. Pitch (+ = forward, about X), roll (+ = top toward
    the figure's left, about Y) and twist (about Z) accumulate along s as smoothstep
    bends [(s0, s1, degrees)]."""

    def __init__(self, P):
        self.P = P
        self.yaw = P.get("yaw", 0.0)
        self.Ryaw = _rz(self.yaw)
        self.root = Vector((P.get("root", (0, 0))[0], P.get("root", (0, 0))[1], 0.0))
        self.ceiling = P.get("ceiling")
        self.squash = P.get("squash", 0.07)
        self.bulge = P.get("bulge", 1.2)
        self.pel = self.B(P["pelvis"])
        self.ds = 0.005
        self.Cs = [self.pel.copy()]
        z = Vector((0, 0, 1))
        s = 0.0
        prev = self.F(0.0) @ z
        while s < 2.0:
            s += self.ds
            cur = self.F(s) @ z
            self.Cs.append(self.Cs[-1] + (prev + cur) * (0.5 * self.ds))
            prev = cur

    def B(self, p):
        """Body frame (x left, y back, z up; yawed and rooted) -> world."""
        return self.Ryaw @ Vector(p) + self.root

    def Bd(self, d):
        return self.Ryaw @ Vector(d)

    def _ang(self, key, s):
        base, bends = self.P.get(key, (0.0, []))
        return base + sum(a * _smooth(s0, s1, s) for s0, s1, a in bends)

    def F(self, s):
        s = max(0.0, s)
        tw = sum(a * _smooth(s0, s1, s) for s0, s1, a in self.P.get("twist", []))
        return self.Ryaw @ _rz(tw) @ _ry(self._ang("roll", s)) @ _rx(self._ang("pitch", s))

    def C(self, s):
        if s <= 0.0:
            return self.pel + (self.F(0.0) @ Vector((0, 0, 1))) * s
        f = s / self.ds
        i = min(int(f), len(self.Cs) - 2)
        w = f - i
        return self.Cs[i].lerp(self.Cs[i + 1], w)

    def clamp(self, p):
        """Soft ceiling: anything that would rise above it is squashed into a thin band
        just under it, so the padding flattens against the tiles."""
        if self.ceiling is None:
            return p
        w = self.squash
        d = p.z - (self.ceiling - w)
        if d > 0:
            z = self.ceiling - w + w * math.tanh(d / w)
            # the squashed padding spreads sideways (about the body's own centre line)
            spread = 1.0 + self.bulge * (p.z - z)
            c = self.pel
            p = Vector((c.x + (p.x - c.x) * spread, c.y + (p.y - c.y) * (1.0 + 0.3 * self.bulge * (p.z - z)), z))
        return p

    def T(self, p):
        x, y, s = p
        return self.clamp(self.C(s) + self.F(s) @ Vector((x, y, 0.0)))

    def TB(self, pb):
        return self.T(G(pb))


# ------------------------------------------------------------------ jacket + costume (base space)
def _jacket(kit, shell, body, n=30):
    zs = set(round(z, 4) for z in shell.zs)
    z = 0.855
    while z < 1.70:
        zs.add(round(z, 4))
        z += 0.030
    while z < 1.89:
        zs.add(round(z, 4))
        z += 0.015
    for z in (1.897, 1.902, 1.906, 1.910, 1.912):
        zs.add(z)
    rings = []
    for z in sorted(zs):
        yc, hx, hy, e = shell.section(z)
        ring = []
        for s in range(n):
            x, y = _se(2 * math.pi * s / n, e)
            px, py = hx * x, yc + hy * y
            k = 1.0 - 0.26 * _smooth(0.22, 0.42, abs(px)) * _smooth(1.64, 1.75, z)
            py = SLEEVE_Y + (py - SLEEVE_Y) * k
            ring.append(body.TB((px, py, z)))
        rings.append(ring)
    return _ring_mesh(kit, rings, SUIT, "jacket shell")


def _panel(kit, shell, body, corners, lift, slot, name, nu=8, nv=10, sink=0.004, back=False):
    """A thin panel hugging the jacket front (base-space corners (x, z): bottom-left,
    bottom-right, top-right, top-left seen from the front), mapped onto the posed body."""
    (x00, z00), (x10, z10), (x11, z11), (x01, z01) = corners
    bm = bmesh.new()
    outer, inner = [], []
    for j in range(nv + 1):
        v = j / nv
        ro, ri = [], []
        for i in range(nu + 1):
            u = i / nu
            x = (1 - u) * (1 - v) * x00 + u * (1 - v) * x10 + u * v * x11 + (1 - u) * v * x01
            z = (1 - u) * (1 - v) * z00 + u * (1 - v) * z10 + u * v * z11 + (1 - u) * v * z01
            y = shell.front_y(x, z, back)
            sg = 1 if back else -1
            ro.append(bm.verts.new(body.TB((x, y + sg * lift, z))))
            ri.append(bm.verts.new(body.TB((x, y - sg * sink, z))))
        outer.append(ro)
        inner.append(ri)
    for j in range(nv):
        for i in range(nu):
            bm.faces.new((outer[j][i], outer[j][i + 1], outer[j + 1][i + 1], outer[j + 1][i]))
            bm.faces.new((inner[j][i], inner[j + 1][i], inner[j + 1][i + 1], inner[j][i + 1]))
    rim = ([(0, i) for i in range(nu)] + [(j, nu) for j in range(nv)]
           + [(nv, i) for i in range(nu, 0, -1)] + [(j, 0) for j in range(nv, 0, -1)])
    for k in range(len(rim)):
        (j0, i0), (j1, i1) = rim[k], rim[(k + 1) % len(rim)]
        bm.faces.new((outer[j0][i0], inner[j0][i0], inner[j1][i1], outer[j1][i1]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _surface_normal(shell, x, z, back=False):
    dx = (shell.front_y(x + 0.002, z, back) - shell.front_y(x - 0.002, z, back)) / 0.004
    dz = (shell.front_y(x, z + 0.002, back) - shell.front_y(x, z - 0.002, back)) / 0.004
    return Vector((-dx, 1.0, -dz)).normalized() if back else Vector((dx, -1.0, dz)).normalized()


def _button(kit, shell, body, x, z, name):
    """A coat button built in base space on the jacket front, mapped with the body."""
    p = Vector((x, shell.front_y(x, z), z))
    nrm = _surface_normal(shell, x, z)
    rot = nrm.to_track_quat("Z", "Y").to_matrix()
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=10, radius1=0.014, radius2=0.012, depth=0.008)
    for v in bm.verts:
        v.co = body.TB(p + nrm * 0.004 + rot @ v.co)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, BLACK, "metres", "xz")


def _ridge(kit, body, pts_base, r, name, slot=SUIT):
    """A strain crease: a thin tube through base-space surface points, mapped."""
    return kit.tube([body.TB(p) for p in pts_base], r, slot, verts=6, name=name)


def _fold_arcs(kit, a, b, c, inward, rads, ts, name, tube=0.016, arc=200.0):
    """Bunched-sleeve folds: crescent ridges round the limb a-b-c near joint b, centred
    on the inside of the bend (inward). ts: positions along the limb (-1..0 on a-b,
    0..1 on b-c); rads: limb radius at each."""
    out = []
    for t, r in zip(ts, rads):
        if t < 0:
            p, ax = b + (b - a) * t, (b - a).normalized()
        else:
            p, ax = b + (c - b) * t, (c - b).normalized()
        n = (inward - ax * inward.dot(ax)).normalized()
        m = ax.cross(n)
        pts = []
        for i in range(9):
            ang = math.radians(-arc / 2 + arc * i / 8)
            pts.append(p + (n * math.cos(ang) + m * math.sin(ang)) * r)
        out.append(kit.tube(pts, tube, SUIT, verts=6, name=name))
    return out


# ------------------------------------------------------------------ head (base head space, scaled by M)
HEAD_W, HEAD_D, HEAD_H, HEAD_EGG = 0.20, 0.23, 0.27, 0.10


def _egg_scale(zl):
    t = max(-1.0, min(1.0, zl / (HEAD_H / 2)))
    return math.sqrt(max(0.0, 1 - t * t)) * (1 + HEAD_EGG * t)


def _egg_front(xl, zl):
    s = _egg_scale(zl)
    a, b = HEAD_W / 2 * s, HEAD_D / 2 * s
    if a < 1e-6:
        return 0.0
    return -b * math.sqrt(max(0.0, 1 - (xl / a) ** 2))


def _inside_egg(pl):
    s = _egg_scale(pl.z)
    if abs(pl.z) >= HEAD_H / 2 or s < 1e-6:
        return False
    return (pl.x / (HEAD_W / 2 * s)) ** 2 + (pl.y / (HEAD_D / 2 * s)) ** 2 < 1.0


def _head(kit, M):
    """Egg shell + CRT-glass face, built in (base) head space and moved/scaled by M."""
    segs, rings = 28, 18
    bm = bmesh.new()
    top = bm.verts.new(M @ Vector((0, 0, HEAD_H / 2)))
    bot = bm.verts.new(M @ Vector((0, 0, -HEAD_H / 2)))
    vr = []
    for i in range(1, rings):
        zl = -math.cos(math.pi * i / rings) * HEAD_H / 2
        s = _egg_scale(zl)
        ring = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            ring.append(bm.verts.new(M @ Vector((HEAD_W / 2 * s * math.cos(a), HEAD_D / 2 * s * math.sin(a), zl))))
        vr.append(ring)
    for a, b in zip(vr, vr[1:]):
        for j in range(segs):
            k = (j + 1) % segs
            bm.faces.new((a[j], a[k], b[k], b[j]))
    for j in range(segs):
        k = (j + 1) % segs
        bm.faces.new((vr[0][k], vr[0][j], bot))
        bm.faces.new((vr[-1][j], vr[-1][k], top))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    kit._new_object("head shell", bm, SHELL, "metres", "xz")

    ga, gb, gz, ge = 0.060, 0.075, -0.012, 3.2
    bm = bmesh.new()
    nr, na = 6, 32
    centre = bm.verts.new(M @ Vector((0, _egg_front(0, gz) - 0.0057, gz)))
    grid = []
    for r in range(1, nr + 1):
        rho = r / nr
        ring = []
        for k in range(na):
            cx, cz = _se(2 * math.pi * k / na, ge)
            xl, zl = ga * rho * cx, gz + gb * rho * cz
            lift = 0.0012 + 0.0045 * (1 - rho * rho)
            ring.append(bm.verts.new(M @ Vector((xl, _egg_front(xl, zl) - lift, zl))))
        grid.append(ring)
    for k in range(na):
        bm.faces.new((centre, grid[0][(k + 1) % na], grid[0][k]))
    for a, b in zip(grid, grid[1:]):
        for k in range(na):
            kk = (k + 1) % na
            bm.faces.new((a[k], a[kk], b[kk], b[k]))
    fwd = (M.to_3x3() @ Vector((0, -1, 0))).normalized()
    for f in bm.faces:
        f.normal_update()
        if f.normal.dot(fwd) < 0:
            f.normal_flip()
    kit._new_object("face glass", bm, GLASS, "decal", "xz")
    return M @ Vector((0, _egg_front(0, gz), gz))


# ------------------------------------------------------------------ hands
def _mitten(kit, wrist, tip, palm_toward, side, name, k=HAND_K):
    """Display-figure hand (fingers together, no nails), scaled by k; side +1 right
    hand, -1 left. Returns (L, N, W) so the wrist seam can be placed."""
    L = (tip - wrist).normalized()
    N = (palm_toward - L * palm_toward.dot(L)).normalized()
    W = L.cross(N) * side
    st = [
        (-0.050, 0.024, 0.020, 0.0),
        (0.000, 0.027, 0.019, 0.0),
        (0.035, 0.037, 0.018, 0.0),
        (0.095, 0.042, 0.015, 0.0),
        (0.135, 0.040, 0.0135, 0.006),
        (0.168, 0.035, 0.012, 0.016),
        (0.188, 0.026, 0.010, 0.026),
        (0.197, 0.011, 0.006, 0.032),
    ]
    stations = [(wrist + (L * d + N * c) * k, W, N, a * k, b * k, 2.6) for d, a, b, c in st]
    _loft(kit, stations, SHELL, name, n=14, steps=2)
    base = wrist + (L * 0.035 + W * 0.025 + N * 0.008) * k
    tdir = (L * 0.92 + W * 0.10 + N * 0.30).normalized()
    u, v = _perp(tdir)
    th = [(base, u, v, 0.015 * k, 0.014 * k, 2.0), (base + tdir * 0.035 * k, u, v, 0.014 * k, 0.012 * k, 2.0),
          (base + tdir * 0.060 * k, u, v, 0.011 * k, 0.0095 * k, 2.0),
          (base + tdir * 0.070 * k, u, v, 0.005 * k, 0.005 * k, 2.0)]
    _loft(kit, th, SHELL, name + " thumb", n=10, steps=2)
    return L, N, W


# ------------------------------------------------------------------ shoes
SHOE = [  # distance from heel back, z centre, half-width, half-height, exponent (base metres)
    (0.000, 0.058, 0.030, 0.040, 2.2),
    (0.012, 0.060, 0.045, 0.054, 2.4),
    (0.050, 0.064, 0.053, 0.062, 2.6),
    (0.110, 0.062, 0.058, 0.060, 2.6),
    (0.170, 0.052, 0.062, 0.052, 2.6),
    (0.230, 0.040, 0.063, 0.040, 2.6),
    (0.280, 0.033, 0.058, 0.032, 2.5),
    (0.312, 0.030, 0.046, 0.026, 2.3),
    (0.330, 0.029, 0.022, 0.016, 2.2),
]


def _prism(kit, outline, z0, z1, M, slot, name, bevel=0.004):
    bm = bmesh.new()
    lo = [bm.verts.new(M @ Vector((u, v, z0))) for u, v in outline]
    hi = [bm.verts.new(M @ Vector((u, v, z1))) for u, v in outline]
    bm.faces.new(lo)
    bm.faces.new(list(reversed(hi)))
    n = len(outline)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = kit._new_object(name, bm, slot, "metres", "xz")
    kit._bevel(ob, bevel, 1, angle=35)
    return ob


def _shoe(kit, heel, yaw, pitch, name, k=SHOE_K):
    """Oversized black oxford scaled by k. heel: world (x, y) of the heel back; yaw in
    world degrees (toe toward -Y at 0); pitch > 0 lifts the heel on the toe tip."""
    L = SHOE[-1][0]
    toe = Vector((0, -L, 0))
    M = (Matrix.Translation(Vector((heel[0], heel[1], 0.0))) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
         @ Matrix.Scale(k, 4) @ Matrix.Translation(toe) @ Matrix.Rotation(math.radians(pitch), 4, "X")
         @ Matrix.Translation(-toe))
    X, Z = Vector((1, 0, 0)), Vector((0, 0, 1))
    Mr = M.to_3x3()
    stations = [(M @ Vector((0, -d, cz)), (Mr @ X).normalized(), (Mr @ Z).normalized(), a * k, b * k, e)
                for d, cz, a, b, e in SHOE]
    _loft(kit, stations, BLACK, name + " upper", n=16, steps=2)
    half = [(d, a + 0.006) for d, cz, a, b, e in SHOE[1:-1]]
    outline = [(w, -d) for d, w in half] + [(0.0, -(L + 0.004))] + [(-w, -d) for d, w in reversed(half)] + [(0.0, 0.004)]
    _prism(kit, outline, 0.0, 0.020, M, BLACK, name + " sole", bevel=0.005 * k)
    heelp = [(0.040, -0.004), (0.045, -0.04), (0.042, -0.085), (-0.042, -0.085), (-0.045, -0.04), (-0.040, -0.004)]
    _prism(kit, heelp, 0.0, 0.034, M, BLACK, name + " heel", bevel=0.004 * k)
    return M @ Vector((0, -0.075, 0.115))


def _report(kit):
    groups = {}
    for o in kit.parts:
        deps = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
        tris = sum(len(p.vertices) - 2 for p in deps.data.polygons)
        key = o.name.split(" ")[0]
        groups[key] = groups.get(key, 0) + tris
    print("[giantA] tris by part: " + ", ".join("%s %d" % kv for kv in sorted(groups.items(), key=lambda kv: -kv[1])))


# ------------------------------------------------------------------ pose parameters
# One parameter set per pose drives the whole body; the costume follows it.
# Body frame: x = the figure's left, y = back (it faces -y), z = height; yaw/root place it.
# pelvis: body-frame point of the torso's hip line (s = 0).
# pitch/roll/twist: (base deg, [(s0, s1, deg), ...]) accumulating along the spine.
# ceiling/squash/bulge: soft clamp height for the torso, the band it squashes into, and
#   how much the squashed padding spreads sideways (None = free).
# neck_z: base-space height of the neck root under the yoke; neck: offsets from it to
#   the Bezier control point (mid) and the head centre (body frame, or world if world=True).
# head: (pitch, roll, yaw) degrees, yaw relative to the body; attach: neck entry in head space.
# arms: wrist target, elbow pole direction, hand tip target, palm-toward (body frame, or
#   world if world=True).
# legs: heel (x, y), shoe yaw (relative), heel-lift pitch, knee pole (body frame or world).
POSE_PARAMS = {
    "std": dict(
        yaw=0.0, root=(0.0, 0.0),
        pelvis=(0.0, 0.30, 1.36),
        pitch=(-2.0, [(0.6, 1.2, 22.0), (1.05, 1.6, 40.0)]),
        ceiling=2.84, squash=0.06, bulge=1.5,
        neck_z=1.68,
        neck=dict(mid=(0.0, -0.22, -0.12), head=(0.0, -0.30, -0.68)),
        head=(20.0, -6.0, 0.0), attach=(0.0, 0.10, 0.03),
        arms={
            "l": dict(wrist=(0.16, -0.60, 1.55), pole=(1.0, 0.25, 0.5), tip=(-0.05, -0.69, 1.40), palm=(0, 1, 0)),
            "r": dict(wrist=(-0.15, -0.57, 1.57), pole=(-1.0, 0.25, 0.5), tip=(0.05, -0.66, 1.42), palm=(0, 1, 0)),
        },
        legs={
            "l": dict(heel=(0.40, -0.02), yaw=14.0, pitch=0.0, pole=(0.7, -1.0, 0.0)),
            "r": dict(heel=(-0.40, 0.50), yaw=-14.0, pitch=14.0, pole=(-0.7, -1.0, 0.0)),
        },
    ),
}
POSE_PARAMS["low"] = dict(
    # Under the 2.4 m Low ceiling: deepest fold, a wide sumo squat, the back and yoke
    # flattened on the tiles, the head hung between the splayed elbows, face tipped up.
    yaw=0.0, root=(0.0, 0.0),
    pelvis=(0.0, 0.36, 0.90),
    pitch=(4.0, [(0.3, 1.0, 20.0), (0.95, 1.6, 40.0)]),
    ceiling=2.36, squash=0.06, bulge=1.5,
    neck_z=1.68,
    neck=dict(mid=(0.0, -0.22, -0.10), head=(0.0, -0.30, -0.46)),
    head=(2.0, 5.0, 0.0), attach=(0.0, 0.10, 0.03),
    arms={
        "l": dict(wrist=(0.15, -0.72, 0.98), pole=(1.0, 0.2, 0.3), tip=(-0.06, -0.80, 0.83), palm=(0, 1, 0)),
        "r": dict(wrist=(-0.14, -0.69, 1.00), pole=(-1.0, 0.2, 0.3), tip=(0.06, -0.77, 0.85), palm=(0, 1, 0)),
    },
    legs={
        "l": dict(heel=(0.46, 0.02), yaw=24.0, pitch=0.0, pole=(0.9, -1.0, 0.7)),
        "r": dict(heel=(-0.46, 0.10), yaw=-24.0, pitch=6.0, pole=(-0.9, -1.0, 0.7)),
    },
)
POSE_PARAMS["door"] = dict(
    # Sideways through the 1.0 x 2.1 m door (plane y = 0), deep squat, the trunk laid over
    # toward the room it is entering, the yoke tilted to pass leading (left) shoulder first.
    yaw=-76.0, root=(0.11, 0.86),
    pelvis=(0.0, 0.0, 0.73),
    pitch=(6.6, [(0.1, 1.1, 9.9)]),
    roll=(26.6, [(0.0, 0.9, 39.9), (0.95, 1.6, -44.5)]),
    ceiling=2.86, squash=0.06, bulge=1.0,
    neck_z=1.68,
    neck=dict(world=True, mid=(-0.10, -0.20, -0.02), head=(-0.16, -0.36, -0.08)),
    head=(15.0, 20.0, 50.0), attach=(0.0, 0.10, 0.03),
    arms={
        "l": dict(world=True, wrist=(-0.60, -0.24, 1.36), pole=(0.3, -0.8, -0.5), tip=(-0.72, -0.24, 1.66), palm=(0, 1, 0)),
        # trailing hand braced flat on the wall above the header, behind the door
        "r": dict(world=True, wrist=(-0.08, 0.26, 2.02), pole=(0.2, 1.0, 0.4), tip=(0.06, 0.26, 2.30), palm=(0, -1, 0)),
    },
    legs={
        "l": dict(world=True, heel=(0.06, 0.40), yaw=-46.0, pitch=0.0, pole=(-0.6, -0.8, 0.3)),
        "r": dict(world=True, heel=(0.36, 0.75), yaw=-26.0, pitch=16.0, pole=(-0.9, 0.3, 0.3)),
    },
)
POSE_PARAMS["tall"] = dict(
    # The reveal in a 5.4 m Tall zone: nearly upright, a slight stoop, the head lifted out
    # from under the yoke but still below its line, hands clasped at the belt.
    yaw=0.0, root=(0.0, 0.0),
    pelvis=(0.0, 0.05, 1.50),
    pitch=(2.0, [(0.6, 1.3, 7.0), (1.1, 1.6, 8.0)]),
    ceiling=None,
    neck_z=1.70,
    neck=dict(mid=(0.0, -0.20, 0.04), head=(0.0, -0.42, 0.14)),
    head=(18.0, -6.0, 0.0), attach=(0.0, 0.05, -0.05),
    arms={
        "l": dict(wrist=(0.19, -0.44, 1.86), pole=(1.0, 0.4, 0.1), tip=(-0.05, -0.52, 1.72), palm=(0, 1, 0)),
        "r": dict(wrist=(-0.18, -0.41, 1.88), pole=(-1.0, 0.4, 0.1), tip=(0.05, -0.49, 1.74), palm=(0, 1, 0)),
    },
    legs={
        "l": dict(heel=(0.24, -0.08), yaw=8.0, pitch=0.0, pole=(0.3, -1.0, 0.0)),
        "r": dict(heel=(-0.26, 0.30), yaw=-8.0, pitch=10.0, pole=(-0.3, -1.0, 0.0)),
    },
)


# ------------------------------------------------------------------ build
def build(kit, cl, pose="std"):
    P = POSE_PARAMS[pose]
    body = Body(P)
    shell = _Shell(TORSO)
    _jacket(kit, shell, body)
    B, Bd = body.B, body.Bd
    dbg = {}

    # --- arms: shoulder (inside the yoke) - elbow - sleeve end, bunched at the elbow -----
    hands = {}
    for s, sx in (("l", 1), ("r", -1)):
        A = P["arms"][s]
        Wp = (lambda q: Vector(q)) if A.get("world") else B
        Wd = (lambda q: Vector(q)) if A.get("world") else Bd
        sh = body.TB((0.343 * sx, SLEEVE_Y, 1.83))
        el, wr, clamped = _ik(sh, Wp(A["wrist"]), UPPER_ARM, FOREARM, Wd(A["pole"]))
        if clamped:
            print("[giantA] WARNING %s: %s wrist out of reach" % (pose, s))
        dbg["shoulder_" + s], dbg["elbow_" + s], dbg["wrist_" + s] = sh, el, wr
        ua, fa = el - sh, wr - el
        j = {"shoulder": (sh, (0.150, 0.125))}
        bones, prev = [], "shoulder"
        # sleeve bunching: ripples above and below the elbow
        for nm, t, r in (("u1", 0.55, (0.128, 0.120)), ("u2", 0.74, (0.132, 0.126)),
                         ("u3", 0.84, (0.118, 0.112)), ("u4", 0.93, (0.128, 0.124))):
            j[nm] = (sh + ua * t, r)
            bones.append((prev, nm))
            prev = nm
        j["elbow"] = (el, (0.112, 0.118))
        bones.append((prev, "elbow"))
        prev = "elbow"
        for nm, t, r in (("f1", 0.10, (0.118, 0.114)), ("f2", 0.20, (0.106, 0.104)), ("f3", 0.30, (0.112, 0.108))):
            j[nm] = (el + fa * t, r)
            bones.append((prev, nm))
            prev = nm
        j["sleeve"] = (el + fa * 0.78, 0.098)
        bones.append((prev, "sleeve"))
        joints = {k + "_" + s: (tuple(v[0]), v[1]) for k, v in j.items()}
        bones = [(a + "_" + s, b + "_" + s) for a, b in bones]
        cl.decimate_to(cl.skin_body(kit, joints, bones, SUIT, subdiv=2, name="sleeve " + s), 850)
        # folds bunched into the crook of the elbow
        crook = ((sh + wr) * 0.5 - el)
        _fold_arcs(kit, sh, el, wr, crook, (0.122, 0.118, 0.112, 0.112, 0.106), (-0.22, -0.13, -0.05, 0.06, 0.15),
                   "sleeve fold")
        cj = {"cuffa_" + s: (tuple(el.lerp(wr, 0.74)), 0.080), "cuffb_" + s: (tuple(el.lerp(wr, 0.92)), 0.075)}
        cl.decimate_to(cl.skin_body(kit, cj, [("cuffa_" + s, "cuffb_" + s)], WHITE, subdiv=2, name="cuff " + s), 260)
        side = 1 if s == "r" else -1
        L, N, W = _mitten(kit, wr, Wp(A["tip"]), Wd(A["palm"]), side, "hand " + s)
        _loop_tube(kit, wr + L * (-0.006), W, N, 0.0272 * HAND_K, 0.0192 * HAND_K, 0.0042, BLACK, "wrist seam " + s)
        hands[s] = (wr, L, N, W)

    # --- trousers: one chain per leg from inside the jacket --------------------------
    for s, sx in (("l", 1), ("r", -1)):
        Lg = P["legs"][s]
        heel = Vector((Lg["heel"][0], Lg["heel"][1], 0.0)) if Lg.get("world") else B((Lg["heel"][0], Lg["heel"][1], 0.0))
        ankle = _shoe(kit, (heel.x, heel.y), body.yaw + Lg["yaw"], Lg["pitch"], "shoe " + s)
        hip = body.T((0.19 * sx, 0.06, 0.0))
        seat = body.T((0.14 * sx, 0.08, 0.17))
        hem = ankle + Vector((0, 0, -0.01)) + Bd((0, 0.012, 0))
        kn, hem2, clamped = _ik(hip, hem, THIGH, SHIN, Vector(Lg["pole"]) if Lg.get("world") else Bd(Lg["pole"]))
        if clamped:
            print("[giantA] WARNING %s: %s leg out of reach (%.3f)" % (pose, s, (hem - hip).length))
        dbg["hip_" + s], dbg["knee_" + s], dbg["ankle_" + s] = hip, kn, hem
        th, sn = kn - hip, hem2 - kn
        j = {"seat_" + s: (tuple(seat), 0.175), "hip_" + s: (tuple(hip), 0.190),
             "thigh_" + s: (tuple(hip + th * 0.55), 0.172),
             "knee_" + s: (tuple(kn), 0.140), "kb_" + s: (tuple(kn + sn * 0.14), 0.150),
             "hem_" + s: (tuple(hem2), 0.130)}
        bones = [("seat_" + s, "hip_" + s), ("hip_" + s, "thigh_" + s), ("thigh_" + s, "knee_" + s),
                 ("knee_" + s, "kb_" + s), ("kb_" + s, "hem_" + s)]
        cl.decimate_to(cl.skin_body(kit, j, bones, SUIT, subdiv=2, name="trouser " + s), 900)

    # --- head: hung forward and down under the yoke on a craned neck ----------------
    nz = P.get("neck_z", 1.72)
    N0 = body.TB((0.0, -0.13, nz))
    NP = P["neck"]
    Nd = (lambda q: Vector(q)) if NP.get("world") else Bd
    HC = N0 + Nd(NP["head"])
    hp, hr, hy = P["head"]
    R = (body.Ryaw @ _rz(hy) @ _rx(hp) @ _ry(hr)).to_4x4()
    M = Matrix.Translation(HC) @ R @ Matrix.Scale(HEAD_K, 4)
    face = _head(kit, M)
    neck_end = M @ Vector(P["attach"])
    ctrl = N0 + Nd(NP["mid"]) if NP.get("mid") is not None else N0.lerp(neck_end, 0.5)

    def npath(t):
        return N0 * (1 - t) ** 2 + ctrl * (2 * t * (1 - t)) + neck_end * (t * t)

    def ntan(t):
        return ((ctrl - N0) * (2 * (1 - t)) + (neck_end - ctrl) * (2 * t)).normalized()

    nj, nb = {}, []
    for i, t in enumerate((0.0, 0.3, 0.6, 0.85, 1.0)):
        nj["neck%d" % i] = (tuple(npath(t)), 0.112 - 0.022 * t)
        if i:
            nb.append(("neck%d" % (i - 1), "neck%d" % i))
    cl.decimate_to(cl.skin_body(kit, nj, nb, SHELL, subdiv=2, name="neck"), 420)
    Minv = M.inverted()
    t_head = 1.0
    while t_head > 0.3 and _inside_egg(Minv @ npath(t_head)):
        t_head -= 0.005
    ax = ntan(t_head)
    u, v = _perp(ax)
    _loop_tube(kit, npath(t_head) - ax * 0.006, u, v, 0.094, 0.094, 0.0042, BLACK, "neck seam")

    def frames(t0, t1, n):
        out = []
        u, v = _perp(ntan(t0))
        for i in range(n + 1):
            t = t0 + (t1 - t0) * i / n
            tn = ntan(t)
            u = (u - tn * u.dot(tn)).normalized()
            out.append((npath(t), u, tn.cross(u), t))
        return out

    # The collars ride up the craned neck: the navy jacket collar outside, the white
    # shirt collar a little further, then a short seamed neck peg into the head.
    t_jk = NP.get("jacket", 0.62) * t_head
    t_sh = NP.get("shirt", 0.80) * t_head
    st = [(p, u, v, 0.176 - 0.040 * (t / t_jk), 0.168 - 0.036 * (t / t_jk), 2.0) for p, u, v, t in frames(0.0, t_jk, 5)]
    _loft(kit, st, SUIT, "collar ride", n=16, steps=2)
    st = [(p, u, v, 0.138 - 0.014 * (t - t_jk + 0.05) / (t_sh - t_jk + 0.05), 0.134 - 0.014 * (t - t_jk + 0.05) / (t_sh - t_jk + 0.05), 2.0)
          for p, u, v, t in frames(max(0.0, t_jk - 0.05), t_sh, 3)]
    _loft(kit, st, WHITE, "collar", n=16, steps=2)
    ax = ntan(t_sh + 0.02)
    u, v = _perp(ax)
    _loop_tube(kit, npath(t_sh + 0.02), u, v, 0.104, 0.104, 0.0042, BLACK, "neck seam")
    # accordion folds where the jacket collar is shoved up the neck (inside of the crane)
    bend = (N0 - ctrl * 2 + neck_end)
    for f, arc in ((0.38, 230.0), (0.58, 260.0), (0.80, 300.0)):
        t = f * t_jk
        tn = ntan(t)
        inward = bend - tn * bend.dot(tn)
        if inward.length < 1e-4:
            inward = _perp(tn)[0]
        r = 0.176 - 0.040 * f
        _fold_arcs(kit, npath(t) - tn, npath(t), npath(t) + tn, inward, (r - 0.002,), (0.0,), "collar fold",
                   tube=0.017, arc=arc)
    dbg["neck_base"], dbg["head"], dbg["face"] = N0, HC, face
    dbg["yoke_front"] = body.TB((0.0, -0.207, 1.85))
    dbg["yoke_tip_l"] = body.TB((0.42, -0.08, 1.85))
    dbg["hump"] = body.TB((0.0, 0.146, 1.52))

    # --- jacket front: shirt V, peaked lapels, buttons, pocket flaps ------------------
    _panel(kit, shell, body, [(-0.004, 1.352), (0.004, 1.352), (0.075, 1.705), (-0.075, 1.705)], 0.004, WHITE,
           "shirt front")

    def mirrored(q, sx):
        if sx > 0:
            return q
        m = [(-x, z) for x, z in q]
        return [m[1], m[0], m[3], m[2]]

    for sx in (1, -1):
        tg = "l" if sx > 0 else "r"
        _panel(kit, shell, body, mirrored([(0.0, 1.322), (0.016, 1.322), (0.212, 1.700), (0.080, 1.748)], sx), 0.012,
               SUIT, "lapel " + tg, nu=4, nv=8)
        _panel(kit, shell, body, mirrored([(-0.012, 1.792), (0.190, 1.726), (0.205, 1.906), (-0.012, 1.909)], sx),
               0.012 if sx > 0 else 0.0125, SUIT, "collar piece " + tg, nu=5, nv=5)
        for z in (1.285, 1.185):
            _button(kit, shell, body, 0.068 * sx, z, "button")
        flap = [(0.068 * sx, 0.955), (0.162 * sx, 0.958), (0.160 * sx, 1.003), (0.066 * sx, 1.000)]
        if sx < 0:
            flap = [flap[1], flap[0], flap[3], flap[2]]
        _panel(kit, shell, body, flap, 0.009, SUIT, "pocket flap", nu=6, nv=3)
        # strain: folds fanning out from the top button toward the chest and the side
        for (x1, z1) in ((0.150, 1.400), (0.165, 1.230)):
            pts = []
            for kk in range(7):
                tt = kk / 6
                x = (0.085 + (x1 - 0.085) * tt) * sx
                z = 1.285 + (z1 - 1.285) * tt + 0.012 * math.sin(math.pi * tt)
                pts.append((x, shell.front_y(x, z) + 0.0005, z))
            _ridge(kit, body, pts, 0.0105, "strain fold")

    _panel(kit, shell, body, [(-0.002, 1.322), (0.010, 1.322), (-0.062, 1.236), (-0.074, 1.236)], 0.007, SUIT,
           "front edge", nu=2, nv=4)
    _panel(kit, shell, body, [(-0.074, 0.866), (-0.062, 0.866), (-0.062, 1.236), (-0.074, 1.236)], 0.007, SUIT,
           "front edge", nu=2, nv=8)
    _panel(kit, shell, body, [(0.006, 1.10), (-0.006, 1.10), (-0.006, 1.86), (0.006, 1.86)], 0.004, SUIT, "back seam",
           nu=1, nv=14, back=True)
    _panel(kit, shell, body, [(0.040, 0.862), (-0.004, 0.862), (-0.004, 1.105), (0.040, 1.105)], 0.007, SUIT,
           "back vent", nu=3, nv=4, back=True)
    # strain: creases pulled across the back between the shoulder blades
    for zc, half, sag in ((1.47, 0.150, 0.030), (1.56, 0.165, 0.028), (1.65, 0.190, 0.022), (1.38, 0.120, 0.025)):
        pts = []
        for kk in range(9):
            tt = kk / 8
            x = -half + 2 * half * tt
            z = zc - sag * math.sin(math.pi * tt)
            pts.append((x, shell.front_y(x, z, back=True) - 0.0005, z))
        _ridge(kit, body, pts, 0.012, "back crease")

    # --- blank badge on the left breast, on a dark lanyard strap --------------------
    _panel(kit, shell, body, [(0.078, 1.375), (0.133, 1.375), (0.133, 1.460), (0.078, 1.460)], 0.016, WHITE, "badge",
           nu=4, nv=4)
    strap = []
    for kk in range(9):
        tt = kk / 8
        x = 0.045 + (0.105 - 0.045) * tt
        z = 1.735 + (1.462 - 1.735) * tt
        strap.append(body.TB((x, shell.front_y(x, z) - 0.016, z)))
    kit.tube(strap, 0.0072, BLACK, verts=8, name="lanyard")

    # --- swing tag on the left wrist (hangs plumb) ---------------------------------
    wl, Ll, Nl, Wl = hands["l"]
    k = TAG_K
    tag_top = wl + Ll * 0.03 + Vector((0, 0, -0.17))
    kit.tube([wl + Ll * 0.01 - Nl * 0.03, (wl + tag_top) / 2 + Bd((0.004, -0.008, 0)), tag_top],
             0.0035, BLACK, verts=6, name="tag string")
    outline = [(-0.035, 0.0), (0.035, 0.0), (0.035, 0.092), (0.020, 0.110), (-0.020, 0.110), (-0.035, 0.092)]
    Mt = (Matrix.Translation(tag_top + Vector((0, 0, -0.112 * k))) @ Matrix.Rotation(math.radians(body.yaw + 9), 4, "Z")
          @ Matrix.Rotation(math.radians(-4), 4, "Y") @ Matrix.Rotation(math.radians(90), 4, "X") @ Matrix.Scale(k, 4))
    _prism(kit, outline, -0.002, 0.002, Mt, TAG, "swing tag", bevel=0.0015)
    for kk, (w_, z_) in enumerate(((0.040, 0.070), (0.030, 0.055), (0.044, 0.040))):
        bar = [(-w_ / 2, z_), (w_ / 2, z_), (w_ / 2, z_ + 0.007), (-w_ / 2, z_ + 0.007)]
        _prism(kit, bar, 0.0018, 0.0032, Mt, BLACK, "tag print %d" % kk, bevel=0.0)
    _prism(kit, [(-0.006, 0.092), (0.006, 0.092), (0.006, 0.100), (-0.006, 0.100)], -0.0030, 0.0030, Mt, BLACK,
           "tag eyelet", bevel=0.0)

    _report(kit)
    print("[giantA] %s joints: " % pose + "; ".join("%s (%.2f, %.2f, %.2f)" % (kk, dbg[kk].x, dbg[kk].y, dbg[kk].z)
                                                 for kk in sorted(dbg)))
    lo = cl.floor_parts(kit)
    EYE[pose] = round(face.z - lo, 3)
    bpy.context.view_layer.update()
    allv = [(o.matrix_world @ v.co) for o in kit.parts for v in o.data.vertices]
    top = max(v.z for v in allv)
    print("[giantA] %s floored by %.3f; face centre %.3f; top %.3f; |x| %.3f; y %.3f..%.3f; parts %d" % (
        pose, lo, EYE[pose], top, max(abs(v.x) for v in allv), min(v.y for v in allv), max(v.y for v in allv),
        len(kit.parts)))
    kit.no_collider()
