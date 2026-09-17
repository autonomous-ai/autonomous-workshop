"""drive_pin: one manufactured solid in support-free print pose."""
import params as p
from parts.drive_pin import drive_pin
from features.primitives import on_bed
from validation import validate_parameters
PRINTABLE = True

def gen_step():
    validate_parameters()
    return on_bed(drive_pin(),p.PRINT_ROTATIONS['drive_pin'])
