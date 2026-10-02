"""1990s office task chair (the black "secretarial / operator" chair of every
open-plan office, c. 1990-98: Steelcase / Global / Hon era).

Construction, bottom to top:
* 5-star base, black glass-filled nylon: tapered legs that slope down from a
  round hub to the tips, 0.66 m across the casters.
* 5 twin-wheel casters: a teardrop body between two 50 mm wheels with
  recessed hub caps, each caster parked at a different swivel angle.
* Gas lift: 3-stage black telescopic shroud over a chrome cylinder.
* Seat mechanism: black pressed-steel housing with a big spoked tension knob
  under the front, a height paddle on the user's right and a tilt-lock lever
  on the left; mounting plate and screws under the black seat shell.
* Seat: soft crowned foam cushion (0.48 W x 0.46 D, top at 0.45 m) with a
  slight dish and a waterfall front, welted top seam, on a black shell.
* Backrest: separate upholstered pad (top at 0.95 m) curved in plan with a
  lumbar swell, in a black plastic back shell, carried on a curved
  flat-steel spine that runs under the seat to the mechanism; height-adjust
  knob and bolted bracket on the rear.
* Loop armrests: closed black loops beside the seat with soft PU pads,
  bolted to the seat underside by flat steel straps.

Real-world reference size: 0.66 W x 0.66 D (base) x 0.95 H; seat 0.45 high.
Front (seat edge) faces -Y. The user's right hand is on -X.
Fabric: Prop_FabricChair. Four slots only (kit rule): the pressed-steel
mechanism, spine and arm straps are painted black and share
Prop_PlasticBlack; Prop_Rubber is the caster treads; Prop_Chrome the gas
cylinder and screws. The PU arm pads also sit on Prop_PlasticBlack until the
kit has a soft-PU slot.

Budget: ~8.9k tris LOD0 (12-sided caster wheels, 4-sided welts, 3-step arm
loop fillets), LOD1 = 0.35 of that.

Upholstery and the loop arms need shapes kitlib has no primitive for (a
rounded-rectangle "pillow" lofted through many rings, a filleted loop), so
this module builds them as bmesh parts and hands them to the kit with
kit._new_object / kit._place / kit._bevel (same UV, slot and join path as
every other primitive).
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_TaskChair"
LOD1 = 0.35            # kit-decimated ~3.1k LOD1 (the chair is at 75% of desk stations)

FABRIC = "Prop_FabricChair"
BLACK = "Prop_PlasticBlack"
RUBBER = "Prop_Rubber"
STEEL = BLACK          # black-painted pressed steel (shares the plastic slot)
CHROME = "Prop_Chrome"
PAD = BLACK            # soft PU arm pads (no soft-PU slot yet)


# --------------------------------------------------------------------- helpers
def _rrect(hw, hd, r, nc=5, nx=5, ny=5):
    """Rounded rectangle outline (CCW, fixed point count for any size)."""
    r = max(min(r, hw * 0.98, hd * 0.98), 0.0015)
    corners = [(hw - r, hd - r, 0.0), (-hw + r, hd - r, 90.0), (-hw + r, -hd + r, 180.0), (hw - r, -hd + r, 270.0)]
    pts = []
    for k, (cx, cy, a0) in enumerate(corners):
        for i in range(nc + 1):
            a = math.radians(a0 + 90.0 * i / nc)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        a_end = math.radians(a0 + 90.0)
        p0 = (cx + r * math.cos(a_end), cy + r * math.sin(a_end))
        nxt = corners[(k + 1) % 4]
        a_nxt = math.radians(nxt[2])
        p1 = (nxt[0] + r * math.cos(a_nxt), nxt[1] + r * math.sin(a_nxt))
        n = nx if k % 2 == 0 else ny
        for i in range(1, n):
            t = i / n
            pts.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))
    return pts


def _soft_block(kit, name, slot, hw, hd, r, profile, loc, rot=(0, 0, 0), warp=None, nc=5, nx=5, ny=5):
    """Upholstery pad: rounded-rect rings lofted through ``profile`` [(inset,
    z), ...] (bottom to top), capped with fans so a warp can dish or bend
    the faces. ``warp(x, y, z)`` reshapes every vertex in local space."""
    bm = bmesh.new()

    def vert(x, y, z):
        return bm.verts.new(warp(x, y, z) if warp else (x, y, z))

    rings = []
    for inset, z in profile:
        rr = max(r - inset, r * 0.35)
        rings.append([vert(x, y, z) for x, y in _rrect(hw - inset, hd - inset, rr, nc, nx, ny)])
    n = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    for ring, z in ((rings[0], profile[0][1]), (rings[-1], profile[-1][1])):
        c = vert(0.0, 0.0, z)
        for i in range(n):
            bm.faces.new((ring[i], ring[(i + 1) % n], c))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = kit._new_object(name, bm, slot, "metres", "xz")
    kit._place(obj, loc, rot)
    return obj


def _fillet_poly(corners, radii, nc=5, nseg=3):
    """Closed convex polygon (CCW, 2D) with every corner rounded."""
    n = len(corners)
    arcs = []
    for i in range(n):
        p = Vector(corners[i])
        a = Vector(corners[i - 1])
        b = Vector(corners[(i + 1) % n])
        d1 = (a - p).normalized()
        d2 = (b - p).normalized()
        ang = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
        r = radii[i]
        dist = r / math.tan(ang / 2)
        c = p + (d1 + d2).normalized() * (r / math.sin(ang / 2))
        t1 = p + d1 * dist
        t2 = p + d2 * dist
        a1 = math.atan2(t1.y - c.y, t1.x - c.x)
        a2 = math.atan2(t2.y - c.y, t2.x - c.x)
        da = a2 - a1
        while da > math.pi:
            da -= 2 * math.pi
        while da < -math.pi:
            da += 2 * math.pi
        arcs.append([(c.x + r * math.cos(a1 + da * k / nc), c.y + r * math.sin(a1 + da * k / nc)) for k in range(nc + 1)])
    out = []
    for i in range(n):
        out.extend(arcs[i])
        p0 = arcs[i][-1]
        p1 = arcs[(i + 1) % n][0]
        for k in range(1, nseg):
            t = k / nseg
            out.append((p0[0] + (p1[0] - p0[0]) * t, p0[1] + (p1[1] - p0[1]) * t))
    return out


def _inset_poly(corners, t):
    """Offset a convex CCW polygon inward by t."""
    n = len(corners)
    lines = []
    for i in range(n):
        p = Vector(corners[i])
        q = Vector(corners[(i + 1) % n])
        d = (q - p).normalized()
        nrm = Vector((-d.y, d.x))
        lines.append((p + nrm * t, d))
    out = []
    for i in range(n):
        p1, d1 = lines[i - 1]
        p2, d2 = lines[i]
        den = d1.x * d2.y - d1.y * d2.x
        s = ((p2.x - p1.x) * d2.y - (p2.y - p1.y) * d2.x) / den
        q = p1 + d1 * s
        out.append((q.x, q.y))
    return out


def _loop_solid(kit, name, slot, outer, inner, width, x, bevel=0.007):
    """Closed loop (outer/inner 2D outlines in Y/Z with equal point counts)
    extruded ``width`` along X and centred at ``x``."""
    bm = bmesh.new()
    n = len(outer)
    def ring(pts, xx):
        return [bm.verts.new((xx, u, v)) for u, v in pts]
    of, ob = ring(outer, x - width / 2), ring(outer, x + width / 2)
    inf, inb = ring(inner, x - width / 2), ring(inner, x + width / 2)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((of[i], of[j], inf[j], inf[i]))
        bm.faces.new((ob[j], ob[i], inb[i], inb[j]))
        bm.faces.new((of[j], of[i], ob[i], ob[j]))
        bm.faces.new((inf[i], inf[j], inb[j], inb[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = kit._new_object(name, bm, slot, "metres", "xz")
    kit._bevel(obj, bevel, 1)
    return obj


def _strip_outline(points, half):
    """Closed 2D outline of a flat bar of half-thickness ``half`` along a
    polyline (mitred joints)."""
    pts = [Vector(p) for p in points]
    left, right = [], []
    for k, p in enumerate(pts):
        if k == 0:
            d = (pts[1] - pts[0]).normalized()
        elif k == len(pts) - 1:
            d = (pts[-1] - pts[-2]).normalized()
        else:
            d = ((pts[k] - pts[k - 1]).normalized() + (pts[k + 1] - pts[k]).normalized()).normalized()
        nrm = Vector((-d.y, d.x))
        left.append(tuple(p + nrm * half))
        right.append(tuple(p - nrm * half))
    return left + list(reversed(right))


def _fillet_path(a, corner, b, radius, steps=8):
    """Points from a to b passing round ``corner`` with an arc of ``radius``."""
    a, c, b = Vector(a), Vector(corner), Vector(b)
    d1 = (a - c).normalized()
    d2 = (b - c).normalized()
    ang = math.acos(max(-1.0, min(1.0, d1.dot(d2))))
    dist = radius / math.tan(ang / 2)
    centre = c + (d1 + d2).normalized() * (radius / math.sin(ang / 2))
    t1, t2 = c + d1 * dist, c + d2 * dist
    a1 = math.atan2(t1.y - centre.y, t1.x - centre.x)
    a2 = math.atan2(t2.y - centre.y, t2.x - centre.x)
    da = a2 - a1
    while da > math.pi:
        da -= 2 * math.pi
    while da < -math.pi:
        da += 2 * math.pi
    pts = [tuple(a)]
    for k in range(steps + 1):
        ak = a1 + da * k / steps
        pts.append((centre.x + radius * math.cos(ak), centre.y + radius * math.sin(ak)))
    pts.append(tuple(b))
    return pts


def _ring_tube(kit, name, slot, points, radius, normal, verts=6):
    """Seamless closed tube (welt cord) through a closed, roughly planar loop
    of 3D points; ``normal`` is the loop's plane normal (keeps the cord's
    cross-section from twisting)."""
    nref = Vector(normal).normalized()
    pts = [Vector(p) for p in points]
    n = len(pts)
    bm = bmesh.new()
    rings = []
    for k in range(n):
        t = ((pts[k] - pts[k - 1]).normalized() + (pts[(k + 1) % n] - pts[k]).normalized()).normalized()
        side = t.cross(nref).normalized()
        up = side.cross(t).normalized()
        rings.append([bm.verts.new(pts[k] + (side * math.cos(2 * math.pi * i / verts) + up * math.sin(2 * math.pi * i / verts)) * radius)
                      for i in range(verts)])
    for k in range(n):
        a, b = rings[k], rings[(k + 1) % n]
        for i in range(verts):
            j = (i + 1) % verts
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


# ----------------------------------------------------------------------- build
def build(kit):
    # ---------------------------------------------------------------- base
    hub_r = 0.048
    kit.lathe([(0.040, 0.086), (0.047, 0.091), (0.049, 0.100), (0.049, 0.148), (0.046, 0.157),
               (0.038, 0.162), (0.030, 0.163)], (0, 0, 0), BLACK, verts=20, name="base hub")
    tip_r = 0.318
    leg_in = 0.028
    length = tip_r - leg_in
    rc = (tip_r + leg_in) / 2
    tip_cz, hub_cz = 0.088, 0.126
    caster_yaw = [25.0, 150.0, 80.0, 300.0, 205.0]
    for k in range(5):
        th = 36.0 + 72.0 * k
        s, c = math.sin(math.radians(th)), math.cos(math.radians(th))
        kit.loft_box((0.040, 0.030), (0.054, 0.050), length, (s * rc, -c * rc, tip_cz), BLACK,
                     back_offset=(0, hub_cz - tip_cz), bevel=0.012, segments=2, rot=(0, 0, th), name="base leg")
        # Socket boss under the toe, and the caster.
        sx, sy = s * 0.303, -c * 0.303
        kit.cylinder(0.015, 0.012, (sx, sy, 0.070), BLACK, verts=12, bevel=0.0, name="caster socket")
        kit.cylinder(0.011, 0.008, (sx, sy, 0.062), BLACK, verts=10, bevel=0.0, name="caster collar")
        yaw = caster_yaw[k]
        ty, tx = math.cos(math.radians(yaw)), -math.sin(math.radians(yaw))
        ax, ay = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        body = [(-0.012, 0.066), (0.004, 0.068), (0.018, 0.060), (0.031, 0.046), (0.036, 0.030),
                (0.032, 0.016), (0.020, 0.010), (0.006, 0.018), (-0.010, 0.040), (-0.014, 0.056)]
        kit.extrude(body, 0.018, (sx, sy, 0), BLACK, plane="yz", rot=(0, 0, yaw), bevel=0.004, segments=1, name="caster body")
        axle = (sx + tx * 0.022, sy + ty * 0.022)
        # 12-sided wheels: 30 deg between side faces stays under the 35 deg
        # smoothing angle, so the tread shades round (10 sides facet).
        for side in (-1, 1):
            wx, wy = axle[0] + ax * 0.0185 * side, axle[1] + ay * 0.0185 * side
            kit.cylinder(0.025, 0.017, (wx, wy, 0.0252), RUBBER, verts=12, rot=(0, 90, yaw), bevel=0.005, segments=1, name="caster wheel")
            hx, hy = axle[0] + ax * 0.0285 * side, axle[1] + ay * 0.0285 * side
            kit.cylinder(0.0115, 0.004, (hx, hy, 0.0252), BLACK, verts=6, rot=(0, 90, yaw), bevel=0.0, name="wheel cap")

    # ------------------------------------------------------- gas lift column
    kit.lathe([(0.0345, 0.150), (0.0345, 0.212), (0.032, 0.216), (0.0315, 0.216), (0.0315, 0.255),
               (0.029, 0.259), (0.0285, 0.259), (0.0285, 0.285), (0.026, 0.288)], (0, 0, 0), BLACK,
              verts=20, name="column shroud")
    kit.cylinder(0.0245, 0.075, (0, 0, 0.3225), CHROME, verts=20, bevel=0.002, segments=1, name="gas cylinder")

    # ------------------------------------------------------- seat mechanism
    seat_y = -0.03
    kit.box((0.15, 0.22, 0.040), (0, 0.0, 0.342), STEEL, bevel=0.008, segments=2, name="mechanism housing")
    kit.box((0.20, 0.27, 0.007), (0, -0.01, 0.3655), STEEL, bevel=0.002, name="mounting plate")
    kit.cylinder(0.030, 0.012, (0, 0.0, 0.318), STEEL, verts=16, bevel=0.003, segments=1, name="column socket")
    for sxs in (-1, 1):
        for syy in (-1, 1):
            kit.cylinder(0.0055, 0.003, (sxs * 0.085, -0.01 + syy * 0.115, 0.3615), CHROME, verts=6,
                         bevel=0.0, name="plate screw")
    # Tension knob: boss and a ribbed knob under the front of the housing.
    kit.cylinder(0.012, 0.04, (0, -0.105, 0.31), STEEL, verts=10, bevel=0.0, name="knob boss")
    kit.cylinder(0.034, 0.026, (0, -0.105, 0.285), BLACK, verts=20, bevel=0.005, segments=1, name="tension knob")
    for i in range(10):
        a = math.radians(i * 36)
        kit.box((0.010, 0.007, 0.022), (math.cos(a) * 0.034, -0.105 + math.sin(a) * 0.034, 0.285), BLACK,
                bevel=0.0, rot=(0, 0, i * 36), name="knob rib")
    # Height paddle (user's right, -X) and tilt lock lever (+X).
    kit.box((0.13, 0.012, 0.006), (-0.135, -0.04, 0.340), STEEL, bevel=0.002, name="height lever")
    kit.box((0.045, 0.030, 0.012), (-0.215, -0.045, 0.342), BLACK, bevel=0.005, segments=2, rot=(0, 0, 8), name="height paddle")
    kit.box((0.10, 0.010, 0.010), (0.12, 0.06, 0.336), STEEL, bevel=0.002, rot=(0, 0, -12), name="tilt lever")
    kit.cylinder(0.011, 0.034, (0.185, 0.072, 0.336), BLACK, verts=10, rot=(0, 90, -12), bevel=0.004, segments=1, name="tilt lever grip")

    # ---------------------------------------------------------------- seat
    shell_z = 0.362
    cush_z = 0.374
    cush_h = 0.076
    seat_hw, seat_hd = 0.240, 0.230

    def taper(x, y, z):
        return (x * (1.0 - 0.05 * max(0.0, y) / seat_hd), y, z)

    _soft_block(kit, "seat shell", BLACK, 0.236, 0.226, 0.075,
                [(0.012, 0.0), (0.003, 0.004), (0.0, 0.011), (0.0, 0.017)],
                (0, seat_y, shell_z), warp=taper, nc=5, nx=4, ny=4)

    def seat_warp(x, y, z):
        f = max(0.0, min(1.0, z / cush_h))
        # back of the seat a touch narrower than the front
        x *= 1.0 - 0.05 * max(0.0, y) / seat_hd
        # dish where you sit, waterfall roll at the front edge
        dish = 0.007 * math.exp(-(x * x) / 0.018 - ((y - 0.03) ** 2) / 0.02)
        roll = 0.020 * max(0.0, (-y - 0.13) / 0.10) ** 2
        return (x, y, z - (dish + roll) * f)

    seat_prof = [(0.020, 0.0), (0.006, 0.008), (0.0, 0.026), (0.002, 0.045), (0.009, 0.059), (0.022, 0.068),
                 (0.045, 0.074), (0.095, cush_h)]
    _soft_block(kit, "seat cushion", FABRIC, seat_hw, seat_hd, 0.085, seat_prof, (0, seat_y, cush_z), warp=seat_warp, nc=5)
    # Welt cord on the top seam.
    welt = [seat_warp(x, y, 0.0605) for x, y in _rrect(seat_hw - 0.0085, seat_hd - 0.0085, 0.085 - 0.0085, 5, 5, 5)]
    welt = [(p[0], p[1] + seat_y, p[2] + cush_z) for p in welt]
    _ring_tube(kit, "seat welt", FABRIC, welt, 0.0035, (0, 0, 1), verts=4)

    # ------------------------------------------------------------- backrest
    alpha = 10.0
    sa, ca = math.sin(math.radians(alpha)), math.cos(math.radians(alpha))
    by, bz = 0.292, 0.734
    back_hw, back_hd = 0.215, 0.210
    bend = 0.62
    back_t = 0.058

    def to_world(u, v, w):
        """Back-local (x, up, out-front) to world."""
        return (u, by + v * sa - w * ca, bz + v * ca + w * sa)

    def cushion_warp(x, y, z):
        f = max(0.0, min(1.0, z / back_t))
        lumbar = 0.014 * math.exp(-((y + 0.08) / 0.09) ** 2)
        return (x * (1.0 + 0.04 * y / back_hd), y, z + bend * x * x + lumbar * f)

    def shell_warp(x, y, z):
        return (x * (1.0 + 0.04 * y / back_hd), y, z + bend * x * x)

    rot_back = (90.0 - alpha, 0, 0)
    back_prof = [(0.012, 0.0), (0.003, 0.008), (0.0, 0.021), (0.005, 0.037), (0.018, 0.049), (0.042, 0.055),
                 (0.100, back_t)]
    _soft_block(kit, "back cushion", FABRIC, back_hw, back_hd, 0.085, back_prof, (0, by, bz), rot=rot_back,
                warp=cushion_warp, nc=5)
    shell_prof = [(0.000, 0.004), (0.000, -0.009), (0.005, -0.020), (0.016, -0.029), (0.045, -0.035),
                  (0.110, -0.037)]
    _soft_block(kit, "back shell", BLACK, back_hw + 0.007, back_hd + 0.007, 0.09, shell_prof, (0, by, bz),
                rot=rot_back, warp=shell_warp, nc=5)
    bwelt = [cushion_warp(x, y, 0.0425) for x, y in _rrect(back_hw - 0.0085, back_hd - 0.0085, 0.085 - 0.0085, 5, 5, 5)]
    bwelt = [to_world(*p) for p in bwelt]
    _ring_tube(kit, "back welt", FABRIC, bwelt, 0.0035, (0, -ca, sa), verts=4)

    # Bracket on the back shell, spine, knob.
    spine_w = -0.037 - 0.008
    kit.box((0.10, 0.20, 0.012), to_world(0, -0.11, -0.040), BLACK, bevel=0.005, segments=2, rot=rot_back,
            name="back bracket")
    top = to_world(0, -0.03, spine_w)
    low = to_world(0, -0.21, spine_w)
    # Spine: horizontal under the seat, filleted up into the back line.
    d = Vector((top[1] - low[1], top[2] - low[2])).normalized()
    # corner where the back line meets z = 0.340
    k = (low[2] - 0.340) / d.y
    corner = (low[1] - d.x * k, 0.340)
    path = _fillet_path((0.03, 0.340), corner, (top[1], top[2]), 0.11, steps=8)
    kit.extrude(_strip_outline(path, 0.006), 0.05, (0, 0, 0), STEEL, plane="yz", bevel=0.0035, name="back spine")
    for v in (-0.17, -0.05):
        for u in (-0.016, 0.016):
            kit.cylinder(0.005, 0.004, to_world(u, v, spine_w - 0.007), CHROME, verts=6, rot=rot_back,
                         bevel=0.0, name="spine screw")
    kit.cylinder(0.024, 0.020, to_world(0, -0.11, spine_w - 0.016), BLACK, verts=16, rot=rot_back,
                 bevel=0.005, segments=1, name="back height knob")
    kit.cylinder(0.010, 0.012, to_world(0, -0.11, spine_w - 0.008), STEEL, verts=10, rot=rot_back,
                 bevel=0.0, name="knob stem")

    # ------------------------------------------------------- loop armrests
    loop_outer = [(-0.140, 0.352), (0.130, 0.352), (0.170, 0.640), (-0.160, 0.640)]
    radii_o = [0.030, 0.030, 0.055, 0.055]
    loop_inner = _inset_poly(loop_outer, 0.026)
    radii_i = [0.010, 0.010, 0.030, 0.030]
    outer = _fillet_poly(loop_outer, radii_o, nc=3, nseg=1)
    inner = _fillet_poly(loop_inner, radii_i, nc=3, nseg=1)
    for side in (-1, 1):
        x = side * 0.268
        _loop_solid(kit, "arm loop", BLACK, outer, inner, 0.034, x, bevel=0.008)
        _soft_block(kit, "arm pad", PAD, 0.036, 0.135, 0.032,
                    [(0.005, 0.0), (0.0, 0.009), (0.003, 0.022), (0.012, 0.028), (0.030, 0.030)],
                    (x, 0.005, 0.636), nc=2, nx=2, ny=4)
        # Straps bolted flat to the shell underside (shell bottom at z 0.362).
        kit.box((0.17, 0.05, 0.008), (side * 0.175, -0.04, 0.358), STEEL, bevel=0.002, segments=1, name="arm strap")
        kit.box((0.17, 0.05, 0.008), (side * 0.175, 0.09, 0.358), STEEL, bevel=0.002, segments=1, name="arm strap")
        for yy in (-0.04, 0.09):
            kit.cylinder(0.0055, 0.004, (side * 0.13, yy, 0.3525), CHROME, verts=6, bevel=0.0, name="strap screw")

    # ------------------------------------------------------------ metadata
    seat_top = cush_z + cush_h
    kit.support("seat", (0, seat_y, seat_top), (0.40, 0.38))
    kit.anchor("sit", (0, seat_y, seat_top))
    kit.anchor("back_top", (0, by + back_hd * sa, 0.95))
    kit.collider((0, 0.02, 0.085), (0.63, 0.64, 0.17))
    kit.collider((0, 0, 0.26), (0.08, 0.08, 0.18))
    kit.collider((0, seat_y, 0.51), (0.58, 0.47, 0.32))
    kit.collider((0, 0.27, 0.74), (0.46, 0.19, 0.43))
    kit.tag("office", "seat")
    kit.pile("Seat", mass=1, palette="office90s", states=["Upright", "Inverted", "Side", "Back"])
