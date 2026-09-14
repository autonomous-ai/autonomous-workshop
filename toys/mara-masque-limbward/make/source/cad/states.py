"""Exact placements of loose pieces; no joints or optical simulation."""
from build123d import Pos, Rot, Color, export_step
from cadgen.assembly import AssemblyHelper
from limbward_lib import camera_board, piece, COLORS, PITCH, BODY_H
from collections import Counter
from pathlib import Path

BACK=('rook','knight','bishop','queen','king','bishop','knight','rook')

def square_xy(square):
    return (-70+PITCH*(ord(square[0])-97),-60+PITCH*(int(square[1])-1))

def placements(state='inventory'):
    rows=[('camera_board','camera_board',None,(0,0,0),0)]
    counts=Counter()
    def add(side,role,square=None,off=None):
        key=side+'_'+role
        counts[key]+=1
        name=key if counts[key]==1 else f'{key}_{counts[key]:02}'
        xyz=(*square_xy(square),BODY_H) if square else (*off,0)
        rows.append((name,key,side,xyz,180 if side=='black' else 0))
    if state in ('before','after'):
        add('white','king','a1');add('white','rook','h1' if state=='before' else 'h8');add('black','king','a8')
        return rows
    for side,rank,pawns in (('white',1,2),('black',8,7)):
        for file,role in enumerate(BACK):add(side,role,chr(97+file)+str(rank))
        for file in range(8):add(side,'pawn',chr(97+file)+str(pawns))
    if state=='inventory':
        for side,x0 in (('white',-156),('black',116)):
            for col,role in enumerate(('queen','rook','bishop','knight')):
                for row in range(8):add(side,role,off=(x0+20*col,118+20*row))
    return rows

def build_scene(state='inventory'):
    asm=AssemblyHelper('limbward_'+state)
    originals={}
    for name,key,side,xyz,angle in placements(state):
        if key not in originals:
            originals[key]=camera_board() if key=='camera_board' else piece(side,key.split('_')[1])
        shape=Pos(*xyz)*Rot(0,0,angle)*originals[key]
        asm.add(shape,name,color=Color(*COLORS[side or 'camera']))
    return asm.build()

def gen_step():
    """Sparse exact fixture for the requested unconstrained rook motion audit."""
    return build_scene('before')

if __name__=='__main__':
    dest=Path(__file__).parent/'states';dest.mkdir(exist_ok=True)
    for state in ('setup','before','after'):
        export_step(build_scene(state),dest/(state+'.step'))
        print('wrote exact state',state)
