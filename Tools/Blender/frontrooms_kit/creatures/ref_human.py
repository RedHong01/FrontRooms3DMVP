"""Scale reference for the Hunter line-ups: a neutral 1.80 m adult (the
player is a 1.75 m capsule with the eye at 1.62 m). Grey mannequin, A-pose
arms, no features. Not a concept; the look-dev harness draws it beside every
line-up instead of a capsule."""

NAME = "Ref_Human180"
TITLE = "1.80 m human"
EYE = 1.68
SLOT = "Prop_PlasticGrey"


def build(kit, cl):
    j = {
        "pelvis": ((0, 0, 0.98), (0.17, 0.11)),
        "belly": ((0, 0, 1.15), (0.15, 0.10)),
        "chest": ((0, 0, 1.36), (0.17, 0.11)),
        "neck": ((0, 0, 1.55), 0.055),
        "head": ((0, -0.01, 1.68), (0.085, 0.10)),
        "crown": ((0, 0, 1.81), 0.05),
        "shoulder_l": ((0.19, 0, 1.45), 0.06), "shoulder_r": ((-0.19, 0, 1.45), 0.06),
        "elbow_l": ((0.25, 0.01, 1.17), 0.045), "elbow_r": ((-0.25, 0.01, 1.17), 0.045),
        "wrist_l": ((0.29, -0.02, 0.92), 0.035), "wrist_r": ((-0.29, -0.02, 0.92), 0.035),
        "hand_l": ((0.30, -0.03, 0.83), (0.03, 0.045)), "hand_r": ((-0.30, -0.03, 0.83), (0.03, 0.045)),
        "hip_l": ((0.10, 0, 0.92), 0.08), "hip_r": ((-0.10, 0, 0.92), 0.08),
        "knee_l": ((0.11, -0.01, 0.50), 0.055), "knee_r": ((-0.11, -0.01, 0.50), 0.055),
        "ankle_l": ((0.11, 0.01, 0.08), 0.04), "ankle_r": ((-0.11, 0.01, 0.08), 0.04),
        "toe_l": ((0.11, -0.15, 0.035), (0.045, 0.035)), "toe_r": ((-0.11, -0.15, 0.035), (0.045, 0.035)),
    }
    b = [("pelvis", "belly"), ("belly", "chest"), ("chest", "neck"), ("neck", "head"), ("head", "crown"),
         ("chest", "shoulder_l"), ("shoulder_l", "elbow_l"), ("elbow_l", "wrist_l"), ("wrist_l", "hand_l"),
         ("chest", "shoulder_r"), ("shoulder_r", "elbow_r"), ("elbow_r", "wrist_r"), ("wrist_r", "hand_r"),
         ("pelvis", "hip_l"), ("hip_l", "knee_l"), ("knee_l", "ankle_l"), ("ankle_l", "toe_l"),
         ("pelvis", "hip_r"), ("hip_r", "knee_r"), ("knee_r", "ankle_r"), ("ankle_r", "toe_r")]
    body = cl.skin_body(kit, j, b, SLOT, subdiv=2)
    cl.decimate_to(body, 6000)
    # Sit the skinned result exactly on the floor (skin radii push the soles below 0).
    lo = min(v.co.z for v in body.data.vertices)
    for v in body.data.vertices:
        v.co.z -= lo
    kit.no_collider()
