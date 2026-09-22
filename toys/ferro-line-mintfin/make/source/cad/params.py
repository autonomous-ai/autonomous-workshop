"""Mintfin millimetres. Shared dimensional inputs and derived mates."""
import cadfits
PIN_CAP_R=4.2
PIN_NECK_R=2.2
PIN_HEIGHT=7.8
HINGE_CLEARANCE=0.45
BEARING_R=7.2
OPENING_DEG=104.0
STEM_WIDTH=3.2
STEM_HEIGHT=2.0
RELIEF=0.4
JOINT_PITCH=18.0
FIRST_JOINT_X=34.0
BODY_WIDTHS=(24,24,23,22,21,19,17)
BODY_HEIGHTS=(15,15,14,14,13,12,11)
PALETTE={'mint':'#83D5BB','coral':'#EF857E','cream':'#FFF0CF','charcoal':'#303844'}

def bore_radius(pin_radius, clearance):
    return cadfits.slot_for(2*pin_radius,clearance)/2

HEAD_FACE_PARAMS = {
    'head_length': 26.0, 'head_width': 38.0, 'head_top_width': 34.0,
    'head_height': 20.4, 'head_corner': 5.0,
    'head_hinge_x': 34.0, 'stem_width': 3.2, 'stem_height': 2.0,
    'face_x': 12.0, 'face_length': 20.0, 'face_width': 28.0,
    'face_thickness': 2.4, 'face_corner': 3.0, 'face_seat_z': 17.6,
    'side_clearance': .15, 'end_clearance': .25,
    'arm_width': 1.2, 'arm_root_x': 20.0, 'arm_tip_x': 8.0,
    'arm_slot': .8, 'catch_x': 10.0, 'catch_length': 2.0,
    'catch_projection': .35, 'groove_depth': .55,
    'horn_x': 24.1, 'horn_y': 10.0,
    'horn_base_radius': 1.85, 'horn_tip_radius': .8,
}
