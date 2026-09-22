"""Print belly_07 broad seat down; bed Z=0. Geometry gates pending."""
from parts.decor import belly_print
PRINTABLE = True

def gen_step():
    return belly_print(6)
