"""Beige 101-key office keyboard, c. 1990-97 (the generic AT / PS/2 board
that came with every office PC: two-part moulded case, sloped key well,
numeric pad, lock LEDs, straight cable out of the back).

Real-world reference size: 0.46 m wide, 0.17 m deep, 25 mm tall at the back
and 15 mm at the front (case; keycaps stand ~6 mm proud of the surround).
Keycaps are real geometry: every key is a tapered cap with authored UVs into
Prop_KeyboardKeys (2048 x 768 layout, 23 x 6.7 key units; uv="keep", see
_uv_keys): each cap reads its legend cell at true proportions, and the
numeric pad, which the texture draws as a calculator block, is remapped onto
the real 101-key pad (Num / * -, 7 8 9 +, 4 5 6, 1 2 3 Enter, 0 .). The nav
cluster and arrows have no legends in the texture; they sample its darker
ground, the grey keys of the period two-tone boards. A dark liner on the
key-well walls gives the darker key-field surround.
Front (space bar, user side) faces -Y; the cable leaves the back (+Y) and
ends in its PS/2 plug on the desk.
"""

import math

import bmesh
import bpy

NAME = "Kit_Keyboard"

BEIGE = "Prop_PlasticBeige"
DARK = "Prop_PlasticGrey"
BLACK = "Prop_PlasticBlack"
RUBBER = "Prop_Rubber"
KEYS = "Prop_KeyboardKeys"
LENS = "Prop_GlassCRT"

W, D = 0.46, 0.17
Z_FRONT, Z_BACK = 0.015, 0.025          # top of the case at the front / back edge
TILT = math.atan2(Z_BACK - Z_FRONT, D)  # slope of the key deck
SURROUND_T = 0.0095                     # upper shell thickness (its skirt hides the plate edges)
WELL_DEPTH = 0.0075                     # key plate top below the surround
FOOT = 0.0025                           # rubber pads lift the case off the desk

# Texture layout (gen_props.keyboard_keys): 2048 x 768 px, 23 units across.
TEX_W, TEX_H = 2048.0, 768.0
UNIT = TEX_W / 23.0
UNIT_Y = (TEX_H - 60) / 6.2
PITCH = 0.0185                                  # key pitch in metres
SX = PITCH / UNIT                               # metres per texture pixel
SY = PITCH / UNIT_Y
PLATE_W, PLATE_D = TEX_W * SX, TEX_H * SY       # 0.4255 x 0.1244 m


def _row_top(r):
    """Texture y (px, from the top/back edge) of key row r (0 = F keys)."""
    return 30.0 if r == 0 else 30.0 + UNIT_Y + 18.0 + (r - 1) * UNIT_Y


def _main_cell(units_before, r):
    """Top-left (px) of the drawn cap rect of a main-block key in the texture:
    ``units_before`` key units from the block's left edge in row r."""
    return (40.0 + units_before * UNIT + 4.0, _row_top(r) + 4.0)


def _pad_cell(c, tr):
    """Top-left (px) of a numeric-pad cell as the texture draws it: columns
    0-2 at u = 19..21, texture rows 1-4 holding 7 8 9 / 4 5 6 / 1 2 3 / 0 . +"""
    return ((19 + c) * UNIT + 4.0, _row_top(tr) + 4.0)


CAP_PX = UNIT - 8.0                     # drawn width of a 1-unit cap (px)
CELL_H = UNIT_Y - 8.0                   # drawn height of a 1-unit cap (px)
SPACE = _main_cell(3.5, 5)              # space bar: plain cap fill, no legend


def _key_rects():
    """Every cap as (x0, x1, y0, y1, row, src) in texture px on the model's
    101-key grid. src None = the cap's own texture cell (main block);
    otherwise (ox, oy, w, h, split): the texture cell (top-left, size) whose
    legend the cap should show, and how a 2-unit cap is split so the legend
    keeps its proportions (see _uv_keys)."""
    rows = [
        ["Esc", None, "F1", "F2", "F3", "F4", None, "F5", "F6", "F7", "F8", None, "F9", "F10", "F11", "F12"],
        ["`", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "=", ("Bksp", 2)],
        [("Tab", 1.5), "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]", ("\\", 1.5)],
        [("Caps", 1.75), "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", ("Enter", 2.25)],
        [("Shift", 2.25), "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", ("Shift", 2.75)],
        [("Ctrl", 1.5), None, ("Alt", 1.5), ("", 7), ("Alt", 1.5), None, ("Ctrl", 1.5)],
    ]
    rects = []
    for r, row in enumerate(rows):
        x = 40.0
        y = _row_top(r)
        for key in row:
            if key is None:
                x += UNIT * 0.5
                continue
            w = 1 if isinstance(key, str) else key[1]
            rects.append((x + 4, x + UNIT * w - 4, y + 4, y + UNIT_Y - 4, r, None))
            x += UNIT * w

    def cap(u0, u1, r0, r1, src):
        rects.append((u0 * UNIT + 4, u1 * UNIT - 4, _row_top(r0) + 4, _row_top(r1) + UNIT_Y - 4, r1, src))

    def one(origin):
        return (origin[0], origin[1], CAP_PX, CELL_H, None)

    # Numeric pad on the real 101-key grid (u = 19..23, rows 1-5). The
    # texture only draws a calculator block (7 8 9 / 4 5 6 / 1 2 3 / 0 . +),
    # so each cap points its UVs at the right legend: digits one texture row
    # up, '/' and '-' borrowed from the main block, the tall '+' and Enter
    # and the wide '0' split so their legends are not stretched. Num Lock and
    # '*' have no legend in the texture and show plain cap fill.
    space_right = (SPACE[0] + 7 * UNIT - 8 - CAP_PX, SPACE[1])
    cap(19, 20, 1, 1, one(SPACE))                                   # Num Lock (blank)
    cap(20, 21, 1, 1, one(_main_cell(2.25 + 9, 4)))                 # /
    cap(21, 22, 1, 1, one(space_right))                             # * (blank)
    cap(22, 23, 1, 1, one(_main_cell(11, 1)))                       # -
    for r in range(3):                                              # 7 8 9 / 4 5 6 / 1 2 3
        for c in range(3):
            cap(19 + c, 20 + c, 2 + r, 2 + r, one(_pad_cell(c, 1 + r)))
    ox, oy = _pad_cell(2, 4)
    cap(22, 23, 2, 3, (ox, oy, CAP_PX, CELL_H, "v"))                # + (tall)
    ox, oy = _main_cell(12.75, 3)
    cap(22, 23, 4, 5, (ox, oy, CAP_PX, CELL_H, "v", 1.22))          # Enter (tall; legend condensed to fit 1 unit)
    ox, oy = _pad_cell(0, 4)
    cap(19, 21, 5, 5, (ox, oy, CAP_PX, CELL_H, "u"))                # 0 (wide)
    cap(21, 22, 5, 5, one(_pad_cell(1, 4)))                         # .

    # Navigation cluster and arrows: no legends in the texture; they sample
    # the darker texture ground, the grey keys of the period two-tone boards.
    nav = 15.72
    k = 0
    def ground():
        return one(((16.2 + (k % 6) * 0.9) * UNIT, _row_top(0) + 4.0))
    for c in range(3):
        for r in (0, 1, 2, 5):                    # Print/Scroll/Pause, Ins/Home/PgUp, Del/End/PgDn, arrows
            cap(nav + c, nav + c + 1, r, r, ground())
            k += 1
    cap(nav + 1, nav + 2, 4, 4, ground())         # arrow up
    return rects


def _deck(u, v, w):
    """Point on the sloped deck frame -> asset space. u across, v up the
    slope (toward the back), w normal to the deck; origin on the top surface
    above the asset centre."""
    z0 = (Z_FRONT + Z_BACK) / 2
    return (u, v * math.cos(TILT) - w * math.sin(TILT), z0 + v * math.sin(TILT) + w * math.cos(TILT))


def _join(kit, objs):
    """Join parts into the first one (so one planar decal spans them all)."""
    keep, others = objs[0], objs[1:]
    kit.parts = [p for p in kit.parts if not any(p is o for o in others)]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = keep
    bpy.ops.object.join()
    return keep


def _smooth(points, sub):
    """Catmull-Rom resample of a polyline (cables without kinks)."""
    pts = [tuple(p) for p in points]
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        for k in range(sub):
            t = k / sub
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(3)))
    out.append(pts[-1])
    return out


def _islands(bm):
    """Connected face groups of a bmesh (one per keycap, one for the plate)."""
    seen, out = set(), []
    for f in bm.faces:
        if f in seen:
            continue
        seen.add(f)
        stack, isl = [f], []
        while stack:
            g = stack.pop()
            isl.append(g)
            for e in g.edges:
                for h in e.link_faces:
                    if h not in seen:
                        seen.add(h)
                        stack.append(h)
        out.append(isl)
    return out


def _uv_keys(obj, rects):
    """Author the key field's UVs (the part is uv="keep").

    Plate: planar over the whole texture, as the old decal did. Caps: each
    maps from its own top-left corner at the texture's X scale on both axes,
    so the legends keep their drawn proportions (the texture rows are 1.28x
    taller than the square caps; a plain planar decal squashed them). Caps
    whose legend lives elsewhere in the texture (the numeric pad) read from
    that cell. A 2-unit cap is first cut in two: the band carrying the legend
    maps at true scale, the other band takes the rest of the cell stretched,
    which is only plain cap fill and outline."""
    split_px = {"u": 45.0, "v": 50.0}
    want = []
    for x0, x1, y0, y1, row, src in rects:
        cx = (x0 + x1) / 2 * SX - PLATE_W / 2
        cy = PLATE_D / 2 - (y0 + y1) / 2 * SY
        if src is None:
            src = (x0, y0, x1 - x0, y1 - y0, None)
        want.append((cx, cy, (x1 - x0) * SX, (y1 - y0) * SY, src))

    def match(isl):
        xs = [v.co.x for f in isl for v in f.verts]
        ys = [v.co.y for f in isl for v in f.verts]
        bx0, bx1, by0, by1 = min(xs), max(xs), min(ys), max(ys)
        if bx1 - bx0 > PLATE_W * 0.9:
            return None, (bx0, bx1, by0, by1)
        mx, my = (bx0 + bx1) / 2, (by0 + by1) / 2
        best = min(range(len(want)), key=lambda i: (want[i][0] - mx) ** 2 + (want[i][1] - my) ** 2)
        return best, (bx0, bx1, by0, by1)

    bm = bmesh.new()
    bm.from_mesh(obj.data)
    # Cut the split caps.
    for isl in _islands(bm):
        i, (bx0, bx1, by0, by1) = match(isl)
        if i is None or want[i][4][4] is None:
            continue
        axis = want[i][4][4]
        geom = list({v for f in isl for v in f.verts}) + list({e for f in isl for e in f.edges}) + isl
        if axis == "u":
            co, no = (bx0 + split_px["u"] * SX, 0, 0), (1, 0, 0)
        else:
            co, no = (0, by1 - split_px["v"] * SX, 0), (0, 1, 0)
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=co, plane_no=no)
    layer = bm.loops.layers.uv.verify()
    for isl in _islands(bm):
        i, (bx0, bx1, by0, by1) = match(isl)
        if i is None:
            for f in isl:
                for loop in f.loops:
                    c = loop.vert.co
                    loop[layer].uv = ((c.x + PLATE_W / 2) / PLATE_W, (c.y + PLATE_D / 2) / PLATE_D)
            continue
        cw, ch = bx1 - bx0, by1 - by0
        ox, oy, sw, sh, split = want[i][4][:5]
        xs = want[i][4][5] if len(want[i][4]) > 5 else 1.0      # >1 condenses a legend that is wider than the cap
        sh = min(sh, CELL_H * SY / SX)          # caps show the top of their cell at true scale
        for f in isl:
            fc = f.calc_center_median()
            far_u = split == "u" and fc.x - bx0 > split_px["u"] * SX
            far_v = split == "v" and by1 - fc.y > split_px["v"] * SX
            for loop in f.loops:
                dx = loop.vert.co.x - bx0
                dy = by1 - loop.vert.co.y
                if far_u:
                    lm = split_px["u"] * SX
                    up = ox + split_px["u"] + (dx - lm) * (sw - split_px["u"]) / max(cw - lm, 1e-6)
                else:
                    up = ox + dx / SX * xs
                if far_v:
                    lm = split_px["v"] * SX
                    vp = oy + split_px["v"] + (dy - lm) * (sh - split_px["v"]) / max(ch - lm, 1e-6)
                else:
                    vp = oy + dy / SX
                loop[layer].uv = (up / TEX_W, 1.0 - vp / TEX_H)
    bm.to_mesh(obj.data)
    bm.free()
    obj["fr_uv"] = "keep"


def _pt_tube(kit, points, radius, slot, verts=8, name="tube", caps=True):
    """Round tube along a polyline with parallel-transport frames (no ring
    flips where the path turns vertical, unlike kit.tube)."""
    from mathutils import Vector
    pts = [Vector(p) for p in points]
    n = len(pts)
    tangents = []
    for k in range(n):
        if k == 0:
            t = pts[1] - pts[0]
        elif k == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[k] - pts[k - 1]).normalized() + (pts[k + 1] - pts[k]).normalized()
        tangents.append(t.normalized())
    up = Vector((0, 0, 1))
    nrm = up - tangents[0] * up.dot(tangents[0])
    if nrm.length < 1e-4:
        nrm = Vector((1, 0, 0)) - tangents[0] * tangents[0].x
    nrm.normalize()
    bm = bmesh.new()
    rings = []
    for p, t in zip(pts, tangents):
        nrm = (nrm - t * nrm.dot(t)).normalized()
        b = t.cross(nrm)
        rings.append([bm.verts.new(p + (nrm * math.cos(2 * math.pi * i / verts) + b * math.sin(2 * math.pi * i / verts)) * radius)
                      for i in range(verts)])
    for a, c in zip(rings, rings[1:]):
        for i in range(verts):
            j = (i + 1) % verts
            bm.faces.new((a[i], a[j], c[j], c[i]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _ps2_plug(kit, end, prev):
    """PS/2 mini-DIN plug lying on the desk at the cable end, pointing along
    the cable's last (horizontal) tangent: tapered strain relief, round
    moulded body, metal shell with the dark pin face."""
    dx, dy = end[0] - prev[0], end[1] - prev[1]
    l = math.hypot(dx, dy) or 1.0
    dx, dy = dx / l, dy / l
    rz = math.degrees(math.atan2(dy, dx)) - 90.0      # cylinder Z -> rot X 90 points it along +Y, then yaw
    zc = 0.0065

    def at(d):
        return (end[0] + dx * d, end[1] + dy * d, zc)
    kit.cylinder(0.0028, 0.008, at(0.004), BLACK, verts=12, rot=(-90, 0, rz), bevel=0.0, radius_top=0.0050,
                 name="plug strain relief")
    kit.cylinder(0.0065, 0.016, at(0.016), BLACK, verts=12, rot=(-90, 0, rz), bevel=0.001, segments=1, name="plug body")
    kit.cylinder(0.0048, 0.004, at(0.026), "Prop_Aluminium", verts=12, rot=(-90, 0, rz), bevel=0.0, name="plug shell")
    kit.cylinder(0.0040, 0.0006, at(0.0281), BLACK, verts=12, rot=(-90, 0, rz), bevel=0.0, name="plug pin face")


def build(kit):
    tilt_deg = math.degrees(TILT)
    deck_len = D / math.cos(TILT)

    # ------------------------------------------------------------ key field
    # Key extents (texture px) -> where the well opening goes.
    rects = _key_rects()
    kx0 = min(r[0] for r in rects) * SX - PLATE_W / 2
    kx1 = max(r[1] for r in rects) * SX - PLATE_W / 2
    ky1 = PLATE_D / 2 - min(r[2] for r in rects) * SY     # back edge of the keys (plate coords)
    ky0 = PLATE_D / 2 - max(r[3] for r in rects) * SY     # front edge
    front_border = 0.0145
    # Plate centre in deck coordinates so the keys are centred across and
    # sit front_border behind the front edge.
    pu = -(kx0 + kx1) / 2
    pv = -deck_len / 2 + front_border - ky0
    clear = 0.0026
    well_w = (kx1 - kx0) + 2 * clear
    well_d = (ky1 - ky0) + 2 * clear
    well_cu = pu + (kx0 + kx1) / 2
    well_cv = pv + (ky0 + ky1) / 2

    plate_w = -WELL_DEPTH                                   # deck-normal height of the plate top
    plate = kit.box((PLATE_W, PLATE_D, 0.0015), (0, 0, -0.00075), KEYS, bevel=0.0, name="key plate",
                    uv="keep")
    caps = [plate]
    heights = {0: 0.0118, 1: 0.0128, 2: 0.0124, 3: 0.0121, 4: 0.0121, 5: 0.0124}
    for x0, x1, y0, y1, row, _src in rects:
        bw, bd = (x1 - x0) * SX, (y1 - y0) * SY
        cx = (x0 + x1) / 2 * SX - PLATE_W / 2
        cy = PLATE_D / 2 - (y0 + y1) / 2 * SY
        h = heights[row]
        side, back, front = 0.0018, 0.0010, 0.0029
        caps.append(kit.loft_box((bw, bd), (bw - 2 * side, bd - back - front), h, (cx, cy, h / 2), KEYS,
                                 back_offset=(0, -(front - back) / 2), bevel=0.0, rot=(90, 0, 0), name="keycap"))
    keyfield = _join(kit, caps)
    keyfield.name = "key field"
    # Undersides of the caps and plate are never seen: drop them.
    bm = bmesh.new()
    bm.from_mesh(keyfield.data)
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.z < -0.99], context="FACES")
    bm.to_mesh(keyfield.data)
    bm.free()
    _uv_keys(keyfield, rects)
    keyfield.location = _deck(pu, pv, plate_w)
    keyfield.rotation_euler = (TILT, 0, 0)

    # Dark liner on the walls of the key well: the darker key-field surround
    # of the period boards (a ledge + wall between the beige lip and the keys).
    liner_top, liner_bot = -0.0040, plate_w
    kit.frame((well_w + 0.0004, well_d + 0.0004), (well_w - 0.0036, well_d - 0.0036), liner_top - liner_bot,
              _deck(well_cu, well_cv, (liner_top + liner_bot) / 2), DARK, bevel=0.0,
              rot=(90 + tilt_deg, 0, 0), name="well liner")

    # ------------------------------------------------------------ case
    # Upper shell: one sloped frame around the key well (rounded outer edge).
    kit.frame((W, deck_len), (well_w, well_d), SURROUND_T, _deck(0, 0, -SURROUND_T / 2), BEIGE,
              inner_offset=(well_cu, -well_cv), bevel=0.0042, segments=3, rot=(90 + tilt_deg, 0, 0), name="upper shell")
    # Lower tray: wedge side profile extruded across, its top under the shell
    # so the two shells meet in a moulded parting line.
    zb_front = Z_FRONT - SURROUND_T / math.cos(TILT)
    zb_back = Z_BACK - SURROUND_T / math.cos(TILT)
    prof = [(-D / 2, FOOT), (D / 2, FOOT), (D / 2, zb_back), (-D / 2, zb_front)]
    kit.extrude(prof, W - 0.0016, (0, 0, 0), BEIGE, plane="yz", bevel=0.0028, segments=2, name="lower tray")

    # Rubber pads, folded tilt legs.
    for sx in (-1, 1):
        for y in (-0.068, 0.068):
            kit.cylinder(0.0065, FOOT + 0.0004, (sx * 0.196, y, (FOOT + 0.0004) / 2), RUBBER, verts=8, bevel=0.0, name="rubber pad")
        kit.box((0.040, 0.014, 0.0022), (sx * 0.160, 0.072, FOOT + 0.0003), DARK, bevel=0.0007, segments=1, name="tilt leg")

    # Lock LEDs in a dark window on the back border above the numpad.
    led_u = pu + (TEX_W - 2.0 * UNIT) * SX - PLATE_W / 2
    led_v = well_cv + well_d / 2 + 0.0105
    kit.box((0.062, 0.0105, 0.0012), _deck(led_u, led_v, 0.0003), DARK, bevel=0.0004, segments=1,
            rot=(tilt_deg, 0, 0), name="LED window")
    for k in range(3):
        kit.cylinder(0.0017, 0.0012, _deck(led_u - 0.019 + k * 0.019, led_v + 0.0012, 0.0009), LENS, verts=8,
                     rot=(tilt_deg, 0, 0), bevel=0.0, name="lock LED")
        kit.box((0.010, 0.0016, 0.0004), _deck(led_u - 0.019 + k * 0.019, led_v - 0.0028, 0.0009), BEIGE,
                bevel=0.0, rot=(tilt_deg, 0, 0), name="LED legend")
    # Maker's badge on the back border over the F keys.
    bu = -W / 2 + 0.050
    kit.box((0.046, 0.0085, 0.0010), _deck(bu, led_v, 0.0002), DARK, bevel=0.0003, segments=1,
            rot=(tilt_deg, 0, 0), name="badge")
    kit.box((0.034, 0.0030, 0.0004), _deck(bu, led_v, 0.0008), BEIGE, bevel=0.0, rot=(tilt_deg, 0, 0), name="badge script")

    # Cable: strain-relief grommet in the back edge, then the cord lies back
    # toward the PC and ends in its (unplugged) PS/2 mini-DIN plug.
    gx, gz = -0.060, (FOOT + zb_back) / 2 + 0.001
    kit.cylinder(0.0050, 0.010, (gx, D / 2 + 0.003, gz), BLACK, verts=12, rot=(90, 0, 0), bevel=0.0012,
                 segments=1, radius_top=0.0062, name="cable grommet")
    r = 0.0021
    ctrl = [(gx, D / 2 + 0.007, gz), (gx - 0.002, D / 2 + 0.016, gz - 0.002), (gx - 0.004, D / 2 + 0.027, 0.0026),
            (gx - 0.009, D / 2 + 0.044, r), (gx - 0.007, D / 2 + 0.058, r + 0.0005), (gx - 0.001, D / 2 + 0.067, 0.0050),
            (gx + 0.007, D / 2 + 0.073, 0.0065)]
    cable = [(x, y, max(z, r)) for x, y, z in _smooth(ctrl, 3)]
    _pt_tube(kit, cable, r, BLACK, verts=8, name="cable")
    _ps2_plug(kit, ctrl[-1], ctrl[-2])

    kit.anchor("keys_centre", _deck(well_cu, well_cv, 0.006))
    kit.collider((0, 0, Z_BACK / 2 + 0.003), (W, D, Z_BACK + 0.006))
    kit.tag("office", "desk_top", "pile_piece")
    kit.pile("Small", mass=0, palette="office90s")
