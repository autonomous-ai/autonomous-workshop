"""Fixed eye-like shield over the front carrier hub and spokes."""

from cadgen.assembly import label_shape
from features.common import cylinder_from
import params as p


def build_eye_guard():
    eye = cylinder_from(p.EYE_D / 2.0, p.EYE_T) - cylinder_from(p.CARRIER_BORE / 2.0, p.EYE_T)
    pupil = cylinder_from(p.EYE_D * 0.16, p.EYE_T, x=p.EYE_D * 0.12)
    return label_shape(eye - pupil, "eye_guard")
