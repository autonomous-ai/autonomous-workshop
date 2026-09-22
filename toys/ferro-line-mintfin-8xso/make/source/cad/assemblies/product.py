"""Named physical occurrences; positioning only, no manufactured unions.

Each chain subtree contains all distal physical parts for honest joint sweeps.
The detachable face and loose test kit remain separately addressable.
"""
from build123d import Axis, Color
from cadgen.assembly import AssemblyHelper
from params import DESIGN
from params.assembly import SPARE_FACE_AT, COUPON_SOCKET_AT, COUPON_BALL_AT, STOCK_COLORS, FACE_ADHESIVE_FILM
from parts.head import head_front_world, head_rear_world
from parts.body import body_half
from parts.face import face_instances, face_to_world
from parts.decor import (belly_world, spike_world, leg_world, claw_world,
                         gill_world, horn_world, tail_world)
from parts.coupon import coupon_socket, coupon_ball
import validation


def add_part(assembly, shape, role, color):
    """Store exact requested sRGB, with nearest stocked spool name in label."""
    h = DESIGN['colors'][color].lstrip('#')
    rgb = Color(*(int(h[i:i+2],16)/255 for i in (0,2,4)))
    name = role + '_' + STOCK_COLORS[color]
    shape.label = name
    shape.color = rgb
    assembly.add(shape, name, color=rgb)


def build_face(expression, active):
    a = AssemblyHelper('active_face' if active else 'spare_face')
    for role, builder, translation, color in face_instances(expression):
        u, v, n = translation
        # All inserts move together above a finite adhesive film; secondary
        # highlight/eye and tongue/mouth offsets remain unchanged.
        if role != 'face_plate':
            n += FACE_ADHESIVE_FILM
        part = builder().translate((u, v, n))
        part = face_to_world(part) if active else part.translate(SPARE_FACE_AT)
        add_part(a, part, expression+'_'+role.replace('-1','left').replace('_1','_right'), color)
    return a.compound()


def build_head():
    a = AssemblyHelper('head')
    structural = AssemblyHelper('structural')
    add_part(structural, head_front_world(), 'head_front', 'mint')
    add_part(structural, head_rear_world(), 'head_rear', 'mint')
    a.add(structural.compound(), 'structural')
    for side, name in ((-1,'left'),(1,'right')):
        add_part(a, gill_world(side), 'gills_'+name, 'coral')
        add_part(a, horn_world('pair',side), 'horn_'+name, 'charcoal')
    add_part(a, horn_world('middle'), 'horn_middle', 'charcoal')
    return a.compound()


def build_segment(index):
    name = f'body_{index+1:02d}'
    a = AssemblyHelper(f'segment_{index+1:02d}')
    structural = AssemblyHelper('structural')
    for side in ('front','rear'):
        add_part(structural, body_half(index,side,print_pose=False), name+'_'+side, 'mint')
    a.add(structural.compound(), 'structural')
    add_part(a, belly_world(index), f'belly_{index+1:02d}', 'cream')
    add_part(a, spike_world(index), f'spike_{index+1:02d}', 'charcoal')
    for foot_index, owner in enumerate(DESIGN['legs']['attach_to']):
        if owner != name:
            continue
        foot = AssemblyHelper(f'foot_{foot_index+1:02d}')
        add_part(foot, leg_world(foot_index), f'leg_{foot_index+1:02d}', 'mint')
        for c in range(DESIGN['legs']['claws_per_paw']):
            add_part(foot, claw_world(foot_index,c), f'claw_{foot_index+1:02d}_{c+1}', 'charcoal')
        a.add(foot.compound(), f'foot_{foot_index+1:02d}')
    return a.compound()


def build_chain(index, joint_angles):
    a = AssemblyHelper(f'chain_{index+1:02d}')
    if index < len(DESIGN['segments']):
        a.add(build_segment(index), f'segment_{index+1:02d}')
        a.add(build_chain(index+1,joint_angles), f'chain_{index+2:02d}')
    else:
        tail = AssemblyHelper('tail')
        for side, name in ((-1,'left'),(1,'right')):
            add_part(tail, tail_world(side), 'tail_'+name, 'coral')
        a.add(tail.compound(), 'tail')
    result = a.compound()
    joint = DESIGN['joints'][index]
    pitch, twist = joint_angles.get(joint['id'], (0,0))
    center = joint['ball_center']
    if twist:
        result = result.rotate(Axis(center,(0,1,0)),twist)
    if pitch:
        result = result.rotate(Axis(center,(1,0,0)),pitch)
    return result


def build_assembly(expression='happy', joint_angles=None, include_kit=True):
    if expression not in DESIGN['face']['expressions']:
        raise ValueError(expression)
    root = AssemblyHelper('mintfin')
    figure = AssemblyHelper('figure')
    figure.add(build_head(), 'head')
    figure.add(build_face(expression,True), 'active_face')
    figure.add(build_chain(0,joint_angles or {}), 'chain_01')
    root.add(figure.compound(), 'figure')
    if include_kit:
        other = 'sleepy' if expression=='happy' else 'happy'
        root.add(build_face(other,False), 'spare_face')
        add_part(root, coupon_socket().translate(COUPON_SOCKET_AT), 'coupon_socket', 'mint')
        for i, location in enumerate(COUPON_BALL_AT):
            add_part(root, coupon_ball().translate(location), f'coupon_ball_half_{i+1}', 'coral')
    return root.compound()
