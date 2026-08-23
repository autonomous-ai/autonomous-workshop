"""A minimalist desk valet tray — a premium-product example.

Demonstrates the aesthetic discipline from ``references/industrial-design.md``:
a single unified corner radius across the whole body (a deliberate radius
language, not a scatter of raw arrises), a crisp chamfer breaking the top rim so
it catches one clean line of light, and a soft inner floor fillet — all done
through the ``cadlib.styling`` helpers so the radius *choice* lives in one place.

Function first: walls stay a printable 2.4 mm, the corner radius is derived from
the plan size (never larger than the wall can carry), and the top chamfer
doubles as a support-free overhang break.
"""

import cadquery as cq

from cadlib.styling import break_edges, design_radius_for, soften_edges

LENGTH = 130.0  # mm, outer
WIDTH = 85.0  # mm, outer
HEIGHT = 28.0  # mm, outer
WALL = 2.4  # mm, uniform (6 perimeters at 0.4 nozzle — rigid)
FLOOR = 2.4  # mm

# One radius language for the whole object, derived from the short plan edge.
CORNER_R = design_radius_for(size=WIDTH)  # 0.08 * 85 -> clamped to 4.0 mm
RIM_CHAMFER = 1.0  # mm, the single crisp line on the top edge
FLOOR_FILLET = 3.0  # mm, soft cavity floor (comfortable, prints clean face-down)


def gen_step():
    # Monolithic outer form with unified vertical corners.
    body = cq.Workplane("XY").box(LENGTH, WIDTH, HEIGHT)
    body = soften_edges(body, radius=CORNER_R, selector="|Z")

    # Hollow it into a tray (cavity opens up).
    body = body.faces(">Z").shell(-WALL)

    # Soft inner floor: round the bottom-of-cavity edges so the recess reads
    # intentional, not milled. Scoped to the internal bottom edges.
    body = soften_edges(body, radius=FLOOR_FILLET, selector="<Z")

    # One crisp chamfer on the top rim — the premium line, and a support-free
    # break for the printed top edge.
    body = break_edges(body, size=RIM_CHAMFER, selector=">Z")

    return body
