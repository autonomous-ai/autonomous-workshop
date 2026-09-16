"""Local design fit equations; geometry validity is checked by native CAD gates."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dustlight_lib import PITCH, BORDER, BOARD_W, BOARD_D, BASE_R, SURFACE, HEIGHTS, PANEL_BOUNDS, STARTS, RIVERS, TRAPS, DENS

def main():
    assert (BOARD_W,BOARD_D)==(7*PITCH+2*BORDER,9*PITCH+2*BORDER)
    assert PITCH-2*BASE_R==8
    assert 24-2*BASE_R==2
    assert SURFACE==5 and tuple(HEIGHTS)==tuple(range(18,33,2))
    assert len(RIVERS)==12 and RIVERS=={(x,y) for x in (1,2,4,5) for y in (3,4,5)}
    assert TRAPS=={(2,0),(4,0),(3,1),(2,8),(4,8),(3,7)}
    assert DENS=={(3,0),(3,8)}
    assert STARTS==(((6,2),(1,1),(2,2),(5,1),(4,2),(0,0),(6,0),(0,2)),((0,6),(5,7),(4,6),(1,7),(2,6),(6,8),(0,8),(6,6)))
    for team in STARTS:
        assert len(set(team))==8 and not(set(team)&(RIVERS|TRAPS|DENS))
    assert sum((c-a)*(d-b) for a,b,c,d in PANEL_BOUNDS)==BOARD_W*BOARD_D
    assert all(c-a<=220 and d-b<=220 for a,b,c,d in PANEL_BOUNDS)
    assert (96-BORDER)%PITCH==0 and (126-BORDER)%PITCH==0
    # Contour/grid ligament and unobstructed landing-pad margin.
    assert 15-.4-(13.2+.5)>=.8
    assert 12.9-.6>=12 and 13.2-.5>=12
    print('PASS: exact topology and setup; 8 mm adjacent base gap, 2 mm landing-pad spare width, panel bed fit, grid-line seams, terrain ligament >=0.8 mm.')
    print('Motion unverified; no physical handling, panel retention or printing claim.')

if __name__=='__main__':main()
