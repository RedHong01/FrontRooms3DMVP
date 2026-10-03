"""Two-tier turned-leg side / serving table on brass cup casters (the
"escapee" standing upright in front of the pile in A24 "Backrooms" Still A).

Real-world reference: 1970s Colonial-revival / Jacobean-style occasional
table, dark walnut stain: 22 mm top with a rounded edge over a 72 mm apron,
four bobbin-turned legs with square blocks where the apron and the lower shelf
join, a lower shelf, brass cup casters with small black wheels.

Budget pass (2026-10-02, §5.3: 2,200 LOD0 / 900 LOD1, WoodWalnut + Brass;
live 2,688 / 1,102 = 1.22x after the fix pass restored the bobbins):
* slots: Prop_WoodWalnut (§5.3; was WoodDark), Prop_Brass, Prop_Rubber
  (wheels). The brace screws are gone (hidden, below 5 mm).
* legs: 8-sided lathes (SMOOTH_ANGLE 48 shades them round) with six
  rounded bobbins (fix pass: neck, shoulder, full bead, shoulder: a 4-step
  sine, so they read as beads at 2 m, not as twisted barrels) between the
  blocks and a bulb foot + long taper below the shelf; both ends are buried
  (cup, apron block) so they are left open. 7 sides was tried: faceted at
  0.5 m.
* the lower shelf is a plain slab (1-segment edge) whose corners are buried
  in the leg blocks; rails have no bevel (the top and the bead moulding cover
  their edges).

Size (§5.3 / Still A, A3): 0.46 m square, 0.66 m tall on its casters, the
legs set 48 mm in from the top's edge. Symmetric apart from the casters'
trail; -Y is the front. Wood grain follows each part's length (kitlib;
walnut's albedo grain is on V, so no transpose), each part on its own patch.
_pilecases_grain.install fixes the LOD1 sharp edges.
"""

import math

import _pilecases_grain as grain

NAME = "Kit_SideTableTurned"
LOD1 = 0.41
SMOOTH_ANGLE = 48.0            # 8-sided turnings (45 deg facets) shade round

WOOD = "Prop_WoodWalnut"
BRASS = "Prop_Brass"
RUBBER = "Prop_Rubber"

W, D, H = 0.46, 0.46, 0.66
TOP_T = 0.022
LX, LY = 0.182, 0.182          # leg centres (48 mm in from the top's edge)
BLOCK = 0.040                  # square block section
APRON_H = 0.072
SHELF_Z = 0.185                # top of the lower shelf
SHELF_T = 0.018
CUP_TOP = 0.062
LEG_SIDES = 8


def _leg_profile(bobbins=6):
    top = H - TOP_T
    shelf_block = (SHELF_Z - SHELF_T - 0.016, SHELF_Z + 0.016)     # 0.151 .. 0.201
    apron_block0 = top - APRON_H - 0.006                           # 0.540
    p = [(0.0150, 0.050),                       # inside the cup
         (0.0190, CUP_TOP + 0.013),             # foot bulb
         (0.0122, CUP_TOP + 0.030),             # neck, then a long taper up to
         (0.0178, shelf_block[0] - 0.003),      # the collar under the shelf block
         (0.0178, shelf_block[1] + 0.004)]      # collar over it (core hidden in the block)
    # Bobbins: neck, shoulder, full bead, shoulder (a 4-step sine).
    z0, z1 = shelf_block[1] + 0.011, apron_block0 - 0.012
    pitch = (z1 - z0) / bobbins
    for k in range(bobbins):
        b = z0 + k * pitch
        p += [(0.0118, b), (0.0168, b + 0.22 * pitch), (0.0188, b + 0.50 * pitch), (0.0168, b + 0.78 * pitch)]
    p += [(0.0118, z1), (0.0182, apron_block0 + 0.004)]    # last neck, then a flared collar into the block
    return p


def _cup_caster(kit, x, y):
    """Brass cup caster: cup round the foot, fork, black wheel."""
    cup = [(0.0176, 0.036), (0.0190, CUP_TOP)]          # flared socket, clear of the leg's corners
    kit.lathe(cup, (x, y, 0), BRASS, verts=8, close_top=False, name="caster cup")
    trail = 0.006
    kit.box((0.016, 0.014, 0.024), (x, y + trail * 0.5, 0.024), BRASS, bevel=0.0, name="caster fork")
    kit.cylinder(0.0120, 0.010, (x, y + trail, 0.012 * math.cos(math.pi / 6)), RUBBER, verts=6, rot=(0, 90, 0), bevel=0.0, name="wheel")


def build(kit):
    top_z0 = H - TOP_T
    prof = _leg_profile()
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * LX, sy * LY
            leg = kit.lathe(prof, (x, y, 0), WOOD, verts=LEG_SIDES, close_top=False, close_bottom=False,
                            name="turned leg")
            leg["fr_grain"] = "z"
            # Square blocks where apron and shelf are joined.
            kit.box((BLOCK, BLOCK, APRON_H + 0.006), (x, y, top_z0 - (APRON_H + 0.006) / 2), WOOD,
                    bevel=0.003, segments=1, name="apron block")
            kit.box((BLOCK, BLOCK, SHELF_T + 0.032), (x, y, SHELF_Z - SHELF_T / 2), WOOD,
                    bevel=0.0, name="shelf block")
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
                bevel=0.0, name="apron rail long")
        kit.cylinder(bead_r, 2 * LX - BLOCK + 0.002, (0, yy + sy * (rail_t / 2 - 0.0015), bead_z), WOOD,
                     verts=6, rot=(0, 90, 0), bevel=0.0, name="apron bead")
    for sx in (-1, 1):
        xx = sx * (LX + inset)
        kit.box((rail_t, 2 * LY - BLOCK + 0.004, APRON_H), (xx, 0, top_z0 - APRON_H / 2), WOOD,
                bevel=0.0, name="apron rail short")
        kit.cylinder(bead_r, 2 * LY - BLOCK + 0.002, (xx + sx * (rail_t / 2 - 0.0015), 0, bead_z), WOOD,
                     verts=6, rot=(90, 0, 0), bevel=0.0, name="apron bead")

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
            kit.extrude(outline, 0.045, (0, 0, zc), WOOD, plane="xy", bevel=0.0, name="corner brace")

    # Top: rounded (thumbnail) edge, 40 mm overhang past the legs.
    kit.box((W, D, TOP_T), (0, 0, top_z0 + TOP_T / 2), WOOD, bevel=0.008, segments=2, name="top")

    # Lower shelf: a slab with rounded edges whose corners sit inside the
    # leg blocks (reads as notched round them).
    sx_, sy_ = LX + BLOCK / 2 - 0.004, LY + BLOCK / 2 - 0.004
    nx = LX - BLOCK / 2
    kit.box((2 * sx_, 2 * sy_, SHELF_T), (0, 0, SHELF_Z - SHELF_T / 2), WOOD, bevel=0.005, segments=1,
            name="lower shelf")

    # --- Metadata --------------------------------------------------------
    kit.support("top", (0, 0, H), (W - 0.02, D - 0.02))
    kit.support("shelf", (0, 0, SHELF_Z), (2 * nx, 2 * (LY + BLOCK / 2) - 0.02))
    kit.anchor("top", (0, 0, H))
    kit.collider((0, 0, H / 2), (W, D, H))       # one box (§5.3); the pile uses blockers
    kit.tag("domestic", "table", "pile", "pile_piece")
    kit.pile("Table", mass=1, palette="domestic70s", states=["Upright", "Inverted"])

    # Each part on its own patch of veneer (grain direction: kitlib).
    grain.scatter_offsets(kit, seed=2207, slots=(WOOD,), tile=(1.8, 1.8))    # Walnut TileSize 1.8 m
    grain.install(kit, SMOOTH_ANGLE)
