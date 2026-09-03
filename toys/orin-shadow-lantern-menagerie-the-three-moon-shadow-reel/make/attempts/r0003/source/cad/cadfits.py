#!/usr/bin/env python3
"""Project-local FDM mating-fit derivations for isolated verification.

This small module preserves the API and clearance table used by the
materialized CAD skill's ``scripts/cadfits.py`` (source SHA-256
``f69cb9f34a6c78714827a7276e005dae0bf2f7a01dd30cbbce49541fb524f3fb``).
It is stored with the CAD project because the Workshop host verifies a copied
project tree in isolation, where the skill scripts directory is not importable
by project-local measurement hooks.
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
    """Return the per-side clearance in millimetres for a named or explicit fit."""
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
    """Derive a female opening from a male nominal and one per-side fit."""
    if tab <= 0:
        raise ValueError(f"tab must be > 0, got {tab}")
    return tab + 2 * mating_clearance(fit)


def peg_for(hole: float, fit: str | float = DEFAULT_FIT) -> float:
    """Derive a male peg from a female nominal and one per-side fit."""
    if hole <= 0:
        raise ValueError(f"hole must be > 0, got {hole}")
    peg = hole - 2 * mating_clearance(fit)
    if peg <= 0:
        raise ValueError(
            f"fit {fit!r} clearance is too large for a {hole} mm hole"
        )
    return peg


def _self_check() -> int:
    import math

    checks = [
        list(FIT_TABLE.values()) == sorted(FIT_TABLE.values()),
        FIT_TABLE["press"] < 0,
        math.isclose(peg_for(slot_for(10.0, "slip"), "slip"), 10.0),
        math.isclose(slot_for(10.0, "slip") - 10.0, 0.4),
        math.isclose(mating_clearance(0.15), 0.15),
    ]
    print("all checks passed" if all(checks) else "self-check failed")
    return 0 if all(checks) else 1


if __name__ == "__main__":
    raise SystemExit(_self_check())
