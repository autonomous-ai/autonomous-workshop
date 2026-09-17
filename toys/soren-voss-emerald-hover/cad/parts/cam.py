"""One physical cam; local axis X, manufacturing dimensions in params."""
import params as p
from features.primitives import box_at, axial_x, d_shaft, finish

def cam():
    raw=axial_x(p.CAM_R,-p.CAM_T/2,p.CAM_T/2,p.ECCENTRICITY)
    raw=raw-d_shaft(p.CAM_BORE/2,p.SHAFT_FLAT,-p.CAM_T,p.CAM_T)
    return finish(raw,'eccentric_cam',p.BRASS)
