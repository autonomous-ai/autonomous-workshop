"""Cratercade captive access door: receiver."""
from parts.access_door import receiver, print_pose
PRINTABLE = True
def gen_step():
    return print_pose(receiver(), 'receiver')
