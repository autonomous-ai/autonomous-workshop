"""Printable occurrence lane_07_yellow; flat on the bed at Z0."""
from build123d import Location

from parts.tile import lane_tile_print

PRINTABLE = True


def gen_step():
    result = lane_tile_print(7).moved(Location())
    result.label = "lane_07_yellow"
    result.color = lane_tile_print(7).color
    return result
