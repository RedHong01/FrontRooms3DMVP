"""Hunter direction C — "Duplicate" (Documentation/research/hunter/10_hunter_directions.md §5, §7.4).

A bad photocopy of an employee: toner-black head with a flat printed paper face,
a white short-sleeved shirt stretched over a trunk as long as the legs, oxblood
tie, navy trousers, soft black office shoes. Built in the "copy's step" render
pose (Hunt slump; also the pose of every static copy).

Coordinates are the spec's (metres, Z up, facing -Y, left = +X) before flooring.
"""

import math

from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

NAME = "Hunter_C_Duplicate"
TITLE = "Duplicate"
PITCH = ("A bad photocopy of an office worker: a flat printed face on a toner-black head, "
         "a shirt stretched over a trunk as long as his legs, and identical copies of him in every office.")
EYE = 1.64            # replaced in build() by the measured centre of the printed face after flooring
SMOOTH_ANGLE = 60.0

PAPER = "Prop_Paper"
TONER = "Creature_Toner"
SKIN = "Creature_SkinPale"
TIE = "Creature_TieOxblood"
NAVY = "Prop_FabricNavy"
SHOE = "Prop_PlasticBlack"

# Head frame: centre, rotation (deg XYZ: pitch 8 down, roll 4), size.
HEAD_C = Vector((0.0, -0.245, 1.672))
HEAD_ROT = (8.0, 4.0, 0.0)
HEAD_SIZE = (0.19, 0.23, 0.26)
HEAD_FRONT = 0.086          # the skull is cut flat this far in front of its centre
FACE_W, FACE_H, FACE_Z = 0.150, 0.200, -0.016   # printed face (head-local)


# ------------------------------------------------------------------ helpers
def _head_matrix():
    return Matrix.Translation(HEAD_C) @ Euler([math.radians(a) for a in HEAD_ROT]).to_matrix().to_4x4()


def _bvh(obj):
    mw = obj.matrix_world
    return BVHTree.FromPolygons([mw @ v.co for v in obj.data.vertices], [tuple(p.vertices) for p in obj.data.polygons])


def _front(tree, x, z):
    """First surface hit looking from the front (-Y) toward +Y at (x, z): (location, normal) or None."""
    loc, nrm, _i, _d = tree.ray_cast(Vector((x, -2.0, z)), Vector((0, 1, 0)))
    return (loc, nrm) if loc is not None else None


def _section(obj, z, tol=0.012):
    """Half-width and front/back of a mesh in a thin horizontal slab at height z."""
    vs = [v.co for v in obj.data.vertices if abs(v.co.z - z) < tol]
    return max(abs(v.x) for v in vs), min(v.y for v in vs), max(v.y for v in vs)


def _ellipse(cx, cz, w, h, n=14, tilt=0.0, droop=0.0, power=1.0):
    """Closed outline (u, v) of an ellipse-ish blob; droop pulls the outer (+u) end down."""
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


def _face_outline(n=44):
    """The printed face: a flat egg (broad forehead, narrow chin), head-local (u, v)."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        e = 0.72 if s > 0 else 0.92
        u = math.copysign(abs(c) ** e, c) * FACE_W / 2
        v = math.copysign(abs(s) ** e, s) * FACE_H / 2
        if s < 0:
            u *= 1 - 0.36 * (-s) ** 1.6
        pts.append((u, FACE_Z + v))
    return pts


def _on_head(kit, outline, y, depth, slot, name, bevel=0.0):
    """Extrude a head-local (u, v) outline as a flat plate at head-local depth y."""
    loc = _head_matrix() @ Vector((0.0, y, 0.0))
    return kit.extrude(outline, depth, tuple(loc), slot, plane="xz", rot=HEAD_ROT, bevel=bevel, name=name)


def _soft_shape(obj, fn):
    for v in obj.data.vertices:
        v.co = fn(Vector(v.co))


# ------------------------------------------------------------------ body data
def _joints():
    j = {}
    # Shirt torso: one vertical chain, hem tucked inside the trousers.
    j.update({
        "hem": ((0, 0.075, 0.905), (0.160, 0.122)),
        "waist": ((0, 0.07, 0.955), (0.178, 0.138)),
        "belly": ((0, 0.01, 1.13), (0.218, 0.195)),     # the paunch
        "chest": ((0, -0.065, 1.39), (0.212, 0.152)),
        "chest_top": ((0, -0.118, 1.575), (0.180, 0.112)),
    })
    # Shirt yoke: one chain across the shoulders, sleeves hanging off its ends (no branch nodes).
    j.update({
        "yoke_l": ((0.105, -0.115, 1.625), 0.088), "yoke_r": ((-0.105, -0.112, 1.622), 0.088),
        "shoulder_l": ((0.245, -0.12, 1.595), 0.084), "shoulder_r": ((-0.245, -0.115, 1.588), 0.084),
        "sleeve_l": ((0.282, -0.128, 1.425), 0.070), "sleeve_r": ((-0.282, -0.118, 1.418), 0.070),
    })
    # Bare arms (start inside the sleeves) and hands: palm + mitten fingers + thumb.
    for s, sx, dy, dz in (("l", 1, 0.0, 0.0), ("r", -1, 0.02, -0.01)):
        j.update({
            "armin_" + s: ((sx * 0.272, -0.125 + dy, 1.48 + dz), 0.047),
            "elbow_" + s: ((sx * 0.300, -0.128 + dy, 1.315 + dz), 0.049),
            "wrist_" + s: ((sx * 0.318, -0.190 + dy, 1.040 + dz), 0.036),
            "knuckle_" + s: ((sx * 0.322, -0.208 + dy, 0.945 + dz), (0.021, 0.046)),
            "fing_" + s: ((sx * 0.314, -0.218 + dy, 0.893 + dz), (0.018, 0.040)),
            "tip_" + s: ((sx * 0.302, -0.212 + dy, 0.858 + dz), (0.014, 0.030)),
            "thumb0_" + s: ((sx * 0.312, -0.215 + dy, 1.005 + dz), 0.017),
            "thumb1_" + s: ((sx * 0.304, -0.243 + dy, 0.960 + dz), 0.015),
            "thumb2_" + s: ((sx * 0.296, -0.252 + dy, 0.928 + dz), 0.012),
        })
    # Neck: rises forward out of the collar into the hung head.
    j.update({
        "neck_base": ((0, -0.135, 1.585), 0.064),
        "neck": ((0, -0.185, 1.630), 0.058),
        "neck_top": ((0, -0.225, 1.655), 0.052),
    })
    # Trousers: a seat chain plus two separate leg chains that start inside it.
    j.update({
        "waist_t": ((0, 0.07, 0.972), (0.176, 0.137)),
        "pelvis": ((0, 0.09, 0.86), (0.175, 0.13)),
        "seat_l": ((0.075, 0.095, 0.88), 0.10), "seat_r": ((-0.075, 0.105, 0.88), 0.10),
        "hip_l": ((0.105, 0.10, 0.80), 0.112), "hip_r": ((-0.105, 0.12, 0.80), 0.112),
        "knee_l": ((0.11, -0.05, 0.46), 0.078), "knee_r": ((-0.11, 0.21, 0.45), 0.078),
        "ankle_l": ((0.11, -0.10, 0.115), 0.060), "ankle_r": ((-0.11, 0.31, 0.135), 0.060),
    })
    # Shoe uppers: from inside the trouser hem down into the shoe.
    j.update({
        "shin_l": ((0.11, -0.088, 0.21), 0.044), "sock_l": ((0.11, -0.10, 0.075), 0.047),
        "shin_r": ((-0.11, 0.285, 0.225), 0.044), "sock_r": ((-0.11, 0.315, 0.095), 0.047),
    })
    return j


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


# ------------------------------------------------------------------ build
def build(kit, cl):
    global EYE
    j = _joints()

    # --- shirt (paper white): torso chain + yoke/sleeve chain
    shirt = _skin(kit, cl, j, [
        ("hem", "waist"), ("waist", "belly"), ("belly", "chest"), ("chest", "chest_top"),
        ("sleeve_r", "shoulder_r"), ("shoulder_r", "yoke_r"), ("yoke_r", "yoke_l"),
        ("yoke_l", "shoulder_l"), ("shoulder_l", "sleeve_l"),
    ], PAPER, "shirt")

    # --- bare arms and hands
    for s in ("l", "r"):
        _skin(kit, cl, j, [("armin_" + s, "elbow_" + s), ("elbow_" + s, "wrist_" + s),
                           ("wrist_" + s, "knuckle_" + s), ("knuckle_" + s, "fing_" + s), ("fing_" + s, "tip_" + s),
                           ("thumb0_" + s, "thumb1_" + s), ("thumb1_" + s, "thumb2_" + s)], SKIN, "arm_" + s)

    # --- neck
    _skin(kit, cl, j, [("neck_base", "neck"), ("neck", "neck_top")], SKIN, "neck")

    # --- trousers
    _skin(kit, cl, j, [("waist_t", "pelvis"),
                       ("seat_l", "hip_l"), ("hip_l", "knee_l"), ("knee_l", "ankle_l"),
                       ("seat_r", "hip_r"), ("hip_r", "knee_r"), ("knee_r", "ankle_r")], NAVY, "trousers")

    # --- shoes: soft-soled office shoes (flat sole, low toe, instep rising to the ankle)
    def shoe_shape(p):
        hl = 0.14
        f = max(0.0, -p.y / hl)          # toward the toe
        b = max(0.0, p.y / hl)           # toward the heel
        if p.z > 0:
            p.z *= 1 - 0.42 * f ** 1.4
        p.x *= (1 - 0.16 * f ** 2.5) * (1 - 0.14 * b ** 2)
        return p
    for s, loc, rot in (("l", (0.11, -0.172, 0.040), (0, 0, 2)), ("r", (-0.11, 0.240, 0.064), (10, 0, -2))):
        shoe = kit.soft_box((0.098, 0.28, 0.080), loc, SHOE, radius=0.028, segments=24, rings=12, rot=rot, name="shoe_" + s)
        _soft_shape(shoe, shoe_shape)
    _skin(kit, cl, j, [("shin_l", "sock_l")], SHOE, "upper_l")
    _skin(kit, cl, j, [("shin_r", "sock_r")], SHOE, "upper_r")

    # --- belt: an elliptical band fitted to the measured waist (no hoop gap)
    hw, yf, yb = _section(shirt, 0.955)
    belt = kit.lathe([(1.0, -0.023), (1.018, -0.016), (1.018, 0.016), (1.0, 0.023)], (0, (yf + yb) / 2, 0.955), SHOE,
                     verts=40, name="belt")
    belt.scale = (hw + 0.004, (yb - yf) / 2 + 0.004, 1.0)

    # --- head: toner-black skull and hair, cut flat at the front
    H = _head_matrix()
    head = kit.soft_box(HEAD_SIZE, tuple(HEAD_C), TONER, radius=0.075, segments=28, rings=16, rot=HEAD_ROT, name="head")
    hz = HEAD_SIZE[2] / 2

    def head_shape(p):
        if p.z < 0:
            k = -p.z / hz
            p.x *= 1 - 0.20 * k ** 2                 # jaw narrower than the cranium
            if p.y > 0:
                p.y *= 1 - 0.38 * k ** 1.5           # nape tucks in above the neck
        if p.y < -HEAD_FRONT:
            p.y = -HEAD_FRONT                        # the face has no relief
        return p
    _soft_shape(head, head_shape)
    for sx in (1, -1):
        ear = cl.ellipsoid(kit, (0.026, 0.048, 0.062), tuple(H @ Vector((sx * 0.090, 0.012, -0.012))), TONER,
                           rot=HEAD_ROT, segments=12, rings=8, name="ear")

    # --- the printed face: a flat paper egg on the flat skull front, then toner print on it
    paper_y = -HEAD_FRONT - 0.002
    _on_head(kit, _face_outline(), paper_y, 0.004, PAPER, "face_paper", bevel=0.0015)
    ink_y = -HEAD_FRONT - 0.0045
    ink = []
    fz = FACE_Z
    for sx in (1, -1):
        # brows: inner ends raised (faintly sad)
        ink.append(_stroke([(sx * 0.016, fz + 0.046), (sx * 0.038, fz + 0.042), (sx * 0.060, fz + 0.033)], 0.010, 0.6))
        # eye sockets: thresholded to solid black, outer corners drooping
        ink.append(_ellipse(sx * 0.034, fz + 0.018, 0.040, 0.022, n=16, tilt=0.0, droop=0.004, power=0.85)
                   if sx > 0 else [(-u, v) for (u, v) in _ellipse(0.034, fz + 0.018, 0.040, 0.022, n=16, droop=0.004, power=0.85)])
        # nostril
        ink.append(_ellipse(sx * 0.010, fz - 0.036, 0.011, 0.007, n=10))
    # nose shadow (one side, light from the left), philtrum and mouth (corners down), under-lip shadow
    ink.append(_stroke([(-0.010, fz + 0.012), (-0.012, fz - 0.010), (-0.016, fz - 0.028)], 0.005, 0.6))
    ink.append(_stroke([(-0.026, fz - 0.068), (-0.012, fz - 0.062), (0.0, fz - 0.061), (0.012, fz - 0.062), (0.026, fz - 0.068)], 0.006, 0.5))
    ink.append(_ellipse(0.0, fz - 0.078, 0.022, 0.006, n=10))
    for k, outline in enumerate(ink):
        _on_head(kit, outline, ink_y, 0.0012, TONER, "print_%d" % k)
    # one vertical drum streak, broken (the scan direction)
    for z0, z1 in ((fz + 0.088, fz + 0.030), (fz + 0.004, fz - 0.052)):
        _on_head(kit, [(0.050, z0), (0.053, z0), (0.053, z1), (0.050, z1)], ink_y, 0.0012, TONER, "streak")

    # --- collar: a short band round the neck base, axis along the neck
    nb, nk = Vector(j["neck_base"][0]), Vector(j["neck"][0])
    axis = (nk - nb).normalized()
    tilt = math.degrees(math.atan2(-axis.y, axis.z))
    kit.cylinder(0.072, 0.050, tuple(nb + axis * 0.004), PAPER, radius_top=0.066, verts=28, rot=(tilt, 0, 0), name="collar")

    # --- tie: knot at the collar, blade following the shirt front, too short for the stretched trunk
    tree = _bvh(shirt)
    pts = []
    for z in [1.555 - 0.025 * i for i in range(18)]:
        hit = _front(tree, 0.0, z)
        if hit:
            pts.append(hit[0] + Vector((0, -0.005, 0)))
    blade_top, blade_end = 1.545, 1.17
    blade = [p for p in pts if blade_end <= p.z <= blade_top]
    if len(blade) >= 3:
        widths = [0.040 + (0.082 - 0.040) * (blade_top - p.z) / (blade_top - blade_end) for p in blade]
        _tie_blade(kit, blade, widths)
    kn = _front(tree, 0.0, 1.565)
    if kn:
        kit.soft_box((0.044, 0.030, 0.042), tuple(kn[0] + Vector((0, -0.010, 0))), TIE, radius=0.012, rot=(-10, 0, 0), name="knot")

    cl.floor_parts(kit)
    # Measured face-print centre after flooring.
    head_floor = head.location.z - HEAD_C.z
    EYE = round((H @ Vector((0, paper_y, FACE_Z))).z + head_floor, 3)
    kit.no_collider()


def _tie_blade(kit, pts, widths, thick=0.010):
    """A flat strip through pts (top to bottom) with a pointed tip, as one closed mesh."""
    import bmesh
    bm = bmesh.new()
    rows = []
    for p, w in zip(pts, widths):
        rows.append([bm.verts.new(p + Vector((sx * w / 2, dy, 0))) for sx, dy in
                     ((-1, -thick / 2), (1, -thick / 2), (1, thick / 2), (-1, thick / 2))])
    tip_front = bm.verts.new(pts[-1] + Vector((0, -thick / 2, -widths[-1] * 0.55)))
    tip_back = bm.verts.new(pts[-1] + Vector((0, thick / 2, -widths[-1] * 0.55)))
    for a, b in zip(rows, rows[1:]):
        for i in range(4):
            k = (i + 1) % 4
            bm.faces.new((a[i], a[k], b[k], b[i]))
    bm.faces.new(list(reversed(rows[0])))
    last = rows[-1]
    bm.faces.new((last[0], last[1], tip_front))
    bm.faces.new((last[2], last[3], tip_back))
    bm.faces.new((last[1], last[2], tip_back, tip_front))
    bm.faces.new((last[3], last[0], tip_front, tip_back))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object("tie", bm, TIE, "metres", "xz")
