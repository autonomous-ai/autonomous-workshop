"""Print claw broad seat down; bed Z=0. Geometry gates pending."""
from parts.decor import claw_print
PRINTABLE = True

def gen_step():
    return claw_print()
