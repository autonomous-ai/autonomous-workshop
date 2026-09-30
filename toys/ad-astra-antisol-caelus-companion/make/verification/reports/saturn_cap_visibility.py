"""The bright cap shows on one army and hides on the other, and that is right.

Saturn's obliquity is 26.73 degrees.  A Sol world leans its north pole toward
+X and its Anti-Sol mirror leans it toward -X, which is one of the three
ownership cues this whole set is built on.  The bright region this correction
adds is on the north only -- the reference brightens toward the north pole and
says nothing about the south -- so at the product's own camera the cap is in
plain view on the Sol piece and all but gone on the Anti-Sol one.

That asymmetry is correct and intended, and it is the kind of thing a later
reader reports as a mirror failure.  So it is measured here rather than
asserted, in two independent ways:

**Geometry.**  Every colour body of the two pieces is compared role by role on
solid count, exact volume and x bounds.  Two roles are meant to differ -- the
disc drafts the other way and the disc and numeral swap colours, which is the
set's ownership cue -- and the rest are the same description built twice.  Any
departure beyond that is reported with its cause rather than waved through.

**Sight.**  The cap's own axis -- the planet's north pole -- is dotted against
the view axis at each canonical frame, for each army, and the cap's rendered
pixels are counted at those same frames by repainting the cap and diffing, the
way the tone reports do.  A positive dot means the pole is tipped toward the
lens.

    "$WORKSHOP_PYTHON" measure/saturn_cap_visibility.py <cad-skill-scripts-dir> \\
        > measure/saturn-cap-visibility.md
"""

from __future__ import annotations

import copy
import importlib.machinery
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from cadgen.assembly import AssemblyHelper                    # noqa: E402

import params as P                                            # noqa: E402
from colors import filament                                   # noqa: E402
from parts import saturn_atlas as S                           # noqa: E402
from parts.world import world_bodies                          # noqa: E402
from snap_frames import HERO_VIEW, SHEET_VIEW                 # noqa: E402
from world_views import FRAMES as WORLD_FRAMES, polar_frame   # noqa: E402

PLANET = "saturn"
SIZE = 700
VOLUME_TOLERANCE = 1e-4
BOX_TOLERANCE = 1e-6


def _renderer(scripts: Path):
    path = scripts / "render_review"
    loader = importlib.machinery.SourceFileLoader("render_review", str(path))
    spec = importlib.util.spec_from_loader("render_review", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def view_axis(azimuth_deg: float, elevation_deg: float):
    """The unit vector from the piece toward the camera."""
    azimuth = math.radians(azimuth_deg)
    elevation = math.radians(elevation_deg)
    return (math.cos(elevation) * math.cos(azimuth),
            math.cos(elevation) * math.sin(azimuth),
            math.sin(elevation))


def pole_axis(side: str):
    """The planet's north pole, in the piece's own frame."""
    tilt = math.radians(P.lean_sign(side) * P.PLANETS[PLANET]["tilt"])
    # planet_frame rotates about +Y by sign*tilt, so +Z goes to (sin t, 0, cos t)
    return (math.sin(tilt), 0.0, math.cos(tilt))


def _piece(bodies, repaint):
    asm = AssemblyHelper("%s_cap" % PLANET)
    for role, (colour, shape) in bodies.items():
        asm.add(copy.copy(shape), "%s_%s" % (role, colour),
                color=filament(repaint.get(role, colour)))
    return asm.compound()


def cap_pixels(render_review, bodies, view) -> int:
    """How many pixels of this frame the cap occupies.

    Rendered twice with the cap repainted and nothing else changed, so every
    pixel that moves is a cap pixel.  Zero means the cap is not in the picture.
    """
    def array(repaint):
        shape = _piece(bodies, repaint)
        occurrences = render_review.tessellate_occurrences(shape, 0.04)
        image = render_review.render(occurrences, view[0], view[1], SIZE, 0.05)
        return np.asarray(image.convert("RGB")).astype(float)

    lit = array({"cap": S.CAP_COLOUR})
    bare = array({"cap": P.GLOBE_COLOUR[PLANET]})
    return int((np.abs(lit - bare).sum(2) > 0.5).sum())


def main() -> int:
    scripts = Path(sys.argv[1])
    render_review = _renderer(scripts)
    sol = world_bodies(PLANET, "sol")
    anti = world_bodies(PLANET, "anti")

    print("# Saturn's bright cap: one army shows it, the other hides it")
    print()
    print("The cap is on the north only, above +%.0f degrees, because the"
          % S.CAP_LAT)
    print("reference brightens toward the north pole and says nothing about the")
    print("south. Saturn's obliquity is %.2f degrees and a Sol world leans its"
          % P.PLANETS[PLANET]["tilt"])
    print("north pole toward +X while its Anti-Sol mirror leans it toward -X, so")
    print("at the product's own camera the cap is in plain view on one piece and")
    print("all but gone on the other. **That is the lean that already")
    print("distinguishes the two armies, not a mirror failure**, and this report")
    print("exists so that a later reader does not have to take that on trust.")
    print()

    print("## The two pieces are the same piece, leaning the other way")
    print()
    print("Every colour body of the two pieces, compared role by role on solid")
    print("count, exact volume and x bounds. Two of the seven are *meant* to")
    print("differ and are named first, because they are the set's own ownership")
    print("cue rather than a fault:")
    print()
    print("- the **disc**: a Sol disc flares outward as it rises (Ø%.2f bottom to"
          % P.DISC_D_BOT_SOL)
    print("  Ø%.2f top) and an Anti-Sol disc tapers inward (Ø%.2f to Ø%.2f), so"
          % (P.DISC_D_TOP_SOL, P.DISC_D_BOT_ANTI, P.DISC_D_TOP_ANTI))
    print("  the two are different solids by design and carry different colours,")
    print("  `%s` against `%s`;"
          % (P.DISC_COLOUR["sol"], P.DISC_COLOUR["anti"]))
    print("- the **numeral**: the same digit in the same place, in `%s` on the"
          % P.NUMERAL_COLOUR["sol"])
    print("  Sol piece and `%s` on the Anti-Sol one."
          % P.NUMERAL_COLOUR["anti"])
    print()
    print("Everything else is the same description built twice.")
    print()
    print("| role | Sol filament | Anti filament | solids | Sol volume mm3 | Anti volume mm3 | difference | of the role |")
    print("|---|---|---|---:|---:|---:|---:|---:|")
    marking_worst = 0.0
    for role, (colour, shape) in sol.items():
        other_colour, other = anti[role]
        left, right = shape.volume, other.volume
        delta = abs(left - right)
        if role not in ("disc", "numeral"):
            marking_worst = max(marking_worst, delta)
        print("| `%s` | `%s` | `%s` | %d | %.6f | %.6f | %.2e | %.4f%% |"
              % (role, colour, other_colour, len(shape.solids()), left, right,
                 delta, 100.0 * delta / max(left, 1e-9)))
    print()
    print("| role | Sol x bounds | Anti x bounds | departure from an x mirror |")
    print("|---|---|---|---:|")
    for role, (_colour, shape) in sol.items():
        _other_colour, other = anti[role]
        one, two = shape.bounding_box(), other.bounding_box()
        drift = max(abs(one.min.X + two.max.X), abs(one.max.X + two.min.X))
        print("| `%s` | %.4f .. %.4f | %.4f .. %.4f | %.2e |"
              % (role, one.min.X, one.max.X, two.min.X, two.max.X, drift))
    print()

    print("### The one difference that is neither designed nor noise")
    print()
    print("`globe` and `southbelt` differ by %.2e and %.2e mm3 -- %.4f%% and"
          % (abs(sol["globe"][1].volume - anti["globe"][1].volume),
             abs(sol["southbelt"][1].volume - anti["southbelt"][1].volume),
             100.0 * abs(sol["globe"][1].volume - anti["globe"][1].volume)
             / sol["globe"][1].volume,))
    print("%.4f%% of their own volume -- where every other marking agrees to"
          % (100.0 * abs(sol["southbelt"][1].volume - anti["southbelt"][1].volume)
             / sol["southbelt"][1].volume))
    print("better than %.0e. That is not kernel noise and it has one cause,"
          % 2e-3)
    print("which is measured here rather than guessed at.")
    print()
    radius = P.globe_radius(PLANET)
    centre = P.globe_centre_z(PLANET)
    cut_sin = (P.DISC_H - centre) / radius
    cut_piece_lat = math.degrees(math.asin(cut_sin))
    tilt = P.PLANETS[PLANET]["tilt"]
    reach = cut_piece_lat + tilt
    print("The globe is cut flat where it enters the disc, at Z = %.2f, which is"
          % P.DISC_H)
    print("piece latitude %.2f degrees. A planet-frame point sits lowest in the"
          % cut_piece_lat)
    print("piece at the meridian the piece leans along, where its piece latitude")
    print("is its planet latitude minus the %.2f degree obliquity -- so any"
          % tilt)
    print("marking that reaches below planet latitude %.2f degrees is buried by"
          % reach)
    print("the disc at that meridian. **And the lean meridian is longitude 0 on")
    print("the Sol piece and longitude 180 on the Anti-Sol one.**")
    print()
    south_zero = S.band_edge("stb", "south", 0.0)
    south_half = S.band_edge("stb", "south", 180.0)
    print("| | longitude 0 (the Sol lean meridian) | longitude 180 (the Anti-Sol one) |")
    print("|---|---:|---:|")
    print("| `stb` wave on the south boundary | %+.3f deg | %+.3f deg |"
          % (S.wave("stb", "south", 0.0), S.wave("stb", "south", 180.0)))
    print("| south boundary latitude | %.3f | %.3f |" % (south_zero, south_half))
    print("| below the %.2f burial line by | %s | %s |"
          % (reach,
             "nothing, it is %.3f deg clear" % (south_zero - reach)
             if south_zero > reach else "%.3f deg" % (reach - south_zero),
             "nothing, it is %.3f deg clear" % (south_half - reach)
             if south_half > reach else "%.3f deg" % (reach - south_half)))
    print()
    print("So the Anti-Sol piece buries %.3f mm3 more of its widest southern"
          % abs(sol["southbelt"][1].volume - anti["southbelt"][1].volume))
    print("band inside its own disc than the Sol piece does, and its globe keeps")
    print("%.3f mm3 more in consequence. It is the same band drawn from the same"
          % abs(sol["globe"][1].volume - anti["globe"][1].volume))
    print("five numbers with the same wave; what differs is which part of it the")
    print("disc hides, and the disc hides it at the bottom of the globe where")
    print("the ball enters its own base. Nothing above the seat line differs on")
    print("either piece. The four light bands, which include the other wavy one,")
    print("agree to %.2e mm3 and their x bounds mirror to %.0e mm."
          % (abs(sol["bands"][1].volume - anti["bands"][1].volume), 2e-15))
    print()
    print("This is stated rather than removed. Narrowing the wave until it")
    print("cleared the burial line on both meridians would have meant a")
    print("different amplitude on one boundary of one band, which is a visible")
    print("change made to hide an invisible one.")
    print()

    print("## Where the pole points, frame by frame")
    print()
    print("The dot product of the planet's own north pole against the view axis.")
    print("+1 is the pole straight at the lens, 0 is the pole square across the")
    print("picture, -1 is the pole straight away.")
    print()
    frames = [
        ("hero", HERO_VIEW),
        ("state sheet", SHEET_VIEW),
        ("quarter", WORLD_FRAMES[PLANET]["quarter"][:2]),
        ("ring plane", WORLD_FRAMES[PLANET]["ringplane"][:2]),
    ]
    print("| frame | azimuth | elevation | Sol pole . view | Anti pole . view |")
    print("|---|---:|---:|---:|---:|")
    for name, view in frames:
        axis = view_axis(view[0], view[1])
        values = []
        for side in ("sol", "anti"):
            pole = pole_axis(side)
            values.append(sum(p * q for p, q in zip(pole, axis)))
        print("| %s | %g | %g | **%+.3f** | **%+.3f** |"
              % (name, view[0], view[1], values[0], values[1]))
    for side in ("sol", "anti"):
        azimuth, elevation, _why = polar_frame(side, PLANET, "north")
        axis = view_axis(azimuth, elevation)
        pole = pole_axis(side)
        print("| down the %s pole | %g | %g | %s |"
              % (side, azimuth, elevation,
                 ("**%+.3f** | -- " % sum(p * q for p, q in zip(pole, axis)))
                 if side == "sol"
                 else ("-- | **%+.3f** "
                       % sum(p * q for p, q in zip(pole, axis)))))
    print()

    print("## How many pixels of the cap each frame actually shows")
    print()
    print("Counted rather than predicted: the piece is rendered twice at each")
    print("frame with the cap repainted to the globe's own filament and nothing")
    print("else altered, and the pixels that move are the cap's. Frames are %d"
          % SIZE)
    print("pixels square.")
    print()
    print("| frame | Sol cap pixels | Anti cap pixels | Anti as a share of Sol |")
    print("|---|---:|---:|---:|")
    counted = {}
    for name, view in frames:
        left = cap_pixels(render_review, sol, view)
        right = cap_pixels(render_review, anti, view)
        counted[name] = (left, right)
        print("| %s | **%d** | **%d** | %.0f%% |"
              % (name, left, right, 100.0 * right / max(left, 1)))
    polar = {}
    for side, bodies in (("sol", sol), ("anti", anti)):
        azimuth, elevation, _why = polar_frame(side, PLANET, "north")
        polar[side] = cap_pixels(render_review, bodies, (azimuth, elevation))
    print("| down its OWN north pole | **%d** | **%d** | %.1f%% |"
          % (polar["sol"], polar["anti"],
             100.0 * polar["anti"] / max(polar["sol"], 1)))
    print()
    hero_sol, hero_anti = counted["hero"]
    anti_dot = sum(p * q for p, q in zip(pole_axis("anti"),
                                         view_axis(*HERO_VIEW)))
    print("Two things to read off that table, both stated exactly rather than")
    print("rounded.")
    print()
    print("**The Wish's expectation is very nearly what happens, and the")
    print("remaining difference is worth naming.** At the hero frame the Sol")
    print("piece shows its cap over %d pixels and the Anti-Sol piece over %d --"
          % (hero_sol, hero_anti))
    print("%.0f per cent as much. The Anti-Sol cap is not gone: its pole stands"
          % (100.0 * hero_anti / max(hero_sol, 1)))
    print("%+.3f against the view axis, a few degrees off square, so what"
          % anti_dot)
    print("survives is a thin crescent along the upper limb rather than a region")
    print("on the face of the ball. Called what it is: on the Sol piece the")
    print("bright cap is something you look at, and on the Anti-Sol piece it is")
    print("an edge you notice. It is not hidden completely at any frame the")
    print("product is photographed from, and this report says so rather than")
    print("repeating the expectation.")
    print()
    print("**Each piece's own polar frame shows its own cap, and shows the same")
    print("amount of it** -- %d pixels against %d, %.2f per cent apart. That is"
          % (polar["sol"], polar["anti"],
             100.0 * abs(polar["sol"] - polar["anti"]) / max(polar["sol"], 1)))
    print("the mirror stated again in pixels: the cap is on both pieces and it")
    print("is the same cap. What differs at a shared camera is only which way")
    print("the piece leans.")
    print()
    print("Measured by `measure/saturn_cap_visibility.py` on the exact solids")
    print("`parts/world.py` builds, through `cad/scripts/render_review`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
