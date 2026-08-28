"""Shared thrust washer for the central axle and crank grip; print two."""

from cadgen.assembly import label_shape
from features.common import cylinder_from
import params as p


def build_small_washer():
    washer = cylinder_from(p.WASHER_OD / 2.0, p.WASHER_T)
    bore = cylinder_from(p.SMALL_WASHER_BORE / 2.0, p.WASHER_T)
    return label_shape(washer - bore, "small_thrust_washer")
