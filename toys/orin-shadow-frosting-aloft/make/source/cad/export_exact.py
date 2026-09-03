from pathlib import Path
from build123d import export_step, export_stl
from model import assembly

root = Path(__file__).parent
shape = assembly("raised")
export_step(shape, str(root / "frosting_aloft.step"))
export_stl(shape, str(root.parent / "assembled.stl"), tolerance=0.08, angular_tolerance=0.1)
