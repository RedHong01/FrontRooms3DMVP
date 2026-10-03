"""1980s-90s upholstered club armchair (Still B: the teal tweed chair that
"rolled off" the tower and sits upright 1 m out; B7 is the oatmeal one).

Construction:
* One continuous upholstered "tub": deep, fat rounded arms that sweep round
  the back corners and rise into a rounded back roll (lofted along a U path
  in plan; the section changes from the 0.165 m arm to the 0.15 m back and the
  top line climbs from 0.62 to 0.82 m through the corners).
* Padded arm fronts with a piping welt; the arms run past the seat front.
  A second welt follows the outside seam (under the widest point of the
  roll) all round the tub and runs over the arm noses into the front welts.
* Tight (attached) inner back: a raked, puffed pad set into the tub.
* Loose seat cushion (kit.soft_box with sag toward the front) with a welted
  top seam, on an upholstered deck with a front rail.
* Four short tapered dark-wood feet; black cambric dust cover underneath.

Real-world reference size: 0.85 W x 0.85 D x 0.82 H; seat 0.44, arms 0.62.
Front (seat) faces -Y. Origin = floor under the centre.
Slots: Prop_FabricTeal (variant swaps it to oatmeal), Prop_WoodDark (feet),
Prop_FabricChair (dust cover).
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_ClubChair"
LOD1 = 0.4
SMOOTH_ANGLE = 70.0
VARIANTS = {"Kit_ClubChair_Oatmeal": {"Prop_FabricTeal": "Prop_FabricBeige"}}

FABRIC = "Prop_FabricTeal"
WOOD = "Prop_WoodDark"
CAMBRIC = "Prop_FabricChair"

FOOT_H = 0.075         # underside of the upholstered body
DECK = 0.295           # top of the seat deck
ARM_X = 0.329          # arm section centre line (outer welt at 0.425)
ARM_W, BACK_W = 0.165, 0.150
ARM_H, BACK_H = 0.620, 0.820
ARM_FRONT = -0.400
CORNER_R = 0.150
SEAM = 13              # section point at the outer side of the roll (arc 0 deg)
BACK_Y = 0.4115 - BACK_W / 2   # back roll centre line (outer welt at 0.425)


# --------------------------------------------------------------------- helpers
def _arc(cx, cz, r, a0, a1, n):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _normals2d(pts):
    """Outward vertex normals of a closed 2D outline (either winding)."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sgn = 1.0 if area > 0 else -1.0
    out = []
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        acc = [0.0, 0.0]
        for a, b in ((p0, p1), (p1, p2)):
            dx, dz = b[0] - a[0], b[1] - a[1]
            l = math.hypot(dx, dz) or 1.0
            acc[0] += sgn * dz / l
            acc[1] += -sgn * dx / l
        l = math.hypot(*acc) or 1.0
        out.append((acc[0] / l, acc[1] / l))
    return out


def _loft(kit, rings, slot, name, cap0=None, cap1=None):
    """Quads between consecutive rings (equal point counts). cap0 / cap1:
    None = n-gon, "tri" = flat cap ear-clip triangulated (concave outlines),
    a 3D point = triangle fan to that point (domed end)."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for a, b in zip(vs, vs[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    for ring, cap in ((vs[0], cap0), (vs[-1], cap1)):
        if cap is None:
            bm.faces.new(ring)
        elif cap == "tri":
            f = bm.faces.new(ring)
            f.normal_update()          # polyfill projects on the face normal
            bmesh.ops.triangulate(bm, faces=[f], quad_method="BEAUTY", ngon_method="EAR_CLIP")
        else:
            c = bm.verts.new(cap)
            for i in range(n):
                bm.faces.new((c, ring[(i + 1) % n], ring[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _welt(kit, points, radius, slot, verts=6, name="welt"):
    """Piping cord along a 3D polyline (parallel-transport frame, open ends)."""
    pts = [Vector(p) for p in points]
    bm = bmesh.new()
    rings = []
    normal = None
    for k, p in enumerate(pts):
        if k == 0:
            t = pts[1] - pts[0]
        elif k == len(pts) - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[k + 1] - pts[k]).normalized() + (pts[k] - pts[k - 1]).normalized()
        t.normalize()
        if normal is None:
            ref = Vector((0, 1, 0)) if abs(t.y) < 0.9 else Vector((1, 0, 0))
            normal = (ref - t * ref.dot(t)).normalized()
        else:
            normal = (normal - t * normal.dot(t)).normalized()
        bi = t.cross(normal)
        rings.append([bm.verts.new(p + (normal * math.cos(2 * math.pi * i / verts) +
                                        bi * math.sin(2 * math.pi * i / verts)) * radius) for i in range(verts)])
    for a, b in zip(rings, rings[1:]):
        for i in range(verts):
            j = (i + 1) % verts
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _clip_above(loop, zmin):
    """The part of a closed (s, z) outline above z = zmin, as one open
    polyline with exact end points on z = zmin (welts that stop at a rail)."""
    n = len(loop)
    start = next(i for i in range(n) if loop[i][1] < zmin)
    seq = [loop[(start + k) % n] for k in range(n + 1)]
    out = []
    for a, b in zip(seq, seq[1:]):
        if (a[1] < zmin) != (b[1] < zmin):
            t = (zmin - a[1]) / (b[1] - a[1])
            out.append((a[0] + (b[0] - a[0]) * t, zmin))
        if b[1] >= zmin:
            out.append(b)
    return out


def _soft_point(size, radius, u, v, sag=0.0, puff=0.0):
    """A point of kit.soft_box's surface at parameters (u, v) (same formula)
    and its approximate outward normal: for welts on its seams."""
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    e = max(0.08, min(0.6, radius / max(min(size), 1e-3) * 1.5))

    def c(w):
        return math.copysign(abs(math.cos(w)) ** e, math.cos(w))

    def sn(w):
        return math.copysign(abs(math.sin(w)) ** e, math.sin(w))
    x, y, z = hx * c(u) * c(v), hy * c(u) * sn(v), hz * sn(u)
    ux, uy, uz = x / hx, y / hy, z / hz
    n = Vector((ux / hx, uy / hy, uz / hz)).normalized()
    if puff:
        x += puff * ux * max(0.0, 1 - uy * uy) * max(0.0, 1 - uz * uz)
        y += puff * uy * max(0.0, 1 - ux * ux) * max(0.0, 1 - uz * uz)
        z += puff * 0.5 * uz * max(0.0, 1 - ux * ux) * max(0.0, 1 - uy * uy)
    if sag and uz > 0:
        z -= sag * uz * max(0.0, 1 - ux * ux) * max(0.0, 1 - uy * uy)
    return Vector((x, y, z)), n


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# ------------------------------------------------------------------- the tub
def _section(w, h):
    """Arm/back cross-section (s, z): s = offset along the outward normal.
    Flat inner face, fat round top, the outer face flaring slightly out."""
    r = w / 2
    pts = [(-w / 2, FOOT_H), (-w / 2, DECK - 0.02), (-w / 2, h - r - 0.06)]
    pts += _arc(0.004, h - r, r, 180.0, 0.0, 10)[0:]
    pts[3] = (-w / 2, h - r)                     # keep the inner face exactly vertical
    pts += [(w / 2 - 0.006, h - r - 0.10), (w / 2 - 0.012, FOOT_H)]
    return pts


def _tub(kit):
    # Right half: back centre -> corner -> right arm (towards the front).
    cy = BACK_Y - CORNER_R
    cx = ARM_X - CORNER_R
    right = [(0.0, BACK_Y, 0.0, 1.0), (0.075, BACK_Y, 0.0, 1.0)]
    for i in range(1, 10):
        a = math.radians(90.0 - 90.0 * i / 9)
        right.append((cx + CORNER_R * math.cos(a), cy + CORNER_R * math.sin(a), math.cos(a), math.sin(a)))
    for y in (0.10, -0.08, -0.25):
        right.append((ARM_X, y, 1.0, 0.0))
    # (x, y, nx, ny): outward normal in plan. Arc length for the blends.
    left = [(-x, y, -nx, ny) for x, y, nx, ny in reversed(right[1:])]
    path = left + right
    # blend 0 at the arms, 1 at the back, eased through the corners
    def blend(x, y):
        if y <= cy:
            return 0.25 * _smooth((y - 0.02) / (cy - 0.02))
        a = math.atan2(y - cy, abs(x) - cx) if abs(x) > cx else math.pi / 2
        return 0.25 + 0.75 * _smooth(a / (math.pi / 2))

    def ring(x, y, nx, ny, inset=0.0, dy=0.0):
        b = blend(x, y)
        w = ARM_W + (BACK_W - ARM_W) * b
        h = ARM_H + (BACK_H - ARM_H) * b
        sec = _section(w, h)
        out = []
        nrm = _normals2d(sec)
        for (s, z), (ns, nz) in zip(sec, nrm):
            s2, z2 = s - ns * inset, z - nz * inset
            out.append((x + nx * s2, y + ny * s2 + dy, z2))
        return out

    # Padded arm fronts: flat panel ring, rounding rings, then the run.
    def front(side):
        x = side * ARM_X
        nx = float(side)
        return [ring(x, ARM_FRONT, nx, 0.0, 0.050), ring(x, ARM_FRONT, nx, 0.0, 0.030),
                ring(x, ARM_FRONT + 0.006, nx, 0.0, 0.016), ring(x, ARM_FRONT + 0.018, nx, 0.0, 0.005),
                ring(x, ARM_FRONT + 0.034, nx, 0.0, 0.0)]
    rings = front(-1) + [ring(*p) for p in path] + list(reversed(front(1)))
    _loft(kit, rings, FABRIC, "tub", cap0="tri", cap1="tri")
    # Piping welts round the arm-front panels.
    for side in (-1, 1):
        sec = _section(ARM_W, ARM_H)
        nrm = _normals2d(sec)
        loop = [(s - ns * 0.029, z - nz * 0.029) for (s, z), (ns, nz) in zip(sec, nrm)]
        pts = [(side * (ARM_X + s2), ARM_FRONT - 0.001, z2) for s2, z2 in _clip_above(loop, FOOT_H + 0.035)]
        _welt(kit, pts, 0.006, FABRIC, verts=6, name="arm welt")
    # Outside seam welt: where the inside/top panel meets the outside panel,
    # just under the widest point of the roll, all round the tub.
    # It runs forward over the padded front and into the arm-front welt.
    def nose(side):
        x, nx = side * ARM_X, float(side)
        return [ring(x, ARM_FRONT - 0.001, nx, 0.0, 0.029)[SEAM], ring(x, ARM_FRONT + 0.005, nx, 0.0, 0.0135)[SEAM],
                ring(x, ARM_FRONT + 0.017, nx, 0.0, 0.0025)[SEAM], ring(x, ARM_FRONT + 0.034, nx, 0.0, -0.0035)[SEAM]]
    seam = nose(-1) + [ring(x, y, nx, ny, -0.0035)[SEAM] for x, y, nx, ny in path] + list(reversed(nose(1)))
    _welt(kit, seam, 0.006, FABRIC, verts=6, name="seam welt")
    # Black cambric dust cover: the tub's footprint, 12 mm in from its edge.
    outline = [ring(x, y, nx, ny, 0.0)[15] for x, y, nx, ny in path]
    foot = [(x - nx * 0.012, y - ny * 0.012) for (x, y, z), (_, _, nx, ny) in zip(outline, path)]
    foot = [(-ARM_X - 0.066, ARM_FRONT + 0.012)] + foot + [(ARM_X + 0.066, ARM_FRONT + 0.012)]
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, FOOT_H - 0.0015)) for x, y in foot])
    f.normal_update()
    if f.normal.z > 0:
        f.normal_flip()
    bmesh.ops.triangulate(bm, faces=[f], quad_method="BEAUTY", ngon_method="EAR_CLIP")
    kit._new_object("dust cover", bm, CAMBRIC, "metres", "xy")
    return path


# ------------------------------------------------------------------------ build
SEAT = (0.500, 0.590, 0.150)
SEAT_R, SEAT_SAG, SEAT_PUFF = 0.030, 0.024, 0.012


def _front_sag(co):
    w, d, h = SEAT
    if co.z > 0:
        u = co.y / (d / 2)
        k = max(0.0, 1 - (co.x / (w / 2)) ** 2)
        co.z -= 0.010 * k * max(0.0, 0.6 - u) * (co.z / (h / 2))
    return co


def build(kit):
    _tub(kit)
    inner = ARM_X - ARM_W / 2
    # Seat deck with its upholstered front rail.
    kit.box((2 * inner + 0.01, 0.695, DECK - FOOT_H - 0.006), (0, -0.0475, (DECK + FOOT_H + 0.006) / 2), FABRIC,
            bevel=0.025, segments=3, name="deck")

    # Loose seat cushion.
    w, d, h = SEAT
    loc = Vector((0.0, -0.425 + d / 2, DECK + h / 2 - 0.004))
    obj = kit.soft_box(SEAT, tuple(loc), FABRIC, radius=SEAT_R, segments=24, rings=10,
                       sag=SEAT_SAG, puff=SEAT_PUFF, name="seat cushion")
    for v in obj.data.vertices:
        v.co = _front_sag(v.co.copy())
    pts = []
    for k in range(20):
        vv = math.radians(60.0 - 300.0 * k / 19)
        p, n = _soft_point(SEAT, SEAT_R, math.radians(40.0), vv, SEAT_SAG, SEAT_PUFF)
        pts.append(tuple(_front_sag(p) + n * 0.0025 + loc))
    _welt(kit, pts, 0.0055, FABRIC, verts=6, name="cushion welt")

    # Tight inner back: a raked, puffed pad set into the tub.
    kit.soft_box((0.50, 0.15, 0.44), (0.0, BACK_Y - BACK_W / 2 - 0.035, DECK + 0.26), FABRIC, radius=0.035,
                 segments=20, rings=12, puff=0.030, rot=(-11.0, 0, 0), name="inner back")

    # Short tapered square feet.
    for x, y in ((-0.355, -0.33), (0.355, -0.33), (-0.30, 0.29), (0.30, 0.29)):
        kit.loft_box((0.034, 0.034), (0.046, 0.046), FOOT_H + 0.004, (x, y, (FOOT_H + 0.004) / 2), WOOD,
                     bevel=0.004, segments=1, rot=(90, 0, 0), name="foot")


    kit.support("seat", (0, -0.12, DECK + h - 0.012), (0.42, 0.40))
    kit.anchor("sit", (0, -0.12, DECK + h - 0.012))
    kit.collider((0, 0.0, 0.25), (0.85, 0.85, 0.50))
    kit.collider((0, 0.33, 0.66), (0.85, 0.19, 0.32))
    kit.tag("domestic", "upholstery", "seat", "pile_piece")
    kit.pile("Soft", mass=2, states=["Upright", "Back", "Side", "Inverted"], palette="domestic70s")
