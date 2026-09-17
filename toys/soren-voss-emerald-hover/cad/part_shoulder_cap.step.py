"""shoulder_cap: one manufactured solid in support-free print pose."""
import params as p
from parts.shoulder_cap import shoulder_cap
from features.primitives import on_bed
from validation import validate_parameters
PRINTABLE = True

def gen_step():
    validate_parameters()
    return on_bed(shoulder_cap(),p.PRINT_ROTATIONS['shoulder_cap'])
