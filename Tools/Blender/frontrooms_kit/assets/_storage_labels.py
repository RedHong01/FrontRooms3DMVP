"""Prop_Label atlas helper for the storage group (filing cabinet, binders,
paper stack). Not an asset: it has no NAME/build.

Prop_Label_A.png is a 1024 x 1024 atlas of sixteen 256 px cells, 4 x 4,
row-major from the top left (kit.atlas_cell(i, 4, 4) is the whole cell):

    0 "A - C"   1 "D - F"   2 "G - K"   3 "L - P"      typed drawer cards
    4 "1994"    5 "1995"    6 "PAYROLL" 7 "MISC"       typed cards
    8 "Q3 REPORTS" 9 "MINUTES"   (portrait binder spine inserts, middle 40 %)
   10 "CLIENT FILES" folder tab strip (middle band)  11 furniture maker's label
   12 TV rating plate  13 INSPECTED stamp  14 asset tag + barcode  15 caution

A whole cell also shows the grey sheet around the printed piece, so labels
here map to the printed piece only: BOXES holds each piece's pixel box inside
its cell (measured on the texture), and card() crops it to the quad's aspect
around a chosen centre, so the text is never squashed.
"""

SLOT = "Prop_Label"
CELL = 256.0
ATLAS = 1024.0
COLS = 4

# Printed piece inside each cell, pixels (x0, y0, x1, y1), y down, border excluded.
BOXES = {i: (10, 54, 246, 202) for i in range(8)}
BOXES.update({
    8: (80, 7, 175, 248),
    9: (81, 8, 175, 248),
    10: (6, 106, 250, 150),
    11: (21, 43, 235, 213),
    12: (12, 62, 244, 194),
    13: (38, 38, 218, 218),
    14: (18, 72, 238, 184),
    15: (30, 30, 226, 216),
})
# Where the text sits (crop centre, pixels in the cell) for the typed cards:
# the word is centred at y ~ 120 with a blue rule under it at y ~ 151.
TEXT_CENTRE = {i: (128, 128) for i in range(8)}


def rect_px(cell, x0, y0, x1, y1, mirror=False):
    """uv_rect (u0, v0, u1, v1) of a pixel box inside ``cell``."""
    c, r = cell % COLS, cell // COLS
    u0 = (c * CELL + x0) / ATLAS
    u1 = (c * CELL + x1) / ATLAS
    v1 = 1.0 - (r * CELL + y0) / ATLAS
    v0 = 1.0 - (r * CELL + y1) / ATLAS
    return (u1, v0, u0, v1) if mirror else (u0, v0, u1, v1)


def rect(cell, aspect=None, mirror=False):
    """uv_rect of the printed piece in ``cell``; with ``aspect`` (width /
    height of the quad, in reading direction) it is cropped to that aspect
    around the text centre instead of being stretched."""
    x0, y0, x1, y1 = BOXES[cell]
    if aspect:
        w, h = x1 - x0, y1 - y0
        cx, cy = TEXT_CENTRE.get(cell, ((x0 + x1) / 2, (y0 + y1) / 2))
        if aspect >= w / h:
            h = w / aspect
        else:
            w = h * aspect
        cx = min(max(cx, x0 + w / 2), x1 - w / 2)
        cy = min(max(cy, y0 + h / 2), y1 - h / 2)
        x0, x1, y0, y1 = cx - w / 2, cx + w / 2, cy - h / 2, cy + h / 2
    return rect_px(cell, x0, y0, x1, y1, mirror)


def card(kit, cell, width, height, loc, facing="-y", crop=True, name="label"):
    """A ``width`` x ``height`` label quad facing ``facing`` (kit.quad
    facings) showing atlas ``cell``. Quads facing +y / +x are seen from the
    other side, so their UVs are mirrored to keep the text readable."""
    mirror = facing in ("+y", "+x")
    uv = rect(cell, width / height if crop else None, mirror)
    return kit.quad(width, height, loc, SLOT, facing=facing, name=name, uv_rect=uv)
