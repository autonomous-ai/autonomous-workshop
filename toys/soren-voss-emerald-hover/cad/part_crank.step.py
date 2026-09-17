"""crank: one manufactured solid in support-free print pose."""
import params as p
from parts.crank import crank
from features.primitives import on_bed
from validation import validate_parameters
PRINTABLE = True

def gen_step():
    validate_parameters()
    return on_bed(crank(),p.PRINT_ROTATIONS['crank'])
