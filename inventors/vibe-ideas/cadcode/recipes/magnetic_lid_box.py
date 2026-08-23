"""Recipe: D10x3 magnetic lid box (60 x 60 x 25 mm).

The 2 mm shell rim is narrower than a D10 magnet. Each base pocket therefore
sits in a full-height corner boss fused into both adjacent walls; cutting a
circle in the empty cavity would not make a usable pocket. Base and lid remain
named, separately printable assembly parts.
"""

from __future__ import annotations

import cadquery as cq

from cadlib.cutouts import add_magnet_pocket
from cadlib.enclosure import hollow_box
from cadlib.layout import four_corner_points
from cadlib.tables import MAGNET_TABLE


class Params:
    length = 60.0
    width = 60.0
    height = 25.0
    wall = 2.0
    corner_radius = 3.0
    lid_thickness = 4.0
    magnet_size = "10x3"
    magnet_margin = 8.0
    magnet_boss_wall = 2.0
    top_wall = 0.0
    lid_gap = 0.5


def magnet_points(p: Params) -> list[tuple[float, float]]:
    return four_corner_points(
        length=p.length,
        width=p.width,
        margin=p.magnet_margin,
    )


def build_base_supports(p: Params) -> cq.Workplane:
    """Build the shell plus four wall-connected magnet columns."""
    shell = hollow_box(
        length=p.length,
        width=p.width,
        height=p.height,
        wall=p.wall,
        corner_radius=p.corner_radius,
    )
    magnet = MAGNET_TABLE[p.magnet_size]
    pocket_radius = (magnet["d"] + 0.2) / 2
    boss_radius = pocket_radius + p.magnet_boss_wall
    points = magnet_points(p)

    for x, y in points:
        assert abs(x) + boss_radius <= p.length / 2
        assert abs(y) + boss_radius <= p.width / 2
        assert abs(x) + boss_radius > p.length / 2 - p.wall
        assert abs(y) + boss_radius > p.width / 2 - p.wall

    bosses = (
        cq.Workplane("XY")
        .pushPoints(points)
        .circle(boss_radius)
        .extrude(p.height)
        .translate((0, 0, -p.height / 2))
    )
    return shell.union(bosses)


def build_base(p: Params) -> cq.Workplane:
    assert p.top_wall == 0, "this recipe requires post-print-accessible pockets"
    return add_magnet_pocket(
        build_base_supports(p),
        positions=magnet_points(p),
        magnet_size=p.magnet_size,
        fit_type="slip",
        top_wall=p.top_wall,
        open_face=">Z",
    )


def build_lid(p: Params) -> cq.Workplane:
    lid = cq.Workplane("XY").box(p.length, p.width, p.lid_thickness)
    if p.corner_radius > 0:
        lid = lid.edges("|Z").fillet(p.corner_radius)
    magnet = MAGNET_TABLE[p.magnet_size]
    assert p.top_wall == 0, "this recipe requires post-print-accessible pockets"
    assert p.lid_thickness > magnet["h"] + 0.1, (
        "lid must leave solid material behind the magnet pocket"
    )
    return add_magnet_pocket(
        lid,
        positions=magnet_points(p),
        magnet_size=p.magnet_size,
        fit_type="slip",
        top_wall=p.top_wall,
        open_face="<Z",
    )


def _place_assembly(
    p: Params,
    base_part: cq.Workplane,
    lid_part: cq.Workplane,
) -> cq.Assembly:
    lid_z = (p.height + p.lid_thickness) / 2 + p.lid_gap
    result = cq.Assembly()
    result.add(base_part, name="base", color=cq.Color(0.80, 0.82, 0.85))
    result.add(
        lid_part,
        name="lid",
        loc=cq.Location((0, 0, lid_z)),
        color=cq.Color(0.30, 0.55, 0.90),
    )
    return result


def assembly(p: Params) -> cq.Assembly:
    return _place_assembly(p, build_base(p), build_lid(p))


p = Params()
magnet_pts = magnet_points(p)
base_before_pockets = build_base_supports(p)
base = add_magnet_pocket(
    base_before_pockets,
    positions=magnet_pts,
    magnet_size=p.magnet_size,
    fit_type="slip",
    top_wall=p.top_wall,
    open_face=">Z",
)
lid = build_lid(p)


def gen_step():
    return _place_assembly(p, base, lid)
