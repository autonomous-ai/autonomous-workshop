"""Derive the exact display states this revision's evidence needs.

Every state is an exact STEP written from the same builders the delivered parts
come from; nothing here is a presentation-only edit of geometry. The STEP header
timestamp is zeroed so the same geometry always hashes the same.
"""
from pathlib import Path
import re

from build123d import export_step, Compound, Pos, Rot
from assembly import build_assembly
from periastra_lib import *

STAMP = re.compile(r"(FILE_NAME\('[^']*',')[^']*(')")

SEAT = FLOOR                   # a counter's underside on a flush inlay top, z11.0


def export_deterministic(shape, path):
    export_step(shape, str(path))
    path = Path(path)
    path.write_text(STAMP.sub(r"\g<1>1970-01-01T00:00:00\g<2>", path.read_text(), count=1))


def cell(c, r):
    return cell_centre(c, r)


def _placed(forked, location, name):
    shape = location*build_counter(forked)
    shape.label = name
    shape.color = FORKED_COLOR if forked else SINGLE_COLOR
    return shape


def man(forked, c, r, spin=0.0):
    """One counter sitting on a dark cell."""
    x, y = cell(c, r)
    side = 'moon' if forked else 'sun'
    return [_placed(forked, Pos(x, y, SEAT)*Rot(Z=spin), f'{side}_man')]


def king(forked, c, r, top_spin=0.0):
    """A crowned piece: a second counter of the same colour stacked face to face.

    The upper counter is turned over, so the two rim bands and the two symbol
    tops meet as four coplanar surfaces at full face level.
    """
    x, y = cell(c, r)
    side = 'moon' if forked else 'sun'
    return [_placed(forked, Pos(x, y, SEAT), f'{side}_king_lower'),
            _placed(forked, Pos(x, y, SEAT + 2*COUNTER_HEIGHT)*Rot(X=180)*Rot(Z=top_spin),
                    f'{side}_king_upper')]


def counter_faces(forked):
    """The same counter three ways: as built, turned over, and standing on edge.

    The turned-over copy is rotated 180 deg about X - the axis the crescent is
    symmetric about - so if the two faces really are mirror images the two discs
    present an identical face. The third stands on its edge, canted 20 deg off
    the camera so one face is seen at a grazing angle: the rim band and the top
    of the raised symbol read as one straight line at full face level.
    """
    pitch = COUNTER_DIAMETER + 6.0
    return Compound(label='counter_faces', children=[
        _placed(forked, Pos(-pitch, 0, 0), 'as_built_face_up'),
        _placed(forked, Pos(0, 0, COUNTER_HEIGHT)*Rot(X=180), 'turned_over_face_up'),
        _placed(forked, Pos(pitch, 0, COUNTER_DIAMETER/2)*Rot(Z=20)*Rot(Y=90), 'on_edge'),
    ])


def counter_flip(forked):
    """One counter rolled over in four steps, so both of its faces are seen on one piece."""
    pitch = COUNTER_DIAMETER + 8.0
    poses = [(0, 'face_a_up'), (55, 'rolling_a'), (125, 'rolling_b'), (180, 'face_b_up')]
    return Compound(label='counter_flip', children=[
        _placed(forked, Pos((i-1.5)*pitch, 0, COUNTER_DIAMETER/2)*Rot(X=angle), name)
        for i, (angle, name) in enumerate(poses)])


def board_scene(populated):
    """The whole board seen on its own: base plus its 32 inlays, with or without
    the 24 counters in their starting rows.

    This is the frame the chequer question is asked on. The inlays are separate
    occurrences carrying their own colour, so what the renderer shows is the
    colour contrast a player actually gets, not a shading artefact.
    """
    parts = [build_base()]
    inlay = build_inlay()
    for n, (c, r) in enumerate(dark_cells(), start=1):
        x, y = cell(c, r)
        shape = Pos(x, y, BACKING)*inlay
        shape.label = f'inlay_{n:02d}'
        shape.color = INLAY_COLOR
        parts.append(shape)
    if populated:
        for forked, rows in ((False, range(3)), (True, range(5, 8))):
            for r in rows:
                for c in range(ROWS):
                    if (c + r) % 2 == 0:
                        parts += man(forked, c, r)
    return Compound(label='board_populated' if populated else 'board_empty', children=parts)


def kings_scene():
    """A populated corner of the board: single men beside crowned stacks."""
    parts = [build_base()]
    inlay = build_inlay()
    for n, (c, r) in enumerate(dark_cells(), start=1):
        x, y = cell(c, r)
        shape = Pos(x, y, BACKING)*inlay
        shape.label = f'inlay_{n:02d}'
        shape.color = INLAY_COLOR
        parts.append(shape)
    parts += man(False, 2, 2) + man(True, 4, 4)
    parts += king(False, 4, 2)                  # a Sun king, crowned by stacking
    parts += king(True, 2, 4, top_spin=180)     # worst case: the two crescents on opposite sides
    return Compound(label='kings', children=parts)


def write_states():
    out = Path(__file__).parent.parent/'evidence-states'
    out.mkdir(exist_ok=True)
    export_deterministic(build_assembly(LIFT), out/'opened.step')
    export_deterministic(build_assembly(include_roof=False), out/'playing.step')
    export_deterministic(build_roof(), out/'roof.step')
    export_deterministic(kings_scene(), out/'kings.step')
    export_deterministic(board_scene(True), out/'board-populated.step')
    export_deterministic(board_scene(False), out/'board-empty.step')
    export_deterministic(build_inlay(), out/'inlay.step')
    for name, forked in (('sun', False), ('moon', True)):
        shape = build_counter(forked)
        shape.label = f'{name}_counter'
        export_deterministic(shape, out/f'counter-{name}.step')
        export_deterministic(counter_faces(forked), out/f'faces-{name}.step')
        export_deterministic(counter_flip(forked), out/f'flip-{name}.step')


if __name__ == '__main__':
    write_states()
