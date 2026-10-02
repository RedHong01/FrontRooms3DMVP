"""Build the editable Office furniture source and export Unity-ready FBX files.

Run with Blender 4.x:
  Blender.app/Contents/MacOS/Blender -b --python Tools/Blender/generate_office_furniture_assets.py

The exported meshes are deliberately low/mid poly and keep separate material
slots. Unity replaces the embedded preview materials with the project's URP
materials at runtime, while the .blend remains the editable modelling source.
"""

import bpy
import math
import os
from mathutils import Vector


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
OUT_DIR = os.path.join(ROOT, "Assets", "Resources", "Models", "Office")
SOURCE_DIR = os.path.join(ROOT, "Tools", "Blender", "Source")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(SOURCE_DIR, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    # Keep the shared preview materials alive between per-asset exports. The
    # global M dictionary intentionally reuses them for every FBX.
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def material(name, color, metallic=0.0, roughness=0.55):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


M = {
    "wood": material("OfficeWood", (0.27, 0.24, 0.19), 0.0, 0.48),
    "edge": material("OfficeWoodEdge", (0.38, 0.33, 0.25), 0.0, 0.42),
    "metal": material("OfficeMetal", (0.50, 0.52, 0.49), 0.48, 0.40),
    "dark": material("OfficeDarkHardware", (0.045, 0.055, 0.052), 0.22, 0.42),
    "plastic": material("OfficePlastic", (0.43, 0.44, 0.40), 0.0, 0.38),
    "screen": material("OfficeScreenGlass", (0.025, 0.065, 0.062), 0.05, 0.20),
    "paper": material("OfficePaper", (0.82, 0.78, 0.66), 0.0, 0.68),
    "vinyl": material("OfficeVinyl", (0.41, 0.48, 0.46), 0.0, 0.60),
    "fabric": material("OfficeFabric", (0.25, 0.29, 0.29), 0.0, 0.88),
    "wall": material("OfficeWall", (0.36, 0.36, 0.31), 0.0, 0.82),
    "product": material("OfficeProduct", (0.56, 0.42, 0.22), 0.0, 0.52),
    "blue": material("OfficeProductBlue", (0.12, 0.25, 0.29), 0.0, 0.48),
    "red": material("OfficeProductRed", (0.38, 0.16, 0.12), 0.0, 0.50),
}


def assign(obj, mat):
    obj.data.materials.append(mat)


def parent(obj, root):
    obj.parent = root
    obj.matrix_parent_inverse = root.matrix_world.inverted()


def box(root, name, loc, dims, mat, bevel=0.0, rotation=None):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    if rotation:
        obj.rotation_euler = rotation
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    assign(obj, mat)
    if bevel > 0:
        mod = obj.modifiers.new("small production bevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
        mod.limit_method = "ANGLE"
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=mod.name)
    parent(obj, root)
    return obj


def cylinder(root, name, loc, radius, depth, mat, vertices=16, rotation=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc)
    obj = bpy.context.object
    obj.name = name
    if rotation:
        obj.rotation_euler = rotation
    assign(obj, mat)
    bevel = obj.modifiers.new("edge bevel", "BEVEL")
    bevel.width = min(radius * .18, .025)
    bevel.segments = 2
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=bevel.name)
    parent(obj, root)
    return obj


def root_node(name):
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    # Blender is Z-up while Unity is Y-up. The FBX exporter maps the local
    # coordinates through (x, -z, -y); a 180-degree X rotation on the asset
    # root restores the intended Unity height/depth axes without baking the
    # source mesh into a destructive transform.
    root.rotation_euler = (math.pi, 0.0, 0.0)
    return root


def desk():
    root = root_node("OfficeDesk")
    box(root, "desk top", (0, .78, 0), (1.92, .11, .78), M["wood"], .055)
    box(root, "desk front edge", (0, .69, -.33), (1.82, .10, .08), M["edge"], .025)
    box(root, "desk left pedestal", (-.68, .39, .03), (.34, .65, .58), M["wood"], .035)
    box(root, "desk right pedestal", (.68, .39, .03), (.34, .65, .58), M["wood"], .035)
    for side in (-1, 1):
        for row in range(2):
            y = .43 + row * .19
            box(root, "drawer face", (side * .68, y, -.275), (.26, .14, .025), M["edge"], .012)
            box(root, "drawer pull", (side * .68, y, -.302), (.08, .012, .012), M["dark"], .004)
    box(root, "desk modesty panel", (0, .43, .22), (1.18, .48, .055), M["wood"], .018)
    for side in (-1, 1):
        box(root, "steel leg", (side * .89, .36, .24), (.055, .66, .055), M["metal"], .012)
    return root


def computer():
    root = root_node("OfficeCRTComputer")
    # Coordinates match the former workstation-local CRT anchor: the root
    # sits on the desk/floor origin while the monitor and keyboard occupy the
    # same relative offsets as the authored scene kit.
    box(root, "CRT casing", (0, 1.08, .19), (.66, .43, .39), M["plastic"], .06)
    box(root, "CRT screen glass", (0, 1.10, -.015), (.47, .29, .018), M["screen"], .035)
    box(root, "CRT bezel lip", (0, 1.10, -.032), (.54, .34, .018), M["dark"], .012)
    box(root, "CRT neck", (0, .79, .20), (.12, .18, .11), M["plastic"], .02)
    box(root, "CRT stand foot", (0, .69, .18), (.30, .045, .21), M["metal"], .018)
    for i in (-1, 0, 1):
        box(root, "CRT side vent", (i * .15, 1.04, .397), (.06, .018, .006), M["dark"], .002)
    box(root, "CRT power button", (.22, 1.00, -.045), (.035, .035, .012), M["dark"], .006)
    box(root, "keyboard shell", (0, .74, -.18), (.52, .035, .20), M["plastic"], .018)
    for row in range(3):
        box(root, "keyboard key row", (0, .765, -.235 + row * .045), (.42, .012, .022), M["paper"], .004)
    box(root, "mouse", (.35, .755, -.165), (.095, .025, .13), M["plastic"], .03)
    box(root, "mouse cable", (.22, .76, -.165), (.19, .008, .012), M["dark"], .003)
    box(root, "computer tower", (.56, .25, .20), (.28, .50, .44), M["plastic"], .025)
    for row in range(2):
        box(root, "tower drive bay", (.56, .38 + row * .09, -.028), (.18, .035, .012), M["dark"], .003)
    box(root, "tower power light", (.56, .16, -.03), (.025, .018, .012), M["blue"], .004)
    box(root, "tower lower vent", (.56, .08, -.03), (.18, .06, .012), M["dark"], .004)
    return root


def chair():
    root = root_node("OfficeTaskChair")
    box(root, "chair seat", (0, .52, 0), (.60, .14, .56), M["vinyl"], .07)
    box(root, "chair back", (0, .94, .16), (.60, .78, .14), M["vinyl"], .075, (math.radians(-5), 0, 0))
    for side in (-1, 1):
        box(root, "chair arm", (side * .34, .76, .02), (.055, .08, .34), M["metal"], .012)
    cylinder(root, "chair gas lift", (0, .28, 0), .055, .26, M["metal"])
    cylinder(root, "chair base", (0, .06, 0), .26, .035, M["metal"])
    for i in range(5):
        angle = i * math.pi * 2.0 / 5.0
        x, z = math.cos(angle) * .28, math.sin(angle) * .28
        box(root, "chair star arm", (x * .55, .055, z * .55), (.26, .035, .035), M["metal"], .009, (0, -angle, 0))
        cylinder(root, "chair caster", (x, .01, z), .045, .045, M["dark"])
    return root


def panel():
    root = root_node("OfficeCubiclePanel")
    box(root, "cubicle fabric panel", (0, 1.20, .82), (1.45, 1.0, .09), M["fabric"], .025)
    box(root, "cubicle metal cap", (0, 1.69, .82), (1.38, .025, .11), M["metal"], .006)
    return root


def filing():
    root = root_node("OfficeFilingCabinet")
    box(root, "filing body", (0, .74, 0), (.76, 1.48, .58), M["metal"], .045)
    for i in range(3):
        y = .34 + i * .39
        box(root, "filing drawer", (0, y, -.302), (.64, .32, .025), M["metal"], .012)
        box(root, "filing label pull", (0, y + .03, -.328), (.16, .018, .014), M["paper"], .004)
    box(root, "cabinet foot left", (-.27, .045, 0), (.08, .09, .40), M["dark"], .012)
    box(root, "cabinet foot right", (.27, .045, 0), (.08, .09, .40), M["dark"], .012)
    return root


def copier():
    root = root_node("OfficeCopier")
    box(root, "copier lower body", (0, .58, 0), (.92, 1.16, .76), M["metal"], .05)
    box(root, "copier upper body", (0, 1.30, .02), (.82, .24, .72), M["plastic"], .04)
    box(root, "copier document lid", (0, 1.47, .02), (.66, .035, .55), M["paper"], .018)
    box(root, "copier output tray", (0, .94, -.43), (.48, .045, .20), M["dark"], .006)
    box(root, "copier control panel", (.27, 1.39, -.37), (.18, .04, .025), M["dark"], .006)
    for drawer in range(2):
        box(root, "copier paper drawer", (0, .28 + drawer * .32, -.39), (.62, .20, .025), M["metal"], .012)
    return root


def water_cooler():
    root = root_node("OfficeWaterCooler")
    box(root, "cooler base", (0, .62, 0), (.56, 1.24, .56), M["metal"], .07)
    cylinder(root, "cooler bottle neck", (0, 1.18, 0), .11, .16, M["screen"], 20)
    box(root, "cooler bottle", (0, 1.52, 0), (.36, .52, .36), M["screen"], .11)
    box(root, "cooler tap panel", (0, .92, -.29), (.27, .19, .025), M["dark"], .006)
    box(root, "cooler drip tray", (0, .77, -.32), (.22, .035, .12), M["dark"], .01)
    return root


def vending():
    root = root_node("OfficeVendingMachine")
    box(root, "vending body", (0, 1.10, 0), (.74, 2.20, .58), M["metal"], .06)
    box(root, "vending display", (-.02, 1.55, -.302), (.52, .42, .018), M["dark"], .008)
    box(root, "vending lower label", (.04, .92, -.31), (.30, .04, .015), M["paper"], .004)
    for row in range(4):
        for col in range(4):
            mat = (M["product"], M["blue"], M["red"], M["paper"])[(row + col) % 4]
            box(root, "vending product", (-.22 + col * .145, 1.28 + row * .16, -.325), (.09, .10, .018), mat, .008)
    return root


def shelf():
    root = root_node("OfficeShelf")
    for side in (-1, 1):
        box(root, "shelf upright", (side * .52, .72, 0), (.065, 1.45, .34), M["metal"], .012)
    for i in range(4):
        box(root, "shelf plank", (0, .12 + i * .40, 0), (1.12, .075, .42), M["wood"], .018)
    return root


def pillar():
    root = root_node("OfficePillar")
    box(root, "structural pier", (0, 1.35, 0), (.78, 2.70, .78), M["wall"], .055)
    box(root, "pier base", (0, .04, 0), (.88, .08, .88), M["metal"], .012)
    return root


BUILDERS = {
    "OfficeDesk": desk,
    "OfficeCRTComputer": computer,
    "OfficeTaskChair": chair,
    "OfficeCubiclePanel": panel,
    "OfficeFilingCabinet": filing,
    "OfficeCopier": copier,
    "OfficeWaterCooler": water_cooler,
    "OfficeVendingMachine": vending,
    "OfficeShelf": shelf,
    "OfficePillar": pillar,
}


def select_tree(root):
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for obj in bpy.context.scene.objects:
        if obj != root and obj.parent == root:
            obj.select_set(True)
    bpy.context.view_layer.objects.active = root


def export_asset(name, builder):
    clear_scene()
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0
    root = builder()
    select_tree(root)
    path = os.path.join(OUT_DIR, name + ".fbx")
    bpy.ops.export_scene.fbx(
        filepath=path,
        use_selection=True,
        object_types={"EMPTY", "MESH"},
        apply_unit_scale=True,
        global_scale=1.0,
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=False,
        add_leaf_bones=False,
        use_armature_deform_only=True,
        use_mesh_modifiers=True,
        embed_textures=False,
        path_mode="AUTO",
    )
    return root


for asset_name, builder in BUILDERS.items():
    export_asset(asset_name, builder)

# Rebuild all assets in one editable source file for future art direction.
clear_scene()
bpy.context.scene.unit_settings.system = "METRIC"
bpy.context.scene.unit_settings.scale_length = 1.0
for asset_name, builder in BUILDERS.items():
    root = builder()
    root.location.x = list(BUILDERS.keys()).index(asset_name) * 3.0
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(SOURCE_DIR, "OfficeFurnitureKit.blend"))

print("Generated", len(BUILDERS), "Office FBX assets in", OUT_DIR)
