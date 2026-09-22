"""View-only assembly; print the separate part entries."""
from assemblies.product import assembled
PRINTABLE=False

def gen_step():
    return assembled()
