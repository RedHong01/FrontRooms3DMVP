"""Low-poly building blocks for the desk electronics (helper, NOT an asset
module). Used by pc_desktop, keyboard, mouse and desk_phone (opt-computer).

Why: these props carry tight budgets (PC 900, keyboard 1,200, mouse 300,
phone 900 LOD0 tris, synthesis §5.3). kit.box with a bevel costs 44 tris
even for a 5 mm button, and most of a desk prop's faces are never seen
(undersides on the desk, backs against the bezel). These helpers build only
the faces that show:

* face_box()   a part standing proud of a face: front (optionally with a
               chamfered rim, which reads as a rounded moulding under top
               light) and the side walls; no back.  10 / 18 tris.
* box_faces()  an unbevelled kit.box keeping only the listed faces.
* disc() / annulus()  flat n-gon / ring lying on a face (LEDs, jacks, fan).
* rings_mesh() bridge a list of equal-length vertex rings into quads (the
               keyboard and PC shells, rounded profiles).
* tube()       parallel-transport tube (cables never twist where they turn
               vertical, unlike kit.tube); caps off by default (cable ends
               are buried in grommets and plugs).
* smooth()     Catmull-Rom resample of a polyline.
"""

import math

import bmesh
from mathutils import Matrix, Vector

# facing -> rotation (degrees) taking the -Y-facing local build to that facing.
_FACING_ROT = {"-y": (0, 0, 0), "+y": (0, 0, 180), "-x": (0, 0, -90), "+x": (0, 0, 90),
               "+z": (-90, 0, 0), "-z": (90, 0, 0)}


def smooth(points, sub):
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


def frames(points):
    """Parallel-transport frames along a polyline: (point, tangent, normal,
    binormal); the normal starts as world-up projected off the tangent."""
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
    out = []
    for p, t in zip(pts, tangents):
        nrm = (nrm - t * nrm.dot(t)).normalized()
        out.append((p, t, nrm, t.cross(nrm)))
    return out


def tube(kit, points, radius, slot, verts=6, name="cable", caps=False, flat=1.0):
    """Tube along a polyline on parallel-transport frames. flat < 1 squashes
    the section along the frame normal (flat line cords)."""
    bm = bmesh.new()
    rings = []
    for p, t, nrm, b in frames(points):
        ring = []
        for i in range(verts):
            a = 2 * math.pi * (i + 0.5) / verts
            ring.append(bm.verts.new(p + (nrm * (math.cos(a) * flat) + b * math.sin(a)) * radius))
        rings.append(ring)
    for a, c in zip(rings, rings[1:]):
        for i in range(verts):
            j = (i + 1) % verts
            bm.faces.new((a[i], a[j], c[j], c[i]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def prune(obj, test):
    """Delete the faces of a part whose LOCAL normal passes ``test``."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if test(f.normal)], context="FACES")
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def _axis_of(n):
    ax = max(range(3), key=lambda i: abs(n[i]))
    return ("+" if n[ax] > 0 else "-") + "xyz"[ax]


def box_faces(kit, size, loc, slot, faces=("-y", "+y", "-x", "+x", "+z"), rot=(0, 0, 0), name="box", uv="metres"):
    """Unbevelled box keeping only ``faces`` (local axes: -y front ... +z top)."""
    obj = kit.box(size, loc, slot, bevel=0.0, rot=rot, name=name, uv=uv)
    keep = set(faces)
    return prune(obj, lambda n: _axis_of(n) not in keep)


def face_box(kit, size, loc, slot, chamfer=0.0, facing="-y", rot_extra=0.0, name="face box", sides=True):
    """A block standing proud of a face, built facing -Y then turned to
    ``facing``: size = (width, depth, height) in that local frame, loc = the
    block centre. The front face (with an optional chamfered rim) and the
    four side walls only; the back sits on the parent and is never seen.
    rot_extra spins it about its facing axis (degrees)."""
    w, d, h = size
    hw, hh = w / 2, h / 2
    y0, y1 = -d / 2, d / 2
    bm = bmesh.new()

    def ring(iw, ih, y):
        return [bm.verts.new(p) for p in ((-iw, y, -ih), (iw, y, -ih), (iw, y, ih), (-iw, y, ih))]
    c = min(chamfer, hw * 0.45, hh * 0.45, d * 0.9)
    if c > 0:
        front = ring(hw - c, hh - c, y0)
        mid = ring(hw, hh, y0 + c)
        bm.faces.new(list(reversed(front)))
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((front[i], front[j], mid[j], mid[i]))
        top = mid
    else:
        top = ring(hw, hh, y0)
        bm.faces.new(list(reversed(top)))
    if sides:
        back = ring(hw, hh, y1)
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((top[i], top[j], back[j], back[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    # recalc can flip an open shell inward: make the front face point -Y.
    bm.normal_update()
    fr = min(bm.faces, key=lambda f: f.calc_center_median().y)
    if fr.normal.y > 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    obj = kit._new_object(name, bm, slot, "metres", "xz")
    rx, ry, rz = _FACING_ROT[facing]
    if facing in ("-y", "+y"):
        ry += rot_extra
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = [math.radians(a) for a in (rx, ry, rz)]
    if facing in ("+z", "-z") and rot_extra:
        obj.rotation_euler = (Matrix.Rotation(math.radians(rot_extra), 3, "Z") @ obj.rotation_euler.to_matrix()).to_euler()
    obj.location = loc
    return obj


def disc(kit, radius, loc, slot, verts=8, facing="-y", name="disc", spin=0.0, uv="metres", radius_z=None):
    """Flat n-gon lying on a face (LED lens, jack, fan opening)."""
    rz_ = radius if radius_z is None else radius_z
    bm = bmesh.new()
    vs = []
    for i in range(verts):
        a = 2 * math.pi * i / verts + math.radians(spin)
        vs.append(bm.verts.new((math.cos(a) * radius, 0.0, math.sin(a) * rz_)))
    f = bm.faces.new(vs)
    f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()
    obj = kit._new_object(name, bm, slot, uv, "xz")
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = [math.radians(a) for a in _FACING_ROT[facing]]
    obj.location = loc
    return obj


def annulus(kit, r_in, r_out, loc, slot, verts=12, facing="-y", name="ring"):
    """Flat ring (fan guard, connector shell rim)."""
    bm = bmesh.new()
    inner, outer = [], []
    for i in range(verts):
        a = 2 * math.pi * i / verts
        inner.append(bm.verts.new((math.cos(a) * r_in, 0.0, math.sin(a) * r_in)))
        outer.append(bm.verts.new((math.cos(a) * r_out, 0.0, math.sin(a) * r_out)))
    for i in range(verts):
        j = (i + 1) % verts
        f = bm.faces.new((inner[i], inner[j], outer[j], outer[i]))
    bm.normal_update()
    for f in bm.faces:
        if f.normal.y > 0:
            f.normal_flip()
    obj = kit._new_object(name, bm, slot, "metres", "xz")
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = [math.radians(a) for a in _FACING_ROT[facing]]
    obj.location = loc
    return obj


def rings_mesh(kit, rings, slot, name="shell", closed=True, cap_first=False, cap_last=False, uv="metres", orient="out",
               centre=None):
    """Bridge consecutive rings of 3D points (equal length) into quads.
    closed: each ring is a loop. Normals are made consistent, then turned to
    face away from (orient="out") or toward (orient="in") ``centre``
    (default: the mesh centroid)."""
    bm = bmesh.new()
    vr = [[bm.verts.new(p) for p in r] for r in rings]
    n = len(rings[0])
    for a, b in zip(vr, vr[1:]):
        for i in range(n if closed else n - 1):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap_first:
        bm.faces.new(list(reversed(vr[0])))
    if cap_last:
        bm.faces.new(vr[-1])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if orient:
        c = Vector(centre) if centre is not None else sum((v.co for v in bm.verts), Vector()) / max(len(bm.verts), 1)
        bm.normal_update()
        s = sum(f.normal.dot(f.calc_center_median() - c) * f.calc_area() for f in bm.faces)
        if (s < 0) == (orient == "out"):
            bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, uv, "xz")


def round_rect(w, h, r, seg=3, cx=0.0, cy=0.0):
    """Counter-clockwise rounded rectangle (2D), ``seg`` segments per corner,
    starting at the bottom-right corner."""
    pts = []
    r = min(r, w / 2 - 1e-5, h / 2 - 1e-5)
    for ox, oy, a0 in ((w / 2 - r, -h / 2 + r, -90), (w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90.0 * k / seg)
            pts.append((cx + ox + r * math.cos(a), cy + oy + r * math.sin(a)))
    return pts
