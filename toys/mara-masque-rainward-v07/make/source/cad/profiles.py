"""Plan outlines for the whole board. No CAD kernel here.

The lane frames and sector outlines live in `geom`, the corona in `flame`;
this module re-exports both. There is no hero arch: an earlier correction
removed the closed loop entirely, and nothing replaced it but ordinary flames.
"""
from geom import (  # noqa: F401  re-exported plan surface
    bank_boundary_points,
    boundary_width,
    next_point,
    polar_extent,
    sector_corners,
    sector_curves,
    sector_profile,
    theta,
    xy,
)
from flame import (  # noqa: F401  re-exported plan surface
    converging_pairs,
    flame_cap,
    flame_clearance,
    flame_plan,
    flame_rise,
    flank_edge_count,
    flank_fit_error,
    pitch_arc_mm,
    root_arc_mm,
    sense_runs,
    spine_heading,
    spine_point,
    tongue_curves,
    tongue_face_curves,
    tongue_face_outline,
    tongue_flank,
    tongue_frame,
    tongue_half_width,
    tongue_mid_over_root,
    tongue_mid_width,
    tongue_normal,
    tongue_sense,
    tongue_outline,
    tongue_ramp,
    tongue_tip,
    tongue_tip_thickness,
    tongue_top_z,
    tongue_turn,
    valley,
    valley_arc_mm,
)
