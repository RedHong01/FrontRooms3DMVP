"""Freestanding 1990s systems-furniture partition panel, 60" wide x 65" tall:
the high privacy panel used on about 10 % of pods (§4.5). At 1.65 m it is
the only panel height that blocks the Hunter's 1.6 m sight ray (spec §7).
Same construction as Kit_CubiclePanel (see cubicle_panel.py): fabric on both
faces, rounded putty top cap, end trims with slotted standards, dark base
rail on two levelling glides. 1.524 m wide, 1.65 m tall, 64 mm thick.
"""

from cubicle_panel import build_panel

NAME = "Kit_CubiclePanelTall"
LOD1 = 0.45


def build(kit):
    build_panel(kit, 1.524, 1.65)
    # Pile use: OfficeCluster only (office90s palette). The class filters of
    # CentreSculpture / CopyPasteRow would take a Case panel, so
    # FrontRoomsFurniturePile.BuildPile must drop "office_cluster_only"
    # entries unless tableau == OfficeCluster (C# side, not wired yet).
    kit.pile("Case", mass=1, states=["Upright", "Side", "Back"], palette="office90s")
    kit.tag("office_cluster_only")
