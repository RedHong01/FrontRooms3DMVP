"""Floor-standing office photocopier, c. 1992-98 (Canon NP / Xerox 50xx class:
an A4/A3 copier body with an in-body exit tray, on its two-cassette paper
pedestal with swivel casters).

Construction, bottom to top: four swivel casters under a grey plinth; a beige
pedestal with two paper cassettes (recessed grips, paper-level windows, size
cards); a grey accent band; the off-white engine body with its own cassette
and a drop-down front door (handle recesses, louvre, jam sticker); the in-body
exit: a 70 mm cavity between the engine top and the scanner, open to the front
and the right (+X) side, walled by the left column and a rear cover, with a
ribbed grey exit tray, the exit slot and roller on the column and a stack of
A4 copies; then the scanner unit, whose front is the sloped control console
carrying the CopierPanel decal (4:1 art: LCD, keypad, START), and a grey
document cover over the platen with rear hinges. Key counter, power switch and
the jam-access side door on the right flank, cooling louvres and a carrying
grip on the left, vents, a guarded fan and the power cord on the back.

Real-world reference size: 0.60 m wide body (0.63 m over the key counter and
grips), 0.56 m deep body (0.67 m over cassette grips, console lip and the
power cord on the floor), 1.14 m tall to the top of the cover hinges; the
body is wider than deep, as on the real machines and in the target office
image. Front (console, cassettes) faces -Y. Origin = floor, bounds centred on
x = y = 0 (the body sits 8 mm left of centre to balance the key counter).
"""

import math

NAME = "Kit_Copier"

WHITE = "Prop_PlasticWhite"
BEIGE = "Prop_PlasticBeige"
GREY = "Prop_PlasticGrey"
BLACK = "Prop_PlasticBlack"
RUBBER = "Prop_Rubber"
STEEL = "Prop_SteelPutty"
ALU = "Prop_Aluminium"
CHROME = "Prop_Chrome"
PAPER = "Prop_Paper"
DARKGLASS = "Prop_GlassCRT"

CX = -0.008           # body centre x
BW, BD = 0.60, 0.56   # body width / depth
FRONT = -BD / 2       # body front plane (y)
PED_Z0, PED_Z1 = 0.080, 0.440
BODY_Z0 = 0.452       # engine body underside
ENG_TOP = 0.858       # engine top = exit tray floor
SCAN_Z0 = 0.928       # underside of the scanner / platen unit (70 mm exit cavity)
BODY_Z1 = 1.092       # platen level
SEAM = 0.010          # dark shut line between engine frame and scanner
COLW = 0.11           # left column (holds the scanner, carries the exit slot)
SPD = 0.09            # rear cover depth behind the exit cavity


def _caster(kit, x, y):
    """Swivel caster: mounting plate (screwed to the plinth), swivel race,
    yoke, fork, rubber wheel."""
    top = PED_Z0
    kit.box((0.05, 0.05, 0.006), (x, y, top - 0.003), STEEL, bevel=0.0015, segments=1, name="caster plate")
    kit.cylinder(0.018, 0.010, (x, y, top - 0.011), STEEL, verts=12, bevel=0.002, segments=1, name="caster race")
    off = 0.012  # trailing offset of the wheel axle
    for s in (-1, 1):
        kit.box((0.004, 0.040, 0.044), (x + s * 0.0125, y + off, 0.040), STEEL, bevel=0.0015, segments=1, name="caster fork")
    kit.box((0.029, 0.024, 0.006), (x, y + 0.004, top - 0.019), STEEL, bevel=0.0015, segments=1, name="caster yoke")
    kit.cylinder(0.026, 0.018, (x, y + off, 0.026), RUBBER, verts=16, rot=(0, 90, 0), bevel=0.004, segments=1, name="caster wheel")
    kit.cylinder(0.006, 0.030, (x, y + off, 0.026), STEEL, verts=8, rot=(0, 90, 0), bevel=0.0, name="caster axle")


def _cassette(kit, z0, z1, width, y_face, slot, name):
    """Paper cassette front: face plate, recessed grip, paper-level window,
    size card. y_face = front plane of the face plate."""
    h = z1 - z0
    zc = (z0 + z1) / 2
    kit.box((width, 0.022, h), (CX, y_face + 0.011, zc), slot, bevel=0.006, segments=2, name=name + " face")
    # Grip: grey moulding with a dark finger slot under its lip.
    gz = z1 - 0.030
    gw = min(0.24, width * 0.42)
    kit.box((gw, 0.010, 0.030), (CX, y_face - 0.004, gz), GREY, bevel=0.004, segments=2, name=name + " grip")
    kit.box((gw - 0.02, 0.006, 0.010), (CX, y_face - 0.0085, gz - 0.006), BLACK, bevel=0.0, name=name + " grip slot")
    # Paper-level window (left): dark slit with a pointer.
    wx = CX - width / 2 + 0.040
    kit.box((0.014, 0.004, min(0.07, h - 0.05)), (wx, y_face - 0.001, zc - 0.006), BLACK, bevel=0.0, name=name + " level window")
    kit.box((0.012, 0.004, 0.006), (wx, y_face - 0.002, zc - 0.018), WHITE, bevel=0.0, name=name + " level pointer")
    # Paper-size card (right) in a little grey holder.
    sx = CX + width / 2 - 0.060
    kit.box((0.060, 0.004, 0.036), (sx, y_face - 0.0015, zc - 0.006), GREY, bevel=0.0015, segments=1, name=name + " card holder")
    kit.box((0.050, 0.002, 0.026), (sx, y_face - 0.0035, zc - 0.006), PAPER, bevel=0.0, name=name + " size card")


def build(kit):
    x0, x1 = CX - BW / 2, CX + BW / 2
    xc = x0 + COLW                      # inner face of the left column
    zt = SCAN_Z0 - SEAM                 # top of the engine frame (column / rear cover)
    by = BD / 2

    # ------------------------------------------------------------ pedestal
    for sx in (-1, 1):
        for sy in (-1, 1):
            _caster(kit, CX + sx * (BW / 2 - 0.055), sy * (BD / 2 - 0.065))
    PW, PD = BW - 0.02, BD - 0.04
    kit.box((PW, PD, 0.03), (CX, 0, PED_Z0 + 0.015), GREY, bevel=0.006, segments=2, name="plinth")
    ped_front = -PD / 2
    kit.box((PW, PD, PED_Z1 - PED_Z0 - 0.03), (CX, 0.0, (PED_Z0 + 0.03 + PED_Z1) / 2), BEIGE,
            bevel=0.010, segments=2, name="pedestal carcass")
    gap = 0.006
    z_mid = (PED_Z0 + 0.03 + PED_Z1) / 2
    cas_face = ped_front - 0.020        # face plates overlap the carcass by 2 mm
    _cassette(kit, PED_Z0 + 0.036, z_mid - gap / 2, BW - 0.04, cas_face, BEIGE, "cassette 3")
    _cassette(kit, z_mid + gap / 2, PED_Z1 - 0.006, BW - 0.04, cas_face, BEIGE, "cassette 2")
    kit.box((BW - 0.04, 0.012, 0.010), (CX, ped_front - 0.010, PED_Z0 + 0.034), GREY, bevel=0.002, segments=1, name="kick strip")

    # Grey accent band between pedestal and body.
    kit.box((BW - 0.004, BD - 0.004, BODY_Z0 - PED_Z1 + 0.004), (CX, 0, (PED_Z1 + BODY_Z0) / 2), GREY,
            bevel=0.004, segments=1, name="accent band")

    # ----------------------------------------------------------- main body
    # Engine body + left column as one L-section shell (no seam on the left
    # flank or the column front), extruded front to back. Triangulated so the
    # concave cap faces import cleanly.
    outline = [(x0, BODY_Z0), (x1, BODY_Z0), (x1, ENG_TOP), (xc, ENG_TOP), (xc, zt), (x0, zt)]
    eng = kit.extrude(outline, BD, (0, 0, 0), WHITE, plane="xz", bevel=0.012, segments=3, name="engine body")
    tri = eng.modifiers.new("tri", "TRIANGULATE")
    tri.min_vertices = 5
    # Rear cover closing the back of the exit cavity (a separate moulding,
    # 2 mm proud on the back and the right flank).
    kit.box((x1 + 0.002 - (x0 + 0.004), SPD + 0.002, zt - 0.001 - (ENG_TOP - 0.012)),
            ((x0 + 0.004 + x1 + 0.002) / 2, by - SPD / 2 + 0.001, (zt - 0.001 + ENG_TOP - 0.012) / 2), WHITE,
            bevel=0.008, segments=2, name="rear cover")
    # Dark shut line / scanner underside.
    kit.box((BW - 0.02, BD - 0.02, SEAM + 0.004), (CX, 0, zt + SEAM / 2), BLACK, bevel=0.0, name="scanner seam")

    # Scanner unit on top, 6 mm proud all round; its front is the console.
    console_y = FRONT + 0.16            # rear edge of the sloped console
    SW = BW + 0.012
    kit.box((SW, by + 0.006 - console_y, BODY_Z1 - SCAN_Z0), (CX, (console_y + by + 0.006) / 2, (SCAN_Z0 + BODY_Z1) / 2), WHITE,
            bevel=0.012, segments=3, name="scanner body")
    # Sloped console (side profile extruded across the width).
    (y0, z0), (y1, z1) = (FRONT - 0.004, 1.036), (FRONT + 0.138, 1.082)
    prof = [(FRONT - 0.012, SCAN_Z0), (FRONT - 0.012, 1.022), (y0, z0), (y1, z1), (console_y, 1.086), (console_y, SCAN_Z0)]
    kit.extrude(prof, SW, (CX, 0, 0), BEIGE, plane="yz", bevel=0.008, segments=2, name="console")
    # Decal panel on the slope + grey bezel.
    slope = math.atan2(z1 - z0, y1 - y0)
    ny, nz = -math.sin(slope), math.cos(slope)
    my, mz = (y0 + y1) / 2, (z0 + z1) / 2
    rot = (-(90 - math.degrees(slope)), 0, 0)
    kit.frame((0.500, 0.132), (0.480, 0.120), 0.004, (CX, my + ny * 0.0015, mz + nz * 0.0015), GREY,
              rot=rot, bevel=0.0012, segments=1, name="panel bezel")
    kit.box((0.480, 0.003, 0.120), (CX, my + ny * 0.0012, mz + nz * 0.0012), "Prop_CopierPanel",
            bevel=0.0, rot=rot, uv="decal", decal_axes="xz", name="control panel")
    # Front lip strip under the console (grey accent) with a brand badge.
    kit.box((SW - 0.004, 0.012, 0.022), (CX, FRONT - 0.014, SCAN_Z0 + 0.013), GREY, bevel=0.004, segments=1, name="console bumper")
    kit.box((0.085, 0.004, 0.018), (x0 + 0.075, FRONT - 0.0135, 0.988), ALU, bevel=0.0015, segments=1, name="badge")
    kit.box((0.05, 0.004, 0.010), (x1 - 0.065, FRONT - 0.0135, 0.988), GREY, bevel=0.001, segments=1, name="model plate")

    # Body cassette (tray 1) and the drop-down front door above it.
    _cassette(kit, BODY_Z0 + 0.012, BODY_Z0 + 0.112, BW - 0.03, FRONT - 0.020, BEIGE, "cassette 1")
    door_z0, door_z1 = BODY_Z0 + 0.122, ENG_TOP - 0.014
    kit.box((BW - 0.03, 0.014, door_z1 - door_z0), (CX, FRONT - 0.006, (door_z0 + door_z1) / 2), BEIGE,
            bevel=0.006, segments=2, name="front door")
    for sx in (-1, 1):
        hx = CX + sx * (BW / 2 - 0.080)
        kit.box((0.090, 0.008, 0.020), (hx, FRONT - 0.0135, door_z1 - 0.026), GREY, bevel=0.003, segments=1, name="door pull")
        kit.box((0.080, 0.006, 0.007), (hx, FRONT - 0.0170, door_z1 - 0.031), BLACK, bevel=0.0, name="door pull slot")
        kit.box((0.040, 0.010, 0.012), (CX + sx * BW * 0.2, FRONT - 0.010, door_z0 + 0.004), GREY, bevel=0.002, segments=1, name="door hinge")
    # Louvre on the door (fuser cooling) and a jam-clearance sticker.
    for k in range(6):
        kit.box((0.12, 0.004, 0.005), (CX + BW * 0.23, FRONT - 0.0145, door_z0 + 0.045 + k * 0.012), BLACK, bevel=0.0, name="door louvre")
    kit.box((0.075, 0.001, 0.05), (CX - BW * 0.25, FRONT - 0.0135, door_z0 + 0.10), PAPER, bevel=0.0, name="jam sticker")
    # Column front above the door: toner-door release and a small label.
    kit.box((0.040, 0.006, 0.014), (x0 + COLW / 2, FRONT - 0.002, ENG_TOP + 0.030), GREY, bevel=0.002, segments=1, name="column release")
    kit.box((0.050, 0.001, 0.016), (x0 + COLW / 2, FRONT - 0.0006, ENG_TOP + 0.003), PAPER, bevel=0.0, name="column label")

    # --------------------------------------------------- in-body exit tray
    tray_x0, tray_x1 = xc + 0.004, x1 - 0.016
    tray_y0, tray_y1 = FRONT + 0.016, by - SPD - 0.002
    tz = ENG_TOP + 0.0025
    kit.box((tray_x1 - tray_x0, tray_y1 - tray_y0, 0.005), ((tray_x0 + tray_x1) / 2, (tray_y0 + tray_y1) / 2, tz), GREY,
            bevel=0.002, segments=1, name="exit tray")
    for k in range(5):
        ry = tray_y0 + 0.04 + k * (tray_y1 - tray_y0 - 0.08) / 4
        kit.box((tray_x1 - tray_x0 - 0.03, 0.004, 0.004), ((tray_x0 + tray_x1) / 2 + 0.01, ry, tz + 0.0045), GREY,
                bevel=0.0, name="tray rib")
    # Exit slot and roller on the column's inner face.
    kit.box((0.006, 0.32, 0.012), (xc + 0.001, (tray_y0 + tray_y1) / 2, ENG_TOP + 0.030), BLACK, bevel=0.0, name="exit slot")
    kit.cylinder(0.0055, 0.30, (xc + 0.003, (tray_y0 + tray_y1) / 2, ENG_TOP + 0.026), GREY, verts=10, rot=(90, 0, 0),
                 bevel=0.0, name="exit roller")
    kit.box((0.010, 0.34, 0.006), (xc + 0.004, (tray_y0 + tray_y1) / 2, ENG_TOP + 0.039), GREY, bevel=0.002, segments=1, name="exit lip")
    # Copies that came out and stayed: A4 long edge first (0.21 x 0.297),
    # pulled toward the front so the stack shows under the console lip.
    cpx, cpy = xc + 0.018 + 0.105, FRONT + 0.026 + 0.1485
    cz = tz + 0.0065 + 0.0035
    kit.box((0.210, 0.297, 0.007), (cpx, cpy, cz), PAPER, bevel=0.0008, segments=1, name="copies")
    kit.box((0.210, 0.297, 0.0015), (cpx + 0.014, cpy + 0.006, cz + 0.0045), PAPER, bevel=0.0, rot=(0, -1.0, 3.0), name="top copy")
    # Copy stopper flipped up at the open end of the tray.
    kit.box((0.004, 0.10, 0.020), (tray_x1 - 0.012, cpy, tz + 0.012), GREY, bevel=0.0015, segments=1, rot=(0, 12, 0), name="copy stopper")

    # ------------------------------------------------------ platen + cover
    top = BODY_Z1
    kit.box((BW - 0.04, BD * 0.5, 0.004), (CX, 0.04, top + 0.001), DARKGLASS, bevel=0.0, name="platen glass edge")
    lid_d = by - console_y - 0.026
    lid_y = console_y + 0.006 + lid_d / 2
    kit.box((BW - 0.026, lid_d, 0.030), (CX, lid_y, top + 0.004 + 0.015), GREY, bevel=0.008, segments=2, name="document cover")
    kit.box((BW - 0.040, lid_d - 0.014, 0.004), (CX, lid_y, top + 0.0045), WHITE, bevel=0.0, name="cover pad")
    kit.box((0.12, 0.006, 0.008), (CX, console_y + 0.003, top + 0.016), BLACK, bevel=0.0, name="cover finger pull")
    for sx in (-1, 1):
        kit.box((0.05, 0.030, 0.050), (CX + sx * BW * 0.24, by - 0.006, top + 0.024), GREY, bevel=0.006, segments=2, name="cover hinge")
    # Original-size scale strip along the left of the platen.
    kit.box((0.012, lid_d - 0.03, 0.002), (x0 + 0.008, lid_y, top + 0.001), ALU, bevel=0.0, name="size scale")

    # -------------------------------- right side: key counter, switch, door
    kcx = x1 + 0.011
    kit.box((0.022, 0.07, 0.08), (kcx, FRONT + 0.05, 0.70), GREY, bevel=0.005, segments=2, name="key counter")
    kit.box((0.004, 0.040, 0.008), (kcx + 0.0105, FRONT + 0.05, 0.715), BLACK, bevel=0.0, name="key slot")
    kit.box((0.004, 0.026, 0.016), (kcx + 0.0105, FRONT + 0.05, 0.685), DARKGLASS, bevel=0.0, name="counter window")
    kit.box((0.010, 0.032, 0.040), (x1 + 0.004, FRONT + 0.05, 0.58), GREY, bevel=0.003, segments=1, name="power switch bezel")
    kit.box((0.008, 0.020, 0.024), (x1 + 0.008, FRONT + 0.05, 0.58), BLACK, bevel=0.002, segments=1, name="power rocker")
    # Jam-access side door: a 3 mm shut line all round and its latch.
    sd_len, sd_y = BD - 0.21, 0.065
    kit.frame((sd_len, 0.29), (sd_len - 0.008, 0.282), 0.003, (x1 + 0.0005, sd_y, 0.645), BLACK, rot=(0, 0, 90),
              bevel=0.0, name="side door seam")
    kit.box((0.012, 0.06, 0.016), (x1 + 0.006, sd_y - sd_len / 2 + 0.045, 0.765), GREY, bevel=0.003, segments=1, name="side door latch")

    # --------------------------------------- left side: louvres + carry grip
    for k in range(9):
        kit.box((0.004, BD * 0.4, 0.006), (x0 - 0.0005, 0.06, 0.62 + k * 0.014), BLACK, bevel=0.0, name="left louvre")
    kit.box((0.010, 0.20, 0.034), (x0 - 0.003, -0.05, 0.800), GREY, bevel=0.004, segments=2, name="carry grip")
    kit.box((0.006, 0.18, 0.012), (x0 - 0.006, -0.05, 0.793), BLACK, bevel=0.0, name="carry grip slot")

    # ------------------------------------------------------------- back
    for r in range(4):
        for c in range(3):
            kit.box((0.10, 0.004, 0.006), (CX + (c - 1) * BW * 0.25, by + 0.0005, 0.725 + r * 0.016), BLACK, bevel=0.0, name="rear vent")
    # Cooling fan: grey bezel ring, recessed black well, chrome wire guard.
    fx, fz = CX + BW * 0.25, 0.615
    kit.lathe([(0.050, 0.0), (0.050, 0.004), (0.054, 0.007), (0.060, 0.007), (0.063, 0.004), (0.063, 0.0)],
              (fx, by, fz), GREY, verts=24, rot=(-90, 0, 0), close_top=False, close_bottom=False, name="fan bezel")
    kit.cylinder(0.050, 0.004, (fx, by + 0.002, fz), BLACK, verts=24, rot=(90, 0, 0), bevel=0.0, name="fan well")
    kit.cylinder(0.016, 0.004, (fx, by + 0.004, fz), GREY, verts=12, rot=(90, 0, 0), bevel=0.001, segments=1, name="fan hub")
    for r, n in ((0.044, 20), (0.033, 16), (0.022, 12)):
        pts = [(fx + r * math.cos(2 * math.pi * i / n), by + 0.008, fz + r * math.sin(2 * math.pi * i / n)) for i in range(n + 1)]
        kit.tube(pts, 0.0015, CHROME, verts=6, name="fan guard ring")
    for a in (0, 45, 90, 135):
        kit.box((0.088, 0.003, 0.003), (fx, by + 0.008, fz), CHROME, bevel=0.0, rot=(0, a, 0), name="fan guard spoke")
    kit.box((0.10, 0.0015, 0.06), (CX - BW * 0.22, by + 0.0006, 0.60), ALU, bevel=0.0, name="rating plate")
    # Rear panel screws (engine, rear cover and pedestal backs).
    for x in (x0 + 0.025, x1 - 0.025):
        for z, yb in ((BODY_Z0 + 0.03, by), (ENG_TOP - 0.04, by), ((ENG_TOP + zt) / 2, by + 0.002),
                      (PED_Z0 + 0.06, PD / 2), (PED_Z1 - 0.03, PD / 2)):
            kit.cylinder(0.0045, 0.003, (x, yb + 0.0012, z), STEEL, verts=8, rot=(90, 0, 0), bevel=0.0, name="rear screw")
    # Pedestal back: a hand-hold slot for wheeling it out from the wall.
    kit.box((0.16, 0.004, 0.026), (CX, PD / 2 + 0.0015, PED_Z1 - 0.07), BLACK, bevel=0.0, name="pedestal hand slot")
    ix, iz = CX + 0.03, 0.53
    kit.box((0.05, 0.020, 0.04), (ix, by + 0.010, iz), GREY, bevel=0.004, segments=1, name="inlet socket")
    kit.tube([(ix, by + 0.02, iz), (ix, by + 0.040, iz - 0.01), (ix + 0.005, by + 0.050, iz - 0.06),
              (ix + 0.01, by + 0.052, 0.20), (ix + 0.015, by + 0.050, 0.03), (ix + 0.025, by + 0.052, 0.0046),
              (ix + 0.07, by + 0.064, 0.0046), (ix + 0.14, by + 0.072, 0.0046)], 0.0045, BLACK, verts=8, name="power cord")

    # ------------------------------------------------------------- meta
    kit.support("cover", (CX, lid_y, top + 0.034), (BW - 0.04, lid_d - 0.02))
    kit.anchor("console", (CX, my, mz))
    kit.anchor("output", (cpx, cpy, cz + 0.006))
    cx0, cx1 = x0 - 0.01, x1 + 0.03
    cy0, cy1 = FRONT - 0.03, by + 0.006
    kit.collider(((cx0 + cx1) / 2, (cy0 + cy1) / 2, (top + 0.034) / 2), (cx1 - cx0, cy1 - cy0, top + 0.034))
    kit.tag("office", "wall_unit")
    kit.pile("Case", mass=3, palette="office90s", states=["Upright", "Back", "Side"])
