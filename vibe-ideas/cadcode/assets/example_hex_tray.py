"""Honeycomb tray: rectangular grid of hex pockets in a plate.

Canonical example demonstrating: parametric grid via .pushPoints, hex via
.polygon(circumscribed=False), flat-to-flat math.
"""

import math

import cadquery as cq

# --- Parameters (mm) ---
CELL_FLAT = 20.0          # flat-to-flat distance (apothem * 2)
WALL = 2.0
BASE_H = 3.0
CELL_DEPTH = 18.0
COLS = 4
ROWS = 3

# --- Derived ---
R = CELL_FLAT / math.sqrt(3)              # circumradius
HEX_VERTEX = 2 * R                         # vertex-to-vertex distance

COL_SPACING = CELL_FLAT + WALL
ROW_SPACING = HEX_VERTEX + WALL

TRAY_W = COLS * CELL_FLAT + (COLS + 1) * WALL
TRAY_D = ROWS * HEX_VERTEX + (ROWS + 1) * WALL
TRAY_H = BASE_H + CELL_DEPTH

# Hex center positions (rectangular grid, NOT staggered honeycomb)
points = []
for row in range(ROWS):
    cy = WALL + HEX_VERTEX / 2 + row * ROW_SPACING - TRAY_D / 2
    for col in range(COLS):
        cx = WALL + CELL_FLAT / 2 + col * COL_SPACING - TRAY_W / 2
        points.append((cx, cy))

result = (
    cq.Workplane("XY")
    .box(TRAY_W, TRAY_D, TRAY_H)
    .faces(">Z")
    .workplane()
    .pushPoints(points)
    .polygon(6, CELL_FLAT, circumscribed=False)
    .cutBlind(-CELL_DEPTH)
)
