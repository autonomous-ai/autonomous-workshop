"""Recipe: one-part open storage bin with a provably empty interior.

Use this shape when the request explicitly forbids internal posts, dividers,
skins, or other solids. The final B-rep is checked over the complete requested
cavity volume; a few hand-picked center probes are not accepted as proof.
"""

from __future__ import annotations

import cadquery as cq

from cadlib.validation import verify_bbox, verify_clearance_box


class Params:
    width = 80.0
    depth = 60.0
    height = 40.0
    wall = 3.0
    floor = 3.0
    boolean_overshoot = 0.5


p = Params()

outer = cq.Workplane("XY").box(
    p.width,
    p.depth,
    p.height,
    centered=(True, True, False),
)
cavity_width = p.width - 2 * p.wall
cavity_depth = p.depth - 2 * p.wall
cavity_height = p.height - p.floor + p.boolean_overshoot
cavity = (
    cq.Workplane("XY")
    .box(cavity_width, cavity_depth, cavity_height)
    .translate((0, 0, p.floor + cavity_height / 2))
)
body = outer.cut(cavity)

extent_proof = verify_bbox(
    shape=body,
    expected_size=(p.width, p.depth, p.height),
    expected_min=(-p.width / 2, -p.depth / 2, 0),
    expected_max=(p.width / 2, p.depth / 2, p.height),
    label="storage bin",
)
cavity_proof = verify_clearance_box(
    part=body,
    expected_min=(-cavity_width / 2, -cavity_depth / 2, p.floor),
    expected_max=(cavity_width / 2, cavity_depth / 2, p.height),
    open_faces=("+Z",),
    label="empty storage cavity",
)


def gen_step():
    return body
