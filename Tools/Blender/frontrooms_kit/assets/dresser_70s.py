"""1970s teak-veneer chest of drawers (the "tall 5-drawer chest" tipped 40
degrees onto its corner in A24 "Backrooms" Still A).

Real-world reference: mass-market mid-1970s American/Danish-export chest,
orange-grain teak veneer on particleboard, inset drawers between thin face
rails, recessed plinth, a 28 mm top that overhangs the carcass by 12 mm with a
rounded (bullnose) edge, brass bail pulls on stamped backplates, tempered
hardboard back panel with the maker's paper label.

Budget pass (2026-10-02, §5.3 Kit_Chest5 / Kit_Dresser70s: 1,500 / 600;
fix pass: resized to the §5.3 0.86 x 0.46 x 1.22, ~1,610 / ~680 tris):
* slots: Prop_WoodTeak, Prop_Brass, Prop_Hardboard (back, interior seen
  through the shut lines, plinth glue blocks), Prop_Label (atlas cell 11,
  maker's label). The nylon glides and the 4 mm back brads are gone (below
  the 5 mm rule); the plinth now reaches the floor.
* bevels: 3-segment bullnose on the top (the silhouette), 1 segment on the
  sides and drawer fronts, none on the rails/stile (they only border the dark
  shut lines) or on parts hidden inside the plinth.
* pulls: stadium backplate (3-segment ends), two 6-sided posts and a
  6-sided bail tube on a 4-segment arc (~116 tris each, 8 pulls).

Wood grain: kitlib's metre UVs follow each board's length (horizontal on
drawer fronts, rails and top, vertical on the sides and stile);
_pilecases_grain.install transposes them for the teak albedo (grain on U),
fixes the LOD1 sharp edges, and scatter_offsets gives each board its own
patch of veneer.

Size (§5.3 Kit_Chest5): 0.86 m wide, 0.46 m deep (top), 1.22 m tall. Drawers:
2 small side by side on top, 3 wide graduated below (rows scaled x1.135 to
fill the taller stack). Front (drawer faces) looks -Y.
"""

import math

import kitlib
import _pilecases_grain as grain

NAME = "Kit_Dresser70s"
LOD1 = 0.42
SMOOTH_ANGLE = 40.0            # 1-segment 45-degree chamfers stay crisp

TEAK = "Prop_WoodTeak"
BRASS = "Prop_Brass"
BACK = "Prop_Hardboard"        # back panel, interior shadow, glue blocks
LABEL = "Prop_Label"

W, D, H = 0.86, 0.46, 1.22
SIDE_T = 0.018
CX = 0.418                     # outer half-width of the carcass
Y_FRONT = -0.217               # front edge of sides / rails / drawer faces
Y_BACK = 0.227
PLINTH_H = 0.075
TOP_T = 0.028
TOP_Z0 = H - TOP_T             # underside of the top
RAIL = 0.016                   # face rail between drawer rows
GAP = 0.0025                   # shut line each side of a drawer front


def _label_rect(mirror=False):
    """Maker's label (Prop_Label atlas cell 11), cropped to the paper."""
    u0, v0, u1, v1 = kitlib.Kit.atlas_cell(11, 4, 4)       # (0.75, 0.25, 1.0, 0.5)
    w, h = u1 - u0, v1 - v0
    r = (u0 + 0.076 * w, v0 + 0.156 * h, u0 + 0.924 * w, v0 + 0.836 * h)
    # A +Y-facing decal is seen from behind its XZ mapping: swap U to read.
    return (r[2], r[1], r[0], r[3]) if mirror else r


def _stadium(w, h, n=3):
    """Rounded-end plate outline (u = x, v = z), centred on 0."""
    r = h / 2
    cx = w / 2 - r
    pts = []
    for i in range(n + 1):
        a = -math.pi / 2 + math.pi * i / n
        pts.append((cx + r * math.cos(a), r * math.sin(a)))
    for i in range(n + 1):
        a = math.pi / 2 + math.pi * i / n
        pts.append((-cx + r * math.cos(a), r * math.sin(a)))
    return pts


def _bail_pull(kit, x, z, span=0.076):
    """Brass bail pull: stamped backplate, two posts, hanging bail."""
    yf = Y_FRONT
    kit.extrude(_stadium(span + 0.03, 0.042), 0.0025, (x, yf - 0.00125, z), BRASS,
                plane="xz", bevel=0.0, name="pull backplate")
    hx = span / 2
    post_len = 0.013
    for sx in (-1, 1):
        kit.cylinder(0.0042, post_len, (x + sx * hx, yf - 0.0025 - post_len / 2, z + 0.006), BRASS,
                     verts=6, rot=(90, 0, 0), bevel=0.0, name="pull post")
    # The bail hangs from inside the post ends and rests its bottom on the plate.
    n = 4
    y_top = yf - 0.0025 - post_len + 0.003
    y_bot = yf - 0.0053                       # tube back touches the plate front
    pts = []
    for i in range(n + 1):
        a = math.pi + math.pi * i / n
        t = math.sin(a)                       # 0 .. -1 .. 0
        pts.append((x + hx * math.cos(a), y_top + (y_bot - y_top) * (-t), z + 0.006 + 0.022 * t))
    kit.tube(pts, 0.0028, BRASS, verts=6, caps=False, name="pull bail")


def build(kit):
    # --- Carcass ---------------------------------------------------------
    car_d = Y_BACK - Y_FRONT
    car_yc = (Y_BACK + Y_FRONT) / 2
    car_h = TOP_Z0 - PLINTH_H
    car_zc = PLINTH_H + car_h / 2
    for sx in (-1, 1):
        kit.box((SIDE_T, car_d, car_h), (sx * (CX - SIDE_T / 2), car_yc, car_zc), TEAK,
                bevel=0.0025, segments=1, name="side panel")
    inner = CX - SIDE_T
    # Bottom panel (its front edge is the bottom rail) and top rail.
    kit.box((2 * inner, car_d, 0.020), (0, car_yc, PLINTH_H + 0.010), TEAK, bevel=0.0, name="bottom rail")
    kit.box((2 * inner, 0.020, 0.020), (0, Y_FRONT + 0.010, TOP_Z0 - 0.010), TEAK, bevel=0.0, name="top rail")
    # Dark interior seen through the shut lines.
    z_lo, z_hi = PLINTH_H + 0.020, TOP_Z0 - 0.020
    kit.box((2 * inner - 0.002, Y_BACK - 0.03 - (Y_FRONT + 0.022), z_hi - z_lo),
            (0, (Y_BACK - 0.03 + Y_FRONT + 0.022) / 2, (z_lo + z_hi) / 2), BACK, bevel=0.0, name="interior shadow")

    # Overhanging top with a bullnose edge.
    top_y0, top_y1 = -D / 2, D / 2 - 0.002
    kit.box((W, top_y1 - top_y0, TOP_T), (0, (top_y0 + top_y1) / 2, TOP_Z0 + TOP_T / 2), TEAK,
            bevel=0.011, segments=3, name="top")

    # Recessed plinth: an open ring of boards, 30 mm back from the front,
    # standing on the floor; dark glue blocks in its corners.
    ph = PLINTH_H                  # floor to carcass: no seam under the bottom rail
    py = 0.018
    kit.frame((0.79, 0.41), (0.754, 0.374), ph, (0, py, ph / 2), TEAK,
              rot=(90, 0, 0), bevel=0.0, name="plinth")
    kit.box((0.76, 0.38, 0.004), (0, py, PLINTH_H - 0.004), BACK, bevel=0.0, name="plinth shadow")
    for sx in (-1, 1):
        for sy in (-1, 1):
            bx, by = sx * (0.377 - 0.0225), py + sy * (0.187 - 0.0225)
            kit.box((0.045, 0.045, 0.05), (bx, by, PLINTH_H - 0.004 - 0.025), BACK, bevel=0.0, name="glue block")

    # Back: hardboard panel set 2 mm into the rabbet, with the maker's label
    # (Prop_Label cell 11) 0.6 mm proud of its outer face (Y_BACK - 0.002).
    kit.box((2 * CX - 0.012, 0.005, car_h - 0.004), (0, Y_BACK - 0.0045, car_zc), BACK, bevel=0.0, name="back panel")
    kit.quad(0.11, 0.088, (0.21, Y_BACK - 0.0014, 0.95), LABEL, facing="+y", name="maker label",
             uv_rect=_label_rect(mirror=True))

    # --- Drawer rows (bottom to top) -------------------------------------
    rows = [0.302, 0.277, 0.252, 0.178]           # fills the 1.009 m stack
    z = PLINTH_H + 0.020
    ft = 0.019
    for k, h in enumerate(rows):
        zc = z + h / 2 + GAP
        if k < 3:
            kit.box((2 * inner - 2 * GAP, ft, h), (0, Y_FRONT + ft / 2, zc), TEAK,
                    bevel=0.003, segments=1, name="wide drawer front")
            for px in (-0.205, 0.205):
                _bail_pull(kit, px, zc + 0.012)
        else:
            stile = 0.016
            half = (2 * inner - stile) / 2
            for sx in (-1, 1):
                cxd = sx * (stile / 2 + half / 2)
                kit.box((half - 2 * GAP, ft, h), (cxd, Y_FRONT + ft / 2, zc), TEAK,
                        bevel=0.003, segments=1, name="small drawer front")
                _bail_pull(kit, cxd, zc + 0.008)
            kit.box((stile, 0.020, h + 2 * GAP), (0, Y_FRONT + 0.010, z + h / 2 + GAP), TEAK, bevel=0.0, name="stile")
        z += h + 2 * GAP
        if k < 3:
            kit.box((2 * inner, 0.020, RAIL), (0, Y_FRONT + 0.010, z + RAIL / 2), TEAK, bevel=0.0, name="face rail")
            z += RAIL

    # --- Metadata ----------------------------------------------------------
    kit.support("top", (0, 0, H), (W - 0.04, D - 0.04))
    kit.anchor("top", (0, 0, H))
    kit.collider((0, -0.0023, H / 2), (W, 0.4605, H))     # top + the pulls' 2.5 mm
    kit.tag("domestic", "case_goods", "pile", "pile_piece")
    kit.pile("Case", mass=3, palette="domestic70s", states=["Upright", "Back", "Front", "Side", "EdgeLean"])

    # Grain along each board (kitlib), each board on its own patch of veneer.
    grain.scatter_offsets(kit, seed=7031, slots=(TEAK,), tile=(1.0, 1.0))      # Teak TileSize 1.0 m
    grain.install(kit, SMOOTH_ANGLE)
