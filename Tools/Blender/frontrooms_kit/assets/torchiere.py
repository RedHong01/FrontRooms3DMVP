"""Black halogen torchiere floor lamp, c. 1992-98 (the 300 W "uplight" every
dorm room and furniture showroom had: weighted steel disc base, slim
three-section steel pole with threaded couplings, a rotary dimmer pod at
hand height, a wide shallow bowl with a rolled lip, white enamel inside and
a linear R7s halogen tube on a bracket).

Real-world reference size: 1.85 m tall, base 0.28 m diameter (domed steel
cover over a cast-iron weight), pole 19 mm diameter, bowl 0.36 m diameter x
85 mm deep. Cord leaves the back of the base and ends in a two-pin plug.
Front (dimmer knob) faces -Y. Origin = floor under the base centre.
Film: Still B, the black pole / white bowl spike on top of the pile (it
leans out of the pile, hence the EdgeLean state as well as Upright).

Budget (§5.3): 600 LOD0 tris, 2 slots, no collider. Optimised 2026-10-02
from 4.5k / 6 slots: the boss, pole, couplings and bowl neck are ONE
8-sided lathe; base and bowl keep 16 / 20 sides for their silhouettes;
details under ~5 mm at 2 m (wire guard, dimmer scale, plug blades,
grommets) are gone; rubber foot, pod plastic and chrome merged into the
black steel slot.
"""

import math

import bmesh
from mathutils import Vector

NAME = "Kit_Torchiere"
LOD1 = 0.42
# Rolled bowl lip and base rim turn ~40 deg per step: keep them one smooth bead.
SMOOTH_ANGLE = 48.0

STEEL = "Prop_SteelBlack"     # base, pole, bowl outside, dimmer pod, cord
WHITE = "Prop_PlasticWhite"   # enamel inside the bowl, halogen tube

POLE_R = 0.0095
BOWL_R = 0.181
BOWL_BOTTOM = 1.766
TOP = 1.852


def face_towards(obj, direction):
    """Open lathes have no inside/outside: flip the winding so most faces
    point along ``direction`` (a function of the face centre)."""
    mesh = obj.data
    score = sum(p.normal.dot(direction(Vector(p.center))) * p.area for p in mesh.polygons)
    if score < 0:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
        bm.to_mesh(mesh)
        bm.free()
    return obj


def drop_faces(obj, test):
    """Delete the faces whose local normal satisfies ``test`` (hidden backs
    and ends of small parts). Call before any bevel is applied."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    dead = [f for f in bm.faces if test(f.normal)]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(obj.data)
    bm.free()
    return obj


def build(kit):
    b = BOWL_BOTTOM

    # ---------------------------------------------------------------- base
    # Domed steel cover over the weight: a rolled rim (two steps that shade
    # as one bead) and a gentle dome. 16 sides: it is seen edge-on as a disc.
    base = [(0.133, 0.0), (0.1405, 0.010), (0.1300, 0.0255), (0.0300, 0.0405)]
    kit.lathe(base, (0, 0, 0), STEEL, verts=16, name="base cover", close_top=False)

    # --------------------------------------------- pole (boss to bowl neck)
    # One 8-sided lathe: socket boss, three pole sections with two threaded
    # coupling collars, and the flared neck that carries the bowl.
    pole = [
        (0.0260, 0.034), (0.0230, 0.058), (POLE_R, 0.078),                     # boss
        (POLE_R, 0.660), (0.0128, 0.672), (POLE_R, 0.684),                     # coupling
        (POLE_R, 1.160), (0.0128, 1.172), (POLE_R, 1.184),                     # coupling
        (POLE_R, 1.700), (0.0160, 1.736), (0.0420, b + 0.001),                 # bowl neck
    ]
    kit.lathe(pole, (0, 0, 0), STEEL, verts=8, name="pole", close_top=False, close_bottom=False)

    # ---------------------------------------------------------- rotary dimmer
    # Moulded pod round the pole at hand height, knob facing -Y.
    dz = 1.05
    kit.box((0.040, 0.044, 0.092), (0, -0.009, dz), STEEL, bevel=0.008, segments=1, name="dimmer pod")
    knob = kit.cylinder(0.0140, 0.014, (0, -0.037, dz + 0.012), STEEL, verts=12, rot=(90, 0, 0),
                        bevel=0.0, name="dimmer knob")
    drop_faces(knob, lambda n: n.z < -0.9)          # back cap is inside the pod

    # ---------------------------------------------------------------- bowl
    # Black spun-steel outside up to a rolled lip; 20 sides for the rim.
    outer = [(0.040, b - 0.001), (0.105, b + 0.020), (0.156, b + 0.054), (0.177, b + 0.076),
             (0.181, b + 0.0825), (0.175, b + 0.0860)]
    shell = kit.lathe(outer, (0, 0, 0), STEEL, verts=20, name="bowl outside",
                      close_top=False, close_bottom=False)
    face_towards(shell, lambda c: Vector((c.x, c.y, -0.6 * math.hypot(c.x, c.y) - 0.02)))
    # White enamel inside, meeting the inner edge of the lip.
    inside = [(0.175, b + 0.0860), (0.160, b + 0.0700), (0.0, b + 0.0150)]
    liner = kit.lathe(inside, (0, 0, 0), WHITE, verts=20, name="bowl inside",
                      close_top=False, close_bottom=False)
    face_towards(liner, lambda c: Vector((-c.x, -c.y, 1.0)))

    # Lamp holder: stamped bracket and the linear halogen tube (seen from
    # above when the lamp leans out of a pile).
    hz = b + 0.022
    kit.box((0.124, 0.022, 0.006), (0, 0, hz), STEEL, bevel=0.0, name="holder bracket")
    kit.box((0.012, 0.018, 0.022), (-0.058, 0, hz + 0.013), WHITE, bevel=0.0, name="ceramic clip")
    kit.box((0.012, 0.018, 0.022), (0.058, 0, hz + 0.013), WHITE, bevel=0.0, name="ceramic clip")
    kit.cylinder(0.0055, 0.106, (0, 0, hz + 0.017), WHITE, verts=6, rot=(0, 90, 0),
                 bevel=0.0, name="halogen tube")

    # ---------------------------------------------------------------- cord
    # Leaves the back of the base, curls round inside the bowl footprint
    # (so the lamp packs into a pile) and ends in a two-pin plug.
    kit.tube([(0, 0.128, 0.020), (0.004, 0.150, 0.004), (0.050, 0.172, 0.0032),
              (0.110, 0.158, 0.0032), (0.150, 0.125, 0.0032), (0.165, 0.082, 0.0032)],
             0.0032, STEEL, verts=4, name="power cord")
    kit.box((0.026, 0.034, 0.016), (0.166, 0.060, 0.008), STEEL, bevel=0.0, name="plug body")

    kit.anchor("light", (0, 0, TOP - 0.04))
    kit.anchor("dimmer", (0, -0.044, dz + 0.012))
    kit.no_collider()
    kit.tag("pile", "lamp", "domestic")
    kit.pile("Tall", mass=0, palette="domestic70s", topper=True, states=["Upright", "EdgeLean"])
