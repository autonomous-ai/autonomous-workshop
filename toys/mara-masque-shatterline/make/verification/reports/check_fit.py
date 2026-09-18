"""Project-specific algebraic fit audit; generic tools measure the solids."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from veinwake_lib import (SEAT_DIAMETER,FOOT_DIAMETER,SEAT_CLEARANCE,GRID_PITCH,
                         SEAT_Z,FIELD_HEIGHT,SEAT_DEPTH,CLUSTER_HEIGHT,
                         ASSEMBLED_HEIGHT,DRAW_CELLS,GRID)

def main():
    assert 0.99 <= (SEAT_DIAMETER-FOOT_DIAMETER)/2 <= 1.01
    assert SEAT_CLEARANCE == 1.0
    assert GRID_PITCH - SEAT_DIAMETER >= 3.0
    assert SEAT_Z >= 3.0 and FIELD_HEIGHT-SEAT_Z == SEAT_DEPTH == 2.0
    assert SEAT_Z+CLUSTER_HEIGHT == ASSEMBLED_HEIGHT == 32.0
    assert len(GRID) == len(set(GRID)) == 9
    assert DRAW_CELLS.count('X') == 5 and DRAW_CELLS.count('O') == 4
    p=Path(__file__).resolve().parents[1]
    names={'rind'}|{f'tooth_{i}' for i in range(1,6)}|{f'bubble_{i}' for i in range(1,5)}
    assert {q.name.removeprefix('part_').removesuffix('.step.py') for q in p.glob('part_*.step.py')} == names
    print('PASS: shared seat band, spacing, floor, envelope, inventory and role naming. Open upward placement/removal; floor stops downward travel.')

if __name__ == '__main__':
    main()
