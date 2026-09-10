"""The full 32-piece starting position and four-panel board. Millimetres."""
from build123d import Pos, Rot, Color
from cadgen.assembly import AssemblyHelper
from city_lib import BUILDERS, build_panel, build_dark_tile, FRAME, SQUARE, PANEL, BOARD_H, SEAT_Z, IVORY, MIDNIGHT, TILE_COLOR
PRINTABLE = False

def gen_step():
    asm=AssemblyHelper("civic_skyline")
    for qx in range(2):
        for qy in range(2):
            asm.add(Pos(qx*PANEL,qy*PANEL,0)*build_panel(qx,qy),f'board_{qx}_{qy}',color=Color(*IVORY))
    for f in range(8):
        for r in range(8):
            if (f+r)%2==0:
                asm.add(Pos(FRAME+SQUARE*(f+0.5),FRAME+SQUARE*(r+0.5),SEAT_Z)*build_dark_tile(),f'tile_{chr(97+f)}{r+1}',color=Color(*TILE_COLOR))
    back=['rook','knight','bishop','queen','king','bishop','knight','rook']
    for side,rank,pawns,color in [('ivory',0,1,IVORY),('midnight',7,6,MIDNIGHT)]:
        for f,role in enumerate(back):
            rot=180 if side=='midnight' else 0
            asm.add(Pos(FRAME+SQUARE*(f+0.5),FRAME+SQUARE*(rank+0.5),BOARD_H)*Rot(0,0,rot)*BUILDERS[role](),f'{side}_{role}_{chr(97+f)}{rank+1}',color=Color(*color))
        for f in range(8):
            asm.add(Pos(FRAME+SQUARE*(f+0.5),FRAME+SQUARE*(pawns+0.5),BOARD_H)*BUILDERS['pawn'](),f'{side}_pawn_{chr(97+f)}{pawns+1}',color=Color(*color))
    return asm.compound()
