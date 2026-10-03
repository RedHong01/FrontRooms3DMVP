"""LOD1 shim for the workstation group (Kit_OfficeDesk, the cubicle panels).

Two problems with kitlib.Kit.make_lod1's blind collapse-decimate:

1. It never re-marks sharp edges, so on the LOD1 the 90-degree box corners
   interpolate their normals: square legs and rails shade like round tubes
   and laminate edges smear into gradients (a visible shading change at the
   LOD switch).
2. It spends the reduction on whatever collapses cheapest. On a cubicle
   panel the 84 isolated 2-tri standard slots cannot collapse, so it eats
   the rounded top cap (it turns into a wedge) and the trims' round corners
   instead, and half-collapses the slots into sub-pixel shimmer.

``sharp_lod1(kit)`` wraps THIS Kit instance's make_lod1 (kitlib itself is
not edited). Parts flagged with ``lod1_drop(obj)`` (details that are sub-pixel
at the LOD1 switch, ~10 % screen height: standard slots, glides) are deleted
from the LOD1 copy first; the collapse-decimate then only runs if what is
left is still above ``ratio`` x LOD0, so the silhouette survives intact.
Finally the LOD1 is shaded smooth and its sharp edges re-marked at the same
angle finish() uses. If kitlib later does the sharp pass itself, the shim
repeats it harmlessly. Without flagged parts it is kitlib's make_lod1 plus
the sharp pass.
"""

import math

import bmesh
import bpy

DROP = "fr_lod1_drop"


def lod1_drop(obj):
    """Flag every face of a part (before kit.finish) as LOD0-only."""
    me = obj.data
    attr = me.attributes.get(DROP) or me.attributes.new(DROP, "INT", "FACE")
    attr.data.foreach_set("value", [1] * len(me.polygons))
    return obj


def _tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def _strip(obj):
    if obj is not None and obj.data.attributes.get(DROP) is not None:
        obj.data.attributes.remove(obj.data.attributes[DROP])


def sharp_lod1(kit, angle=35.0):
    if getattr(kit, "_fr_sharp_lod1", False):
        return
    base = kit.make_lod1

    def make_lod1(ratio):
        src = kit.object
        if not ratio or ratio >= 0.95 or src.data.attributes.get(DROP) is None:
            base(ratio)
        else:
            old = getattr(kit, "lod1", None)
            if old is not None:
                bpy.data.objects.remove(old, do_unlink=True)
                kit.lod1 = None
            lod1 = src.copy()
            lod1.data = src.data.copy()
            bpy.context.scene.collection.objects.link(lod1)
            bm = bmesh.new()
            bm.from_mesh(lod1.data)
            layer = bm.faces.layers.int.get(DROP)
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[layer]], context="FACES")
            bm.to_mesh(lod1.data)
            bm.free()
            target = ratio * _tris(src)
            left = _tris(lod1)
            if left > target:
                mod = lod1.modifiers.new("lod1", "DECIMATE")
                mod.ratio = target / left
                mod.use_collapse_triangulate = True
                bpy.ops.object.select_all(action="DESELECT")
                bpy.context.view_layer.objects.active = lod1
                lod1.select_set(True)
                bpy.ops.object.modifier_apply(modifier=mod.name)
            src.name = kit.name + "_LOD0"
            lod1.name = kit.name + "_LOD1"
            kit.lod1 = lod1
            kit.meta["trianglesLod1"] = _tris(lod1)
        lod1 = getattr(kit, "lod1", None)
        _strip(src)
        _strip(lod1)
        if lod1 is not None:
            lod1.data.shade_smooth()
            lod1.data.set_sharp_from_angle(angle=math.radians(angle))

    kit.make_lod1 = make_lod1
    kit._fr_sharp_lod1 = True
