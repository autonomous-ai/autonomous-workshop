"""One flat-base printed mission guide."""
import params as p
from parts import mission_guide
PRINTABLE=True

def gen_step():
    return mission_guide.build()
