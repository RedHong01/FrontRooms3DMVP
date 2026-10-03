"""Build Hunter concept blockouts (creatures/<module>.py) headless.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python Tools/Blender/frontrooms_kit/build_creature.py -- relay_a relay_b \
      --out-root /unity/copy [--preview-dir /path] [--no-preview] [--samples 48]

Outputs <out-root>/Assets/Resources/Creatures/<NAME>.fbx + .json (same sidecar
format as the prop kit) and Cycles previews <NAME>_a/_b.png (+ _side.png, a
straight side view for the silhouette).
"""

import importlib
import json
import math
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "creatures"))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import creature_lib  # noqa: E402
import kitlib  # noqa: E402


def side_preview(kit, png, samples):
    """An orthographic side and front silhouette pair for the readability sheet."""
    scene = bpy.context.scene
    cam = scene.camera
    if cam is None:
        return
    lo, hi = Vector(kit.meta["boundsMin"]), Vector(kit.meta["boundsMax"])
    centre = (lo + hi) / 2
    # Portrait frame fitted on the figure's height (and width, if wider).
    scene.render.resolution_x = 640
    scene.render.resolution_y = 900
    cam.data.type = "ORTHO"
    cam.data.sensor_fit = "AUTO"
    cam.data.ortho_scale = max(hi.z - lo.z, (max(hi.x - lo.x, hi.y - lo.y)) * 900 / 640) * 1.12
    for suffix, direction in (("side", Vector((1, 0, 0))), ("front", Vector((0, -1, 0)))):
        cam.location = centre + direction * 6.0
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = png + "_" + suffix + ".png"
        bpy.ops.render.render(write_still=True)


SIL_PX_PER_M = 400       # fixed scale for every creature: Figma line-ups stay true to size
SIL_FRAME = (1.4, 2.5)   # metres (width, height), feet at the bottom edge


def silhouettes(kit, png, frame=SIL_FRAME):
    """Transparent black front/side cut-outs at a fixed scale (SIL_PX_PER_M), feet on the
    bottom edge, centred on x = 0: <png>_sil_front.png / _sil_side.png. `frame` is the
    canvas in metres (width, height); giants use a bigger one at the same scale."""
    scene = bpy.context.scene
    cam = scene.camera
    engine = scene.render.engine
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "FLAT"
    shading.color_type = "SINGLE"
    shading.single_color = (0.0, 0.0, 0.0)
    scene.render.film_transparent = True
    scene.render.resolution_x = int(frame[0] * SIL_PX_PER_M)
    scene.render.resolution_y = int(frame[1] * SIL_PX_PER_M)
    scene.render.resolution_percentage = 100
    cam.data.type = "ORTHO"
    cam.data.sensor_fit = "VERTICAL"
    cam.data.ortho_scale = frame[1]
    hidden = [o for o in scene.objects if o.type == "MESH" and o is not kit.object]
    for o in hidden:
        o.hide_render = True
    for suffix, direction in (("front", Vector((0, -1, 0))), ("side", Vector((1, 0, 0)))):
        centre = Vector((0, 0, frame[1] / 2))
        cam.location = centre + direction * 8.0
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = png + "_sil_" + suffix + ".png"
        bpy.ops.render.render(write_still=True)
    for o in hidden:
        o.hide_render = False
    scene.render.film_transparent = False
    scene.render.engine = engine


def envelope(kit, module, pose=None, limits=None):
    """Measure the finished mesh against the Relay's gameplay envelope
    (LEVEL_MODULE_SPEC §7, FrontRoomsModuleUnits: r 0.30, <= 2.05 m walking,
    eye 1.60, 1.0 x 2.1 m door). Blender axes: Z up, the creature faces -Y.
    Multi-pose modules (squeezed giants) pass per-pose limits:
    {"top": max height, "halfWidth": max |x|, "door": True = must fit the
    1.0 x 2.1 opening where it crosses the door plane (|y| < 0.15)}."""
    if limits is not None:
        return pose_envelope(kit, module, pose, limits)
    vs = [v.co for v in kit.object.data.vertices]
    top = max(v.z for v in vs)
    low = min(v.z for v in vs)
    half_w = max(abs(v.x) for v in vs if v.z < 2.1)
    half_w_shoulder = max([abs(v.x) for v in vs if 1.0 <= v.z <= 2.1] or [0.0])
    radial = max([math.hypot(v.x, v.y) for v in vs if 0.4 <= v.z <= 1.95] or [0.0])
    env = {
        "height": round(top, 3), "lowest": round(low, 3),
        "halfWidth": round(half_w, 3), "halfWidthShoulders": round(half_w_shoulder, 3),
        "depthFront": round(-min(v.y for v in vs), 3), "depthBack": round(max(v.y for v in vs), 3),
        "probeRadial": round(radial, 3), "eye": getattr(module, "EYE", None),
        "walkHeightOk": top <= 2.05, "doorOk": top <= 2.08 and half_w <= 0.5, "feetOnFloor": abs(low) <= 0.01,
    }
    print("[creature] envelope %s: h %.2f (<=2.05 %s), door %s, half-width %.2f (shoulders %.2f), probe r %.2f, eye %s, feet %s" % (
        module.NAME, top, "ok" if env["walkHeightOk"] else "OVER", "ok" if env["doorOk"] else "FAIL",
        half_w, half_w_shoulder, radial, env["eye"], "ok" if env["feetOnFloor"] else "off by %.3f" % low))
    return env


def pose_envelope(kit, module, pose, limits):
    vs = [v.co for v in kit.object.data.vertices]
    top = max(v.z for v in vs)
    low = min(v.z for v in vs)
    half_w = max(abs(v.x) for v in vs)
    eye = getattr(module, "EYE", None)
    eye = eye.get(pose) if isinstance(eye, dict) else eye
    env = {"pose": pose, "height": round(top, 3), "lowest": round(low, 3), "halfWidth": round(half_w, 3),
           "depthFront": round(-min(v.y for v in vs), 3), "depthBack": round(max(v.y for v in vs), 3),
           "eye": eye, "feetOnFloor": abs(low) <= 0.01,
           "topOk": top <= limits.get("top", 2.05), "widthOk": half_w <= limits.get("halfWidth", 0.5)}
    if limits.get("door"):
        plane = [v for v in vs if abs(v.y) < 0.15]
        env["doorTop"] = round(max((v.z for v in plane), default=0.0), 3)
        env["doorHalfWidth"] = round(max((abs(v.x) for v in plane), default=0.0), 3)
        env["doorOk"] = env["doorTop"] <= 2.08 and env["doorHalfWidth"] <= 0.48
        env["widthOk"] = True
    flags = " ".join("%s=%s" % (k, "ok" if env[k] else "FAIL") for k in ("topOk", "widthOk", "feetOnFloor", "doorOk") if k in env)
    print("[creature] envelope %s/%s: top %.2f (<= %.2f), half-width %.2f (<= %.2f), eye %s, %s" % (
        module.NAME, pose, top, limits.get("top", 2.05), half_w, limits.get("halfWidth", 0.5), eye, flags))
    return env


def main(argv):
    names, preview_dir, preview, samples, out_root, only_pose = [], None, True, 48, ROOT, None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--preview-dir":
            preview_dir = argv[i + 1]; i += 2; continue
        if a == "--no-preview":
            preview = False; i += 1; continue
        if a == "--samples":
            samples = int(argv[i + 1]); i += 2; continue
        if a == "--out-root":
            out_root = argv[i + 1]; i += 2; continue
        if a == "--pose":
            only_pose = argv[i + 1]; i += 2; continue
        names.append(a); i += 1
    out = os.path.join(out_root, "Assets", "Resources", "Creatures")
    preview_dir = preview_dir or os.path.join(out_root, "Verification", "creature_previews")
    os.makedirs(preview_dir, exist_ok=True)
    failed = []
    jobs = []
    for module_name in names:
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module)
        except Exception:
            traceback.print_exc()
            failed.append(module_name)
            continue
        poses = getattr(module, "POSES", None)
        if poses:
            # Multi-pose module: build(kit, cl, pose) once per pose -> <NAME>_<pose>.
            for pose, limits in poses.items():
                if only_pose is None or pose == only_pose:
                    jobs.append((module_name, module, pose, limits))
        else:
            jobs.append((module_name, module, None, None))
    for module_name, module, pose, limits in jobs:
        try:
            name = module.NAME if pose is None else module.NAME + "_" + pose
            kit = kitlib.Kit(name)
            if pose is None:
                module.build(kit, creature_lib)
            else:
                module.build(kit, creature_lib, pose)
            kit.finish(getattr(module, "SMOOTH_ANGLE", 60.0))
            env = envelope(kit, module, pose, limits)
            kit.make_lod1(getattr(module, "LOD1", None))
            json_path = os.path.join(out, name + ".json")
            kit.export(os.path.join(out, name + ".fbx"), json_path)
            with open(json_path) as fh:
                sidecar = json.load(fh)
            sidecar["envelope"] = env
            sidecar["concept"] = {"title": getattr(module, "TITLE", module.NAME), "pitch": getattr(module, "PITCH", ""), "pose": pose}
            with open(json_path, "w") as fh:
                json.dump(sidecar, fh, indent=1)
            print("[creature] exported %s: %d tris, height %.2f m, slots %s" % (
                name, kit.meta["triangles"], kit.meta["boundsMax"][2], kit.meta["slots"]))
            if preview:
                base = os.path.join(preview_dir, name)
                kit.preview(base, samples=samples)
                side_preview(kit, base, samples)
                silhouettes(kit, base, getattr(module, "SIL_FRAME", SIL_FRAME))
        except Exception:
            traceback.print_exc()
            failed.append(module_name if pose is None else module_name + "/" + pose)
    if failed:
        print("[creature] FAILED: %s" % ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
