"""Cratercade captive access door: frame."""
from parts.access_door import moving_frame, print_pose
PRINTABLE = True
def gen_step():
    return print_pose(moving_frame(), 'frame')
