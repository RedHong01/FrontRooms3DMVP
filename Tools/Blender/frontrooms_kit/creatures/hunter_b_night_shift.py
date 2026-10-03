"""Hunter concept B "Night Shift" (Documentation/research/hunter/10_hunter_directions.md §4, §7.3).

The building's night electrician in a faded spruce rental coverall, hood drawn tight round a
flat opal troffer lens that is his face. Render pose: the "shrugged stalk" (Hunt): left foot
forward, knees soft, shoulders shrugged up into the hood (no neck), torso pitched ~15 deg,
hood bowed 18 deg like a head reading a meter, long forearms hanging the gloves to mid-thigh,
tool pouch on the right hip, key ring on the left.

Construction (deviations from §7.3 are listed in the DESIGN note at the bottom):
* Garments are separate Skin chains (torso, arms, legs, boots, gloves), so no chain branches
  with big radii (the flat-sheet artefact at the crotch / chest top).
* The shrug is the torso's own top: a wide flat shoulder section tapering to a high, wide
  collar behind the hood, so the trapezius is one slope from shoulder tip to hood crown. The
  arms hang from inside the shoulder ends, so the shrug reads as mass, not as bent arms.
* The hood is a superellipsoid cut open at the face plane (bmesh bisect) with a soft peak at
  the back; its opening is capped and recessed, with a rolled drawcord hem round it, and the
  lens door sits inside the opening.
* Tape cuffs and the tool belt are strips cut from the garment they wrap and pushed out along
  the normals, so they hug the cloth instead of floating as cylinders.
* Lens emission is preview-only (Hunt: dim, steady) with a procedural mask for the two lamp
  bands and the pressed face shadow; Unity drives the real emission from HunterState.
"""

import math

import bmesh
import bpy
from mathutils import Euler, Matrix, Vector

NAME = "Hunter_B_NightShift"
TITLE = "Night Shift"
PITCH = ("The building's night electrician went up into the ceiling and came back down wearing it: "
         "a hooded figure in a faded work coverall whose face is a lit ceiling-light panel.")
EYE = 1.64            # lens centre after flooring; build() overwrites it with the measured value
SMOOTH_ANGLE = 60.0
LENS_GLOW = 3.0       # preview emission strength (Hunt state: dim, steady); 0 = Listen (off)

TWILL = "Creature_TwillSpruce"
LENS = "Creature_LensOpal"
WHITE = "Prop_PlasticWhite"
TAPE = "Creature_TapeSilver"
GLOVE = "Prop_FabricChair"
VINYL = "Prop_Vinyl"


# ------------------------------------------------------------------ small maths helpers
def V(x, y, z):
    return Vector((x, y, z))


def deg(m3):
    e = m3.to_euler("XYZ")
    return (math.degrees(e.x), math.degrees(e.y), math.degrees(e.z))


def basis(x, y, z):
    """Rotation whose local X/Y/Z axes are the given world vectors."""
    return Matrix((x, y, z)).transposed()


def frame_z(direction, hint=None):
    """Rotation taking local +Z to `direction` (local X kept close to `hint`, default world X)."""
    z = direction.normalized()
    hint = hint or V(1, 0, 0)
    y = z.cross(hint)
    if y.length < 1e-4:
        y = z.cross(V(0, 1, 0))
    y.normalize()
    x = y.cross(z).normalized()
    return basis(x, y, z)


def ik(root, end, l1, l2, pole):
    """Two-bone IK: the middle joint for segment lengths l1, l2, bent toward `pole`."""
    d = end - root
    L = min(d.length, l1 + l2 - 1e-4)
    n = d.normalized()
    a = (l1 * l1 - l2 * l2 + L * L) / (2 * L)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    p = pole - n * pole.dot(n)
    p.normalize()
    return root + n * a + p * h


def lerp(a, b, t):
    return a.lerp(b, t)


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


# ------------------------------------------------------------------ mesh helpers
def resample_loop(pts, count):
    """Even arc-length resampling of a closed polyline."""
    segs = [(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    lens = [(b - a).length for a, b in segs]
    total = sum(lens)
    out, k, acc = [], 0, 0.0
    for i in range(count):
        target = total * i / count
        while acc + lens[k] < target:
            acc += lens[k]
            k += 1
        a, b = segs[k]
        out.append(a.lerp(b, (target - acc) / max(lens[k], 1e-9)))
    return out


def loop_tube(kit, pts, radius, slot, normal, verts=10, name="loop"):
    """Closed round tube along a planar loop; the ring frame uses the loop's plane normal,
    so it never twists (kitlib.tube flips its reference near vertical tangents)."""
    bm = bmesh.new()
    n = len(pts)
    rings = []
    for k in range(n):
        p = pts[k]
        t = (pts[(k + 1) % n] - pts[k - 1]).normalized()
        side = t.cross(normal).normalized()
        up = side.cross(t).normalized()
        rings.append([bm.verts.new(p + (side * math.cos(2 * math.pi * i / verts) +
                                        up * math.sin(2 * math.pi * i / verts)) * radius)
                      for i in range(verts)])
    for k in range(n):
        a, b = rings[k], rings[(k + 1) % n]
        for i in range(verts):
            j = (i + 1) % verts
            bm.faces.new((a[i], a[j], b[j], b[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def strip(kit, src, planes, keep, offset, thickness, slot, name="strip"):
    """Cut a strip out of a finished garment mesh between `planes` [(co, outward normal)],
    keep the vertices `keep(co)` accepts, push it out along the normals by `offset` and give
    it `thickness` (outward). Tape, belts: they hug the cloth they wrap."""
    bm = bmesh.new()
    bm.from_mesh(src.data)
    bm.transform(src.matrix_world.copy())
    for co, no in planes:
        geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
        bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=co, plane_no=no, clear_outer=True)
    doomed = [v for v in bm.verts if not keep(v.co)]
    if doomed:
        bmesh.ops.delete(bm, geom=doomed, context="VERTS")
    loose = [v for v in bm.verts if not v.link_faces]
    if loose:
        bmesh.ops.delete(bm, geom=loose, context="VERTS")
    bm.normal_update()
    for v in bm.verts:
        v.co += v.normal * offset
    obj = kit._new_object(name, bm, slot, "metres", "xz")
    if thickness:
        mod = obj.modifiers.new("solid", "SOLIDIFY")
        mod.thickness = thickness
        mod.offset = 1.0
        mod.use_even_offset = True
    return obj


def ray(objs, origin, direction):
    """Nearest hit on any of objs (applied meshes, identity transforms): (point, normal)."""
    best = None
    for o in objs:
        ok, loc, nor, _ = o.ray_cast(origin, direction)
        if ok:
            d = (loc - origin).length
            if best is None or d < best[0]:
                best = (d, loc.copy(), nor.normalized())
    if best is None:
        raise RuntimeError("ray missed at %s" % (tuple(origin),))
    return best[1], best[2]


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


# ------------------------------------------------------------------ body parts
def build_hood(kit, H, pitch, half, t_cut, lens, border, zc=0.0, recess=0.04, hem_r=0.012, peak=0.03,
               round_=0.65, side_back=0.045, chin_back=0.03):
    """Hood shell (TWILL) cut open at the face plane through H, recessed opening, rolled hem,
    enamel lens door (WHITE) and the opal lens (LENS). The opening is then bent so its sides
    and chin recede behind the brim (a hood's profile, not a visor's straight edge).
    Returns a dict: lens, shell, centre, R, hem (world points)."""
    R = Euler((math.radians(pitch), 0, 0)).to_matrix()
    hx, hy, hz = half
    cy = t_cut * hy
    shell_loc = H + R @ V(0, cy, zc)
    shell = kit.soft_box((2 * hx, 2 * hy, 2 * hz), shell_loc, TWILL, radius=2 * max(half),
                         segments=28, rings=16, rot=(pitch, 0, 0), name="hood shell")
    bm = bmesh.new()
    bm.from_mesh(shell.data)
    # Fabric, not a helmet: a soft peak at the back of the crown (the centre seam pulls it)
    # and the lower back draped down into the shoulder yoke.
    for v in bm.verts:
        p = v.co.copy()
        k = 1.0 / max(1e-6, math.sqrt((p.x / hx) ** 2 + (p.y / hy) ** 2 + (p.z / hz) ** 2))
        v.co = p.lerp(p * k, round_)
    for v in bm.verts:
        fy, fz = v.co.y / hy, v.co.z / hz
        if fy > -0.3 and fz > 0:
            # parka peak: a soft ridge along the centre seam, highest just behind the crown,
            # so the hood reads as a hood even in the black cut-out
            f = smooth((fy + 0.3) * 0.9) * smooth(fz * 1.2) * max(0.0, 1 - abs(v.co.x / hx)) ** 1.5
            v.co.y += peak * 0.7 * f
            v.co.z += peak * f
        if fy > 0 and fz < 0:
            v.co.z -= 0.04 * smooth(fy) * smooth(-fz)
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=(0, -cy, 0), plane_no=(0, -1, 0), clear_outer=True)
    edges = [e for e in bm.edges if e.is_boundary]
    ring = {v for e in edges for v in e.verts}
    loop = sorted((v.co.copy() for v in ring), key=lambda c: math.atan2(c.z, c.x))
    cap = bmesh.ops.holes_fill(bm, edges=edges, sides=0)["faces"]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.inset_region(bm, faces=cap, thickness=0.004, depth=-recess, use_even_offset=True)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)

    def bend(co):
        yh, zh = co.y + cy, co.z + zc            # head frame (the cut plane is yh = 0)
        w = smooth((0.12 - yh) / 0.12)
        dy = side_back * (co.x / hx) ** 2 + chin_back * max(0.0, -zh / hz) ** 2
        return co + V(0, w * dy, 0)
    for v in bm.verts:
        v.co = bend(v.co)
    bm.to_mesh(shell.data)
    bm.free()
    # Rolled drawcord hem on the cut edge (world space), evenly resampled.
    pts = resample_loop([shell_loc + R @ bend(c) for c in loop], 40)
    loop_tube(kit, pts, hem_r, TWILL, R @ V(0, -1, 0), verts=8, name="hood hem")
    # Lens door rim and the flat opal lens, set in the opening.
    lw, lh = lens
    # The lens door sits at the floor of the recess: a light deep inside a drawn hood.
    kit.frame((lw + 2 * border, lh + 2 * border), (lw, lh), 0.06, H + R @ V(0, recess + 0.02, 0), WHITE,
              bevel=0.003, rot=(pitch, 0, 0), name="lens door")
    lens_obj = kit.bulged_panel(lw, lh, 0.008, H + R @ V(0, recess - 0.008, 0), LENS, segments=12,
                                rot=(pitch, 0, 0), name="opal lens")
    return {"lens": lens_obj, "shell": shell, "centre": shell_loc, "R": R, "hem": pts}


def build_glove(kit, cl, wrist_in, wrist, d, toward_body, name):
    """Black canvas work glove: cuff tube, palm block, four curled fingers and a thumb."""
    d = d.normalized()
    n = (toward_body - d * toward_body.dot(d)).normalized()     # palm normal (faces the thigh)
    s = n.cross(d).normalized()                                  # across the knuckles
    thumb = s if s.y < 0 else -s                                 # thumb toward the front
    cl.skin_body(kit, {"in": (tuple(wrist_in), 0.042), "w": (tuple(wrist), 0.046),
                       "p": (tuple(wrist + d * 0.04), 0.044)},
                 [("in", "w"), ("w", "p")], GLOVE, subdiv=1, name=name + " cuff")
    kit.soft_box((0.098, 0.048, 0.112), wrist + d * 0.068 - n * 0.002, GLOVE, radius=0.014,
                 segments=16, rings=10, rot=deg(basis(s, n, d)), name=name + " palm")
    joints, bones = {}, []
    for i, (off, ls) in enumerate(((0.034, 0.93), (0.0115, 1.0), (-0.0115, 0.95), (-0.033, 0.80))):
        k0 = wrist + d * 0.106 + thumb * off - n * 0.004
        k1 = k0 + (d * 0.044 + n * 0.012) * ls
        k2 = k1 + (d * 0.024 + n * 0.024) * ls
        k3 = k2 + (d * 0.006 + n * 0.022) * ls
        for j, (p, r) in enumerate(((k0, 0.0138), (k1, 0.0134), (k2, 0.0126), (k3, 0.0115))):
            joints["f%d%d" % (i, j)] = (tuple(p), r)
        bones += [("f%d0" % i, "f%d1" % i), ("f%d1" % i, "f%d2" % i), ("f%d2" % i, "f%d3" % i)]
    t0 = wrist + d * 0.035 + thumb * 0.032 + n * 0.010
    t1 = t0 + d * 0.035 + thumb * 0.020 + n * 0.020
    t2 = t1 + d * 0.026 + thumb * 0.002 + n * 0.020
    joints.update({"t0": (tuple(t0), 0.019), "t1": (tuple(t1), 0.017), "t2": (tuple(t2), 0.0145)})
    bones += [("t0", "t1"), ("t1", "t2")]
    cl.decimate_to(cl.skin_body(kit, joints, bones, GLOVE, subdiv=1, name=name + " fingers"), 620)


def foot_points(ball, yaw, pitch):
    """Boot points from the ball-of-foot contact on the floor. Local frame: +Y = back.
    `pitch` lifts everything behind the ball (heel raised), the toe stays flat."""
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    rz = Euler((0, 0, math.radians(yaw))).to_matrix()

    def P(x, y, z, flex=True):
        if flex and y > 0:
            y, z = y * cp - z * sp, y * sp + z * cp
        return ball + rz @ V(x, y, z)
    return {
        "ankle": P(0, 0.150, 0.112), "instep": P(0, 0.070, 0.086),
        "heel": P(0, 0.205, 0.064), "mid": P(0, 0.100, 0.064),
        "ball": P(0, 0.0, 0.058, False), "toe": P(0, -0.098, 0.050, False),
        "_P": P,
    }


def build_boot(kit, cl, fp, shaft_top, yaw, pitch, name):
    """Rubber-soled work boot: a shaft chain into the instep, a heel-to-toe foot chain, a sole."""
    P = fp["_P"]
    j = {"s": (tuple(shaft_top), 0.056), "a": (tuple(fp["ankle"]), 0.064), "i": (tuple(fp["instep"]), 0.058),
         "h": (tuple(fp["heel"]), 0.056), "m": (tuple(fp["mid"]), 0.060), "b": (tuple(fp["ball"]), 0.059),
         "t": (tuple(fp["toe"]), 0.052)}
    upper = cl.skin_body(kit, j, [("s", "a"), ("a", "i"), ("h", "m"), ("m", "b"), ("b", "t")], VINYL,
                         subdiv=2, name=name)
    # Measure the upper along the foot (toe and heel ends, width near the floor) so the
    # rubber sole sits just inside its outline instead of sticking out like a sled.
    rz = Euler((0, 0, math.radians(yaw))).to_matrix().inverted()
    loc = [rz @ (v.co - fp["ball"] + V(0, 0, fp["ball"].z)) for v in upper.data.vertices]
    low = [c for c in loc if c.z < 0.05]
    front = min(c.y for c in loc if c.y < 0.02)
    back = max(c.y for c in low) if pitch <= 0.5 else 0.195
    half_w = max(abs(c.x) for c in low)
    y0, y1 = front + 0.006, back - 0.006
    w = 2 * half_w + 0.004
    # Rubber sole: rear part follows the raised heel, toe part stays flat on the floor.
    if pitch > 0.5:
        kit.soft_box((w, y1 - 0.0, 0.03), P(0, y1 / 2, 0.015), VINYL, radius=0.012, segments=16, rings=8,
                     rot=(pitch, 0, yaw), name=name + " sole heel")
        kit.soft_box((w - 0.002, 0.01 - y0, 0.03), P(0, (y0 + 0.01) / 2, 0.015, False), VINYL, radius=0.012,
                     segments=16, rings=8, rot=(0, 0, yaw), name=name + " sole toe")
    else:
        kit.soft_box((w, y1 - y0, 0.03), P(0, (y0 + y1) / 2, 0.015), VINYL, radius=0.012, segments=16, rings=8,
                     rot=(0, 0, yaw), name=name + " sole")
    print("[nightshift] %s upper y %.3f..%.3f half-width %.3f" % (name, front, back, half_w))
    cl.decimate_to(upper, 560)


def lens_glow(kit, strength):
    """Preview-only: opal lens emission with two lamp bands behind the diffuser and the
    shadow of a face pressed against it from inside (the tell, 02 S3)."""
    mat = kit._material(LENS)
    nt = mat.node_tree
    N, L = nt.nodes, nt.links
    bsdf = N.get("Principled BSDF")
    tc = N.new("ShaderNodeTexCoord")
    sep = N.new("ShaderNodeSeparateXYZ")
    L.new(tc.outputs["UV"], sep.inputs[0])
    u, v = sep.outputs[0], sep.outputs[1]

    def m(op, a, b=None, clamp=False):
        node = N.new("ShaderNodeMath")
        node.operation = op
        node.use_clamp = clamp
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                node.inputs[i].default_value = x
            else:
                L.new(x, node.inputs[i])
        return node.outputs[0]

    def blob(cx, cy, rx, ry, soft):
        dx = m("DIVIDE", m("SUBTRACT", u, cx), rx)
        dy = m("DIVIDE", m("SUBTRACT", v, cy), ry)
        d = m("ADD", m("MULTIPLY", dx, dx), m("MULTIPLY", dy, dy))
        mr = N.new("ShaderNodeMapRange")
        mr.interpolation_type = "SMOOTHSTEP"
        L.new(d, mr.inputs["Value"])
        mr.inputs["From Min"].default_value = max(0.0, 1.0 - soft)
        mr.inputs["From Max"].default_value = 1.0
        mr.inputs["To Min"].default_value = 1.0
        mr.inputs["To Max"].default_value = 0.0
        return mr.outputs["Result"]

    # Shadow of a face pressed against the opal from inside: a soft head oval and sharper,
    # darker contact patches (brow, cheekbones, nose, lips, chin). No eyes: it is a shadow.
    terms = [(blob(0.50, 0.50, 0.30, 0.38, 0.8), 0.34),
             (blob(0.50, 0.72, 0.17, 0.07, 0.6), 0.20),
             (blob(0.34, 0.52, 0.06, 0.045, 0.7), 0.16), (blob(0.66, 0.52, 0.06, 0.045, 0.7), 0.16),
             (blob(0.50, 0.46, 0.04, 0.08, 0.6), 0.24)]
    shadow = None
    for sock, w in terms:
        s = m("MULTIPLY", sock, w)
        shadow = s if shadow is None else m("ADD", shadow, s)
    lit = m("SUBTRACT", 1.0, m("MINIMUM", shadow, 0.8))
    # Two lamps behind the opal: vertical bright bands, hidden where the head blocks them.
    band = None
    for c in (0.2, 0.8):
        b = m("SUBTRACT", 1.0, m("DIVIDE", m("ABSOLUTE", m("SUBTRACT", u, c)), 0.10), clamp=True)
        b = m("POWER", b, 0.6)
        band = b if band is None else m("ADD", band, b)
    glow = m("MULTIPLY", lit, m("ADD", 0.25, m("MULTIPLY", band, 1.6)))
    L.new(m("MULTIPLY", glow, strength), bsdf.inputs["Emission Strength"])
    bsdf.inputs["Emission Color"].default_value = (1.0, 0.92, 0.78, 1.0)
    base = N.new("ShaderNodeMixRGB")
    base.blend_type = "MIX"
    L.new(lit, base.inputs["Fac"])
    base.inputs["Color1"].default_value = (0.45, 0.44, 0.41, 1)
    base.inputs["Color2"].default_value = (0.91, 0.894, 0.847, 1)
    L.new(base.outputs["Color"], bsdf.inputs["Base Color"])


# ------------------------------------------------------------------ the figure
def build(kit, cl):
    global EYE
    # ---- feet first: the legs are solved down to them
    yaw_l, yaw_r, pitch_r = 5.0, -6.0, 14.0
    fl = foot_points(V(0.13, -0.27, 0.0), yaw_l, 0.0)
    fr = foot_points(V(-0.135, 0.125, 0.0), yaw_r, pitch_r)

    # ---- legs (coverall), one chain each from inside the seat
    THIGH, SHIN = 0.48, 0.44
    hip_l, hip_r = V(0.115, 0.06, 0.97), V(-0.115, 0.08, 0.965)
    knee_l = ik(hip_l, fl["ankle"], THIGH, SHIN, V(0.05, -1, 0))
    knee_r = ik(hip_r, fr["ankle"], THIGH, SHIN, V(-0.05, -1, 0))
    legs, leg_bones = {}, []
    for s, hip, knee, fp in (("l", hip_l, knee_l, fl), ("r", hip_r, knee_r, fr)):
        sx = 1 if s == "l" else -1
        legs["seat_" + s] = ((0.055 * sx, 0.05, 1.05), 0.12)
        legs["hip_" + s] = (tuple(hip), 0.126)
        legs["knee_" + s] = (tuple(knee), 0.087)
        legs["tape_" + s] = (tuple(lerp(knee, fp["ankle"], 0.80)), 0.070)
        legs["hem_" + s] = (tuple(lerp(knee, fp["ankle"], 0.93)), 0.086)
        leg_bones += [("seat_" + s, "hip_" + s), ("hip_" + s, "knee_" + s), ("knee_" + s, "tape_" + s),
                      ("tape_" + s, "hem_" + s)]
    legs_obj = cl.skin_body(kit, legs, leg_bones, TWILL, subdiv=2, name="coverall legs")
    cl.decimate_to(legs_obj, 1500)

    # ---- torso (coverall): pelvis to a collar hidden in the hood; the chest carries the mass
    # The shrug lives in the torso's own top: a wide, flat shoulder section tapering to a
    # high collar behind the hood, so the trapezius is one slope from shoulder to hood.
    torso = {
        "crotch": ((0, 0.065, 0.925), (0.085, 0.085)),
        "pelvis": ((0, 0.05, 1.00), (0.19, 0.150)),
        "belly": ((0, 0.012, 1.22), (0.195, 0.152)),
        "chest": ((0, -0.052, 1.45), (0.275, 0.165)),
        "shoulders": ((0, -0.07, 1.675), (0.355, 0.175)),
        "collar": ((0, -0.055, 1.83), (0.235, 0.135)),
    }
    torso_obj = cl.skin_body(kit, torso, [("crotch", "pelvis"), ("pelvis", "belly"), ("belly", "chest"),
                                          ("chest", "shoulders"), ("shoulders", "collar")],
                             TWILL, subdiv=2, name="coverall torso")

    # ---- arms (coverall sleeves) hang from inside the shoulder ends of the torso
    UPPER, FORE = 0.35, 0.41
    arm, arm_bones = {}, []
    wrists, elbows = {}, {}
    for s, sx, dz in (("l", 1, 0.0), ("r", -1, -0.01)):
        shoulder = V(0.285 * sx, -0.12, 1.70 + dz)
        wrist = V(0.32, -0.285, 1.02) if s == "l" else V(-0.325, -0.26, 1.03)
        elbow = ik(shoulder, wrist, UPPER, FORE, V(0.42 * sx, 1, 0))
        wrists[s], elbows[s] = wrist, elbow
        arm.update({"sh_" + s: (tuple(shoulder), 0.094), "elbow_" + s: (tuple(elbow), 0.074),
                    "fore_" + s: (tuple(lerp(elbow, wrist, 0.45)), 0.070),
                    "cinch_" + s: (tuple(lerp(elbow, wrist, 0.83)), 0.056),
                    "sleeve_" + s: (tuple(lerp(elbow, wrist, 0.93)), 0.062)})
        arm_bones += [("sh_" + s, "elbow_" + s), ("elbow_" + s, "fore_" + s), ("fore_" + s, "cinch_" + s),
                      ("cinch_" + s, "sleeve_" + s)]
    arms_obj = cl.skin_body(kit, arm, arm_bones, TWILL, subdiv=2, name="coverall arms")
    cl.decimate_to(arms_obj, 1500)

    # ---- gloves
    for s, sx in (("l", 1), ("r", -1)):
        e, w = elbows[s], wrists[s]
        d = (w - e).normalized().lerp(V(0, -0.1, -1).normalized(), 0.6)
        build_glove(kit, cl, lerp(e, w, 0.84), w, d, V(-1.0 * sx, 0.25, 0), "glove " + s)

    # ---- boots
    build_boot(kit, cl, fl, lerp(knee_l, fl["ankle"], 0.78), yaw_l, 0.0, "boot l")
    build_boot(kit, cl, fr, lerp(knee_r, fr["ankle"], 0.78), yaw_r, pitch_r, "boot r")

    # ---- hood + lens door
    H = V(0, -0.305, 1.635)
    hd = build_hood(kit, H, 18.0, (0.145, 0.155, 0.188), 0.4, (0.18, 0.25), 0.012, zc=0.01)
    lens_obj, hood, hood_c, HR = hd["lens"], hd["shell"], hd["centre"], hd["R"]

    # ---- tape cuffs (wrists, ankles): strips of the sleeve / trouser leg, pushed out
    bpy.context.view_layer.update()
    for s in ("l", "r"):
        e, w = elbows[s], wrists[s]
        ax = (w - e).normalized()
        c = lerp(e, w, 0.83)
        strip(kit, arms_obj, [(c + ax * 0.026, ax), (c - ax * 0.026, -ax)],
              lambda co, c=c, ax=ax: ((co - c) - ax * (co - c).dot(ax)).length < 0.11,
              0.003, 0.003, TAPE, name="tape wrist " + s)
        k = V(*legs["knee_" + s][0])
        a = (fl if s == "l" else fr)["ankle"]
        ax = (a - k).normalized()
        c = lerp(k, a, 0.80)
        strip(kit, legs_obj, [(c + ax * 0.026, ax), (c - ax * 0.026, -ax)],
              lambda co, c=c, ax=ax: ((co - c) - ax * (co - c).dot(ax)).length < 0.14,
              0.003, 0.003, TAPE, name="tape ankle " + s)

    # ---- drawcords: leave the hem at the opening's lower corners and lie on the chest
    # (a work hood, not a sealed suit), each ending in a metal aglet.
    for sx in (1, -1):
        corner = min(hd["hem"], key=lambda q: (HR.transposed() @ (q - hood_c) - V(sx * 0.10, 0, -0.17)).length)
        start = corner + HR @ V(-sx * 0.003, -0.006, 0)
        e_hit, e_nor = ray([torso_obj], V(start.x + sx * 0.018, -1.0, start.z - 0.15), V(0, 1, 0))
        end = e_hit + e_nor * 0.008
        m_hit, m_nor = ray([torso_obj], V((start.x + end.x) / 2, -1.0, start.z - 0.07), V(0, 1, 0))
        mid = m_hit + m_nor * 0.008
        mid = V(mid.x, min(mid.y, (start.y + end.y) / 2 - 0.004), mid.z)   # sag a little off the cloth
        kit.tube([start, mid, end], 0.0055, VINYL, verts=8, name="drawcord")
        tip = end + (end - mid).normalized() * 0.012
        kit.cylinder(0.0075, 0.026, tip, TAPE, verts=10, rot=deg(frame_z(end - mid)), name="aglet")

    # ---- hood centre seam (raised strip of the shell along x = 0, front edge to nape)
    strip(kit, hood, [(V(0.0045, 0, 0), V(1, 0, 0)), (V(-0.0045, 0, 0), V(-1, 0, 0))],
          lambda co: (HR.transposed() @ (co - hood_c)).z > -0.02 and (HR.transposed() @ (co - hood_c)).y > -0.02,
          0.0, 0.002, TWILL, name="hood seam")

    # ---- action back: a yoke seam across the shoulder blades and two pleats below it
    yz = 1.585
    strip(kit, torso_obj, [(V(0, 0, yz + 0.006), V(0, 0, 1)), (V(0, 0, yz - 0.006), V(0, 0, -1))],
          lambda co: co.y > 0.0, 0.0, 0.005, TWILL, name="back yoke seam")
    for px in (0.095, -0.095):
        strip(kit, torso_obj, [(V(px + 0.007, 0, 0), V(1, 0, 0)), (V(px - 0.007, 0, 0), V(-1, 0, 0))],
              lambda co: co.y > 0.0 and 1.29 < co.z < yz, 0.0, 0.006, TWILL, name="action pleat")

    # ---- coverall front: zip placket from the crotch to under the hood, two chest pocket flaps
    strip(kit, torso_obj, [(V(0.013, 0, 0), V(1, 0, 0)), (V(-0.013, 0, 0), V(-1, 0, 0))],
          lambda co: co.y < -0.05 and 0.97 < co.z < 1.56, 0.0, 0.005, TWILL, name="zip placket")
    for sx in (1, -1):
        x0, x1 = sorted((sx * 0.045, sx * 0.185))
        strip(kit, torso_obj, [(V(x1, 0, 0), V(1, 0, 0)), (V(x0, 0, 0), V(-1, 0, 0)),
                               (V(0, 0, 1.36), V(0, 0, 1)), (V(0, 0, 1.31), V(0, 0, -1))],
              lambda co: co.y < -0.05, 0.002, 0.008, TWILL, name="pocket flap")

    # ---- tool belt: a strip of the coverall round the waist, square to the torso axis
    p0, p1 = V(*torso["pelvis"][0]), V(*torso["belly"][0])
    ax = (p1 - p0).normalized()
    c = p0 + ax * 0.12
    strip(kit, torso_obj, [(c + ax * 0.03, ax), (c - ax * 0.03, -ax)], lambda co: True,
          0.004, 0.012, VINYL, name="tool belt")

    # ---- tool pouch on the right hip (hangs from the belt), two tool handles
    hit, nor = ray([torso_obj, legs_obj], V(-1.0, 0.02, c.z - 0.05), V(1, 0, 0))
    out = V(nor.x, nor.y, 0).normalized()
    up = V(0, 0, 1)
    side = up.cross(out).normalized()
    pc = hit + out * 0.045 - up * 0.045
    M = basis(out, side, up)
    kit.soft_box((0.08, 0.15, 0.19), pc, VINYL, radius=0.02, segments=16, rings=10, rot=deg(M), name="pouch")
    kit.soft_box((0.09, 0.158, 0.055), pc + out * 0.006 + up * 0.08, VINYL, radius=0.012, segments=12, rings=8,
                 rot=deg(M), name="pouch flap")
    for k, (o, tilt, r, ln) in enumerate(((-0.035, 8, 0.013, 0.10), (0.036, -12, 0.010, 0.09))):
        tp = pc + side * o + up * 0.125 + out * 0.005
        dirn = (up + side * math.tan(math.radians(tilt))).normalized()
        kit.cylinder(r, ln, tp, VINYL, verts=12, rot=deg(frame_z(dirn)), name="tool handle %d" % k)

    # ---- key ring on the left hip
    hit, nor = ray([torso_obj, legs_obj], V(1.0, -0.04, c.z - 0.02), V(-1, 0, 0))
    out = V(nor.x, nor.y, 0).normalized()
    kc = hit + out * 0.012 - V(0, 0, 0.055)
    kit.box((0.012, 0.02, 0.05), hit + out * 0.006 - V(0, 0, 0.015), TAPE, rot=deg(frame_z(V(0, 0, 1), out)),
            name="key clip")
    tang = out.cross(V(0, 0, 1)).normalized()
    ring_pts = [kc + (V(0, 0, 1) * math.cos(a) + tang * math.sin(a)) * 0.024
                for a in [2 * math.pi * i / 16 for i in range(16)]]
    loop_tube(kit, ring_pts, 0.0028, TAPE, out, verts=4, name="key ring")
    for k, ang in enumerate((-25, 0, 20)):
        dirn = (V(0, 0, -1) + tang * math.tan(math.radians(ang))).normalized()
        kit.box((0.016, 0.003, 0.05), kc + dirn * 0.045, TAPE, bevel=0.001,
                rot=deg(frame_z(-dirn, tang)), name="key %d" % k)

    # ---- blank oval name patch on the left chest, below the hood
    hit, nor = ray([torso_obj], V(0.15, -1.0, 1.415), V(0, 1, 0))
    patch = kit.cylinder(0.044, 0.004, hit + nor * 0.002, WHITE, verts=24, rot=deg(frame_z(nor, V(1, 0, 0))),
                         name="name patch")
    patch.scale = (1.0, 0.58, 1.0)

    # ---- diagnostics: the rim's lower edge must stand clear of the chest
    R = Euler((math.radians(18.0), 0, 0)).to_matrix()
    rim_lo = H + R @ V(0, 0.04, -0.137)
    t_hit, _ = ray([torso_obj], V(0, -1.0, rim_lo.z), V(0, 1, 0))
    print("[nightshift] rim bottom y %.3f z %.3f, chest front y %.3f (clearance %.3f)" % (
        rim_lo.y, rim_lo.z, t_hit.y, t_hit.y - rim_lo.y))

    # ---- finish
    lens_z = lens_obj.location.z
    lo = cl.floor_parts(kit)
    EYE = round(lens_z - lo, 3)
    kit.no_collider()
    if LENS_GLOW > 0:
        lens_glow(kit, LENS_GLOW)
    total = sum(tris(o) for o in kit.parts)
    bpy.context.view_layer.update()
    ws = [o.matrix_world @ v.co for o in kit.parts for v in o.data.vertices]
    front = max(-w.y for w in ws if w.z > 1.0)
    radial = max(math.hypot(w.x, w.y) for w in ws if 0.4 <= w.z <= 1.95)
    back = max(w.y for w in ws if 0.4 <= w.z <= 1.95)
    print("[nightshift] front above 1 m %.3f, probe radial %.3f, back 0.4-1.95 %.3f" % (front, radial, back))
    print("[nightshift] parts %d, tris (pre-modifier) %d, floor shift %.3f, eye %.3f" % (len(kit.parts), total, lo, EYE))


# DESIGN (what changed from §7.3 and why; full notes in the Figma hand-off)
# * Shrug: §7.3's trap joints on the arm chain read as arms arching out of the neck; the
#   trapezius is now the torso's wide shoulder section + collar (rx 0.355 / 0.235).
# * Hood: §7.3's 0.235 m ellipsoid with a 0.25 m flat rim in front read as a pasted screen
#   (the spec's own TV-head risk). It is now a 0.29 x 0.38 m cut-open hood with a parka peak,
#   a rolled hem whose sides and chin recede behind the brim, hanging drawcords, and the lens
#   door set 4 cm deep in the opening: a light inside a hood, not a box.
# * Lens 0.18 x 0.25 m (spec 0.21 x 0.28) so the dark hood frames it on all sides.
# * Lens door and name patch both Prop_PlasticWhite; key ring and aglets Creature_TapeSilver
#   instead of Prop_Brass / Prop_Paper, to stay at 6 material slots.
# * Coverall read added: zip placket, chest pocket flaps, action-back yoke seam and pleats,
#   sleeves and trouser legs cinched by the tape and bloused below it.
# * Legs solved by IK to the boots (thigh 0.48, shin 0.44) so both knees stay soft; the
#   trailing heel is raised 14 deg with the toe flat.
