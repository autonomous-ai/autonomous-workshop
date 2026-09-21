"""One physical shaft; local axis X, manufacturing dimensions in params."""
import params as p
from features.primitives import box_at, axial_x, d_shaft, finish

def shaft():
    raw=axial_x(p.SHAFT_FLANGE_D/2,p.SHAFT_LEFT-p.SHAFT_FLANGE_T,p.SHAFT_LEFT)
    raw=raw+d_shaft(p.SHAFT_D/2,p.SHAFT_FLAT,p.SHAFT_LEFT-p.BOOLEAN_OVERLAP,p.SHAFT_RIGHT)
    return finish(raw,'headed_d_shaft',p.DARK_BRASS)
