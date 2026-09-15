"""Cratercade captive access door: latch_sleeve."""
from parts.access_door import latch_sleeve, print_pose
PRINTABLE = True
def gen_step():
    return print_pose(latch_sleeve(), 'latch_sleeve')
