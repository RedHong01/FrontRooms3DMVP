"""Office interior window (borrowed-light glazing between an office and the
open plan), c. 1985-2000: clear-anodised aluminium 50 x 85 mm frame with
mitred head corners, a centre mullion, snap-in glazing beads with black
rubber gaskets, a protruding aluminium sill with horns. The glass is dark:
the room behind is unlit, so the pane reads as a black room with the open
plan reflected in it.

Real-world reference size: 2.44 m wide (sill) x 1.22 m tall x 0.12 m deep;
frame 2.40 x 1.22 m, 50 mm face. Decor piece: the asset's back (+Y) is the
wall plane at y = +0.06 (it is set 2 cm into the wall), so it stands 0.10 m
proud with the glass 47 mm behind the frame face. Origin = bottom centre of
the frame (z = 0 is the underside of the bottom rail). Front looks -Y.
"""

NAME = "Kit_InteriorWindow"

ALU = "Prop_Aluminium"
GLASS = "Prop_GlassCRT"
GASKET = "Prop_Rubber"

FW, FH = 2.40, 1.22        # frame outer
SILL_W = 2.44
FACE = 0.050               # frame face width
Y_FRONT, Y_BACK = -0.025, 0.060
GLASS_Y = 0.025            # glass centre plane
GLASS_T = 0.006
BEAD = 0.016               # glazing bead face width
MULLION = True


def build(kit):
    hw = FW / 2
    iw = hw - FACE
    zi0, zi1 = FACE, FH - FACE
    depth = Y_BACK - Y_FRONT
    yc = (Y_FRONT + Y_BACK) / 2
    # Four frame members, mitred at 45 degrees: the bevel on each piece
    # leaves a fine V where they meet, like a real mitre joint.
    bars = {
        "head": [(-hw, FH), (-iw, zi1), (iw, zi1), (hw, FH)],
        "bottom rail": [(-hw, 0.0), (hw, 0.0), (iw, zi0), (-iw, zi0)],
        "left jamb": [(-hw, 0.0), (-iw, zi0), (-iw, zi1), (-hw, FH)],
        "right jamb": [(hw, 0.0), (hw, FH), (iw, zi1), (iw, zi0)],
    }
    for name, outline in bars.items():
        kit.extrude(outline, depth, (0, yc, 0), ALU, plane="xz", bevel=0.0025, segments=2, name=name)

    # Sill: a nose with horns proud of the frame face, and a stool that
    # runs back inside the opening to the glazing bead.
    sill_top = zi0 + 0.004
    kit.box((SILL_W, 0.040, 0.020), (0, Y_FRONT - 0.020 + 0.005, sill_top - 0.010), ALU, bevel=0.004, segments=3, name="sill nose")
    kit.box((iw * 2, GLASS_Y - BEAD - Y_FRONT + 0.004, 0.006), (0, (Y_FRONT + GLASS_Y - BEAD) / 2 + 0.002, sill_top - 0.003),
            ALU, bevel=0.0015, segments=1, name="sill stool")

    # Panes, each in its own bead + gasket surround.
    if MULLION:
        mw = FACE
        kit.box((mw, Y_BACK - (Y_FRONT + 0.006), zi1 - sill_top), (0, (Y_FRONT + 0.006 + Y_BACK) / 2, (sill_top + zi1) / 2), ALU,
                bevel=0.0025, segments=2, name="mullion")
        pane_w = iw - mw / 2
        centres = (-(mw / 2 + pane_w / 2), mw / 2 + pane_w / 2)
    else:
        pane_w = iw * 2
        centres = (0.0,)
    pane_h = zi1 - sill_top
    pz = (sill_top + zi1) / 2
    for cx in centres:
        kit.box((pane_w + 0.01, GLASS_T, pane_h + 0.01), (cx, GLASS_Y, pz), GLASS, bevel=0.0, name="pane")
        bead_d = 0.014
        kit.frame((pane_w, pane_h), (pane_w - 2 * BEAD, pane_h - 2 * BEAD), bead_d,
                  (cx, GLASS_Y - GLASS_T / 2 - bead_d / 2, pz), ALU, bevel=0.002, segments=2, name="glazing bead")
        kit.frame((pane_w - 2 * BEAD + 0.002, pane_h - 2 * BEAD + 0.002), (pane_w - 2 * BEAD - 0.007, pane_h - 2 * BEAD - 0.007),
                  0.004, (cx, GLASS_Y - GLASS_T / 2 - 0.002, pz), GASKET, bevel=0.001, segments=1, name="gasket")

    kit.anchor("centre", (0, Y_FRONT, FH / 2))
    # Decor only: a thin slab so the player cannot push into the glass.
    kit.collider((0, -0.005, FH / 2), (SILL_W, 0.05, FH))
    kit.tag("office", "wall_decor")
