"""Hunter direction D — "Delivery" (Documentation/research/hunter/10_hunter_directions.md §6, §7.5).

The delivery nobody signed for: a mover bent under a square-cornered, strapped
moving-pad bundle that has become his back. Charcoal knit watch cap with an ecru
cuff turned up at the brow (the only light on the head); the face below it is
charcoal, plain big planes, in the load's shadow. Brown duck-canvas work jacket
(waist length, banded hem), charcoal trousers, oversized pale cotton work gloves,
steel-toe boots. Built in the "carry" render pose (Hunt plod).

Coordinates are the spec's (metres, Z up, facing -Y, left = +X) before flooring.
Rotations are Blender XYZ Euler degrees: X pitches, Y rolls (+Y lowers the +X end),
Z yaws (§7.0). The load is a slab 0.72 x 0.42 x 0.50 m, corner radius 0.05, pitched
20 deg with the torso, rolled -11 deg about Y (its right end down) and sitting 3 cm
toward its left shoulder, so from the front it is a tilted block, not a round head.

The tell: the cargo straps come down the load and run INTO the tops of the
shoulders (the canvas puckers where they go in); they come back out of the front of
the shoulders and cross the chest in an X with a buckle. It never sets the load down.

Slots (6): pad navy (load), canvas brown (jacket, collar), charcoal
(trousers, cap, face, neck), paper (gloves, cap cuff, binding, label), vinyl (boots,
straps, label print), chrome (the two buckles). No tape anywhere: the first build's
silver tape over the eyes and mouth read as a bound hostage and sat near Little
Nightmares' Janitor (critic C1, C6.5), so Creature_TapeSilver is gone.
"""

import math

import bmesh
from mathutils import Euler, Vector
from mathutils.bvhtree import BVHTree

NAME = "Hunter_D_Delivery"
TITLE = "Delivery"
PITCH = ("A mover bent under a tilted, strapped moving-pad load whose straps run into his shoulders; "
         "his face stays in its shadow, and every relay brings a fresh carrier with the same load and label.")
EYE = 1.60            # replaced in build() by the measured centre of the face (eye line) after flooring
SMOOTH_ANGLE = 60.0

PAD = "Creature_PadNavy"
JACKET = "Creature_CanvasBrown"
CLOTH = "Prop_FabricCharcoal"
LIGHT = "Prop_Paper"
DARK = "Prop_Vinyl"
CHROME = "Prop_Chrome"

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
# A square-cornered slab (rounded box, radius 0.05) on a grid laid out for it: two
# rows per corner quarter-round and the quilt seams / cell middles in between, so the
# corners stay crisp, the faces bow a little, the quilting is a few grid-aligned
# stitch lines (production bakes it to a normal map) and the straps cinch on a row.
L_HALF = V((0.36, 0.21, 0.25))       # 0.72 W x 0.42 D x 0.50 H
L_R = 0.05
L_LOC = V((0.03, 0.06, 1.59))        # 3 cm toward its left shoulder
L_ROT = (20.0, -11.0, 0.0)           # pitch 20 with the torso; roll -11 (right end down)
L_PUFF = 0.016                       # faces bow out a little: a pad over something hard
L_SAG = 0.008
L_QUILT = 0.015                      # depth of a stitch line
L_CELL = 0.15                        # target quilt cell
L_CINCH = 0.012
STRAP_W, STRAP_T = 0.055, 0.010
GIRTH_Z = 0.0                        # local z of the girth strap (a cell-middle row)
LR = _R(L_ROT)
STRAP_END = {}                       # local z where each shoulder strap leaves the front face (set in build)


def _inner(i):
    return L_HALF[i] - L_R


def _seams(i):
    """Interior quilt-seam positions along local axis i (the face perimeter is left plain)."""
    inner = _inner(i)
    n = max(1, round(2 * inner / L_CELL))
    cell = 2 * inner / n
    return [-inner + cell * m for m in range(1, n)], cell, n


def _rows(i):
    """Grid positions along local axis i: edge, 22.5 deg on the round, seams and cell middles."""
    h, inner = L_HALF[i], _inner(i)
    t = math.tan(math.radians(22.5)) * L_R
    _s, cell, n = _seams(i)
    return [-h, -inner - t] + [-inner + cell * m / 2 for m in range(2 * n + 1)] + [inner + t, h]


STRAP_X = _inner(0) - _seams(0)[1] / 2      # local x of the two vertical straps: the outer cell middles


def _rbox(q):
    """Box-surface point q (|q_k| = half size on its face) -> rounded-box point, normal."""
    inner = [_inner(i) for i in range(3)]
    c = V([max(-inner[i], min(inner[i], q[i])) for i in range(3)])
    d = V(q) - c
    n = d.normalized() if d.length > 1e-9 else V((0, 0, 1))
    return c + n * L_R, n


def _stitch(i, x):
    seams = _seams(i)[0]
    if not seams:
        return 0.0
    d = min(abs(x - s) for s in seams)
    return math.exp(-(d / 0.03) ** 2)


def _cinch(q, n):
    """How much the straps pull the surface in at q (0..1)."""
    h = L_HALF
    front = n[1] < -0.7
    cin = 0.0
    for side, sx in (("l", 1), ("r", -1)):
        g = math.exp(-((q[0] - sx * STRAP_X) / 0.05) ** 2)
        if front:      # the shoulder strap only runs down the front face as far as its exit
            g *= _smooth(STRAP_END.get(side, -h.z) - 0.06, STRAP_END.get(side, -h.z), q[2])
        cin = max(cin, g)
    g = math.exp(-((q[2] - GIRTH_Z) / 0.05) ** 2)
    if front:          # the girth strap tucks under at the front corners
        g *= _smooth(h.x - 0.12, h.x - 0.05, abs(q[0]))
    if abs(n[2]) > 0.7:
        g = 0.0
    return max(cin, g)


def _load_disp(q, n, quilt=True):
    k = max(range(3), key=lambda i: abs(n[i]))
    a, b = [i for i in range(3) if i != k]
    w = max(0.0, 1 - (q[a] / L_HALF[a]) ** 2) * max(0.0, 1 - (q[b] / L_HALF[b]) ** 2)
    disp = L_PUFF * w * (0.7 if k == 2 else 1.0)
    cin = _cinch(q, n)
    disp -= (L_CINCH + L_PUFF * w * 0.8) * cin
    if quilt and L_QUILT:
        fade = _smooth(0.9, 0.99, abs(n[k])) * (1 - 0.8 * cin)
        disp -= L_QUILT * max(_stitch(a, q[a]), _stitch(b, q[b])) * fade
    return disp


def _warp(p):
    """The soft load sags a touch at its two ends."""
    return V((p.x, p.y, p.z - L_SAG * (p.x / L_HALF.x) ** 2))


def _load_point(q, off=0.0, quilt=False):
    """World point and normal on the (displaced) load surface for box-surface point q."""
    q = V(q)
    p, n = _rbox(q)
    p = _warp(p + n * (_load_disp(q, n, quilt) + off))
    return L_LOC + LR @ p, (LR @ n).normalized()


def _pad(kit):
    bm = bmesh.new()
    h = L_HALF
    rows = [_rows(i) for i in range(3)]
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
            for ra in rows[a]:
                row = []
                for rb in rows[b]:
                    q = [0.0, 0.0, 0.0]
                    q[k], q[a], q[b] = s * h[k], ra, rb
                    row.append(vert(q))
                grid.append(row)
            for i in range(len(rows[a]) - 1):
                for j in range(len(rows[b]) - 1):
                    bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = kit._new_object("load", bm, PAD, "metres", "xz")
    kit._place(obj, tuple(L_LOC), L_ROT)
    return obj


def _binding_lift(q):
    """Straps lift over the binding where they cross it (top-front edge, left-front edge)."""
    h = L_HALF
    d1 = abs(q[1] + h.y) + abs(q[2] - h.z)
    d2 = abs(q[0] - h.x) + abs(q[1] + h.y)
    return 0.015 * math.exp(-(min(d1, d2) / 0.035) ** 2)


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


# ------------------------------------------------------------------ the head
H_LOC = V((0.0, -0.255, 1.659))
H_ROT = (36.0, 0.0, 3.0)                # hung 36 deg under the load, turned a touch to its left
H_HALF = (0.09, 0.105, 0.1175)          # 0.18 W x 0.21 D x 0.235 H in the cap
HR = _R(H_ROT)
FACE_Z = 0.004                          # head-local z of the eye line (the face's centre)
CUFF_Z = (0.030, 0.074)                 # the turned-up ecru cuff at the brow (head-local z at the front)
CUFF_OUT = (0.011, 0.016)               # stands proud of the head, flaring a little at the fold
CUFF_TILT = 0.04                        # a watch cap sits lower at the back (over the ears and nape)


def _cuff_dz(v):
    """Head-local z offset of the cuff line at angle v (-pi/2 = the brow, +pi/2 = the nape)."""
    return -CUFF_TILT * 0.5 * (1 + math.sin(v))


def _head_deform(p):
    t = max(0.0, -p.z / H_HALF[2])
    return V((p.x * (1 - 0.26 * t * t), p.y * (1 - 0.06 * t * t) - 0.014 * t * t, p.z))


def _face_planes(p):
    """Flatten the front of the face below the brow into one broad plane (no features but the nose)."""
    if p.y >= 0:
        return p
    f = 0.10 * _smooth(0.02, -0.04, p.z) * _smooth(0.0, -0.06, p.y)
    return V((p.x, p.y * (1 - f), p.z))


def _head(kit):
    """The face (charcoal, in shadow) and the charcoal knit cap over it, cut at the cuff."""
    for part, scale, cut in (("face", 1.0, None), ("cap", 1.06, CUFF_Z[0] + 0.012)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=12, radius=1.0)
        if cut is not None:
            # cut along the tilted cuff line (the cuff hides the stepped edge)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z * H_HALF[2]
                                       < cut + _cuff_dz(math.atan2(v.co.y, v.co.x))], context="VERTS")
        for v in bm.verts:
            p = V((v.co.x * H_HALF[0], v.co.y * H_HALF[1], v.co.z * H_HALF[2]))
            if cut is not None:
                # knit cap: fuller than the skull, with a soft slouch at the top-back
                p = p * scale + V((0, 0.012, 0.016)) * max(0.0, p.z / H_HALF[2]) ** 2
            else:
                p = _face_planes(p)
            v.co = _head_deform(p)
        obj = kit._new_object("head " + part, bm, CLOTH, "metres", "xz")
        kit._place(obj, tuple(H_LOC), H_ROT)


def _head_ring_point(v, z, off):
    zz = max(-0.999, min(0.999, z / H_HALF[2]))
    u = math.asin(zz)
    base = V((H_HALF[0] * math.cos(u) * math.cos(v), H_HALF[1] * math.cos(u) * math.sin(v), H_HALF[2] * math.sin(u)))
    nrm = V((base.x / H_HALF[0] ** 2, base.y / H_HALF[1] ** 2, base.z / H_HALF[2] ** 2)).normalized()
    return _head_deform(base + nrm * off)


def _band(kit, z0, z1, t_out, slot, name, verts=24):
    """A full band round the head between head-local heights z0..z1 (at the brow; lower at the
    back, _cuff_dz), standing t_out = (bottom, top) proud of the head, with a rounded fold on top:
    a turned-up knit cuff."""
    bm = bmesh.new()
    rings = []
    prof = ((z0, t_out[0]), (z1 - 0.012, t_out[1]), (z1, t_out[1] - 0.005), (z1, -0.006), (z0, -0.006))
    for i in range(verts):
        v = -math.pi / 2 + 2 * math.pi * i / verts
        dz = _cuff_dz(v)
        rings.append([bm.verts.new(_head_ring_point(v, z + dz, off)) for z, off in prof])
    np_ = len(prof)
    for a, b in zip(rings, rings[1:] + rings[:1]):
        for k in range(np_):
            m = (k + 1) % np_
            bm.faces.new((a[k], a[m], b[m], b[k]))
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


def _extent(tree, c, d, reach=0.6):
    """How far the surface in tree reaches from c along direction d (0 if it does not)."""
    hit = tree.ray_cast(c + d * reach, -d, reach)
    return reach - hit[3] if hit[0] is not None else 0.0


def _smoothed(fn, n=72, passes=3):
    """fn(a) sampled round the circle, smoothed (so a measured radius has no saw teeth)."""
    vals = [fn(2 * math.pi * i / n) for i in range(n)]
    for _ in range(passes):
        vals = [(vals[i - 1] + 2 * vals[i] + vals[(i + 1) % n]) / 4 for i in range(n)]

    def f(a):
        x = (a % (2 * math.pi)) / (2 * math.pi) * n
        i = int(x) % n
        t = x - int(x)
        return vals[i] * (1 - t) + vals[(i + 1) % n] * t
    return f


def _ring_tube(kit, axis, rings_def, slot, name, verts=24, wall=0.01, gap=0.0):
    """An open garment edge (hem band, collar) round ``axis``. rings_def: [(centre(a), radius(a))]
    from the top ring down, as functions of the angle a round the axis (0 = +X, -pi/2 = front).
    gap > 0 leaves the front open by +-gap radians (a collar's opening)."""
    ex = V((1, 0, 0))
    ex = (ex - axis * ex.dot(axis)).normalized()
    ey = axis.cross(ex).normalized()
    if ey.y < 0:
        ey = -ey                                  # +ey = back, so a = -pi/2 is the front
    closed = gap <= 0
    n = verts if closed else verts + 1
    angs = [-math.pi / 2 + gap + (2 * math.pi - 2 * gap) * i / verts for i in range(n)]
    bm = bmesh.new()
    outer, inner = [], []
    for centre, radius in rings_def:
        o_ring, i_ring = [], []
        for a in angs:
            d = ex * math.cos(a) + ey * math.sin(a)
            c, r = centre(a), radius(a)
            o_ring.append(bm.verts.new(c + d * r))
            i_ring.append(bm.verts.new(c + d * (r - wall)))
        outer.append(o_ring)
        inner.append(i_ring)
    profile = outer + [inner[-1]] + list(reversed(inner))[1:]     # down the outside, up the inside
    loop = profile + [profile[0]]
    for ra, rb in zip(loop, loop[1:]):
        for i in range(n if closed else n - 1):
            m = (i + 1) % n
            bm.faces.new((ra[i], ra[m], rb[m], rb[i]))
    if not closed:
        for k in (0, n - 1):
            bm.faces.new([ring[k] for ring in profile])
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


def _to_load(p):
    """World point -> load-local (before the warp/displacement)."""
    return LR.transposed() @ (p - L_LOC)


# ------------------------------------------------------------------ build
def build(kit, cl):
    global EYE
    j = frame()
    J = lambda names, radii: {n: (j[n], r) for n, r in zip(names, radii)}  # noqa: E731
    h = L_HALF
    # Where each shoulder strap leaves the load's front face (7 cm above the shoulder).
    for s in ("l", "r"):
        STRAP_END[s] = min(h.z - 0.06, _to_load(j["shoulder_" + s]).z + 0.07)

    # Jacket: torso chain (hem to chest top) and two sleeve chains starting inside the
    # chest (separate chains: no flat Skin sheets at a 3-way branch).
    torso = cl.skin_body(kit, J(["pelvis", "belly", "chest", "chest_top"],
                                [(0.236, 0.17), (0.228, 0.175), (0.232, 0.18), (0.235, 0.15)]),
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
    # Trousers: two leg chains from inside the jacket.
    trousers = cl.skin_body(kit, J(["seat_l", "hip_l", "knee_l", "hemt_l", "seat_r", "hip_r", "knee_r", "hemt_r"],
                                   [0.10, 0.118, 0.09, 0.082, 0.10, 0.118, 0.09, 0.082]),
                            [("seat_l", "hip_l"), ("hip_l", "knee_l"), ("knee_l", "hemt_l"),
                             ("seat_r", "hip_r"), ("hip_r", "knee_r"), ("knee_r", "hemt_r")], CLOTH, name="trousers")
    # Jacket hem: a boxy, waist-length work jacket (as wide at the hem as at the chest) ending
    # in a short, straight band at the hip, square to the pitched torso (it rides up at the
    # back, as a jacket does when you bend). The first build's flared chore-coat skirt over
    # a narrow waist read from the front as an apron.
    # Per angle, the band hugs the jacket (it does not flare) and only clears the trousers.
    axis = (j["belly"] - j["pelvis"]).normalized()
    t_tree, l_tree = _bvh([torso]), _bvh([trousers])
    ex = (V((1, 0, 0)) - axis * axis.x).normalized()
    ey = axis.cross(ex).normalized()
    ey = ey if ey.y > 0 else -ey

    def _d(a):
        return ex * math.cos(a) + ey * math.sin(a)

    c_top, c_mid = j["pelvis"] + axis * 0.07, j["pelvis"] + axis * 0.03
    bot = lambda a: j["pelvis"] - axis * (0.04 - 0.02 * max(0.0, -math.sin(a)))  # noqa: E731  shorter in front
    r_top = _smoothed(lambda a: 0.97 * _extent(t_tree, c_top, _d(a)))
    r_bot = _smoothed(lambda a: max(1.0 * _extent(t_tree, c_mid, _d(a)), _extent(l_tree, bot(a), _d(a)) + 0.014))
    _ring_tube(kit, axis, [(lambda a: c_top, r_top), (bot, r_bot)], JACKET, "jacket hem", verts=28, wall=0.012)
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
    # Neck and face: charcoal, big plain planes, in the load's shadow; the ecru cuff turned
    # up at the brow is the only light on the head.
    j["neck_top"] = H_LOC + HR @ V((0, 0.012, -0.045))           # inside the skull: no ball under the chin
    cl.skin_body(kit, J(["neck_base", "neck", "neck_top"], [0.068, 0.06, 0.052]),
                 [("neck_base", "neck"), ("neck", "neck_top")], CLOTH, name="neck")
    # A low canvas collar lying open at the front (a jacket neckline, not a turtleneck).
    axis = (j["neck"] - j["neck_base"]).normalized()
    nb = j["neck_base"]
    _ring_tube(kit, axis, [(lambda a: nb + axis * 0.025, lambda a: 0.086),
                           (lambda a: nb - axis * 0.01, lambda a: 0.118),
                           (lambda a: nb - axis * 0.03, lambda a: 0.122)],
               JACKET, "collar", verts=18, wall=0.01, gap=math.radians(28))
    _head(kit)
    # one plane for the nose: a blunt wedge from under the cuff, sloping with the face
    kit.soft_box((0.028, 0.03, 0.07), tuple(H_LOC + HR @ V((0, -0.095, -0.008))), CLOTH, radius=0.012,
                 segments=10, rings=6, rot=(H_ROT[0] - 12, 0, H_ROT[2]), name="nose")
    _band(kit, CUFF_Z[0], CUFF_Z[1], CUFF_OUT, LIGHT, "cap cuff", verts=22)
    # Gloves.
    for s in ("l", "r"):
        _hand(kit, cl, j, s, "glove " + s)

    # The load.
    _pad(kit)
    # Binding: the pad's pale edge tape, folded over the top-front edge and down the
    # left-front edge (on the corner round, so it sits on the slab and draws its edge).
    bq = _path([(-h.x, -h.y, h.z), (h.x, -h.y, h.z), (h.x, -h.y, -h.z + 0.03)], 0.03)
    bpts, bnrm = [], []
    for q in bq:
        p, n = _load_point(q, 0.006)
        bpts.append(p)
        bnrm.append(n)
    _ribbon(kit, bpts, bnrm, 0.046, 0.012, LIGHT, "binding")
    # Shipping label on the top face (it faces up into the troffers and forward), askew, with print.
    lab_c, lab_a = (-0.03, 0.0), 7.0
    _patch(kit, lab_c, (0.21, 0.26), lab_a, 0.004, LIGHT, "label")
    ca, sa = math.cos(math.radians(lab_a)), math.sin(math.radians(lab_a))
    for du, dv, su, sv in ((-0.015, 0.085, 0.14, 0.014), (-0.03, 0.055, 0.11, 0.012), (-0.02, 0.028, 0.13, 0.012),
                           (0.0, -0.075, 0.15, 0.05)):
        cx = lab_c[0] + du * ca - dv * sa
        cy = lab_c[1] + du * sa + dv * ca
        _patch(kit, (cx, cy), (su, sv), lab_a, 0.0055, DARK, "label print", n=2)

    # Straps over the load: up the back, over the top, down the front face and INTO the shoulders.
    sleeve_tree = _bvh(sleeves)
    for s, x0 in (("l", STRAP_X), ("r", -STRAP_X)):
        z_end = STRAP_END[s]
        q = _path([(x0, -h.y * 0.2, -h.z), (x0, h.y, -h.z), (x0, h.y, h.z), (x0, -h.y, h.z), (x0, -h.y, z_end)], 0.03)
        pts, nrm = [], []
        for qq in q:
            p, n = _load_point(qq, STRAP_T / 2 + 0.002 + _binding_lift(qq))
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
        off = STRAP_T / 2 + 0.002 + _binding_lift(qq) if 0 < i < len(gq) - 1 else -0.01
        p, n = _load_point(qq, off)
        gp.append(p)
        gn.append(n)
    _ribbon(kit, gp, gn, STRAP_W, STRAP_T, DARK, "girth strap")
    # Cam buckle on the girth strap, right side.
    bp, bn = _load_point((-h.x, -0.05, GIRTH_Z), STRAP_T + 0.008)
    kit.box((0.05, 0.016, 0.075), tuple(bp), CHROME, bevel=0.004, rot=_rot_to(bn), name="cam buckle")

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
    kit.frame((0.085, 0.07), (0.055, 0.04), 0.014, tuple(loc + n * 0.032), CHROME, bevel=0.003,
              rot=_rot_to(n), name="buckle")

    lo = cl.floor_parts(kit)
    # Eye: the centre of the face at the eye line, after flooring.
    eye = H_LOC + HR @ _head_ring_point(-math.pi / 2, FACE_Z, 0.0)
    EYE = round(eye.z - lo, 3)
    cuff = H_LOC + HR @ _head_ring_point(-math.pi / 2, sum(CUFF_Z) / 2, CUFF_OUT[1])
    import bpy
    bpy.context.view_layer.update()
    ws = [o.matrix_world @ v.co for o in kit.parts for v in o.data.vertices]
    front = -min(p.y for p in ws if p.z > 1.0)
    back = max(p.y for p in ws if 0.4 <= p.z <= 1.95)
    load = [o for o in kit.parts if o.name.startswith("load")][0]
    lw = [load.matrix_world @ v.co for v in load.data.vertices]
    print("[delivery] load top %.3f (+0.04 bob %.3f), load x %.3f..%.3f; cuff front z %.3f; strap exits %s" % (
        max(p.z for p in lw), max(p.z for p in lw) + 0.04, min(p.x for p in lw), max(p.x for p in lw),
        cuff.z - lo, ", ".join("%s %.3f" % kv for kv in sorted(STRAP_END.items()))))
    print("[delivery] reach: front above 1 m %.3f, back 0.4-1.95 m %.3f" % (front, back))
    tris = {}
    for o in kit.parts:
        key = o.name.rstrip(".0123456789")
        tris[key] = tris.get(key, 0) + sum(len(p.vertices) - 2 for p in o.data.polygons)
    print("[delivery] floor shift %.3f, eye %.3f (front y %.3f), tris %d: %s" % (
        lo, EYE, eye.y, sum(tris.values()),
        ", ".join("%s %d" % kv for kv in sorted(tris.items(), key=lambda kv: -kv[1]))))
    kit.no_collider()
