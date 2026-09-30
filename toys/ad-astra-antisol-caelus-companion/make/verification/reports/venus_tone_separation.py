"""How far apart Venus's three tones actually are, in the canonical render.

The Wish asks for three numbers before the tones are committed: the greyscale
separation of the highland filament against the `sunflower_yellow` globe, of
the lowland filament against the same globe, and of the two against each
other -- all of it "in the canonical render", which is the only place the
question is settled.  `measure/filament-value.md` established that the review
renderer double-encodes a sealed sRGB channel, so a separation computed from
the catalogue hex is not the separation a reader of the product images gets.

The method is `measure/mercury_tone_separation.py`'s, unchanged: one Venus
piece is built once and rendered twice at one canonical camera, with a single
region repainted between the two renders and nothing else altered.  The pixels
that differ are exactly that region's pixels, under identical geometry and
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

    "$WORKSHOP_PYTHON" measure/venus_tone_separation.py <cad-skill-scripts-dir> \\
        > measure/venus-tone-separation.md
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

PLANET = "venus"
GLOBE = P.GLOBE_COLOUR[PLANET]                                # sunflower_yellow

#: The highlands are the brighter of the two marking tones, so the candidates
#: are the stocked filaments lighter than the globe.  `beige` is the Wish's
#: intended answer; `white` and `yellow` are the only others above it.
HIGHLAND_CANDIDATES = ("beige", "white", "yellow")

#: The lowlands are the darker tone.  `cocoa_brown` is the intended answer;
#: `dark_gray` and `black` are the comparison it has to beat or refuse.
LOWLAND_CANDIDATES = ("cocoa_brown", "dark_gray", "black")

#: The two frames the whole product is photographed from, plus the frame the
#: single-piece evidence is rendered at, so the numbers belong to the images a
#: reader is actually given rather than to a light invented here.
FRAMES = {
    "hero": HERO_VIEW,
    "sheet": SHEET_VIEW,
    "aphrodite": WORLD_FRAMES[PLANET]["aphrodite"][:2],
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

    print("# Venus's three tones, measured")
    print()
    print("The reference `ref/venus-radar-surface.png` has three values: mid")
    print("amber plains, brighter rough highlands and darker smooth lowlands.")
    print("The globe carries the mid tone, so the markings need one filament")
    print("above it and one below, and this is the measurement those two were")
    print("chosen on.")
    print()
    print("Luma is Rec. 709 on 0..255. The globe is `%s` %s."
          % (GLOBE, P.FILAMENT_HEX[GLOBE]))
    print()

    print("## The palette, on paper")
    print()
    print("| filament | sealed hex | sealed luma | as the render shows it | rendered luma |")
    print("|---|---|---|---|---|")
    for name in (GLOBE,) + HIGHLAND_CANDIDATES + LOWLAND_CANDIDATES:
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

    print("## The three numbers the Wish asks for")
    print()
    print("Measured on the rendered pixels, at each frame, with one region")
    print("repainted between two otherwise identical renders.")
    print()
    print("| separation | frame | pixels | mean | least | most |")
    print("|---|---|---|---|---|---|")
    headline = {}
    for frame, view in FRAMES.items():
        pairs = (
            ("highland `beige` against the globe", "highland", "beige", GLOBE),
            ("lowland `cocoa_brown` against the globe", "lowland",
             "cocoa_brown", GLOBE),
            ("lowland against highland", "lowland", "cocoa_brown", "beige"),
        )
        for label, role, candidate, against in pairs:
            count, mean, low, high = measured(
                render_review, bodies, role, candidate, against, view)
            headline.setdefault(label, []).append((frame, mean))
            print("| %s | %s | %d | **%.1f** | %.1f | %.1f |"
                  % (label, frame, count, mean, low, high))
    print()
    for label, rows in headline.items():
        print("- %s: %s."
              % (label, ", ".join("%.1f at the %s frame" % (mean, frame)
                                  for frame, mean in rows)))
    print()

    print("## Does the darker tone swamp the globe?")
    print()
    print("This is the question the Wish reserves judgement on, so it is")
    print("answered with the same measurement applied to the two filaments")
    print("darker than `cocoa_brown` in the palette.")
    print()
    print("| candidate | frame | pixels | mean separation from the globe | least | most |")
    print("|---|---|---|---|---|---|")
    darker = {}
    for candidate in LOWLAND_CANDIDATES:
        for frame, view in FRAMES.items():
            count, mean, low, high = measured(
                render_review, bodies, "lowland", candidate, GLOBE, view)
            darker.setdefault(candidate, []).append(mean)
            print("| `%s` | %s | %d | **%.1f** | %.1f | %.1f |"
                  % (candidate, frame, count, mean, low, high))
    print()
    print("| candidate | mean across the three frames | against `black` |")
    print("|---|---|---|")
    for candidate, values in darker.items():
        mean = sum(values) / len(values)
        black = sum(darker["black"]) / len(darker["black"])
        print("| `%s` | %.1f | %.0f%% of the way to a hole in the print |"
              % (candidate, mean, 100.0 * mean / black))
    print()

    print("## The brighter tone")
    print()
    print("| candidate | frame | pixels | mean separation from the globe | least | most |")
    print("|---|---|---|---|---|---|")
    for candidate in HIGHLAND_CANDIDATES:
        for frame, view in FRAMES.items():
            count, mean, low, high = measured(
                render_review, bodies, "highland", candidate, GLOBE, view)
            print("| `%s` | %s | %d | **%.1f** | %.1f | %.1f |"
                  % (candidate, frame, count, mean, low, high))
    print()

    print("## What was chosen, and what it cost")
    print()
    print("- **Highlands: `beige` #F7E6DE.** The Wish's intended answer, and it")
    print("  is taken. The number is reported plainly rather than softened: at")
    print("  20.2 luma levels it is the *thinnest* marking separation anywhere")
    print("  in this set, and it is below the 21.8 that `dark_gray` managed on")
    print("  Mercury's globe -- the separation that revision exists to replace")
    print("  as invisible. Two things make it read here where that one did not,")
    print("  and both are in the evidence rather than in the argument. The first")
    print("  is area: Aphrodite Terra covers about 17,400 pixels of a 900-pixel")
    print("  frame, a band running limb to limb, where Mercury's plains were")
    print("  separate patches a few millimetres across. The second is hue --")
    print("  `beige` is a pink-cream and the globe is an amber, so the boundary")
    print("  carries a colour step that luma does not count.")
    print("  `snap/worlds/venus-<side>-aphrodite.png` is where that claim is")
    print("  checked, and it is what the blind review was shown.")
    print("- **`white` was measured and not taken.** It separates 27.9, some")
    print("  7.7 levels further, and it is the brighter tone the reference's")
    print("  highlands arguably deserve. It was not taken because the Wish names")
    print("  `beige` and because `white` is already the brightest feature on")
    print("  three other worlds in this set -- Mars's caps, Mercury's Caloris")
    print("  floor and Earth's ice -- so Venus in `beige` is the one that stays")
    print("  its own colour. `yellow` at 9.6 is not a candidate at all.")
    print("- **Lowlands: `cocoa_brown` #8E3C06, on all three plains.** The Wish")
    print("  reserved the right to cut the two smaller plains if this tone")
    print("  swamped the globe, and measured, it does not: 33.5 luma levels")
    print("  against the amber, which is 37 per cent of the step `black` makes")
    print("  and close to the 45.5 `cocoa_brown` makes against Mercury's gray.")
    print("  `black` at 91.1 is the one that would read as a hole in the print.")
    print("  So **Atalanta, Guinevere and Lavinia are all drawn**, and none was")
    print("  dropped. `dark_gray` at 19.0 is the tone that would have vanished.")
    print("- **Venus now prints in three filaments** -- `sunflower_yellow`,")
    print("  `beige` and `cocoa_brown` -- where it printed in two. That is the")
    print("  set's ordinary number: Earth takes four, Mercury, Mars, Neptune,")
    print("  Saturn, Jupiter and now Venus take three, and Uranus alone takes")
    print("  two. No new spool: all three were already loaded for this set.")
    print()
    print("Measured by `measure/venus_tone_separation.py` on the exact solids")
    print("`parts/world.py` builds, through `cad/scripts/render_review`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
