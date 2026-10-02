"""FrontRooms prop kit: shared modelling, UV, export and preview helpers.

Every asset is one Python module in ``assets/`` with a ``build(kit)`` function.
``build_asset.py`` runs it inside Blender 4.3 (headless) and writes:

* ``Assets/Resources/Props/Models/<Name>.fbx``  one mesh, one submesh per slot
* ``Assets/Resources/Props/Models/<Name>.json``  sidecar: bounds, footprint,
  support surfaces (where other props may rest), collider boxes, slots
* ``<preview dir>/<Name>_a.png`` / ``_b.png``      Cycles turntable stills

Conventions (Blender side)
* Metres, Z up. The asset stands on z = 0 and is centred on x = y = 0.
* The FRONT of the asset (the side a person uses: seat, drawer faces, CRT
  screen, vending glass) faces -Y. Unity receives it facing +Z (see export()).
* Material slot names are the contract with Unity: a submesh whose material is
  called ``Prop_WoodCherry`` is rendered with ``Resources/Props/Materials/
  Prop_WoodCherry.mat`` (created by FrontRoomsRenderSetup). Use SLOTS below.
* UVs: ``uv="metres"`` (default) box-projects in world metres, so tiling
  materials (wood, fabric, steel) keep one texel density across the kit and
  match the FrontRooms/Surface shader's mesh-UV mode. ``uv="decal"`` maps the
  part's front face 0..1 for unique art (screens, labels, vending front).

Module-level options read by build_asset.py
* ``LOD1 = 0.42``  export <NAME>_LOD1, collapse-decimated to that triangle
  ratio (Unity builds a LODGroup; switch at 10 % screen height). Omit for props
  under ~600 tris.
* ``VARIANTS = {"Kit_Sofa3_Floral": {"Prop_FabricBeige": "Prop_FabricFloral"}}``
  export extra assets with slots swapped (colour variety without new meshes).
* ``SMOOTH_ANGLE = 35``  auto-smooth angle (upholstery: 60-80).
Budgets and rules: research/10_synthesis.md §5 (≤ 4 slots per asset, desk-top
items call kit.no_collider(), painted steel is non-metallic, upholstery uses
kit.soft_box()).
"""

import bpy
import bmesh
import json
import math
import os
from mathutils import Matrix, Vector

# Slot -> preview colour (linear-ish sRGB), roughness, metallic. The real look
# comes from the Unity material; these only make previews readable.
SLOTS = {
    "Prop_WoodCherry": ((0.36, 0.13, 0.07), 0.45, 0.0),
    "Prop_WoodOak": ((0.55, 0.36, 0.18), 0.5, 0.0),
    "Prop_WoodTeak": ((0.62, 0.30, 0.10), 0.45, 0.0),
    "Prop_WoodDark": ((0.16, 0.08, 0.05), 0.4, 0.0),
    "Prop_WoodLaminate": ((0.52, 0.40, 0.26), 0.55, 0.0),
    "Prop_Plywood": ((0.66, 0.48, 0.32), 0.7, 0.0),
    "Prop_PinePallet": ((0.70, 0.56, 0.38), 0.8, 0.0),
    "Prop_LaminateBeige": ((0.72, 0.66, 0.54), 0.5, 0.0),
    "Prop_PlasticBeige": ((0.74, 0.70, 0.60), 0.45, 0.0),
    "Prop_PlasticBlack": ((0.03, 0.03, 0.03), 0.5, 0.0),
    "Prop_PlasticGrey": ((0.22, 0.22, 0.22), 0.5, 0.0),
    "Prop_PlasticWhite": ((0.82, 0.82, 0.78), 0.4, 0.0),
    "Prop_Rubber": ((0.02, 0.02, 0.02), 0.85, 0.0),
    # Painted / powder-coated steel is dielectric (metallic 0).
    "Prop_SteelPutty": ((0.55, 0.53, 0.48), 0.55, 0.0),
    "Prop_SteelBlack": ((0.04, 0.04, 0.04), 0.55, 0.0),
    "Prop_SteelBrown": ((0.16, 0.11, 0.08), 0.55, 0.0),
    "Prop_Chrome": ((0.8, 0.8, 0.8), 0.12, 1.0),
    "Prop_Aluminium": ((0.7, 0.7, 0.7), 0.35, 1.0),
    "Prop_Brass": ((0.7, 0.52, 0.25), 0.3, 1.0),
    "Prop_FabricCubicle": ((0.24, 0.28, 0.33), 0.95, 0.0),
    "Prop_FabricChair": ((0.05, 0.05, 0.055), 0.95, 0.0),
    "Prop_VelvetPink": ((0.70, 0.45, 0.44), 0.9, 0.0),
    "Prop_FabricTeal": ((0.25, 0.42, 0.44), 0.95, 0.0),
    "Prop_FabricFloral": ((0.70, 0.62, 0.50), 0.95, 0.0),
    "Prop_FabricBeige": ((0.62, 0.52, 0.38), 0.95, 0.0),
    "Prop_Vinyl": ((0.10, 0.09, 0.08), 0.6, 0.0),
    "Prop_Glass": ((0.8, 0.85, 0.85), 0.05, 0.0),
    "Prop_GlassCRT": ((0.03, 0.04, 0.04), 0.08, 0.0),
    "Prop_ScreenCRT": ((0.05, 0.07, 0.06), 0.1, 0.0),
    "Prop_VendingFront": ((0.5, 0.4, 0.3), 0.3, 0.0),
    "Prop_CopierPanel": ((0.3, 0.3, 0.3), 0.4, 0.0),
    "Prop_KeyboardKeys": ((0.72, 0.68, 0.58), 0.5, 0.0),
    "Prop_Paper": ((0.85, 0.84, 0.78), 0.8, 0.0),
    "Prop_Cardboard": ((0.55, 0.40, 0.25), 0.85, 0.0),
    "Prop_BottleBlue": ((0.35, 0.55, 0.75), 0.05, 0.0),
    "Prop_LampShade": ((0.88, 0.84, 0.72), 0.9, 0.0),
    "Prop_Label": ((0.8, 0.8, 0.75), 0.6, 0.0),
    "Prop_WoodWalnut": ((0.27, 0.17, 0.10), 0.5, 0.0),
    "Prop_WoodEbony": ((0.10, 0.07, 0.05), 0.35, 0.0),
    "Prop_Chipboard": ((0.61, 0.52, 0.40), 0.75, 0.0),
    "Prop_Studs": ((0.79, 0.68, 0.52), 0.8, 0.0),
    "Prop_TapeBlue": ((0.18, 0.52, 0.76), 0.7, 0.0),
    "Prop_FabricCharcoal": ((0.23, 0.23, 0.24), 0.9, 0.0),
    "Prop_FabricNavy": ((0.14, 0.19, 0.29), 0.9, 0.0),
    "Prop_Ceramic": ((0.35, 0.23, 0.14), 0.2, 0.0),
    # Round-1 requests (2026-10-02): finishes the kit was missing.
    "Prop_PVCEdge": ((0.10, 0.07, 0.05), 0.55, 0.0),      # T-mould / vinyl edge band
    "Prop_Backer": ((0.42, 0.30, 0.18), 0.8, 0.0),        # kraft backer under desk tops
    "Prop_SteelAlmond": ((0.66, 0.60, 0.48), 0.55, 0.0),  # almond painted steel (pedestals)
    "Prop_PlasticPutty": ((0.58, 0.55, 0.48), 0.5, 0.0),  # warm putty plastic trim
    "Prop_Hardboard": ((0.30, 0.20, 0.13), 0.65, 0.0),    # tempered hardboard backs
    "Prop_PlasticRed": ((0.55, 0.05, 0.04), 0.4, 0.0),
    "Prop_PlasticBlue": ((0.05, 0.15, 0.45), 0.4, 0.0),
    "Prop_CeramicGlaze": ((0.86, 0.85, 0.80), 0.15, 0.0),
    "Prop_FoamPU": ((0.03, 0.03, 0.03), 0.75, 0.0),       # soft matte black PU (arm pads)
    "Prop_LEDGreen": ((0.1, 0.9, 0.2), 0.3, 0.0),         # emissive indicator lenses
    "Prop_LEDAmber": ((1.0, 0.55, 0.05), 0.3, 0.0),
    "Prop_LEDRed": ((0.9, 0.05, 0.03), 0.3, 0.0),
    "Prop_LCD": ((0.45, 0.50, 0.38), 0.3, 0.0),           # unlit grey-green segment display
    "Prop_StencilBlack": ((0.02, 0.02, 0.02), 0.8, 0.0),  # alpha-clipped spray stencil (decal)
    "Prop_PhoneKeys": ((0.75, 0.73, 0.68), 0.5, 0.0),     # phone keypad legends (decal)
    "Prop_VendingHeader": ((0.8, 0.2, 0.1), 0.4, 0.0),    # lit header sign (decal, emissive)
    "Prop_LampShadeLit": ((0.95, 0.88, 0.70), 0.1, 0.0),  # lamp shade, emissive when on
    "Prop_BulbLit": ((1.0, 0.95, 0.85), 0.2, 0.0),        # frosted bulb / halogen tube, emissive
}

WOOD_PREFIXES = ("Prop_Wood", "Prop_Plywood", "Prop_PinePallet", "Prop_Studs", "Prop_Chipboard", "Prop_Hardboard")


def register_slot(slot, colour=(0.6, 0.6, 0.6), roughness=0.6, metallic=0.0):
    """Add a slot at run time (imported CC0 assets bring their own materials)."""
    SLOTS.setdefault(slot, (colour, roughness, metallic))


def _hex_slot_check(slot):
    if slot not in SLOTS:
        raise KeyError("Unknown material slot %r. Add it to kitlib.SLOTS first." % slot)


class Kit:
    """Builds one asset out of parts, then joins, UVs, exports and previews it."""

    def __init__(self, name):
        self.name = name
        self.parts = []
        self.meta = {"name": name, "supports": [], "colliders": [], "anchors": {}, "tags": []}
        self._reset_scene()

    # ------------------------------------------------------------------ scene
    def _reset_scene(self):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        scene.unit_settings.system = "METRIC"
        scene.unit_settings.scale_length = 1.0

    def _material(self, slot):
        _hex_slot_check(slot)
        mat = bpy.data.materials.get(slot)
        if mat is None:
            colour, rough, metal = SLOTS[slot]
            mat = bpy.data.materials.new(slot)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes.get("Principled BSDF")
            bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
            bsdf.inputs["Roughness"].default_value = rough
            bsdf.inputs["Metallic"].default_value = metal
            if slot in ("Prop_Glass", "Prop_BottleBlue"):
                bsdf.inputs["Transmission Weight"].default_value = 0.85
            mat.diffuse_color = (*colour, 1.0)
        return mat

    def _new_object(self, name, bm, slot, uv, decal_axes):
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.data.materials.append(self._material(slot))
        obj["fr_uv"] = uv
        obj["fr_decal_axes"] = decal_axes
        self.parts.append(obj)
        return obj

    @staticmethod
    def _place(obj, loc, rot):
        obj.rotation_mode = "XYZ"
        obj.rotation_euler = [math.radians(a) for a in rot]
        obj.location = loc

    @staticmethod
    def _bevel(obj, width, segments, angle=40.0):
        if width <= 0:
            return
        mod = obj.modifiers.new("bevel", "BEVEL")
        mod.width = width
        mod.segments = segments
        mod.limit_method = "ANGLE"
        mod.angle_limit = math.radians(angle)
        mod.miter_outer = "MITER_ARC"
        mod.use_clamp_overlap = True

    # -------------------------------------------------------------- primitives
    def box(self, size, loc, slot, bevel=0.004, segments=2, rot=(0, 0, 0), name="box", uv="metres", decal_axes="xz"):
        """Axis box of ``size`` (x, y, z) centred at ``loc``; rot in degrees."""
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector(size), verts=bm.verts)
        obj = self._new_object(name, bm, slot, uv, decal_axes)
        self._place(obj, loc, rot)
        self._bevel(obj, min(bevel, min(size) * 0.45), segments)
        return obj

    def cylinder(self, radius, depth, loc, slot, verts=24, rot=(0, 0, 0), bevel=0.003, segments=2, name="cylinder", uv="metres", radius_top=None):
        """Z-aligned cylinder (or cone/frustum with radius_top) centred at loc."""
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts,
                              radius1=radius, radius2=radius if radius_top is None else radius_top, depth=depth)
        obj = self._new_object(name, bm, slot, uv, "xz")
        self._place(obj, loc, rot)
        self._bevel(obj, min(bevel, radius * 0.4, depth * 0.4), segments, angle=50)
        return obj

    def loft_box(self, front_size, back_size, depth, loc, slot, back_offset=(0.0, 0.0), bevel=0.006, segments=2, rot=(0, 0, 0), name="loft"):
        """Tapered box along Y: a front rectangle (x, z) at y = -depth/2 and a
        back rectangle at y = +depth/2, the back shifted by back_offset (x, z).
        CRT tubes, TV backs, lamp housings, drawer fronts with draft."""
        bm = bmesh.new()
        fx, fz = front_size[0] / 2, front_size[1] / 2
        bx, bz = back_size[0] / 2, back_size[1] / 2
        ox, oz = back_offset
        y0, y1 = -depth / 2, depth / 2
        f = [bm.verts.new(p) for p in ((-fx, y0, -fz), (fx, y0, -fz), (fx, y0, fz), (-fx, y0, fz))]
        b = [bm.verts.new(p) for p in ((-bx + ox, y1, -bz + oz), (bx + ox, y1, -bz + oz), (bx + ox, y1, bz + oz), (-bx + ox, y1, bz + oz))]
        bm.faces.new(list(reversed(f)))
        bm.faces.new(b)
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((f[i], f[j], b[j], b[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        obj = self._new_object(name, bm, slot, "metres", "xz")
        self._place(obj, loc, rot)
        self._bevel(obj, min(bevel, min(front_size + back_size) * 0.3), segments, angle=25)
        return obj

    def soft_box(self, size, loc, slot, radius=0.05, segments=24, rings=14, sag=0.0, puff=0.0, rot=(0, 0, 0), name="cushion"):
        """Upholstery: a superellipsoid 'rounded box' of ``size`` whose corner
        softness follows ``radius`` (metres, like a bevel), with the top pressed
        down by ``sag`` at the centre (a used seat) and the faces bowed out by
        ``puff`` (a stuffed cushion). Even tessellation (~segments*rings*2
        tris, ~650 by default), so it deforms cleanly and reads soft at 3 m."""
        hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
        # Smaller exponent = boxier. Map the radius to the exponent.
        e = max(0.08, min(0.6, radius / max(min(size), 1e-3) * 1.5))
        def c(w, m):
            v = math.cos(w)
            return math.copysign(abs(v) ** m, v)
        def sn(w, m):
            v = math.sin(w)
            return math.copysign(abs(v) ** m, v)
        bm = bmesh.new()
        grid = []
        for i in range(rings + 1):
            u = -math.pi / 2 + math.pi * i / rings
            row = []
            for j in range(segments):
                v = -math.pi + 2 * math.pi * j / segments
                x = hx * c(u, e) * c(v, e)
                y = hy * c(u, e) * sn(v, e)
                z = hz * sn(u, e)
                ux, uy, uz = x / hx, y / hy, z / hz
                if puff:
                    x += puff * ux * max(0.0, 1 - uy * uy) * max(0.0, 1 - uz * uz)
                    y += puff * uy * max(0.0, 1 - ux * ux) * max(0.0, 1 - uz * uz)
                    z += puff * 0.5 * uz * max(0.0, 1 - ux * ux) * max(0.0, 1 - uy * uy)
                if sag and uz > 0:
                    z -= sag * uz * max(0.0, 1 - ux * ux) * max(0.0, 1 - uy * uy)
                row.append(bm.verts.new((x, y, z)))
            grid.append(row)
        for i in range(rings):
            for j in range(segments):
                k = (j + 1) % segments
                a, b2, c2, d = grid[i][j], grid[i][k], grid[i + 1][k], grid[i + 1][j]
                try:
                    bm.faces.new((a, b2, c2, d))
                except ValueError:
                    pass  # poles: remove_doubles below welds the degenerate rings
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        obj = self._new_object(name, bm, slot, "metres", "xz")
        self._place(obj, loc, rot)
        return obj

    def frame(self, outer, inner, depth, loc, slot, inner_offset=(0.0, 0.0), bevel=0.004, segments=2, rot=(0, 0, 0), name="frame"):
        """A rectangular frame facing -Y: outer (w, h) with an inner hole
        (w, h) shifted by inner_offset (x, z), extruded ``depth`` along Y.
        One closed mesh, so bevels run round the corners without seams."""
        bm = bmesh.new()
        ow, oh = outer[0] / 2, outer[1] / 2
        iw, ih = inner[0] / 2, inner[1] / 2
        ix, iz = inner_offset
        y0, y1 = -depth / 2, depth / 2
        def ring(w, h, cx, cz, y):
            return [bm.verts.new(p) for p in ((cx - w, y, cz - h), (cx + w, y, cz - h), (cx + w, y, cz + h), (cx - w, y, cz + h))]
        of, ob = ring(ow, oh, 0, 0, y0), ring(ow, oh, 0, 0, y1)
        inf, inb = ring(iw, ih, ix, iz, y0), ring(iw, ih, ix, iz, y1)
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((of[i], of[j], inf[j], inf[i]))      # front face band
            bm.faces.new((ob[j], ob[i], inb[i], inb[j]))      # back face band
            bm.faces.new((of[j], of[i], ob[i], ob[j]))        # outer side
            bm.faces.new((inf[i], inf[j], inb[j], inb[i]))    # inner side
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        obj = self._new_object(name, bm, slot, "metres", "xz")
        self._place(obj, loc, rot)
        self._bevel(obj, min(bevel, depth * 0.4), segments)
        return obj

    def bulged_panel(self, width, height, bulge, loc, slot, segments=16, rot=(0, 0, 0), name="glass", uv="decal"):
        """A rectangle facing -Y, pushed toward -Y by ``bulge`` at its centre
        (spherical cap): CRT faces, convex TV glass. Decal UVs span it 0..1."""
        bm = bmesh.new()
        hw, hh = width / 2, height / 2
        grid = []
        for j in range(segments + 1):
            row = []
            for i in range(segments + 1):
                x = -hw + width * i / segments
                z = -hh + height * j / segments
                d = 1 - min(1.0, (x / hw) ** 2 * 0.5 + (z / hh) ** 2 * 0.5)
                row.append(bm.verts.new((x, -bulge * d, z)))
            grid.append(row)
        for j in range(segments):
            for i in range(segments):
                bm.faces.new((grid[j][i], grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for face in bm.faces:
            face.normal_update()
            if face.normal.y > 0:
                face.normal_flip()
        obj = self._new_object(name, bm, slot, uv, "xz")
        self._place(obj, loc, rot)
        return obj

    def lathe(self, profile, loc, slot, verts=32, rot=(0, 0, 0), name="lathe", uv="metres", close_top=True, close_bottom=True):
        """Revolve a (radius, z) profile around Z. Profile runs bottom to top."""
        bm = bmesh.new()
        rings = []
        for r, z in profile:
            ring = []
            for i in range(verts):
                a = 2 * math.pi * i / verts
                ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for i in range(verts):
                j = (i + 1) % verts
                bm.faces.new((a[i], a[j], b[j], b[i]))
        if close_bottom and profile[0][0] > 1e-5:
            bm.faces.new(list(reversed(rings[0])))
        if close_top and profile[-1][0] > 1e-5:
            bm.faces.new(rings[-1])
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        obj = self._new_object(name, bm, slot, uv, "xz")
        self._place(obj, loc, rot)
        return obj

    def extrude(self, outline, depth, loc, slot, plane="xz", rot=(0, 0, 0), bevel=0.003, segments=2, name="extrude", uv="metres"):
        """Extrude a closed 2D outline (list of (u, v)) by ``depth``.

        plane "xz": outline in X/Z (side profile), extruded along Y.
        plane "yz": outline in Y/Z, extruded along X.  plane "xy": along Z.
        The extrusion is centred on the plane.
        """
        bm = bmesh.new()
        def to3(u, v, w):
            if plane == "xz":
                return (u, w, v)
            if plane == "yz":
                return (w, u, v)
            return (u, v, w)
        front = [bm.verts.new(to3(u, v, -depth / 2)) for u, v in outline]
        back = [bm.verts.new(to3(u, v, depth / 2)) for u, v in outline]
        bm.faces.new(front)
        bm.faces.new(list(reversed(back)))
        n = len(outline)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((front[i], front[j], back[j], back[i]))
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        obj = self._new_object(name, bm, slot, uv, "xz")
        self._place(obj, loc, rot)
        self._bevel(obj, min(bevel, depth * 0.4), segments)
        return obj

    def tube(self, points, radius, slot, verts=12, name="tube", uv="metres", caps=True):
        """Round tube along a polyline of 3D points (mitred joints)."""
        pts = [Vector(p) for p in points]
        bm = bmesh.new()
        rings = []
        for k, p in enumerate(pts):
            if k == 0:
                tangent = (pts[1] - pts[0]).normalized()
            elif k == len(pts) - 1:
                tangent = (pts[-1] - pts[-2]).normalized()
            else:
                tangent = ((pts[k] - pts[k - 1]).normalized() + (pts[k + 1] - pts[k]).normalized()).normalized()
            ref = Vector((0, 0, 1)) if abs(tangent.z) < 0.9 else Vector((1, 0, 0))
            side = tangent.cross(ref).normalized()
            up = side.cross(tangent).normalized()
            ring = []
            for i in range(verts):
                a = 2 * math.pi * i / verts
                ring.append(bm.verts.new(p + (side * math.cos(a) + up * math.sin(a)) * radius))
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for i in range(verts):
                j = (i + 1) % verts
                bm.faces.new((a[i], a[j], b[j], b[i]))
        if caps:
            bm.faces.new(list(reversed(rings[0])))
            bm.faces.new(rings[-1])
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        return self._new_object(name, bm, slot, uv, "xz")

    def quad(self, size_u, size_v, loc, slot, facing="-y", name="quad", uv="decal", uv_rect=None):
        """Single-sided rectangle (labels, screens). facing: -y, +y, +z, -x, +x.
        uv_rect=(u0, v0, u1, v1) maps the decal into one cell of an atlas
        texture (see Kit.atlas_cell); Prop_Label is a 4 x 3 atlas."""
        bm = bmesh.new()
        hu, hv = size_u / 2, size_v / 2
        if facing in ("-y", "+y"):
            vs = [(-hu, 0, -hv), (hu, 0, -hv), (hu, 0, hv), (-hu, 0, hv)]
            axes = "xz"
        elif facing in ("-x", "+x"):
            vs = [(0, hu, -hv), (0, -hu, -hv), (0, -hu, hv), (0, hu, hv)]
            axes = "yz"
        else:
            vs = [(-hu, -hv, 0), (hu, -hv, 0), (hu, hv, 0), (-hu, hv, 0)]
            axes = "xy"
        verts = [bm.verts.new(v) for v in vs]
        face = bm.faces.new(verts)
        face.normal_update()
        want = {"-y": (0, -1, 0), "+y": (0, 1, 0), "-x": (-1, 0, 0), "+x": (1, 0, 0), "+z": (0, 0, 1)}[facing]
        if face.normal.dot(Vector(want)) < 0:
            face.normal_flip()
        obj = self._new_object(name, bm, slot, uv, axes)
        obj.location = loc
        if uv_rect is not None:
            obj["fr_uv_rect"] = list(uv_rect)
        return obj

    def adopt(self, obj, slot_names, uv="keep"):
        """Take an imported mesh object into the asset. Its material slots are
        renamed in order to ``slot_names`` (registered with register_slot)."""
        for i, name in enumerate(slot_names):
            if i < len(obj.data.materials):
                mat = self._material(name) if name in SLOTS else None
                if mat is not None:
                    obj.data.materials[i] = mat
        obj["fr_uv"] = uv
        obj["fr_decal_axes"] = "xz"
        if obj.name not in bpy.context.scene.collection.objects and not obj.users_collection:
            bpy.context.scene.collection.objects.link(obj)
        self.parts.append(obj)
        return obj

    def duplicate(self, obj, loc=None, rot=None, name=None):
        """Linked-free copy of a part (keeps slot and UV mode)."""
        new = obj.copy()
        new.data = obj.data.copy()
        if name:
            new.name = name
        bpy.context.scene.collection.objects.link(new)
        if loc is not None:
            new.location = loc
        if rot is not None:
            new.rotation_euler = [math.radians(a) for a in rot]
        self.parts.append(new)
        return new

    # ----------------------------------------------------------------- metadata
    def support(self, name, centre, size):
        """A flat top other props may rest on: centre (x, y, z top), size (x, y)."""
        self.meta["supports"].append({"name": name, "centre": list(centre), "size": list(size)})

    def collider(self, centre, size):
        """Box collider in asset space (x, y, z centre; x, y, z size)."""
        self.meta["colliders"].append({"centre": list(centre), "size": list(size)})

    def no_collider(self):
        """Desk-top clutter (keyboard, mouse, phone, paper, binders): no box."""
        self.meta["noCollider"] = True

    def anchor(self, name, pos):
        self.meta["anchors"][name] = list(pos)

    def tag(self, *tags):
        self.meta["tags"].extend(tags)

    PILE_CLASSES = ("Seat", "Table", "Case", "Soft", "Tall", "Screen", "Crate", "Small")
    PILE_STATES = ("Upright", "Back", "Front", "Side", "Inverted", "EdgeLean")

    def pile(self, cls, mass=1, states=None, tolerance=None, palette="office90s", topper=False):
        """How FrontRoomsFurniturePile may use this asset.
        cls: Seat | Table | Case | Soft | Tall | Screen | Crate | Small
        mass: 0 light .. 3 heavy (heavy pieces form the base)
        states: allowed rest states (Upright, Back, Front, Side, Inverted, EdgeLean)
        tolerance: max fraction of own volume allowed inside other pieces
        palette: domestic70s | office90s | storage | hotel
        topper: good silhouette on top of a pile (sofa, CRT, lamp)"""
        if cls not in self.PILE_CLASSES:
            raise ValueError("pile class %r" % cls)
        defaults = {
            "Seat": (["Upright", "Inverted", "Side", "Back"], 0.45),
            "Table": (["Upright", "Inverted", "Side"], 0.35),
            "Case": (["Upright", "Back", "Side", "EdgeLean"], 0.20),
            "Soft": (["Upright", "Back", "Side"], 0.30),
            "Tall": (["Upright"], 0.30),
            "Screen": (["Upright", "Side", "Front"], 0.15),
            "Crate": (["Upright", "Side"], 0.20),
            "Small": (["Upright", "Side"], 0.50),
        }[cls]
        states = list(states or defaults[0])
        for s in states:
            if s not in self.PILE_STATES:
                raise ValueError("pile state %r" % s)
        self.meta["pile"] = {"cls": cls, "mass": int(mass), "states": states,
                             "tolerance": float(defaults[1] if tolerance is None else tolerance),
                             "palette": palette, "topper": bool(topper)}

    # ------------------------------------------------------------------ finish
    def _apply_modifiers(self, obj):
        bpy.context.view_layer.objects.active = obj
        for mod in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=mod.name)

    @staticmethod
    def _uv_metres(obj):
        """Box projection in world metres (after the part's transform).
        Wood slots (WOOD_PREFIXES) run the grain (texture V) along the part's
        grain axis: obj["fr_grain"] ("x"/"y"/"z") if set, else per face the
        longer in-plane extent, so rails, drawer fronts and tops read along
        the board. obj["fr_uv_offset"] = (du, dv) shifts a part's UVs so
        neighbouring boards don't share one continuous sheet of grain."""
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        layer = bm.loops.layers.uv.verify()
        mw = obj.matrix_world
        rot = mw.to_3x3()
        mats = mesh.materials
        slot = mats[0].name.split(".")[0] if len(mats) and mats[0] is not None else ""
        wood = slot.startswith(WOOD_PREFIXES)
        forced = obj.get("fr_grain")
        forced = "xyz".index(forced) if forced in ("x", "y", "z") else None
        pts = [mw @ v.co for v in bm.verts]
        ext = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)] if pts else [1, 1, 1]
        off = obj.get("fr_uv_offset")
        du, dv = (float(off[0]), float(off[1])) if off is not None else (0.0, 0.0)
        for face in bm.faces:
            n = (rot @ face.normal).normalized()
            ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
            if az >= ax and az >= ay:
                axis, sgn, plane = 2, (1 if n.z >= 0 else -1), (0, 1)
            elif ax >= ay:
                axis, sgn, plane = 0, (1 if n.x >= 0 else -1), (1, 2)
            else:
                axis, sgn, plane = 1, (1 if n.y >= 0 else -1), (0, 2)
            g = None
            if wood:
                g = forced if (forced is not None and forced in plane) else (plane[0] if ext[plane[0]] > ext[plane[1]] else plane[1])
            for loop in face.loops:
                p = mw @ loop.vert.co
                if axis == 2:
                    u, v = p.x * sgn, p.y
                elif axis == 0:
                    u, v = -p.y * sgn, p.z
                else:
                    u, v = -p.x * sgn, p.z
                if g is not None:
                    if axis == 2 and g == 0:      # top/bottom, grain along X
                        u, v = -p.y * sgn, p.x
                    elif axis == 0 and g == 1:    # end face, grain along Y
                        u, v = -p.z * sgn, p.y
                    elif axis == 1 and g == 0:    # front/back, grain along X
                        u, v = p.z * sgn, p.x
                loop[layer].uv = (u + du, v + dv)
        bm.to_mesh(mesh)
        bm.free()

    @staticmethod
    def _uv_decal(obj, axes):
        """Planar 0..1 mapping across the part's own bounds on the given axes."""
        mesh = obj.data
        bm = bmesh.new()
        bm.from_mesh(mesh)
        layer = bm.loops.layers.uv.verify()
        idx = {"x": 0, "y": 1, "z": 2}
        a, b = idx[axes[0]], idx[axes[1]]
        cos = [v.co for v in bm.verts]
        lo_a, hi_a = min(c[a] for c in cos), max(c[a] for c in cos)
        lo_b, hi_b = min(c[b] for c in cos), max(c[b] for c in cos)
        for face in bm.faces:
            for loop in face.loops:
                c = loop.vert.co
                u = (c[a] - lo_a) / max(hi_a - lo_a, 1e-6)
                v = (c[b] - lo_b) / max(hi_b - lo_b, 1e-6)
                if axes == "yz":
                    u = 1 - u
                loop[layer].uv = (u, v)
        bm.to_mesh(mesh)
        bm.free()

    @staticmethod
    def _uv_remap(obj, rect):
        """Squeeze 0..1 decal UVs into rect = (u0, v0, u1, v1) of an atlas."""
        u0, v0, u1, v1 = [float(x) for x in rect]
        for loop_uv in obj.data.uv_layers.active.data:
            u, v = loop_uv.uv
            loop_uv.uv = (u0 + (u1 - u0) * u, v0 + (v1 - v0) * v)

    @staticmethod
    def atlas_cell(index, cols, rows):
        """uv_rect of cell ``index`` (row-major from the top-left) in a cols x rows atlas."""
        c, r = index % cols, index // cols
        return (c / cols, 1 - (r + 1) / rows, (c + 1) / cols, 1 - r / rows)

    def finish(self, smooth_angle=35.0):
        """Apply modifiers, generate UVs, join into one object, shade."""
        for obj in self.parts:
            self._apply_modifiers(obj)
            if obj.get("fr_uv") == "decal":
                self._uv_decal(obj, obj.get("fr_decal_axes", "xz"))
                rect = obj.get("fr_uv_rect")
                if rect is not None:
                    self._uv_remap(obj, rect)
        # Metre UVs need world-space positions, so bake transforms first.
        # uv="keep" (imported scans) leaves the authored UVs alone.
        for obj in self.parts:
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            if obj.get("fr_uv") not in ("decal", "keep"):
                self._uv_metres(obj)
        bpy.ops.object.select_all(action="DESELECT")
        for obj in self.parts:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = self.parts[0]
        if len(self.parts) > 1:
            bpy.ops.object.join()
        merged = bpy.context.view_layer.objects.active
        merged.name = self.name
        merged.data.name = self.name
        mesh = merged.data
        mesh.shade_smooth()
        mesh.set_sharp_from_angle(angle=math.radians(smooth_angle))
        self.object = merged
        # Bounds and footprint for the sidecar.
        xs = [v.co.x for v in mesh.vertices]
        ys = [v.co.y for v in mesh.vertices]
        zs = [v.co.z for v in mesh.vertices]
        self.meta["boundsMin"] = [min(xs), min(ys), min(zs)]
        self.meta["boundsMax"] = [max(xs), max(ys), max(zs)]
        self.meta["triangles"] = sum(len(p.vertices) - 2 for p in mesh.polygons)
        self.meta["slots"] = [m.name for m in mesh.materials]
        if not self.meta["colliders"] and not self.meta.get("noCollider"):
            lo, hi = Vector(self.meta["boundsMin"]), Vector(self.meta["boundsMax"])
            self.collider(list((lo + hi) / 2), list(hi - lo))
        return merged

    # --------------------------------------------------------------- variants
    def set_slot(self, old_slot, new_slot):
        """Swap one material slot on the finished mesh (material variants)."""
        objects = [self.object] + ([self.lod1] if getattr(self, "lod1", None) is not None else [])
        for obj in objects:
            mats = obj.data.materials
            for i, m in enumerate(mats):
                if m is not None and m.name == old_slot:
                    mats[i] = self._material(new_slot)

    # ------------------------------------------------------------------ export
    def make_lod1(self, ratio):
        """Add <NAME>_LOD1: a collapse-decimated copy at ``ratio`` of LOD0's
        triangles (UVs and slots kept). Unity builds a LODGroup from the
        _LOD0/_LOD1 names; FrontRoomsKitImporter sets the switch heights."""
        lod1 = getattr(self, "lod1", None)
        if lod1 is not None:
            bpy.data.objects.remove(lod1, do_unlink=True)
            self.lod1 = None
        if not ratio or ratio >= 0.95:
            self.object.name = self.name
            return
        lod1 = self.object.copy()
        lod1.data = self.object.data.copy()
        bpy.context.scene.collection.objects.link(lod1)
        mod = lod1.modifiers.new("lod1", "DECIMATE")
        mod.ratio = ratio
        mod.use_collapse_triangulate = True
        bpy.context.view_layer.objects.active = lod1
        bpy.ops.object.select_all(action="DESELECT")
        lod1.select_set(True)
        bpy.ops.object.modifier_apply(modifier=mod.name)
        self.object.name = self.name + "_LOD0"
        lod1.name = self.name + "_LOD1"
        self.lod1 = lod1
        self.meta["trianglesLod1"] = sum(len(p.vertices) - 2 for p in lod1.data.polygons)

    def export(self, fbx_path, json_path, name=None):
        """FBX for Unity: metres, -Z forward / Y up baked into the vertices, so
        the imported object has identity rotation and unit scale. With a LOD1
        the file holds <NAME>_LOD0 and <NAME>_LOD1 under the file root."""
        os.makedirs(os.path.dirname(fbx_path), exist_ok=True)
        bpy.ops.object.select_all(action="DESELECT")
        self.object.select_set(True)
        if getattr(self, "lod1", None) is not None:
            self.lod1.select_set(True)
        bpy.context.view_layer.objects.active = self.object
        bpy.ops.export_scene.fbx(
            filepath=fbx_path,
            use_selection=True,
            object_types={"MESH"},
            apply_unit_scale=True,
            apply_scale_options="FBX_SCALE_ALL",
            axis_forward="-Z",
            axis_up="Y",
            bake_space_transform=True,
            mesh_smooth_type="OFF",
            use_mesh_modifiers=True,
            use_tspace=True,
            add_leaf_bones=False,
            bake_anim=False,
            path_mode="STRIP",
        )
        # Sidecar in UNITY space. Verified with assets/axis_probe.py: Unity
        # imports Blender (x, y, z) as (-x, z, -y) with identity rotation and
        # unit scale (a handedness change, not a mirror). The front (-Y in
        # Blender) therefore faces +Z in Unity.
        def to_unity(p):
            return [-p[0], p[2], -p[1]]
        def size_unity(s):
            return [s[0], s[2], s[1]]
        out = dict(self.meta)
        out["name"] = name or self.name
        out["slots"] = [m.name for m in self.object.data.materials if m is not None]
        lo, hi = self.meta["boundsMin"], self.meta["boundsMax"]
        a, b = to_unity(lo), to_unity(hi)
        out["boundsMin"] = [min(a[i], b[i]) for i in range(3)]
        out["boundsMax"] = [max(a[i], b[i]) for i in range(3)]
        out["supports"] = [{"name": s["name"], "centre": to_unity(s["centre"]), "size": [s["size"][0], s["size"][1]]} for s in self.meta["supports"]]
        out["colliders"] = [{"centre": to_unity(c["centre"]), "size": size_unity(c["size"])} for c in self.meta["colliders"]]
        out["anchors"] = [{"name": k, "pos": to_unity(v)} for k, v in self.meta["anchors"].items()]
        out["frontAxis"] = "+Z"
        # Level Designer fields (LEVEL_MODULE_SPEC): the physical footprint is
        # the union of the collider boxes (cables and overhangs excluded),
        # falling back to the bounds; placement from tags; service depth in
        # front for wall units; the ceiling height the piece needs.
        boxes = self.meta["colliders"] or [{"centre": [(lo[i] + hi[i]) / 2 for i in range(3)], "size": [hi[i] - lo[i] for i in range(3)]}]
        fx0 = min(b["centre"][0] - b["size"][0] / 2 for b in boxes)
        fx1 = max(b["centre"][0] + b["size"][0] / 2 for b in boxes)
        fy0 = min(b["centre"][1] - b["size"][1] / 2 for b in boxes)
        fy1 = max(b["centre"][1] + b["size"][1] / 2 for b in boxes)
        out["footprintCentre"] = [-(fx0 + fx1) / 2, -(fy0 + fy1) / 2]   # Unity (x, z)
        out["footprintSize"] = [fx1 - fx0, fy1 - fy0]
        tags = set(self.meta["tags"])
        out["placement"] = ("DeskTop" if "desk_top" in tags else "Wall" if tags & {"wall_unit", "wall_decor"}
                            else "Ceiling" if "ceiling" in tags else "Floor")
        out["service"] = self.meta.get("service", 0.5 if "wall_unit" in tags else 0.0)
        out["minCeiling"] = round(hi[2] + 0.05, 3)
        with open(json_path, "w") as f:
            json.dump(out, f, indent=1)

    # ----------------------------------------------------------------- preview
    def preview(self, png_base, samples=48):
        """Two Cycles stills (3/4 front, 3/4 back) on a neutral floor."""
        scene = bpy.context.scene
        if getattr(self, "lod1", None) is not None:
            self.lod1.hide_render = True
        scene.render.engine = "CYCLES"
        scene.cycles.samples = samples
        scene.cycles.use_denoising = True
        scene.cycles.device = "CPU"
        scene.render.resolution_x = 900
        scene.render.resolution_y = 700
        scene.render.film_transparent = False
        scene.view_settings.view_transform = "AgX"
        world = bpy.data.worlds.new("preview world")
        world.use_nodes = True
        world.node_tree.nodes["Background"].inputs[0].default_value = (0.28, 0.27, 0.25, 1)
        world.node_tree.nodes["Background"].inputs[1].default_value = 0.6
        scene.world = world
        lo, hi = Vector(self.meta["boundsMin"]), Vector(self.meta["boundsMax"])
        centre = (lo + hi) / 2
        radius = max((hi - lo).length / 2, 0.15)
        bm = bmesh.new()
        bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=radius * 6)
        floor_mesh = bpy.data.meshes.new("floor")
        bm.to_mesh(floor_mesh)
        bm.free()
        floor = bpy.data.objects.new("floor", floor_mesh)
        scene.collection.objects.link(floor)
        fm = bpy.data.materials.new("floor")
        fm.use_nodes = True
        fm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.42, 0.40, 0.36, 1)
        floor_mesh.materials.append(fm)
        key = bpy.data.lights.new("key", "AREA")
        key.energy = 220 * radius * radius + 60
        key.size = radius * 2
        key_obj = bpy.data.objects.new("key", key)
        key_obj.location = centre + Vector((-radius * 1.5, -radius * 2.2, radius * 3.0 + 1.2))
        key_obj.rotation_euler = (math.radians(35), 0, math.radians(-30))
        scene.collection.objects.link(key_obj)
        cam_data = bpy.data.cameras.new("cam")
        cam_data.lens = 40
        cam = bpy.data.objects.new("cam", cam_data)
        scene.collection.objects.link(cam)
        scene.camera = cam
        for suffix, yaw in (("a", -35.0), ("b", 145.0)):
            d = radius * 3.1
            a = math.radians(yaw - 90)
            cam.location = centre + Vector((math.cos(a) * d, math.sin(a) * d, radius * 1.1 + 0.2))
            direction = centre - cam.location
            cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
            scene.render.filepath = png_base + "_" + suffix + ".png"
            bpy.ops.render.render(write_still=True)
