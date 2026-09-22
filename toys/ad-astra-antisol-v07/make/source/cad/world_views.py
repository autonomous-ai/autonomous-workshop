"""One world on its own, in colour, for a frame that shows its surface.

The set renders show sixteen worlds at board scale, where Earth is five
millimetres of blue and Mars is less.  All three corrections this set has
carried are surface outlines, so each needs a frame where an outline is what
you see: one exact piece, alone and large, with the camera on the face the
Wish names.

Written for Earth's coastline correction and reused unchanged in shape for
Mars's albedo one and then for Mercury's plains and Caloris basin -- the only
thing any of those worlds needs of it is its own list of frames, so `FRAMES`
is keyed by planet and `polar_frame` takes the planet whose pole it is looking
down.

Nothing here is a print target and nothing is turned or modified.  This writes
the exact colour bodies `parts.world` builds, at the origin, in their own
print orientation; `render_review --view <az>,<el>` moves the camera.

It also writes the two pieces side by side in one frame.  Apart is where the
Wish wants them -- one piece, alone, large -- but a reader given only the two
single frames reads the mirrored lean as "the maps are in different
orientations", because at one camera the Sol world tips its north pole toward
the lens and the Anti-Sol world tips it away.  Side by side, under one camera,
that is plainly one cue inverted and the surfaces are plainly the same.

    "$WORKSHOP_PYTHON" world_views.py <scratch>/worlds mars \\
        <cad-skill-scripts-dir> snap/worlds

The third and fourth arguments turn on rendering: the exact colour STEPs are
written to the scratch directory, and one PNG per named frame -- plus the two
armies' own polar frames and the side-by-side pair at each named frame -- is
written into the product tree beside them.  Without them only the STEPs are
written, which is what the earlier revisions did before their renders were
driven from here.
"""

from __future__ import annotations

import sys
from pathlib import Path

from build123d import Location, export_step

from cadgen.assembly import AssemblyHelper

from colors import filament
from parts.world import world_bodies

#: planet -> frame name -> (azimuth, elevation, what faces the camera).
#: `render_review` puts the camera at that azimuth with east to the right, and
#: longitude 0 of a world faces piece +X, so the azimuth IS the meridian in the
#: middle of the picture, give or take the globe's own lean.
FRAMES = {
    "earth": {
        "atlantic": (-30.0, 12.0,
                     "longitude 30 west: the Americas on the left of the "
                     "Atlantic, Africa and Europe on the right"),
        "pacific": (170.0, 12.0,
                    "longitude 170 east: the Pacific, Asia and Australia on "
                    "the left, the Americas coming round on the right"),
        "eurasia": (70.0, 12.0,
                    "longitude 70 east: Europe and Asia across the top, "
                    "Africa below them, Australia coming round on the right"),
    },
    "mercury": {
        "caloris": (-50.0, 20.0,
                    "longitude 50 west: the Caloris basin in the middle of "
                    "the picture, its bright floor inside a rim of the same "
                    "tone as the plains, with bare gray globe all round it"),
        "opposite": (130.0, 20.0,
                     "longitude 130 east: the far face, with the three "
                     "southern plains run together into one region and no "
                     "Caloris anywhere in it"),
    },
    "venus": {
        # Venus is upside down, so the azimuth that shows a Venusian longitude
        # is not that longitude: the 177.36 degree obliquity turns the map
        # over before the camera sees it.  Both azimuths below were measured
        # rather than read off -- the dot product of each province against the
        # view axis, swept over azimuth at this elevation, on both armies.
        # `measure/venus-facing.md`.
        "aphrodite": (-46.0, 12.0,
                      "Aphrodite Terra square in the middle of the picture, "
                      "the long beige equatorial highland the reference is "
                      "recognised by, with the darker Atalanta plain coming "
                      "round the upper limb"),
        "beta_phoebe": (164.0, 12.0,
                        "the opposite face: Beta Regio and Phoebe Regio, the "
                        "two small highlands, with Guinevere Planitia beside "
                        "them and no Aphrodite anywhere in the picture"),
    },
    "jupiter": {
        # The spot's own meridian is longitude -48, and longitude 0 of a world
        # faces piece +X, so the azimuth that puts the Great Red Spot in the
        # middle of the picture IS -48.  Jupiter's obliquity is 3.13 degrees,
        # the second smallest in the set, so the mirrored lean moves it by
        # almost nothing and the same azimuth serves both armies -- unlike
        # Venus, where a 177 degree obliquity turns the map over first.
        # `measure/jupiter-facing.md` measures what each frame actually sees.
        #
        # Elevation 5 rather than the 12 the other worlds use, and not
        # something below the equator.  Below it, for the reason Mars's frames
        # give: a world's disc is Ø34.00 and every globe in the set is
        # smaller, so a camera under the equator sees the underside of the
        # disc.  Above it, because a camera at +12 puts its own sub-point at
        # planet latitude +10 and lands the North Equatorial Belt face-on while
        # foreshortening the South Equatorial by its own width.  The South
        # Equatorial is the wider of the two -- 13 degrees against 10, measured
        # in `measure/jupiter-atlas-resolution.md` -- and an independent reader
        # of the +12 frames reported the opposite, that the widest belt sat
        # north of the middle.  That was the camera, not the globe.  At +5 the
        # sub-point sits within a couple of degrees of the equator on both
        # armies and the two belts are shown on equal terms.
        "spot": (-48.0, 5.0,
                 "longitude 48 west: the Great Red Spot in the middle of the "
                 "picture, low and south of the equator, sitting in the bright "
                 "South Tropical Zone with the South Equatorial Belt bending "
                 "north around it"),
        "opposite": (132.0, 5.0,
                     "longitude 132 east: the far face, six unequal belts and "
                     "five bright zones across it and no spot anywhere in the "
                     "picture"),
    },
    "saturn": {
        # Saturn's obliquity is 26.73 degrees and the Sol piece leans its north
        # pole toward +X, so at the product's own azimuth of -55 the north pole
        # tips toward the lens on the Sol piece and away from it on the
        # Anti-Sol one.  That asymmetry is the ownership cue the whole set is
        # built on and it is what makes the bright northern cap visible on one
        # army and hidden on the other; `measure/saturn-cap-visibility.md`
        # measures it rather than leaving a reader to call it a mirror failure.
        #
        # Elevation 20 rather than the 12 the inner worlds use.  This is the
        # one piece in the set whose widest feature is not its disc: the ring
        # projects 2.00 mm per side of a globe that already fills the disc, and
        # at +12 the ring's own ellipse is narrow enough that a reader reads it
        # as a rim rather than as a ring in projection.  At +20 it opens to a
        # third of its own diameter on the Sol piece.  Not higher: above about
        # +25 the ring starts to hide the equatorial band behind it.
        "quarter": (-55.0, 20.0,
                    "the product's own azimuth: the ring seen in projection as "
                    "an open ellipse, the five unequal bands across the globe, "
                    "and -- on the Sol piece, which leans its north pole toward "
                    "the lens -- the bright cap above +58"),
        # Straight along the ring's own plane.  The ring plane is the globe's
        # equator turned about +Y by the obliquity, so its normal lies in the
        # XZ plane on both armies; a camera on the Y axis at zero elevation is
        # therefore square to that normal and sees the ring exactly edge-on,
        # whichever way the piece leans.  That is the frame that shows the ring
        # is a flat annulus of one thickness rather than a cone or a skirt, and
        # it is the frame where the web under it is in plain view.
        #
        # -90 rather than +90, and that is about light rather than geometry.
        # Both are exactly in the ring plane -- the ring's normal has no Y
        # component on either army, so either camera on the Y axis is square to
        # it -- but the renderer's key light comes over the camera's left
        # shoulder, and at +90 the piece is lit from behind: the whole globe
        # falls into its own terminator, the white disc renders mid-gray and
        # the band tones this correction exists to judge cannot be read at all.
        # Both were rendered before choosing. At -90 the same geometry is lit
        # square on.
        "ringplane": (-90.0, 0.0,
                      "along the ring's own plane: the ring edge-on as a single "
                      "line across the globe, the support web under its low "
                      "side, and the band system seen from the equator"),
    },
    "mars": {
        # There is deliberately no frame below the equator.  A world's disc is
        # Ø34.00 and its globe is smaller than that on every planet in the
        # set, so a camera placed under the equator sees the underside of the
        # disc and almost nothing of the ball.  That is the geometry, not a
        # gap in the evidence, and what the southern hemisphere carries is
        # measured on the solids in `measure/mars-surface.md` instead.
        "syrtis": (70.0, 12.0,
                   "longitude 70 east: Syrtis Major in the middle of the "
                   "picture, Sinus Sabaeus running away to its west and Mare "
                   "Cimmerium coming round on the left"),
        "opposite": (250.0, 12.0,
                     "longitude 250 east: the far face, with the southern "
                     "belt -- Sirenum, Cimmerium and Tyrrhenum -- across the "
                     "middle and no Syrtis anywhere in it"),
    },
}


#: planet -> which poles get their own frame.  North alone everywhere the
#: pole is up; Venus gets both because its 177.36 degree obliquity puts the
#: north pole under the board, and the north frame is kept as the evidence of
#: exactly that.
POLES = {"venus": ("north", "south")}


def polar_frame(side: str, planet: str = "earth",
                pole: str = "north") -> tuple[float, float, str]:
    """Straight down one of the planet's own poles.

    The pole leans at the planet's true obliquity, toward +X on a Sol world
    and toward -X on its Anti-Sol mirror, so the camera that looks down it is
    not the piece's own top view and is not the same camera for both armies,
    nor the same camera for two planets with different obliquities.  This is
    the frame that shows whether a cap is a lid or an ice field.

    `pole` defaults to north, which is every frame this project wrote before
    Venus.  Venus needs the other one as well and is the reason the argument
    exists: at 177.36 degrees its north pole points very nearly straight DOWN,
    so the north-pole camera sits 87 degrees below the horizon and sees the
    underside of the disc rather than the ball.  That is the geometry the
    obliquity actually produces, and it is rendered and kept as the proof of
    it; the frame that shows this world's visible pole region is the south
    one.  Nothing else in the set changes: for a planet whose pole is up, the
    south frame is the one that sees the disc.
    """
    import params as P

    tilt = P.PLANETS[planet]["tilt"]
    azimuth = 0.0 if P.lean_sign(side) > 0 else 180.0
    if pole == "south":
        # The south pole is the north pole turned through 180 degrees about
        # the piece's own axis: the azimuth flips and the elevation negates.
        return (azimuth + 180.0) % 360.0, tilt - 90.0, (
            "down the south pole of the %s world" % side)
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


#: How large a per-world frame is rendered.  Big enough that a 4.33 mm basin
#: on a 13.78 mm globe is hundreds of pixels across, which is the whole point
#: of rendering one piece alone.
FRAME_SIZE = 900

#: How finely the piece is tessellated for these frames, in millimetres of
#: chord error and in radians of angle.  An independent reader of these frames
#: called the ball "visibly low-poly" -- polygonal silhouettes, faceted shading
#: across the pale zones, stair-stepping along every band boundary and about
#: twenty hard concentric rings over each bare polar cap.  None of that is in
#: the solid: the globe is an exact sphere and every band boundary is an exact
#: ruled surface, so it is the tessellation to fix.
#:
#: The millimetre tolerance is not what fixes it, and that was measured rather
#: than assumed.  On this piece `Shape.tessellate` returns 138,761 triangles at
#: 0.03 mm, 138,911 at 0.008 and 144,981 at 0.002: the chord error is nowhere
#: near binding.  What binds is the ANGULAR tolerance, which build123d defaults
#: to 0.1 radians -- 5.7 degrees, about sixty-three steps around a full circle,
#: which is exactly the twenty rings a reader counts across a 45 degree polar
#: cap.  `render_review.tessellate_occurrences` does not expose it, so these
#: frames tessellate here instead and pass it.  At 0.03 radians, 1.7 degrees,
#: the same piece comes out at 1,357,677 triangles and the faceting is gone;
#: finer than that the mesh grows faster than the picture improves.
FRAME_TOLERANCE = 0.008
FRAME_ANGULAR_TOLERANCE = 0.03


def _tessellate(render_review, shape):
    """`render_review.tessellate_occurrences`, with the angular tolerance named.

    Identical to the renderer's own routine -- same leaves, same colour lookup,
    same array shapes -- except that it hands `Shape.tessellate` both halves of
    the deflection instead of letting the angular half default.
    """
    import numpy as np

    occurrences = []
    for index, child in enumerate(render_review._leaves(shape)):
        vertices, triangles = child.tessellate(
            FRAME_TOLERANCE, FRAME_ANGULAR_TOLERANCE)
        points = np.asarray([[p.X, p.Y, p.Z] for p in vertices], dtype=float)
        faces = np.asarray(triangles, dtype=np.int64)
        if len(points) and len(faces):
            occurrences.append(
                (points, faces, render_review._shape_colour(child, index)))
    if not occurrences:
        raise ValueError("tessellation produced no triangles")
    return occurrences


def _renderer(scripts: Path):
    import importlib.machinery
    import importlib.util

    path = scripts / "render_review"
    loader = importlib.machinery.SourceFileLoader("render_review", str(path))
    spec = importlib.util.spec_from_loader("render_review", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def render_frames(planet: str, steps: Path, scripts: Path, target: Path) -> list[Path]:
    """One PNG per named frame, per army, plus the polar and pair frames.

    The file names are `<planet>-<side>-<frame>.png` and
    `<planet>-pair-<frame>.png`, which is what the README and the spec cite.
    The camera for each comes from `FRAMES` and `polar_frame` above, so a
    frame cannot drift away from the sentence that describes it.
    """
    render_review = _renderer(scripts)
    target.mkdir(parents=True, exist_ok=True)
    written = []

    def shot(source: Path, view, out: Path):
        _src, shape = render_review.build_shape(source)
        occurrences = _tessellate(render_review, shape)
        render_review.render(
            occurrences, view[0], view[1], FRAME_SIZE, 0.05).save(out)
        written.append(out)
        return out

    for side in ("sol", "anti"):
        source = steps / ("%s-%s.step" % (planet, side))
        for name, view in FRAMES[planet].items():
            shot(source, view, target / ("%s-%s-%s.png" % (planet, side, name)))
        for pole in POLES.get(planet, ("north",)):
            azimuth, elevation, _why = polar_frame(side, planet, pole)
            suffix = "polar" if pole == "north" else "%s-polar" % pole
            shot(source, (azimuth, elevation),
                 target / ("%s-%s-%s.png" % (planet, side, suffix)))

    pair = steps / ("%s-pair.step" % planet)
    for name, view in FRAMES[planet].items():
        shot(pair, view, target / ("%s-pair-%s.png" % (planet, name)))
    return written


if __name__ == "__main__":
    where = Path(sys.argv[1] if len(sys.argv) > 1 else "snap/worlds")
    planet = sys.argv[2] if len(sys.argv) > 2 else "earth"
    for item in write_worlds(planet, where):
        print(item)
    if len(sys.argv) > 4:
        for item in render_frames(planet, where, Path(sys.argv[3]), Path(sys.argv[4])):
            print(item)
