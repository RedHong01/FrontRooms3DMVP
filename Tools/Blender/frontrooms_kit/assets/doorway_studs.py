"""Unfinished stud doorway (the raw framed opening outlined in blue
painter's tape beside the low pile in A24 "Backrooms" Still A).

Real-world reference: a rough door opening framed in kiln-dried SPF 2x4s
(38 mm faces, eased 3 mm edges), the way a framing crew leaves it before
drywall: a sill (bottom) plate still running through the opening, a king
stud each side running plate to plate, a jack (trimmer) stud inside each
king carrying a doubled header (two 2x6 plies on edge with a spacer), two
short cripple studs on the 16-inch layout above the header, and a doubled
top plate. Somebody has outlined the opening on the room side with 48 mm
blue painter's tape: one strip up each jamb, one along the underside of the
header, one along the sill, laid by hand (each a little off square, the
ends overlapping, one strip re-laid at the top corner).

Module: 1.20 m wide x 2.40 m tall x 0.14 m deep (a 4 x 8 ft framing module
that drops into a 0.16 m wall slot with 1 cm to spare each side, so the
members are 140 mm deep: 2x4 faces at the slot's depth). Clear opening
1.048 m x 2.03 m (header underside). Origin = bottom centre, room side -Y.
Budget 800 tris LOD0 / 300 LOD1. Slots: Studs, TapeBlue.
Colliders: one per stud pair (king + jack each side) and one for the
header assembly; the sill plate stays walkable (38 mm).
"""

import math
import random

import bmesh
from mathutils import Vector

NAME = "Kit_DoorwayStuds"
LOD1 = 0.42
SMOOTH_ANGLE = 35.0

STUD = "Prop_Studs"
TAPE = "Prop_TapeBlue"

W, H, D = 1.20, 2.40, 0.14
T = 0.038                      # 2x face
EASE = 0.003                   # eased edge of dimensional lumber
HEADER_Z0 = 2.032              # underside of the header (80-inch rough opening)
HEADER_H = 0.140               # 2x6 on edge
TOP_Z0 = H - 2 * T             # underside of the doubled top plate
TAPE_W = 0.048
TAPE_Y = -D / 2 - 0.0008       # tape plane, just proud of the room-side faces


def _board(kit, size, loc, name, grain):
    obj = kit.box(size, loc, STUD, bevel=EASE, segments=1, name=name)
    obj["fr_grain"] = grain
    return obj


def _tape(kit, length, centre, angle_deg, name, rng, facing="-y", lift=0.0, torn=(True, True)):
    """A hand-laid strip of 48 mm painter's tape with torn ends.

    facing "-y": on the room-side faces; the strip runs along Z, centred at
    centre = (x, z), turned angle_deg about Y. facing "+z": on the sill top;
    it runs along X, centred at centre = (x, y), turned about Z."""
    hw, hl = TAPE_W / 2, length / 2
    def end(v0, sign, ragged):
        if not ragged:
            return [(-hw * sign, v0), (hw * sign, v0)]
        pts = []
        for i in range(6):
            u = -hw + TAPE_W * i / 5
            pts.append((u * sign, v0 + sign * rng.uniform(-0.004, 0.003)))
        return pts
    outline = end(-hl, 1, torn[0]) + end(hl, -1, torn[1])     # CCW: bottom L->R, top R->L
    a = math.radians(angle_deg)
    c, s_ = math.cos(a), math.sin(a)
    if facing == "-y":
        y = TAPE_Y - lift
        verts = [(centre[0] + u * c + v * s_, y, centre[1] - u * s_ + v * c) for u, v in outline]
        want = Vector((0, -1, 0))
    else:
        z = T + 0.0008 + lift
        verts = [(centre[0] + v * c - u * s_, centre[1] + v * s_ + u * c, z) for u, v in outline]
        want = Vector((0, 0, 1))
    bm = bmesh.new()
    face = bm.faces.new([bm.verts.new(p) for p in verts])
    face.normal_update()
    if face.normal.dot(want) < 0:
        face.normal_flip()
    return kit._new_object(name, bm, TAPE, "metres", "xz")


def build(kit):
    rng = random.Random(2400)
    xk = W / 2 - T / 2                 # king stud centre
    xj = W / 2 - T - T / 2             # jack stud centre
    x_open = W / 2 - 2 * T             # half the clear opening

    # Plates.
    _board(kit, (W, D, T), (0, 0, T / 2), "sill plate", "x")
    _board(kit, (W, D, T), (0, 0, TOP_Z0 + T / 2), "top plate", "x")
    _board(kit, (W, D, T), (0, 0, TOP_Z0 + 1.5 * T), "top plate cap", "x")

    # King studs (plate to plate) and jack studs (sill to header).
    for sx in (-1, 1):
        _board(kit, (T, D, TOP_Z0 - T), (sx * xk, 0, T + (TOP_Z0 - T) / 2), "king stud", "z")
        _board(kit, (T, D, HEADER_Z0 - T), (sx * xj, 0, T + (HEADER_Z0 - T) / 2), "jack stud", "z")

    # Doubled header: two 2x6 plies on edge at the faces, a spacer between
    # (set 6 mm up so the underside shows the lamination).
    hl = W - 2 * T
    hz = HEADER_Z0 + HEADER_H / 2
    for sy in (-1, 1):
        _board(kit, (hl, T, HEADER_H), (0, sy * (D / 2 - T / 2), hz), "header ply", "x")
    kit.box((hl - 0.004, D - 2 * T + 0.002, HEADER_H - 0.012), (0, 0, hz), STUD, bevel=0.0, name="header spacer")

    # Cripple studs on the 16-inch layout from the module's left end.
    zc0, zc1 = HEADER_Z0 + HEADER_H, TOP_Z0
    for x in (-W / 2 + 0.406, -W / 2 + 0.812):
        _board(kit, (T, D, zc1 - zc0), (x, 0, (zc0 + zc1) / 2), "cripple stud", "z")

    # Each board on its own patch of grain.
    for obj in kit.parts:
        obj["fr_uv_offset"] = (round(rng.uniform(0, 0.5), 3), round(rng.uniform(0, 0.5), 3))

    # --- Blue painter's tape on the room side ---------------------------
    # Jamb strips on the jack + king faces (76 mm of wood for 48 mm of tape),
    # each laid a little off plumb: the inner edge touches the opening edge
    # at one end and wanders 25 mm off it at the other.
    jl = HEADER_Z0 + 0.03
    lean = 0.7
    swing = jl / 2 * math.sin(math.radians(lean))
    _tape(kit, jl, (-(x_open + TAPE_W / 2 + swing + 0.001), jl / 2), lean, "tape jamb left", rng, torn=(True, False))
    _tape(kit, jl - 0.014, (x_open + TAPE_W / 2 + swing * 0.8 + 0.001, (jl - 0.014) / 2 + 0.006), lean * 0.8,
          "tape jamb right", rng, torn=(True, False))
    # Header strip on the header face along its underside, ends lapping onto
    # the jamb strips (and slightly off level).
    _tape(kit, 2 * x_open + 0.12, (0.006, HEADER_Z0 + TAPE_W / 2 - 0.003), -89.6, "tape header", rng, lift=0.0004)
    # Re-laid corner: a short second piece over the top-left joint.
    _tape(kit, 0.17, (-x_open + 0.035, HEADER_Z0 + 0.016), 86.0, "tape patch", rng, lift=0.0008)
    # Sill strip: along the room-side edge of the sill plate, across the opening.
    _tape(kit, 2 * x_open + 0.03, (0.006, -D / 2 + TAPE_W / 2 + 0.005), 0.6, "tape sill", rng, facing="+z")

    # --- Metadata -------------------------------------------------------
    for sx in (-1, 1):
        kit.collider((sx * (xk + xj) / 2, 0, (TOP_Z0) / 2), (2 * T, D, TOP_Z0))
    kit.collider((0, 0, (HEADER_Z0 + H) / 2), (W - 4 * T, D, H - HEADER_Z0))
    kit.anchor("opening", (0, 0, 0))
    kit.anchor("header", (0, -D / 2, HEADER_Z0))
    kit.tag("arch", "wall_decor")
