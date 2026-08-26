"""Host-side STL inspection helpers retained for Factory handoff."""

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

__all__ = [
    "KERNEL_BODY_OBSERVATION_VERSION",
    "KernelBodyObservation",
    "STL_INSPECTION_RECEIPT_VERSION",
    "StlInspectionLimits",
    "StlPathInspectionError",
    "StlTopologyReceipt",
    "UPSTREAM_MIT_NOTICE",
    "UPSTREAM_SOURCE_COMMIT",
    "UPSTREAM_SOURCE_PATHS",
    "fits_bed_envelope",
    "inspect_stl_path",
    "inspect_stl_topology",
]
