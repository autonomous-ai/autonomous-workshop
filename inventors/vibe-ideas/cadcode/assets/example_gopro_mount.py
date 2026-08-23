"""GoPro-style 3-finger mount — the universal action-camera attachment.

Three parallel fingers spaced for a 2-finger receiving end, M5 bolt hole
through all three, mounted on a flat baseplate with screw holes.

Demonstrates: standard mechanical tolerances (GoPro spec), fillets/chamfers
for both ergonomics and printability, .pushPoints for fastener arrays.
"""

import cadquery as cq

# --- GoPro 3-finger spec (web-sourced standard; verify against the current
#     GoPro interface spec — these are the well-known nominal values) ---
FINGER_W = 3.0          # each finger thickness (mm)
FINGER_GAP = 3.0        # gap between fingers — must be ≥3mm to receive 2-finger end
FINGER_DIAMETER = 18.0  # diameter of the circular finger cap
BOLT_DIAMETER = 5.5     # M5 clearance hole

# --- Stem (connects fingers to baseplate) ---
STEM_W = 14.0
STEM_H = 12.0           # height from baseplate top to bolt center
STEM_T = FINGER_W * 3 + FINGER_GAP * 2  # total stack of all 3 fingers + 2 gaps

# --- Baseplate ---
BASE_L = 50.0
BASE_W = 30.0
BASE_H = 5.0
MOUNT_HOLE = 4.5        # M4 clearance
MOUNT_SPACING_X = 38.0  # screw hole spacing along long axis

# --- Aesthetics ---
EDGE_FILLET = 0.8

# --- Build baseplate ---
base = (
    cq.Workplane("XY")
    .box(BASE_L, BASE_W, BASE_H)
    .edges("|Z")
    .fillet(3.0)             # corner-round the plate
    .faces(">Z")
    .workplane()
    .pushPoints([(-MOUNT_SPACING_X / 2, 0), (MOUNT_SPACING_X / 2, 0)])
    .cboreHole(MOUNT_HOLE, 8.0, 2.5)   # countersink for M4 cap screws
)

# --- Build stem rising from baseplate ---
stem = (
    cq.Workplane("XY")
    .workplane(offset=BASE_H / 2)
    .box(STEM_T, STEM_W, STEM_H, centered=(True, True, False))
)

# --- Build 3-finger head ---
# Stack: finger | gap | finger | gap | finger, total = STEM_T
# Each finger: rectangular at the stem side, circular cap at the bolt end.
# Build as a single solid (3 fingers + filler material between bolt and stem),
# then cut the gaps and the bolt hole.

bolt_z = BASE_H / 2 + STEM_H + FINGER_DIAMETER / 2 - 2  # bolt center height

# Solid block that contains all 3 finger volumes
head_block = (
    cq.Workplane("XY")
    .workplane(offset=BASE_H / 2 + STEM_H - 2)
    .box(STEM_T, STEM_W, FINGER_DIAMETER, centered=(True, True, False))
)

# Round the head: cylinder at the bolt center, unioned, then cut to a half-pill
head_round = (
    cq.Workplane("YZ")
    .workplane(offset=-STEM_T / 2)
    .center(0, bolt_z)
    .circle(FINGER_DIAMETER / 2)
    .extrude(STEM_T)
)

head = head_block.union(head_round)

# Cut the two gaps between the three fingers
for sign in (-1, 1):
    gap_x = sign * (FINGER_W + FINGER_GAP) / 2.0
    gap = (
        cq.Workplane("XY")
        .workplane(offset=BASE_H / 2 + STEM_H - 1)
        .center(gap_x, 0)
        .box(FINGER_GAP, STEM_W + 1, FINGER_DIAMETER + 2,
             centered=(True, True, False))
    )
    head = head.cut(gap)

# Bolt hole through all 3 fingers (X axis)
bolt_hole = (
    cq.Workplane("YZ")
    .workplane(offset=-STEM_T / 2 - 1)
    .center(0, bolt_z)
    .circle(BOLT_DIAMETER / 2)
    .extrude(STEM_T + 2)
)
head = head.cut(bolt_hole)

# Combine base + stem + head. Skip the global edge fillet — OCCT can fail
# on complex combined geometry. If you want soft edges, add them per-region.
result = base.union(stem).union(head)
