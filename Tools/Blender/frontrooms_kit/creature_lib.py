"""Creature blockouts for the Hunter concepts (early-stage, not production).

A creature module (creatures/<name>.py) defines NAME and build(kit, cl) where
``cl`` is this module. The typical body is a Skin-modifier blockout: a list
of joints (name, (x, y, z) metres, radius) and the bones between them, skinned,
subdivided and applied into one smooth organic mesh. Hard parts (a head shell,
costume pieces, props) use the normal kitlib primitives on the same Kit, so the
export, sidecar and preview pipeline is identical to the prop kit:

  Blender -b --factory-startup --python Tools/Blender/frontrooms_kit/build_creature.py -- <module> \
          --out-root /unity/copy --preview-dir /path

Conventions (as the kit): metres, Z up, the creature FACES -Y (Unity +Z), feet
on z = 0, centred on x = y = 0. Build it already in its stalking pose.
"""

import math

import bmesh
import bpy
from mathutils import Vector


def skin_body(kit, joints, bones, slot, subdiv=2, name="body", smooth=True):
    """joints: {name: ((x, y, z), radius) or ((x, y, z), (rx, ry))}; bones: [(a, b), ...].
    Returns the skinned, subdivided, applied mesh object (registered with the kit)."""
    mesh = bpy.data.meshes.new(name)
    names = list(joints.keys())
    index = {n: i for i, n in enumerate(names)}
    verts = [Vector(joints[n][0]) for n in names]
    edges = [(index[a], index[b]) for a, b in bones]
    mesh.from_pydata(verts, edges, [])
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    skin = obj.modifiers.new("skin", "SKIN")
    skin.use_smooth_shade = smooth
    skin.branch_smoothing = 0.6
    # Root = the first joint (pelvis), required for a stable skin.
    obj.data.skin_vertices[0].data[0].use_root = True
    for i, n in enumerate(names):
        r = joints[n][1]
        rx, ry = (r, r) if isinstance(r, (int, float)) else r
        obj.data.skin_vertices[0].data[i].radius = (rx, ry)
    sub = obj.modifiers.new("subdiv", "SUBSURF")
    sub.levels = subdiv
    sub.render_levels = subdiv
    bpy.context.view_layer.objects.active = obj
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)
    obj.data.materials.append(kit._material(slot))
    obj["fr_uv"] = "metres"
    obj["fr_decal_axes"] = "xz"
    kit.parts.append(obj)
    return obj


def ellipsoid(kit, size, loc, slot, rot=(0, 0, 0), segments=24, rings=14, name="ellipsoid"):
    """A smooth ellipsoid (head shells, joints, padding)."""
    return kit.soft_box(size, loc, slot, radius=max(size) * 0.6, segments=segments, rings=rings, rot=rot, name=name)


def decimate_to(obj, max_tris):
    """Keep blockouts light: collapse-decimate a part above max_tris."""
    tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
    if tris <= max_tris:
        return tris
    mod = obj.modifiers.new("dec", "DECIMATE")
    mod.ratio = max(0.05, max_tris / tris)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)
