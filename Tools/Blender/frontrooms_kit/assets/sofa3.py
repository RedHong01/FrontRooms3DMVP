"""1990s three-seat sofa, the department-store "rolled-arm pillow-back"
(Still B: the beige floral sofa lying on top of the tower; trailer T05).

Construction:
* Rolled (English scroll) arms: a tall upholstered side panel whose top
  rolls OUTWARD over a 3.5 cm tucked undercut, lofted front to back with
  padded, rounded ends (flat arm-front panel ringed by a piping welt).
* Plinth base between the arms (upholstered front rail under the seat
  cushions), on short turned dark-wood feet.
* Tight back frame, lower than the cushions, with a rounded top; its ends
  round down in a shoulder and dive into the arm rolls (no "ears").
* Three loose seat cushions (kit.soft_box with sag: a used sofa) and three
  plump loose back pillows (kit.soft_box with puff) raked back ~12 deg and
  rising above the frame: the pillow-back silhouette of the era.

UVs: the arms and the back frame carry authored "cover" UVs (fr_uv = keep),
cut where a real sofa's covers are sewn: the inside-arm cover wraps up the
inside, over the roll and tucks under it; the outside-arm panel, the arm
front panel (under its piping), the inside back and the outside back are
separate pieces. A floral jacquard therefore runs unbroken over each roll.
Cushions and the plinth keep kitlib's metre box projection.

Real-world reference size: 2.00 W x 0.90 D x 0.82 H; seat 0.45, arms 0.645.
Front (seat) faces -Y. Origin = floor under the centre.
Slots: Prop_FabricBeige (oatmeal; variants swap it to floral / charcoal),
Prop_WoodDark (base rail, feet, and the near-black dust cover underneath).
"""

import math

import bmesh
from mathutils import Euler, Vector

NAME = "Kit_Sofa3"
LOD1 = 0.4
SMOOTH_ANGLE = 70.0
VARIANTS = {
    "Kit_Sofa3_Floral": {"Prop_FabricBeige": "Prop_FabricFloral"},
    "Kit_Sofa3_Charcoal": {"Prop_FabricBeige": "Prop_FabricCharcoal"},
}

FABRIC = "Prop_FabricBeige"
WOOD = "Prop_WoodDark"
CAMBRIC = WOOD   # dust cover: near-black, shares the wood submesh (2 slots, not 3)

FOOT_H = 0.07          # underside of the upholstered body
DECK = 0.30            # top of the seat deck (cushions rest on it)
ARM_FRONT = -0.43
ARM_BACK = 0.45
BACK_FRONT = 0.31      # front face of the back frame
BACK_TOP = 0.74
RAIL_TOP = 0.115     # top of the dark-wood base rail (show-wood kick trim)


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
    """Piping cord along a 3D polyline. Parallel-transport frame (no flips
    on vertical runs, unlike a fixed up-vector), open ends."""
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


def _arm_profile():
    """Right arm cross-section (x, z), outer side at +x. The roll overhangs
    the outer panel; a concave fillet tucks the cover under it."""
    cx, cz, r = 0.910, 0.555, 0.090
    x_out, rf = 0.962, 0.030
    # Fillet circle outside the solid, tangent to the panel and the roll.
    fx = x_out + rf
    fz = cz - math.sqrt((r + rf) ** 2 - (fx - cx) ** 2)
    a_roll = math.degrees(math.atan2(fz - cz, fx - cx))          # roll angle at the tangent point
    a_fil = math.degrees(math.atan2(cz - fz, cx - fx))           # fillet angle at the same point
    pts = [(0.802, FOOT_H), (x_out, FOOT_H), (x_out, 0.30)]
    pts += _arc(fx, fz, rf, 180.0, a_fil, 3)
    pts += _arc(cx, cz, r, a_roll, 180.0, 18)[1:]
    pts += [(0.816, 0.47), (0.808, 0.33), (0.803, 0.18)]
    return pts


TUCK = 6   # _arm_profile index of the tuck under the roll (fillet meets roll)


def _arm(kit, side):
    prof = _arm_profile()
    nrm = _normals2d(prof)
    n = len(prof)

    def ring(y, inset):
        return [(side * (x - nx * inset), y, z - nz * inset) for (x, z), (nx, nz) in zip(prof, nrm)]
    # Padded front: a flat front panel (inner ring keeps its shading flat),
    # three rounding rings, the run to the back, rounded again.
    spec = [(ARM_FRONT, 0.050), (ARM_FRONT, 0.030), (ARM_FRONT + 0.006, 0.016), (ARM_FRONT + 0.018, 0.005),
            (ARM_FRONT + 0.034, 0.0), (ARM_BACK - 0.03, 0.0), (ARM_BACK - 0.012, 0.008), (ARM_BACK, 0.024)]
    rings = [ring(y, k) for y, k in spec]

    # Cover UVs (metres). Along the arm: distance travelled, = y on the run,
    # continued over the padded ends. Round the profile: the outside-arm
    # panel runs from the floor up to the tuck under the roll; the inside-arm
    # cover runs from the floor up the inside, over the roll and down to the
    # same tuck (pattern upright where it is seen, upside down only under
    # the roll, as on a real wrapped cover). Ring 0-1 is the flat arm-front
    # panel, cut under its piping and mapped flat.
    lu = [0.0] * len(spec)
    lu[4] = spec[4][0]
    for r in range(3, -1, -1):
        lu[r] = lu[r + 1] - math.hypot(spec[r + 1][0] - spec[r][0], spec[r + 1][1] - spec[r][1])
    for r in range(5, len(spec)):
        lu[r] = lu[r - 1] + math.hypot(spec[r][0] - spec[r - 1][0], spec[r][1] - spec[r - 1][1])
    seg = [math.dist(prof[i], prof[(i + 1) % n]) for i in range(n)]
    v_out = {1: FOOT_H}
    for k in range(2, TUCK + 1):
        v_out[k] = v_out[k - 1] + seg[k - 1]
    v_in = {0: FOOT_H}
    prev = 0
    for k in range(n - 1, TUCK - 1, -1):
        v_in[k] = v_in[prev] + seg[k]
        prev = k
    v_bot = {1: FOOT_H, 0: FOOT_H - seg[0]}

    def face_uv(r, s, rr, i, co):
        if r == 0:                                   # arm-front panel
            return (co.x, co.z)
        if s == 0:                                   # underside
            return (side * lu[rr], v_bot[i])
        if s < TUCK:                                 # outside-arm panel
            return (side * lu[rr], v_out[i])
        return (-side * lu[rr], v_in[i])             # inside-arm cover, over the roll

    def cap_uv(rr, co):
        return (co.x, co.z) if rr == 0 else (-co.x, co.z)
    _loft_uv(kit, rings, FABRIC, "rolled arm", face_uv, cap_uv, cap0="tri", cap1="tri")
    # Piping welt round the arm-front panel, on the panel's edge.
    loop = [(x - nx * 0.029, z - nz * 0.029) for (x, z), (nx, nz) in zip(prof, nrm)]
    welt = [(side * x, ARM_FRONT - 0.001, z) for x, z in _clip_above(loop, RAIL_TOP + 0.006)]
    _welt(kit, welt, 0.006, FABRIC, verts=6, name="arm welt")


def _back_section(drop):
    """Back frame (y, z) section, its rounded top lowered by ``drop``.
    Points: 0 front at the deck, 1-2 bottom, 3 back top (outside-back seam),
    4-9 the round top (6 = crown), 9 -> 0 the front face."""
    t = ARM_BACK - BACK_FRONT
    yb = ARM_BACK - 0.006      # just inside the arm ends (no coplanar faces)
    top = BACK_TOP - t / 2 - drop
    prof = [(BACK_FRONT, DECK), (BACK_FRONT, FOOT_H + 0.004), (yb, FOOT_H + 0.004), (yb, top)]
    prof += _arc((BACK_FRONT + ARM_BACK) / 2, top, t / 2, 0.0, 180.0, 6)[1:]
    return prof


def _back_frame(kit):
    """Tight back lofted along X. Level across the middle, then each end
    rounds down in a shoulder (a quarter ellipse in front view) to 0.63 at
    |x| = 0.80, inside the arm's inner face, and dives on into the arm roll
    to its buried end at |x| = 0.86. Nothing rises above the 0.645 arm top
    outboard of |x| = 0.80 (no square "ears" between arm and pillow)."""
    half = [(0.70 + 0.10 * math.cos(math.radians(a)), 0.11 * (1 - math.sin(math.radians(a))))
            for a in (90.0, 60.0, 30.0, 0.0)] + [(0.86, 0.15)]
    stations = [(-x, d) for x, d in reversed(half)] + half
    secs = [_back_section(d) for _, d in stations]
    rings = [[(x, y, z) for y, z in sec] for (x, _), sec in zip(stations, secs)]
    n = len(secs[0])
    CROWN = 6

    # Cover UVs: the inside-back cover runs from the deck up the front, over
    # the crown to the seam at the back top; V = z on the front face (the
    # crown is anchored at its height, so the lowered shoulder rings map
    # without shear) and U = x. The outside back is its own flat panel.
    def v_inside(sec):
        seg = [math.dist(sec[i], sec[(i + 1) % n]) for i in range(n)]
        v = {CROWN: sec[CROWN][1]}
        for k in (5, 4, 3):
            v[k] = v[k + 1] + seg[k]
        for k in (7, 8, 9):
            v[k] = v[k - 1] - seg[k - 1]
        v[0] = v[9] - seg[9]
        v[1] = v[0] - seg[0]
        return v
    vin = [v_inside(sec) for sec in secs]

    def face_uv(r, s, rr, i, co):
        if s == 2:                                   # outside back panel
            return (-co.x, co.z)
        if s == 1:                                   # underside
            return (co.x, co.y)
        return (co.x, vin[rr][i])                    # inside back, over the crown

    _loft_uv(kit, rings, FABRIC, "back frame", face_uv, lambda rr, co: (co.y, co.z))


def _soft_point(size, radius, u, v, sag=0.0, puff=0.0):
    """A point of kit.soft_box's surface at parameters (u, v) (same formula),
    plus its approximate outward normal: for welts that sit on its seams."""
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


SEAT = (0.536, 0.585, 0.160)
SEAT_R, SEAT_SAG, SEAT_PUFF = 0.031, 0.026, 0.012


def _front_sag(co):
    """Sag is where people sit: push the dip toward the front edge."""
    w, d, h = SEAT
    if co.z > 0:
        u = co.y / (d / 2)
        k = max(0.0, 1 - (co.x / (w / 2)) ** 2)
        co.z -= 0.010 * k * max(0.0, 0.6 - u) * (co.z / (h / 2))
    return co


def _seat_cushion(kit, x, tilt):
    w, d, h = SEAT
    loc = Vector((x, -0.446 + d / 2, DECK + h / 2 - 0.004))
    obj = _weld(kit.soft_box(SEAT, tuple(loc), FABRIC, radius=SEAT_R, segments=24, rings=10,
                             sag=SEAT_SAG, puff=SEAT_PUFF, rot=(0, tilt, 0), name="seat cushion"))
    for v in obj.data.vertices:
        v.co = _front_sag(v.co.copy())
    # Top seam welt (boxed cushion): round the sides and the front; the back
    # run is hidden under the back pillows.
    rot = Euler((0.0, math.radians(tilt), 0.0)).to_matrix()
    pts = []
    for k in range(20):
        vv = math.radians(60.0 - 300.0 * k / 19)
        p, n = _soft_point(SEAT, SEAT_R, math.radians(40.0), vv, SEAT_SAG, SEAT_PUFF)
        p = _front_sag(p) + n * 0.0025
        pts.append(tuple(rot @ p + loc))
    _welt(kit, pts, 0.0055, FABRIC, verts=6, name="cushion welt")
    return obj


def _back_cushion(kit, x, rake, roll):
    w, d, h = 0.528, 0.19, 0.49
    obj = _weld(kit.soft_box((w, d, h), (x, 0.205, DECK + h / 2 + 0.012), FABRIC, radius=0.040, segments=20,
                             rings=14, puff=0.040, rot=(-rake, 0, roll), name="back cushion"))
    # Pillows slump: the top folds forward a little, the bottom wedges back.
    for v in obj.data.vertices:
        t = v.co.z / (h / 2)
        v.co.y -= 0.012 * max(0.0, t) ** 2
    return obj


def _foot(kit, x, y):
    # Tapered bun foot with a collar; the top end is buried in the body
    # (no cap), the 3 mm toe chamfer is below the 5 mm detail floor.
    kit.lathe([(0.020, 0.0), (0.025, 0.040), (0.030, 0.050), (0.030, FOOT_H + 0.004)],
              (x, y, 0.0), WOOD, verts=8, name="turned foot", close_top=False)


# ------------------------------------------------------------------------ build
def build(kit):
    for side in (-1, 1):
        _arm(kit, side)
    # Plinth / seat deck between the arms, upholstered front rail.
    kit.box((1.66, ARM_BACK - ARM_FRONT - 0.02, DECK - FOOT_H - 0.006), (0, (ARM_FRONT + ARM_BACK) / 2 - 0.005,
            (DECK + FOOT_H + 0.006) / 2), FABRIC, bevel=0.03, segments=3, name="plinth")
    _back_frame(kit)
    # Show-wood base rail: the body sits on a moulded dark-wood band (front
    # and both sides), the turned feet screw into it.
    rh = RAIL_TOP - FOOT_H + 0.003
    kit.box((1.948, 0.024, rh), (0, ARM_FRONT - 0.004, RAIL_TOP - rh / 2), WOOD, bevel=0.005, segments=1,
            name="base rail front")
    for side in (-1, 1):
        kit.box((0.024, ARM_BACK - ARM_FRONT - 0.004, rh), (side * 0.962, (ARM_FRONT + ARM_BACK) / 2 - 0.004,
                RAIL_TOP - rh / 2), WOOD, bevel=0.005, segments=1, name="base rail side")

    # Dark dust cover under the frame (shows when the sofa is piled on its
    # back or side): 5 mm under the body, inside the base rails.
    y0, y1 = ARM_FRONT + 0.012, ARM_BACK - 0.010
    dust = kit.quad(1.89, y1 - y0, (0, (y0 + y1) / 2, FOOT_H - 0.005), CAMBRIC,
                    facing="+z", name="dust cover", uv="metres")
    dust.rotation_euler = (math.pi, 0.0, 0.0)

    for x, tilt in ((-0.527, -0.6), (0.0, 0.4), (0.527, 0.0)):
        _seat_cushion(kit, x, tilt)
    for x, rake, roll in ((-0.528, 12.5, 1.2), (0.0, 11.0, -0.6), (0.528, 13.5, -1.0)):
        _back_cushion(kit, x, rake, roll)

    for x in (-0.885, 0.885):
        for y in (-0.385, 0.395):
            _foot(kit, x, y)
    for y in (-0.36, 0.38):
        _foot(kit, 0.0, y)

    kit.support("seat", (0, -0.17, 0.45), (1.50, 0.46))
    kit.anchor("sit_left", (-0.527, -0.17, 0.45))
    kit.anchor("sit", (0.0, -0.17, 0.45))
    kit.anchor("sit_right", (0.527, -0.17, 0.45))
    # Seat block up to the cushion tops (= the seat support), back box above.
    kit.collider((0, 0.0, 0.225), (2.00, 0.90, 0.45))
    kit.collider((0, 0.33, 0.635), (2.00, 0.24, 0.37))
    kit.tag("domestic", "upholstery", "seat", "pile_piece")
    kit.pile("Soft", mass=2, states=["Upright", "Back", "Side"], palette="domestic70s", topper=True)
