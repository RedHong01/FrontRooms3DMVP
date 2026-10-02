"""Two-tier turned-leg side / serving table on brass cup casters (the
"escapee" standing upright in front of the pile in A24 "Backrooms" Still A).

Real-world reference: 1970s Colonial-revival / Jacobean-style occasional
table, dark walnut stain: 22 mm top with a rounded edge over a 70 mm apron,
four bobbin-turned legs with square blocks where the apron and the lower shelf
join, a notched lower shelf, brass cup casters with small black wheels.

Size: 0.62 m wide, 0.40 m deep, 0.64 m tall on its casters. The long side is
the front (-Y); the table is symmetric apart from the casters' trail.
Wood grain follows each part's length via _pilecases_grain (along the top,
shelf and rails, up the legs and blocks).
"""

import math

import _pilecases_grain as grain

NAME = "Kit_SideTableTurned"
SMOOTH_ANGLE = 40.0            # 10-vert turnings (36 deg facets) shade round; bead necks stay crisp

WOOD = "Prop_WoodDark"
BRASS = "Prop_Brass"
BLACK = "Prop_PlasticBlack"

W, D, H = 0.62, 0.40, 0.64
TOP_T = 0.022
LX, LY = 0.262, 0.152          # leg centres
BLOCK = 0.040                  # square block section
APRON_H = 0.072
SHELF_Z = 0.185                # top of the lower shelf
SHELF_T = 0.018
CUP_TOP = 0.062


def _bobbins(z0, z1, n, r_neck, r_bead, steps=4):
    """Profile points for n bobbins (elongated beads) between z0 and z1."""
    pts = []
    pitch = (z1 - z0) / n
    for b in range(n):
        base = z0 + b * pitch
        for s in range(steps):
            t = s / steps
            # flattened sine: fuller bobbin shoulders than a plain bead
            k = math.sin(math.pi * t) ** 0.7
            pts.append((r_neck + (r_bead - r_neck) * k, base + pitch * t))
    pts.append((r_neck, z1))
    return pts


def _leg_profile():
    top = H - TOP_T
    shelf_block = (SHELF_Z - SHELF_T - 0.016, SHELF_Z + 0.016)
    apron_block = (top - APRON_H - 0.006, top)
    p = [(0.0145, 0.040), (0.0150, CUP_TOP + 0.002)]
    # foot: a small bulb above the cup
    p += [(0.0190, CUP_TOP + 0.010), (0.0160, CUP_TOP + 0.019), (0.0130, CUP_TOP + 0.024)]
    # one long bobbin below the shelf (matches the 46 mm upper pitch better than two squat balls)
    p += _bobbins(CUP_TOP + 0.026, shelf_block[0] - 0.008, 1, 0.0120, 0.0180, steps=6)
    # collar rings either side of the shelf block; the core between them is hidden in the block
    p += [(0.0175, shelf_block[0] - 0.004), (0.0175, shelf_block[1] + 0.004)]
    upper0, upper1 = shelf_block[1] + 0.008, apron_block[0] - 0.010
    p += _bobbins(upper0, upper1, 7, 0.0122, 0.0186)
    # collar under the apron block; the leg ends (capped) 3 mm inside the block
    p += [(0.0160, upper1 + 0.004), (0.0182, upper1 + 0.008), (0.0182, apron_block[0] + 0.003)]
    return p


def _cup_caster(kit, x, y):
    """Brass cup caster: cup round the foot, swivel, fork, black wheel."""
    cup = [(0.0168, 0.036), (0.0178, 0.039), (0.0178, 0.058), (0.0172, CUP_TOP), (0.0150, CUP_TOP)]
    kit.lathe(cup, (x, y, 0), BRASS, verts=14, close_top=False, name="caster cup")
    kit.cylinder(0.0085, 0.006, (x, y, 0.033), BRASS, verts=10, bevel=0.001, segments=1, name="caster swivel")
    trail = 0.006
    for sx in (-1, 1):
        kit.extrude([(-0.008, 0.0), (0.008, 0.0), (0.006, 0.026), (-0.006, 0.026)], 0.0018,
                    (x + sx * 0.0068, y + trail, 0.006), BRASS, plane="yz", bevel=0.0, name="fork cheek")
    kit.box((0.016, 0.016, 0.003), (x, y + trail * 0.5, 0.0315), BRASS, bevel=0.001, segments=1, name="fork crown")
    kit.cylinder(0.0120, 0.010, (x, y + trail, 0.012), BLACK, verts=16, rot=(0, 90, 0), bevel=0.0025, segments=1, name="wheel")
    kit.cylinder(0.0030, 0.0165, (x, y + trail, 0.012), BRASS, verts=8, rot=(0, 90, 0), bevel=0.0007, segments=1, name="axle")


def build(kit):
    top_z0 = H - TOP_T
    prof = _leg_profile()
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * LX, sy * LY
            kit.lathe(prof, (x, y, 0), WOOD, verts=10, name="turned leg")
            # Square blocks where apron and shelf are joined.
            kit.box((BLOCK, BLOCK, APRON_H + 0.006), (x, y, top_z0 - (APRON_H + 0.006) / 2), WOOD,
                    bevel=0.003, segments=2, name="apron block")
            kit.box((BLOCK, BLOCK, SHELF_T + 0.032), (x, y, SHELF_Z - SHELF_T / 2), WOOD,
                    bevel=0.003, segments=2, name="shelf block")
            _cup_caster(kit, x, y)

    # Apron: rails tenoned into the blocks, set back 3 mm, with an applied
    # bead moulding along the bottom edge (4.5 mm proud, 1.5 mm below the rail).
    inset = BLOCK / 2 - 0.009 - 0.003
    rail_t = 0.018
    bead_r = 0.006
    bead_z = top_z0 - APRON_H + 0.0045
    for sy in (-1, 1):
        yy = sy * (LY + inset)
        kit.box((2 * LX - BLOCK + 0.004, rail_t, APRON_H), (0, yy, top_z0 - APRON_H / 2), WOOD,
                bevel=0.002, segments=1, name="apron rail long")
        kit.cylinder(bead_r, 2 * LX - BLOCK + 0.002, (0, yy + sy * (rail_t / 2 - 0.0015), bead_z), WOOD,
                     verts=12, rot=(0, 90, 0), bevel=0.0, name="apron bead")
    for sx in (-1, 1):
        xx = sx * (LX + inset)
        kit.box((rail_t, 2 * LY - BLOCK + 0.004, APRON_H), (xx, 0, top_z0 - APRON_H / 2), WOOD,
                bevel=0.002, segments=1, name="apron rail short")
        kit.cylinder(bead_r, 2 * LY - BLOCK + 0.002, (xx + sx * (rail_t / 2 - 0.0015), 0, bead_z), WOOD,
                     verts=12, rot=(90, 0, 0), bevel=0.0, name="apron bead")

    # Corner braces screwed across the inside of each apron corner (seen when
    # the table lies inverted in a pile): trapezoids whose 45-degree mitred
    # ends sit flush on the rails' inner faces, clear of the leg blocks.
    xr = LX + inset - rail_t / 2 + 0.001         # 1 mm into the short rail
    yr = LY + inset - rail_t / 2 + 0.001         # 1 mm into the long rail
    a, wd = 0.046, 0.022 * math.sqrt(2)          # outer-edge setback, brace width along the rail
    zc = top_z0 - 0.0235
    for sx in (-1, 1):
        for sy in (-1, 1):
            outline = [(sx * xr, sy * (yr - a)), (sx * xr, sy * (yr - a - wd)),
                       (sx * (xr - a - wd), sy * yr), (sx * (xr - a), sy * yr)]
            kit.extrude(outline, 0.045, (0, 0, zc), WOOD, plane="xy", bevel=0.002, segments=1, name="corner brace")
            # screw head on the inner face, mid-length
            mx, my = (xr + xr - a - wd) / 2, (yr - a - wd + yr) / 2
            k = 0.0007 / math.sqrt(2)
            ang = math.degrees(math.atan2(-sy, sx))
            kit.cylinder(0.0035, 0.0018, (sx * (mx - k), sy * (my - k), zc), "Prop_SteelBlack", verts=8,
                         rot=(90, 0, ang), bevel=0.0, name="brace screw")

    # Top: rounded (thumbnail) edge, 40 mm overhang past the legs.
    kit.box((W, D, TOP_T), (0, 0, top_z0 + TOP_T / 2), WOOD, bevel=0.009, segments=4, name="top")

    # Lower shelf: notched round the leg blocks, rounded edges.
    sx_, sy_ = LX + BLOCK / 2 - 0.004, LY + BLOCK / 2 - 0.004
    nx, ny = LX - BLOCK / 2, LY - BLOCK / 2
    outline = [(-nx, -sy_), (nx, -sy_), (nx, -ny), (sx_, -ny), (sx_, ny), (nx, ny), (nx, sy_), (-nx, sy_),
               (-nx, ny), (-sx_, ny), (-sx_, -ny), (-nx, -ny)]
    kit.extrude(outline, SHELF_T, (0, 0, SHELF_Z - SHELF_T / 2), WOOD, plane="xy", bevel=0.005, segments=2, name="lower shelf")

    # --- Metadata --------------------------------------------------------
    kit.support("top", (0, 0, H), (W - 0.02, D - 0.02))
    kit.support("shelf", (0, 0, SHELF_Z), (2 * nx, 2 * (LY + BLOCK / 2) - 0.02))
    kit.anchor("top", (0, 0, H))
    kit.collider((0, 0, top_z0 - APRON_H / 2 + TOP_T / 2), (W, D, APRON_H + TOP_T))
    # Open frame below the apron: one box per leg and a slab for the shelf
    # (its top is the 'shelf' support height, so things rest on it, not in it).
    for sx in (-1, 1):
        for sy in (-1, 1):
            kit.collider((sx * LX, sy * LY, (top_z0 - APRON_H) / 2), (BLOCK, BLOCK, top_z0 - APRON_H))
    kit.collider((0, 0, SHELF_Z - SHELF_T / 2), (2 * LX + BLOCK, 2 * LY + BLOCK, SHELF_T))
    kit.tag("domestic", "table", "pile", "pile_piece")
    kit.pile("Table", mass=1, palette="domestic70s", states=["Upright", "Inverted", "Side"])

    # Grain along each part, each part on its own patch of veneer.
    grain.scatter_offsets(kit, seed=2207, slots=(WOOD,))
    grain.install(kit)
