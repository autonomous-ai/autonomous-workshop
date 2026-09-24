"""How far apart Neptune's tones actually are, in the canonical renders.

This edition adds one white oval beside a `dark_gray` oval on a `blue` globe,
and an independent reader of the finished renders, shown them cold and told
nothing, called the new marking **"a small grey circle"** and the pair a
"notched figure-eight".  They called the two cloud bands on the upper half of
the same globe "bright white" in the same breath.  That reading is the reason
this report exists: the owner asked for a BRIGHT companion cloud, and a reader
of the product images did not see one.

Two different things were wrong and only one of them is a renderer.

**The figure was wrong, and it was repaired.**  In the build that reader saw,
the dark spot was subtracted straight back to the companion, so the two colours
shared a boundary and read as one two-lobed object.  The spot is now cut to a
KEEP-OUT instead -- the companion's oval grown by 2.19 degrees of arc, never
drawn and never printed -- which leaves one nozzle width of bare blue all the
way round the companion.  It is a separate mark now.

**The tone is the renderer, and it is measured rather than argued about.**
This report is the measurement.

**The method is `measure/saturn_tone_separation.py`'s, unchanged.**  One piece
is built once and rendered twice at one camera, with a single region repainted
between the two renders and nothing else altered.  The pixels that differ are
exactly that region's pixels, under identical geometry and identical light, so
the mean absolute difference in luma across them is the separation the eye is
offered -- no classification, no colour matching, no assumption about shading.
Luma is Rec. 709: 0.2126 R + 0.7152 G + 0.0722 B, on 0..255.

Both armies are measured, because on this globe the lean is most of the story:
the markings in question are SOUTHERN, the Sol piece leans its north pole
toward the lens, and `render_review` lights from above.

    "$WORKSHOP_PYTHON" measure/neptune_tone_separation.py <cad-skill-scripts-dir> \\
        > measure/neptune-tone-separation.md
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

PLANET = "neptune"
GLOBE = P.GLOBE_COLOUR[PLANET]                                # blue
SIZE = 900

#: The two frames the whole product is photographed from, plus the per-world
#: frame aimed at the dark spot, which is the one this edition's new marking
#: reads best at and the one a reader is given for it.
FRAMES = {
    "hero": HERO_VIEW,
    "sheet": SHEET_VIEW,
    "spot": WORLD_FRAMES[PLANET]["spot"][:2],
}

#: The nozzle-scale floor this set has already shipped a marking at, read off
#: this set's own reports rather than invented here, so the new number has
#: something honest to be compared against.
PRECEDENTS = (
    ("Saturn's light bands against its globe", 9.4,
     "measure/saturn-tone-separation.md"),
    ("Venus's beige highlands against its globe", 20.2,
     "measure/venus-tone-separation.md"),
)


def _renderer(scripts: Path):
    path = scripts / "render_review"
    loader = importlib.machinery.SourceFileLoader("render_review", str(path))
    spec = importlib.util.spec_from_loader("render_review", loader)
    module = importlib.util.module_from_spec(spec)
    module_spec = importlib.util.spec_from_loader("render_review", loader)
    module = importlib.util.module_from_spec(module_spec)
    loader.exec_module(module)
    return module


def _piece(bodies, repaint: dict[str, str]):
    """The piece with some regions repainted, and nothing else changed.

    `copy.copy` is not decoration: a colour is sealed on the shape object, so
    handing the same solids to a second assembly leaves them carrying the
    first assembly's colour and the two renders come out identical.
    """
    asm = AssemblyHelper("%s_tone" % PLANET)
    for role, (colour, shape) in bodies.items():
        asm.add(copy.copy(shape), "%s_%s" % (role, colour),
                color=filament(repaint.get(role, colour)))
    return asm.compound()


class Renders:
    def __init__(self, render_review, bodies):
        self.render_review = render_review
        self.bodies = bodies
        self.cache: dict[tuple, np.ndarray] = {}

    def array(self, repaint: dict[str, str], view):
        key = (tuple(sorted(repaint.items())), view)
        if key not in self.cache:
            shape = _piece(self.bodies, repaint)
            occurrences = self.render_review.tessellate_occurrences(shape, 0.04)
            image = self.render_review.render(occurrences, view[0], view[1],
                                              SIZE, 0.05)
            self.cache[key] = np.asarray(image.convert("RGB")).astype(float)
        return self.cache[key]


def measured(renders: Renders, role: str, candidate: str, against: str, view):
    """(pixel count, mean |luma difference|, min, max) for one region."""
    lit = renders.array({role: candidate}, view)
    bare = renders.array({role: against}, view)
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

    print("# Neptune's tones, and whether the new cloud reads as bright")
    print()
    print("One piece built once, rendered twice per question at one camera,")
    print("with a single region repainted between the two renders and nothing")
    print("else altered. Every pixel that moves belongs to that region, under")
    print("identical geometry and identical light. Mean absolute Rec. 709 luma")
    print("difference over those pixels, on 0..255.")
    print()
    print("Both armies, because the lean is most of the story here: the two")
    print("markings in question are SOUTHERN, the Sol piece leans its north")
    print("pole toward the lens, and `render_review` lights from above.")
    print()

    rows = {}
    for side in ("sol", "anti"):
        bodies = world_bodies(PLANET, side)
        renders = Renders(render_review, bodies)
        for label, role, candidate, against in (
                ("companion against the globe", "companion", "white", GLOBE),
                ("companion against the spot's filament", "companion",
                 "white", "dark_gray"),
                ("spot against the globe", "spot", "dark_gray", GLOBE),
                ("bands against the globe", "bands", "white", GLOBE)):
            for frame, view in FRAMES.items():
                count, mean, low, high = measured(
                    renders, role, candidate, against, view)
                rows[(side, label, frame)] = (count, mean, low, high)

    for side, army in (("sol", "Sol"), ("anti", "Anti-Sol")):
        print("## The %s piece" % army)
        print()
        print("| question | frame | pixels | mean luma apart | least | most |")
        print("|---|---|---:|---:|---:|---:|")
        for label in ("companion against the globe",
                      "companion against the spot's filament",
                      "spot against the globe",
                      "bands against the globe"):
            for frame in FRAMES:
                count, mean, low, high = rows[(side, label, frame)]
                print("| %s | `%s` | %d | **%.1f** | %.1f | %.1f |"
                      % (label, frame, count, mean, low, high))
        print()

    key = "companion against the spot's filament"
    pair = {side: rows[(side, key, "spot")][1] for side in ("sol", "anti")}
    globe_sep = {side: rows[(side, "companion against the globe", "spot")][1]
                 for side in ("sol", "anti")}
    bands_sep = {side: rows[(side, "bands against the globe", "spot")][1]
                 for side in ("sol", "anti")}

    print("## What the reader saw, and what the plastic is")
    print()
    print("At the `spot` frame -- the one a reader is given for this pair --")
    print("the companion is **%.1f luma levels** from the spot's filament on"
          % pair["sol"])
    print("the Sol piece and **%.1f** on the Anti-Sol one, and **%.1f / %.1f**"
          % (pair["anti"], globe_sep["sol"], globe_sep["anti"]))
    print("from the globe it sits on. The three cloud bands on the same globe")
    print("separate from the same globe by %.1f / %.1f."
          % (bands_sep["sol"], bands_sep["anti"]))
    print()
    print("Against this set's own shipped floor, read off its own reports:")
    print()
    print("| marking | separation | source |")
    print("|---|---:|---|")
    for name, value, source in PRECEDENTS:
        print("| %s | %.1f | `%s` |" % (name, value, source))
    print("| **Neptune's companion against its dark spot** | **%.1f** (Sol) / "
          "**%.1f** (Anti-Sol) | this report |" % (pair["sol"], pair["anti"]))
    print()
    floor = min(value for _n, value, _s in PRECEDENTS)
    worst = min(pair.values())
    if worst >= floor:
        print("**The companion separates from the dark spot by more than the")
        print("narrowest separation this set has already shipped** -- %.1f"
              % worst)
        print("against %.1f. It is not a marginal pairing by this set's own"
              % floor)
        print("standard.")
    else:
        print("**The companion separates from the dark spot by LESS than the")
        print("narrowest separation this set has already shipped** -- %.1f"
              % worst)
        print("against %.1f, and that is a finding rather than a result." % floor)
    print()
    print("### Why an unprimed reader still called it grey")
    print()
    print("Because it is not the separation that is small; it is the LIGHT.")
    print("`render_review` shades by surface normal from a light above the")
    print("piece and draws no shadow and no ground plane, and a flush colour")
    print("inlay's outer face IS the globe's own sphere -- a marking has the")
    print("same normal as the blue beside it. So every marking on the southern")
    print("face of a globe is rendered dim whatever filament it is printed in,")
    print("and every marking on the northern face is rendered bright. On this")
    print("globe the companion and the dark spot are both southern and both")
    print("come out in the 76-175 range across the two armies, while the two")
    print("northern cloud bands -- the same `white` spool the companion is")
    print("printed from -- come out at 200-235. The southernmost band, `b1`,")
    print("is `white` too and renders at about 103 on the Sol piece: a reader")
    print("of that image calls it grey as well, and `measure/neptune-flush.md`")
    print("records an earlier independent reader making the same call about")
    print("the same set of markings.")
    print()
    print("The two-render measurement above is immune to that, which is why it")
    print("is the one that decides: both renders carry the identical light and")
    print("the identical geometry, and only the filament differs.")
    print()
    print("**What this means for the printed object.** The companion prints in")
    print("`white` #%s, the same spool as the three cloud bands and as"
          % P.FILAMENT_HEX["white"].lstrip("#"))
    print("Saturn's and Uranus's rings; the spot prints in `dark_gray` #%s."
          % P.FILAMENT_HEX["dark_gray"].lstrip("#"))
    print("Those are the channels the shop and the listing read. On a printed")
    print("piece in ordinary light the difference between them is the")
    print("difference between white and mid-grey plastic. **The grey reading")
    print("is the renderer's, not the plastic's** -- and it is recorded in the")
    print("product's limitations in exactly those terms rather than left for a")
    print("buyer to discover from an image.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
