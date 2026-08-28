"""Captive T slider with D-like channel body and unequal-lug round moon pilot."""

from cadgen.assembly import label_shape
from features.common import box_from, cylinder_from
import params as p


def build_lunar_slider():
    x0 = -p.SLIDER_LENGTH / 2.0
    base = box_from(x0, -p.SLIDER_BASE_W / 2.0, 0.0, p.SLIDER_LENGTH, p.SLIDER_BASE_W, p.SLIDER_BASE_T)
    neck = box_from(
        x0, -p.SLIDER_THROAT_W / 2.0, p.SLIDER_BASE_T,
        p.SLIDER_LENGTH, p.SLIDER_THROAT_W, p.SLIDER_T - p.SLIDER_BASE_T,
    )
    follower_x = p.FOLLOWER_LOCAL_X
    round_hole = cylinder_from(p.FOLLOWER_BORE / 2.0, p.SLIDER_T, x=follower_x)
    d_window = box_from(
        follower_x - p.FOLLOWER_BORE / 2.0,
        -p.FOLLOWER_BORE / 2.0,
        0.0,
        p.FOLLOWER_BORE / 2.0 + p.FOLLOWER_SHAFT_FLAT + p.RUN_CLEAR, p.FOLLOWER_BORE, p.SLIDER_T,
    )
    return label_shape(base + neck - (round_hole & d_window), "lunar_slider")
