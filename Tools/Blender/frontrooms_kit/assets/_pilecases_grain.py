"""Grain, LOD1 and preview fixes for the pilecases group (helper, NOT an
asset module). Used by dresser_70s, rolling_cabinet, side_table_turned,
pallet and crate only. kitlib.py is not edited: install(kit) patches THIS Kit
instance, and every patch checks kitlib first so it switches itself off once
kitlib gains the same fix.

install(kit, smooth_angle, planks=None) does four things:

1. Grain on U (fix pass 2026-10-02). The CC0 albedos of Prop_WoodTeak /
   Cherry / Oak / Dark / Ebony / Laminate / Plywood / PinePallet run their
   grain along texture U, but kitlib._uv_metres puts each board's length on V
   and FrontRooms/Surface samples uv = metres / _TileSize with no rotation, so
   in Unity every drawer front, rail, cleat and board would show cross grain.
   After kitlib's projection these slots get (u, v) -> (v, u) (offsets
   included). Unity rebuilds Mikk tangents from the new UVs, so the normal
   maps need no swizzle. Prop_WoodWalnut and Prop_Studs (grain on V) are left
   alone. Whether kitlib still needs it is PROBED (a 1 m test board), so a
   kitlib that learns the swap turns this off by itself.
2. LOD1 shading. kitlib.make_lod1's collapse decimate drops most of the
   sharp-edge flags (Dresser 219 of 1,036 kept), and the .fbx.meta imports
   normals as authored, so LOD1 pillow-shades. The LOD1 mesh gets
   set_sharp_from_angle(smooth_angle) after the decimate (idempotent if
   kitlib does it too).
3. Plank seams (planks={"Prop_PinePallet": PINE_PLANKS}). Prop_PinePallet is
   ambientCG Planks021, a sheet of 11 planks per 1.4 m tile (dark seams every
   0.127 m across the grain) with painted nail dots every 0.7 m along it.
   Each part's UVs are shifted so its main face (obj["fr_face"], default up)
   lies inside one plank, clear of the seams, and the nail dots fall off the
   part where it is short enough, else onto obj["fr_nail_lines"] (world
   coordinates along the grain where real nails are). A part whose main
   face is wider than a plank (the 0.135-0.14 m pallet lead and bottom
   boards) has its UVs squeezed across the grain (by <= 20 %) to fit one.
   Remove the planks= argument when Prop_PinePallet becomes a single-board
   scan.
4. Preview stencils. kitlib.preview renders slot colours without alpha, so the
   Prop_StencilBlack quads came out as solid black panels in the §5.4 gate
   images. The preview material loads Prop_StencilBlack_A.png and alpha-clips
   it (export is untouched: preview runs after it).

scatter_offsets() gives every board its own patch of veneer (unchanged), and
_uv_metres_grain is the fr_grain projection for kitlib copies without it.
"""

import inspect
import math
import os
import random
import zlib

import bmesh
import bpy
from mathutils import Vector

import kitlib

WOOD_SLOTS = ("Prop_WoodCherry", "Prop_WoodOak", "Prop_WoodTeak", "Prop_WoodDark",
              "Prop_WoodLaminate", "Prop_Plywood", "Prop_PinePallet")

# Albedos whose grain runs along texture U (checked on the CC0 maps 2026-10-02).
U_GRAIN_SLOTS = ("Prop_WoodTeak", "Prop_WoodCherry", "Prop_WoodOak", "Prop_WoodDark", "Prop_WoodEbony",
                 "Prop_WoodLaminate", "Prop_Plywood", "Prop_PinePallet")

# Planks021 (Prop_PinePallet_A.png, 1024 px, TileSize 1.4): seams at V = k/11
# (rows 0, 93, 186 ... measured), 4-6 px wide; nail dots at U 0.156 and 0.656
# in every plank (0.218 m + k * 0.7 m along the grain), ~8 px across.
PINE_PLANKS = {"pitch": 1.4 / 11, "planks": 11, "seam_hw": 0.0045,
               "dot_phase": 0.218, "dot_period": 0.7, "dot_r": 0.006, "periods": 2}

STENCIL_TEX = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(kitlib.__file__)), "..", "..", "..",
                                            "Assets", "Resources", "Surfaces", "Textures", "Prop_StencilBlack_A.png"))


def _kitlib_has_grain():
    try:
        return "fr_grain" in inspect.getsource(kitlib.Kit._uv_metres)
    except (OSError, TypeError):
        return False


def _slot_of(obj):
    mats = obj.data.materials
    return mats[0].name if len(mats) and mats[0] is not None else ""


_GRAIN_ON_V = None


def _kitlib_grain_on_v():
    """True while kitlib's metre UVs put a board's length on V. Probed on a
    1.0 x 0.1 x 0.1 m teak test board, then cached for the session."""
    global _GRAIN_ON_V
    if _GRAIN_ON_V is None:
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        bmesh.ops.scale(bm, vec=Vector((1.0, 0.1, 0.1)), verts=bm.verts)
        me = bpy.data.meshes.new("fr_grain_probe")
        bm.to_mesh(me)
        bm.free()
        mat = bpy.data.materials.new("Prop_WoodTeak.fr_probe")   # kitlib reads the name before the dot
        me.materials.append(mat)
        ob = bpy.data.objects.new("fr_grain_probe", me)
        try:
            kitlib.Kit._uv_metres(ob)
            uvs = me.uv_layers.active.data
            top = [p for p in me.polygons if p.normal.z > 0.9][0]
            us = [uvs[i].uv[0] for i in top.loop_indices]
            vs = [uvs[i].uv[1] for i in top.loop_indices]
            _GRAIN_ON_V = (max(vs) - min(vs)) > (max(us) - min(us))
        finally:
            bpy.data.objects.remove(ob, do_unlink=True)
            bpy.data.meshes.remove(me)
            bpy.data.materials.remove(mat)
    return _GRAIN_ON_V


def _uv_metres_grain(obj):
    """fr_grain-aware metre projection for kitlib copies that lack it."""
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    layer = bm.loops.layers.uv.verify()
    mw = obj.matrix_world
    rot = mw.to_3x3()
    wood = _slot_of(obj).split(".")[0] in WOOD_SLOTS
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
            axis, s, plane = 2, (1 if n.z >= 0 else -1), (0, 1)
        elif ax >= ay:
            axis, s, plane = 0, (1 if n.x >= 0 else -1), (1, 2)
        else:
            axis, s, plane = 1, (1 if n.y >= 0 else -1), (0, 2)
        g = None
        if wood:
            if forced is not None and forced in plane:
                g = forced
            else:
                g = plane[0] if ext[plane[0]] > ext[plane[1]] else plane[1]
        for loop in face.loops:
            p = mw @ loop.vert.co
            if axis == 2:
                u, v = p.x * s, p.y
            elif axis == 0:
                u, v = -p.y * s, p.z
            else:
                u, v = -p.x * s, p.z
            if g is not None:
                if axis == 2 and g == 0:
                    u, v = -p.y * s, p.x
                elif axis == 0 and g == 1:
                    u, v = -p.z * s, p.y
                elif axis == 1 and g == 0:
                    u, v = p.z * s, p.x
            loop[layer].uv = (u + du, v + dv)
    bm.to_mesh(mesh)
    bm.free()


def _transpose_uvs(obj):
    for d in obj.data.uv_layers.active.data:
        u, v = d.uv
        d.uv = (v, u)


def _snap_planks(obj, cfg):
    """Shift obj's UVs (U along the grain, V across, metres) so its main face
    sits inside one plank of a plank-sheet albedo and avoids its nail dots."""
    me = obj.data
    uvl = me.uv_layers.active.data
    prim = Vector(obj.get("fr_face", (0.0, 0.0, 1.0))).normalized()
    pitch, hw = cfg["pitch"], cfg["seam_hw"]
    keep = hw + 0.004                    # main faces keep this far from a seam's centre
    # A main face wider than a plank: squeeze V (across the grain) about its
    # centre so it fits one plank; the figure narrows a little, no seam.
    mains = [p for p in me.polygons if p.normal.dot(prim) > 0.9]
    if mains:
        big = max(mains, key=lambda p: p.area)
        vs = [uvl[i].uv[1] for i in big.loop_indices]
        width, centre = max(vs) - min(vs), (max(vs) + min(vs)) / 2
        room = pitch - 2 * keep - 0.002
        if width > room:
            k = max(room / width, 0.8)
            for d in uvl:
                d.uv = (d.uv[0], centre + (d.uv[1] - centre) * k)
    faces = []
    for p in me.polygons:
        us = [uvl[i].uv[0] for i in p.loop_indices]
        vs = [uvl[i].uv[1] for i in p.loop_indices]
        d = p.normal.dot(prim)
        w = p.area * (1.0 if d > 0.7 else 0.3 if d > -0.3 else 0.05)
        faces.append((min(us), max(us), min(vs), max(vs), w, d > 0.7, p))
    rng = random.Random(zlib.crc32(obj.name.encode()))

    # Across the grain: seams every `pitch`; a seam band (half width hw, or
    # `keep` for a main face) that touches a face costs 0.1, one well inside
    # it costs 1 (weighted by area).
    step = 0.0005
    n = int(round(pitch / step))
    costs = []
    for i in range(n):
        sh = i * step
        c = 0.0
        for a0, a1, c0, c1, w, is_prim, _ in faces:
            lo, hi = c0 + sh, c1 + sh
            h = keep if is_prim else hw
            for k in range(math.floor((lo - h) / pitch), math.floor((hi + h) / pitch) + 1):
                s = k * pitch
                if s + h <= lo or s - h >= hi:
                    continue
                dd = min(s - lo, hi - s)
                c += w * (0.1 + 0.9 * min(1.0, max(0.0, (dd + h) / (2 * h + 0.010))))
        costs.append(c)
    best = min(costs)
    ok = [c <= best + 1e-9 for c in costs]
    # The middle of the longest run of best shifts (circular) = most margin.
    run, start, best_run = 0, 0, (0, 0)
    for i in range(2 * n):
        if ok[i % n]:
            if run == 0:
                start = i
            run += 1
            if run > best_run[0]:
                best_run = (min(run, n), start)
        else:
            run = 0
    shift_v = ((best_run[1] + (best_run[0] - 1) / 2.0) * step) % pitch + rng.randrange(cfg["planks"]) * pitch

    # Along the grain: nail dots every `period`, as few as possible inside the
    # faces; ties go to dots over the part's real nail lines, else at random.
    period, phase, r = cfg["dot_period"], cfg["dot_phase"], cfg["dot_r"]
    nails = [float(x) for x in obj.get("fr_nail_lines", [])]
    nail_u = []
    prim_faces = [f[6] for f in faces if f[5]]
    prim_loops = list(max(prim_faces, key=lambda p: p.area).loop_indices) if prim_faces else []
    if nails and prim_loops:
        forced = obj.get("fr_grain")
        if forced in ("x", "y", "z"):
            g = "xyz".index(forced)
        else:
            cos = [v.co for v in me.vertices]
            g = max(range(3), key=lambda a: max(c[a] for c in cos) - min(c[a] for c in cos))
        pts = [(me.vertices[me.loops[i].vertex_index].co[g], uvl[i].uv[0]) for i in prim_loops]
        p0, p1 = min(pts), max(pts)
        if p1[0] - p0[0] > 1e-4:
            s = (p1[1] - p0[1]) / (p1[0] - p0[0])
            nail_u = [p0[1] + s * (x - p0[0]) for x in nails]
    # Only faces that run along the grain count (not end grain or edges).
    long_ = 0.25 * max(f[1] - f[0] for f in faces)
    step_a = 0.0025
    cand = []
    for i in range(int(round(period / step_a))):
        sh = i * step_a
        c, pref = 0.0, 0.0
        for a0, a1, c0, c1, w, is_prim, _ in faces:
            lo, hi = a0 + r, a1 - r
            if hi <= lo or a1 - a0 < long_:
                continue
            for k in range(math.ceil((lo + sh - phase) / period), math.floor((hi + sh - phase) / period) + 1):
                c += w
                if is_prim and nail_u:
                    dot = phase + k * period - sh
                    pref += min(abs(dot - u) for u in nail_u)
        cand.append((c, pref, sh))
    cbest = min(x[0] for x in cand)
    cand = [x for x in cand if x[0] <= cbest + 1e-9]
    pbest = min(x[1] for x in cand)
    cand = [x for x in cand if x[1] <= pbest + 0.002]
    shift_u = rng.choice(cand)[2] + rng.randrange(cfg["periods"]) * period
    for d in uvl:
        d.uv = (d.uv[0] + shift_u, d.uv[1] + shift_v)


def _stencil_preview():
    """Alpha-clip Prop_StencilBlack in the preview stills (kitlib renders slot
    colours only, so the stencils showed as black panels)."""
    mat = bpy.data.materials.get("Prop_StencilBlack")
    if mat is None or not mat.use_nodes or not os.path.exists(STENCIL_TEX):
        return
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    if bsdf is None or bsdf.inputs["Alpha"].is_linked:
        return
    img = nt.nodes.new("ShaderNodeTexImage")
    img.image = bpy.data.images.load(STENCIL_TEX, check_existing=True)
    clip = nt.nodes.new("ShaderNodeMath")
    clip.operation = "GREATER_THAN"
    clip.inputs[1].default_value = 0.5
    nt.links.new(img.outputs["Alpha"], clip.inputs[0])
    nt.links.new(clip.outputs[0], bsdf.inputs["Alpha"])
    nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    try:
        mat.blend_method = "CLIP"
    except (AttributeError, TypeError):
        pass


def install(kit, smooth_angle=35.0, planks=None):
    """Patch this Kit instance: grain on U, plank snapping, LOD1 sharp edges,
    stencil preview. Call at the end of build(kit)."""
    base = kit._uv_metres if _kitlib_has_grain() else _uv_metres_grain
    swap = _kitlib_grain_on_v()
    planks = planks or {}

    def uv_metres(obj):
        base(obj)
        slot = _slot_of(obj).split(".")[0]
        if swap and slot in U_GRAIN_SLOTS:
            _transpose_uvs(obj)
        if slot in planks:
            _snap_planks(obj, planks[slot])
    kit._uv_metres = uv_metres

    make_lod1 = kit.make_lod1

    def make_lod1_sharp(ratio):
        make_lod1(ratio)
        lod1 = getattr(kit, "lod1", None)
        if lod1 is not None:
            lod1.data.set_sharp_from_angle(angle=math.radians(smooth_angle))
    kit.make_lod1 = make_lod1_sharp

    preview = kit.preview

    def preview_stencil(png_base, samples=48):
        _stencil_preview()
        return preview(png_base, samples=samples)
    kit.preview = preview_stencil


def scatter_offsets(kit, seed, slots=WOOD_SLOTS, tile=(0.6, 1.2), skip=(), margin=0.03, seam_at=None):
    """Give every part on `slots` its own UV offset (du, dv), in kitlib's
    pre-swap terms (dv along the grain).

    Where a part is shorter than one tile along its grain the offset keeps it
    inside one tile; a longer part gets its seam at world coordinate
    `seam_at` along its grain, if given, else at random. U is random in one
    tile.
    """
    rng = random.Random(seed)
    tu, tv = tile
    for obj in kit.parts:
        if _slot_of(obj).split(".")[0] not in slots or obj.name.split(".")[0] in skip:
            continue
        m = obj.matrix_basis
        pts = [m @ v.co for v in obj.data.vertices]
        ext = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
        forced = obj.get("fr_grain")
        g = "xyz".index(forced) if forced in ("x", "y", "z") else max(range(3), key=lambda i: ext[i])
        lo, length = min(p[g] for p in pts), ext[g]
        du = rng.uniform(0.0, tu)
        if length + 2 * margin < tv:
            dv = rng.uniform(margin, tv - length - margin) - lo
        elif seam_at is not None:
            dv = (-seam_at) % tv
        else:
            dv = rng.uniform(0.0, tv)
        obj["fr_uv_offset"] = (round(du, 4), round(dv, 4))
