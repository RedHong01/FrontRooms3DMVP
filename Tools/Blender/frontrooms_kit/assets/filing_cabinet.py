"""Vertical 4-drawer letter file cabinet, putty steel, c. 1988-98 (HON 310 /
Steelcase 900 family: welded sheet-steel case, pan-formed drawer fronts with a
full-width recessed aluminium pull along the top edge, a small chrome card
holder under each pull, a push-plunger lock in the top rail, a lid that
overhangs the case by a few millimetres and a recessed toe kick).

Real-world reference size: 0.38 m wide x 0.66 m deep x 1.32 m tall (52",
26.5" deep). Drawer faces 340 x 290 mm with 3 mm shut gaps. Origin = floor
under the centre of the case. Front (drawer faces) looks -Y; the back is a
plain steel panel meant to stand against a wall.
"""

import _storage_labels as labels

NAME = "Kit_FilingCabinet"

STEEL = "Prop_SteelPutty"
SHADOW = "Prop_SteelBlack"
ALU = "Prop_Aluminium"
CHROME = "Prop_Chrome"
RUBBER = "Prop_Rubber"
LABEL = "Prop_Label"

W, D, H = 0.38, 0.66, 1.32
CASE_HW = 0.185            # case half width (lid overhangs 5 mm a side)
FACE_Y = -0.322            # front plane of the face frame
KICK_Y = -0.272            # front of the recessed toe kick (50 mm back)
LID_T = 0.020
CASE_TOP = H - LID_T       # 1.300
KICK_TOP = 0.075
GAP = 0.003                # drawer shut gap
STILE = 0.012              # face-frame stile width
OPEN_Z0 = KICK_TOP + 0.010 # bottom rail 10 mm
OPEN_Z1 = 1.258            # top rail 42 mm (houses the lock)
DRAWERS = 4
DRAWER_FACE_Y = -0.325     # drawer fronts stand 3 mm proud of the frame
DRAWER_T = 0.022
PULL_BAND = 0.042


def build(kit):
    # ---------------------------------------------------------------- carcass
    # Welded wrapper (sides, back, top) on four rubber glides.
    kit.box((CASE_HW * 2, 0.326 - KICK_Y, CASE_TOP - 0.006), (0, (0.326 + KICK_Y) / 2, 0.006 + (CASE_TOP - 0.006) / 2),
            STEEL, bevel=0.004, segments=2, name="case wrapper")
    for x in (-0.158, 0.158):
        for y in (-0.262, 0.298):
            kit.cylinder(0.013, 0.006, (x, y, 0.003), RUBBER, verts=12, bevel=0.001, segments=1, name="glide")

    # Face frame: one closed frame, opening set low so the top rail is deep
    # enough for the lock. Its rear edge against the wrapper reads as the seam.
    ff_h = CASE_TOP - KICK_TOP
    ff_cz = KICK_TOP + ff_h / 2
    open_w = CASE_HW * 2 - STILE * 2
    open_h = OPEN_Z1 - OPEN_Z0
    open_cz = (OPEN_Z0 + OPEN_Z1) / 2
    ff_depth = KICK_Y - FACE_Y
    kit.frame((CASE_HW * 2, ff_h), (open_w, open_h), ff_depth, (0, (FACE_Y + KICK_Y) / 2, ff_cz), STEEL,
              inner_offset=(0, open_cz - ff_cz), bevel=0.004, segments=2, name="face frame")
    # Dark cavity behind the drawer fronts: what the shut gaps look into.
    kit.box((open_w, 0.010, open_h), (0, -0.295, open_cz), SHADOW, bevel=0.0, name="cavity")

    # Lid: separate cap, overhangs 5 mm at the sides, 8 mm at the front.
    kit.box((W, D, LID_T), (0, 0, CASE_TOP + LID_T / 2), STEEL, bevel=0.006, segments=3, name="lid")

    # ---------------------------------------------------------------- drawers
    dw = open_w - GAP * 2
    dh = (open_h - GAP * (DRAWERS + 1)) / DRAWERS
    yc = DRAWER_FACE_Y + DRAWER_T / 2
    for i in range(DRAWERS):
        z0 = OPEN_Z0 + GAP + i * (dh + GAP)
        z1 = z0 + dh
        panel_h = dh - PULL_BAND
        # Pan-formed face below the pull.
        kit.box((dw, DRAWER_T, panel_h), (0, yc, z0 + panel_h / 2), STEEL, bevel=0.005, segments=3, name="drawer face")
        # Pull band: putty end cheeks, dark finger recess, aluminium lip + lid.
        for sx in (-1, 1):
            kit.box((0.008, DRAWER_T, PULL_BAND), (sx * (dw / 2 - 0.004), yc, z1 - PULL_BAND / 2), STEEL,
                    bevel=0.003, segments=2, name="pull cheek")
        kit.box((dw - 0.012, 0.004, PULL_BAND - 0.004), (0, -0.305, z1 - PULL_BAND / 2), SHADOW, bevel=0.0, name="finger recess")
        kit.box((dw - 0.010, 0.006, 0.019), (0, DRAWER_FACE_Y + 0.002, z1 - 0.0095), ALU, bevel=0.0025, segments=2, name="pull lip")
        kit.box((dw - 0.012, 0.020, 0.004), (0, DRAWER_FACE_Y + 0.012, z1 - 0.002), ALU, bevel=0.0012, segments=1, name="pull top")
        kit.box((dw - 0.012, 0.012, 0.003), (0, DRAWER_FACE_Y + 0.010, z1 - 0.018), ALU, bevel=0.001, segments=1, name="pull return")
        # Card holder: chrome frame with a paper card, two rivets.
        hz = z1 - PULL_BAND - 0.034
        kit.frame((0.088, 0.036), (0.078, 0.027), 0.003, (0, DRAWER_FACE_Y - 0.0015, hz), CHROME,
                  inner_offset=(0, 0.0015), bevel=0.001, segments=1, name="card holder")
        # Typed index card from the Prop_Label atlas: A - C on the top drawer
        # down to L - P on the bottom one.
        card = labels.label(kit, DRAWERS - 1 - i, 0.078, 0.027, (1, 0, 0), (0, 0, 1), name="file label card")
        card.location = (0, DRAWER_FACE_Y - 0.0006, hz + 0.0015)
        for sx in (-1, 1):
            kit.cylinder(0.0022, 0.002, (sx * 0.0395, DRAWER_FACE_Y - 0.0035, hz), CHROME, verts=8,
                         rot=(90, 0, 0), bevel=0.0006, segments=1, name="rivet")
        kit.anchor("drawer%d_pull" % (i + 1), (0, DRAWER_FACE_Y - 0.01, z1 - 0.02))

    # ------------------------------------------------------------- top rail
    rail_z = (OPEN_Z1 + CASE_TOP) / 2
    lock_x = 0.128
    kit.cylinder(0.0135, 0.003, (lock_x, FACE_Y - 0.0015, rail_z), CHROME, verts=20, rot=(90, 0, 0),
                 bevel=0.0012, segments=2, name="lock flange")
    kit.cylinder(0.0098, 0.007, (lock_x, FACE_Y - 0.0045, rail_z), CHROME, verts=20, rot=(90, 0, 0),
                 bevel=0.0015, segments=2, name="lock plunger")
    kit.box((0.0024, 0.002, 0.010), (lock_x, FACE_Y - 0.0082, rail_z), SHADOW, bevel=0.0, name="keyway")
    kit.box((0.044, 0.002, 0.009), (-0.125, FACE_Y - 0.001, rail_z), ALU, bevel=0.0008, segments=1, name="maker badge")
    kit.anchor("lock", (lock_x, FACE_Y - 0.01, rail_z))

    # ------------------------------------------------------------------ back
    # Stamped stiffening pan on the back panel and an inventory sticker.
    kit.box((0.31, 0.003, 1.12), (0, 0.3265, 0.66), STEEL, bevel=0.0015, segments=1, name="back pan")
    # Facilities inventory sticker (reads from behind the cabinet).
    sticker = labels.label(kit, "LEVEL 4", 0.09, 0.055, (-1, 0, 0), (0, 0, 1), name="inventory sticker")
    sticker.location = (0.06, 0.3285, 1.12)

    # ------------------------------------------------------------- metadata
    kit.support("top", (0, 0, H), (0.36, 0.62))
    kit.collider((0, 0, H / 2), (W, D, H))
    kit.tag("office", "wall_unit")
    kit.pile("Case", mass=2, palette="office90s", states=["Upright", "Back", "Side", "EdgeLean"])
