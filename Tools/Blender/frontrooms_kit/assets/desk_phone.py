"""1990s office desk phone (multi-line key telephone: Panasonic KX-T7000 /
Nortel Meridian / AT&T Partner family): beige wedge base with a raised
handset cradle on the left (two cups and a hookswitch slot), the handset
resting in it, coiled handset cord to the side jack, dark grey faceplate
with a 3 x 4 dial pad, LCD strip, soft keys, a column of line / memory keys
with LEDs and a paper designation card, feature keys, volume rocker and a
speaker grille at the front; flat line cord out of the back to an RJ-11 plug.

Real-world reference size: 0.22 m wide, 0.20 m deep, 0.09 m tall over the
handset (base 26 mm at the front rising to 50 mm at the back, ~8 deg deck;
the cradle stands 10 mm proud of the deck).
Front (dial pad, user side) faces -Y. Origin = desk under the base centre.
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_DeskPhone"
# LOD0 is ~3.6k tris, 1.27k of them the coiled cord (8 points per turn,
# 5-sided wire: the minimum that reads as a round coil). LOD1 decimates it.
LOD1 = 0.5

BEIGE = "Prop_PlasticBeige"
DARK = "Prop_PlasticGrey"
BLACK = "Prop_PlasticBlack"
WHITE = "Prop_PlasticWhite"
RUBBER = "Prop_Rubber"
LENS = "Prop_GlassCRT"
CARD = "Prop_Label"
PAPER = "Prop_Paper"
CLEAR = "Prop_Glass"

W, D = 0.22, 0.20
FOOT = 0.004
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
POD_R = 0.0198                       # widest point of the cup dome, just inside the 40 mm grip


def _deck(u, v, w):
    """Deck frame -> asset space: u across, v up the slope, w off the deck."""
    return (u, v * math.cos(TILT) - w * math.sin(TILT), Z0 + v * math.sin(TILT) + w * math.cos(TILT))


def _deck_z(y, w=0.0):
    """Height of the plane w above the deck at asset y."""
    return DECK_FRONT_Z + (y - DECK_FRONT_Y) * math.tan(TILT) + w / math.cos(TILT)


def _smooth(points, sub):
    """Catmull-Rom resample of a polyline."""
    pts = [tuple(p) for p in points]
    out = []
    for i in range(len(pts) - 1):
        p0 = pts[max(i - 1, 0)]
        p1, p2 = pts[i], pts[i + 1]
        p3 = pts[min(i + 2, len(pts) - 1)]
        for k in range(sub):
            t = k / sub
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * t + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in range(3)))
    out.append(pts[-1])
    return out


def _round_rect(w, d, r, seg=2):
    pts = []
    for cx, cy, a0 in ((w / 2 - r, d / 2 - r, 0), (-w / 2 + r, d / 2 - r, 90), (-w / 2 + r, -d / 2 + r, 180), (w / 2 - r, -d / 2 + r, 270)):
        for k in range(seg + 1):
            a = math.radians(a0 + 90.0 * k / seg)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _frames(points):
    """Parallel-transport frames along a polyline: (point, tangent, normal,
    binormal). The normal starts as world-up projected off the tangent and is
    carried along by removing each new tangent component, so the frame never
    flips (kit.tube swaps its reference vector when the path turns vertical,
    which twisted and pinched the old coil)."""
    pts = [Vector(p) for p in points]
    n = len(pts)
    tangents = []
    for k in range(n):
        if k == 0:
            t = pts[1] - pts[0]
        elif k == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[k] - pts[k - 1]).normalized() + (pts[k + 1] - pts[k]).normalized()
        tangents.append(t.normalized())
    up = Vector((0, 0, 1))
    nrm = up - tangents[0] * up.dot(tangents[0])
    if nrm.length < 1e-4:
        nrm = Vector((1, 0, 0)) - tangents[0] * tangents[0].x
    nrm.normalize()
    out = []
    for p, t in zip(pts, tangents):
        nrm = (nrm - t * nrm.dot(t)).normalized()
        out.append((p, t, nrm, t.cross(nrm)))
    return out


def _pt_tube(kit, points, radius, slot, verts=8, name="tube", caps=True, flat=1.0):
    """Tube along a polyline on parallel-transport frames. flat < 1 squashes
    the section along the frame normal (flat line cord: 6 x 3 mm)."""
    bm = bmesh.new()
    rings = []
    for p, t, nrm, b in _frames(points):
        ring = []
        for i in range(verts):
            a = 2 * math.pi * (i + 0.5) / verts
            ring.append(bm.verts.new(p + (nrm * (math.cos(a) * flat) + b * math.sin(a)) * radius))
        rings.append(ring)
    for a, c in zip(rings, rings[1:]):
        for i in range(verts):
            j = (i + 1) % verts
            bm.faces.new((a[i], a[j], c[j], c[i]))
    if caps:
        bm.faces.new(list(reversed(rings[0])))
        bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _coil(centre, radius, pitch, per_turn):
    """Helix wound round a centre polyline (parallel-transport frames)."""
    lengths = [0.0]
    for a, b in zip(centre, centre[1:]):
        lengths.append(lengths[-1] + (Vector(b) - Vector(a)).length)
    total = lengths[-1]
    n = max(8, int(round(total / pitch * per_turn)))
    samples = []
    for k in range(n + 1):
        s = total * k / n
        for i in range(len(centre) - 1):
            if lengths[i + 1] >= s or i == len(centre) - 2:
                seg = max(lengths[i + 1] - lengths[i], 1e-9)
                t = min(max((s - lengths[i]) / seg, 0.0), 1.0)
                samples.append(Vector(centre[i]).lerp(Vector(centre[i + 1]), t))
                break
    out = []
    for k, (p, t, nrm, b) in enumerate(_frames(samples)):
        phi = 2 * math.pi * k / per_turn
        out.append(tuple(p + (nrm * math.cos(phi) + b * math.sin(phi)) * radius))
    return out


def _key(kit, u, v, w, h, slot, name="key"):
    """Tapered key cap standing on the faceplate (no bevel: the taper reads)."""
    tilt = math.degrees(TILT)
    cap = kit.loft_box((w, h), (w - 0.0024, h - 0.0024), 0.0045, _deck(u, v, 0.00225 + 0.0012), slot,
                       back_offset=(0, 0), bevel=0.0, rot=(90 + tilt, 0, 0), name=name)
    # Its base (the loft's front rectangle) sits on the faceplate: never seen.
    bm = bmesh.new()
    bm.from_mesh(cap.data)
    bm.normal_update()
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.y < -0.99], context="FACES")
    bm.to_mesh(cap.data)
    bm.free()
    return cap


def _rj11(kit, end, prev):
    """Clear RJ-11 plug lying on the desk at the line-cord end, pointing along
    the cord's last tangent, with its black latch tab on top."""
    dx, dy = end[0] - prev[0], end[1] - prev[1]
    l = math.hypot(dx, dy) or 1.0
    dx, dy = dx / l, dy / l
    rz = math.degrees(math.atan2(-dx, dy))           # local +Y along the cord
    c = (end[0] + dx * 0.010, end[1] + dy * 0.010)
    kit.box((0.0095, 0.020, 0.0065), (c[0], c[1], 0.00325), CLEAR, bevel=0.0008, segments=1, rot=(0, 0, rz), name="rj11 body")
    kit.box((0.004, 0.010, 0.0015), (c[0] - dx * 0.002, c[1] - dy * 0.002, 0.0070), BLACK, bevel=0.0, rot=(0, 0, rz),
            name="rj11 latch")


def build(kit):
    tilt = math.degrees(TILT)

    # ------------------------------------------------------------ base
    # Main body right of the cradle: wedge side profile (front chamfer, deck,
    # rear hump). Its left end is buried 4 mm inside the cradle block.
    prof = [(-D / 2, FOOT), (D / 2, FOOT), (D / 2, 0.044), (0.093, 0.052), (DECK_BACK_Y, DECK_BACK_Z),
            (DECK_FRONT_Y, DECK_FRONT_Z), (-D / 2, 0.019)]
    bx0 = CRADLE_X1 - 0.004
    kit.extrude(prof, W / 2 - bx0, ((W / 2 + bx0) / 2, 0, 0), BEIGE, plane="yz", bevel=0.0055, segments=2, name="base shell")

    # Cradle block: body up to the cup floors (4 mm above the deck) ...
    yf, yb = -D / 2 - 0.0003, D / 2 + 0.0003      # 0.3 mm proud of the base faces (no coplanar fight)
    cprof = [(yf, FOOT + 0.0003), (yb, FOOT + 0.0003), (yb, _deck_z(yb, CUP_FLOOR)), (yf, _deck_z(yf, CUP_FLOOR))]
    kit.extrude(cprof, CRADLE_W, (CRADLE_U, 0, 0), BEIGE, plane="yz", bevel=0.003, segments=2, name="cradle body")
    # ... then the 6 mm cup deck: two frames, each round one cup, with the
    # hookswitch slot between them.
    hv = HANDSET_V
    v_front = (yf + 0.007 * math.sin(TILT)) / math.cos(TILT)
    v_back = (yb + 0.007 * math.sin(TILT)) / math.cos(TILT)
    for nm, v0, v1, cup in (("cradle front cup", v_front, hv - SLOT_V / 2, hv - POD_V),
                            ("cradle back cup", hv + SLOT_V / 2, v_back, hv + POD_V)):
        cv = (v0 + v1) / 2
        kit.frame((CRADLE_W, v1 - v0), (CUP_U, CUP_V), CRADLE_TOP - CUP_FLOOR,
                  _deck(CRADLE_U, cv, (CUP_FLOOR + CRADLE_TOP) / 2), BEIGE, inner_offset=(0, -(cup - cv)),
                  bevel=0.0025, segments=1, rot=(90 + tilt, 0, 0), name=nm)
        kit.box((CUP_U + 0.001, CUP_V + 0.001, 0.0006), _deck(CRADLE_U, cup, CUP_FLOOR + 0.0003), DARK, bevel=0.0,
                rot=(tilt, 0, 0), name="cup floor")
    kit.box((CRADLE_W - 0.002, SLOT_V + 0.001, 0.0006), _deck(CRADLE_U, hv, CUP_FLOOR + 0.0003), DARK, bevel=0.0,
            rot=(tilt, 0, 0), name="hookswitch slot floor")
    kit.box((0.016, 0.009, 0.0080), _deck(CRADLE_U, hv, CUP_FLOOR + 0.0040), BEIGE, bevel=0.0015, segments=1,
            rot=(tilt, 0, 0), name="hookswitch")

    # Parting line between the top cover and the bottom tray: a thin dark
    # band following the rounded plan outline.
    kit.extrude(_round_rect(W + 0.0010, D + 0.0010, 0.0055, seg=2), 0.0012, (0, 0, FOOT + 0.006), DARK,
                plane="xy", bevel=0.0, name="parting line")
    for sx in (-1, 1):
        for sy in (-1, 1):
            kit.box((0.014, 0.014, FOOT), (sx * 0.088, sy * 0.080, FOOT / 2), RUBBER, bevel=0.0, name="foot")

    # ------------------------------------------------------------ faceplate
    fp_u0, fp_u1, fp_v0, fp_v1 = -0.036, 0.104, -0.058, 0.081
    kit.box((fp_u1 - fp_u0, fp_v1 - fp_v0, 0.0024), _deck((fp_u0 + fp_u1) / 2, (fp_v0 + fp_v1) / 2, 0.0004), DARK,
            bevel=0.0012, segments=1, rot=(tilt, 0, 0), name="faceplate")
    top = 0.0016   # faceplate surface (deck w)

    # LCD: bezel frame and the smoked window.
    lu, lv = 0.033, 0.064
    kit.frame((0.098, 0.026), (0.086, 0.016), 0.003, _deck(lu, lv, top + 0.0012), BLACK,
              bevel=0.0, rot=(90 + tilt, 0, 0), name="LCD bezel")
    kit.box((0.087, 0.017, 0.0014), _deck(lu, lv, top + 0.0002), LENS, bevel=0.0, rot=(tilt, 0, 0), name="LCD window")
    # Soft keys under the display.
    for k in range(3):
        _key(kit, 0.005 + k * 0.028, 0.043, 0.018, 0.0072, BEIGE, name="soft key")

    # Dial pad: 3 x 4.
    for r in range(4):
        for c in range(3):
            _key(kit, -0.006 + c * 0.017, 0.022 - r * 0.0135, 0.0135, 0.0100, WHITE, name="dial key")
    # Line / memory keys with their LEDs, designation card under a clear cover.
    for r in range(6):
        v = 0.025 - r * 0.0128
        _key(kit, 0.068, v, 0.0155, 0.0078, BEIGE, name="line key")
        led = kit.quad(0.0036, 0.0022, _deck(0.054, v, top + 0.0003), LENS, facing="+z", name="line LED", uv="metres")
        led.rotation_euler = (TILT, 0, 0)
    # Paper designation strip (ruled) beside the line keys, in a moulded window.
    kit.box((0.0172, 0.0740, 0.0006), _deck(0.0925, -0.007, top + 0.0001), PAPER, bevel=0.0, rot=(tilt, 0, 0), name="designation strip")
    for r in range(7):
        rule = kit.quad(0.0150, 0.0005, _deck(0.0925, 0.0313 - r * 0.0128, top + 0.0005), DARK, facing="+z", name="strip rule", uv="metres")
        rule.rotation_euler = (TILT, 0, 0)
    kit.frame((0.0215, 0.078), (0.0170, 0.0735), 0.0016, _deck(0.0925, -0.007, top + 0.0008), DARK,
              bevel=0.0, rot=(90 + tilt, 0, 0), name="strip window")

    # Feature keys (hold / transfer / conference / release) and the volume rocker.
    for k in range(4):
        _key(kit, -0.024 + k * 0.0215, -0.038, 0.0170, 0.0078, BEIGE, name="feature key")
    _key(kit, -0.002, -0.051, 0.038, 0.0078, WHITE, name="volume rocker")
    kit.box((0.0012, 0.0062, 0.0008), _deck(-0.002, -0.051, top + 0.0048), DARK, bevel=0.0, rot=(tilt, 0, 0), name="rocker split")

    # Front strip on the bare shell: speaker grille slots and microphone hole.
    for k in range(5):
        slot = kit.quad(0.036, 0.0019, _deck(0.075, -0.064 - k * 0.0042, 0.0003), BLACK, facing="+z", name="speaker slot", uv="metres")
        slot.rotation_euler = (TILT, 0, 0)
    kit.cylinder(0.0012, 0.0012, _deck(0.040, -0.074, 0.0002), BLACK, verts=6, rot=(tilt, 0, 0), bevel=0.0, name="mic hole")
    # Speed-dial directory card (printed label sheet) under a clear window.
    card = kit.quad(0.040, 0.020, _deck(-0.013, -0.0735, 0.0004), CARD, facing="+z", name="directory card")
    card.rotation_euler = (TILT, 0, 0)
    kit.frame((0.044, 0.024), (0.0396, 0.0196), 0.0014, _deck(-0.013, -0.0735, 0.0007), DARK,
              bevel=0.0, rot=(90 + tilt, 0, 0), name="card window")

    # ------------------------------------------------------------ handset
    hu = HANDSET_U
    wb = CUP_FLOOR + 0.0014          # pod bottoms just clear the cup floors
    # Side profile (v along the handset, w up): ear / mouth lobes at the ends,
    # the grip arching over the hookswitch slot.
    outline = [(-0.1025, 0.006), (-0.097, 0.0), (-0.056, 0.0), (-0.042, 0.0125), (0.042, 0.0125), (0.056, 0.0),
               (0.097, 0.0), (0.1025, 0.006), (0.1025, 0.028), (0.086, 0.0335), (0.0, 0.0350), (-0.086, 0.0335),
               (-0.1025, 0.028)]
    kit.extrude(outline, 0.040, _deck(hu, hv, wb), BEIGE, plane="yz", rot=(tilt, 0, 0), bevel=0.0085, segments=3, name="handset")
    # Ear / mouth pods: domed undersides seated in the cups (lathe: flat
    # centre, rounded rim, straight wall up into the handset).
    # The dome shows below the handset's rounded underside; above w 8.5 mm it
    # tucks back inside the handset (no faceted bulge through its sides).
    pod = [(0.0095, 0.0), (0.0152, 0.0015), (0.0185, 0.0045), (POD_R, 0.0085), (0.0170, 0.0130), (0.0120, 0.0170)]
    for s, nm in ((1, "earpiece"), (-1, "mouthpiece")):
        p = kit.lathe(pod, _deck(hu, hv + s * POD_V, wb), BEIGE, verts=16, name=nm, close_top=False)
        p.rotation_euler = (TILT, 0, 0)
    # Earpiece perforations and the mouthpiece holes are on the hidden faces;
    # on the back of the handset: two moulded grip seams.
    kit.box((0.0012, 0.070, 0.0010), _deck(hu - 0.0145, hv, wb + 0.0347), DARK, bevel=0.0, rot=(tilt, 0, 0), name="handset seam")
    kit.box((0.0012, 0.070, 0.0010), _deck(hu + 0.0145, hv, wb + 0.0347), DARK, bevel=0.0, rot=(tilt, 0, 0), name="handset seam")

    # ------------------------------------------------------------ coiled cord
    # Mouthpiece end -> drops in front of the cradle -> curls along the desk
    # -> jack in the left side of the cradle block.
    start = _deck(hu, hv - 0.1005, wb + 0.006)
    jack = (CRADLE_X0 - 0.0006, -0.090, 0.013)
    lead_a = (start[0], start[1] - 0.007, start[2] - 0.006)
    centre = _smooth([lead_a, (hu - 0.004, -0.114, 0.0120), (hu - 0.015, -0.119, 0.0060), (-0.106, -0.116, 0.0058),
                      (-0.1175, -0.1035, 0.0062), (jack[0] - 0.007, jack[1], jack[2])], 5)
    centre = [(x, y, max(z, 0.0059)) for x, y, z in centre]          # coil rests on the desk
    _pt_tube(kit, [start, lead_a], 0.0018, BLACK, verts=6, name="cord lead")
    coil = _coil(centre, 0.0042, 0.0052, 8)
    _pt_tube(kit, coil, 0.0014, BLACK, verts=5, name="coiled cord", caps=False)
    _pt_tube(kit, [(jack[0] - 0.007, jack[1], jack[2]), (jack[0] + 0.002, jack[1], jack[2])], 0.0018, BLACK, verts=6,
             name="cord plug lead")
    kit.box((0.004, 0.012, 0.009), (CRADLE_X0 - 0.0008, jack[1], jack[2]), BLACK, bevel=0.0012, segments=1, name="handset jack plug")

    # ------------------------------------------------------------ line cord
    # Flat 6 x 3 mm line cord out of the back to its (unplugged) RJ-11 plug.
    lx = 0.045
    kit.box((0.012, 0.004, 0.009), (lx, D / 2 + 0.0015, 0.012), BLACK, bevel=0.0, name="line plug")
    ctrl = [(lx, D / 2 + 0.003, 0.012), (lx + 0.002, D / 2 + 0.013, 0.008), (lx + 0.006, D / 2 + 0.022, 0.0016),
            (lx + 0.018, D / 2 + 0.040, 0.0015), (lx + 0.024, D / 2 + 0.055, 0.0020), (lx + 0.026, D / 2 + 0.062, 0.0030)]
    line = [(x, y, max(z, 0.0016)) for x, y, z in _smooth(ctrl, 2)]
    _pt_tube(kit, line, 0.0030, DARK, verts=6, name="line cord", flat=0.5)
    _rj11(kit, ctrl[-1], ctrl[-2])

    # ------------------------------------------------------------ metadata
    kit.anchor("handset", _deck(hu, hv, 0.04))
    kit.anchor("lcd", _deck(lu, lv, 0.004))
    kit.collider(((W / 2 + CRADLE_X1) / 2, 0, 0.028), (W / 2 - CRADLE_X1, D, 0.056))
    kit.collider((CRADLE_U, 0, (_deck_z(D / 2, CRADLE_TOP)) / 2), (CRADLE_W, D, _deck_z(D / 2, CRADLE_TOP)))
    # Handset collider from its tilted extent (ends 0.1025 from centre, w wb..wb+0.035).
    zs = [_deck(hu, hv + sv * 0.1025, wb + w)[2] for sv in (-1, 1) for w in (0.0, 0.035)]
    ys = [_deck(hu, hv + sv * 0.1025, wb + w)[1] for sv in (-1, 1) for w in (0.0, 0.035)]
    kit.collider((hu, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2), (0.052, max(ys) - min(ys), max(zs) - min(zs)))
    kit.tag("office", "desk_top", "pile_piece")
    kit.pile("Small", mass=0, palette="office90s")
