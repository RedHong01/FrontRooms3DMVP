"""Wooden stringer pallet, North-American 48 x 40 in. type (the pallet under
the plywood crate at the base of the tall pile in A24 "Backrooms" Still B).

Real-world reference: GMA-style 4-way notched stringer pallet, rough-sawn
pine/mixed softwood. 7 top deck boards (two wide lead boards, five narrow)
nailed across 3 stringers that carry two forklift notches each, 3 bottom
boards (ends + centre, the end ones chamfered on their inner edge for pallet
-jack wheels). Boards are slightly irregular: widths, gaps, tiny twists and
nail heads, as a used pallet is; the -X lead board has a corner broken off,
showing the stringer end and a bent nail. Every deck board seats on (or a
hair into) the stringers, so the deck top never rises above 0.144 m: the
pile stacks the crate on the OBB top.

Budget pass (2026-10-02, §5.3: 900 LOD0 / 400 LOD1, PinePallet; live 994 /
436 = 1.10x with the centre stringer bevelled):
* slots: Prop_PinePallet, Prop_SteelBlack (nail heads).
* nail heads are single 8 mm quads (2 tris) seated on each board's twisted
  top face, turned at random; the underside nails are gone (only Upright is
  allowed in the pile, §5.3) and the bottom boards sit on the floor.
* bevels: 1 segment on the deck boards and all three stringers (the notched
  faces are the pallet's silhouette; the centre one shows through the open
  ends and under the broken corner); none on the bottom boards (their
  chamfer is in the profile).

Texture (fix pass): Prop_PinePallet is ambientCG Planks021, grain on U, 11
planks per 1.4 m tile with painted nail dots. _pilecases_grain.install
transposes the UVs so the grain runs along every board in Unity, then snaps
each board into one plank of the sheet (seams off the boards; the 0.14 m
lead boards are wider than a plank, so their seam is pushed to an edge) and
puts the dots on the stringer lines, where the nails are. LOD1 keeps its
sharp edges. Swap in a single-board scan to drop the snapping.

Size: 1.20 m (X, stringer length) x 1.00 m (Y, deck board length) x 0.144 m.
Symmetric; -Y is the side a forklift would see the deck board ends from.
Grain follows each board (kitlib), each board on its own patch.
"""

import math
import random

import _pilecases_grain as grain

NAME = "Kit_Pallet"
LOD1 = 0.44

PINE = "Prop_PinePallet"
NAIL = "Prop_SteelBlack"

L, Wd, H = 1.20, 1.00, 0.144
BOT_T = 0.020
STR_H = 0.105
STR_T = 0.038
TOP_T = 0.019
STRINGERS_Y = (-Wd / 2 + STR_T / 2, 0.0, Wd / 2 - STR_T / 2)


def _nail(kit, x, y, z, rng):
    q = kit.quad(0.0078, 0.0078, (x, y, z), NAIL, facing="+z", uv="metres", name="nail head")
    q.rotation_euler = (0.0, 0.0, math.radians(rng.uniform(0.0, 90.0)))


def build(kit):
    rng = random.Random(4840)
    z_str0 = BOT_T
    z_top0 = BOT_T + STR_H

    # --- Stringers with two rounded forklift notches each ------------------
    def notch(a, b, depth=0.036):
        return [(a, 0.0), (a + 0.022, depth * 0.72), (a + 0.045, depth), (b - 0.045, depth),
                (b - 0.022, depth * 0.72), (b, 0.0)]
    outline = [(-L / 2, 0.0)] + notch(-0.405, -0.145) + notch(0.145, 0.405) + [(L / 2, 0.0), (L / 2, STR_H), (-L / 2, STR_H)]
    for k, sy in enumerate(STRINGERS_Y):
        st = kit.extrude(outline, STR_T, (rng.uniform(-0.004, 0.004), sy, z_str0), PINE, plane="xz",
                         bevel=0.0025, segments=1, name="stringer")
        st["fr_face"] = (0.0, 1.0 if sy > 0 else -1.0, 0.0)        # the side seen past the deck

    # --- Top deck: 7 boards along Y, irregular widths and gaps -------------
    widths = [0.140, 0.092, 0.088, 0.096, 0.086, 0.094, 0.138]
    total_gap = L - sum(widths)
    gaps = [rng.uniform(0.85, 1.15) for _ in range(6)]
    s = sum(gaps)
    gaps = [g / s * total_gap for g in gaps]
    x = -L / 2
    for i, w in enumerate(widths):
        cx = x + w / 2
        twist = rng.uniform(-0.5, 0.5)
        yaw = rng.uniform(-0.45, 0.45)          # board ends wander ~4 mm
        t = TOP_T + rng.uniform(-0.0025, 0.0)
        # The twist lifts one long edge by (w/2) sin(twist); push the board
        # down by that much so no edge stands above the stringers.
        lift = (w / 2) * math.sin(math.radians(abs(twist)))
        off = rng.uniform(-0.0008, 0.0) - lift
        dy = rng.uniform(-0.004, 0.004)
        length = Wd - rng.uniform(0.0, 0.008)
        loc = (cx, dy, z_top0 + t / 2 + off)
        if i == 0:
            # Lead board with its -X/-Y corner split off along the grain:
            # the split runs up the grain from the end, then snaps across.
            hw, hl = w / 2, length / 2
            outline = [(-hw + 0.061, -hl), (hw, -hl), (hw, hl), (-hw, hl), (-hw, -hl + 0.128),
                       (-hw + 0.021, -hl + 0.106), (-hw + 0.045, -hl + 0.089), (-hw + 0.056, -hl + 0.062),
                       (-hw + 0.062, -hl + 0.024)]
            board = kit.extrude(outline, t, loc, PINE, plane="xy", rot=(0, twist, yaw), bevel=0.0025, segments=1,
                                name="top deck board")
        else:
            board = kit.box((w, length, t), loc, PINE, rot=(0, twist, yaw), bevel=0.0025, segments=1,
                            name="top deck board")
        board["fr_nail_lines"] = list(STRINGERS_Y)     # texture nail dots go where the nails are
        # Nail heads sit 0.4 mm proud of the board's (twisted) top face.
        tw = math.radians(twist)
        for sy in STRINGERS_Y:
            n = 3 if w > 0.12 else 2
            for k in range(n):
                nx = cx + (k - (n - 1) / 2) * (w * 0.55 / max(n - 1, 1))
                if i == 0 and sy < 0 and k == 0:
                    # Under the broken corner: the board split off its nail,
                    # which stays in the stringer, bent over.
                    bx, by = cx - w / 2 + 0.024, sy + 0.003
                    kit.tube([(bx, by, z_top0 - 0.004), (bx, by, z_top0 + 0.009), (bx + 0.003, by - 0.001, z_top0 + 0.0125),
                              (bx + 0.011, by - 0.003, z_top0 + 0.0145)], 0.0014, NAIL, verts=6, caps=False,
                             name="bent nail")
                    continue
                nz = loc[2] + math.cos(tw) * t / 2 - math.sin(tw) * (nx - cx) + 0.0004
                _nail(kit, nx + rng.uniform(-0.002, 0.002), sy + rng.uniform(-0.008, 0.008), nz, rng)
        if i < 6:
            x += w + gaps[i]

    # --- Bottom deck: ends (inner edge chamfered) and centre --------------
    bw = 0.135
    def bottom_board(cx, chamfer_side):
        hw = bw / 2
        c = 0.012
        if chamfer_side > 0:      # chamfer on the +X edge
            o = [(-hw, 0), (hw, 0), (hw, BOT_T - c), (hw - c * 1.6, BOT_T), (-hw, BOT_T)]
        elif chamfer_side < 0:
            o = [(-hw, 0), (hw, 0), (hw, BOT_T), (-hw + c * 1.6, BOT_T), (-hw, BOT_T - c)]
        else:
            o = [(-hw, 0), (hw, 0), (hw, BOT_T), (-hw, BOT_T)]
        # chamfer is on the bottom (entry) edge, so flip the profile upside down
        o = [(u, BOT_T - v) for u, v in reversed(o)]
        kit.extrude(o, Wd + rng.uniform(-0.004, 0.0), (cx, rng.uniform(-0.004, 0.004), 0.0), PINE, plane="xz",
                    rot=(0, 0, rng.uniform(-0.3, 0.3)), bevel=0.0, name="bottom board")
    bottom_board(-L / 2 + bw / 2, +1)
    bottom_board(0.0, 0)
    bottom_board(L / 2 - bw / 2, -1)

    # --- Metadata --------------------------------------------------------
    kit.support("deck", (0, 0, H), (L, Wd))
    kit.anchor("deck", (0, 0, H))
    kit.collider((0, 0, H / 2), (L, Wd, H))
    kit.tag("storage", "pallet", "pile", "pile_piece")
    kit.pile("Crate", mass=2, palette="storage", states=["Upright"])

    # Each board and stringer on its own patch of the (seamless, 1.4 m
    # TileSize) pine texture, so the deck does not read as one sheet cut
    # into strips. Grain direction: kitlib.
    grain.scatter_offsets(kit, seed=4841, slots=(PINE,), tile=(1.4, 1.4))
    grain.install(kit, 35.0, planks={PINE: grain.PINE_PLANKS})
