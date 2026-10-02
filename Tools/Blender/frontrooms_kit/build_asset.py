"""Build one or more kit assets headless.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python Tools/Blender/frontrooms_kit/build_asset.py -- crt_monitor desk_90s \
      [--preview-dir /path] [--no-preview] [--samples 48] [--out-root /unity/project]

Each name is a module in ``assets/`` exposing ``NAME`` (the Unity asset name)
and ``build(kit)``. Outputs go to Assets/Resources/Props/Models/.
"""

import importlib
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "assets"))

import kitlib  # noqa: E402

OUT = os.path.join(ROOT, "Assets", "Resources", "Props", "Models")


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
    preview_dir = preview_dir or os.path.join(out_root, "Verification", "kit_previews")
    out = os.path.join(out_root, "Assets", "Resources", "Props", "Models")
    os.makedirs(preview_dir, exist_ok=True)
    failed = []
    for module_name in names:
        try:
            module = importlib.import_module(module_name)
            importlib.reload(module)
            kit = kitlib.Kit(module.NAME)
            module.build(kit)
            kit.finish(getattr(module, "SMOOTH_ANGLE", 35.0))
            # Optional LOD1 (module.LOD1 = triangle ratio) and material variants
            # (module.VARIANTS = {"Kit_X_Floral": {"Prop_FabricBeige": "Prop_FabricFloral"}}).
            kit.make_lod1(getattr(module, "LOD1", None))
            kit.export(os.path.join(out, module.NAME + ".fbx"), os.path.join(out, module.NAME + ".json"))
            print("[kit] exported %s: %d tris (LOD1 %s), slots %s" % (module.NAME, kit.meta["triangles"], kit.meta.get("trianglesLod1", "-"), kit.meta["slots"]))
            for variant, remap in getattr(module, "VARIANTS", {}).items():
                for old_slot, new_slot in remap.items():
                    kit.set_slot(old_slot, new_slot)
                kit.export(os.path.join(out, variant + ".fbx"), os.path.join(out, variant + ".json"), name=variant)
                print("[kit] exported variant %s" % variant)
                for old_slot, new_slot in remap.items():
                    kit.set_slot(new_slot, old_slot)
            if preview:
                kit.preview(os.path.join(preview_dir, module.NAME), samples=samples)
                print("[kit] preview %s" % os.path.join(preview_dir, module.NAME + "_a.png"))
        except Exception:
            traceback.print_exc()
            failed.append(module_name)
    if failed:
        print("[kit] FAILED: %s" % ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
