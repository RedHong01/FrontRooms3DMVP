"""Golden-oak step-ladder stool (the "library steps" leaning across the
armchair in A24 "Backrooms" Still B).

Real-world reference: 1970s-80s solid-oak household step stool / ladder
stool, 3 steps to 1.0 m: two front stringers raked back ~13 degrees with the
two treads housed into them, two rear legs raked the other way (an A in side
view), all four splayed 2 degrees outward so the base is wider than the top,
a top platform with a bullnose front, a low side brace each side and a back
stretcher. Clear lacquer, no paint, no rubber.

Size: 0.45 m wide at the feet, 0.50 m deep, 1.00 m tall. Steps face -Y.
Budget 800 tris LOD0 (one slot, WoodOak); bevels: 1 segment on the
stringers, legs and braces (3 mm), 2 on the treads and top (seen nosings).
"""

import math
import random

NAME = "Kit_StepStool"
LOD1 = 0.4
SMOOTH_ANGLE = 35.0

OAK = "Prop_WoodOak"

W, D, H = 0.45, 0.50, 1.00
T = 0.022                      # board thickness of stringers and legs (x)
SPLAY = 2.0                    # sideways splay of the side frames, degrees
TOP_T = 0.024
TOP_Z0 = H - TOP_T             # underside of the top = top of the side frames
STR_W = 0.100                  # stringer width (perpendicular to its length)
LEG_W = 0.056                  # rear leg width
FRONT_FOOT = -D / 2            # front edge of the stringer foot
FRONT_TOP = -0.045             # front edge of the stringer under the top
REAR_FOOT = D / 2              # back edge of the rear-leg foot
REAR_TOP = 0.150               # back edge of the rear leg under the top
TREADS = (0.335, 0.668)        # tread top heights
TREAD_T = 0.022
NOSING = 0.014


def _slope(y0, y1):
    return (y1 - y0) / TOP_Z0


def _stringer_front(z):
    return FRONT_FOOT + _slope(FRONT_FOOT, FRONT_TOP) * z


def _rear_back(z):
    return REAR_FOOT + _slope(REAR_FOOT, REAR_TOP) * z


def _x_out(z):
    """Outer face of a side frame at height z (splay pulls it inward)."""
    return W / 2 - z * math.tan(math.radians(SPLAY))


def _raked(kit, side, y_edge0, y_edge1, width_h, sign, name):
    """A raked board in a side frame: the floor and top cuts are level, the
    long edges run from y_edge0 (at z=0) to y_edge1 (at TOP_Z0); the board
    extends width_h horizontally toward ``sign`` (+1 = +Y)."""
    a, b = y_edge0, y_edge1
    outline = [(a, 0.0), (a + sign * width_h, 0.0), (b + sign * width_h, TOP_Z0), (b, TOP_Z0)]
    if sign < 0:
        outline = list(reversed(outline))
    x = side * (W / 2 - T / 2)
    return kit.extrude(outline, T, (x, 0, 0), OAK, plane="yz", rot=(0, -side * SPLAY, 0),
                       bevel=0.003, segments=1, name=name)


def build(kit):
    rng = random.Random(4110)
    # Horizontal widths of the raked boards (their cut faces are level).
    a_str = math.atan(_slope(FRONT_FOOT, FRONT_TOP))
    a_leg = math.atan(-_slope(REAR_FOOT, REAR_TOP))
    str_h = STR_W / math.cos(a_str)
    leg_h = LEG_W / math.cos(a_leg)

    for side in (-1, 1):
        _raked(kit, side, FRONT_FOOT, FRONT_TOP, str_h, +1, "front stringer")
        _raked(kit, side, REAR_FOOT, REAR_TOP, leg_h, -1, "rear leg")
        # Low side brace, lapped onto the inside of the stringer and the leg.
        zb = 0.135
        y0 = _stringer_front(zb) + 0.02
        y1 = _rear_back(zb) - 0.02
        xb = side * (_x_out(zb) - T - 0.008)
        kit.box((0.016, y1 - y0, 0.045), (xb, (y0 + y1) / 2, zb), OAK, bevel=0.003, segments=1,
                rot=(0, -side * SPLAY, 0), name="side brace")

    # Treads housed 6 mm into the stringers, nosing proud of the front edge.
    depth = str_h + NOSING + 0.004
    for zt in TREADS:
        zc = zt - TREAD_T / 2
        half = _x_out(zc) - T + 0.006
        yf = _stringer_front(zt) - NOSING
        kit.box((2 * half, depth, TREAD_T), (0, yf + depth / 2, zc), OAK, bevel=0.0045, segments=1,
                name="tread")

    # Back stretcher between the rear legs and an apron under the top.
    for zs, hs in ((0.22, 0.05), (TOP_Z0 - 0.035, 0.06)):
        half = _x_out(zs) - T + 0.004
        ys = _rear_back(zs) - leg_h / 2
        kit.box((2 * half, 0.018, hs), (0, ys, zs), OAK, bevel=0.003, segments=1, name="back stretcher")

    # Top platform: overhangs the frames 12 mm each side, bullnose front.
    half = _x_out(TOP_Z0) + 0.012
    y0, y1 = FRONT_TOP - 0.025, REAR_TOP + 0.012
    # A hand-hold slot behind the standing area (carry it like a crate).
    # frame() faces -Y; rot X 90 lays it flat (its local +Z becomes world -Y).
    slot_y = y1 - 0.045
    kit.frame((2 * half, y1 - y0), (0.115, 0.030), TOP_T, (0, (y0 + y1) / 2, TOP_Z0 + TOP_T / 2), OAK,
              inner_offset=(0, (y0 + y1) / 2 - slot_y), rot=(90, 0, 0), bevel=0.005, segments=2, name="top")

    # Each board on its own patch of veneer.
    for obj in kit.parts:
        obj["fr_uv_offset"] = (round(rng.uniform(0, 0.6), 3), round(rng.uniform(0, 1.0), 3))

    # --- Metadata -------------------------------------------------------
    for i, zt in enumerate(TREADS):
        yf = _stringer_front(zt) - NOSING
        kit.support("tread%d" % (i + 1), (0, yf + depth / 2, zt), (2 * (_x_out(zt) - T), depth - 0.01))
    kit.support("top", (0, (y0 + y1) / 2, H), (2 * half - 0.02, y1 - y0 - 0.02))
    kit.anchor("top", (0, (y0 + y1) / 2, H))
    kit.collider((0, 0, H / 2), (W, D, H))
    kit.tag("domestic", "seat", "pile", "pile_piece")
    kit.pile("Seat", mass=0, states=["Upright", "EdgeLean", "Side"], palette="domestic70s")
