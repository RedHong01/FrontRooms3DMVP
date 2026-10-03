"""Giant D — "Delivery" as a squeezed giant (Documentation/research/hunter/11_squeezed_giant.md;
direction D in 10_hunter_directions.md §6). Placeholder header; rewritten below once the poses settle.
"""

import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

NAME = "Giant_D_Delivery"
TITLE = "Delivery (giant)"
PITCH = ("A mover the size of the room, folded under a rope-tied moving-blanket bundle that is jammed against "
         "the ceiling tiles; the straps run into his shoulders and his face hangs in its shadow at your eye line.")
SMOOTH_ANGLE = 60.0
POSES = {"low": {"top": 2.37, "halfWidth": 0.80}, "std": {"top": 2.86, "halfWidth": 0.80},
         "door": {"top": 2.9, "door": True}, "tall": {"top": 3.30, "halfWidth": 0.85}}
SIL_FRAME = (2.4, 3.6)
EYE = {"low": 1.45, "std": 1.68, "door": 1.45, "tall": 2.90}   # replaced in build() by the measured face centre

PAD = "Creature_PadNavy"
JACKET = "Creature_CanvasBrown"
CLOTH = "Prop_FabricCharcoal"
LIGHT = "Prop_Paper"
DARK = "Prop_Vinyl"
CHROME = "Prop_Chrome"

V = Vector


def _E(rot):
    return Euler([math.radians(a) for a in rot], "XYZ")


def _R3(rot):
    return _E(rot).to_matrix()


def _R4(rot):
    return _E(rot).to_matrix().to_4x4()


def _T(v):
    return Matrix.Translation(V(v))


def _deg(m):
    return tuple(math.degrees(a) for a in m.to_3x3().normalized().to_euler("XYZ"))


def _rot_to(n, axis=(0, -1, 0)):
    """Euler degrees turning `axis` onto n (for parts that face -Y or +Z)."""
    e = V(axis).rotation_difference(n).to_euler()
    return tuple(math.degrees(a) for a in e)


def _smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def _basis_euler(xaxis, zaxis):
    z = zaxis.normalized()
    x = (xaxis - z * xaxis.dot(z)).normalized()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed()
    return tuple(math.degrees(a) for a in m.to_euler("XYZ"))


# ================================================================== body
# A heavy adult scaled ~1.75x (a 1.80 m person -> ~3.2 m standing with the load). Lengths in metres.
BODY = {
    "ankle": 0.21, "shin": 0.63, "thigh": 0.71,
    "hip_half": 0.19, "hip_drop": 0.08, "hip_back": 0.03,
    "seg": (0.30, 0.34, 0.30),                 # pelvis->belly->chest->top (the top of the chest, at the collar)
    "shoulder": (0.33, 0.04, -0.07),           # shoulder joint in the top frame
    "armin": (0.19, 0.03, -0.04),              # inside the chest: the sleeves start here
    "neck": 0.17, "head": (0.0, -0.035, 0.17),
    "upper": 0.54, "fore": 0.48,
}
G = 1.65            # the base mover's costume, blown up with him (sleeves, trousers, collar, straps)
GH = 1.5            # gloves: ~0.32 m wrist to fingertip
GB = 1.7            # boots: ~0.45 m long
HS = 1.62           # head: 0.38 m tall in the cap (a small head on a massive frame)

# Per-pose parameters. Rotations are degrees (X pitch forward +, Y roll: + lowers his left, Z yaw).
#   root    pelvis centre (world); yaw turns the whole body; pelvis/spine/neck/head are relative rotations
#   feet    side -> ((x, y), yaw, pitch, roll) of each boot sole (world)
#   arms    side -> wrist placement and hand pose (see _arm_targets)
#   load    rel: offset/rotation in the top-of-chest frame; or world: loc/rot
#   arms    thigh: wrist on top of that side's thigh (t along hip->knee); hang: wrist = shoulder + offset
#           (body axes); point: wrist at a body-axes point; dir/palm: finger and curl directions (body axes)
POSE = {
    # Under the 2.9 m ceiling: a porter's carry. The back is near level, the bundle stands on it and is
    # jammed into the tiles; the head cranes out in front under the bundle's lip, at your eye line.
    "std": {
        "root": (0.0, 0.22, 1.24), "yaw": 0.0, "pelvis": (50, 0, 0),
        "spine": ((8, 0, 0), (8, 1, 0), (4, 0, 0)),
        "neck": (30, 0, 0), "head": (-80, 0, 6), "shrug": 0.08,
        "feet": {"l": ((0.30, -0.52), -10, 0, 0), "r": ((-0.30, 0.62), 12, 16, 0)},
        "knee_out": {"l": 0.5, "r": 0.35},
        "arms": {"l": {"thigh": 0.95, "up": 0.0, "out": 0.04, "pole": (0.55, 0.5, 0.75), "curl": 0.6},
                 "r": {"point": (-0.42, -0.88, 1.86), "dir": (-0.05, 0.25, 1.0), "palm": (0, 1, 0),
                       "pole": (-0.42, 0.1, -0.9), "curl": 0.3}},
        "load": {"rel": (0.05, 0.833, 0.105), "rot": (-66, -6, 0)},
        "ceiling": 2.85, "wall": None,
    },
    # Under the 2.4 m ceiling: the deepest fold. Knees high and splayed, the back humped under a bundle
    # squashed to three quarters of its height, the head hung forward under it, a fist down on the carpet.
    "low": {
        "root": (0.0, 0.32, 0.78), "yaw": 0.0, "pelvis": (56, 0, 0),
        "spine": ((8, 0, 0), (8, 1, 0), (6, 0, 0)),
        "neck": (-10, 0, 0), "head": (-55, 0, 6), "shrug": 0.07,
        "feet": {"l": ((0.42, -0.30), -20, 0, 0), "r": ((-0.42, 0.42), 18, 24, 0)},
        "knee_out": {"l": 0.6, "r": 0.5},
        "arms": {"l": {"point": (0.42, -0.62, 0.27), "dir": (0, -0.25, -1), "palm": (0, 1, 0),
                       "pole": (0.6, 0.2, 0.4), "curl": 1.0},
                 "r": {"thigh": 0.9, "up": 0.0, "out": 0.04, "pole": (-0.55, 0.5, 0.75), "curl": 0.6}},
        "load": {"rel": (0.06, 0.81, -0.06), "rot": (-76, -8, 0)},
        "ceiling": 2.365, "wall": None,
    },
    # A 5.4 m zone: he straightens. Nearly upright, a slight stoop, the bundle riding high on his
    # shoulders and tipped forward over his head (the base's carry, at full size).
    "tall": {
        "root": (0.0, 0.04, 1.60), "yaw": 0.0, "pelvis": (6, 0, 0),
        "spine": ((5, 0, 0), (5, 0, 0), (4, 0, 0)),
        "neck": (8, 0, 0), "head": (-14, 0, 4), "shrug": 0.04,
        "feet": {"l": ((0.24, -0.16), -8, 0, 0), "r": ((-0.24, 0.12), 8, 6, 0)},
        "knee_out": {"l": 0.2, "r": 0.2},
        "arms": {"l": {"hang": (0.10, -0.10, -0.98), "dir": (0.05, -0.1, -1), "palm": (-1, 0, 0),
                       "pole": (1.0, 0.6, 0.0), "curl": 0.35},
                 "r": {"hang": (-0.10, -0.08, -0.98), "dir": (-0.05, -0.1, -1), "palm": (1, 0, 0),
                       "pole": (-1.0, 0.6, 0.0), "curl": 0.35}},
        "load": {"rel": (0.05, 0.55, -0.15), "rot": (14, -6, 0)},
        "ceiling": None, "wall": None,
    },
}
POSE["door"] = dict(POSE["std"])


def _ik(a, target, l1, l2, pole):
    """Two-bone IK: (mid, end). The end is clamped to reach; the mid bends toward `pole`."""
    d = target - a
    dist = max(1e-4, d.length)
    u = d / dist
    reach = l1 + l2 - 1e-3
    if dist > reach:
        print("[giant_d] IK: target %.3f beyond reach %.3f" % (dist, reach))
        end = a + u * reach
        dist = reach
    else:
        end = target.copy()
    x = (l1 * l1 - l2 * l2 + dist * dist) / (2 * dist)
    h = math.sqrt(max(0.0, l1 * l1 - x * x))
    perp = pole - u * pole.dot(u)
    perp = perp.normalized() if perp.length > 1e-6 else V((0, -1, 0))
    return a + u * x + perp * h, end


# Boots in sole space (forward = -Y), the base's boot scaled by GB.
BOOT_J = {"ankle": V((0, 0.045, 0.125)) * GB, "anklelow": V((0, 0.03, 0.08)) * GB}
_SOLE_PTS = [V((sx * 0.112, sy, 0.0)) for sx in (-1, 1) for sy in (-0.286, 0.208)]


def _boot_frame(xy, yaw, pitch, roll):
    r = _R4((pitch, roll, yaw))
    lo = min((r @ p).z for p in _SOLE_PTS)
    return _T((xy[0], xy[1], -lo)) @ r


def skeleton(P):
    j, F = {}, {}
    yaw = _R4((0, 0, P.get("yaw", 0.0)))
    root = _T(P["root"]) @ yaw @ _R4(P["pelvis"])
    F["pelvis"] = root
    j["pelvis"] = root.translation.copy()
    m = root
    for name, length, rot in zip(("belly", "chest", "top"), BODY["seg"], P["spine"]):
        m = m @ _T((0, 0, length)) @ _R4(rot)
        F[name] = m
        j[name] = m.translation.copy()
    top = F["top"]
    sh, ai = BODY["shoulder"], BODY["armin"]
    for s, sg in (("l", 1), ("r", -1)):
        j["shoulder_" + s] = top @ V((sg * sh[0], sh[1], sh[2] + P.get("shrug", 0.0)))
        j["armin_" + s] = top @ V((sg * ai[0], ai[1], ai[2]))
    nb = top @ _T((0, -0.02, 0.03)) @ _R4(P["neck"])
    F["neck"] = nb
    j["neck_base"] = (top @ _T((0, -0.01, -0.06))).translation.copy()
    j["neck"] = (nb @ _T((0, 0, BODY["neck"] * 0.5))).translation.copy()
    nk = nb @ _T((0, 0, BODY["neck"]))
    H = nk @ _R4(P["head"]) @ _T(BODY["head"])
    F["head"] = H
    j["neck_top"] = (H @ _T(V((0, 0.012, -0.045)) * HS)).translation.copy()
    pel = F["pelvis"]
    for s, sg in (("l", 1), ("r", -1)):
        j["hip_" + s] = pel @ V((sg * BODY["hip_half"], BODY["hip_back"], -BODY["hip_drop"]))
        j["seat_" + s] = pel @ V((sg * BODY["hip_half"] * 0.6, -0.01, 0.10))
        xy, fy, fp, fr = P["feet"][s]
        bf = _boot_frame(xy, fy, fp, fr)
        F["boot_" + s] = bf
        j["ankle_" + s] = bf @ BOOT_J["ankle"]
        j["anklelow_" + s] = bf @ BOOT_J["anklelow"]
        ko = P.get("knee_out", {}).get(s, 0.3)
        pole = yaw.to_3x3() @ V((sg * ko, -1, 0.0))
        if "knee_pole" in P and s in P["knee_pole"]:
            pole = V(P["knee_pole"][s])
        j["knee_" + s], _end = _ik(j["hip_" + s], j["ankle_" + s], BODY["thigh"], BODY["shin"], pole)
        j["hemt_" + s] = j["knee_" + s].lerp(j["ankle_" + s], 0.80)
        j["shin_" + s] = j["knee_" + s].lerp(j["ankle_" + s], 0.55)
    # Arms: wrist targets, IK, and the hand pose (finger direction d, palm/curl direction m).
    hands = {}
    for s, sg in (("l", 1), ("r", -1)):
        a = P["arms"][s]
        if "thigh" in a:
            hp, kn = j["hip_" + s], j["knee_" + s]
            ax = (kn - hp).normalized()
            up = V((0, 0, 1)) - ax * ax.z
            up = up.normalized()
            side = up.cross(ax)
            side = side if side.dot(yaw.to_3x3() @ V((sg, 0, 0))) > 0 else -side
            base = hp.lerp(kn, a["thigh"])
            wrist = base + up * (0.19 + a.get("up", 0.0)) + side * a.get("out", 0.0) - ax * 0.10
            d = (ax * 0.75 - up * 0.25).normalized()
            m = -up
        else:
            Y = yaw.to_3x3()
            if "hang" in a:
                wrist = j["shoulder_" + s] + Y @ V(a["hang"])
            elif "point" in a:
                wrist = Y @ V(a["point"])
            else:
                wrist = V(a["wrist"])
            d = (Y @ V(a["dir"])).normalized()
            m = (Y @ V(a["palm"])).normalized()
        pole = yaw.to_3x3() @ V(a["pole"]) if not a.get("pole_world") else V(a["pole"])
        el, wr = _ik(j["shoulder_" + s], wrist, BODY["upper"], BODY["fore"], pole)
        j["elbow_" + s], j["wrist_" + s] = el, wr
        j["sleeve_" + s] = el.lerp(wr, 0.86)
        j["wristin_" + s] = el.lerp(wr, 0.74)
        m = (m - d * m.dot(d)).normalized()
        hands[s] = (wr, d, m, a.get("curl", 0.3))
    return j, F, hands


# ================================================================== the head (base, scaled by HS)
H_HALF = (0.09 * HS, 0.105 * HS, 0.1175 * HS)
FACE_Z = 0.004 * HS
CUFF_Z = (0.030 * HS, 0.074 * HS)
CUFF_OUT = (0.011 * HS, 0.016 * HS)
CUFF_TILT = 0.04 * HS


def _cuff_dz(v):
    return -CUFF_TILT * 0.5 * (1 + math.sin(v))


def _head_deform(p):
    t = max(0.0, -p.z / H_HALF[2])
    return V((p.x * (1 - 0.26 * t * t), p.y * (1 - 0.06 * t * t) - 0.014 * HS * t * t, p.z))


def _face_planes(p):
    if p.y >= 0:
        return p
    f = 0.10 * _smooth(0.02 * HS, -0.04 * HS, p.z) * _smooth(0.0, -0.06 * HS, p.y)
    return V((p.x, p.y * (1 - f), p.z))


def _head(kit, H):
    loc, rot = tuple(H.translation), _deg(H)
    for part, scale, cut in (("face", 1.0, None), ("cap", 1.06, CUFF_Z[0] + 0.012 * HS)):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=18, v_segments=11, radius=1.0)
        if cut is not None:
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z * H_HALF[2]
                                       < cut + _cuff_dz(math.atan2(v.co.y, v.co.x))], context="VERTS")
        for v in bm.verts:
            p = V((v.co.x * H_HALF[0], v.co.y * H_HALF[1], v.co.z * H_HALF[2]))
            if cut is not None:
                p = p * scale + V((0, 0.012, 0.016)) * HS * max(0.0, p.z / H_HALF[2]) ** 2
            else:
                p = _face_planes(p)
            v.co = _head_deform(p)
        obj = kit._new_object("head " + part, bm, CLOTH, "metres", "xz")
        kit._place(obj, loc, rot)


def _head_ring_point(v, z, off):
    zz = max(-0.999, min(0.999, z / H_HALF[2]))
    u = math.asin(zz)
    base = V((H_HALF[0] * math.cos(u) * math.cos(v), H_HALF[1] * math.cos(u) * math.sin(v), H_HALF[2] * math.sin(u)))
    nrm = V((base.x / H_HALF[0] ** 2, base.y / H_HALF[1] ** 2, base.z / H_HALF[2] ** 2)).normalized()
    return _head_deform(base + nrm * off)


def _band(kit, H, z0, z1, t_out, slot, name, verts=24):
    bm = bmesh.new()
    rings = []
    k = 0.012 * HS
    prof = ((z0, t_out[0]), (z1 - k, t_out[1]), (z1, t_out[1] - 0.005 * HS), (z1, -0.006 * HS), (z0, -0.006 * HS))
    for i in range(verts):
        v = -math.pi / 2 + 2 * math.pi * i / verts
        dz = _cuff_dz(v)
        rings.append([bm.verts.new(_head_ring_point(v, z + dz, off)) for z, off in prof])
    np_ = len(prof)
    for a, b in zip(rings, rings[1:] + rings[:1]):
        for kk in range(np_):
            m = (kk + 1) % np_
            bm.faces.new((a[kk], a[m], b[m], b[kk]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = kit._new_object(name, bm, slot, "metres", "xz")
    kit._place(obj, tuple(H.translation), _deg(H))
    return obj


# ================================================================== the load: a moving-blanket bundle
# A quilted moving blanket wrapped round something lumpy (a chair-back high on its left end, a hard
# corner low at the front right), tied with a pale cotton rope (two turns round its girth, one loop the
# long way) and carried on two black cargo straps. Soft corners (radius 0.17), faces bowing out between
# the ties, diamond quilting as stitch grooves, one blanket edge with its pale binding running across the
# front face and a loose corner hanging off the left end. Local axes: x across his shoulders, -y its front
# (the face over his head), z up his spine.
LH = V((0.64, 0.40, 0.47))
LRAD = 0.17
L_PUFF = 0.035
Q_CELL = 0.30            # diamond quilting: stitch lines every Q_CELL along u+v and u-v
Q_DEPTH = 0.034
Q_W = 0.045
STEP = 0.022             # the blanket's overlapping edge: the top layer stands this proud
# The edge on the front face, as a polyline in (x, z); the layer on its -x side lies over the other.
EDGE = [(0.16, 0.62), (0.06, 0.30), (-0.16, 0.06), (-0.34, -0.22), (-0.48, -0.60)]
# Gathers: radial folds where the ropes and straps pull the blanket in (face axis, sign, (a, b), folds,
# radius, amplitude). (a, b) are the face's two other axes in order.
GATHERS = [(0, -1, (-0.10, -0.06), 7, 0.36, 0.018), (0, 1, (-0.10, -0.06), 6, 0.34, 0.016)]
ROPE_R = 0.021
ZG = -0.06               # girth rope height (load-local z)
YL = -0.10               # the long rope loop's plane (load-local y)
STRAP_W, STRAP_T = 0.09, 0.016
STRAP_X = 0.36           # load-local x of the two shoulder straps
STRAP_END = {}
BUCKLE = 0.014           # amplitude of the compression folds under the ceiling
CEIL_GAP = 0.028         # the pad squashes to this far under the ceiling; straps and rope fill the gap


Q_STEP = 0.05            # grid step on the flat faces; Q_CELL is a multiple of 2 * Q_STEP, so the stitch
                         # lines run through grid points (a chain of dimples, like real quilting)


def _lrows(i, step=Q_STEP):
    h = LH[i]
    inner = h - LRAD
    rnd = [inner + LRAD * math.tan(math.radians(22.5))]
    k = int(inner / step - 1e-6)
    mid = [m * step for m in range(-k, k + 1)]
    if inner - mid[-1] > step * 0.3:
        mid = [-inner] + mid + [inner]
    else:
        mid = [-inner] + mid[1:-1] + [inner]
    return [-h] + [-r for r in reversed(rnd)] + mid + rnd + [h]


def _rbox(q):
    inner = [LH[i] - LRAD for i in range(3)]
    c = V([max(-inner[i], min(inner[i], q[i])) for i in range(3)])
    d = V(q) - c
    n = d.normalized() if d.length > 1e-9 else V((0, 0, 1))
    return c + n * LRAD, n


def _gs(t, cell, w):
    """Gaussian stitch line every `cell` along t."""
    d = abs(t / cell - round(t / cell)) * cell
    return math.exp(-(d / w) ** 2)


def _cinch(p, n):
    h = LH
    cin = 0.0
    # girth rope (round the four sides)
    if abs(n.z) < 0.8:
        cin = max(cin, math.exp(-((p.z - ZG) / 0.07) ** 2))
    # long rope loop (top, ends, bottom) in the plane y = YL
    if abs(n.y) < 0.8:
        cin = max(cin, 0.8 * math.exp(-((p.y - YL) / 0.07) ** 2))
    # shoulder straps in the planes x = +-STRAP_X (not on the front face below their exit)
    if abs(n.x) < 0.8:
        for s, sx in (("l", 1), ("r", -1)):
            g = math.exp(-((p.x - sx * STRAP_X) / 0.07) ** 2)
            if n.y < -0.7:
                g *= _smooth(STRAP_END.get(s, -h.z) - 0.08, STRAP_END.get(s, -h.z), p.z)
            cin = max(cin, g)
    return cin


def _edge_sd(x, z):
    """Signed distance (front face) to the blanket edge; > 0 on its -x side (the top layer)."""
    best, sgn = 1e9, 1.0
    for (x0, z0), (x1, z1) in zip(EDGE, EDGE[1:]):
        dx, dz = x1 - x0, z1 - z0
        t = max(0.0, min(1.0, ((x - x0) * dx + (z - z0) * dz) / (dx * dx + dz * dz)))
        ex, ez = x - (x0 + dx * t), z - (z0 + dz * t)
        d = math.hypot(ex, ez)
        if d < best:
            best = d
            sgn = 1.0 if (dx * ez - dz * ex) > 0 else -1.0
    return best * sgn


def _ldisp(p, n, quilt=True):
    k = max(range(3), key=lambda i: abs(n[i]))
    a, b = [i for i in range(3) if i != k]
    w = max(0.0, 1 - (p[a] / LH[a]) ** 2) * max(0.0, 1 - (p[b] / LH[b]) ** 2)
    disp = L_PUFF * w
    cin = _cinch(p, n)
    disp -= (0.022 + L_PUFF * w * 0.9) * cin
    if n.y < -0.3:
        disp += STEP * _smooth(-0.004, 0.03, _edge_sd(p.x, p.z)) * _smooth(0.3, 0.7, -n.y)
    for gk, gs, (ga, gb), nf, rad, amp in GATHERS:
        if n[gk] * gs > 0.5:
            ia, ib = [i for i in range(3) if i != gk]
            da, db = p[ia] - ga, p[ib] - gb
            r = math.hypot(da, db)
            env = _smooth(0.04, 0.10, r) * (1 - _smooth(rad * 0.45, rad, r))
            disp += amp * env * math.cos(nf * math.atan2(db, da) + 0.7 * gk)
    if quilt:
        fade = _smooth(0.86, 0.97, abs(n[k])) * (1 - 0.6 * cin)
        u, v = p[a], p[b]
        g = max(_gs(u + v, Q_CELL, Q_W), _gs(u - v + Q_CELL / 2, Q_CELL, Q_W))
        disp -= Q_DEPTH * g * fade
    return disp


def _lump(p, n):
    """The furniture under the pad: a taller left end (a chair back), a slumped right end, a hard
    corner low at the front right, and a slow unevenness everywhere."""
    x, y, z = p
    t = _smooth(-LH.z, LH.z, z)
    dz = 0.12 * t * _smooth(0.05, 0.55, x) * (0.75 + 0.25 * _smooth(0.3, -0.3, y))
    dz -= 0.06 * t * _smooth(-0.15, -0.62, x)
    k = math.exp(-(((x + 0.52) / 0.28) ** 2 + ((y + 0.34) / 0.3) ** 2 + ((z + 0.38) / 0.3) ** 2))
    w = 0.008 * math.sin(3.3 * x + 1.7 * z + 0.4) * math.cos(2.6 * y - 1.1 * x) + 0.004 * math.sin(5.1 * z - 2.3 * x)
    return V((x - 0.035 * k, y - 0.06 * k, z + dz - 0.035 * k)) + n * w


def _lsurf(q, quilt=False):
    """Box-surface point q -> (load-local surface point, local normal)."""
    q = V(q)
    p, n = _rbox(q)
    p = p + n * _ldisp(p, n, quilt)
    return _lump(p, n), n


class Warp:
    """World-space squash of the load against the ceiling (and the wall above a door)."""

    def __init__(self, ceiling=None, wall=None, centre=V((0, 0, 0)), band=0.26, bulge=(0.05, 0.15), wall_band=0.16):
        self.T, self.Y, self.c, self.b, self.bulge, self.wb = ceiling, wall, centre, band, bulge, wall_band

    def __call__(self, p):
        x, y, z = p
        fx = fy = 1.0
        if self.T is not None:
            z0 = self.T - self.b
            if z > z0:
                z = z0 + self.b * math.tanh((z - z0) / self.b)
            k = _smooth(self.T - 0.62, self.T - 0.14, z)       # the pressed pad bellies out under the tiles
            fx += self.bulge[0] * k
            fy += self.bulge[1] * k
            # and buckles in soft horizontal folds just under the contact
            env = _smooth(self.T - 0.40, self.T - 0.24, z) * (1 - _smooth(self.T - 0.08, self.T - 0.02, z))
            if env > 0:
                th = math.atan2(y - self.c.y, x - self.c.x)
                ph = 1.5 * math.sin(2 * th) + 0.7 * math.sin(5 * th + 1.0)
                buck = BUCKLE * env * math.sin(2 * math.pi * (self.T - z) / 0.15 + ph)
                rx, ry = x - self.c.x, y - self.c.y
                rl = math.hypot(rx, ry)
                if rl > 1e-6:
                    x += rx / rl * buck
                    y += ry / rl * buck
        x = self.c.x + (x - self.c.x) * fx
        y = self.c.y + (y - self.c.y) * fy
        if self.Y is not None:
            y1 = self.Y + self.wb
            if y < y1:
                y = y1 - self.wb * math.tanh((y1 - y) / self.wb)
        return V((x, y, z))

    def normal(self, p, n, eps=1e-3):
        w0 = self(p)
        cols = [(self(p + V(e) * eps) - w0) / eps for e in ((1, 0, 0), (0, 1, 0), (0, 0, 1))]
        J = Matrix((cols[0], cols[1], cols[2])).transposed()
        try:
            return (J.inverted().transposed() @ n).normalized()
        except ValueError:
            return n


class Load:
    def __init__(self, M, warp):
        self.M, self.R, self.W = M, M.to_3x3().normalized(), warp
        self.Minv = M.inverted()

    def point(self, q, off=0.0, quilt=False, clear=0.0):
        """World point (warped) and normal on the load surface for box point q, lifted by off; straps
        and rope on top are pressed flat between the pad and the tiles."""
        p, n = _lsurf(q, quilt)
        pw, nw = self.M @ p, (self.R @ n).normalized()
        nw2 = self.W.normal(pw, nw)
        out = self.W(pw) + nw2 * off
        if self.W.T is not None:
            out.z = min(out.z, self.W.T + CEIL_GAP - 0.004 - clear)
        return out, nw2

    def to_local(self, p):
        return self.Minv @ p


def _pad(kit, L):
    bm = bmesh.new()
    h = LH
    rows = [_lrows(i) for i in range(3)]
    cache = {}

    def vert(q):
        key = tuple(round(c, 6) for c in q)
        v = cache.get(key)
        if v is None:
            p, n = _lsurf(q, True)
            v = bm.verts.new(L.W(L.M @ p))
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
                for jj in range(len(rows[b]) - 1):
                    try:
                        bm.faces.new((grid[i][jj], grid[i + 1][jj], grid[i + 1][jj + 1], grid[i][jj + 1]))
                    except ValueError:
                        pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object("load", bm, PAD, "metres", "xz")


def _path(corners, step=0.03):
    out = []
    for a, b in zip(corners, corners[1:]):
        a, b = V(a), V(b)
        n = max(1, int(math.ceil((b - a).length / step)))
        out += [a.lerp(b, i / n) for i in range(n)]
    out.append(V(corners[-1]))
    return out


def _ribbon(kit, pts, nrm, width, thick, slot, name, round_=False):
    """Flat webbing along pts, its face on the normals nrm (round_: a soft elliptical section)."""
    bm = bmesh.new()
    rings = []
    n = len(pts)
    sec = ([(-1, -1), (1, -1), (1, 1), (-1, 1)] if not round_ else
           [(math.cos(a), math.sin(a)) for a in [2 * math.pi * i / 6 for i in range(6)]])
    for k in range(n):
        t = (pts[min(k + 1, n - 1)] - pts[max(k - 1, 0)]).normalized()
        nn = (nrm[k] - t * nrm[k].dot(t)).normalized()
        s = t.cross(nn).normalized()
        w = width(k / (n - 1)) if callable(width) else width
        rings.append([bm.verts.new(pts[k] + s * sx * w / 2 + nn * sy * thick / 2) for sx, sy in sec])
    m = len(sec)
    for a, b in zip(rings, rings[1:]):
        for i in range(m):
            jj = (i + 1) % m
            bm.faces.new((a[i], a[jj], b[jj], b[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _crease(kit, pts, nrm, width, height, slot, name):
    """A soft fold ridge lying on a surface along pts (tapering to nothing at both ends)."""
    bm = bmesh.new()
    n = len(pts)
    prof = [(-1.0, 0.0), (-0.5, 0.75), (0.0, 1.0), (0.5, 0.75), (1.0, 0.0)]
    rings = []
    for k in range(n):
        t = (pts[min(k + 1, n - 1)] - pts[max(k - 1, 0)]).normalized()
        nn = (nrm[k] - t * nrm[k].dot(t)).normalized()
        s = t.cross(nn).normalized()
        taper = math.sin(math.pi * (0.04 + 0.92 * k / (n - 1)))
        rings.append([bm.verts.new(pts[k] + s * u * width / 2 * (0.6 + 0.4 * taper) + nn * (v * height * taper - 0.006))
                      for u, v in prof])
    for a, b in zip(rings, rings[1:]):
        for i in range(len(prof) - 1):
            bm.faces.new((a[i], a[i + 1], b[i + 1], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _rope(kit, L, qs, name, off=0.0, step=0.085):
    pts = []
    for q in _path(qs, step):
        p, _n = L.point(q, ROPE_R + 0.004 + off, clear=ROPE_R)
        pts.append(p)
    return kit.tube(pts, ROPE_R, LIGHT, verts=5, name=name)


def _patch(kit, L, k, sign, centre, size, angle, off, slot, name, n=6):
    """A label-like patch conforming to the load face (axis k, side sign); centre/size in the face's
    two other axes (in order), rotated by angle degrees."""
    a, b = [i for i in range(3) if i != k]
    bm = bmesh.new()
    ca, sa = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    grid = []
    for i in range(n + 1):
        row = []
        for jj in range(n + 1):
            u = (i / n - 0.5) * size[0]
            v = (jj / n - 0.5) * size[1]
            q = [0.0, 0.0, 0.0]
            q[k] = sign * LH[k]
            q[a] = centre[0] + u * ca - v * sa
            q[b] = centre[1] + u * sa + v * ca
            p, _nn = L.point(q, off, quilt=False)
            row.append(bm.verts.new(p))
        grid.append(row)
    for i in range(n):
        for jj in range(n):
            bm.faces.new((grid[i][jj], grid[i + 1][jj], grid[i + 1][jj + 1], grid[i][jj + 1]))
    bm.normal_update()
    bm.faces.ensure_lookup_table()
    out = L.R @ V([sign if i == k else 0 for i in range(3)])
    if bm.faces[len(bm.faces) // 2].normal.dot(out) < 0:
        for f in bm.faces:
            f.normal_flip()
    return kit._new_object(name, bm, slot, "metres", "xz")


def _flap(kit, L, q0, q1, length, sway, name):
    """The blanket's loose corner hanging off the bundle between box points q0..q1, with its binding."""
    top = []
    for q in _path([q0, q1], 0.045):
        p, n = L.point(q, -0.008)
        top.append((p, n))
    ncol, nrow = len(top), 10
    bm = bmesh.new()
    grid = []
    down = V((0, 0, -1))
    edge = []
    for i, (p, n) in enumerate(top):
        u = i / (ncol - 1)
        ln = length * (0.12 + 0.88 * _smooth(0.0, 1.0, max(0.0, 1 - abs(u - 0.72) / 0.72)))
        col = []
        out = L.R @ V((0, -1, 0))
        out = V((out.x, out.y, 0)).normalized()
        for r in range(nrow + 1):
            t = r / nrow
            wave = (0.05 * math.sin(math.pi * 3.0 * u + 0.6) + 0.025 * math.sin(math.pi * 5.0 * u)) * t ** 0.7
            pt = p + down * ln * t + out * (0.04 * t + wave + 0.16 * t ** 3) + V(sway) * t * t
            col.append(bm.verts.new(pt))
        grid.append(col)
        edge.append(col[-1].co.copy())
    for i in range(ncol - 1):
        for r in range(nrow):
            bm.faces.new((grid[i][r], grid[i + 1][r], grid[i + 1][r + 1], grid[i][r + 1]))
    bm.normal_update()
    edge_pts = [grid[0][r].co.copy() for r in range(nrow + 1)] + edge[1:]
    obj = kit._new_object(name, bm, PAD, "metres", "xz")
    sol = obj.modifiers.new("solid", "SOLIDIFY")
    sol.thickness = 0.05
    sol.offset = 0.0
    # binding along the free edge and up the leading side
    nrm = []
    for k in range(len(edge_pts)):
        a = edge_pts[max(0, k - 1)]
        b = edge_pts[min(len(edge_pts) - 1, k + 1)]
        t = (b - a).normalized()
        side = t.cross(V((0, 0, 1)))
        nrm.append(side.normalized() if side.length > 1e-4 else V((1, 0, 0)))
    _ribbon(kit, edge_pts, nrm, 0.07, 0.045, LIGHT, name + " binding", round_=True)
    return obj


# ================================================================== garments (base helpers)
def _section(obj, centre, axis, slab=0.03, rmax=0.35):
    ex = V((1, 0, 0))
    ey = axis.cross(ex).normalized()
    rx = ry = 0.0
    for v in obj.data.vertices:
        d = v.co - centre
        if abs(d.dot(axis)) < slab and (d - axis * d.dot(axis)).length < rmax:
            rx = max(rx, abs(d.dot(ex)))
            ry = max(ry, abs(d.dot(ey)))
    return rx, ry


def _tube_open(kit, top, bot, r_top, r_bot, slot, name, verts=20, wall=0.01):
    axis = (top - bot).normalized()
    ex = V((1, 0, 0))
    ex = ex - axis * ex.dot(axis)
    if ex.length < 1e-3:
        ex = V((0, 1, 0)) - axis * axis.y
    ex = ex.normalized()
    ey = axis.cross(ex).normalized()
    bm = bmesh.new()
    rings = []
    for c, (rx, ry), off in ((top, r_top, 0.0), (bot, r_bot, 0.0), (bot, r_bot, -wall), (top, r_top, -wall)):
        ring = []
        for i in range(verts):
            a = 2 * math.pi * i / verts
            ring.append(bm.verts.new(c + ex * math.cos(a) * (rx + off) + ey * math.sin(a) * (ry + off)))
        rings.append(ring)
    for k in range(3):
        a, b = rings[k], rings[k + 1]
        for i in range(verts):
            m = (i + 1) % verts
            bm.faces.new((a[i], a[m], b[m], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _section_r(obj, centre, axis, slab=0.03, rmax=0.35):
    """Max radius of obj's vertices round axis within a slab (for round sleeve cuffs)."""
    r = 0.0
    for v in obj.data.vertices:
        d = v.co - centre
        if abs(d.dot(axis)) < slab:
            rr = (d - axis * d.dot(axis)).length
            if rr < rmax:
                r = max(r, rr)
    return r


def _extent(tree, c, d, reach=0.9):
    hit = tree.ray_cast(c + d * reach, -d, reach)
    return reach - hit[3] if hit[0] is not None else 0.0


def _smoothed(fn, n=72, passes=3):
    vals = [fn(2 * math.pi * i / n) for i in range(n)]
    for _ in range(passes):
        vals = [(vals[i - 1] + 2 * vals[i] + vals[(i + 1) % n]) / 4 for i in range(n)]

    def f(a):
        x = (a % (2 * math.pi)) / (2 * math.pi) * n
        i = int(x) % n
        t = x - int(x)
        return vals[i] * (1 - t) + vals[(i + 1) % n] * t
    return f


def _ring_tube(kit, axis, rings_def, slot, name, verts=24, wall=0.01, gap=0.0, back=None):
    ex = V((1, 0, 0)) if back is None else back.cross(axis)
    ex = (ex - axis * ex.dot(axis)).normalized()
    ey = axis.cross(ex).normalized()
    ref = V((0, 1, 0)) if back is None else back
    if ey.dot(ref) < 0:
        ey = -ey
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
    profile = outer + [inner[-1]] + list(reversed(inner))[1:]
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


def _bvh(objs):
    verts, polys, off = [], [], 0
    for o in objs:
        mw = o.matrix_world
        verts += [mw @ v.co for v in o.data.vertices]
        polys += [tuple(i + off for i in p.vertices) for p in o.data.polygons]
        off += len(o.data.vertices)
    return BVHTree.FromPolygons(verts, polys)


def _catmull(ctrl, step=0.03):
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


def _draped(tree, ctrl, off, keep_ends=1, lift=None, step=0.045):
    raw = _catmull(ctrl, step)
    hits = [tree.find_nearest(p)[:2] for p in raw]
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


# ================================================================== gloves (base, scaled by GH)
def _hand(kit, cl, j, s, hand, name):
    """Oversized cotton work glove: knit cuff, palm, four fingers held together, thumb. hand = (wrist,
    finger direction d, palm/curl direction m, curl 0 relaxed .. 1 fist)."""
    sign = 1 if s == "l" else -1
    w, d, m, curl = hand
    f = (m.cross(d) if sign > 0 else d.cross(m)).normalized()      # thumb side
    palm = w + d * 0.062 * GH + m * 0.004 * GH
    knuck = w + d * 0.118 * GH + m * 0.008 * GH
    joints = {"wristin": (j["wristin_" + s], 0.05 * GH), "wrist": (w, 0.057 * GH),
              "palm": (palm, (0.036 * GH, 0.062 * GH)), "knuck": (knuck, (0.03 * GH, 0.058 * GH))}
    bones = [("wristin", "wrist"), ("wrist", "palm"), ("palm", "knuck")]
    obj = cl.skin_body(kit, joints, bones, LIGHT, subdiv=2, name=name)
    cl.decimate_to(obj, 380)
    fj, fb = {}, []
    a1 = math.radians(14 + 70 * curl)
    a2 = math.radians(38 + 100 * curl)
    for i, (off, length, r) in enumerate(((0.038, 0.095, 0.0172), (0.013, 0.106, 0.0178),
                                          (-0.0125, 0.099, 0.0172), (-0.037, 0.082, 0.0158))):
        base = knuck + f * off * GH
        a = base - d * 0.03 * GH
        d1 = d * math.cos(a1) + m * math.sin(a1)
        d2 = d * math.cos(a2) + m * math.sin(a2)
        mid = base + d1 * length * 0.55 * GH + f * (0.003 * i - 0.004) * GH
        tip = mid + d2 * length * 0.45 * GH
        fj["f%da" % i], fj["f%db" % i], fj["f%dc" % i] = (a, r * GH), (mid, r * 0.96 * GH), (tip, r * 0.86 * GH)
        fb += [("f%da" % i, "f%db" % i), ("f%db" % i, "f%dc" % i)]
    t0 = w + (d * 0.03 + f * 0.02 + m * 0.016) * GH
    t1 = w + (d * 0.082 + f * 0.034 + m * 0.03) * GH
    t2 = t1 + (d * 0.048 + f * -0.004 + m * (0.014 + 0.03 * curl)) * GH
    fj.update({"t0": (t0, 0.023 * GH), "t1": (t1, 0.02 * GH), "t2": (t2, 0.0175 * GH)})
    fb += [("t0", "t1"), ("t1", "t2")]
    fingers = cl.skin_body(kit, fj, fb, LIGHT, subdiv=1, name=name + " fingers")
    cl.decimate_to(fingers, 400)
    return obj


# ================================================================== build
def _load_matrix(P, F):
    ld = P["load"]
    if "rel" in ld:
        return F["top"] @ _T(ld["rel"]) @ _R4(ld["rot"])
    return _T(ld["loc"]) @ _R4(ld["rot"])


def build(kit, cl, pose):
    P = POSE[pose]
    j, F, hands = skeleton(P)
    J = lambda names, radii: {n: (j[n], r) for n, r in zip(names, radii)}  # noqa: E731
    top3 = F["top"].to_3x3().normalized()
    fwd = top3 @ V((0, -1, 0))

    # ---------------------------------------------------------- jacket
    torso = cl.skin_body(kit, J(["pelvis", "belly", "chest", "top"],
                                [(0.39, 0.31), (0.42, 0.35), (0.43, 0.34), (0.40, 0.28)]),
                         [("pelvis", "belly"), ("belly", "chest"), ("chest", "top")], JACKET, name="jacket torso")
    sleeves = []
    for s in ("l", "r"):
        sl = cl.skin_body(kit, J(["armin_" + s, "shoulder_" + s, "elbow_" + s, "sleeve_" + s],
                                 [0.13, 0.15, 0.115, 0.10]),
                          [("armin_" + s, "shoulder_" + s), ("shoulder_" + s, "elbow_" + s),
                           ("elbow_" + s, "sleeve_" + s)], JACKET, name="sleeve " + s)
        sleeves.append(sl)
        axis = (j["elbow_" + s] - j["wrist_" + s]).normalized()
        c0 = j["sleeve_" + s] + axis * 0.08
        r = min(0.112, _section_r(sl, c0, axis, rmax=0.13))
        _tube_open(kit, c0, j["sleeve_" + s] - axis * 0.02, (r * 0.97, r * 0.97), (r * 1.08, r * 1.08),
                   JACKET, "cuff " + s, verts=16, wall=0.012)
        cl.decimate_to(sl, 560)
    trousers = cl.skin_body(kit, J(["seat_l", "hip_l", "knee_l", "hemt_l", "seat_r", "hip_r", "knee_r", "hemt_r"],
                                   [0.18, 0.215, 0.17, 0.15, 0.18, 0.215, 0.17, 0.15]),
                            [("seat_l", "hip_l"), ("hip_l", "knee_l"), ("knee_l", "hemt_l"),
                             ("seat_r", "hip_r"), ("hip_r", "knee_r"), ("knee_r", "hemt_r")], CLOTH, name="trousers")
    # Jacket hem: a boxy waist-length band, riding up at the back.
    axis = (j["belly"] - j["pelvis"]).normalized()
    t_tree, l_tree = _bvh([torso]), _bvh([trousers])
    back = F["pelvis"].to_3x3() @ V((0, 1, 0))
    ex = (back.cross(axis)).normalized()
    ey = axis.cross(ex).normalized()
    ey = ey if ey.dot(back) > 0 else -ey

    def _d(a):
        return ex * math.cos(a) + ey * math.sin(a)

    c_top, c_mid = j["pelvis"] + axis * 0.11, j["pelvis"] + axis * 0.05
    bot = lambda a: j["pelvis"] - axis * (0.03 - 0.07 * max(0.0, math.sin(a)))  # noqa: E731  rides up at the back
    r_top = _smoothed(lambda a: 0.97 * _extent(t_tree, c_top, _d(a)))
    r_bot = _smoothed(lambda a: max(1.0 * _extent(t_tree, c_mid, _d(a)), _extent(l_tree, bot(a), _d(a)) + 0.022))
    _ring_tube(kit, axis, [(lambda a: c_top, r_top), (bot, r_bot)], JACKET, "jacket hem", verts=28, wall=0.02,
               back=back)
    cl.decimate_to(trousers, 860)
    for s in ("l", "r"):
        ax = (j["knee_" + s] - j["ankle_" + s]).normalized()
        c0 = j["hemt_" + s] + ax * 0.05
        r = min(0.165, _section_r(trousers, c0, ax, slab=0.05, rmax=0.19))
        _tube_open(kit, c0, j["hemt_" + s] - ax * 0.10, (r * 1.08, r * 1.08), (r * 1.14, r * 1.14),
                   CLOTH, "trouser hem " + s, verts=16, wall=0.012)
    # Boots.
    for s in ("l", "r"):
        b = cl.skin_body(kit, J(["shin_" + s, "ankle_" + s, "anklelow_" + s], [0.07 * GB, 0.08 * GB, 0.074 * GB]),
                         [("shin_" + s, "ankle_" + s), ("ankle_" + s, "anklelow_" + s)], DARK, name="boot " + s)
        cl.decimate_to(b, 260)
        bf = F["boot_" + s]
        rot = _deg(bf)
        at = lambda v: tuple(bf @ (V(v) * GB))  # noqa: E731
        kit.soft_box(tuple(V((0.124, 0.262, 0.104)) * GB), at((0, -0.012, 0.078)), DARK, radius=0.022 * GB,
                     puff=0.003 * GB, segments=16, rings=8, rot=rot, name="boot foot " + s)
        cl.ellipsoid(kit, tuple(V((0.124, 0.115, 0.094)) * GB), at((0, -0.108, 0.071)), DARK, rot=rot,
                     segments=14, rings=8, name="steel toe " + s)
        kit.box(tuple(V((0.132, 0.20, 0.026)) * GB), at((0, -0.068, 0.013)), DARK, bevel=0.01 * GB, segments=1,
                rot=rot, name="sole " + s)
        kit.box(tuple(V((0.124, 0.095, 0.04)) * GB), at((0, 0.075, 0.02)), DARK, bevel=0.008 * GB, segments=1,
                rot=rot, name="heel " + s)
    # Neck, collar, head.
    H = F["head"]
    cl.skin_body(kit, J(["neck_base", "neck", "neck_top"], [0.15, 0.135, 0.105]),
                 [("neck_base", "neck"), ("neck", "neck_top")], CLOTH, name="neck")
    ax = (j["neck"] - j["neck_base"]).normalized()
    nb = j["neck_base"]
    bk = top3 @ V((0, 1, 0))
    # collar pushed up at the back by the load
    _ring_tube(kit, ax, [(lambda a: nb + ax * (0.07 + 0.06 * max(0.0, math.sin(a))), lambda a: 0.16),
                         (lambda a: nb + ax * 0.01, lambda a: 0.20),
                         (lambda a: nb - ax * 0.03, lambda a: 0.21)],
               JACKET, "collar", verts=18, wall=0.016, gap=math.radians(30), back=bk)
    _head(kit, H)
    kit.soft_box((0.028 * HS, 0.03 * HS, 0.07 * HS), tuple(H @ (V((0, -0.095, -0.008)) * HS)), CLOTH,
                 radius=0.012 * HS, segments=10, rings=6, rot=_deg(H @ _R4((-12, 0, 0))), name="nose")
    _band(kit, H, CUFF_Z[0], CUFF_Z[1], CUFF_OUT, LIGHT, "cap cuff", verts=22)
    for s in ("l", "r"):
        _hand(kit, cl, j, s, hands[s], "glove " + s)

    # ---------------------------------------------------------- the load
    M = _load_matrix(P, F)
    ceil = P.get("ceiling")
    warp = Warp(None if ceil is None else ceil - CEIL_GAP, P.get("wall"), centre=M.translation.copy(),
                **P.get("warp", {}))
    L = Load(M, warp)
    h = LH
    for s in ("l", "r"):
        STRAP_END[s] = max(-h.z + 0.08, min(h.z - 0.08, L.to_local(j["shoulder_" + s]).z + 0.10))
    raw_top = max((M @ _lsurf(V((x, y, h.z)))[0]).z for x in (-0.6, -0.3, 0, 0.3, 0.6) for y in (-0.3, 0, 0.3))
    pad = _pad(kit, L)
    # the blanket's edge, bound in pale tape, running across the front face
    bq = _path([(0.26, 0.06, h.z), (0.12, -h.y, h.z)] + [(x, -h.y, z) for x, z in EDGE[1:-1]]
               + [(-0.45, -h.y, -h.z)], 0.045)
    bpts, bnrm = [], []
    for q in bq:
        p, n = L.point(q, 0.012 + STEP * 0.6, quilt=False, clear=0.012)
        bpts.append(p)
        bnrm.append(n)
    _ribbon(kit, bpts, bnrm, 0.085, 0.02, LIGHT, "binding")
    # ropes: two turns round the girth, one loop the long way
    for t, dz in enumerate((0.0, 0.05)):
        z = ZG + dz - 0.025
        _rope(kit, L, [(-h.x, YL - 0.06 + 0.03 * t, z), (-h.x, -h.y, z), (h.x, -h.y, z), (h.x, h.y, z),
                       (-h.x, h.y, z), (-h.x, YL + 0.04 + 0.03 * t, z)], "rope girth %d" % t)
    _rope(kit, L, [(-h.x, YL, ZG + 0.10), (-h.x, YL, h.z), (h.x, YL, h.z), (h.x, YL, -h.z), (-h.x, YL, -h.z),
                   (-h.x, YL, ZG - 0.10)], "rope long")
    # the knot on the right end, and the shipping tag hanging from it
    kp, kn = L.point((-h.x, YL, ZG), ROPE_R * 2.2)
    cl.ellipsoid(kit, (0.10, 0.08, 0.12), tuple(kp), LIGHT, rot=_rot_to(kn, (1, 0, 0)), segments=10, rings=6,
                 name="rope knot")
    cl.ellipsoid(kit, (0.07, 0.06, 0.08), tuple(kp + kn * 0.03 + V((0, 0, -0.06))), LIGHT, segments=8, rings=5,
                 name="rope knot b")
    tail = [kp + V((0, 0, -0.04)), kp + kn * 0.06 + V((0, -0.03, -0.18)), kp + kn * 0.05 + V((0.0, -0.06, -0.34))]
    kit.tube(tail, ROPE_R * 0.9, LIGHT, verts=6, name="rope tail")
    tag_top = kp + kn * 0.09 + V((0, -0.05, -0.10))
    kit.tube([kp + kn * 0.04, tag_top], 0.005, DARK, verts=4, name="tag string")
    face = (V((kn.x, kn.y, 0)).normalized() if V((kn.x, kn.y, 0)).length > 1e-3 else V((-1, 0, 0)))
    tyaw = math.degrees(math.atan2(face.x, -face.y))
    tc = tag_top + V((0, 0, -0.14))
    kit.box((0.15, 0.008, 0.26), tuple(tc), LIGHT, bevel=0.003, segments=1, rot=(0, 0, tyaw), name="tag")
    tr = _R3((0, 0, tyaw))
    for dz, w in ((0.07, 0.10), (0.04, 0.08), (0.01, 0.10), (-0.06, 0.11)):
        kit.box((w, 0.004, 0.012 if dz > -0.05 else 0.05), tuple(tc + tr @ V((0, -0.006, dz))), DARK, bevel=0.0,
                segments=1, rot=(0, 0, tyaw), name="tag print")
    # shipping label on the front face (the face over his head), askew
    lab = (0.17, -0.25)
    _patch(kit, L, 1, -1, lab, (0.30, 0.22), -8.0, 0.010, LIGHT, "label")
    ca, sa = math.cos(math.radians(-8)), math.sin(math.radians(-8))
    for du, dv, su, sv in ((-0.03, 0.065, 0.20, 0.02), (-0.05, 0.03, 0.16, 0.018), (-0.03, -0.002, 0.18, 0.018),
                           (0.0, -0.065, 0.22, 0.06)):
        _patch(kit, L, 1, -1, (lab[0] + du * ca - dv * sa, lab[1] + du * sa + dv * ca), (su, sv), -8.0, 0.017,
               DARK, "label print", n=3)
    # the loose corner of the blanket hanging off the left end
    _flap(kit, L, (-0.45, -h.y, -h.z), (-0.63, -h.y * 0.4, -h.z), 0.36, (0.03, -0.04, 0.0), "blanket corner")

    # shoulder straps: up the back of the load, over the top, down its front and INTO the shoulders
    sleeve_tree = _bvh(sleeves)
    for s, x0 in (("l", STRAP_X), ("r", -STRAP_X)):
        z_end = STRAP_END[s]
        q = _path([(x0, h.y * 0.1, -h.z), (x0, h.y, -h.z), (x0, h.y, h.z), (x0, -h.y, h.z), (x0, -h.y, z_end)], 0.06)
        pts, nrm = [], []
        for qq in q:
            p, n = L.point(qq, STRAP_T / 2 + 0.003, clear=STRAP_T / 2)
            pts.append(p)
            nrm.append(n)
        tgt = j["shoulder_" + s] + top3 @ V((0, 0.0, 0.05))
        last = pts[-1]
        for t in (0.35, 0.7, 1.0):
            pts.append(last.lerp(tgt, t))
            nrm.append(nrm[-1])
        _ribbon(kit, pts, nrm, STRAP_W, STRAP_T, DARK, "load strap " + s)
        hit, hn, _i, _d2 = sleeve_tree.ray_cast(last, (tgt - last).normalized(), (tgt - last).length)
        if hit is None:
            hit, hn, _i, _d2 = sleeve_tree.find_nearest(last.lerp(tgt, 0.7))
        across = (tgt - last).cross(hn)
        cl.ellipsoid(kit, (0.17, 0.10, 0.04), tuple(hit + hn * 0.003), JACKET, rot=_basis_euler(across, hn),
                     segments=12, rings=6, name="pucker " + s)
    # the chest X: each strap comes back out of the front of its shoulder and crosses the chest
    torso_tree = _bvh([torso])
    T = F["top"]
    cross = T @ V((0, -0.42, -0.30))
    for s, sg in (("l", 1), ("r", -1)):
        ctrl = [j["shoulder_" + s] + top3 @ V((-sg * 0.05, -0.08, -0.03)),
                T @ V((sg * 0.22, -0.40, -0.12)), cross, T @ V((-sg * 0.24, -0.40, -0.50)),
                T @ V((-sg * 0.36, -0.20, -0.66)), T @ V((-sg * 0.32, 0.02, -0.72))]
        lift = (lambda t: 0.02 * math.exp(-((t - 0.45) / 0.15) ** 2)) if s == "l" else None
        pts, nrm = _draped(torso_tree, ctrl, STRAP_T / 2 + 0.012, keep_ends=2, lift=lift, step=0.06)
        _ribbon(kit, pts, nrm, 0.085, STRAP_T, DARK, "chest strap " + s)
    loc, n, _i, _d2 = torso_tree.find_nearest(cross)
    kit.frame((0.14, 0.115), (0.09, 0.065), 0.022, tuple(loc + n * 0.05), CHROME, bevel=0.004,
              rot=_rot_to(n), name="buckle")

    # ---------------------------------------------------------- strain: creases
    # compression folds across the back of the jacket under the load, pull folds from the armpits
    for k, (z, half) in enumerate(((-0.52, 0.30), (-0.62, 0.33), (-0.72, 0.30))):
        ctrl = [T @ V((-half, 0.40, z + 0.03 * k)), T @ V((-half * 0.4, 0.45, z - 0.025)),
                T @ V((half * 0.3, 0.45, z + 0.02)), T @ V((half, 0.40, z - 0.02))]
        pts, nrm = _draped(torso_tree, ctrl, 0.0, keep_ends=0, step=0.065)
        _crease(kit, pts, nrm, 0.07, 0.022, JACKET, "back crease")
    for s, sg in (("l", 1), ("r", -1)):
        ctrl = [T @ V((sg * 0.33, -0.20, -0.20)), T @ V((sg * 0.22, -0.34, -0.36)), T @ V((sg * 0.10, -0.36, -0.52))]
        pts, nrm = _draped(torso_tree, ctrl, 0.0, keep_ends=0, step=0.065)
        _crease(kit, pts, nrm, 0.06, 0.018, JACKET, "pull crease")
    # sleeves bunched at the elbow (on the inside of the bend)
    for s, sl in zip(("l", "r"), sleeves):
        tree = _bvh([sl])
        el, sh, wr = j["elbow_" + s], j["shoulder_" + s], j["wrist_" + s]
        ua, fa = (sh - el).normalized(), (wr - el).normalized()
        inner = (ua + fa)
        inner = inner.normalized() if inner.length > 1e-3 else fwd
        axis_e = (fa - ua).normalized()
        side = axis_e.cross(inner).normalized()
        for k, (off, span) in enumerate(((-0.07, 1.05), (0.04, 1.25), (0.14, 0.9))):
            c = el + axis_e * off
            ctrl = [c + (inner * math.cos(a) + side * math.sin(a)) * 0.2 for a in
                    (-span, -span * 0.5, 0.0, span * 0.5, span)]
            pts, nrm = _draped(tree, ctrl, 0.0, keep_ends=0, step=0.06)
            _crease(kit, pts, nrm, 0.055, 0.022, JACKET, "sleeve crease")
    # chest pockets with flaps, and the front placket with big buttons
    for sg in (1, -1):
        c = T @ V((sg * 0.19, -0.45, -0.26))
        loc, n, _i, _d2 = torso_tree.find_nearest(c)
        kit.soft_box((0.26, 0.035, 0.10), tuple(loc + n * 0.012), JACKET, radius=0.015, segments=8, rings=4,
                     rot=_basis_euler(top3 @ V((1, 0, 0)), -n), name="pocket flap")
        kit.cylinder(0.022, 0.012, tuple(loc + n * 0.035 - (top3 @ V((0, 0, 0.03)))), DARK, verts=10,
                     rot=_rot_to(n, (0, 0, 1)), name="pocket button")
    ctrl = [T @ V((0, -0.42, -0.02)), T @ V((0.0, -0.45, -0.30)), T @ V((0.0, -0.42, -0.55)), T @ V((0.0, -0.38, -0.70))]
    pts, nrm = _draped(torso_tree, ctrl, 0.006, keep_ends=0)
    _ribbon(kit, pts, nrm, 0.07, 0.014, JACKET, "placket")

    # ---------------------------------------------------------- finish
    lo = cl.floor_parts(kit)
    eye = H @ _head_ring_point(-math.pi / 2, FACE_Z, 0.0)
    EYE[pose] = round(eye.z - lo, 3)
    bpy.context.view_layer.update()
    ws = [o.matrix_world @ v.co for o in kit.parts for v in o.data.vertices]
    lw = [pad.matrix_world @ v.co for v in pad.data.vertices]
    tris = {}
    for o in kit.parts:
        key = o.name.rstrip(".0123456789")
        tris[key] = tris.get(key, 0) + sum(len(p.vertices) - 2 for p in o.data.polygons)
    print("[giant_d] %s: floor shift %.3f, eye %.3f, top %.3f (load raw top %.3f -> %.3f), half-width %.3f, "
          "y %.2f..%.2f" % (pose, lo, EYE[pose], max(p.z for p in ws), raw_top - lo, max(p.z for p in lw),
                             max(abs(p.x) for p in ws), min(p.y for p in ws), max(p.y for p in ws)))
    print("[giant_d] joints: " + ", ".join("%s (%.2f %.2f %.2f)" % (k, *(j[k] - V((0, 0, lo))))
                                          for k in ("pelvis", "top", "shoulder_l", "shoulder_r", "elbow_l", "elbow_r",
                                                    "wrist_l", "wrist_r", "knee_l", "knee_r")))
    print("[giant_d] load centre (%.2f %.2f %.2f) rot %s" % (M.translation.x, M.translation.y, M.translation.z - lo,
                                                           tuple(round(a) for a in _deg(M))))
    print("[giant_d] head (%.2f %.2f %.2f) rot %s; tris %d: %s" % (
        H.translation.x, H.translation.y, H.translation.z - lo, tuple(round(a) for a in _deg(H)), sum(tris.values()),
        ", ".join("%s %d" % kv for kv in sorted(tris.items(), key=lambda kv: -kv[1]))))
    wide = {}
    for o in kit.parts:
        key = o.name.rstrip(".0123456789")
        wide[key] = max(wide.get(key, 0.0), max(abs((o.matrix_world @ v.co).x) for v in o.data.vertices))
    print("[giant_d] widest: " + ", ".join("%s %.3f" % kv for kv in sorted(wide.items(), key=lambda kv: -kv[1])[:6]))
    kit.no_collider()
