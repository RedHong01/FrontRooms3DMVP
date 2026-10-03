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
    # One root per connected chain (the first joint of each), required for a stable skin;
    # a chain without a root is silently dropped by the modifier.
    parent = list(range(len(names)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a, b in edges:
        parent[find(a)] = find(b)
    seen = set()
    for i in range(len(names)):
        if find(i) not in seen:
            seen.add(find(i))
            obj.data.skin_vertices[0].data[i].use_root = True
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


# ---------------------------------------------------------------- humanoid frame
def humanoid_joints(height=1.95, hip=0.92, shoulder_half=0.24, chest_z=None, neck_len=0.12,
                    head_forward=0.0, head_drop=0.0, upper_arm=0.32, forearm=0.28, hand=0.19,
                    arm_out=0.08, arm_forward=0.02, elbow_bend=12.0, stoop=12.0, stride=0.12,
                    foot_len=0.27, hip_half=0.11):
    """A posed adult frame (metres, Z up, facing -Y, feet on z = 0): returns
    {name: (x, y, z)} for pelvis, belly, chest, neck, head, crown, shoulder/elbow/
    wrist/hand _l/_r, hip/knee/ankle/toe _l/_r. Modules give each joint a radius
    and pass subsets to skin_body() per material (jacket, trousers, skin...).

    stoop     forward pitch of everything above the pelvis (deg)
    neck_len  chest-top to head centre; head_forward/head_drop move the head
              forward (-Y) and down relative to that (a head below the shoulders)
    stride    half the foot spread along Y (left foot forward)
    The crown lands near `height` before stoop; check the envelope printout."""
    sx = 1.0
    pelvis = Vector((0, 0, hip))
    torso_len = height - hip - neck_len - 0.20      # head centre ~0.11 under the crown
    chest_z = hip + torso_len * 0.72 if chest_z is None else chest_z
    up = {
        "belly": Vector((0, 0, hip + torso_len * 0.32)),
        "chest": Vector((0, 0, chest_z)),
        "neck": Vector((0, -0.01, hip + torso_len + 0.02)),
        "head": Vector((0, -0.02 - head_forward, hip + torso_len + neck_len - head_drop)),
        "crown": Vector((0, -0.01 - head_forward, hip + torso_len + neck_len + 0.10 - head_drop)),
    }
    sh_z = hip + torso_len * 0.94
    for side, s in (("l", 1), ("r", -1)):
        sh = Vector((s * shoulder_half, 0.0, sh_z))
        bend = math.radians(elbow_bend)
        el = sh + Vector((s * arm_out * 0.6, -arm_forward, -upper_arm))
        wr = el + Vector((s * arm_out * 0.4, -forearm * math.sin(bend), -forearm * math.cos(bend)))
        hd = wr + Vector((0, -hand * 0.15, -hand))
        up.update({"shoulder_" + side: sh, "elbow_" + side: el, "wrist_" + side: wr, "hand_" + side: hd,
                   "cuff_" + side: el.lerp(wr, 0.72)})    # inside the sleeve: hands start here
    up["neck_base"] = up["chest"].lerp(up["neck"], 0.55)    # inside the collar: the neck/head start here
    th = math.radians(stoop)
    out = {"pelvis": pelvis}
    for k, p in up.items():
        rel = p - pelvis
        out[k] = pelvis + Vector((rel.x, rel.y * math.cos(th) - rel.z * math.sin(th), rel.y * math.sin(th) + rel.z * math.cos(th)))
    leg = hip - 0.07
    for side, s, fwd in (("l", 1, -stride), ("r", -1, stride)):
        hp = Vector((s * hip_half, 0, hip - 0.04))
        an = Vector((s * (hip_half + 0.01), fwd, 0.085))
        kn = (hp + an) / 2 + Vector((s * 0.005, -0.035, 0))
        # Keep the shin+thigh length close to `leg` (rough; the stride shortens it a little).
        tp = an + Vector((0, -foot_len * 0.62, -0.05))
        out.update({"hip_" + side: hp, "knee_" + side: kn, "ankle_" + side: an, "toe_" + side: tp,
                    "seat_" + side: Vector((s * hip_half * 0.7, 0.01, hip + 0.06)),   # inside the hem/torso
                    "shin_" + side: kn.lerp(an, 0.7)})    # inside the trouser leg: shoes/feet start here
    return {k: tuple(round(c, 4) for c in v) for k, v in out.items()}


# Bone sets per garment. Parts overlap (cuff, neck_base, shin) so the subdivided tube
# ends tuck inside the neighbouring part instead of leaving gaps.
BODY_BONES = [("pelvis", "belly"), ("belly", "chest"), ("chest", "neck")]
SHOULDER_BONES = [("chest", "shoulder_l"), ("chest", "shoulder_r")]
ARM_BONES = {s: [("shoulder_" + s, "elbow_" + s), ("elbow_" + s, "wrist_" + s)] for s in ("l", "r")}
HAND_BONES = {s: [("cuff_" + s, "wrist_" + s), ("wrist_" + s, "hand_" + s)] for s in ("l", "r")}
# Two separate leg chains starting inside the torso (a shared pelvis branch makes the
# Skin modifier fold a flat sheet at the crotch).
LEG_BONES = [("seat_l", "hip_l"), ("hip_l", "knee_l"), ("knee_l", "ankle_l"),
             ("seat_r", "hip_r"), ("hip_r", "knee_r"), ("knee_r", "ankle_r")]
FOOT_BONES = {s: [("shin_" + s, "ankle_" + s), ("ankle_" + s, "toe_" + s)] for s in ("l", "r")}
HEAD_BONES = [("neck_base", "neck"), ("neck", "head"), ("head", "crown")]


def part(kit, frame, radii, bones, slot, subdiv=2, name="part", max_tris=None):
    """skin_body() over a subset of a humanoid_joints() frame. radii: {joint: r or (rx, ry)};
    the first joint of the first bone is the skin root."""
    names = []
    for a, b in bones:
        for n in (a, b):
            if n not in names:
                names.append(n)
    joints = {n: (frame[n], radii[n]) for n in names}
    obj = skin_body(kit, joints, bones, slot, subdiv=subdiv, name=name)
    if max_tris:
        decimate_to(obj, max_tris)
    return obj


def floor_parts(kit):
    """Drop every part so the lowest vertex of the whole figure sits on z = 0."""
    lo = min((obj.matrix_world @ v.co).z for obj in kit.parts for v in obj.data.vertices)
    for obj in kit.parts:
        obj.location.z -= lo
    return lo
