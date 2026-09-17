"""wing_left: one manufactured solid in support-free print pose."""
import params as p
from parts.wing_left import wing_left
from features.primitives import on_bed
from validation import validate_parameters
PRINTABLE = True

def gen_step():
    validate_parameters()
    return on_bed(wing_left(),p.PRINT_ROTATIONS['wing_left'])
