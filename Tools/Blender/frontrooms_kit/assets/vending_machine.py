"""Glass-front snack vending machine, c. 1988-97 (National Vendors / AP 7000
class: black enamelled steel cabinet, brown-anodised trim, a deep door with
the product window on the left and the money column on the right, push-flap
delivery bin under the window, levelling feet).

The door is a 14 cm deep steel shell: its window opening is a recessed frame
whose inner walls run back to the product field (the Prop_VendingFront decal,
1:2 art, lit by its own emission map) so the snacks sit in real depth behind
a Prop_Glass sheet. The decal card is 0.70 x 1.467 m (art squeezed 4.6 %
across, not stretched in height): its lower ~15 % (the "PUSH" part of the
art) sits below the window, hidden by the door rail and the lowest shelf, and
its dark side margins tuck behind the door stiles, so all six snack rows and
columns show in the full 1.25 m window. The modelled push flap below takes
over the PUSH job.

Real-world reference size: 0.90 m wide x 0.90 m deep overall (0.84 m door
face to back panel + bill acceptor and cord) x 1.83 m tall. Window opening
0.62 x 1.25 m. Front faces -Y. Origin = floor, cabinet centre.
"""

NAME = "Kit_VendingMachine"

BODY = "Prop_SteelBlack"
TRIM = "Prop_SteelBrown"
CHROME = "Prop_Chrome"
BLACK = "Prop_PlasticBlack"
GREY = "Prop_PlasticGrey"
WHITE = "Prop_PlasticWhite"
GLASS = "Prop_Glass"
DARKGLASS = "Prop_GlassCRT"
PAPER = "Prop_Paper"
ALU = "Prop_Aluminium"
RUBBER = "Prop_Rubber"

W = 0.90
D = 0.84                 # door face to back panel; bill acceptor and cord add ~7 cm
H = 1.83
FY = -D / 2              # door front plane
DOOR_D = 0.14            # door shell depth
DOOR_BACK = FY + DOOR_D  # -0.31
BASE_Z = 0.05            # underside of cabinet (feet below)
SPLIT_Z = 0.44           # joint between lower door (bin) and upper door (window)

WX, WW = -0.10, 0.62                 # window centre x, width
WZ0, WZ1 = 0.485, 1.735              # window opening z (1.25 m)
BZ = 0.022                           # trim bezel border round window and bin
CX, CW = 0.325, 0.16                 # money column centre x, width
COL_DZ = 0.045                       # money-column furniture lift (window grew upward)


def _foot(kit, x, y):
    kit.cylinder(0.026, 0.010, (x, y, 0.005), RUBBER, verts=16, bevel=0.003, segments=1, name="foot pad")
    kit.cylinder(0.016, 0.012, (x, y, 0.016), CHROME, verts=6, bevel=0.0015, segments=1, name="foot nut")
    kit.cylinder(0.0075, 0.030, (x, y, 0.036), CHROME, verts=10, bevel=0.0, name="foot stem")


def build(kit):
    # ------------------------------------------------------------ cabinet
    carc_y0 = DOOR_BACK + 0.006          # shadow gap between door and cabinet
    # Levelling feet under the cabinet carcass (not under the hinged door).
    for x in (-W / 2 + 0.05, W / 2 - 0.05):
        for y in (carc_y0 + 0.05, D / 2 - 0.05):
            _foot(kit, x, y)
    kit.box((W - 0.03, D - DOOR_D - 0.03, 0.012), (0, (DOOR_BACK + D / 2) / 2, BASE_Z + 0.006), BODY, bevel=0.003, segments=1, name="base rail")
    kit.box((W, D / 2 - carc_y0, H - BASE_Z - 0.012), (0, (carc_y0 + D / 2) / 2, (BASE_Z + 0.012 + H) / 2), BODY,
            bevel=0.010, segments=2, name="cabinet")
    # Brown trim band wrapping the top of the cabinet sides and back.
    kit.box((W + 0.006, D / 2 - carc_y0 + 0.003, 0.040), (0, (carc_y0 + D / 2) / 2 + 0.0015, H - 0.060), TRIM,
            bevel=0.004, segments=1, name="cabinet trim band")

    # Matching kick band at the floor, and pressed side / back skins (2 mm
    # proud, bevelled) so the big flanks catch a highlight along their edges.
    kit.box((W + 0.006, D / 2 - carc_y0 + 0.003, 0.050), (0, (carc_y0 + D / 2) / 2 + 0.0015, BASE_Z + 0.040), TRIM,
            bevel=0.004, segments=1, name="cabinet kick band")
    side_y0, side_y1 = carc_y0 + 0.04, D / 2 - 0.04
    side_z0, side_z1 = BASE_Z + 0.10, H - 0.11
    for sx in (-1, 1):
        kit.box((0.006, side_y1 - side_y0, side_z1 - side_z0), (sx * (W / 2 - 0.001), (side_y0 + side_y1) / 2, (side_z0 + side_z1) / 2),
                BODY, bevel=0.0025, segments=1, name="side skin")
    kit.box((W - 0.08, 0.006, side_z1 - side_z0), (0, D / 2 - 0.001, (side_z0 + side_z1) / 2), BODY, bevel=0.0025, segments=1, name="back skin")

    # --------------------------------------------------------------- door
    up_h = H - SPLIT_Z
    up_cz = (SPLIT_Z + H) / 2
    w_cz = (WZ0 + WZ1) / 2
    kit.frame((W, up_h), (WW, WZ1 - WZ0), DOOR_D, (0, FY + DOOR_D / 2, up_cz), BODY,
              inner_offset=(WX, w_cz - up_cz), bevel=0.010, segments=2, name="upper door")
    lo_h = SPLIT_Z - BASE_Z
    lo_cz = (BASE_Z + SPLIT_Z) / 2
    bin_w, bin_z0, bin_z1 = 0.56, 0.205, 0.395
    bin_cz = (bin_z0 + bin_z1) / 2
    kit.frame((W, lo_h), (bin_w, bin_z1 - bin_z0), DOOR_D, (0, FY + DOOR_D / 2, lo_cz), BODY,
              inner_offset=(WX, bin_cz - lo_cz), bevel=0.010, segments=2, name="lower door")

    # Window: brown bezel, glass 22 mm in, product field at the back.
    kit.frame((WW + 2 * BZ, WZ1 - WZ0 + 2 * BZ), (WW, WZ1 - WZ0), 0.014, (WX, FY - 0.004, w_cz), TRIM,
              bevel=0.004, segments=2, name="window bezel")
    kit.box((WW + 0.012, 0.006, WZ1 - WZ0 + 0.012), (WX, FY + 0.022, w_cz), GLASS, bevel=0.0, name="window glass")
    # Card: top of the art at the window head; the lowest price strip lands
    # 25 mm above the window sill so the PUSH band stays below the sill. The
    # card is shifted right so its left edge stays 15 mm inside the cabinet
    # flank (it would show in the door / cabinet shadow gap otherwise).
    q_top = WZ1 + 0.005
    q_h = (q_top - (WZ0 + 0.025)) / 0.8384
    q_w = 0.70
    q_x = -W / 2 + 0.015 + q_w / 2
    kit.quad(q_w, q_h, (q_x, DOOR_BACK + 0.003, q_top - q_h / 2), "Prop_VendingFront", facing="-y", name="product field")
    # Product shelves: steel trays with chrome price-channel lips, their
    # tops on the bottom edge of each painted price strip (measured from the
    # art: strip bottoms at 17.5 / 30.8 / 44.0 / 57.3 / 70.6 / 83.8 % down),
    # so the snacks stand on real depth behind the glass.
    card_y = DOOR_BACK + 0.003
    shelf_front = FY + 0.050
    shelf_d = card_y - shelf_front
    for f in (0.1748, 0.3076, 0.4404, 0.5728, 0.7056, 0.8384):
        zs = q_top - f * q_h
        kit.box((WW - 0.004, shelf_d, 0.004), (WX, (card_y + shelf_front) / 2, zs - 0.002), BODY, bevel=0.0, name="shelf tray")
        kit.box((WW - 0.004, 0.004, 0.016), (WX, shelf_front - 0.002, zs - 0.004), CHROME, bevel=0.0015, segments=1, name="shelf lip")
    # Fluorescent valance across the top of the product field.
    kit.box((WW - 0.004, 0.05, 0.022), (WX, FY + 0.052, WZ1 - 0.011), BODY, bevel=0.003, segments=1, name="lamp valance")
    kit.cylinder(0.0125, WW - 0.06, (WX, FY + 0.07, WZ1 - 0.030), WHITE, verts=10, rot=(0, 90, 0), bevel=0.0, name="lamp tube")
    # Glazing beads (rubber gasket line where glass meets the bezel).
    kit.frame((WW + 0.004, WZ1 - WZ0 + 0.004), (WW - 0.010, WZ1 - WZ0 - 0.010), 0.006, (WX, FY + 0.017, w_cz), RUBBER,
              bevel=0.0, name="glazing gasket")

    # Header above the window: recessed sign panel with a chrome script bar.
    # Dark gloss sign glass (until a lit Prop_VendingHeader decal exists).
    hz0, hz1 = WZ1 + BZ + 0.003, H - 0.026
    hz = (hz0 + hz1) / 2
    kit.box((W - 0.06, 0.006, hz1 - hz0), (0, FY - 0.001, hz), DARKGLASS, bevel=0.003, segments=1, name="header panel")
    kit.box((0.22, 0.006, 0.022), (WX, FY - 0.004, hz), CHROME, bevel=0.002, segments=1, name="header badge")
    kit.box((W - 0.03, 0.010, 0.012), (0, FY - 0.003, H - 0.012), TRIM, bevel=0.003, segments=1, name="door top trim")

    # Rail between window and bin: brown trim strip over the door joint.
    kit.box((W - 0.01, 0.012, 0.026), (0, FY - 0.004, SPLIT_Z), TRIM, bevel=0.004, segments=1, name="door rail trim")

    # --------------------------------------------------------- delivery bin
    kit.frame((bin_w + 2 * BZ, bin_z1 - bin_z0 + 2 * BZ), (bin_w, bin_z1 - bin_z0), 0.014, (WX, FY - 0.004, bin_cz), TRIM,
              bevel=0.004, segments=2, name="bin bezel")
    kit.box((bin_w + 0.02, 0.01, bin_z1 - bin_z0 + 0.02), (WX, DOOR_BACK - 0.02, bin_cz), BLACK, bevel=0.0, name="bin back")
    kit.box((bin_w - 0.012, 0.008, bin_z1 - bin_z0 - 0.010), (WX, FY + 0.034, bin_cz + 0.002), BLACK, bevel=0.003,
            segments=1, rot=(-3, 0, 0), name="push flap")
    kit.cylinder(0.005, bin_w - 0.01, (WX, FY + 0.030, bin_z1 - 0.004), CHROME, verts=8, rot=(0, 90, 0), bevel=0.0, name="flap hinge rod")
    kit.box((0.11, 0.003, 0.034), (WX - 0.17, FY + 0.0285, bin_z1 - 0.045), ALU, bevel=0.0008, segments=1, rot=(-3, 0, 0), name="push plate")
    kit.box((bin_w - 0.012, 0.03, 0.006), (WX, FY + 0.015, bin_z0 + 0.003), CHROME, bevel=0.002, segments=1, name="bin sill")

    # Kick plate with intake louvres.
    for k in range(4):
        kit.box((0.70, 0.004, 0.008), (0, FY - 0.0005, BASE_Z + 0.035 + k * 0.022), BLACK, bevel=0.0, name="kick louvre")

    # Door hinges on the left edge.
    for z in (0.30, 1.55):
        kit.cylinder(0.011, 0.09, (-W / 2 + 0.004, FY + 0.012, z), CHROME, verts=10, bevel=0.002, segments=1, name="door hinge")

    # -------------------------------------------------------- money column
    col_z0, col_z1 = WZ0 + 0.03, WZ1
    kit.box((CW, 0.006, col_z1 - col_z0), (CX, FY - 0.002, (col_z0 + col_z1) / 2), TRIM, bevel=0.003, segments=1, name="column panel")
    # Selection display.
    kit.box((0.12, 0.012, 0.050), (CX, FY - 0.008, 1.615 + COL_DZ), BLACK, bevel=0.004, segments=1, name="display bezel")
    kit.box((0.096, 0.004, 0.026), (CX, FY - 0.0145, 1.615 + COL_DZ), DARKGLASS, bevel=0.0, name="display window")
    # Instruction / price card.
    kit.box((0.13, 0.002, 0.10), (CX, FY - 0.0058, 1.505 + COL_DZ), PAPER, bevel=0.0, name="instruction card")
    kit.box((0.136, 0.004, 0.106), (CX, FY - 0.0045, 1.505 + COL_DZ), BLACK, bevel=0.001, segments=1, name="card frame")
    # Selection keypad: 4 x 4 square keys on a black plate.
    kit.box((0.135, 0.008, 0.155), (CX, FY - 0.006, 1.335 + COL_DZ), BLACK, bevel=0.003, segments=1, name="keypad plate")
    for r in range(4):
        for c in range(4):
            kit.box((0.024, 0.010, 0.024), (CX - 0.045 + c * 0.030, FY - 0.012, 1.29 + COL_DZ + r * 0.032 - 0.003), WHITE,
                    bevel=0.0025, segments=1, name="key")
    # Coin slot plate + coin return button.
    kit.box((0.055, 0.008, 0.085), (CX - 0.032, FY - 0.006, 1.165 + COL_DZ), CHROME, bevel=0.003, segments=1, name="coin plate")
    kit.box((0.004, 0.006, 0.030), (CX - 0.032, FY - 0.0095, 1.175 + COL_DZ), BLACK, bevel=0.0, name="coin slot")
    kit.box((0.040, 0.008, 0.050), (CX + 0.042, FY - 0.006, 1.165 + COL_DZ), BLACK, bevel=0.003, segments=1, name="return bezel")
    kit.cylinder(0.013, 0.012, (CX + 0.042, FY - 0.012, 1.165 + COL_DZ), CHROME, verts=16, rot=(90, 0, 0), bevel=0.002, segments=1, name="coin return button")
    # Bill acceptor module with a sloped mouth.
    kit.box((0.11, 0.034, 0.14), (CX, FY - 0.017, 0.995 + COL_DZ), BLACK, bevel=0.006, segments=2, name="bill acceptor")
    kit.box((0.09, 0.018, 0.034), (CX, FY - 0.036, 1.040 + COL_DZ), GREY, bevel=0.004, segments=1, rot=(20, 0, 0), name="bill mouth")
    kit.box((0.072, 0.010, 0.004), (CX, FY - 0.044, 1.046 + COL_DZ), BLACK, bevel=0.0, rot=(20, 0, 0), name="bill slot")
    kit.box((0.06, 0.003, 0.018), (CX, FY - 0.0345, 0.965 + COL_DZ), DARKGLASS, bevel=0.0, name="bill lamp")
    kit.box((0.09, 0.002, 0.03), (CX, FY - 0.0035, 0.895 + COL_DZ), PAPER, bevel=0.0, name="bill sticker")
    # Coin return cup.
    # Coin return cup: a proud chrome hood on the column panel with ~30 mm
    # of visible depth, a black back and a sloped chrome floor.
    cup_z = 0.70
    kit.frame((0.10, 0.09), (0.075, 0.065), 0.035, (CX, FY - 0.0225, cup_z), CHROME, bevel=0.003, segments=1, name="coin cup")
    kit.box((0.08, 0.004, 0.07), (CX, FY - 0.007, cup_z), BLACK, bevel=0.0, name="coin cup back")
    kit.box((0.075, 0.032, 0.006), (CX, FY - 0.022, cup_z - 0.029), CHROME, bevel=0.002, segments=1, rot=(-10, 0, 0), name="coin cup floor")
    # T-handle lock.
    kit.cylinder(0.019, 0.024, (W / 2 - 0.045, FY - 0.006, 0.86), CHROME, verts=16, rot=(90, 0, 0), bevel=0.003, segments=1, name="lock barrel")
    kit.box((0.006, 0.006, 0.016), (W / 2 - 0.045, FY - 0.0185, 0.86), BLACK, bevel=0.0, name="key way")

    # --------------------------------------------------------------- back
    by = D / 2
    for k in range(8):
        kit.box((0.50, 0.004, 0.010), (0, by + 0.0035, 1.45 + k * 0.025), BLACK, bevel=0.0, name="rear louvre")
    kit.box((0.12, 0.0015, 0.07), (-0.25, by + 0.0028, 1.20), ALU, bevel=0.0, name="serial plate")
    for x in (-W / 2 + 0.03, W / 2 - 0.03):
        for z in (0.12, 0.95, H - 0.10):
            kit.cylinder(0.006, 0.003, (x, by + 0.0012, z), CHROME, verts=8, rot=(90, 0, 0), bevel=0.0, name="rear screw")
    kit.box((0.06, 0.024, 0.05), (0.30, by + 0.010, 0.20), BLACK, bevel=0.004, segments=1, name="cord strain relief")
    kit.tube([(0.30, by + 0.016, 0.19), (0.30, by + 0.022, 0.17), (0.302, by + 0.024, 0.10), (0.305, by + 0.024, 0.03),
              (0.315, by + 0.022, 0.005), (0.36, by + 0.020, 0.005), (0.41, by + 0.016, 0.005)], 0.005, BLACK, verts=8, name="power cord")

    # --------------------------------------------------------------- meta
    kit.support("top", (0, 0.0, H), (W - 0.02, D - 0.02))
    kit.anchor("keypad", (CX, FY - 0.02, 1.335 + COL_DZ))
    kit.anchor("delivery", (WX, FY - 0.02, bin_cz))
    kit.anchor("window", (WX, FY - 0.02, w_cz))
    kit.collider((0, 0, H / 2), (W, D, H))
    kit.tag("office", "wall_unit")
    kit.pile("Case", mass=3, states=["Upright", "Back", "EdgeLean"])
