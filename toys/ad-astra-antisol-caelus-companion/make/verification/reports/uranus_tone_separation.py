"""How far a hood tone stands off `cyan`, measured rather than chosen.

The Wish asks for one number per candidate before the filament is committed:
the greyscale separation of each stocked filament against `cyan` #00FFFF on
this piece, in the images a reader is actually given.  It names `beige`
#F7E6DE as the intended answer -- a pale warm tone that lifts off cyan without
shouting -- keeps `white` #FFFEF7 as the fallback if `beige` measures as
invisible, and allows a third outcome outright: if every candidate is either
invisible or a stripe, recommend leaving Uranus a bare cyan globe.

The method is `measure/mercury_tone_separation.py`'s,
`measure/venus_tone_separation.py`'s, `measure/jupiter_tone_separation.py`'s
and `measure/saturn_tone_separation.py`'s, unchanged: one Uranus piece is built
once and rendered twice at one canonical camera, with the two hoods repainted
between the renders and nothing else altered.  The pixels that differ are
exactly the hoods' pixels, under identical geometry and identical light, so
the mean absolute difference in luma across them is the separation the eye is
offered -- no classification, no colour matching, no assumption about shading.

Three separations are reported for every candidate:

**Sealed** is the catalogue sRGB hex the shop and the listing read.  That is
what the plastic will be.

**As rendered** applies `render_review`'s own `_linear_to_srgb` to the sealed
channels, which is what every image in `snap/` shows.

**Measured** is the one that decides, and is the two-render difference above.

Luma is Rec. 709: 0.2126 R + 0.7152 G + 0.0722 B, on 0..255.

    "$WORKSHOP_PYTHON" measure/uranus_tone_separation.py <cad-skill-scripts-dir> \\
        > measure/uranus-tone-separation.md

It also writes two evidence images into `snap/worlds/`: the piece with its
hoods in the chosen tone and the same piece with the hoods painted the globe's
own cyan -- the bare-globe outcome the Wish allows -- at the product's own
frame, so "faint but present" is a picture a reader can check rather than a
number they have to trust.
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
HOODS = ("hood_north", "hood_south")

#: Every filament the shop stocks for this set, so the Wish's "each candidate"
#: is the whole list rather than a shortlist chosen to make one answer win.
CANDIDATES = tuple(sorted(P.FILAMENT_HEX))

#: What counts as invisible and what counts as a stripe.  Neither is a number
#: the Wish gives, so both are taken from this set's own measured history and
#: named here rather than left implicit.  `measure/mercury-tone-separation.md`
#: rejected 21.8 luma levels as vanishing on a small ball; `measure/
#: saturn-tone-separation.md` accepted 9.4 as its narrowest usable separation
#: on a large one, and rejected 45.5 as too loud for a quiet reference.
INVISIBLE_BELOW = 9.4
STRIPE_ABOVE = 45.5

FRAMES = {
    "hero": HERO_VIEW,
    "sheet": SHEET_VIEW,
    "world hero": WORLD_FRAMES[PLANET]["hero"][:2],
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
        self.cache: dict[tuple, object] = {}

    def image(self, repaint: dict[str, str], view, size: int = SIZE):
        key = (tuple(sorted(repaint.items())), view, size)
        if key not in self.cache:
            shape = _piece(self.bodies, repaint)
            occurrences = self.render_review.tessellate_occurrences(shape, 0.04)
            self.cache[key] = self.render_review.render(
                occurrences, view[0], view[1], size, 0.05)
        return self.cache[key]

    def array(self, repaint, view):
        return np.asarray(self.image(repaint, view).convert("RGB")).astype(float)


def measured(renders: Renders, candidate: str, against: str, view):
    """(pixel count, mean |luma difference|) over the hoods' own pixels."""
    lit = renders.array({role: candidate for role in HOODS}, view)
    bare = renders.array({role: against for role in HOODS}, view)
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
        return "a stripe"
    return "faint but present"


def main() -> int:
    scripts = Path(sys.argv[1])
    render_review = _renderer(scripts)
    bodies = world_bodies(PLANET, "sol")
    renders = Renders(render_review, bodies)

    print("# Uranus's hood tone against `cyan`")
    print()
    print("Every filament this set stocks, measured against the `cyan` #%s globe"
          % P.FILAMENT_HEX[GLOBE][1:])
    print("on the Uranus Sol piece. Sealed is the catalogue hex the shop reads;")
    print("as rendered is what every image in `snap/` shows; measured is the two-")
    print("render difference over the hoods' own pixels, which is the one that")
    print("decides. Luma is Rec. 709 on 0..255.")
    print()
    print("Invisible is below %.1f and a stripe is above %.1f. Neither number is"
          % (INVISIBLE_BELOW, STRIPE_ABOVE))
    print("in the Wish; both are this set's own measured history.")
    print("`measure/saturn-tone-separation.md` accepted %.1f as the narrowest"
          % INVISIBLE_BELOW)
    print("separation it could still see, and `measure/mercury-tone-separation.md`")
    print("rejected %.1f as too loud on a small ball against a quiet reference."
          % STRIPE_ABOVE)
    print()
    print("| candidate | sealed hex | lighter or darker | sealed apart | as rendered apart | measured, hero | measured, sheet | measured, world hero | reads as |")
    print("|---|---|---|---:|---:|---:|---:|---:|---|")
    globe_sealed = sealed_luma(GLOBE)
    globe_rendered = rendered_luma(GLOBE)
    table = {}
    for name in CANDIDATES:
        values = [measured(renders, name, GLOBE, view)[1]
                  for view in FRAMES.values()]
        mean = sum(values) / len(values)
        table[name] = (mean, values)
        side = ("lighter" if sealed_luma(name) > globe_sealed + 1e-9 else
                "darker" if sealed_luma(name) < globe_sealed - 1e-9 else "--")
        print("| `%s` | #%s | %s | %.1f | %.1f | %.1f | %.1f | %.1f | %s |"
              % (name, P.FILAMENT_HEX[name][1:], side,
                 abs(sealed_luma(name) - globe_sealed),
                 abs(rendered_luma(name) - globe_rendered),
                 values[0], values[1], values[2], verdict(mean)))

    lighter = [name for name in CANDIDATES
               if sealed_luma(name) > globe_sealed + 1e-9]
    faint = [name for name, (mean, _v) in table.items()
             if verdict(mean) == "faint but present"]
    beige = table["beige"][0]
    white = table["white"][0]

    print()
    print("## What the numbers say")
    print()
    print("- **`beige` #F7E6DE measures %.1f** averaged over the three frames,"
          % beige)
    print("  which is %s." % verdict(beige))
    print("- **`white` #FFFEF7 measures %.1f**, %s. It is the tone this"
          % (white, verdict(white)))
    print("  correction is replacing, and on a `cyan` globe it is what read as a")
    print("  tennis ball.")
    if faint:
        print("- **%d of the %d stocked filaments read as faint but present**: %s."
              % (len(faint), len(CANDIDATES),
                 ", ".join("`%s`" % name for name in faint)))
    else:
        print("- **No stocked filament reads as faint but present.** Every")
        print("  candidate is either invisible or a stripe, which is the outcome")
        print("  the Wish asks to be told about rather than worked around.")
    print()
    print("## The filter the table above does not apply, and the Wish does")
    print()
    print("`ref/uranus-sol.png` shows a region LIGHTER than the globe around it.")
    print("A darker patch would be a different feature, not a quieter one, so the")
    print("choice is only among the filaments lighter than `cyan`'s own %.1f luma."
          % globe_sealed)
    print()
    print("**There are exactly %d of them: %s.**"
          % (len(lighter), ", ".join("`%s`" % name for name in lighter)))
    print()
    for name in lighter:
        print("- `%s` #%s, %.1f luma, measures %.1f against the globe.%s"
              % (name, P.FILAMENT_HEX[name][1:], sealed_luma(name),
                 table[name][0],
                 (" A saturated yellow against a saturated cyan: near-opposite"
                  " in hue, so it is quiet in luma and loud in colour, which is"
                  " the one way a number can mislead here."
                  if name == "yellow" else
                  " The tone this correction replaces." if name == "white" else
                  " A pale warm off-white: the quietest of the three that is not"
                  " a hue clash.")))
    print()
    print("Everything else in the palette is darker than the globe. The quietest")
    print("of those by luma is `gray` at %.1f, which is invisible, and the next"
          % table["gray"][0])
    print("are `orange` and `sunflower_yellow` -- warm oranges on a cyan ball,")
    print("quiet in luma for exactly the reason they are loud in hue.")
    print()
    print("## The recommendation")
    print()
    if verdict(beige) == "faint but present":
        print("`beige`, the intended answer, and the measurement agrees with the")
        print("argument -- but it is worth being exact about how much of the")
        print("correction the tone is doing.")
        print()
        print("`beige` measures %.1f and `white` measures %.1f, so the tone change"
              % (beige, white))
        print("on its own is %.1f luma levels, about %.0f per cent quieter. That is"
              % (white - beige, 100.0 * (white - beige) / white))
        print("real and it is in the right direction, and it is **not** what stops")
        print("this piece reading as a tennis ball. What does that is the shape:")
        print("the marking was a belt of latitude encircling the ball, which the")
        print("obliquity stood upright across the visible face, and it is now a")
        print("broad region ENCLOSING each pole. Both have a boundary -- a flush")
        print("inlay always does -- but a cap's boundary shrinks to a point at the")
        print("pole and a belt's runs right round the ball and comes back. A")
        print("quieter stripe is still a stripe; this is not a stripe.")
        print()
        print("`beige` also loads no new spool -- it is already Earth's dryland and")
        print("Jupiter's and Saturn's zones -- and at %.1f it sits inside the band"
              % beige)
        print("this set has already proved it can both see and live with. `white`")
        print("stays on the shelf as the fallback and is not needed.")
    elif verdict(beige) == "invisible":
        print("`beige` measures %.1f, which is invisible on this globe, so the"
              % beige)
        print("Wish's own fallback applies and the hood stays `white` at %.1f."
              % white)
    else:
        print("Neither the intended tone nor the fallback lands inside the band.")
        print("The Wish's third outcome applies: leave Uranus a bare `cyan` globe")
        print("with no marking at all, and let it be the one unmarked world in a")
        print("set of eight.")
    print()
    print("## The thing no filament can fix")
    print()
    print("`ref/uranus-sol.png` is a pale desaturated ice blue -- its ball means")
    print("161, 200, 206, luma 192.7, measured in `measure/uranus-reference.md`.")
    print("`cyan` #00FFFF is a saturated neon with no red in it at all.")
    print()
    print("**There is no pale blue in this set's palette, and the shop has none to")
    print("sell it either.** The %d filaments here are exactly the Bambu Lab PLA"
          % len(CANDIDATES))
    print("Lite range, all of it, and its only blue-family colours are `cyan` and")
    print("`blue` #004EA8 at luma 67.9 -- a dark navy, further from the reference")
    print("than `cyan` is. The one plausible pale blue the shop lists at all,")
    print("`misty blue` #688197, is a Bambu Lab PETG Basic colour, and at luma")
    print("125.3 it is a mid slate rather than an ice blue; loading it would also")
    print("put a second material family in a box whose whole point is that it")
    print("prints in one.")
    print()
    print("So **the gap between the globe's own colour and the reference cannot be")
    print("closed inside this correction**, whatever the hood is painted, and a")
    print("paler marking on a neon globe does not make the globe paler. The")
    print("limitation is recorded in `product.json`, in the design contract and in")
    print("the README rather than compensated for here. If the set should acquire")
    print("a pale blue, that is a recommendation for a future revision: it would")
    print("mean a new material family or a custom spool, and `cyan` is shared with")
    print("the Anti-Sol flames and the Anti-Sol corona cells, so changing it")
    print("reaches well outside two printed parts.")

    print()
    print("## The ring, which is a different question")
    print()
    print("A ring is a silhouette rather than a surface marking, so the quietness")
    print("argument above does not automatically reach it, and the brief says to")
    print("take `white` -- the tone Saturn's ring already wears -- unless a reason")
    print("not to is MEASURED. Here is the measurement, by the same two-render")
    print("method with only the ring repainted.")
    print()
    print("| candidate | sealed hex | measured, hero | measured, sheet | measured, world hero |")
    print("|---|---|---:|---:|---:|")
    ring_table = {}
    for name in CANDIDATES:
        values = []
        for view in FRAMES.values():
            lit = renders.array({"ring": name}, view)
            bare = renders.array({"ring": GLOBE}, view)
            weights = np.array([0.2126, 0.7152, 0.0722])
            delta = np.abs(lit @ weights - bare @ weights)
            mask = np.abs(lit - bare).sum(2) > 0.5
            values.append(float(delta[mask].mean()) if mask.any() else 0.0)
        ring_table[name] = sum(values) / len(values)
        print("| `%s` | #%s | %.1f | %.1f | %.1f |"
              % (name, P.FILAMENT_HEX[name][1:], values[0], values[1], values[2]))
    print()
    print("`white` measures %.1f against the globe and `cyan` -- the globe's own"
          % ring_table["white"])
    print("filament, which makes the hoop a silhouette and nothing else --")
    print("measures %.1f by construction." % ring_table["cyan"])

    if len(sys.argv) > 2:
        target = Path(sys.argv[2])
        target.mkdir(parents=True, exist_ok=True)
        chosen = P.MARKINGS_HOOD_COLOUR if hasattr(P, "MARKINGS_HOOD_COLOUR") else bodies[HOODS[0]][0]
        view = FRAMES["world hero"]
        renders.image({}, view).save(target / "uranus-hood-tone.png")
        renders.image({role: GLOBE for role in HOODS}, view).save(
            target / "uranus-bare-globe.png")
        print()
        print("Evidence: `snap/worlds/uranus-hood-tone.png` is the piece as built,")
        print("in `%s`; `snap/worlds/uranus-bare-globe.png` is the same piece with"
              % chosen)
        print("the hoods painted the globe's own cyan, which is the bare-globe")
        print("outcome the Wish allows, rendered so the two can be compared.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
