"""Relocation-safe subset of the CAD skill's mating-fit derivation.

The CAD launchers provide their canonical ``cadfits`` module when generating
geometry.  The host also runs project-local audits from an isolated copy where
that launcher directory is intentionally absent.  This fallback preserves the
same explicit-clearance contract for those standalone audits; it is not a
second fit table or a geometry-specific tolerance decision.
"""

from __future__ import annotations

EXPLICIT_MIN = -0.20
EXPLICIT_MAX = 0.60


def mating_clearance(fit: float) -> float:
    """Return one explicit per-side clearance in the canonical allowed band."""
    if isinstance(fit, bool) or not isinstance(fit, (int, float)):
        raise TypeError(f"fit must be an explicit per-side clearance in mm, got {fit!r}")
    value = float(fit)
    if not EXPLICIT_MIN <= value <= EXPLICIT_MAX:
        raise ValueError(
            f"explicit clearance {value} mm is outside the hand-assembly band "
            f"{EXPLICIT_MIN}..{EXPLICIT_MAX} mm"
        )
    return value


def slot_for(tab: float, fit: float) -> float:
    """Derive a female opening as ``tab + 2 * per-side clearance``."""
    if tab <= 0:
        raise ValueError(f"tab must be > 0, got {tab}")
    return tab + 2.0 * mating_clearance(fit)
