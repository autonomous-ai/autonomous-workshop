from build123d import *
from params import *
from features.common import box_bounds, plate_link, cylinder_y

def build():
    y=SUPPORT_INNER; t=SUPPORT_THICKNESS
    s=plate_link(*FRAME_SWING_LINK,y,t)
    pieces=[cylinder_y(FRAME_AXLE_BOSS_R,t,AXLE_X[0],y,AXLE_Z),box_bounds((*FRAME_SWING_TAB_X,y,y+t,*FRAME_SWING_TAB_Z))]
    for x in FRAME_BAG_MOUNTS:
        pieces += [plate_link(FRAME_BAG_STEM_ROOT,(x,FRAME_BAG_MOUNT_Z),FRAME_BAG_STEM_R,y,t),
          box_bounds((x-FRAME_BAG_STEM_R,x+FRAME_BAG_STEM_R,y,y+t,*FRAME_BAG_STEM_Z)),
          box_bounds((x-FRAME_BAG_PIN_HALF,x+FRAME_BAG_PIN_HALF,y+t,FRAME_BAG_INNER_Y,*FRAME_BAG_SHELF_Z)),
          box_bounds((x-FRAME_BAG_PIN_HALF,x+FRAME_BAG_PIN_HALF,FRAME_BAG_INNER_Y,FRAME_BAG_PIN_END,*FRAME_BAG_PIN_Z))]
    return s.fuse(*pieces).cut(cylinder_y(AXLE_BORE/2,t+2*FRAME_CUT_MARGIN,AXLE_X[0],y-FRAME_CUT_MARGIN,AXLE_Z))
