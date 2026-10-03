"""Bottled floor water cooler, c. 1990-98 (the Oasis / Elkay / Sunroc office
cooler: white enamelled cabinet with a moulded waist band, a recessed tap
alcove with a dark back, red hot and blue cold push taps over a drip tray with
a grille, an upturned 5-gallon polycarbonate bottle in a dark collar on top,
condenser coil and power cord on the back, a paper-cup dispenser tube clamped
to the right flank).

Real-world reference size: cabinet 0.32 m wide x 0.32 m deep x 0.97 m tall
(incl. top cap); 5-gallon bottle 0.27 m diameter, of which the cap, neck and
shoulder sit in the collar. Overall 1.34 m. Front (taps) faces -Y. Origin =
floor, centre of the cabinet.

Budget pass (2026-10-02, §5.3: 2,500 / 1,000 tris, <= 4 slots):
* Four slots: PlasticWhite (cabinet, taps, cups), BottleBlue (bottle, cup
  tube, cold paddle and lamp: the classic translucent cold tap), PlasticRed
  (hot paddle and lamp), PlasticBlack (plinth, alcove, collar, grille, coil,
  louvres, cord). The old grey fascia is now the cabinet's own white moulding
  around a black-backed alcove; chrome nozzles are white; the rating plate,
  caution sticker and hot-tap catch (under 5 mm at 2 m) are gone.
* The cabinet is ONE frame running front to back with the alcove as its hole
  (no seams on the flanks), the alcove back set 78 mm in, a service plate
  closing the hole at the rear. Slots and louvres are single quads.
* The bottle is one closed transparent shell (20 sides, paired hoop ribs)
  plus an inward-facing inner wall, so its far side still renders with
  back-face culling (URP default) and the jug reads full, not as a film.
"""

import bmesh

NAME = "Kit_WaterCooler"
LOD1 = 0.42

WHITE = "Prop_PlasticWhite"
BLACK = "Prop_PlasticBlack"
BOTTLE = "Prop_BottleBlue"
HOT = "Prop_PlasticRed"
COLD = "Prop_BottleBlue"     # translucent blue cold tap (keeps the asset at 4 slots)

W = 0.32          # cabinet width = depth
HW = W / 2
FRONT = -HW


def _bottle_profile():
    """Upturned 5-gallon bottle, (radius, z) from where it leaves the collar
    (cap and neck are hidden inside the cabinet) up to its base."""
    return [
        (0.072, 0.124), (0.108, 0.148), (0.127, 0.165), (0.135, 0.188),   # shoulder
        (0.135, 0.212), (0.129, 0.223), (0.135, 0.236), (0.129, 0.249), (0.135, 0.260),  # rib pair
        (0.135, 0.374), (0.129, 0.385), (0.135, 0.398), (0.129, 0.411), (0.135, 0.422),  # rib pair
        (0.134, 0.446), (0.124, 0.465), (0.100, 0.4725), (0.0, 0.469),    # heel + push-up
    ]


def _inner_wall_profile():
    """Inner surface of the bottle (inside the outer shell's rib valleys),
    shoulder to base; rendered with its normals facing inward."""
    return [(0.072, 0.131), (0.102, 0.152), (0.120, 0.168), (0.126, 0.190),
            (0.126, 0.442), (0.118, 0.460), (0.095, 0.468), (0.0, 0.465)]


def _flip_normals(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def build(kit):
    # ---------------------------------------------------------------- cabinet
    # Recessed black plinth.
    kit.box((0.296, 0.296, 0.026), (0, 0, 0.013), BLACK, bevel=0.0, name="plinth")

    cab_z0, cab_z1 = 0.026, 0.920
    cab_cz, cab_h = (cab_z0 + cab_z1) / 2, cab_z1 - cab_z0
    alc_w, alc_h, alc_cz = 0.19, 0.16, 0.735
    alc_z0, alc_z1 = alc_cz - alc_h / 2, alc_cz + alc_h / 2
    alc_depth = 0.078
    # One white shell, the alcove as a hole through it.
    kit.frame((W, cab_h), (alc_w, alc_h), W, (0, 0, cab_cz), WHITE,
              inner_offset=(0, alc_cz - cab_cz), bevel=0.011, segments=2, name="cabinet")
    kit.box((alc_w + 0.004, 0.010, alc_h + 0.004), (0, FRONT + alc_depth + 0.005, alc_cz), BLACK, bevel=0.0, name="alcove back")
    kit.box((alc_w + 0.004, 0.008, alc_h + 0.004), (0, HW - 0.006, alc_cz), WHITE, bevel=0.0, name="rear service plate")
    # Waist band: the moulded belt between cabinet and head.
    kit.box((W + 0.004, W + 0.004, 0.020), (0, 0, 0.600), WHITE, bevel=0.004, segments=1, name="waist band")

    # Top cap (3 mm overhang) and the dark bottle collar (a dished seat).
    cap_z0, cap_z1 = cab_z1, 0.966
    kit.box((W + 0.006, W + 0.006, cap_z1 - cap_z0), (0, 0, (cap_z0 + cap_z1) / 2), WHITE, bevel=0.016, segments=2, name="top cap")
    kit.lathe([(0.110, cap_z1 - 0.006), (0.110, 0.992), (0.096, 1.002), (0.068, 0.985)], (0, 0, 0), BLACK,
              verts=20, close_top=False, close_bottom=False, name="bottle collar")

    # ------------------------------------------------------------------ taps
    for sx, paddle in ((-0.047, HOT), (0.047, COLD)):
        kit.box((0.040, 0.050, 0.030), (sx, -0.104, alc_z1 - 0.014), WHITE, bevel=0.005, segments=1, name="tap body")
        kit.box((0.034, 0.011, 0.044), (sx, -0.134, alc_z1 - 0.026), paddle, bevel=0.004, segments=1, rot=(-9, 0, 0), name="paddle")
        kit.cylinder(0.0045, 0.026, (sx, -0.108, alc_z1 - 0.042), WHITE, verts=8, bevel=0.0, radius_top=0.0065, name="nozzle")

    # Drip tray: white tub 10 mm proud of the cabinet, black well, white grille.
    tray_w, tray_d = 0.186, 0.088
    tray_y = FRONT - 0.010 + tray_d / 2
    tray_top = alc_z0 + 0.014
    kit.box((tray_w, tray_d, 0.014), (0, tray_y, alc_z0 + 0.007), WHITE, bevel=0.004, segments=1, name="drip tray")
    kit.quad(tray_w - 0.016, tray_d - 0.016, (0, tray_y, tray_top + 0.0006), BLACK, facing="+z", uv="metres", name="tray well")
    for k in range(5):
        kit.quad(tray_w - 0.022, 0.005, (0, tray_y - 0.028 + k * 0.014, tray_top + 0.0018), WHITE,
                 facing="+z", uv="metres", name="grille slat")

    # Above the alcove: dark name plate, hot and cold indicator lamps.
    kit.box((0.078, 0.004, 0.016), (0, FRONT - 0.001, 0.862), BLACK, bevel=0.0, name="name plate")
    for x, lens in ((0.093, HOT), (0.111, COLD)):
        kit.cylinder(0.0045, 0.005, (x, FRONT - 0.001, 0.862), lens, verts=8, rot=(90, 0, 0), bevel=0.0, name="lamp lens")

    # Lower front: compressor air intake (dark well, angled white louvres).
    kit.quad(0.24, 0.066, (0, FRONT - 0.0005, 0.085), BLACK, facing="-y", uv="metres", name="intake well")
    for k in range(4):
        kit.box((0.244, 0.010, 0.0055), (0, FRONT - 0.004, 0.062 + k * 0.015), WHITE, bevel=0.0, rot=(-25, 0, 0), name="intake louvre")
    # Side louvres (both flanks, low and toward the back).
    for sx, facing in ((-1, "-x"), (1, "+x")):
        for k in range(6):
            kit.quad(0.13, 0.006, (sx * (HW + 0.0006), 0.055, 0.078 + k * 0.024), BLACK, facing=facing, uv="metres", name="side louvre")

    # ------------------------------------------------------------------ back
    # Serpentine condenser coil on two brackets, with vertical wire fins.
    cy, xL, xR = HW + 0.024, -0.115, 0.115
    rows, z0, step = 9, 0.11, 0.058
    pts = [(xL, cy, z0)]
    for i in range(rows):
        z = z0 + i * step
        end, s = (xR, 1) if i % 2 == 0 else (xL, -1)
        pts.append((end, cy, z))
        if i < rows - 1:
            pts += [(end + s * 0.016, cy, z + step / 2), (end, cy, z + step)]
    kit.tube(pts, 0.0042, BLACK, verts=4, name="condenser coil")
    z_top = z0 + (rows - 1) * step
    for k in range(8):
        x = xL + 0.012 + k * (xR - xL - 0.024) / 7
        kit.quad(0.003, z_top - z0 + 0.02, (x, cy + 0.0055, (z0 + z_top) / 2), BLACK, facing="+y", uv="metres", name="coil wire")
    for z in (z0 - 0.02, z_top + 0.02):
        kit.box((0.25, 0.030, 0.012), (0, HW + 0.015, z), BLACK, bevel=0.0, name="coil bracket")

    # Hot / cold tank switches on the service plate.
    for x in (-0.03, 0.0):
        kit.box((0.012, 0.008, 0.020), (x, HW + 0.002, 0.80), BLACK, bevel=0.0, name="tank switch")
    # Power cord out of the lower back to the floor, then a plug.
    # (kept within 60 mm of the back so the cooler can stand against a wall)
    kit.tube([(0.10, HW - 0.005, 0.07), (0.10, HW + 0.015, 0.066), (0.102, HW + 0.030, 0.040),
              (0.098, HW + 0.040, 0.004), (0.04, HW + 0.048, 0.004), (-0.04, HW + 0.046, 0.004),
              (-0.10, HW + 0.036, 0.004)], 0.0035, BLACK, verts=4, name="power cord")
    kit.box((0.036, 0.022, 0.014), (-0.125, HW + 0.031, 0.007), BLACK, bevel=0.0, rot=(0, 0, 12), name="plug")

    # ------------------------------------------------- cup dispenser (right)
    tx, ty = HW + 0.044, -0.075
    t0, t1 = 0.585, 0.855
    kit.cylinder(0.037, t1 - t0, (tx, ty, (t0 + t1) / 2), BOTTLE, verts=12, bevel=0.0, name="cup tube")
    kit.lathe([(0.0, t0 + 0.040), (0.030, t0 + 0.004), (0.0345, t0 - 0.004), (0.0345, t1 - 0.030), (0.0, t1 - 0.030)],
              (tx, ty, 0), WHITE, verts=8, name="cup stack")
    for z, h in ((t1 + 0.008, 0.020), (t0 - 0.001, 0.022)):
        kit.cylinder(0.041, h, (tx, ty, z), WHITE, verts=12, bevel=0.0, name="tube cap")
        kit.box((0.016, 0.024, 0.014), (HW + 0.007, ty, z), WHITE, bevel=0.0, name="clamp arm")

    # ---------------------------------------------------------------- bottle
    bottle_z = 0.866
    kit.lathe(_bottle_profile(), (0, 0, bottle_z), BOTTLE, verts=20, close_bottom=False, name="water bottle")
    inner = kit.lathe(_inner_wall_profile(), (0, 0, bottle_z), BOTTLE, verts=16, close_bottom=False, name="bottle inner wall")
    _flip_normals(inner)

    # ---------------------------------------------------------------- meta
    kit.anchor("taps", (0, -0.13, alc_z0 + 0.03))
    kit.anchor("bottle_top", (0, 0, bottle_z + 0.4735))
    top = bottle_z + 0.4735
    kit.collider((0, 0, top / 2), (W + 0.006, W + 0.006, top))
    kit.tag("office", "wall_unit")
    kit.pile("Tall", mass=1, states=["Upright", "Side"])
