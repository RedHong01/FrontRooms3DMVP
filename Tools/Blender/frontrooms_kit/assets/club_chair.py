"""1980s-90s upholstered club armchair (Still B: the teal tweed chair that
"rolled off" the tower and sits upright 1 m out; B7 is the oatmeal one).

Construction:
* One continuous upholstered "tub": deep, fat rounded arms that sweep round
  the back corners and rise into a rounded back roll (lofted along a U path
  in plan; the section changes from the 0.165 m arm to the 0.15 m back and the
  top line climbs from 0.62 to 0.82 m in ONE eased sweep that starts on the
  arm at y = 0.02 and ends where the corner meets the back; the path is
  sampled every ~4 cm through the sweep and 14 times round each corner).
* Padded arm fronts with a piping welt; the arms run past the seat front.
  A second welt follows the outside seam (under the widest point of the
  roll) all round the tub and runs over the arm noses into the front welts.
* Tight (attached) inner back: a raked, puffed pad set into the tub.
* Loose seat cushion (kit.soft_box with sag toward the front) with a welted
  top seam, on a soft, puffed upholstered deck (not a hard box face).
* Four short tapered dark-wood feet; a near-black dust cover underneath.

UVs: the tub carries authored cover UVs (fr_uv = keep): the inside cover runs
up the inside of the arms and back and over the roll to the outside seam
welt; the outside panel runs from the floor up to that welt; U is distance
along the tub, so a herringbone or tweed never turns 90 deg at the corners.

Real-world reference size: 0.85 W x 0.85 D x 0.82 H; seat 0.44, arms 0.62.
Front (seat) faces -Y. Origin = floor under the centre.
Slots: Prop_FabricTeal (variant swaps it to oatmeal), Prop_WoodDark (feet and
dust cover).
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
CAMBRIC = WOOD   # dust cover: near-black, shares the feet's submesh (2 slots)

FOOT_H = 0.075         # underside of the upholstered body
DECK = 0.295           # top of the seat deck
ARM_X = 0.329          # arm section centre line (outer welt at 0.425)
ARM_W, BACK_W = 0.165, 0.150
ARM_H, BACK_H = 0.620, 0.820
ARM_FRONT = -0.400
SEAM = 10              # section point at the outer side of the roll (arc 0 deg)
BACK_Y = 0.4115 - BACK_W / 2   # back roll centre line (outer welt at 0.425)
RISE_Y = 0.02          # the arm top starts its sweep up to the back here
# Back corners in plan: curvature eases in from 0 at the arm (sin^2 ramp over
# the first and last 30 % of the turn, radius 0.13 m in the middle), so no
# line of the tub (seam welt, roll top, inner edge) kinks where the straight
# arm meets the corner while the top is rising through it.
CORNER_L, CORNER_F = 0.292, 0.30
SWEEP_N = 20           # path stations from the back junction to RISE_Y


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


def _loft_uv(kit, rings, slot, name, face_uv, cap_uv, cap0=None, cap1=None):
    """_loft with authored UVs (fr_uv = "keep": kitlib leaves them alone).
    face_uv(r, seg, rr, i, co) -> (u, v) for each corner of the quad between
    ring r and r + 1 on profile segment seg (point seg -> seg + 1); rr, i is
    the corner's ring and point index. cap_uv(rr, co) -> (u, v) on the caps.
    UVs are per face corner, so a piece boundary is a clean UV seam."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.verify()     # same layer name as kitlib's metre UVs
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    where = {v: (r, i) for r, ring in enumerate(vs) for i, v in enumerate(ring)}
    n = len(rings[0])
    sides = {}
    for r in range(len(vs) - 1):
        a, b = vs[r], vs[r + 1]
        for i in range(n):
            j = (i + 1) % n
            sides[bm.faces.new((a[i], a[j], b[j], b[i]))] = (r, i)
    for rr, cap in ((0, cap0), (len(vs) - 1, cap1)):
        f = bm.faces.new(vs[rr])
        if cap == "tri":
            f.normal_update()          # polyfill projects on the face normal
            bmesh.ops.triangulate(bm, faces=[f], quad_method="BEAUTY", ngon_method="EAR_CLIP")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f in sides:
            r, seg = sides[f]
            for loop in f.loops:
                rr, i = where[loop.vert]
                loop[uvl].uv = face_uv(r, seg, rr, i, loop.vert.co)
        else:
            rr = where[f.verts[0]][0]
            for loop in f.loops:
                loop[uvl].uv = cap_uv(rr, loop.vert.co)
    return kit._new_object(name, bm, slot, "keep", "xz")


def _weld(obj, dist=1e-3):
    """Weld a soft_box's pole rings. At boxy exponents the pole ring is
    1e-5 .. 2e-4 m across, wider than soft_box's own 1e-5 weld, which left
    micro-holes at the top and bottom centre. Real vertices on these
    cushions are centimetres apart, so 1 mm only closes the poles."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=dist)
    bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
    bm.to_mesh(obj.data)
    bm.free()
    return obj


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


# ------------------------------------------------------------------- the tub
def _section(w, h):
    """Arm/back cross-section (s, z): s = offset along the outward normal.
    Flat inner face, fat round top, the outer face flaring slightly out.
    Points: 0 inner foot, 1 top of the flat inner face, 2-10 the roll
    (10 = SEAM, its outer side), 11 under the roll, 12 outer foot."""
    r = w / 2
    pts = [(-w / 2, FOOT_H), (-w / 2, h - r - 0.06)]
    pts += _arc(0.004, h - r, r, 180.0, 0.0, 8)
    pts[2] = (-w / 2, h - r)                     # keep the inner face exactly vertical
    pts += [(w / 2 - 0.006, h - r - 0.10), (w / 2 - 0.012, FOOT_H)]
    return pts


def _corner_kappa(sig):
    k0 = math.pi / (2 * CORNER_L * (1 - CORNER_F))
    r = CORNER_F * CORNER_L
    if sig < r:
        return k0 * math.sin(math.pi / 2 * sig / r) ** 2
    if sig > CORNER_L - r:
        return k0 * math.sin(math.pi / 2 * (CORNER_L - sig) / r) ** 2
    return k0


def _corner_track(n=600):
    """The right back corner's centre line from the arm junction (heading +Y)
    to the back junction (heading -X): (sigma, dx, dy, heading) offsets."""
    ds = CORNER_L / n
    x = y = th = 0.0
    out = [(0.0, 0.0, 0.0, 0.0)]
    for i in range(n):
        k = _corner_kappa((i + 0.5) * ds)
        mid = th + k * ds / 2
        x += math.sin(mid) * ds
        y += math.cos(mid) * ds
        th += k * ds
        out.append(((i + 1) * ds, x, y, th))
    return out


def _path_right():
    """Right half of the plan path, back centre -> corner -> arm: stations
    (x, y, nx, ny, d, inset); (nx, ny) = outward normal in plan, d = centre
    line distance from the back junction towards the arm (d < 0 on the back).
    Stations are spaced for equal turning (plan curvature plus the change of
    the rising top's slope), so the welts and the top line read smooth."""
    track = _corner_track()
    ex, ey = track[-1][1], track[-1][2]
    y0 = BACK_Y - ey                    # where the corner leaves the arm
    sweep = CORNER_L + (y0 - RISE_Y)

    def at(d):
        if d <= CORNER_L:               # corner: interpolate the track
            sig = CORNER_L - d
            i = min(len(track) - 2, int(sig / CORNER_L * (len(track) - 1)))
            s0, x0, y0_, t0 = track[i]
            s1, x1, y1, t1 = track[i + 1]
            f = (sig - s0) / max(s1 - s0, 1e-9)
            dx, dy, th = x0 + (x1 - x0) * f, y0_ + (y1 - y0_) * f, t0 + (t1 - t0) * f
            return (ARM_X - dx, y0 + dy, math.cos(th), math.sin(th), d, 0.0)
        return (ARM_X, y0 - (d - CORNER_L), 1.0, 0.0, d, 0.0)

    def slope(d):                       # |dz/dd| of the rising top
        return (BACK_H - ARM_H) * 0.5 * math.pi / sweep * abs(math.sin(math.pi * d / sweep))
    n = 2000
    cost = [0.0]
    for i in range(n):
        d0, d1 = sweep * i / n, sweep * (i + 1) / n
        k = _corner_kappa(CORNER_L - (d0 + d1) / 2) if (d0 + d1) / 2 < CORNER_L else 0.0
        cost.append(cost[-1] + k * (d1 - d0) + abs(math.atan(slope(d1)) - math.atan(slope(d0))))
    ds = []
    j = 0
    for q in range(SWEEP_N + 1):
        target = cost[-1] * q / SWEEP_N
        while j < n and cost[j + 1] < target:
            j += 1
        f = (target - cost[j]) / max(cost[j + 1] - cost[j], 1e-12) if j < n else 0.0
        ds.append(sweep * (j + f) / n)
    return [(0.0, BACK_Y, 0.0, 1.0, -(ARM_X - ex), 0.0)] + [at(d) for d in ds], sweep


def _tub(kit):
    right, sweep = _path_right()
    left = [(-x, y, -nx, ny, d, s) for x, y, nx, ny, d, s in reversed(right[1:])]
    path = left + right
    flat = 9.0                                   # d beyond the sweep: plain arm

    def front(side):
        # Padded arm front: flat panel ring, rounding rings, then the run.
        x, nx = side * ARM_X, float(side)
        return [(x, ARM_FRONT, nx, 0.0, flat, 0.050), (x, ARM_FRONT, nx, 0.0, flat, 0.030),
                (x, ARM_FRONT + 0.006, nx, 0.0, flat, 0.016), (x, ARM_FRONT + 0.018, nx, 0.0, flat, 0.005),
                (x, ARM_FRONT + 0.034, nx, 0.0, flat, 0.0)]
    stations = front(-1) + path + list(reversed(front(1)))

    def dims(d):
        # One cosine-eased sweep: 1 on the back, 0 on the arm. No flat step
        # at the corner (the old two-stage blend paused there).
        t = min(1.0, max(0.0, d / sweep))
        b = 0.5 + 0.5 * math.cos(math.pi * t)
        return ARM_W + (BACK_W - ARM_W) * b, ARM_H + (BACK_H - ARM_H) * b

    def ring(x, y, nx, ny, d, inset=0.0, dy=0.0):
        sec = _section(*dims(d))
        nrm = _normals2d(sec)
        out = []
        for (s, z), (ns, nz) in zip(sec, nrm):
            s2, z2 = s - ns * inset, z - nz * inset
            out.append((x + nx * s2, y + ny * s2 + dy, z2))
        return out
    rings = [ring(*st) for st in stations]

    # Cover UVs (metres). U = distance along the tub's centre line (0 at the
    # back centre), continued over the padded fronts. Round the section: the
    # inside cover runs from the floor up the inside, over the roll to the
    # outside seam welt (SEAM); the outside panel from the floor up to it.
    # The flat arm-front panels (first / last band, cut under their piping)
    # and the caps map flat.
    nst = len(stations)
    centre = len(front(-1)) + len(left)
    U = [0.0] * nst
    for i in range(centre + 1, nst):
        a, b = stations[i - 1], stations[i]
        U[i] = U[i - 1] + math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[5] - a[5]) ** 2)
    for i in range(centre - 1, -1, -1):
        a, b = stations[i + 1], stations[i]
        U[i] = U[i + 1] - math.sqrt((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2 + (b[5] - a[5]) ** 2)
    m = 13
    V = []
    for st in stations:
        sec = _section(*dims(st[4]))
        seg = [math.dist(sec[i], sec[(i + 1) % m]) for i in range(m)]
        vin = {0: FOOT_H}
        for i in range(1, SEAM + 1):
            vin[i] = vin[i - 1] + seg[i - 1]
        vout = {12: FOOT_H, 11: FOOT_H + seg[11]}
        vout[10] = vout[11] + seg[10]
        V.append((vin, vout))

    def face_uv(r, s, rr, i, co):
        if r == 0 or r == nst - 2:               # arm-front panels
            return (co.x, co.z)
        if s == m - 1:                           # underside
            return (co.x, co.y)
        if s >= SEAM:                            # outside panel
            return (-U[rr], V[rr][1][i])
        return (U[rr], V[rr][0][i])              # inside cover, over the roll

    _loft_uv(kit, rings, FABRIC, "tub", face_uv, lambda rr, co: (co.x, co.z), cap0="tri", cap1="tri")
    # Piping welts round the arm-front panels.
    for side in (-1, 1):
        sec = _section(ARM_W, ARM_H)
        nrm = _normals2d(sec)
        loop = [(s - ns * 0.029, z - nz * 0.029) for (s, z), (ns, nz) in zip(sec, nrm)]
        pts = [(side * (ARM_X + s2), ARM_FRONT - 0.001, z2) for s2, z2 in _clip_above(loop, FOOT_H + 0.035)]
        _welt(kit, pts, 0.006, FABRIC, verts=6, name="arm welt")
    # Outside seam welt: where the inside/top cover meets the outside panel,
    # just under the widest point of the roll, all round the tub.
    # It runs forward over the padded front and into the arm-front welt.
    def nose(side):
        x, nx = side * ARM_X, float(side)
        return [ring(x, ARM_FRONT - 0.001, nx, 0.0, flat, 0.029)[SEAM],
                ring(x, ARM_FRONT + 0.005, nx, 0.0, flat, 0.0135)[SEAM],
                ring(x, ARM_FRONT + 0.017, nx, 0.0, flat, 0.0025)[SEAM],
                ring(x, ARM_FRONT + 0.034, nx, 0.0, flat, -0.0035)[SEAM]]
    seam = nose(-1) + [ring(x, y, nx, ny, d, -0.0035)[SEAM] for x, y, nx, ny, d, _ in path] + list(reversed(nose(1)))
    _welt(kit, seam, 0.006, FABRIC, verts=6, name="seam welt")
    # Dark dust cover: the tub's footprint, 12 mm in from its edge, 5 mm
    # under the body.
    outline = [ring(x, y, nx, ny, d, 0.0)[-1] for x, y, nx, ny, d, _ in path]
    foot = [(x - st[2] * 0.012, y - st[3] * 0.012) for (x, y, z), st in zip(outline, path)]
    fx = ARM_X + ARM_W / 2 - 0.040
    foot = [(-fx, ARM_FRONT + 0.020)] + foot + [(fx, ARM_FRONT + 0.020)]
    bm = bmesh.new()
    f = bm.faces.new([bm.verts.new((x, y, FOOT_H - 0.005)) for x, y in foot])
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
    # Upholstered seat deck under the cushion: a stuffed, slightly puffed
    # front (its centre just behind the arm fronts), not a flat box face.
    _weld(kit.soft_box((2 * inner + 0.01, 0.695, DECK - FOOT_H - 0.006), (0, -0.0425, (DECK + FOOT_H + 0.006) / 2),
                       FABRIC, radius=0.03, segments=16, rings=8, puff=0.01, name="deck"))

    # Loose seat cushion.
    w, d, h = SEAT
    loc = Vector((0.0, -0.425 + d / 2, DECK + h / 2 - 0.004))
    obj = _weld(kit.soft_box(SEAT, tuple(loc), FABRIC, radius=SEAT_R, segments=24, rings=10,
                             sag=SEAT_SAG, puff=SEAT_PUFF, name="seat cushion"))
    for v in obj.data.vertices:
        v.co = _front_sag(v.co.copy())
    pts = []
    for k in range(20):
        vv = math.radians(60.0 - 300.0 * k / 19)
        p, n = _soft_point(SEAT, SEAT_R, math.radians(40.0), vv, SEAT_SAG, SEAT_PUFF)
        pts.append(tuple(_front_sag(p) + n * 0.0025 + loc))
    _welt(kit, pts, 0.0055, FABRIC, verts=6, name="cushion welt")

    # Tight inner back: a raked, puffed pad set into the tub.
    _weld(kit.soft_box((0.50, 0.15, 0.44), (0.0, BACK_Y - BACK_W / 2 - 0.035, DECK + 0.26), FABRIC, radius=0.035,
                       segments=20, rings=12, puff=0.030, rot=(-11.0, 0, 0), name="inner back"))

    # Short tapered square feet.
    for x, y in ((-0.355, -0.33), (0.355, -0.33), (-0.30, 0.29), (0.30, 0.29)):
        kit.loft_box((0.034, 0.034), (0.046, 0.046), FOOT_H + 0.004, (x, y, (FOOT_H + 0.004) / 2), WOOD,
                     bevel=0.004, segments=1, rot=(90, 0, 0), name="foot")


    kit.support("seat", (0, -0.12, DECK + h - 0.012), (0.42, 0.40))
    kit.anchor("sit", (0, -0.12, DECK + h - 0.012))
    # Seat block up to the cushion top (= the seat support), back box above.
    kit.collider((0, 0.0, 0.22), (0.85, 0.85, 0.44))
    kit.collider((0, 0.33, 0.63), (0.85, 0.19, 0.38))
    kit.tag("domestic", "upholstery", "seat", "pile_piece")
    kit.pile("Soft", mass=2, states=["Upright", "Back", "Side", "Inverted"], palette="domestic70s")
    # Upside down the chair would balance on the 0.82 back roll with the 0.62
    # arm noses 0.20 m in the air. restTilt = extra Unity Euler-X degrees for
    # FrontRoomsFurniturePile.RestRotation (Inverted -> Euler(180 + tilt, 0,
    # 0)) so it rests on the back roll AND both arm noses; measured from the
    # LOD0 lower convex hull under the centre of mass: -16. Re-measure if the
    # arm or back heights change.
    kit.meta["pile"]["restTilt"] = {"Inverted": -16.0}
