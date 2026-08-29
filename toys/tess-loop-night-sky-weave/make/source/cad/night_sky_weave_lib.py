"""Parametric geometry for Night-Sky Weave's three reversible tile families."""

from math import isclose

from build123d import (
    Align,
    Box,
    BuildPart,
    BuildSketch,
    Compound,
    Cylinder,
    Plane,
    Pos,
    RectangleRounded,
    Rot,
    extrude,
)

# All dimensions are millimetres and are deliberate Wish-specific assumptions.
TILE_SIZE = 31.5
TILE_THICKNESS = 5.6
CORNER_RADIUS = 4.0
PLATE_GAP = 2.0
PITCH = TILE_SIZE + PLATE_GAP
MOSAIC_SIZE = 3 * TILE_SIZE + 2 * PLATE_GAP
RECESS_DEPTH = 1.2
EDGE_GATE_WIDTH = 1.8
EDGE_GATE_LENGTH = 7.0
CORE_THICKNESS = TILE_THICKNESS - 2 * RECESS_DEPTH
PIP_RADIUS = 1.1

FAMILIES = ("crescent", "comet", "star")


def validate_parameters():
    assert MOSAIC_SIZE == 98.5
    assert isclose(CORE_THICKNESS, 3.2, abs_tol=1e-9)
    assert EDGE_GATE_WIDTH >= 1.6
    assert CORNER_RADIUS > EDGE_GATE_WIDTH
    assert PLATE_GAP >= 2.0
    assert TILE_SIZE / 2 - EDGE_GATE_LENGTH <= 9.0


def _rounded_body():
    with BuildPart() as body:
        with BuildSketch(Plane.XY):
            RectangleRounded(TILE_SIZE, TILE_SIZE, CORNER_RADIUS)
        extrude(amount=TILE_THICKNESS)
    return body.part


def _dimple(x, y, radius, depth):
    return Pos(x, y, 0) * Cylinder(radius, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))


def _capsule(length, width, depth):
    """Rounded stroke centered on Y, avoiding acute decorative cusps."""
    radius = width / 2
    core = Box(width, length - width, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
    first = Pos(0, (length - width) / 2, 0) * Cylinder(
        radius, depth, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    second = Pos(0, -(length - width) / 2, 0) * Cylinder(
        radius, depth, align=(Align.CENTER, Align.CENTER, Align.MIN)
    )
    return core.fuse(first, second)


def _gate_tools(depth):
    vertical = _capsule(EDGE_GATE_LENGTH + EDGE_GATE_WIDTH, EDGE_GATE_WIDTH, depth)
    north = Pos(0, TILE_SIZE / 2 - EDGE_GATE_LENGTH / 2, 0) * vertical
    south = Rot(0, 0, 180) * north
    east = Rot(0, 0, -90) * north
    west = Rot(0, 0, 90) * north
    return Compound(children=[north, south, east, west])


def _family_center_tool(family, depth):
    if family == "crescent":
        # Four separated dimples trace a crescent while retaining >0.8 mm lands.
        points = [(-2.8, 4.3), (-5.1, 1.7), (-5.1, -1.7), (-2.8, -4.3)]
        return Compound(children=[_dimple(x, y, 1.1, depth) for x, y in points])
    if family == "comet":
        dots = [(-3.0, 3.0, 2.0), (0.0, 0.0, 1.1), (2.5, -2.5, 0.9), (4.5, -4.5, 0.7)]
        return Compound(children=[_dimple(x, y, radius, depth) for x, y, radius in dots])
    if family == "star":
        points = [(0, 0), (0, 4.7), (4.5, 1.45), (2.8, -3.8), (-2.8, -3.8), (-4.5, 1.45)]
        return Compound(children=[_dimple(x, y, 1.0 if x or y else 1.4, depth) for x, y in points])
    raise ValueError(f"unknown tile family: {family}")


def _pip_tools(family, depth):
    count = FAMILIES.index(family) + 1
    positions = [(-10.2, -10.2), (-7.0, -10.2), (-10.2, -7.0)]
    pips = [
        Pos(x, y, 0) * Cylinder(PIP_RADIUS, depth, align=(Align.CENTER, Align.CENTER, Align.MIN))
        for x, y in positions[:count]
    ]
    return Compound(children=pips)


def build_tile(family):
    """Return one closed tile solid in its flat print orientation."""
    validate_parameters()
    tile = _rounded_body()
    face_tool = _gate_tools(RECESS_DEPTH).fuse(_family_center_tool(family, RECESS_DEPTH)).fuse(
        _pip_tools(family, RECESS_DEPTH)
    )
    top_tool = Pos(0, 0, TILE_THICKNESS - RECESS_DEPTH) * face_tool
    bottom_tool = Rot(0, 0, 90) * face_tool
    tile = tile - top_tool - bottom_tool
    tile.label = f"{family}_tile"
    return tile


def build_mosaic():
    """Return nine labeled, non-touching tile solids in the pocket mosaic."""
    placements = []
    sequence = (
        "crescent", "comet", "star",
        "star", "crescent", "comet",
        "comet", "star", "crescent",
    )
    for index, family in enumerate(sequence):
        row, column = divmod(index, 3)
        x = (column - 1) * PITCH
        y = (1 - row) * PITCH
        placed = Pos(x, y, 0) * build_tile(family)
        placed.label = f"tile_{index + 1:02d}_{family}"
        placements.append(placed)
    assembly = Compound(children=placements)
    assembly.label = "night_sky_weave_nine_tile_mosaic"
    return assembly
