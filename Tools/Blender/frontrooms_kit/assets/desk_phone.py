"""1990s office desk phone (multi-line key telephone: Panasonic KX-T7000 /
Nortel Meridian / AT&T Partner family): beige wedge base with a raised
handset cradle on the left (two cups and a hookswitch between them), the
handset resting in it, coiled handset cord to a jack in the cradle's front,
dark grey faceplate with the LCD strip, soft keys, the 3 x 4 dial pad and
its feature keys (HOLD / XFER / CONF / REDIAL / MSG), a column of line keys
with the designation strip, volume rocker and a speaker grille at the
front; flat line cord out of the back to an RJ-11 plug.

Real-world reference size: 0.22 m wide, 0.20 m deep, 0.09 m tall over the
handset (base 26 mm at the front rising to 50 mm at the back, ~8 deg deck;
the cradle stands 10 mm proud of the deck).
Front (dial pad, user side) faces -Y. Origin = desk under the base centre.

Budget (synthesis §5.3): 900 LOD0 tris, LOD1 0.42, no collider (desk-top
clutter), pile Small 0, <= 4 slots: PlasticBeige, PlasticGrey (faceplate,
cords, trims), Prop_PhoneKeys (keypad decal: dial pad on the left 60 %,
feature keys on the right) and Prop_LCD (display).
How: the keypad caps are real tapered caps joined with their plate into one
decal part, so each cap shows its own legend cell; the handset is one
ring-built rounded extrusion (152 tris; the bevelled extrude + two lathed
pods were 904); the coiled cord is a helical band, 8 steps a turn (the
8 x 5-sided wire coil was 1,270); LEDs, rules, seams and holes < 5 mm are gone.
"""

import math

import bmesh
import bpy

import _deskgear as dg

NAME = "Kit_DeskPhone"
LOD1 = 0.42

BEIGE = "Prop_PlasticBeige"
GREY = "Prop_PlasticGrey"
KEYS = "Prop_PhoneKeys"
LCD = "Prop_LCD"

W, D = 0.22, 0.20
DECK_FRONT_Y, DECK_BACK_Y = -0.088, 0.084
DECK_FRONT_Z, DECK_BACK_Z = 0.026, 0.050
TILT = math.atan2(DECK_BACK_Z - DECK_FRONT_Z, DECK_BACK_Y - DECK_FRONT_Y)
Z0 = DECK_FRONT_Z + (0 - DECK_FRONT_Y) * math.tan(TILT)      # deck height above y = 0

# Cradle block on the left: x -0.110 .. -0.040, full depth, its top 10 mm
# above the deck; cups 6 mm deep (floor 4 mm above the deck).
CRADLE_X0, CRADLE_X1 = -W / 2, -0.040
CRADLE_U = (CRADLE_X0 + CRADLE_X1) / 2
CRADLE_W = CRADLE_X1 - CRADLE_X0
CUP_FLOOR, CRADLE_TOP = 0.004, 0.010
CUP_U, CUP_V = 0.050, 0.044          # cup opening (across, along)
SLOT_V = 0.018                       # hookswitch slot between the cups

HANDSET_U = CRADLE_U
HANDSET_V = 0.001
POD_V = 0.074                        # earpiece / mouthpiece centres from the handset centre

# Keypad decal (Prop_PhoneKeys, 512 x 512): where it lies on the faceplate
# (deck u, v of its lower-left corner) and its size.
FIELD_U0, FIELD_V0 = -0.030, -0.041
FIELD_W, FIELD_D = 0.082, 0.068


def _deck(u, v, w):
    """Deck frame -> asset space: u across, v up the slope, w off the deck."""
    return (u, v * math.cos(TILT) - w * math.sin(TILT), Z0 + v * math.sin(TILT) + w * math.cos(TILT))


def _deck_z(y, w=0.0):
    """Height of the plane w above the deck at asset y."""
    return DECK_FRONT_Z + (y - DECK_FRONT_Y) * math.tan(TILT) + w / math.cos(TILT)


def _on_deck(obj, u, v, w):
    """Place a part built flat (local +Z up) onto the sloped deck."""
    obj.location = _deck(u, v, w)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = (TILT, 0, 0)
    return obj


def _cap(kit, x, y, w, h, slot, back=True, name="key"):
    """Tapered key cap standing on z = 0 (local, flat), 4.5 mm tall: top,
    front and sides; the back only where no cap stands behind it."""
    cap = kit.loft_box((w, h), (w - 0.0024, h - 0.0024), 0.0045, (x, y, 0.00225), slot,
                       back_offset=(0, 0), bevel=0.0, rot=(90, 0, 0), name=name)
    # Mesh-local normals: the loft is built along local Y and stood up by
    # rot X 90, so its base is local -Y and its back (world +Y) local -Z.
    dg.prune(cap, lambda n: n.y < -0.99 or (not back and n.z < -0.7))
    return cap


def _join(kit, objs):
    """Join parts into the first one (one planar decal spans them all)."""
    keep, others = objs[0], objs[1:]
    kit.parts = [p for p in kit.parts if not any(p is o for o in others)]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = keep
    bpy.ops.object.join()
    return keep


def _offset(poly, d):
    """Inset a closed counter-clockwise 2D polygon by d (mitred corners)."""
    out = []
    n = len(poly)
    for i in range(n):
        (x0, y0), (x1, y1), (x2, y2) = poly[i - 1], poly[i], poly[(i + 1) % n]
        e1 = (x1 - x0, y1 - y0)
        e2 = (x2 - x1, y2 - y1)
        l1, l2 = math.hypot(*e1) or 1.0, math.hypot(*e2) or 1.0
        n1 = (-e1[1] / l1, e1[0] / l1)            # inward normal of a CCW polygon (left side)
        n2 = (-e2[1] / l2, e2[0] / l2)
        bx, by = n1[0] + n2[0], n1[1] + n2[1]
        bl = math.hypot(bx, by) or 1.0
        bx, by = bx / bl, by / bl
        c = max(0.35, bx * n1[0] + by * n1[1])
        out.append((x1 + bx * d / c, y1 + by * d / c))
    return out


def _handset(kit, hu, hv, wb):
    """Handset: the side outline (v along it, w up) extruded 40 mm across
    with its long edges rolled over a 6.5 mm radius in two steps, built as
    vertex rings (cap, roll, side band, roll, cap). Returns the part."""
    end = [(0.094, 0.0), (0.1005, 0.0025), (0.1035, 0.0085), (0.1035, 0.0225), (0.1010, 0.0295), (0.0945, 0.0335)]
    outline = ([(-v, w) for v, w in reversed(end[:3])] + [(-0.056, 0.0), (-0.042, 0.0125), (0.042, 0.0125), (0.056, 0.0)]
               + end + [(0.0, 0.0350)] + [(-v, w) for v, w in reversed(end[3:])])
    hw, r = 0.020, 0.0065
    rings = []
    for side in (-1, 1):
        steps = (0.0, 45.0, 90.0) if side < 0 else (90.0, 45.0, 0.0)
        for a in steps:
            t = math.radians(a)
            inset = r * (1 - math.sin(t))
            u = side * (hw - r * (1 - math.cos(t)))
            rings.append([(u, v, w) for v, w in _offset(outline, inset)])
    obj = dg.rings_mesh(kit, rings, BEIGE, name="handset", cap_first=True, cap_last=True)
    # rings are in handset-local (u across, v along, w up): place on the deck.
    obj.location = _deck(hu, hv, wb)
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = (TILT, 0, 0)
    # local (u, v, w) must map to deck (u, v, w): the mesh is built with
    # x = u, y = v, z = w already, so the deck rotation is enough.
    return obj


def _rj11(kit, end, prev):
    """RJ-11 plug lying on the desk at the line-cord end, pointing along the
    cord's last tangent."""
    dx, dy = end[0] - prev[0], end[1] - prev[1]
    l = math.hypot(dx, dy) or 1.0
    dx, dy = dx / l, dy / l
    rz = math.degrees(math.atan2(-dx, dy))           # local +Y along the cord
    c = (end[0] + dx * 0.010, end[1] + dy * 0.010)
    dg.box_faces(kit, (0.0095, 0.020, 0.0065), (c[0], c[1], 0.00325), BEIGE, faces=("-x", "+x", "-y", "+y", "+z"),
                 rot=(0, 0, rz), name="rj11 plug")


def _coil(kit, centre, radius, pitch, per_turn, width, slot, name="coiled cord"):
    """Coiled cord as a helical band: each turn is a strip ``width`` wide
    (across the turn) facing out from the coil axis, ``per_turn`` steps
    round. Seen from outside it reads as the round wire's lit outer face;
    2 tris a step, so 8 steps a turn cost what a 3-sided wire costs at 2.7.
    The far half of each turn faces away and is culled in Unity, like the
    wire behind the near turns."""
    from mathutils import Vector
    lengths = [0.0]
    for a, b in zip(centre, centre[1:]):
        lengths.append(lengths[-1] + (Vector(b) - Vector(a)).length)
    total = lengths[-1]
    n = max(8, int(round(total / pitch * per_turn)))
    samples = []
    for k in range(n + 1):
        s_ = total * k / n
        for i in range(len(centre) - 1):
            if lengths[i + 1] >= s_ or i == len(centre) - 2:
                seg = max(lengths[i + 1] - lengths[i], 1e-9)
                t = min(max((s_ - lengths[i]) / seg, 0.0), 1.0)
                samples.append(Vector(centre[i]).lerp(Vector(centre[i + 1]), t))
                break
    bm = bmesh.new()
    rows = []
    for k, (p, t, nrm, b) in enumerate(dg.frames(samples)):
        phi = 2 * math.pi * k / per_turn
        out = nrm * math.cos(phi) + b * math.sin(phi)
        h = p + out * radius
        rows.append((bm.verts.new(h - t * (width / 2)), bm.verts.new(h + t * (width / 2)), out))
    for (a0, a1, o0), (b0, b1, o1) in zip(rows, rows[1:]):
        f = bm.faces.new((a0, a1, b1, b0))
        f.normal_update()
        if f.normal.dot(o0 + o1) < 0:
            f.normal_flip()
    return kit._new_object(name, bm, slot, "metres", "xz")


def build(kit):
    tilt = math.degrees(TILT)

    # ------------------------------------------------------------ base
    # Main body right of the cradle: wedge side profile (front chamfer, deck,
    # rear hump), one chamfered extrusion. Its left end is buried 4 mm inside
    # the cradle block.
    prof = [(-D / 2, 0.0), (D / 2, 0.0), (D / 2, 0.044), (0.093, 0.052), (DECK_BACK_Y, DECK_BACK_Z),
            (DECK_FRONT_Y, DECK_FRONT_Z), (-D / 2, 0.019)]
    bx0 = CRADLE_X1 - 0.004
    kit.extrude(prof, W / 2 - bx0, ((W / 2 + bx0) / 2, 0, 0), BEIGE, plane="yz", bevel=0.0045, segments=1, name="base shell")

    # Cradle block: body up to the cup floors (4 mm above the deck) ...
    yf, yb = -D / 2 - 0.0003, D / 2 + 0.0003      # 0.3 mm proud of the base faces (no coplanar fight)
    cprof = [(yf, 0.0003), (yb, 0.0003), (yb, _deck_z(yb, CUP_FLOOR)), (yf, _deck_z(yf, CUP_FLOOR))]
    kit.extrude(cprof, CRADLE_W, (CRADLE_U, 0, 0), BEIGE, plane="yz", bevel=0.003, segments=1, name="cradle body")
    # ... then the 6 mm cup deck: two frames, each round one cup, with the
    # hookswitch slot between them (the switch itself is under the handset); dark cup floors.
    hv = HANDSET_V
    v_front = (yf + 0.007 * math.sin(TILT)) / math.cos(TILT)
    v_back = (yb + 0.007 * math.sin(TILT)) / math.cos(TILT)
    for nm, v0, v1, cup in (("cradle front cup", v_front, hv - SLOT_V / 2, hv - POD_V),
                            ("cradle back cup", hv + SLOT_V / 2, v_back, hv + POD_V)):
        cv = (v0 + v1) / 2
        fr = kit.frame((CRADLE_W, v1 - v0), (CUP_U, CUP_V), CRADLE_TOP - CUP_FLOOR,
                       _deck(CRADLE_U, cv, (CUP_FLOOR + CRADLE_TOP) / 2), BEIGE, inner_offset=(0, -(cup - cv)),
                       bevel=0.0, rot=(90 + tilt, 0, 0), name=nm)
        dg.prune(fr, lambda n: n.y < -0.9)                        # its underside (local -Y) sits on the body
    # One dark floor under both cups and the slot (the frames hide the rest).
    span = 2 * POD_V + CUP_V
    q = kit.quad(CRADLE_W - 0.002, span, _deck(CRADLE_U, hv, CUP_FLOOR + 0.0002), GREY, facing="+z",
                 name="cup floors", uv="metres")
    q.rotation_euler = (TILT, 0, 0)

    # Parting line between the top cover and the bottom tray: a thin dark
    # band following the plan outline.
    pl = dg.round_rect(W + 0.0010, D + 0.0010, 0.0045, seg=1)    # chamfered corners, like the base
    dg.rings_mesh(kit, [[(x, y, 0.0090) for x, y in pl], [(x, y, 0.0102) for x, y in pl]], GREY, name="parting line",
                  centre=(0, 0, 0.0096))

    # ------------------------------------------------------------ faceplate
    fp_u0, fp_u1, fp_v0, fp_v1 = -0.036, 0.104, -0.058, 0.081
    fp = dg.box_faces(kit, (fp_u1 - fp_u0, fp_v1 - fp_v0, 0.0024), (0, 0, 0.0004), GREY,
                      faces=("-x", "+x", "-y", "+y", "+z"), name="faceplate")
    _on_deck(fp, (fp_u0 + fp_u1) / 2, (fp_v0 + fp_v1) / 2, 0.0004)
    top = 0.0016   # faceplate surface (deck w)

    # LCD: smoked display on a raised dark bezel block.
    lu, lv = 0.033, 0.064
    lb = dg.face_box(kit, (0.098, 0.0016, 0.026), (0, 0, 0), GREY, facing="+z", name="LCD bezel")
    _on_deck(lb, lu, lv, top + 0.0008)
    lb.rotation_euler = (TILT - math.pi / 2, 0, 0)
    disp = kit.quad(0.086, 0.016, (0, 0, 0), LCD, facing="+z", name="LCD", uv="decal")
    _on_deck(disp, lu, lv, top + 0.0018)
    # Soft keys under the display.
    for k in range(3):
        _on_deck(_cap(kit, 0, 0, 0.018, 0.0072, BEIGE, name="soft key"), 0.005 + k * 0.028, 0.043, top)

    # Keypad: plate + caps in one decal part, so the planar Prop_PhoneKeys
    # mapping over the field puts each legend cell on its own cap.
    def tex(px, py):           # texture px (from the top-left) -> metres from the field centre
        return (px / 512.0 - 0.5) * FIELD_W, FIELD_D * (0.5 - py / 512.0)
    plate = kit.quad(FIELD_W, FIELD_D, (0.0, 0.0, 0.0), KEYS, facing="+z", name="keypad", uv="decal")
    parts = [plate]
    for r in range(4):                                         # 1 2 3 / 4 5 6 / 7 8 9 / * 0 #
        for c in range(3):
            x0, y0 = (16, 117, 217)[c], 17 + r * 122
            (ax, ay), (bx, by) = tex(x0, y0), tex(x0 + 88, y0 + 108)
            parts.append(_cap(kit, (ax + bx) / 2, (ay + by) / 2, bx - ax - 0.0012, ay - by - 0.0012, KEYS))
    for r in range(5):                                         # HOLD XFER CONF REDIAL MSG
        y0 = 17 + r * 98
        (ax, ay), (bx, by) = tex(331, y0), tex(496, y0 + 82)
        parts.append(_cap(kit, (ax + bx) / 2, (ay + by) / 2, bx - ax - 0.0012, ay - by - 0.0012, KEYS))
    keypad = _join(kit, parts)
    keypad["fr_uv"] = "decal"
    keypad["fr_decal_axes"] = "xy"
    _on_deck(keypad, FIELD_U0 + FIELD_W / 2, FIELD_V0 + FIELD_D / 2, top)

    # Line / memory keys with the designation strip beside them.
    for r in range(5):
        _on_deck(_cap(kit, 0, 0, 0.0140, 0.0085, BEIGE, back=(r == 0), name="line key"), 0.068, 0.0215 - r * 0.0140, top)
    strip = kit.quad(0.0160, 0.0700, (0, 0, 0), BEIGE, facing="+z", name="designation strip", uv="metres")
    _on_deck(strip, 0.0925, -0.0075, top + 0.0003)
    # Volume rocker under the keypad.
    _on_deck(_cap(kit, 0, 0, 0.038, 0.0078, BEIGE, name="volume rocker"), 0.011, -0.050, top)

    # Front strip on the bare shell: speaker grille slots.
    for k in range(4):
        s = kit.quad(0.036, 0.0020, (0, 0, 0), GREY, facing="+z", name="speaker slot", uv="metres")
        _on_deck(s, 0.075, -0.0665 - k * 0.0048, 0.0003)

    # ------------------------------------------------------------ handset
    hu = HANDSET_U
    wb = CUP_FLOOR + 0.0014          # lobe bottoms just clear the cup floors
    _handset(kit, hu, hv, wb)

    # ------------------------------------------------------------ coiled cord
    # Mouthpiece end -> drops in front of the cradle -> one loop on the desk
    # -> jack in the cradle's front face.
    start = _deck(hu, hv - 0.1005, wb + 0.006)
    jack = (-0.099, -D / 2 - 0.0006, 0.013)
    lead_a = (start[0], start[1] - 0.006, start[2] - 0.006)
    dg.tube(kit, [start, lead_a], 0.0018, GREY, verts=4, name="cord lead", caps=True)
    centre = dg.smooth([lead_a, (hu - 0.002, -0.1135, 0.0140), (hu - 0.008, -0.1180, 0.0062),
                        (-0.092, -0.1160, 0.0060), (jack[0], jack[1] - 0.009, jack[2] - 0.001)], 3)
    centre = [(x, y, max(z, 0.0058)) for x, y, z in centre]          # coil rests on the desk
    _coil(kit, centre, 0.0040, 0.0062, 8, 0.0030, GREY)
    dg.tube(kit, [(jack[0], jack[1] - 0.009, jack[2] - 0.001), (jack[0], jack[1] + 0.002, jack[2])], 0.0018, GREY,
            verts=4, name="cord plug lead", caps=True)
    dg.face_box(kit, (0.012, 0.004, 0.009), (jack[0], jack[1] - 0.0016, jack[2]), GREY, name="handset jack plug")

    # ------------------------------------------------------------ line cord
    # Flat 6 x 3 mm line cord out of the back to its (unplugged) RJ-11 plug.
    lx = 0.045
    dg.face_box(kit, (0.012, 0.004, 0.009), (lx, D / 2 + 0.0015, 0.012), GREY, facing="+y", name="line plug")
    ctrl = [(lx, D / 2 + 0.003, 0.012), (lx + 0.0015, D / 2 + 0.012, 0.0080), (lx + 0.005, D / 2 + 0.021, 0.0016),
            (lx + 0.017, D / 2 + 0.040, 0.0015), (lx + 0.026, D / 2 + 0.062, 0.0030)]
    dg.tube(kit, ctrl, 0.0030, GREY, verts=4, name="line cord", flat=0.5)
    _rj11(kit, ctrl[-1], ctrl[-2])

    # ------------------------------------------------------------ metadata
    kit.anchor("handset", _deck(hu, hv, 0.04))
    kit.anchor("lcd", _deck(lu, lv, 0.004))
    kit.no_collider()
    kit.tag("office", "desk_top", "pile_piece")
    kit.pile("Small", mass=0, palette="office90s")
