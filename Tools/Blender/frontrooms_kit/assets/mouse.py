"""Beige two-button ball mouse on a cloth mouse pad, c. 1990-97 (the
"bar of soap" PS/2 / serial mouse shipped with office PCs).

Real-world reference size: mouse 0.06 m wide, 0.11 m long, 0.035 m tall
(palm hump toward the back, buttons sloping down to the cable end); pad
0.22 x 0.18 m, 3 mm thick (black rubber foam, dark cloth top).
The shell is one sculpted surface (lathed squircle dome, deformed for the
palm hump and the narrower nose). The button split lines are thin dark
ribbons laid on the shell along ray-cast surface points (20 tris instead of
cutting the shell into three closed pieces). The cable leaves the nose and
runs back off the pad (draped over its edge) to a serial DE-9 plug lying on
the desk.
Origin = centre of the pad on the desk. The user sits at -Y; the mouse nose
(buttons, cable) points away from the user, +Y.

Budget (synthesis §5.3): 300 LOD0 tris, no LOD1, no collider (desk-top
clutter), not a pile piece; slots PlasticBeige, PlasticBlack + the pad's
FabricChair.
"""

import math

import bmesh

import _deskgear as dg

NAME = "Kit_Mouse"
SMOOTH_ANGLE = 60          # the 16-sided dome reads smooth; pad and plug edges stay crisp

BEIGE = "Prop_PlasticBeige"
BLACK = "Prop_PlasticBlack"
CLOTH = "Prop_FabricChair"

PAD_W, PAD_D = 0.22, 0.18
PAD_T = 0.003
PAD_R = 0.012

HALF_W, HALF_L = 0.030, 0.055
SHELL_H = 0.035                     # shell height above the pad
SPLIT_Y = 0.014                     # buttons in front of this (41 mm long)

MOUSE_POS = (0.022, -0.004)
MOUSE_YAW = -7.0                    # degrees about Z (nose turned slightly right)


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


def _to_pad(p):
    """Mouse-local point -> asset space (same transform as the shell)."""
    a = math.radians(MOUSE_YAW)
    x, y, z = p
    return (MOUSE_POS[0] + x * math.cos(a) - y * math.sin(a), MOUSE_POS[1] + x * math.sin(a) + y * math.cos(a), z)


def _seam(kit, shell_mesh, plane_co, plane_no, keep, order, width, name, pre_cut=None):
    """Thin dark ribbon lying on the (faceted) shell where a plane cuts it:
    one ribbon vertex per shell edge crossed, so every segment lies flat on
    one facet (a chord between ray hits dipped under the facet ridges).
    keep(co) filters the cut points, order(co) sorts them; lifted 0.2 mm."""
    src = bmesh.new()
    src.from_mesh(shell_mesh)
    if pre_cut is not None:                 # e.g. the cross seam, so the two seams meet on a vertex
        bmesh.ops.bisect_plane(src, geom=src.verts[:] + src.edges[:] + src.faces[:], dist=1e-7,
                               plane_co=pre_cut[0], plane_no=pre_cut[1])
    res = bmesh.ops.bisect_plane(src, geom=src.verts[:] + src.edges[:] + src.faces[:], dist=1e-7,
                                 plane_co=plane_co, plane_no=plane_no)
    src.normal_update()
    cut = [v for v in res["geom_cut"] if isinstance(v, bmesh.types.BMVert) and keep(v.co)]
    cut.sort(key=lambda v: order(v.co))
    hits = [(v.co + v.normal * 0.0002, v.normal.copy()) for v in cut]
    src.free()
    bm = bmesh.new()
    left, right = [], []
    for k, (p, n) in enumerate(hits):
        t = (hits[min(k + 1, len(hits) - 1)][0] - hits[max(k - 1, 0)][0]).normalized()
        side = t.cross(n).normalized() * (width / 2)
        left.append(bm.verts.new(_to_pad(p - side)))
        right.append(bm.verts.new(_to_pad(p + side)))
    for k in range(len(hits) - 1):
        f = bm.faces.new((left[k], right[k], right[k + 1], left[k + 1]))
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    return kit._new_object(name, bm, BLACK, "metres", "xz")


def _db9_plug(kit, end, prev):
    """Serial mouse plug (DE-9 female) lying flat on the desk at the cable
    end: tapered moulded hood and the D-shell, face along the cable's last
    horizontal tangent. 20 tris (thumbscrews and socket holes are < 5 mm)."""
    tx, ty = end[0] - prev[0], end[1] - prev[1]
    l = math.hypot(tx, ty) or 1.0
    tx, ty = tx / l, ty / l
    a = math.degrees(math.atan2(tx, -ty))            # local +Y (cable side) -> -tangent
    zc = 0.0062
    hood_d = 0.022

    def at(along):
        return (end[0] + tx * along, end[1] + ty * along, zc)
    hood = kit.loft_box((0.031, 0.0124), (0.015, 0.0090), hood_d, at(hood_d / 2), BLACK, bevel=0.0,
                        rot=(0, 0, a), name="plug hood")
    dg.prune(hood, lambda n: n.z < -0.9)                         # its underside is on the desk
    t = 0.0016
    shell = [(-0.0085, 0.0037), (0.0085, 0.0037), (0.0085 - t, -0.0037), (-0.0085 + t, -0.0037)]
    d = kit.extrude(shell, 0.006, at(hood_d + 0.0028), BLACK, plane="xz", rot=(0, 0, a), bevel=0.0, name="plug d-shell")
    dg.prune(d, lambda n: n.y > 0.9)                             # its back is inside the hood


def build(kit):
    # ------------------------------------------------------------ mouse pad
    # One extrusion: cloth top and foam edge in the pad slot; the underside is
    # on the desk and never seen. 34 tris.
    pad = kit.extrude(dg.round_rect(PAD_W, PAD_D, PAD_R, seg=2), PAD_T, (0, 0, PAD_T / 2), CLOTH, plane="xy",
                      bevel=0.0, name="mouse pad")
    dg.prune(pad, lambda n: n.z < -0.9)

    # ------------------------------------------------------------ mouse shell
    # Lathed unit dome (16 sides, 4 rings + pole), deformed into the soap bar.
    # Its foot tucks in 3.5 % so the shell meets the pad in a contact line.
    prof = [(0.965, 0.0), (0.995, 0.33), (0.93, 0.68), (0.72, 0.92), (0.0, 1.0)]
    z_shell = PAD_T
    shell = kit.lathe(prof, (0, 0, 0), BEIGE, verts=16, name="mouse shell", close_bottom=False)
    _shell_mesh(shell, z_shell)
    shell.location = (MOUSE_POS[0], MOUSE_POS[1], 0.0)
    shell.rotation_mode = "XYZ"
    shell.rotation_euler = (0.0, 0.0, math.radians(MOUSE_YAW))

    # Button split lines: across the shell at SPLIT_Y (down to the side skirt,
    # 10.5 mm above the pad) and between the two buttons to the nose.
    z_cut = z_shell + 0.0105
    _seam(kit, shell.data, (0, SPLIT_Y, 0), (0, 1, 0), lambda co: co.z > z_cut, lambda co: co.x, 0.0008, "button split")
    _seam(kit, shell.data, (0, 0, 0), (1, 0, 0), lambda co: co.y > SPLIT_Y - 1e-5 and co.z > z_cut,
          lambda co: co.y, 0.0007, "button split", pre_cut=((0, SPLIT_Y, 0), (0, 1, 0)))

    # ------------------------------------------------------------ cable
    # Out of the nose, onto the pad, over its edge (y 0.090) and down to the
    # desk, ending in the serial plug. 9 segments x 5 sides.
    r = 0.0018
    nose_z = z_shell + 0.0085
    pts = [_to_pad(p) for p in ((0, HALF_L - 0.004, nose_z), (0, HALF_L + 0.005, nose_z - 0.0007),
                                (0.0004, HALF_L + 0.0115, nose_z - 0.0040), (0.001, HALF_L + 0.018, PAD_T + r + 0.0004))]
    pts += [(0.0330, 0.0860, PAD_T + r), (0.0334, 0.0935, PAD_T + r - 0.0006), (0.0310, 0.1030, r + 0.0003),
            (0.0190, 0.1220, r), (-0.0010, 0.1380, 0.0042), (-0.0100, 0.1460, 0.0060)]
    dg.tube(kit, pts, r, BLACK, verts=5, name="mouse cable")
    _db9_plug(kit, pts[-1], pts[-2])

    kit.anchor("mouse", (MOUSE_POS[0], MOUSE_POS[1], SHELL_H + PAD_T))
    kit.no_collider()
    kit.tag("office", "desk_top")
