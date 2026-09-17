"""One physical crank; local axis X, manufacturing dimensions in params."""
import params as p
from features.primitives import box_at, axial_x, d_shaft, finish

def crank():
    # Local X socket entrance at 0; print closed face down, so socket opens upward.
    collar=axial_x(p.CRANK_COLLAR_R,0,p.CRANK_THICKNESS)
    paddle=axial_x(p.CRANK_PADDLE_R,p.CRANK_ARM_X0,p.CRANK_THICKNESS,p.CRANK_RADIUS)
    arm=box_at(p.CRANK_ARM_X0,p.CRANK_THICKNESS,-p.CRANK_ARM_HALF_WIDTH,p.CRANK_RADIUS,-p.CRANK_ARM_HALF_WIDTH,p.CRANK_ARM_HALF_WIDTH)
    raw=collar+arm+paddle
    raw=raw-d_shaft(p.CAM_BORE/2,p.SHAFT_FLAT,-p.CUT_EXTENSION,p.CRANK_SOCKET_DEPTH)
    return finish(raw,'crank_keeper',p.BRASS)
