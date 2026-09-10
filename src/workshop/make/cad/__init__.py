"""Host-side STEP inspection helpers retained for Factory handoff.

STEP is the only geometry format Workshop writes, seals or ships (ADR 0062);
the STL topology helpers this package once re-exported are gone with the mesh
gates that produced their input.
"""

from workshop.make.cad.step_color import (
    StepPartColor,
    linear_to_srgb_hex,
    read_step_part_colors,
)

__all__ = [
    "StepPartColor",
    "linear_to_srgb_hex",
    "read_step_part_colors",
]
