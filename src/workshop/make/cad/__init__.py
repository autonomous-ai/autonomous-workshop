"""Host-side STEP inspection helpers retained for Factory handoff.

STEP is the only geometry format Workshop writes, seals or ships (ADR 0062);
the STL topology helpers this package once re-exported are gone with the mesh
gates that produced their input.
"""

from workshop.make.cad.filament_names import (
    FILAMENT_COLOUR_NAMES,
    normalise_colour_name,
    occurrence_colour_name,
)
from workshop.make.cad.step_color import (
    StepPartColor,
    linear_to_srgb_hex,
    read_step_part_colors,
)

__all__ = [
    "FILAMENT_COLOUR_NAMES",
    "StepPartColor",
    "linear_to_srgb_hex",
    "normalise_colour_name",
    "occurrence_colour_name",
    "read_step_part_colors",
]
