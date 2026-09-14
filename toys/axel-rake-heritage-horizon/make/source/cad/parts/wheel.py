"""Common wheel: planar bed side, six broad spokes recessed on outer side only."""
from build123d import *
from features.common import cylinder_y, annular_sector
from params import (WHEEL_RADIUS, WHEEL_WIDTH, AXLE_BORE, BODY_WHEEL_CHAMFER,
    BODY_WHEEL_SPOKES, BODY_WHEEL_POCKET_RADII, BODY_WHEEL_POCKET_ANGLES,
    BODY_WHEEL_POCKET_Y_DEPTH, BODY_WHEEL_BORE_TOOL_Y_LENGTH)

def build():
    tyre=cylinder_y(WHEEL_RADIUS,WHEEL_WIDTH,0,-WHEEL_WIDTH/2,0)
    tyre=chamfer(tyre.edges(),length=BODY_WHEEL_CHAMFER)
    # Six shallow pockets leave a continuous structural disc and broad spokes.
    pitch,start,end=BODY_WHEEL_POCKET_ANGLES
    for i in range(BODY_WHEEL_SPOKES):
        tyre=tyre-annular_sector(0,0,*BODY_WHEEL_POCKET_RADII,
            i*pitch+start,i*pitch+end,*BODY_WHEEL_POCKET_Y_DEPTH)
    y,length=BODY_WHEEL_BORE_TOOL_Y_LENGTH
    return tyre-cylinder_y(AXLE_BORE/2,length,0,y,0)
