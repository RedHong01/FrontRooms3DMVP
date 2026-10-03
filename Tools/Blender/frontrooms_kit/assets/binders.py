"""A row of five 3-ring binders standing spine-out, c. 1985-2000: vinyl-
over-board and cloth-covered D-ring binders with rolled hinge edges, a typed
spine insert or card, the page block (punched sheets plus taller sheet
protectors) showing between the covers, index tabs on some, and the last
binder leaning on its neighbour.

Real-world reference size per binder: 0.29 m tall x 0.27 m deep, spines
40-60 mm (1"-2" rings). Row about 0.33 m long. Origin = shelf / desk
surface under the middle of the row. Spines (front) look -Y.

Budget (round-2 table): 500 tris, desk-top clutter (no collider), pile
Small 0, <= 4 slots: Vinyl and FabricTeal covers, Paper (pages and index
tabs), Label (atlas: spine inserts 8 / 9, typed cards 4 / 6 / 7). Each
binder's covers and spine are ONE U-section prism (the rolled hinge edges
are 3-step arcs in the section, with analytic custom normals so the flat
spine and covers shade flat); nothing under ~5 mm is modelled (the weld
seams, the ring mechanism and the label pocket rims were sub-pixel at 2 m).
"""

import math
import random

import bmesh
from mathutils import Matrix, Vector

import _storage_labels as labels

NAME = "Kit_Binders"
SMOOTH_ANGLE = 50.0

PAPER = "Prop_Paper"
VINYL = "Prop_Vinyl"
CLOTH = "Prop_FabricTeal"

H, D = 0.29, 0.27
COVER_T = 0.0032
ROLL_R = 0.004             # rolled hinge edge radius

# (spine width, cover slot, page fill, index tabs, label (atlas cell, portrait insert?))
ROW = [
    (0.050, VINYL, 0.92, 0, (8, True)),     # "Q3 REPORTS" insert
    (0.045, CLOTH, 0.80, 3, (6, False)),    # "PAYROLL" card
    (0.060, VINYL, 0.95, 0, (9, True)),     # "MINUTES" insert
    (0.040, VINYL, 0.70, 2, (4, False)),    # "1989" card
]
LEANER = (0.050, CLOTH, 0.85, 0, (7, False))   # "MISC" card
LEAN_DEG = 9.0
GAP = 0.004          # between upright binders (their yaw jitter is +/-0.5 deg)


def section_prism(kit, outline, height, slot, name="section"):
    """Extrude a closed (x, y, normal) outline from z = 0 to ``height`` with a
    lid and no floor. normal = (nx, ny) gives that vertex an exact smooth
    normal (points on an arc); None makes it a crisp corner. Faces are smooth
    and the crisp edges are marked sharp, so finish() keeps the custom normals
    in the fans they were encoded in."""
    area = sum(outline[i][0] * outline[(i + 1) % len(outline)][1] - outline[(i + 1) % len(outline)][0] * outline[i][1]
               for i in range(len(outline)))
    pts = outline if area > 0 else list(reversed(outline))
    n = len(pts)
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, 0.0)) for x, y, _ in pts]
    hi = [bm.verts.new((x, y, height)) for x, y, _ in pts]
    lid = bm.faces.new(hi)
    walls = []
    for i in range(n):
        j = (i + 1) % n
        walls.append(bm.faces.new((lo[i], lo[j], hi[j], hi[i])))
    for f in bm.faces:
        f.smooth = True
    for e in lid.edges:
        e.smooth = False
    for i, (_, _, nrm) in enumerate(pts):
        if nrm is None:
            e = bm.edges.get((lo[i], hi[i]))
            if e is not None:
                e.smooth = False
    normals = []
    for f in bm.faces:
        for loop in f.loops:
            if f is lid:
                normals.append((0.0, 0.0, 1.0))
                continue
            i = walls.index(f)
            k = lo.index(loop.vert) if loop.vert in lo else hi.index(loop.vert)
            nrm = pts[k][2]
            if nrm is None:
                a, b = pts[i], pts[(i + 1) % n]
                d = Vector((b[0] - a[0], b[1] - a[1])).normalized()
                normals.append((d.y, -d.x, 0.0))
            else:
                normals.append((nrm[0], nrm[1], 0.0))
    obj = kit._new_object(name, bm, slot, "metres", "xz")
    obj.data.normals_split_custom_set(normals)
    return obj


def box_prism(kit, size, centre, slot, name="block"):
    """Lidded box without a floor (it stands on something): 10 tris."""
    sx, sy, sz = size
    pts = [(-sx / 2, -sy / 2, None), (sx / 2, -sy / 2, None), (sx / 2, sy / 2, None), (-sx / 2, sy / 2, None)]
    obj = section_prism(kit, pts, sz, slot, name=name)
    obj.location = (centre[0], centre[1], centre[2] - sz / 2)
    return obj


def _xform(parts, m):
    for obj in parts:
        obj.matrix_basis = m @ obj.matrix_basis


def binder(kit, w, slot, fill, tabs, label, seed):
    """One binder in local space: spine on the -Y face, x centred, z from 0.
    Returns the parts so the caller can place / lean it."""
    first = len(kit.parts)
    rng = random.Random(seed)
    hw = w / 2
    y0, y1 = -D / 2, D / 2
    t, r = COVER_T, ROLL_R
    # U section: left cover, rolled hinge, spine, rolled hinge, right cover.
    sec = [(-hw, y1, None)]
    for a in (180, 210, 240, 270):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        sec.append((-hw + r + r * c, y0 + r + r * s, (c, s)))
    for a in (270, 300, 330, 360):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        sec.append((hw - r + r * c, y0 + r + r * s, (c, s)))
    sec += [(hw, y1, None), (hw - t, y1, None), (hw - t, y0 + t, None), (-hw + t, y0 + t, None), (-hw + t, y1, None)]
    section_prism(kit, sec, H, slot, name="covers")
    # Page block leaning on the left cover: punched letter sheets, then a
    # few sheet protectors, wider and taller, standing proud of the paper.
    inner = w - 2 * t - 0.001
    pw = inner * fill
    bx = -hw + t + 0.0005
    sheets_w = pw * 0.72
    box_prism(kit, (sheets_w, 0.226, 0.279), (bx + sheets_w / 2, y0 + 0.137 + rng.uniform(-0.002, 0.002), 0.0045 + 0.1395),
              PAPER, name="punched sheets")
    prot_w = pw - sheets_w
    box_prism(kit, (prot_w * 0.95, 0.232, 0.284), (bx + sheets_w + prot_w / 2, y0 + 0.138, 0.0035 + 0.142),
              PAPER, name="sheet protectors")
    # Index tabs on dividers, standing 12 mm proud of the fore-edge.
    for k in range(tabs):
        tz = 0.06 + k * 0.07 + rng.uniform(-0.01, 0.01)
        box_prism(kit, (0.0012, 0.014, 0.038), (bx + rng.uniform(0.15, 0.85) * sheets_w, y0 + 0.255, tz), PAPER,
                  name="index tab")
    # Typed spine label, upper third: a portrait insert fills the window,
    # a typed card sits across the spine.
    cell, portrait = label
    lz = 0.205
    if portrait:
        lw = w - 0.016
        labels.card(kit, cell, lw, lw / 0.394, (0, y0 - 0.0004, lz), crop=False, name="spine insert")
    else:
        lw = min(0.034, w - 0.012)
        labels.card(kit, cell, lw, lw / 2.4, (0, y0 - 0.0004, lz), name="spine card")
    return kit.parts[first:]


def build(kit):
    rng = random.Random(4)
    x = 0.0
    placed = []
    for i, (w, slot, fill, tabs, label) in enumerate(ROW):
        parts = binder(kit, w, slot, fill, tabs, label, seed=10 + i)
        cx = x + w / 2
        yaw = rng.uniform(-0.5, 0.5)
        if i == len(ROW) - 1:
            yaw = 0.0                     # the leaner rests on this one's cover
        m = Matrix.Translation((cx, rng.uniform(-0.006, 0.006), 0)) @ Matrix.Rotation(math.radians(yaw), 4, "Z")
        placed.append((parts, m))
        x += w + GAP
    # The last binder has slipped over: it stands on its inner bottom edge
    # (the outer one lifted) with its top corner resting on the neighbour.
    w, slot, fill, tabs, label = LEANER
    tl = math.radians(LEAN_DEG)
    row_end = x - GAP
    pivot_x = row_end + H * math.sin(tl) + 0.001
    parts = binder(kit, w, slot, fill, tabs, label, seed=20)
    m = (Matrix.Translation((pivot_x, 0.004, 0)) @ Matrix.Rotation(-tl, 4, "Y") @ Matrix.Translation((w / 2, 0, 0)))
    placed.append((parts, m))
    # Centre the row on x = 0.
    length = pivot_x + w * math.cos(tl)
    shift = Matrix.Translation((-length / 2, 0, 0))
    for parts, m in placed:
        _xform(parts, shift @ m)

    kit.anchor("row_start", (-length / 2, -D / 2, 0))
    kit.no_collider()
    kit.tag("office", "desk_top")
    # Upright only: laid on its side the leaning binder would hang in the air.
    kit.pile("Small", mass=0, states=["Upright"])
