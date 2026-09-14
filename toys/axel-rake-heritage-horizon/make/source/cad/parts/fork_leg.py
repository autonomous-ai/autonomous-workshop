from build123d import *
from params import *
from features.common import box_bounds, plate_link, cylinder_y, prism_xz

def build():
    y=SUPPORT_INNER;t=SUPPORT_THICKNESS
    s=plate_link(FRAME_FORK_TOP,(AXLE_X[1],AXLE_Z),FRAME_FORK_RADIUS,y,t)
    # Broad pad bridges to the fender's side face without entering its band.
    pad=prism_xz(FRAME_FENDER_PAD,y,t)
    s=s.fuse(cylinder_y(FRAME_AXLE_BOSS_R,t,AXLE_X[1],y,AXLE_Z),box_bounds((*FRAME_FORK_LAP_X,y,y+t,*FRAME_FORK_LAP_Z)),pad)
    return s.cut(cylinder_y(AXLE_BORE/2,t+2*FRAME_CUT_MARGIN,AXLE_X[1],y-FRAME_CUT_MARGIN,AXLE_Z))
