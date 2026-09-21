"""Derive exact display states and independently addressable production solids."""
from pathlib import Path
from build123d import export_step, Pos, Rot, Compound
from assembly import build_assembly
from periastra_lib import *

def write_states():
    root=Path(__file__).parent
    out=root.parent/'evidence-states'
    out.mkdir(exist_ok=True)
    export_step(build_assembly(LIFT),str(out/'opened.step'))
    export_step(build_assembly(include_roof=False),str(out/'playing.step'))
    examples=[]
    for i,(forked,king) in enumerate([(False,False),(False,True),(True,False),(True,True)]):
        shape=build_counter(forked)
        if not king:
            shape=Pos(0,0,COUNTER_HEIGHT)*Rot(Y=180)*shape
        shape=Pos((i-1.5)*CELL,0,0)*shape
        shape.label=f'counter_{i}'
        examples.append(shape)
    export_step(Compound(label='counter_states',children=examples),str(out/'counter_states.step'))

if __name__=='__main__':
    write_states()
