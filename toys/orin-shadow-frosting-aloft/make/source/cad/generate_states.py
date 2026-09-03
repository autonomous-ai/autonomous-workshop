from pathlib import Path
from build123d import export_step, export_stl
from state_lowered import lowered_shape
from state_mid import mid_shape

def main():
    out = Path(__file__).parent / "review" / "states"
    out.mkdir(parents=True, exist_ok=True)
    for name, shape in (("lowered", lowered_shape()), ("mid", mid_shape())):
        export_step(shape, str(out / f"{name}.step"))
        export_stl(shape, str(out / f"{name}.stl"), tolerance=0.08, angular_tolerance=0.1)

if __name__ == "__main__":
    main()
