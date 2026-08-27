"""Pinion sleeve snap clip."""

from cadgen.assembly import label_shape
from features.common import c_clip
import params as p


def build_pinion_key():
    clip = c_clip(p.PINION_CLIP_OD / 2.0, p.PINION_CLIP_ID / 2.0, p.CLIP_T, p.PINION_CLIP_OPENING)
    return label_shape(clip, "pinion_snap_clip")
