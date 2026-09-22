"""Printed brass planet, 22 teeth, face5mm; bed datumZ0."""
from parts.gears import planet_by_teeth

def gen_step():
    return planet_by_teeth(22)
