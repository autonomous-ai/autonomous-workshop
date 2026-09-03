"""Export exact endpoint and crossover assemblies for the motion signature."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from build123d import export_stl
from neststomp_lib import LEFT_X, RIGHT_X, make_assembly

OUT = ROOT / "review"
states = {
    "state_left.stl": make_assembly(LEFT_X, -5.0, 10.0, True),
    "state_center.stl": make_assembly(0.0, 0.0),
    "state_right.stl": make_assembly(RIGHT_X, 5.0, -10.0, True),
}
for name, shape in states.items():
    export_stl(shape, OUT / name)
    print(OUT / name)
