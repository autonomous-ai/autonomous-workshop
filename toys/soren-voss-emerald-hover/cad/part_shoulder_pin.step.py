"""shoulder_pin: one manufactured solid in support-free print pose."""
import params as p
from parts.shoulder_pin import shoulder_pin
from features.primitives import on_bed
from validation import validate_parameters
PRINTABLE = True

def gen_step():
    validate_parameters()
    return on_bed(shoulder_pin(),p.PRINT_ROTATIONS['shoulder_pin'])
