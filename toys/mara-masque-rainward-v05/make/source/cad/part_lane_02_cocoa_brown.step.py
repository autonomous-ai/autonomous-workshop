"""Printable occurrence lane_02_cocoa_brown; flat on the bed at Z0."""
from build123d import Location

from parts.tile import lane_tile_print

PRINTABLE = True


def gen_step():
    result = lane_tile_print(2).moved(Location())
    result.label = "lane_02_cocoa_brown"
    result.color = lane_tile_print(2).color
    return result
