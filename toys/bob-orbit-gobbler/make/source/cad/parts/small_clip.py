"""Shared snap clip for the central axle and crank grip; print two."""

from cadgen.assembly import label_shape
from features.common import c_clip
import params as p


def build_small_clip():
    clip = c_clip(
        p.SMALL_CLIP_OD / 2.0,
        p.SMALL_CLIP_ID / 2.0,
        p.CLIP_T,
        p.SMALL_CLIP_OPENING,
    )
    return label_shape(clip, "small_snap_clip")
