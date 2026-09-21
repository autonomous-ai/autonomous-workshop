"""Printable occurrence lane_05_yellow; flat on the bed at Z0."""
from build123d import Location

from parts.tile import lane_tile_print

PRINTABLE = True


def gen_step():
    result = lane_tile_print(5).moved(Location())
    result.label = "lane_05_yellow"
    result.color = lane_tile_print(5).color
    return result
