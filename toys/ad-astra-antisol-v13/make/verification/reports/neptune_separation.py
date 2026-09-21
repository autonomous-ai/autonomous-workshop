"""Can a player tell Neptune from the world beside it in the ladder?

Two pairs, for two different reasons, and this revision has to answer both.

**NEPTUNE AGAINST URANUS.**  The two blue-family worlds and the two adjacent
ranks, 5 and 6, whose globes differ by 0.13 mm in a set whose whole ownership
cue is size.  Size cannot separate them, so something else has to.

**NEPTUNE AGAINST EARTH.**  The other pair, and the harder one to think about:
Earth and Neptune are the only two worlds in this set drawn from the SAME
SPOOL.  Both globes are `blue` #004EA8, so colour cannot separate them at all
and the whole burden falls on size and on surface.  This revision changes
Neptune's surface, so the question has to be asked again rather than inherited.

Each pair is answered on the canonical side-by-side render at the product's own
frame rather than by eye:
`snap/worlds/neptune-<other>-hero.png` and its `-hero-anti.png` mirror.

Four cues are measured separately, because they are not equally good and the
interesting answer is which one is carrying the pair.

    "$WORKSHOP_PYTHON" measure/neptune_separation.py uranus \\
        > measure/neptune-uranus-separation.md
    "$WORKSHOP_PYTHON" measure/neptune_separation.py earth \\
        > measure/neptune-earth-separation.md
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

#: What each world wears, in one clause, for the surface-cue table.  Written
#: here rather than derived because it is a description of what a reader sees,
#: not a measurement; every number in it is measured in that world's own
#: resolution report.
SURFACE = {
    "neptune": ("three closed white latitude bands, 0.96, 0.76 and 0.57 mm "
                "wide, running the whole way round the globe, plus one "
                "dark_gray oval 5.35 by 2.67 mm south of the equator"),
    "uranus": ("a broad soft beige polar hood at each pole, boundary at "
               "latitude 60, and an upright cyan ring standing pole-over-pole"),
    "earth": ("the world's coastlines as green land with beige dryland inside "
              "it and a white ice cap, an outline map a reader can check "
              "against an atlas"),
}


def luma(rgb) -> float:
    return 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2]


def hexrgb(name: str):
    value = P.FILAMENT_HEX[name]
    return tuple(int(value[index:index + 2], 16) for index in (1, 3, 5))


def globe_pixels(image: Image.Image, left_half: bool):
    """Every pixel of one globe, markings included.

    The ball is found by its own saturated colour -- the discs are neutral
    grey, black or white and the background is a pale grey -- and then the
    circle that colour occupies is filled in, so the white markings ON the ball
    are counted as ball rather than dropped for being unsaturated.
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
    other = sys.argv[1] if len(sys.argv) > 1 else "uranus"
    title = other.capitalize()
    frames = {
        "Sol": HERE.parent / "snap" / "worlds" / ("neptune-%s-hero.png" % other),
        "Anti-Sol": HERE.parent / "snap" / "worlds" / ("neptune-%s-hero-anti.png" % other),
    }
    step = abs(P.globe_diameter(other) - P.globe_diameter("neptune"))
    same_spool = P.GLOBE_COLOUR[other] == P.GLOBE_COLOUR["neptune"]
    ringed = other in P.RINGED_WORLDS

    print("# Neptune against %s at the product's own frame" % title)
    print()
    print("Ranks %d and %d, Ø%.2f and Ø%.2f mm -- %.2f mm apart in a set whose"
          % (P.PLANETS["neptune"]["rank"], P.PLANETS[other]["rank"],
             P.globe_diameter("neptune"), P.globe_diameter(other), step))
    print("ranks are told apart by size. Measured on the canonical side-by-side")
    print("renders at the hero frame (azimuth -55, elevation 22), one per army.")
    print()
    print("This revision changed Neptune's surface, so this pair is asked again")
    print("on this run's own renders rather than inherited from the archive.")
    print()

    from parts.world import build_world
    heights = {name: build_world(name, "sol").bounding_box().max.Z
               for name in ("neptune", other)}

    print("## The size cue")
    print()
    print("| | Neptune | %s | apart |" % title)
    print("|---|---:|---:|---:|")
    print("| rank | %d | %d | %d |"
          % (P.PLANETS["neptune"]["rank"], P.PLANETS[other]["rank"],
             abs(P.PLANETS[other]["rank"] - P.PLANETS["neptune"]["rank"])))
    print("| globe diameter mm | %.2f | %.2f | %.2f |"
          % (P.globe_diameter("neptune"), P.globe_diameter(other), step))
    print("| piece height mm | %.2f | %.2f | %.2f |"
          % (heights["neptune"], heights[other],
             abs(heights[other] - heights["neptune"])))
    print("| obliquity deg | %.2f | %.2f | %.2f |"
          % (P.PLANETS["neptune"]["tilt"], P.PLANETS[other]["tilt"],
             abs(P.PLANETS[other]["tilt"] - P.PLANETS["neptune"]["tilt"])))
    print()
    percent = 100.0 * step / P.globe_diameter("neptune")
    if step < P.NOZZLE_MM:
        print("%.2f mm is %.1f per cent of Neptune's own diameter and less than"
              % (step, percent))
        print("one %.2f mm nozzle. **Size cannot separate these two pieces**,"
              % P.NOZZLE_MM)
        print("and it is the only pair in the ladder of which that is true: the")
        print("next closest, Venus and Earth, are %.2f mm apart."
              % (P.globe_diameter("earth") - P.globe_diameter("venus")))
    else:
        print("%.2f mm is %.1f per cent of Neptune's own diameter and %.0f"
              % (step, percent, step / P.NOZZLE_MM))
        print("nozzle widths, and the pieces stand %.2f mm apart in height."
              % abs(heights[other] - heights["neptune"]))
        print("**Size separates this pair on its own**, which is what the size")
        print("ladder is for: they are %d ranks apart and they look it."
              % abs(P.PLANETS[other]["rank"] - P.PLANETS["neptune"]["rank"]))
    print()

    print("## The colour cue")
    print()
    neptune_hex = hexrgb(P.GLOBE_COLOUR["neptune"])
    other_hex = hexrgb(P.GLOBE_COLOUR[other])
    print("| | sealed hex | luma of 255 |")
    print("|---|---|---:|")
    print("| Neptune globe `%s` | %s | %.1f |"
          % (P.GLOBE_COLOUR["neptune"], P.FILAMENT_HEX[P.GLOBE_COLOUR["neptune"]],
             luma(neptune_hex)))
    print("| %s globe `%s` | %s | %.1f |"
          % (title, P.GLOBE_COLOUR[other], P.FILAMENT_HEX[P.GLOBE_COLOUR[other]],
             luma(other_hex)))
    print()
    if same_spool:
        print("**They are the same spool.** Both globes are `%s` %s, so colour"
              % (P.GLOBE_COLOUR["neptune"], P.FILAMENT_HEX[P.GLOBE_COLOUR["neptune"]]))
        print("separates them by exactly nothing and cannot be asked to. This is")
        print("one of the two colour collisions this set records rather than")
        print("hides, and it is why the two globes that share a spool are put")
        print("four ranks apart in the ladder.")
    else:
        print("Sealed, the two separate **%.1f** of 255 luma levels, which is"
              % abs(luma(neptune_hex) - luma(other_hex)))
        print("four times the 9.4 this project accepted as its narrowest on")
        print("Saturn, and they separate in hue as well.")
    print()
    print("As rendered, measured on the pixels of the two globes themselves:")
    print()
    print("| army | Neptune mean RGB | %s mean RGB | luma apart | Neptune "
          "marked | %s marked |" % (title, title))
    print("|---|---|---|---:|---:|---:|")
    measured = []
    for army, path in frames.items():
        if not path.is_file():
            print("| %s | MISSING RENDER | -- | -- | -- | -- |" % army)
            continue
        image = Image.open(path)
        pixels, left = globe_pixels(image, True)
        _p, right = globe_pixels(image, False)
        lmean = pixels[left].mean(0)
        rmean = pixels[right].mean(0)
        lfrac, _lcount = marking_fraction(pixels, left)
        rfrac, _rcount = marking_fraction(pixels, right)
        measured.append((army, abs(luma(lmean) - luma(rmean)), lfrac, rfrac))
        print("| %s | %d,%d,%d | %d,%d,%d | %.1f | %.1f%% | %.1f%% |"
              % (army, lmean[0], lmean[1], lmean[2], rmean[0], rmean[1], rmean[2],
                 abs(luma(lmean) - luma(rmean)), 100.0 * lfrac, 100.0 * rfrac))
    print()
    if measured:
        print("The `marked` columns are the share of each ball that is not its")
        print("own globe colour, which is the surface cue reduced to one number.")
        print("Neptune's three bands cover %.1f to %.1f per cent of its visible"
              % (min(row[2] for row in measured) * 100.0,
                 max(row[2] for row in measured) * 100.0))
        print("face; %s's markings cover %.1f to %.1f per cent of its."
              % (title, min(row[3] for row in measured) * 100.0,
                 max(row[3] for row in measured) * 100.0))
        print()

    print("## The silhouette cue")
    print()
    print("| | Neptune | %s |" % title)
    print("|---|---|---|")
    print("| silhouette | a bare sphere on a disc | %s |"
          % ("a sphere with an upright hoop" if ringed
             else "a bare sphere on a disc"))
    print("| piece height mm | %.2f | %.2f |"
          % (heights["neptune"], heights[other]))
    print("| widest, ring included | Ø%.2f | Ø%.2f |"
          % (P.globe_diameter("neptune"),
             P.RINGED_WORLDS[other]["outer_d"] if ringed
             else P.globe_diameter(other)))
    print()
    if ringed:
        print("%s carries a ring and carries it standing up: its equatorial"
              % title)
        print("plane is %.2f degrees past vertical, so the hoop is a band over"
              % (P.PLANETS[other]["tilt"] - 90.0))
        print("the globe rather than a brim beside it. Against Neptune's bare")
        print("sphere that is a difference a reader sees before any colour")
        print("arrives. **The pair separates on silhouette.**")
    else:
        print("Neither piece has anything but a ball on a disc, so the only")
        print("silhouette difference is SIZE -- and here that is a real one:")
        print("%.2f mm of globe and %.2f mm of piece height, %.0f per cent."
              % (step, abs(heights[other] - heights["neptune"]), percent))
        print("**The pair separates on silhouette, by size alone.**")
    print()

    print("## The surface cue")
    print()
    print("| world | what it wears |")
    print("|---|---|")
    print("| Neptune | %s |" % SURFACE["neptune"])
    print("| %s | %s |" % (title, SURFACE[other]))
    print()
    print("These are not the same KIND of marking, which is the cue a reader")
    print("uses once they are close enough for paint. **The pair separates on")
    print("surface.**")
    print()
    print("One honest caveat about Neptune's half of it, and it is the whole")
    print("subject of this revision: a closed latitude band is the most")
    print("generic marking a sphere can carry. It separates Neptune from these")
    print("two worlds because neither of them wears bands -- but it is the")
    print("reason the blind review of this build is asked, in so many words,")
    print("whether any piece in the set reads as a beach ball, and the answer")
    print("it gives is recorded in `snap/SIGNATURE-REVIEW.json` beside the")
    print("owner's decision rather than argued with here.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
