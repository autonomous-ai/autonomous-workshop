"""One physical drive_pin; local axis Y, manufacturing dimensions in params."""
import params as p
from features.primitives import axial_y, finish

def drive_pin():
    raw=axial_y(p.DRIVE_PIN_HEAD_R,-p.DRIVE_PIN_HEAD_T,0)+axial_y(p.DRIVE_PIN_D/2,-p.BOOLEAN_OVERLAP,p.DRIVE_PIN_LENGTH)
    return finish(raw,'wing_drive_pin',p.BRASS)
