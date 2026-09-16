"""Complete starting position; assembly placement only, never a single print."""
from build123d import Compound, Pos, Rot
from dustlight_lib import panel, piece, PANEL_BOUNDS, STARTS, PITCH, BORDER, SURFACE
PRINTABLE = False

def gen_step():
    children=[]
    for index,(x,y,_,__) in enumerate(PANEL_BOUNDS):
        children.append(Pos(x,y,0)*panel(index))
    for team,starts in enumerate(STARTS):
        for rank,(x,y) in enumerate(starts,1):
            children.append(Pos(BORDER+PITCH*(x+.5),BORDER+PITCH*(y+.5),SURFACE)*Rot(0,0,180*team)*piece(team,rank))
    return Compound(label='dustlight_crossing',children=children)
