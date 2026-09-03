"""Single parameter block for Lantern Menagerie, in millimetres."""

import cadfits

# Sealed optical and envelope dimensions [invented.json].
REEL_D, REEL_T = 114.0, 3.2
REEL_OUTER_R, REEL_RING_INNER_R = REEL_D / 2, 55.0
REEL_HUB_R = 7.0
# Keep the near-circular frame and scalloped control perimeters below the
# topology budget of the host's single-process inspection batch.  Seventy-two
# samples retain six vertices per authored reel scallop and sub-nozzle chord
# error on the 54 mm shell radius while avoiding the rejected 144-sample B-rep.
PLANAR_CURVE_FACETS = 72
PORTAL_D, PORTAL_Y = 44.0, 31.0
PORTAL_R = PORTAL_D / 2
CREATURE_PITCH_R = 31.0
SHELL_FACE_T, REAR_FACE_T = 2.4, 3.2
AXIAL_GAP = 0.30
FRONT_INNER_Z = SHELL_FACE_T
REEL_Z = FRONT_INNER_Z + AXIAL_GAP
REAR_INNER_Z = REEL_Z + REEL_T + AXIAL_GAP
ASSEMBLY_DEPTH = REAR_INNER_Z + REAR_FACE_T

# Frame adjusted inside the sealed maximum so the 114 mm reel clears the bed.
FRAME_BOTTOM_Y, FRAME_TOP_Y = -59.0, 60.0
FRAME_BASE_W, FRAME_BASE_H = 108.0, 19.0
FRAME_BASE_CY = FRAME_BOTTOM_Y + FRAME_BASE_H / 2
ARCH_OUTER_R, PILLAR_CY = 32.0, -9.0
PILLAR_W, PILLAR_H = 8.0, 62.0
AXLE_BRIDGE_W, AXLE_BRIDGE_H = 58.0, 12.0

# Fits derive the male from the female once, through cadfits.
SPINDLE_BORE_D = 7.8
SPINDLE_D = cadfits.peg_for(SPINDLE_BORE_D, 0.30)
SPINDLE_LEN = REAR_INNER_Z - SHELL_FACE_T + 1.2
HOOK_W, HOOK_H = 3.2, 5.0
HOOK_SLOT_W = cadfits.slot_for(HOOK_W, "slip")
HOOK_SLOT_H = cadfits.slot_for(HOOK_H, "slip")
HOOK_STEM_LEN = ASSEMBLY_DEPTH - SHELL_FACE_T
HOOK_BARB_T = 1.6
HOOK_BARB_W = HOOK_W + 0.8
HOOK_BARB_H = HOOK_H
HOOK_BARB_SHIFT_X = (HOOK_BARB_W - HOOK_W) / 2
HOOK_LEAD_CHAMFER = 0.80
HOOK_LEAD_W = HOOK_BARB_W - HOOK_LEAD_CHAMFER
HOOK_LEAD_H = HOOK_BARB_H
HOOK_REQUIRED_FLEX = HOOK_BARB_W / 2 + HOOK_BARB_SHIFT_X - HOOK_SLOT_W / 2
HOOK_POSITIONS = ((-43.0, -49.0), (43.0, -49.0), (-15.0, 59.0), (15.0, 59.0))

# Ramped compliant detent: symmetric mouth, rounded tip, deeper rabbit home.
DETENT_NOSE_D, DETENT_NOSE_H = 3.0, 0.80
DETENT_NOSE_R = DETENT_NOSE_D / 2
DETENT_POCKET_D = cadfits.slot_for(DETENT_NOSE_D, "slip")
DETENT_POCKET_R = DETENT_POCKET_D / 2
DETENT_NOSE_CHAMFER = 0.55
DETENT_POCKET_MOUTH_R = 2.40
DETENT_POCKET_RAMP_DEPTH = 0.18
DETENT_POCKET_DEPTH_OTHER, DETENT_POCKET_DEPTH_RABBIT = 0.25, 0.50
DETENT_FLAT_DEFLECTION = DETENT_NOSE_H - AXIAL_GAP
DETENT_OTHER_DEFLECTION = DETENT_FLAT_DEFLECTION - DETENT_POCKET_DEPTH_OTHER
DETENT_RABBIT_DEFLECTION = DETENT_FLAT_DEFLECTION - DETENT_POCKET_DEPTH_RABBIT
DETENT_HOME_DIFFERENTIAL = DETENT_OTHER_DEFLECTION - DETENT_RABBIT_DEFLECTION

# Stand geometry and exact authored pose.
STAND_W = 74.0
STAND_L = 77.5
STAND_T = 5.0
STAND_BODY_T = 4.6
STAND_BODY_Z = 1.2
STAND_ARM_W = 6.0
STAND_BAR_H = 10.0
TRUNNION_D = 6.0
TRUNNION_R = TRUNNION_D / 2
TRUNNION_LEN = 19.0
TRUNNION_SOCKET_D = cadfits.slot_for(TRUNNION_D, "slip")
STAND_HINGE_X = 52.5
STAND_HINGE_Y = -30.5
STAND_HINGE_Z = 14.5
STAND_DEPLOY_DEG = 112.0
TRUNNION_Y = 5.0
BEARING_BLOCK_W = 8.0
BEARING_BLOCK_H = 12.0
BEARING_SOCKET_R = 3.35

# Deliberate print margins, not physical strength proof.
MIN_WEB = 3.2
SPOKE_W = 5.0
EDGE_R = 1.5
