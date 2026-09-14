import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import quayshift_lib as q
assert q.BOARD==5*q.PITCH+2*q.MARGIN
assert q.FERRY_RADIUS*2+6==q.PITCH
assert q.CABIN_WIDTH==12 and q.CABIN_LENGTH==18
assert q.HIGH_SPRING-q.FERRY_HEIGHT>=2
assert q.PORTAL_Y+q.PORTAL_DEPTH==q.PITCH-q.INSET
print('PASS shared grid, opening envelope, cabin and rear print datum')
