"""One physical shoulder_pin; local axis Y, manufacturing dimensions in params."""
import params as p
from features.primitives import axial_y, finish

def shoulder_pin():
    raw=axial_y(p.SHOULDER_PIN_HEAD_R,-p.SHOULDER_PIN_HEAD_T,0)+axial_y(p.HINGE_PIN_D/2,-p.BOOLEAN_OVERLAP,p.SHOULDER_PIN_LENGTH)
    return finish(raw,'shoulder_pin',p.BRASS)
