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
    stem = cadfits.peg_for(bore, "fixed")       # the male, derived

That is the whole point. An assertion that merely restates the sizing formula
can be true by construction and prove nothing. A derivation cannot drift the
same way.

Per-side clearances assume a calibrated 0.4 mm-nozzle FDM printer. Tune once
here and every project that reads the table follows.

House fit rule (owner, 2026-11-13). The numbers are TOTAL clearance:

- fixed fit -- a tab, peg or leg into a socket: socket = feature + 0.1 mm
  (0.05 per side). A 1.0 mm square leg goes into a 1.1 mm socket.
- moving fit -- anything that rotates or slides (axle, hinge, slider):
  hole = shaft + 0.2 mm (0.10 per side). A 1.0 mm shaft goes into a 1.2 mm
  hole.

The table holds per-side values, so ``fixed`` is 0.05 and ``moving`` is 0.10.
``snug`` and ``slip`` are the older names for the same two fits. The rule is
for parts assembled after printing; a print-in-place joint has its own,
larger gaps (:data:`PIP_FIT_TABLE`), and a bought part's seat keeps the
``check_mount`` floor (:data:`BOUGHT_PART_MIN_CLEARANCE`).

Importing it
------------
Every CLI launcher in `skills/cad/scripts/` puts its own directory on
`sys.path` before loading a generator, so a generator, a `*_lib.py`, or a
`measure/*.py` run through `scripts/gen` / `export` / `inspect` / `check_*`
can `import cadfits` with no path setup, and `verify_project` runs the local
audits (`measure/check_fit.py`, `check_spec.py`, `check_landmarks.py`) with this
directory on `PYTHONPATH`. A script run directly by the interpreter
(`.venv/bin/python <project-dir>/measure/check_fit.py`) needs the one insert
those scripts already do for their project directory.

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
    "fixed": 0.05,   # house fixed fit: tab / peg / leg in a socket, 0.1 total
    "snug": 0.05,    # older name for `fixed`
    "moving": 0.10,  # house moving fit: axle / hinge / slider, 0.2 total
    "slip": 0.10,    # older name for `moving`
    "clear": 0.20,   # a bought part dropped into its printed seat (cadmount)
    "free": 0.40,    # loose drop-in or a screw's clearance hole; not a mate
}

# The house default is the moving fit: a mate that must turn or slide never
# binds, and a fixed one is a deliberate `fixed`.
DEFAULT_FIT = "moving"

# Workshop-local (ADR 0105): a design approved under an earlier table keeps
# it. Each named table is the FIT_TABLE and DEFAULT_FIT one period of this
# library shipped. ``WORKSHOP_FIT_TABLE`` names the one a process builds with:
# Workshop's make_round and verify_project set it from a seeded run's
# Approved Proof, and a designer reopening an approved Proof sets it by hand.
# Unset, the current table above holds. An unknown name refuses to import,
# so a pinned design never silently builds with another table.
FIT_TABLE_ENV = "WORKSHOP_FIT_TABLE"
CURRENT_FIT_TABLE = "fits-2026-11-13"
FIT_TABLES: dict[str, tuple[dict[str, float], str]] = {
    # The owner's total-clearance rule (2026-11-13), the table above.
    CURRENT_FIT_TABLE: (dict(FIT_TABLE), DEFAULT_FIT),
    # Every Proof approved before 2026-11-13: per-side snug 0.10, slip 0.20,
    # default slip. That library had no fixed, moving or clear, so no such
    # design names them; they keep their current values for the library's
    # own use (a bought part's seat is cut at clear 0.20, as slip cut it).
    "fits-legacy": ({"press": -0.05, "fixed": 0.05, "snug": 0.10, "moving": 0.10, "slip": 0.20,
                     "clear": 0.20, "free": 0.40}, "slip"),
}


def _pinned_table() -> None:
    import os

    name = os.environ.get(FIT_TABLE_ENV)
    if not name:
        return
    if name not in FIT_TABLES:
        raise ImportError("%s=%r names no fit table; known: %s"
                          % (FIT_TABLE_ENV, name, ", ".join(sorted(FIT_TABLES))))
    table, default = FIT_TABLES[name]
    global DEFAULT_FIT
    FIT_TABLE.clear()
    FIT_TABLE.update(table)
    DEFAULT_FIT = default


_pinned_table()

# A bought part does not compress. Its seat is cut at `clear` by default, and
# `check_mount` fails any seat whose measured gap is under this floor. This is a
# gate value, independent of the printed-part fits above: keep it at 0.10.
BOUGHT_PART_FIT = "clear"
BOUGHT_PART_MIN_CLEARANCE = 0.10

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

    >>> slot_for(1.0, "fixed")
    1.1
    """
    if tab <= 0:
        raise ValueError(f"tab must be > 0, got {tab}")
    return tab + 2 * mating_clearance(fit)


def peg_for(hole: float, fit: str | float = DEFAULT_FIT) -> float:
    """Male peg/lip for a female of size ``hole`` — ``hole − 2·clearance``.

    The inverse of :func:`slot_for`: derive the male from the female the other
    part already owns, so the mate shares one source-of-truth dimension.

    >>> peg_for(1.2, "moving")
    1.0
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
    - ``bottom_chamfer`` — 0.5 mm; the bed-face leg of a break (or extra
      clearance) on any gap feature touching the build plate, to clear
      elephant's foot (the squished first layer widens ~0.2 mm and closes
      plate-level gaps). Lean the break at most 30° off vertical — a symmetric
      45° chamfer fails the overhang gate (wiki: rounded-bodies-on-the-print-bed).

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
    import os

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

    # Workshop-local (ADR 0105): every named table names every class, and a
    # pinned table is exactly the one this process builds with.
    for name, (table, default) in FIT_TABLES.items():
        check(f"fit table {name} names every class", set(table) == set(FIT_TABLES[CURRENT_FIT_TABLE][0]))
        check(f"fit table {name} default is a class", default in table)
    pinned = os.environ.get(FIT_TABLE_ENV) or CURRENT_FIT_TABLE
    check(f"builds with fit table {pinned}", (FIT_TABLE, DEFAULT_FIT) == FIT_TABLES[pinned])
    if pinned == "fits-legacy":
        check("legacy: slip 1.0 mm shaft -> 1.4 mm hole", math.isclose(slot_for(1.0, "slip"), 1.4))
        check("legacy: default fit is slip", DEFAULT_FIT == "slip")
    if pinned == CURRENT_FIT_TABLE:
        # The owner's rule, in TOTAL clearance: fixed +0.1 mm, moving +0.2 mm.
        check("fixed: 1.0 mm leg -> 1.1 mm socket", math.isclose(slot_for(1.0, "fixed"), 1.1))
        check("moving: 1.0 mm shaft -> 1.2 mm hole", math.isclose(slot_for(1.0, "moving"), 1.2))
        check("snug is the older name for fixed", FIT_TABLE["snug"] == FIT_TABLE["fixed"])
        check("slip is the older name for moving", FIT_TABLE["slip"] == FIT_TABLE["moving"])
        check("default fit is the moving fit", DEFAULT_FIT == "moving")
    check("bought-part seat clears the check_mount floor",
          mating_clearance(BOUGHT_PART_FIT) > BOUGHT_PART_MIN_CLEARANCE)
    check("check_mount floor stays 0.10/side",
          math.isclose(BOUGHT_PART_MIN_CLEARANCE, 0.10))
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
