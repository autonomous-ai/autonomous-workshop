"""One physical shoulder_cap; local axis Y, manufacturing dimensions in params."""
import params as p
from features.primitives import axial_y, finish

def shoulder_cap():
    raw=axial_y(p.SHOULDER_CAP_R,0,p.SHOULDER_CAP_LENGTH)-axial_y(p.PIN_CAP_BORE/2,-p.BOOLEAN_OVERLAP,p.SHOULDER_CAP_SOCKET_DEPTH)
    return finish(raw,'shoulder_keeper',p.BRASS)
