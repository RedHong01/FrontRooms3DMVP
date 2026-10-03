"""Office interior window (borrowed-light glazing between an office and the
open plan), c. 1985-2000: dark-bronze painted steel 50 x 85 mm frame with
mitred corners, one undivided pane in snap-in glazing beads with black
rubber gaskets, a protruding steel sill with horns. The glass is dark: the
room behind is unlit, so the pane reads as a black room with the open plan
reflected in it. (Target: ref_office_target.png, right wall: a single pane
in a thin dark frame, no mullion.)

Real-world reference size: 2.44 m wide (sill) x 1.22 m tall x 0.12 m deep;
frame 2.40 x 1.22 m, 50 mm face. Decor piece: the asset's back (+Y) is the
wall plane at y = +0.06 (it is set 2 cm into the wall), so it stands 0.10 m
proud with the glass 47 mm behind the frame face. Origin = bottom centre of
the frame (z = 0 is the underside of the bottom rail); the placer sets the
sill height (0.90 m). Front looks -Y.

WALL-MOUNTED ONLY. There are no back faces and the pane is single-sided:
seen from behind (+Y) the asset is open and the glass vanishes. Never place
it as a free-standing partition; a partition version needs a mirrored back
sweep and a two-sided pane as a separate asset.

Budget 400 tris (~115 used), no collider (§5.3 [critic]: decor on a wall
stretch), 2 slots (§5.2: frame SteelBlack + glass; the gaskets share the
frame's SteelBlack, black on black, one draw fewer). The frame, the glazing
bead and the gasket are each ONE profile swept round a rectangle (mitred
corners for free, 8 tris per profile step), with only the faces that can be
seen: the wall hides their backs. Chamfers are real 3 mm faces, so the
frame catches a highlight line under top light.

Open for Red (T15): Prop_GlassCRT is opaque, so the window reads as a framed
black slab, not a view into a lit back room. Either an interior-mapping pane
material (one opaque material faking a dim room with a ceiling fixture) or a
wall cut with a back-room box behind transparent Prop_Glass.
"""

from mathutils import Vector

import bmesh

NAME = "Kit_InteriorWindow"

FRAME = "Prop_SteelBlack"   # §5.2 / §5.3: window frame is SteelBlack (dark bronze in the target)
GLASS = "Prop_GlassCRT"     # opaque dark glass until T15 decides the back-room read
GASKET = "Prop_SteelBlack"  # black rubber on a black frame: shares the frame slot

FW, FH = 2.40, 1.22        # frame outer
SILL_W = 2.44
FACE = 0.050               # frame face width
Y_FRONT, Y_BACK = -0.025, 0.060
GLASS_Y = 0.025            # glass centre plane
GLASS_T = 0.006
BEAD = 0.016               # glazing bead face width
BEAD_Y = 0.008             # glazing bead front plane
CH = 0.003                 # chamfer on the frame front edges


def rect_sweep(kit, cx, cz, hw, hh, profile, slot, name="sweep"):
    """Sweep a (d, y) profile round the rectangle (cx +/- hw, cz +/- hh) in
    the XZ plane: d grows the rectangle outward, y is depth. Corners are
    mitred. Traverse the profile from the inner back edge, forward along the
    inside, outward along the front, back along the outside: each face then
    gets the normal (dy, -dd) of its profile step (into the opening on the
    inside, toward -Y on the front, away on the outside)."""
    bm = bmesh.new()
    rings = []
    for d, y in profile:
        w, h = hw + d, hh + d
        rings.append([bm.verts.new(p) for p in ((cx - w, y, cz - h), (cx + w, y, cz - h), (cx + w, y, cz + h), (cx - w, y, cz + h))])
    side_dir = (Vector((0, 0, -1)), Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((-1, 0, 0)))
    for k in range(len(profile) - 1):
        dd = profile[k + 1][0] - profile[k][0]
        dy = profile[k + 1][1] - profile[k][1]
        a, b = rings[k], rings[k + 1]
        for i in range(4):
            j = (i + 1) % 4
            f = bm.faces.new((a[i], a[j], b[j], b[i]))
            f.normal_update()
            want = side_dir[i] * dy + Vector((0, 1, 0)) * -dd
            if f.normal.dot(want) < 0:
                f.normal_flip()
    return kit._new_object(name, bm, slot, "metres", "xz")


def build(kit):
    hw = FW / 2
    iw = hw - FACE
    zi0, zi1 = FACE, FH - FACE
    cz = FH / 2
    # Frame: inner side (from behind the bead) -> chamfer -> 50 mm face ->
    # chamfer -> outer side back to the wall.
    kit_frame = [(0.0, GLASS_Y), (0.0, Y_FRONT + CH), (CH, Y_FRONT), (FACE - CH, Y_FRONT),
                 (FACE, Y_FRONT + CH), (FACE, Y_BACK)]
    rect_sweep(kit, 0.0, cz, iw, (zi1 - zi0) / 2, kit_frame, FRAME, name="frame")

    # Sill nose with horns, proud of the frame face (its back is buried 5 mm
    # in the bottom rail); its top stands 4 mm above the rail's inner face.
    sill_top = zi0 + 0.004
    sb = sill_top - 0.020
    kit.extrude([(Y_FRONT + 0.005, sb), (-0.055, sb), (-0.0590, sb + 0.0020), (-0.0607, sb + 0.0060),
                 (-0.0607, sb + 0.0110), (-0.0590, sb + 0.0160), (-0.0560, sb + 0.0190), (-0.0525, sill_top),
                 (Y_FRONT + 0.005, sill_top)],
                SILL_W, (0, 0, 0), FRAME, plane="yz", bevel=0.0, name="sill nose")

    # One undivided pane over the whole opening in its bead + gasket
    # surround (the lit room behind reads straight across, as in the
    # target). The swept rectangle is the visible glass: bead inner edge
    # (d = 0) out to the frame.
    pane_w = 2 * iw
    pane_h = zi1 - zi0
    glass_front = GLASS_Y - GLASS_T / 2
    kit.quad(pane_w, pane_h, (0.0, glass_front, cz), GLASS, facing="-y", uv="metres", name="pane")
    gw, gh = pane_w / 2 - BEAD, pane_h / 2 - BEAD
    rect_sweep(kit, 0.0, cz, gw, gh, [(0.0, glass_front), (0.0, BEAD_Y + 0.002), (0.002, BEAD_Y), (BEAD, BEAD_Y)],
               FRAME, name="glazing bead")
    rect_sweep(kit, 0.0, cz, gw, gh, [(-0.0045, glass_front - 0.0002), (-0.0045, glass_front - 0.0032),
                                      (0.0, glass_front - 0.0032)], GASKET, name="gasket")

    kit.anchor("centre", (0, Y_FRONT, FH / 2))
    # Decor only (§5.3 [critic]): no collider; the wall behind blocks.
    kit.no_collider()
    kit.tag("office", "wall_decor")
