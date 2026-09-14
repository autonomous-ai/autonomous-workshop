"""Algebraic loose-piece spacing audit; geometry is owned by standard gates."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from limbward_lib import BOARD_W,PITCH,FOOT_R,HEIGHTS,BODY_H,RIM_H
assert BOARD_W==8*PITCH==160
assert PITCH-2*FOOT_R==4
assert min(HEIGHTS.values())==12 and max(HEIGHTS.values())==34
assert BODY_H+min(HEIGHTS.values())>BODY_H+RIM_H
print('PASS:160 mm board;20 mm pitch;16 mm feet;4 mm spacing; all roles exceed rim.')
