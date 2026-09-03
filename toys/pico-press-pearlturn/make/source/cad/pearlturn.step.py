from build123d import Compound
from pearlturn_lib import build_shell, build_pearl

PRINTABLE = False

def gen_step():
    shell = build_shell()
    pearl = build_pearl()
    return Compound(children=[shell, pearl], label="Pearlturn")
