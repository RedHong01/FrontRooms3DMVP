"""Scratch test of creature_lib.humanoid_joints (delete after use)."""
NAME = "Hunter_ZZTest"
EYE = 1.60


def build(kit, cl):
    f = cl.humanoid_joints(height=2.02, hip=0.95, shoulder_half=0.27, stoop=14, head_forward=0.06, head_drop=0.10,
                           forearm=0.36, hand=0.22, neck_len=0.10)
    r = {"pelvis": (0.19, 0.13), "belly": (0.20, 0.14), "chest": (0.25, 0.16), "neck": 0.08,
         "shoulder_l": 0.09, "shoulder_r": 0.09, "elbow_l": 0.06, "elbow_r": 0.06, "wrist_l": 0.05, "wrist_r": 0.05,
         "hand_l": (0.035, 0.05), "hand_r": (0.035, 0.05), "head": (0.10, 0.115), "crown": 0.07,
         "hip_l": 0.10, "hip_r": 0.10, "cuff_l": 0.045, "cuff_r": 0.045, "neck_base": 0.07, "shin_l": 0.05, "shin_r": 0.05, "seat_l": 0.09, "seat_r": 0.09, "knee_l": 0.07, "knee_r": 0.07, "ankle_l": 0.055, "ankle_r": 0.055,
         "toe_l": (0.045, 0.035), "toe_r": (0.045, 0.035)}
    jacket = cl.BODY_BONES + cl.SHOULDER_BONES + cl.ARM_BONES["l"] + cl.ARM_BONES["r"]
    cl.part(kit, f, r, jacket, "Prop_FabricCharcoal", name="jacket")
    cl.part(kit, f, r, cl.LEG_BONES, "Prop_FabricCharcoal", name="trousers")
    cl.part(kit, f, r, cl.HEAD_BONES, "Creature_SkinPale", name="head")
    for s in ("l", "r"):
        cl.part(kit, f, r, cl.HAND_BONES[s], "Creature_SkinPale", name="hand " + s)
        cl.part(kit, f, r, cl.FOOT_BONES[s], "Prop_PlasticBlack", name="shoe " + s)
    cl.floor_parts(kit)
    kit.no_collider()
