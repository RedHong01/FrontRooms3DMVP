"""Beige horizontal desktop PC, c. 1993-97 (the slimline office box the CRT
sits on: Compaq Deskpro / Dell OptiPlex / IBM PC 300 desktop family).

Real-world reference size: 0.42 m wide, 0.40 m deep, 0.12 m tall on four
rubber feet. Painted-steel U cover over a steel chassis, moulded beige front
bezel: a 5.25" bay blank over a 3.5" floppy drive on the right, badge, LEDs,
power / reset buttons, key lock and a ribbed intake grille on the left. Back:
PSU with wire fan guard, IEC inlet + monitor outlet, voltage switch, the I/O
row (PS/2, serial, parallel, VGA) on a shield beside a punched vent field,
three horizontal riser-slot covers; the power cord lies loose behind the case
and ends in its moulded NEMA 5-15P plug. ~5k tris (one CRT + PC + desk per
workstation; small hidden parts are unbevelled on purpose).
The LED lenses use Prop_GlassCRT until an emissive Prop_LED slot exists
(anchors power_led / hdd_led mark them).
Front (bezel) faces -Y. Origin = desk under the feet.
"""

import math

NAME = "Kit_PCDesktop"

BEIGE = "Prop_PlasticBeige"
DARK = "Prop_PlasticGrey"
BLACK = "Prop_PlasticBlack"
STEEL = "Prop_SteelPutty"
CHROME = "Prop_Chrome"
ALU = "Prop_Aluminium"
RUBBER = "Prop_Rubber"
LENS = "Prop_GlassCRT"

W, D, H = 0.42, 0.40, 0.12
FRONT = -0.200          # bezel front face
BEZEL_D = 0.026
COVER_BACK = 0.196      # back face of the steel cover
PANEL = 0.198           # back face of the chassis rear panel (things mount on it)


def _dsub(kit, x, z, width, height, y, shell=ALU, name="d-sub"):
    """D-sub connector on the rear panel: trapezoid shell, dark insert, two
    hex standoffs. width = top edge of the shell."""
    t = height * 0.2
    shell_out = [(-width / 2, height / 2), (width / 2, height / 2), (width / 2 - t, -height / 2), (-width / 2 + t, -height / 2)]
    kit.extrude(shell_out, 0.006, (x, y + 0.003, z), shell, plane="xz", bevel=0.0008, segments=1, name=name + " shell")
    iw, ih = width - 0.004, height - 0.004
    insert = [(-iw / 2, ih / 2), (iw / 2, ih / 2), (iw / 2 - t, -ih / 2), (-iw / 2 + t, -ih / 2)]
    kit.extrude(insert, 0.0062, (x, y + 0.0032, z), BLACK, plane="xz", bevel=0.0, name=name + " insert")
    for sx in (-1, 1):
        kit.cylinder(0.0024, 0.005, (x + sx * (width / 2 + 0.0045), y + 0.0025, z), CHROME, verts=6,
                     rot=(90, 0, 30), bevel=0.0, name=name + " standoff")


def _smooth(points, sub):
    """Catmull-Rom resample of a polyline (cables without kinks)."""
    pts = [tuple(p) for p in points]
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        for k in range(sub):
            t = k / sub
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(3)))
    out.append(pts[-1])
    return out


def _pt_tube(kit, points, radius, slot, verts=8, name="tube", caps=True):
    """Round tube along a polyline with parallel-transport frames: each ring's
    normal is the previous one with the new tangent removed, so the rings
    never flip where the cable turns vertical (kit.tube swaps its reference
    vector there and the quads twist into kinks)."""
    import bmesh
    from mathutils import Vector
    pts = [Vector(p) for p in points]
    n = len(pts)
    tangents = []
    for k in range(n):
        if k == 0:
            t = pts[1] - pts[0]
        elif k == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[k] - pts[k - 1]).normalized() + (pts[k + 1] - pts[k]).normalized()
        tangents.append(t.normalized())
    up = Vector((0, 0, 1))
    nrm = up - tangents[0] * up.dot(tangents[0])
    if nrm.length < 1e-4:
        nrm = Vector((1, 0, 0)) - tangents[0] * tangents[0].x
    nrm.normalize()
    bm = bmesh.new()
    rings = []
    for p, t in zip(pts, tangents):
        nrm = (nrm - t * nrm.dot(t)).normalized()
        b = t.cross(nrm)
        rings.append([bm.verts.new(p + (nrm * math.cos(2 * math.pi * i / verts) + b * math.sin(2 * math.pi * i / verts)) * radius)
                      for i in range(verts)])
    for a, c in zip(rings, rings[1:]):
        for i in range(verts):
            j = (i + 1) % verts
            bm.faces.new((a[i], a[j], c[j], c[i]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _screw(kit, x, y, z, r=0.0034, facing="+y", name="screw"):
    """Pan-head screw seated on a face (facing +y or -y): an 8-sided head
    with a single dark slot (a quad on the head face). ~30 tris."""
    s = 1 if facing == "+y" else -1
    kit.cylinder(r, 0.0024, (x, y + s * 0.0012, z), CHROME, verts=8, rot=(90, 0, 22.5), bevel=0.0, name=name)
    kit.quad(r * 1.3, r * 0.30, (x, y + s * 0.00245, z), BLACK, facing=facing, name=name + " slot", uv="metres")


def _plug(kit, end, prev):
    """Moulded NEMA 5-15P plug lying on the desk at the end of a cord: the
    cord enters the back of the body, the blades point along the cord's last
    tangent (prev -> end). Module-local version of torchiere.plug()."""
    dx, dy = end[0] - prev[0], end[1] - prev[1]
    l = math.hypot(dx, dy) or 1.0
    dx, dy = dx / l, dy / l
    rz = math.degrees(math.atan2(dy, dx))          # body length runs along local X
    sx, sy = -dy, dx                                # across the plug
    c = (end[0] + dx * 0.015, end[1] + dy * 0.015)
    kit.box((0.030, 0.020, 0.014), (c[0], c[1], 0.007), BLACK, bevel=0.003, segments=1, rot=(0, 0, rz), name="plug body")
    kit.box((0.004, 0.016, 0.010), (c[0] - dx * 0.0165, c[1] - dy * 0.0165, 0.0058), BLACK, bevel=0.0015, segments=1,
            rot=(0, 0, rz), name="plug strain relief")
    for o in (-0.0063, 0.0063):
        kit.box((0.0065, 0.0015, 0.0065), (c[0] + dx * 0.0182 + sx * o, c[1] + dy * 0.0182 + sy * o, 0.0085),
                CHROME, bevel=0.0, rot=(0, 0, rz), name="plug blade")
    kit.cylinder(0.0022, 0.006, (c[0] + dx * 0.0175, c[1] + dy * 0.0175, 0.0036), CHROME, verts=8,
                 rot=(0, 90, rz), bevel=0.0, name="plug ground pin")


def build(kit):
    # ------------------------------------------------------------ chassis
    # Rubber feet and the steel bottom pan showing as a darker band under the cover.
    for sx in (-1, 1):
        for sy in (-1, 1):
            kit.cylinder(0.010, 0.006, (sx * 0.172, sy * 0.150, 0.003), RUBBER, verts=6, bevel=0.0, name="foot")
    kit.box((0.406, 0.372, 0.008), (0, 0.006, 0.010), STEEL, bevel=0.0015, segments=1, name="bottom pan")
    # Painted steel U-cover (top + sides): crisp sheet-metal radius.
    cover_front = -0.176
    cover_len = COVER_BACK - cover_front
    kit.box((0.414, cover_len, 0.110), (0, (COVER_BACK + cover_front) / 2, 0.064), BEIGE,
            bevel=0.0035, segments=3, name="steel cover")
    # Pressed stiffening swage across the top, 60 mm in from the back edge.
    kit.box((0.396, 0.006, 0.0016), (0, 0.132, 0.1190), BEIGE, bevel=0.0007, segments=1, name="cover swage")

    # Side vents: punched slots in the cover sides near the front (intake)
    # and at the back on the PSU side (exhaust).
    for sx in (-1, 1):
        for row in range(4):
            for col in range(7):
                y = -0.140 + col * 0.016
                z = 0.046 + row * 0.011
                kit.quad(0.011, 0.0032, (sx * 0.2072, y, z), BLACK, facing="+x" if sx > 0 else "-x", name="side vent", uv="metres")
    for row in range(5):
        for col in range(4):
            kit.quad(0.011, 0.0032, (-0.2072, 0.112 + col * 0.016, 0.040 + row * 0.011), BLACK, facing="-x", name="psu vent", uv="metres")

    # ------------------------------------------------------------ front bezel
    bay_x = 0.095
    bezel_zc = 0.063
    bezel_h = 0.114
    bay525_z = 0.088
    hole_w, hole_h = 0.152, 0.046
    kit.frame((W, bezel_h), (hole_w, hole_h), BEZEL_D, (0, FRONT + BEZEL_D / 2, bezel_zc), BEIGE,
              inner_offset=(bay_x, bay525_z - bezel_zc), bevel=0.007, segments=3, name="front bezel")
    # Accent groove along the bottom of the bezel (moulded plinth line).
    kit.box((W - 0.02, 0.002, 0.0022), (0, FRONT - 0.0002, 0.018), DARK, bevel=0.0, name="bezel plinth groove")

    # 5.25" bay: dark cavity behind, a blank plate recessed 3 mm with a 2 mm shut line.
    kit.box((hole_w - 0.002, 0.004, hole_h - 0.002), (bay_x, FRONT + 0.016, bay525_z), BLACK, bevel=0.0, name="5.25 bay cavity")
    kit.box((0.146, 0.006, 0.040), (bay_x, FRONT + 0.006, bay525_z), BEIGE, bevel=0.0018, segments=1, name="5.25 bay blank")
    kit.box((0.022, 0.0015, 0.0035), (bay_x, FRONT + 0.0025, bay525_z - 0.012), DARK, bevel=0.0006, segments=1, name="blank finger notch")

    # 3.5" floppy drive in a raised bezel insert.
    fz = 0.040
    kit.frame((0.122, 0.036), (0.106, 0.026), 0.006, (bay_x, FRONT - 0.002, fz), BEIGE,
              bevel=0.002, segments=1, name="floppy insert")
    kit.box((0.104, 0.004, 0.024), (bay_x, FRONT - 0.0005, fz), BEIGE, bevel=0.0012, segments=1, name="floppy face")
    kit.box((0.094, 0.003, 0.0055), (bay_x, FRONT - 0.002, fz + 0.003), BLACK, bevel=0.0008, segments=1, name="floppy slot")
    kit.box((0.090, 0.0016, 0.0032), (bay_x, FRONT - 0.0034, fz + 0.0032), DARK, bevel=0.0005, segments=1, name="floppy dust flap")
    kit.box((0.017, 0.007, 0.0065), (bay_x + 0.036, FRONT - 0.0045, fz - 0.0068), BEIGE, bevel=0.0015, segments=1, name="floppy eject button")
    kit.box((0.006, 0.003, 0.0025), (bay_x - 0.040, FRONT - 0.0024, fz - 0.0072), LENS, bevel=0.0, name="floppy busy LED")

    # Left half: badge, LEDs, power + reset, key lock, intake grille.
    upper_z = 0.088
    kit.box((0.056, 0.0016, 0.014), (-0.150, FRONT - 0.0008, upper_z + 0.002), ALU, bevel=0.0007, segments=1, name="badge plate")
    kit.box((0.048, 0.0012, 0.008), (-0.150, FRONT - 0.0016, upper_z + 0.002), DARK, bevel=0.0, name="badge field")
    kit.box((0.014, 0.0010, 0.0028), (-0.163, FRONT - 0.0022, upper_z + 0.002), ALU, bevel=0.0, name="badge logo")
    kit.box((0.022, 0.0010, 0.0028), (-0.140, FRONT - 0.0022, upper_z + 0.002), ALU, bevel=0.0, name="badge logo")

    # Power (green) and disk-activity (amber) LEDs in a dark window.
    kit.box((0.026, 0.0012, 0.009), (-0.082, FRONT - 0.0006, upper_z), DARK, bevel=0.0, name="LED window")
    for k, lx in enumerate((-0.088, -0.076)):
        kit.cylinder(0.0021, 0.003, (lx, FRONT - 0.0015, upper_z), LENS, verts=8, rot=(90, 0, 0), bevel=0.0, name="LED lens")

    # Power button: square push button standing in a dark well (frame).
    px, pz = -0.040, upper_z
    kit.frame((0.028, 0.028), (0.021, 0.021), 0.005, (px, FRONT - 0.0005, pz), DARK, bevel=0.0012, segments=1, name="power well")
    kit.box((0.019, 0.010, 0.019), (px, FRONT - 0.002, pz), BEIGE, bevel=0.003, segments=2, name="power button")
    kit.box((0.006, 0.0008, 0.0016), (px, FRONT - 0.0072, pz + 0.004), DARK, bevel=0.0, name="power mark")
    # Reset: small round pin-button in a ring.
    rz = 0.061
    kit.cylinder(0.0050, 0.002, (px, FRONT - 0.0008, rz), DARK, verts=12, rot=(90, 0, 0), bevel=0.0, name="reset ring")
    kit.cylinder(0.0034, 0.004, (px, FRONT - 0.0018, rz), BEIGE, verts=12, rot=(90, 0, 0), bevel=0.0012, segments=1, name="reset button")
    # Key lock (chrome cylinder, keyway).
    lz = 0.036
    kit.cylinder(0.0075, 0.004, (px, FRONT - 0.0018, lz), CHROME, verts=14, rot=(90, 0, 0), bevel=0.0015, segments=1, name="key lock")
    kit.cylinder(0.0050, 0.003, (px, FRONT - 0.0026, lz), ALU, verts=12, rot=(90, 0, 0), bevel=0.0, name="lock plug")
    kit.box((0.0012, 0.0010, 0.0060), (px, FRONT - 0.0042, lz), BLACK, bevel=0.0, name="keyway")

    # Intake grille: dark backing and raised moulded ribs.
    gx, gz, gw = -0.128, 0.040, 0.118
    kit.box((gw + 0.004, 0.0014, 0.036), (gx, FRONT - 0.0003, gz), BLACK, bevel=0.0, name="grille backing")
    for i in range(6):
        kit.box((gw, 0.0042, 0.0030), (gx, FRONT - 0.0018, gz - 0.0150 + i * 0.0060), BEIGE, bevel=0.001, segments=1, name="grille rib")
    for sx in (-1, 1):
        kit.box((0.0030, 0.0042, 0.036), (gx + sx * (gw / 2 + 0.0005), FRONT - 0.0018, gz), BEIGE, bevel=0.0, name="grille end")

    # ------------------------------------------------------------ rear panel
    kit.box((0.398, 0.004, 0.092), (0, COVER_BACK, 0.061), STEEL, bevel=0.0012, segments=1, name="rear panel")
    # Cover thumb screws along the top lip.
    for sx in (-0.17, 0.0, 0.17):
        _screw(kit, sx, COVER_BACK, 0.1125, r=0.0040, name="cover screw")

    # PSU block (left when seen from the back = +x... at -x in asset space).
    psu_x = -0.120
    kit.box((0.150, 0.0016, 0.086), (psu_x, PANEL + 0.0008, 0.061), STEEL, bevel=0.0, name="psu plate")
    for sx in (-1, 1):
        for sz in (-1, 1):
            _screw(kit, psu_x + sx * 0.068, PANEL + 0.0016, 0.061 + sz * 0.037, r=0.0026, name="psu screw")
    # Fan: dark opening, hub and blades, wire guard.
    fan_x, fan_z, fan_r = -0.150, 0.066, 0.034
    kit.cylinder(fan_r, 0.0012, (fan_x, PANEL + 0.0023, fan_z), BLACK, verts=20, rot=(90, 0, 0), bevel=0.0, name="fan opening")
    kit.cylinder(0.012, 0.003, (fan_x, PANEL + 0.0038, fan_z), DARK, verts=12, rot=(90, 0, 0), bevel=0.0, name="fan hub")
    for k in range(7):
        a = 360.0 / 7 * k
        r = 0.022
        ar = math.radians(a)
        kit.box((0.019, 0.0012, 0.011), (fan_x + math.cos(ar) * r, PANEL + 0.0035, fan_z + math.sin(ar) * r), DARK,
                rot=(25, -a, 0), bevel=0.0, name="fan blade")
    gy = PANEL + 0.0068
    for rr, n in ((0.032, 20), (0.022, 14)):
        pts = [(fan_x + math.cos(2 * math.pi * i / n) * rr, gy, fan_z + math.sin(2 * math.pi * i / n) * rr) for i in range(n + 1)]
        kit.tube(pts, 0.0008, CHROME, verts=3, name="fan guard ring", caps=False)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        kit.tube([(fan_x + math.cos(a) * 0.006, gy, fan_z + math.sin(a) * 0.006),
                  (fan_x + math.cos(a) * 0.035, gy, fan_z + math.sin(a) * 0.035)], 0.0008, CHROME, verts=3, name="fan guard spoke")

    # IEC C14 inlet and C13 monitor outlet, voltage selector.
    def iec(x, z, female, name):
        body = [(-0.0155, 0.0115), (0.0155, 0.0115), (0.0155, -0.0045), (0.010, -0.0115), (-0.010, -0.0115), (-0.0155, -0.0045)]
        kit.extrude(body, 0.006, (x, PANEL + 0.003, z), BLACK, plane="xz", bevel=0.0012, segments=1, name=name + " body")
        well = [(-0.0115, 0.0080), (0.0115, 0.0080), (0.0115, -0.0030), (0.0075, -0.0080), (-0.0075, -0.0080), (-0.0115, -0.0030)]
        kit.extrude(well, 0.0062, (x, PANEL + 0.0032, z), RUBBER, plane="xz", bevel=0.0, name=name + " well")
        if female:
            for px_, pz_ in ((-0.0045, 0.002), (0.0045, 0.002), (0.0, -0.004)):
                kit.box((0.0015, 0.0010, 0.0035), (x + px_, PANEL + 0.0064, z + pz_), BLACK, bevel=0.0, name=name + " socket hole")
        else:
            for px_, pz_ in ((-0.0045, 0.002), (0.0045, 0.002), (0.0, -0.0035)):
                kit.box((0.0012, 0.0040, 0.0035), (x + px_, PANEL + 0.0050, z + pz_), CHROME, bevel=0.0, name=name + " pin")
    iec(-0.092, 0.040, False, "power inlet")
    iec(-0.092, 0.084, True, "monitor outlet")
    kit.box((0.016, 0.004, 0.009), (-0.185, PANEL + 0.002, 0.030), BLACK, bevel=0.0, name="voltage switch housing")
    kit.box((0.006, 0.004, 0.006), (-0.188, PANEL + 0.004, 0.030), DARK, bevel=0.0, name="voltage slider")

    # Moulded power-cord plug in the inlet; the cord drops to the desk and runs off back.
    kit.box((0.026, 0.024, 0.020), (-0.092, PANEL + 0.012 + 0.004, 0.040), BLACK, bevel=0.004, segments=1, name="inlet plug")
    kit.cylinder(0.0042, 0.016, (-0.092, PANEL + 0.034, 0.038), BLACK, verts=10, rot=(90, 0, 0), bevel=0.0015, segments=1, radius_top=0.0060, name="inlet plug strain relief")
    # The cord lies loose behind the case and ends in its (unplugged) wall plug,
    # kept inside the case's left edge and the old 0.281 m depth.
    ctrl = [(-0.092, PANEL + 0.040, 0.038), (-0.092, PANEL + 0.050, 0.035), (-0.093, PANEL + 0.058, 0.024),
            (-0.095, PANEL + 0.061, 0.010), (-0.101, PANEL + 0.064, 0.0036), (-0.120, PANEL + 0.064, 0.0036),
            (-0.142, PANEL + 0.057, 0.0036), (-0.160, PANEL + 0.053, 0.0040), (-0.172, PANEL + 0.058, 0.0052)]
    cord = _smooth(ctrl, 3)
    cord = [(x, y, max(z, 0.0036)) for x, y, z in cord]
    _pt_tube(kit, cord, 0.0036, BLACK, verts=8, name="power cord")
    _plug(kit, ctrl[-1], ctrl[-2])

    # I/O shield and connector row (lower right seen from the back = +x).
    io_z = 0.036
    kit.box((0.140, 0.0012, 0.040), (0.053, PANEL + 0.0006, io_z), STEEL, bevel=0.0, name="io shield")
    # Punched ventilation field in the bare rear panel beside the I/O shield.
    for row in range(3):
        for col in range(5):
            kit.quad(0.0105, 0.0030, (0.140 + col * 0.0135, PANEL + 0.0002, 0.026 + row * 0.0085), BLACK,
                     facing="+y", name="rear vent", uv="metres")
    # PS/2 keyboard + mouse (round mini-DIN).
    for k, (x, z) in enumerate(((-0.005, io_z + 0.008), (-0.005, io_z - 0.009))):
        kit.cylinder(0.0062, 0.003, (x, PANEL + 0.0015, z), ALU, verts=10, rot=(90, 0, 0), bevel=0.0, name="ps2 shell")
        kit.cylinder(0.0045, 0.0032, (x, PANEL + 0.0017, z), BLACK, verts=10, rot=(90, 0, 0), bevel=0.0, name="ps2 insert")
    _dsub(kit, 0.045, io_z + 0.007, 0.040, 0.010, PANEL, name="parallel port")
    _dsub(kit, 0.045, io_z - 0.010, 0.024, 0.009, PANEL, name="serial A")
    _dsub(kit, 0.100, io_z - 0.010, 0.024, 0.009, PANEL, name="serial B")
    _dsub(kit, 0.100, io_z + 0.007, 0.024, 0.0095, PANEL, name="VGA")
    # USB was not on these yet; an RJ-45 network jack on the riser card instead (below).

    # Riser expansion slots: three horizontal covers, the middle one a sound card.
    for k in range(3):
        sz = 0.066 + k * 0.014
        kit.box((0.150, 0.0016, 0.0115), (0.110, PANEL + 0.0008, sz), STEEL, bevel=0.0, name="slot cover")
        _screw(kit, 0.182, PANEL + 0.0016, sz, r=0.0026, name="slot screw")
    card_z = 0.080
    _dsub(kit, 0.070, card_z, 0.030, 0.0085, PANEL + 0.0016, name="game port")
    for k in range(3):
        x = 0.110 + k * 0.014
        kit.cylinder(0.0036, 0.004, (x, PANEL + 0.0035, card_z), BLACK, verts=8, rot=(90, 0, 0), bevel=0.0, name="audio jack")
        kit.cylinder(0.0016, 0.0042, (x, PANEL + 0.0037, card_z), RUBBER, verts=6, rot=(90, 0, 0), bevel=0.0, name="audio jack hole")
    kit.box((0.014, 0.004, 0.0095), (0.155, PANEL + 0.002, 0.094), BLACK, bevel=0.0008, segments=1, name="rj45 jack")
    kit.box((0.010, 0.0008, 0.006), (0.155, PANEL + 0.0042, 0.093), RUBBER, bevel=0.0, name="rj45 opening")

    kit.support("top", (0, 0, H), (0.38, 0.36))
    kit.anchor("monitor", (0, -0.01, H))
    kit.anchor("power_led", (-0.088, FRONT - 0.003, upper_z))
    kit.anchor("hdd_led", (-0.076, FRONT - 0.003, upper_z))
    kit.collider((0, 0.0, H / 2), (W, D, H))
    kit.tag("office", "electronics", "desk_top", "pile_piece")
    kit.pile("Crate", mass=1, palette="office90s")
