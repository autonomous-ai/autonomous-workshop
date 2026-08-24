#!/usr/bin/env python3
"""Print-parameter derivations for FDM, and the hollow that actually hollows.

The sibling of `cadfits`. That one derives the second half of a mate from the
first so a clearance cannot be typed twice; this one derives a wall from the
nozzle that has to lay it down, and removes material the same way every time.

    import cadprint
    WALL = cadprint.min_wall(0.4)              # 0.80 -- two perimeters
    body = cadprint.hollow(body, cadprint.shell_wall(0.4))

**`offset(solid, -wall)` does not hollow anything.** It shrinks the solid: a
20 mm cube offset by -2 comes back as 4096 mm3, which is 16 cubed, not the
3904 mm3 of a 2 mm shell. The sign reads like "shell inward" and is not. The
two forms that do work are the two below, and both are verified in the
self-check against volumes known in closed form:

    hollow(part, wall)                 part - offset(part, -wall)   sealed void
    open_shell(part, wall, face)       offset(part, -wall, openings=face)

A sealed void is fine for FDM and wrong for resin, which needs somewhere for
the uncured liquid to leave from; `open_shell` or a drilled drain is that. The
sealed form also exports as a mesh with **two shells**, an outer and an inner,
which `check_mesh` reports and which is correct rather than a defect.

Measure the result rather than assuming it:

    python skills/cad/scripts/check_thickness <part>.stl --nozzle 0.4

and read `references/print-optimisation.md` for when hollowing is not worth it.

    .venv/bin/python skills/cad/scripts/cadprint.py      # self-check
"""

from __future__ import annotations

PLA_DENSITY = 1.24          # g/cm3
DEFAULT_NOZZLE = 0.4        # mm
PERIMETERS = 2              # the fewest that make a wall rather than a line
SHELL_PERIMETERS = 3        # a wall that also carries load


def line_width(nozzle: float = DEFAULT_NOZZLE) -> float:
    """Extruded line width. Slicers default this to the nozzle diameter."""
    if nozzle <= 0:
        raise ValueError(f"nozzle must be positive, got {nozzle}")
    return float(nozzle)


def min_wall(nozzle: float = DEFAULT_NOZZLE, perimeters: int = PERIMETERS) -> float:
    """The thinnest wall the printer can lay down as a wall.

    Below two lines a slicer either drops the wall entirely or prints two
    perimeters with a gap between them, and neither shows up in any B-rep check.
    """
    if perimeters < 1:
        raise ValueError(f"perimeters must be at least 1, got {perimeters}")
    return line_width(nozzle) * perimeters


def shell_wall(nozzle: float = DEFAULT_NOZZLE,
               perimeters: int = SHELL_PERIMETERS) -> float:
    """The wall to leave when hollowing: thicker than the minimum, on purpose.

    A shell at exactly `min_wall` has no perimeter left over for a fillet, a
    countersink or a screw boss, and nothing to lose to the inward offset's own
    rounding at a concave corner.
    """
    return min_wall(nozzle, perimeters)


def _core(part, wall):
    """The inward offset, with a real message when it collapses."""
    from build123d import Kind, offset
    if wall <= 0:
        raise ValueError(f"wall must be positive, got {wall}")
    try:
        return offset(part, -wall, kind=Kind.INTERSECTION)
    except Exception as exc:                       # noqa: BLE001 - retyped, not hidden
        raise ValueError(
            f"a {wall} mm wall leaves nothing to remove -- the part is thinner "
            f"than {2 * wall} mm somewhere. Measure it with check_thickness "
            f"before choosing a wall. ({type(exc).__name__}: {exc})") from exc


def hollow(part, wall: float):
    """Remove everything more than `wall` from the surface, leaving a sealed void.

    Returns the part unchanged, and says so, when the wall is thick enough that
    there is nothing inside to remove -- a silent no-op here reads downstream as
    a hollow that happened.
    """
    core = _core(part, wall)
    if core is None or not core.solids():
        raise ValueError(
            f"a {wall} mm wall removes nothing: no point in this part is further "
            f"than {wall} mm from its surface. It is already a shell.")
    result = part - core
    if not result.solids():
        raise ValueError(f"hollowing at {wall} mm returned no solid")
    if result.volume >= part.volume:
        raise ValueError(
            f"hollowing at {wall} mm did not remove anything "
            f"({part.volume:.1f} -> {result.volume:.1f} mm3)")
    return result


def open_shell(part, wall: float, openings):
    """Hollow and open it, so the void can drain and support can be removed."""
    from build123d import Kind, offset
    if wall <= 0:
        raise ValueError(f"wall must be positive, got {wall}")
    try:
        result = offset(part, -wall, openings=openings, kind=Kind.INTERSECTION)
    except Exception as exc:                       # noqa: BLE001
        raise ValueError(
            f"a {wall} mm open shell failed; the part is likely thinner than "
            f"{2 * wall} mm somewhere ({type(exc).__name__}: {exc})") from exc
    if result is None or not result.solids():
        raise ValueError(f"open_shell at {wall} mm returned no solid")
    return result


def savings(before, after, density: float = PLA_DENSITY,
            infill: float = 0.15) -> dict:
    """What hollowing bought, in the two units that differ by an order of magnitude.

    `removed` is what left the model. `filament` is what will actually not be
    extruded, which is far less: the slicer was only going to put `infill` of
    that space in anyway. Reporting the first as if it were the second is the
    standard way to overstate this by 6x.
    """
    removed = float(before.volume - after.volume)
    return {
        "removed_mm3": removed,
        "removed_share": removed / float(before.volume) if before.volume else 0.0,
        "filament_mm3": removed * infill,
        "filament_g": removed * infill / 1000.0 * density,
    }


def _self_check():
    import math
    from build123d import Axis, Box, Kind, Sphere, offset

    assert min_wall(0.4) == 0.8, min_wall(0.4)
    assert min_wall(0.6) == 1.2, min_wall(0.6)
    assert min_wall(0.4, 3) == shell_wall(0.4), shell_wall(0.4)

    # The claim in the docstring, checked rather than repeated: a bare inward
    # offset shrinks, and only the difference hollows.
    cube = Box(20, 20, 20)
    shrunk = offset(cube, -2, kind=Kind.INTERSECTION)
    assert abs(shrunk.volume - 16.0 ** 3) < 1e-6, shrunk.volume

    shell = hollow(cube, 2)
    assert abs(shell.volume - (20.0 ** 3 - 16.0 ** 3)) < 1e-6, shell.volume
    assert len(shell.solids()) == 1, len(shell.solids())
    assert len(shell.shells()) == 2, len(shell.shells())      # outer and void

    ball = hollow(Sphere(20), 2)
    want = 4 / 3 * math.pi * (20.0 ** 3 - 18.0 ** 3)
    assert abs(ball.volume - want) / want < 1e-9, ball.volume

    top = cube.faces().sort_by(Axis.Z)[-1]
    opened = open_shell(cube, 2, top)
    assert abs(opened.volume - (20.0 ** 3 - 16.0 ** 3 - 16.0 * 16.0 * 2)) < 1e-6, opened.volume

    for wall, part, why in ((2, Box(20, 20, 3), "thinner than 2 x wall"),
                            (12, Box(20, 20, 20), "nothing further than the wall")):
        try:
            hollow(part, wall)
        except ValueError:
            pass
        else:
            raise AssertionError(f"hollow should have refused: {why}")

    got = savings(cube, shell, infill=0.15)
    assert abs(got["removed_mm3"] - 16.0 ** 3) < 1e-6, got
    assert abs(got["filament_mm3"] - 16.0 ** 3 * 0.15) < 1e-6, got
    print("cadprint self-check: ok")


if __name__ == "__main__":
    _self_check()
