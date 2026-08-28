"""Portable compatibility subset of the Workshop CAD fit helpers.

Normal generation imports the canonical ``cadfits`` module supplied by the
Workshop CAD launchers.  The host also executes project audits from a copied,
standalone project whose ``PYTHONPATH`` intentionally contains only that copy.
This module keeps those read-only audits self-contained without relying on a
workspace-relative path.

Compatibility target:
``skills/cad/scripts/cadfits.py`` SHA-256
``f69cb9f34a6c78714827a7276e005dae0bf2f7a01dd30cbbce49541fb524f3fb``.
Only the two functions used by Lunar Relay are reproduced here.
"""

from __future__ import annotations


FIT_TABLE: dict[str, float] = {
    "press": -0.05,
    "snug": 0.10,
    "slip": 0.20,
    "free": 0.40,
}
DEFAULT_FIT = "slip"
EXPLICIT_MIN = -0.20
EXPLICIT_MAX = 0.60


def mating_clearance(fit: str | float = DEFAULT_FIT) -> float:
    """Return the per-side FDM clearance in millimetres."""

    if isinstance(fit, str):
        try:
            return FIT_TABLE[fit]
        except KeyError:
            raise ValueError(
                f"unknown fit class {fit!r}; choose one of {sorted(FIT_TABLE)}, "
                "or pass an explicit per-side clearance in mm"
            ) from None
    if isinstance(fit, bool) or not isinstance(fit, (int, float)):
        raise TypeError(
            f"fit must be a class name or a per-side clearance in mm, got {fit!r}"
        )
    value = float(fit)
    if not EXPLICIT_MIN <= value <= EXPLICIT_MAX:
        raise ValueError(
            f"explicit clearance {value} mm is outside the hand-assembly band "
            f"{EXPLICIT_MIN}..{EXPLICIT_MAX} mm"
        )
    return value


def slot_for(tab: float, fit: str | float = DEFAULT_FIT) -> float:
    """Derive a female opening from one male dimension and one fit."""

    if tab <= 0:
        raise ValueError(f"tab must be > 0, got {tab}")
    return tab + 2 * mating_clearance(fit)
