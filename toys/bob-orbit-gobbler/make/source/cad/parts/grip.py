"""Free-spinning cylindrical hand grip."""

from cadgen.assembly import label_shape
from features.common import cylinder_from
import params as p


def build_grip():
    return label_shape(
        cylinder_from(p.GRIP_D / 2.0, p.GRIP_L) - cylinder_from(p.GRIP_BORE / 2.0, p.GRIP_L),
        "crank_grip",
    )
