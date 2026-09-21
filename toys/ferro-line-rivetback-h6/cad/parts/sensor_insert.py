from build123d import Align, Box, Pos
from features.forms import color_part, clipped_prism
from params import cyan_rgb


def build():
    # Two-millimetre light gaps keep the three unequal towers legible in the
    # frontal signature silhouette.  A low bridge makes them one printable
    # component, while the rear tongue provides the actual keyed hub seat.
    center = clipped_prism(11.0, 5.0, 9.0, 1.5)
    left = Pos(-10.5, 0, 0.0) * clipped_prism(6.0, 5.0, 8.0, 1.0)
    right = Pos(10.5, 0, 0.0) * clipped_prism(6.0, 5.0, 8.0, 1.0)
    bridge = Box(21.0, 5.0, 4.0, align=(Align.CENTER, Align.CENTER, Align.MIN))
    tongue = Pos(0, -3.0, 2.0) * Box(16.0, 6.0, 4.0, align=(Align.CENTER, Align.CENTER, Align.CENTER))
    return color_part(center + left + right + bridge + tongue, "sensor_insert", cyan_rgb)
