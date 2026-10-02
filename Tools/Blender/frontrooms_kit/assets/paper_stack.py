"""Desk-corner pile of paperwork, c. 1990s office: three letter-size stacks
crossed on top of each other (portrait / landscape / portrait, the way
in-trays get emptied onto a desk), each built from loose bundles that never
quite line up, with a few stray sheets sticking out; a closed manila file
folder with papers inside on top, its tab and label facing the viewer, held
shut at one end with a black binder clip (folded wire handles).

Real-world reference sizes: letter sheet 216 x 279 mm; stacks 35, 22 and
14 mm thick; letter folder 298 x 241 mm closed (front leaf 12 mm shorter so
the tab shows); medium binder clip 32 mm wide, 18 mm jaw body. Overall
footprint about 0.35 x 0.32 m, 0.08 m tall. Origin = desk surface under the
centre of the pile. Front (folder tab) looks -Y.

The two bent sheets (one draped over a stack edge, one memo with a curled
corner) are bmesh grids with real thickness registered through
kit._new_object, so they share the kit's UV/export path.
"""

import math
import random

import bmesh

import _storage_labels as labels

NAME = "Kit_PaperStack"
SMOOTH_ANGLE = 40.0

PAPER = "Prop_Paper"
CARD = "Prop_Cardboard"
LABEL = "Prop_Label"
CLIP = "Prop_SteelBlack"
WIRE = "Prop_Chrome"

SHEET_W, SHEET_L = 0.216, 0.279


def _rot(x, y, deg):
    a = math.radians(deg)
    return x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a)


def stack(kit, centre, yaw, bundles, z0, landscape, seed, strays=()):
    """A stack of loose bundles. Each listed bundle is split into 2-3 mm
    reams, every ream shifted (+/-2 mm) and turned a little on top of its
    bundle's own offset, so the edges show many fine stepped layers rather
    than a few rounded slabs. strays: (bundle index, dx, dy, dyaw) single
    sheets slid out of the stack; each is slotted into the z sequence under
    that bundle (the bundles above ride up 0.9 mm), so no faces are
    coplanar. Returns the top z."""
    rng = random.Random(seed)
    sx, sy = (SHEET_L, SHEET_W) if landscape else (SHEET_W, SHEET_L)
    stray_t = 0.0009
    z = z0
    for idx, t in enumerate(bundles):
        for _, dx, dy, dyaw in [st for st in strays if st[0] == idx]:
            ox, oy = _rot(dx, dy, yaw)
            kit.box((sx, sy, stray_t), (centre[0] + ox, centre[1] + oy, z + stray_t / 2), PAPER,
                    bevel=0.0002, segments=1, rot=(0, 0, yaw + dyaw), name="stray sheet")
            z += stray_t
        bx, by = rng.uniform(-0.0025, 0.0025), rng.uniform(-0.0025, 0.0025)
        byaw = rng.uniform(-0.8, 0.8)
        n = max(1, int(round(t / 0.0026)))
        for k in range(n):
            tk = t / n
            dx, dy = bx + rng.uniform(-0.002, 0.002), by + rng.uniform(-0.002, 0.002)
            ox, oy = _rot(dx, dy, yaw)
            kit.box((sx, sy, tk), (centre[0] + ox, centre[1] + oy, z + tk / 2), PAPER,
                    bevel=min(0.0004, tk * 0.1), segments=1, rot=(0, 0, yaw + byaw + rng.uniform(-0.5, 0.5)), name="paper ream")
            z += tk
    return z


def sheet(kit, w, l, centre, yaw, z, bend, us, vs, thick=0.0006, name="loose sheet"):
    """One loose sheet that is not flat: a grid sampled at local positions
    us (across w) and vs (along l), lifted by bend(u, v), given a real
    thickness. Bends are where paper reads as paper."""
    bm = bmesh.new()
    top = [[bm.verts.new((u, v, bend(u, v))) for u in us] for v in vs]
    bot = [[bm.verts.new((u, v, bend(u, v) - thick)) for u in us] for v in vs]
    nu, nv = len(us), len(vs)
    for j in range(nv - 1):
        for i in range(nu - 1):
            bm.faces.new((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]))
            bm.faces.new((bot[j][i], bot[j + 1][i], bot[j + 1][i + 1], bot[j][i + 1]))
    # Edges of the sheet (closed rim), wound outward.
    ring = [(0, i) for i in range(nu)] + [(j, nu - 1) for j in range(1, nv)] + \
           [(nv - 1, i) for i in range(nu - 2, -1, -1)] + [(j, 0) for j in range(nv - 2, 0, -1)]
    for k in range(len(ring)):
        a, b = ring[k], ring[(k + 1) % len(ring)]
        bm.faces.new((bot[a[0]][a[1]], bot[b[0]][b[1]], top[b[0]][b[1]], top[a[0]][a[1]]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = kit._new_object(name, bm, PAPER, "metres", "xz")
    obj.location = (centre[0], centre[1], z + thick + 0.0002)
    obj.rotation_euler = (0, 0, math.radians(yaw))
    return obj


def build(kit):
    # ----------------------------------------------------------- the stacks
    z = stack(kit, (-0.032, 0.016), 2.0, [0.008, 0.006, 0.007, 0.005, 0.008], 0.0, False, seed=1,
              strays=((2, 0.010, -0.011, 3.0), (4, -0.008, 0.006, -2.5)))
    # A sheet trapped between the first two stacks, its free end draped over
    # the front edge of the bottom stack.
    s1_front = 0.016 - SHEET_L / 2          # local front edge of stack 1 (y)
    dc = (-0.058, -0.009)
    v0 = s1_front - dc[1]                   # 25 mm of the sheet overhang
    def drape(u, v):
        d = max(0.0, v0 - v)
        return -18.0 * d * d * (1.0 + 1.2 * u)
    vs = [-SHEET_L / 2 + (v0 + SHEET_L / 2) * k / 4 for k in range(4)] + [v0, v0 + 0.03, 0.04, SHEET_L / 2]
    us = [-SHEET_W / 2 + SHEET_W * k / 5 for k in range(6)]
    sheet(kit, SHEET_W, SHEET_L, dc, 0.0, z, drape, us, vs, name="draped sheet")
    z += 0.0008
    z = stack(kit, (0.012, -0.006), -3.5, [0.006, 0.005, 0.007, 0.004], z, True, seed=2,
              strays=((1, 0.014, -0.006, -4.0),))
    z = stack(kit, (-0.040, 0.020), -7.0, [0.005, 0.004, 0.005], z, False, seed=3,
              strays=((1, -0.009, -0.012, 5.0),))

    # ---------------------------------------------------- manila file folder
    fc, fyaw = (-0.004, -0.012), 4.0
    zf = z

    def P(x, y):
        rx, ry = _rot(x, y, fyaw)
        return fc[0] + rx, fc[1] + ry

    fw, fd = 0.298, 0.241
    leaf = 0.0010
    inner = 0.0040
    # Back leaf (bottom), with the cut tab on its open (-Y) edge.
    kit.box((fw, fd, leaf), (*P(0, 0), zf + leaf / 2), CARD, bevel=0.0004, segments=1, rot=(0, 0, fyaw), name="folder back leaf")
    tab_x = -0.062
    kit.extrude([(-0.050, 0.0), (-0.044, -0.0125), (0.044, -0.0125), (0.050, 0.0)], leaf,
                (*P(tab_x, -fd / 2 + 0.0004), zf + leaf / 2), CARD, plane="xy", rot=(0, 0, fyaw), bevel=0.0003, segments=1,
                name="folder tab")
    # Typed tab label: one card of the Prop_Label atlas, reading from the front.
    lab = labels.label(kit, "PAYROLL", 0.066, 0.0085, (1, 0, 0), (0, 1, 0), name="folder tab label", min_h=34.0)
    lab.location = (*P(tab_x - 0.006, -fd / 2 - 0.0062), zf + leaf + 0.0002)
    lab.rotation_euler = (0, 0, math.radians(fyaw))
    # Papers inside, slid toward the open edge so their edge peeks out.
    for k, (dx, dy, dyaw) in enumerate(((0.004, -0.008, 0.8), (0.001, -0.005, -0.4))):
        kit.box((SHEET_L, SHEET_W, inner / 2), (*P(dx, dy), zf + leaf + inner / 4 + k * inner / 2), PAPER, bevel=0.0002, segments=1,
                rot=(0, 0, fyaw + dyaw), name="folder contents")
    # Front leaf, 12 mm shorter on the open edge; the scored fold at +Y.
    ztop = zf + leaf + inner
    kit.box((fw, fd - 0.012, leaf), (*P(0, 0.006), ztop + leaf / 2), CARD, bevel=0.0004, segments=1, rot=(0, 0, fyaw),
            name="folder front leaf")
    fold_r = (ztop + leaf - zf) / 2
    kit.cylinder(fold_r, fw, (*P(0, fd / 2), zf + fold_r), CARD, verts=10, rot=(0, 90, fyaw), bevel=0.0, name="folder fold")

    # A half-letter memo dropped on the folder, one corner curling up.
    mw, ml = 0.140, 0.216
    def curl(u, v):
        t = max(0.0, (u / mw + v / ml) * 1.6 - 0.45)
        return 0.013 * t * t
    us = [-mw / 2 + mw * k / 5 for k in range(6)]
    vs = [-ml / 2 + ml * k / 7 for k in range(8)]
    sheet(kit, mw, ml, P(-0.066, 0.006), fyaw - 17.0, ztop + leaf, curl, us, vs, name="memo")

    # --------------------------------------------- binder clip on the +X end
    th = ztop + leaf - zf                  # folder thickness at the clip
    zc = zf + th / 2
    edge = fw / 2
    xj, xb = edge - 0.011, edge + 0.007    # jaw line, spring back
    half_back = 0.0095
    jaw = th / 2 + 0.0006
    width = 0.032
    for s in (1, -1):
        dx, dz = xb - xj, half_back - jaw
        length = math.hypot(dx, dz)
        ang = math.degrees(math.atan2(dz, dx))
        cx, cz = (xj + xb) / 2, zc + s * (jaw + half_back) / 2
        kit.box((length + 0.001, width, 0.0008), (*P(cx, 0), cz), CLIP, bevel=0.0003, segments=1,
                rot=(0, -s * ang, fyaw), name="clip plate")
        kit.cylinder(0.0011, width, (*P(xj, 0), zc + s * jaw), CLIP, verts=8, rot=(90, 0, fyaw), bevel=0.0003,
                     segments=1, name="clip lip")
    kit.box((0.0008, width, half_back * 2), (*P(xb, 0), zc), CLIP, bevel=0.0003, segments=1, rot=(0, 0, fyaw), name="clip back")

    def wire(pts):
        out = []
        for x, y, zz in pts:
            out.append((*P(x, y), zz))
        kit.tube(out, 0.0009, WIRE, verts=6, name="clip wire")

    # Top handle folded flat onto the folder; bottom handle folded back
    # along the spring and hanging off the edge.
    zt = ztop + leaf + 0.0011
    wire([(xj + 0.0008, -0.0115, zc + jaw + 0.0004), (xj - 0.003, -0.0112, zt), (xj - 0.026, -0.0085, zt),
          (xj - 0.029, -0.006, zt), (xj - 0.029, 0.006, zt), (xj - 0.026, 0.0085, zt), (xj - 0.003, 0.0112, zt),
          (xj + 0.0008, 0.0115, zc + jaw + 0.0004)])
    zl = zc - jaw
    wire([(xj, -0.0115, zl - 0.0004), (xj + 0.008, -0.0112, zl - 0.0032), (xj + 0.024, -0.0088, zl - 0.0090),
          (xj + 0.027, -0.006, zl - 0.0100), (xj + 0.027, 0.006, zl - 0.0100), (xj + 0.024, 0.0088, zl - 0.0090),
          (xj + 0.008, 0.0112, zl - 0.0032), (xj, 0.0115, zl - 0.0004)])

    # Free strip of the folder between the memo and the clip handle (its
    # corners stay clear of both at the folder's 4 degree yaw).
    kit.support("top", (*P(0.075, 0.0), ztop + leaf + 0.0005), (0.05, 0.16))
    kit.anchor("folder_tab", (*P(tab_x, -fd / 2 - 0.006), zf))
    kit.tag("office", "desk_top")
    # Upright only: on its side the loose sheets would hang in the air.
    kit.pile("Small", states=["Upright"])
