"""Horizontal-grain metre UVs for the seating group (helper, NOT an asset module).

Used by ladder_chair and bar_stool.

Why: Prop_WoodOak is rendered in Unity with the DoorVeneer texture, whose
grain runs along V (tile 0.6 x 1.2). kitlib._uv_metres puts V on world Z for
every face whose normal is mostly +-X or +-Y, so a horizontal part (a back
slat, a seat rail, a turned rung, a steam-bent foot ring, the rim of a
round seat) shows its stripes running ACROSS its width instead of along it.

What install(kit) does: on THIS Kit instance only (kitlib.py is not edited),
parts whose ``obj["fr_uv"]`` is ``"metres_h"`` first get kitlib's own metre
projection, then

* faces whose dominant normal is X or Y have their UVs turned a quarter
  ((u, v) -> (v, -u)), so V runs horizontally along the part;
* faces whose dominant normal is Z are turned the same way only when the
  part's grain axis is X: ``obj["fr_grain"]`` ("x" / "y") if set, else the
  longer of the part's world X / Y extents (a front rail's top runs along X,
  a side rail's top already runs along Y).

Parts whose ``obj["fr_uv"]`` is ``"metres_ring"`` (a steam-bent hoop such
as a stool foot ring) get a cylindrical mapping round the part's own vertical
axis instead: V = arc length along the hoop's centre line (radius
``obj["fr_ring_r"]``), U = height on the side faces and radius on the top
and bottom faces, so the grain follows the bend on every face. The one UV
seam (the scarf joint of a real bent ring) is at the back (+Y).

Parts whose ``obj["fr_uv"]`` is ``"metres_axis"`` (a splayed turned leg) get
a cylindrical mapping round their own turning axis (``obj["fr_axis_o"]``,
``obj["fr_axis_d"]``): V = distance along the axis, U = arc length round it,
so the grain runs straight down a raked leg instead of breaking into
chevrons at the box-projection seams. The single seam faces
``-obj["fr_axis_out"]`` (pass the outward direction so it hides on the
inside of the leg); end caps are planar.

Every other part (legs, posts, blocks, fabric, metal) keeps kitlib's
mapping exactly, and texel density stays 1 UV unit per metre. If kitlib's
own _uv_metres later learns all three modes, install() does nothing and kitlib
takes over; this file can then be deleted.

2026-10-02 (round 2): kitlib._uv_metres is now grain-aware for every wood slot
(obj["fr_grain"] or the board's long axis), so "metres_h" no longer needs the
quarter turn: horizontal() just sets fr_grain and kitlib does the rest (the
turn is skipped when kitlib reads fr_grain, otherwise it would cross the grain
again). "metres_ring" and "metres_axis" are still this helper's job.
"""

import inspect
import math

import bmesh
from mathutils import Vector

import kitlib

MODE = "metres_h"
RING = "metres_ring"
AXIS = "metres_axis"


def _kitlib_has_modes():
    try:
        src = inspect.getsource(kitlib.Kit._uv_metres)
    except (OSError, TypeError):
        return False
    return MODE in src and RING in src and AXIS in src


def _uv_ring(obj):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    layer = bm.loops.layers.uv.verify()
    mw = obj.matrix_world
    rot = mw.to_3x3()
    pts = [mw @ v.co for v in bm.verts]
    cx = (max(p.x for p in pts) + min(p.x for p in pts)) / 2
    cy = (max(p.y for p in pts) + min(p.y for p in pts)) / 2
    r0 = float(obj.get("fr_ring_r", 0.0)) or sum(math.hypot(p.x - cx, p.y - cy) for p in pts) / len(pts)
    for face in bm.faces:
        n = (rot @ face.normal).normalized()
        c = mw @ face.calc_center_median()
        rad = math.hypot(c.x - cx, c.y - cy) or 1.0
        nr = (n.x * (c.x - cx) + n.y * (c.y - cy)) / rad
        top = abs(n.z) > abs(nr)
        uvs = []
        for loop in face.loops:
            p = mw @ loop.vert.co
            th = math.atan2(-(p.x - cx), -(p.y - cy))      # wraps at the back (+Y)
            u = math.hypot(p.x - cx, p.y - cy) * (1 if n.z >= 0 else -1) if top else p.z
            uvs.append([u, th])
        ths = [t for _, t in uvs]
        if max(ths) - min(ths) > math.pi:
            for uv in uvs:
                if uv[1] < 0:
                    uv[1] += 2 * math.pi
        for loop, (u, th) in zip(face.loops, uvs):
            loop[layer].uv = (u, th * r0)
    bm.to_mesh(mesh)
    bm.free()


def _uv_axis(obj):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    layer = bm.loops.layers.uv.verify()
    mw = obj.matrix_world
    rot = mw.to_3x3()
    o = Vector(obj["fr_axis_o"])
    a = Vector(obj["fr_axis_d"]).normalized()
    out = Vector(obj.get("fr_axis_out", (0.0, 1.0, 0.0)))
    e1 = out - a * out.dot(a)
    if e1.length < 1e-6:
        e1 = a.orthogonal()
    e1.normalize()
    e2 = a.cross(e1)
    pts = [mw @ v.co for v in bm.verts]
    r0 = sum(((p - o) - a * (p - o).dot(a)).length for p in pts) / len(pts)
    for face in bm.faces:
        n = (rot @ face.normal).normalized()
        cap = abs(n.dot(a)) > 0.7
        uvs = []
        for loop in face.loops:
            w = (mw @ loop.vert.co) - o
            t = w.dot(a)
            q = w - a * t
            if cap:
                uvs.append([q.dot(e1), q.dot(e2)])
            else:
                uvs.append([math.atan2(q.dot(e2), q.dot(e1)), t])
        if not cap:
            ths = [uv[0] for uv in uvs]
            if max(ths) - min(ths) > math.pi:
                for uv in uvs:
                    if uv[0] < 0:
                        uv[0] += 2 * math.pi
            for uv in uvs:
                uv[0] *= r0
        for loop, uv in zip(face.loops, uvs):
            loop[layer].uv = tuple(uv)
    bm.to_mesh(mesh)
    bm.free()


def _kitlib_has_grain():
    """kitlib >= round 2 runs wood grain along obj["fr_grain"] itself."""
    try:
        return "fr_grain" in inspect.getsource(kitlib.Kit._uv_metres)
    except (OSError, TypeError):
        return False


def _uv_metres_h(obj):
    kitlib.Kit._uv_metres(obj)
    if obj.get("fr_uv") == RING:
        _uv_ring(obj)
        return
    if obj.get("fr_uv") == AXIS:
        _uv_axis(obj)
        return
    if obj.get("fr_uv") != MODE:
        return
    if _kitlib_has_grain():
        # kitlib's own projection already put V along fr_grain (or the
        # board's long axis); the legacy quarter turn below would now turn
        # the grain back across the part.
        return
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    layer = bm.loops.layers.uv.verify()
    mw = obj.matrix_world
    rot = mw.to_3x3()
    pts = [mw @ v.co for v in bm.verts]
    grain = obj.get("fr_grain")
    if grain not in ("x", "y"):
        ext_x = max(p.x for p in pts) - min(p.x for p in pts)
        ext_y = max(p.y for p in pts) - min(p.y for p in pts)
        grain = "x" if ext_x > ext_y else "y"
    for face in bm.faces:
        n = (rot @ face.normal).normalized()
        ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
        if az >= ax and az >= ay and grain != "x":
            continue
        for loop in face.loops:
            u, v = loop[layer].uv
            loop[layer].uv = (v, -u)
    bm.to_mesh(mesh)
    bm.free()


def install(kit):
    """Honour fr_uv = metres_h / metres_ring / metres_axis for this Kit's metre UVs."""
    if not _kitlib_has_modes():
        kit._uv_metres = _uv_metres_h


def ring(obj, radius):
    """Mark a bent hoop for cylindrical grain round its vertical axis."""
    obj["fr_uv"] = RING
    obj["fr_ring_r"] = float(radius)
    return obj


def axial(obj, p0, p1, out=None):
    """Mark a turned part for grain along its axis p0 -> p1 (seam facing -out)."""
    d = Vector(p1) - Vector(p0)
    obj["fr_uv"] = AXIS
    obj["fr_axis_o"] = tuple(Vector(p0))
    obj["fr_axis_d"] = tuple(d.normalized())
    if out is not None:
        obj["fr_axis_out"] = tuple(out)
    return obj


def horizontal(obj, grain=None):
    """Mark a part for horizontal grain (optionally forcing the top-face axis)."""
    obj["fr_uv"] = MODE
    if grain:
        obj["fr_grain"] = grain
    return obj
