"""Derive exact display states and independently addressable production solids."""
from pathlib import Path
import re
from build123d import export_step, Pos, Rot, Compound
from assembly import build_assembly
from periastra_lib import *

# export_step stamps the wall clock into the STEP header; zero it so the same
# geometry always hashes the same. See export_delivery.py.
STAMP = re.compile(r"(FILE_NAME\('[^']*',')[^']*(')")


def export_deterministic(shape, path):
    export_step(shape, str(path))
    path = Path(path)
    path.write_text(STAMP.sub(r"\g<1>1970-01-01T00:00:00\g<2>", path.read_text(), count=1))

FACES = [('sun-man', False, False), ('sun-king', False, True),
         ('moon-man', True, False), ('moon-king', True, True)]


def write_states():
    root = Path(__file__).parent
    out = root.parent/'evidence-states'
    out.mkdir(exist_ok=True)
    export_deterministic(build_assembly(LIFT), out/'opened.step')
    export_deterministic(build_assembly(include_roof=False), out/'playing.step')
    examples = []
    for i, (name, forked, king) in enumerate(FACES):
        shape = build_counter(forked)
        if king:
            # The disc is round, so its mark's bearing on the board is free. Turn the king
            # face to the same bearing the flipped man face lands on, so one camera shows
            # both faces of a counter alike. Presentation only; the solid is unchanged.
            shape = Rot(Z=180)*shape
        else:                             # built man-face-down; flip to show the man face
            shape = Pos(0, 0, COUNTER_HEIGHT)*Rot(Y=180)*shape
        shape.label = name
        shape.color = FORKED_COLOR if forked else SINGLE_COLOR
        export_deterministic(shape, out/f'counter-{name}.step')
        examples.append(Pos((i-1.5)*CELL, 0, 0)*shape)
    export_deterministic(Compound(label='counter_states', children=examples), out/'counter_states.step')


if __name__ == '__main__':
    write_states()
