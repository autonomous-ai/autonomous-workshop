"""Replaceable printed cam follower roller."""

from cadgen.assembly import label_shape
from features.common import cylinder_from
import params as p


def build_follower_roller():
    roller = cylinder_from(p.FOLLOWER_D / 2.0, p.FOLLOWER_ROLLER_T) - cylinder_from(
        p.FOLLOWER_BORE / 2.0, p.FOLLOWER_ROLLER_T
    )
    return label_shape(roller, "follower_roller")
