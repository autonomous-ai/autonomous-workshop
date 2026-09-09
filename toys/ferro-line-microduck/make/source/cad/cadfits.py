#!/usr/bin/env python
"""FDM mating fits — one source of truth for assembled-part clearances.

A mating interface (tab/slot, lip/groove, peg/socket, pin/hole, lid/cavity) has
a male and a female half that **must** derive from one nominal dimension plus a
clearance, or they drift until the parts jam or fall apart. Size the two halves
independently and nothing in the toolchain notices: `validate`, `interfere`,
`check_fit` and `check_motion` all read a model that is internally consistent
and still wrong on the bed.

Derive the second half instead, and the drift becomes unrepresentable:

    import cadfits

    bore = SEAT_BORE_D                          # the female, owned by the seat
    stem = cadfits.peg_for(bore, "slip")        # the male, derived

That is the whole point. An assertion that merely restates the sizing formula
can be true by construction and prove nothing. A derivation cannot drift the
same way.

Per-side clearances assume a calibrated 0.4 mm-nozzle FDM printer. Tune once
here and every project that reads the table follows.

Importing it
------------
Every CLI launcher in `skills/cad/scripts/` puts its own directory on
`sys.path` before loading a generator, so a generator, a `*_lib.py`, or a
`measure/*.py` run through `scripts/gen` / `export` / `inspect` / `check_*`
can `import cadfits` with no path setup. A script run directly by the
interpreter (`.venv/bin/python <project-dir>/measure/check_fit.py`) needs the
one insert those scripts already do for their project directory.

Deliberately NOT inside the vendored `cadgen` package: `cadgen` is installed
into `.venv` as a *copy* while the launchers prefer the vendored
`scripts/packages/cadgen/src`, so a module living there is read from two
different files depending on how the process started. This one has a single
home.

Self-check:

    .venv/bin/python "$CAD_SKILL_ROOT/scripts/cadfits.py"
"""

from __future__ import annotations

# Per-side clearance (mm) by fit class. Positive = gap; negative = interference.
# Ordered tight -> loose. ``press`` is a true interference: it seats with force
# or heat and does not come apart again by hand.
FIT_TABLE: dict[str, float] = {
    "press": -0.05,  # interference — won't fall out; needs force / heat to seat
    "snug": 0.10,    # light friction; hand-press, stays put without force
    "slip": 0.20,    # slides / seats freely by hand — default assembled fit
    "free": 0.40,    # loose, easy hand assembly; drops in with no fuss
}

DEFAULT_FIT = "slip"

# Hand-assembly band for an explicit per-side clearance. Outside it the mate is
# either an interference fit that needs force (below) or a rattling one (above),
# and both want to be a deliberate, named decision rather than a typo.
EXPLICIT_MIN = -0.20
EXPLICIT_MAX = 0.60


def mating_clearance(fit: str | float = DEFAULT_FIT) -> float:
    """Per-side FDM clearance (mm) for a fit.

    ``fit`` is normally a class name from :data:`FIT_TABLE` — that is the form
    to reach for in new work, because a name carries the intent ("this slides",
    "this is captive") where a float carries only a number.

    An explicit per-side clearance in millimetres is also accepted when a
    project has calibrated a value against a printed part. Both forms give the
    derivation one owner, which is the property that matters.
    """
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
            f"{EXPLICIT_MIN}..{EXPLICIT_MAX} mm; if that is intended, say so in "
            "the project spec and widen this band deliberately"
        )
    return value


def slot_for(tab: float, fit: str | float = DEFAULT_FIT) -> float:
    """Female opening for a male of size ``tab`` — ``tab + 2·clearance``.

    Build the male at ``tab`` and the female at ``slot_for(tab, fit)`` so the
    two halves are always one edit apart and cannot drift.

    >>> slot_for(4.0, "slip")
    4.4
    """
    if tab <= 0:
        raise ValueError(f"tab must be > 0, got {tab}")
    return tab + 2 * mating_clearance(fit)


def peg_for(hole: float, fit: str | float = DEFAULT_FIT) -> float:
    """Male peg/lip for a female of size ``hole`` — ``hole − 2·clearance``.

    The inverse of :func:`slot_for`: derive the male from the female the other
    part already owns, so the mate shares one source-of-truth dimension.

    >>> peg_for(5.6, "slip")
    5.2
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
# nozzle / 0.2 mm layer.
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

    Parts printed together in one job (never separated) must leave an OPEN gap
    on **every** mating face or they fuse into one solid — the "everything stuck
    together" failure. Returns the gaps to apply, keyed by direction:

    - ``xy`` — horizontal gap per mating face, from :data:`PIP_FIT_TABLE`. Add
      0.05 mm for ooze-prone filaments (PETG/ABS/ASA).
    - ``z`` — vertical gap, ``xy + layer_height``. It **must** exceed ``xy``:
      the top surface of a gap is an unsupported bridge that droops onto the
      layer below and bonds. The ``+layer_height`` is a conservative rule of
      thumb — the *direction* (Z > XY) is well established, but no exact
      multiplier is validated, so tune empirically if a joint still fuses or
      rattles.
    - ``bottom_chamfer`` — 0.5 mm; apply as a 45° chamfer (or extra clearance)
      to any gap feature touching the build plate, to clear elephant's foot (the
      squished first layer widens ~0.2 mm and closes plate-level gaps).

    A rigid-body sweep (`scripts/check_motion`) cannot answer whether a
    print-in-place joint comes out free — only a print can.
    """
    try:
        xy = PIP_FIT_TABLE[fit]
    except KeyError:
        raise ValueError(
            f"unknown print-in-place fit {fit!r}; choose one of "
            f"{sorted(PIP_FIT_TABLE)}"
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


def _self_check() -> int:
    """Assertions this module has to keep. Run as a script; no test framework."""
    import math

    failures: list[str] = []

    def check(label: str, ok: bool, detail: str = "") -> None:
        print(f"{'ok  ' if ok else 'FAIL'} {label}{('  - ' + detail) if detail else ''}")
        if not ok:
            failures.append(label)

    check("fit table ordered tight -> loose",
          list(FIT_TABLE.values()) == sorted(FIT_TABLE.values()),
          " ".join(f"{k}={v}" for k, v in FIT_TABLE.items()))
    check("press is an interference", FIT_TABLE["press"] < 0)
    check("default fit is a class", DEFAULT_FIT in FIT_TABLE)

    for name in FIT_TABLE:
        # The property the whole module exists for: the two derivations are
        # exact inverses, so a male and a female built from one nominal agree.
        check(f"peg_for/slot_for round-trip ({name})",
              math.isclose(peg_for(slot_for(10.0, name), name), 10.0, abs_tol=1e-9))
        check(f"gap is 2x the per-side clearance ({name})",
              math.isclose(slot_for(10.0, name) - 10.0, 2 * mating_clearance(name),
                           abs_tol=1e-9))

    check("slip is the documented 0.2/side", math.isclose(mating_clearance("slip"), 0.20))
    check("explicit clearance passes through", math.isclose(mating_clearance(0.15), 0.15))

    for bad, exc, label in (
        ("sloppy", ValueError, "unknown class rejected"),
        (5.0, ValueError, "absurd explicit clearance rejected"),
        (-1.0, ValueError, "absurd interference rejected"),
        (None, TypeError, "non-numeric fit rejected"),
        (True, TypeError, "bool rejected (it is not a clearance)"),
    ):
        try:
            mating_clearance(bad)
        except exc:
            check(label, True)
        except BaseException as err:  # noqa: BLE001 — reporting, not handling
            check(label, False, f"raised {type(err).__name__}")
        else:
            check(label, False, "no error raised")

    for bad_call, label in (
        (lambda: slot_for(0.0), "zero tab rejected"),
        (lambda: peg_for(-1.0), "negative hole rejected"),
        (lambda: peg_for(0.3, "free"), "clearance wider than the hole rejected"),
    ):
        try:
            bad_call()
        except ValueError:
            check(label, True)
        else:
            check(label, False, "no error raised")

    pip = print_in_place_gap("sliding")
    check("print-in-place Z gap exceeds XY", pip["z"] > pip["xy"], str(pip))
    check("ooze-prone filament gets more gap",
          print_in_place_gap("sliding", material="PETG")["xy"] > pip["xy"])
    try:
        print_in_place_gap("snug")  # an assembled class, not a print-in-place one
    except ValueError:
        check("print-in-place rejects an assembled fit class", True)
    else:
        check("print-in-place rejects an assembled fit class", False)

    print(f"\n{len(failures)} failed" if failures else "\nall checks passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_self_check())
