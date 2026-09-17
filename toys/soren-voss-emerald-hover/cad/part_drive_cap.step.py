"""drive_cap: one manufactured solid in support-free print pose."""
import params as p
from parts.drive_cap import drive_cap
from features.primitives import on_bed
from validation import validate_parameters
PRINTABLE = True

def gen_step():
    validate_parameters()
    return on_bed(drive_cap(),p.PRINT_ROTATIONS['drive_cap'])
