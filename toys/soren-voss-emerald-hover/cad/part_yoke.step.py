import params as p
"""yoke: one manufactured solid in support-free print pose."""
from parts.yoke import yoke
from features.primitives import on_bed
from validation import validate_parameters
PRINTABLE = True
def gen_step():
    validate_parameters()
    return on_bed(yoke(), p.PRINT_ROTATIONS["yoke"])
