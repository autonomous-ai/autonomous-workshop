"""Mintfin head and in-plane snap faces; exact source, all dimensions in mm.

All geometry is invented from WISH.json; no image or likeness target exists.
No Sphere primitives, floating ornaments, magnets, or cosmetic loose pieces.
Root owns generation, deterministic checks and scene assembly.
"""
from math import atan2, degrees, hypot
from build123d import (
    Align, Box, Cone, Cylinder, Plane, Polygon, Pos, RectangleRounded,
    Rot, extrude, loft,
)
import cadfits
from mintfin_lib import male_pin

from params import HEAD_FACE_PARAMS

P = HEAD_FACE_PARAMS
FACE_POCKET_WIDTH = cadfits.slot_for(P['face_width'], P['side_clearance'])
FACE_POCKET_LENGTH = cadfits.slot_for(P['face_length'], P['end_clearance'])
FACE_SEAT_Z = P['face_seat_z']
FACE_INSTALL = Pos(0, 0, FACE_SEAT_Z)


def _rr(x, y, z, length, width, radius):
    return Pos(x, y, z) * RectangleRounded(length, width, radius)


def _box(x0, x1, y0, y1, z0, z1):
    return Pos(x0, y0, z0) * Box(x1-x0, y1-y0, z1-z0,
        align=(Align.MIN, Align.MIN, Align.MIN))


def _union(items):
    shape = items[0]
    for item in items[1:]:
        shape = shape + item
    return shape


def _head_shell():
    return loft([
        _rr(13, 0, 0, 26, 38, 5),
        _rr(13, 0, 3, 26, 38, 5),
        _rr(13, 0, 16, 26, 36, 5),
        _rr(13, 0, P['head_height'], 26, 34, 5),
    ], ruled=True)


def _gills():
    """Six broad bed-rooted fins; every top section contracts."""
    fins = []
    for side in (-1, 1):
        for x, height in ((7.5, 10.0), (13.0, 13.0), (18.5, 10.0)):
            fins.append(loft([
                _rr(x, side*21.5, 0, 4.6, 11.0, 1.8),
                _rr(x, side*21.5, 7, 4.6, 11.0, 1.8),
                _rr(x, side*21.0, height, 3.4, 9.8, 1.4),
            ], ruled=True))
    return fins


def _horns():
    # Repair: front limit22.25 clears the complete seated face, including base.
    # Rear limit25.95 still stays ahead of receiver26.8; base remains in shell.
    horn_x, horn_base_radius = P['horn_x'], P['horn_base_radius']
    return [Pos(horn_x, side*P['horn_y'], 18.5) * Cone(
        horn_base_radius, P['horn_tip_radius'], 6.5,
        align=(Align.CENTER, Align.CENTER, Align.MIN)) for side in (-1, 1)]


def _pocket_cutters():
    """Seat with local planar latch cuts and a completely open front step.

    Repair for head/r0001: long grooves reached curved rear corners, and
    partial-width front access left hairline cheek remnants. Neither feature
    contributes retention. Keep only local grooves behind the exposed tabs.
    """
    cutters = [extrude(_rr(P['face_x'], 0, FACE_SEAT_Z,
        FACE_POCKET_LENGTH, FACE_POCKET_WIDTH,
        P['face_corner']+P['side_clearance']), amount=15)]
    # Remove entire front cheek height, across Y beyond both head sides.
    # This creates one flat bed-supported nose step, not two thin curved strips.
    cutters.append(_box(-3, 9, -40, 40, FACE_SEAT_Z, 35))
    throat = FACE_POCKET_WIDTH / 2
    depth = P['groove_depth']
    groove_start_x = P['catch_x']-P['catch_length']/2-.25
    groove_end_x = P['catch_x']+P['catch_length']/2+1.0
    for side in (-1, 1):
        # Tool ends are planar atX8.75 and12, in the straight side cheek.
        # Its inner side crosses the open seat; the outer wall remains2.3 mm.
        # Roof advances0.55 mm across0.90 mm rise (>58deg above horizontal).
        points = [(side*y, z) for y, z in (
            (12.8, 18.0), (throat, 18.0),
            (throat+depth, 18.7), (throat+depth, 19.45),
            (throat, 20.35), (12.8, 20.35),
        )]
        profile = Plane.YZ * Polygon(*points, align=None)
        cutters.append(Pos(groove_start_x, 0, 0) * extrude(profile,
            amount=groove_end_x-groove_start_x, dir=(1,0,0)))
    return cutters


def head():
    shell = _head_shell()
    for cutter in _pocket_cutters():
        shell = shell - cutter
    stem = _box(24, P['head_hinge_x'], -P['stem_width']/2,
        P['stem_width']/2, 0, P['stem_height'])
    pin = Pos(P['head_hinge_x'], 0, 0) * male_pin()
    shape = _union([shell, stem, pin] + _gills() + _horns())
    assert len(shape.solids()) == 1, 'head must be one printable connected solid'
    shape.label = 'Mintfin head with six gills, horns and captive outgoing pin'
    return shape


def head_color_masks():
    """Masks only: intersect with head; subtract prior masks for disjoint color."""
    # Keep the material seam above the horn-base/pocket tangency at Z18.5.
    # This changes buried color only, preserving the exact fused exterior.
    upper = _box(-17, 43, -30, 30, 19.2, 39.2)
    return {
        'coral': _gills(),
        'charcoal': [horn & upper for horn in _horns()],
        'cream': [_box(-2, 26, -20, 20, 0, 1.2)],
    }


def _latches():
    pieces = []
    q = P['face_width']/2
    for side in (-1, 1):
        #0.2 mm overlap into arm;0.70 mm flat ridge avoids a knife-edge catch.
        points = [(side*y, z) for y, z in (
            (q-.2, .3), (q+P['catch_projection'], .85),
            (q+P['catch_projection'], 1.55), (q-.2, 2.1),
        )]
        profile = Plane.YZ * Polygon(*points, align=None)
        pieces.append(Pos(P['catch_x']-P['catch_length']/2, 0, 0) *
            extrude(profile, amount=P['catch_length'], dir=(1,0,0)))
    return pieces


def face_blank():
    """Bed-down back and XY bending arms; head pocket derives from this plate."""
    plate = extrude(_rr(P['face_x'], 0, 0, P['face_length'],
        P['face_width'], P['face_corner']), amount=P['face_thickness'])
    q = P['face_width']/2
    inner = q-P['arm_width']
    for side in (-1, 1):
        # Slot rounded ends preserve a rounded flex root without an edge selector.
        length = P['arm_root_x']-6.8
        slot = extrude(_rr((P['arm_root_x']+6.8)/2,
            side*(inner-P['arm_slot']/2), -.5,
            length, P['arm_slot'], .39), amount=4)
        plate = plate-slot
        # Open the outer strip forwards of each arm tip. Full-through Z cut.
        if side == 1:
            cut = _box(-2, P['arm_tip_x'], inner-P['arm_slot'], 16, -.5, 4)
        else:
            cut = _box(-2, P['arm_tip_x'], -16, -inner+P['arm_slot'], -.5, 4)
        plate = plate-cut
    return _union([plate]+_latches())


def _disc(x, y, radius, z=2.25, height=1.35):
    return Pos(x, y, z) * Cylinder(radius, height,
        align=(Align.CENTER, Align.CENTER, Align.MIN))


def _stroke(a, b, width=1.2, z=2.25, height=1.15):
    dx, dy = b[0]-a[0], b[1]-a[1]
    length = hypot(dx, dy)
    bar = Pos((a[0]+b[0])/2, (a[1]+b[1])/2, z) * Rot(0,0,
        degrees(atan2(dy,dx))) * Box(length, width, height,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    return _union([bar, _disc(*a, width/2, z, height),
        _disc(*b, width/2, z, height)])


def _expression(mood):
    if mood not in ('happy', 'sleepy', 'angry'):
        raise ValueError('face mood must be happy, sleepy or angry')
    marks, sparkles = [], []
    if mood in ('happy', 'angry'):
        for side in (-1, 1):
            marks.append(_disc(12.0, side*6.7, 3.5))
            # Sparkle intersects eye disc; never a disconnected decorative bead.
            sparkles.append(_disc(11.2, side*6.0, .8, 3.45, .8))
            if mood == 'angry':
                a = (14.7, side*3.6)
                b = (16.0, side*9.0)
                marks.append(_stroke(a, b, 1.6))
    else:
        for side in (-1, 1):
            cy = side*6.7
            marks.extend([_stroke((12.6,cy-3),(11.0,cy),1.4),
                          _stroke((11.0,cy),(12.6,cy+3),1.4)])
    # Nose-forward X is decreasing: happy mouth bows toward the nose.
    mouth = ([(6.4,-4),(5.3,-2),(5.0,0),(5.3,2),(6.4,4)]
        if mood != 'angry' else [(4.9,-4),(6.0,-2),(6.3,0),(6.0,2),(4.9,4)])
    marks.extend(_stroke(a,b,1.2) for a,b in zip(mouth,mouth[1:]))
    return marks, sparkles


def face(mood='happy'):
    marks, sparkles = _expression(mood)
    shape = _union([face_blank()]+marks+sparkles)
    assert len(shape.solids()) == 1, 'face, latches and marks must be one solid'
    shape.label = 'Mintfin '+mood+' swappable snap face'
    return shape


def face_color_masks(mood='happy'):
    """Give cream sparkles priority, charcoal marks next; remaining face cream."""
    marks, sparkles = _expression(mood)
    return {'cream': sparkles, 'charcoal': marks}
