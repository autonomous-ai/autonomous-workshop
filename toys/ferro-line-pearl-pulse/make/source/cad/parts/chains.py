"""Captive PIP strand. XY is radial/vertical; Z is the printed hinge axis.

Each shape is a single distinct solid. Eye belongs to the proximal link;
retained male belongs to the distal link. No post-print bead assembly is implied.
The widened axial dimension is the handoff's permitted cheek-roof repair.
"""
import math
from build123d import (Align, Axis, Box, Compound, Cylinder, Plane, Polygon,
                      Pos, extrude, revolve)
from params import *

_BASE = (Align.CENTER, Align.CENTER, Align.MIN)


def _turn_profile(points):
    """One closed axial profile avoids coincident cone/cylinder seams."""
    return revolve(Plane.XZ * Polygon(*points, align=None), axis=Axis.Z)


def _eye():
    bore = CHAIN_BORE_D / 2
    eye = _turn_profile([
        (bore + CHAIN_RELIEF_R, 0), (CHAIN_EYE_R - 0.2, 0),
        (CHAIN_EYE_R, CHAIN_RELIEF_H),
        (CHAIN_EYE_R, CHAIN_EYE_H - 0.8),
        (CHAIN_EYE_R - 0.25, CHAIN_EYE_H),
        (bore, CHAIN_EYE_H), (bore, CHAIN_RELIEF_H),
    ])
    # Sector opens DOWN localY; its cheeks grow laterally at 0.96mm/mm,
    # then meet under a 1.3mm roof. There is no horizontal annulus bridge.
    w = CHAIN_SLOT_HALF_WIDTH
    cutter = extrude(Plane.XZ * Polygon(
        (-w, -1), (w, -1), (w, CHAIN_SLOT_BASE_H),
        (0, CHAIN_SLOT_ROOF_H), (-w, CHAIN_SLOT_BASE_H), align=None),
        amount=CHAIN_EYE_R+1, dir=(0,-1,0))
    s = CHAIN_EYE_R + 1
    half = s * math.tan(math.radians(CHAIN_SLOT_HALF_ANGLE))
    sector = extrude(Polygon((0,0),(-half,-s),(half,-s),align=None),
                     amount=CHAIN_EYE_H+2, dir=(0,0,1))
    return eye - (cutter & sector)


def _male():
    r = CHAIN_PIN_D / 2
    return _turn_profile([
        (0,0), (r-CHAIN_RELIEF_R,0), (r,CHAIN_RELIEF_H),
        (r,CHAIN_PIN_H), (CHAIN_HEAD_R,CHAIN_PIN_H+CHAIN_HEAD_RISE),
        (CHAIN_HEAD_R,CHAIN_PIN_H+CHAIN_HEAD_RISE+CHAIN_HEAD_CAP),
        (0,CHAIN_PIN_H+CHAIN_HEAD_RISE+CHAIN_HEAD_CAP),
    ])


def _tag(shape, label, color=PEARL):
    assert len(shape.solids()) == 1, f'{label}: disconnected physical body'
    shape.label = label
    shape.color = color
    return shape


def bead(terminal=False):
    """Male axis at origin; distal eye/tip centre at (0,-7.2)."""
    distal_radius = 2.8 if terminal else CHAIN_EYE_R
    neck_length = CHAIN_PITCH - distal_radius + 0.4
    neck = Pos(0,-neck_length/2,0) * Box(
        CHAIN_NECK_WIDTH, neck_length, CHAIN_NECK_H, align=_BASE)
    if terminal:
        distal = _turn_profile([(0,0),(2.55,0),(2.8,0.4),
            (2.8,3.4),(2.4,4.6),(1.5,5.1),(0,5.1)])
    else:
        distal = _eye()
    body = _male() + neck + Pos(0,-CHAIN_PITCH,0)*distal
    return _tag(body, 'terminal_bead' if terminal else 'captive_bead')


def root():
    """P=(0,0,1.6), A=(-7,0,1.6), Q=(0,-18,1.6)."""
    hub = Cylinder(3.2, CHAIN_PIVOT_H, align=_BASE)
    stem_length = ROOT_LENGTH - CHAIN_EYE_R + 0.4
    stem = Pos(0,-stem_length/2,0)*Box(3.2, stem_length,2.4,align=_BASE)
    # Arm stops inside its integral horn cylinder; same bed plane throughout.
    horn = Pos(-HORN_LENGTH/2,0,0)*Box(HORN_LENGTH,2.4,2.4,align=_BASE)
    pin = Pos(-HORN_LENGTH,0,0)*Cylinder(PIVOT_D/2,3.2,align=_BASE)
    hub = hub + stem + horn + pin + Pos(0,-ROOT_LENGTH,0)*_eye()
    bore = Pos(0,0,-1)*Cylinder(PIVOT_BORE/2,CHAIN_PIVOT_H+2,align=_BASE)
    return _tag(hub-bore,'rocker_root_with_captive_eye')


def local_parts(root_angle_deg=0.0, link_angles_deg=None):
    """Nine labelled solids. Link angles are absolute in the local XY plane.

    Each bead rotates about its own retained pin, not an arbitrary centroid.
    This function states geometry; it does not verify settling or motion.
    """
    angles = tuple(link_angles_deg or (0.0,)*CHAIN_COUNT)
    if len(angles) != CHAIN_COUNT:
        raise ValueError('one absolute angle is required for each of eight beads')
    result = [_tag(root().rotate(Axis.Z,root_angle_deg),'rocker_root')]
    t = math.radians(root_angle_deg)
    x,y = ROOT_LENGTH*math.sin(t), -ROOT_LENGTH*math.cos(t)
    standard, terminal = bead(), bead(True)
    for i,a in enumerate(angles):
        last = i == CHAIN_COUNT-1
        shape = (terminal if last else standard).rotate(Axis.Z,a).translate((x,y,0))
        result.append(_tag(shape, f'bead_{i+1:02d}' + ('_terminal' if last else '')))
        t = math.radians(a)
        x += CHAIN_PITCH*math.sin(t)
        y -= CHAIN_PITCH*math.cos(t)
    return result


def print_parts():
    """Exact gently serpentine PIP build: every body has minZ=0."""
    return local_parts(link_angles_deg=CHAIN_PRINT_ANGLES)


def world_parts(azimuth_deg=0.0, root_angle_deg=0.0, link_angles_deg=None):
    """Local→world: Rx90, translate(29,1.6,91), Rz(azimuth).

    Local +X becomes radial out, +Y becomes world up, +Z is minus tangent.
    Inverse: Rz(-azimuth), translate(-29,-1.6,-91), Rx(-90).
    """
    return [s.rotate(Axis.X,90).translate((PIVOT_R,CHAIN_AXIS_Z,PIVOT_Z))
            .rotate(Axis.Z,azimuth_deg)
            for s in local_parts(root_angle_deg,link_angles_deg)]


def print_module():
    # One uniformly coloured manufacturing compound avoids redundant XCAF
    # occurrence-colour overrides whose serialization order is unstable.
    # The nine captive bodies remain separate; world_parts supplies the
    # individually labelled occurrences of the finished assembly.
    return Compound(print_parts(),
                    label='one_root_and_eight_captive_beads_print_in_place',
                    color=PEARL)
