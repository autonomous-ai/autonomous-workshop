"""Isolated printable mouth_back, bed datum Z=0."""
from seesaw_lib import print_part
PRINTABLE = True
def gen_step():
    return print_part("mouth_back")
