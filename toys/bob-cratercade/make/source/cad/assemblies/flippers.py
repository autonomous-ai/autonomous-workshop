"""Flipper placement only; root supplies deck incline and fastener instances."""
from build123d import Axis, Pos
import params as p
from parts.flipper import rotor
from parts.flipper_pedestal import pedestal
from parts.flipper_sleeve import sleeve
from parts.flipper_guard_base import guard_base
from parts.flipper_guard import guard


def local_components(side="left", fraction=0.0, covers=True):
    assert side in p.FLIPPER_PIVOTS and 0.0 <= fraction <= 1.0
    direction = 1 if side == "left" else -1
    angle = direction * p.FLIPPER_TRAVEL * fraction
    parts = [
        (f"flipper_{side}_rotor", rotor(side).rotate(Axis.Z, angle), "#F28C32", {"moving":True,"joint":"revolute","axis":[0,0,1],"origin":[0,0,0],"limits":[0,direction*p.FLIPPER_TRAVEL]}),
        (f"flipper_{side}_pedestal", pedestal(), "#174B6B", {"moving":False}),
        (f"flipper_{side}_sleeve", sleeve(), "#A7C4C8", {"moving":False}),
        (f"flipper_{side}_guard_base", guard_base(side), "#174B6B", {"moving":False}),
    ]
    if covers:
        parts.append((f"flipper_{side}_guard",guard(side),"#287998",{"moving":False,"removable":True}))
    for label, shape, _, _ in parts:
        shape.label = label
    return parts


def components(left_fraction=0.0, right_fraction=0.0, covers=True):
    out = []
    for side, fraction in (("left",left_fraction),("right",right_fraction)):
        x, y = p.FLIPPER_PIVOTS[side]
        for label, shape, color, metadata in local_components(side,fraction,covers):
            placed = Pos(x,y,0) * shape
            placed.label = label
            out.append((label,placed,color,metadata))
    return out
