"""Connector post for the 1.37 m cubicle panels: the square putty steel post
that joins two to four panels at an L, T or X junction (Steelcase 9000 /
Haworth type). 64 x 64 mm (the panel thickness), 1.37 m tall, rounded
corners, a chamfered end cap flush with the panel caps and a levelling glide
under it. One slot, no collider (the panels carry the collision).

``build_post(kit, h)`` is shared with panel_post_tall.py (Kit_PanelPostTall,
1.65 m, for the Kit_CubiclePanelTall pods).
"""

import math

NAME = "Kit_PanelPost"

STEEL = "Prop_SteelPutty"

S = 0.064
H = 1.37
R = 0.008               # corner radius of the post section
GLIDE_H = 0.012
CAP_H = 0.010


def _rounded_square(half, r, steps=2):
    pts = []
    for cx, cy, a0 in ((half - r, -half + r, -90), (half - r, half - r, 0),
                       (-half + r, half - r, 90), (-half + r, -half + r, 180)):
        for k in range(steps + 1):
            a = math.radians(a0 + 90 * k / steps)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def build_post(kit, h=H):
    """A connector post ``h`` tall whose end cap is flush with the panel caps."""
    z0, z1 = GLIDE_H, h - CAP_H + 0.002
    kit.extrude(_rounded_square(S / 2, R), z1 - z0, (0, 0, (z0 + z1) / 2), STEEL, plane="xy",
                bevel=0.0, name="post")
    kit.box((S, S, CAP_H), (0, 0, h - CAP_H / 2), STEEL, bevel=0.003, segments=1, name="end cap")
    kit.cylinder(0.014, GLIDE_H, (0, 0, GLIDE_H / 2), STEEL, verts=6, bevel=0.0, name="glide")
    kit.no_collider()
    kit.anchor("top_centre", (0, 0, h))
    kit.tag("office", "panel")


def build(kit):
    build_post(kit, H)
