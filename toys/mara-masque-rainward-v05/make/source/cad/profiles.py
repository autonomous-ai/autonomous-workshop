"""Plan outlines for the whole board. No CAD kernel here.

The lane frames and sector outlines live in `geom`, the corona skirt in
`flame`; this module re-exports both and owns the hero arch.
"""
from math import pi, radians, sin, sqrt

import params as P
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
    boundary_radius_limit,
    core_curves,
    flank_edge_count,
    flank_fit_error,
    skirt_curves,
    skirt_outline,
    skirt_radius,
    spine_point,
    tongue_curves,
    tongue_face_curves,
    tongue_flank,
    tongue_frame,
    tongue_half_width,
    tongue_mid_width,
    tongue_normal,
    tongue_outline,
    tongue_ramp,
    tongue_tip,
    tongue_tip_thickness,
    tongue_top_z,
    tongue_turn,
    trough,
)


# --- the hero arch ---------------------------------------------------------

def _hero_spine(t):
    """Steep legs under a domed crest, the crest leaning the way tongues sweep."""
    rise = sin(pi * min(max(t, 0.0), 1.0) ** P.HERO_SKEW) ** P.HERO_DOME
    return P.HERO_FOOT_R + (P.HERO_APEX_R - P.HERO_FOOT_R) * rise


def hero_profile():
    """The hero arch as a polar strip: it cannot self-intersect.

    The outer edge is the arch itself. The inner edge thickens exactly where a
    leg dives, so each foot keeps its full 2.8 mm across where it enters the
    body instead of touching the skirt at a point.
    """
    outer, inner = [], []
    n = P.HERO_SAMPLES
    for i in range(n + 1):
        t = i / n
        angle = P.HERO_START + P.HERO_SPAN * t
        r = _hero_spine(t)
        eps = 1.0 / (2 * n)
        t0, t1 = max(t - eps, 0.0), min(t + eps, 1.0)
        ds = r * radians(P.HERO_SPAN * (t1 - t0))
        slope = abs((_hero_spine(t1) - _hero_spine(t0)) / ds) if ds else 0.0
        deep = min(P.HERO_HALF * sqrt(1.0 + slope * slope), P.HERO_ROOT_CAP)
        outer.append(xy(r + P.HERO_HALF, angle))
        inner.append(xy(r - deep, angle))
    return outer + list(reversed(inner))
