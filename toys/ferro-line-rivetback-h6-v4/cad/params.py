"""Single source of invented RIVETBACK H-6 dimensions (millimetres)."""

import cadfits

nozzle = 0.4
bed_width = 180.0
bed_depth = 180.0
bed_height = 180.0

yellow_rgb = (217 / 255, 165 / 255, 20 / 255)
black_rgb = (25 / 255, 27 / 255, 28 / 255)
cable_rgb = (215 / 255, 215 / 255, 205 / 255)
steel_rgb = (82 / 255, 88 / 255, 92 / 255)

chassis_width = 68.0
chassis_depth = 76.0
chassis_height = 16.0
chassis_assembly_z = 30.0
chassis_corner_cut = 15.0

small_peg = 4.0
small_socket = cadfits.slot_for(small_peg, 0.20)
small_peg_length = 4.5
dorsal_key = 8.0
dorsal_socket = cadfits.slot_for(dorsal_key, 0.25)
hip_peg = 8.0
hip_socket = cadfits.slot_for(hip_peg, 0.25)
hip_peg_length = 7.0
tenon_width = 8.0
tenon_height = 8.0
tenon_socket_width = cadfits.slot_for(tenon_width, 0.25)
tenon_socket_height = cadfits.slot_for(tenon_height, 0.25)
tenon_length = 6.0
pin_diameter = 3.2
pin_hole = cadfits.slot_for(pin_diameter, 0.20)
pin_length = 18.0

# Public ledger aliases used by the numeric spec audit. [assumed]
NOZZLE_MM = nozzle
SMALL_PEG_CLEARANCE_MM = (small_socket - small_peg) / 2
HIP_CLEARANCE_MM = (hip_socket - hip_peg) / 2
TENON_CLEARANCE_MM = (tenon_socket_width - tenon_width) / 2
PIN_CLEARANCE_MM = (pin_hole - pin_diameter) / 2

plate_width = 64.0
plate_height = 6.0
plate_depths = {"fore": 36.0, "center": 28.0, "aft": 30.0}
plate_centers_y = {"fore": 29.0, "center": -3.0, "aft": -32.0}
plate_assembly_z = 46.0
plate_peg_x = 15.0
PLATE_WIDTH_MM = plate_width

yoke_length = 10.0
yoke_width = 14.0
yoke_height = 12.0
upper_dx = 32.0
upper_dz = -7.0
upper_width = 10.0
upper_height = 9.0
lower_dx = 18.0
lower_dz = -25.0
lower_width = 9.0
lower_height = 8.0
foot_length = 24.0
foot_width = 12.0
foot_height = 8.0
foot_socket_z = 3.8

leg_roots = {
    "rf": ((29.0, 25.0, 38.0), 32.0),
    "rm": ((34.0, 0.0, 38.0), 0.0),
    "rr": ((29.0, -25.0, 38.0), -32.0),
    "lf": ((-29.0, 25.0, 38.0), 148.0),
    "lm": ((-34.0, 0.0, 38.0), 180.0),
    "lr": ((-29.0, -25.0, 38.0), -148.0),
}

assert small_socket > small_peg
assert dorsal_socket > dorsal_key
assert hip_socket > hip_peg
assert tenon_socket_width > tenon_width
assert tenon_socket_height > tenon_height
assert pin_hole > pin_diameter
