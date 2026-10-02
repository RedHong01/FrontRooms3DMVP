"""Beige two-button ball mouse on a cloth mouse pad, c. 1990-97 (the
"bar of soap" PS/2 / serial mouse shipped with office PCs).

Real-world reference size: mouse 0.06 m wide, 0.11 m long, 0.035 m tall
(palm hump toward the back, buttons sloping down to the cable end); pad
0.22 x 0.18 m, 3 mm thick (black rubber foam, dark cloth top).
The shell is one sculpted surface (lathed squircle dome, deformed for the
palm hump and the narrower nose) that is then cut into palm shell + two
button plates, so the split lines are real gaps. The cable leaves the nose
and runs back off the pad (draped over its edge) to a serial DE-9 plug lying
on the desk.
Origin = centre of the pad on the desk. The user sits at -Y; the mouse nose
(buttons, cable) points away from the user, +Y.
"""

import math

import bmesh
import bpy

NAME = "Kit_Mouse"

BEIGE = "Prop_PlasticBeige"
DARK = "Prop_PlasticGrey"
BLACK = "Prop_PlasticBlack"
RUBBER = "Prop_Rubber"
CLOTH = "Prop_FabricChair"

PAD_W, PAD_D = 0.22, 0.18
PAD_T = 0.003
PAD_R = 0.012

HALF_W, HALF_L = 0.030, 0.055
BASE_T = 0.0028                     # dark bottom plate under the shell
SHELL_H = 0.035 - BASE_T + 0.0005   # shell rises from just above the plate to 35 mm
SPLIT_Y = 0.014                     # buttons in front of this (41 mm long)
GAP = 0.0007                        # width of the split lines

MOUSE_POS = (0.022, -0.004)
MOUSE_YAW = -7.0                    # degrees about Z (nose turned slightly right)


def _round_rect(w, d, r, seg=3):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90.0 * k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _squircle(a, p=0.50):
    c, s = math.cos(a), math.sin(a)
    return math.copysign(abs(c) ** p, c), math.copysign(abs(s) ** p, s)


def _half_width(yn):
    """Plan half-width along the length (yn -1 palm .. +1 nose)."""
    t = max(0.0, (yn + 0.15) / 1.15)
    return HALF_W * (1.0 - 0.16 * t * t)


def _height(yn):
    """Height factor along the length: palm hump behind centre."""
    if yn >= -0.22:
        t = (yn + 0.22) / 1.22
        return 1.0 - 0.44 * t * t
    t = (yn + 0.22) / 0.78
    return 1.0 - 0.34 * t * t


def _shell_mesh(obj, z0):
    """Deform the unit lathe into the mouse shell (in place)."""
    me = obj.data
    for v in me.vertices:
        x, y, z = v.co
        r = math.hypot(x, y)
        a = math.atan2(y, x)
        cx, cy = _squircle(a)
        yn = r * cy
        v.co = (r * cx * _half_width(yn), r * cy * HALF_L, z0 + z * SHELL_H * _height(yn))
    me.update()


def _cut(obj, planes):
    """Keep the side of each (point, normal) plane the normal points away
    from... i.e. keep where (p - co) . n <= 0, cap every cut."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for co, no in planes:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-7, plane_co=co, plane_no=no, clear_outer=True)
        boundary = [e for e in bm.edges if e.is_boundary]
        if boundary:
            bmesh.ops.holes_fill(bm, edges=boundary, sides=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def _notch(obj, y_cut, z_cut):
    """Remove the button region (y > y_cut and z > z_cut) from the body shell
    and close it with a vertical wall and a horizontal ledge, so the body
    stays one closed piece and the buttons sit in a real step."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    for co, no in (((0, y_cut, 0), (0, 1, 0)), ((0, 0, z_cut), (0, 0, 1))):
        bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-7, plane_co=co, plane_no=no)
    eps = 1e-6
    kill = []
    for f in bm.faces:
        c = f.calc_center_median()
        if c.y > y_cut + eps and c.z > z_cut + eps:
            kill.append(f)
    bmesh.ops.delete(bm, geom=kill, context="FACES")
    boundary = [e for e in bm.edges if e.is_boundary]
    on_wall = lambda v: abs(v.co.y - y_cut) < 1e-5
    on_ledge = lambda v: abs(v.co.z - z_cut) < 1e-5
    wall = [e for e in boundary if all(on_wall(v) for v in e.verts)]
    ledge = [e for e in boundary if all(on_ledge(v) for v in e.verts) and e not in wall]
    corners = sorted({v for e in boundary for v in e.verts if on_wall(v) and on_ledge(v)}, key=lambda v: v.co.x)
    ne = bm.edges.new((corners[0], corners[-1]))
    bmesh.ops.contextual_create(bm, geom=wall + [ne])
    bmesh.ops.contextual_create(bm, geom=ledge + [ne])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


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
    """Round tube along a polyline with parallel-transport frames (no ring
    flips where the path turns, unlike kit.tube)."""
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


def _db9_plug(kit, end, prev):
    """Serial mouse plug (DE-9 female) lying flat on the desk at the cable
    end: tapered moulded hood, metal D-shell with its dark socket face, two
    thumbscrews standing proud of the flange.
    Its face points along the cable's last horizontal tangent."""
    tx, ty = end[0] - prev[0], end[1] - prev[1]
    l = math.hypot(tx, ty) or 1.0
    tx, ty = tx / l, ty / l
    a = math.degrees(math.atan2(tx, -ty))            # local +Y (cable side) -> -tangent
    sx, sy = -ty, tx                                 # local +X in world... (sign irrelevant, symmetric)
    zc = 0.0062
    hood_d = 0.022

    def at(along, across=0.0, z=zc):
        return (end[0] + tx * along + sx * across, end[1] + ty * along + sy * across, z)
    kit.loft_box((0.031, 0.0124), (0.015, 0.0090), hood_d, at(hood_d / 2), BLACK, bevel=0.0018, segments=1,
                 rot=(0, 0, a), name="plug hood")
    t = 0.0016
    shell = [(-0.0085, 0.0037), (0.0085, 0.0037), (0.0085 - t, -0.0037), (-0.0085 + t, -0.0037)]
    kit.extrude(shell, 0.006, at(hood_d + 0.0028), "Prop_Aluminium", plane="xz", rot=(0, 0, a), bevel=0.0,
                name="plug d-shell")
    i = 0.0011
    insert = [(-0.0085 + i, 0.0037 - i), (0.0085 - i, 0.0037 - i), (0.0085 - t - i * 0.6, -0.0037 + i), (-0.0085 + t + i * 0.6, -0.0037 + i)]
    kit.extrude(insert, 0.0058, at(hood_d + 0.0031), BLACK, plane="xz", rot=(0, 0, a), bevel=0.0, name="plug d-insert")
    # Thumbscrews through the flange beside the D, tips standing proud.
    for o in (-0.0124, 0.0124):
        kit.cylinder(0.0016, 0.006, at(hood_d + 0.002, o), "Prop_Chrome", verts=6, rot=(90, 0, a), bevel=0.0,
                     name="plug thumbscrew")


def _drop_faces(obj, test):
    """Delete the faces of a part whose (local) normal passes ``test``."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if test(f.normal)], context="FACES")
    bm.to_mesh(obj.data)
    bm.free()


def _place(obj):
    obj.location = (MOUSE_POS[0], MOUSE_POS[1], obj.location.z)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = (0.0, 0.0, math.radians(MOUSE_YAW))


def _to_pad(p):
    """Mouse-local point -> asset space (same transform as _place)."""
    a = math.radians(MOUSE_YAW)
    x, y, z = p
    return (MOUSE_POS[0] + x * math.cos(a) - y * math.sin(a), MOUSE_POS[1] + x * math.sin(a) + y * math.cos(a), z)


def build(kit):
    # ------------------------------------------------------------ mouse pad
    outline = _round_rect(PAD_W, PAD_D, PAD_R)
    foam = kit.extrude(outline, PAD_T - 0.0008, (0, 0, (PAD_T - 0.0008) / 2), RUBBER, plane="xy", bevel=0.0, name="pad foam")
    cloth = kit.extrude(outline, 0.0008, (0, 0, PAD_T - 0.0004), CLOTH, plane="xy", bevel=0.0, name="pad cloth")
    # Only the foam's edge band and the cloth's top and edge are ever seen.
    _drop_faces(foam, lambda n: abs(n.z) > 0.9)
    _drop_faces(cloth, lambda n: n.z < -0.9)

    # ------------------------------------------------------------ mouse
    z_base = PAD_T
    # Dark bottom plate following the shell footprint.
    foot = []
    for k in range(20):
        a = 2 * math.pi * k / 20
        cx, cy = _squircle(a)
        yn = 0.992 * cy
        foot.append((0.992 * cx * _half_width(yn), 0.992 * cy * HALF_L))
    base = kit.extrude(foot, BASE_T, (0, 0, z_base + BASE_T / 2), DARK, plane="xy", bevel=0.0, name="mouse base")
    _place(base)

    prof = [(1.0, 0.0), (1.0, 0.22), (0.993, 0.40), (0.976, 0.555), (0.945, 0.685), (0.895, 0.795), (0.82, 0.88),
            (0.71, 0.942), (0.56, 0.98), (0.33, 0.997), (0.0, 1.0)]
    z_shell = z_base + BASE_T - 0.0002
    shell = kit.lathe(prof, (0, 0, 0), BEIGE, verts=24, name="mouse shell", close_bottom=False)
    _shell_mesh(shell, z_shell)
    left = kit.duplicate(shell, name="left button")
    right = kit.duplicate(shell, name="right button")
    # Buttons are plates over the nose: the body keeps its side skirt up to
    # z_cut, the buttons start just above it.
    z_cut = z_shell + 0.0105
    _notch(shell, SPLIT_Y - GAP / 2, z_cut)
    _cut(left, [((0, SPLIT_Y + GAP / 2, 0), (0, -1, 0)), ((0, 0, z_cut + 0.0004), (0, 0, -1)), ((-GAP / 2, 0, 0), (1, 0, 0))])
    _cut(right, [((0, SPLIT_Y + GAP / 2, 0), (0, -1, 0)), ((0, 0, z_cut + 0.0004), (0, 0, -1)), ((GAP / 2, 0, 0), (-1, 0, 0))])
    for part in (shell, left, right):
        kit._bevel(part, 0.0006, 1, angle=50)
        _place(part)

    # Cable: strain-relief nub low on the nose, then the cord runs back to the PC.
    nose_z = z_shell + 0.0085
    nub = kit.cylinder(0.0032, 0.007, (0, HALF_L * 0.985 + 0.0025, nose_z), DARK, verts=8, rot=(90, 0, 0),
                       bevel=0.0, radius_top=0.0042, name="cable nub")
    nub.location = _to_pad(nub.location)
    nub.rotation_euler = (math.radians(90), 0, math.radians(MOUSE_YAW))
    r = 0.0018
    pts = [(0, HALF_L + 0.005, nose_z), (0, HALF_L + 0.0125, nose_z - 0.0028), (0.0005, HALF_L + 0.021, PAD_T + r + 0.0012)]
    pts = [_to_pad(p) for p in pts]
    # Evenly spaced control points (Catmull-Rom kinks on uneven spacing). Over
    # the pad edge (y 0.090) the cable stays above the 3 mm pad top, then
    # drapes down to the desk and ends in the serial (DE-9) plug.
    pts += [(0.0330, 0.0820, PAD_T + r + 0.0001), (0.0335, 0.0905, PAD_T + r + 0.0002), (0.0330, 0.0985, PAD_T * 0.55 + r),
            (0.0300, 0.1080, r), (0.0190, 0.1240, r), (0.0030, 0.1370, 0.0030), (-0.0100, 0.1460, 0.0060)]
    cable = [(x, y, max(z, r)) for x, y, z in _smooth(pts, 2)]   # never below the desk
    _pt_tube(kit, cable, r, BLACK, verts=8, name="mouse cable")
    _db9_plug(kit, pts[-1], pts[-2])

    kit.anchor("mouse", (MOUSE_POS[0], MOUSE_POS[1], 0.035 + PAD_T))
    kit.collider((0, 0, PAD_T / 2), (PAD_W, PAD_D, PAD_T))
    kit.collider((MOUSE_POS[0], MOUSE_POS[1], PAD_T + 0.0175), (0.074, 0.118, 0.035))   # covers the -7 deg yaw
    kit.tag("office", "desk_top", "pile_piece")
    kit.pile("Small", mass=0, palette="office90s")
