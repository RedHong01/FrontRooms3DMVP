"""Freestanding 1990s systems-furniture partition panel, 60" wide x 60" tall
(the slate fabric cubicle wall in Red's target office image).

Real-world reference: Steelcase Series 9000 / Haworth Unigroup-era acoustic
panels. 1.524 m wide, 1.52 m tall (in the reference office the panel tops sit
just above the eye-level horizon), 64 mm thick. Fabric-wrapped tackable core on BOTH faces, set 4 mm
inside a moulded putty frame: rounded top cap rail, vertical end trims with
rounded outer corners and slotted hang-on standards beside them, on a dark
100 mm base rail that stands 20 mm off the floor on two levelling glides
(§4.5 / T6: "light putty trim and top cap against the dark fabric; dark base
rail"). Both faces (-Y and +Y) are identical.

Budget build (round 2): the trims and the cap are single extrusions of their
rounded sections (no bevel modifier), the fabric core is a plain box (every
edge is tucked into a trim, the cap or the base rail), slots are 2-tri quads.
Slots are the §5.3 list: FabricCubicle, SteelPutty (cap, trims, standards:
the same paint as Kit_PanelPost, so post joints show no tone step) and
PlasticBlack. The cap is exactly ``width`` long and the end trims stop
0.5 mm short of it, so butt joints and posts never z-fight with the cap and
nothing leaves the collider. LOD1 (_workstation_lod.sharp_lod1): the slots,
standards and glides (sub-pixel at the ~12 m LOD1 switch, where half-collapsed
slots would shimmer) are dropped instead of decimating the cap and trims, so
the LOD1 keeps the round cap and corners, and its sharp edges are re-marked
(the base rail stays crisp).

``build_panel(kit, width, height)`` is shared with cubicle_panel_short.py and
cubicle_panel_tall.py; ``cap_profile`` and the constants with panel_post.py.
"""

import math

from _workstation_lod import lod1_drop, sharp_lod1

NAME = "Kit_CubiclePanel"
LOD1 = 0.45

FABRIC = "Prop_FabricCubicle"
TRIM = "Prop_SteelPutty"     # cap rail, end trims, standards (§5.2 "panel trim")
DARK = "Prop_PlasticBlack"   # base rail, glides, standard slots

H = 1.52  # measured in the target office frame (panel tops above eye-level horizon)
T = 0.064
TRIM_W = 0.030          # vertical end trim (X)
TRIM_R = 0.011          # outer corner radius of the end trim
STRIP_W = 0.016         # slotted standard beside each trim
FABRIC_INSET = 0.004    # fabric face below the trim face
RACE_Z0, RACE_H = 0.020, 0.100
CAP_TOP_H = 0.026       # cap height above the panel body
CAP_LIP = 0.008         # cap sides overlap the fabric this far
SLOT_PITCH = 0.050


def cap_profile(steps=8):
    """Rounded top-cap section in (y, z): flat sides that lap over the
    fabric, then a flattened arch (22.5 deg steps, so it shades smooth).
    z = 0 is the body top."""
    half = T / 2 + 0.0015
    pts = [(half, -CAP_LIP), (half, 0.006)]
    for i in range(1, steps):
        a = math.pi * i / steps
        pts.append((half * math.cos(a), 0.006 + (CAP_TOP_H - 0.006) * math.sin(a)))
    pts += [(-half, 0.006), (-half, -CAP_LIP)]
    return pts


def _arc(cx, cy, r, a0, a1, steps):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * k / steps)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * k / steps))) for k in range(steps + 1)]


TRIM_SHORT = 0.0005     # end trims stop this far inside the cap ends


def _trim_profile(hw, sx):
    """End-trim section in (x, y) for the trim at x = sx * hw: the outer
    corners rounded (TRIM_R, 3 steps), the inner corners chamfered 2 mm.
    The outer face sits TRIM_SHORT inside hw, so it never shares a plane
    with the cap end."""
    ix, c, ht = hw - TRIM_W, 0.002, T / 2
    ox = hw - TRIM_SHORT
    pts = [(ix + c, -ht)]
    pts += _arc(ox - TRIM_R, -ht + TRIM_R, TRIM_R, -90, 0, 3)
    pts += _arc(ox - TRIM_R, ht - TRIM_R, TRIM_R, 0, 90, 3)
    pts += [(ix + c, ht), (ix, ht - c), (ix, -ht + c)]
    return [(sx * x, y) for x, y in pts]


def build_panel(kit, width, height=H):
    sharp_lod1(kit)
    hw = width / 2
    body_top = height - CAP_TOP_H
    race_top = RACE_Z0 + RACE_H
    face = T / 2 - FABRIC_INSET          # fabric face |y|
    inner_x = hw - TRIM_W                # inside face of the end trims

    # Top cap rail: one extrusion along X, exactly ``width`` long (inside the
    # collider); the trims stop TRIM_SHORT short of its ends.
    kit.extrude(cap_profile(), width, (0, 0, body_top), TRIM, plane="yz", bevel=0.0, name="top cap")

    # Vertical end trims: rounded sections extruded up from the base rail
    # into the cap. Levelling glide under each.
    trim_z0, trim_z1 = RACE_Z0, body_top + 0.002
    for sx in (-1, 1):
        kit.extrude(_trim_profile(hw, sx), trim_z1 - trim_z0, (0, 0, (trim_z0 + trim_z1) / 2), TRIM,
                    plane="xy", bevel=0.0, name="end trim")
        lod1_drop(kit.cylinder(0.013, RACE_Z0, (sx * (hw - TRIM_W / 2 - 0.003), 0, RACE_Z0 / 2), DARK, verts=6,
                               bevel=0.0, name="glide"))

    # Fabric core, both faces; its ends run into the trims, its top under the
    # cap's lap and its foot into the base rail, so no edge of it is seen.
    fab_w = 2 * inner_x + 0.006
    fab_z0, fab_z1 = race_top - 0.002, body_top + 0.002
    kit.box((fab_w, 2 * face, fab_z1 - fab_z0), (0, 0, (fab_z0 + fab_z1) / 2), FABRIC, bevel=0.0, name="fabric")

    # Slotted standards: a putty channel beside each trim on both faces,
    # 1 mm proud of the fabric, with a column of 24 mm slots at 50 mm pitch
    # (hang-on shelves and binder bins). Slots are 2-tri quads 0.5 mm off
    # the standard's face.
    std_z0, std_z1 = race_top + 0.001, body_top + 0.002
    slot_z = [race_top + 0.07 + k * SLOT_PITCH
              for k in range(int((body_top - race_top - 0.12) / SLOT_PITCH) + 1)]
    for sx in (-1, 1):
        sxc = sx * (inner_x - STRIP_W / 2 + 0.002)
        lod1_drop(kit.box((STRIP_W + 0.004, 2 * face + 0.002, std_z1 - std_z0), (sxc, 0, (std_z0 + std_z1) / 2),
                          TRIM, bevel=0.0, name="standard"))
        for sy in (-1, 1):
            for z in slot_z:
                lod1_drop(kit.quad(0.0045, 0.024, (sxc, sy * (face + 0.0015), z), DARK,
                                   facing="-y" if sy < 0 else "+y", uv="metres", name="standard slot"))

    # Dark base rail (raceway cover), 2 mm proud of the fabric, its ends
    # inside the trims.
    kit.box((2 * inner_x + 0.004, T - 0.004, RACE_H), (0, 0, RACE_Z0 + RACE_H / 2), DARK,
            bevel=0.003, segments=1, name="base rail")

    kit.collider((0, 0, height / 2), (width, T, height))
    kit.anchor("top_centre", (0, 0, height))
    kit.tag("office", "panel")


def build(kit):
    build_panel(kit, 1.524)
    # Pile use: OfficeCluster only (office90s palette). The class filters of
    # CentreSculpture / CopyPasteRow would take a Case panel, so
    # FrontRoomsFurniturePile.BuildPile must drop "office_cluster_only"
    # entries unless tableau == OfficeCluster (C# side, not wired yet).
    kit.pile("Case", mass=1, states=["Upright", "Side", "Back"], palette="office90s")
    kit.tag("office_cluster_only")
