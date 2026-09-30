"""Can a player tell one world from the world beside it?

`measure/neptune_separation.py` asked this of Neptune and two neighbours and
answered it on four cues measured separately.  This is the same question and
the same method with both worlds named on the command line, because the owner's
second pass moved the burden onto Uranus and Uranus has three neighbours worth
asking about rather than two.

Uranus is now the only world in the set with NO surface marking, so everything
that tells a player what it is comes from three things: the ring, the size and
the `cyan`.  Each of the three is checked here against the world that contests
it.

**URANUS AGAINST NEPTUNE.**  Its neighbour in rank and in colour family, ranks
6 and 5, Ø22.02 against Ø21.89 -- 0.13 mm apart in a set whose whole ownership
cue is size.  Size cannot separate them.  Neptune now carries three white bands
and a dark spot; Uranus carries nothing at all.

**URANUS AGAINST SATURN.**  The other ringed world, and since this revision the
other world whose ring prints `white`.  A plate lying almost flat against a
hoop standing on edge, Ø30.00 against Ø24.02.  The colour of the ring no longer
separates these two, so the question is whether orientation alone still does.

**URANUS AGAINST EARTH.**  The other `blue`-family globe, four ranks apart.

Each pair is answered on the canonical side-by-side render at the product's own
frame rather than by eye:
`snap/worlds/<first>-<second>-hero.png` and its `-hero-anti.png` mirror.

    "$WORKSHOP_PYTHON" measure/world_separation.py uranus saturn \\
        > measure/uranus-saturn-separation.md
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import numpy as np                                            # noqa: E402
from PIL import Image                                         # noqa: E402

import params as P                                            # noqa: E402

BACKGROUND = (237, 240, 244)

#: What each world wears, in one clause.  A description of what a reader sees,
#: not a measurement; every number in it is measured in that world's own
#: resolution report.
SURFACE = {
    "mercury": "seven smooth albedo plains traced as rings and the Caloris basin",
    "venus": "seven radar highland provinces and three lowland plains",
    "earth": ("the world's coastlines as green land with beige dryland inside "
              "it and a white ice cap, an outline map a reader can check "
              "against an atlas"),
    "mars": "the classical albedo map and two lobed polar caps",
    "neptune": ("three closed white latitude bands, 0.96, 0.76 and 0.57 mm "
                "wide, running the whole way round the globe, plus one "
                "dark_gray oval 5.35 by 2.67 mm south of the equator"),
    "uranus": ("nothing. Since the owner's second pass this globe carries no "
               "marking of any kind: no hood, no cap, no band, no spot. It is "
               "one undivided cyan sphere with a white hoop standing on edge "
               "around its equator"),
    "saturn": ("five unequal soft bands in a mid amber, a bright white cap "
               "above +58, and a flat white ring plate lying almost level"),
    "jupiter": "six unequal belts, five bright zones and the Great Red Spot",
}

#: How each world's ring stands, for the silhouette table.
#:
#: Both are equatorial rings and neither passes over its planet's poles.  What
#: differs is where the poles point: Saturn's axis is 26.73 degrees off vertical
#: so its equatorial plane lies nearly flat, and Uranus's is 97.77 degrees -- its
#: poles point sideways -- so its equatorial plane stands nearly upright.  An
#: independent reviewer of this build caught an earlier draft of this table
#: describing Uranus's hoop as "pole-over-pole" and was right to: the hoop arches
#: over the ball's EQUATOR, and the two points it crosses at the top and bottom
#: of the mounted piece are equatorial points, not poles.
RING_STANCE = {
    "saturn": "a flat plate lying almost level, in the planet's own equatorial "
              "plane, 26.73 degrees off horizontal",
    "uranus": "an upright hoop standing on edge, in the planet's own equatorial "
              "plane, which on a world tipped 97.77 degrees stands 7.77 degrees "
              "past vertical, so it arches over the ball's equator while both "
              "poles point sideways",
}


def luma(rgb) -> float:
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def hexrgb(name: str):
    value = P.FILAMENT_HEX[name]
    return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5))


def globe_pixels(image: Image.Image, left_half: bool):
    """Every pixel of one globe, markings included.

    `measure/neptune_separation.py`'s routine, unchanged: the ball is found by
    its own saturated colour -- the discs are neutral and the background is a
    pale grey -- and the circle that colour occupies is then filled in, so pale
    markings ON the ball are counted as ball rather than dropped.
    """
    pixels = np.asarray(image.convert("RGB")).astype(int)
    height, width, _ = pixels.shape
    not_background = np.abs(pixels - np.array(BACKGROUND)).sum(2) > 24
    coloured = (pixels.max(2) - pixels.min(2)) > 40
    columns = np.arange(width)[None, :]
    rows = np.arange(height)[:, None]
    half = (columns < width * 0.55) if left_half else (columns > width * 0.45)
    upper = (rows < height * 0.72) if left_half else (rows < height * 0.60)
    seed = not_background & coloured & half & upper
    if not seed.any():
        return pixels, seed
    ys, xs = np.nonzero(seed)
    centre_x, centre_y = xs.mean(), ys.mean()
    radius = math.sqrt(seed.sum() / math.pi) * 1.02
    disc = ((columns - centre_x) ** 2 + (rows - centre_y) ** 2) <= radius ** 2
    return pixels, disc & not_background


def marking_fraction(pixels, mask):
    """How much of the ball is not its own globe colour: the pale pixels."""
    pale = (pixels.max(2) - pixels.min(2)) < 45
    count = int(mask.sum())
    if not count:
        return 0.0, 0
    return float((mask & pale).sum()) / count, count


def main() -> int:
    first, second = sys.argv[1], sys.argv[2]
    left, right = first.capitalize(), second.capitalize()
    frames = {
        "Sol": HERE.parent / "snap" / "worlds" / ("%s-%s-hero.png" % (first, second)),
        "Anti-Sol": HERE.parent / "snap" / "worlds" / ("%s-%s-hero-anti.png" % (first, second)),
    }
    step = abs(P.globe_diameter(second) - P.globe_diameter(first))
    same_spool = P.GLOBE_COLOUR[second] == P.GLOBE_COLOUR[first]
    ringed = [name for name in (first, second) if name in P.RINGED_WORLDS]

    print("# %s against %s at the product's own frame" % (left, right))
    print()
    print("Ranks %d and %d, Ø%.2f and Ø%.2f mm -- %.2f mm apart in a set whose"
          % (P.PLANETS[first]["rank"], P.PLANETS[second]["rank"],
             P.globe_diameter(first), P.globe_diameter(second), step))
    print("ranks are told apart by size. Measured on the canonical side-by-side")
    print("renders at the hero frame (azimuth -55, elevation 22), one per army.")
    print()
    print("This revision took every marking off Uranus, so this pair is asked")
    print("again on this run's own renders rather than inherited from the")
    print("archive.")
    print()

    from parts.world import build_world
    heights = {name: build_world(name, "sol").bounding_box().max.Z
               for name in (first, second)}

    print("## The size cue")
    print()
    print("| | %s | %s | apart |" % (left, right))
    print("|---|---:|---:|---:|")
    print("| rank | %d | %d | %d |"
          % (P.PLANETS[first]["rank"], P.PLANETS[second]["rank"],
             abs(P.PLANETS[second]["rank"] - P.PLANETS[first]["rank"])))
    print("| globe diameter mm | %.2f | %.2f | %.2f |"
          % (P.globe_diameter(first), P.globe_diameter(second), step))
    print("| piece height mm | %.2f | %.2f | %.2f |"
          % (heights[first], heights[second], abs(heights[second] - heights[first])))
    print("| obliquity deg | %.2f | %.2f | %.2f |"
          % (P.PLANETS[first]["tilt"], P.PLANETS[second]["tilt"],
             abs(P.PLANETS[second]["tilt"] - P.PLANETS[first]["tilt"])))
    print()
    percent = 100.0 * step / P.globe_diameter(first)
    if step < P.NOZZLE_MM:
        print("%.2f mm is %.1f per cent of %s's own diameter and less than one"
              % (step, percent, left))
        print("%.2f mm nozzle. **Size cannot separate these two globes**, and"
              % P.NOZZLE_MM)
        print("they are the only pair in the ladder of which that is true.")
    else:
        print("%.2f mm is %.1f per cent of %s's own diameter and %.0f nozzle"
              % (step, percent, left, step / P.NOZZLE_MM))
        print("widths, and the pieces stand %.2f mm apart in height."
              % abs(heights[second] - heights[first]))
        print("**Size separates this pair on its own**, which is what the size")
        gap = abs(P.PLANETS[second]["rank"] - P.PLANETS[first]["rank"])
        print("ladder is for: they are %d rank%s apart and they look it."
              % (gap, "" if gap == 1 else "s"))
    print()

    print("## The colour cue")
    print()
    first_hex, second_hex = hexrgb(P.GLOBE_COLOUR[first]), hexrgb(P.GLOBE_COLOUR[second])
    print("| | sealed hex | luma of 255 |")
    print("|---|---|---:|")
    for name, title, rgb in ((first, left, first_hex), (second, right, second_hex)):
        print("| %s globe `%s` | %s | %.1f |"
              % (title, P.GLOBE_COLOUR[name], P.FILAMENT_HEX[P.GLOBE_COLOUR[name]],
                 luma(rgb)))
    print()
    if same_spool:
        print("**They are the same spool**, so colour separates them by exactly")
        print("nothing and cannot be asked to.")
    else:
        print("Sealed, the two separate **%.1f** of 255 luma levels, and they"
              % abs(luma(first_hex) - luma(second_hex)))
        print("separate in hue as well. For scale, this project accepted 9.4 as")
        print("its narrowest usable separation, on Saturn's bands.")
    print()
    print("As rendered, measured on the pixels of the two globes themselves:")
    print()
    print("| army | %s mean RGB | %s mean RGB | luma apart | %s marked | %s marked |"
          % (left, right, left, right))
    print("|---|---|---|---:|---:|---:|")
    measured = []
    for army, path in frames.items():
        if not path.is_file():
            print("| %s | MISSING RENDER | -- | -- | -- | -- |" % army)
            continue
        image = Image.open(path)
        pixels, lmask = globe_pixels(image, True)
        _p, rmask = globe_pixels(image, False)
        lmean, rmean = pixels[lmask].mean(0), pixels[rmask].mean(0)
        lfrac, _lc = marking_fraction(pixels, lmask)
        rfrac, _rc = marking_fraction(pixels, rmask)
        measured.append((army, abs(luma(lmean) - luma(rmean)), lfrac, rfrac))
        print("| %s | %d,%d,%d | %d,%d,%d | %.1f | %.1f%% | %.1f%% |"
              % (army, lmean[0], lmean[1], lmean[2], rmean[0], rmean[1], rmean[2],
                 abs(luma(lmean) - luma(rmean)), 100.0 * lfrac, 100.0 * rfrac))
    print()
    if measured:
        print("The `marked` columns are the share of each ball that is not its")
        print("own globe colour, which is the surface cue reduced to one number.")
        print("%s's is %.1f to %.1f per cent of its visible face; %s's is %.1f"
              % (left, min(r[2] for r in measured) * 100.0,
                 max(r[2] for r in measured) * 100.0, right,
                 min(r[3] for r in measured) * 100.0))
        print("to %.1f per cent."
              % (max(r[3] for r in measured) * 100.0))
        if first == "uranus":
            print()
            print("**%s's own figure is the ring and nothing else.** There is no"
                  % left)
            print("marking on that globe, so every pale pixel inside its")
            print("silhouette belongs to the hoop standing over it or to the")
            print("specular highlight the renderer puts on a curved surface.")
    print()

    print("## The silhouette cue")
    print()
    print("| | %s | %s |" % (left, right))
    print("|---|---|---|")
    print("| silhouette | %s | %s |"
          % (("a sphere with " + RING_STANCE[first]) if first in RING_STANCE
             else "a bare sphere on a disc",
             ("a sphere with " + RING_STANCE[second]) if second in RING_STANCE
             else "a bare sphere on a disc"))
    print("| piece height mm | %.2f | %.2f |" % (heights[first], heights[second]))
    print("| widest, ring included | Ø%.2f | Ø%.2f |"
          % (P.RINGED_WORLDS[first]["outer_d"] if first in P.RINGED_WORLDS
             else P.globe_diameter(first),
             P.RINGED_WORLDS[second]["outer_d"] if second in P.RINGED_WORLDS
             else P.globe_diameter(second)))
    print("| ring filament | %s | %s |"
          % (("`%s`" % P.RINGED_WORLDS[first]["colour"]) if first in P.RINGED_WORLDS
             else "--",
             ("`%s`" % P.RINGED_WORLDS[second]["colour"]) if second in P.RINGED_WORLDS
             else "--"))
    print()
    if len(ringed) == 2:
        print("**Both worlds carry a ring and, since this revision, both rings")
        print("print in the same `%s`.** The colour of the ring is therefore no"
              % P.RINGED_WORLDS[first]["colour"])
        print("longer a cue at all, and the whole weight falls on orientation")
        print("and on size.")
        print()
        print("Orientation carries it. %s's ring is %s: its equatorial plane is"
              % (right if second == "saturn" else left,
                 RING_STANCE["saturn"]))
        print("%.2f degrees from horizontal, so the ring reads as a brim beside"
              % P.PLANETS["saturn"]["tilt"])
        print("the ball and widens the piece without raising it. %s's is %s:"
              % (left if first == "uranus" else right, RING_STANCE["uranus"]))
        print("its equatorial plane stands %.2f degrees PAST vertical, so the"
              % (P.PLANETS["uranus"]["tilt"] - 90.0))
        print("hoop reads as a band over the top of the ball -- over its EQUATOR,")
        print("since this world's poles point sideways -- and raises the piece")
        print("without widening it much. One is wider than it is tall and")
        print("the other is taller than it is wide: Ø%.2f against Ø%.2f across,"
              % (P.RINGED_WORLDS["saturn"]["outer_d"],
                 P.RINGED_WORLDS["uranus"]["outer_d"]))
        print("%.2f mm against %.2f mm tall. **The pair separates on silhouette"
              % (heights["saturn"], heights["uranus"]))
        print("and on size, and no longer on colour anywhere.** Whether that is")
        print("enough without the colour is a question for the blind review,")
        print("which is asked it in so many words; the answer is in")
        print("`snap/SIGNATURE-REVIEW.json`.")
    elif ringed:
        print("%s carries a ring and %s does not, which is a difference a reader"
              % (ringed[0].capitalize(),
                 (second if ringed[0] == first else first).capitalize()))
        print("sees before any colour arrives. **The pair separates on")
        print("silhouette.**")
    else:
        print("Neither piece has anything but a ball on a disc, so the only")
        print("silhouette difference is SIZE: %.2f mm of globe and %.2f mm of"
              % (step, abs(heights[second] - heights[first])))
        print("piece height, %.0f per cent. **The pair separates on silhouette,"
              % percent)
        print("by size alone.**")
    print()

    print("## The surface cue")
    print()
    print("| world | what it wears |")
    print("|---|---|")
    print("| %s | %s |" % (left, SURFACE[first]))
    print("| %s | %s |" % (right, SURFACE[second]))
    print()
    if "uranus" in (first, second):
        print("**This is the cue the revision spent.** Uranus used to carry two")
        print("pale polar hoods and now carries nothing, so on surface alone it")
        print("is a bare ball against a marked one. That is a separation rather")
        print("than a collision -- bare is as distinctive as marked, and no")
        print("other world in the set is bare -- but it is a separation that")
        print("only works while Uranus stays the only unmarked world.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
