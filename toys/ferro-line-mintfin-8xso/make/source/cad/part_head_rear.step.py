"""Mintfin head_rear; one physical print, flat bed datum Z=0."""
from parts.head import head_rear
PRINTABLE = True
def gen_step():
    return head_rear()
