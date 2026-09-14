"""Cratercade captive access door: hinge_sleeve."""
from parts.access_door import hinge_sleeve, print_pose
PRINTABLE = True
def gen_step():
    return print_pose(hinge_sleeve(), 'hinge_sleeve')
