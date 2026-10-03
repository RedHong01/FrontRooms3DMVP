"""Unfinished stud doorway (the raw framed opening outlined in blue
painter's tape beside the low pile in A24 "Backrooms" Still A).

Real-world reference: a rough opening in a non-bearing partition, framed in
kiln-dried SPF lumber (38 mm faces, eased 3 mm edges) the way a framing crew
leaves it before drywall: a sill (bottom) plate still running through the
opening, a king stud each side running plate to plate, a jack (trimmer)
stud inside each king carrying a doubled header (two 2x4 plies on edge with
a spacer, set tight under the single top plate, so no cripples). Somebody
has outlined the opening on the room side with 48 mm blue painter's tape:
one strip up each jamb, one along the header's lower edge, one along the
sill, laid by hand (each a little off square, ends overlapping, one strip
re-laid at the top corner).

Arch contract (LEVEL_MODULE_SPEC §3: arches 1.1-1.8 m wide, top 2.2 m; the
Relay walks at up to 2.05 m). The CLEAR passage is never narrower or lower
than the arch it dresses: CLEAR wide x 2.20 m (ArchTop) to the header's
underside; the 38 mm sill plate stays walkable (step 0.3). The framing sits
OUTSIDE the clear passage, so the wall's rough opening for this piece is
W = CLEAR + 4 x 0.038 (a king + jack each side) by H = 2.327 m (header 2.20
+ 0.089 + top plate 0.038), through the 0.16 m wall. Three widths, the map
snapping a stud arch to one of them:
  Kit_DoorwayStuds     clear 1.10 (ArchMinWidth)  outer 1.252
  Kit_DoorwayStuds140  clear 1.40                 outer 1.552
  Kit_DoorwayStuds180  clear 1.80 (ArchMaxWidth)  outer 1.952
Anchors clear_corner_a / _b are opposite corners of the clear box. The
map must keep the OUTER edge (0.076 past the clear edge) inside its 0.2 m
corner margin. H 2.327 keeps the sidecar minCeiling (top + 0.05) at 2.377,
under the 2.4 m Low ceiling. Not wired yet: the map chat has to agree the
snap + wider cut (no code places Kit_DoorwayStuds today).

Members are 140 mm deep (2x6 section) to fill the 0.16 m wall slot with
1 cm to spare each side (Red's call whether to go true 2x4 + blocking).
Origin = bottom centre, room side -Y. Budget 800 tris LOD0 / 300 LOD1.
Slots: Studs, TapeBlue. Colliders: one per stud pair (king + jack each
side) and one for the header assembly.
"""

import math
import random

import bmesh
from mathutils import Vector

NAME = "Kit_DoorwayStuds"
CLEAR = 1.10                   # clear passage width (ArchMinWidth)
LOD1 = 0.42
SMOOTH_ANGLE = 35.0

STUD = "Prop_Studs"
TAPE = "Prop_TapeBlue"

D = 0.14
T = 0.038                      # 2x face
EASE = 0.003                   # eased edge of dimensional lumber
HEADER_Z0 = 2.20               # underside of the header = ModuleUnits.ArchTop
HEADER_H = 0.089               # doubled 2x4 on edge
TOP_Z0 = HEADER_Z0 + HEADER_H  # single top plate sits on the header
H = TOP_Z0 + T                 # 2.327
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


def build_frame(kit, clear, seed=2400):
    rng = random.Random(seed)
    W = clear + 4 * T                  # outer width = the wall's rough opening
    xk = W / 2 - T / 2                 # king stud centre
    xj = W / 2 - T - T / 2             # jack stud centre
    x_open = clear / 2                 # half the clear passage

    # Plates.
    _board(kit, (W, D, T), (0, 0, T / 2), "sill plate", "x")
    _board(kit, (W, D, T), (0, 0, TOP_Z0 + T / 2), "top plate", "x")

    # King studs (plate to plate) and jack studs (sill to header).
    for sx in (-1, 1):
        _board(kit, (T, D, TOP_Z0 - T), (sx * xk, 0, T + (TOP_Z0 - T) / 2), "king stud", "z")
        _board(kit, (T, D, HEADER_Z0 - T), (sx * xj, 0, T + (HEADER_Z0 - T) / 2), "jack stud", "z")

    # Doubled header between the kings, on the jacks: two 2x4 plies on edge
    # at the faces and a spacer between, set 6 mm up so the underside shows
    # the lamination (eased like the rest: its edges show from below).
    hl = W - 2 * T
    hz = HEADER_Z0 + HEADER_H / 2
    for sy in (-1, 1):
        _board(kit, (hl, T, HEADER_H), (0, sy * (D / 2 - T / 2), hz), "header ply", "x")
    _board(kit, (hl - 0.004, D - 2 * T + 0.002, HEADER_H - 0.012), (0, 0, hz), "header spacer", "x")

    # Each board on its own patch of grain.
    for obj in kit.parts:
        obj["fr_uv_offset"] = (round(rng.uniform(0, 0.5), 3), round(rng.uniform(0, 0.5), 3))

    # --- Blue painter's tape on the room side ---------------------------
    # Jamb strips on the jack + king faces (76 mm of wood for 48 mm of tape),
    # each laid a little off plumb: the inner edge touches the opening edge
    # at one end and wanders ~25 mm off it at the other.
    jl = HEADER_Z0 + 0.03
    lean = 0.7
    swing = jl / 2 * math.sin(math.radians(lean))
    _tape(kit, jl, (-(x_open + TAPE_W / 2 + swing + 0.001), jl / 2 + 0.005), lean, "tape jamb left", rng, torn=(True, False))
    _tape(kit, jl - 0.014, (x_open + TAPE_W / 2 + swing * 0.8 + 0.001, (jl - 0.014) / 2 + 0.006), lean * 0.8,
          "tape jamb right", rng, torn=(True, False))
    # Header strip along the header's lower edge (kept on the face: 0.4 deg
    # off level over the span), its ends lapping onto the king faces.
    _tape(kit, 2 * x_open + 0.12, (0.006, HEADER_Z0 + TAPE_W / 2 + 0.005), -89.6, "tape header", rng, lift=0.0004)
    # Re-laid corner: a short second piece over the top-left joint.
    _tape(kit, 0.17, (-x_open + 0.035, HEADER_Z0 + 0.020), 86.0, "tape patch", rng, lift=0.0008)
    # Sill strip: along the room-side edge of the sill plate, across the opening.
    _tape(kit, 2 * x_open + 0.03, (0.006, -D / 2 + TAPE_W / 2 + 0.005), 0.6, "tape sill", rng, facing="+z")

    # --- Metadata -------------------------------------------------------
    for sx in (-1, 1):
        kit.collider((sx * (xk + xj) / 2, 0, H / 2), (2 * T, D, H))
    kit.collider((0, 0, (HEADER_Z0 + H) / 2), (clear, D, H - HEADER_Z0))
    kit.anchor("opening", (0, 0, 0))
    kit.anchor("header", (0, -D / 2, HEADER_Z0))
    # Opposite corners of the clear passage box (take min / max per axis).
    kit.anchor("clear_corner_a", (-x_open, -D / 2, 0))
    kit.anchor("clear_corner_b", (x_open, D / 2, HEADER_Z0))
    kit.tag("arch", "wall_decor")


def build(kit):
    build_frame(kit, CLEAR)
