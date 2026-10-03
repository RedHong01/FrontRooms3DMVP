"""Hunter direction C — "Duplicate" (Documentation/research/hunter/10_hunter_directions.md §5, §7.4).

A bad photocopy of an employee: toner-black head with a flat printed paper face,
a white short-sleeved shirt stretched over a trunk as long as the legs, oxblood
tie, navy trousers, soft black office shoes. Built in the "copy's step" render
pose (Hunt slump; also the pose of every static copy).

Coordinates are the spec's (metres, Z up, facing -Y, left = +X) before flooring.
Deviations from §7.4 are noted where they happen (see also the design notes).
"""

import math

import bmesh
import bpy
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


# ------------------------------------------------------------------ body data
def _joints():
    j = {}
    # Shirt torso: one vertical chain from the hem (tucked under the belt) to the collar.
    j.update({
        "hem": ((0, 0.072, 0.925), (0.158, 0.112)),
        "waist": ((0, 0.07, 0.955), (0.178, 0.138)),
        "belly": ((0, 0.012, 1.13), (0.204, 0.198)),     # the paunch (deep, not wide)
        "chest": ((0, -0.062, 1.385), (0.208, 0.150)),
        "upper": ((0, -0.098, 1.495), (0.228, 0.130)),
        "shoulders": ((0, -0.115, 1.560), (0.262, 0.106)),   # the shoulder line belongs to the torso block
        "trap": ((0, -0.128, 1.618), (0.105, 0.080)),        # trapezius slope up to the collar
    })
    # Short sleeves: a straight cone per side from inside the torso's shoulder corner (no bend node,
    # so no ball-joint deltoid).
    for s, sx, dz in (("l", 1, 0.0), ("r", -1, -0.008)):
        j.update({
            "shoulder_" + s: ((sx * 0.220, -0.118, 1.550 + dz), 0.062),
            "sleeve_" + s: ((sx * 0.283, -0.126, 1.405 + dz), 0.061),
        })
    # Bare arms (start inside the sleeves) and hands: palm + mitten fingers + thumb.
    for s, sx, dy, dz in (("l", 1, 0.0, 0.0), ("r", -1, 0.02, -0.008)):
        j.update({
            "armin_" + s: ((sx * 0.272, -0.124 + dy, 1.45 + dz), 0.045),
            "elbow_" + s: ((sx * 0.296, -0.128 + dy, 1.305 + dz), 0.047),
            "wrist_" + s: ((sx * 0.316, -0.188 + dy, 1.035 + dz), 0.035),
            "knuckle_" + s: ((sx * 0.322, -0.206 + dy, 0.942 + dz), (0.021, 0.046)),
            "fing_" + s: ((sx * 0.314, -0.216 + dy, 0.890 + dz), (0.018, 0.040)),
            "tip_" + s: ((sx * 0.302, -0.210 + dy, 0.856 + dz), (0.014, 0.030)),
            "thumb0_" + s: ((sx * 0.312, -0.214 + dy, 1.002 + dz), 0.017),
            "thumb1_" + s: ((sx * 0.304, -0.241 + dy, 0.958 + dz), 0.015),
            "thumb2_" + s: ((sx * 0.296, -0.250 + dy, 0.926 + dz), 0.012),
        })
    # Neck: rises forward out of the collar into the hung head.
    j.update({
        "neck_base": ((0, -0.130, 1.585), 0.060),
        "neck": ((0, -0.188, 1.620), 0.056),
        "neck_top": ((0, -0.240, 1.640), 0.052),
    })
    # Trousers: a seat chain plus two separate leg chains that start inside it.
    j.update({
        "waist_t": ((0, 0.07, 0.972), (0.182, 0.142)),
        "pelvis": ((0, 0.092, 0.872), (0.182, 0.122)),
        "seat_l": ((0.090, 0.095, 0.905), 0.112), "seat_r": ((-0.090, 0.105, 0.905), 0.112),
        "hip_l": ((0.102, 0.10, 0.78), 0.104), "hip_r": ((-0.102, 0.12, 0.78), 0.104),
        "knee_l": ((0.11, -0.05, 0.46), 0.072), "knee_r": ((-0.11, 0.21, 0.45), 0.072),
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
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=22, radius=1.0)
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
    # Hair and the shadow band round the face stay toner; round the ear and down the nape is skin,
    # so in profile the dark dome reads as hair on a hung head, not a helmet. The hairline is cut
    # into the mesh with planes (a clean, graphic edge, like a cut-out), not stepped along faces.
    cuts = [(HAIR_BAND, Vector((0, 1, 0)))]
    for a, b in HAIRLINE:
        d = Vector(b) - Vector(a)
        cuts.append((Vector(a), Vector((0, -d.z, d.y)).normalized()))
    for co, no in cuts:
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-6, plane_co=co, plane_no=no)
    obj = _new_mesh(kit, bm, TONER, "head")
    obj.data.materials.append(kit._material(SKIN))
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
    shoe = kit.soft_box((0.096, 0.255, 0.094), loc, SHOE, radius=0.026, segments=24, rings=12, rot=rot, name=name)
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
    return _band(kit, rings, SHOE, "belt")


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


def _sleeve_hem(kit, top, bottom, radius, name):
    """An open, slightly flared cuff at the end of a short sleeve (axis top -> bottom)."""
    axis = (bottom - top).normalized()
    prof = [(radius * 0.92, 0.028), (radius * 1.00, 0.0), (radius * 1.03, -0.010), (radius * 0.93, -0.012), (radius * 0.82, 0.010)]
    q = Vector((0, 0, -1)).rotation_difference(axis)
    rot = [math.degrees(a) for a in q.to_euler("XYZ")]
    return kit.lathe(prof, tuple(bottom), PAPER, verts=24, rot=rot, name=name, close_top=False, close_bottom=False)


# ------------------------------------------------------------------ build
def build(kit, cl):
    global EYE
    j = _joints()

    # --- shirt (paper white): one long torso chain; each short sleeve its own straight cone + open hem
    shirt = _skin(kit, cl, j, [
        ("hem", "waist"), ("waist", "belly"), ("belly", "chest"), ("chest", "upper"), ("upper", "shoulders"),
        ("shoulders", "trap"),
    ], PAPER, "shirt")
    sleeves = []
    for s in ("l", "r"):
        sleeve = _skin(kit, cl, j, [("shoulder_" + s, "sleeve_" + s)], PAPER, "sleeve_" + s)
        sleeves.append(sleeve)
        sh, sl = Vector(j["shoulder_" + s][0]), Vector(j["sleeve_" + s][0])
        ax = (sl - sh).normalized()
        r_meas = _tube_radius(sleeve, sl - ax * 0.03, ax)      # the subdivided sleeve is thinner than its skin radius
        _sleeve_hem(kit, sh, sl - ax * 0.012, r_meas + 0.002, "hem_" + s)

    # --- bare arms and hands
    arms = []
    for s in ("l", "r"):
        arms.append(_skin(kit, cl, j, [("armin_" + s, "elbow_" + s), ("elbow_" + s, "wrist_" + s),
                                        ("wrist_" + s, "knuckle_" + s), ("knuckle_" + s, "fing_" + s),
                                        ("fing_" + s, "tip_" + s), ("thumb0_" + s, "thumb1_" + s),
                                        ("thumb1_" + s, "thumb2_" + s)], SKIN, "arm_" + s, max_tris=1500))

    # --- neck
    neck = _skin(kit, cl, j, [("neck_base", "neck"), ("neck", "neck_top")], SKIN, "neck")

    # --- trousers
    trousers = _skin(kit, cl, j, [("waist_t", "pelvis"),
                                  ("seat_l", "hip_l"), ("hip_l", "knee_l"), ("knee_l", "ankle_l"), ("ankle_l", "cuff_l"),
                                  ("seat_r", "hip_r"), ("hip_r", "knee_r"), ("knee_r", "ankle_r"), ("ankle_r", "cuff_r")],
                     NAVY, "trousers")

    # --- shoes: soft-soled office shoes; the right heel is raised (mid-stride)
    _shoe(kit, (0.11, -0.160, 0.047), (0, 0, 2), "shoe_l")
    _shoe(kit, (-0.11, 0.244, 0.070), (10, 0, -2), "shoe_r")
    _skin(kit, cl, j, [("shin_l", "sock_l")], SHOE, "upper_l")
    _skin(kit, cl, j, [("shin_r", "sock_r")], SHOE, "upper_r")

    # --- belt fitted round shirt + trouser top
    _belt(kit, [shirt, trousers], 0.955, 0.07)

    # --- head: toner skull/hair cut flat, ears, the paper face and its print
    H = _head_matrix()
    head = _head(kit)
    for sx in (1, -1):
        # Pale ears outside the toner mass: the dark dome reads as hair on a head, not a helmet.
        cl.ellipsoid(kit, (0.024, 0.046, 0.062), tuple(H @ Vector((sx * 0.090, 0.016, -0.016))), SKIN,
                     rot=(HEAD_ROT[0], HEAD_ROT[1], HEAD_ROT[2] + sx * 8.0), segments=12, rings=8, name="ear")
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

    # --- collar: a short band round the neck base, axis along the neck
    nb, nk = Vector(j["neck_base"][0]), Vector(j["neck"][0])
    axis = (nk - nb).normalized()
    tilt = math.degrees(math.atan2(-axis.y, axis.z))
    kit.cylinder(0.067, 0.034, tuple(nb - axis * 0.004 + Vector((0, -0.004, 0))), PAPER, radius_top=0.062, verts=28,
                 rot=(tilt, 0, 0), name="collar")

    # --- tie: knot at the collar, blade lying on the shirt front; too short for the stretched trunk
    tree = _bvh([shirt])
    hits = [_front(tree, 0.0, 1.548 - 0.022 * i) for i in range(18)]
    hits = [h for h in hits if h and 1.175 <= h[0].z <= 1.548]
    if len(hits) >= 3:
        top, end = hits[0][0].z, hits[-1][0].z
        widths = [0.038 + (0.080 - 0.038) * (top - h[0].z) / (top - end) for h in hits]
        _strip(kit, [h[0] + Vector((0, 0.002, 0)) for h in hits], widths, [Vector((0, -1, 0))] * len(hits), 0.011, TIE, "tie",
               tip=0.042)
    kn = _front(tree, 0.0, 1.562)
    if kn:
        kit.soft_box((0.046, 0.030, 0.042), tuple(kn[0] + Vector((0, -0.010, 0))), TIE, radius=0.012, segments=12, rings=8,
                     rot=(-12, 0, 0), name="knot")

    # --- breast pocket (stretched with the trunk: 1.8x taller than wide) and a pen
    _pocket(kit, tree, 0.104, 0.092, 1.468, 1.300)
    pa, pb = _front(tree, 0.086, 1.430), _front(tree, 0.086, 1.490)
    if pa and pb:
        d = (pb[0] - pa[0]).normalized()
        mid = (pa[0] + pb[0]) / 2 + pa[1] * 0.0075 + d * 0.012
        kit.cylinder(0.0055, 0.085, tuple(mid), TONER, verts=10, rot=(math.degrees(math.atan2(-d.y, d.z)), 0, 0), name="pen")

    # --- the drum streak continues down the shirt front, in line with the one on the face
    sh = [_front(tree, STREAK_X - 0.006, 1.56 - 0.02 * i) for i in range(30)]
    sh = [h for h in sh if h and 0.985 <= h[0].z <= 1.56]
    if len(sh) >= 3:
        _strip(kit, [h[0] + h[1] * 0.0006 for h in sh], [0.004] * len(sh), [h[1] for h in sh], 0.0010, TONER, "streak_shirt")

    cl.floor_parts(kit)
    head_floor = head.location.z - HEAD_C.z
    EYE = round((H @ Vector((0, paper_y, FACE_Z))).z + head_floor, 3)
    _toner_edges(kit, {shirt: 1.0, sleeves[0]: 1.0, sleeves[1]: 1.0, neck: 0.6, arms[0]: 0.45, arms[1]: 0.45})
    kit.no_collider()


def _toner_edges(kit, weights):
    """The 'printed' shirt: up- and front-facing planes stay paper-white, flanks and undersides go
    toner-grey (a baked darkening toward the silhouette edge, doc 10 §5). Stored as a colour
    attribute 'toner' on every part (1 = no change) and multiplied into the Paper/Skin slots."""
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
                back = _smooth(0.20, 0.90, n.y)
                val = max(0.34, 1.0 - w * (0.60 * side + 0.42 * down + 0.25 * back))
            attr.data[i].color = (val, val, val, 1.0)
    for slot in (PAPER, SKIN):
        mat = bpy.data.materials.get(slot)
        if mat is None or not mat.use_nodes:
            continue
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
