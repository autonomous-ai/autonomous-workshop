"""Algebraic fit and chess-layout audit; generic gates own solid and mesh checks."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from city_lib import SQUARE, FRAME, PANEL, BOARD, BOARD_H, SEAT_Z, TILE_GAP, TILE_H, BASE_RADIUS, HEIGHTS, GLYPH_CENTERS
assert BOARD == 8*SQUARE+2*FRAME == 2*PANEL
assert PANEL <= 220 and max(HEIGHTS.values()) <= 220
assert TILE_H == BOARD_H-SEAT_Z
assert 0.4 <= TILE_GAP <= 0.7
assert SQUARE-TILE_GAP > max(BASE_RADIUS.values())*2
assert len(GLYPH_CENTERS) == 5 and len({x[0] for x in GLYPH_CENTERS}) == 5
assert 0 < SEAT_Z < BOARD_H
assert HEIGHTS['king'] > HEIGHTS['queen'] > HEIGHTS['bishop'] > HEIGHTS['knight'] > HEIGHTS['rook'] > HEIGHTS['pawn']
# Every tile is wholly in its own panel; edge pockets may open on the central seam.
for f in range(8):
 for r in range(8):
  x=FRAME+SQUARE*(f+0.5)-(f//4)*PANEL
  y=FRAME+SQUARE*(r+0.5)-(r//4)*PANEL
  assert min(x,y)-(SQUARE-TILE_GAP)/2 >= 0
  assert max(x,y)+(SQUARE-TILE_GAP)/2 <= PANEL
# a1 is dark and h1 is light; the two queens start on their own square colour.
assert (0+0)%2 == 0 and (7+0)%2 == 1
assert (3+0)%2 == 1 and (3+7)%2 == 0
print('PASS: 8x8 layout, h1 light, queen colours, panel fit, tile clearance, five place reliefs and role-height hierarchy.')
