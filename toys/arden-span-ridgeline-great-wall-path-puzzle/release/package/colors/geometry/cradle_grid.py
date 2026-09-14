"""RIDGELINE cradle cues: recessed grid, numbered cells and a north tab.

Units are mm. The tile support plane stays at Z=4; marks cut downwards.
No tile, route, cell pitch or placement changes.
"""
from math import atan2, degrees, hypot
from build123d import Axis, Face, Solid, Vector, Wire

FLOOR = 4.0
PITCH = 56.0
GRID_HALF_LENGTH = 84.2
GRID_WIDTH = 1.2
MARK_DEPTH = 0.6
NUMBER_HEIGHT = 10.0
NUMBER_WIDTH = 6.0
NUMBER_STROKE = 1.2
TAB_OUTLINE = [(-18, 82.5), (18, 82.5), (18, 92), (15, 95), (-15, 95), (-18, 92)]


def prism(points, direction):
    return Solid.extrude(Face(Wire.make_polygon(points, close=True)), Vector(direction))


def v_stroke(x1, y1, x2, y2, width=NUMBER_STROKE):
    length = hypot(x2-x1, y2-y1)
    # The tiny extension above the floor makes a clean cut; floor width is
    # exactly the specified value, with 45-degree flanks when width=1.2.
    overshoot = 0.05
    top_half = width / 2 * (1 + overshoot / MARK_DEPTH)
    tool = prism([(0, -top_half, FLOOR+overshoot),
                  (0, top_half, FLOOR+overshoot),
                  (0, 0, FLOOR-MARK_DEPTH)], (length, 0, 0))
    return tool.rotate(Axis.Z, degrees(atan2(y2-y1, x2-x1))).translate((x1, y1, 0))


SEGMENTS = {
    'a': ((-3, 5), (3, 5)), 'b': ((3, 5), (3, 0)),
    'c': ((3, 0), (3, -5)), 'd': ((-3, -5), (3, -5)),
    'e': ((-3, 0), (-3, -5)), 'f': ((-3, 5), (-3, 0)),
    'g': ((-3, 0), (3, 0)),
}
DIGITS = {'0': 'abcdef', '2': 'abged', '3': 'abgcd', '4': 'fgbc',
          '5': 'afgcd', '6': 'afgecd', '7': 'abc', '8': 'abcdefg'}


def marking_tools():
    grid = []
    for offset in (-PITCH/2, PITCH/2):
        grid.append(v_stroke(offset, -GRID_HALF_LENGTH, offset, GRID_HALF_LENGTH, GRID_WIDTH))
        grid.append(v_stroke(-GRID_HALF_LENGTH, offset, GRID_HALF_LENGTH, offset, GRID_WIDTH))
    numbers = []
    for cell in range(9):
        cx, cy = PITCH*(cell % 3-1), PITCH*(1-cell//3)
        segments = [((0, -5), (0, 5))] if cell == 1 else [SEGMENTS[k] for k in DIGITS[str(cell)]]
        for (x1, y1), (x2, y2) in segments:
            numbers.append(v_stroke(cx+x1, cy+y1, cx+x2, cy+y2))
    # N and a north-facing arrow remain visible beyond the tiles.
    north = [v_stroke(*a, *b) for a, b in [
        ((-7, 88), (-7, 92.5)), ((-7, 92.5), (-3, 88)), ((-3, 88), (-3, 92.5)),
        ((5, 87.7), (5, 92.7)), ((2.5, 90.2), (5, 92.7)), ((5, 92.7), (7.5, 90.2)),
    ]]
    return {'grid': grid, 'numbers': numbers, 'north': north}


def enhance_cradle(original):
    tab = prism([(x, y, 0) for x, y in TAB_OUTLINE], (0, 0, FLOOR))
    shape = original.fuse(tab)
    tools = marking_tools()
    shape = shape.cut(*(tools['grid'] + tools['numbers'] + tools['north'])).clean()
    assert len(shape.solids()) == 1 and shape.is_valid
    shape.label = 'cradle'
    return shape
