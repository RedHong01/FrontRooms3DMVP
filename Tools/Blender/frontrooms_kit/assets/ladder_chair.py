"""Oak ladder-back (slat-back) dining chair, the hotel-liquidator chair the
film bought ~40 of and stacks into every pile (Still B). Mid-1980s/90s
production chair in golden oak.

Construction:
* Front legs: turned (foot, swell, ring at stretcher height, bead and
  neck) under a square block that takes the seat rails.
* Rear legs: turned below the seat, square block at the seat rails, then
  turned posts raked back 7 degrees up to acorn finials at 0.95 m.
* Four graduated, plan-curved back slats morticed into the posts (the top
  slat taller with an arched top edge).
* Seat rails (aprons) with an arched front rail; box stretcher of turned
  rungs: decorative front rung, plain side and back rungs.
* Padded drop-in seat in teal fabric with a welt (piping) round the top.

Real-world reference size: 0.45 W x 0.50 D x 0.95 H, seat at 0.465 m.
Front faces -Y. One identical mesh is instanced many times in piles, so it
must read from any side, upside-down included.

Turned parts use kit.lathe; the slats, the upholstered pad and the piping
are bmesh parts handed to the kit with kit._new_object / kit._place /
kit._bevel (same UV, slot and join path as every other primitive).

Grain: Prop_WoodOak's DoorVeneer grain runs along V, and kitlib's metre UVs
put V on world Z on every side face. The slats, seat rails and rungs are
therefore marked fr_uv = "metres_h" (assets/_seating_grain.py) so their grain
runs along their length; legs, posts and blocks keep vertical grain.

Budget: the mesh is instanced 4-6 times per pile and up to 20 times in a
corridor drift, so LOD0 is held to ~3.9k tris (turned parts 12 sides, rungs
8; SMOOTH_ANGLE 50 lets those shade round) and LOD1 = 0.38 gives the kit's
decimated ~1.5k LOD1 in the same FBX.
"""

import math

import bmesh
from mathutils import Vector

import _seating_grain as grain

NAME = "Kit_LadderChair"
LOD1 = 0.38
SMOOTH_ANGLE = 50.0

OAK = "Prop_WoodOak"
FABRIC = "Prop_FabricTeal"

RAKE = 7.0                 # back post rake, degrees
SEAT_TOP_RAIL = 0.415      # top of the seat rails
BLOCK_LO, BLOCK_HI = 0.335, 0.425


# --------------------------------------------------------------------- helpers
def _rot_to(d):
    """Euler (degrees) turning +Z onto direction d."""
    e = Vector((0, 0, 1)).rotation_difference(Vector(d).normalized()).to_euler("XYZ")
    return tuple(math.degrees(a) for a in e)


def _turned(kit, name, profile, p0, p1, verts=16):
    """Lathe ``profile`` [(radius, t)] with t in 0..1 of the p0->p1 length,
    standing on p0 and pointing at p1."""
    p0, p1 = Vector(p0), Vector(p1)
    length = (p1 - p0).length
    prof = [(r, t * length) for r, t in profile]
    return kit.lathe(prof, tuple(p0), OAK, verts=verts, rot=_rot_to(p1 - p0), name=name)


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


def _soft_block(kit, name, slot, hw, hd, r, profile, loc, warp=None, nc=5, nx=5, ny=5):
    """Upholstery pad: rounded-rect rings lofted through ``profile`` [(inset,
    z)] bottom to top, fan-capped; ``warp(x, y, z)`` reshapes it."""
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
    kit._place(obj, loc, (0, 0, 0))
    return obj


def _ring_tube(kit, name, slot, points, radius, normal, verts=6):
    """Seamless closed cord (piping) through a closed planar-ish loop."""
    pts = [Vector(p) for p in points]
    nref = Vector(normal).normalized()
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


def _sweep_rect(kit, name, slot, path, up, half_t, bottoms, tops, bevel=0.003, segments=1):
    """Rectangular section swept along a 3D polyline. At point k the section
    spans -bottoms[k]..tops[k] along ``up`` and +-half_t across it."""
    pts = [Vector(p) for p in path]
    upv = Vector(up).normalized()
    bm = bmesh.new()
    secs = []
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
        secs.append([bm.verts.new(p + n * half_t + u * lo), bm.verts.new(p - n * half_t + u * lo),
                     bm.verts.new(p - n * half_t + u * hi), bm.verts.new(p + n * half_t + u * hi)])
    for a, b in zip(secs, secs[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bm.faces.new(list(reversed(secs[0])))
    bm.faces.new(secs[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = kit._new_object(name, bm, slot, "metres", "xz")
    kit._bevel(obj, bevel, segments)
    return grain.horizontal(obj, "x")


# Lathe profiles as (radius, fraction of length). Legs and posts are turned
# from 42 mm square stock (the blocks are the unturned blank), so no radius
# exceeds 0.0205; the plain shaft is ~37 mm, the rings and beads full stock.
LEG_LOWER = [(0.0150, 0.0), (0.0168, 0.014), (0.0185, 0.36), (0.0205, 0.390), (0.0205, 0.425), (0.0182, 0.455),
             (0.0176, 0.62), (0.0196, 0.865), (0.0205, 0.900), (0.0172, 0.940), (0.0205, 1.0)]
POST_UPPER = [(0.0205, 0.0), (0.0193, 0.035), (0.0204, 0.06), (0.0188, 0.55), (0.0179, 0.86),
              (0.0196, 0.885), (0.0202, 0.90), (0.0151, 0.925), (0.0185, 0.950), (0.0190, 0.965), (0.0168, 0.982),
              (0.0101, 0.995), (0.0000, 1.0)]
RUNG_PLAIN = [(0.0085, 0.0), (0.0095, 0.08), (0.0118, 0.30), (0.0122, 0.50), (0.0118, 0.70), (0.0095, 0.92),
              (0.0085, 1.0)]
RUNG_FRONT = [(0.0085, 0.0), (0.0100, 0.08), (0.0115, 0.22), (0.0130, 0.27), (0.0108, 0.31), (0.0118, 0.36),
              (0.0158, 0.46), (0.0162, 0.50), (0.0158, 0.54), (0.0118, 0.64), (0.0108, 0.69), (0.0130, 0.73),
              (0.0115, 0.78), (0.0100, 0.92), (0.0085, 1.0)]


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

    for s in (-1, 1):
        # Front leg: turned lower part, square block.
        _turned(kit, "front leg", LEG_LOWER, (s * fx, fy, 0.0), (s * fx, fy, BLOCK_LO), verts=12)
        # Front block flush with the seat-rail tops (the pad sits on 0.415).
        kit.box((0.042, 0.042, SEAT_TOP_RAIL - BLOCK_LO), (s * fx, fy, (BLOCK_LO + SEAT_TOP_RAIL) / 2), OAK,
                bevel=0.004, segments=1, name="front leg block")
        # Rear leg: turned lower part, block, raked post with finial.
        # (foot lifted 0.65 mm: the 2.4 deg back splay tips the foot disc's rear edge to z = 0)
        _turned(kit, "rear leg", LEG_LOWER, (s * rx, ry_floor, 0.00065), (s * rx, ry, BLOCK_LO), verts=12)
        kit.box((0.042, 0.042, BLOCK_HI - BLOCK_LO), (s * rx, ry, (BLOCK_LO + BLOCK_HI) / 2), OAK,
                bevel=0.004, segments=1, name="rear leg block")
        post_len = (0.950 - BLOCK_HI) / math.cos(math.radians(RAKE))
        top = (s * rx, ry + post_len * math.sin(math.radians(RAKE)), 0.950)
        _turned(kit, "back post", POST_UPPER, (s * rx, ry - 0.0012, BLOCK_HI - 0.008), top, verts=12)

    # Seat rails. Front rail: arched lower edge, set 3 mm back from the legs.
    rail_t = 0.020
    z_top, z_bot = SEAT_TOP_RAIL, SEAT_TOP_RAIL - 0.070
    half = fx - 0.012
    arch = [(-half + 2 * half * i / 10, z_bot + 0.016 * math.sin(math.pi * i / 10)) for i in range(11)]
    outline = [(half, z_top), (-half, z_top)] + arch
    grain.horizontal(kit.extrude(outline, rail_t, (0, fy - 0.021 + 0.003 + rail_t / 2, 0), OAK, plane="xz",
                                 bevel=0.003, segments=1, name="front rail"))
    # Side rails (front block to rear block) and back rail.
    for s in (-1, 1):
        a = Vector((s * (fx - 0.008), fy))
        b = Vector((s * (rx - 0.008), ry))
        d = b - a
        mid = (a + b) / 2
        yaw = math.degrees(math.atan2(-d.x, d.y))
        grain.horizontal(kit.box((rail_t, d.length, 0.070), (mid.x, mid.y, (z_top + z_bot) / 2), OAK,
                                 bevel=0.003, segments=1, rot=(0, 0, yaw), name="side rail"), "y")
    grain.horizontal(kit.box((2 * rx, rail_t, 0.060), (0, ry + 0.004, z_top - 0.030), OAK,
                             bevel=0.003, segments=1, name="back rail"), "x")

    # Underside (seen whenever a pile turns the chair over): plywood seat
    # board inside the rails, glued corner blocks.
    fy_in = fy - 0.021 + 0.003 + rail_t
    ry_in = ry + 0.004 - rail_t / 2
    fx_in, rx_in = fx - 0.018, rx - 0.018
    board = [(fx_in, fy_in), (rx_in, ry_in), (-rx_in, ry_in), (-fx_in, fy_in)]
    kit.extrude(board, 0.012, (0, 0, z_top - 0.007), "Prop_Plywood", plane="xy",
                bevel=0.0015, segments=1, name="seat board")
    for (cx, cy), (ax, ay), (bx, by) in (((fx_in, fy_in), (-1, 0), (-0.05, 1)), ((-fx_in, fy_in), (1, 0), (0.05, 1)),
                                         ((rx_in, ry_in), (-1, 0), (0.05, -1)), ((-rx_in, ry_in), (1, 0), (-0.05, -1))):
        leg = 0.065
        tri = [(cx, cy), (cx + ax * leg, cy + ay * leg), (cx + bx * leg, cy + by * leg)]
        kit.extrude(tri, 0.040, (0, 0, z_top - 0.013 - 0.020), OAK, plane="xy", bevel=0.002, segments=1,
                    name="corner block")

    # Stretchers: plain sides low, decorative front and plain back higher.
    z_side, z_fb = 0.125, 0.170
    for s in (-1, 1):
        grain.horizontal(_turned(kit, "side rung", RUNG_PLAIN, (s * fx, fy, z_side),
                                 (s * rx, rear_axis(z_side), z_side), verts=8), "y")
    grain.horizontal(_turned(kit, "front rung", RUNG_FRONT, (-fx, fy, z_fb), (fx, fy, z_fb), verts=8), "x")
    grain.horizontal(_turned(kit, "back rung", RUNG_PLAIN, (-rx, rear_axis(z_fb), z_fb),
                             (rx, rear_axis(z_fb), z_fb), verts=8), "x")

    # Back slats: graduated, curved in plan (centre 18 mm further back),
    # tilted with the posts; the top slat has an arched top edge.
    up = (0.0, math.sin(math.radians(RAKE)), math.cos(math.radians(RAKE)))
    slats = [(0.545, 0.050), (0.645, 0.054), (0.745, 0.058), (0.852, 0.068)]
    n = 6
    for i, (zc, h) in enumerate(slats):
        y0 = rear_axis(zc)
        path, tops, bots = [], [], []
        for k in range(n + 1):
            x = -rx + 2 * rx * k / n
            f = 1.0 - (x / rx) ** 2
            path.append((x, y0 + 0.018 * f, zc))
            bots.append(h / 2)
            tops.append(h / 2 + (0.014 * f if i == len(slats) - 1 else 0.0))
        _sweep_rect(kit, "back slat", OAK, path, up, 0.0068, bots, tops, bevel=0.003, segments=1)

    # Padded drop-in seat with piping.
    seat_hw, seat_hd, seat_cy = 0.222, 0.197, -0.014
    pad_h = 0.052

    def seat_warp(x, y, z):
        f = (y + seat_hd) / (2 * seat_hd)
        return (x * (1.0 - 0.125 * f), y + seat_cy, z)

    # Short boxing band, piping, then a domed top that sags a little at the
    # front edge where people sit.
    prof = [(0.008, 0.0), (0.0, 0.008), (0.0, 0.021), (0.006, 0.029), (0.022, 0.039), (0.060, 0.047),
            (0.150, pad_h)]
    _soft_block(kit, "seat pad", FABRIC, seat_hw, seat_hd, 0.035, prof, (0, 0, z_top), warp=seat_warp,
                nc=3, nx=4, ny=4)
    piping = [seat_warp(x, y, 0.0225) for x, y in _rrect(seat_hw + 0.0008, seat_hd + 0.0008, 0.0358, 3, 4, 4)]
    piping = [(p[0], p[1], p[2] + z_top) for p in piping]
    _ring_tube(kit, "piping", FABRIC, piping, 0.0042, (0, 0, 1), verts=4)

    # ------------------------------------------------------------ metadata
    seat_top = z_top + pad_h
    kit.support("seat", (0, seat_cy, seat_top), (0.36, 0.34))
    kit.anchor("sit", (0, seat_cy, seat_top))
    kit.collider((0, 0.0, seat_top / 2), (0.45, 0.46, seat_top))
    kit.collider((0, 0.242, (seat_top + 0.95) / 2), (0.41, 0.085, 0.95 - seat_top))
    kit.tag("pile")
    kit.pile("Seat", mass=0, palette="hotel", states=["Upright", "Inverted", "Side", "Back"])
