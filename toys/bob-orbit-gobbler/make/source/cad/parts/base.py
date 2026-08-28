"""Wide weighted-looking printed base with frame and brace sockets."""

from cadgen.assembly import label_shape
from features.common import box_from
import params as p


def build_base():
    body = box_from(-p.BASE_W / 2.0, -p.BASE_D / 2.0, 0.0, p.BASE_W, p.BASE_D, p.BASE_H)
    frame_y = p.FRAME_REAR_Y - p.FRAME_T / 2.0
    for x in (-p.FRAME_TENON_X, p.FRAME_TENON_X):
        mortise = box_from(
            x - p.FRAME_MORTISE_W / 2.0,
            frame_y - p.FRAME_MORTISE_T / 2.0,
            p.BASE_H - p.FRAME_MORTISE_DEPTH,
            p.FRAME_MORTISE_W, p.FRAME_MORTISE_T, p.FRAME_MORTISE_DEPTH,
        )
        keyway = box_from(
            x - p.KEY_SLOT_W / 2.0,
            frame_y - p.FRAME_KEY_SLOT_L / 2.0,
            p.BASE_H - p.FRAME_KEY_SLOT_T,
            p.KEY_SLOT_W, p.FRAME_KEY_SLOT_L, p.KEY_SLOT_T,
        )
        body = body - mortise - keyway
    for x in (-p.BRACE_X, p.BRACE_X):
        brace_slot = box_from(
            x - p.BRACE_SLOT_W / 2.0,
            p.BRACE_BASE_Y,
            p.BASE_H - p.FRAME_MORTISE_DEPTH,
            p.BRACE_SLOT_W, p.BRACE_SLOT_L, p.FRAME_MORTISE_DEPTH,
        )
        body = body - brace_slot
    return label_shape(body, "base")
