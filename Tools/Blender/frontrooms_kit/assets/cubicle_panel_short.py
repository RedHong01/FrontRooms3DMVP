"""Freestanding 1990s systems-furniture partition panel, 30" wide x 54" tall:
the narrow filler/return panel of a cubicle island (same family as
Kit_CubiclePanel; see cubicle_panel.py for construction and reference).

Real-world size: 0.762 m wide, 1.52 m tall, 64 mm thick. Fabric on both
faces inside a rounded putty top cap and vertical end trims with slotted
standards, dark 100 mm base rail on two levelling glides. Both faces (-Y and
+Y) are identical. No pile entry (§5.3).
"""

from cubicle_panel import build_panel

NAME = "Kit_CubiclePanelShort"
LOD1 = 0.45


def build(kit):
    build_panel(kit, 0.762)
