"""Beige horizontal desktop PC, c. 1993-97 (the slimline office box the CRT
sits on: Compaq Deskpro / Dell OptiPlex / IBM PC 300 desktop family).

Real-world reference size (synthesis §5.3): 0.42 m wide, 0.42 m deep,
0.14 m tall on four rubber feet. Painted-steel U cover over a steel chassis,
moulded beige front bezel standing 3 mm proud of the cover all round (its
back lip closes the step): a 5.25" bay blank over a 3.5" floppy drive on the
right, nameplate, LED window, power / reset buttons, key lock and a ribbed
intake grille on the left; louvres in the cover sides. The machine is OFF
(the office is abandoned and the CRTs are dark): no lit LED. The anchors
power_led / hdd_led mark the lenses for a runtime glow if a level wants one
PC still humming. Back: PSU with its fan guard, IEC inlet + monitor outlet, the
I/O row (PS/2, serial, parallel, VGA), riser-slot covers with a sound card's
game port and jacks; the power cord lies loose behind the case and ends in
its moulded NEMA 5-15P plug.
Front (bezel) faces -Y. Origin = desk under the feet.

Budget (synthesis §5.3): 900 LOD0 / 350 LOD1 tris, 1 collider, pile Small 1,
3 slots: PlasticBeige, PlasticBlack, SteelPutty (rear panel, badge, lock,
connector shells; painted, non-metallic). LOD1 is authored
(_deskgear.authored_lod1): rear-panel I/O, cord and plug, grille ribs,
buttons, lock and small trims are LOD0-only; flat stand-ins (striped grille,
button and lock faces, one dark I/O field) take their place at LOD1.
How: every part is built from only the faces that can show (_deskgear:
face_box / box_faces / disc / rings_mesh); the bezel and cover are ring-built
with rounded front / top edges instead of bevel modifiers; screws, socket
holes, the keyway detail and fan blades (< 5 mm at 2 m) are gone.
"""

import math

import bmesh
from mathutils import Vector

import _deskgear as dg

NAME = "Kit_PCDesktop"
LOD1 = 0.42                # any number: the LOD1 is authored (see build), not decimated

BEIGE = "Prop_PlasticBeige"
BLACK = "Prop_PlasticBlack"
STEEL = "Prop_SteelPutty"

W, D, H = 0.42, 0.42, 0.14
FRONT = -D / 2          # bezel front face
BEZEL_D = 0.026
BEZEL_BACK = FRONT + BEZEL_D
BEZEL_Z0, BEZEL_Z1 = 0.006, H
PANEL = D / 2 - 0.002   # back face of the case (cover end + rear panel); things mount on it
COVER_FRONT = BEZEL_BACK - 0.002    # the cover tucks 2 mm into the bezel's back lip
COVER_Z0 = 0.012        # cover bottom edge (the steel pan shows below it)
COVER_TOP = H - 0.0005
COVER_HW = W / 2 - 0.003            # the bezel stands 3 mm proud of the cover all round
COVER_R = 0.004


def zr(z):
    """Heights laid out on the old 0.12 m case -> the 0.14 m case."""
    return BEZEL_Z0 + (z - BEZEL_Z0) * (BEZEL_Z1 - BEZEL_Z0) / (0.120 - BEZEL_Z0)


def _cover_profile(r=COVER_R, seg=3):
    """(x, z) section of the U cover: up the left side, over the rounded top
    corners, down the right side; open at the bottom."""
    pts = [(-COVER_HW, COVER_Z0)]
    for k in range(seg + 1):
        a = math.radians(180 - 90 * k / seg)
        pts.append((-COVER_HW + r + r * math.cos(a), COVER_TOP - r + r * math.sin(a)))
    for k in range(seg + 1):
        a = math.radians(90 - 90 * k / seg)
        pts.append((COVER_HW - r + r * math.cos(a), COVER_TOP - r + r * math.sin(a)))
    pts.append((COVER_HW, COVER_Z0))
    return pts


def _bezel(kit, hole_w, hole_h, hole_x, hole_z, z0, z1, rr=0.006, seg=3):
    """Moulded front bezel: front face with the 5.25" bay opening, its
    perimeter rolled back over ``rr`` in ``seg`` steps, short side walls to
    the cover, and the bay's cavity walls. ~48 tris (a frame + bevel
    modifier was 448)."""
    hw = W / 2

    def rect(inset, y):
        return [(-hw + inset, y, z0 + inset), (hw - inset, y, z0 + inset), (hw - inset, y, z1 - inset), (-hw + inset, y, z1 - inset)]
    rings = []
    for k in range(seg + 1):
        a = math.radians(90.0 * k / seg)
        rings.append(rect(rr * (1 - math.sin(a)), FRONT + rr * (1 - math.cos(a))))
    rings.append(rect(0.0, BEZEL_BACK))
    bm = bmesh.new()
    vr = [[bm.verts.new(p) for p in r] for r in rings]
    hx0, hx1, hz0, hz1 = hole_x - hole_w / 2, hole_x + hole_w / 2, hole_z - hole_h / 2, hole_z + hole_h / 2
    h0 = [bm.verts.new(p) for p in ((hx0, FRONT, hz0), (hx1, FRONT, hz0), (hx1, FRONT, hz1), (hx0, FRONT, hz1))]
    h1 = [bm.verts.new(p) for p in ((hx0, FRONT + 0.016, hz0), (hx1, FRONT + 0.016, hz0), (hx1, FRONT + 0.016, hz1),
                                    (hx0, FRONT + 0.016, hz1))]
    for i in range(4):
        j = (i + 1) % 4
        bm.faces.new((vr[0][j], vr[0][i], h0[i], h0[j]))            # front face band
        for a_, b_ in zip(vr, vr[1:]):
            bm.faces.new((a_[i], a_[j], b_[j], b_[i]))              # roll + side walls
        bm.faces.new((h0[i], h0[j], h1[j], h1[i]))                  # bay cavity walls
    bm.normal_update()
    # Front band faces -Y, roll/sides face outward, cavity walls face inward.
    for f in bm.faces:
        c = f.calc_center_median()
        inside_hole = hx0 - 1e-6 <= c.x <= hx1 + 1e-6 and hz0 - 1e-6 <= c.z <= hz1 + 1e-6 and c.y > FRONT + 1e-5
        if inside_hole:
            want = (hole_x - c.x, 0.0, hole_z - c.z)
        elif abs(c.y - FRONT) < 1e-6:
            want = (0.0, -1.0, 0.0)
        else:
            want = (c.x, 0.0, c.z - (z0 + z1) / 2)
        if f.normal.dot(Vector(want)) < 0:
            f.normal_flip()
    return kit._new_object("front bezel", bm, BEIGE, "metres", "xz")


def _bezel_lip(kit, z0, z1):
    """The bezel's back lip: the +Y-facing rim at BEZEL_BACK between the
    bezel outline and the cover section (+ the pan below it), so the 3 mm
    step can't be seen through from behind. Explicit fans (14 tris), no
    concave n-gons for the importer to triangulate."""
    hw = W / 2
    prof = _cover_profile()
    inner = [(-COVER_HW, z0)] + prof + [(COVER_HW, z0)]          # 12 points, left to right
    y = BEZEL_BACK
    bm = bmesh.new()
    I = [bm.verts.new((x, y, z)) for x, z in inner]
    O = [bm.verts.new(p) for p in ((-hw, y, z0), (-hw, y, z1), (hw, y, z1), (hw, y, z0))]
    tris = [(O[0], I[0], I[1]), (O[0], I[1], O[1]), (O[1], I[1], I[2]),          # left strip
            (O[1], I[2], I[3]), (O[1], I[3], I[4]), (O[1], I[4], I[5]),          # left corner
            (O[1], I[5], I[6]), (O[1], I[6], O[2]),                              # top strip
            (O[2], I[6], I[7]), (O[2], I[7], I[8]), (O[2], I[8], I[9]),          # right corner
            (O[2], I[9], I[10]), (O[2], I[10], O[3]), (O[3], I[10], I[11])]      # right strip
    for t in tris:
        f = bm.faces.new(t)
        f.normal_update()
        if f.normal.y < 0:
            f.normal_flip()
    return kit._new_object("bezel lip", bm, BEIGE, "metres", "xz")


def _dsub(kit, x, z, width, height, name="d-sub"):
    """D-sub shell on the rear panel: a 3 mm trapezoid block (10 tris)."""
    t = height * 0.2
    shell = [(-width / 2, height / 2), (width / 2, height / 2), (width / 2 - t, -height / 2), (-width / 2 + t, -height / 2)]
    obj = kit.extrude(shell, 0.003, (x, PANEL + 0.0015, z), BLACK, plane="xz", bevel=0.0, name=name)
    return dg.prune(obj, lambda n: n.y < -0.9)


def _plug(kit, end, prev):
    """Moulded NEMA 5-15P plug lying on the desk at the end of the cord: the
    cord enters the back of the body, the blades point along the cord's last
    tangent (prev -> end)."""
    dx, dy = end[0] - prev[0], end[1] - prev[1]
    l = math.hypot(dx, dy) or 1.0
    dx, dy = dx / l, dy / l
    rz = math.degrees(math.atan2(dy, dx))          # body length runs along local X
    sx, sy = -dy, dx                                # across the plug
    c = (end[0] + dx * 0.013, end[1] + dy * 0.013)
    body = kit.box((0.030, 0.020, 0.014), (c[0], c[1], 0.007), BLACK, bevel=0.0, rot=(0, 0, rz), name="plug body")
    parts = [body]                       # bottom kept: in the pile 'Side' state the plug hangs free
    for o in (-0.0063, 0.0063):
        parts.append(dg.box_faces(kit, (0.0065, 0.0015, 0.0065), (c[0] + dx * 0.0182 + sx * o, c[1] + dy * 0.0182 + sy * o, 0.0085),
                                  STEEL, faces=("-y", "+y", "+x", "+z"), rot=(0, 0, rz), name="plug blade"))
    return parts


def build(kit):
    dg.authored_lod1(kit)
    lod0 = []            # parts too small to matter at the LOD1 switch (PC ~0.45 m: beyond ~4 m)

    # ------------------------------------------------------------ chassis
    # Rubber feet, then the steel bottom pan as a darker band under the cover,
    # flush with the cover sides (a closed box seen from below).
    for sx in (-1, 1):
        for sy in (-1, 1):
            dg.box_faces(kit, (0.020, 0.020, 0.006), (sx * 0.172, sy * 0.160, 0.003), BLACK,
                         faces=("-x", "+x", "-y", "+y", "-z"), name="foot")
    pan_y0 = COVER_FRONT
    dg.box_faces(kit, (2 * COVER_HW, PANEL - pan_y0, COVER_Z0 - BEZEL_Z0), (0, (PANEL + pan_y0) / 2, (COVER_Z0 + BEZEL_Z0) / 2),
                 STEEL, faces=("-x", "+x", "+y", "-z"), name="bottom pan")
    # Painted steel U cover: one ring-built section, rounded top corners.
    prof = _cover_profile()
    dg.rings_mesh(kit, [[(x, COVER_FRONT, z) for x, z in prof], [(x, PANEL, z) for x, z in prof]], BEIGE,
                  name="steel cover", closed=False, centre=(0, 0, H / 2))
    # Pressed stiffening swage across the top, 66 mm in from the back edge.
    lod0.append(dg.box_faces(kit, (2 * COVER_HW - 0.011, 0.006, 0.0016), (0, PANEL - 0.066, COVER_TOP + 0.0006), BEIGE,
                             faces=("+z", "-y", "+y"), name="cover swage"))
    # Side louvres near the front (intake), and the PSU exhaust on the left.
    for sx in (-1, 1):
        for k in range(7):
            kit.quad(0.0034, 0.030, (sx * (COVER_HW + 0.0002), COVER_FRONT + 0.046 + k * 0.016, zr(0.062)), BLACK,
                     facing="+x" if sx > 0 else "-x", name="side louvre", uv="metres")
    for k in range(4):
        kit.quad(0.0034, 0.030, (-(COVER_HW + 0.0002), PANEL - 0.082 + k * 0.016, zr(0.062)), BLACK, facing="-x",
                 name="psu louvre", uv="metres")
    # Rear panel: the cover section closed in steel.
    bm = bmesh.new()
    ring = [bm.verts.new((x, PANEL, z)) for x, z in prof]
    f = bm.faces.new(ring)
    f.normal_update()
    if f.normal.y < 0:
        f.normal_flip()
    kit._new_object("rear panel", bm, STEEL, "metres", "xz")

    # ------------------------------------------------------------ front bezel
    bay_x = 0.095
    bay525_z = zr(0.088)
    hole_w, hole_h = 0.152, 0.046
    _bezel(kit, hole_w, hole_h, bay_x, bay525_z, BEZEL_Z0, BEZEL_Z1)
    _bezel_lip(kit, BEZEL_Z0, BEZEL_Z1)
    # Accent groove along the bottom of the bezel (moulded plinth line).
    kit.quad(W - 0.03, 0.0022, (0, FRONT - 0.0002, 0.018), BLACK, facing="-y", name="bezel plinth groove", uv="metres")
    # 5.25" bay: dark cavity, a blank plate recessed 3 mm inside a 2 mm shut line.
    kit.quad(hole_w, hole_h, (bay_x, FRONT + 0.016, bay525_z), BLACK, facing="-y", name="5.25 bay cavity", uv="metres")
    dg.face_box(kit, (0.146, 0.006, 0.040), (bay_x, FRONT + 0.006, bay525_z), BEIGE, chamfer=0.0015, name="5.25 bay blank")
    lod0.append(kit.quad(0.022, 0.0035, (bay_x, FRONT + 0.0029, bay525_z - 0.012), BLACK, facing="-y", name="blank finger notch",
                         uv="metres"))

    # 3.5" floppy drive: raised bezel insert, slot, eject button, busy LED.
    fz = zr(0.040)
    dg.face_box(kit, (0.112, 0.004, 0.032), (bay_x, FRONT - 0.002, fz), BEIGE, chamfer=0.0015, name="floppy insert")
    kit.quad(0.094, 0.0055, (bay_x, FRONT - 0.0042, fz + 0.003), BLACK, facing="-y", name="floppy slot", uv="metres")
    lod0.append(dg.face_box(kit, (0.017, 0.003, 0.0065), (bay_x + 0.036, FRONT - 0.0050, fz - 0.0068), BEIGE,
                            name="floppy eject button"))
    lod0.append(kit.quad(0.006, 0.0025, (bay_x - 0.040, FRONT - 0.0042, fz - 0.0072), BLACK, facing="-y", name="floppy busy LED",
                         uv="metres"))

    # Left half: nameplate, LED window, power + reset, key lock, intake grille.
    upper_z = zr(0.088)
    # Nameplate: a light painted plate with a short dark logo bar.
    kit.quad(0.048, 0.010, (-0.150, FRONT - 0.0004, upper_z + 0.002), STEEL, facing="-y", name="nameplate", uv="metres")
    lod0.append(kit.quad(0.026, 0.0024, (-0.157, FRONT - 0.0008, upper_z + 0.002), BLACK, facing="-y", name="nameplate logo",
                         uv="metres"))
    # Smoked LED window (power + disk lenses behind it, unlit: the PC is off).
    kit.quad(0.026, 0.009, (-0.082, FRONT - 0.0004, upper_z), BLACK, facing="-y", name="LED window", uv="metres")
    # Power button: a shallow rounded cap ~3 mm proud of its dark well.
    px = -0.040
    kit.quad(0.026, 0.026, (px, FRONT - 0.0004, upper_z), BLACK, facing="-y", name="power well", uv="metres")
    lod0.append(dg.face_box(kit, (0.019, 0.004, 0.019), (px, FRONT - 0.001, upper_z), BEIGE, chamfer=0.0035, name="power button"))
    lod1_button = kit.quad(0.017, 0.017, (px, FRONT - 0.0008, upper_z), BEIGE, facing="-y", name="LOD1 power button", uv="metres")
    # Reset: a small beige pin-button in a dark ring.
    rz_ = zr(0.061)
    lod0.append(dg.disc(kit, 0.0055, (px, FRONT - 0.0004, rz_), BLACK, verts=8, facing="-y", name="reset well"))
    lod0.append(dg.face_box(kit, (0.009, 0.003, 0.009), (px, FRONT - 0.0005, rz_), BEIGE, chamfer=0.002, name="reset button"))
    # Key lock: painted lock face with its keyway.
    lz = zr(0.036)
    lock = kit.cylinder(0.0075, 0.004, (px, FRONT - 0.002, lz), STEEL, verts=10, rot=(90, 0, 0), bevel=0.0, name="key lock")
    lod0.append(dg.prune(lock, lambda n: n.z < -0.9))
    lod0.append(kit.quad(0.0014, 0.0065, (px, FRONT - 0.0042, lz), BLACK, facing="-y", name="keyway", uv="metres"))
    lod1_lock = dg.disc(kit, 0.0075, (px, FRONT - 0.0004, lz), STEEL, verts=6, facing="-y", name="LOD1 lock face")
    # Intake grille: dark backing and raised moulded ribs.
    gx, gz, gw = -0.128, zr(0.040), 0.118
    kit.quad(gw + 0.004, 0.036, (gx, FRONT - 0.0003, gz), BLACK, facing="-y", name="grille backing", uv="metres")
    lod1 = [lod1_lock, lod1_button]
    for i in range(6):
        zc = gz - 0.0150 + i * 0.0060
        lod0.append(dg.box_faces(kit, (gw, 0.0042, 0.0030), (gx, FRONT - 0.0021, zc), BEIGE,
                                 faces=("-y", "+z", "-z"), name="grille rib"))
        lod1.append(kit.quad(gw, 0.0030, (gx, FRONT - 0.0006, zc), BEIGE, facing="-y", name="LOD1 grille rib", uv="metres"))
    for sx in (-1, 1):
        lod0.append(dg.box_faces(kit, (0.0030, 0.0042, 0.036), (gx + sx * (gw / 2 + 0.0005), FRONT - 0.0021, gz), BEIGE,
                                 faces=("-y", "-x", "+x", "+z", "-z"), name="grille end"))

    # ------------------------------------------------------------ rear panel
    # PSU plate with the fan: dark opening, silver hub label, wire guard.
    psu_x = -0.120
    dg.face_box(kit, (0.150, 0.0016, 0.086), (psu_x, PANEL + 0.0008, zr(0.064)), STEEL, facing="+y", name="psu plate")
    fan_x, fan_z = -0.150, zr(0.068)
    fy = PANEL + 0.0016
    dg.disc(kit, 0.034, (fan_x, fy + 0.0003, fan_z), BLACK, verts=12, facing="+y", name="fan opening")
    lod0.append(dg.disc(kit, 0.011, (fan_x, fy + 0.0012, fan_z), STEEL, verts=8, facing="+y", name="fan hub"))
    lod0.append(dg.annulus(kit, 0.0305, 0.0330, (fan_x, fy + 0.0020, fan_z), STEEL, verts=12, facing="+y", name="fan guard ring"))
    lod0.append(dg.annulus(kit, 0.0190, 0.0210, (fan_x, fy + 0.0020, fan_z), STEEL, verts=10, facing="+y", name="fan guard ring"))
    for rot in (45, -45):
        g = kit.quad(0.064, 0.0016, (fan_x, fy + 0.0022, fan_z), STEEL, facing="+y", name="fan guard spoke", uv="metres")
        g.rotation_euler = (0, math.radians(rot), 0)
        lod0.append(g)

    # IEC C14 inlet with the power cord's plug in it, C13 monitor outlet,
    # voltage selector.
    inlet_z = zr(0.040)
    for nm, z in (("power inlet", inlet_z), ("monitor outlet", zr(0.084))):
        lod0.append(dg.face_box(kit, (0.031, 0.006, 0.023), (-0.092, PANEL + 0.003, z), BLACK, facing="+y", name=nm))
    lod0.append(kit.quad(0.016, 0.009, (-0.185, PANEL + 0.0018, zr(0.030)), BLACK, facing="+y", name="voltage switch", uv="metres"))
    lod0.append(dg.face_box(kit, (0.026, 0.024, 0.020), (-0.092, PANEL + 0.006 + 0.012, inlet_z), BLACK, chamfer=0.003,
                            facing="+y", name="inlet plug"))
    relief = kit.cylinder(0.0045, 0.014, (-0.092, PANEL + 0.036, inlet_z - 0.002), BLACK, verts=6, rot=(90, 0, 0), bevel=0.0,
                          radius_top=0.0062, name="inlet plug strain relief")
    lod0.append(dg.prune(relief, lambda n: n.z > 0.9))       # its wide end is inside the plug
    # The cord lies loose behind the case and ends in its (unplugged) wall plug.
    cz = inlet_z - 0.002
    ctrl = [(-0.092, PANEL + 0.040, cz), (-0.092, PANEL + 0.050, cz - 0.004), (-0.093, PANEL + 0.058, cz - 0.016),
            (-0.095, PANEL + 0.062, 0.014), (-0.100, PANEL + 0.065, 0.0045), (-0.110, PANEL + 0.0665, 0.0036),
            (-0.124, PANEL + 0.065, 0.0036), (-0.142, PANEL + 0.058, 0.0036), (-0.160, PANEL + 0.054, 0.0040),
            (-0.172, PANEL + 0.059, 0.0052)]
    lod0.append(dg.tube(kit, ctrl, 0.0036, BLACK, verts=6, name="power cord"))
    lod0.extend(_plug(kit, ctrl[-1], ctrl[-2]))

    # I/O row (lower right seen from the back): PS/2 keyboard + mouse, the
    # parallel / serial / VGA shells, and a punched vent field.
    io_z = zr(0.036)
    for z in (io_z + 0.008, io_z - 0.009):
        lod0.append(dg.disc(kit, 0.0062, (-0.005, PANEL + 0.0004, z), BLACK, verts=8, facing="+y", name="ps2 port"))
    lod0.append(_dsub(kit, 0.045, io_z + 0.007, 0.040, 0.010, name="parallel port"))
    lod0.append(_dsub(kit, 0.045, io_z - 0.010, 0.024, 0.009, name="serial A"))
    lod0.append(_dsub(kit, 0.100, io_z - 0.010, 0.024, 0.009, name="serial B"))
    lod0.append(_dsub(kit, 0.100, io_z + 0.007, 0.024, 0.0095, name="VGA"))
    for col in range(5):
        lod0.append(kit.quad(0.0045, 0.018, (0.140 + col * 0.0135, PANEL + 0.0002, io_z - 0.0015), BLACK, facing="+y",
                             name="rear vent", uv="metres"))
    # LOD1: one dark I/O field stands in for the connector row.
    lod1.append(kit.quad(0.130, 0.030, (0.055, PANEL + 0.0004, io_z - 0.001), BLACK, facing="+y", name="LOD1 io field", uv="metres"))
    # Riser expansion slots: three horizontal covers (dark shut lines between
    # them); the middle one is a sound card with game port and audio jacks.
    for k in range(4):
        kit.quad(0.150, 0.0016, (0.110, PANEL + 0.0002, zr(0.059) + k * 0.016), BLACK, facing="+y", name="slot shut line",
                 uv="metres")
    card_z = zr(0.059) + 1.5 * 0.016
    lod0.append(_dsub(kit, 0.070, card_z, 0.030, 0.0085, name="game port"))
    for k in range(3):
        lod0.append(dg.disc(kit, 0.0036, (0.110 + k * 0.014, PANEL + 0.0004, card_z), BLACK, verts=6, facing="+y",
                            name="audio jack"))
    lod0.append(dg.face_box(kit, (0.014, 0.004, 0.0095), (0.155, PANEL + 0.002, card_z + 0.016), BLACK, facing="+y",
                            name="rj45 jack"))

    dg.lod0_only(*lod0)
    dg.lod1_only(*lod1)

    kit.support("top", (0, 0, H), (0.38, 0.38))
    kit.anchor("monitor", (0, -0.01, H))
    kit.anchor("power_led", (-0.088, FRONT - 0.003, upper_z))
    kit.anchor("hdd_led", (-0.076, FRONT - 0.003, upper_z))
    kit.collider((0, (FRONT + PANEL) / 2, H / 2), (W, PANEL - FRONT, H))
    kit.tag("office", "electronics", "desk_top", "pile_piece")
    kit.pile("Small", mass=1, palette="office90s")
