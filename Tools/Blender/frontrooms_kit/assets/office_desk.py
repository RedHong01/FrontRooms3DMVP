"""1990s open-plan office desk: almond laminate worksurface on a dark-brown
painted steel tube frame with a free-standing box/box/file pedestal (the desk
in Red's target office image, left foreground).

Real-world reference: the 30" x 60" "steel-frame pedestal desk" sold by every
contract dealer c. 1985-98 (Steelcase/Hon/Global clones). 1.524 m wide,
0.762 m deep, worksurface at 0.74 m (29"), 30 mm particleboard top in
high-pressure laminate with a rounded laminate self-edge (the target shows a
light edge band, §5.1 "edge banding is a bevel in the same slot") and a kraft
backer sheet underneath. Frame: 40 mm square legs on levelling glides,
25 x 50 mm rails under the top, foot rails at both ends, a pressed-steel
modesty panel with folded hems and two stiffening beads at the back (+Y).
Every frame member runs up into the underside of the top. Right-hand
pedestal 0.38 W x 0.56 D x 0.71 H (carcass top meets the top's underside)
with two 150 mm box drawers and a 350 mm file drawer, recessed pulls and a
lock in the top drawer, painted almond, a touch lighter and cooler than the
laminate top.

Front (user side, knee space, drawer faces) faces -Y. User's left = -X.

Budget build (round 2, the three §5.3 slots: LaminateBeige top, SteelBrown
frame, SteelPutty pedestal, so the pedestal shares its paint with the
filing cabinets, panel trims and posts): small dark parts (glides, pull
recesses, grommet, lock, the void behind the drawer shut lines) and the
underside backer (a dark phenolic sheet, seen on an inverted pile desk)
share the frame's dark-brown paint; bolts and screws are gone (< 5 mm at
2 m); the modesty panel's hems and beads are one extrusion; the top is one
bevelled slab with a real hole cut for the cable grommet (a rim lathed over
a dark recess, so it reads as a grommet and not a brown dot). A dark PVC
T-mould (Prop_PVCEdge) would be a fourth slot: set EDGE below.
LOD1 is re-marked sharp after the decimate (_workstation_lod.sharp_lod1).
"""

import math

import bmesh

from _workstation_lod import sharp_lod1

NAME = "Kit_OfficeDesk"
LOD1 = 0.41

LAM = "Prop_LaminateBeige"
STEEL = "Prop_SteelBrown"
PED = "Prop_SteelPutty"         # pedestal (§5.3; shared with files, panels, posts)
BACKER = STEEL                  # dark phenolic-style underside sheet
EDGE = LAM                      # self-edge (target); "Prop_PVCEdge" for a T-mould
DARK = STEEL                    # glides, pull recesses, grommet, lock

W, D = 1.524, 0.762
TOP = 0.74
TOP_T = 0.030

# Cable grommet, back left (where the CRT cords drop): a moulded rim 1.2 mm
# proud over a hole cut through the laminate (r 30 mm, hidden under the rim)
# and a dark sleeve/floor GROM_DEPTH down, open, so a shadowed hole reads.
GROM_X, GROM_Y = -0.47, 0.285
GROM_R_OUT, GROM_R_IN, GROM_HOLE = 0.034, 0.026, 0.030
GROM_DEPTH = 0.022             # deep sleeve: walls in shadow, floor half hidden

LEG = 0.040                     # square leg tube
LEG_X = W / 2 - 0.030 - LEG / 2  # 30 mm overhang at the ends
LEG_Y = D / 2 - 0.030 - LEG / 2  # 30 mm overhang front and back
LEG_Z0 = 0.016                  # leg bottom (glide underneath)
UNDER = TOP - TOP_T + 0.0005    # frame members end 0.5 mm inside the top

# Pedestal footprint (right end, inside the right legs). Its carcass top
# meets the top's underside.
P_W, P_D, P_H = 0.38, 0.56, TOP - TOP_T
P_X1 = LEG_X - LEG / 2 - 0.010
P_X0 = P_X1 - P_W
P_CX = (P_X0 + P_X1) / 2
P_FRONT = -LEG_Y - LEG / 2       # flush with the front legs
P_CY = P_FRONT + P_D / 2


def _cut_hole(obj, cx, cy, r, verts=12):
    """Replace a kit.box slab's top face by a triangle fan around a round
    hole of radius r at world (cx, cy). The slab stays closed below (the
    hole's edge is hidden under the grommet rim); the top stays one plane,
    so it still shades flat and only its outer edges take the bevel."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    top = max(bm.faces, key=lambda f: f.calc_center_median().z)
    zt = top.verts[0].co.z
    hx, hy = cx - obj.location.x, cy - obj.location.y
    two_pi = 2 * math.pi

    def ang(co):
        return math.atan2(co[1] - hy, co[0] - hx)

    corners = sorted(top.verts, key=lambda v: ang(v.co))
    ca = [ang(v.co) for v in corners]
    bmesh.ops.delete(bm, geom=[top], context="FACES_ONLY")
    ra = [two_pi * i / verts + math.pi / verts for i in range(verts)]
    ring = [bm.verts.new((hx + r * math.cos(a), hy + r * math.sin(a), zt)) for a in ra]

    def rel(a, base):
        return (a - base) % two_pi

    faces = []
    for k in range(4):
        t0, t1 = ca[k], ca[(k + 1) % 4]
        span = rel(t1, t0) or two_pi
        inside = sorted((i for i in range(verts) if rel(ra[i], t0) < span), key=lambda i: rel(ra[i], t0))
        nxt = min(range(verts), key=lambda i: rel(ra[i], t1))
        poly = [corners[k], corners[(k + 1) % 4], ring[nxt]] + [ring[i] for i in reversed(inside)]
        f = bm.faces.new(poly)
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
        faces.append(f)
    bmesh.ops.triangulate(bm, faces=faces, quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(me)
    bm.free()
    me.update()


def _orient_open(obj, eye=(0.0, 0.0, 0.5)):
    """Point every face of an open lathe (the grommet) toward ``eye`` (local
    space, above the hole): rim up, sleeve wall inward, floor up."""
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    for f in bm.faces:
        f.normal_update()
        c = f.calc_center_median()
        if f.normal.dot((eye[0] - c.x, eye[1] - c.y, eye[2] - c.z)) < 0:
            f.normal_flip()
    bm.to_mesh(me)
    bm.free()


def _top(kit):
    # One laminate slab; the 2-segment 2.5 mm round is the self-edge that
    # catches the top light along the front.
    slab = kit.box((W, D, TOP_T), (0, 0, TOP - TOP_T / 2), LAM,
                   bevel=0.0025, segments=2, name="worksurface")
    _cut_hole(slab, GROM_X, GROM_Y, GROM_HOLE)
    if EDGE != LAM:
        kit.frame((W, D), (W - 0.008, D - 0.008), TOP_T + 0.001, (0, 0, TOP - TOP_T / 2 + 0.0005), EDGE,
                  rot=(90, 0, 0), bevel=0.003, segments=1, name="t-mould edge")
    # Backer sheet on the underside (seen when crouching or on an inverted
    # pile desk): a down-facing quad 0.6 mm under the slab, dark phenolic.
    backer = kit.quad(W - 0.008, D - 0.008, (0, 0, TOP - TOP_T - 0.0006), BACKER, facing="+z", uv="metres",
                      name="backer")
    backer.rotation_euler = (math.pi, 0, 0)
    # Cable grommet: rounded rim ring (r 34 -> 26 mm, 1.2 mm proud), then an
    # open sleeve straight down GROM_DEPTH to a dark floor; no cap.
    prof = [(GROM_R_OUT, 0.0), (GROM_R_OUT - 0.0015, 0.0012), (GROM_R_IN + 0.0005, 0.0012),
            (GROM_R_IN, -GROM_DEPTH), (0.0, -GROM_DEPTH)]
    g = kit.lathe(prof, (GROM_X, GROM_Y, TOP), DARK, verts=12, name="grommet",
                  close_top=False, close_bottom=False)
    _orient_open(g)


def _modesty_profile(z0, z1, zc):
    """Pressed-steel modesty panel section in (y, z), y outward = +Y:
    8 mm web, 16 mm folded hems top and bottom, two 4 mm beads on the back."""
    pts = [(-0.008, z0 + 0.003), (-0.005, z0), (0.005, z0), (0.008, z0 + 0.003),
           (0.008, z0 + 0.016), (0.004, z0 + 0.016)]
    for dz in (-0.07, 0.07):
        b = zc + dz
        pts += [(0.004, b - 0.007), (0.008, b - 0.004), (0.008, b + 0.004), (0.004, b + 0.007)]
    pts += [(0.004, z1 - 0.016), (0.008, z1 - 0.016), (0.008, z1), (-0.008, z1),
            (-0.008, z1 - 0.016), (-0.004, z1 - 0.016), (-0.004, z0 + 0.016), (-0.008, z0 + 0.016)]
    return pts


def _frame(kit):
    leg_h = UNDER - LEG_Z0
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * LEG_X, sy * LEG_Y
            kit.box((LEG, LEG, leg_h), (x, y, LEG_Z0 + leg_h / 2), STEEL, bevel=0.003, segments=1, name="leg")
            # Levelling glide: a dark round foot under the tube.
            kit.cylinder(0.016, LEG_Z0, (x, y, LEG_Z0 / 2), DARK, verts=8, bevel=0.0, name="glide")

    rail_len_y = 2 * LEG_Y - LEG
    rail_z = UNDER - 0.025
    for sx in (-1, 1):
        x = sx * LEG_X
        # End rail under the top and the foot rail: the panel-end frame.
        kit.box((0.025, rail_len_y, 0.050), (x, 0, rail_z), STEEL, bevel=0.003, segments=1, name="end rail")
        kit.box((0.025, rail_len_y, 0.035), (x, 0, 0.075), STEEL, bevel=0.003, segments=1, name="foot rail")

    # Back rail (full length) and the front apron over the knee space only.
    kit.box((2 * LEG_X - LEG, 0.025, 0.050), (0, LEG_Y, rail_z), STEEL, bevel=0.003, segments=1, name="back rail")
    fx0, fx1 = -LEG_X + LEG / 2, P_X0 - 0.004
    kit.box((fx1 - fx0, 0.025, 0.045), ((fx0 + fx1) / 2, -LEG_Y + 0.004, UNDER - 0.0225), STEEL,
            bevel=0.003, segments=1, name="front apron")

    # Hat-channel cross brace under the top at mid-knee (seen when crouching).
    by0, by1 = -LEG_Y + 0.017, LEG_Y - 0.0125
    kit.box((0.030, by1 - by0, 0.022), (-0.20, (by0 + by1) / 2, UNDER - 0.011), STEEL, bevel=0.0, name="cross brace")

    # Pressed-steel modesty panel between the back legs: one extrusion of
    # the hemmed, beaded section. Its top hem tucks 2 mm up into the back
    # rail, so there is no see-through slit.
    mp_w = 2 * LEG_X - LEG - 0.002
    mp_z0, mp_z1 = 0.33, rail_z - 0.025 + 0.002
    kit.extrude(_modesty_profile(mp_z0, mp_z1, (mp_z0 + mp_z1) / 2), mp_w, (0, LEG_Y + 0.002, 0), STEEL,
                plane="yz", bevel=0.0, name="modesty panel")


def _bevel_outer_only(obj):
    """Limit a kit.frame part's bevel to its outer silhouette (the first 8
    verts are the outer rings). Bevelling the opening's reflex corners bends
    the front-face normals and smears a shading wedge across the front."""
    me = obj.data
    attr = me.attributes.get("bevel_weight_edge") or me.attributes.new("bevel_weight_edge", "FLOAT", "EDGE")
    for e in me.edges:
        attr.data[e.index].value = 1.0 if e.vertices[0] < 8 and e.vertices[1] < 8 else 0.0
    obj.modifiers["bevel"].limit_method = "WEIGHT"


def _drawer(kit, cz, h, name, lock=False, card=False):
    """One inset drawer front (2 mm round) with a recessed full pull at the
    top: the opening, a dark cup behind it and the formed finger lip."""
    fw = P_W - 2 * 0.016 - 2 * 0.003
    front = P_FRONT - 0.002                 # 2 mm proud of the carcass
    fy = front + 0.010
    pull_w, pull_h = 0.240, 0.026
    pull_cz = cz + h / 2 - 0.014 - pull_h / 2
    _bevel_outer_only(kit.frame((fw, h), (pull_w, pull_h), 0.020, (P_CX, fy, cz), PED,
                                inner_offset=(0, pull_cz - cz), bevel=0.002, segments=1, name=name))
    kit.box((pull_w + 0.006, 0.010, pull_h + 0.006), (P_CX, fy + 0.006, pull_cz), DARK, bevel=0.0, name=name + " pull cup")
    kit.box((pull_w - 0.002, 0.004, 0.008), (P_CX, front - 0.001, pull_cz + pull_h / 2 - 0.004), PED,
            bevel=0.0, name=name + " pull lip")
    if lock:
        lx = P_CX + pull_w / 2 + (fw / 2 - pull_w / 2) / 2
        kit.cylinder(0.0105, 0.004, (lx, front - 0.002, pull_cz), DARK, verts=8, rot=(90, 0, 0),
                     bevel=0.0, name="lock")
    if card:
        # Card holder: a pressed frame 1.5 mm proud and a beige index card.
        cz_card = pull_cz - pull_h / 2 - 0.045
        kit.frame((0.086, 0.036), (0.074, 0.026), 0.003, (P_CX, front - 0.0015, cz_card), PED,
                  inner_offset=(0, 0.003), bevel=0.0, name="card holder")
        kit.quad(0.074, 0.026, (P_CX, front - 0.0007, cz_card + 0.003), LAM, uv="metres", name="drawer card")


def _pedestal(kit):
    glide_h = 0.018
    body_h = P_H - glide_h
    cz = glide_h + body_h / 2
    wall = 0.016
    # Carcass: a closed sleeve (sides, top, bottom) with a back panel and a
    # dark void behind the drawer fronts so the 3 mm shut lines read.
    kit.frame((P_W, body_h), (P_W - 2 * wall, body_h - 2 * wall), P_D, (P_CX, P_CY, cz), PED,
              bevel=0.003, segments=1, name="pedestal carcass")
    kit.box((P_W - 0.01, 0.010, body_h - 0.01), (P_CX, P_FRONT + P_D - 0.006, cz), PED, bevel=0.0, name="pedestal back")
    kit.box((P_W - 2 * wall + 0.002, 0.006, body_h - 2 * wall + 0.002), (P_CX, P_FRONT + 0.035, cz), DARK,
            bevel=0.0, name="drawer void")
    # Box / box / file, 3 mm gaps (the last 3 mm is the top shut line).
    z0 = glide_h + wall + 0.003
    hs = (0.3495, 0.150, 0.150)
    names = ("file drawer", "box drawer 2", "box drawer 1")
    for i, (h, n) in enumerate(zip(hs, names)):
        _drawer(kit, z0 + h / 2, h, n, lock=(i == 2), card=(i == 0))
        z0 += h + 0.003
    # Levelling glides at the four corners (in the shadow under the carcass).
    for sx in (-1, 1):
        for sy in (-1, 1):
            kit.box((0.026, 0.026, glide_h), (P_CX + sx * (P_W / 2 - 0.028), P_CY + sy * (P_D / 2 - 0.030), glide_h / 2),
                    DARK, bevel=0.0, name="pedestal glide")


def build(kit):
    sharp_lod1(kit)
    _top(kit)
    _frame(kit)
    _pedestal(kit)

    kit.support("top", (0, 0, TOP), (1.50, 0.74))
    kit.anchor("monitor", (-0.20, 0.08, TOP))
    kit.anchor("keyboard", (-0.20, -0.245, TOP))
    kit.anchor("chair", (-0.20, -0.62, 0.0))
    kit.collider((0, 0, (TOP + 0.001) / 2), (W, D, TOP + 0.001))
    kit.tag("office", "workstation")
    kit.pile("Table", mass=2, states=["Upright", "Inverted", "Side"])
