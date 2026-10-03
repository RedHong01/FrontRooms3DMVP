"""Unfinished stud doorway, 1.40 m clear (the middle of the map's 1.1-1.8 m
arch range). Same construction, tape and arch contract as Kit_DoorwayStuds
(see doorway_studs.py): clear passage 1.40 x 2.20 m, outer (the wall's
rough opening) 1.552 x 2.327 m, 0.14 m deep. Budget 800 / 300. Slots:
Studs, TapeBlue. Colliders: one per stud pair plus the header.
"""

from doorway_studs import build_frame

NAME = "Kit_DoorwayStuds140"
CLEAR = 1.40
LOD1 = 0.42
SMOOTH_ANGLE = 35.0


def build(kit):
    build_frame(kit, CLEAR, seed=2401)
