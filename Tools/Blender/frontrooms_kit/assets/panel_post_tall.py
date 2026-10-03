"""Connector post for the 1.65 m Kit_CubiclePanelTall pods (§4.5: about
10 % of pods, the only panel height that blocks the Hunter's 1.6 m sight
ray). Same construction as Kit_PanelPost (see panel_post.py): 64 x 64 mm
rounded putty steel post, chamfered end cap flush with the 1.65 m panel
caps, levelling glide. One slot, no collider.
"""

from panel_post import build_post

NAME = "Kit_PanelPostTall"
H = 1.65


def build(kit):
    build_post(kit, H)
