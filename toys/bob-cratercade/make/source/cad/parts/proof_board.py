"""Neutral held-form blockout only; replaced by located tiles after early review."""
import params as p
from build123d import Pos
from features.primitives import bounded_box,z_cylinder
from parts.landing_ramp import seat_cutter

def build_blockout(holes=()):
    board=bounded_box(0,p.DECK_W,0,p.DECK_L,-p.DECK_T,0)
    for x,y in holes:
        board-=z_cylinder(x,y,-p.DECK_T,p.DECK_T,p.M4_BORE/2)
    board-=Pos(p.JACKPOT_AXIS[0],p.RAMP_Y0,0)*seat_cutter()
    return board
