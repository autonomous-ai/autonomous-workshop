"""One physical drive_cap; local axis Y, manufacturing dimensions in params."""
import params as p
from features.primitives import axial_y, finish

def drive_cap():
    raw=axial_y(p.DRIVE_CAP_R,0,p.DRIVE_CAP_LENGTH)-axial_y(p.DRIVE_CAP_BORE/2,-p.BOOLEAN_OVERLAP,p.DRIVE_CAP_SOCKET_DEPTH)
    return finish(raw,'wing_drive_keeper',p.BRASS)
