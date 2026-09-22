"""How far apart Saturn's tones actually are, in the canonical render.

This correction runs the opposite way from the last three.  Saturn was not too
plain; it was too loud.  Four `cocoa_brown` bands on a `yellow` globe is one of
the highest-contrast pairings in the whole palette, and `ref/saturn-sol.png` is
the softest image in the reference set: a cream-to-pale-tan globe whose bands
are wide, soft-edged and low in contrast, and whose strongest band is barely
darker than its neighbours.

So the Wish asks for three numbers before the filament is committed: the
greyscale separation of `sunflower_yellow` against `yellow`, and of
`cocoa_brown` against both.  It names `beige` #F7E6DE as the fallback if the
first of those turns out to be too close to see at all, and it forbids quietly
going back to brown.

The method is `measure/mercury_tone_separation.py`'s,
`measure/venus_tone_separation.py`'s and `measure/jupiter_tone_separation.py`'s,
unchanged: one Saturn piece is built once and rendered twice at one canonical
camera, with a single region repainted between the two renders and nothing else
altered.  The pixels that differ are exactly that region's pixels, under
identical geometry and identical light, so the mean absolute difference in luma
across them is the separation the eye is offered -- no classification, no colour
matching, no assumption about shading.

Three separations are reported for every candidate:

**Sealed** is the catalogue sRGB hex the shop and the listing read.  That is
what the plastic will be.

**As rendered** applies `render_review`'s own `_linear_to_srgb` to the sealed
channels, which is what every image in `snap/` shows.

**Measured** is the one that decides, and is the two-render difference above.

Luma is Rec. 709: 0.2126 R + 0.7152 G + 0.0722 B, on 0..255.

    "$WORKSHOP_PYTHON" measure/saturn_tone_separation.py <cad-skill-scripts-dir> \\
        > measure/saturn-tone-separation.md

It also writes two side-by-side evidence images into `snap/worlds/`: the piece
with its one darker band and the same piece without it, at the product's own
frame, so the "without dominating" half of the Wish's test is a picture a
reader can check rather than a number they have to trust.
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
from parts import saturn_atlas as S                           # noqa: E402
from parts.world import world_bodies                          # noqa: E402
from snap_frames import HERO_VIEW, SHEET_VIEW                 # noqa: E402
from world_views import FRAMES as WORLD_FRAMES                # noqa: E402

PLANET = "saturn"
GLOBE = P.GLOBE_COLOUR[PLANET]                                # yellow

#: The band tones this piece may wear.  `sunflower_yellow` is the Wish's own
#: first choice, `beige` is the fallback it allows, `cocoa_brown` is what is
#: being replaced and is measured so the replacement can be compared with it,
#: and `white` is measured because it is the tone the cap takes and the tone
#: the ring already wears.
CANDIDATES = ("sunflower_yellow", "beige", "white", "cocoa_brown")

#: The two frames the whole product is photographed from, plus the frame the
#: single-piece evidence is rendered at, so the numbers belong to the images a
#: reader is actually given rather than to a light invented here.
FRAMES = {
    "hero": HERO_VIEW,
    "sheet": SHEET_VIEW,
    "quarter": WORLD_FRAMES[PLANET]["quarter"][:2],
}
SIZE = 900
EVIDENCE = Path("snap/worlds")


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
    """The piece with some regions repainted, and nothing else changed.

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


class Renders:
    """One render per (repaint, frame), computed once and kept."""

    def __init__(self, render_review, bodies):
        self.render_review = render_review
        self.bodies = bodies
        self.cache: dict[tuple, np.ndarray] = {}

    def image(self, repaint: dict[str, str], view, size: int = SIZE):
        key = (tuple(sorted(repaint.items())), view, size)
        if key not in self.cache:
            shape = _piece(self.bodies, repaint)
            occurrences = self.render_review.tessellate_occurrences(shape, 0.04)
            image = self.render_review.render(occurrences, view[0], view[1],
                                              size, 0.05)
            self.cache[key] = image
        return self.cache[key]

    def array(self, repaint, view):
        return np.asarray(self.image(repaint, view).convert("RGB")).astype(float)


def measured(renders: Renders, role: str, candidate: str, against: str, view):
    """(pixel count, mean |luma difference|, min, max) for one region.

    Two renders of one build: the region in `candidate`, and the region in
    `against`.  Every pixel that moved belongs to the region, and nothing else
    about the two images differs.
    """
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


def mean_over_frames(renders, role, candidate, against, summary_key=None,
                     store=None):
    values = []
    for _frame, view in FRAMES.items():
        values.append(measured(renders, role, candidate, against, view)[1])
    value = sum(values) / len(values)
    if store is not None and summary_key is not None:
        store[summary_key] = value
    return value


#: What the four dark-band images show, written down after they existed rather
#: than predicted from the luma table.  The Wish allows one darker band "only if
#: it measures as distinguishable without dominating", and dominating is not a
#: number, so this is the read.
DARK_BAND_VERDICT = """
**Distinguishable: yes, on both armies, and not marginally.** At 39.5 luma
levels against the globe it is the only marking on this piece a reader would
call dark, and it is the one band the reference lets you notice.

**Dominating: no -- but the margin is smaller on the Anti-Sol piece, and that is
reported rather than averaged away.** On the Sol piece the band sits at -14/-30
and the Sol lean tips the north pole toward the lens, so most of it is below the
ring and near the lower limb; that piece reads as a pale gold ball with soft
stripes and one darker one low down. On the Anti-Sol piece the opposite lean
brings the same band into the middle of the lit face, where it is a broad brown
swath over roughly a fifth of it and is plainly the loudest thing on the globe.
Even there the piece does not go back to what this correction replaced: four
hard brown bands spread over sixty degrees of latitude read as a striped ball,
and one brown band under four soft amber ones reads as a ball with a belt.

**What the dropped image shows, and it is not a one-sided answer.** With that
band in the band filament the Anti-Sol piece is both calmer AND flatter: the
whole globe becomes one soft amber-on-gold rhythm with a white cap, and no band
stands out at all. That is quieter than the build as shipped, and it is further
from the reference rather than closer, because the reference does have one band
you notice. The trade is an accent against a little more quiet, and the accent
is what the Wish asks for. The band is kept.

**What that costs, stated:** the two armies are not equally quiet at the
product's own camera. The Sol piece is the softer of the two and the Anti-Sol
piece carries its dark band face-on. That is the mirrored lean rather than any
difference between the parts -- `measure/saturn-cap-visibility.md` shows the
same lean working the other way on the bright cap, which is face-on on the Sol
piece and a limb crescent on the Anti-Sol one. Between them the two effects
roughly cancel: each army has one strong marking facing the camera and one
turned away.
"""


def main() -> int:
    scripts = Path(sys.argv[1])
    render_review = _renderer(scripts)
    bodies = world_bodies(PLANET, "sol")
    renders = Renders(render_review, bodies)

    print("# Saturn's tones, measured")
    print()
    print("`ref/saturn-sol.png` is the softest image in the reference set: a")
    print("cream-to-pale-tan globe whose bands are wide, soft-edged and low in")
    print("contrast, whose strongest band is barely darker than its neighbours,")
    print("and whose northern part is lighter than its southern. The build this")
    print("corrects wore four `cocoa_brown` bands on a `yellow` globe -- one of")
    print("the highest-contrast pairings in the palette -- so it read as a")
    print("hard-striped gold ball. This is the measurement the replacement tone")
    print("was chosen on.")
    print()
    print("Luma is Rec. 709 on 0..255. The globe is `%s` %s and is unchanged by"
          % (GLOBE, P.FILAMENT_HEX[GLOBE]))
    print("this correction, as is the `white` %s ring."
          % P.FILAMENT_HEX["white"])
    print()

    print("## The palette, on paper")
    print()
    print("| filament | sealed hex | sealed luma | as the render shows it | rendered luma |")
    print("|---|---|---|---|---|")
    for name in (GLOBE,) + CANDIDATES:
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
    print("where that was first measured, and it is why the light candidates")
    print("below measure so much closer than their sealed hex suggests: the")
    print("`yellow` globe is already near the top of the encode.")
    print()

    print("## The numbers the Wish asks for")
    print()
    print("Measured on the rendered pixels, at each frame, with one region")
    print("repainted between two otherwise identical renders.")
    print()
    print("| separation | on | frame | pixels | mean | least | most |")
    print("|---|---|---|---:|---:|---:|---:|")
    store: dict[str, float] = {}
    rows = [
        ("`%s` against the `%s` globe" % (S.BAND_COLOUR, GLOBE),
         "bands", S.BAND_COLOUR, GLOBE, "band_vs_globe"),
        ("`beige` against the `%s` globe" % GLOBE,
         "bands", "beige", GLOBE, "beige_vs_globe"),
        ("`white` against the `%s` globe" % GLOBE,
         "bands", "white", GLOBE, "white_vs_globe"),
        ("`cocoa_brown` against the `%s` globe" % GLOBE,
         "southbelt", "cocoa_brown", GLOBE, "cocoa_vs_globe"),
        ("`cocoa_brown` against the `%s` bands" % S.BAND_COLOUR,
         "southbelt", "cocoa_brown", S.BAND_COLOUR, "cocoa_vs_band"),
        ("`cocoa_brown` against `beige` bands",
         "southbelt", "cocoa_brown", "beige", "cocoa_vs_beige"),
        ("the `white` cap against the `%s` globe" % GLOBE,
         "cap", "white", GLOBE, "cap_vs_globe"),
        ("a `beige` cap against the `%s` globe" % GLOBE,
         "cap", "beige", GLOBE, "beigecap_vs_globe"),
    ]
    for label, role, candidate, against, key in rows:
        means = []
        for frame, view in FRAMES.items():
            count, mean, low, high = measured(renders, role, candidate,
                                              against, view)
            means.append(mean)
            print("| %s | `%s` | %s | %d | **%.1f** | %.1f | %.1f |"
                  % (label, role, frame, count, mean, low, high))
        store[key] = sum(means) / len(means)
    print()
    print("| separation | mean across the three frames |")
    print("|---|---:|")
    for label, _role, _candidate, _against, key in rows:
        print("| %s | **%.1f** |" % (label, store[key]))
    print()

    print("## The reference points this set already has")
    print()
    print("A luma number means nothing on its own, so here are the separations")
    print("this set has already measured and already judged.")
    print()
    print("| separation | measured | the judgement that was made on it |")
    print("|---|---:|---|")
    print("| `dark_gray` on Mercury's gray globe | 21.8 | invisible; the Mercury correction exists to replace it |")
    print("| `beige` on Venus's amber globe | 20.2 | the thinnest in the set, kept, and it reads |")
    print("| `beige` on Jupiter's orange globe | 30.5 | clear |")
    print("| `cocoa_brown` on Venus's amber globe | 33.5 | clear, and not swamping |")
    print("| `cocoa_brown` on Mercury's gray globe | 45.5 | clear |")
    print("| `black` on Venus's amber globe | 91.1 | reads as a hole in the print |")
    print()

    print("## The dark band, as a picture")
    print()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    keep = EVIDENCE / "saturn-dark-band-kept.png"
    drop = EVIDENCE / "saturn-dark-band-dropped.png"
    renders.image({}, FRAMES["quarter"], 1200).save(keep)
    renders.image({"southbelt": S.BAND_COLOUR}, FRAMES["quarter"], 1200).save(drop)
    print("The Wish allows one darker band, `cocoa_brown`, at -14/-30, and only")
    print("if it measures as distinguishable without dominating. Distinguishable")
    print("is a number and it is above. Dominating is not, so it is rendered:")
    print()
    print("- `%s` -- the piece as built, with the one darker band;" % keep)
    print("- `%s` -- the same piece with that band in the" % drop)
    print("  band filament, so the only thing that differs between the two")
    print("  images is whether the band is dark.")
    print()
    print("Those two are the Sol piece, and on the Sol piece the answer is easy")
    print("because the band is at -14/-30 and the Sol piece leans its north pole")
    print("toward the lens: most of that band is below the ring and near the")
    print("lower limb. **The Anti-Sol piece is the hard case and it is the one")
    print("that has to be looked at**, because the opposite lean brings the same")
    print("band round to the middle of the visible face. So the same pair is")
    print("rendered on that army too:")
    print()
    anti_bodies = world_bodies(PLANET, "anti")
    anti = Renders(render_review, anti_bodies)
    anti_keep = EVIDENCE / "saturn-dark-band-kept-anti.png"
    anti_drop = EVIDENCE / "saturn-dark-band-dropped-anti.png"
    anti.image({}, FRAMES["quarter"], 1200).save(anti_keep)
    anti.image({"southbelt": S.BAND_COLOUR}, FRAMES["quarter"], 1200).save(anti_drop)
    print("- `%s` -- the Anti-Sol piece as built;" % anti_keep)
    print("- `%s` -- the same piece with the band in the" % anti_drop)
    print("  band filament.")
    print()
    print(DARK_BAND_VERDICT.strip())
    print()

    print("## The cap, as a picture")
    print()
    white_cap = EVIDENCE / "saturn-cap-white.png"
    beige_cap = EVIDENCE / "saturn-cap-beige.png"
    renders.image({"cap": "white"}, FRAMES["quarter"], 1200).save(white_cap)
    renders.image({"cap": "beige"}, FRAMES["quarter"], 1200).save(beige_cap)
    print("The same question is asked of the bright northern region. `white` is")
    print("the lightest tone this piece already carries -- it is the ring -- and")
    print("`beige` is the next one down. Requirement 3 asks for *a wide soft")
    print("brightening on an already light globe*, so soft is the test and it is")
    print("rendered rather than argued:")
    print()
    print("- `%s` -- the cap in `white` %s;"
          % (white_cap, P.FILAMENT_HEX["white"]))
    print("- `%s` -- the cap in `beige` %s."
          % (beige_cap, P.FILAMENT_HEX["beige"]))
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
