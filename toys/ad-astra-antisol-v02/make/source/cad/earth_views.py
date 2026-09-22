"""One world on its own, in colour, for a frame that shows its surface.

The set renders show sixteen worlds at board scale, where Earth is five
millimetres of blue.  The correction this revision carries is a coastline, so
it needs a frame where a coastline is what you see: one exact piece, alone and
large, with the camera on the ocean the Wish names.

Nothing here is a print target and nothing is turned or modified.  This writes
the exact colour bodies `parts.world` builds, at the origin, in their own
print orientation; `render_review --view <az>,<el>` moves the camera.

It also writes the two pieces side by side in one frame.  Apart is where the
Wish wants them -- one piece, alone, large -- but a reader given only the two
single frames reads the mirrored lean as "the maps are in different
orientations", because at one camera the Sol world tips its north pole toward
the lens and the Anti-Sol world tips it away.  Side by side, under one camera,
that is plainly one cue inverted and the continents are plainly the same.

    "$WORKSHOP_PYTHON" earth_views.py snap/worlds earth
"""

from __future__ import annotations

import sys
from pathlib import Path

from build123d import Location, export_step

from cadgen.assembly import AssemblyHelper

from colors import filament
from parts.world import world_bodies

#: frame name -> (azimuth, elevation, what faces the camera).  `render_review`
#: puts the camera at that azimuth with east to the right, and longitude 0 of
#: a world faces piece +X, so the azimuth IS the meridian in the middle of the
#: picture, give or take the globe's own lean.
FRAMES = {
    "atlantic": (-30.0, 12.0,
                 "longitude 30 west: the Americas on the left of the "
                 "Atlantic, Africa and Europe on the right"),
    "pacific": (170.0, 12.0,
                "longitude 170 east: the Pacific, Asia and Australia on the "
                "left, the Americas coming round on the right"),
    "eurasia": (70.0, 12.0,
                "longitude 70 east: Europe and Asia across the top, Africa "
                "below them, Australia coming round on the right"),
}


def polar_frame(side: str) -> tuple[float, float, str]:
    """Straight down the planet's own north pole.

    The pole leans at the planet's true obliquity, toward +X on a Sol world
    and toward -X on its Anti-Sol mirror, so the camera that looks down it is
    not the piece's own top view and is not the same camera for both armies.
    This is the frame that shows whether the cap is a lid or an ice field.
    """
    import params as P

    tilt = P.PLANETS["earth"]["tilt"]
    azimuth = 0.0 if P.lean_sign(side) > 0 else 180.0
    return azimuth, 90.0 - tilt, "down the north pole of the %s world" % side


def world_assembly(planet: str, side: str):
    asm = AssemblyHelper("%s_%s" % (planet, side))
    for role, (colour, shape) in world_bodies(planet, side).items():
        asm.add(shape, "%s_%s_%s_%s" % (planet, side, role, colour),
                color=filament(colour))
    return asm.compound()


#: How far apart the two pieces stand in the side-by-side frame.  Their discs
#: are \u00d834.00, so this is a clear 8 mm of air between them.
PAIR_GAP = 42.0


def pair_assembly(planet: str):
    """Sol on the left, Anti-Sol on the right, both in their own orientation."""
    asm = AssemblyHelper("%s_pair" % planet)
    for side, offset in (("sol", -PAIR_GAP / 2.0), ("anti", PAIR_GAP / 2.0)):
        at = Location((0, offset, 0))
        for role, (colour, shape) in world_bodies(planet, side).items():
            asm.add(at * shape, "%s_%s_%s_%s" % (planet, side, role, colour),
                    color=filament(colour))
    return asm.compound()


def write_worlds(planet: str, target: Path) -> list[Path]:
    target.mkdir(parents=True, exist_ok=True)
    written = []
    for side in ("sol", "anti"):
        path = target / ("%s-%s.step" % (planet, side))
        export_step(world_assembly(planet, side), str(path))
        written.append(path)
    path = target / ("%s-pair.step" % planet)
    export_step(pair_assembly(planet), str(path))
    written.append(path)
    return written


if __name__ == "__main__":
    where = Path(sys.argv[1] if len(sys.argv) > 1 else "snap/worlds")
    for item in write_worlds(sys.argv[2] if len(sys.argv) > 2 else "earth", where):
        print(item)
