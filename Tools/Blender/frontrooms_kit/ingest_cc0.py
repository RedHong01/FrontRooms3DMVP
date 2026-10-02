"""Bring downloaded CC0 models (Poly Haven glTF/.blend/.fbx) into the kit.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      --python Tools/Blender/frontrooms_kit/ingest_cc0.py -- ingest.json \
      [--only Kit_PH_ArmChair01] [--out-root /unity/project] [--preview-dir /path] [--samples 32]

ingest.json is a list of entries:
  {
    "name": "Kit_PH_ArmChair01",            # Unity asset name
    "source": "/downloads/ArmChair_01/ArmChair_01_2k.gltf",
    "license": "CC0 1.0, Poly Haven, ArmChair_01 by Kirill Sannikov",
    "yaw": 0,                               # degrees about Z so the FRONT faces -Y
    "scale": 1.0,
    "decimate": 1.0,                        # <1 collapses to that triangle ratio
    "max_texture": 2048,
    "tags": ["pile"],
    "pile": {"cls": "Seat", "mass": 1, "states": ["Upright", "Back", "Side"], "palette": "domestic70s", "topper": false},
    "supports": [{"name": "seat", "centre": [0, -0.05, 0.45], "size": [0.5, 0.45]}]   # Blender space
  }

For every material the importer created, the script reads the Principled BSDF
image inputs (base colour, normal, roughness / glTF metallic-roughness, AO),
writes FrontRooms maps  PH_<asset>_<n>_A.png (sRGB albedo), _N.png (OpenGL
normal), _S.png (R smoothness = 1 - roughness, G = AO)  into
Assets/Resources/Surfaces/Textures, appends a material definition to
Assets/Resources/Props/materials_manifest.json (read by FrontRoomsRenderSetup),
then exports the FBX + sidecar exactly like build_asset.py.
"""

import json
import math
import os
import sys
import traceback

import bpy
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import kitlib  # noqa: E402


def import_source(path):
    before = set(bpy.data.objects)
    ext = os.path.splitext(path)[1].lower()
    if ext in (".gltf", ".glb"):
        bpy.ops.import_scene.gltf(filepath=path)
    elif ext == ".fbx":
        bpy.ops.import_scene.fbx(filepath=path)
    elif ext == ".blend":
        with bpy.data.libraries.load(path, link=False) as (src, dst):
            dst.objects = [n for n in src.objects]
        for obj in dst.objects:
            if obj is not None:
                bpy.context.scene.collection.objects.link(obj)
    elif ext == ".obj":
        bpy.ops.wm.obj_import(filepath=path)
    else:
        raise ValueError("unsupported source " + path)
    return [o for o in bpy.data.objects if o not in before]


def merge_meshes(objects):
    meshes = [o for o in objects if o.type == "MESH"]
    if not meshes:
        raise RuntimeError("no meshes imported")
    bpy.ops.object.select_all(action="DESELECT")
    for o in meshes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    # Bake parents (glTF imports under empties) before joining.
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    if len(meshes) > 1:
        bpy.ops.object.join()
    merged = bpy.context.view_layer.objects.active
    for o in objects:
        if o.name in bpy.data.objects and o is not merged and o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
    return merged


def normalise(obj, yaw, scale):
    obj.rotation_euler = (0, 0, math.radians(yaw))
    obj.scale = (scale, scale, scale)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    xs = [v.co.x for v in obj.data.vertices]
    ys = [v.co.y for v in obj.data.vertices]
    zs = [v.co.z for v in obj.data.vertices]
    shift = Vector(((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, min(zs)))
    obj.data.transform(Matrix.Translation(-shift))
    obj.location = (0, 0, 0)


def decimate(obj, ratio):
    if ratio >= 0.999:
        return
    mod = obj.modifiers.new("decimate", "DECIMATE")
    mod.ratio = ratio
    mod.use_collapse_triangulate = True


def image_input(node, socket_name):
    """Follow a BSDF input back to an image node (through normal/separate nodes)."""
    sock = node.inputs.get(socket_name)
    if sock is None or not sock.is_linked:
        return None, None
    n = sock.links[0].from_node
    channel = None
    for _ in range(4):
        if n.type == "TEX_IMAGE":
            return n.image, channel
        if n.type in ("SEPARATE_COLOR", "SEPRGB", "SEPARATE_RGB"):
            channel = {"Red": 0, "R": 0, "Green": 1, "G": 1, "Blue": 2, "B": 2}.get(sock.links[0].from_socket.name, None)
        nxt = None
        for inp in n.inputs:
            if inp.is_linked:
                nxt = inp.links[0].from_node
                if n.type in ("SEPARATE_COLOR", "SEPRGB", "SEPARATE_RGB"):
                    pass
                break
        if nxt is None:
            return None, None
        sock = inp
        n = nxt
    return None, None


def pixels(image, size):
    if image is None:
        return None
    img = image.copy()
    if max(img.size) > size:
        f = size / max(img.size)
        img.scale(max(1, int(img.size[0] * f)), max(1, int(img.size[1] * f)))
    w, h = img.size
    arr = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(arr)
    bpy.data.images.remove(img)
    return arr.reshape(h, w, 4)


def save_png(path, rgba, colorspace="sRGB"):
    h, w = rgba.shape[:2]
    img = bpy.data.images.new(os.path.basename(path), width=w, height=h, alpha=True, float_buffer=False)
    img.colorspace_settings.name = colorspace if colorspace in ("sRGB", "Non-Color") else "sRGB"
    img.pixels.foreach_set(np.clip(rgba, 0, 1).astype(np.float32).ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def convert_material(mat, stem, tex_dir, max_size):
    """Write _A/_N/_S maps for one imported material; return the manifest entry."""
    bsdf = None
    if mat and mat.use_nodes:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                bsdf = n
                break
    entry = {"name": stem, "texture": stem, "tile": [1, 1], "meshUV": True, "smooth": 1.0,
             "metallic": 0.0, "bump": 1.0, "macroTone": 0.05, "macroDirt": 0.06, "tint": [1, 1, 1]}
    if bsdf is None:
        entry["texture"] = None
        entry["smooth"] = 0.4
        return entry
    base_img, _ = image_input(bsdf, "Base Color")
    rough_img, rough_ch = image_input(bsdf, "Roughness")
    metal_img, metal_ch = image_input(bsdf, "Metallic")
    normal_img = None
    nsock = bsdf.inputs.get("Normal")
    if nsock is not None and nsock.is_linked and nsock.links[0].from_node.type == "NORMAL_MAP":
        nm = nsock.links[0].from_node
        if nm.inputs["Color"].is_linked and nm.inputs["Color"].links[0].from_node.type == "TEX_IMAGE":
            normal_img = nm.inputs["Color"].links[0].from_node.image
    # glTF puts occlusion in a separate group/image; look for an image named *ao* / *occlusion*.
    ao_img = None
    for n in mat.node_tree.nodes:
        if n.type == "TEX_IMAGE" and n.image is not None:
            nm = n.image.name.lower()
            if "_ao" in nm or "occlusion" in nm or "_arm" in nm:
                ao_img = n.image
    base = pixels(base_img, max_size)
    if base is None:
        col = bsdf.inputs["Base Color"].default_value
        entry["texture"] = None
        entry["tint"] = [col[0], col[1], col[2]]
        entry["smooth"] = 1.0 - float(bsdf.inputs["Roughness"].default_value)
        entry["metallic"] = float(bsdf.inputs["Metallic"].default_value)
        return entry
    h, w = base.shape[:2]
    save_png(os.path.join(tex_dir, stem + "_A.png"), base)
    if normal_img is not None:
        nrm = pixels(normal_img, max_size)
        save_png(os.path.join(tex_dir, stem + "_N.png"), nrm, "Non-Color")
    rough = pixels(rough_img, max_size) if rough_img is not None else None
    r = rough[..., rough_ch if rough_ch is not None else 1] if rough is not None else np.full((h, w), float(bsdf.inputs["Roughness"].default_value), np.float32)
    ao = pixels(ao_img, max_size) if ao_img is not None else None
    a = ao[..., 0] if ao is not None else np.ones_like(r)
    if a.shape != r.shape:
        a = np.ones_like(r)
    s = np.stack([1.0 - r, a, np.zeros_like(r), np.ones_like(r)], -1)
    save_png(os.path.join(tex_dir, stem + "_S.png"), s, "Non-Color")
    if metal_img is not None:
        m = pixels(metal_img, 256)
        entry["metallic"] = float(np.mean(m[..., metal_ch if metal_ch is not None else 2]))
    else:
        entry["metallic"] = float(bsdf.inputs["Metallic"].default_value)
    return entry


def reslot_by_albedo(kit, obj, rules, default_slot):
    """Split a single-atlas scan into kit slots: sample the base-colour image
    at each face's UV centroid and assign the first rule whose test holds
    (tests are Python expressions over r, g, b in 0..1)."""
    mat = obj.data.materials[0] if obj.data.materials else None
    img = None
    if mat and mat.use_nodes:
        for n in mat.node_tree.nodes:
            if n.type == "BSDF_PRINCIPLED":
                img, _ = image_input(n, "Base Color")
    if img is None:
        raise RuntimeError("reslot_by_albedo needs a base-colour image")
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    px = px.reshape(h, w, 4)
    slots = [r["slot"] for r in rules] + [default_slot]
    for s in slots:
        kitlib.register_slot(s)
    mesh = obj.data
    mesh.materials.clear()
    for s in slots:
        mesh.materials.append(kit._material(s))
    uv = mesh.uv_layers.active.data

    def classify(poly):
        votes = [0.0] * len(slots)
        pts = [uv[i].uv for i in poly.loop_indices]
        cu = sum(u.x for u in pts) / len(pts)
        cv = sum(u.y for u in pts) / len(pts)
        for u in pts + [type(pts[0])((cu, cv))]:
            r, g, b, _ = px[min(h - 1, int((u.y % 1.0) * h)), min(w - 1, int((u.x % 1.0) * w))]
            idx = len(slots) - 1
            for k, rule in enumerate(rules):
                if eval(rule["test"], {}, {"r": float(r), "g": float(g), "b": float(b)}):
                    idx = k
                    break
            votes[idx] += 1.0
        return votes

    # Vote per connected part (upholstery and frame are usually separate
    # pieces), area-weighted; parts are found with a union-find over edges.
    parent = list(range(len(mesh.polygons)))
    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    edge_faces = {}
    for poly in mesh.polygons:
        for key in poly.edge_keys:
            edge_faces.setdefault(key, []).append(poly.index)
    for faces in edge_faces.values():
        for f in faces[1:]:
            ra, rb = find(faces[0]), find(f)
            if ra != rb:
                parent[rb] = ra
    part_votes = {}
    for poly in mesh.polygons:
        v = classify(poly)
        acc = part_votes.setdefault(find(poly.index), [0.0] * len(slots))
        for k in range(len(slots)):
            acc[k] += v[k] * poly.area
    for poly in mesh.polygons:
        acc = part_votes[find(poly.index)]
        poly.material_index = max(range(len(slots)), key=lambda k: acc[k])
    print("[ingest] reslot: %d parts" % len(part_votes))
    return slots


def uv_to_metres(obj):
    """Rescale UVs per material so 1 UV unit = 1 m (tiling kit materials)."""
    mesh = obj.data
    uv = mesh.uv_layers.active.data
    world = {}
    uvarea = {}
    for poly in mesh.polygons:
        pts = [uv[i].uv for i in poly.loop_indices]
        a = 0.0
        for k in range(1, len(pts) - 1):
            a += abs((pts[k].x - pts[0].x) * (pts[k + 1].y - pts[0].y) - (pts[k + 1].x - pts[0].x) * (pts[k].y - pts[0].y)) / 2
        world[poly.material_index] = world.get(poly.material_index, 0.0) + poly.area
        uvarea[poly.material_index] = uvarea.get(poly.material_index, 0.0) + a
    for poly in mesh.polygons:
        m = poly.material_index
        f = math.sqrt(world[m] / max(uvarea[m], 1e-9))
        for i in poly.loop_indices:
            uv[i].uv = (uv[i].uv.x * f, uv[i].uv.y * f)


def main(argv):
    config, only, out_root, preview_dir, samples = None, None, ROOT, None, 32
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--only":
            only = argv[i + 1]; i += 2; continue
        if a == "--out-root":
            out_root = argv[i + 1]; i += 2; continue
        if a == "--preview-dir":
            preview_dir = argv[i + 1]; i += 2; continue
        if a == "--samples":
            samples = int(argv[i + 1]); i += 2; continue
        config = a; i += 1
    entries = json.load(open(config))
    models = os.path.join(out_root, "Assets", "Resources", "Props", "Models")
    tex_dir = os.path.join(out_root, "Assets", "Resources", "Surfaces", "Textures")
    manifest_path = os.path.join(out_root, "Assets", "Resources", "Props", "materials_manifest.json")
    preview_dir = preview_dir or os.path.join(out_root, "Verification", "kit_previews")
    for d in (models, tex_dir, preview_dir):
        os.makedirs(d, exist_ok=True)
    manifest = json.load(open(manifest_path)) if os.path.exists(manifest_path) else []
    failed = []
    for e in entries:
        if only and e["name"] != only:
            continue
        try:
            kit = kitlib.Kit(e["name"])
            objs = import_source(e["source"])
            merged = merge_meshes(objs)
            normalise(merged, e.get("yaw", 0.0), e.get("scale", 1.0))
            decimate(merged, e.get("decimate", 1.0))
            short = e["name"].replace("Kit_", "")
            slots = []
            if "reslot_by_albedo" in e:
                # Kit slots instead of the scan's own textures (one consistent kit).
                spec = e["reslot_by_albedo"]
                slots = reslot_by_albedo(kit, merged, spec["rules"], spec["default"])
                uv_to_metres(merged)
                kit.adopt(merged, slots, uv="keep")
                entries_done = True
            else:
                entries_done = False
            for k, mat in ([] if entries_done else enumerate(merged.data.materials)):
                stem = "PH_%s_%d" % (short, k)
                entry = convert_material(mat, stem, tex_dir, e.get("max_texture", 2048))
                manifest = [m for m in manifest if m["name"] != stem] + [entry]
                kitlib.register_slot(stem)
                slots.append(stem)
            if not entries_done:
                # Rename the imported materials to the slot names (the FBX submesh names).
                for k, mat in enumerate(merged.data.materials):
                    if mat is not None:
                        mat.name = slots[k]
                kit.adopt(merged, slots, uv="keep")
            for t in e.get("tags", []):
                kit.tag(t)
            if "pile" in e:
                p = e["pile"]
                kit.pile(p["cls"], p.get("mass", 1), p.get("states"), p.get("tolerance"), p.get("palette", "domestic70s"), p.get("topper", False))
            for s in e.get("supports", []):
                kit.support(s["name"], s["centre"], s["size"])
            kit.meta["license"] = e.get("license", "")
            kit.meta["source"] = e.get("source_url", "")
            kit.finish(e.get("smooth_angle", 180.0))
            kit.make_lod1(e.get("lod1"))
            kit.export(os.path.join(models, e["name"] + ".fbx"), os.path.join(models, e["name"] + ".json"))
            print("[ingest] exported %s: %d tris, slots %s" % (e["name"], kit.meta["triangles"], slots))
            kit.preview(os.path.join(preview_dir, e["name"]), samples=samples)
        except Exception:
            traceback.print_exc()
            failed.append(e["name"])
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=1)
    if failed:
        print("[ingest] FAILED: " + ", ".join(failed))
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
