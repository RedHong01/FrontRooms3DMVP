"""Desk-corner pile of paperwork, c. 1990s office: three letter-size stacks
crossed on top of each other (portrait / landscape / portrait, the way
in-trays get emptied onto a desk), each built from loose bundles that never
quite line up, with a few stray sheets sticking out; a closed manila file
folder with papers inside on top, its tab and label facing the viewer, held
shut at one end with a black binder clip, and a memo with a curled corner.

Real-world reference sizes: letter sheet 216 x 279 mm; stacks 35, 22 and
14 mm thick; letter folder 298 x 241 mm closed (front leaf 12 mm shorter so
the tab shows); medium binder clip 32 mm wide, 18 mm jaw body. Overall
footprint about 0.35 x 0.32 m, 0.08 m tall. Origin = desk surface under the
centre of the pile. Front (folder tab) looks -Y.

Budget (§5.3 / round-2 table): 300 tris, desk-top clutter (no collider),
pile Small 0. A stack reads by its stepped edges, so the triangles go there:
every bundle is a lidded prism with no hidden floor (10 tris), jittered in
x / y / yaw. Loose sheets are single-sided bent grids (paper has no visible
thickness at 2 m); only the curled memo corner is two-sided, because it can
be seen from behind. Slots: Paper, Cardboard (folder), Label (tab strip,
atlas cell 10), SteelBlack (clip); the folded wire handle is in the Paper
slot, whose off-white matches nickel wire under flat top light.
"""

import math
import random

import bmesh

import _storage_labels as labels

NAME = "Kit_PaperStack"
SMOOTH_ANGLE = 40.0

PAPER = "Prop_Paper"
CARD = "Prop_Cardboard"
CLIP = "Prop_SteelBlack"

SHEET_W, SHEET_L = 0.216, 0.279


def _rot(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def prism(kit, outline, z0, z1, slot, centre=(0.0, 0.0), yaw=0.0, bottom=False, name="prism"):
    """Vertical prism of a closed (x, y) outline from z0 to z1, turned by yaw
    about its own origin and moved to centre: lid and walls, a floor only if
    asked (things lying on something never show theirs)."""
    area = sum(outline[i][0] * outline[(i + 1) % len(outline)][1] - outline[(i + 1) % len(outline)][0] * outline[i][1]
               for i in range(len(outline)))
    pts = outline if area > 0 else list(reversed(outline))      # counter-clockwise from above
    pts = [_rot(x, y, yaw) for x, y in pts]
    bm = bmesh.new()
    lo = [bm.verts.new((centre[0] + x, centre[1] + y, z0)) for x, y in pts]
    hi = [bm.verts.new((centre[0] + x, centre[1] + y, z1)) for x, y in pts]
    bm.faces.new(hi)
    if bottom:
        bm.faces.new(list(reversed(lo)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    return kit._new_object(name, bm, slot, "metres", "xz")


def _rect(sx, sy, dx=0.0, dy=0.0):
    return [(dx - sx / 2, dy - sy / 2), (dx + sx / 2, dy - sy / 2), (dx + sx / 2, dy + sy / 2), (dx - sx / 2, dy + sy / 2)]


def stack(kit, centre, yaw, layers, z0, landscape, seed, strays=()):
    """A stack of loose bundles, one jittered prism each (shifted +/-3 mm and
    turned +/-1 degree), so the edges step like real paper. strays: (layer
    index, dx, dy, dyaw) single sheets slid out of the stack, slotted in
    under that layer as an up-facing quad (the layers above ride up 0.8 mm,
    so nothing is coplanar). Returns the top z."""
    rng = random.Random(seed)
    sx, sy = (SHEET_L, SHEET_W) if landscape else (SHEET_W, SHEET_L)
    z = z0
    for idx, t in enumerate(layers):
        for _, dx, dy, dyaw in [st for st in strays if st[0] == idx]:
            ox, oy = _rot(dx, dy, yaw)
            q = kit.quad(sx, sy, (centre[0] + ox, centre[1] + oy, z + 0.0004), PAPER, facing="+z", uv="metres",
                         name="stray sheet")
            q.rotation_euler = (0, 0, math.radians(yaw + dyaw))
            z += 0.0008
        ox, oy = _rot(rng.uniform(-0.003, 0.003), rng.uniform(-0.003, 0.003), yaw)
        prism(kit, _rect(sx, sy), z, z + t, PAPER, (centre[0] + ox, centre[1] + oy), yaw + rng.uniform(-1.0, 1.0),
              name="paper bundle")
        z += t
    return z


def sheet(kit, centre, yaw, z, lift, us, vs, back_faces=None, slot=PAPER, name="loose sheet"):
    """One loose sheet that is not flat: a single-sided grid sampled at local
    positions us (across) and vs (along), lifted by lift(u, v). back_faces(u,
    v) -> True also gives that cell an underside (a curl seen from behind)."""
    bm = bmesh.new()
    a = math.radians(yaw)
    ca, sa = math.cos(a), math.sin(a)

    def P(u, v, dz=0.0):
        return (centre[0] + u * ca - v * sa, centre[1] + u * sa + v * ca, z + lift(u, v) + dz)

    top = [[bm.verts.new(P(u, v)) for u in us] for v in vs]
    under = {}
    for j in range(len(vs) - 1):
        for i in range(len(us) - 1):
            bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]))
            if back_faces and back_faces((us[i] + us[i + 1]) / 2, (vs[j] + vs[j + 1]) / 2):
                cell = []
                for jj, ii in ((j, i), (j + 1, i), (j + 1, i + 1), (j, i + 1)):
                    if (jj, ii) not in under:
                        under[(jj, ii)] = bm.verts.new(P(us[ii], vs[jj], -0.0004))
                    cell.append(under[(jj, ii)])
                bm.faces.new(cell)
    for f in bm.faces:
        f.normal_update()
    return kit._new_object(name, bm, slot, "metres", "xz")


def build(kit):
    # ----------------------------------------------------------- the stacks
    s1c, s1yaw = (-0.032, 0.016), 2.0
    z = stack(kit, s1c, s1yaw, [0.006, 0.005, 0.0055, 0.004, 0.006, 0.005, 0.0035], 0.0, False, seed=1,
              strays=((2, 0.010, -0.011, 3.0), (5, -0.008, 0.006, -2.5)))
    # A sheet trapped between the first two stacks, its free end draped over
    # the front edge of the bottom stack (the far end hides under stack 2).
    dc = (-0.040, -0.009)
    v0 = (s1c[1] - SHEET_L / 2) - dc[1]          # local v of stack 1's front edge
    def drape(u, v):
        d = max(0.0, v0 - v)
        return -18.0 * d * d * (1.0 + 1.2 * u)
    sheet(kit, dc, 0.0, z + 0.0003, drape, [-SHEET_W / 2, 0.0, SHEET_W / 2],
          [-SHEET_L / 2, v0 - 0.012, v0, SHEET_L / 2], name="draped sheet")
    z += 0.0008
    z = stack(kit, (0.012, -0.006), -3.5, [0.005, 0.004, 0.0045, 0.0035, 0.005], z, True, seed=2,
              strays=((2, 0.014, -0.006, -4.0),))
    z = stack(kit, (-0.040, 0.020), -7.0, [0.004, 0.0035, 0.003, 0.0035], z, False, seed=3,
              strays=((2, -0.009, -0.012, 5.0),))

    # ---------------------------------------------------- manila file folder
    fc, fyaw = (-0.004, -0.012), 4.0
    zf = z

    def P(x, y):
        rx, ry = _rot(x, y, fyaw)
        return fc[0] + rx, fc[1] + ry

    fw, fd = 0.298, 0.241
    leaf = 0.0010
    inner = 0.0040
    tab_x = -0.062
    # Back leaf with the cut tab on its open (-Y) edge, one outline.
    prism(kit, [(-fw / 2, -fd / 2), (tab_x - 0.050, -fd / 2), (tab_x - 0.044, -fd / 2 - 0.0125),
                (tab_x + 0.044, -fd / 2 - 0.0125), (tab_x + 0.050, -fd / 2), (fw / 2, -fd / 2),
                (fw / 2, fd / 2), (-fw / 2, fd / 2)],
          zf, zf + leaf, CARD, fc, fyaw, name="folder back leaf")
    # Typed tab strip (atlas cell 10) reading from the front.
    lab = labels.card(kit, 10, 0.060, 0.011, (*P(tab_x - 0.002, -fd / 2 - 0.0063), zf + leaf + 0.0002), facing="+z",
                      name="folder tab label")
    lab.rotation_euler = (0, 0, math.radians(fyaw))
    # Papers inside, slid toward the open edge so their edge peeks out.
    prism(kit, _rect(SHEET_L, SHEET_W, 0.004, -0.010), zf + leaf, zf + leaf + inner, PAPER, fc, fyaw + 0.6,
          name="folder contents")
    # Front leaf, 12 mm shorter on the open edge.
    ztop = zf + leaf + inner
    prism(kit, _rect(fw, fd - 0.012, 0.0, 0.006), ztop, ztop + leaf, CARD, fc, fyaw, name="folder front leaf")
    # The scored fold along +Y: a half-round spine closing the two leaves.
    th = ztop + leaf - zf
    arc = [(fd / 2 + th / 2 * math.cos(a), zf + th / 2 + th / 2 * math.sin(a))
           for a in (math.radians(d) for d in (-90, -30, 30, 90))]
    bm = bmesh.new()
    rows = [[bm.verts.new((x, y, zz)) for x in (-fw / 2, fw / 2)] for y, zz in arc]
    for j in range(len(rows) - 1):
        f = bm.faces.new((rows[j][0], rows[j][1], rows[j + 1][1], rows[j + 1][0]))
        f.normal_update()
        if f.normal.y < 0:
            f.normal_flip()
    fold = kit._new_object("folder fold", bm, CARD, "metres", "xz")
    fold.location = (fc[0], fc[1], 0.0)
    fold.rotation_euler = (0, 0, math.radians(fyaw))

    # A half-letter memo dropped on the folder, one corner curling up.
    mw, ml = 0.140, 0.216
    def curl(u, v):
        t = max(0.0, (u / mw + v / ml) * 1.6 - 0.45)
        return 0.0005 + 0.013 * t * t
    sheet(kit, P(-0.066, 0.006), fyaw - 17.0, ztop + leaf,
          curl, [-mw / 2, 0.0, 0.3 * mw, mw / 2], [-ml / 2, 0.0, 0.3 * ml, ml / 2],
          back_faces=lambda u, v: u > 0 and v > 0, name="memo")

    # --------------------------------------------- binder clip on the +X end
    zc = zf + th / 2
    edge = fw / 2
    xj, xb = edge - 0.011, edge + 0.007    # jaw line, spring back
    half_back = 0.0095
    jaw = th / 2 + 0.0008
    width = 0.032
    kit.extrude([(xj, zc - jaw), (xb, zc - half_back), (xb, zc + half_back), (xj, zc + jaw)], width,
                (fc[0], fc[1], 0.0), CLIP, plane="xz", rot=(0, 0, fyaw), bevel=0.0, name="clip body")
    # Top handle folded flat onto the folder (3-sided wire: it is 2 mm thick).
    zt = ztop + leaf + 0.0011
    pts = [(xj + 0.0008, -0.0115, zc + jaw + 0.0004), (xj - 0.026, -0.0085, zt), (xj - 0.026, 0.0085, zt),
           (xj + 0.0008, 0.0115, zc + jaw + 0.0004)]
    kit.tube([(*P(x, y), zz) for x, y, zz in pts], 0.0009, PAPER, verts=3, caps=False, name="clip wire")

    # Free strip of the folder between the memo and the clip handle.
    kit.support("top", (*P(0.075, 0.0), ztop + leaf + 0.0005), (0.05, 0.16))
    kit.anchor("folder_tab", (*P(tab_x, -fd / 2 - 0.006), zf))
    kit.no_collider()
    kit.tag("office", "desk_top")
    # Upright only: on its side the loose sheets would hang in the air.
    kit.pile("Small", mass=0, states=["Upright"])
