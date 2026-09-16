"""Combined rest-state review assembly; use isolated entries for printing."""
from assemblies.pearl import assembly
PRINTABLE = False

def gen_step():
    return assembly()
