"""wing_right: one manufactured solid in support-free print pose."""
import params as p
from parts.wing_right import wing_right
from features.primitives import on_bed
from validation import validate_parameters
PRINTABLE = True

def gen_step():
    validate_parameters()
    return on_bed(wing_right(),p.PRINT_ROTATIONS['wing_right'])
