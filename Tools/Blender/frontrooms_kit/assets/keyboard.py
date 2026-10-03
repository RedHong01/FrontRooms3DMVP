"""Beige 101-key office keyboard, c. 1990-97 (the generic AT / PS/2 board
that came with every office PC: two-part moulded case, sloped key well,
numeric pad, straight cable out of the back).

Real-world reference size: 0.46 m wide, 0.17 m deep, 25 mm tall at the back
and 15 mm at the front (case; keycaps stand ~6 mm proud of the surround).
Keycaps are real geometry: every key is a tapered cap with authored UVs into
Prop_KeyboardKeys (2048 x 768 layout, 23 x 6.7 key units; uv="keep", see
_uv_keys): each cap reads its legend cell at true proportions, and the
numeric pad, which the texture draws as a calculator block, is remapped onto
the real 101-key pad (Num / * -, 7 8 9 +, 4 5 6, 1 2 3 Enter, 0 .). The nav
cluster and arrows have no legends in the texture; they sample its darker
ground, the grey keys of the period two-tone boards. Grey walls in the key
well give the darker key-field surround.
Front (space bar, user side) faces -Y; the cable leaves the back (+Y) and
ends in its PS/2 plug on the desk.

Budget (synthesis §5.3): 1,200 LOD0 tris, LOD1 0.42, no collider (desk-top
clutter), pile Small 0, <= 4 slots (KeyboardKeys, PlasticBeige, PlasticGrey,
PlasticBlack). Where the triangles went:
* caps keep top, front and sides; a cap's back is dropped where the cap
  behind it covers it (only a sliver could show, and only from behind), so
  the back row keeps its walls (_cull_hidden). Dropping the inner side walls
  too (CULL_SIDES) saved 330 tris but read as hollow caps at 0.5-1 m;
* the case is one ring-built shell (rounded top edge, moulded parting step,
  rounded plan corners, flat bottom) instead of a bevelled frame + tray;
* lock LEDs, rubber pads, tilt legs and badge lettering (< 5 mm at 2 m) are
  gone; the LED window and badge are flat grey plates.
"""

import math

import bmesh
import bpy

import _deskgear as dg

NAME = "Kit_Keyboard"
LOD1 = 0.42
SMOOTH_ANGLE = 48          # 3-segment plan corners and the 2-segment top roll shade smooth

BEIGE = "Prop_PlasticBeige"
DARK = "Prop_PlasticGrey"
BLACK = "Prop_PlasticBlack"
KEYS = "Prop_KeyboardKeys"

W, D = 0.46, 0.17
Z_FRONT, Z_BACK = 0.015, 0.025          # top of the case at the front / back edge
TILT = math.atan2(Z_BACK - Z_FRONT, D)  # slope of the key deck
SURROUND_T = 0.0095                     # upper shell thickness (parting line this far under the deck)
WELL_DEPTH = 0.0075                     # key plate top below the surround
CULL_SIDES = False                      # also drop cap side walls facing a close neighbour

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


def _covered(rects):
    """Per cap: (left, right, back) True where a neighbouring cap stands within
    0.2 key units and covers >= 80 % of that wall (texture px; y grows to the
    front, so 'back' is the smaller y)."""
    gap_u, gap_v = 0.2 * UNIT, 0.3 * UNIT_Y
    out = []
    for a in rects:
        ax0, ax1, ay0, ay1 = a[:4]
        h, w = ay1 - ay0, ax1 - ax0
        left = right = back = 0.0
        for b in rects:
            if b is a:
                continue
            bx0, bx1, by0, by1 = b[:4]
            oy = max(0.0, min(ay1, by1) - max(ay0, by0))
            ox = max(0.0, min(ax1, bx1) - max(ax0, bx0))
            if 0 <= ax0 - bx1 <= gap_u:
                left += oy
            if 0 <= bx0 - ax1 <= gap_u:
                right += oy
            if 0 <= ay0 - by1 <= gap_v:
                back += ox
        out.append((left >= 0.8 * h, right >= 0.8 * h, back >= 0.8 * w))
    return out


def _cull_hidden(obj, rects):
    """Drop cap walls that face a close neighbour (after the UVs are authored,
    so the remaining faces keep their legend mapping). Plate-local normals:
    sides +-X, back +Y (the caps are not yet tilted onto the deck)."""
    cover = _covered(rects)
    centres = [((x0 + x1) / 2 * SX - PLATE_W / 2, PLATE_D / 2 - (y0 + y1) / 2 * SY) for x0, x1, y0, y1, _r, _s in rects]
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    kill = []
    for isl in _islands(bm):
        xs = [v.co.x for f in isl for v in f.verts]
        ys = [v.co.y for f in isl for v in f.verts]
        if max(xs) - min(xs) > PLATE_W * 0.9:
            continue
        mx, my = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
        i = min(range(len(centres)), key=lambda k: (centres[k][0] - mx) ** 2 + (centres[k][1] - my) ** 2)
        left, right, back = cover[i]
        for f in isl:
            n = f.normal
            if (CULL_SIDES and ((left and n.x < -0.7) or (right and n.x > 0.7))) or (back and n.y > 0.7):
                kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    bm.to_mesh(obj.data)
    bm.free()


def _ps2_plug(kit, end, prev):
    """PS/2 mini-DIN plug lying on the desk at the cable end, pointing along
    the cable's last (horizontal) tangent: round moulded body and the metal
    shell with its pin face (8 / 6 sides; 44 tris)."""
    dx, dy = end[0] - prev[0], end[1] - prev[1]
    l = math.hypot(dx, dy) or 1.0
    dx, dy = dx / l, dy / l
    rz = math.degrees(math.atan2(dy, dx)) - 90.0      # cylinder Z -> rot X -90 points it along +Y, then yaw
    zc = 0.0065

    def at(d):
        return (end[0] + dx * d, end[1] + dy * d, zc)
    kit.cylinder(0.0065, 0.020, at(0.010), BLACK, verts=8, rot=(-90, 0, rz), bevel=0.0, name="plug body")
    shell = kit.cylinder(0.0048, 0.005, at(0.0225), DARK, verts=6, rot=(-90, 0, rz), bevel=0.0, name="plug shell")
    dg.prune(shell, lambda n: n.z < -0.9)             # its back is inside the body


def _case_rings(well_w, well_d, well_cu, well_cv, deck_len):
    """Vertex rings of the one-piece case shell (asset space, 12 verts each,
    counter-clockwise from the front-right corner): flat bottom, lower tray
    wall, the moulded parting step, the upper wall, a 2-segment roll onto the
    deck, and the deck itself in to the key-well rim."""
    rc, rb = 0.0065, 0.0040                  # plan corner radius, top-edge roll radius

    def plan(inset):
        return dg.round_rect(W - 2 * inset, deck_len - 2 * inset, rc - inset, seg=2)

    def on_deck(inset, w):
        return [_deck(u, v, w) for u, v in plan(inset)]

    roll = [on_deck(rb * (1 - math.sin(a)), -rb * (1 - math.cos(a))) for a in (0.0, math.pi / 4, math.pi / 2)]
    top_edge = roll[-1]                       # full plan outline, rb under the deck
    step_in = 0.0008
    inner = on_deck(step_in, -rb)             # the tray wall sits 0.8 mm inside the upper shell

    def part_z(p):
        return p[2] - (SURROUND_T - rb) / math.cos(TILT)
    part_hi = [(p[0], p[1], part_z(p)) for p in top_edge]
    part_lo = [(p[0], p[1], part_z(q)) for p, q in zip(inner, top_edge)]
    bottom = [(p[0], p[1], 0.0) for p in on_deck(step_in + 0.0012, -rb)]
    well = [_deck(u, v, 0.0) for u, v in dg.round_rect(well_w, well_d, 0.0015, seg=2, cx=well_cu, cy=well_cv)]
    return [bottom, part_lo, part_hi, top_edge, roll[1], roll[0], well]




def build(kit):
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
    dg.prune(plate, lambda n: abs(n.z) < 0.9)              # its edges are under the surround
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
    _cull_hidden(keyfield, rects)
    keyfield.location = _deck(pu, pv, plate_w)
    keyfield.rotation_euler = (TILT, 0, 0)

    # ------------------------------------------------------------ case
    # One beige shell: flat bottom, lower-tray wall, the moulded parting step
    # (a 0.8 mm ledge that reads as the line between the two mouldings), the
    # upper wall rolling onto the sloped deck, the deck in to the well rim.
    rings = _case_rings(well_w, well_d, well_cu, well_cv, deck_len)
    dg.rings_mesh(kit, rings, BEIGE, name="case", cap_first=True)
    # Grey key-well walls down to the plate: the darker key-field surround.
    # They draft 2.4 mm inward, so their foot lands on the plate everywhere
    # (the numeric pad runs to within 0.8 mm of the plate's right edge).
    well_top = rings[-1]
    well_bot = [_deck(u, v, plate_w) for u, v in dg.round_rect(well_w - 0.0048, well_d - 0.0048, 0.0010, seg=2,
                                                                 cx=well_cu, cy=well_cv)]
    dg.rings_mesh(kit, [well_top, well_bot], DARK, name="well walls", orient="in")

    # Lock-LED window over the numeric pad and the maker's badge over the F
    # keys: flat grey plates on the back border (LEDs and lettering < 5 mm).
    led_u = pu + (TEX_W - 2.0 * UNIT) * SX - PLATE_W / 2
    led_v = well_cv + well_d / 2 + 0.0105
    for nm, u, w_ in (("LED window", led_u, 0.062), ("badge", -W / 2 + 0.050, 0.046)):
        q = kit.quad(w_, 0.0095, _deck(u, led_v, 0.0003), DARK, facing="+z", name=nm, uv="metres")
        q.rotation_euler = (TILT, 0, 0)

    # Cable: strain-relief grommet in the back edge, then the cord lies back
    # toward the PC and ends in its (unplugged) PS/2 mini-DIN plug.
    zb_back = Z_BACK - SURROUND_T / math.cos(TILT)
    gx, gz = -0.060, zb_back / 2 + 0.001
    grommet = kit.cylinder(0.0050, 0.010, (gx, D / 2 + 0.003, gz), BLACK, verts=8, rot=(90, 0, 0), bevel=0.0,
                           radius_top=0.0062, name="cable grommet")
    dg.prune(grommet, lambda n: n.z > 0.9)                 # its wide end is buried in the case
    r = 0.0021
    ctrl = [(gx, D / 2 + 0.006, gz), (gx - 0.001, D / 2 + 0.012, gz - 0.0008), (gx - 0.002, D / 2 + 0.018, gz - 0.0035),
            (gx - 0.004, D / 2 + 0.027, 0.0028), (gx - 0.008, D / 2 + 0.040, r), (gx - 0.008, D / 2 + 0.054, r + 0.0003),
            (gx - 0.003, D / 2 + 0.065, 0.0045), (gx + 0.007, D / 2 + 0.073, 0.0065)]
    dg.tube(kit, [(x, y, max(z, r)) for x, y, z in ctrl], r, BLACK, verts=5, name="cable")
    _ps2_plug(kit, ctrl[-1], ctrl[-2])

    kit.anchor("keys_centre", _deck(well_cu, well_cv, 0.006))
    kit.no_collider()
    kit.tag("office", "desk_top", "pile_piece")
    kit.pile("Small", mass=0, palette="office90s")
