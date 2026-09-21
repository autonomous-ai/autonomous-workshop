"""Combined neutral assembly; production print entries are separate part_ files."""
from assemblies.hummingbird import build
PRINTABLE=False

def gen_step():
    return build(0)
