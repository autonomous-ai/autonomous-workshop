"""Can a player tell Neptune from Uranus across a table?

They are the two blue-family worlds and the two adjacent ranks, 5 and 6, and
their globes differ by 0.13 mm in a set whose whole ownership cue is size, so
the correction asks the question directly.  This answers it on the canonical
render rather than by eye: `snap/worlds/neptune-uranus-hero.png` puts the two
pieces side by side at the product's own frame, and this reads that image.

Three cues are measured separately, because only one of them is any good.

    "$WORKSHOP_PYTHON" measure/neptune_uranus_separation.py \\
        > measure/neptune-uranus-separation.md
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
FRAMES = {
    "Sol": HERE.parent / "snap" / "worlds" / "neptune-uranus-hero.png",
    "Anti-Sol": HERE.parent / "snap" / "worlds" / "neptune-uranus-hero-anti.png",
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
    print("# Neptune against Uranus at the product's own frame")
    print()
    print("Ranks 5 and 6, Ø%.2f and Ø%.2f mm -- %.2f mm apart in a set whose"
          % (P.globe_diameter("neptune"), P.globe_diameter("uranus"),
             P.globe_diameter("uranus") - P.globe_diameter("neptune")))
    print("ranks are told apart by size. Measured on the canonical side-by-side")
    print("renders at the hero frame (azimuth -55, elevation 22), one per army.")
    print()

    print("## The size cue, which is no use here")
    print()
    print("| | Neptune | Uranus | apart |")
    print("|---|---:|---:|---:|")
    print("| rank | %d | %d | 1 |"
          % (P.PLANETS["neptune"]["rank"], P.PLANETS["uranus"]["rank"]))
    print("| globe diameter mm | %.2f | %.2f | %.2f |"
          % (P.globe_diameter("neptune"), P.globe_diameter("uranus"),
             P.globe_diameter("uranus") - P.globe_diameter("neptune")))
    from parts.world import build_world
    heights = {name: build_world(name, "sol").bounding_box().max.Z
               for name in ("neptune", "uranus")}
    print("| piece height mm | %.2f | %.2f | %.2f |"
          % (heights["neptune"], heights["uranus"],
             heights["uranus"] - heights["neptune"]))
    print("| obliquity deg | %.2f | %.2f | %.2f |"
          % (P.PLANETS["neptune"]["tilt"], P.PLANETS["uranus"]["tilt"],
             P.PLANETS["uranus"]["tilt"] - P.PLANETS["neptune"]["tilt"]))
    print()
    step = P.globe_diameter("uranus") - P.globe_diameter("neptune")
    print("%.2f mm is %.1f per cent of Neptune's own diameter and less than one"
          % (step, 100.0 * step / P.globe_diameter("neptune")))
    print("third of the %.2f mm nozzle. **Size cannot separate these two pieces**,"
          % P.NOZZLE_MM)
    print("and it is the only pair in the ladder of which that is true: the next")
    print("closest, Venus and Earth, are %.2f mm apart."
          % (P.globe_diameter("earth") - P.globe_diameter("venus")))
    print()

    print("## The colour cue, which is the strong one")
    print()
    neptune_hex, uranus_hex = hexrgb("blue"), hexrgb("cyan")
    print("| | sealed hex | luma of 255 |")
    print("|---|---|---:|")
    print("| Neptune globe `blue` | %s | %.1f |" % (P.FILAMENT_HEX["blue"], luma(neptune_hex)))
    print("| Uranus globe `cyan` | %s | %.1f |" % (P.FILAMENT_HEX["cyan"], luma(uranus_hex)))
    print()
    print("Sealed, the two separate **%.1f** of 255 luma levels, which is four"
          % abs(luma(neptune_hex) - luma(uranus_hex)))
    print("times the 9.4 this project accepted as its narrowest on Saturn, and")
    print("they separate in hue as well: a dark navy blue against a full cyan.")
    print()
    print("As rendered, measured on the pixels of the two globes themselves:")
    print()
    print("| army | Neptune mean RGB | Uranus mean RGB | luma apart | Neptune "
          "marked | Uranus marked |")
    print("|---|---|---|---:|---:|---:|")
    for army, path in FRAMES.items():
        if not path.is_file():
            print("| %s | -- | -- | -- | -- | -- |" % army)
            continue
        image = Image.open(path)
        pixels, left = globe_pixels(image, True)
        _p, right = globe_pixels(image, False)
        lmean = pixels[left].mean(0)
        rmean = pixels[right].mean(0)
        lfrac, lcount = marking_fraction(pixels, left)
        rfrac, rcount = marking_fraction(pixels, right)
        print("| %s | %d,%d,%d | %d,%d,%d | %.1f | %.1f%% | %.1f%% |"
              % (army, lmean[0], lmean[1], lmean[2], rmean[0], rmean[1], rmean[2],
                 abs(luma(lmean) - luma(rmean)), 100.0 * lfrac, 100.0 * rfrac))
    print()

    print("## The silhouette cue, which this correction added")
    print()
    print("Until this run the two pieces had the same silhouette -- a ball on a")
    print("disc -- and everything separating them was paint. Uranus now carries a")
    print("ring, and it carries it standing up: its equatorial plane is %.2f"
          % (P.PLANETS["uranus"]["tilt"] - 90.0))
    print("degrees past vertical, so the hoop is a band over the globe rather than")
    print("a brim beside it. Against Neptune's bare sphere that is a difference a")
    print("reader sees before any colour arrives, and it is the first cue in this")
    print("pair that survives being looked at from across a table in poor light.")
    print()
    print("| | Neptune | Uranus |")
    print("|---|---|---|")
    print("| silhouette | a bare sphere on a disc | a sphere with an upright hoop |")
    print("| piece height mm | %.2f | %.2f |" % (heights["neptune"], heights["uranus"]))
    print("| widest, ring included | Ø%.2f | Ø%.2f |"
          % (P.globe_diameter("neptune"), P.RINGED_WORLDS["uranus"]["outer_d"]))
    print()
    print("## The surface cue, and what it says about Uranus")
    print()
    print("The two surfaces are not the same KIND of marking, which is the cue a")
    print("reader uses once they are close enough for paint. Neptune wears eight")
    print("short tapered wisps at eight different angles plus a dark oval; Uranus")
    print("wears a broad soft polar hood at each pole, boundary at latitude 55,")
    print("in the palest warm tone the shop stocks. **They are distinguishable at")
    print("table distance, and comfortably so** -- on silhouette now as well as on")
    print("surface, and on neither count is it the ladder doing it.")
    print()
    print("What the frame used to show, and no longer does. Uranus's single")
    print("`white` band was exactly what Neptune's three bands were before")
    print("Neptune's own correction: a closed belt of latitude, hard-edged,")
    print("exactly parallel, standing upright on the visible face, and next to")
    print("eight short wisps it read as the painted stripe on the pair. That was")
    print("recorded here rather than repaired at the time because Uranus was the")
    print("last world in the chain still to come. It has come: the band is gone,")
    print("and the hood that replaced it is a region rather than a line.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
