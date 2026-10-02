"""1990s open-plan office desk: almond laminate worksurface on a dark-brown
painted steel tube frame with a free-standing box/box/file pedestal (the desk
in Red's target office image, left foreground).

Real-world reference: the 30" x 60" "steel-frame pedestal desk" sold by every
contract dealer c. 1985-98 (Steelcase/Hon/Global clones). 1.524 m wide,
0.762 m deep, worksurface at 0.74 m (29"), 30 mm particleboard top in
high-pressure laminate with a dark PVC T-mould edge (2-3 mm rounded lip seen
from above) and a kraft backer sheet underneath. Frame: 40 mm square legs
on screw-in levelling glides, 25 x 50 mm rails under the top, foot rails at
both ends, a pressed-steel modesty panel with two stiffening beads at the
back (+Y). Every frame member runs up into the underside of the top. Right-hand
pedestal 0.38 W x 0.56 D x 0.71 H (carcass top meets the top's underside)
with two 150 mm box drawers and a 350 mm file drawer, recessed pulls, a lock
in the top drawer and a card holder. Painted almond, a touch lighter and
cooler than the laminate top.

Front (user side, knee space, drawer faces) faces -Y. User's left = -X.

Slot requests: Prop_PVCEdge (T-mould, now Prop_WoodDark), Prop_Backer (now
Prop_Cardboard), Prop_SteelAlmond (pedestal, now Prop_PlasticBeige).
"""

NAME = "Kit_OfficeDesk"

LAM = "Prop_LaminateBeige"
PED = "Prop_PlasticBeige"       # pedestal paint until Prop_SteelAlmond exists
EDGE = "Prop_WoodDark"          # non-metallic T-mould until Prop_PVCEdge exists
BACKER = "Prop_Cardboard"       # kraft backer until Prop_Backer exists
STEEL = "Prop_SteelBrown"
DARK = "Prop_PlasticGrey"
BLACK = "Prop_PlasticBlack"
CHROME = "Prop_Chrome"
ALU = "Prop_Aluminium"
LABEL = "Prop_Label"

W, D = 1.524, 0.762
TOP = 0.74
TOP_T = 0.030

LEG = 0.040                     # square leg tube
LEG_X = W / 2 - 0.030 - LEG / 2  # 30 mm overhang at the ends
LEG_Y = D / 2 - 0.030 - LEG / 2  # 30 mm overhang front and back
LEG_Z0 = 0.018                  # leg bottom (glide underneath)
CORE_T = TOP_T - 0.0015         # laminate core (T-mould stands 1 mm proud)
CORE_UNDER = TOP - CORE_T       # 0.7115, underside of the core
UNDER = CORE_UNDER + 0.0005     # frame members end 0.5 mm inside the core

# Pedestal footprint (right end, inside the right legs). Its carcass top
# meets the core's underside (0.2 % over the 0.71 spec).
P_W, P_D, P_H = 0.38, 0.56, CORE_UNDER
P_X1 = LEG_X - LEG / 2 - 0.010
P_X0 = P_X1 - P_W
P_CX = (P_X0 + P_X1) / 2
P_FRONT = -LEG_Y - LEG / 2       # flush with the front legs
P_CY = P_FRONT + P_D / 2


def _top(kit):
    # Laminate core and the T-mould band wrapped round it (one closed ring,
    # rounded, 1 mm proud of the laminate on top). The ring laps 1 mm over
    # the core edge, so from above only a 2-3 mm rounded dark lip shows.
    kit.box((W - 0.006, D - 0.006, CORE_T), (0, 0, TOP - CORE_T / 2), LAM,
            bevel=0.0015, segments=1, name="worksurface")
    kit.frame((W, D), (W - 0.008, D - 0.008), TOP_T + 0.001, (0, 0, TOP - TOP_T / 2 + 0.0005), EDGE,
              rot=(90, 0, 0), bevel=0.0035, segments=3, name="t-mould edge")
    # Kraft backer sheet on the underside (seen when crouching or on an
    # inverted pile desk), running out to 1 mm inside the T-mould's inner
    # edge so no beige band shows. Frame tops pass through it into the core.
    kit.box((W - 0.010, D - 0.010, 0.0008), (0, 0, CORE_UNDER - 0.0004), BACKER, bevel=0.0, name="backer")
    # Flush cable grommet, back left (where the CRT cords drop): black rim
    # 0.8 mm proud, a dark cap with a printed cable slot.
    gx, gy = -0.47, 0.285
    rim = [(0.024, TOP - 0.0005), (0.0335, TOP - 0.0005), (0.0345, TOP + 0.0003), (0.0330, TOP + 0.0008),
           (0.0255, TOP + 0.0008), (0.0238, TOP + 0.0003), (0.024, TOP - 0.0005)]
    kit.lathe(rim, (gx, gy, 0), BLACK, verts=24, close_top=False, close_bottom=False, name="grommet rim")
    kit.cylinder(0.0245, 0.0012, (gx, gy, TOP + 0.0001), DARK, verts=24, bevel=0.0004, segments=1, name="grommet cap")
    kit.quad(0.026, 0.007, (gx, gy + 0.012, TOP + 0.0008), BLACK, facing="+z", name="grommet cable slot")
    # The grommet's sleeve lip under the top, seen from below.
    kit.cylinder(0.0275, 0.003, (gx, gy, CORE_UNDER - 0.001), BLACK, verts=16, bevel=0.0008, segments=1, name="grommet sleeve")


def _frame(kit):
    leg_h = UNDER - LEG_Z0
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * LEG_X, sy * LEG_Y
            kit.box((LEG, LEG, leg_h), (x, y, LEG_Z0 + leg_h / 2), STEEL, bevel=0.004, segments=2, name="leg")
            # Screw-in levelling glide: black foot, steel stem, end plug.
            kit.cylinder(0.017, 0.010, (x, y, 0.005), BLACK, verts=16, bevel=0.003, segments=2, name="glide foot")
            kit.cylinder(0.0055, 0.010, (x, y, 0.014), CHROME, verts=10, bevel=0.0, name="glide stem")
            kit.box((LEG - 0.006, LEG - 0.006, 0.003), (x, y, LEG_Z0 - 0.001), BLACK, bevel=0.001, segments=1, name="leg plug")

    rail_len_y = 2 * LEG_Y - LEG
    rail_z = UNDER - 0.025
    for sx in (-1, 1):
        x = sx * LEG_X
        # End rail under the top and the foot rail: the panel-end frame.
        kit.box((0.025, rail_len_y, 0.050), (x, 0, rail_z), STEEL, bevel=0.003, segments=2, name="end rail")
        kit.box((0.025, rail_len_y, 0.035), (x, 0, 0.075), STEEL, bevel=0.003, segments=2, name="foot rail")
        # Knock-down bolts where the end rail meets each leg (outer face).
        for sy in (-1, 1):
            kit.cylinder(0.0065, 0.004, (x + sx * 0.0145, sy * (LEG_Y - 0.040), rail_z), STEEL, verts=6,
                         rot=(0, 90, 0), bevel=0.0008, segments=1, name="frame bolt")

    # Back rail (full length) and the front apron over the knee space only.
    kit.box((2 * LEG_X - LEG, 0.025, 0.050), (0, LEG_Y, rail_z), STEEL, bevel=0.003, segments=2, name="back rail")
    fx0, fx1 = -LEG_X + LEG / 2, P_X0 - 0.004
    kit.box((fx1 - fx0, 0.025, 0.045), ((fx0 + fx1) / 2, -LEG_Y + 0.004, UNDER - 0.0225), STEEL,
            bevel=0.003, segments=2, name="front apron")

    # Hat-channel cross brace under the top at mid-knee (front apron to back
    # rail) with its two top-fixing screws, seen when crouching under it.
    bx = -0.20
    by0, by1 = -LEG_Y + 0.017, LEG_Y - 0.0125
    kit.box((0.030, by1 - by0, 0.022), (bx, (by0 + by1) / 2, UNDER - 0.011), STEEL, bevel=0.002, segments=1, name="cross brace")
    for y in (by0 + 0.12, by1 - 0.12):
        kit.cylinder(0.005, 0.002, (bx, y, UNDER - 0.023), STEEL, verts=8, bevel=0.0005, segments=1, name="brace screw")

    # Pressed-steel modesty panel between the back legs, with two stiffening
    # beads and the four bolts that hang it from the legs.
    # The panel and its top hem tuck 2 mm up into the back rail (hidden inside
    # the rail's 25 mm thickness), so there is no see-through slit.
    mp_w = 2 * LEG_X - LEG - 0.004
    mp_z0, mp_z1 = 0.33, rail_z - 0.025 + 0.002
    mp_cz = (mp_z0 + mp_z1) / 2
    kit.box((mp_w, 0.008, mp_z1 - mp_z0), (0, LEG_Y + 0.002, mp_cz), STEEL, bevel=0.003, segments=2, name="modesty panel")
    # Folded hems along the top and bottom edges (formed sheet steel).
    for z in (mp_z0 + 0.008, mp_z1 - 0.008):
        kit.box((mp_w, 0.016, 0.016), (0, LEG_Y + 0.002, z), STEEL, bevel=0.006, segments=3, name="modesty hem")
    # Two pressed stiffening beads along the outer (+Y) face.
    for dz in (-0.07, 0.07):
        kit.box((mp_w - 0.08, 0.004, 0.012), (0, LEG_Y + 0.006 + 0.002, mp_cz + dz), STEEL,
                bevel=0.0015, segments=2, name="modesty bead")
    for sx in (-1, 1):
        for z in (mp_z0 + 0.04, mp_z1 - 0.04):
            kit.cylinder(0.006, 0.004, (sx * (mp_w / 2 - 0.022), LEG_Y + 0.002 - 0.0075, z), STEEL, verts=6,
                         rot=(90, 0, 0), bevel=0.0008, segments=1, name="modesty bolt")


def _drawer(kit, cz, h, name, lock=False, card=False):
    """One inset drawer front with a recessed full pull at the top."""
    fw = P_W - 2 * 0.016 - 2 * 0.003
    fy = P_FRONT - 0.002 + 0.010            # 2 mm proud of the carcass
    pull_w, pull_h = 0.240, 0.026
    pull_cz = cz + h / 2 - 0.014 - pull_h / 2
    kit.frame((fw, h), (pull_w, pull_h), 0.020, (P_CX, fy, cz), PED,
              inner_offset=(0, pull_cz - cz), bevel=0.003, segments=2, name=name)
    # Pull cup behind the opening and the finger lip hanging from its top.
    kit.box((pull_w + 0.006, 0.010, pull_h + 0.006), (P_CX, fy + 0.014, pull_cz), BLACK, bevel=0.0, name=name + " pull cup")
    kit.box((pull_w - 0.002, 0.003, 0.008), (P_CX, fy - 0.003, pull_cz + pull_h / 2 - 0.004), PED,
            bevel=0.001, segments=1, name=name + " pull lip")
    front = fy - 0.010
    if lock:
        lx = P_CX + pull_w / 2 + (fw / 2 - pull_w / 2) / 2
        kit.cylinder(0.0105, 0.004, (lx, front - 0.002, pull_cz), CHROME, verts=16, rot=(90, 0, 0),
                     bevel=0.0012, segments=2, name="lock collar")
        kit.cylinder(0.0075, 0.003, (lx, front - 0.0045, pull_cz), CHROME, verts=16, rot=(90, 0, 0),
                     bevel=0.0008, segments=1, name="lock plug")
        kit.box((0.0018, 0.002, 0.009), (lx, front - 0.0060, pull_cz), BLACK, bevel=0.0, name="keyway")
    if card:
        cz_card = pull_cz - pull_h / 2 - 0.045
        kit.frame((0.086, 0.036), (0.074, 0.026), 0.003, (P_CX, front - 0.0015, cz_card), ALU,
                  inner_offset=(0, 0.003), bevel=0.0008, segments=1, name="card holder")
        kit.quad(0.074, 0.026, (P_CX, front - 0.0007, cz_card + 0.003), LABEL, name="drawer card")


def _pedestal(kit):
    glide_h = 0.018
    body_h = P_H - glide_h
    cz = glide_h + body_h / 2
    wall = 0.016
    # Carcass: a closed sleeve (sides, top, bottom) with a back panel and a
    # dark void behind the drawer fronts so the shut lines read.
    kit.frame((P_W, body_h), (P_W - 2 * wall, body_h - 2 * wall), P_D, (P_CX, P_CY, cz), PED,
              bevel=0.004, segments=2, name="pedestal carcass")
    kit.box((P_W - 0.01, 0.010, body_h - 0.01), (P_CX, P_FRONT + P_D - 0.006, cz), PED, bevel=0.002, name="pedestal back")
    kit.box((P_W - 2 * wall + 0.002, 0.006, body_h - 2 * wall + 0.002), (P_CX, P_FRONT + 0.035, cz), BLACK,
            bevel=0.0, name="drawer void")
    # Box / box / file, 3 mm gaps (the last 3 mm is the top shut line).
    z0 = glide_h + wall + 0.003
    hs = (0.3495, 0.150, 0.150)
    names = ("file drawer", "box drawer 2", "box drawer 1")
    for i, (h, n) in enumerate(zip(hs, names)):
        _drawer(kit, z0 + h / 2, h, n, lock=(i == 2), card=(i == 0))
        z0 += h + 0.003
    # Levelling glides at the four corners.
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = P_CX + sx * (P_W / 2 - 0.028)
            y = P_CY + sy * (P_D / 2 - 0.030)
            kit.cylinder(0.015, 0.010, (x, y, 0.005), BLACK, verts=14, bevel=0.003, segments=2, name="pedestal glide")
            kit.cylinder(0.005, 0.009, (x, y, 0.0135), CHROME, verts=8, bevel=0.0, name="pedestal glide stem")
    # Mounting bracket tying the front apron to the pedestal side.
    kit.box((0.004, 0.034, 0.045), (P_X0 - 0.002, -LEG_Y + 0.004, UNDER - 0.0225), STEEL, bevel=0.001, name="apron bracket")


def build(kit):
    _top(kit)
    _frame(kit)
    _pedestal(kit)

    kit.support("top", (0, 0, TOP), (1.50, 0.74))
    kit.anchor("monitor", (-0.20, 0.08, TOP))
    kit.anchor("keyboard", (-0.20, -0.245, TOP))
    kit.anchor("chair", (-0.20, -0.62, 0.0))
    kit.collider((0, 0, (TOP + 0.001) / 2), (W, D, TOP + 0.001))
    kit.tag("office", "workstation")
    kit.pile("Table", mass=2, states=["Upright", "Inverted", "Side", "EdgeLean"])
