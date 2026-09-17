"""Chosen millimetre dimensions from completed Soren handoff; [assumed] unless derived."""
import cadfits
NOZZLE = 0.4
SHAFT_D = 6.0
SHAFT_FLAT = 2.2
SHAFT_BORE = cadfits.slot_for(SHAFT_D, 0.3)
CAM_BORE = cadfits.slot_for(SHAFT_D, 0.15)
CAM_R, ECCENTRICITY, CAM_T = 8.0, 3.0, 4.0
CAM_X = (-7.0, 7.0)
SHAFT_Z = 22.0
SHAFT_LEFT, SHAFT_RIGHT = -24.9, 29.4
SHAFT_FLANGE_T, SHAFT_FLANGE_D = 2.5, 11.0
YOKE_X, YOKE_Y, YOKE_Z = 28.0, 33.0, 26.0
TUNNEL_Y, TUNNEL_Z = 24.8, 16.4
YOKE_CENTER_Z = 21.8
ROD_SIDE, ROD_LENGTH, ROD_SOCKET_DEPTH = 6.0, 47.0, 2.0
ROD_SOCKET = cadfits.slot_for(ROD_SIDE, 0.15)
GUIDE_BORE = cadfits.slot_for(ROD_SIDE, 0.3)
CROSSHEAD_Z = 81.8
CROSSHEAD_X, CROSSHEAD_Y, CROSSHEAD_H = 15.0, 5.0, 8.0
SLOT_X0, SLOT_X1, SLOT_HEIGHT, SLOT_Z = 1.0, 6.3, 3.4, 4.0
HINGE_X, HINGE_Z, INPUT_ARM = 10.0, 86.0, 7.0
HINGE_PIN_D, DRIVE_PIN_D = 4.0, 3.0
HINGE_BORE = cadfits.slot_for(HINGE_PIN_D, 0.25)
HINGE_FRAME_BORE = cadfits.slot_for(HINGE_PIN_D, 0.1)
DRIVE_BORE = cadfits.slot_for(DRIVE_PIN_D, 0.1)
PIN_CAP_BORE = cadfits.slot_for(HINGE_PIN_D, 0.1)
DRIVE_CAP_BORE = cadfits.slot_for(DRIVE_PIN_D, 0.1)
HUB_R, HUB_Y0, HUB_Y1 = 4.5, -4.0, 3.0
WING_T, WING_TOP = 1.6, 7.6
BRASS = (0.72, 0.50, 0.18)
EMERALD = (0.03, 0.48, 0.30)
VIOLET = (0.42, 0.16, 0.66)
DARK_BRASS = (0.40, 0.28, 0.12)

# [assumed] CAD Boolean overlap and cutter extensions; spec manufacturing ledger.
BOOLEAN_OVERLAP = 0.1
CUT_EXTENSION = 1.0
CUT_RADIAL_EXTENSION = 2.0
RIGHT_ANGLE = 90.0

# [assumed] Crank and bonded keepers; spec mechanism/assembly dimensions.
CRANK_COLLAR_R = SHAFT_FLANGE_D / 2
CRANK_THICKNESS = 7.0
CRANK_ARM_X0 = 4.5
CRANK_RADIUS = 13.0
CRANK_PADDLE_R = 4.0
CRANK_ARM_HALF_WIDTH = 3.0
CRANK_SOCKET_DEPTH = 4.5
SHOULDER_PIN_HEAD_R = 3.0
SHOULDER_PIN_HEAD_T = 2.0
SHOULDER_PIN_LENGTH = 15.5
SHOULDER_CAP_R = 3.5
SHOULDER_CAP_LENGTH = 2.8
SHOULDER_CAP_SOCKET_DEPTH = 1.0
DRIVE_PIN_HEAD_R = 2.7
DRIVE_PIN_HEAD_T = 2.0
DRIVE_PIN_LENGTH = 17.1
DRIVE_CAP_R = 2.7
DRIVE_CAP_LENGTH = 2.3
DRIVE_CAP_SOCKET_DEPTH = 0.5

# [assumed] Continuous feather/lever outlines; spec wing silhouette ledger.
WING_ROOT_PROFILE = ((-5,7.6),(8,7.6),(8,6),(6,6),(4.5,0),(3.3,-3.3),(0,-4.5),(-3.3,-3.3),(-9.5,-2.5),(-9.5,2.5))
WING_BLADE_OUTLINE = ((6,-4),(8,1),(14,2),(22,0),(30,-4),(38,-10),(37.5,-11.5),(29,-10.5),(28,-9.5),(23,-10),(22,-8.5),(17,-8.5),(16,-7),(11,-7),(10,-5.5),(6,-5))
WING_BORE_Y0 = HUB_Y0 - CUT_EXTENSION
WING_BORE_Y1 = HUB_Y1 + CUT_EXTENSION

# [assumed] Print rotations in degrees, bed placement applied after rotation.
PRINT_ROTATIONS = {
    'cam': (0,-RIGHT_ANGLE,0), 'shaft': (0,-RIGHT_ANGLE,0),
    'crank': (0,RIGHT_ANGLE,0), 'yoke': (0,RIGHT_ANGLE,0),
    'rod': (0,0,0), 'frame': (0,0,0),
    'crosshead': (-RIGHT_ANGLE,0,0),
    'shoulder_pin': (RIGHT_ANGLE,0,0), 'drive_pin': (RIGHT_ANGLE,0,0),
    'shoulder_cap': (-RIGHT_ANGLE,0,0), 'drive_cap': (-RIGHT_ANGLE,0,0),
    'wing_left': (2*RIGHT_ANGLE,0,0), 'wing_right': (2*RIGHT_ANGLE,0,0),
}

# [assumed] Original loft stations, cutouts, print datum and finish zones;
# spec bird silhouette ledger. Coordinates and dimensions are millimetres.
# Station rows (forward y, vertical z, lateral half-width, vertical half-height).
# Smooth changing sections make a tapered tail, lifted torso and round small head.
BODY_STATIONS = (
    (-26.0, 88.5, 2.3, 1.3), (-23.0, 89.3, 3.0, 1.7),
    (-20.0, 90.5, 3.5, 2.2), (-16.0, 92.6, 4.1, 3.6),
    (-12.0, 95.2, 5.2, 5.8), (-7.0, 97.5, 6.7, 7.8),
    (-2.0, 98.2, 7.0, 7.8), (3.0, 98.2, 6.0, 7.8),
    (8.0, 99.6, 4.8, 6.8), (12.0, 102.0, 4.7, 5.7),
    (16.0, 104.0, 5.8, 6.0), (19.0, 105.0, 4.8, 4.9),
    (21.0, 105.8, 2.8, 3.5),
)
BILL_STATIONS = ((19.0, 106.5, 1.9, 1.7),
                 (22.0, 106.9, 1.65, 1.45),
                 (28.0, 107.5, 1.2, 1.1),
                 (36.0, 108.0, 0.9, 0.9))
FOOT_MIN = (-3.5, -14.0, 88.0)
FOOT_SIZE = (7.0, 4.0, 8.0)
KEEPOUT_MIN = (-8.5, -4.0, 0.0)
KEEPOUT_SIZE = (17.0, 17.2, 95.2)
TAIL_NOTCH_POINTS = ((0.0, -24.5), (-4.0, -28.0), (4.0, -28.0))
TAIL_NOTCH_BOTTOM = 80.0
TAIL_NOTCH_HEIGHT = 20.0
EYE_CENTER = (5.35, 17.0, 106.0)
EYE_RADIUS = 0.92
SPLIT_BOX_SIZE = (50.0, 100.0, 150.0)
SPLIT_BOX_CENTER_YZ = (0.0, 75.0)
PRINT_ORIGIN_Y = 28.0
PRINT_ORIGIN_Z = 80.0
DARK_BILL = (0.13, 0.10, 0.18)
EYE_COLOR = (0.04, 0.043, 0.05)
TAIL_COLOR_END_Y = -17.0
BILL_COLOR_START_Y = 21.5
THROAT_COLOR_MIN_Y = 10.0
THROAT_COLOR_MAX_Z = 102.5

# [assumed] Reviewed open-frame refinement, 2026-09-16; specification support ledger.
BASE_BOUNDS = (-35,35,-25,25,0,4)
BASE_CORNER_R = 3.0
MAST_BOUNDS = (-6.5,6.5,-25,-21,3.9,86)
SUPPORT_X = (-6.5,6.5)
SUPPORT_YZ = ((-21,36),(-21,75),(6.5,75),(6.5,64))
FAN_SECTIONS = ((0,-19,64,13,4),(0,-13,82.3,29.6,16))
BRIDGE_BOUNDS = (-14.8,14.8,-21,-5,82.2,83.2)
BOSS_HALF_X,BOSS_Y0,BOSS_Y1,BOSS_Z0,BOSS_Z1 = 4.8,-17,-5,82.2,89.8
PEDESTAL_SECTIONS = ((0,-14,83.1,7,6),(0,-13.5,85,7,7))
PEDESTAL_BOUNDS = (-3.5,3.5,-17,-10,84.9,88)
TOWER_X,TOWER_HALF_X,TOWER_HALF_Y,TOWER_Z0,TOWER_Z1 = 22,2.5,6,3.9,29
GUIDE_CUT_Z = (38,79)
HINGE_FRAME_CUT_Y = (-18,-4)
HEAD_ACCESS_R,HEAD_ACCESS_Y0,HEAD_ACCESS_Y1,HEAD_ACCESS_TOP = 3.2,-26,-11,92
FRAME_SIDE_WINDOW_YZ = ((-17,45),(-7,55.2),(-7,66.5),(-12,72),(-17,66.5))
FRAME_SIDE_WINDOW_X = (-16,16)
FRAME_LOWER_WINDOW_XZ = ((-3.2,8),(3.2,8),(3.2,27),(0,30.5),(-3.2,27))
FRAME_LOWER_WINDOW_Y = (-26,-20.5)
FRAME_UPPER_WINDOW_XZ = ((-3.2,47),(3.2,47),(3.2,62.5),(0,66),(-3.2,62.5))
FRAME_UPPER_WINDOW_Y = (-26,-16.8)
DRIVE_HEAD_CLEARANCE = (-6.7,6.7,-6.5,-4,79,92)
YOKE_WINDOW_XZ = ((-11,0),(-3,-7),(11,-7),(11,7),(-3,7))
YOKE_WINDOW_Y = (-17,17)
CROSSHEAD_FRONT_Y,CROSSHEAD_REAR_Y = 7.1,12.1
CROSSHEAD_TONGUE_BOUNDS = (-3,3,-3,7.2,-2,0)
CROSSHEAD_RISER_BOUNDS = (-3,3,5.2,7.2,-0.1,2)
CROSSHEAD_RAMP_YZ = ((7.1,-2),(7.2,-2),(9.6,0),(7.1,0))
CROSSHEAD_RAMP_X = (-3,3)
CROSSHEAD_SLOT_Y = (7.0,12.2)
ROD_BASE_Z = YOKE_CENTER_Z+YOKE_Z/2-ROD_SOCKET_DEPTH
SHOULDER_PIN_Y = -11.0
SHOULDER_CAP_Y = 3.5
DRIVE_PIN_Y = -4.0
DRIVE_CAP_Y = 12.6
BIRD_SEAT_DATUM = (0,-12,88)

# [assumed] Remove wedge/bore knife edge with a printable pointed front opening.
GUIDE_FRONT_RELIEF_XZ = ((-3.3,38),(3.3,38),(3.3,64),(0,67.3),(-3.3,64))
GUIDE_FRONT_RELIEF_Y = (3.2,7.5)
