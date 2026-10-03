"""Blush-pink velvet Queen Anne / bergere-style open armchair, c. 1980-95
reproduction (the department-store "French" chair: exposed walnut show-wood
frame, two cabriole front legs on turned pad feet, splayed back legs that
carry on above the seat as stiles into the back frame, a bowed front apron
with a carved rosette, open arms whose shaped (board-section) supports
sweep up into knuckles carved with a spiral volute, padded velvet
manchettes on flat arm rails, a tall serpentine-crested upholstered back
inside a closed moulded frame with a carved crest rosette, a tight
upholstered seat deck and a thick piped loose cushion).

Real-world reference size: 0.72 m wide (across the arms), 0.70 m deep,
1.05 m tall to the crest. Seat (cushion top) 0.50 m, arm pads 0.68 m,
back raked 12 degrees. Front (seat) faces -Y. Origin = floor under the
centre of the seat. Film: Still A, the pink armchair tipped onto the desk.

Budget (§5.3, Kit_BergereChair row): 4,200 LOD0 tris, VelvetPink +
WoodWalnut, 1 collider, Seat 1 (U, B, E). Optimised 2026-10-02 from 11.8k:
every upholstered part is a kit.soft_box (superellipsoid, so it reads soft
at 3 m): the back is remapped onto the serpentine-crest outline, the seat
cushion and deck keep their own plans with a fixed-width rolled edge and a
bowed front, the manchettes bend along the arm rails. Carved members
keep their paths with 8-sided (small parts 6-sided) sections and one
sample per control point; the apron bead and knee blocks (hidden under
the rail) are gone; one piping welt on the cushion's top edge.
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_QueenAnneArmchair"
LOD1 = 0.42
# 8- and 6-sided carved sections turn up to 60 deg per edge, and the
# upholstery is all curves: smooth everything below 62 deg.
SMOOTH_ANGLE = 62.0

WOOD = "Prop_WoodWalnut"
VELVET = "Prop_VelvetPink"

# Back geometry: rear face centre, rake, outline in the back plane (u, v).
BACK_TILT = math.radians(12.0)
BACK_O = Vector((0.0, 0.292, 0.714))
BACK_U = Vector((1.0, 0.0, 0.0))
BACK_V = Vector((0.0, math.sin(BACK_TILT), math.cos(BACK_TILT)))
BACK_N = Vector((0.0, -math.cos(BACK_TILT), math.sin(BACK_TILT)))
BACK_OUTLINE_R = [   # right half, bottom centre -> top centre (u, v); mirrored for the left
    (0.0, -0.290), (0.170, -0.290), (0.215, -0.282), (0.240, -0.258), (0.252, -0.200),
    (0.256, -0.100), (0.250, 0.000), (0.242, 0.080), (0.230, 0.140), (0.212, 0.190),
    (0.190, 0.226), (0.160, 0.248), (0.120, 0.262), (0.080, 0.276), (0.040, 0.290),
    (0.0, 0.298),
]
BACK_DEPTH = 0.094

# Seat rail plan (rail centre line) and heights.
RAIL_Z0, RAIL_Z1 = 0.335, 0.395
FL = (0.285, -0.255)       # front leg centre (x mirrored)
BL = (0.262, 0.255)        # back leg top centre


# ------------------------------------------------------------------ helpers
def catmull(ctrl, sub):
    """Catmull-Rom through tuples of any length (positions plus scales)."""
    pts = [list(c) for c in ctrl]
    first = [2 * a - b for a, b in zip(pts[0], pts[1])]
    last = [2 * a - b for a, b in zip(pts[-1], pts[-2])]
    ext = [first] + pts + [last]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(sub):
            t = s / sub
            out.append([0.5 * (2 * b + (-a + c) * t + (2 * a - 5 * b + 4 * c - d) * t * t
                               + (-a + 3 * b - 3 * c + d) * t * t * t) for a, b, c, d in zip(p0, p1, p2, p3)])
    out.append(pts[-1])
    return out


def squircle(n, e=2.4, phase=0.0):
    """Unit rounded-square cross-section, n points."""
    pts = []
    for j in range(n):
        a = 2 * math.pi * j / n + phase
        c, s = math.cos(a), math.sin(a)
        pts.append((math.copysign(abs(c) ** (2 / e), c), math.copysign(abs(s) ** (2 / e), s)))
    return pts


def recalc(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def sweep(kit, ctrl, section, slot, ref, sub=1, grain=None, name="sweep"):
    """Carved member: a cross-section swept along a smooth path whose size
    changes along it. ctrl = (x, y, z, scale_s, scale_u); the section's u
    axis follows ``ref`` (a vector, or a function of the point)."""
    pts = catmull(ctrl, sub)
    n = len(section)
    obj = kit.tube([p[:3] for p in pts], 1.0, slot, verts=n, name=name)
    verts = obj.data.vertices
    P = [Vector(p[:3]) for p in pts]
    for k, p in enumerate(pts):
        if k == 0:
            t = P[1] - P[0]
        elif k == len(P) - 1:
            t = P[-1] - P[-2]
        else:
            t = (P[k + 1] - P[k - 1])
        t.normalize()
        r = Vector(ref(P[k]) if callable(ref) else ref)
        n1 = (r - t * r.dot(t)).normalized()
        n2 = t.cross(n1).normalized()
        for j, (s, u) in enumerate(section):
            co = P[k] + n2 * (s * p[3]) + n1 * (u * p[4])
            co.z = max(co.z, 0.0)          # feet stand flat on the floor
            verts[k * n + j].co = co
    recalc(obj)
    if grain:
        obj["fr_grain"] = grain
    return obj


def polar_polygon(points):
    """Ray-cast a star-shaped polygon from its origin: phi -> boundary point."""
    def shape(phi):
        d = Vector((math.cos(phi), math.sin(phi)))
        best = None
        for (x0, y0), (x1, y1) in zip(points, points[1:] + points[:1]):
            e = Vector((x1 - x0, y1 - y0))
            den = d.x * e.y - d.y * e.x
            if abs(den) < 1e-12:
                continue
            t = (x0 * e.y - y0 * e.x) / den
            s = (x0 * d.y - y0 * d.x) / den
            if t > 0 and -1e-6 <= s <= 1 + 1e-6 and (best is None or t < best):   # rays through a vertex
                best = t
        return (d.x * best, d.y * best)
    return shape


# ------------------------------------------------------------ upholstery
def _soft_e(size, radius):
    """The superellipsoid exponent kitlib.soft_box derives from ``radius``."""
    return max(0.08, min(0.6, radius / max(min(size), 1e-3) * 1.5))


def soft_point(size, radius, u, v, sag=0.0, puff=0.0):
    """A point of kit.soft_box's surface at parameters (u, v), same formula
    (piping that rides on a cushion is computed from it)."""
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    e = _soft_e(size, radius)

    def c(w):
        k = math.cos(w)
        return math.copysign(abs(k) ** e, k)

    def sn(w):
        k = math.sin(w)
        return math.copysign(abs(k) ** e, k)
    x, y, z = hx * c(u) * c(v), hy * c(u) * sn(v), hz * sn(u)
    ux, uy, uz = x / hx, y / hy, z / hz
    if puff:
        x += puff * ux * max(0.0, 1 - uy * uy) * max(0.0, 1 - uz * uz)
        y += puff * uy * max(0.0, 1 - ux * ux) * max(0.0, 1 - uz * uz)
        z += puff * 0.5 * uz * max(0.0, 1 - ux * ux) * max(0.0, 1 - uy * uy)
    if sag and uz > 0:
        z -= sag * uz * max(0.0, 1 - ux * ux) * max(0.0, 1 - uy * uy)
    return [x, y, z]


def outline_map(size, radius, axes, shape=None, rim=None, bow=None):
    """Radial remap of a soft_box in its ``axes`` plane.

    * ``shape`` (phi -> outline point): the soft_box's own outline (a
      superellipse) is pulled onto that silhouette (the serpentine back).
      Without it the native outline stays (seat cushion and deck: their
      plans ARE soft_box superellipses, and keeping kitlib's vertex spacing
      keeps the corners round).
    * Without ``rim`` every ring is scaled, so the edge roll is a fixed
      fraction of the half-size (a domed pillow: the back). With ``rim``
      (metres) rings are inset by a distance instead, so a wide flat cushion
      gets a roll of about that width on every side (a boxed seat cushion).
    * ``bow`` = (amount, half_y): the front (-b side) bows forward. The
      shift is taken at the outline point in each vertex's direction, so
      every ring of the rolled edge moves together (no lip), fading to 0
      toward the middle of the top face."""
    a, b = axes
    ha, hb = size[a] / 2, size[b] / 2
    e = _soft_e(size, radius)
    n = 2.0 / e
    rho45 = math.cos(math.pi / 4) ** e      # plan radius of the 45-degree ring

    def f(co):
        p, q = co[a], co[b]
        r = math.hypot(p, q)
        if r < 1e-9:
            return list(co)
        phi = math.atan2(q, p)
        c, s = math.cos(phi), math.sin(phi)
        r_se = 1.0 / ((abs(c) / ha) ** n + (abs(s) / hb) ** n) ** (1.0 / n)
        r_t = math.hypot(*shape(phi)) if shape else r_se
        rho = r / r_se
        if rim is None:
            k = r_t / r_se
        else:
            k = max(r_t - rim * (1.0 - rho) / (1.0 - rho45), 0.5 * rho * r_t) / r
        co = list(co)
        co[a], co[b] = p * k, q * k
        if bow:
            amount, half = bow
            ox, oy = r_t * c, r_t * s
            if oy < 0:
                w = min(1.0, rho / rho45) ** 2
                co[b] -= amount * (1 - min(1.0, (ox / 0.30) ** 2)) * (-oy / half) ** 2 * w
        return co
    return f


def cushion(kit, size, loc, radius, segments, rings, shape=None, axes=(0, 1), deform=None,
            sag=0.0, puff=0.0, rot=(0, 0, 0), rim=None, bow=None, name="cushion"):
    """kit.soft_box upholstery, remapped by outline_map() (outline shape,
    edge roll width, bowed front) and then ``deform(x, y, z)`` (local,
    centred: bends it along a rail)."""
    obj = kit.soft_box(size, loc, VELVET, radius=radius, segments=segments, rings=rings,
                       sag=sag, puff=puff, rot=rot, name=name)
    remap = outline_map(size, radius, axes, shape, rim, bow) if (shape or rim or bow) else None
    for v in obj.data.vertices:
        co = list(v.co)
        if remap:
            co = remap(co)
        if deform:
            co = list(deform(*co))
        v.co = co
    recalc(obj)
    return obj


def back_point(u, v, w=0.0):
    return BACK_O + BACK_U * u + BACK_V * v + BACK_N * w


def scallop(obj, verts, depth):
    """Pull every other angular column of a Z-axis part inward (petals)."""
    step = 2 * math.pi / verts
    for v in obj.data.vertices:
        r = math.hypot(v.co.x, v.co.y)
        if r < 1e-6:
            continue
        k = int(round(math.atan2(v.co.y, v.co.x) / step)) % verts
        if k % 2:
            f = max(r - depth, 0.0) / r
            v.co.x *= f
            v.co.y *= f
    return obj


def rosette(kit, centre, rot, radius, name):
    """Carved rosette: a 16-petal scalloped disc (its back cap sits in the
    wood behind it) with a turned boss."""
    disc = kit.cylinder(radius, 0.010, tuple(centre), WOOD, verts=16, rot=rot, bevel=0.0, name=name)
    scallop(disc, 16, radius * 0.15)
    bm = bmesh.new()
    bm.from_mesh(disc.data)
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.9], context="FACES")
    bm.to_mesh(disc.data)
    bm.free()
    return disc


# -------------------------------------------------------------------- build
def build(kit):
    sec = squircle(8, e=2.4)        # legs, rails, arms, back frame
    sec_small = squircle(6, e=2.2)  # ears, leaves, volutes

    # ------------------------------------------------- cabriole front legs
    for sx in (-1, 1):
        cx, cy = sx * FL[0], FL[1]
        dx, dy = sx * 0.7071, -0.7071        # knee points out of the corner
        ctrl = []
        for o, z, r in ((0.000, 0.400, 0.025), (0.008, 0.352, 0.027), (0.030, 0.302, 0.0275),
                        (0.017, 0.252, 0.022), (0.002, 0.192, 0.0165), (-0.011, 0.125, 0.0128),
                        (-0.015, 0.068, 0.0110), (-0.009, 0.040, 0.0118), (0.002, 0.026, 0.0132),
                        (0.010, 0.017, 0.0140)):
            ctrl.append((cx + dx * o, cy + dy * o, z, r, r))
        sweep(kit, ctrl, sec, WOOD, (1, 0, 0), grain="z", name="cabriole leg")
        # Pad foot: a turned, domed club (wider than the knee) thrown forward
        # of the ankle; the ankle dies into its crown.
        kit.lathe([(0.0, 0.0), (0.0315, 0.0), (0.0326, 0.0045), (0.0295, 0.0120), (0.0205, 0.0210),
                   (0.0, 0.0258)], (cx + dx * 0.012, cy + dy * 0.012, 0.0), WOOD, verts=10, name="pad foot")
        # Knee ears: little brackets running into the front and side rails.
        for ex, ey in ((-sx * 0.036, -0.006), (sx * 0.004, 0.034)):
            ctrl_e = [(cx + ex * 0.2, cy + ey * 0.2 - 0.004, RAIL_Z0 + 0.004, 0.010, 0.010),
                      (cx + ex * 0.7, cy + ey * 0.7 - 0.004, RAIL_Z0 - 0.002, 0.008, 0.012),
                      (cx + ex * 1.2, cy + ey * 1.2 - 0.004, RAIL_Z0 + 0.010, 0.006, 0.006)]
            sweep(kit, ctrl_e, sec_small, WOOD, (0, 0, 1), name="knee ear")

    # ---------------------------------------------------- raked back legs
    for sx in (-1, 1):
        # The leg carries on above the seat as the back stile: it leaves the
        # splayed leg, swings forward onto the back plane and turns up along
        # the 12-degree rake, running inside the side of the back frame.
        ctrl = [(sx * 0.272, 0.352, 0.000, 0.0140, 0.0150), (sx * 0.270, 0.336, 0.090, 0.0150, 0.0160),
                (sx * 0.266, 0.304, 0.210, 0.0170, 0.0180), (sx * BL[0], 0.268, 0.330, 0.0190, 0.0200),
                (sx * BL[0], BL[1], 0.405, 0.0195, 0.0200), (sx * 0.263, 0.2400, 0.462, 0.0205, 0.0175),
                (sx * 0.264, 0.2275, 0.512, 0.0215, 0.0155), (sx * 0.265, 0.2296, 0.545, 0.0215, 0.0150),
                (sx * 0.265, 0.2381, 0.585, 0.0210, 0.0145)]
        sweep(kit, ctrl, sec, WOOD, (1, 0, 0), grain="z", name="back leg")

    # ------------------------------------------------------- seat rails
    rail_z = (RAIL_Z0 + RAIL_Z1) / 2
    rh = (RAIL_Z1 - RAIL_Z0) / 2
    front = []
    for i in range(9):
        x = -FL[0] + 2 * FL[0] * i / 8
        front.append((x, FL[1] - 0.042 * (1 - (x / FL[0]) ** 2), rail_z, 0.014, rh))
    sweep(kit, front, sec, WOOD, (0, 0, 1), grain="x", name="front apron")
    for sx in (-1, 1):
        sweep(kit, [(sx * FL[0], FL[1], rail_z, 0.013, rh), (sx * (FL[0] + BL[0]) / 2, 0.0, rail_z, 0.013, rh),
                    (sx * BL[0], BL[1], rail_z, 0.013, rh)], sec, WOOD, (0, 0, 1), grain="y", name="side rail")
    sweep(kit, [(-BL[0], BL[1], rail_z, 0.013, rh), (BL[0], BL[1], rail_z, 0.013, rh)],
          sec, WOOD, (0, 0, 1), grain="x", name="back rail")
    # Carved rosette at the centre of the apron.
    ros_y = FL[1] - 0.042 - 0.014
    rosette(kit, (0, ros_y - 0.003, rail_z - 0.002), (90, 0, 0), 0.024, "apron rosette")
    kit.lathe([(0.0, -0.001), (0.0105, 0.002), (0.007, 0.007), (0.0, 0.0085)],
              (0, ros_y - 0.007, rail_z - 0.002), WOOD, verts=8, rot=(90, 0, 0), name="rosette boss")

    # ---------------------------------------------------- upholstered seat
    # Plans are the soft_boxes' own superellipses; outline_map() bows the
    # fronts so every ring of the rolled edge moves together.
    # Tight seat deck on the rails (its bowed front shows under the cushion).
    deck_size = (0.604, 0.568, 0.050)
    cushion(kit, deck_size, (0, -0.012, RAIL_Z1 + 0.015), 0.012, 24, 6, rim=0.012,
            bow=(0.040, 0.284), name="seat deck")
    # Loose boxed cushion: soft rolled edges, a sat-in dip, a piped top edge.
    cush_size = (0.544, 0.456, 0.088)
    cush_r, cush_sag, cush_puff, cush_rim = 0.030, 0.010, 0.006, 0.020
    cush_bow = (0.036, 0.228)
    cush_loc = Vector((0, -0.040, RAIL_Z1 + 0.074))
    cushion(kit, cush_size, tuple(cush_loc), cush_r, 28, 10, rim=cush_rim, bow=cush_bow,
            sag=cush_sag, puff=cush_puff, name="seat cushion")
    remap = outline_map(cush_size, cush_r, (0, 1), rim=cush_rim, bow=cush_bow)
    welt = []
    for j in range(29):
        # u = 36 deg is the ring where the rolled edge turns onto the top:
        # a boxed cushion's seam. Same 28 steps as the cushion, so it sits
        # on that ring.
        p = soft_point(cush_size, cush_r, math.radians(36.0), -math.pi + 2 * math.pi * j / 28,
                       sag=cush_sag, puff=cush_puff)
        x, y, z = remap(p)
        welt.append((x * 1.004, y * 1.004 + cush_loc.y, z + cush_loc.z))
    kit.tube(welt, 0.0045, VELVET, verts=4, name="cushion welt")

    # -------------------------------------------------- back and its frame
    right = BACK_OUTLINE_R
    outline = right + [(-u, v) for u, v in reversed(right[1:-1])]
    back_shape = polar_polygon(outline)
    # Upright soft_box (x = width, y = thickness, z = height) raked back by
    # BACK_TILT; its outline in the x/z plane is remapped onto the back shape.
    cushion(kit, (0.512, BACK_DEPTH, 0.596), tuple(back_point(0.0, 0.0, BACK_DEPTH / 2)), 0.034, 20, 12,
            shape=back_shape, axes=(0, 2), puff=0.010, rot=(-math.degrees(BACK_TILT), 0, 0),
            name="back upholstery")
    # Show-wood frame round the back: one closed moulded loop over the
    # serpentine crest; its bottom member sits on the deck behind the
    # cushion and the stiles run into its sides.
    ctrl = []
    a0, a1 = -math.pi / 2, 3 * math.pi / 2
    steps = 24
    for i in range(steps + 1):
        phi = a0 + (a1 - a0) * i / steps
        bx, by = back_shape(phi)
        d = math.hypot(bx, by)
        k = (d + 0.012) / d
        p = back_point(bx * k, by * k, 0.026)
        ctrl.append((p.x, p.y, p.z, 0.017, 0.024))
    sweep(kit, ctrl, sec, WOOD, tuple(BACK_N), name="back frame")
    # Carved crest rosette with two leaf scrolls.
    top = back_shape(math.pi / 2)
    rot_back = (90.0 - math.degrees(BACK_TILT), 0.0, 0.0)
    rosette(kit, back_point(0.0, top[1] + 0.016, 0.052), rot_back, 0.026, "crest rosette")
    kit.lathe([(0.0, 0.0), (0.0115, 0.003), (0.0075, 0.008), (0.0, 0.0095)],
              tuple(back_point(0.0, top[1] + 0.016, 0.057)), WOOD, verts=8, rot=rot_back, name="crest boss")
    # Acanthus scrolls: swell out of the rosette, taper, curl down at the tips.
    for sx in (-1, 1):
        leaf = []
        for i in range(6):
            t = i / 5.0
            u = sx * (0.016 + 0.074 * t)
            v = top[1] + 0.012 + 0.016 * math.sin(math.pi * min(1.0, t * 1.15)) - 0.010 * t
            p = back_point(u, v, 0.047 - 0.006 * t)
            r = 0.0105 * math.sin(math.pi * (0.18 + 0.8 * t)) + 0.0015
            leaf.append((p.x, p.y, p.z, r, r * 0.75))
        sweep(kit, leaf, sec_small, WOOD, tuple(BACK_N), name="crest leaf")

    # ------------------------------------------------------------- arms
    for sx in (-1, 1):
        # Shaped, not piped: (x, y, z, side-view depth, front-view width).
        # The support is a board seen edge-on from the front (12 mm wide,
        # 40 mm deep), waisted at z 0.50, swelling into the knuckle, then the
        # rail flattens to a 22 mm x 44 mm board under the manchette.
        ctrl = [
            (0.290, -0.243, 0.370, 0.0200, 0.0130), (0.296, -0.250, 0.430, 0.0190, 0.0120),
            (0.304, -0.258, 0.505, 0.0165, 0.0110), (0.309, -0.262, 0.570, 0.0175, 0.0125),
            (0.312, -0.256, 0.620, 0.0200, 0.0180), (0.316, -0.236, 0.650, 0.0220, 0.0200),
            (0.322, -0.200, 0.660, 0.0160, 0.0210), (0.333, -0.110, 0.660, 0.0110, 0.0220),
            (0.337, 0.000, 0.664, 0.0110, 0.0220), (0.332, 0.100, 0.672, 0.0110, 0.0220),
            (0.312, 0.180, 0.684, 0.0125, 0.0200), (0.276, 0.226, 0.692, 0.0150, 0.0185),
            (0.263, 0.252, 0.696, 0.0160, 0.0180),
        ]
        ctrl = [(sx * x, y, z, a, b) for x, y, z, a, b in ctrl]
        sweep(kit, ctrl, sec, WOOD, (1, 0, 0), grain="y", name="arm")
        # Carved volute on the outer face of the knuckle: a 1.25-turn spiral
        # bead that rolls forward and down round the knuckle into an eye.
        vol = []
        for i in range(7):
            t = i / 6.0
            th = math.radians(90.0 + 450.0 * t)
            r = 0.020 - 0.014 * t
            face = (1.0 - min(0.95, r / 0.024) ** 2.5) ** 0.4      # squircle bulge of the knuckle
            x = 0.316 + 0.0200 * face - 0.0006
            b = 0.0060 - 0.0030 * t
            vol.append((sx * x, -0.236 + r * math.cos(th), 0.645 + r * math.sin(th), b, b * 0.7))
        sweep(kit, vol, sec_small, WOOD, (1, 0, 0), name="arm volute")

        # Padded manchette on the arm rail: a soft_box bent along the rail.
        def pad_bend(x, y, z, sx=sx):
            # follow the arm rail's outward bow and its rise toward the back
            wy = y - 0.040
            xr = 0.337 - 0.45 * wy * wy
            zr = 0.661 + 0.09 * max(0.0, wy)
            return (x + sx * xr, wy, z + zr + 0.012 + 0.0185)
        # (negative sag = a stuffed crown along the pad)
        cushion(kit, (0.050, 0.250, 0.037), (0, 0, 0), 0.020, 16, 6, deform=pad_bend, sag=-0.006,
                name="arm pad")

    # ---------------------------------------------------------- metadata
    kit.support("seat", (0, -0.06, 0.505), (0.50, 0.44))
    kit.anchor("sit", (0, -0.06, 0.505))
    # One box (§5.3): the whole chair, floor to crest.
    kit.collider((0, 0.015, 0.529), (0.72, 0.70, 1.058))
    kit.tag("pile", "seat", "domestic")
    kit.pile("Seat", mass=1, palette="domestic70s", states=["Upright", "Back", "EdgeLean"])
