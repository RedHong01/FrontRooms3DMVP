"""1990s three-seat sofa, the department-store "rolled-arm pillow-back"
(Still B: the beige floral sofa lying on top of the tower; trailer T05).

Construction:
* Rolled (English scroll) arms: a tall upholstered side panel whose top
  rolls OUTWARD over a 3.5 cm tucked undercut, lofted front to back with
  padded, rounded ends (flat arm-front panel ringed by a piping welt).
* Plinth base between the arms (upholstered front rail under the seat
  cushions), on short turned dark-wood feet.
* Tight back frame, lower than the cushions, with a rounded top.
* Three loose seat cushions (kit.soft_box with sag: a used sofa) and three
  plump loose back pillows (kit.soft_box with puff) raked back ~12 deg and
  rising above the frame: the pillow-back silhouette of the era.

Real-world reference size: 2.00 W x 0.90 D x 0.82 H; seat 0.45, arms 0.645.
Front (seat) faces -Y. Origin = floor under the centre.
Slots: Prop_FabricBeige (oatmeal; variants swap it to floral / charcoal),
Prop_WoodDark (feet).
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_Sofa3"
LOD1 = 0.4
SMOOTH_ANGLE = 70.0
VARIANTS = {
    "Kit_Sofa3_Floral": {"Prop_FabricBeige": "Prop_FabricFloral"},
    "Kit_Sofa3_Charcoal": {"Prop_FabricBeige": "Prop_FabricCharcoal"},
}

FABRIC = "Prop_FabricBeige"
WOOD = "Prop_WoodDark"

FOOT_H = 0.07          # underside of the upholstered body
DECK = 0.30            # top of the seat deck (cushions rest on it)
ARM_FRONT = -0.43
ARM_BACK = 0.45
BACK_FRONT = 0.31      # front face of the back frame
BACK_TOP = 0.74
RAIL_TOP = 0.115     # top of the dark-wood base rail (show-wood kick trim)


# --------------------------------------------------------------------- helpers
def _arc(cx, cz, r, a0, a1, n):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cz + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _normals2d(pts):
    """Outward vertex normals of a closed 2D outline (either winding)."""
    n = len(pts)
    area = sum(pts[i][0] * pts[(i + 1) % n][1] - pts[(i + 1) % n][0] * pts[i][1] for i in range(n))
    sgn = 1.0 if area > 0 else -1.0
    out = []
    for i in range(n):
        p0, p1, p2 = pts[i - 1], pts[i], pts[(i + 1) % n]
        acc = [0.0, 0.0]
        for a, b in ((p0, p1), (p1, p2)):
            dx, dz = b[0] - a[0], b[1] - a[1]
            l = math.hypot(dx, dz) or 1.0
            acc[0] += sgn * dz / l
            acc[1] += -sgn * dx / l
        l = math.hypot(*acc) or 1.0
        out.append((acc[0] / l, acc[1] / l))
    return out


def _loft(kit, rings, slot, name, cap0=None, cap1=None):
    """Quads between consecutive rings (equal point counts). cap0 / cap1:
    None = n-gon, a 3D point = triangle fan to that point (domed end)."""
    bm = bmesh.new()
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for a, b in zip(vs, vs[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    for ring, cap in ((vs[0], cap0), (vs[-1], cap1)):
        if cap is None:
            bm.faces.new(ring)
        else:
            c = bm.verts.new(cap)
            for i in range(n):
                bm.faces.new((c, ring[(i + 1) % n], ring[i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return kit._new_object(name, bm, slot, "metres", "xz")


def _arm_profile():
    """Right arm cross-section (x, z), outer side at +x. The roll overhangs
    the outer panel and tucks under it."""
    cx, cz, r = 0.910, 0.555, 0.090
    x_out = 0.962
    a_j = -math.degrees(math.acos((x_out - cx) / r))
    pts = [(0.802, FOOT_H), (0.935, FOOT_H), (x_out - 0.004, FOOT_H + 0.006), (x_out, FOOT_H + 0.03),
           (x_out, 0.30)]
    pts += _arc(cx, cz, r, a_j, 180.0, 16)
    pts += [(0.816, 0.47), (0.808, 0.33), (0.803, 0.18)]
    return pts


def _arm(kit, side):
    prof = _arm_profile()
    nrm = _normals2d(prof)

    def ring(y, inset):
        return [(side * (x - nx * inset), y, z - nz * inset) for (x, z), (nx, nz) in zip(prof, nrm)]
    # Padded front: three rounding rings, then the run to the back, rounded again.
    rings = [ring(ARM_FRONT, 0.030), ring(ARM_FRONT + 0.006, 0.016), ring(ARM_FRONT + 0.018, 0.005),
             ring(ARM_FRONT + 0.034, 0.0), ring(ARM_BACK - 0.03, 0.0), ring(ARM_BACK - 0.012, 0.008),
             ring(ARM_BACK, 0.024)]
    fx = side * 0.885
    _loft(kit, rings, FABRIC, "rolled arm", cap0=(fx, ARM_FRONT - 0.003, 0.42), cap1=(fx, ARM_BACK + 0.002, 0.42))
    # Piping welt round the arm-front panel.
    welt = [Vector((side * (x - nx * 0.027), ARM_FRONT - 0.0005, z - nz * 0.027)) for (x, z), (nx, nz) in zip(prof, nrm)]
    welt = [p for p in welt if p.z > RAIL_TOP]
    kit.tube([tuple(p) for p in welt], 0.0055, FABRIC, verts=5, name="arm welt", caps=False)


def _back_frame(kit):
    """Tight back: (y, z) section with a rounded top, lofted along X between
    the arms (its ends bury in them)."""
    t = ARM_BACK - BACK_FRONT
    prof = [(BACK_FRONT, DECK), (BACK_FRONT, FOOT_H), (ARM_BACK, FOOT_H), (ARM_BACK, BACK_TOP - t / 2)]
    prof += _arc((BACK_FRONT + ARM_BACK) / 2, BACK_TOP - t / 2, t / 2, 0.0, 180.0, 8)[1:]
    xs = (-0.90, 0.90)
    rings = [[(x, y, z) for y, z in prof] for x in xs]
    _loft(kit, rings, FABRIC, "back frame")


def _seat_cushion(kit, x, tilt):
    w, d, h = 0.536, 0.585, 0.160
    cy = -0.446 + d / 2
    obj = kit.soft_box((w, d, h), (x, cy, DECK + h / 2 - 0.004), FABRIC, radius=0.031, segments=24, rings=10,
                       sag=0.026, puff=0.012, rot=(0, tilt, 0), name="seat cushion")
    # Sag is where people sit: push the dip toward the front edge.
    for v in obj.data.vertices:
        if v.co.z > 0:
            u = v.co.y / (d / 2)
            k = max(0.0, 1 - (v.co.x / (w / 2)) ** 2)
            v.co.z -= 0.010 * k * max(0.0, 0.6 - u) * (v.co.z / (h / 2))
    return obj


def _back_cushion(kit, x, rake, roll):
    w, d, h = 0.528, 0.19, 0.49
    obj = kit.soft_box((w, d, h), (x, 0.205, DECK + h / 2 + 0.012), FABRIC, radius=0.040, segments=20, rings=14,
                       puff=0.040, rot=(-rake, 0, roll), name="back cushion")
    # Pillows slump: the top folds forward a little, the bottom wedges back.
    for v in obj.data.vertices:
        t = v.co.z / (h / 2)
        v.co.y -= 0.012 * max(0.0, t) ** 2
    return obj


def _foot(kit, x, y):
    kit.lathe([(0.019, 0.0), (0.022, 0.006), (0.025, 0.040), (0.030, 0.050), (0.030, FOOT_H + 0.004)],
              (x, y, 0.0), WOOD, verts=8, name="turned foot")


# ------------------------------------------------------------------------ build
def build(kit):
    for side in (-1, 1):
        _arm(kit, side)
    # Plinth / seat deck between the arms, upholstered front rail.
    kit.box((1.66, ARM_BACK - ARM_FRONT - 0.02, DECK - FOOT_H), (0, (ARM_FRONT + ARM_BACK) / 2 - 0.005,
            (DECK + FOOT_H) / 2), FABRIC, bevel=0.03, segments=3, name="plinth")
    _back_frame(kit)
    # Show-wood base rail: the body sits on a moulded dark-wood band (front
    # and both sides), the turned feet screw into it.
    rh = RAIL_TOP - FOOT_H
    kit.box((1.948, 0.024, rh), (0, ARM_FRONT - 0.004, FOOT_H + rh / 2), WOOD, bevel=0.005, segments=1,
            name="base rail front")
    for side in (-1, 1):
        kit.box((0.024, ARM_BACK - ARM_FRONT - 0.004, rh), (side * 0.962, (ARM_FRONT + ARM_BACK) / 2 - 0.004,
                FOOT_H + rh / 2), WOOD, bevel=0.005, segments=1, name="base rail side")

    for x, tilt in ((-0.527, -0.6), (0.0, 0.4), (0.527, 0.0)):
        _seat_cushion(kit, x, tilt)
    for x, rake, roll in ((-0.528, 12.5, 1.2), (0.0, 11.0, -0.6), (0.528, 13.5, -1.0)):
        _back_cushion(kit, x, rake, roll)

    for x in (-0.885, 0.885):
        for y in (-0.385, 0.395):
            _foot(kit, x, y)
    for y in (-0.36, 0.38):
        _foot(kit, 0.0, y)

    kit.support("seat", (0, -0.17, 0.45), (1.50, 0.46))
    kit.anchor("sit_left", (-0.527, -0.17, 0.45))
    kit.anchor("sit", (0.0, -0.17, 0.45))
    kit.anchor("sit_right", (0.527, -0.17, 0.45))
    kit.collider((0, 0.0, 0.25), (2.00, 0.90, 0.50))
    kit.collider((0, 0.33, 0.66), (2.00, 0.24, 0.32))
    kit.tag("domestic", "upholstery", "seat", "pile_piece")
    kit.pile("Soft", mass=2, states=["Upright", "Back", "Side"], palette="domestic70s", topper=True)
