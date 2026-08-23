"""Parametric spur gear with shaft bore and keyway.

Simplified trapezoidal teeth (not full involute) — visually correct,
geometrically sound, prints cleanly. Demonstrates polar arrays and the
canonical "build N copies of a 2D feature radially" pattern.

Tweak MODULE + TEETH together to change the gear pitch; OUTER_R follows.
"""

import math

import cadquery as cq

# --- Gear parameters ---
MODULE = 2.0          # mm per tooth (standard metric gear sizing)
TEETH = 24            # number of teeth
FACE_WIDTH = 8.0      # gear thickness
BORE = 6.0            # shaft hole diameter

# --- Keyway (optional; set to 0 to omit) ---
KEYWAY_W = 2.0
KEYWAY_DEPTH = 1.0

# --- Derived geometry ---
PITCH_R = MODULE * TEETH / 2.0
ADDENDUM = MODULE
DEDENDUM = 1.25 * MODULE
OUTER_R = PITCH_R + ADDENDUM
ROOT_R = PITCH_R - DEDENDUM
TOOTH_W_AT_PITCH = math.pi * MODULE / 2.0       # tooth width at pitch circle
ANGULAR_PITCH = 2 * math.pi / TEETH
HALF_TOOTH_ARC = math.atan2(TOOTH_W_AT_PITCH / 2.0, PITCH_R)

# A single trapezoidal tooth profile (in 2D, centered on +X axis):
#   - root-left, tip-left, tip-right, root-right
ROOT_HALF = HALF_TOOTH_ARC * 1.3           # slightly wider at root
TIP_HALF = HALF_TOOTH_ARC * 0.45           # narrower at tip

tooth_pts = [
    (ROOT_R * math.cos(-ROOT_HALF), ROOT_R * math.sin(-ROOT_HALF)),
    (OUTER_R * math.cos(-TIP_HALF), OUTER_R * math.sin(-TIP_HALF)),
    (OUTER_R * math.cos(TIP_HALF), OUTER_R * math.sin(TIP_HALF)),
    (ROOT_R * math.cos(ROOT_HALF), ROOT_R * math.sin(ROOT_HALF)),
]

tooth = (
    cq.Workplane("XY")
    .polyline(tooth_pts)
    .close()
    .extrude(FACE_WIDTH)
)

# Root disk (the dedendum cylinder all teeth ride on)
root_disk = cq.Workplane("XY").circle(ROOT_R).extrude(FACE_WIDTH)

# Union N teeth onto the root disk via polar rotation
gear = root_disk
for i in range(TEETH):
    angle = i * 360.0 / TEETH
    gear = gear.union(tooth.rotate((0, 0, 0), (0, 0, 1), angle))

# Shaft bore + optional keyway
gear = gear.faces(">Z").workplane().hole(BORE)

if KEYWAY_W > 0:
    keyway = (
        cq.Workplane("XY")
        .center(BORE / 2.0, -KEYWAY_W / 2.0)
        .rect(KEYWAY_DEPTH * 2, KEYWAY_W, centered=False)
        .extrude(FACE_WIDTH + 1)
        .translate((0, 0, -0.5))
    )
    gear = gear.cut(keyway)

result = gear
