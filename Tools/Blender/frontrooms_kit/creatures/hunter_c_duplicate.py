"""Hunter direction C — "Duplicate" (Documentation/research/hunter/10_hunter_directions.md §5, §7.4).

A bad black-and-white photocopy of an employee, in the two materials a copy has: paper and
toner. A toner-black head with a flat printed paper face set flush into it; a long-sleeved
paper-white shirt buttoned at the cuff, stretched over a trunk as long as the legs; toner tie,
trousers, belt and soft shoes. Only the hands and neck are bare, and they are paper too, shaded
with toner. No hue anywhere. Built in the "copy's step" render pose (the Hunt slump; the static
copies stand in §7.4's upright Listen pose).

The one countable shape (the 12 m read): the shirt prints as a page. The trunk is a portrait
rectangle, straight-sided from the belt to a flat, level shoulder line with square corners, the
sleeves drop straight from those corners, and the toner head sticks up out of the middle of the
line: a pale page between a dark head and dark legs. No other office figure has that shoulder line.

Coordinates are the spec's (metres, Z up, facing -Y, left = +X; rotations X pitch, Y roll,
Z yaw, §7.0) before flooring. Deviations from §7.4 are noted where they happen.
"""

import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector
from mathutils.bvhtree import BVHTree

NAME = "Hunter_C_Duplicate"
TITLE = "Duplicate"
PITCH = ("A bad black-and-white photocopy of an office worker: a flat printed face on a toner-black head, "
         "a white shirt stretched into a long, square-shouldered page over short toner legs, "
         "and identical copies of him standing in every office.")
EYE = 1.64            # replaced in build() by the measured centre of the printed face after flooring
SMOOTH_ANGLE = 60.0

PAPER = "Prop_Paper"          # shirt, collar, cuffs, face, hands, neck, ears (with the baked toner-edge term)
TONER = "Creature_Toner"      # head and hair, print ink, tie, trousers, belt, shoes, pen

# The shirt trunk as a page: rows (z, half-width, front y, back y) lofted with superellipse sections.
# Front/back follow the first build's measured skin (paunch, hunched back); the half-width is held
# nearly constant from the belt up (straight flanks), then opens under the sleeves into a level
# shoulder block whose outer corners are square (SHOULDER_R), not sloped.
TRUNK = [
    (0.936, 0.180, -0.040, 0.158),     # hem, tucked inside the belt
    (0.952, 0.199, -0.066, 0.173),
    (1.000, 0.208, -0.103, 0.190),
    (1.075, 0.213, -0.140, 0.190),
    (1.150, 0.215, -0.164, 0.178),     # paunch
    (1.225, 0.216, -0.178, 0.157),
    (1.300, 0.216, -0.189, 0.128),
    (1.375, 0.217, -0.199, 0.094),
    (1.405, 0.222, -0.203, 0.080),     # armpit: the block opens out behind the sleeve tops
    (1.435, 0.272, -0.206, 0.064),
    (1.455, 0.310, -0.208, 0.054),
    (1.475, 0.321, -0.209, 0.046),     # from here up the flank is plumb and flush with the sleeve
    (1.525, 0.322, -0.210, 0.024),
    (1.574, 0.322, -0.204, -0.004),    # start of the shoulder corner
]
SHOULDER_R = 0.028                     # corner radius seen from the front
SHOULDER_TOP = 1.605                   # the level shoulder line (§5: the shirt block runs up to 1.61)
COLLAR_RING = (0.092, 1.620, -0.172, -0.048)   # top ring round the neck: half-width, z, front y, back y
SECTION_N = 2.5                        # superellipse exponent of the trunk sections (2 = ellipse)

# Head frame: centre, rotation (deg XYZ: pitch 8 down, roll 4), half-sizes.
HEAD_C = Vector((0.0, -0.264, 1.662))
HEAD_ROT = (8.0, 4.0, 0.0)            # (the live one turns its head: set Z to yaw it; the copies never do)
HEAD_HX = 0.095                       # half-width
HEAD_HY_FRONT, HEAD_HY_BACK = 0.130, 0.118
HEAD_HZ_TOP, HEAD_HZ_BOT = 0.145, 0.125
HEAD_FRONT = 0.060                    # the skull is cut flat this far in front of its centre
FACE_W, FACE_H, FACE_Z = 0.148, 0.190, -0.006   # the printed paper face (head-local)
STREAK_X = -0.054                     # one vertical drum streak, face and shirt (the lit side)
HAIR_BAND = Vector((0, -0.024, 0))    # in front of this the head's sides stay toner (the face's dark frame)
HAIRLINE = [((0, -0.024, 0.034), (0, 0.070, 0.014)),     # above the ear, then down to the nape
            ((0, 0.040, 0.030), (0, 0.125, -0.080))]


# ------------------------------------------------------------------ helpers
def _head_matrix():
    return Matrix.Translation(HEAD_C) @ Euler([math.radians(a) for a in HEAD_ROT]).to_matrix().to_4x4()


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


def _face_outline(n=64):
    """The printed face, head-local (u, v): what a copier keeps of a face lit from its right.
    A flat egg (broad forehead, narrow chin) whose top is cut by the hair (a side parting, the
    hair swept down over the left temple) and whose left cheek and jaw drop into toner shadow."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        c, s = math.cos(t), math.sin(t)
        e = 0.74 if s > 0 else 0.92
        u = math.copysign(abs(c) ** e, c) * FACE_W / 2
        v = math.copysign(abs(s) ** e, s) * FACE_H / 2
        if s < 0:
            u *= 1 - 0.36 * (-s) ** 1.6
        # hairline: highest at the parting (u = -0.03), swept down toward the left temple
        top = FACE_H / 2 - 0.004 - 0.030 * _smooth(-0.030, 0.075, u) - 0.010 * _smooth(-0.030, -0.080, u)
        v = min(v, top)
        # shadow side (the figure's left, +u): cheek and jaw go to toner below the cheekbone
        if u > 0 and v < 0.004:
            lim = 0.066 - 0.030 * _smooth(0.004, -0.060, v)
            u = min(u, lim)
        pts.append((u, FACE_Z + v))
    return pts


def _v_range(outline, u):
    """Vertical extent of a closed outline at abscissa u."""
    vs = []
    for (u0, v0), (u1, v1) in zip(outline, outline[1:] + outline[:1]):
        if (u0 - u) * (u1 - u) <= 0 and u0 != u1:
            vs.append(v0 + (v1 - v0) * (u - u0) / (u1 - u0))
    return min(vs), max(vs)


def _on_head(kit, outline, y, depth, slot, name, bevel=0.0):
    """Extrude a head-local (u, v) outline as a flat plate at head-local depth y."""
    loc = _head_matrix() @ Vector((0.0, y, 0.0))
    return kit.extrude(outline, depth, tuple(loc), slot, plane="xz", rot=HEAD_ROT, bevel=bevel, name=name)


def _reshape(obj, fn):
    for v in obj.data.vertices:
        v.co = fn(Vector(v.co))


def _new_mesh(kit, bm, slot, name):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


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


def _pocket(kit, tree, cx, w, z_top, z_bot, nu=6, nv=9, front=0.0035, back=0.002):
    """A patch pocket lying on the shirt: surface points from front ray casts, thickened along the
    normal; the bottom corners are clipped (a pointed pocket bottom)."""
    grid = []
    for jv in range(nv):
        f = jv / (nv - 1)
        z = z_top + (z_bot - z_top) * f
        row = []
        for iu in range(nu):
            g = iu / (nu - 1)
            x = cx - w / 2 + w * g
            zz = z + (0.014 * abs(2 * g - 1) ** 2 if f == 1.0 else 0.0)   # clip the bottom corners
            hit = _front(tree, x, zz)
            row.append(hit if hit else (Vector((x, -0.2, zz)), Vector((0, -1, 0))))
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


def _strip(kit, pts, widths, normals, thick, slot, name, tip=0.0):
    """A flat strip lying on a surface: pts top to bottom, offset along the normals, optional pointed tip."""
    bm = bmesh.new()
    rows = []
    for p, w, nrm in zip(pts, widths, normals):
        side = Vector((1, 0, 0))
        rows.append([bm.verts.new(p + side * sx * w / 2 + nrm * off) for sx, off in
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
    """Dense rows through control rows (tuples), Catmull-Rom by row index; ends clamped."""
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


def _trunk(kit, n_around=28):
    """The shirt trunk: superellipse sections lofted through TRUNK, then a square shoulder corner
    (a quarter round of SHOULDER_R) and a level shoulder top closing in to the collar ring."""
    rows = _catmull(TRUNK)
    z_c, w_c, f_c, b_c = TRUNK[-1]
    yc, hd = (f_c + b_c) / 2, (b_c - f_c) / 2
    for k in range(1, 7):                               # the corner: width turns in, depth rounds a little
        th = math.radians(15 * k)
        w = w_c - SHOULDER_R + SHOULDER_R * math.cos(th)
        z = z_c + (SHOULDER_TOP - z_c) * math.sin(th)
        h = hd * (1 - 0.30 * (1 - math.cos(th)))      # rounder in profile than from the front
        rows.append((z, w, yc - h, yc + h))
    w0, z0, f0, b0 = rows[-1][1], rows[-1][0], rows[-1][2], rows[-1][3]
    wt, zt, ft, bt = COLLAR_RING
    for t in (0.3, 0.6, 0.85, 1.0):                     # level top, rising only at the collar
        rows.append((z0 + (zt - z0) * t * t, w0 + (wt - w0) * t, f0 + (ft - f0) * t, b0 + (bt - b0) * t))
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


# ------------------------------------------------------------------ body data
def _joints():
    j = {}
    # Long sleeves: shoulder (its cap hidden inside the trunk's shoulder block, the tube emerging
    # under it flush with the block's plumb flank) -> elbow -> sleeve end at elbow->wrist 0.86 (§7.4
    # derived joint). The arms hang nearly plumb, so the outline drops straight from the square
    # corner with no deltoid bump. Right side 2 cm back, 8 mm low.
    for s, sx, dy, dz in (("l", 1, 0.0, 0.0), ("r", -1, 0.02, -0.008)):
        el = Vector((sx * 0.282, -0.128 + dy, 1.305 + dz))
        wr = Vector((sx * 0.302, -0.188 + dy, 1.035 + dz))
        j.update({
            "shoulder_" + s: ((sx * 0.272, -0.118 + dy * 0.5, 1.505 + dz), 0.055),
            "elbow_" + s: (tuple(el), 0.052),
            "sleeve_" + s: (tuple(el.lerp(wr, 0.86)), 0.047),
            # Bare hands start inside the cuff (elbow->wrist 0.80): palm + mitten fingers + thumb.
            "handin_" + s: (tuple(el.lerp(wr, 0.80)), 0.031),
            "wrist_" + s: (tuple(wr), 0.034),
            "knuckle_" + s: ((sx * 0.308, -0.206 + dy, 0.942 + dz), (0.021, 0.046)),
            "fing_" + s: ((sx * 0.300, -0.216 + dy, 0.890 + dz), (0.018, 0.040)),
            "tip_" + s: ((sx * 0.288, -0.210 + dy, 0.856 + dz), (0.014, 0.030)),
            "thumb0_" + s: ((sx * 0.298, -0.214 + dy, 1.002 + dz), 0.017),
            "thumb1_" + s: ((sx * 0.290, -0.241 + dy, 0.958 + dz), 0.015),
            "thumb2_" + s: ((sx * 0.282, -0.250 + dy, 0.926 + dz), 0.012),
        })
    # Neck: rises forward out of the collar into the hung head.
    j.update({
        "neck_base": ((0, -0.130, 1.585), 0.060),
        "neck": ((0, -0.188, 1.620), 0.056),
        "neck_top": ((0, -0.240, 1.640), 0.052),
    })
    # Trousers: two separate leg chains, each rooted at waist_l/_r behind the belt (§7.0, §7.4);
    # no shared pelvis node, so no crotch sheet and no trouser arch hanging under the shirt. The
    # roots start 4.5 cm higher than §7.4 (their rounded ends hide inside the shirt, above the belt)
    # and they and the hips sit 1-1.5 cm nearer the middle, so the two seats overlap: one seat down
    # to the crotch, instead of two leg tops parting right under the belt.
    j.update({
        "waist_l": ((0.075, 0.07, 0.975), (0.120, 0.110)), "waist_r": ((-0.075, 0.08, 0.975), (0.120, 0.110)),
        "hip_l": ((0.095, 0.10, 0.82), 0.115), "hip_r": ((-0.095, 0.12, 0.82), 0.115),
        "knee_l": ((0.11, -0.05, 0.46), 0.074), "knee_r": ((-0.11, 0.21, 0.45), 0.074),
        "ankle_l": ((0.11, -0.10, 0.125), 0.057), "ankle_r": ((-0.11, 0.31, 0.142), 0.057),
        "cuff_l": ((0.11, -0.106, 0.084), 0.062), "cuff_r": ((-0.11, 0.322, 0.104), 0.062),
    })
    # Shoe uppers: from inside the trouser hem down into the shoe.
    j.update({
        "shin_l": ((0.11, -0.090, 0.20), 0.044), "sock_l": ((0.11, -0.105, 0.070), 0.048),
        "shin_r": ((-0.11, 0.290, 0.215), 0.044), "sock_r": ((-0.11, 0.318, 0.090), 0.048),
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


# ------------------------------------------------------------------ parts
def _head(kit):
    """Toner skull + hair: an egg-headed ellipsoid, jaw narrower, nape tucked, front cut flat."""
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=34, v_segments=20, radius=1.0)
    for v in bm.verts:
        x, y, z = v.co
        x *= HEAD_HX
        y *= HEAD_HY_FRONT if y < 0 else HEAD_HY_BACK
        z *= HEAD_HZ_TOP if z > 0 else HEAD_HZ_BOT
        if z < 0:
            k = -z / HEAD_HZ_BOT
            x *= 1 - 0.22 * k ** 2                   # jaw narrower than the cranium
            if y > 0:
                y *= 1 - 0.40 * k ** 1.5             # nape tucks in above the neck
                z *= 1 - 0.30 * min(1.0, y / HEAD_HY_BACK)   # skull base higher than the chin
        if y < -HEAD_FRONT:
            y = -HEAD_FRONT                          # the face has no relief
        v.co = (x, y, z)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    # Hair and the shadow band round the face stay toner; round the ear and down the nape is paper
    # (toner-shaded by the edge term), so in profile the dark dome reads as hair on a hung head, not
    # a helmet. The hairline is cut into the mesh with planes (a clean, graphic edge, like a
    # cut-out), not stepped along faces.
    cuts = [(HAIR_BAND, Vector((0, 1, 0)))]
    for a, b in HAIRLINE:
        d = Vector(b) - Vector(a)
        cuts.append((Vector(a), Vector((0, -d.z, d.y)).normalized()))
    for co, no in cuts:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=co, plane_no=no)
    obj = _new_mesh(kit, bm, TONER, "head")
    obj.data.materials.append(kit._material(PAPER))
    for poly in obj.data.polygons:
        c = poly.center
        if all((c - co).dot(no) > 0 for co, no in cuts[:1]) and all((c - co).dot(no) < 0 for co, no in cuts[1:]):
            poly.material_index = 1
    kit._place(obj, tuple(HEAD_C), HEAD_ROT)
    return obj


def _shoe(kit, loc, rot, name):
    def shape(p):
        hl = 0.1275
        f = max(0.0, -p.y / hl)          # toward the toe
        b = max(0.0, p.y / hl)           # toward the heel
        if p.z > 0:
            p.z *= 1 - 0.40 * f ** 1.3   # low toe box, instep rising to the ankle
        else:
            p.z += 0.010 * max(0.0, f - 0.6) ** 2 / 0.16   # toe spring
        p.x *= (1 - 0.18 * f ** 2.5) * (1 - 0.12 * b ** 2)
        return p
    shoe = kit.soft_box((0.096, 0.255, 0.094), loc, TONER, radius=0.026, segments=20, rings=10, rot=rot, name=name)
    _reshape(shoe, shape)
    return shoe


def _belt(kit, objs, z, centre_y, n=48):
    """An elliptical band fitted to the measured waist (rays cast inward), so it never hoops or sinks."""
    tree = _bvh(objs)
    c = Vector((0.0, centre_y, z))
    rad = []
    for i in range(n):
        a = 2 * math.pi * i / n
        d = Vector((math.cos(a), math.sin(a), 0.0))
        r = 0.0
        for dz in (-0.022, -0.011, 0.0, 0.011, 0.022):
            loc, _n, _i, _d = tree.ray_cast(c + d * 0.6 + Vector((0, 0, dz)), -d)
            if loc is not None:
                r = max(r, (loc - c - Vector((0, 0, dz))).length)
        rad.append((r or 0.17) + 0.006)
    rings = []
    for dz, grow in ((-0.024, -0.010), (-0.020, 0.0), (0.020, 0.0), (0.024, -0.010)):
        rings.append([c + Vector((math.cos(2 * math.pi * i / n) * (r + grow), math.sin(2 * math.pi * i / n) * (r + grow), dz))
                      for i, r in enumerate(rad)])
    return _band(kit, rings, TONER, "belt")


def _tube_radius(obj, point, axis, slab=0.008, reach=0.12):
    """Mean distance from an axis of the mesh vertices in a thin slab across it (a measured tube radius)."""
    ds = []
    for v in obj.data.vertices:
        d = v.co - point
        h = d.dot(axis)
        if abs(h) < slab:
            r = (d - axis * h).length
            if r < reach:
                ds.append(r)
    return sum(ds) / len(ds) if ds else 0.05


def _cuff(kit, end, axis, radius, name):
    """A buttoned shirt cuff round the end of a long sleeve: a band 5 mm proud of the sleeve, its
    lower lip turned in to the wrist (the hand comes out of it), and the stitch line at its top
    printed as one thin toner ring. ``end`` is the wrist end of the cuff, ``axis`` points down the arm."""
    q = Vector((0, 0, -1)).rotation_difference(axis)          # local +Z runs up the arm
    rot = [math.degrees(a) for a in q.to_euler("XYZ")]
    ro = radius + 0.005
    band = kit.lathe([(0.024, 0.0), (ro - 0.003, 0.0), (ro, 0.004), (ro, 0.050), (ro - 0.004, 0.055),
                      (radius - 0.008, 0.058)], tuple(end), PAPER, verts=24, rot=rot, name="cuff_" + name,
                     close_top=False, close_bottom=False)
    seam = kit.lathe([(ro + 0.0002, 0.041), (ro + 0.0016, 0.042), (ro + 0.0016, 0.046), (ro + 0.0002, 0.047)],
                     tuple(end), TONER, verts=16, rot=rot, name="cuff_seam_" + name, close_top=False, close_bottom=False)
    return band, seam


# ------------------------------------------------------------------ build
def build(kit, cl):
    global EYE
    j = _joints()

    # --- shirt (paper): the trunk printed as a page; long sleeves with buttoned cuffs
    shirt = _trunk(kit)
    sleeves, cuffs, hands = [], [], []
    for s in ("l", "r"):
        sleeve = _skin(kit, cl, j, [("shoulder_" + s, "elbow_" + s), ("elbow_" + s, "sleeve_" + s)], PAPER, "sleeve_" + s,
                       max_tris=520)
        sleeves.append(sleeve)
        el, sl = Vector(j["elbow_" + s][0]), Vector(j["sleeve_" + s][0])
        ax = (sl - el).normalized()
        r_meas = _tube_radius(sleeve, sl - ax * 0.035, ax)    # the subdivided sleeve is thinner than its skin radius
        band, _seam = _cuff(kit, sl + ax * 0.030, ax, r_meas, s)
        cuffs.append(band)
        # bare hands, paper like the rest of the print (toner-shaded by the edge term)
        hands.append(_skin(kit, cl, j, [("handin_" + s, "wrist_" + s), ("wrist_" + s, "knuckle_" + s),
                                         ("knuckle_" + s, "fing_" + s), ("fing_" + s, "tip_" + s),
                                         ("thumb0_" + s, "thumb1_" + s), ("thumb1_" + s, "thumb2_" + s)],
                           PAPER, "hand_" + s, max_tris=720))

    # --- neck (paper)
    neck = _skin(kit, cl, j, [("neck_base", "neck"), ("neck", "neck_top")], PAPER, "neck")

    # --- trousers (toner): two leg chains from waist_l/_r
    trousers = _skin(kit, cl, j, [("waist_l", "hip_l"), ("hip_l", "knee_l"), ("knee_l", "ankle_l"), ("ankle_l", "cuff_l"),
                                  ("waist_r", "hip_r"), ("hip_r", "knee_r"), ("knee_r", "ankle_r"), ("ankle_r", "cuff_r")],
                     TONER, "trousers", max_tris=1600)

    # --- shoes (toner): soft-soled office shoes; the right heel is raised (mid-stride)
    _shoe(kit, (0.11, -0.160, 0.047), (0, 0, 2), "shoe_l")
    _shoe(kit, (-0.11, 0.244, 0.070), (10, 0, -2), "shoe_r")
    _skin(kit, cl, j, [("shin_l", "sock_l")], TONER, "upper_l")
    _skin(kit, cl, j, [("shin_r", "sock_r")], TONER, "upper_r")

    # --- belt (toner) fitted round shirt + trouser tops
    _belt(kit, [shirt, trousers], 0.955, 0.07)

    # --- head: toner skull/hair cut flat, paper ears, the paper face and its print
    H = _head_matrix()
    head = _head(kit)
    ears = []
    for sx in (1, -1):
        # Pale ears outside the toner mass: the dark dome reads as hair on a head, not a helmet.
        ears.append(cl.ellipsoid(kit, (0.024, 0.046, 0.062), tuple(H @ Vector((sx * 0.090, 0.016, -0.016))), PAPER,
                                 rot=(HEAD_ROT[0], HEAD_ROT[1], HEAD_ROT[2] + sx * 8.0), segments=12, rings=8, name="ear"))
    face = _face_outline()
    paper_y = -HEAD_FRONT - 0.0001                  # flush with the cut skull: a print, not a mask
    _on_head(kit, face, paper_y, 0.0024, PAPER, "face_paper")
    ink_y = -HEAD_FRONT - 0.0018
    fz = FACE_Z
    ink = []
    eye = _ellipse(0.034, fz + 0.022, 0.040, 0.022, n=16, droop=0.004, power=0.85)
    brow = _stroke([(0.015, fz + 0.050), (0.037, fz + 0.046), (0.060, fz + 0.036)], 0.010, 0.6)
    nostril = _ellipse(0.010, fz - 0.032, 0.011, 0.007, n=10)
    for shape in (eye, brow, nostril):
        ink += [shape, _mirror(shape)]
    ink.append(_stroke([(-0.010, fz + 0.016), (-0.012, fz - 0.006), (-0.016, fz - 0.024)], 0.005, 0.6))   # nose side
    ink.append(_stroke([(-0.026, fz - 0.064), (-0.012, fz - 0.058), (0.0, fz - 0.057), (0.012, fz - 0.058),
                        (0.026, fz - 0.064)], 0.006, 0.5))                                                    # mouth
    ink.append(_ellipse(0.0, fz - 0.073, 0.022, 0.006, n=10))                                                # under-lip
    for k, outline in enumerate(ink):
        _on_head(kit, outline, ink_y, 0.0010, TONER, "print_%d" % k)
    v0, v1 = _v_range(face, STREAK_X)
    _on_head(kit, [(STREAK_X - 0.002, v0 + 0.002), (STREAK_X + 0.002, v0 + 0.002),
                   (STREAK_X + 0.002, v1 - 0.002), (STREAK_X - 0.002, v1 - 0.002)], ink_y, 0.0010, TONER, "streak_face")

    # --- collar (paper): a short band round the neck base, axis along the neck
    nb, nk = Vector(j["neck_base"][0]), Vector(j["neck"][0])
    axis = (nk - nb).normalized()
    tilt = math.degrees(math.atan2(-axis.y, axis.z))
    collar = kit.cylinder(0.067, 0.034, tuple(nb - axis * 0.004 + Vector((0, -0.004, 0))), PAPER, radius_top=0.062,
                          verts=28, rot=(tilt, 0, 0), name="collar")

    # --- tie (toner): knot at the collar, blade lying on the shirt front; too short for the stretched trunk
    tree = _bvh([shirt])
    hits = [_front(tree, 0.0, 1.548 - 0.022 * i) for i in range(18)]
    hits = [h for h in hits if h and 1.175 <= h[0].z <= 1.548]
    if len(hits) >= 3:
        top, end = hits[0][0].z, hits[-1][0].z
        widths = [0.038 + (0.080 - 0.038) * (top - h[0].z) / (top - end) for h in hits]
        _strip(kit, [h[0] + Vector((0, 0.002, 0)) for h in hits], widths, [Vector((0, -1, 0))] * len(hits), 0.011, TONER,
               "tie", tip=0.042)
    kn = _front(tree, 0.0, 1.562)
    if kn:
        kit.soft_box((0.046, 0.030, 0.042), tuple(kn[0] + Vector((0, -0.010, 0))), TONER, radius=0.012, segments=12,
                     rings=8, rot=(-12, 0, 0), name="knot")

    # --- breast pocket (stretched with the trunk: 1.8x taller than wide) and a pen
    pocket = _pocket(kit, tree, 0.104, 0.092, 1.468, 1.300)
    pa, pb = _front(tree, 0.086, 1.430), _front(tree, 0.086, 1.490)
    if pa and pb:
        d = (pb[0] - pa[0]).normalized()
        mid = (pa[0] + pb[0]) / 2 + pa[1] * 0.0075 + d * 0.012
        kit.cylinder(0.0055, 0.085, tuple(mid), TONER, verts=10, rot=(math.degrees(math.atan2(-d.y, d.z)), 0, 0), name="pen")

    # --- page-slip mark: the drum streak continues down the shirt front, in line with the one on the face
    sh = [_front(tree, STREAK_X - 0.006, 1.56 - 0.02 * i) for i in range(30)]
    sh = [h for h in sh if h and 0.985 <= h[0].z <= 1.56]
    if len(sh) >= 3:
        _strip(kit, [h[0] + h[1] * 0.0006 for h in sh], [0.004] * len(sh), [h[1] for h in sh], 0.0010, TONER, "streak_shirt")

    cl.floor_parts(kit)
    head_floor = head.location.z - HEAD_C.z
    EYE = round((H @ Vector((0, paper_y, FACE_Z))).z + head_floor, 3)
    weights = {shirt: 1.0, sleeves[0]: 1.0, sleeves[1]: 1.0, cuffs[0]: 0.8, cuffs[1]: 0.8, pocket: 1.0,
               collar: 0.6, neck: 0.8, hands[0]: 0.6, hands[1]: 0.6, head: 0.55, ears[0]: 0.55, ears[1]: 0.55}
    _toner_edges(kit, weights)
    kit.no_collider()


def _toner_edges(kit, weights):
    """The 'printed' paper: up- and front-facing planes stay paper-white, flanks and undersides go
    toner-grey (a baked darkening toward the silhouette edge, doc 10 §5), so the figure draws its own
    dark outline against yellow wallpaper. The back-facing term is kept small: a copy is dark at its
    edges, not dirty all over its back. Stored as a colour attribute 'toner' on every part (1 = no
    change) and multiplied into the Paper slot (the toner slot is dark already)."""
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
