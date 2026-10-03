"""Hunter direction D — "Delivery" (Documentation/research/hunter/10_hunter_directions.md §6, §7.5).

The delivery nobody signed for: a mover bent under a quilted, strapped moving-pad
bundle that has become his back. Knit watch cap, two bands of silver tape over the
eyes and mouth, brown duck-canvas work jacket, charcoal trousers, oversized pale
cotton work gloves, steel-toe boots. Built in the "carry" render pose (Hunt plod).

Coordinates are the spec's (metres, Z up, facing -Y, left = +X) before flooring.
The tell: the cargo straps come down the load and run INTO the tops of the
shoulders (the canvas puckers where they go in); they come back out of the front of
the shoulders and cross the chest in an X with a buckle. It never sets the load down.

Slots (6, the cap): pad navy (load, hanging corner), canvas brown (jacket),
charcoal (trousers, knit cap), paper (gloves, binding, label), silver tape (tape,
buckles), vinyl (face and neck in shadow, boots, straps, label print). The spec's
SkinSallow neck and Chrome buckle are folded into vinyl and silver tape to stay
within six slots (no skin reads, as §6 asks).
"""

import math

import bmesh
from mathutils import Euler, Vector
from mathutils.bvhtree import BVHTree

NAME = "Hunter_D_Delivery"
TITLE = "Delivery"
PITCH = ("A mover bent double under a strapped, quilted moving pad that has grown into his back; "
         "every time it relays, a fresh carrier arrives with the same load and the same label.")
EYE = 1.60            # replaced in build() by the measured centre of the eye tape after flooring
SMOOTH_ANGLE = 60.0

PAD = "Creature_PadNavy"
JACKET = "Creature_CanvasBrown"
CLOTH = "Prop_FabricCharcoal"
LIGHT = "Prop_Paper"
TAPE = "Creature_TapeSilver"
DARK = "Prop_Vinyl"

V = Vector


def _R(rot):
    return Euler([math.radians(a) for a in rot], "XYZ").to_matrix()


def _rot_to(n, axis=(0, -1, 0)):
    """Euler degrees turning `axis` onto n (for parts that face -Y or +Z)."""
    e = V(axis).rotation_difference(n).to_euler()
    return tuple(math.degrees(a) for a in e)


def _smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------ the load
# A rounded box on a uniform grid (so the faces can bow, quilt and be cinched by the
# straps), pitched with the torso and rolled so its right side sits lower; its two
# ends sag like a soft load. Spec: 0.76 x 0.42 x 0.62.
L_HALF = V((0.38, 0.21, 0.31))
L_R = 0.13
L_LOC = V((0.01, 0.06, 1.60))
L_ROT = (20.0, -6.0, 0.0)        # spec wrote (20, 0, -6): in XYZ Euler that is a yaw; the roll is about Y
L_PUFF = 0.032
L_SAG = 0.035
L_QUILT = 0.02
L_QSTEP = 0.24
L_CINCH = 0.016
STRAP_X = 0.22                   # local x of the two vertical straps
GIRTH_Z = -0.05                  # local z of the girth strap
STRAP_W, STRAP_T = 0.055, 0.010
LR = _R(L_ROT)


def _radius(q):
    """Soft everywhere except the top-back-left corner, where something boxy presses through."""
    w = 1.0
    for i in range(3):
        w *= _smooth(0.15, 0.95, q[i] / L_HALF[i])
    return L_R - 0.07 * w


def _rbox(q):
    """Box-surface point q (|q_k| = half size on its face) -> rounded-box point, normal."""
    r = _radius(q)
    inner = [L_HALF[i] - r for i in range(3)]
    c = V([max(-inner[i], min(inner[i], q[i])) for i in range(3)])
    d = V(q) - c
    n = d.normalized() if d.length > 1e-9 else V((0, 0, 1))
    return c + n * r, n


def _load_disp(q, n, quilt=True):
    k = max(range(3), key=lambda i: abs(n[i]))
    a, b = [i for i in range(3) if i != k]
    w = max(0.0, 1 - (q[a] / L_HALF[a]) ** 2) * max(0.0, 1 - (q[b] / L_HALF[b]) ** 2)
    disp = L_PUFF * w * (0.7 if k == 2 else 1.0)
    cin = max(math.exp(-((q[0] - STRAP_X) / 0.05) ** 2), math.exp(-((q[0] + STRAP_X) / 0.05) ** 2),
              math.exp(-((q[2] - GIRTH_Z) / 0.05) ** 2))
    disp -= (L_CINCH + L_PUFF * w * 0.8) * cin
    if quilt and L_QUILT:
        fade = _smooth(0.84, 0.97, abs(n[k])) * (1 - 0.8 * cin)
        u, v = q[a] / L_QSTEP, q[b] / L_QSTEP
        g1, g2 = u + v + 0.5, u - v + 0.5
        d1, d2 = abs(g1 - round(g1)), abs(g2 - round(g2))
        stitch = max(math.exp(-(d1 / 0.15) ** 2), math.exp(-(d2 / 0.15) ** 2))
        disp -= L_QUILT * stitch * fade
    return disp


def _warp(p):
    """The soft load sags at its two ends."""
    return V((p.x, p.y, p.z - L_SAG * (p.x / L_HALF.x) ** 2))


def _load_point(q, off=0.0, quilt=False):
    """World point and normal on the (displaced) load surface for box-surface point q."""
    q = V(q)
    p, n = _rbox(q)
    p = _warp(p + n * (_load_disp(q, n, quilt) + off))
    return L_LOC + LR @ p, (LR @ n).normalized()


def _pad(kit, step=0.037):
    bm = bmesh.new()
    h = L_HALF
    cnt = [max(4, round(2 * h[i] / step)) for i in range(3)]
    cache = {}

    def vert(q):
        key = tuple(round(c, 6) for c in q)
        v = cache.get(key)
        if v is None:
            qv = V(q)
            p, n = _rbox(qv)
            v = bm.verts.new(_warp(p + n * _load_disp(qv, n, True)))
            cache[key] = v
        return v

    for k in range(3):
        a, b = [i for i in range(3) if i != k]
        for s in (-1, 1):
            grid = []
            for i in range(cnt[a] + 1):
                row = []
                for j in range(cnt[b] + 1):
                    q = [0.0, 0.0, 0.0]
                    q[k] = s * h[k]
                    q[a] = -h[a] + 2 * h[a] * i / cnt[a]
                    q[b] = -h[b] + 2 * h[b] * j / cnt[b]
                    row.append(vert(q))
                grid.append(row)
            for i in range(cnt[a]):
                for j in range(cnt[b]):
                    bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = kit._new_object("load", bm, PAD, "metres", "xz")
    kit._place(obj, tuple(L_LOC), L_ROT)
    return obj


def _path(corners, step=0.025):
    """Resample a polyline of box-surface points every ``step`` metres."""
    out = []
    for a, b in zip(corners, corners[1:]):
        a, b = V(a), V(b)
        n = max(1, int(math.ceil((b - a).length / step)))
        out += [a.lerp(b, i / n) for i in range(n)]
    out.append(V(corners[-1]))
    return out


def _ribbon(kit, pts, nrm, width, thick, slot, name):
    """Flat webbing strap along pts, lying with its face on the normals nrm."""
    bm = bmesh.new()
    rings = []
    n = len(pts)
    for k in range(n):
        t = (pts[min(k + 1, n - 1)] - pts[max(k - 1, 0)]).normalized()
        nn = (nrm[k] - t * nrm[k].dot(t)).normalized()
        s = t.cross(nn).normalized()
        w = width(k / (n - 1)) if callable(width) else width
        rings.append([bm.verts.new(pts[k] + s * sx * w / 2 + nn * sy * thick / 2)
                      for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for a, b in zip(rings, rings[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _patch(kit, centre_xy, size, angle, off, slot, name, n=6):
    """A label-like patch conforming to the load's top face (local x, y; rotated by angle deg)."""
    bm = bmesh.new()
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    grid = []
    for i in range(n + 1):
        row = []
        for j in range(n + 1):
            u = (i / n - 0.5) * size[0]
            v = (j / n - 0.5) * size[1]
            q = (centre_xy[0] + u * ca - v * sa, centre_xy[1] + u * sa + v * ca, L_HALF.z)
            p, _nn = _load_point(q, off)
            row.append(bm.verts.new(p))
        grid.append(row)
    for i in range(n):
        for j in range(n):
            bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bm.normal_update()
    bm.faces.ensure_lookup_table()
    up = LR @ V((0, 0, 1))
    if bm.faces[0].normal.dot(up) < 0:
        for f in bm.faces:
            f.normal_flip()
    return kit._new_object(name, bm, slot, "metres", "xz")


def _tail(kit, drop=0.27, nu=8, nv=7, thick=0.014):
    """A loose corner of the moving blanket hanging off the bundle's bottom-back-left corner,
    bound on both edges (the pale binding again, continuing the edge that runs down the
    left side): the load is a blanket wrapped round something."""
    h = L_HALF
    attach = _path([(0.04, h.y - 0.035, -h.z), (h.x - 0.10, h.y - 0.035, -h.z), (h.x - 0.10, 0.0, -h.z)], 0.01)
    top_pts = [_load_point(q, -0.006)[0] for q in attach]
    acc = [0.0]
    for a, b in zip(top_pts, top_pts[1:]):
        acc.append(acc[-1] + (b - a).length)

    def top(u):
        t = u * acc[-1]
        for k in range(len(acc) - 1):
            if t <= acc[k + 1] or k == len(acc) - 2:
                f = (t - acc[k]) / max(1e-9, acc[k + 1] - acc[k])
                return top_pts[k].lerp(top_pts[k + 1], max(0.0, min(1.0, f)))

    corner, cn = _load_point((h.x, h.y, -h.z), 0.0)
    out = V((cn.x, cn.y, 0)).normalized()
    tip = corner + out * -0.11 + V((0, 0.045, -drop))
    side = V((-out.y, out.x, 0))

    def S(u, v):
        p = top(u).lerp(tip + side * (u - 0.5) * 0.04, v ** 0.9)
        bow = math.sin(math.pi * v) * (0.035 + 0.02 * math.sin(math.pi * u))
        fold = 0.012 * math.sin(2 * math.pi * (1.5 * u + 0.3 * v)) * v
        return p + out * (bow + fold)

    def N(u, v):
        e = 1e-3
        du = S(min(1, u + e), v) - S(max(0, u - e), v)
        dv = S(u, min(1, v + e)) - S(u, max(0, v - e))
        n = du.cross(dv).normalized()
        return n if n.dot(out) > 0 else -n

    bm = bmesh.new()
    layers = []
    for sd in (1, -1):
        layers.append([[bm.verts.new(S(i / nu, k / nv) + N(i / nu, k / nv) * sd * thick / 2) for k in range(nv + 1)]
                       for i in range(nu + 1)])
    a, b = layers
    for i in range(nu):
        for k in range(nv):
            bm.faces.new((a[i][k], a[i + 1][k], a[i + 1][k + 1], a[i][k + 1]))
            bm.faces.new((b[i][k], b[i][k + 1], b[i + 1][k + 1], b[i + 1][k]))
    loop = [(0, k) for k in range(nv + 1)] + [(i, nv) for i in range(1, nu + 1)] + [(nu, k) for k in range(nv - 1, -1, -1)]
    for (i0, k0), (i1, k1) in zip(loop, loop[1:]):
        bm.faces.new((a[i0][k0], a[i1][k1], b[i1][k1], b[i0][k0]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    kit._new_object("blanket corner", bm, PAD, "metres", "xz")
    # binding: down one edge, round the tip, back up the other, folded over the edge
    pts, nrm = [], []
    e = 1e-3
    for u, ks in ((0.0, range(1, nv + 1)), (1.0, range(nv, 0, -1))):
        for k in ks:
            v = k / nv
            d = (S(min(1, u + e), v) - S(max(0, u - e), v)).normalized() * (1 if u > 0.5 else -1)
            pts.append(S(u, v) + d * 0.006)
            nrm.append(d)
    _ribbon(kit, pts, nrm, thick + 0.012, 0.03, LIGHT, "corner binding")


# ------------------------------------------------------------------ the head
H_LOC = V((0.0, -0.255, 1.659))
H_ROT = (36.0, 0.0, 3.0)                # hung 36 deg under the load, turned a touch to its left
H_HALF = (0.09, 0.105, 0.1175)          # 0.18 W x 0.21 D x 0.235 H in the cap
HR = _R(H_ROT)
EYE_Z = (-0.014, 0.024)                 # head-local z of the eye tape
MOUTH_Z = (-0.076, -0.048)
CUFF_Z = (0.026, 0.072)


def _head_deform(p):
    t = max(0.0, -p.z / H_HALF[2])
    return V((p.x * (1 - 0.26 * t * t), p.y * (1 - 0.06 * t * t) - 0.014 * t * t, p.z))


def _head(kit):
    """The face (dark, in shadow) and the knit cap over it, cut at the cuff."""
    for part, slot, scale, cut in (("face", DARK, 1.0, None), ("cap", CLOTH, 1.045, CUFF_Z[0] - 0.006)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=12, radius=1.0)
        if cut is not None:
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z * H_HALF[2] < cut], context="VERTS")
        for v in bm.verts:
            p = V((v.co.x * H_HALF[0], v.co.y * H_HALF[1], v.co.z * H_HALF[2]))
            if cut is not None:
                # knit cap: a little fuller, with a soft peak at the top-back
                p = p * scale + V((0, 0.006, 0.012)) * max(0.0, p.z / H_HALF[2]) ** 3
            v.co = _head_deform(p)
        obj = kit._new_object("head " + part, bm, slot, "metres", "xz")
        kit._place(obj, tuple(H_LOC), H_ROT)


def _head_ring_point(v, z, off):
    zz = max(-0.999, min(0.999, z / H_HALF[2]))
    u = math.asin(zz)
    base = V((H_HALF[0] * math.cos(u) * math.cos(v), H_HALF[1] * math.cos(u) * math.sin(v), H_HALF[2] * math.sin(u)))
    nrm = V((base.x / H_HALF[0] ** 2, base.y / H_HALF[1] ** 2, base.z / H_HALF[2] ** 2)).normalized()
    return _head_deform(base + nrm * off)


def _band(kit, z0, z1, arc_deg, t_out, slot, name, tilt=0.0, verts=24, bulge=None):
    """A band wrapped round the head between head-local heights z0..z1, centred on the front.
    bulge(v) adds extra outward offset (tape bridging the nose)."""
    bm = bmesh.new()
    arc = math.radians(arc_deg)
    full = arc_deg >= 359.9
    count = verts if full else verts + 1
    rings = []
    for i in range(count):
        v = -math.pi / 2 - arc / 2 + arc * i / verts
        dz = tilt * H_HALF[0] * math.cos(v)
        extra = bulge(v) if bulge else 0.0
        rings.append([bm.verts.new(_head_ring_point(v, z + dz, off + (extra if off > 0 else 0.0)))
                      for z, off in ((z0, t_out), (z1, t_out), (z1, -0.006), (z0, -0.006))])
    pairs = list(zip(rings, rings[1:])) + ([(rings[-1], rings[0])] if full else [])
    for a, b in pairs:
        for k in range(4):
            m = (k + 1) % 4
            bm.faces.new((a[k], a[m], b[m], b[k]))
    if not full:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = kit._new_object(name, bm, slot, "metres", "xz")
    kit._place(obj, tuple(H_LOC), H_ROT)
    return obj


# ------------------------------------------------------------------ body frame
def _knee(hip, ankle, thigh, shin, out=0.0):
    """Two-bone IK in the leg's plane, knee pointing forward (-Y) and `out` sideways."""
    d = ankle - hip
    dist = d.length
    u = d / dist
    if dist >= thigh + shin - 1e-4:
        return hip + u * thigh
    x = (thigh ** 2 - shin ** 2 + dist ** 2) / (2 * dist)
    h = math.sqrt(max(0.0, thigh ** 2 - x ** 2))
    fwd = V((out, -1, 0)).normalized()
    perp = (fwd - u * fwd.dot(u)).normalized()
    return hip + u * x + perp * h


# Boots in sole space (forward = -Y): sole centre, rotation, then joints.
BOOT_L = (V((0.145, -0.16, 0.0)), (0.0, 0.0, -4.0))
BOOT_R = (V((-0.145, 0.31, 0.036)), (12.0, 0.0, 5.0))     # trailing foot, heel lifted
BOOT_J = {"ankle": V((0, 0.045, 0.125)), "anklelow": V((0, 0.03, 0.08))}


def _boot_pts(boot):
    c, rot = boot
    r = _R(rot)
    return {k: c + r @ p for k, p in BOOT_J.items()}


def frame():
    j = {
        "pelvis": V((0, 0.14, 0.91)), "belly": V((0, 0.07, 1.1)),
        "chest": V((0, -0.025, 1.29)), "chest_top": V((0, -0.115, 1.43)),
        "neck_base": V((0, -0.155, 1.49)), "neck": V((0, -0.225, 1.57)),
        "shoulder_l": V((0.245, -0.125, 1.42)), "shoulder_r": V((-0.245, -0.12, 1.41)),
        "armin_l": V((0.15, -0.12, 1.44)), "armin_r": V((-0.15, -0.115, 1.43)),
        "elbow_l": V((0.275, -0.20, 1.115)), "elbow_r": V((-0.275, -0.185, 1.12)),
        "wrist_l": V((0.305, -0.33, 0.845)), "wrist_r": V((-0.305, -0.29, 0.865)),
        "hip_l": V((0.11, 0.16, 0.86)), "hip_r": V((-0.11, 0.18, 0.86)),
        "seat_l": V((0.07, 0.12, 0.95)), "seat_r": V((-0.07, 0.13, 0.95)),
    }
    for s, sign, boot in (("l", 1, BOOT_L), ("r", -1, BOOT_R)):
        b = _boot_pts(boot)
        for k, p in b.items():
            j[k + "_" + s] = p
        j["knee_" + s] = _knee(j["hip_" + s], j["ankle_" + s], 0.44, 0.40, out=sign * 0.12)
        j["hemt_" + s] = j["knee_" + s].lerp(j["ankle_" + s], 0.80)     # trouser hem
        j["shin_" + s] = j["knee_" + s].lerp(j["ankle_" + s], 0.55)     # boot shaft starts inside the leg
        j["sleeve_" + s] = j["elbow_" + s].lerp(j["wrist_" + s], 0.86)
        j["wristin_" + s] = j["elbow_" + s].lerp(j["wrist_" + s], 0.74)
    return j


def _hand(kit, cl, j, s, name):
    """Oversized cotton work glove: knit cuff, palm, four curled fingers held together, thumb."""
    sign = 1 if s == "l" else -1
    w = j["wrist_" + s]
    d = (w - j["elbow_" + s]).normalized()
    d = (d + V((0, 0.12, 0))).normalized()     # the wrist hangs back a little from the forearm line
    m = V((-sign, 0, 0))                       # palm faces the thigh
    m = (m - d * m.dot(d)).normalized()
    f = d.cross(m).normalized()
    if f.y > 0:
        f = -f                                 # thumb side forward
    palm = w + d * 0.062 + m * 0.004
    knuck = w + d * 0.118 + m * 0.008
    joints = {"wristin": (j["wristin_" + s], 0.05), "wrist": (w, 0.057),
              "palm": (palm, (0.036, 0.062)), "knuck": (knuck, (0.03, 0.058))}
    bones = [("wristin", "wrist"), ("wrist", "palm"), ("palm", "knuck")]
    obj = cl.skin_body(kit, joints, bones, LIGHT, subdiv=2, name=name)
    fj, fb = {}, []
    spread = (0.0, 0.004, 0.008, 0.013)
    for i, (off, length, r) in enumerate(((0.038, 0.095, 0.0172), (0.013, 0.106, 0.0178),
                                          (-0.0125, 0.099, 0.0172), (-0.037, 0.082, 0.0158))):
        base = knuck + f * off
        a = base - d * 0.03
        mid = base + d * length * 0.5 + m * (0.012 + 0.004 * i) + f * spread[i] * (1 if off > 0 else -1)
        tip = mid + d * length * 0.3 + m * (0.034 + 0.006 * i)
        fj["f%da" % i], fj["f%db" % i], fj["f%dc" % i] = (a, r), (mid, r * 0.96), (tip, r * 0.86)
        fb += [("f%da" % i, "f%db" % i), ("f%db" % i, "f%dc" % i)]
    # thumb: out of the palm's heel, lying down along the index finger
    t0 = w + d * 0.03 + f * 0.02 + m * 0.016
    t1 = w + d * 0.082 + f * 0.034 + m * 0.03
    t2 = t1 + d * 0.048 + f * -0.004 + m * 0.014
    fj.update({"t0": (t0, 0.023), "t1": (t1, 0.02), "t2": (t2, 0.0175)})
    fb += [("t0", "t1"), ("t1", "t2")]
    fingers = cl.skin_body(kit, fj, fb, LIGHT, subdiv=1, name=name + " fingers")
    cl.decimate_to(fingers, 640)
    return obj


def _section(obj, centre, axis, slab=0.02, rmax=0.2):
    """Half-extents of a skin part across world X and across the axis in the YZ plane
    (only vertices within rmax of the axis: one leg of a two-leg part)."""
    ex = V((1, 0, 0))
    ey = axis.cross(ex).normalized()
    rx = ry = 0.0
    for v in obj.data.vertices:
        d = v.co - centre
        if abs(d.dot(axis)) < slab and (d - axis * d.dot(axis)).length < rmax:
            rx = max(rx, abs(d.dot(ex)))
            ry = max(ry, abs(d.dot(ey)))
    return rx, ry


def _tube_open(kit, top, bot, r_top, r_bot, slot, name, verts=20, wall=0.01, level=False):
    """An open elliptical tube from top to bot (radii (rx, ry) across X / across the axis):
    a garment edge with its inside showing (hem, cuff)."""
    axis = (top - bot).normalized()
    ex = V((1, 0, 0))
    ex = (ex - axis * ex.dot(axis)).normalized()
    ey = axis.cross(ex).normalized()
    bm = bmesh.new()
    rings = []
    for c, (rx, ry), off in ((top, r_top, 0.0), (bot, r_bot, 0.0), (bot, r_bot, -wall), (top, r_top, -wall)):
        ring = []
        for i in range(verts):
            a = 2 * math.pi * i / verts
            p = c + ex * math.cos(a) * (rx + off) + ey * math.sin(a) * (ry + off)
            if level and c is bot:
                p = p + axis * ((bot.z - p.z) / axis.z)
            ring.append(bm.verts.new(p))
        rings.append(ring)
    for k in range(3):
        a, b = rings[k], rings[k + 1]
        for i in range(verts):
            m = (i + 1) % verts
            bm.faces.new((a[i], a[m], b[m], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _basis_euler(xaxis, zaxis):
    """Euler degrees of a frame with the given x and z axes."""
    from mathutils import Matrix
    z = zaxis.normalized()
    x = (xaxis - z * xaxis.dot(z)).normalized()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed()
    return tuple(math.degrees(a) for a in m.to_euler("XYZ"))


def _bvh(objs):
    verts, polys, off = [], [], 0
    for o in objs:
        mw = o.matrix_world
        verts += [mw @ v.co for v in o.data.vertices]
        polys += [tuple(i + off for i in p.vertices) for p in o.data.polygons]
        off += len(o.data.vertices)
    return BVHTree.FromPolygons(verts, polys)


def _catmull(ctrl, step=0.025):
    pts = [V(p) for p in ctrl]
    pts = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        n = max(2, int(math.ceil((p2 - p1).length / step)))
        for k in range(n):
            t = k / n
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-2])
    return out


def _draped(tree, ctrl, off, keep_ends=1, lift=None):
    """A curve through ctrl, snapped onto the surface in tree and lifted by off."""
    raw = _catmull(ctrl)
    hits = [tree.find_nearest(p)[:2] for p in raw]
    # average the facet normals along the strap so the webbing lies flat instead of twisting
    nrm = []
    for i in range(len(raw)):
        acc = V((0, 0, 0))
        for k in range(max(0, i - 2), min(len(raw), i + 3)):
            acc += hits[k][1]
        nrm.append(acc.normalized())
    pts = []
    for i, p in enumerate(raw):
        extra = lift(i / (len(raw) - 1)) if lift else 0.0
        if i < keep_ends or i >= len(raw) - keep_ends:
            pts.append(p)
        else:
            pts.append(hits[i][0] + nrm[i] * (off + extra))
    return pts, nrm


# ------------------------------------------------------------------ build
def build(kit, cl):
    global EYE
    j = frame()
    J = lambda names, radii: {n: (j[n], r) for n, r in zip(names, radii)}  # noqa: E731

    # Jacket: torso chain (hem to chest top) and two sleeve chains starting inside the
    # chest (separate chains: no flat Skin sheets at a 3-way branch).
    torso = cl.skin_body(kit, J(["pelvis", "belly", "chest", "chest_top"],
                                [(0.19, 0.16), (0.20, 0.17), (0.232, 0.18), (0.235, 0.15)]),
                         [("pelvis", "belly"), ("belly", "chest"), ("chest", "chest_top")],
                         JACKET, name="jacket torso")
    sleeves = []
    for s in ("l", "r"):
        sleeves.append(cl.skin_body(kit, J(["armin_" + s, "shoulder_" + s, "elbow_" + s, "sleeve_" + s],
                                           [0.078, 0.082, 0.064, 0.058]),
                                    [("armin_" + s, "shoulder_" + s), ("shoulder_" + s, "elbow_" + s),
                                     ("elbow_" + s, "sleeve_" + s)], JACKET, name="sleeve " + s))
        # a crisp open cuff, so the sleeve ends like a sleeve
        axis = (j["elbow_" + s] - j["wrist_" + s]).normalized()
        c0 = j["sleeve_" + s] + axis * 0.05
        rx, ry = _section(sleeves[-1], c0, axis)
        _tube_open(kit, c0, j["sleeve_" + s] - axis * 0.012, (rx * 0.97, ry * 0.97), (rx * 1.08, ry * 1.08),
                   JACKET, "cuff " + s, verts=16, wall=0.008)
        cl.decimate_to(sleeves[-1], 560)
    # Jacket hem: a short flared skirt with a straight edge (chore-coat length, over the seat),
    # perpendicular to the pitched torso; the skin's round end hides inside it.
    axis = (j["belly"] - j["pelvis"]).normalized()
    c0 = j["pelvis"] + axis * 0.06
    rx, ry = _section(torso, c0, axis, rmax=0.4)
    hang = (axis + V((0, 0, 0.6))).normalized()
    _tube_open(kit, c0, j["pelvis"] - hang * 0.16, (rx * 0.97, ry * 0.97), (max(rx * 1.12, 0.235), ry * 1.12),
               JACKET, "jacket hem", verts=24, wall=0.012, level=True)
    # Trousers: two leg chains from inside the jacket.
    trousers = cl.skin_body(kit, J(["seat_l", "hip_l", "knee_l", "hemt_l", "seat_r", "hip_r", "knee_r", "hemt_r"],
                                   [0.10, 0.118, 0.09, 0.082, 0.10, 0.118, 0.09, 0.082]),
                            [("seat_l", "hip_l"), ("hip_l", "knee_l"), ("knee_l", "hemt_l"),
                             ("seat_r", "hip_r"), ("hip_r", "knee_r"), ("knee_r", "hemt_r")], CLOTH, name="trousers")
    cl.decimate_to(trousers, 900)
    for s in ("l", "r"):
        # trouser bottoms break over the boot tops: an open hem flush with the leg
        axis = (j["knee_" + s] - j["ankle_" + s]).normalized()
        c0 = j["hemt_" + s] + axis * 0.03
        rx, ry = _section(trousers, c0, axis, slab=0.03)
        _tube_open(kit, c0, j["hemt_" + s] - axis * 0.06, (rx * 1.1, ry * 1.1), (rx * 1.14, ry * 1.14),
                   CLOTH, "trouser hem " + s, verts=16, wall=0.008)
    # Steel-toe work boots: a shaft out of the trouser hem, a blunt rounded foot, and a
    # lugged sole with a deeper heel.
    for s, boot in (("l", BOOT_L), ("r", BOOT_R)):
        b = cl.skin_body(kit, J(["shin_" + s, "ankle_" + s, "anklelow_" + s], [0.07, 0.08, 0.074]),
                         [("shin_" + s, "ankle_" + s), ("ankle_" + s, "anklelow_" + s)], DARK, name="boot " + s)
        cl.decimate_to(b, 220)
        c, rot = boot
        r = _R(rot)
        kit.soft_box((0.124, 0.262, 0.104), tuple(c + r @ V((0, -0.012, 0.078))), DARK, radius=0.022, puff=0.003,
                     segments=16, rings=8, rot=rot, name="boot foot " + s)
        cl.ellipsoid(kit, (0.124, 0.115, 0.094), tuple(c + r @ V((0, -0.108, 0.071))), DARK, rot=rot,
                     segments=14, rings=8, name="steel toe " + s)
        kit.box((0.132, 0.20, 0.026), tuple(c + r @ V((0, -0.068, 0.013))), DARK, bevel=0.01, segments=1,
                rot=rot, name="sole " + s)
        kit.box((0.124, 0.095, 0.04), tuple(c + r @ V((0, 0.075, 0.02))), DARK, bevel=0.008, segments=1,
                rot=rot, name="heel " + s)
    # Neck (charcoal: no skin reads) and the capped, taped head with a nose under the tape.
    cl.skin_body(kit, J(["neck_base", "neck"], [0.068, 0.062]), [("neck_base", "neck")], DARK, name="neck")
    _head(kit)
    cl.ellipsoid(kit, (0.03, 0.034, 0.05), tuple(H_LOC + HR @ V((0, -0.097, -0.016))), DARK,
                 rot=(H_ROT[0] - 14, 0, H_ROT[2]), segments=10, rings=6, name="nose")
    _band(kit, CUFF_Z[0], CUFF_Z[1], 360, 0.009, CLOTH, "cap cuff", verts=20)
    nose_bridge = lambda v: 0.012 * math.exp(-((v + math.pi / 2) / 0.22) ** 2)  # noqa: E731
    _band(kit, EYE_Z[0], EYE_Z[1], 205, 0.0045, TAPE, "tape eyes", tilt=0.06, bulge=nose_bridge, verts=22)
    _band(kit, MOUTH_Z[0], MOUTH_Z[1], 160, 0.004, TAPE, "tape mouth", tilt=-0.05, verts=18)
    # Gloves.
    for s in ("l", "r"):
        _hand(kit, cl, j, s, "glove " + s)

    # The load.
    _pad(kit)
    h = L_HALF
    # Binding: the pad's pale edge tape, folded over the top-front lip and running
    # down the left front corner; it wanders a little like a real blanket edge.
    bq = _path([(-h.x, -h.y + 0.035, h.z), (h.x, -h.y + 0.035, h.z), (h.x, -h.y + 0.035, -h.z * 0.4)], 0.03)
    bpts, bnrm = [], []
    for i, q in enumerate(bq):
        wob = 0.012 * math.sin(i * 0.55)
        q = V((q.x, q.y + wob, q.z)) if q.z > h.z - 1e-6 else V((q.x, q.y + wob, q.z))
        p, n = _load_point(q, 0.007)
        bpts.append(p)
        bnrm.append(n)
    _ribbon(kit, bpts, bnrm, 0.04, 0.012, LIGHT, "binding")
    _tail(kit)
    # Shipping label on the top face, stuck on slightly askew, with print.
    lab_c, lab_a = (-0.02, 0.01), 7.0
    _patch(kit, lab_c, (0.21, 0.27), lab_a, 0.004, LIGHT, "label")
    ca, sa = math.cos(math.radians(lab_a)), math.sin(math.radians(lab_a))
    for du, dv, su, sv in ((-0.015, 0.085, 0.14, 0.014), (-0.03, 0.055, 0.11, 0.012), (-0.02, 0.028, 0.13, 0.012),
                           (0.0, -0.075, 0.15, 0.05)):
        cx = lab_c[0] + du * ca - dv * sa
        cy = lab_c[1] + du * sa + dv * ca
        _patch(kit, (cx, cy), (su, sv), lab_a, 0.0055, DARK, "label print", n=2)

    # Straps over the load: down the back, over the top, down the front face and INTO the shoulders.
    sleeve_tree = _bvh(sleeves)
    for s, x0 in (("l", STRAP_X), ("r", -STRAP_X)):
        sh_local = LR.transposed() @ (j["shoulder_" + s] - L_LOC)
        z_end = sh_local.z + 0.07
        q = _path([(x0, -h.y * 0.2, -h.z), (x0, h.y, -h.z), (x0, h.y, h.z), (x0, -h.y, h.z), (x0, -h.y, z_end)], 0.03)
        pts, nrm = [], []
        for qq in q:
            p, n = _load_point(qq, STRAP_T / 2 + 0.002)
            pts.append(p)
            nrm.append(n)
        tgt = j["shoulder_" + s] + V((0, -0.01, 0.0))
        last = pts[-1]
        for t in (0.4, 0.75, 1.0):
            pts.append(last.lerp(tgt, t))
            nrm.append(nrm[-1])
        _ribbon(kit, pts, nrm, STRAP_W, STRAP_T, DARK, "load strap " + s)
        # where it goes in, the canvas puckers round it
        hit, hn, _i, _d = sleeve_tree.ray_cast(last, (tgt - last).normalized(), (tgt - last).length)
        if hit is None:
            hit, hn, _i, _d = sleeve_tree.find_nearest(last.lerp(tgt, 0.6))
        across = (tgt - last).cross(hn)
        cl.ellipsoid(kit, (0.105, 0.06, 0.026), tuple(hit + hn * 0.002), JACKET, rot=_basis_euler(across, hn),
                     segments=12, rings=6, name="pucker " + s)
    # Girth strap round the back and sides (its ends tuck under the pad at the front corners).
    gq = _path([(h.x - 0.06, -h.y, GIRTH_Z), (h.x, -h.y, GIRTH_Z), (h.x, h.y, GIRTH_Z), (-h.x, h.y, GIRTH_Z),
                (-h.x, -h.y, GIRTH_Z), (-h.x + 0.06, -h.y, GIRTH_Z)], 0.03)
    gp, gn = [], []
    for i, qq in enumerate(gq):
        off = STRAP_T * 1.5 + 0.002 if 0 < i < len(gq) - 1 else -0.01
        p, n = _load_point(qq, off)
        gp.append(p)
        gn.append(n)
    _ribbon(kit, gp, gn, STRAP_W, STRAP_T, DARK, "girth strap")
    # Cam buckle on the girth strap, right side.
    bp, bn = _load_point((-h.x, -0.05, GIRTH_Z), STRAP_T * 2 + 0.008)
    kit.box((0.05, 0.016, 0.075), tuple(bp), TAPE, bevel=0.004, rot=_rot_to(bn), name="cam buckle")

    # The chest X: each strap comes back out of the front of its shoulder and crosses
    # the chest to the opposite flank, where it runs into the jacket.
    torso_tree = _bvh([torso])
    cross = V((0.0, -0.28, 1.27))
    for s, sign in (("l", 1), ("r", -1)):
        ctrl = [j["shoulder_" + s] + V((-sign * 0.03, -0.03, -0.01)),
                V((sign * 0.16, -0.26, 1.39)), cross, V((-sign * 0.13, -0.23, 1.15)),
                V((-sign * 0.19, -0.12, 1.05)), V((-sign * 0.15, -0.06, 1.0))]
        lift = (lambda t: 0.012 * math.exp(-((t - 0.45) / 0.15) ** 2)) if s == "l" else None
        pts, nrm = _draped(torso_tree, ctrl, STRAP_T / 2 + 0.009, keep_ends=2, lift=lift)
        _ribbon(kit, pts, nrm, 0.05, STRAP_T, DARK, "chest strap " + s)
    loc, n, _i, _d = torso_tree.find_nearest(cross)
    kit.frame((0.085, 0.07), (0.055, 0.04), 0.014, tuple(loc + n * 0.032), TAPE, bevel=0.003,
              rot=_rot_to(n), name="buckle")

    lo = cl.floor_parts(kit)
    # Eye: the centre of the eye tape's front, after flooring.
    eye = H_LOC + HR @ _head_ring_point(-math.pi / 2, sum(EYE_Z) / 2, 0.0045)
    EYE = round(eye.z - lo, 3)
    import bpy
    bpy.context.view_layer.update()
    ws = [o.matrix_world @ v.co for o in kit.parts for v in o.data.vertices]
    front = -min(p.y for p in ws if p.z > 1.0)
    back = max(p.y for p in ws if 0.4 <= p.z <= 1.95)
    print("[delivery] reach: front above 1 m %.3f, back 0.4-1.95 m %.3f" % (front, back))
    tris = {}
    for o in kit.parts:
        key = o.name.rstrip(".0123456789")
        tris[key] = tris.get(key, 0) + sum(len(p.vertices) - 2 for p in o.data.polygons)
    print("[delivery] floor shift %.3f, eye %.3f (front y %.3f), tris %d: %s" % (
        lo, EYE, eye.y, sum(tris.values()),
        ", ".join("%s %d" % kv for kv in sorted(tris.items(), key=lambda kv: -kv[1]))))
    kit.no_collider()
