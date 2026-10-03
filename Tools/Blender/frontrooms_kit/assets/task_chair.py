"""1990s office task chair (the black "secretarial / operator" chair of every
open-plan office, c. 1990-98: Steelcase / Global / Hon era).

Construction, bottom to top:
* 5-star base, black glass-filled nylon: tapered legs that slope down from a
  round hub to the tips, 0.66 m across the casters.
* 5 twin-wheel nylon casters: a teardrop hood between two 50 mm wheels,
  each caster parked at a different swivel angle.
* Gas lift: 3-stage black telescopic shroud over a chrome cylinder.
* Seat mechanism: black pressed-steel housing on a mounting plate, a big
  lobed tension knob under the front, a height paddle on the user's right
  and a tilt-lock lever on the left.
* Seat: soft crowned foam cushion (0.48 W x 0.46 D, top at 0.45 m) with a
  slight dish and a waterfall front, welted top seam, on a black shell.
* Backrest: separate upholstered pad (top at 0.95 m) curved in plan with a
  lumbar swell, in a black plastic back shell, carried on a curved
  flat-steel spine that runs under the seat to the mechanism; height-adjust
  knob and bracket on the rear.
* Loop armrests: closed black loops beside the seat with soft PU pads,
  bolted to the seat underside by flat steel straps.

Real-world reference size: 0.66 W x 0.66 D (base) x 0.95 H; seat 0.45 high.
Front (seat edge) faces -Y. The user's right hand is on -X.

Slots (4, §5.3 + the round-2 Prop_FoamPU): Prop_FabricChair (cushions),
Prop_PlasticBlack (nylon base, casters, shells, and the black-painted
pressed-steel mechanism / spine / straps: painted steel is non-metallic, so
it shares the plastic's dielectric slot), Prop_Chrome (gas cylinder),
Prop_FoamPU (arm pads). The caster wheels are nylon, not rubber, so the old
Prop_Rubber slot is gone.

Budget (§5.3 4,500 / 1,800): ~4.5k tris LOD0 (was 8.9k), LOD1 0.40.
* Upholstery keeps its tessellation where it is seen (crowned cushion,
  dish, waterfall, lumbar, plan curve, 5-step corners); the separate welt
  cords are replaced by a bead-and-crevice ring in each cushion's own
  profile, which draws the same dark seam line. Faces and rings buried in a
  shell are left out.
* Casters: twin 8-sided wheels with a rounded outer tyre edge, a 1-segment
  bevelled hood and one stem (was socket + collar + hub caps).
* 1-segment bevels on the base legs, housing, bracket and spine
  (SMOOTH_ANGLE 50 shades a 45-degree bevel as a round-over); no bevels on
  rods and straps thinner than 8 mm; hood and knob bevels only round their
  90-degree rims. The screws under the seat and the knob's separate ribs are
  gone (the knob is one lobed extrusion); the four spine screws on the back
  stay as 6-sided chrome domes because they catch the light.

Upholstery and the loop arms need shapes kitlib has no primitive for (a
rounded-rectangle "pillow" lofted through rings, a filleted loop), so this
module builds them as bmesh parts and hands them to the kit with
kit._new_object / kit._place / kit._bevel (same UV, slot and join path as
every other primitive).
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_TaskChair"
LOD1 = 0.40            # kit-decimated ~1.8k LOD1 (§5.3)
SMOOTH_ANGLE = 50.0

FABRIC = "Prop_FabricChair"
BLACK = "Prop_PlasticBlack"
STEEL = BLACK          # black-painted pressed steel (dielectric, shares the plastic slot)
CHROME = "Prop_Chrome"
PAD = "Prop_FoamPU"    # soft matte PU arm pads


# --------------------------------------------------------------------- helpers
def _rrect(hw, hd, r, nc, nx, ny):
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


def _soft_block(kit, name, slot, hw, hd, r, profile, loc, rot=(0, 0, 0), warp=None, nc=3, nx=3, ny=3,
                cap_bottom=True, cap_top=True):
    """Upholstery pad: rounded-rect rings lofted through ``profile`` [(inset,
    z), ...] (bottom to top; a negative inset bulges out, e.g. a welt bead),
    capped with fans so a warp can dish or bend the faces. ``warp(x, y, z)``
    reshapes every vertex in local space. A cap buried in a shell is skipped."""
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
    caps = ([(rings[0], profile[0][1])] if cap_bottom else []) + ([(rings[-1], profile[-1][1])] if cap_top else [])
    for ring, z in caps:
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
    kit._bevel(obj, bevel, 1, angle=50.0)     # the loop's faces, not its 30-deg fillet steps
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


# ----------------------------------------------------------------------- build
def build(kit):
    # ---------------------------------------------------------------- base
    # Hub: top buried in the column shroud.
    kit.lathe([(0.040, 0.086), (0.049, 0.097), (0.049, 0.148), (0.042, 0.159), (0.030, 0.163)], (0, 0, 0), BLACK,
              verts=12, close_top=False, name="base hub")
    tip_r = 0.318
    leg_in = 0.028
    length = tip_r - leg_in
    rc = (tip_r + leg_in) / 2
    tip_cz, hub_cz = 0.088, 0.126
    caster_yaw = [25.0, 150.0, 80.0, 300.0, 205.0]
    body = [(-0.012, 0.066), (0.006, 0.068), (0.026, 0.054), (0.036, 0.032), (0.030, 0.014),
            (0.016, 0.010), (-0.006, 0.030), (-0.014, 0.054)]
    for k in range(5):
        th = 36.0 + 72.0 * k
        s, c = math.sin(math.radians(th)), math.cos(math.radians(th))
        kit.loft_box((0.040, 0.030), (0.054, 0.050), length, (s * rc, -c * rc, tip_cz), BLACK,
                     back_offset=(0, hub_cz - tip_cz), bevel=0.012, segments=1, rot=(0, 0, th), name="base leg")
        # Caster: one stem into the toe, the hood, twin wheels.
        sx, sy = s * 0.303, -c * 0.303
        kit.cylinder(0.012, 0.018, (sx, sy, 0.066), BLACK, verts=6, bevel=0.0, name="caster stem")
        yaw = caster_yaw[k]
        ty, tx = math.cos(math.radians(yaw)), -math.sin(math.radians(yaw))
        ax, ay = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        hood = kit.extrude(body, 0.018, (sx, sy, 0), BLACK, plane="yz", rot=(0, 0, yaw), bevel=0.0, name="caster hood")
        kit._bevel(hood, 0.004, 1, angle=50.0)     # round the side faces' rims, not the outline's 45-deg steps
        axle = (sx + tx * 0.022, sy + ty * 0.022)
        h = 0.0085
        for side in (-1, 1):
            wx, wy = axle[0] + ax * 0.0185 * side, axle[1] + ay * 0.0185 * side
            # Rounded tyre edge on the outer side only (the inner face meets the hood).
            prof = ([(0.025, -h), (0.025, h - 0.0035), (0.0215, h)] if side > 0 else
                    [(0.0215, -h), (0.025, -h + 0.0035), (0.025, h)])
            kit.lathe(prof, (wx, wy, 0.0252), BLACK, verts=8, rot=(0, 90, yaw), name="caster wheel")

    # ------------------------------------------------------- gas lift column
    kit.lathe([(0.0345, 0.150), (0.0345, 0.213), (0.0315, 0.216), (0.0315, 0.256), (0.0285, 0.259),
               (0.0285, 0.286), (0.0260, 0.288)], (0, 0, 0), BLACK, verts=12, close_bottom=False,
              name="column shroud")
    kit.lathe([(0.0245, 0.284), (0.0245, 0.346)], (0, 0, 0), CHROME, verts=12, close_bottom=False,
              close_top=False, name="gas cylinder")

    # ------------------------------------------------------- seat mechanism
    seat_y = -0.03
    kit.box((0.15, 0.22, 0.040), (0, 0.0, 0.342), STEEL, bevel=0.008, segments=1, name="mechanism housing")
    kit.box((0.20, 0.27, 0.007), (0, -0.01, 0.3655), STEEL, bevel=0.0, name="mounting plate")
    kit.cylinder(0.030, 0.012, (0, 0.0, 0.318), STEEL, verts=10, bevel=0.0, name="column socket")
    # Tension knob: a boss and one lobed knob under the front of the housing.
    kit.cylinder(0.012, 0.04, (0, -0.105, 0.31), STEEL, verts=6, bevel=0.0, name="knob boss")
    lobes = [((0.034 if i % 2 == 0 else 0.027) * math.cos(math.radians(i * 36)),
              (0.034 if i % 2 == 0 else 0.027) * math.sin(math.radians(i * 36))) for i in range(10)]
    knob = kit.extrude(lobes, 0.026, (0, -0.105, 0.285), BLACK, plane="xy", bevel=0.0, name="tension knob")
    kit._bevel(knob, 0.004, 1, angle=50.0)
    # Height paddle (user's right, -X) and tilt lock lever (+X).
    kit.box((0.13, 0.012, 0.006), (-0.135, -0.04, 0.340), STEEL, bevel=0.0, name="height lever")
    kit.box((0.045, 0.030, 0.012), (-0.215, -0.045, 0.342), BLACK, bevel=0.005, segments=1, rot=(0, 0, 8),
            name="height paddle")
    kit.box((0.10, 0.010, 0.010), (0.12, 0.06, 0.336), STEEL, bevel=0.0, rot=(0, 0, -12), name="tilt lever")
    kit.cylinder(0.011, 0.034, (0.185, 0.072, 0.336), BLACK, verts=6, rot=(0, 90, -12), bevel=0.0,
                 name="tilt lever grip")

    # ---------------------------------------------------------------- seat
    shell_z = 0.362
    cush_z = 0.374
    cush_h = 0.076
    seat_hw, seat_hd = 0.240, 0.230

    def taper(x, y, z):
        return (x * (1.0 - 0.05 * max(0.0, y) / seat_hd), y, z)

    # Shell: both caps (the top one closes the gap round the cushion's foot).
    _soft_block(kit, "seat shell", BLACK, 0.236, 0.226, 0.075,
                [(0.012, 0.0), (0.003, 0.004), (0.0, 0.011), (0.0, 0.017)],
                (0, seat_y, shell_z), warp=taper, nc=3, nx=2, ny=2)

    def seat_warp(x, y, z):
        f = max(0.0, min(1.0, z / cush_h))
        # back of the seat a touch narrower than the front
        x *= 1.0 - 0.05 * max(0.0, y) / seat_hd
        # dish where you sit, waterfall roll at the front edge
        dish = 0.007 * math.exp(-(x * x) / 0.018 - ((y - 0.03) ** 2) / 0.02)
        roll = 0.020 * max(0.0, (-y - 0.13) / 0.10) ** 2
        return (x, y, z - (dish + roll) * f)

    # Boxing (its foot starts inside the shell rim), then the welt: a cord
    # bead proud of the face panel with a 90-degree crevice on its inner side
    # (the dark seam line the separate cord used to make), crowned top.
    seat_prof = [(0.006, 0.003), (0.0, 0.032), (0.0045, 0.0540), (-0.0035, 0.0590), (0.0005, 0.0670), (0.0065, 0.0600),
                 (0.017, 0.0695), (0.045, 0.0745), (0.095, cush_h)]
    _soft_block(kit, "seat cushion", FABRIC, seat_hw, seat_hd, 0.085, seat_prof, (0, seat_y, cush_z),
                warp=seat_warp, nc=5, nx=3, ny=3, cap_bottom=False)

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
    # (two inner crown rings sample the plan bend and the lumbar swell, so the
    # centre fan stays small and doesn't facet into an X under top light)
    back_prof = [(0.004, 0.002), (0.0, 0.023), (0.004, 0.0345), (-0.0030, 0.0395), (0.0005, 0.0470), (0.0055, 0.0425),
                 (0.016, 0.0500), (0.045, 0.0560), (0.090, 0.0577), (0.140, back_t)]
    _soft_block(kit, "back cushion", FABRIC, back_hw, back_hd, 0.085, back_prof, (0, by, bz), rot=rot_back,
                warp=cushion_warp, nc=5, nx=3, ny=3, cap_bottom=False)
    shell_prof = [(0.000, 0.004), (0.000, -0.009), (0.008, -0.024), (0.030, -0.033), (0.110, -0.037)]
    _soft_block(kit, "back shell", BLACK, back_hw + 0.007, back_hd + 0.007, 0.09, shell_prof, (0, by, bz),
                rot=rot_back, warp=shell_warp, nc=5, nx=3, ny=3)

    # Bracket on the back shell, spine, knob.
    spine_w = -0.037 - 0.008
    kit.box((0.10, 0.20, 0.012), to_world(0, -0.11, -0.040), BLACK, bevel=0.005, segments=1, rot=rot_back,
            name="back bracket")
    top = to_world(0, -0.03, spine_w)
    low = to_world(0, -0.21, spine_w)
    # Spine: horizontal under the seat, filleted up into the back line.
    d = Vector((top[1] - low[1], top[2] - low[2])).normalized()
    k = (low[2] - 0.340) / d.y        # corner where the back line meets z = 0.340
    corner = (low[1] - d.x * k, 0.340)
    path = _fillet_path((0.03, 0.340), corner, (top[1], top[2]), 0.11, steps=4)
    kit.extrude(_strip_outline(path, 0.006), 0.05, (0, 0, 0), STEEL, plane="yz", bevel=0.0035, segments=1,
                name="back spine")
    kit.cylinder(0.024, 0.020, to_world(0, -0.11, spine_w - 0.016), BLACK, verts=10, rot=rot_back,
                 bevel=0.005, segments=1, name="back height knob")
    # Four domed chrome screws holding the spine to the bracket (they catch
    # the light on the chair's back, the side most chairs show).
    for v in (-0.17, -0.05):
        for u in (-0.016, 0.016):
            kit.lathe([(0.0052, 0.0), (0.0044, 0.0021), (0.0, 0.0030)], to_world(u, v, spine_w - 0.006), CHROME,
                      verts=6, rot=(rot_back[0] + 180.0, 0, 0), close_bottom=False, name="spine screw")

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
                    [(0.005, 0.0), (0.0, 0.009), (0.004, 0.023), (0.030, 0.030)],
                    (x, 0.005, 0.636), nc=2, nx=2, ny=3)
        # Straps bolted flat to the shell underside (shell bottom at z 0.362).
        kit.box((0.17, 0.05, 0.008), (side * 0.175, -0.04, 0.358), STEEL, bevel=0.0, name="arm strap")
        kit.box((0.17, 0.05, 0.008), (side * 0.175, 0.09, 0.358), STEEL, bevel=0.0, name="arm strap")

    # ------------------------------------------------------------ metadata
    seat_top = cush_z + cush_h
    kit.support("seat", (0, seat_y, seat_top), (0.40, 0.38))
    kit.anchor("sit", (0, seat_y, seat_top))
    kit.anchor("back_top", (0, by + back_hd * sa, 0.95))
    # §5.3: one box, 0.6 x 0.6 x 0.95 (chairs are static, not pushable).
    kit.collider((0, 0.0, 0.475), (0.60, 0.60, 0.95))
    kit.tag("office", "seat")
    kit.pile("Seat", mass=1, palette="office90s", states=["Upright", "Inverted", "Side", "Back"])
