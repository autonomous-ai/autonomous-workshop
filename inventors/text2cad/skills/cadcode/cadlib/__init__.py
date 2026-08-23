"""cadcode helper library — composable CadQuery building blocks.

Import the helpers, don't copy-paste from references. Example:

    import cadquery as cq
    from cadlib.enclosure import hollow_box
    from cadlib.mounting import add_screw_post
    from cadlib.layout import four_corner_points

    body = hollow_box(length=80, width=60, height=30, wall=2.0, corner_radius=4)
    body = add_screw_post(
        body,
        positions=four_corner_points(length=80, width=60, margin=5),
        screw_size="M3",
        boss_height=12,
        hole_type="self_tap",
    )

    def gen_step():
        return body

Each helper follows the convention:

- pure function, returns a new ``cq.Workplane`` (does not mutate ``part``)
- keyword-only arguments (no positional surprises)
- raises ``ValueError`` on impossible parameter combinations (so failures
  point at the spec, not at OCCT five frames deep)
- has a docstring with units, parameter ranges, and one example

Each module is its own focused topic:

- ``cadlib.enclosure``   — hollow boxes, lid lips, shells
- ``cadlib.mounting``    — screw bosses, heat-set pockets, nut traps
- ``cadlib.cutouts``     — press-fit / magnet / bearing / cable channels
- ``cadlib.mechanical``  — snap fits, dovetails, rib stiffeners
- ``cadlib.fits``        — FDM mating clearances: derive a slot/peg from one nominal
- ``cadlib.styling``     — unified radius language: soften / chamfer edges, derive radii
- ``cadlib.layout``      — point generators (corner / grid / circle)
- ``cadlib.tables``      — canonical hardware dimension tables

When no helper fits, write custom geometry directly in the user's ``.py``
in a function named ``custom_<feature>()`` — that's a signal that the
library is missing a helper, worth promoting later.
"""
