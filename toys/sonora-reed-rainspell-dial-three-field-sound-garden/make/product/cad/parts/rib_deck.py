"""Indexed 46-event rib deck."""

from __future__ import annotations

from build123d import Align, Cylinder, Location

import params as p
from features.primitives import rib_bar


def _add_field(deck, field, angles, heights):
    radial_inner, radial_outer = p.RIB_RADIAL_SPANS[field]
    for index, (angle, height) in enumerate(zip(angles, heights)):
        offset = 0.0
        if field == "crickets":
            offset = p.CRICKET_PACKET_OFFSETS[index // 5]
        rib = rib_bar(
            radial_inner + offset,
            radial_outer + offset,
            p.rib_root_width(height),
            height,
            p.WORKING_RADIUS + offset,
            angle,
            p.RIB_CREST_WIDTH,
            p.RIB_CREST_RADIUS,
        )
        deck += Location((0, 0, p.DECK_THICKNESS)) * rib
    return deck


def build_rib_deck():
    alignment = (Align.CENTER, Align.CENTER, Align.MIN)
    deck = Cylinder(p.DECK_RADIUS, p.DECK_THICKNESS, align=alignment) - Cylinder(p.DECK_BORE_RADIUS, p.DECK_THICKNESS + 0.2, align=alignment)
    top_edges = [edge for edge in deck.edges() if abs(edge.center().Z - p.DECK_THICKNESS) < 1e-6]
    deck = deck.chamfer(0.8, None, top_edges)
    deck = _add_field(deck, "rain", p.RAIN_ANGLES, p.RAIN_HEIGHTS)
    deck = _add_field(deck, "frog_song", p.FROG_ANGLES, p.FROG_HEIGHTS)
    deck = _add_field(deck, "crickets", p.CRICKET_ANGLES, p.CRICKET_HEIGHTS)
    return deck
