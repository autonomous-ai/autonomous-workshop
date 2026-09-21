"""Printable occurrence lane_14_cocoa_brown; flat on the bed at Z0."""
from build123d import Location

from parts.tile import lane_tile_print

PRINTABLE = True


def gen_step():
    result = lane_tile_print(14).moved(Location())
    result.label = "lane_14_cocoa_brown"
    result.color = lane_tile_print(14).color
    return result
