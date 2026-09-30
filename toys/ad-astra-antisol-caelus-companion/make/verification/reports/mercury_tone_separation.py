"""How far apart two filaments actually are on Mercury, in the canonical render.

The Wish asks for a number rather than an opinion: measure the greyscale
separation of `dark_gray` against the `gray` globe as the set stands, then
measure whichever tone replaces it, and measure both candidates for the
Caloris floor.  All of it "in the greyscale of the canonical render", which is
the only place the question is settled -- `measure/filament-value.md` already
established that the review renderer double-encodes a sealed sRGB channel, so
a separation computed from the catalogue hex is not the separation a reader of
the product images gets.

Three separations are reported for every candidate, and they are different
numbers doing different jobs.

**Sealed** is the catalogue sRGB hex the shop and the listing read, straight
out of `params.FILAMENT_HEX`.  That is what the plastic will be.

**As rendered** applies `render_review`'s own `_linear_to_srgb` to the sealed
channels, which is what every image in `snap/` shows.

**Measured** is the one that decides.  The same Mercury piece is built once
and rendered twice at one canonical camera: once with the region painted in
the candidate filament and once with it painted the globe's own `gray`.  The
pixels that differ between the two images are exactly that region's pixels,
under identical geometry and identical light, so the mean absolute difference
in luma across them is the separation the eye is offered -- with no
classification, no colour matching and no assumption about shading.

Luma is Rec. 709: 0.2126 R + 0.7152 G + 0.0722 B, on 0..255.

    "$WORKSHOP_PYTHON" measure/mercury_tone_separation.py <cad-skill-scripts-dir> \\
        > measure/mercury-tone-separation.md
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

PLANET = "mercury"
GLOBE = P.GLOBE_COLOUR[PLANET]                                # gray

#: The tone the plains and the Caloris rim are drawn in, and the tones this
#: report has to weigh it against.  `dark_gray` is what the set carried;
#: `cocoa_brown` and `black` are the only stocked filaments darker than it.
TERRAIN_CANDIDATES = ("dark_gray", "cocoa_brown", "black")

#: The Caloris floor has to be brighter than the globe, and these are the only
#: two stocked filaments lighter than `gray`.
FLOOR_CANDIDATES = ("beige", "white")

#: Rendered at the two frames the product is photographed from, applied to the
#: lone piece, so the measurement is taken under the light the product images
#: are lit by rather than under a light invented for the measurement.
FRAMES = {"hero": HERO_VIEW, "sheet": SHEET_VIEW}
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

    `copy.copy` is not decoration.  A colour is sealed on the shape object
    itself, so handing the same solids to a second assembly leaves them
    carrying the first assembly's colour and the two renders come out
    identical -- measured here as a separation of zero on a patch that is
    plainly visible in both images.  A shallow copy shares the B-rep and gets
    its own colour, which is exactly what this needs.
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


def measured(render_review, bodies, role: str, candidate: str, view):
    """(pixel count, mean |luma difference|, min, max) for one region.

    Two renders of one build: the region in `candidate`, and the region in the
    globe's own filament.  Every pixel that moved belongs to the region, and
    nothing else about the two images differs.
    """
    lit = _image(render_review, bodies, {role: candidate}, view)
    bare = _image(render_review, bodies, {role: GLOBE}, view)
    weights = np.array([0.2126, 0.7152, 0.0722])
    delta = np.abs(lit @ weights - bare @ weights)
    mask = np.abs(lit - bare).sum(2) > 0.5
    if not mask.any():
        return 0, 0.0, 0.0, 0.0
    values = delta[mask]
    return int(mask.sum()), float(values.mean()), float(values.min()), float(values.max())


def main() -> int:
    scripts = Path(sys.argv[1])
    render_review = _renderer(scripts)
    bodies = world_bodies(PLANET, "sol")

    print("# Mercury's tones, measured")
    print()
    print("Mercury's globe is Ø%.2f mm, the smallest in the set. The question"
          % P.globe_diameter(PLANET))
    print("this answers is which filaments a reader of the product images can")
    print("actually tell apart on a ball that size, and the answer is measured")
    print("three ways: on the sealed channels, on those channels as the review")
    print("renderer encodes them, and on the rendered pixels themselves.")
    print()
    print("Luma is Rec. 709 on 0..255. The globe is `%s` %s."
          % (GLOBE, P.FILAMENT_HEX[GLOBE]))
    print()

    print("## The palette, on paper")
    print()
    print("| filament | sealed hex | sealed luma | as the render shows it | rendered luma |")
    print("|---|---|---|---|---|")
    for name in (GLOBE,) + TERRAIN_CANDIDATES + FLOOR_CANDIDATES:
        shown = tuple(linear_to_srgb(value)
                      for value in channels(P.FILAMENT_HEX[name]))
        as_hex = "#" + "".join("%02X" % round(255 * value) for value in shown)
        print("| `%s` | %s | %.1f | %s | %.1f |"
              % (name, P.FILAMENT_HEX[name], sealed_luma(name), as_hex,
                 rendered_luma(name)))
    print()
    print("The render column is not decoration. `render_review` applies its own")
    print("`_linear_to_srgb` to channels that are already sRGB, so every image in")
    print("`snap/` is encoded twice, which lifts the mid-tones hard and leaves the")
    print("top end almost untouched. A dark tone therefore separates *better* in")
    print("the images than the sealed hex suggests, and a light one *worse*.")
    print("`measure/filament-value.md` is where that was first measured.")
    print()

    print("## The terrain tone: what the set carried, and what replaces it")
    print()
    print("The seven smooth plains and the Caloris rim are one tone. It has to")
    print("read as rock on a small gray ball: dark enough to separate, not so")
    print("dark that it reads as a gap in the print.")
    print()
    for frame, view in FRAMES.items():
        print("### Measured at the %s frame (azimuth %g, elevation %g)"
              % (frame, view[0], view[1]))
        print()
        print("| candidate | region | pixels | mean separation | least | most |")
        print("|---|---|---|---|---|---|")
        for candidate in TERRAIN_CANDIDATES:
            for role in ("plains", "caloris_rim"):
                count, mean, low, high = measured(
                    render_review, bodies, role, candidate, view)
                print("| `%s` | %s | %d | **%.1f** | %.1f | %.1f |"
                      % (candidate, role, count, mean, low, high))
        print()

    print("## The Caloris floor")
    print()
    print("The floor is the brightest thing on the reference, brighter than the")
    print("globe, and the only stocked filaments lighter than `gray` are these")
    print("two. The boundary a reader actually reads is the floor against the")
    print("rim around it rather than against the globe, so both are measured.")
    print()
    for frame, view in FRAMES.items():
        print("### Measured at the %s frame (azimuth %g, elevation %g)"
              % (frame, view[0], view[1]))
        print()
        print("| candidate | against | pixels | mean separation | least | most |")
        print("|---|---|---|---|---|---|")
        for candidate in FLOOR_CANDIDATES:
            count, mean, low, high = measured(
                render_review, bodies, "caloris_floor", candidate, view)
            print("| `%s` | the gray globe | %d | **%.1f** | %.1f | %.1f |"
                  % (candidate, count, mean, low, high))
        print()
    print("Against the rim, on the sealed channels and as rendered:")
    print()
    print("| pair | sealed | as rendered |")
    print("|---|---|---|")
    for candidate in FLOOR_CANDIDATES:
        print("| `%s` against `cocoa_brown` | %.1f | %.1f |"
              % (candidate,
                 abs(sealed_luma(candidate) - sealed_luma("cocoa_brown")),
                 abs(rendered_luma(candidate) - rendered_luma("cocoa_brown"))))
    print("| `beige` against `white` | %.1f | %.1f |"
          % (abs(sealed_luma("beige") - sealed_luma("white")),
             abs(rendered_luma("beige") - rendered_luma("white"))))
    print()
    print("The last row is the set's known weak pair, and it is why the Earth")
    print("reviewer could not reliably tell beige from white. Only one of the")
    print("two is used on Mercury, so that pair never occurs here.")
    print()

    print("## What was chosen")
    print()
    print("- **Terrain: `cocoa_brown`.** It is the darkest tone in the palette")
    print("  that still reads as rock. `black` separates further on every")
    print("  measure above and was not taken: a black patch on a 13.78 mm gray")
    print("  ball reads as a hole in the print rather than as terrain, and the")
    print("  reference's darkest terrain is a mid grey-brown, not black.")
    print("- **Caloris floor: `white`.** It separates further than `beige` from")
    print("  the globe on every measure above, and Mercury spends a third")
    print("  filament to have it.")
    print()
    print("What it cost is in `README.md` and in the product limitations:")
    print("Mercury now prints in three filaments rather than two, and")
    print("`cocoa_brown` is a warm brown rather than a neutral grey, so Mercury's")
    print("plains are the same family of colour as Mars's albedo and Jupiter's")
    print("and Saturn's bands. That is a real cost and it was paid deliberately:")
    print("the neutral alternative, `dark_gray`, is the tone this correction")
    print("exists to replace.")
    print()
    print("Measured by `measure/mercury_tone_separation.py` on the exact solids")
    print("`parts/world.py` builds, through `cad/scripts/render_review`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
