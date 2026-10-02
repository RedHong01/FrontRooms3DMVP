"""Bottled floor water cooler, c. 1990-98 (the Oasis / Elkay / Sunroc office
cooler: white enamelled cabinet, grey front fascia with a recessed tap alcove,
two push taps over a removable drip tray, an upturned 5-gallon polycarbonate
bottle in a collar on top, condenser coil and power cord on the back, a
paper-cup dispenser tube clamped to one side).

Real-world reference size: cabinet 0.32 m wide x 0.32 m deep x 1.00 m tall
(incl. bottle collar); 5-gallon bottle 0.27 m diameter x 0.475 m tall, of
which ~0.13 m (cap, neck and shoulder) sits in the collar seat. Overall
~1.34 m. Front (taps) faces -Y. Origin = floor, centre of the cabinet.

Hot / cold colour coding: the hot paddle and heating lamp use HOT, the cold
paddle uses COLD. The kit has no red or blue opaque plastic yet, so HOT is the
nearest saturated red (Prop_WoodCherry, reads as maroon plastic at tap size)
and COLD is the bottle's translucent blue (Prop_BottleBlue, like the classic
translucent cold tap). Swap both to Prop_PlasticRed / Prop_PlasticBlue once
those slots exist.

The bottle is one closed transparent shell plus an inward-facing inner wall,
so its far side and ribs still render with back-face culling (URP default)
and the jug reads full rather than as a tinted film.
"""

import bmesh

NAME = "Kit_WaterCooler"

WHITE = "Prop_PlasticWhite"
GREY = "Prop_PlasticGrey"
BLACK = "Prop_PlasticBlack"
CHROME = "Prop_Chrome"
STEEL = "Prop_SteelBlack"
BOTTLE = "Prop_BottleBlue"
GLASS = "Prop_Glass"
DARKGLASS = "Prop_GlassCRT"
PAPER = "Prop_Paper"
RUBBER = "Prop_Rubber"
HOT = "Prop_WoodCherry"     # interim for Prop_PlasticRed
COLD = "Prop_BottleBlue"    # interim for Prop_PlasticBlue

W = 0.32          # cabinet width = depth
HW = W / 2


def _bottle_profile():
    """Upturned 5-gallon bottle, (radius, z) from the cap tip upward."""
    # Cap and neck sit inside the cabinet (hidden under the top cap), so they
    # are kept simple: capped neck, then the flange the collar probe pierces.
    p = [
        (0.0, 0.0), (0.030, 0.0),                                       # cap face
        (0.030, 0.040), (0.026, 0.070),                                 # cap skirt + neck
        (0.034, 0.078), (0.029, 0.087),                                 # neck flange (support ring)
        (0.031, 0.098), (0.048, 0.114), (0.080, 0.133),                 # shoulder
        (0.108, 0.148), (0.127, 0.165), (0.135, 0.186),
    ]
    # Body with two pairs of hoop ribs (stiffening grooves).
    def groove(z):
        return [(0.135, z - 0.010), (0.130, z - 0.003), (0.130, z + 0.003), (0.135, z + 0.010)]
    for zc in (0.222, 0.258):
        p += groove(zc)
    p += [(0.135, 0.300), (0.1355, 0.340)]
    for zc in (0.386, 0.422):
        p += groove(zc)
    # Bottle base (now the top): rounded heel, shallow push-up dome.
    p += [(0.135, 0.444), (0.131, 0.458), (0.121, 0.468),
          (0.100, 0.4735), (0.070, 0.4735), (0.035, 0.470), (0.0, 0.469)]
    return p


def _cup_stack_profile(z0, z1):
    """Nested paper cone cups seen through the dispenser tube: open mouth at
    the bottom (concave), a sawtooth of rolled rims up the stack."""
    p = [(0.0, z0 + 0.055), (0.012, z0 + 0.034), (0.026, z0 + 0.008), (0.0305, z0 + 0.001),
         (0.0335, z0), (0.0345, z0 + 0.004)]
    z = z0 + 0.012
    while z < z1 - 0.012:
        p += [(0.0322, z - 0.005), (0.0345, z)]
        z += 0.030
    p += [(0.0322, z1 - 0.004), (0.020, z1), (0.0, z1)]
    return p


def _inner_wall_profile():
    """Simplified inner surface of the bottle (3 mm in from the outer wall),
    shoulder to base; rendered with its normals facing inward."""
    p = [(0.046, 0.119), (0.078, 0.137), (0.105, 0.152), (0.124, 0.168), (0.132, 0.188)]
    for zc in (0.222, 0.258):
        p += [(0.132, zc - 0.010), (0.127, zc), (0.132, zc + 0.010)]
    p += [(0.1325, 0.320)]
    for zc in (0.386, 0.422):
        p += [(0.132, zc - 0.010), (0.127, zc), (0.132, zc + 0.010)]
    p += [(0.132, 0.442), (0.127, 0.456), (0.117, 0.465), (0.097, 0.4705), (0.050, 0.4685), (0.0, 0.466)]
    return p


def _flip_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def build(kit):
    # ---------------------------------------------------------------- cabinet
    # Recessed black plinth and four levelling feet under it.
    kit.box((0.296, 0.296, 0.026), (0, 0, 0.017), BLACK, bevel=0.004, name="plinth")
    for sx in (-1, 1):
        for sy in (-1, 1):
            kit.cylinder(0.016, 0.006, (sx * 0.125, sy * 0.125, 0.003), RUBBER, verts=10, bevel=0.0, name="foot")

    cab_z0, cab_top = 0.026, 0.600
    kit.box((W, W, cab_top - cab_z0), (0, 0, (cab_z0 + cab_top) / 2), WHITE, bevel=0.011, segments=3, name="lower cabinet")

    # Head section: one full-depth white shell (a frame run front to back, so
    # the flanks have no seam), closed at the back by a rear panel; the grey
    # fascia sits 2.5 mm inside the front opening and carries the tap alcove.
    head_z0, head_z1 = 0.600, 0.920
    hz, hh = (head_z0 + head_z1) / 2, head_z1 - head_z0
    fascia_z = hz - 0.004
    kit.frame((W, hh), (0.272, 0.272), W, (0, 0, hz), WHITE,
              inner_offset=(0, -0.004), bevel=0.011, segments=3, name="head shell")
    kit.box((0.274, 0.012, 0.274), (0, HW - 0.006, fascia_z), WHITE, bevel=0.002, segments=1, name="head rear panel")
    # Waist band: a deliberate moulded belt over the cabinet / head joint.
    kit.box((W + 0.004, W + 0.004, 0.020), (0, 0, 0.600), WHITE, bevel=0.004, segments=2, name="waist band")
    alc_w, alc_h, alc_cz = 0.19, 0.16, 0.735
    alc_z0, alc_z1 = alc_cz - alc_h / 2, alc_cz + alc_h / 2
    fascia_front = -0.156
    kit.frame((0.267, 0.267), (alc_w, alc_h), 0.078, (0, fascia_front + 0.039, fascia_z), GREY,
              inner_offset=(0, alc_cz - fascia_z), bevel=0.009, segments=3, name="fascia")
    kit.box((alc_w + 0.01, 0.01, alc_h + 0.01), (0, -0.074, alc_cz), BLACK, bevel=0.0, name="alcove back")

    # Top cap (3 mm overhang) and the bottle collar.
    cap_z0, cap_z1 = head_z1, 0.966
    kit.box((W + 0.006, W + 0.006, cap_z1 - cap_z0), (0, 0, (cap_z0 + cap_z1) / 2), WHITE, bevel=0.016, segments=3, name="top cap")
    # Collar: a dished seat that follows the bottle shoulder.
    kit.lathe([(0.044, 0.958), (0.044, 0.975), (0.052, 0.984), (0.066, 0.990), (0.096, 1.002),
               (0.106, 1.000), (0.110, 0.990), (0.110, 0.958)], (0, 0, 0), GREY, verts=24, name="bottle collar")
    kit.cylinder(0.044, 0.004, (0, 0, cap_z1 + 0.001), BLACK, verts=24, bevel=0.0, name="collar throat")

    # ------------------------------------------------------------------ taps
    for sx, name in ((-0.047, "hot"), (0.047, "cold")):
        kit.box((0.040, 0.050, 0.030), (sx, -0.104, alc_z1 - 0.014), GREY, bevel=0.006, segments=2, name=name + " tap body")
        kit.box((0.034, 0.011, 0.044), (sx, -0.134, alc_z1 - 0.026), HOT if name == "hot" else COLD,
                bevel=0.004, segments=2, rot=(-9, 0, 0), name=name + " paddle")
        kit.box((0.022, 0.003, 0.008), (sx, -0.1405, alc_z1 - 0.012), WHITE, bevel=0.0, rot=(-9, 0, 0), name=name + " paddle inlay")
        kit.cylinder(0.0062, 0.020, (sx, -0.108, alc_z1 - 0.038), CHROME, verts=12, bevel=0.0015, segments=1, name=name + " nozzle")
        kit.cylinder(0.0042, 0.008, (sx, -0.108, alc_z1 - 0.051), CHROME, verts=12, bevel=0.0, radius_top=0.0062, name=name + " nozzle tip")
    # Child-safety catch on the hot tap.
    kit.box((0.012, 0.008, 0.010), (-0.047 - 0.026, -0.112, alc_z1 - 0.012), WHITE, bevel=0.002, segments=1, name="hot safety catch")

    # Drip tray: grey tub that stands 10 mm proud of the fascia, rim frame,
    # black well and a slatted grille.
    tray_w, tray_d = 0.186, 0.088
    tray_y = fascia_front - 0.010 + tray_d / 2
    kit.box((tray_w, tray_d, 0.012), (0, tray_y, alc_z0 + 0.006), GREY, bevel=0.004, name="drip tray tub")
    kit.box((tray_w - 0.016, tray_d - 0.016, 0.003), (0, tray_y, alc_z0 + 0.0135), BLACK, bevel=0.0, name="drip tray well")
    kit.frame((tray_w, tray_d), (tray_w - 0.016, tray_d - 0.016), 0.008, (0, tray_y, alc_z0 + 0.016), GREY,
              rot=(90, 0, 0), bevel=0.003, name="drip tray rim")
    for k in range(7):
        kit.box((tray_w - 0.018, 0.0045, 0.004), (0, tray_y - 0.030 + k * 0.010, alc_z0 + 0.016), GREY, bevel=0.0, name="grille slat")

    # Fascia furniture above the alcove: badge and two indicator lamps.
    kit.box((0.078, 0.005, 0.016), (0, fascia_front - 0.0015, 0.862), CHROME, bevel=0.002, segments=1, name="badge")
    for k, x in enumerate((0.093, 0.111)):
        kit.cylinder(0.0065, 0.004, (x, fascia_front - 0.001, 0.862), BLACK, verts=12, rot=(90, 0, 0), bevel=0.0, name="lamp bezel")
        kit.cylinder(0.0042, 0.004, (x, fascia_front - 0.003, 0.862), DARKGLASS if k else HOT, verts=10, rot=(90, 0, 0), bevel=0.0012, segments=1, name="lamp lens")

    # Lower front: compressor air-intake grille near the floor, caution label.
    kit.box((0.24, 0.004, 0.066), (0, -HW - 0.0005, 0.085), BLACK, bevel=0.0, name="intake well")
    for k in range(6):
        kit.box((0.244, 0.010, 0.0055), (0, -HW - 0.004, 0.058 + k * 0.011), WHITE, bevel=0.002, segments=1, rot=(-25, 0, 0), name="intake louvre")
    kit.box((0.085, 0.001, 0.045), (0, -HW - 0.0004, 0.548), PAPER, bevel=0.0, name="caution sticker")

    # Side louvres (both sides, low and toward the back).
    for sx in (-1, 1):
        for k in range(7):
            kit.box((0.004, 0.13, 0.006), (sx * (HW + 0.0005), 0.055, 0.075 + k * 0.022), BLACK, bevel=0.0, name="side louvre")

    # ------------------------------------------------------------------ back
    # Serpentine condenser coil on stand-offs, with vertical wire fins.
    cy, xL, xR = HW + 0.024, -0.115, 0.115
    rows, z0, step = 12, 0.11, 0.044
    pts = [(xL, cy, z0)]
    for i in range(rows):
        z = z0 + i * step
        end, s = (xR, 1) if i % 2 == 0 else (xL, -1)
        pts.append((end, cy, z))
        if i < rows - 1:
            pts += [(end + s * 0.011, cy, z + 0.008), (end + s * 0.017, cy, z + step / 2), (end + s * 0.011, cy, z + step - 0.008)]
            pts.append((end, cy, z + step))
    kit.tube(pts, 0.0042, STEEL, verts=6, name="condenser coil")
    for k in range(13):
        x = xL + 0.004 + k * (xR - xL - 0.008) / 12
        kit.cylinder(0.0014, rows * step + 0.01, (x, cy + 0.0058, z0 + (rows - 1) * step / 2), STEEL, verts=6, bevel=0.0, name="coil wire")
    for x in (xL + 0.01, xR - 0.01):
        for z in (z0 - 0.02, z0 + (rows - 1) * step + 0.02):
            kit.box((0.016, 0.026, 0.012), (x, HW + 0.012, z), STEEL, bevel=0.0, name="coil standoff")
    kit.box((0.25, 0.006, 0.016), (0, cy, z0 - 0.02), STEEL, bevel=0.002, segments=1, name="coil rail")
    kit.box((0.25, 0.006, 0.016), (0, cy, z0 + (rows - 1) * step + 0.02), STEEL, bevel=0.002, segments=1, name="coil rail")

    # Hot / cold tank rocker switches, rating plate, drain plug.
    for x in (-0.03, 0.0):
        kit.box((0.016, 0.006, 0.024), (x, HW + 0.003, 0.80), BLACK, bevel=0.002, segments=1, name="switch bezel")
        kit.box((0.010, 0.006, 0.016), (x, HW + 0.006, 0.80), BLACK, bevel=0.002, segments=1, rot=(12, 0, 0), name="rocker")
    kit.box((0.09, 0.0015, 0.055), (0.07, HW + 0.0006, 0.79), "Prop_Aluminium", bevel=0.0, name="rating plate")
    kit.cylinder(0.009, 0.008, (-0.08, HW + 0.004, 0.685), BLACK, verts=12, rot=(90, 0, 0), bevel=0.002, segments=1, name="drain plug")

    # Power cord out of the lower back, down to the floor, then a plug.
    # (kept within 60 mm of the back so the cooler can stand against a wall)
    kit.tube([(0.10, HW - 0.005, 0.07), (0.10, HW + 0.015, 0.066), (0.102, HW + 0.028, 0.045),
              (0.100, HW + 0.036, 0.015), (0.092, HW + 0.042, 0.004), (0.06, HW + 0.048, 0.004),
              (0.0, HW + 0.050, 0.004), (-0.06, HW + 0.045, 0.004), (-0.10, HW + 0.036, 0.004)], 0.0035, BLACK, verts=8, name="power cord")
    kit.box((0.036, 0.022, 0.014), (-0.125, HW + 0.031, 0.007), BLACK, bevel=0.003, segments=1, rot=(0, 0, 12), name="plug")

    # ------------------------------------------------- cup dispenser (right)
    tx, ty = HW + 0.044, -0.075
    t0, t1 = 0.585, 0.855
    kit.cylinder(0.037, t1 - t0, (tx, ty, (t0 + t1) / 2), GLASS, verts=20, bevel=0.0, name="cup tube")
    kit.lathe(_cup_stack_profile(t0 - 0.006, t1 - 0.03), (tx, ty, 0), PAPER, verts=10, name="cup stack")
    kit.cylinder(0.0395, 0.020, (tx, ty, t1 + 0.008), GREY, verts=20, bevel=0.004, segments=1, name="tube cap")
    kit.lathe([(0.0345, t0 - 0.010), (0.0395, t0 - 0.012), (0.0412, t0 - 0.006), (0.0412, t0 + 0.012),
               (0.0372, t0 + 0.014)], (tx, ty, 0), GREY, verts=20, close_top=False, close_bottom=False, name="tube bezel")
    for z in (0.64, 0.80):
        kit.cylinder(0.0405, 0.014, (tx, ty, z), GREY, verts=16, bevel=0.002, segments=1, name="tube clamp")
        kit.box((0.012, 0.024, 0.014), (HW + 0.004, ty, z), GREY, bevel=0.002, segments=1, name="clamp arm")

    # ---------------------------------------------------------------- bottle
    # Shoulder seated in the collar dish; the neck flange (0.941-0.949) stays
    # hidden under the top cap.
    bottle_z = 0.866
    kit.lathe(_bottle_profile(), (0, 0, bottle_z), BOTTLE, verts=40, name="water bottle")
    inner = kit.lathe(_inner_wall_profile(), (0, 0, bottle_z), BOTTLE, verts=24, close_bottom=False, name="bottle inner wall")
    _flip_normals(inner)

    # ---------------------------------------------------------------- meta
    kit.anchor("taps", (0, -0.13, alc_z0 + 0.03))
    kit.anchor("bottle_top", (0, 0, bottle_z + 0.4735))
    kit.collider((0, 0, cap_z1 / 2), (W + 0.006, W + 0.006, cap_z1))
    kit.collider((0, 0, 1.165), (0.27, 0.27, 0.35))
    kit.tag("office", "wall_unit")
    kit.pile("Tall", mass=1)
