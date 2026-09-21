"""Placement only. Closed state is canonical; opened state is exact +Z lift."""
from build123d import Pos, Rot, Location
from cadgen.assembly import AssemblyHelper
from periastra_lib import *

def build_assembly(lift=0.0, include_roof=True):
    assert 0 <= lift <= LIFT
    asm = AssemblyHelper('periastra')
    base = asm.add(build_base(),'base',color=BASE_COLOR)
    if include_roof:
        roof = asm.add(build_roof(),'roof',color=ROOF_COLOR)
        seat = asm.rigid_frame(base,'roof_seat',Location((0,0,LEDGE_TOP+lift)))
        underside = asm.rigid_frame(roof,'roof_underside',Location((0,0,0)))
        asm.face_to_face(seat,underside)
    for forked, rows in [(False,range(3)),(True,range(5,8))]:
        counter = build_counter(forked)
        n=0
        for r in rows:
            for c in range(ROWS):
                if (c+r)%2 == 0:
                    n += 1
                    x = -BOARD/2+(c+0.5)*CELL
                    y = -BOARD/2+(r+0.5)*CELL
                    name = ('forked_' if forked else 'single_')+f'{n:02d}'
                    pose=Pos(x,y,FLOOR-RECESS+COUNTER_HEIGHT)*Rot(Z=180 if forked else 0)*Rot(Y=180)
                    asm.add(pose*counter,name,color=FORKED_COLOR if forked else SINGLE_COLOR)
    return asm.compound()
