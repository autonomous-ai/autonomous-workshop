"""Source-controlled chess placements; freely handled pieces, no coupled mechanism."""
from build123d import Compound,Pos,Rot
from tidal_lib import board,man,CELL,BOARD_HEIGHT
from functools import lru_cache
from copy import deepcopy

BACK=['rook','knight','bishop','queen','king','bishop','knight','rook']

def square(name):
    return (-63+(ord(name[0])-97)*CELL,-63+(int(name[1])-1)*CELL,BOARD_HEIGHT)

@lru_cache(maxsize=13)
def prototype(role,side):
    return board() if role=='board' else man(role,side)

def positioned(role,side,label,xyz):
    shape=deepcopy(prototype(role,side))
    # Horse-neck side profiles face both seated players; head orientation has no rule meaning.
    angle=0 if role!='knight' else (0 if side=='white' else 180)
    shape=Pos(*xyz)*Rot(0,0,angle)*shape
    shape.label=label
    return shape

def placements(state):
    rows=[]
    if state in ('before','after'):
        return [('king','white','white_king',square('f6')),('queen','white','white_queen',square('h1' if state=='before' else 'h8')),('king','black','black_king',square('f8'))]
    for side,rank,pawn_rank in [('white',1,2),('black',8,7)]:
        seen={}
        for f,role in enumerate(BACK):
            seen[role]=seen.get(role,0)+1
            label=side+'_'+role+('' if seen[role]==1 else '_2')
            rows.append((role,side,label,square(chr(97+f)+str(rank))))
        for f in range(8):
            label=side+'_pawn'+('' if f==0 else '_'+str(f+1))
            rows.append(('pawn',side,label,square(chr(97+f)+str(pawn_rank))))
        rows.append(('queen',side,side+'_queen_spare',(-112 if side=='white' else 112,0,0)))
    if state=='crowded':
        # Legal opening after1.e4 e5 2.Nf3 Nc6 3.Bc4 Bc5 4.d3 d6.
        moves={'white_pawn_5':'e4','black_pawn_5':'e5','white_knight_2':'f3','black_knight':'c6','white_bishop_2':'c4','black_bishop_2':'c5','white_pawn_4':'d3','black_pawn_4':'d6'}
        rows=[(r,s,l,square(moves[l]) if l in moves else xyz) for r,s,l,xyz in rows]
    return rows

def build_state(state='initial'):
    children=[deepcopy(prototype('board','board'))]
    children.extend(positioned(*row) for row in placements(state))
    return Compound(label='tidal_crown',children=children)
