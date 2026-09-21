"""Printable occurrence lane_10_cocoa_brown; flat on the bed at Z0."""
from build123d import Location

from parts.tile import lane_tile_print

PRINTABLE = True


def gen_step():
    result = lane_tile_print(10).moved(Location())
    result.label = "lane_10_cocoa_brown"
    result.color = lane_tile_print(10).color
    return result
