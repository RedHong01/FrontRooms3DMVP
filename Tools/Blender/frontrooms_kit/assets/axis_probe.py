"""Calibration asset: a 1 m cube with a nose on its FRONT (-Y) and a mast on
top (+Z). Used once to verify the Blender -> Unity axis mapping."""

NAME = "Kit_AxisProbe"


def build(kit):
    kit.box((1.0, 1.0, 1.0), (0, 0, 0.5), "Prop_PlasticGrey", bevel=0.02)
    kit.box((0.2, 0.4, 0.2), (0, -0.7, 0.5), "Prop_WoodCherry", bevel=0.01, name="front nose")
    kit.box((0.1, 0.1, 0.6), (0.3, 0, 1.3), "Prop_SteelPutty", bevel=0.01, name="mast at +x")
    kit.support("top", (0, 0, 1.0), (1.0, 1.0))
    kit.anchor("nose", (0, -0.9, 0.5))
