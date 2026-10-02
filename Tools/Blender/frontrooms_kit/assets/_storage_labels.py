"""Prop_Label atlas helper for the storage group (filing cabinet, binders,
paper stack). Not an asset: it has no NAME/build.

Assets/Resources/Surfaces/Textures/Prop_Label_A.png is a 1024 x 512 atlas of
twelve typed file-label cards in a 4 x 3 grid (row-major from the top left):

    0 "A - C"    1 "D - F"    2 "G - K"    3 "L - P"
    4 "Q - S"    5 "T - Z"    6 "1994"     7 "1995"
    8 "PAYROLL"  9 "MISC"    10 "OLD"     11 "LEVEL 4"

A quad mapped 0..1 (kit.quad's decal UVs) shows the whole sheet of twelve
cards, so labels here are built with UVs on one card, cropped inside its
printed border to the quad's aspect (the text is left-aligned, so a crop in
width keeps the left end), and registered with uv="keep".
"""

import bmesh
from mathutils import Vector

SLOT = "Prop_Label"
TILES = ("A - C", "D - F", "G - K", "L - P", "Q - S", "T - Z", "1994", "1995",
         "PAYROLL", "MISC", "OLD", "LEVEL 4")
ATLAS_W, ATLAS_H = 1024.0, 512.0
COLS, ROWS = 4, 3
CELL_W, CELL_H = ATLAS_W / COLS, ATLAS_H / ROWS
# Card interior inside the printed border, pixels within one cell (top-down).
CARD_X0, CARD_X1 = 22.0, 234.0
CARD_Y0, CARD_Y1 = 34.0, 136.0
TEXT_MIN_W = 168.0          # longest word ("PAYROLL") ends ~180 px into the cell
TEXT_MIN_H = 44.0           # cap height 27 px, centred on the card


def tile_rect(tile, aspect, min_h=TEXT_MIN_H):
    """(u0, v0, u1, v1) on card ``tile`` for a quad of width/height ``aspect``
    (in reading direction). ``min_h`` (px) keeps the text band whole on very
    thin labels, at the cost of some horizontal stretch."""
    if isinstance(tile, str):
        tile = TILES.index(tile)
    col, row = tile % COLS, tile // COLS
    w, h = CARD_X1 - CARD_X0, CARD_Y1 - CARD_Y0
    cy = (CARD_Y0 + CARD_Y1) / 2
    if aspect >= w / h:
        h = max(w / aspect, min_h)
        x0 = CARD_X0
    else:
        w = max(h * aspect, TEXT_MIN_W)
        x0 = CARD_X0
    y0, y1 = cy - h / 2, cy + h / 2
    u0 = (col * CELL_W + x0) / ATLAS_W
    u1 = (col * CELL_W + x0 + w) / ATLAS_W
    v1 = 1.0 - (row * CELL_H + y0) / ATLAS_H
    v0 = 1.0 - (row * CELL_H + y1) / ATLAS_H
    return u0, v0, u1, v1


def label(kit, tile, width, height, right, up, name="label", min_h=TEXT_MIN_H):
    """A label card of ``width`` x ``height`` metres showing atlas card
    ``tile``. ``right`` is the reading direction and ``up`` the text's up, as
    unit 3-vectors in the part's local space; right x up is the face normal
    (it must point at the viewer). The part sits at the origin: place it with
    obj.location / obj.rotation_euler like any kit part."""
    r = Vector(right).normalized() * width / 2
    u = Vector(up).normalized() * height / 2
    u0, v0, u1, v1 = tile_rect(tile, width / height, min_h)
    bm = bmesh.new()
    layer = bm.loops.layers.uv.verify()     # same default layer the kit UVs use, so join merges them
    corners = ((-r - u, (u0, v0)), (r - u, (u1, v0)), (r + u, (u1, v1)), (-r + u, (u0, v1)))
    verts = [bm.verts.new(p) for p, _ in corners]
    face = bm.faces.new(verts)
    for loop, (_, uv) in zip(face.loops, corners):
        loop[layer].uv = uv
    return kit._new_object(name, bm, SLOT, "keep", "xz")
