"""Cross key retaining one frame tenon; print two."""

from cadgen.assembly import label_shape
from features.common import box_from
import params as p


def build_frame_key():
    return label_shape(box_from(0.0, 0.0, 0.0, p.KEY_W, p.FRAME_KEY_L, p.KEY_T), "frame_key")
