"""Face and head reference parameters; user measured dimensions from DESIGN."""
from math import sin, cos, radians
from params import DESIGN
FACE = DESIGN['face']
OUTLINE = [tuple(p) for p in FACE['outline']]
MAGNETS = [(-17,6),(17,6),(0,-13)]
MAGNET_D = 8.15
MAGNET_DEPTH = 1.2
BASE_T = 1.4
BACK_T = 1.2
FACE_T = BASE_T + BACK_T
FACE_ORIGIN = (0,-2.9,36)
FACE_ANGLE = 78.0
COLORS = DESIGN['colors']
HEAD_STATIONS = [(-6,26.5,16.0),(-3,29,18.5),(2,31,21),(10,32.8,22.7),(20,33.25,23),(30,31.8,22),(40,27.5,19),(47,19,14),(51,11,9)]
HEAD_SPLIT_Y = 20
HEAD_CENTER_Z = 36
JOINT = DESIGN['joints'][0]
EYE_DIAMETER = 15
EYE_HEIGHT = 6.7
EYE_FOOT_HEIGHT = 1.2  # [assumed] full-width foot removes thin spherical base edge
HIGHLIGHT_RECESS_FLOOR = 5.0
FEATURE_BASE = FACE_T

# Posterior headstock accommodation preserves the first barrel crown at25deg.
HEAD_REAR_Y = 45.4
HEAD_REAR_HALF_HEIGHT = 15.654565935

NOSTRIL_HEIGHT = 1.0  # [assumed] robust height above0.8mm standing-feature minimum
TONGUE_CENTER_V = -0.8  # local to smile; keeps a substantial lower border
TONGUE_HEIGHT = 1.0  # slight raised inset above the smile recess
