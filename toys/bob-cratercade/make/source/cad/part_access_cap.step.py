"""Cratercade captive access door: cap."""
from parts.access_door import cap, print_pose
PRINTABLE = True
def gen_step():
    return print_pose(cap(), 'cap')
