"""Accessory dimensions [observed] WISH; accommodations [assumed] BRIEF."""
from params import DESIGN
COLORS = DESIGN['colors']
GILL_ROOT = (29.0, 30.0, 38.0)
GILL_THICKNESS = 2.4  # [assumed] broad print face; raised shaft adds 1.2
GILL_SHAFT_HEIGHT = 1.2
GILL_ROOT_PROFILE = [(0,-11),(7,-11),(9,8),(5,13),(0,13)]
GILL_LEAVES = [((4,9),(22,35),9), ((5,3),(37.5,12),10), ((4,-6),(32,-16),9)]
GILL_SLOT_DEPTH = 1.2
GILL_SLOT_WIDTH = 1.0
LEG_STATIONS = [(0,2,-2,12,12),(3,2,-2,12,12),(7,1,0,11,11),(13,-5,4,8,8),(19,-7,6,6,6)]
LEG_FEET = DESIGN['legs']['feet']
LEG_KEY = (5,5,4)
# [assumed] External claw bonding plane replaces the failed slotted toes.
LEG_TOE_FACE_Y = -8.5
# z, full width, forward length, blunt nose width, nose bevel depth.
# Nested sections and a constant rear plane leave no unsupported claw floor.
CLAW_SECTIONS = [(0,4.4,5.5,1.2,1.2),(1.2,4.4,5.5,1.2,1.2),
                 (3,3.2,3.8,1.2,.8),(4.4,1.6,1.2,1.2,.2)]
CLAW_CENTERS = [(-5.5,LEG_TOE_FACE_Y,0),(0,LEG_TOE_FACE_Y,0),
                (5.5,LEG_TOE_FACE_Y,0)]
HORN_MIDDLE = {'size':(8,8,13),'base':(0,29,55),'lean':(0,2)}
HORN_PAIR = {'size':(11,13,23),'base':(17,30,53),'lean':(1,4)}
HORN_TIP = 1.2
KEY_DEPTH = 2.0
KEY_CLEARANCE = 0.2
SPIKE_SIZE = (8,8,12)
SPIKE_LEAN = (0,2)
BELLY_THICKNESS = 1.2
BELLY_FIRST_WIDTH = 45.0
BELLY_FIRST_HEIGHT = 9.0
# Five blunt rooted lobes, sagittal Y/Z outline; no mathematical zero-width tips.
# [assumed] Repair: 2mm flat fifth-lobe tip; broad posterior root and trimmed leading spur.
TAIL_OUTLINE = [(136,48),(139,48),(151,62),(157,71),(157,74),(153,75),(145,69),(145,78),(150,85),(150,88),(147,89),(138,80),(137,88),(134,93),(131,93),(128,90),(128,81),(124,86),(121,86),(121,83),(121,73),(120,77),(118,77),(118,74),(120,68),(123,68),(134,58),(136,58)]
TAIL_HALF_THICKNESS = 4.0
TAIL_KEY_CENTERS = [(128,65),(137,74)]
TAIL_KEY_RADIUS = 2.0
TAIL_KEY_DEPTH = 1.2

# [assumed] Repair: sloping horn flare retains at least 1.3mm rise per radial mm.
HORN_FLARE_RISE_RATIO = 1.3
TAIL_SOCKET_CLEARANCE = 0.3
# Historical unused marker; current cuts use parent_clearance(8).
TAIL_SOCKET_CLEAR_Y = 130.8
TAIL_NECK_REAR_Y = 137.0
# Posterior flare begins beyond the conservative parent-cup envelope.
TAIL_NECK_FLARE_START_Y = 134.2
TAIL_NECK_FLARE_REAR_Y = 137.5
TAIL_NECK_FLARE_RADIUS = 4.0

# [assumed] External adhesive seats; independent of keyed head horns.
BELLY_FRONT_SEAT_OFFSET = 1.2
SPIKE_CROWN_SEAT_DEPTH = 1.2
# Constant 1.2mm foot avoids the measured sub-minimum basal taper band.
SPIKE_TAPER_STATIONS = [(0.0,1.0,0.0),(0.10,1.0,0.0),(0.40,0.78,0.2),(0.75,0.44,0.7),(1.0,None,1.0)]

# [assumed] First-spike clearance repair; selected Inventor J00-DECOR-PROBE.
FRONT_SPIKE_BASE = (0,55.5,46.7)
FRONT_SPIKE_STATIONS = [(0,0,0,4,2),(1.2,0,0,4,2),(4.8,0,2.2,3.12,1.56),(9,0,4.125,1.76,.88),(12,0,5.5,.6,.6)]

# [assumed] Measured assembled clearance repairs; see BELLY-ASSEMBLY-REPAIR.
BELLY_FIRST_PRINT_WIDTH = 42.0
BELLY_LAST_CENTER_Y = 126.6
