"""Glass-front snack vending machine, c. 1988-97 (National Vendors / AP 7000
class: black enamelled steel cabinet, a deep door with the product window on
the left and the money column on the right, a plain unlit black band above
the window, a push-flap delivery bin under the window, levelling feet).

The door is a 14 cm deep steel shell: its window opening is a recessed frame
whose inner walls run back to the cabinet front, so the snacks sit in real
depth behind a Prop_Glass sheet. The target office frame shows FOUR trays of
FOUR packets, so the product field is no longer one 6 x 6 card: each tray is
its own Prop_VendingFront decal quad 9 cm behind the glass, uv-mapped to four
columns of one row of the art (packets and coils, no price strip), standing
on a steel shelf whose front lip carries a lit price strip of the same art,
numbered in tray order (11-14 at the top down to 41-44). One tray combines
two-column halves of different art rows so the field is a mix; one slot is
sold out.

Real-world reference size: 0.90 m wide x 0.90 m deep overall (0.84 m door
face to back panel + cord) x 1.83 m tall. Window opening 0.62 x 1.135 m
(sill 0.565 m, as in the target), a 0.108 m unlit black band above it (the
target shows no lit header). Front faces -Y. Origin = floor, cabinet centre.

Budget pass (2026-10-02, §5.3: 4,000 + snack quads / 2,200 tris, <= 4 slots):
* Three slots: SteelBlack (cabinet, door, trim, shelves, money-column
  hardware, feet, cord; the brown trim, chrome and black plastic merge into
  it, matching the all-dark machine in the target), Glass and VendingFront
  (trays, price lips, and the column details uv-mapped into its art: keypad
  rows = runs of price labels, the selection display = a lit price, the lamp
  tube and bill-entry lamp = a blank lit label patch, the flap's PUSH plate =
  the art's PUSH lettering). The lit Prop_VendingHeader sign was removed:
  it is not in the target and would bloom in the office grade.
* Keys are four rows, not sixteen boxes; slots, screws, kick louvres, the
  key way and the rear serial plate (under 5 mm, black on black, or no
  honest art) are gone. The glass is a single quad so LOD1's collapse
  decimation cannot fold it. Decal quads sit 0.5-0.6 mm proud of their
  parent faces (no z-fighting on 24-bit depth).
* Previews: kit previews show flat slot colours; the decal mapping was
  checked with the real _A/_E textures at 2 m and 5 m (LOD1).
"""

NAME = "Kit_VendingMachine"
LOD1 = 0.42

BODY = "Prop_SteelBlack"
GLASS = "Prop_Glass"
FRONTART = "Prop_VendingFront"

W = 0.90
D = 0.84                 # door face to back panel; cord adds ~3 cm
H = 1.83
FY = -D / 2              # door front plane
DOOR_D = 0.14            # door shell depth
DOOR_BACK = FY + DOOR_D
BASE_Z = 0.05            # underside of cabinet (feet below)
SPLIT_Z = 0.52           # joint between lower door (bin) and upper door (window)

WX, WW = -0.10, 0.62                 # window centre x, width
WZ0, WZ1 = 0.565, 1.700              # window opening z
BZ = 0.022                           # bezel border round window and bin
CX, CW = 0.325, 0.16                 # money column centre x, width

# Prop_VendingFront art (1024 x 2048): 6 x 6 snack grid. Column c (1-based)
# spans x 59.5 + 151 (c - 1) .. + 151 px; row r's cell starts 86 + 272 (r - 1)
# px from the top, its packets + coils fill the first 214 px, its price strip
# (labels 331..354) lies at 325..358.
ART_W, ART_H = 1024.0, 2048.0


def _cols(a, b):
    return (59.5 + 151 * (a - 1)) / ART_W, (59.5 + 151 * b) / ART_W


def _rect(x0, y0, x1, y1):
    """Pixel box (top-left origin) -> uv_rect (bottom-left origin)."""
    return (x0 / ART_W, 1 - y1 / ART_H, x1 / ART_W, 1 - y0 / ART_H)


def _packets(r, a, b):
    u0, u1 = _cols(a, b)
    y0 = 86 + 272 * (r - 1)
    return (u0, 1 - (y0 + 214) / ART_H, u1, 1 - y0 / ART_H)


def _price_strip(r, a, b):
    u0, u1 = _cols(a, b)
    y0 = 325 + 272 * (r - 1)
    return (u0, 1 - (y0 + 33) / ART_H, u1, 1 - y0 / ART_H)


def _labels(r, a, b):
    """Only the cream labels of row r, columns a..b (keypad rows)."""
    y0 = 331 + 272 * (r - 1)
    return _rect(68 + 151 * (a - 1), y0, 68 + 151 * (b - 1) + 135, y0 + 23)


LIT_PATCH = _rect(189, 335, 199, 350)          # blank end of a price label (lit)
PRICE_LED = _rect(112, 331, 190, 354)          # "$0.65" on label 11
PUSH_TEXT = _rect(120, 1830, 265, 1875)        # the art's PUSH lettering
DARK_SLOT = _rect(300, 1880, 340, 1900)        # darkest field (coin slot)
STICKER = _rect(822, 603, 957, 626)            # label 26

# Trays, top to bottom: list of (art row, first col, last col) halves.
TRAYS = [
    [(1, 2, 5)],                 # SALTS ZESTO Mallo SALTS
    [(2, 1, 2), (3, 2, 3)],      # CRUNCHOS ZESTO | PRETZL NUTBAR
    [(6, 1, 4)],                 # Choco POPPS (sold out) Tater
    [(5, 3, 6)],                 # Mallo CRUNCHOS CRUNCHOS SALTS
]
TRAY_PITCH = 0.262
TRAY_Z0 = WZ0 + 0.045             # shelf top of the lowest tray


def _uv(obj, rect):
    obj["fr_uv_rect"] = list(rect)
    return obj


def build(kit):
    # ------------------------------------------------------------ cabinet
    carc_y0 = DOOR_BACK + 0.006          # shadow gap between door and cabinet
    # Levelling feet under the cabinet carcass (not under the hinged door).
    for x in (-W / 2 + 0.05, W / 2 - 0.05):
        for y in (carc_y0 + 0.05, D / 2 - 0.05):
            kit.cylinder(0.020, BASE_Z, (x, y, BASE_Z / 2), BODY, verts=8, bevel=0.0, name="foot")
    kit.box((W - 0.03, D - DOOR_D - 0.03, 0.012), (0, (DOOR_BACK + D / 2) / 2, BASE_Z + 0.006), BODY, bevel=0.0, name="base rail")
    kit.box((W, D / 2 - carc_y0, H - BASE_Z - 0.012), (0, (carc_y0 + D / 2) / 2, (BASE_Z + 0.012 + H) / 2), BODY,
            bevel=0.010, segments=2, name="cabinet")
    # Trim band round the top of the cabinet sides and back, kick band at
    # the floor, and pressed side / back skins (2 mm proud, bevelled) so the
    # big flanks catch a highlight along their edges.
    kit.box((W + 0.006, D / 2 - carc_y0 + 0.003, 0.040), (0, (carc_y0 + D / 2) / 2 + 0.0015, H - 0.060), BODY,
            bevel=0.004, segments=1, name="cabinet trim band")
    kit.box((W + 0.006, D / 2 - carc_y0 + 0.003, 0.050), (0, (carc_y0 + D / 2) / 2 + 0.0015, BASE_Z + 0.040), BODY,
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
    bin_w, bin_z0, bin_z1 = 0.56, 0.270, 0.465
    bin_cz = (bin_z0 + bin_z1) / 2
    kit.frame((W, lo_h), (bin_w, bin_z1 - bin_z0), DOOR_D, (0, FY + DOOR_D / 2, lo_cz), BODY,
              inner_offset=(WX, bin_cz - lo_cz), bevel=0.010, segments=2, name="lower door")
    # Rail between window and bin, over the door joint.
    kit.box((W - 0.01, 0.012, 0.026), (0, FY - 0.004, SPLIT_Z), BODY, bevel=0.004, segments=1, name="door rail")

    # Window: raised bezel, glass 22 mm in, gasket line.
    kit.frame((WW + 2 * BZ, WZ1 - WZ0 + 2 * BZ), (WW, WZ1 - WZ0), 0.014, (WX, FY - 0.004, w_cz), BODY,
              bevel=0.004, segments=2, name="window bezel")
    # The glass is a single quad, not a thin box: LOD1's
    # collapse decimation flattens a 6 mm box into coincident opposite faces.
    kit.quad(WW + 0.012, WZ1 - WZ0 + 0.012, (WX, FY + 0.021, w_cz), GLASS, facing="-y", uv="metres", name="window glass")
    kit.frame((WW + 0.004, WZ1 - WZ0 + 0.004), (WW - 0.010, WZ1 - WZ0 - 0.010), 0.006, (WX, FY + 0.017, w_cz), BODY,
              bevel=0.0, name="glazing gasket")

    # No header sign: in the target the band above the window (0.108 m here)
    # is the door's own unlit black steel; a lit red sign would be the most
    # saturated, blooming element in the desaturated office grade.

    # Fluorescent valance and tube across the top of the product field.
    kit.box((WW - 0.004, 0.05, 0.022), (WX, FY + 0.052, WZ1 - 0.011), BODY, bevel=0.003, segments=1, name="lamp valance")
    _uv(kit.cylinder(0.0125, WW - 0.06, (WX, FY + 0.07, WZ1 - 0.030), FRONTART, verts=8, rot=(0, 90, 0), bevel=0.0,
                     uv="decal", name="lamp tube"), LIT_PATCH)

    # ------------------------------------------------------ trays (4 x 4)
    wq = WW - 0.008                         # tray / product width
    hq = wq * 214.0 / 604.0                 # art aspect: four columns x one cell
    yq = FY + 0.11                          # packet plane, 88 mm behind the glass
    lip_y = FY + 0.050
    for k, halves in enumerate(TRAYS):
        zs = TRAY_Z0 + (len(TRAYS) - 1 - k) * TRAY_PITCH
        n = len(halves)
        for i, (r, a, b) in enumerate(halves):
            x = WX - wq / 2 + wq * (i + 0.5) / n
            kit.quad(wq / n, hq, (x, yq, zs + 0.002 + hq / 2), FRONTART, facing="-y", uv_rect=_packets(r, a, b), name="tray packets")
        # Selections numbered in tray order (11-14, 21-24, 31-34, 41-44) from
        # the art's first four price strips, whatever row the packets use.
        _uv(kit.box((wq + 0.004, 0.006, 0.036), (WX, lip_y, zs - 0.018), FRONTART, bevel=0.0, uv="decal", name="price lip"),
            _price_strip(k + 1, 1, 4))
        kit.box((wq + 0.004, yq - lip_y - 0.003, 0.004), (WX, (yq + lip_y + 0.003) / 2, zs - 0.002), BODY, bevel=0.0, name="shelf")

    # --------------------------------------------------------- delivery bin
    kit.frame((bin_w + 2 * BZ, bin_z1 - bin_z0 + 2 * BZ), (bin_w, bin_z1 - bin_z0), 0.014, (WX, FY - 0.004, bin_cz), BODY,
              bevel=0.004, segments=1, name="bin bezel")
    kit.box((bin_w + 0.02, 0.01, bin_z1 - bin_z0 + 0.02), (WX, DOOR_BACK - 0.02, bin_cz), BODY, bevel=0.0, name="bin back")
    kit.box((bin_w - 0.012, 0.008, bin_z1 - bin_z0 - 0.010), (WX, FY + 0.034, bin_cz + 0.002), BODY, bevel=0.003,
            segments=1, rot=(-3, 0, 0), name="push flap")
    kit.quad(0.11, 0.034, (WX - 0.17, FY + 0.0312, bin_z1 - 0.045), FRONTART, facing="-y", uv_rect=PUSH_TEXT, name="push plate")
    kit.box((bin_w - 0.012, 0.03, 0.006), (WX, FY + 0.015, bin_z0 + 0.003), BODY, bevel=0.0, name="bin sill")

    # Door hinges on the left edge.
    for z in (0.30, 1.55):
        kit.cylinder(0.011, 0.09, (-W / 2 + 0.004, FY + 0.012, z), BODY, verts=8, bevel=0.0, name="door hinge")

    # -------------------------------------------------------- money column
    col_z0, col_z1 = WZ0 + 0.03, WZ1
    front = FY - 0.005                      # column panel face
    kit.box((CW, 0.006, col_z1 - col_z0), (CX, FY - 0.002, (col_z0 + col_z1) / 2), BODY, bevel=0.003, segments=1, name="column panel")
    # Selection display: a lit price readout in a black bezel.
    kit.box((0.12, 0.012, 0.050), (CX, FY - 0.008, 1.620), BODY, bevel=0.004, segments=1, name="display bezel")
    kit.quad(0.096, 0.026, (CX, FY - 0.0146, 1.620), FRONTART, facing="-y", uv_rect=PRICE_LED, name="display window")
    # Selection keypad: four rows of four lit keys on a black plate, the
    # same labels as the price lips (11-14 on top .. 41-44 at the bottom).
    kp_z = 1.450
    kit.box((0.135, 0.008, 0.150), (CX, FY - 0.006, kp_z), BODY, bevel=0.003, segments=1, name="keypad plate")
    for i, r in enumerate((4, 3, 2, 1)):
        _uv(kit.box((0.122, 0.006, 0.024), (CX, FY - 0.0125, kp_z - 0.048 + i * 0.032), FRONTART, bevel=0.0,
                    uv="decal", name="key row"), _labels(r, 1, 4))
    # Coin entry plate, coin return.
    cz = 1.300
    kit.box((0.055, 0.008, 0.085), (CX - 0.032, FY - 0.006, cz), BODY, bevel=0.003, segments=1, name="coin plate")
    kit.quad(0.004, 0.030, (CX - 0.032, FY - 0.0106, cz + 0.010), FRONTART, facing="-y", uv_rect=DARK_SLOT, name="coin slot")
    kit.box((0.040, 0.008, 0.050), (CX + 0.042, FY - 0.006, cz), BODY, bevel=0.003, segments=1, name="return bezel")
    kit.cylinder(0.013, 0.012, (CX + 0.042, FY - 0.012, cz), BODY, verts=10, rot=(90, 0, 0), bevel=0.0, name="coin return button")
    # Bill acceptor with a sloped mouth and its lit entry lamp; a price sticker.
    bz = 1.130
    kit.box((0.11, 0.034, 0.14), (CX, FY - 0.017, bz), BODY, bevel=0.006, segments=1, name="bill acceptor")
    kit.box((0.09, 0.018, 0.034), (CX, FY - 0.036, bz + 0.045), BODY, bevel=0.004, segments=1, rot=(20, 0, 0), name="bill mouth")
    kit.quad(0.06, 0.018, (CX, FY - 0.0345, bz - 0.030), FRONTART, facing="-y", uv_rect=LIT_PATCH, name="bill lamp")
    kit.quad(0.09, 0.03, (CX, front - 0.0006, bz - 0.120), FRONTART, facing="-y", uv_rect=STICKER, name="bill sticker")
    # Coin return cup: a proud hood with ~30 mm of depth and a sloped floor.
    cup_z = 0.780
    kit.frame((0.10, 0.09), (0.075, 0.065), 0.035, (CX, FY - 0.0225, cup_z), BODY, bevel=0.003, segments=1, name="coin cup")
    kit.box((0.075, 0.032, 0.006), (CX, FY - 0.022, cup_z - 0.029), BODY, bevel=0.0, rot=(-10, 0, 0), name="coin cup floor")
    # T-handle lock.
    kit.cylinder(0.019, 0.024, (W / 2 - 0.045, FY - 0.006, 0.66), BODY, verts=12, rot=(90, 0, 0), bevel=0.0, name="lock barrel")

    # --------------------------------------------------------------- back
    by = D / 2
    # Compressor / lamp-ballast louvres (the serial plate is gone: the art
    # has no plate, and a price label on the back read wrong).
    for k in range(6):
        kit.box((0.50, 0.006, 0.010), (0, by + 0.004, 1.45 + k * 0.03), BODY, bevel=0.0, rot=(-30, 0, 0), name="rear louvre")
    kit.box((0.06, 0.024, 0.05), (0.30, by + 0.010, 0.20), BODY, bevel=0.0, name="cord strain relief")
    kit.tube([(0.30, by + 0.016, 0.19), (0.30, by + 0.022, 0.17), (0.302, by + 0.024, 0.10), (0.305, by + 0.024, 0.03),
              (0.315, by + 0.022, 0.005), (0.36, by + 0.020, 0.005), (0.41, by + 0.016, 0.005)], 0.005, BODY, verts=5, name="power cord")

    # --------------------------------------------------------------- meta
    kit.support("top", (0, 0.0, H), (W - 0.02, D - 0.02))
    kit.anchor("keypad", (CX, FY - 0.02, kp_z))
    kit.anchor("delivery", (WX, FY - 0.02, bin_cz))
    kit.anchor("window", (WX, FY - 0.02, w_cz))
    kit.collider((0, 0, H / 2), (W, D, H))
    kit.tag("office", "wall_unit")
    kit.pile("Case", mass=3, states=["Upright", "Back"])
