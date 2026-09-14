"""Cratercade captive access door: lever."""
from parts.access_door import latch_lever, print_pose
PRINTABLE = True
def gen_step():
    return print_pose(latch_lever(), 'lever')
