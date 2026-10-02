"""1970s teak-veneer chest of drawers (the "tall 5-drawer chest" tipped 40
degrees onto its corner in A24 "Backrooms" Still A).

Real-world reference: mass-market mid-1970s American/Danish-export chest,
orange-grain teak veneer on particleboard, inset drawers between thin face
rails, recessed plinth, a 28 mm top that overhangs the carcass by 12 mm with a
rounded (bullnose) edge, brass bail pulls on stamped backplates, hardboard
back panel with a paper maker's label.

Wood grain: kitlib's metre UVs would run the DoorVeneer grain up the drawer
fronts; _pilecases_grain.install() makes it follow each board's length
(horizontal on drawer fronts, rails and top, vertical on sides and stile),
with a per-part offset so the drawer fronts do not share one sheet.

Size: 0.90 m wide, 0.45 m deep (top), 1.10 m tall. Drawers: 2 small side by
side on top, 3 wide graduated below. Front (drawer faces) looks -Y.
"""

import math

import _pilecases_grain as grain

NAME = "Kit_Dresser70s"
SMOOTH_ANGLE = 40.0            # 10-vert brass posts / bail tube render smooth

TEAK = "Prop_WoodTeak"
DARK = "Prop_WoodDark"
BRASS = "Prop_Brass"
BACK = "Prop_WoodDark"         # tempered hardboard; move to Prop_Hardboard when that slot exists

W, D, H = 0.90, 0.45, 1.10
SIDE_T = 0.018
CX = 0.438                     # outer half-width of the carcass
Y_FRONT = -0.212               # front edge of sides / rails / drawer faces
Y_BACK = 0.222
PLINTH_H = 0.075
TOP_T = 0.028
TOP_Z0 = H - TOP_T             # underside of the top
RAIL = 0.016                   # face rail between drawer rows
GAP = 0.0025                   # shut line each side of a drawer front


def _stadium(w, h, n=6):
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
                plane="xz", bevel=0.0009, segments=1, name="pull backplate")
    hx = span / 2
    post_len = 0.013
    for sx in (-1, 1):
        kit.cylinder(0.0042, post_len, (x + sx * hx, yf - 0.0025 - post_len / 2, z + 0.006), BRASS,
                     verts=10, rot=(90, 0, 0), bevel=0.0012, segments=1, name="pull post")
        kit.cylinder(0.0055, 0.003, (x + sx * hx, yf - 0.004, z + 0.006), BRASS,
                     verts=10, rot=(90, 0, 0), bevel=0.001, segments=1, name="post rosette")
    # The bail hangs from the post ends and rests its bottom on the plate.
    pts = []
    n = 10
    y_top = yf - 0.0025 - post_len + 0.003
    y_bot = yf - 0.0053                       # tube back touches the plate front
    pts.append((x - hx, yf - 0.0035, z + 0.006))
    for i in range(n + 1):
        a = math.pi + math.pi * i / n
        t = math.sin(a)                       # 0 .. -1 .. 0
        pts.append((x + hx * math.cos(a) * 1.0,
                    y_top + (y_bot - y_top) * (-t),
                    z + 0.006 + 0.022 * t))
    pts.append((x + hx, yf - 0.0035, z + 0.006))
    kit.tube(pts, 0.0028, BRASS, verts=10, name="pull bail")


def build(kit):
    # --- Carcass ---------------------------------------------------------
    car_d = Y_BACK - Y_FRONT
    car_yc = (Y_BACK + Y_FRONT) / 2
    car_h = TOP_Z0 - PLINTH_H
    car_zc = PLINTH_H + car_h / 2
    for sx in (-1, 1):
        kit.box((SIDE_T, car_d, car_h), (sx * (CX - SIDE_T / 2), car_yc, car_zc), TEAK,
                bevel=0.0025, segments=2, name="side panel")
    inner = CX - SIDE_T
    # Bottom panel (its front edge is the bottom rail) and top rail.
    kit.box((2 * inner, car_d, 0.020), (0, car_yc, PLINTH_H + 0.010), TEAK, bevel=0.002, name="bottom rail")
    kit.box((2 * inner, 0.020, 0.020), (0, Y_FRONT + 0.010, TOP_Z0 - 0.010), TEAK, bevel=0.002, name="top rail")
    # Dark interior seen through the shut lines.
    z_lo, z_hi = PLINTH_H + 0.020, TOP_Z0 - 0.020
    kit.box((2 * inner - 0.002, Y_BACK - 0.03 - (Y_FRONT + 0.022), z_hi - z_lo),
            (0, (Y_BACK - 0.03 + Y_FRONT + 0.022) / 2, (z_lo + z_hi) / 2), DARK, bevel=0.0, name="interior shadow")

    # Overhanging top with a bullnose edge.
    top_y0, top_y1 = -D / 2, D / 2 - 0.002
    kit.box((W, top_y1 - top_y0, TOP_T), (0, (top_y0 + top_y1) / 2, TOP_Z0 + TOP_T / 2), TEAK,
            bevel=0.011, segments=4, name="top")

    # Recessed plinth: an open ring of boards, 30 mm back from the front.
    glide = 0.003
    ph = PLINTH_H - glide
    kit.frame((0.83, 0.40), (0.794, 0.364), ph, (0, 0.017, glide + ph / 2), TEAK,
              rot=(90, 0, 0), bevel=0.002, segments=1, name="plinth")
    kit.box((0.80, 0.37, 0.004), (0, 0.017, PLINTH_H - 0.004), DARK, bevel=0.0, name="plinth shadow")
    # Glue blocks in the plinth corners and nail-in nylon glides under them.
    for sx in (-1, 1):
        for sy in (-1, 1):
            bx, by = sx * (0.397 - 0.0225), 0.017 + sy * (0.182 - 0.0225)
            kit.box((0.045, 0.045, 0.05), (bx, by, PLINTH_H - 0.004 - 0.025), DARK, bevel=0.002, segments=1, name="glue block")
            kit.cylinder(0.011, glide, (sx * 0.404, 0.017 + sy * 0.189, glide / 2), "Prop_PlasticBlack",
                         verts=12, bevel=0.001, segments=1, name="glide")

    # Back: hardboard panel set 2 mm into the rabbet, with a maker's label.
    kit.box((2 * CX - 0.012, 0.005, car_h - 0.004), (0, Y_BACK - 0.0045, car_zc), BACK, bevel=0.001, name="back panel")
    # Back panel's outer face is at Y_BACK - 0.002; the paper label sits 0.6 mm proud of it.
    kit.quad(0.11, 0.07, (0.22, Y_BACK - 0.0014, 0.86), "Prop_Paper", facing="+y", name="maker label")
    # Wire brads round the hardboard edge, ~11 cm apart (seen when the chest lies on its front).
    bx, bz0, bz1 = CX - 0.016, PLINTH_H + 0.010, TOP_Z0 - 0.010
    for i in range(9):
        x = -bx + 2 * bx * i / 8
        for z in (bz0, bz1):
            kit.quad(0.004, 0.004, (x, Y_BACK - 0.0015, z), "Prop_PlasticBlack", facing="+y", uv="metres", name="back brad")
    for i in range(1, 9):
        z = bz0 + (bz1 - bz0) * i / 9
        for x in (-bx, bx):
            kit.quad(0.004, 0.004, (x, Y_BACK - 0.0015, z), "Prop_PlasticBlack", facing="+y", uv="metres", name="back brad")

    # --- Drawer rows (bottom to top) -------------------------------------
    rows = [0.266, 0.244, 0.222, 0.157]
    z = PLINTH_H + 0.020
    ft = 0.019
    for k, h in enumerate(rows):
        zc = z + h / 2 + GAP
        if k < 3:
            kit.box((2 * inner - 2 * GAP, ft, h), (0, Y_FRONT + ft / 2, zc), TEAK,
                    bevel=0.003, segments=2, name="wide drawer front")
            for px in (-0.215, 0.215):
                _bail_pull(kit, px, zc + 0.012)
        else:
            stile = 0.016
            half = (2 * inner - stile) / 2
            for sx in (-1, 1):
                cxd = sx * (stile / 2 + half / 2)
                kit.box((half - 2 * GAP, ft, h), (cxd, Y_FRONT + ft / 2, zc), TEAK,
                        bevel=0.003, segments=2, name="small drawer front")
                _bail_pull(kit, cxd, zc + 0.008)
            kit.box((stile, 0.020, h + 2 * GAP), (0, Y_FRONT + 0.010, z + h / 2 + GAP), TEAK, bevel=0.002, name="stile")
        z += h + 2 * GAP
        if k < 3:
            kit.box((2 * inner, 0.020, RAIL), (0, Y_FRONT + 0.010, z + RAIL / 2), TEAK, bevel=0.002, name="face rail")
            z += RAIL

    # --- Metadata ----------------------------------------------------------
    kit.support("top", (0, 0, H), (0.86, 0.42))
    kit.anchor("top", (0, 0, H))
    kit.collider((0, 0, PLINTH_H + (H - PLINTH_H) / 2), (W, D, H - PLINTH_H))
    kit.collider((0, 0.017, PLINTH_H / 2), (0.83, 0.40, PLINTH_H))
    kit.tag("domestic", "case_goods", "pile", "pile_piece")
    kit.pile("Case", mass=3, palette="domestic70s", states=["Upright", "Back", "Side", "EdgeLean"])

    # Grain along each board, and each board on its own patch of veneer.
    grain.scatter_offsets(kit, seed=7031, slots=(TEAK,))
    grain.install(kit)
