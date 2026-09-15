"""Captive loading/reset roof interfaces in deck coordinates.

Derived from Bob's completed access-door-design.md. Ordinary access retains
receivers, roof supports, corner mounts and all hinge/latch hardware.
"""
from build123d import Axis, Color, Plane, Pos, Rot
import params as p
from parts import access_door, canopy_frame
from parts.purchased_hardware import screw_csk, screw_socket, nut

CELLS = {(0, 2): 'reset', (1, 0): 'load'}
LOCAL_HINGE = Axis((-10, 0, 126), (0, 1, 0))


def state_for(column, row, states=None):
    state = (states or {}).get(CELLS[column, row], {})
    angle = float(state.get('angle', 0))
    turns = state.get('latch_angles', [0, 0])
    lifts = state.get('latch_lifts', [0, 0])
    if not 0 <= angle <= 120 or len(turns) != 2 or len(lifts) != 2:
        raise ValueError('Door angle 0..120 and two independent latch states required')
    if any(not 0 <= float(a) <= 90 for a in turns) or any(not 0 <= float(z) <= 3.5 for z in lifts):
        raise ValueError('Latch angle 0..90 and lift 0..3.5 required')
    return angle, list(map(float, turns)), list(map(float, lifts))


def to_board(shape, column, row):
    if column:
        return Pos(p.DECK_W, p.CANOPY_ROW_Y[row], 0) * shape.mirror(Plane.YZ)
    return Pos(0, p.CANOPY_ROW_Y[row], 0) * shape


def pose_door(shape, angle):
    return shape.rotate(LOCAL_HINGE, -angle)


def components(column, row, states=None):
    angle, turns, lifts = state_for(column, row, states)
    prefix = f'canopy_roof_{column}_{row}'
    out = []
    def add(suffix, shape, color=p.CANOPY_PRINT_COLOR, printed=True, moving=False):
        if moving:
            shape = pose_door(shape, angle)
        shape = to_board(shape, column, row)
        label = prefix + '_' + suffix
        shape.label = label
        out.append((label, shape, color, {'role': 'moving' if moving else 'stationary',
            'printable': printed, 'removable': True,
            'material': 'printed PETG' if printed else 'clear PET cut sheet'}))
    add('frame', access_door.receiver())
    add('door_frame', access_door.moving_frame(), moving=True)
    add('cap', access_door.cap(), p.CANOPY_CAP_COLOR, moving=True)
    add('pet', access_door.sheet(), Color(*p.CANOPY_PET_COLOR), False, moving=True)
    for i, v in enumerate((32, 112)):
        add(f'hinge_{i}_sleeve', Pos(-10, v, 126) * access_door.hinge_sleeve())
    for i, v in enumerate((30, 114)):
        add(f'latch_{i}_sleeve', Pos(147, v, 0) * access_door.latch_sleeve())
        lever = Pos(147, v, lifts[i]) * Rot(0, 0, -turns[i]) * access_door.latch_lever()
        add(f'latch_{i}_lever', lever, p.CANOPY_CAP_COLOR)
    return out


def hardware_components(column, row, states=None):
    angle, _, _ = state_for(column, row, states)
    prefix = f'canopy_roof_{column}_{row}'
    out = []
    def add(suffix, shape, moving=False):
        if moving:
            shape = pose_door(shape, angle)
        shape = to_board(shape, column, row)
        label = prefix + '_' + suffix
        shape.label = label
        out.append((label, shape, Color(.64, .67, .70),
                    {'role': 'fastener', 'printable': False, 'removable': True}))
    # Preserve old physical corner/clamp occurrence identities after mirroring.
    for kind, points, head, bottom in (
        ('mount', canopy_frame.bolt_points(), p.CANOPY_FRAME_TOP, p.CANOPY_POST_TOP_Z-p.NUT_T),
        ('clamp', canopy_frame.clamp_points(), p.CANOPY_CAP_BOTTOM+p.CANOPY_CAP_T+8,
         p.CANOPY_FRAME_BOTTOM-p.NUT_T+8)):
        for old_i, (x, v) in enumerate(points):
            u = p.CANOPY_CELL_W-x if column else x
            add(f'{kind}_{old_i}_bolt', Pos(u, v, head)*screw_csk(), kind == 'clamp')
            add(f'{kind}_{old_i}_nut', Pos(u, v, bottom)*nut(), kind == 'clamp')
    for i, v in enumerate((32, 112)):
        add(f'hinge_{i}_bolt', Pos(-10, v-10.3, 126)*Rot(90, 0, 0)*screw_socket())
        add(f'hinge_{i}_nut', Pos(-10, v+10.3, 126)*Rot(-90, 0, 0)*nut())
    for i, v in enumerate((30, 114)):
        add(f'latch_{i}_bolt', Pos(147, v, 136)*screw_socket())
        add(f'latch_{i}_nut', Pos(147, v, 111.8)*nut())
    return out
