"""Constant-section curved fender, printed on one side of its arch."""
from features.common import annular_sector
from params import (ARCH_INNER, ARCH_OUTER, BODY_FENDER_CENTER_XZ,
    BODY_FENDER_ANGLES, BODY_FENDER_Y_WIDTH)

def build():
    # Fit repair r3: 14.5 width meets fork faces instead of overlapping them.
    return annular_sector(*BODY_FENDER_CENTER_XZ,ARCH_INNER,ARCH_OUTER,
        *BODY_FENDER_ANGLES,*BODY_FENDER_Y_WIDTH)
