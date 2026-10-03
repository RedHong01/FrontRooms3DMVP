"""Prototype for 04_unity_implementation.md (GD1): a radial + concentric 2D
Voronoi "fracture stamp" for a 1.4 x 1.65 m, 6 mm pane, clipped to the pane,
extruded and bevelled in Blender, with exact triangle counts and timings.

Run (scratchpad only, never Red's project):
  Blender -b --factory-startup --python stamp_proto.py -- OUTDIR

Pure geometry: half-plane clipping of convex polygons (every Voronoi cell is
convex), so the same code ports 1:1 to C# for the runtime fit in Unity.
"""
import math, random, sys, os, time, json

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = ARGS[0] if ARGS else "/tmp/glass_proto"
os.makedirs(OUT, exist_ok=True)

PANE_W, PANE_H, T = 1.4, 1.65, 0.006


def clip(poly, a, b, c):
    """Keep the part of convex polygon `poly` where a*x + b*y <= c."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        dp = a * p[0] + b * p[1] - c
        dq = a * q[0] + b * q[1] - c
        if dp <= 0:
            out.append(p)
        if (dp < 0 < dq) or (dq < 0 < dp):
            t = dp / (dp - dq)
            out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return out


def area(poly):
    s = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % len(poly)]
        s += x0 * y1 - x1 * y0
    return 0.5 * s


def centroid(poly):
    a = area(poly); cx = cy = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % len(poly)]
        f = x0 * y1 - x1 * y0
        cx += (x0 + x1) * f; cy += (y0 + y1) * f
    return (cx / (6 * a), cy / (6 * a))


def radial_seeds(rng, impact, spokes=11, r0=0.010, growth=1.42, rmax=2.6):
    """Seeds on jittered rings around the impact. The angular count grows
    outward so radial cracks branch; ring spacing grows geometrically so cells
    are small (crushed) near the impact and large near the frame."""
    seeds, ring = [], []
    rot = rng.uniform(0, 2 * math.pi)
    r, k = r0, 0
    while r < rmax:
        n = max(4, int(round(spokes * (1.0 + 0.22 * max(0, k - 3)))))
        n = min(n, 34)
        for i in range(n):
            a = rot + (i + 0.5 + rng.uniform(-0.28, 0.28)) * 2 * math.pi / n
            rr = r * rng.uniform(0.86, 1.14)
            seeds.append((impact[0] + rr * math.cos(a), impact[1] + rr * math.sin(a)))
            ring.append(k)
        r *= growth * rng.uniform(0.92, 1.08)
        k += 1
    return seeds, ring


def voronoi_in_rect(seeds, rect):
    x0, y0, x1, y1 = rect
    box = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    cells = []
    for i, s in enumerate(seeds):
        poly = box
        # nearest first: most clipping is done by close neighbours
        order = sorted(range(len(seeds)), key=lambda j: (seeds[j][0] - s[0]) ** 2 + (seeds[j][1] - s[1]) ** 2)
        for j in order[1:]:
            o = seeds[j]
            dx, dy = o[0] - s[0], o[1] - s[1]
            d2 = dx * dx + dy * dy
            # a neighbour farther than twice the cell's max radius cannot clip it
            if poly:
                rmax2 = max((p[0] - s[0]) ** 2 + (p[1] - s[1]) ** 2 for p in poly)
                if d2 > 4 * rmax2:
                    break
            mx, my = (s[0] + o[0]) * 0.5, (s[1] + o[1]) * 0.5
            poly = clip(poly, dx, dy, dx * mx + dy * my)
            if len(poly) < 3:
                break
        cells.append(poly if len(poly) >= 3 and abs(area(poly)) > 1e-7 else None)
    return cells


def build_stamp(seed, impact_uv, spokes):
    rng = random.Random(seed)
    impact = ((impact_uv[0] - 0.5) * PANE_W, (impact_uv[1] - 0.5) * PANE_H)
    seeds, ring = radial_seeds(rng, impact, spokes=spokes)
    rect = (-PANE_W / 2, -PANE_H / 2, PANE_W / 2, PANE_H / 2)
    t0 = time.perf_counter()
    cells = voronoi_in_rect(seeds, rect)
    dt = time.perf_counter() - t0
    pieces = []
    eps = 1e-6
    for poly, k in zip(cells, ring):
        if poly is None:
            continue
        border = any(abs(abs(p[0]) - PANE_W / 2) < eps or abs(abs(p[1]) - PANE_H / 2) < eps for p in poly)
        # merge micro-slivers (< 1 cm2) into dust: they become particles, not pieces
        a = abs(area(poly))
        pieces.append({"poly": poly, "ring": k, "border": border, "area": a})
    return pieces, dt, impact


def stats(pieces):
    n = len(pieces)
    verts = [len(p["poly"]) for p in pieces]
    big = [p for p in pieces if p["area"] >= 1e-4]
    dust = n - len(big)
    border = sum(1 for p in pieces if p["border"])
    # teeth: border pieces whose inward reach from the frame is < 0.22 m
    teeth = 0
    for p in pieces:
        if not p["border"]:
            continue
        reach = max(min(PANE_W / 2 - abs(x), PANE_H / 2 - abs(y)) for x, y in p["poly"])
        p["tooth"] = reach < 0.22
        teeth += p["tooth"]
    return {"cells": n, "pieces_ge_1cm2": len(big), "dust_lt_1cm2": dust, "border": border,
            "teeth_reach_lt_22cm": teeth, "avg_verts": round(sum(verts) / n, 2), "max_verts": max(verts)}


def blender_build(pieces, name, tilt_deg=0.6, push=0.002):
    """Extrude 6 mm, bevel 0.6 mm (1 segment), one object per piece, origin at
    the centroid (the piece pivot). Returns exact triangle counts and time."""
    import bpy, bmesh
    from mathutils import Vector, Matrix
    t0 = time.perf_counter()
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    tris_total, objs = 0, []
    rng = random.Random(7)
    for idx, p in enumerate(pieces):
        if p["area"] < 1e-4:
            continue
        cx, cy = centroid(p["poly"])
        bm = bmesh.new()
        vs = [bm.verts.new((x - cx, 0.0, y - cy)) for x, y in p["poly"]]  # pane in XZ, normal along Y
        f = bm.faces.new(vs)
        bmesh.ops.recalc_face_normals(bm, faces=[f])
        ext = bmesh.ops.extrude_face_region(bm, geom=[f])
        nv = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0, T, 0), verts=nv)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.0006, segments=1, affect="EDGES", clamp_overlap=True)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new("P%03d" % idx)
        bm.to_mesh(me); bm.free()
        tris_total += len(me.polygons)
        ob = bpy.data.objects.new(me.name, me)
        # stage-2 pose: tilt + push toward the far side, stronger near the impact
        r = math.hypot(cx - p.get("ix", 0), cy - p.get("iy", 0))
        w = math.exp(-r / 0.35)
        ob.location = (cx, push * w + rng.uniform(0, 0.0005), cy)
        ob.rotation_euler = (math.radians(rng.uniform(-tilt_deg, tilt_deg) * w), 0, math.radians(rng.uniform(-tilt_deg, tilt_deg) * w))
        coll.objects.link(ob)
        objs.append(ob)
    return {"objects": len(objs), "triangles": tris_total, "build_s": round(time.perf_counter() - t0, 3)}, objs, coll


def render_preview(pieces, impact, path_png, title):
    """Top-down orthographic look at the stamp: pieces coloured by ring, teeth red."""
    import bpy
    scene = bpy.context.scene
    for ob in list(bpy.data.objects):
        if ob.type in ("CAMERA", "LIGHT"):
            bpy.data.objects.remove(ob)
    cam_data = bpy.data.cameras.new("cam"); cam_data.type = "ORTHO"; cam_data.ortho_scale = 1.85
    cam = bpy.data.objects.new("cam", cam_data); scene.collection.objects.link(cam)
    cam.location = (0, -3, 0); cam.rotation_euler = (math.radians(90), 0, 0)
    scene.camera = cam
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "FLAT"
    scene.display.shading.color_type = "OBJECT"
    scene.display.shading.show_object_outline = True
    scene.display.shading.object_outline_color = (0.02, 0.02, 0.02)
    scene.render.resolution_x, scene.render.resolution_y = 900, 1040
    scene.render.film_transparent = False
    scene.world = bpy.data.worlds.new("w") if scene.world is None else scene.world
    scene.render.filepath = path_png
    bpy.ops.render.render(write_still=True)


def main():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    results = []
    configs = [
        ("eye_centre", 1001, (0.50, 0.70), 11),
        ("eye_left", 2002, (0.28, 0.66), 11),
        ("low_right", 3003, (0.70, 0.45), 9),
    ]
    for name, seed, uv, spokes in configs:
        pieces, dt, impact = build_stamp(seed, uv, spokes)
        for p in pieces:
            p["ix"], p["iy"] = impact
        st = stats(pieces)
        st.update({"name": name, "seed": seed, "impact_uv": uv, "spokes": spokes, "voronoi_s_cpython": round(dt, 3)})
        b, objs, coll = blender_build(pieces, name)
        st.update(b)
        # colour objects: teeth red, others by ring
        big = [p for p in pieces if p["area"] >= 1e-4]
        for ob, p in zip(objs, big):
            if p.get("tooth"):
                ob.color = (0.85, 0.15, 0.12, 1)
            else:
                g = min(1.0, 0.25 + 0.07 * p["ring"])
                ob.color = (0.25 * g, 0.55 * g + 0.2, 0.5 * g + 0.25, 1)
        render_preview(pieces, impact, os.path.join(OUT, "stamp_%s.png" % name), name)
        coll.hide_render = True
        for ob in objs:
            ob.hide_render = True
        results.append(st)
        print("[proto]", json.dumps(st))
    with open(os.path.join(OUT, "stamp_stats.json"), "w") as f:
        json.dump(results, f, indent=1)


main()
