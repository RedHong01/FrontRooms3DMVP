"""Budget modelling helpers for the new-casegoods group (NOT an asset module).

Used by display_cabinet, bookcase, ply_cabinet, hutch, credenza, dresser_low.
Case goods have to read as real 1970s-90s furniture at 2-4 m under flat top
light inside 500-2,000 triangles, so every helper here spends triangles only
where the light catches:

* plate()     a board or front whose FRONT face edges are moulded by a list
              of (inset, height) steps. A chamfered board is 20 tris, an ogee
              front 28-36, a frame-and-raised-panel door in one piece ~52
              (kit.box with a 1-segment bevel is 44, 2 segments 108).
* sweep()     a closed moulding section swept along a polyline with mitred
              corners: crown and base mouldings round three sides, door and
              side frames as a closed ring (optionally one part per member,
              so each member keeps its own grain and the mitre joint reads).
* bail_pull() brass bail pull: oval backplate, two post nuts, a diamond-
              section wire bail that slopes off the plate (86-102 tris).
* knob()      brass mushroom knob, 12-sided lathe open at the base, 82 tris.
* knuckle()   hinge barrel, 6-sided, 20 tris.
* ply_edge()  a cut plywood edge as one quad whose UVs squeeze the scan
              across the 18 mm thickness so its grain streaks read as plies.
* shadow()    dark quad behind shut lines, so drawer and door reveals read as
              lines under flat top light (2 tris for the whole front).
* label()     one cropped Prop_Label atlas cell (maker's label, asset tag).
* scatter()   per-part uv offsets so neighbouring boards don't share grain.
* lod1_sharp() re-split LOD1 normals after kitlib's collapse decimation.
* tri()       triangulate concave extrude caps up front.

Conventions as kitlib: metres, Z up, front -Y, stands on z = 0.
"""

import math
import random

import bmesh
from mathutils import Vector

# facing -> (U, V, N): U right and V up as seen by a viewer on the +N side.
FACING = {
    "-y": ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
    "+y": ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "+z": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "-z": ((1, 0, 0), (0, -1, 0), (0, 0, -1)),
    "-x": ((0, -1, 0), (0, 0, 1), (-1, 0, 0)),
    "+x": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
}

# The wood scans in Assets/Resources/Surfaces/Textures run their grain along
# texture U (horizontal in the image). ply_edge() lays U along the edge so the
# streaks run along it; flip this if the scans are ever rotated to V.
TEX_GRAIN_ALONG_U = True


def _axes(facing):
    u, v, n = FACING[facing]
    return Vector(u), Vector(v), Vector(n)


def _orient(face, want):
    face.normal_update()
    if face.normal.dot(Vector(want)) < 0:
        face.normal_flip()


def _emit(kit, bm, slot, name, loc=(0, 0, 0), grain=None, closed=True, tri=False, uv="metres"):
    if closed:
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if tri:
        ngons = [f for f in bm.faces if len(f.verts) > 4]
        if ngons:
            bmesh.ops.triangulate(bm, faces=ngons, quad_method="BEAUTY", ngon_method="BEAUTY")
    obj = kit._new_object(name, bm, slot, uv, "xz")
    obj.location = loc
    if grain:
        obj["fr_grain"] = grain
    return obj


def tri(obj):
    """Triangulate a kit part's n-gons (concave extrude caps) up front, so
    Unity's importer never has to guess."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons, quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(obj.data)
    bm.free()
    return obj


# ---------------------------------------------------------------- plates
def plate(kit, w, h, steps, loc, slot, facing="-y", name="plate", grain=None):
    """Board of w (along U) x h (along V), its back face centred on ``loc``,
    built out along N (see FACING) through ``steps``: (inset, height) or
    (inset_u, inset_v, height) rings from the back face (height 0) to the
    front face. The front face is the last ring. 8 tris per step + 4."""
    u, v, n = _axes(facing)
    bm = bmesh.new()
    rings = []
    for st in steps:
        iu, iv, d = (st[0], st[0], st[1]) if len(st) == 2 else st
        hw, hh = w / 2 - iu, h / 2 - iv
        rings.append([bm.verts.new(u * a + v * b + n * d) for a, b in ((-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh))])
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bm.faces.new(rings[-1])
    bm.faces.new(list(reversed(rings[0])))
    return _emit(kit, bm, slot, name, loc, grain)


def chamfer(t, c=0.003):
    """Square board, front arrises chamfered 45 degrees (20 tris)."""
    return [(0, 0), (0, t - c), (c, t)]


def eased(t, c=0.0025):
    """Both faces' arrises chamfered (a loose board seen from both sides)."""
    return [(c, 0), (0, c), (0, t - c), (c, t)]


def rounded(t, r=0.006):
    """Front arris rounded (3 x 30 degree facets, shades smooth at 40)."""
    pts = [(0, 0)]
    for k in range(4):
        a = math.radians(30 * k)
        pts.append((r - r * math.cos(a), t - r + r * math.sin(a)))
    return pts


def ogee(t, r=0.008):
    """Classic routed ogee: a cove into a bead, ending on a narrow flat."""
    s = t - r
    return [(0, 0), (0, s), (r * 0.15, s + r * 0.45), (r * 0.45, s + r * 0.62), (r * 0.75, s + r * 0.80),
            (r * 0.95, t)]


def raised_panel(t, rail=0.058, field=0.022, edge=0.004, drop=0.005):
    """Frame-and-raised-panel door in one plate: eased outer edge, a flat
    frame band ``rail`` wide, a quirk dropping ``drop``, then the panel's
    bevelled field rising back to the face over ``field``."""
    return [(0, 0), (0, t - edge), (edge, t), (rail, t), (rail + 0.003, t - drop),
            (rail + field, t - 0.001), (rail + field + 0.004, t)]


def routed(t, border=0.045, edge=0.004, groove=0.006, depth=0.003):
    """Flat slab with an eased edge and a routed V-groove border."""
    return [(0, 0), (0, t - edge), (edge, t), (border, t), (border + groove / 2, t - depth), (border + groove, t)]


# ---------------------------------------------------------------- sweeps
def sweep(kit, path, profile, slot, facing="+z", origin=(0, 0, 0), closed=False, split=False,
          name="moulding", grain=None):
    """Sweep the closed section ``profile`` [(o, h), ...] along ``path``
    [(pu, pv), ...]. Points land at origin + U*pu + V*pv + (mitre * o) + N*h
    (U, V, N from FACING). ``o`` is the offset to the RIGHT of travel, so run
    the path counter-clockwise as seen from the +N side and o points outward.
    closed: the path loops (a frame). split: one part per path segment, each
    capped on its mitre plane (own grain direction and uv offset; the joint
    line reads like a real mitre). Open paths get end caps."""
    U, V, N = _axes(facing)
    O = Vector(origin)
    P = [Vector((a, b)) for a, b in path]
    n = len(P)
    nseg = n if closed else n - 1
    nrm = []
    for k in range(nseg):
        d = (P[(k + 1) % n] - P[k]).normalized()
        nrm.append(Vector((d.y, -d.x)))

    def mitre(k):
        if closed:
            a, b = nrm[(k - 1) % nseg], nrm[k % nseg]
        elif k == 0:
            return nrm[0].copy()
        elif k == n - 1:
            return nrm[-1].copy()
        else:
            a, b = nrm[k - 1], nrm[k]
        return (a + b) / (1 + a.dot(b))

    M = [mitre(k) for k in range(n)]

    def ring(bm, k):
        out = []
        for o, h in profile:
            p = P[k] + M[k] * o
            out.append(bm.verts.new(O + U * p.x + V * p.y + N * h))
        return out

    def bridge(bm, r0, r1):
        m = len(profile)
        for i in range(m):
            j = (i + 1) % m
            bm.faces.new((r0[i], r1[i], r1[j], r0[j]))

    parts = []
    if split:
        for k in range(nseg):
            bm = bmesh.new()
            r0, r1 = ring(bm, k), ring(bm, (k + 1) % n)
            bridge(bm, r0, r1)
            bm.faces.new(r0)
            bm.faces.new(r1)
            obj = _emit(kit, bm, slot, name, grain=grain, tri=True)
            parts.append(obj)
        return parts
    bm = bmesh.new()
    rings = [ring(bm, k) for k in range(n)]
    for k in range(nseg):
        bridge(bm, rings[k], rings[(k + 1) % n])
    if not closed:
        bm.faces.new(rings[0])
        bm.faces.new(rings[-1])
    return [_emit(kit, bm, slot, name, grain=grain, tri=True)]


def rect_path(x0, x1, y0, y1):
    """Counter-clockwise rectangle (as seen from the facing's +N side)."""
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def three_sides(hw, y_front, y_back):
    """Plan path round the left side, front and right side (CCW from above):
    for crown and base mouldings on a piece that stands against a wall."""
    return [(-hw, y_back), (-hw, y_front), (hw, y_front), (hw, y_back)]


def cove(depth, height, n=3, back=0.004):
    """Concave cove section (o out, h up) for a crown under an overhang."""
    pts = []
    for k in range(n + 1):
        a = math.pi - (math.pi / 2) * k / n
        pts.append((depth + depth * math.cos(a), height * math.sin(a)))
    return pts + [(-back, height), (-back, 0)]


# --------------------------------------------------------------- hardware
def _flat(kit, outline, y, slot, name, want=(0, -1, 0)):
    """One-sided flat n-gon in the XZ plane at depth y (backplates)."""
    bm = bmesh.new()
    verts = [bm.verts.new((x, y, z)) for x, z in outline]
    face = bm.faces.new(verts)
    _orient(face, want)
    bmesh.ops.triangulate(bm, faces=[face], quad_method="BEAUTY", ngon_method="BEAUTY")
    return _emit(kit, bm, slot, name, closed=False)


def bail_pull(kit, x, z, y_face, slot="Prop_Brass", span=0.076, drop=0.022, plate_h=0.034, vertical=False,
              post_verts=6, plate_w=None):
    """Brass bail pull: oval stamped backplate 0.8 mm proud of the face, two
    post nuts standing 9 mm off it and a diamond-section wire bail hanging
    from them, its foot resting on the plate (so it slopes and catches the
    top light: it reads as a separate wire, not part of the plate).
    Plate 10 tris + bail 52 + posts (20 each at 6 sides, 12 at 4).
    vertical=True turns it 90 degrees (for door stiles)."""
    def tf(dx, dz):
        return (x + dz, z - dx) if vertical else (x + dx, z + dz)
    a = (plate_w or span + 0.026) / 2
    b = plate_h / 2
    oval = [tf(a * math.cos(2 * math.pi * k / 12), b * math.sin(2 * math.pi * k / 12)) for k in range(12)]
    _flat(kit, oval, y_face - 0.0008, slot, "pull backplate")
    hx, z0 = span / 2, 0.005
    w, t = 0.0050, 0.0036                    # wire section (radial, depth)
    y_top, y_foot = y_face - 0.0098, y_face - 0.0008 - t / 2
    bm = bmesh.new()
    rings = []
    n = 6
    for k in range(n + 1):
        th = math.pi + math.pi * k / n
        c, sn = math.cos(th), math.sin(th)
        # radial unit in the bail plane (ellipse normal approximation)
        rx, rz = c / max(hx, 1e-6), sn / max(drop, 1e-6)
        ln = math.hypot(rx, rz)
        rx, rz = rx / ln, rz / ln
        px, pz = hx * c, z0 + drop * sn
        f = -sn                               # 0 at the posts, 1 at the foot
        yc = y_top + (y_foot - y_top) * f
        ring = []
        for dr, dy in ((w / 2, 0), (0, -t / 2), (-w / 2, 0), (0, t / 2)):
            gx, gz = tf(px + rx * dr, pz + rz * dr)
            ring.append(bm.verts.new((gx, yc + dy, gz)))
        rings.append(ring)
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((r0[i], r0[j], r1[j], r1[i]))
    bm.faces.new(rings[0])
    bm.faces.new(list(reversed(rings[-1])))
    _emit(kit, bm, slot, "pull bail")
    for sx in (-1, 1):
        px, pz = tf(sx * hx, z0)
        kit.cylinder(0.0040, 0.0095, (px, y_face - 0.0008 - 0.00475, pz), slot, verts=post_verts, rot=(90, 0, 0),
                     bevel=0.0, name="pull post")


def knob(kit, x, z, y_face, slot="Prop_Brass", scale=1.0, verts=12):
    """Brass mushroom knob, axis along -Y, open at the base (82 tris at 12 sides)."""
    s = scale
    prof = [(0.009 * s, 0.0), (0.0055 * s, 0.009 * s), (0.0125 * s, 0.021 * s), (0.0075 * s, 0.028 * s)]
    return kit.lathe(prof, (x, y_face, z), slot, verts=verts, rot=(90, 0, 0), name="knob", close_bottom=False)


def knuckle(kit, x, y, z, length, slot="Prop_Brass", radius=0.0042):
    """Butt-hinge barrel, vertical, 6-sided (20 tris)."""
    return kit.cylinder(radius, length, (x, y, z), slot, verts=6, bevel=0.0, name="hinge knuckle")


# ---------------------------------------------------------------- surfaces
def ply_edge(kit, centre, normal, along, length, thick, slot="Prop_Plywood", rng=None, proud=0.0003,
             squeeze=0.065, name="ply edge"):
    """Cover a cut plywood edge with one quad facing ``normal`` (outward unit
    axis), ``length`` along ``along`` and ``thick`` across. UVs (uv="keep")
    run the scan's grain along the edge in metres and squeeze ``squeeze``
    metres of the scan into the thickness, so its streaks read as 5-7 plies
    (texture-filtered, so it holds up at 4 m where 3 mm geometry would alias)."""
    rng = rng or random.Random(1)
    nrm, al = Vector(normal).normalized(), Vector(along).normalized()
    ac = nrm.cross(al).normalized()
    c = Vector(centre) + nrm * proud
    hl, ht = length / 2, thick / 2
    du, dv = rng.uniform(0, 1), rng.uniform(0, 1)
    bm = bmesh.new()
    layer = bm.loops.layers.uv.verify()
    verts = [bm.verts.new(c + al * a + ac * b) for a, b in ((-hl, -ht), (hl, -ht), (hl, ht), (-hl, ht))]
    face = bm.faces.new(verts)
    _orient(face, nrm)
    for loop in face.loops:
        p = loop.vert.co - c
        s_, t = p.dot(al), (p.dot(ac) + ht) / thick
        if TEX_GRAIN_ALONG_U:
            loop[layer].uv = (s_ + du, t * squeeze + dv)
        else:
            loop[layer].uv = (t * squeeze + du, s_ + dv)
    return _emit(kit, bm, slot, name, closed=False, uv="keep")


def shadow(kit, w, h, loc, slot, facing="-y", name="reveal shadow"):
    """Dark quad behind the shut lines of a bank of fronts."""
    return kit.quad(w, h, loc, slot, facing=facing, uv="metres", name=name)


def label(kit, cell, crop, w, h, loc, facing="-y", name="label"):
    """Prop_Label 4x4 atlas cell ``cell`` cropped to ``crop`` = (x0, y0, x1,
    y1) fractions of the cell (top-down), on a w x h quad. Mirrored for
    +y / +x facings so the print reads the right way round."""
    u0, v0, u1, v1 = kit.atlas_cell(cell, 4, 4)
    x0, y0, x1, y1 = crop
    r = (u0 + (u1 - u0) * x0, v1 - (v1 - v0) * y1, u0 + (u1 - u0) * x1, v1 - (v1 - v0) * y0)
    if facing in ("+y", "+x"):
        r = (r[2], r[1], r[0], r[3])
    return kit.quad(w, h, loc, "Prop_Label", facing=facing, uv_rect=r, name=name)


MAKER_LABEL = (11, (0.085, 0.17, 0.92, 0.835))    # "MODEL 4417-B / MADE IN U.S.A. / QC 03/1979"
ASSET_TAG = (14, (0.075, 0.285, 0.93, 0.72))      # "ASSET 004193" + barcode


def scatter(kit, seed, slots):
    """Each wood part on its own patch of the scan."""
    rng = random.Random(seed)
    for obj in kit.parts:
        mats = obj.data.materials
        if not len(mats) or mats[0] is None or obj.get("fr_uv") == "keep":
            continue
        if mats[0].name.split(".")[0] in slots:
            obj["fr_uv_offset"] = (round(rng.uniform(0, 1), 4), round(rng.uniform(0, 1), 4))


def lod1_sharp(kit, smooth_angle):
    """On THIS Kit instance only (kitlib.py is not edited): after kitlib's
    collapse-decimated LOD1 is made, re-run the auto-smooth split. The
    decimator drops most sharp-edge flags, so LOD1 doors, tops and glass
    shade as one smeared smooth surface; re-splitting at the module's
    SMOOTH_ANGLE makes LOD1 match LOD0's flat faces."""
    orig = kit.make_lod1

    def make_lod1(ratio):
        orig(ratio)
        lod1 = getattr(kit, "lod1", None)
        if lod1 is not None:
            lod1.data.shade_smooth()
            lod1.data.set_sharp_from_angle(angle=math.radians(smooth_angle))

    kit.make_lod1 = make_lod1
