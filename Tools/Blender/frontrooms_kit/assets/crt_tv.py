"""Black 21-inch CRT television, c. 1993-99 (the living-room / motel set:
black textured cabinet, flat-square tube behind a rounded bezel, slotted
speaker grilles either side of the tube, a chin with power button, standby
LED, IR window, nameplate and a small control strip, a steeply tapered
rear cabinet with vent slots, AV terminal block and a rating label).

Real-world reference size: 0.62 m wide, 0.50 m tall, 0.48 m deep. Visible
picture about 0.41 x 0.31 m (20" V); the glass sits 15-35 mm behind the
bezel face and bulges ~20 mm. The cabinet bottom is flat (it stands on four
moulded feet), so the rear taper is all on the top and sides.
Front (screen) faces -Y. Origin = floor under the cabinet centre.
Film: Still B, the black CRT on top of the pile facing the camera.
"""

import math

from mathutils import Vector

NAME = "Kit_CRTTV"

BLACK = "Prop_PlasticBlack"
GREY = "Prop_PlasticGrey"
DARK = "Prop_Rubber"
GLASS = "Prop_GlassCRT"

W, D, H = 0.62, 0.48, 0.50
FOOT = 0.008                     # cabinet bottom above the floor
ZC = FOOT + (H - FOOT) / 2       # cabinet centre height
FRONT = -D / 2                   # bezel face
OPEN_W, OPEN_H = 0.445, 0.336    # tube opening in the bezel
OPEN_TOP = H - 0.048
OPEN_CZ = OPEN_TOP - OPEN_H / 2

# Rear cabinet: front and back rectangles of the taper, back dropped so the
# bottom stays flat.
LOFT_Y0, LOFT_Y1 = -0.070, 0.192
LOFT_FRONT = (0.586, 0.462)
LOFT_BACK = (0.400, 0.300)
LOFT_ZC = ZC - 0.002
LOFT_DROP = -0.080


def smooth_path(points, sub=4):
    """Catmull-Rom through the control points (cords that sag, not kink)."""
    pts = [Vector(p) for p in points]
    ext = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(ext) - 2):
        p0, p1, p2, p3 = ext[i - 1], ext[i], ext[i + 1], ext[i + 2]
        for s in range(sub):
            t = s / sub
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t))
    out.append(pts[-1])
    return [tuple(v) for v in out]


def chamfered_section(depth, height, c):
    """(y, z) outline of a bar ``depth`` deep (front at -depth/2, facing -Y)
    and ``height`` tall whose two front edges are chamfered by ``c``."""
    d, h = depth / 2, height / 2
    return [(d, -h), (-d + c, -h), (-d, -h + c), (-d, h - c), (-d + c, h), (d, h)]


def build(kit):
    # ------------------------------------------------------------ cabinet
    # Bezel: one rounded frame with the tube opening set high (deep chin).
    kit.frame((W, H - FOOT), (OPEN_W, OPEN_H), 0.045, (0, FRONT + 0.0225, ZC), BLACK,
              inner_offset=(0, OPEN_CZ - ZC), bevel=0.016, segments=3, name="bezel")
    # Body block behind the bezel (7 mm inset = the bezel/cabinet seam).
    kit.box((W - 0.014, 0.135, H - FOOT - 0.012), (0, -0.1325, ZC), BLACK, bevel=0.010, segments=2,
            name="front cabinet")
    # Tapered rear cabinet (flat bottom, steep top/side draft).
    depth = LOFT_Y1 - LOFT_Y0
    kit.loft_box(LOFT_FRONT, LOFT_BACK, depth, (0, (LOFT_Y0 + LOFT_Y1) / 2, LOFT_ZC), BLACK,
                 back_offset=(0, LOFT_DROP), bevel=0.014, segments=3, name="rear cabinet")
    back_cz = LOFT_ZC + LOFT_DROP
    # Neck housing bump on the back.
    cap_h = 0.20
    kit.box((0.29, 0.042, cap_h), (0, LOFT_Y1 + 0.015, back_cz + 0.005), BLACK, bevel=0.012, segments=2,
            name="neck housing")
    back_y = LOFT_Y1 + 0.036     # rear face of the neck housing
    # Moulded feet (front pair under the body, rear pair under the taper).
    for x, y, h in ((-0.25, -0.17, 0.016), (0.25, -0.17, 0.016), (-0.17, 0.15, 0.026), (0.17, 0.15, 0.026)):
        kit.cylinder(0.017, h, (x, y, h / 2), DARK, verts=8, bevel=0.002, segments=1, name="foot")

    # ------------------------------------------------------------- tube
    kit.box((OPEN_W + 0.01, 0.02, OPEN_H + 0.01), (0, FRONT + 0.050, OPEN_CZ), BLACK, bevel=0.0,
            name="tube mask")
    kit.bulged_panel(OPEN_W + 0.006, OPEN_H + 0.006, 0.020, (0, FRONT + 0.036, OPEN_CZ), "Prop_ScreenCRT",
                     segments=12, name="screen glass")

    # --------------------------------------------------- speaker grilles
    side = (W - OPEN_W) / 4 + OPEN_W / 2      # centre of the side border
    gh = OPEN_H - 0.05
    for sx in (-1, 1):
        kit.box((0.050, 0.002, gh + 0.010), (sx * side, FRONT - 0.0005, OPEN_CZ), DARK, bevel=0.0008,
                segments=1, name="grille backing")
        # Bars and rails are extruded sections with 0.9 mm chamfers on the
        # front edges (20 tris each instead of a 44-tri bevelled box); the
        # bar ends hide under the rails.
        n = 14
        pitch = gh / n
        bar = chamfered_section(0.004, pitch * 0.42, 0.0009)
        for i in range(n + 1):
            kit.extrude(bar, 0.050, (sx * side, FRONT - 0.0015, OPEN_CZ - gh / 2 + i * pitch), BLACK,
                        plane="yz", bevel=0.0, name="grille bar")
        rail = [(x, y) for y, x in chamfered_section(0.004, 0.003, 0.0008)]
        for xx in (-0.026, 0.026):
            kit.extrude(rail, gh + 0.010, (sx * side + xx, FRONT - 0.0015, OPEN_CZ), BLACK,
                        plane="xy", bevel=0.0, name="grille rail")

    # ------------------------------------------------------------- chin
    chin_z = FOOT + (OPEN_CZ - OPEN_H / 2 - FOOT) / 2
    fy = FRONT - 0.0005
    # Power button in a dark recess ring, standby LED, IR window.
    kit.cylinder(0.0145, 0.004, (-0.235, fy + 0.0005, chin_z), DARK, verts=16, rot=(90, 0, 0), bevel=0.0,
                 name="power recess")
    kit.cylinder(0.0115, 0.010, (-0.235, fy - 0.002, chin_z), BLACK, verts=16, rot=(90, 0, 0), bevel=0.002,
                 segments=1, name="power button")
    kit.cylinder(0.0028, 0.003, (-0.205, fy - 0.0005, chin_z + 0.012), GLASS, verts=8, rot=(90, 0, 0),
                 bevel=0.0, name="standby led")
    kit.box((0.036, 0.003, 0.016), (-0.160, fy - 0.0005, chin_z + 0.004), GLASS, bevel=0.001, segments=1,
            name="ir window")
    # Nameplate.
    kit.box((0.078, 0.002, 0.012), (0, fy - 0.0005, chin_z + 0.020), "Prop_Aluminium", bevel=0.0008,
            segments=1, name="nameplate")
    # Control strip: grey recessed panel with six rocker/push keys.
    kit.box((0.170, 0.002, 0.024), (0.180, fy, chin_z - 0.002), GREY, bevel=0.0008, segments=1,
            name="control strip")
    for k in range(6):
        kit.box((0.019, 0.006, 0.011), (0.180 - 0.0675 + k * 0.027, fy - 0.003, chin_z - 0.002), BLACK,
                bevel=0.0018, segments=1, name="control key")
    # Moulded design line across the chin.
    kit.box((W - 0.06, 0.002, 0.0025), (0, fy, OPEN_CZ - OPEN_H / 2 - 0.016), DARK, bevel=0.0,
            name="chin groove")

    # ------------------------------------------------- rear vent slots
    # Fins across the sloping top of the rear cabinet over a dark slot bed.
    fz = LOFT_ZC + LOFT_FRONT[1] / 2
    bz = back_cz + LOFT_BACK[1] / 2
    slope = math.atan2(fz - bz, depth)
    for s0 in range(13):
        s = 0.16 + s0 * 0.052
        y = LOFT_Y0 + depth * s
        z = fz + (bz - fz) * s
        w = LOFT_FRONT[0] + (LOFT_BACK[0] - LOFT_FRONT[0]) * s
        nrm = Vector((0, math.sin(slope), math.cos(slope)))
        p = Vector((0, y, z)) + nrm * 0.0003
        for sx in (-1, 1):
            ln = w / 2 - 0.075
            kit.box((ln, 0.0065, 0.0008), (sx * (0.035 + ln / 2), p.y, p.z), DARK, bevel=0.0,
                    rot=(-math.degrees(slope), 0, 0), name="top vent slot")

    # Vent slots on the neck housing and the back panel.
    for i in range(7):
        kit.box((0.090, 0.002, 0.0055), (0.075, back_y + 0.0005, back_cz - 0.07 + i * 0.016), DARK,
                bevel=0.0, name="rear vent slot")
    # AV terminal block: grey plate, F connector, three RCA jacks.
    kit.box((0.100, 0.004, 0.060), (-0.075, back_y + 0.001, back_cz - 0.039), GREY, bevel=0.0015,
            segments=1, name="av plate")
    kit.cylinder(0.0055, 0.008, (-0.105, back_y + 0.007, back_cz - 0.024), "Prop_Chrome", verts=6,
                 rot=(90, 0, 0), bevel=0.0008, segments=1, name="antenna f connector")
    kit.cylinder(0.0030, 0.005, (-0.105, back_y + 0.0135, back_cz - 0.024), "Prop_Chrome", verts=8,
                 rot=(90, 0, 0), bevel=0.0, name="f connector thread")
    for k in range(3):
        x = -0.080 + k * 0.022
        kit.cylinder(0.0050, 0.010, (x, back_y + 0.008, back_cz - 0.052), "Prop_Brass", verts=8,
                     rot=(90, 0, 0), bevel=0.0008, segments=1, name="rca jack")
        # Dark socket bore, flush with the jack face (0.3 mm proud).
        kit.cylinder(0.0022, 0.003, (x, back_y + 0.0118, back_cz - 0.052), DARK, verts=6,
                     rot=(90, 0, 0), bevel=0.0, name="rca hole")
    # Rating label and four cabinet screws.
    kit.quad(0.085, 0.050, (-0.010, back_y + 0.0012, back_cz + 0.060), "Prop_Label", facing="+y",
             name="rating label")
    # (Bottom pair at -0.078 so they sit on the housing's flat face, inside its 12 mm bevel.)
    for x, z in ((-0.125, back_cz + 0.085), (0.125, back_cz + 0.085), (-0.125, back_cz - 0.078),
                 (0.125, back_cz - 0.078)):
        kit.cylinder(0.0045, 0.003, (x, back_y + 0.0012, z), "Prop_SteelBlack", verts=8, rot=(90, 0, 0),
                     bevel=0.0, name="cabinet screw")

    # ------------------------------------------------------------- cord
    # Leaves the underside of the taper, drops to the floor and lies along
    # the back edge (kept inside the cabinet footprint for pile stacking).
    kit.tube(smooth_path([(0.10, 0.150, 0.028), (0.104, 0.166, 0.012), (0.115, 0.182, 0.0041),
                          (0.160, 0.200, 0.0041), (0.215, 0.208, 0.0041), (0.250, 0.214, 0.0041)], 3),
             0.0035, BLACK, verts=6, name="power cord")
    kit.box((0.034, 0.024, 0.018), (0.2735, 0.2185, 0.009), BLACK, bevel=0.005, segments=1, rot=(0, 0, 10),
            name="plug body")
    for dy in (-0.0055, 0.0055):
        kit.box((0.014, 0.0018, 0.0065), (0.2965, 0.2225 + dy, 0.0095), "Prop_Chrome", bevel=0.0,
                rot=(0, 0, 10), name="plug blade")

    # Flat top of the front cabinet behind the bezel crown (bezel is all bevel on top).
    kit.support("top", (0, -0.1325, H - 0.006), (0.58, 0.115))
    kit.anchor("screen", (0, FRONT - 0.005, OPEN_CZ))
    kit.collider((0, -0.15, ZC), (W, 0.18, H - FOOT))
    # Tapered rear cabinet as three steps, so stacked props rest on its slope.
    kit.collider((0, -0.0225, 0.235), (0.58, 0.085, 0.43))
    kit.collider((0, 0.065, 0.21), (0.50, 0.09, 0.38))
    kit.collider((0, 0.169, 0.18), (0.44, 0.118, 0.32))
    kit.tag("pile", "electronics", "screen", "domestic")
    kit.pile("Screen", mass=1, palette="domestic70s", topper=True)
