"""Oak ladder-back (slat-back) dining chair, the hotel-liquidator chair the
film bought ~40 of and stacks into every pile (Still B). Mid-1980s/90s
production chair in golden oak. HERO pile piece: one mesh, copy-pasted
dozens of times, so the silhouette is the device and the budget is tight.

Construction:
* Front legs: turned (foot, swell, ring at stretcher height, neck, bead)
  under a square block that takes the seat rails.
* Rear legs: turned below the seat, square block at the seat rails, then
  turned posts raked back 7 degrees up to acorn finials at 0.965 m.
* Four graduated, plan-curved back slats morticed into the posts (the top
  slat taller with an arched top edge).
* Seat rails (aprons) with an arched front rail; box stretcher of turned
  rungs: decorative front rung, swelled (cigar) side and back rungs.
* Padded drop-in seat in teal fabric; the piping round its top is a bead
  between two creases in the pad's own profile (reads like the cord).
* Underside (seen whenever a pile turns the chair over): seat board inside
  the rails and four glued corner blocks.

Real-world reference size: 0.45 W x 0.50 D x 0.965 H, seat at 0.467 m
(§5.3: 0.45 x 0.50 x 0.98, seat 0.46). Front faces -Y. Must read from any
side, upside-down included.

Budget (§5.3 Kit_LadderBackChair 1,800 / 700): ~1.78k tris LOD0 (was 3.9k),
LOD1 0.40 (~710).
* Turned parts are 8-sided: at 41 mm stock an octagon departs from the
  circle by 1.6 mm (sub-pixel at 2 m) and SMOOTH_ANGLE 50 shades it round;
  profiles keep only the points that change the silhouette (foot, rings,
  neck, the acorn finial). Ends buried in blocks / legs are left open.
* Slats are a chamfered 8-point section swept along the plan bow, open at
  the mortices; seat rails and leg blocks are chamfered prisms (the 45-deg
  chamfer shades as a round-over at SMOOTH_ANGLE 50) instead of 2-segment
  bevelled boxes. The seat board and glue blocks under the seat are
  single-sided panels (only their undersides can be seen).
* Seat pad: 3-step corners, no mid-edge points (the warp only tapers it
  linearly), open underside, piping folded into the profile (was a
  separate 224-tri cord).
* Two slots only: Prop_WoodOak (the seat board is oak too, it was the only
  Plywood part) and Prop_FabricTeal.

Grain: kitlib's metre UVs are grain-aware for wood now; slats, rails and
rungs set fr_grain along their length (assets/_seating_grain.horizontal),
legs, posts and blocks keep vertical grain; neighbouring boards get a
fr_uv_offset so they don't share one sheet of figure.
"""

import math

import bmesh
from mathutils import Vector

import _seating_grain as grain

NAME = "Kit_LadderChair"
LOD1 = 0.40
SMOOTH_ANGLE = 50.0

OAK = "Prop_WoodOak"
FABRIC = "Prop_FabricTeal"

RAKE = 7.0                 # back post rake, degrees
SEAT_TOP_RAIL = 0.415      # top of the seat rails
BLOCK_LO, BLOCK_HI = 0.335, 0.425
TOP_Z = 0.965              # finial tops
TURN_SIDES = 8


# --------------------------------------------------------------------- helpers
def _rot_to(d):
    """Euler (degrees) turning +Z onto direction d."""
    e = Vector((0, 0, 1)).rotation_difference(Vector(d).normalized()).to_euler("XYZ")
    return tuple(math.degrees(a) for a in e)


def _turned(kit, name, profile, p0, p1, verts=TURN_SIDES, close_bottom=True, close_top=True):
    """Lathe ``profile`` [(radius, t)] with t in 0..1 of the p0->p1 length,
    standing on p0 and pointing at p1. Ends buried in other parts stay open."""
    p0, p1 = Vector(p0), Vector(p1)
    length = (p1 - p0).length
    prof = [(r, t * length) for r, t in profile]
    return kit.lathe(prof, tuple(p0), OAK, verts=verts, rot=_rot_to(p1 - p0), name=name,
                     close_bottom=close_bottom, close_top=close_top)


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


def _soft_block(kit, name, slot, hw, hd, r, profile, loc, warp=None, nc=2, nx=2, ny=2, cap_bottom=False):
    """Upholstery pad: rounded-rect rings lofted through ``profile`` [(inset,
    z)] bottom to top (a negative inset bulges out: piping), fan-capped on
    top; ``warp(x, y, z)`` reshapes it. The bottom sits on the seat board
    and is left open unless cap_bottom."""
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
    caps = [(rings[-1], profile[-1][1])] + ([(rings[0], profile[0][1])] if cap_bottom else [])
    for ring, z in caps:
        c = vert(0.0, 0.0, z)
        for i in range(n):
            bm.faces.new((ring[i], ring[(i + 1) % n], c))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = kit._new_object(name, bm, slot, "metres", "xz")
    kit._place(obj, loc, (0, 0, 0))
    return obj


def _slat(kit, name, path, up, half_t, bottoms, tops, chamfer=0.0028):
    """Back slat: a chamfered 8-point board section swept along a 3D polyline,
    open at both ends (they sit in the post mortices). At point k the
    section spans -bottoms[k]..tops[k] along ``up`` and +-half_t across it."""
    pts = [Vector(p) for p in path]
    upv = Vector(up).normalized()
    c = chamfer
    bm = bmesh.new()
    secs, frames = [], []
    for k, p in enumerate(pts):
        if k == 0:
            t = (pts[1] - pts[0]).normalized()
        elif k == len(pts) - 1:
            t = (pts[-1] - pts[-2]).normalized()
        else:
            t = (pts[k + 1] - pts[k - 1]).normalized()
        u = (upv - t * upv.dot(t)).normalized()
        n = t.cross(u).normalized()
        lo, hi = -bottoms[k], tops[k]
        sec2 = [(half_t, lo + c), (half_t, hi - c), (half_t - c, hi), (-half_t + c, hi),
                (-half_t, hi - c), (-half_t, lo + c), (-half_t + c, lo), (half_t - c, lo)]
        secs.append([bm.verts.new(p + n * a + u * b) for a, b in sec2])
        frames.append(p + u * (hi + lo) / 2)
    for k, (a, b) in enumerate(zip(secs, secs[1:])):
        mid = (frames[k] + frames[k + 1]) / 2
        for i in range(8):
            j = (i + 1) % 8
            f = bm.faces.new((a[i], a[j], b[j], b[i]))
            f.normal_update()
            if f.normal.dot(f.calc_center_median() - mid) < 0:
                f.normal_flip()
    obj = kit._new_object(name, bm, OAK, "metres", "xz")
    return grain.horizontal(obj, "x")


def _chamfered_rect(w, h, c, outer=(True, True, True, True)):
    """Outline (u, v) of a w x h rectangle centred on 0 with 45-deg chamfers
    on the corners flagged in ``outer`` (+u+v, -u+v, -u-v, +u-v)."""
    hw, hh = w / 2, h / 2
    pts = []
    for (su, sv), on in zip(((1, 1), (-1, 1), (-1, -1), (1, -1)), outer):
        if on:
            # CCW: arrive along the edge before the corner, leave along the next.
            if su * sv > 0:
                pts += [(su * hw, sv * (hh - c)), (su * (hw - c), sv * hh)]
            else:
                pts += [(su * (hw - c), sv * hh), (su * hw, sv * (hh - c))]
        else:
            pts.append((su * hw, sv * hh))
    return pts


def _panels(kit, name, polys):
    """Single-sided polygons [(points, outward normal)]: the seat board and
    the glue blocks under the seat, whose other faces are buried."""
    bm = bmesh.new()
    for pts, nrm in polys:
        f = bm.faces.new([bm.verts.new(p) for p in pts])
        f.normal_update()
        if f.normal.dot(Vector(nrm)) < 0:
            f.normal_flip()
    obj = kit._new_object(name, bm, OAK, "metres", "xz")
    return obj


# Lathe profiles as (radius, fraction of length). Legs and posts are turned
# from 42 mm square stock (the blocks are the unturned blank), so no radius
# exceeds 0.0205. Only silhouette points are kept.
LEG_LOWER = [(0.0150, 0.0), (0.0185, 0.36), (0.0205, 0.39), (0.0205, 0.425), (0.0178, 0.455),
             (0.0196, 0.865), (0.0205, 0.90), (0.0170, 0.94), (0.0205, 1.0)]
POST_UPPER = [(0.0205, 0.0), (0.0190, 0.05), (0.0178, 0.86), (0.0200, 0.89), (0.0150, 0.925),
              (0.0188, 0.955), (0.0166, 0.982), (0.0095, 0.996), (0.0000, 1.0)]
RUNG_PLAIN = [(0.0092, 0.0), (0.0122, 0.5), (0.0092, 1.0)]      # swelled (cigar) rung
RUNG_FRONT = [(0.0085, 0.0), (0.0128, 0.25), (0.0104, 0.31), (0.0158, 0.45), (0.0158, 0.55),
              (0.0104, 0.69), (0.0128, 0.75), (0.0085, 1.0)]


def build(kit):
    grain.install(kit)
    tr = math.tan(math.radians(RAKE))
    fx, fy = 0.204, -0.195          # front leg centres (+-x)
    rx, ry = 0.182, 0.200           # rear leg centres at the seat block
    ry_floor = 0.214                # rear feet splay back slightly

    def rear_axis(z):
        """Rear leg / post centre y at height z."""
        if z <= BLOCK_LO:
            return ry_floor + (ry - ry_floor) * z / BLOCK_LO
        if z <= BLOCK_HI:
            return ry
        return ry + (z - BLOCK_HI) * tr

    blank = _chamfered_rect(0.042, 0.042, 0.004)
    for s in (-1, 1):
        # Front leg: turned lower part (top buried in the block), square block.
        _turned(kit, "front leg", LEG_LOWER, (s * fx, fy, 0.0), (s * fx, fy, BLOCK_LO), close_top=False)
        kit.extrude(blank, SEAT_TOP_RAIL - BLOCK_LO, (s * fx, fy, (BLOCK_LO + SEAT_TOP_RAIL) / 2), OAK,
                    plane="xy", bevel=0.0, name="front leg block")
        # Rear leg: turned lower part, block, raked post with finial.
        # (foot lifted 0.65 mm: the 2.4 deg back splay tips the foot disc's rear edge to z = 0)
        _turned(kit, "rear leg", LEG_LOWER, (s * rx, ry_floor, 0.00065), (s * rx, ry, BLOCK_LO), close_top=False)
        kit.extrude(blank, BLOCK_HI - BLOCK_LO, (s * rx, ry, (BLOCK_LO + BLOCK_HI) / 2), OAK,
                    plane="xy", bevel=0.0, name="rear leg block")
        post_len = (TOP_Z - BLOCK_HI) / math.cos(math.radians(RAKE))
        top = (s * rx, ry + post_len * math.sin(math.radians(RAKE)), TOP_Z)
        _turned(kit, "back post", POST_UPPER, (s * rx, ry - 0.0012, BLOCK_HI - 0.008), top, close_bottom=False)

    # Seat rails. Front rail: arched lower edge, set 3 mm back from the legs.
    rail_t = 0.020
    z_top, z_bot = SEAT_TOP_RAIL, SEAT_TOP_RAIL - 0.070
    half = fx - 0.012
    arch = [(-half + 2 * half * i / 6, z_bot + 0.016 * math.sin(math.pi * i / 6)) for i in range(7)]
    outline = [(half, z_top), (-half, z_top)] + arch
    rail = kit.extrude(outline, rail_t, (0, fy - 0.021 + 0.003 + rail_t / 2, 0), OAK, plane="xz",
                       bevel=0.003, segments=1, name="front rail")
    grain.horizontal(rail, "x")["fr_uv_offset"] = (0.31, 0.12)
    # Side rails (front block to rear block) and back rail: prisms with the
    # outer top and bottom edges chamfered (the inner faces are under the pad).
    for s in (-1, 1):
        a = Vector((s * (fx - 0.008), fy))
        b = Vector((s * (rx - 0.008), ry))
        d = b - a
        mid = (a + b) / 2
        yaw = math.degrees(math.atan2(-d.x, d.y))
        side = _chamfered_rect(rail_t, 0.070, 0.003, outer=(s > 0, s < 0, s < 0, s > 0))
        r = kit.extrude(side, d.length, (mid.x, mid.y, (z_top + z_bot) / 2), OAK, plane="xz",
                        rot=(0, 0, yaw), bevel=0.0, name="side rail")
        grain.horizontal(r, "y")["fr_uv_offset"] = (0.17 * s, 0.41)
    back = _chamfered_rect(rail_t, 0.060, 0.003, outer=(True, False, False, True))
    r = kit.extrude(back, 2 * rx, (0, ry + 0.004, z_top - 0.030), OAK, plane="yz", bevel=0.0, name="back rail")
    grain.horizontal(r, "x")["fr_uv_offset"] = (0.07, 0.53)

    # Underside: seat board inside the rails (only its underside shows),
    # glued corner blocks.
    fy_in = fy - 0.021 + 0.003 + rail_t
    ry_in = ry + 0.004 - rail_t / 2
    fx_in, rx_in = fx - 0.018, rx - 0.018
    zb = z_top - 0.013
    board = [(fx_in, fy_in, zb), (rx_in, ry_in, zb), (-rx_in, ry_in, zb), (-fx_in, fy_in, zb)]
    grain.horizontal(_panels(kit, "seat board", [(board, (0, 0, -1))]), "x")["fr_uv_offset"] = (0.6, 0.2)
    blocks = []
    for (cx, cy), (ax, ay), (bx, by) in (((fx_in, fy_in), (-1, 0), (-0.05, 1)), ((-fx_in, fy_in), (1, 0), (0.05, 1)),
                                         ((rx_in, ry_in), (-1, 0), (0.05, -1)), ((-rx_in, ry_in), (1, 0), (-0.05, -1))):
        leg = 0.065
        p, q = (cx + ax * leg, cy + ay * leg), (cx + bx * leg, cy + by * leg)
        lo = zb - 0.040
        inward = (-cx, -cy, 0)
        blocks.append(([(p[0], p[1], lo), (q[0], q[1], lo), (q[0], q[1], zb), (p[0], p[1], zb)], inward))
        blocks.append(([(cx, cy, lo), (p[0], p[1], lo), (q[0], q[1], lo)], (0, 0, -1)))
    _panels(kit, "corner blocks", blocks)

    # Stretchers: plain sides low, decorative front and plain back higher
    # (ends buried in the legs).
    z_side, z_fb = 0.125, 0.170
    for s in (-1, 1):
        g = grain.horizontal(_turned(kit, "side rung", RUNG_PLAIN, (s * fx, fy, z_side),
                                     (s * rx, rear_axis(z_side), z_side), close_bottom=False, close_top=False), "y")
        g["fr_uv_offset"] = (0.23 * s, 0.0)
    grain.horizontal(_turned(kit, "front rung", RUNG_FRONT, (-fx, fy, z_fb), (fx, fy, z_fb),
                             close_bottom=False, close_top=False), "x")
    grain.horizontal(_turned(kit, "back rung", RUNG_PLAIN, (-rx, rear_axis(z_fb), z_fb),
                             (rx, rear_axis(z_fb), z_fb), close_bottom=False, close_top=False),
                     "x")["fr_uv_offset"] = (0.29, 0.61)

    # Back slats: graduated, curved in plan (centre 18 mm further back),
    # tilted with the posts; the top slat has an arched top edge.
    up = (0.0, math.sin(math.radians(RAKE)), math.cos(math.radians(RAKE)))
    slats = [(0.545, 0.050), (0.645, 0.054), (0.745, 0.058), (0.852, 0.068)]
    for i, (zc, h) in enumerate(slats):
        y0 = rear_axis(zc)
        top_slat = i == len(slats) - 1
        n = 6 if top_slat else 4
        path, tops, bots = [], [], []
        for k in range(n + 1):
            x = -rx + 2 * rx * k / n
            f = 1.0 - (x / rx) ** 2
            path.append((x, y0 + 0.018 * f, zc))
            bots.append(h / 2)
            tops.append(h / 2 + (0.014 * f if top_slat else 0.0))
        _slat(kit, "back slat", path, up, 0.0068, bots, tops)["fr_uv_offset"] = (0.11 * i, 0.37 * i)

    # Padded drop-in seat; the piping is the bulge ring in the profile.
    seat_hw, seat_hd, seat_cy = 0.222, 0.197, -0.014
    pad_h = 0.052

    def seat_warp(x, y, z):
        f = (y + seat_hd) / (2 * seat_hd)
        return (x * (1.0 - 0.125 * f), y + seat_cy, z)

    prof = [(0.008, 0.0), (0.0, 0.010), (0.0008, 0.0170), (-0.0034, 0.0215), (0.0020, 0.0258), (0.022, 0.039),
            (0.062, 0.047), (0.150, pad_h)]
    _soft_block(kit, "seat pad", FABRIC, seat_hw, seat_hd, 0.035, prof, (0, 0, z_top), warp=seat_warp,
                nc=3, nx=1, ny=1)

    # ------------------------------------------------------------ metadata
    seat_top = z_top + pad_h
    kit.support("seat", (0, seat_cy, seat_top), (0.36, 0.34))
    kit.anchor("sit", (0, seat_cy, seat_top))
    # §5.3: one box (pile pieces swap it for blockers anyway).
    y0, y1 = fy - 0.0215, ry + (TOP_Z - BLOCK_HI) * tr + 0.02
    kit.collider((0, (y0 + y1) / 2, TOP_Z / 2), (0.45, y1 - y0, TOP_Z))
    kit.tag("pile")
    kit.pile("Seat", mass=0, palette="hotel", states=["Upright", "Inverted", "Side", "Back"])
