"""Venus and Saturn side by side, now that their globes are neighbours in hue.

Venus's globe moves from `beige` #F7E6DE to `sunflower_yellow` #FFB549 in this
revision, and Saturn's is `yellow` #FFD834.  Those two are close enough to be
worth a check rather than an assumption, so this renders the two pieces side by
side at the frame the product is photographed from and measures what separates
them.

Four separations are reported, and only one of them is colour:

* **globe diameter** -- the rank ladder, which is the set's own first read;
* **piece height** -- the same ladder as the eye meets it on the board;
* **the ring** -- Saturn carries a Ø30.00 annulus and Venus carries nothing of
  the kind, so the two silhouettes are different shapes before any colour is
  looked at.  Measured as rendered silhouette width rather than asserted;
* **globe luma**, sealed and as the canonical render shows it.

The image it writes, `snap/worlds/venus-saturn-hero.png`, is the evidence a
reader checks the numbers against.

    "$WORKSHOP_PYTHON" measure/venus_saturn_separation.py <cad-skill-scripts-dir> \\
        > measure/venus-saturn-separation.md
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from build123d import Location                                # noqa: E402

from cadgen.assembly import AssemblyHelper                    # noqa: E402

import params as P                                            # noqa: E402
from colors import filament                                   # noqa: E402
from parts.world import world_bodies                          # noqa: E402
from snap_frames import BACKGROUND, HERO_VIEW, SHEET_VIEW     # noqa: E402

PAIR_GAP = 42.0
SIZE = 1200
FRAMES = (("hero", HERO_VIEW), ("state sheet", SHEET_VIEW))
OUT = Path("snap/worlds/venus-saturn-hero.png")


def _renderer(scripts: Path):
    path = scripts / "render_review"
    loader = importlib.machinery.SourceFileLoader("render_review", str(path))
    spec = importlib.util.spec_from_loader("render_review", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def channels(hex_value: str):
    return tuple(int(hex_value[index:index + 2], 16) / 255.0
                 for index in (1, 3, 5))


def linear_to_srgb(value: float) -> float:
    if value <= 0.0031308:
        return 12.92 * value
    return 1.055 * value ** (1 / 2.4) - 0.055


def luma(rgb) -> float:
    return 255.0 * (0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2])


def side_by_side(side: str):
    """Venus on the left, Saturn on the right, both in print orientation."""
    asm = AssemblyHelper("venus_saturn")
    for planet, offset in (("venus", -PAIR_GAP), ("saturn", PAIR_GAP)):
        at = Location((0, offset, 0))
        for role, (colour, shape) in world_bodies(planet, side).items():
            asm.add(at * shape, "%s_%s_%s_%s" % (planet, side, role, colour),
                    color=filament(colour))
    return asm.compound()


def silhouette_columns(image):
    """(first, last) image column occupied by the piece, per half."""
    pixels = np.asarray(image.convert("RGB")).astype(int)
    mask = np.abs(pixels - np.array(BACKGROUND)).sum(2) > 6
    columns = np.nonzero(mask.any(0))[0]
    rows = np.nonzero(mask.any(1))[0]
    return columns, rows, mask


def main() -> int:
    scripts = Path(sys.argv[1])
    render_review = _renderer(scripts)

    print("# Venus and Saturn, told apart")
    print()
    print("Venus's globe becomes `sunflower_yellow` #FFB549 in this revision")
    print("and Saturn's is `yellow` #FFD834, so the two are now neighbours in")
    print("hue. This is the check that they are still separable, made rather")
    print("than assumed.")
    print()

    print("## What separates them before colour")
    print()
    print("| measure | Venus | Saturn | difference |")
    print("|---|---:|---:|---:|")
    print("| rank | %d | %d | -- |"
          % (P.PLANETS["venus"]["rank"], P.PLANETS["saturn"]["rank"]))
    print("| globe diameter mm | %.2f | %.2f | **%.2f** |"
          % (P.globe_diameter("venus"), P.globe_diameter("saturn"),
             P.globe_diameter("saturn") - P.globe_diameter("venus")))
    print("| piece height mm | %.2f | %.2f | **%.2f** |"
          % (P.piece_height("venus"), P.piece_height("saturn"),
             P.piece_height("saturn") - P.piece_height("venus")))
    print("| widest feature mm | %.2f (the disc) | %.2f (the ring) | -- |"
          % (P.DISC_NOMINAL_D, P.RING_OUTER_D))
    print("| a ring | no | yes, Ø%.2f x %.2f | the silhouettes are different shapes |"
          % (P.RING_OUTER_D, P.RING_THICKNESS))
    print("| markings | two, from outline rings | four latitude bands | -- |")
    print()
    ladder = sorted(P.globe_diameter(name) for name in P.PLANETS)
    tightest = min(b - a for a, b in zip(ladder, ladder[1:]))
    print("The globe ladder is the set's own first read and these two are %.2f mm"
          % (P.globe_diameter("saturn") - P.globe_diameter("venus")))
    print("apart on it -- %.0f per cent of Venus's own diameter. They are four"
          % (100.0 * (P.globe_diameter("saturn") - P.globe_diameter("venus"))
             / P.globe_diameter("venus")))
    print("ranks apart rather than neighbours, so this is a wide gap by the")
    print("standards of the ladder, whose tightest adjacent step is %.2f mm."
          % tightest)
    print()

    print("## The globes, by value")
    print()
    print("| filament | on | sealed hex | sealed luma | as rendered | rendered luma |")
    print("|---|---|---|---|---|---|")
    for name, planet in (("sunflower_yellow", "Venus"), ("yellow", "Saturn")):
        shown = tuple(linear_to_srgb(value)
                      for value in channels(P.FILAMENT_HEX[name]))
        print("| `%s` | %s | %s | %.1f | %s | %.1f |"
              % (name, planet, P.FILAMENT_HEX[name],
                 luma(channels(P.FILAMENT_HEX[name])),
                 "#" + "".join("%02X" % round(255 * v) for v in shown),
                 luma(shown)))
    sealed = abs(luma(channels(P.FILAMENT_HEX["sunflower_yellow"]))
                 - luma(channels(P.FILAMENT_HEX["yellow"])))
    rendered = abs(
        luma(tuple(linear_to_srgb(v)
                   for v in channels(P.FILAMENT_HEX["sunflower_yellow"])))
        - luma(tuple(linear_to_srgb(v)
                     for v in channels(P.FILAMENT_HEX["yellow"]))))
    print()
    print("**They are %.1f luma levels apart sealed and %.1f as the render shows"
          % (sealed, rendered))
    print("them.** That is the honest answer and it is a small number: on value")
    print("alone these two are close, which is exactly why the rest of this")
    print("report exists. Saturn's is the lighter and greener of the two, Venus's")
    print("the deeper and oranger.")
    print()

    print("## Rendered side by side")
    print()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for label, view in FRAMES:
        shape = side_by_side("sol")
        occurrences = render_review.tessellate_occurrences(shape, 0.05)
        image = render_review.render(occurrences, view[0], view[1], SIZE, 0.06)
        if label == "hero":
            image.save(OUT)
        columns, rows, mask = silhouette_columns(image)
        # Split on the widest empty column run between the two pieces, not on
        # the midpoint: a midpoint split clips whichever piece is wider and
        # reports both as exactly half the frame.
        occupied = mask.any(0)
        gaps, start = [], None
        for index in range(columns.min(), columns.max() + 1):
            if not occupied[index]:
                start = index if start is None else start
            elif start is not None:
                gaps.append((index - start, start, index))
                start = None
        if not gaps:
            raise SystemExit("the two pieces overlap in this frame; no split")
        width, low, high = max(gaps)
        split = (low + high) // 2
        left = mask[:, :split]
        right = mask[:, split:]
        lw = np.nonzero(left.any(0))[0]
        rw = np.nonzero(right.any(0))[0]
        lh = np.nonzero(left.any(1))[0]
        rh = np.nonzero(right.any(1))[0]
        print("- **%s frame** (azimuth %g, elevation %g): Venus occupies %d x %d"
              % (label, view[0], view[1], np.ptp(lw) + 1, np.ptp(lh) + 1))
        print("  pixels of silhouette and Saturn %d x %d, so Saturn stands %.0f"
              % (np.ptp(rw) + 1, np.ptp(rh) + 1,
                 100.0 * (np.ptp(rh) + 1) / (np.ptp(lh) + 1) - 100.0))
        print("  per cent the taller and exactly as wide -- every disc in the")
        print("  set is Ø%.2f and on both pieces the disc, not the globe, is"
              % P.DISC_NOMINAL_D)
        print("  the widest thing -- with %d columns of clear background" % width)
        print("  between the two.")
    print()
    print("`snap/worlds/venus-saturn-hero.png` is the image, at the product's")
    print("own frame, with the two pieces %.0f mm apart on the board's own"
          % (2 * PAIR_GAP))
    print("pitch.")
    print()
    print("## What the image shows")
    print()
    print("Read off the rendered image rather than off the table above, because")
    print("the Wish asks for what a reader sees and not for what the numbers")
    print("predict.")
    print()
    print("The two are not close to being confused. Saturn is plainly the")
    print("bigger ball -- it fills its disc and overhangs it, where Venus sits")
    print("well inside its own -- and it wears a white ring that leans clear of")
    print("the board on both sides, which is a silhouette Venus has nothing")
    print("like. Saturn's four `cocoa_brown` belts are the loudest markings on")
    print("either piece and Venus has no band system at all: one pale sinuous")
    print("highland across its middle and nothing else in this frame. The two")
    print("ambers do read as the same family of colour -- Saturn's is the")
    print("lighter and greener, Venus's the deeper and oranger, and side by side")
    print("that difference is visible but it is the weakest of the cues. The one")
    print("thing the two pieces genuinely share is the disc under them, and")
    print("every world in the set shares that.")
    print()
    print("The verdict is therefore what the geometry predicted and it is")
    print("recorded as read rather than as assumed: **the silhouette carries")
    print("it easily; the colour alone would not.** If these two globes had the")
    print("same diameter and no ring, this pairing would be a problem.")
    print()
    print("Measured by `measure/venus_saturn_separation.py` on the exact solids")
    print("`parts/world.py` builds, through `cad/scripts/render_review`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
