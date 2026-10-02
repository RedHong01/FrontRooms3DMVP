"""Blush-pink velvet Queen Anne / bergere-style open armchair, c. 1980-95
reproduction (the department-store "French" chair: exposed cherry show-wood
frame, two cabriole front legs on turned pad feet, splayed back legs that
carry on above the seat as stiles into the back frame, a bowed front apron
with a carved rosette, open arms whose shaped (board-section) supports
sweep up into knuckles carved with a spiral volute, padded velvet
manchettes on flat arm rails, a tall oval-ish serpentine-crested
upholstered back inside a closed moulded frame with a carved crest
rosette, a tight upholstered seat deck and a thick piped loose cushion).
Budget ~11.8k tris (chair cap 12k).

Real-world reference size: 0.72 m wide (across the arms), 0.70 m deep,
1.05 m tall to the crest. Seat (cushion top) 0.50 m, arm pads 0.68 m,
back raked 12 degrees. Front (seat) faces -Y. Origin = floor under the
centre of the seat. Film: Still A, the pink armchair tipped onto the desk.
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_QueenAnneArmchair"
SMOOTH_ANGLE = 42.0

WOOD = "Prop_WoodCherry"
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


def squircle(n, e=3.0, phase=0.0):
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


def sweep(kit, ctrl, section, slot, ref, sub=3, name="sweep"):
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
    return obj


def superellipse(a, b, e=4.0):
    def shape(phi):
        c, s = math.cos(phi), math.sin(phi)
        return (a * math.copysign(abs(c) ** (2 / e), c), b * math.copysign(abs(s) ** (2 / e), s))
    return shape


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
            if t > 0 and -1e-9 <= s <= 1 + 1e-9 and (best is None or t < best):
                best = t
        return (d.x * best, d.y * best)
    return shape


def pillow(kit, shape, profile, loc, slot, verts=48, rot=(0, 0, 0), deform=None, rim=None, name="pillow"):
    """Upholstered volume: lathe a (unit radius, height) profile, then map
    every ring onto ``shape`` (phi -> outline point). Gives crowned tops and
    rolled edges like stuffed fabric. ``deform(x, y, z)`` may bend it.
    With ``rim`` (metres) rings are inset by a constant distance instead of
    scaled, so long narrow pads keep an even rolled edge."""
    obj = kit.lathe(profile, loc, slot, verts=verts, rot=rot, name=name)
    for v in obj.data.vertices:
        r = math.hypot(v.co.x, v.co.y)
        if r < 1e-9:
            x, y = 0.0, 0.0
        else:
            sx, sy = shape(math.atan2(v.co.y, v.co.x))
            if rim is None:
                x, y = sx * r, sy * r
            else:
                d = math.hypot(sx, sy)
                f = max(0.02, 1.0 - (1.0 - min(r, 1.0)) * rim / d)
                x, y = sx * f, sy * f
        z = v.co.z
        if deform:
            x, y, z = deform(x, y, z)
        v.co = (x, y, z)
    recalc(obj)
    return obj


def welt(kit, shape, r_unit, z, radius, slot, n=48, deform=None, name="welt"):
    """Piping cord along a pillow outline at a given profile radius/height."""
    pts = []
    for i in range(n + 1):
        phi = 2 * math.pi * i / n
        sx, sy = shape(phi)
        p = (sx * r_unit, sy * r_unit, z)
        pts.append(deform(*p) if deform else p)
    return kit.tube(pts, radius, slot, verts=6, name=name)


def back_point(u, v, w=0.0):
    return BACK_O + BACK_U * u + BACK_V * v + BACK_N * w


# -------------------------------------------------------------------- build
def build(kit):
    sec_leg = squircle(12, e=3.2)
    sec_rail = squircle(12, e=3.2)     # max turn 37 deg < SMOOTH_ANGLE: no crease lines
    sec_arm = squircle(12, e=2.5)
    sec_small = squircle(8, e=2.6)

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
        sweep(kit, ctrl, sec_leg, WOOD, (1, 0, 0), sub=2, name="cabriole leg")
        # Pad foot: a turned, domed club (62 mm, wider than the 55 mm knee)
        # on a thin pad disc, thrown forward of the ankle; the ankle dies
        # into its crown.
        kit.lathe([(0.0, 0.0), (0.0310, 0.0), (0.0326, 0.0018), (0.0326, 0.0052), (0.0302, 0.0068),
                   (0.0300, 0.0100), (0.0272, 0.0160), (0.0212, 0.0212), (0.0120, 0.0246), (0.0, 0.0258)],
                  (cx + dx * 0.012, cy + dy * 0.012, 0.0), WOOD, verts=16, name="pad foot")
        # Knee block under the rail corner.
        kit.box((0.050, 0.050, 0.060), (cx, cy, RAIL_Z0 + 0.028), WOOD, bevel=0.010, segments=2,
                name="knee block")
        # Knee ears: little brackets running into the front and side rails.
        for ex, ey in ((-sx * 0.036, -0.006), (sx * 0.004, 0.034)):
            ctrl_e = [(cx + ex * 0.2, cy + ey * 0.2 - 0.004, RAIL_Z0 + 0.004, 0.010, 0.010),
                      (cx + ex * 0.7, cy + ey * 0.7 - 0.004, RAIL_Z0 - 0.002, 0.008, 0.012),
                      (cx + ex * 1.2, cy + ey * 1.2 - 0.004, RAIL_Z0 + 0.010, 0.006, 0.006)]
            sweep(kit, ctrl_e, sec_small, WOOD, (0, 0, 1), sub=2, name="knee ear")

    # ---------------------------------------------------- raked back legs
    for sx in (-1, 1):
        # The leg carries on above the seat as the back stile: it leaves the
        # splayed leg, swings forward onto the back plane and turns up along
        # the 12-degree rake, running 6 cm inside the side of the back frame
        # (v -0.21..-0.14). Scales are (side-view depth, front-view width),
        # kept 2-3 mm inside the frame's 48 x 34 mm moulding so the frame
        # reads proud of the stile where they meet.
        ctrl = [(sx * 0.272, 0.352, 0.000, 0.0140, 0.0150), (sx * 0.270, 0.336, 0.090, 0.0150, 0.0160),
                (sx * 0.266, 0.304, 0.210, 0.0170, 0.0180), (sx * BL[0], 0.268, 0.330, 0.0190, 0.0200),
                (sx * BL[0], BL[1], 0.405, 0.0195, 0.0200), (sx * 0.263, 0.2400, 0.462, 0.0205, 0.0175),
                (sx * 0.264, 0.2275, 0.512, 0.0215, 0.0155), (sx * 0.265, 0.2296, 0.545, 0.0215, 0.0150),
                (sx * 0.265, 0.2381, 0.585, 0.0210, 0.0145)]
        sweep(kit, ctrl, sec_leg, WOOD, (1, 0, 0), sub=2, name="back leg")

    # ------------------------------------------------------- seat rails
    rail_z = (RAIL_Z0 + RAIL_Z1) / 2
    rh = (RAIL_Z1 - RAIL_Z0) / 2
    front = []
    for i in range(9):
        x = -FL[0] + 2 * FL[0] * i / 8
        front.append((x, FL[1] - 0.042 * (1 - (x / FL[0]) ** 2), rail_z, 0.014, rh))
    sweep(kit, front, sec_rail, WOOD, (0, 0, 1), sub=2, name="front apron")
    for sx in (-1, 1):
        sweep(kit, [(sx * FL[0], FL[1], rail_z, 0.013, rh), (sx * (FL[0] + BL[0]) / 2, 0.0, rail_z, 0.013, rh),
                    (sx * BL[0], BL[1], rail_z, 0.013, rh)], sec_rail, WOOD, (0, 0, 1), sub=1, name="side rail")
    sweep(kit, [(-BL[0], BL[1], rail_z, 0.013, rh), (0.0, BL[1], rail_z, 0.013, rh), (BL[0], BL[1], rail_z, 0.013, rh)],
          sec_rail, WOOD, (0, 0, 1), sub=1, name="back rail")
    # Moulded bead along the bottom of the front apron.
    bead = [(x, y - 0.012, RAIL_Z0 + 0.006, 0.0065, 0.0065) for x, y, z, a, b in front]
    sweep(kit, bead, squircle(8, e=2.0), WOOD, (0, 0, 1), sub=2, name="apron bead")
    # Carved rosette at the centre of the apron.
    ros_y = FL[1] - 0.042 - 0.014
    ros = kit.cylinder(0.024, 0.010, (0, ros_y - 0.003, rail_z - 0.002), WOOD, verts=24, rot=(90, 0, 0),
                       bevel=0.003, segments=1, name="apron rosette")
    scallop(ros, 24, 0.0035)
    kit.lathe([(0.0, -0.001), (0.010, -0.001), (0.0105, 0.003), (0.007, 0.007), (0.0, 0.0085)],
              (0, ros_y - 0.007, rail_z - 0.002), WOOD, verts=12, rot=(90, 0, 0), name="rosette boss")

    # ---------------------------------------------------- upholstered seat
    def bow_front(amount, half_y):
        def f(x, y, z):
            if y < 0:
                y -= amount * (1 - min(1.0, (x / 0.30) ** 2)) * (-y / half_y) ** 2
            return x, y, z
        return f
    deck_shape = superellipse(0.302, 0.284, e=5.0)
    deck_bow = bow_front(0.040, 0.284)
    pillow(kit, deck_shape, [(0.0, 0.0), (0.93, 0.0), (0.985, 0.006), (1.0, 0.020), (0.985, 0.034),
                             (0.94, 0.042), (0.6, 0.046), (0.0, 0.047)],
           (0, -0.012, RAIL_Z1 - 0.010), VELVET, verts=48, deform=deck_bow, name="seat deck")
    # Loose boxed cushion with piping on both edges.
    cush_shape = superellipse(0.272, 0.228, e=4.5)
    cush_bow = bow_front(0.036, 0.228)
    cz = RAIL_Z1 + 0.030
    cushion_prof = [(0.0, 0.0), (0.90, 0.0), (0.960, 0.003), (0.988, 0.012), (1.0, 0.040),
                    (0.990, 0.066), (0.962, 0.076), (0.90, 0.080), (0.55, 0.086), (0.0, 0.088)]
    pillow(kit, cush_shape, cushion_prof, (0, -0.040, cz), VELVET, verts=48, deform=cush_bow,
           name="seat cushion")

    def cush_world(x, y, z):
        x, y, z = cush_bow(x, y, z)
        return (x, y - 0.040, z + cz)
    welt(kit, cush_shape, 0.982, 0.0085, 0.0048, VELVET, n=32, deform=cush_world, name="cushion welt")
    welt(kit, cush_shape, 0.982, 0.0715, 0.0048, VELVET, n=32, deform=cush_world, name="cushion welt")

    # -------------------------------------------------- back and its frame
    right = BACK_OUTLINE_R
    outline = right + [(-u, v) for u, v in reversed(right[1:-1])]
    back_shape = polar_polygon(outline)
    rot_back = (90.0 - math.degrees(BACK_TILT), 0.0, 0.0)
    pillow(kit, back_shape, [(0.0, 0.0), (0.94, 0.0), (0.985, 0.006), (1.0, 0.020), (0.99, 0.038),
                             (0.955, 0.055), (0.86, 0.072), (0.55, 0.088), (0.0, 0.094)],
           tuple(BACK_O), VELVET, verts=56, rot=rot_back, name="back upholstery")
    # Show-wood frame round the back: one closed moulded loop over the
    # serpentine crest; its bottom member sits on the deck behind the
    # cushion and the stiles run into its sides.
    ctrl = []
    a0, a1 = -math.pi / 2, 3 * math.pi / 2
    steps = 28
    for i in range(steps + 1):
        phi = a0 + (a1 - a0) * i / steps
        bx, by = back_shape(phi)
        d = math.hypot(bx, by)
        k = (d + 0.012) / d
        p = back_point(bx * k, by * k, 0.026)
        ctrl.append((p.x, p.y, p.z, 0.017, 0.024))
    sweep(kit, ctrl, sec_rail, WOOD, tuple(BACK_N), sub=2, name="back frame")
    # Carved crest rosette with two leaf scrolls.
    top = back_shape(math.pi / 2)
    cp = back_point(0.0, top[1] + 0.016, 0.052)
    crest = kit.cylinder(0.026, 0.012, tuple(cp), WOOD, verts=24, rot=rot_back, bevel=0.003, segments=1,
                         name="crest rosette")
    scallop(crest, 24, 0.004)
    kit.lathe([(0.0, 0.0), (0.011, 0.0), (0.0115, 0.004), (0.0075, 0.008), (0.0, 0.0095)],
              tuple(back_point(0.0, top[1] + 0.016, 0.057)), WOOD, verts=12, rot=rot_back, name="crest boss")
    # Acanthus scrolls: swell out of the rosette, taper, curl down at the tips.
    for sx in (-1, 1):
        leaf = []
        for i in range(7):
            t = i / 6.0
            u = sx * (0.016 + 0.074 * t)
            v = top[1] + 0.012 + 0.016 * math.sin(math.pi * min(1.0, t * 1.15)) - 0.010 * t
            p = back_point(u, v, 0.047 - 0.006 * t)
            r = 0.0105 * math.sin(math.pi * (0.18 + 0.8 * t)) + 0.0015
            leaf.append((p.x, p.y, p.z, r, r * 0.75))
        sweep(kit, leaf, sec_small, WOOD, tuple(BACK_N), sub=2, name="crest leaf")

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
        sweep(kit, ctrl, sec_arm, WOOD, (1, 0, 0), sub=2, name="arm")
        # Carved volute on the outer face of the knuckle: a 1.25-turn spiral
        # bead that starts on the rail top, rolls forward and down round the
        # knuckle and winds into an eye. It follows the knuckle's rounded face.
        vol = []
        for i in range(15):
            t = i / 14.0
            th = math.radians(90.0 + 450.0 * t)
            r = 0.020 - 0.014 * t
            face = (1.0 - min(0.95, r / 0.024) ** 2.5) ** 0.4      # squircle bulge of the knuckle
            x = 0.316 + 0.0200 * face - 0.0006
            b = 0.0060 - 0.0030 * t
            vol.append((sx * x, -0.236 + r * math.cos(th), 0.645 + r * math.sin(th), b, b * 0.7))
        sweep(kit, vol, sec_small, WOOD, (1, 0, 0), sub=1, name="arm volute")
        # Padded manchette on the arm rail.
        pad_shape = superellipse(0.025, 0.125, e=2.8)

        def pad_bend(x, y, z, sx=sx):
            # follow the arm rail's outward bow and its rise toward the back
            wy = y - 0.040
            xr = 0.337 - 0.45 * wy * wy
            zr = 0.661 + 0.09 * max(0.0, wy)
            return (x + sx * xr, wy, z + zr + 0.012)
        pillow(kit, pad_shape, [(0.0, 0.0), (0.88, 0.0), (0.95, 0.003), (1.0, 0.011), (0.975, 0.022),
                                (0.90, 0.030), (0.70, 0.035), (0.0, 0.037)],
               (0, 0, 0), VELVET, verts=28, deform=pad_bend, rim=0.032, name="arm pad")
        welt(kit, pad_shape, 0.995, 0.0065, 0.0032, VELVET, n=24, deform=pad_bend, name="arm pad welt")

    # ---------------------------------------------------------- metadata
    kit.support("seat", (0, -0.06, 0.505), (0.50, 0.44))
    kit.anchor("sit", (0, -0.06, 0.505))
    kit.collider((0, -0.01, 0.255), (0.70, 0.66, 0.51))
    # Raked back as two steps; arms cover rail + manchette (top 0.73).
    kit.collider((0, 0.228, 0.63), (0.60, 0.145, 0.24))
    kit.collider((0, 0.29, 0.90), (0.60, 0.16, 0.30))
    kit.collider((-0.322, -0.01, 0.645), (0.08, 0.52, 0.17))
    kit.collider((0.322, -0.01, 0.645), (0.08, 0.52, 0.17))
    kit.tag("pile", "seat", "domestic")
    kit.pile("Seat", mass=1, palette="domestic70s", states=["Upright", "Back", "Side"])


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
