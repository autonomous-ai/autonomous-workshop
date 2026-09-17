"""Single source of invented RIVETBACK H-6 dimensions (millimetres)."""

import cadfits

nozzle = 0.4
bed_width = 180.0
bed_depth = 180.0
bed_height = 180.0

yellow_rgb = (217 / 255, 165 / 255, 20 / 255)
black_rgb = (25 / 255, 27 / 255, 28 / 255)
cyan_rgb = (37 / 255, 199 / 255, 217 / 255)

chassis_width = 78.0
chassis_depth = 92.0
chassis_height = 18.0
chassis_assembly_z = 35.0
chassis_corner_cut = 13.0

small_peg = 4.0
small_socket = cadfits.slot_for(small_peg, 0.20)
small_peg_length = 4.5
hip_peg = 8.0
hip_socket = cadfits.slot_for(hip_peg, 0.25)
hip_peg_length = 7.0
tenon_width = 8.0
tenon_height = 6.0
tenon_socket_width = cadfits.slot_for(tenon_width, 0.25)
tenon_socket_height = cadfits.slot_for(tenon_height, 0.25)
tenon_length = 6.0
pin_diameter = 5.0
pin_hole = cadfits.slot_for(pin_diameter, 0.20)
pin_length = 13.5

# Public ledger aliases used by the numeric spec audit. [assumed]
NOZZLE_MM = nozzle
SMALL_PEG_CLEARANCE_MM = (small_socket - small_peg) / 2
HIP_CLEARANCE_MM = (hip_socket - hip_peg) / 2
TENON_CLEARANCE_MM = (tenon_socket_width - tenon_width) / 2
PIN_CLEARANCE_MM = (pin_hole - pin_diameter) / 2

plate_width = 88.0
plate_height = 8.0
plate_depths = {"fore": 36.0, "center": 38.0, "aft": 34.0}
plate_centers_y = {"fore": 36.0, "center": 0.0, "aft": -36.0}
plate_assembly_z = 55.0
plate_peg_x = 20.0
PLATE_WIDTH_MM = plate_width

hub_width = 28.0
hub_depth = 30.0
hub_height = 18.0
hub_center_y = 7.0
hub_assembly_z = 53.0

yoke_length = 12.0
yoke_width = 14.0
yoke_height = 12.0
upper_dx = 24.0
upper_dz = -8.0
upper_width = 11.0
upper_height = 10.0
lower_dx = 18.0
lower_dz = -29.0
lower_width = 9.0
lower_height = 9.0
foot_length = 18.0
foot_width = 13.0
foot_height = 10.0

leg_roots = {
    "rf": ((34.0, 30.0, 44.0), 28.0),
    "rm": ((39.0, 0.0, 44.0), 0.0),
    "rr": ((34.0, -30.0, 44.0), -28.0),
    "lf": ((-34.0, 30.0, 44.0), 152.0),
    "lm": ((-39.0, 0.0, 44.0), 180.0),
    "lr": ((-34.0, -30.0, 44.0), -152.0),
}

assert small_socket > small_peg
assert hip_socket > hip_peg
assert tenon_socket_width > tenon_width
assert tenon_socket_height > tenon_height
assert pin_hole > pin_diameter
