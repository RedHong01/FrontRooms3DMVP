"""Floor-standing office photocopier, c. 1986-95 (Canon NP / Xerox 50xx class:
an analog A4/A3 copier body on its two-cassette paper pedestal with swivel
casters, delivering to a side exit tray on the left flank).

Era fix (2026-10-02, research/office_and_film/22_era_lock.md): the body
used to carry an in-body exit, a cavity between engine and scanner, which is a
mid/late-'90s digital-copier layout. A 1990 analog copier closes that gap and
delivers sideways onto a sloped tray, so the engine is one block up to the
scanner and the copies sit on the side tray.

Construction, bottom to top: four swivel casters under a grey plinth; a beige
pedestal with two paper cassettes (grey grips with a dark finger slot,
paper-level windows, tray-number cards); a grey accent band; the engine body with its
own cassette and a drop-down front door (pulls, louvre) running up to the
scanner seam; then the scanner unit, whose front is the sloped control
console carrying the CopierPanel decal (4:1 art: LCD, keypad, START), and a
grey document cover over the platen with rear hinges. Key counter, power
switch and the jam-access side door on the right flank. On the left flank:
cooling louvres low down, and under the scanner seam the exit slot with its
lip and the grey exit tray hooked into the flank, rising 12 degrees outward,
with paper guides, a flip-up copy stopper and a stack of A4 copies. Vents, a
guarded fan and the power cord on the back.

Real-world reference size: 0.60 m wide body (0.63 m over the key counter),
0.92 m over the side exit tray, 0.56 m deep body (0.67 m over cassette grips,
console lip and the power cord on the floor), 1.14 m tall to the top of the
cover hinges; the body is wider than deep, as on the real machines and in the
target office image. Front (console, cassettes) faces -Y. Origin = floor
under the body (the body sits 8 mm left of centre to balance the key
counter); the tray hangs 0.30 m off the left flank, so bounds and footprint
are off-centre toward -X (Unity +X). Lying on its Side rest the copier rests
on the right flank, tray up.

Budget pass (2026-10-02, §5.3: 2,500 / 1,000 tris, <= 4 slots):
* Four slots: PlasticBeige (all light mouldings; the old white engine merges
  into it, as in the target), PlasticGrey (plinth, band, grips, cover,
  casters, tray, fan), PlasticBlack (slots, seams, louvres, wheels, cord) and
  CopierPanel (the console decal). The copies, the cassette number cards
  and the key-counter window are CopierPanel too, uv-mapped into its art: a
  flat light key-cap patch for the copies, the keypad's "1" / "2" / "3" caps
  for the cassette cards (tray numbers), the LCD digits for the counter. The
  jam sticker and column label were dropped: the key-cap patch is too close
  to PlasticBeige to read on the beige door.
* Casters are a wheel, two fork plates and a swivel block; slots, louvres
  and vents are single quads; screws, rating plate, tray ribs and door
  hinges (under 5 mm at 2 m) are gone. Big ABS shells keep 2-segment
  bevels; small trims are 1-segment or raw.
"""

import math

NAME = "Kit_Copier"
LOD1 = 0.42

BEIGE = "Prop_PlasticBeige"
GREY = "Prop_PlasticGrey"
BLACK = "Prop_PlasticBlack"
PANEL = "Prop_CopierPanel"

# Regions of the CopierPanel art (u0, v0, u1, v1) reused as unique detail.
PAPER_UV = (0.408, 0.2344, 0.420, 0.2578)          # flat light key-cap patch (copies only)
CARD_UVS = ((0.391, 0.719, 0.441, 0.883),            # keypad "1": cassette 1 (body)
            (0.454, 0.719, 0.504, 0.883),            # keypad "2": cassette 2
            (0.516, 0.719, 0.566, 0.883))            # keypad "3": cassette 3
COUNTER_UV = (0.283, 0.531, 0.205, 0.707)            # LCD "001", u flipped (quad faces +X)

CX = -0.008           # body centre x
BW, BD = 0.60, 0.56   # body width / depth
FRONT = -BD / 2       # body front plane (y)
PED_Z0, PED_Z1 = 0.080, 0.440
BODY_Z0 = 0.452       # engine body underside
SCAN_Z0 = 0.928       # underside of the scanner / platen unit
BODY_Z1 = 1.092       # platen level
SEAM = 0.010          # dark shut line between engine frame and scanner
EXIT_Y, EXIT_Z = 0.0, 0.872   # side exit slot centre on the left flank
TRAY_L, TRAY_W = 0.30, 0.33   # exit tray: reach off the flank, width (A3 short edge + guides)
TRAY_TILT = 12.0              # degrees the tray rises toward its outer end


def _uv(obj, rect):
    """Map a decal part into one region of its slot's art."""
    obj["fr_uv_rect"] = list(rect)
    return obj


def _caster(kit, x, y):
    """Swivel caster: swivel block under the plinth, two fork plates, wheel."""
    off = 0.012  # trailing offset of the wheel axle
    kit.box((0.036, 0.034, 0.024), (x, y + 0.004, PED_Z0 - 0.012), GREY, bevel=0.0, name="caster swivel")
    for s in (-1, 1):
        kit.box((0.004, 0.040, 0.046), (x + s * 0.0125, y + off, 0.043), GREY, bevel=0.0, name="caster fork")
    kit.cylinder(0.026, 0.018, (x, y + off, 0.026), BLACK, verts=10, rot=(0, 90, 0), bevel=0.0, name="caster wheel")


def _cassette(kit, z0, z1, width, y_face, card_uv, name):
    """Paper cassette front: face plate, grip with its finger slot,
    paper-level window, size card in a holder. y_face = front plane."""
    h = z1 - z0
    zc = (z0 + z1) / 2
    kit.box((width, 0.022, h), (CX, y_face + 0.011, zc), BEIGE, bevel=0.006, segments=1, name=name + " face")
    gz = z1 - 0.030
    gw = min(0.24, width * 0.42)
    kit.box((gw, 0.010, 0.030), (CX, y_face - 0.004, gz), GREY, bevel=0.004, segments=1, name=name + " grip")
    kit.quad(gw - 0.02, 0.010, (CX, y_face - 0.0095, gz - 0.006), BLACK, facing="-y", uv="metres", name=name + " grip slot")
    wx = CX - width / 2 + 0.040
    kit.quad(0.014, min(0.07, h - 0.05), (wx, y_face - 0.0005, zc - 0.006), BLACK, facing="-y", uv="metres", name=name + " level window")
    # Tray-number card (the keypad's own digit art, so it reads 1 / 2 / 3)
    # in a grey holder; decals sit >= 0.5 mm proud against z-fighting.
    sx = CX + width / 2 - 0.060
    kit.box((0.042, 0.004, 0.034), (sx, y_face - 0.0015, zc - 0.006), GREY, bevel=0.0, name=name + " card holder")
    kit.quad(0.032, 0.026, (sx, y_face - 0.0041, zc - 0.006), PANEL, facing="-y", uv_rect=card_uv, name=name + " size card")


def build(kit):
    x0, x1 = CX - BW / 2, CX + BW / 2
    zt = SCAN_Z0 - SEAM                 # top of the engine body
    by = BD / 2

    # ------------------------------------------------------------ pedestal
    for sx in (-1, 1):
        for sy in (-1, 1):
            _caster(kit, CX + sx * (BW / 2 - 0.055), sy * (BD / 2 - 0.065))
    PW, PD = BW - 0.02, BD - 0.04
    kit.box((PW, PD, 0.03), (CX, 0, PED_Z0 + 0.015), GREY, bevel=0.006, segments=1, name="plinth")
    ped_front = -PD / 2
    kit.box((PW, PD, PED_Z1 - PED_Z0 - 0.03), (CX, 0.0, (PED_Z0 + 0.03 + PED_Z1) / 2), BEIGE,
            bevel=0.010, segments=2, name="pedestal carcass")
    gap = 0.006
    z_mid = (PED_Z0 + 0.03 + PED_Z1) / 2
    cas_face = ped_front - 0.020        # face plates overlap the carcass by 2 mm
    _cassette(kit, PED_Z0 + 0.036, z_mid - gap / 2, BW - 0.04, cas_face, CARD_UVS[2], "cassette 3")
    _cassette(kit, z_mid + gap / 2, PED_Z1 - 0.006, BW - 0.04, cas_face, CARD_UVS[1], "cassette 2")
    kit.box((BW - 0.04, 0.012, 0.010), (CX, ped_front - 0.010, PED_Z0 + 0.034), GREY, bevel=0.0, name="kick strip")

    # Grey accent band between pedestal and body.
    kit.box((BW - 0.004, BD - 0.004, BODY_Z0 - PED_Z1 + 0.004), (CX, 0, (PED_Z1 + BODY_Z0) / 2), GREY,
            bevel=0.004, segments=1, name="accent band")

    # ----------------------------------------------------------- main body
    # Engine body: one block from the accent band up to the scanner seam (no
    # in-body exit cavity; the copies leave through the left flank).
    kit.box((BW, BD, zt - BODY_Z0), (CX, 0, (BODY_Z0 + zt) / 2), BEIGE, bevel=0.012, segments=2, name="engine body")
    # Dark shut line / scanner underside.
    kit.box((BW - 0.02, BD - 0.02, SEAM + 0.004), (CX, 0, zt + SEAM / 2), BLACK, bevel=0.0, name="scanner seam")

    # Scanner unit on top, 6 mm proud all round; its front is the console.
    console_y = FRONT + 0.16            # rear edge of the sloped console
    SW = BW + 0.012
    kit.box((SW, by + 0.006 - console_y, BODY_Z1 - SCAN_Z0), (CX, (console_y + by + 0.006) / 2, (SCAN_Z0 + BODY_Z1) / 2), BEIGE,
            bevel=0.012, segments=2, name="scanner body")
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
              rot=rot, bevel=0.0, name="panel bezel")
    kit.box((0.480, 0.003, 0.120), (CX, my + ny * 0.0012, mz + nz * 0.0012), PANEL,
            bevel=0.0, rot=rot, uv="decal", decal_axes="xz", name="control panel")
    # Front lip strip under the console (grey accent) with a name badge.
    kit.box((SW - 0.004, 0.012, 0.022), (CX, FRONT - 0.014, SCAN_Z0 + 0.013), GREY, bevel=0.004, segments=1, name="console bumper")
    kit.box((0.085, 0.004, 0.018), (x0 + 0.075, FRONT - 0.0135, 0.988), GREY, bevel=0.0, name="badge")

    # Body cassette (tray 1) and the drop-down front door above it.
    _cassette(kit, BODY_Z0 + 0.012, BODY_Z0 + 0.112, BW - 0.03, FRONT - 0.020, CARD_UVS[0], "cassette 1")
    door_z0, door_z1 = BODY_Z0 + 0.122, zt - 0.024
    kit.box((BW - 0.03, 0.014, door_z1 - door_z0), (CX, FRONT - 0.006, (door_z0 + door_z1) / 2), BEIGE,
            bevel=0.006, segments=1, name="front door")
    for sx in (-1, 1):
        hx = CX + sx * (BW / 2 - 0.080)
        kit.box((0.090, 0.008, 0.020), (hx, FRONT - 0.0135, door_z1 - 0.026), GREY, bevel=0.0, name="door pull")
        kit.quad(0.080, 0.007, (hx, FRONT - 0.0181, door_z1 - 0.031), BLACK, facing="-y", uv="metres", name="door pull slot")
    # Louvre on the door (fuser cooling).
    for k in range(6):
        kit.quad(0.12, 0.005, (CX + BW * 0.23, FRONT - 0.0135, door_z0 + 0.045 + k * 0.012), BLACK, facing="-y", uv="metres", name="door louvre")
    # ------------------------------------------- side exit (left flank, -X)
    # Exit slot under the scanner seam with a lip over it, and the copy tray
    # hooked into the flank below it, rising TRAY_TILT degrees outward.
    kit.quad(0.32, 0.012, (x0 - 0.0006, EXIT_Y, EXIT_Z), BLACK, facing="-x", uv="metres", name="exit slot")
    kit.box((0.012, 0.35, 0.008), (x0 - 0.005, EXIT_Y, EXIT_Z + 0.013), GREY, bevel=0.0, name="exit lip")
    t = math.radians(TRAY_TILT)
    ct, st = math.cos(t), math.sin(t)
    hx, hz = x0 - 0.006, EXIT_Z - 0.020         # tray hinge: inner edge, mid-plane

    def on_tray(d, h=0.0):
        """(x, z) of the point d metres out along the tray, h above its mid-plane."""
        return hx - d * ct + h * st, hz + d * st + h * ct

    rot = (0, TRAY_TILT, 0)                     # +Y rotation lifts the outer (-X) end
    tx, tz = on_tray(TRAY_L / 2)
    kit.box((TRAY_L, TRAY_W, 0.006), (tx, EXIT_Y, tz), GREY, bevel=0.0, rot=rot, name="exit tray")
    gx, gz = on_tray(TRAY_L / 2, 0.010)
    for s in (-1, 1):  # paper guides along both long edges
        kit.box((TRAY_L - 0.02, 0.004, 0.014), (gx, EXIT_Y + s * (TRAY_W / 2 - 0.004), gz), GREY, bevel=0.0, rot=rot,
                name="paper guide")
    sx, sz = on_tray(TRAY_L - 0.004, 0.016)
    kit.box((0.004, 0.12, 0.026), (sx, EXIT_Y, sz), GREY, bevel=0.0, rot=rot, name="copy stopper")
    for s in (-1, 1):  # hooks into the flank under the slot
        kit.box((0.014, 0.020, 0.026), (x0 - 0.006, EXIT_Y + s * 0.12, hz - 0.006), GREY, bevel=0.0, name="tray hook")
    # Copies that came out and stayed: A4 long edge first (0.21 out x 0.297
    # across), slid back against the flank by the tilt.
    cd = 0.012 + 0.105
    cpx, cpz = on_tray(cd, 0.003 + 0.0035)
    cpy = EXIT_Y
    _uv(kit.box((0.210, 0.297, 0.007), (cpx, cpy, cpz), PANEL, bevel=0.0, rot=rot, uv="decal", name="copies"), PAPER_UV)
    tcx, tcz = on_tray(cd + 0.012, 0.003 + 0.007 + 0.00075)
    _uv(kit.box((0.210, 0.297, 0.0015), (tcx, cpy + 0.006, tcz), PANEL, bevel=0.0, rot=(0, TRAY_TILT - 1.0, 3.0),
                uv="decal", name="top copy"), PAPER_UV)

    # ------------------------------------------------------ platen + cover
    top = BODY_Z1
    kit.box((BW - 0.04, BD * 0.5, 0.004), (CX, 0.04, top + 0.001), BLACK, bevel=0.0, name="platen glass edge")
    lid_d = by - console_y - 0.026
    lid_y = console_y + 0.006 + lid_d / 2
    kit.box((BW - 0.026, lid_d, 0.030), (CX, lid_y, top + 0.004 + 0.015), GREY, bevel=0.008, segments=2, name="document cover")
    kit.box((0.12, 0.006, 0.008), (CX, console_y + 0.003, top + 0.016), BLACK, bevel=0.0, name="cover finger pull")
    for sx in (-1, 1):
        kit.box((0.05, 0.030, 0.050), (CX + sx * BW * 0.24, by - 0.006, top + 0.024), GREY, bevel=0.006, segments=1, name="cover hinge")

    # -------------------------------- right side: key counter, switch, door
    kcx = x1 + 0.011
    kit.box((0.022, 0.07, 0.08), (kcx, FRONT + 0.05, 0.70), GREY, bevel=0.005, segments=1, name="key counter")
    kit.quad(0.040, 0.008, (kcx + 0.0116, FRONT + 0.05, 0.715), BLACK, facing="+x", uv="metres", name="key slot")
    kit.quad(0.028, 0.016, (kcx + 0.0116, FRONT + 0.05, 0.685), PANEL, facing="+x", uv_rect=COUNTER_UV, name="counter window")
    kit.box((0.010, 0.032, 0.040), (x1 + 0.004, FRONT + 0.05, 0.58), GREY, bevel=0.0, name="power switch bezel")
    kit.box((0.008, 0.020, 0.024), (x1 + 0.008, FRONT + 0.05, 0.58), BLACK, bevel=0.0, rot=(8, 0, 0), name="power rocker")
    # Jam-access side door: a 3 mm shut line all round and its latch.
    sd_len, sd_y = BD - 0.21, 0.065
    kit.frame((sd_len, 0.29), (sd_len - 0.008, 0.282), 0.003, (x1 + 0.0005, sd_y, 0.645), BLACK, rot=(0, 0, 90),
              bevel=0.0, name="side door seam")
    kit.box((0.012, 0.06, 0.016), (x1 + 0.006, sd_y - sd_len / 2 + 0.045, 0.765), GREY, bevel=0.0, name="side door latch")

    # ------------------------------------- left side: louvres (below the tray)
    for k in range(9):
        kit.quad(BD * 0.4, 0.006, (x0 - 0.0006, 0.06, 0.62 + k * 0.014), BLACK, facing="-x", uv="metres", name="left louvre")

    # ------------------------------------------------------------- back
    for r in range(4):
        for c in range(3):
            kit.quad(0.10, 0.006, (CX + (c - 1) * BW * 0.25, by + 0.0006, 0.725 + r * 0.016), BLACK, facing="+y", uv="metres", name="rear vent")
    # Cooling fan: grey bezel ring, recessed black well, grey guard cross.
    fx, fz = CX + BW * 0.25, 0.615
    kit.cylinder(0.063, 0.006, (fx, by + 0.003, fz), GREY, verts=16, rot=(90, 0, 0), bevel=0.0, name="fan bezel")
    kit.cylinder(0.051, 0.006, (fx, by + 0.0045, fz), BLACK, verts=16, rot=(90, 0, 0), bevel=0.0, name="fan well")
    kit.cylinder(0.016, 0.006, (fx, by + 0.007, fz), GREY, verts=8, rot=(90, 0, 0), bevel=0.0, name="fan hub")
    for a in (45, 135):
        kit.box((0.100, 0.003, 0.004), (fx, by + 0.009, fz), GREY, bevel=0.0, rot=(0, a, 0), name="fan guard spoke")
    kit.tube([(fx + 0.036 * math.cos(2 * math.pi * i / 12), by + 0.009, fz + 0.036 * math.sin(2 * math.pi * i / 12)) for i in range(13)],
             0.0016, GREY, verts=4, caps=False, name="fan guard ring")
    # Pedestal back: a hand-hold slot for wheeling it out from the wall.
    kit.quad(0.16, 0.026, (CX, PD / 2 + 0.0006, PED_Z1 - 0.07), BLACK, facing="+y", uv="metres", name="pedestal hand slot")
    ix, iz = CX + 0.03, 0.53
    kit.box((0.05, 0.020, 0.04), (ix, by + 0.010, iz), GREY, bevel=0.0, name="inlet socket")
    kit.tube([(ix, by + 0.02, iz), (ix, by + 0.040, iz - 0.01), (ix + 0.005, by + 0.050, iz - 0.06),
              (ix + 0.01, by + 0.052, 0.20), (ix + 0.015, by + 0.050, 0.03), (ix + 0.025, by + 0.052, 0.0046),
              (ix + 0.07, by + 0.064, 0.0046), (ix + 0.14, by + 0.072, 0.0046)], 0.0045, BLACK, verts=5, name="power cord")

    # ------------------------------------------------------------- meta
    kit.support("cover", (CX, lid_y, top + 0.034), (BW - 0.04, lid_d - 0.02))
    kit.anchor("console", (CX, my, mz))
    kit.anchor("output", (cpx, cpy, cpz + 0.006))
    cx0, cx1 = x0 - 0.01, x1 + 0.03
    cy0, cy1 = FRONT - 0.03, by + 0.006
    kit.collider(((cx0 + cx1) / 2, (cy0 + cy1) / 2, (top + 0.034) / 2), (cx1 - cx0, cy1 - cy0, top + 0.034))
    # Thin box for the exit tray (it sits below 1 m, at hip height), so the
    # footprint (the union of the colliders) covers it too.
    ox, oz = on_tray(TRAY_L, 0.030)
    tx0, tz0 = ox - 0.004, hz - 0.020
    kit.collider(((tx0 + cx0) / 2, EXIT_Y, (tz0 + oz) / 2), (cx0 - tx0, TRAY_W + 0.02, oz - tz0))
    kit.tag("office", "wall_unit")
    kit.pile("Case", mass=2, palette="office90s", states=["Upright", "Side", "Back"])
