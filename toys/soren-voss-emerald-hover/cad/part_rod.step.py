import params as p
"""rod: one manufactured solid in support-free print pose."""
from parts.rod import rod
from features.primitives import on_bed
from validation import validate_parameters
PRINTABLE = True
def gen_step():
    validate_parameters()
    return on_bed(rod(), p.PRINT_ROTATIONS["rod"])
