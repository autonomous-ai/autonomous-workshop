"""Shared parameter feasibility, before CAD construction.

These checks establish arithmetic consistency, not strength or physical fit.
Numeric imports expose the same actual source values to documentation checks.
"""
from math import cos, sin, radians, sqrt, isclose, ceil
from params import DESIGN
from params.face import MAGNET_D, MAGNET_DEPTH, FACE_T, EYE_HEIGHT, EYE_FOOT_HEIGHT, NOSTRIL_HEIGHT
from params.body import WALL, SLIT, BODY08_SEAM
from params.decor import (BELLY_THICKNESS, FRONT_SPIKE_BASE, FRONT_SPIKE_STATIONS,
                          LEG_TOE_FACE_Y, CLAW_SECTIONS, SPIKE_TAPER_STATIONS,
                          TAIL_NECK_FLARE_START_Y, TAIL_NECK_FLARE_REAR_Y,
                          BELLY_LAST_CENTER_Y)
from params.face import HEAD_REAR_Y
from params.assembly import FACE_ADHESIVE_FILM


# Source-derived construction facts for documentation. They are not geometry
# assertions: actual clearances, walls, support and contact require CAD reports.
CONSTRUCTION_FACTS = {
    'body08_full_section_y': (123.1, 126.6),
    'body08_seam_y': BODY08_SEAM,
    'belly07_size_xyz': (6.0, 2.2, BELLY_THICKNESS),
    'belly07_center_xy_bottom_z': (0.0, 115.4, 30.3),
    'belly08_size_xyz': (4.8, 2.2, BELLY_THICKNESS),
    'belly08_center_xy_bottom_z': (0.0, BELLY_LAST_CENTER_Y, 40.5),
    'belly08_bonded_stock_y': (BELLY_LAST_CENTER_Y-1.1, 126.6),
    'belly08_adhesive_instruction': 'Bond only the backed anterior half; keep the posterior overhang and socket fingers free of adhesive',
    'tail_root_collar_y': (TAIL_NECK_FLARE_START_Y, TAIL_NECK_FLARE_REAR_Y),
    'parent_clearance': 'six inverse 5-degree cup stations plus eleven 2.5-degree YZ hull stations',
    'tail_clearance': 'parent, prior ball, and spike07/08 envelopes cut from fan',
    'head_face_floor_n': 0.0,
    'head_magnet_pocket_n': (-1.2, 0.0),
    'nominal_opposed_magnet_face_gap_for_1mm_discs': 2*(MAGNET_DEPTH-1.0),
    'body01_front_land_y': (52.15, 53.35),
    'body01_to06_front_land_y': tuple((s['center'][1]-1.2,s['center'][1])
                                    for s in DESIGN['segments'][:6]),
    'body07_root_relief_y': (115.4,117.0),
    'body07_root_relief_half_width': 6.4,
    'J04_ball_center': tuple(DESIGN['joints'][4]['ball_center']),
    'J04_axial_mouth_land': DESIGN['joints'][4]['axial_mouth_land'],
    'J04_neck_diameter': DESIGN['joints'][4]['neck_diameter'],
    'J08_axial_mouth_land': DESIGN['joints'][8]['axial_mouth_land'],
    'J08_neck_diameter': DESIGN['joints'][8]['neck_diameter'],
    'paw_toe_face_local_y': LEG_TOE_FACE_Y,
    'claw_sections': CLAW_SECTIONS,
    'common_spike_stations': SPIKE_TAPER_STATIONS,
    'body01_rear_root_opening_y': (53.25, 55.35),
    'J01_ball_center': tuple(DESIGN['joints'][1]['ball_center']),
    'J01_axial_mouth_land': DESIGN['joints'][1]['axial_mouth_land'],
    'J01_neck_diameter': DESIGN['joints'][1]['neck_diameter'],
    'J01_parent_envelope_axial_allowance': (
        DESIGN['joints'][1]['parent_clearance_lip_offset']
        - DESIGN['joints'][1]['lip_axial_position_from_center']),
    'head_posterior_stock_cut_y': HEAD_REAR_Y,
    'head_socket_lip_end_y': (DESIGN['joints'][0]['ball_center'][1]
                            + DESIGN['joints'][0]['lip_axial_position_from_center']),
    'maximum_face_projection_from_back': FACE_T+EYE_HEIGHT+FACE_ADHESIVE_FILM,
    'face_adhesive_film': FACE_ADHESIVE_FILM,
    'slit_length_semantics': 'requested material cut limit; not effective free finger span',
    'eye_foot_height': EYE_FOOT_HEIGHT,
    'eye_overall_height': EYE_HEIGHT,
    'nostril_height': NOSTRIL_HEIGHT,
    'front_spike_base': FRONT_SPIKE_BASE,
    'front_spike_stations': FRONT_SPIKE_STATIONS,
    'male_coupon_print_quantity': 2,
    'planned_total_print_quantity': 75,
    'physical_friction_and_compliance': 'UNVERIFIED',
    'print_ready_claim': False,
}


def check_dimensions():
    assert isclose(MAGNET_D, 8.15, abs_tol=1e-9)
    assert isclose(MAGNET_DEPTH, 1.2, abs_tol=1e-9)
    assert FACE_T-MAGNET_DEPTH >= 1.2
    assert WALL >= 2.0
    assert SLIT >= 0.8
    assert BELLY_THICKNESS >= 1.2
    for j in DESIGN['joints']:
        diameter=j['ball_diameter']
        cavity=j['cavity_diameter']
        mouth=j['mouth_diameter']
        assert 9.0 <= diameter <= 12.0
        assert isclose(cavity-diameter, .25, abs_tol=1e-9)
        assert (diameter-mouth)/2 >= .6-1e-9
        angle=radians(25)
        radial_need=j['neck_diameter']/2/cos(angle)+j['lip_axial_position_from_center']*sin(angle)/cos(angle)
        assert mouth/2-radial_need >= 0, 'neck section cannot reach declared angle'
        expected_lip=sqrt((cavity/2)**2-(mouth/2)**2)
        assert j['lip_axial_position_from_center'] >= expected_lip-1e-6, 'lip cannot remove retaining undercut'
        # Lip coordinates are stored rounded to six decimals;1e-6mm accepts
        # that arithmetic rounding, not any meaningful geometric undercut loss.
        # A documented straight throat land may continue beyond the sphere.
    j01=DESIGN['joints'][1]
    sphere_lip=sqrt((j01['cavity_diameter']/2)**2-(j01['mouth_diameter']/2)**2)
    assert tuple(j01['ball_center']) == (0, 57.85, 34)
    assert isclose(j01['neck_diameter'], 5.1, abs_tol=1e-9)
    assert isclose(j01['lip_axial_position_from_center']-sphere_lip, .6, abs_tol=1e-6)
    assert isclose(j01['parent_clearance_lip_offset']-j01['lip_axial_position_from_center'], .1, abs_tol=1e-9)
    j07=DESIGN['joints'][7]
    sphere_lip=sqrt((j07['cavity_diameter']/2)**2-(j07['mouth_diameter']/2)**2)
    assert isclose(j07['neck_diameter'], 4.2, abs_tol=1e-8)
    assert isclose(j07['lip_axial_position_from_center']-sphere_lip, .6, abs_tol=1e-6)
    assert isclose(BODY08_SEAM, 125.4, abs_tol=1e-8)
    j08=DESIGN['joints'][8]
    sphere_lip=sqrt((j08['cavity_diameter']/2)**2-(j08['mouth_diameter']/2)**2)
    assert isclose(j08['neck_diameter'], 4.2, abs_tol=1e-8)
    assert isclose(j08['lip_axial_position_from_center']-sphere_lip, .6, abs_tol=1e-6)
    cavity_intrusion=max(0.0, j08['cavity_diameter']/2-(j08['ball_center'][1]-BODY08_SEAM))
    coupon_base=ceil((1.4+cavity_intrusion)/.2-1e-9)*.2
    assert coupon_base-cavity_intrusion >= 1.4-1e-9
    assert coupon_base-MAGNET_DEPTH >= 1.2-1e-9
    # The belly extends past the stock in Y but lies below the socket housing.
    # Only its backed anterior half bonds to stock, before the slit starts.
    # Check the actual 3D arrangement rather than requiring all Y bounds to
    # precede the slit. These are feasibility bounds, not a new geometry gate.
    j08_slit_start=max(BODY08_SEAM+1.6, j08['ball_center'][1]+j08['lip_axial_position_from_center']-8)
    belly08_y=CONSTRUCTION_FACTS['belly08_center_xy_bottom_z'][1]
    belly08_depth=CONSTRUCTION_FACTS['belly08_size_xyz'][1]
    stock_end=CONSTRUCTION_FACTS['body08_full_section_y'][1]
    belly08_top=CONSTRUCTION_FACTS['belly08_center_xy_bottom_z'][2]+BELLY_THICKNESS
    socket_outer_bottom=j08['ball_center'][2]-(j08['cavity_diameter']/2+WALL)
    assert BODY08_SEAM <= belly08_y-belly08_depth/2 < stock_end
    assert stock_end < j08_slit_start
    assert (belly08_y+belly08_depth/2 <= stock_end
            or belly08_top < socket_outer_bottom), 'belly overhang must clear the socket housing'
    assert FACE_ADHESIVE_FILM >= 0
    assert isclose(DESIGN['face']['pocket_depth'], MAGNET_DEPTH, abs_tol=1e-9)
    assert isclose(DESIGN['face']['head_floor_local_n'], 0.0, abs_tol=1e-9)
    assert isclose(DESIGN['face']['head_to_plate_back_gap'], 0.0, abs_tol=1e-9)
    assert isclose(DESIGN['face']['maximum_feature_projection_from_back'], FACE_T+EYE_HEIGHT, abs_tol=1e-9)
    assert DESIGN['legs']['attach_to'] == ['body_01','body_01','body_04','body_04']
    assert isclose(DESIGN['segments'][7]['construction_seam_y'], BODY08_SEAM, abs_tol=1e-9)
    assert isclose(DESIGN['head']['posterior_stock_cut_y'], HEAD_REAR_Y, abs_tol=1e-9)
    assert len(DESIGN['segments']) == 8
    assert len(DESIGN['legs']['feet']) == 4
    assert all(p[2]==0 for p in DESIGN['legs']['feet'])


check_dimensions()
