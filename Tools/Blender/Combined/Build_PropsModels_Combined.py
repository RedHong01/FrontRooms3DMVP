import bpy
import json
import math
import os
from pathlib import Path
from mathutils import Vector

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_DIR = PROJECT_ROOT / "Assets" / "Resources" / "Props" / "Models"
OUT_DIR = Path(__file__).resolve().parent
OUT_BLEND = OUT_DIR / "Props_Models_Combined.blend"
OUT_RENDER = OUT_DIR / "Props_Models_Combined_preview.png"

# The source folder is read only. This script only writes into Tools/Blender/Combined.
fbx_paths = sorted(MODEL_DIR.glob("*.fbx"), key=lambda p: p.name.lower())

# Start from an empty scene; imported FBX data is kept local to this catalog blend.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    if collection.name != "Collection":
        bpy.data.collections.remove(collection)
if "Collection" in bpy.data.collections:
    root_collection = bpy.data.collections["Collection"]
    root_collection.name = "MODEL_CATALOG"
else:
    root_collection = bpy.data.collections.new("MODEL_CATALOG")
    bpy.context.scene.collection.children.link(root_collection)

# Remove default collection children left by factory startup.
for child in list(bpy.context.scene.collection.children):
    if child != root_collection:
        bpy.context.scene.collection.children.unlink(child)

# Scene folders for quick inspection.
collections = {"Office": bpy.data.collections.new("01_OFFICE"),
               "Domestic": bpy.data.collections.new("02_DOMESTIC"),
               "Storage": bpy.data.collections.new("03_STORAGE"),
               "Other": bpy.data.collections.new("04_OTHER")}
for c in collections.values():
    root_collection.children.link(c)

# Neutral catalog materials.
def mat(name, color, roughness=0.65, metallic=0.0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (*color, 1.0)
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = metallic
    return m
floor_mat = mat("Catalog_Floor", (0.16, 0.19, 0.23), 0.82)
label_mat = mat("Catalog_Label", (0.82, 0.91, 1.0), 0.5)
header_mat = mat("Catalog_Header", (1.0, 0.55, 0.12), 0.5)

# Read sidecar tags without changing them.
def sidecar_info(name):
    p = MODEL_DIR / (name + ".json")
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text())
    except Exception:
        return {}

def category(info):
    tags = set(info.get("tags", []))
    if "office" in tags:
        return "Office"
    if "storage" in tags or "case_goods" in tags or "pile" in tags:
        # Domestic furniture remains visually grouped separately from crates/pallets.
        if "domestic" in tags or "upholstery" in tags or "seat" in tags:
            return "Domestic"
        return "Storage"
    if "domestic" in tags or "upholstery" in tags or "seat" in tags:
        return "Domestic"
    if "crate" in tags or "pallet" in tags:
        return "Storage"
    return "Other"

# Assets are arranged in category blocks, six columns wide.
cols = 6
cell_x = 4.6
cell_y = 4.6
block_gap = 2.0
category_order = ["Office", "Domestic", "Storage", "Other"]
category_rows = {key: 0 for key in category_order}
category_base_y = {}
row_cursor = 0
for key in category_order:
    category_base_y[key] = row_cursor
    count = sum(1 for p in fbx_paths if category(sidecar_info(p.stem)) == key)
    row_cursor += max(1, math.ceil(count / cols)) + 1

# Text labels lie on the catalog floor, readable in top/angled view.
def add_text(body, location, size, material, parent=None):
    curve = bpy.data.curves.new("LabelCurve_" + body, type='FONT')
    curve.body = body
    curve.align_x = 'CENTER'
    curve.align_y = 'CENTER'
    curve.size = size
    curve.extrude = 0.004
    obj = bpy.data.objects.new("LABEL_" + body, curve)
    target_collection = (next(iter(parent.users_collection), root_collection) if parent else root_collection)
    target_collection.objects.link(obj)
    obj.location = location
    obj.data.materials.append(material)
    return obj

imported_count = 0
asset_records = []
for index, fbx in enumerate(fbx_paths):
    info = sidecar_info(fbx.stem)
    cat = category(info)
    cat_collection = collections[cat]
    local_index = category_rows[cat]
    category_rows[cat] += 1
    col = local_index % cols
    row = local_index // cols
    x = (col - (cols - 1) / 2.0) * cell_x
    y = (row + category_base_y[cat]) * cell_y

    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(fbx), use_custom_normals=True, use_image_search=False)
    imported = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in imported if o.type == 'MESH']
    if not meshes:
        continue

    # Keep every imported object and move it under a named asset root.
    root = bpy.data.objects.new("ASSET_" + fbx.stem, None)
    cat_collection.objects.link(root)
    root.empty_display_type = 'PLAIN_AXES'
    root.empty_display_size = 0.35
    root["source_fbx"] = str(fbx)
    root["source_json"] = str(MODEL_DIR / (fbx.stem + ".json"))
    root["kit_name"] = fbx.stem
    root["category"] = cat
    root["tags"] = ", ".join(info.get("tags", []))
    root["placement"] = info.get("placement", "")
    root["triangles_lod0"] = int(info.get("triangles", 0) or 0)
    root["triangles_lod1"] = int(info.get("trianglesLod1", 0) or 0)

    for obj in imported:
        # Move imported objects to the category collection, preserving transforms.
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        cat_collection.objects.link(obj)
        obj.parent = root
        obj.matrix_parent_inverse = root.matrix_world.inverted()

    # Compute imported bounds in world space, then put the whole asset on the floor.
    depsgraph = bpy.context.evaluated_depsgraph_get()
    corners = []
    for mesh in meshes:
        evaluated = mesh.evaluated_get(depsgraph)
        for corner in evaluated.bound_box:
            corners.append(evaluated.matrix_world @ Vector(corner))
    if corners:
        min_x = min(v.x for v in corners); max_x = max(v.x for v in corners)
        min_y = min(v.y for v in corners); max_y = max(v.y for v in corners)
        min_z = min(v.z for v in corners); max_z = max(v.z for v in corners)
        # Blender is Z-up; Unity FBX imports arrive with an X=90° object
        # rotation so their world bounds are X width, Y depth, Z height.
        root.location += Vector((x - (min_x + max_x) * 0.5, y - (min_y + max_y) * 0.5, -min_z))
        root["bounds_m"] = "%.4f x %.4f x %.4f" % (max_x - min_x, max_y - min_y, max_z - min_z)

    label = add_text(fbx.stem.replace("Kit_", ""), (0, -1.95, 0.012), 0.25, label_mat, parent=root)
    label["source_fbx"] = str(fbx)
    imported_count += 1
    asset_records.append((fbx.stem, cat, info.get("tags", [])))

# Floor plane, grid strips and category headers.
width = cols * cell_x + 3.0
depth = (row_cursor + 1) * cell_y + 2.0
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, (row_cursor - 1) * cell_y * 0.5, -0.035))
floor = bpy.context.object
floor.name = "CATALOG_FLOOR"
floor.scale = (width * 0.5, depth * 0.5, 1)
floor.data.materials.append(floor_mat)
for c in list(floor.users_collection): c.objects.unlink(floor)
root_collection.objects.link(floor)

for key in category_order:
    header_y = (category_base_y[key] - 0.53) * cell_y
    add_text(f"{key.upper()}  ({sum(1 for n,c,t in asset_records if c == key)})", (0, header_y, 0.02), 0.42, header_mat)

# A small legend / provenance plaque.
legend_text = (
    "FRONTROOMS PROP MODEL CATALOG\n"
    f"{imported_count} FBX assets imported from Assets/Resources/Props/Models\n"
    "Source folder preserved; this file is a separate inspection copy\n"
    "Kit FBX + JSON sidecars | Blender catalog build"
)
curve = bpy.data.curves.new("CatalogLegendCurve", type='FONT')
curve.body = legend_text
curve.align_x = 'LEFT'
curve.align_y = 'BOTTOM'
curve.size = 0.28
curve.extrude = 0.004
legend = bpy.data.objects.new("CATALOG_LEGEND", curve)
root_collection.objects.link(legend)
legend.location = (-width * 0.5 + 0.6, -2.5, 0.02)
legend.data.materials.append(header_mat)

# Notes inside the .blend for provenance.
notes = bpy.data.texts.new("SOURCE_NOTES")
notes.write(
    "FRONTROOMS PROP MODEL CATALOG\n"
    "============================\n"
    f"Imported FBX count: {imported_count}\n"
    f"Read-only source folder: {MODEL_DIR}\n"
    "This catalog does not overwrite or rewrite the source FBX/JSON files.\n"
    "Most Kit FBX files are generated by Tools/Blender/frontrooms_kit/build_asset.py\n"
    "from one Python module per asset. Kit_BergereChair is the exception: it\n"
    "was ingested from the Poly Haven GreenChair_01 glTF and re-slotted.\n"
    "Each asset root stores source_fbx/source_json custom properties.\n"
)

# World, camera and lights for an immediately useful inspection view.
scene = bpy.context.scene
scene["catalog_source_folder"] = str(MODEL_DIR)
scene["catalog_imported_count"] = imported_count
scene["catalog_source_folder_fbx_count"] = len(fbx_paths)
scene["catalog_status"] = "Source folder preserved; combined inspection copy"
scene.render.engine = 'BLENDER_WORKBENCH'
scene.render.resolution_x = 1600
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 50
scene.render.image_settings.file_format = 'PNG'
scene.render.filepath = str(OUT_RENDER)
scene.display.shading.light = 'STUDIO'
scene.display.shading.color_type = 'MATERIAL'
scene.display.shading.show_shadows = True
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = 'WORLD'
scene.display.shading.show_specular_highlight = True
scene.display.shading.background_type = 'WORLD'
scene.world.color = (0.04, 0.05, 0.07)
scene.world.use_nodes = True
world_bg = scene.world.node_tree.nodes.get('Background')
if world_bg:
    world_bg.inputs['Color'].default_value = (0.045, 0.055, 0.075, 1.0)
    world_bg.inputs['Strength'].default_value = 0.45

# Camera looking at the catalog center.
def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

cam_data = bpy.data.cameras.new("CatalogCamera")
cam = bpy.data.objects.new("CATALOG_CAMERA", cam_data)
root_collection.objects.link(cam)
cam.location = (width * 0.9, -depth * 0.95, depth * 0.9)
cam.data.type = 'ORTHO'
cam.data.ortho_scale = depth * 1.08
look_at(cam, (0, (row_cursor - 1) * cell_y * 0.5, 0.0))
scene.camera = cam

for name, loc, energy, size in [
    ("Key", (0, (row_cursor - 1) * cell_y * 0.5, depth), 1800, 10),
    ("Fill", (-width, 0, depth * 0.6), 1200, 8),
    ("Rim", (width, depth, depth * 0.7), 1600, 8),
]:
    data = bpy.data.lights.new(name, type='AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    light = bpy.data.objects.new("CATALOG_LIGHT_" + name, data)
    root_collection.objects.link(light)
    light.location = loc
    look_at(light, (0, (row_cursor - 1) * cell_y * 0.5, 0))

sun_data = bpy.data.lights.new("CatalogSun", type='SUN')
sun_data.energy = 3.0
sun_data.angle = math.radians(25)
sun = bpy.data.objects.new("CATALOG_LIGHT_Sun", sun_data)
root_collection.objects.link(sun)
sun.rotation_euler = (math.radians(20), math.radians(-25), math.radians(-20))

# Set a useful viewport state.
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type == 'VIEW_3D':
        area.spaces.active.region_3d.view_distance = max(width, depth) * 0.7

# Save only to the Combined directory.
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
# Render a quick verification still.
bpy.ops.render.render(write_still=True)
print("CATALOG_DONE", imported_count, "FBX", "OUT", OUT_BLEND)
