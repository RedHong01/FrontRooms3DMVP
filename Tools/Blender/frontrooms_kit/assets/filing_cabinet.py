"""Vertical 4-drawer letter file cabinet, putty steel, c. 1988-98 (HON 310 /
Steelcase 900 family: welded sheet-steel case, pan-formed drawer fronts with a
full-width recessed aluminium pull along the top edge, a card holder under
each pull, a push-plunger lock in the top rail, a lid that overhangs the case
by a few millimetres and a recessed toe kick).

Real-world reference size: 0.38 m wide x 0.66 m deep x 1.32 m tall (52",
26.5" deep). Drawer faces 340 x 290 mm with 3 mm shut gaps. Origin = floor
under the centre of the case. Front (drawer faces) looks -Y; the back is a
plain steel panel meant to stand against a wall.

Budget (10_synthesis §5.3): 1,400 / 600 tris, slots SteelPutty + one metal
+ Atlas (here SteelBlack carries the shadow cavity, the finger slots and the
glides: the shut gaps only read under flat top light if they look into
black). Each drawer front is one pan-formed frame whose hole is the pull
channel; the satin pull, the card plate and its typed card sit in it.
"""

import math

import _storage_labels as labels

NAME = "Kit_FilingCabinet"
LOD1 = 0.43

STEEL = "Prop_SteelPutty"
SHADOW = "Prop_SteelBlack"
METAL = "Prop_Aluminium"   # satin pulls, card plates, lock, badge

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
CHANNEL_TOP = 0.005        # rolled steel lip above the pull channel
CHANNEL_H = 0.040          # pull channel (pull + 20 mm finger slot)
CHEEK = 0.008              # steel cheek at each end of the channel


def _keep_lod1_creases(kit, angle=35.0):
    """The collapse-decimated LOD1 loses the sharp-edge marks, so its big
    flat drawer faces shade with gradients. Re-mark them on this instance's
    LOD1 after kitlib makes it (kitlib itself is untouched)."""
    make_lod1 = kit.make_lod1

    def wrapped(ratio):
        make_lod1(ratio)
        lod1 = getattr(kit, "lod1", None)
        if lod1 is not None:
            lod1.data.set_sharp_from_angle(angle=math.radians(angle))
    kit.make_lod1 = wrapped


def build(kit):
    _keep_lod1_creases(kit)
    # ---------------------------------------------------------------- carcass
    # Welded wrapper (sides, back, top) standing on four rubber glides.
    kit.box((CASE_HW * 2, 0.326 - KICK_Y, CASE_TOP - 0.006), (0, (0.326 + KICK_Y) / 2, 0.006 + (CASE_TOP - 0.006) / 2),
            STEEL, bevel=0.003, segments=1, name="case wrapper")
    for x in (-0.158, 0.158):
        for y in (-0.262, 0.298):
            kit.cylinder(0.013, 0.006, (x, y, 0.003), SHADOW, verts=6, bevel=0.0, name="glide")

    # Face frame: one closed frame, opening set low so the top rail is deep
    # enough for the lock. Its rear edge against the wrapper reads as the seam.
    ff_h = CASE_TOP - KICK_TOP
    ff_cz = KICK_TOP + ff_h / 2
    open_w = CASE_HW * 2 - STILE * 2
    open_h = OPEN_Z1 - OPEN_Z0
    open_cz = (OPEN_Z0 + OPEN_Z1) / 2
    ff_depth = KICK_Y - FACE_Y
    kit.frame((CASE_HW * 2, ff_h), (open_w, open_h), ff_depth, (0, (FACE_Y + KICK_Y) / 2, ff_cz), STEEL,
              inner_offset=(0, open_cz - ff_cz), bevel=0.003, segments=1, name="face frame")
    # Dark cavity behind the drawer fronts: what the shut gaps look into.
    kit.quad(open_w, open_h, (0, -0.296, open_cz), SHADOW, facing="-y", uv="metres", name="cavity")

    # Lid: separate cap, overhangs 5 mm at the sides, 8 mm at the front. Its
    # front edge is seen from standing height, so it keeps a 2-step round.
    kit.box((W, D, LID_T), (0, 0, CASE_TOP + LID_T / 2), STEEL, bevel=0.005, segments=2, name="lid")

    # ---------------------------------------------------------------- drawers
    dw = open_w - GAP * 2
    dh = (open_h - GAP * (DRAWERS + 1)) / DRAWERS
    yc = DRAWER_FACE_Y + DRAWER_T / 2
    ch_w = dw - 2 * CHEEK
    for i in range(DRAWERS):
        z0 = OPEN_Z0 + GAP + i * (dh + GAP)
        z1 = z0 + dh
        zc = (z0 + z1) / 2
        ch_top = z1 - CHANNEL_TOP
        ch_cz = ch_top - CHANNEL_H / 2
        # Pan-formed face: a frame whose hole is the full-width pull channel.
        # The bevel rolls the face edges and the channel lips alike.
        kit.frame((dw, dh), (ch_w, CHANNEL_H), DRAWER_T, (0, yc, zc), STEEL,
                  inner_offset=(0, ch_cz - zc), bevel=0.0035, segments=1, name="drawer face")
        # Satin pull: hangs from the channel top 1.5 mm behind the face; its
        # front bows out (one soft highlight under top light) and its lower
        # edge curls back (the lip the fingers hook under).
        py = DRAWER_FACE_Y + 0.0015
        pull_h = 0.019
        kit.extrude([(py + 0.016, 0.0), (py + 0.001, 0.0), (py - 0.0008, -0.006), (py, -0.014),
                     (py + 0.003, -pull_h), (py + 0.006, -pull_h + 0.001), (py + 0.005, -0.006), (py + 0.016, -0.005)],
                    ch_w, (0, 0, ch_top), METAL, plane="yz", bevel=0.0, name="pull")
        # Black finger space under the pull: a back wall 20 mm in and a black
        # channel floor, so the slot stays dark when seen from standing height.
        slot_h = CHANNEL_H - pull_h + 0.002
        back_y = DRAWER_FACE_Y + DRAWER_T - 0.002
        kit.quad(ch_w, slot_h, (0, back_y, ch_top - CHANNEL_H + slot_h / 2), SHADOW, facing="-y",
                 uv="metres", name="finger recess")
        floor_y0 = DRAWER_FACE_Y + 0.0036
        kit.quad(ch_w, back_y - floor_y0, (0, (floor_y0 + back_y) / 2, ch_top - CHANNEL_H + 0.0003), SHADOW,
                 facing="+z", uv="metres", name="finger recess floor")
        # Card plate under the pull (its 5 mm rim reads as the holder frame)
        # with a typed index card: A - C on the top drawer down to L - P.
        hz = z1 - 0.076
        kit.box((0.088, 0.002, 0.036), (0, DRAWER_FACE_Y - 0.001, hz), METAL, bevel=0.0, name="card holder")
        labels.card(kit, DRAWERS - 1 - i, 0.078, 0.027, (0, DRAWER_FACE_Y - 0.0023, hz + 0.0012), name="file label card")
        kit.anchor("drawer%d_pull" % (i + 1), (0, DRAWER_FACE_Y - 0.01, z1 - 0.02))

    # ------------------------------------------------------------- top rail
    rail_z = (OPEN_Z1 + CASE_TOP) / 2
    lock_x = 0.128
    kit.cylinder(0.012, 0.008, (lock_x, FACE_Y - 0.004, rail_z), METAL, verts=12, rot=(90, 0, 0),
                 bevel=0.0, name="lock plunger")
    kit.quad(0.0024, 0.010, (lock_x, FACE_Y - 0.0082, rail_z), SHADOW, facing="-y", uv="metres", name="keyway")
    kit.quad(0.044, 0.009, (-0.125, FACE_Y - 0.0006, rail_z), METAL, facing="-y", uv="metres", name="maker badge")
    kit.anchor("lock", (lock_x, FACE_Y - 0.01, rail_z))

    # ------------------------------------------------------------------ back
    # Stamped stiffening pan on the back panel and a facilities asset tag.
    kit.box((0.31, 0.003, 1.12), (0, 0.3265, 0.66), STEEL, bevel=0.0, name="back pan")
    labels.card(kit, 14, 0.064, 0.032, (0.06, 0.3285, 1.12), facing="+y", name="asset tag")

    # ------------------------------------------------------------- metadata
    kit.support("top", (0, 0, H), (0.36, 0.62))
    kit.collider((0, 0, H / 2), (W, D, H))
    kit.tag("office", "wall_unit")
    kit.pile("Case", mass=2, palette="office90s", states=["Upright", "Back", "Side", "EdgeLean"])
