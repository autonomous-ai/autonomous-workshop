"""One support-free triangular rear brace; print two."""

from cadgen.assembly import label_shape
from features.common import prism
import params as p


def build_brace():
    points = [(0.0, 0.0), (p.BRACE_RUN, 0.0), (p.BRACE_RUN, p.BRACE_RISE), (p.BRACE_RUN - p.BRACE_FOOT_W, p.BRACE_RISE)]
    return label_shape(prism(points, p.BRACE_T), "rear_brace")
