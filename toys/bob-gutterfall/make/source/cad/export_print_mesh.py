"""Export the complete fused source shape to the canonical printable STL."""
from build123d import export_step, export_stl
from gutterfall_v7_lib import build_gargoyle


if __name__ == "__main__":
    shape = build_gargoyle()
    export_step(shape, "gutterfall_final.step")
    export_stl(
        shape,
        "gutterfall.stl",
        tolerance=0.05,
        angular_tolerance=0.05,
    )
