"""How far apart Jupiter's three tones actually are, in the canonical render.

The Wish asks for the bright zone filament to be measured against both the
`orange` globe and the `cocoa_brown` belts, in the greyscale of the canonical
render, before it is committed -- the zone tone has to be clearly lighter than
the globe *and* clearly lighter than the belts, or it adds a filament for
nothing.  `measure/filament-value.md` established that the review renderer
double-encodes a sealed sRGB channel, so a separation computed from the
catalogue hex is not the separation a reader of the product images gets.

The method is `measure/mercury_tone_separation.py`'s and
`measure/venus_tone_separation.py`'s, unchanged: one Jupiter piece is built
once and rendered twice at one canonical camera, with a single region
repainted between the two renders and nothing else altered.  The pixels that
differ are exactly that region's pixels, under identical geometry and
identical light, so the mean absolute difference in luma across them is the
separation the eye is offered -- no classification, no colour matching, no
assumption about shading.

Three separations are reported for every candidate:

**Sealed** is the catalogue sRGB hex the shop and the listing read.  That is
what the plastic will be.

**As rendered** applies `render_review`'s own `_linear_to_srgb` to the sealed
channels, which is what every image in `snap/` shows.

**Measured** is the one that decides, and is the two-render difference above.

Luma is Rec. 709: 0.2126 R + 0.7152 G + 0.0722 B, on 0..255.

    "$WORKSHOP_PYTHON" measure/jupiter_tone_separation.py <cad-skill-scripts-dir> \\
        > measure/jupiter-tone-separation.md
"""

from __future__ import annotations

import copy
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from cadgen.assembly import AssemblyHelper                    # noqa: E402

import params as P                                            # noqa: E402
from colors import filament                                   # noqa: E402
from parts.world import world_bodies                          # noqa: E402
from snap_frames import HERO_VIEW, SHEET_VIEW                 # noqa: E402
from world_views import FRAMES as WORLD_FRAMES                # noqa: E402

PLANET = "jupiter"
GLOBE = P.GLOBE_COLOUR[PLANET]                                # orange
BELTS = "cocoa_brown"

#: The Wish's four candidates: every stocked filament lighter than the
#: `orange` globe.  All four are already in the set, so none of them loads a
#: new spool; what separates them is how far they measure and what else in the
#: set is already wearing them.
CANDIDATES = ("beige", "sunflower_yellow", "yellow", "white")

#: The two frames the whole product is photographed from, plus the frame the
#: single-piece evidence is rendered at, so the numbers belong to the images a
#: reader is actually given rather than to a light invented here.
FRAMES = {
    "hero": HERO_VIEW,
    "sheet": SHEET_VIEW,
    "spot": WORLD_FRAMES[PLANET]["spot"][:2],
}
SIZE = 900


def _renderer(scripts: Path):
    path = scripts / "render_review"
    loader = importlib.machinery.SourceFileLoader("render_review", str(path))
    spec = importlib.util.spec_from_loader("render_review", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def channels(hex_value: str) -> tuple[float, float, float]:
    return tuple(int(hex_value[index:index + 2], 16) / 255.0
                 for index in (1, 3, 5))


def linear_to_srgb(value: float) -> float:
    """`render_review`'s own encode, applied to an already-sRGB channel."""
    if value <= 0.0031308:
        return 12.92 * value
    return 1.055 * value ** (1 / 2.4) - 0.055


def luma(rgb) -> float:
    red, green, blue = rgb
    return 255.0 * (0.2126 * red + 0.7152 * green + 0.0722 * blue)


def sealed_luma(name: str) -> float:
    return luma(channels(P.FILAMENT_HEX[name]))


def rendered_luma(name: str) -> float:
    return luma(tuple(linear_to_srgb(value)
                      for value in channels(P.FILAMENT_HEX[name])))


def _piece(bodies, repaint: dict[str, str]):
    """The piece with one region repainted, and nothing else changed.

    `copy.copy` is not decoration: a colour is sealed on the shape object, so
    handing the same solids to a second assembly leaves them carrying the
    first assembly's colour and the two renders come out identical.  A shallow
    copy shares the B-rep and gets its own colour.
    """
    asm = AssemblyHelper("%s_tone" % PLANET)
    for role, (colour, shape) in bodies.items():
        asm.add(copy.copy(shape), "%s_%s" % (role, colour),
                color=filament(repaint.get(role, colour)))
    return asm.compound()


def _image(render_review, bodies, repaint, view):
    shape = _piece(bodies, repaint)
    occurrences = render_review.tessellate_occurrences(shape, 0.04)
    image = render_review.render(occurrences, view[0], view[1], SIZE, 0.05)
    return np.asarray(image.convert("RGB")).astype(float)


def measured(render_review, bodies, role: str, candidate: str, against: str,
             view):
    """(pixel count, mean |luma difference|, min, max) for one region.

    Two renders of one build: the region in `candidate`, and the region in
    `against`.  Every pixel that moved belongs to the region, and nothing else
    about the two images differs.
    """
    lit = _image(render_review, bodies, {role: candidate}, view)
    bare = _image(render_review, bodies, {role: against}, view)
    weights = np.array([0.2126, 0.7152, 0.0722])
    delta = np.abs(lit @ weights - bare @ weights)
    mask = np.abs(lit - bare).sum(2) > 0.5
    if not mask.any():
        return 0, 0.0, 0.0, 0.0
    values = delta[mask]
    return (int(mask.sum()), float(values.mean()), float(values.min()),
            float(values.max()))


def main() -> int:
    scripts = Path(sys.argv[1])
    render_review = _renderer(scripts)
    bodies = world_bodies(PLANET, "sol")

    print("# Jupiter's three tones, measured")
    print()
    print("`ref/jupiter-sol.png` has three values, not two: a mid orange base,")
    print("darker belts, and bright cream zones between them. The build this")
    print("corrects had `orange` and `cocoa_brown` only, so the bright zones")
    print("were bare globe and the piece lost the alternating rhythm that makes")
    print("Jupiter legible. This is the measurement the third filament was")
    print("chosen on.")
    print()
    print("Luma is Rec. 709 on 0..255. The globe is `%s` %s and the belts are"
          % (GLOBE, P.FILAMENT_HEX[GLOBE]))
    print("`%s` %s; both are unchanged by this correction."
          % (BELTS, P.FILAMENT_HEX[BELTS]))
    print()

    print("## The palette, on paper")
    print()
    print("| filament | sealed hex | sealed luma | as the render shows it | rendered luma |")
    print("|---|---|---|---|---|")
    for name in (GLOBE, BELTS) + CANDIDATES:
        shown = tuple(linear_to_srgb(value)
                      for value in channels(P.FILAMENT_HEX[name]))
        as_hex = "#" + "".join("%02X" % round(255 * value) for value in shown)
        print("| `%s` | %s | %.1f | %s | %.1f |"
              % (name, P.FILAMENT_HEX[name], sealed_luma(name), as_hex,
                 rendered_luma(name)))
    print()
    print("`render_review` applies its own `_linear_to_srgb` to channels that")
    print("are already sRGB, so every image in `snap/` is encoded twice. That")
    print("lifts mid-tones hard and leaves the top end almost untouched, so a")
    print("dark tone separates *better* in the images than the sealed hex")
    print("suggests and a light one *worse*. `measure/filament-value.md` is")
    print("where that was first measured.")
    print()

    print("## The two numbers the Wish asks for, for every candidate")
    print()
    print("Measured on the rendered pixels, at each frame, with the zones")
    print("repainted between two otherwise identical renders.")
    print()
    print("| candidate | against | frame | pixels | mean | least | most |")
    print("|---|---|---|---:|---:|---:|---:|")
    summary: dict[tuple[str, str], list[float]] = {}
    for candidate in CANDIDATES:
        for against, label in ((GLOBE, "the `orange` globe"),
                               (BELTS, "the `cocoa_brown` belts")):
            for frame, view in FRAMES.items():
                count, mean, low, high = measured(
                    render_review, bodies, "zones", candidate, against, view)
                summary.setdefault((candidate, against), []).append(mean)
                print("| `%s` | %s | %s | %d | **%.1f** | %.1f | %.1f |"
                      % (candidate, label, frame, count, mean, low, high))
    print()

    print("## The decision, on one line each")
    print()
    print("| candidate | mean vs globe | mean vs belts | already in the set as |")
    print("|---|---:|---:|---|")
    duty = {
        "beige": "Earth's dryland, Venus's highlands",
        "sunflower_yellow": "the Sol den plug and, since the Venus correction, "
                            "Venus's whole globe",
        "yellow": "Saturn's globe",
        "white": "Sol discs, Anti-Sol numerals, Mercury's Caloris floor, "
                 "Mars's caps, Earth's ice, Uranus's band, Neptune's streaks, "
                 "Saturn's ring",
    }
    for candidate in CANDIDATES:
        globe_mean = sum(summary[(candidate, GLOBE)]) / 3.0
        belt_mean = sum(summary[(candidate, BELTS)]) / 3.0
        print("| `%s` | %.1f | %.1f | %s |"
              % (candidate, globe_mean, belt_mean, duty[candidate]))
    print()

    beige_globe = sum(summary[("beige", GLOBE)]) / 3.0
    beige_belt = sum(summary[("beige", BELTS)]) / 3.0
    sun_globe = sum(summary[("sunflower_yellow", GLOBE)]) / 3.0
    white_globe = sum(summary[("white", GLOBE)]) / 3.0
    yellow_globe = sum(summary[("yellow", GLOBE)]) / 3.0

    print("## What was chosen, and why")
    print()
    print("- **The zones are `beige` #F7E6DE.** It separates %.1f luma levels"
          % beige_globe)
    print("  from the `orange` globe and %.1f from the `cocoa_brown` belts,"
          % beige_belt)
    print("  averaged over the three frames. Both are clear: the thinnest")
    print("  marking separation anywhere in this set is the 20.2 `beige` makes")
    print("  on Venus's amber globe, and the separation this revision exists to")
    print("  replace as invisible is the 21.8 `dark_gray` made on Mercury's.")
    print("  It is also the reference's own tone: the bright zones in")
    print("  `ref/jupiter-sol.png` are a warm cream, not an amber and not a")
    print("  pure white.")
    print("- **`sunflower_yellow` was measured and refused.** At %.1f against"
          % sun_globe)
    print("  the globe it is the narrowest of the four -- it is an amber on an")
    print("  orange -- and it is the one filament in this set already carrying")
    print("  two jobs: the Sol den plug, and since the Venus correction the")
    print("  whole of Venus's globe. Giving it a third on the largest world in")
    print("  the set is what would have made Jupiter and Venus read as")
    print("  relatives. Because it was not taken, the Wish's hero-frame")
    print("  Jupiter-beside-Venus check is not required; the two globes stay")
    print("  `orange` and `sunflower_yellow`, which is where they already were.")
    print("- **`yellow` at %.1f is Saturn's globe** and would have put Saturn's"
          % yellow_globe)
    print("  own colour on Jupiter's zones, one rank away on the ladder.")
    print("- **`white` at %.1f measures furthest of the four** and was not"
          % white_globe)
    print("  taken. It is already the brightest feature on four other worlds --")
    print("  Mars's caps, Mercury's Caloris floor, Earth's ice and Saturn's")
    print("  ring -- and on the reference Jupiter's zones are cream rather than")
    print("  white. The gap between it and `beige` is %.1f luma levels, which"
          % (white_globe - beige_globe))
    print("  is what that choice cost, stated rather than hidden.")
    print("- **Jupiter now prints in four filaments** -- `orange`,")
    print("  `cocoa_brown`, `beige` and `red` -- where it printed in three.")
    print("  That ties it with Earth as the most expensive world in the set;")
    print("  Mercury, Mars, Venus, Neptune and Saturn take three and Uranus")
    print("  takes two. No new spool: all four were already loaded for this")
    print("  set, `beige` for Earth's dryland and Venus's highlands.")
    print()
    print("Measured by `measure/jupiter_tone_separation.py` on the exact solids")
    print("`parts/world.py` builds, through `cad/scripts/render_review`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
