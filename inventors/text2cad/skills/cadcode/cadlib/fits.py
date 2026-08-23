"""FDM mating fits — one source of truth for assembled-part clearances.

A mating interface (tab/slot, lip/groove, peg/socket, lid/cavity) has a male and
a female half that **must** derive from one nominal dimension plus a clearance,
or they drift until the parts jam or fall apart. These helpers pick the correct
per-side FDM clearance for a named fit class and apply it in one place, so both
halves stay locked to the same nominal:

    from cadlib.fits import peg_for, slot_for

    cavity = inner_l                     # the female, owned by the base
    lip    = peg_for(cavity, "slip")     # the male, derived — can't drift

Per-side clearances assume a calibrated 0.4 mm-nozzle FDM printer. Tune once
here if your printer runs tight or loose; every helper that reads the table
follows.
"""

from __future__ import annotations

# Per-side clearance (mm) by fit class. Positive = gap; negative = interference.
# Ordered tight -> loose. ``press`` is a true interference (seats with force or
# heat); for a structural press fit also see ``cutouts.add_press_fit_pocket``.
FIT_TABLE: dict[str, float] = {
    "press": -0.05,  # interference — won't fall out; needs force / heat to seat
    "snug": 0.10,    # light friction; hand-press, stays put without force
    "slip": 0.20,    # slides / seats freely by hand — default assembled fit
    "free": 0.40,    # loose, easy hand assembly; drops in with no fuss
}

DEFAULT_FIT = "slip"


def mating_clearance(fit: str = DEFAULT_FIT) -> float:
    """Per-side FDM clearance (mm) for a named fit class (see ``FIT_TABLE``)."""
    try:
        return FIT_TABLE[fit]
    except KeyError:
        raise ValueError(
            f"unknown fit class {fit!r}; choose one of {sorted(FIT_TABLE)}"
        ) from None


def slot_for(tab: float, fit: str = DEFAULT_FIT) -> float:
    """Female opening for a male of size ``tab`` — ``tab + 2·clearance``.

    Build the male at ``tab`` and the female at ``slot_for(tab, fit)`` so the two
    halves are always one edit apart and never drift.
    """
    if tab <= 0:
        raise ValueError(f"tab must be > 0, got {tab}")
    return tab + 2 * mating_clearance(fit)


def peg_for(hole: float, fit: str = DEFAULT_FIT) -> float:
    """Male peg/lip for a female of size ``hole`` — ``hole − 2·clearance``.

    The inverse of :func:`slot_for`: derive the male from the female the base
    already owns, so the mate shares one source-of-truth dimension.
    """
    if hole <= 0:
        raise ValueError(f"hole must be > 0, got {hole}")
    peg = hole - 2 * mating_clearance(fit)
    if peg <= 0:
        raise ValueError(
            f"fit {fit!r} clearance is too large for a {hole} mm hole "
            "(peg would be non-positive)"
        )
    return peg


# Print-in-place gap (mm) — the gap to leave on a mating FACE for two parts
# printed together in ONE job and never separated. This is the gap per face, not
# a per-side value to double. It is looser than the assembled FIT_TABLE above
# because simultaneously-printed faces must survive bridge sag, stringing, and
# first-layer squish that hand-assembled parts avoid. Calibrated to a 0.4 mm
# nozzle / 0.2 mm layer. Sources + rationale: references/patterns/print-in-place.md
PIP_FIT_TABLE: dict[str, float] = {
    "tight": 0.20,    # pin-in-barrel hinge sweet spot — minimal wobble
    "sliding": 0.30,  # default: a captive slider / drawer that moves freely
    "loose": 0.40,    # generous — large faces, tall Z spans, extra safety margin
}

PIP_DEFAULT_FIT = "sliding"

# Filaments that ooze/string more than PLA need a touch more gap to stay free.
_PIP_OOZE_BUMP = {"PETG", "ABS", "ASA", "PETG-CF"}


def print_in_place_gap(
    fit: str = PIP_DEFAULT_FIT,
    *,
    layer_height: float = 0.2,
    material: str = "PLA",
) -> dict[str, float]:
    """XY, Z, and bottom-chamfer clearances (mm) for a print-in-place joint.

    Parts printed together in one job (never separated) must leave an OPEN gap on
    **every** mating face or they fuse into one solid — the "everything stuck
    together" failure. Returns the gaps to apply, keyed by direction:

    - ``xy`` — horizontal gap per mating face, from :data:`PIP_FIT_TABLE`. Add
      0.05 mm for ooze-prone filaments (PETG/ABS/ASA).
    - ``z`` — vertical gap, ``xy + layer_height``. It **must** exceed ``xy``: the
      top surface of a gap is an unsupported bridge that droops onto the layer
      below and bonds. The ``+layer_height`` is a conservative rule of thumb —
      the *direction* (Z > XY) is well established, but no exact multiplier is
      validated, so tune empirically if a joint still fuses or rattles.
    - ``bottom_chamfer`` — 0.5 mm; apply as a 45° chamfer (or extra clearance) to
      any gap feature touching the build plate, to clear elephant's foot (the
      squished first layer widens ~0.2 mm and closes plate-level gaps).

    See ``references/patterns/print-in-place.md`` for how to apply these.
    """
    try:
        xy = PIP_FIT_TABLE[fit]
    except KeyError:
        raise ValueError(
            f"unknown print-in-place fit {fit!r}; choose one of {sorted(PIP_FIT_TABLE)}"
        ) from None
    if layer_height <= 0:
        raise ValueError(f"layer_height must be > 0, got {layer_height}")
    if material.upper() in _PIP_OOZE_BUMP:
        xy += 0.05
    return {
        "xy": round(xy, 3),
        "z": round(xy + layer_height, 3),
        "bottom_chamfer": 0.5,
    }
