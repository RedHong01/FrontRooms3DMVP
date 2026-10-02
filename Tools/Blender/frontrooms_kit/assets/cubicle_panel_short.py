"""Freestanding 1990s systems-furniture partition panel, 30" wide x 62" tall:
the narrow filler/return panel of a cubicle island (same family as
Kit_CubiclePanel; see cubicle_panel.py for construction and reference).

Real-world size: 0.762 m wide, 1.57 m tall, 65 mm thick. Fabric on both
faces inside a rounded top cap and vertical end trims with slotted standards,
100 mm base raceway with duplex-outlet knockouts, two levelling glides.
Both faces (-Y and +Y) are identical.
"""

from cubicle_panel import build_panel

NAME = "Kit_CubiclePanelShort"


def build(kit):
    build_panel(kit, 0.762)
