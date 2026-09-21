"""Printable occurrence lane_19_yellow; flat on the bed at Z0."""
from build123d import Location

from parts.tile import lane_tile_print

PRINTABLE = True


def gen_step():
    result = lane_tile_print(19).moved(Location())
    result.label = "lane_19_yellow"
    result.color = lane_tile_print(19).color
    return result
