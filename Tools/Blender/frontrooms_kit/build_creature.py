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


def silhouettes(kit, png):
    """Transparent black front/side cut-outs at a fixed scale (SIL_PX_PER_M), feet on the
    bottom edge, centred on x = 0: <png>_sil_front.png / _sil_side.png."""
    scene = bpy.context.scene
    cam = scene.camera
    engine = scene.render.engine
    scene.render.engine = "BLENDER_WORKBENCH"
    shading = scene.display.shading
    shading.light = "FLAT"
    shading.color_type = "SINGLE"
    shading.single_color = (0.0, 0.0, 0.0)
    scene.render.film_transparent = True
    scene.render.resolution_x = int(SIL_FRAME[0] * SIL_PX_PER_M)
    scene.render.resolution_y = int(SIL_FRAME[1] * SIL_PX_PER_M)
    scene.render.resolution_percentage = 100
    cam.data.type = "ORTHO"
    cam.data.sensor_fit = "VERTICAL"
    cam.data.ortho_scale = SIL_FRAME[1]
    hidden = [o for o in scene.objects if o.type == "MESH" and o is not kit.object]
    for o in hidden:
        o.hide_render = True
    for suffix, direction in (("front", Vector((0, -1, 0))), ("side", Vector((1, 0, 0)))):
        centre = Vector((0, 0, SIL_FRAME[1] / 2))
        cam.location = centre + direction * 8.0
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = png + "_sil_" + suffix + ".png"
        bpy.ops.render.render(write_still=True)
    for o in hidden:
        o.hide_render = False
    scene.render.film_transparent = False
    scene.render.engine = engine


def envelope(kit, module):
    """Measure the finished mesh against the Relay's gameplay envelope
    (LEVEL_MODULE_SPEC §7, FrontRoomsModuleUnits: r 0.30, <= 2.05 m walking,
    eye 1.60, 1.0 x 2.1 m door). Blender axes: Z up, the creature faces -Y."""
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


def main(argv):
    names, preview_dir, preview, samples, out_root = [], None, True, 48, ROOT
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
        names.append(a); i += 1
    out = os.path.join(out_root, "Assets", "Resources", "Creatures")
    preview_dir = preview_dir or os.path.join(out_root, "Verification", "creature_previews")
    os.makedirs(preview_dir, exist_ok=True)
    failed = []
    for module_name in names:
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module)
            kit = kitlib.Kit(module.NAME)
            module.build(kit, creature_lib)
            kit.finish(getattr(module, "SMOOTH_ANGLE", 60.0))
            env = envelope(kit, module)
            kit.make_lod1(getattr(module, "LOD1", None))
            json_path = os.path.join(out, module.NAME + ".json")
            kit.export(os.path.join(out, module.NAME + ".fbx"), json_path)
            with open(json_path) as fh:
                sidecar = json.load(fh)
            sidecar["envelope"] = env
            sidecar["concept"] = {"title": getattr(module, "TITLE", module.NAME), "pitch": getattr(module, "PITCH", "")}
            with open(json_path, "w") as fh:
                json.dump(sidecar, fh, indent=1)
            print("[creature] exported %s: %d tris, height %.2f m, slots %s" % (
                module.NAME, kit.meta["triangles"], kit.meta["boundsMax"][2], kit.meta["slots"]))
            if preview:
                base = os.path.join(preview_dir, module.NAME)
                kit.preview(base, samples=samples)
                side_preview(kit, base, samples)
                silhouettes(kit, base)
        except Exception:
            traceback.print_exc()
            failed.append(module_name)
    if failed:
        print("[creature] FAILED: %s" % ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
