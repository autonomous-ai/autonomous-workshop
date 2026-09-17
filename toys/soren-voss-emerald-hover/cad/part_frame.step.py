import params as p
from parts.frame import *
from features.primitives import on_bed
from validation import validate_parameters
PRINTABLE=True
def gen_step():
    validate_parameters()
    return on_bed(frame(),(0,0,0))
