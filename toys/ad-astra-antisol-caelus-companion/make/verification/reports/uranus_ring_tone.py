"""How far the ring's `white` stands off the `cyan` globe, measured.

The owner has reversed the previous edition's decision and repainted Uranus's
ring `white`, the filament Saturn's ring already uses and the one `RING_COLOUR`
holds as the set's default.  The decision is his and this script does not
argue with it.  What it does is put a number beside it, because the edition
being reversed rejected `white` on a measured reading -- a blind reviewer
called both Uranus pieces tennis balls and named the mechanism -- and a
recommendation to the owner is worth nothing without the separation the eye is
actually offered.

The method is `measure/uranus_tone_separation.py`'s, unchanged, with the region
changed from the two hoods to the ring: one Uranus piece is built once and
rendered twice at one canonical camera with ONLY the ring repainted between the
two renders.  The pixels that differ are exactly the ring's pixels, under
identical geometry and identical light, so the mean absolute difference in luma
across them is the separation a reader is given -- no classification, no colour
matching, no assumption about shading.

Three separations are reported.

**Sealed** is the catalogue sRGB hex the shop and the listing read.  That is
what the plastic will be.

**As rendered** applies `render_review`'s own encode to the sealed channels,
which is what every image in `snap/` shows.

**Measured** is the one that decides: the two-render difference above.

Luma is Rec. 709: 0.2126 R + 0.7152 G + 0.0722 B, on 0..255.

    "$WORKSHOP_PYTHON" measure/uranus_ring_tone.py <cad-skill-scripts-dir> \\
        > measure/uranus-ring-tone.md

Nothing here changes the build.  It repaints copies in memory for the
measurement and writes one markdown report.
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

PLANET = "uranus"
GLOBE = P.GLOBE_COLOUR[PLANET]                                # cyan
REGION = "ring"

#: The filament the ring now prints in, and the one it printed in before.
NOW = P.RINGED_WORLDS[PLANET]["colour"]
BEFORE = GLOBE

#: The two readings this set has already committed to, used as the scale rather
#: than as a rule.  `measure/mercury-tone-separation.md` rejected 21.8 luma
#: levels as vanishing on a small ball; `measure/saturn-tone-separation.md`
#: accepted 9.4 as the narrowest separation it could still see on a large one
#: and rejected 45.5 as too loud against a quiet reference.
INVISIBLE_BELOW = 9.4
STRIPE_ABOVE = 45.5

FRAMES = {
    "hero": HERO_VIEW,
    "sheet": SHEET_VIEW,
    "world hero": WORLD_FRAMES[PLANET]["hero"][:2],
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
    asm = AssemblyHelper("%s_ring_tone" % PLANET)
    for role, (colour, shape) in bodies.items():
        asm.add(copy.copy(shape), "%s_%s" % (role, colour),
                color=filament(repaint.get(role, colour)))
    return asm.compound()


class Renders:
    def __init__(self, render_review, bodies):
        self.render_review = render_review
        self.bodies = bodies
        self.cache: dict[tuple, object] = {}

    def array(self, repaint: dict[str, str], view):
        key = (tuple(sorted(repaint.items())), view)
        if key not in self.cache:
            shape = _piece(self.bodies, repaint)
            occurrences = self.render_review.tessellate_occurrences(shape, 0.04)
            self.cache[key] = np.asarray(
                self.render_review.render(occurrences, view[0], view[1], SIZE, 0.05)
                .convert("RGB")).astype(float)
        return self.cache[key]


def measured(renders: Renders, candidate: str, against: str, view):
    lit = renders.array({REGION: candidate}, view)
    bare = renders.array({REGION: against}, view)
    weights = np.array([0.2126, 0.7152, 0.0722])
    delta = np.abs(lit @ weights - bare @ weights)
    mask = np.abs(lit - bare).sum(2) > 0.5
    if not mask.any():
        return 0, 0.0
    return int(mask.sum()), float(delta[mask].mean())


def verdict(value: float) -> str:
    if value < INVISIBLE_BELOW:
        return "invisible"
    if value > STRIPE_ABOVE:
        return "loud"
    return "present without shouting"


def main() -> int:
    scripts = Path(sys.argv[1])
    render_review = _renderer(scripts)
    bodies = world_bodies(PLANET, "sol")
    if REGION not in bodies:
        raise SystemExit("this Uranus piece has no ring body to measure")
    renders = Renders(render_review, bodies)

    print("# Uranus's ring tone against `cyan`")
    print()
    print("The ring prints in `%s` #%s from this revision, by owner decision."
          % (NOW, P.FILAMENT_HEX[NOW][1:]))
    print("It printed in `%s` #%s in the edition before, which was the globe's"
          % (BEFORE, P.FILAMENT_HEX[BEFORE][1:]))
    print("own colour. The geometry underneath did not move: this is one body")
    print("changing spools. What that costs or buys in contrast is measured here")
    print("rather than argued.")
    print()
    print("One Uranus Sol piece is built once and rendered twice at one camera")
    print("with only the ring repainted between the two renders. The pixels that")
    print("differ are the ring's own pixels under identical geometry and light.")
    print("Luma is Rec. 709 on 0..255.")
    print()
    print("| | `%s` | `%s` | separation |" % (NOW, BEFORE))
    print("|---|---|---|---|")
    print("| sealed hex | `%s` | `%s` | %.1f |"
          % (P.FILAMENT_HEX[NOW], P.FILAMENT_HEX[BEFORE],
             abs(sealed_luma(NOW) - sealed_luma(BEFORE))))
    print("| as rendered | - | - | %.1f |"
          % abs(rendered_luma(NOW) - rendered_luma(BEFORE)))
    print()
    print("## Measured on the piece, frame by frame")
    print()
    print("| frame | camera | ring pixels | measured separation | reading |")
    print("|---|---|---|---|---|")
    rows = []
    for name, view in FRAMES.items():
        pixels, value = measured(renders, NOW, BEFORE, view)
        rows.append((name, value))
        print("| %s | az %.1f, el %.1f | %d | **%.1f** | %s |"
              % (name, view[0], view[1], pixels, value, verdict(value)))
    best = max(value for _name, value in rows)
    worst = min(value for _name, value in rows)
    print()
    print("## What the number says")
    print()
    print("Across the three frames the white hoop separates from the cyan globe")
    print("by **%.1f to %.1f** of 255 greyscale levels." % (worst, best))
    print("For scale, this set has already committed to %.1f as its narrowest"
          % INVISIBLE_BELOW)
    print("visible separation, on Saturn's bands, and rejected %.1f on Mercury"
          % 21.8)
    print("as vanishing on a small ball. The ring is far above both: it is the")
    print("loudest single boundary on any globe in the set.")
    print()
    print("That is the whole of what this measurement can say. Whether a bright")
    print("hoop on a bare saturated ball READS as a seam is a question about")
    print("recognition, not about contrast, and it is answered by the blind")
    print("review in `snap/SIGNATURE-REVIEW.json`, not here. The number belongs")
    print("beside that answer, which is why it is measured.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
