"""Unfinished stud doorway, 1.80 m clear (ArchMaxWidth). Same construction,
tape and arch contract as Kit_DoorwayStuds (see doorway_studs.py): clear
passage 1.80 x 2.20 m, outer (the wall's rough opening) 1.952 x 2.327 m,
0.14 m deep; the doubled 2x4 header is still plausible over 1.8 m in a
non-bearing partition. Budget 800 / 300. Slots: Studs, TapeBlue.
Colliders: one per stud pair plus the header.
"""

from doorway_studs import build_frame

NAME = "Kit_DoorwayStuds180"
CLEAR = 1.80
LOD1 = 0.42
SMOOTH_ANGLE = 35.0


def build(kit):
    build_frame(kit, CLEAR, seed=2402)
