"""Hunter direction A, "Floor Sample" (Documentation/research/hunter/10_hunter_directions.md
§3 and the blockout spec §7.2). Early concept blockout, not production.

The furniture store's display figure in a faded late-1980s power suit, built in
its Hunt render pose (the "showroom walk"): mid-stride, left foot forward, right
heel lifted, hands clasped low in front with the elbows held out, the pale egg
head hung forward and down under a level padded yoke, a CRT-glass oval where the
face should be.

Build (headless, from the Unity project root):
  Blender -b --factory-startup --python Tools/Blender/frontrooms_kit/build_creature.py -- hunter_a_floor_sample

Construction: the limbs, neck and cuffs are Skin-modifier chains with the
spec's joint names (cl.skin_body); the jacket body is one lofted shell of
superellipse sections (narrow waist flaring into the 0.84 m yoke); the head,
hands and shoes are lofted/ovoid rigid parts; lapels, collar band, shirt front,
front edge, pocket flaps, back seam/vent and badge are thin panels that hug the
jacket surface. Envelope (after flooring): top 1.925 (yoke, left end 1 cm high),
face centre 1.58, half-width 0.42, crown 1.77, forward reach above 1 m 0.38.

Deviations from §7.2, and why:
* Jacket torso + yoke are one lofted shell instead of a skin chain plus a
  separate soft_box yoke. The spec's check build read as a bolster floating on
  a tube; one shell makes the yoke the jacket's own squared shoulder line. The
  pad tips taper front-to-back toward the sleeve heads (bow-tie plan) and the
  sleeve roots start inside the yoke band, so the outline drops straight from
  the yoke corner down the arm with no notch.
* Side profile is cut cloth, not a plank: seat skirt, waist tuck, chest swell,
  a recess under the head, a shoulder-blade hunch, a crowned yoke top.
* Peaked lapels plus a collar band run up the yoke's face to the shoulder line,
  so the navy wall above the head reads as jacket, not cushion.
* Hip joints ±0.095 with radius 0.093 (spec ±0.11, r 0.12): hips 0.37 m wide
  instead of 0.46, so the waist-to-yoke taper reads as a power suit, not a pear.
* Elbows at ±0.36 with oval sleeves (spec ±0.32) and a 0.34 m chest: the arm
  loops stay open at 12 m while the elbows stay inside the yoke width.
* Head 0.02 m further forward than the spec (centre y -0.258) and the upper
  chest recessed, so the head hangs clear instead of sinking into the chest;
  the 6 deg tilt is a true roll (about Y), not a yaw.
* CRT glass is a rounded-rectangle tube face (squircle), not an oval with a
  rim: an oval with a bezel read as a camera lens.
* Hands are mitten-shaped mannequin hands (fingers together, tucked thumb)
  crossed left over right, instead of skin sausages.
* Black seam lines at the neck and both wrists make the countable tell.
"""

import math

import bmesh
import bpy
from mathutils import Matrix, Vector

NAME = "Hunter_A_FloorSample"
TITLE = "Floor Sample"
PITCH = ("The furniture store's display figure in a faded 1980s power suit, head hung "
         "below its padded shoulders, walks the stockrooms in plain sight; when it relays, "
         "the store has set it up again somewhere else.")
EYE = 1.581           # CRT-glass face centre after flooring (re-measured in build(), see log)
SMOOTH_ANGLE = 70.0

SUIT = "Prop_FabricNavy"
SHELL = "Creature_ShellSatin"
GLASS = "Prop_GlassCRT"
WHITE = "Prop_PlasticWhite"
BLACK = "Prop_PlasticBlack"
TAG = "Prop_Paper"

YOKE_ROLL = 1.5       # degrees: the yoke's left end ~1 cm high (spec)


# ------------------------------------------------------------------ helpers
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


def _loop_tube(kit, centre, U, V, ra, rb, r, slot, name, n=16):
    """A thin closed ring (seam lines, bezels) round an ellipse in the U-V plane."""
    pts = [centre + U * (ra * math.cos(2 * math.pi * i / n)) + V * (rb * math.sin(2 * math.pi * i / n))
           for i in range(n)]
    pts += pts[:2]
    return kit.tube(pts, r, slot, verts=6, name=name, caps=False)


# ------------------------------------------------------------------ the jacket shell
# Side profile as front / back lines (y) so the jacket reads as cut cloth, not a plank:
# skirt over the seat, waist tuck, chest swell, a recess under the hung head, a
# shoulder-blade hunch, and the yoke rolled forward over the head like an eave.
_TORSO_SIDE = [  # z, front y, back y, half-width x, superellipse exponent
    (0.855, -0.080, 0.178, 0.170, 2.4),
    (0.870, -0.092, 0.192, 0.188, 2.4),
    (0.950, -0.094, 0.186, 0.186, 2.4),
    (1.040, -0.097, 0.160, 0.176, 2.3),
    (1.150, -0.106, 0.125, 0.163, 2.3),     # waist 0.33 m, small of the back
    (1.280, -0.142, 0.130, 0.168, 2.4),
    (1.420, -0.178, 0.144, 0.168, 2.5),     # chest swell / shoulder-blade hunch
    (1.520, -0.186, 0.146, 0.184, 2.6),
    (1.620, -0.170, 0.132, 0.214, 2.9),     # recess: the head hangs clear of the chest
    (1.700, -0.178, 0.108, 0.275, 3.4),
    (1.745, -0.198, 0.092, 0.392, 4.4),     # underside of the pads (quick flare)
    (1.790, -0.205, 0.078, 0.420, 5.0),     # yoke: squared pads, 0.84 m
    (1.850, -0.207, 0.066, 0.421, 5.0),
    (1.880, -0.200, 0.055, 0.414, 4.6),
    (1.900, -0.185, 0.036, 0.396, 4.0),     # crowned top (side view), level (front)
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


SLEEVE_Y = -0.080     # y of the sleeve heads under the pad tips


def _smooth(a, b, x):
    t = min(1.0, max(0.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _roll(p):
    """Yoke roll: lift the left (+X) shoulder, fading in above the chest."""
    z = p[2]
    w = min(1.0, max(0.0, (z - 1.55) / 0.2))
    w = w * w * (3 - 2 * w)
    return Vector((p[0], p[1], z + p[0] * math.tan(math.radians(YOKE_ROLL)) * w))


def _jacket(kit, shell, n=36):
    zs = set(round(z, 4) for z in shell.zs)
    z = 0.855
    while z < 1.70:
        zs.add(round(z, 4))
        z += 0.035
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
            # Shoulders taper front-to-back toward the sleeve heads (a bow-tie plan,
            # not a slab): full depth at the neck, ~0.7 of it at the pad tips.
            k = 1.0 - 0.26 * _smooth(0.22, 0.42, abs(px)) * _smooth(1.64, 1.75, z)
            py = SLEEVE_Y + (py - SLEEVE_Y) * k
            ring.append(_roll((px, py, z)))
        rings.append(ring)
    return _ring_mesh(kit, rings, SUIT, "jacket shell")


def _panel(kit, shell, corners, lift, slot, name, nu=8, nv=10, sink=0.004, back=False):
    """A thin panel hugging the jacket front. corners: (x, z) bottom-left,
    bottom-right, top-right, top-left as seen from the front; lift = how far it
    stands proud of the cloth (its inner face sinks `sink` into the shell)."""
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
            ro.append(bm.verts.new(_roll((x, y + sg * lift, z))))
            ri.append(bm.verts.new(_roll((x, y - sg * sink, z))))
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


def _surface_frame(shell, x, z):
    """Point on the jacket front and its outward normal."""
    p = Vector((x, shell.front_y(x, z), z))
    dx = (shell.front_y(x + 0.002, z) - shell.front_y(x - 0.002, z)) / 0.004
    dz = (shell.front_y(x, z + 0.002) - shell.front_y(x, z - 0.002)) / 0.004
    nrm = Vector((dx, -1.0, dz)).normalized()
    return _roll(p), nrm


def _button(kit, shell, x, z, name):
    p, nrm = _surface_frame(shell, x, z)
    ob = kit.cylinder(0.014, 0.008, (0, 0, 0), BLACK, verts=10, bevel=0.0, name=name)
    rot = nrm.to_track_quat("Z", "Y").to_matrix().to_4x4()
    ob.matrix_world = Matrix.Translation(p + nrm * 0.004) @ rot
    return ob


# ------------------------------------------------------------------ head
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
    """Egg shell + CRT-glass oval + bezel, built in head space and moved by M."""
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

    # CRT glass: 0.12 x 0.15 m, a rounded-rectangle tube face (squircle, not a lens
    # oval), convex, its rim flush with the shell and its centre ~6 mm proud.
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
def _mitten(kit, wrist, tip, palm_toward, side, name):
    """Display-figure hand: fingers together, no nails; side +1 right hand, -1 left.
    Returns (L, N, W) so the wrist seam can be placed."""
    L = (tip - wrist).normalized()
    N = (palm_toward - L * palm_toward.dot(L)).normalized()   # palm normal
    W = L.cross(N) * side                                     # toward the thumb
    st = [  # distance along L, half-width, half-thickness, curl toward the palm
        (-0.050, 0.024, 0.020, 0.0),
        (0.000, 0.027, 0.019, 0.0),
        (0.035, 0.037, 0.018, 0.0),
        (0.095, 0.042, 0.015, 0.0),
        (0.135, 0.040, 0.0135, 0.006),
        (0.168, 0.035, 0.012, 0.016),
        (0.188, 0.026, 0.010, 0.026),
        (0.197, 0.011, 0.006, 0.032),
    ]
    stations = [(wrist + L * d + N * c, W, N, a, b, 2.6) for d, a, b, c in st]
    _loft(kit, stations, SHELL, name, n=14, steps=2)
    # Thumb, laid along the index finger, tucked toward the palm.
    base = wrist + L * 0.035 + W * 0.025 + N * 0.008
    tdir = (L * 0.92 + W * 0.10 + N * 0.30).normalized()
    u, v = _perp(tdir)
    th = [(base, u, v, 0.015, 0.014, 2.0), (base + tdir * 0.035, u, v, 0.014, 0.012, 2.0),
          (base + tdir * 0.060, u, v, 0.011, 0.0095, 2.0), (base + tdir * 0.070, u, v, 0.005, 0.005, 2.0)]
    _loft(kit, th, SHELL, name + " thumb", n=10, steps=2)
    return L, N, W


# ------------------------------------------------------------------ shoes
SHOE = [  # distance from heel back, z centre, half-width, half-height, exponent
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


def _shoe(kit, heel_x, heel_y, yaw, pitch, name):
    """Oversized black oxford (0.33 m). Local: heel back at the origin, toe toward -Y.
    pitch > 0 lifts the heel, pivoting on the toe tip."""
    L = SHOE[-1][0]
    R = Matrix.Rotation(math.radians(yaw), 4, "Z") @ Matrix.Rotation(math.radians(pitch), 4, "X")
    # Pivot on the toe tip so it stays on the floor while the heel rises.
    toe = Vector((0, -L, 0))
    M = Matrix.Translation(Vector((heel_x, heel_y, 0)) + toe) @ R @ Matrix.Translation(-toe)
    X, Y, Z = Vector((1, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1))
    Mr = M.to_3x3()
    stations = [(M @ Vector((0, -d, cz)), Mr @ X, Mr @ Z, a, b, e) for d, cz, a, b, e in SHOE]
    _loft(kit, stations, BLACK, name + " upper", n=16, steps=2)
    half = [(d, a + 0.006) for d, cz, a, b, e in SHOE[1:-1]]
    outline = [(w, -d) for d, w in half] + [(0.0, -(L + 0.004))] + [(-w, -d) for d, w in reversed(half)] + [(0.0, 0.004)]
    _prism(kit, outline, 0.0, 0.020, M, BLACK, name + " sole", bevel=0.005)
    heel = [(0.040, -0.004), (0.045, -0.04), (0.042, -0.085), (-0.042, -0.085), (-0.045, -0.04), (-0.040, -0.004)]
    _prism(kit, heel, 0.0, 0.034, M, BLACK, name + " heel", bevel=0.004)
    return M @ Vector((0, -0.075, 0.115))     # the ankle opening, where the trouser hem lands


def _report(kit):
    """Triangles per part group (after modifiers), for the 15 k budget."""
    groups = {}
    for o in kit.parts:
        deps = o.evaluated_get(bpy.context.evaluated_depsgraph_get())
        tris = sum(len(p.vertices) - 2 for p in deps.data.polygons)
        key = o.name.split(" ")[0]
        groups[key] = groups.get(key, 0) + tris
    print("[hunterA] tris by part: " + ", ".join("%s %d" % kv for kv in sorted(groups.items(), key=lambda kv: -kv[1])))


# ------------------------------------------------------------------ build
def build(kit, cl):
    global EYE
    shell = _Shell(TORSO)
    _jacket(kit, shell)

    # --- joints (spec names; metres, before flooring) --------------------------
    lerp = lambda a, b, t: tuple(a[i] + (b[i] - a[i]) * t for i in range(3))
    J = {
        "shoulder_l": _roll((0.343, SLEEVE_Y, 1.885))[:], "shoulder_r": _roll((-0.343, SLEEVE_Y, 1.885))[:],
        "elbow_l": (0.360, -0.140, 1.395), "elbow_r": (-0.356, -0.130, 1.390),
        "wrist_l": (0.130, -0.300, 1.150), "wrist_r": (-0.125, -0.275, 1.165),
    }
    J = {k: tuple(v) for k, v in J.items()}
    for s in ("l", "r"):
        e, w = J["elbow_" + s], J["wrist_" + s]
        J["sleeve_" + s] = lerp(e, w, 0.78)
        J["cuffa_" + s] = lerp(e, w, 0.74)
        J["cuffb_" + s] = lerp(e, w, 0.92)

    # --- sleeves: shoulder (inside the yoke) - elbow - sleeve end -----------------
    for s in ("l", "r"):
        j = {"shoulder_" + s: (J["shoulder_" + s], (0.088, 0.070)), "elbow_" + s: (J["elbow_" + s], (0.058, 0.066)),
             "sleeve_" + s: (J["sleeve_" + s], 0.057)}
        ob = cl.skin_body(kit, j, [("shoulder_" + s, "elbow_" + s), ("elbow_" + s, "sleeve_" + s)], SUIT, subdiv=2,
                          name="sleeve " + s)
        cl.decimate_to(ob, 650)
        j = {"cuffa_" + s: (J["cuffa_" + s], 0.049), "cuffb_" + s: (J["cuffb_" + s], 0.046)}
        cl.decimate_to(cl.skin_body(kit, j, [("cuffa_" + s, "cuffb_" + s)], WHITE, subdiv=2, name="cuff " + s), 220)

    # --- hands: crossed low in front, left over right --------------------------
    back = Vector((0, 1, 0))
    hands = {}
    hands["r"] = (Vector(J["wrist_r"]), Vector((0.035, -0.285, 1.035)))
    hands["l"] = (Vector(J["wrist_l"]), Vector((-0.030, -0.326, 1.025)))
    for s, side in (("r", 1), ("l", -1)):
        w, tip = hands[s]
        L, N, W = _mitten(kit, w, tip, back, side, "hand " + s)
        # wrist seam: the hand is a separate fitted part
        _loop_tube(kit, w + L * (-0.004), W, N, 0.0272, 0.0192, 0.0019, BLACK, "wrist seam " + s)
        hands[s] = (w, tip, L, N, W)

    # --- trousers: one chain per leg, starting inside the jacket ---------------
    heel_l = (0.110, -0.072)
    heel_r = (-0.118, 0.335)
    ankle_l = _shoe(kit, heel_l[0], heel_l[1], 4.0, 0.0, "shoe l")
    ankle_r = _shoe(kit, heel_r[0], heel_r[1], -4.0, 4.0, "shoe r")
    legs = {
        "l": {"seat_l": ((0.075, 0.035, 1.07), 0.080), "hip_l": ((0.095, 0.030, 0.970), 0.093),
              "knee_l": ((0.105, -0.090, 0.535), 0.075), "hem_l": (tuple(ankle_l + Vector((0, 0.010, -0.010))), 0.077)},
        "r": {"seat_r": ((-0.075, 0.050, 1.07), 0.080), "hip_r": ((-0.095, 0.060, 0.970), 0.093),
              "knee_r": ((-0.105, 0.120, 0.550), 0.075), "hem_r": (tuple(ankle_r + Vector((0, 0.010, -0.010))), 0.077)},
    }
    for s in ("l", "r"):
        j = legs[s]
        ob = cl.skin_body(kit, j, [("seat_" + s, "hip_" + s), ("hip_" + s, "knee_" + s), ("knee_" + s, "hem_" + s)],
                          SUIT, subdiv=2, name="trouser " + s)
        cl.decimate_to(ob, 760)

    # --- head: hung forward and down under the yoke's front edge ---------------
    C = Vector((0.005, -0.258, 1.634))
    R = (Matrix.Rotation(math.radians(-6.0), 4, "Y") @ Matrix.Rotation(math.radians(22.0), 4, "X"))
    M = Matrix.Translation(C) @ R
    face = _head(kit, M)

    # neck: from inside the chest, 45 deg forward and down into the head's underside
    neck_base = Vector((0.0, -0.150, 1.738))
    neck_end = M @ Vector((0, 0.030, -0.060))
    ob = cl.skin_body(kit, {"neck_base": (tuple(neck_base), 0.056), "neck": (tuple(neck_end), 0.050)},
                      [("neck_base", "neck")], SHELL, subdiv=2, name="neck")
    cl.decimate_to(ob, 320)
    axis = (neck_end - neck_base).normalized()
    # neck seam where the neck leaves the head
    Minv = M.inverted()
    t = 0.0
    p = neck_end
    while t < 0.2:
        p = neck_end - axis * t
        if not _inside_egg(Minv @ p):
            break
        t += 0.002
    u, v = _perp(axis)
    _loop_tube(kit, p - axis * 0.004, u, v, 0.0480, 0.0480, 0.0022, BLACK, "neck seam")
    # white shirt collar where the neck leaves the jacket
    t = 0.0
    while t < 0.2:
        q = neck_base + axis * t
        if q.y < shell.front_y(q.x, q.z):
            break
        t += 0.002
    cc = neck_base + axis * t
    col = []
    for off, r in ((-0.040, 0.078), (-0.010, 0.080), (0.022, 0.076), (0.030, 0.068)):
        col.append((cc + axis * off, u, v, r, r, 2.0))
    _loft(kit, col, WHITE, "collar", n=24, steps=2)

    # --- jacket front: shirt V, peaked lapels, buttons, pocket flaps -----------
    _panel(kit, shell, [(-0.004, 1.352), (0.004, 1.352), (0.075, 1.705), (-0.075, 1.705)], 0.004, WHITE, "shirt front")
    def mirrored(q, sx):
        """Quad (x, z) given for the figure's left; mirrored keeps the winding."""
        if sx > 0:
            return q
        m = [(-x, z) for x, z in q]
        return [m[1], m[0], m[3], m[2]]

    for sx in (1, -1):
        tag = "l" if sx > 0 else "r"
        # peaked lapel: V point at the top button, peak at the gorge
        _panel(kit, shell, mirrored([(0.0, 1.322), (0.016, 1.322), (0.212, 1.700), (0.080, 1.748)], sx), 0.012, SUIT,
               "lapel " + tag, nu=4, nv=8)
        # jacket collar above the gorge notch, one band rolling over the shoulder line,
        # dipping at the centre where the neck leaves the jacket
        _panel(kit, shell, mirrored([(-0.012, 1.792), (0.190, 1.726), (0.205, 1.906), (-0.012, 1.909)], sx),
               0.012 if sx > 0 else 0.0125, SUIT, "collar piece " + tag, nu=5, nv=5)
        for z in (1.285, 1.185):
            _button(kit, shell, 0.068 * sx, z, "button")
        flap = [(0.068 * sx, 0.955), (0.162 * sx, 0.958), (0.160 * sx, 1.003), (0.066 * sx, 1.000)]
        if sx < 0:
            flap = [flap[1], flap[0], flap[3], flap[2]]
        _panel(kit, shell, flap, 0.009, SUIT, "pocket flap", nu=6, nv=3)

    # double-breasted front edge (left over right), back seam and vent
    _panel(kit, shell, [(-0.002, 1.322), (0.010, 1.322), (-0.062, 1.236), (-0.074, 1.236)], 0.007, SUIT, "front edge",
           nu=2, nv=4)
    _panel(kit, shell, [(-0.074, 0.866), (-0.062, 0.866), (-0.062, 1.236), (-0.074, 1.236)], 0.007, SUIT, "front edge",
           nu=2, nv=8)
    _panel(kit, shell, [(0.006, 1.10), (-0.006, 1.10), (-0.006, 1.86), (0.006, 1.86)], 0.004, SUIT, "back seam",
           nu=1, nv=14, back=True)
    _panel(kit, shell, [(0.040, 0.862), (-0.004, 0.862), (-0.004, 1.105), (0.040, 1.105)], 0.007, SUIT, "back vent",
           nu=3, nv=4, back=True)

    # --- blank badge on the left breast, on a dark lanyard strap ---------------
    _panel(kit, shell, [(0.078, 1.375), (0.133, 1.375), (0.133, 1.460), (0.078, 1.460)], 0.016, WHITE, "badge",
           nu=4, nv=4)
    strap = []
    for k in range(9):
        tt = k / 8
        x = 0.045 + (0.105 - 0.045) * tt
        z = 1.735 + (1.462 - 1.735) * tt
        strap.append(_roll((x, shell.front_y(x, z) - 0.016, z)))
    kit.tube(strap, 0.0045, BLACK, verts=8, name="lanyard")

    # --- swing tag on the left wrist (manila, printed stock number) ------------
    wl = hands["l"][0]
    tag_top = Vector((0.142, -0.330, 1.050))
    kit.tube([wl + Vector((0.008, -0.02, -0.02)), (wl + tag_top) / 2 + Vector((0.004, -0.006, 0)), tag_top],
             0.0022, BLACK, verts=6, name="tag string")
    outline = [(-0.035, 0.0), (0.035, 0.0), (0.035, 0.092), (0.020, 0.110), (-0.020, 0.110), (-0.035, 0.092)]
    Mt = (Matrix.Translation(tag_top + Vector((0, 0, -0.112))) @ Matrix.Rotation(math.radians(9), 4, "Z")
          @ Matrix.Rotation(math.radians(-4), 4, "Y") @ Matrix.Rotation(math.radians(90), 4, "X"))
    _prism(kit, outline, -0.002, 0.002, Mt, TAG, "swing tag", bevel=0.001)
    for k, (w_, z_) in enumerate(((0.040, 0.070), (0.030, 0.055), (0.044, 0.040))):
        bar = [(-w_ / 2, z_), (w_ / 2, z_), (w_ / 2, z_ + 0.007), (-w_ / 2, z_ + 0.007)]
        _prism(kit, bar, 0.0018, 0.0032, Mt, BLACK, "tag print %d" % k, bevel=0.0)
    _prism(kit, [(-0.006, 0.092), (0.006, 0.092), (0.006, 0.100), (-0.006, 0.100)], -0.0030, 0.0030, Mt, BLACK,
           "tag eyelet", bevel=0.0)

    _report(kit)
    lo = cl.floor_parts(kit)
    EYE = round(face.z - lo, 3)
    bpy.context.view_layer.update()
    top = max((o.matrix_world @ v.co).z for o in kit.parts for v in o.data.vertices)
    print("[hunterA] floored by %.3f; face centre %.3f; top %.3f; parts %d" % (lo, EYE, top, len(kit.parts)))
    kit.no_collider()
