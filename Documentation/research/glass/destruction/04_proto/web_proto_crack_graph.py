"""Prototype v2 for 04_unity_implementation.md (GD1): an explicit crack GRAPH
(radial tracks that wander and fork + concentric chords), the pattern annealed
glass shows after a point impact, instead of plain Voronoi cells.

  Blender -b --factory-startup --python web_proto.py -- OUTDIR

Output: per config a top-down preview PNG (stage-2 pieces by band, teeth red,
crush zone dark, stage-1 radial cracks drawn as thin fins) + stats JSON with
exact Blender triangle counts after a 6 mm extrude and 0.6 mm bevel.
"""
import math, random, sys, os, time, json

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = ARGS[0] if ARGS else "/tmp/glass_proto"
os.makedirs(OUT, exist_ok=True)
PANE_W, PANE_H, T = 1.4, 1.65, 0.006


def clip(poly, a, b, c):
    out, n = [], len(poly)
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


def clip_rect(poly, hw, hh):
    for a, b, c in ((1, 0, hw), (-1, 0, hw), (0, 1, hh), (0, -1, hh)):
        poly = clip(poly, a, b, c)
        if len(poly) < 3:
            return []
    return poly


def area(poly):
    return 0.5 * sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))


def centroid(poly):
    a = area(poly); cx = cy = 0.0
    for i in range(len(poly)):
        x0, y0 = poly[i]; x1, y1 = poly[(i + 1) % len(poly)]
        f = x0 * y1 - x1 * y0
        cx += (x0 + x1) * f; cy += (y0 + y1) * f
    return (cx / (6 * a), cy / (6 * a))


def build_web(seed, impact_uv, radials=10, r1=0.030, growth=1.55, fork_p=0.32, arc_inner=0.97, arc_outer=0.45):
    rng = random.Random(seed)
    ix, iy = (impact_uv[0] - 0.5) * PANE_W, (impact_uv[1] - 0.5) * PANE_H
    rmax = max(math.hypot(cx - ix, cy - iy) for cx in (-PANE_W / 2, PANE_W / 2) for cy in (-PANE_H / 2, PANE_H / 2)) * 1.15
    rings = [0.012]
    r = r1
    while r < rmax:
        rings.append(r); r *= growth * rng.uniform(0.9, 1.1)
    rings.append(rmax)
    K = len(rings)
    rot = rng.uniform(0, 2 * math.pi)
    # tracks: dict(theta per ring index, start ring)
    tracks = []
    for i in range(radials):
        th = rot + (i + rng.uniform(-0.3, 0.3)) * 2 * math.pi / radials
        tracks.append({"start": 0, "th": {0: th}})
    # walk outward: wander + forks
    for k in range(1, K):
        active = sorted([t for t in tracks if t["start"] <= k - 1], key=lambda t: t["th"][k - 1] % (2 * math.pi))
        n_act = len(active)
        for j, t in enumerate(active):
            t["th"][k] = t["th"][k - 1] + rng.gauss(0, 0.035)  # ~2 deg of wander per ring
        # keep the order of the previous ring, with at least 0.02 rad between neighbours
        base = active[0]["th"][k - 1]
        rel = [((t["th"][k] - base) % (2 * math.pi)) for t in active]
        prev_rel = [((t["th"][k - 1] - base) % (2 * math.pi)) for t in active]
        for j in range(n_act):
            lo = prev_rel[j - 1] + 0.02 if j > 0 else -0.5
            hi = prev_rel[j + 1] - 0.02 if j + 1 < n_act else 2 * math.pi - 0.02
            rel[j] = min(max(rel[j], max(lo, rel[j - 1] + 0.02 if j > 0 else lo)), hi)
            active[j]["th"][k] = base + rel[j]
        if k >= 2 and k < K - 1:
            n = len(active)
            for j in range(n):
                a, b = active[j], active[(j + 1) % n]
                ta, tb = a["th"][k], b["th"][k]
                gap = (tb - ta) % (2 * math.pi)
                if gap > 0.30 and rng.random() < fork_p:
                    tracks.append({"start": k, "th": {k: ta + gap * rng.uniform(0.35, 0.65)}})
    # finish forks forward
    for k in range(1, K):
        for t in tracks:
            if t["start"] < k and k not in t["th"]:
                t["th"][k] = t["th"][k - 1] + rng.gauss(0, 0.035)
    # per-node radius jitter (concentric cracks are not circles)
    for t in tracks:
        t["r"] = {k: rings[k] * (rng.uniform(0.88, 1.12) if 0 < k < K - 1 else 1.0) for k in t["th"]}

    def P(t, k):
        return (ix + t["r"][k] * math.cos(t["th"][k]), iy + t["r"][k] * math.sin(t["th"][k]))

    # Pieces: for every ring band k and every pair of angularly adjacent active
    # tracks (a, b), a quad A_k B_k B_k+1 A_k+1 (plus any fork nodes that start on
    # the top chord). A missing concentric chord merges the band with the next one.
    frac = lambda k: arc_inner + (arc_outer - arc_inner) * min(1.0, k / max(1, K - 3))
    def adjacent(k):
        act = sorted([t for t in tracks if t["start"] <= k], key=lambda t: t["th"][k] % (2 * math.pi))
        return [(act[j], act[(j + 1) % len(act)]) for j in range(len(act))]
    def forks_on_top(a, b, k):
        span = (b["th"][k + 1] - a["th"][k + 1]) % (2 * math.pi)
        fs = [t for t in tracks if t["start"] == k + 1 and 0 < (t["th"][k + 1] - a["th"][k + 1]) % (2 * math.pi) < span]
        return sorted(fs, key=lambda t: (t["th"][k + 1] - a["th"][k + 1]) % (2 * math.pi))
    pieces = []
    # crushed core: the polygon through the first ring of nodes
    core = [P(t, 0) for t in sorted([t for t in tracks if t["start"] == 0], key=lambda t: t["th"][0] % (2 * math.pi))]
    pieces.append({"poly": core, "band": 0})
    done = set()
    for k in range(0, K - 1):
        for a, b in adjacent(k):
            if (id(a), id(b), k) in done:
                continue
            left, right, kk = [P(a, k)], [P(b, k)], k
            while True:
                fs = forks_on_top(a, b, kk)
                left.append(P(a, kk + 1)); right.append(P(b, kk + 1))
                last = kk + 1 >= K - 1
                if fs or last or rng.random() < frac(kk + 1):
                    break
                kk += 1
                done.add((id(a), id(b), kk))
            top = [P(f, kk + 1) for f in fs]
            poly = [left[0]] + right + list(reversed(top)) + list(reversed(left[1:]))
            if area(poly) < 0:
                poly.reverse()
            pieces.append({"poly": poly, "band": k})
    return pieces, (ix, iy), rings, tracks


def finalize(pieces, impact, rng):
    hw, hh = PANE_W / 2, PANE_H / 2
    out = []
    for p in pieces:
        poly = clip_rect(p["poly"], hw, hh)
        if len(poly) < 3 or abs(area(poly)) < 2e-6:
            continue
        if area(poly) < 0:
            poly.reverse()
        touches = any(abs(abs(x) - hw) < 1e-6 or abs(abs(y) - hh) < 1e-6 for x, y in poly)
        q = dict(p); q["poly"] = poly; q["area"] = abs(area(poly)); q["kind"] = "crush" if p["band"] == 0 else "shard"
        if not touches or q["kind"] == "crush":
            out.append(q); continue
        # tooth cut: a chord 6-24 cm in from the frame side this piece touches most,
        # tilted up to +-25 deg, so a jagged dagger stays in the glazing stop.
        sides = {"r": 0.0, "l": 0.0, "t": 0.0, "b": 0.0}
        for i in range(len(poly)):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % len(poly)]
            L = math.hypot(x1 - x0, y1 - y0)
            if abs(x0 - hw) < 1e-6 and abs(x1 - hw) < 1e-6: sides["r"] += L
            if abs(x0 + hw) < 1e-6 and abs(x1 + hw) < 1e-6: sides["l"] += L
            if abs(y0 - hh) < 1e-6 and abs(y1 - hh) < 1e-6: sides["t"] += L
            if abs(y0 + hh) < 1e-6 and abs(y1 + hh) < 1e-6: sides["b"] += L
        side = max(sides, key=sides.get)
        if sides[side] < 0.01:
            out.append(dict(q, kind="shard")); continue
        d = rng.uniform(0.06, 0.24)
        tilt = math.radians(rng.uniform(-25, 25))
        n = {"r": (1, 0), "l": (-1, 0), "t": (0, 1), "b": (0, -1)}[side]
        nx = n[0] * math.cos(tilt) - n[1] * math.sin(tilt)
        ny = n[0] * math.sin(tilt) + n[1] * math.cos(tilt)
        cx, cy = centroid(poly)
        # a point on the cut line: d in from the frame along the side normal, at the piece's centroid
        px = (hw - d) * n[0] if n[0] else cx
        py = (hh - d) * n[1] if n[1] else cy
        c = nx * px + ny * py
        inner = clip(poly, nx, ny, c)        # toward the impact: falls
        outer = clip(poly, -nx, -ny, -c)     # in the stop: stays
        ok_in = len(inner) >= 3 and abs(area(inner)) > 2e-5
        ok_out = len(outer) >= 3 and abs(area(outer)) > 2e-6
        if ok_in and ok_out:
            out.append(dict(q, poly=inner, area=abs(area(inner)), kind="shard"))
            out.append(dict(q, poly=outer, area=abs(area(outer)), kind="tooth"))
        elif ok_out:
            out.append(dict(q, kind="tooth"))
        else:
            out.append(dict(q, kind="shard"))
    return out


def blender_pieces(pieces, impact, name):
    import bpy, bmesh
    t0 = time.perf_counter()
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    tris = {"shard": 0, "tooth": 0, "crush": 0}
    objs = []
    rng = random.Random(11)
    for idx, p in enumerate(pieces):
        cx, cy = centroid(p["poly"])
        bm = bmesh.new()
        vs = [bm.verts.new((x - cx, 0.0, y - cy)) for x, y in p["poly"]]
        f = bm.faces.new(vs)
        ext = bmesh.ops.extrude_face_region(bm, geom=[f])
        nv = [e for e in ext["geom"] if isinstance(e, bmesh.types.BMVert)]
        bmesh.ops.translate(bm, vec=(0, T, 0), verts=nv)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        bmesh.ops.bevel(bm, geom=bm.edges[:], offset=0.0006, segments=1, affect="EDGES", clamp_overlap=True)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new("P%03d" % idx); bm.to_mesh(me); bm.free()
        tris[p["kind"]] += len(me.polygons)
        ob = bpy.data.objects.new(me.name, me)
        r = math.hypot(cx - impact[0], cy - impact[1])
        w = math.exp(-r / 0.35)
        ob.location = (cx, 0.002 * w, cy)
        ob.rotation_euler = (math.radians(rng.uniform(-0.6, 0.6) * w), 0, math.radians(rng.uniform(-0.6, 0.6) * w))
        if p["kind"] == "tooth":
            ob.color = (0.82, 0.18, 0.14, 1)
        elif p["kind"] == "crush":
            ob.color = (0.12, 0.12, 0.12, 1)
        else:
            g = 0.55 + 0.05 * (p["band"] % 6)
            ob.color = (0.30 * g, 0.62 * g + 0.15, 0.58 * g + 0.2, 1)
        coll.objects.link(ob); objs.append(ob)
    return tris, round(time.perf_counter() - t0, 3), coll


def render(path):
    import bpy
    scene = bpy.context.scene
    if scene.camera is None:
        cd = bpy.data.cameras.new("cam"); cd.type = "ORTHO"; cd.ortho_scale = 1.85
        cam = bpy.data.objects.new("cam", cd); scene.collection.objects.link(cam)
        cam.location = (0, -3, 0); cam.rotation_euler = (math.radians(90), 0, 0); scene.camera = cam
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "FLAT"; scene.display.shading.color_type = "OBJECT"
    scene.display.shading.show_object_outline = True
    scene.display.shading.object_outline_color = (0.02, 0.02, 0.02)
    scene.render.resolution_x, scene.render.resolution_y = 700, 810
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    configs = [("web_eye_centre", 1001, (0.50, 0.70), 10), ("web_eye_left", 2002, (0.27, 0.66), 9),
               ("web_low_right", 3003, (0.72, 0.42), 11), ("web_eye_centre_b", 4004, (0.52, 0.72), 12)]
    results, prev = [], None
    for name, seed, uv, rad in configs:
        t0 = time.perf_counter()
        web, impact, rings, tracks = build_web(seed, uv, radials=rad)
        pieces = finalize(web, impact, random.Random(seed + 1))
        gen = time.perf_counter() - t0
        tris, bt, coll = blender_pieces(pieces, impact, name)
        if prev is not None:
            prev.hide_render = True
        prev = coll
        render(os.path.join(OUT, name + ".png"))
        kinds = {k: sum(1 for p in pieces if p["kind"] == k) for k in ("shard", "tooth", "crush")}
        areas = sorted(p["area"] for p in pieces if p["kind"] == "shard")
        st = {"name": name, "seed": seed, "impact_uv": uv, "radials_start": rad,
              "radial_tracks_total": len(tracks), "rings": len(rings), "pieces": kinds,
              "shard_area_cm2_p10_p50_p90": [round(areas[int(len(areas) * q)] * 1e4, 1) for q in (0.1, 0.5, 0.9)],
              "avg_verts": round(sum(len(p["poly"]) for p in pieces) / len(pieces), 2),
              "tris": tris, "tris_total": sum(tris.values()),
              "coverage_pct": round(100 * sum(p["area"] for p in pieces) / (PANE_W * PANE_H), 2),
              "gen_s_cpython": round(gen, 4), "blender_mesh_s": bt}
        results.append(st); print("[web]", json.dumps(st))
    json.dump(results, open(os.path.join(OUT, "web_stats.json"), "w"), indent=1)


main()
