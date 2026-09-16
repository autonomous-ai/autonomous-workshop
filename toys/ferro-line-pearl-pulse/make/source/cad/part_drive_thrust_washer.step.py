"""Flat annular drive thrust washer."""
from parts.drive import drive_thrust_washer
from features.common import bed
PRINTABLE = True

def gen_step():
    return bed(drive_thrust_washer())
