"""Pinion thrust washer."""

from cadgen.assembly import label_shape
from features.common import cylinder_from
import params as p


def build_pinion_washer():
    return label_shape(
        cylinder_from(p.WASHER_OD / 2.0, p.WASHER_T) - cylinder_from(p.PINION_WASHER_BORE / 2.0, p.WASHER_T),
        "pinion_washer",
    )
