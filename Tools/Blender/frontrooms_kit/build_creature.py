"""Build Hunter concept blockouts (creatures/<module>.py) headless.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python Tools/Blender/frontrooms_kit/build_creature.py -- relay_a relay_b \
      --out-root /unity/copy [--preview-dir /path] [--no-preview] [--samples 48]

Outputs <out-root>/Assets/Resources/Creatures/<NAME>.fbx + .json (same sidecar
format as the prop kit) and Cycles previews <NAME>_a/_b.png (+ _side.png, a
straight side view for the silhouette).
"""

import importlib
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
            kit.make_lod1(getattr(module, "LOD1", None))
            kit.export(os.path.join(out, module.NAME + ".fbx"), os.path.join(out, module.NAME + ".json"))
            print("[creature] exported %s: %d tris, height %.2f m, slots %s" % (
                module.NAME, kit.meta["triangles"], kit.meta["boundsMax"][2], kit.meta["slots"]))
            if preview:
                base = os.path.join(preview_dir, module.NAME)
                kit.preview(base, samples=samples)
                side_preview(kit, base, samples)
        except Exception:
            traceback.print_exc()
            failed.append(module_name)
    if failed:
        print("[creature] FAILED: %s" % ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
