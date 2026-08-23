"""Knurled tactile knob — for shafts, dials, volume controls.

A cylindrical body with N radial knurling grooves around its perimeter,
a chamfered top, and an interference-fit shaft hole with optional
hex insert for an M3 set screw.

Demonstrates: polar arrays of cutting features (knurling), chamfers,
multi-feature fastener handling.
"""

import math

import cadquery as cq

# --- Knob body ---
KNOB_D = 30.0        # outer diameter
KNOB_H = 14.0        # height
TOP_CHAMFER = 1.5    # top edge chamfer
BOTTOM_CHAMFER = 0.5 # bottom edge chamfer

# --- Shaft hole ---
SHAFT_D = 6.0        # nominal shaft diameter
SHAFT_FIT = 0.0      # +slop on the hole (0 = press-fit; 0.2 for free-fit)
SHAFT_DEPTH = 11.0   # how deep the shaft goes (leave 3mm of cap)

# --- Knurling ---
N_KNURLS = 36                  # number of grooves
KNURL_D = 1.4                  # diameter of each groove (cut depth)
KNURL_INSET = 0.6              # depth into the cylinder from outer surface

# --- Optional set-screw hole (M3 grub screw radially into the shaft hole) ---
SET_SCREW = True
M3_TAP = 2.5                   # tap drill for M3 (or use 3.4 for clearance)
SET_SCREW_Z = KNOB_H / 2.0     # height of the set-screw hole

# --- Build the body ---
body = (
    cq.Workplane("XY")
    .circle(KNOB_D / 2)
    .extrude(KNOB_H)
    .edges(">Z").chamfer(TOP_CHAMFER)
    .edges("<Z").chamfer(BOTTOM_CHAMFER)
)

# --- Knurling: polar array of small cylindrical grooves ---
groove_r = KNURL_D / 2.0
groove_center_r = KNOB_D / 2.0 - KNURL_INSET + groove_r   # how far out the groove sits
for i in range(N_KNURLS):
    theta = 2 * math.pi * i / N_KNURLS
    cx = groove_center_r * math.cos(theta)
    cy = groove_center_r * math.sin(theta)
    groove = (
        cq.Workplane("XY")
        .center(cx, cy)
        .circle(groove_r)
        .extrude(KNOB_H + 1)
        .translate((0, 0, -0.5))
    )
    body = body.cut(groove)

# --- Shaft hole (from bottom) ---
body = (
    body
    .faces("<Z").workplane()
    .hole(SHAFT_D + SHAFT_FIT, depth=SHAFT_DEPTH)
)

# --- Set-screw hole (perpendicular, into the shaft pocket) ---
if SET_SCREW:
    set_screw = (
        cq.Workplane("XZ")
        .workplane(offset=-KNOB_D / 2 - 1)
        .center(0, SET_SCREW_Z)
        .circle(M3_TAP / 2.0)
        .extrude(KNOB_D)
    )
    body = body.cut(set_screw)

result = body
