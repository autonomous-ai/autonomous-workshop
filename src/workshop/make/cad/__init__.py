"""Host-side STL and STEP inspection helpers retained for Factory handoff."""

from workshop.make.cad.mesh import (
    KERNEL_BODY_OBSERVATION_VERSION,
    STL_INSPECTION_RECEIPT_VERSION,
    UPSTREAM_MIT_NOTICE,
    UPSTREAM_SOURCE_COMMIT,
    UPSTREAM_SOURCE_PATHS,
    KernelBodyObservation,
    StlInspectionLimits,
    StlPathInspectionError,
    StlTopologyReceipt,
    fits_bed_envelope,
    inspect_stl_path,
    inspect_stl_topology,
)
from workshop.make.cad.step_color import (
    StepPartColor,
    linear_to_srgb_hex,
    read_step_part_colors,
)

__all__ = [
    "KERNEL_BODY_OBSERVATION_VERSION",
    "KernelBodyObservation",
    "STL_INSPECTION_RECEIPT_VERSION",
    "StlInspectionLimits",
    "StlPathInspectionError",
    "StepPartColor",
    "StlTopologyReceipt",
    "UPSTREAM_MIT_NOTICE",
    "UPSTREAM_SOURCE_COMMIT",
    "UPSTREAM_SOURCE_PATHS",
    "fits_bed_envelope",
    "inspect_stl_path",
    "inspect_stl_topology",
    "linear_to_srgb_hex",
    "read_step_part_colors",
]
