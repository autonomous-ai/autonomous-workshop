"""One flat-base printed mission crater."""
import params as p
from parts import crater
PRINTABLE=True

def gen_step():
    return crater.build()
