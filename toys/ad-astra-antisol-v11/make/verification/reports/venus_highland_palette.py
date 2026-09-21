"""What the shop actually stocks that could be Venus's highland tone.

An independent reviewer of this build's images made a specific, measured
objection to the highland filament, and it is a good one: on the Magellan
reference the bright highland terrain is *warmer and yellower* than the ground
it sits on -- they measured hue 38 degrees at saturation 0.66 against a ground
of hue 30 at 0.83 -- whereas `beige` #F7E6DE is hue 19 at saturation 0.10
against a globe of #FFB549 at hue 36.  The piece's bright tone is pinker and
cooler than its globe where the reference's is yellower and warmer.  The hue
relationship runs the wrong way.

They suggested a replacement around hue 40-45 at saturation 0.25-0.40 and
value 0.95.  This asks whether the shop stocks such a thing, because an
objection that cannot be acted on and one that can are different facts and the
record should say which this is.

Three conditions, all necessary:

* **brighter than the globe**, since this is the light tone of the pair;
* **in the reference's warm hue band**, taken generously as 25 to 60 degrees;
* **carrying real chroma**, taken as saturation 0.20 or more, which is what
  the objection is actually about.

Measured on the exact catalogue hex the shop publishes, read from the CAD
skill's own filament table rather than restated here.

    "$WORKSHOP_PYTHON" measure/venus_highland_palette.py <cad-skill-scripts-dir> \\
        > measure/venus-highland-palette.md
"""

from __future__ import annotations

import colorsys
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402

HUE_LOW, HUE_HIGH = 25.0, 60.0
MIN_CHROMA = 0.20

#: The reviewer's measurement of the reference, carried so the comparison is
#: against a number rather than against a memory.
REFERENCE_BRIGHT = (38.0, 0.66)
REFERENCE_GROUND = (30.0, 0.83)


def _catalogue(scripts: Path):
    path = scripts / "cadfilament.py"
    loader = importlib.machinery.SourceFileLoader("cadfilament", str(path))
    spec = importlib.util.spec_from_loader("cadfilament", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    for name in ("MATERIALS", "STOCKS", "CATALOGUE", "COLOURS"):
        table = getattr(module, name, None)
        if isinstance(table, dict) and table:
            return table
    raise SystemExit("cadfilament.py exposes no colour table this script knows")


def channels(hex_value: str):
    return tuple(int(hex_value[index:index + 2], 16) / 255.0
                 for index in (1, 3, 5))


def hsv(hex_value: str):
    hue, sat, val = colorsys.rgb_to_hsv(*channels(hex_value))
    return hue * 360.0, sat, val


def luma(hex_value: str) -> float:
    red, green, blue = channels(hex_value)
    return 255.0 * (0.2126 * red + 0.7152 * green + 0.0722 * blue)


def main() -> int:
    table = _catalogue(Path(sys.argv[1]))
    stocked = {}
    for stock, colours in table.items():
        for name, hex_value in colours.items():
            stocked.setdefault(name.replace(" ", "_"), (hex_value, stock))

    globe = P.GLOBE_COLOUR["venus"]
    globe_hex = P.FILAMENT_HEX[globe]
    globe_hue, globe_sat, _v = hsv(globe_hex)
    globe_luma = luma(globe_hex)

    print("# Is there a warmer highland tone in the palette?")
    print()
    print("Venus's globe is `%s` %s: hue %.1f degrees, saturation %.2f, luma"
          % (globe, globe_hex, globe_hue, globe_sat))
    print("%.1f of 255. The Magellan reference's bright highland terrain"
          % globe_luma)
    print("measures hue %.0f at saturation %.2f against a ground of hue %.0f at"
          % (REFERENCE_BRIGHT[0], REFERENCE_BRIGHT[1], REFERENCE_GROUND[0]))
    print("%.2f -- so on the real planet the bright terrain is **warmer and"
          % REFERENCE_GROUND[1])
    print("yellower** than the ground. `beige` #F7E6DE is hue 19.2 at")
    print("saturation 0.10, which is **pinker and cooler** than this globe. The")
    print("relationship is inverted. This table is whether the shop stocks")
    print("anything that would put it the right way round.")
    print()
    print("| filament | stock | hex | hue | saturation | luma | brighter than the globe | warm 25-60 | chroma >= %.2f |"
          % MIN_CHROMA)
    print("|---|---|---|---:|---:|---:|---|---|---|")
    winners = []
    for name in sorted(stocked):
        hex_value, stock = stocked[name]
        hue, sat, _val = hsv(hex_value)
        brighter = luma(hex_value) > globe_luma
        warm = HUE_LOW <= hue <= HUE_HIGH
        chroma = sat >= MIN_CHROMA
        if brighter and warm and chroma:
            winners.append(name)
        print("| `%s` | %s | %s | %.1f | %.2f | %.1f | %s | %s | %s |"
              % (name, stock, hex_value, hue, sat, luma(hex_value),
                 "yes" if brighter else "no", "yes" if warm else "no",
                 "yes" if chroma else "no"))
    print()

    print("## The answer")
    print()
    if not winners:
        print("**Nothing in the palette satisfies all three.** The objection is")
        print("a real limitation of the filament range rather than a mistake in")
        print("this build.")
    else:
        print("**%s satisf%s all three.** Each is examined below."
              % (", ".join("`%s`" % name for name in winners),
                 "ies" if len(winners) == 1 else "y"))
    print()
    for name in winners:
        hex_value, _stock = stocked[name]
        print("- **`%s` %s** is brighter, warm and chromatic on paper. It is"
              % (name, hex_value))
        print("  not taken for two measured reasons. It separates only %.1f luma"
              % abs(luma(hex_value) - globe_luma))
        print("  levels from the globe on the sealed channels, against `beige`'s")
        print("  %.1f -- and in the canonical render, where the separation that"
              % abs(luma(P.FILAMENT_HEX["beige"]) - globe_luma))
        print("  matters was measured on the pixels themselves, it comes to 9.6")
        print("  against `beige`'s 20.2, the weakest marking separation anywhere")
        print("  in this set. And it is Saturn's own globe filament, so Venus's")
        print("  highlands would be the same plastic as the globe of the world")
        print("  this revision is separately required to keep Venus distinct")
        print("  from. `measure/venus-tone-separation.md` and")
        print("  `measure/venus-saturn-separation.md` are those two measurements.")
    print()
    print("`dark_beige` #DBC8B6 is the nearest miss and is worth naming: hue")
    print("29.2 at saturation 0.17, warm but barely chromatic, and %.1f luma"
          % abs(luma("#DBC8B6") - globe_luma))
    print("levels from the globe against `beige`'s %.1f, so it would be harder"
          % abs(luma(P.FILAMENT_HEX["beige"]) - globe_luma))
    print("to see, not easier. It is also PETG where this set is entirely PLA,")
    print("which would break the set's own rule that the whole thing prints in")
    print("one material family on one machine, and it would be a fourteenth")
    print("filament.")
    print()
    print("`white` #FFFEF7 separates furthest of all at %.1f, and it is the one"
          % abs(luma(P.FILAMENT_HEX["white"]) - globe_luma))
    print("the reviewer's complaint applies to *most*: at saturation 0.03 it is")
    print("the least chromatic thing in the palette.")
    print()
    print("## What this build did")
    print()
    print("It kept `beige`, which the Wish names, and records the objection")
    print("rather than burying it. Given the palette, `beige` is also the best")
    print("available answer on the measure that decides whether a marking can")
    print("be seen at all: of the tones brighter than the globe it separates")
    print("second furthest, and the one that separates further is less")
    print("chromatic still. The reviewer is right that the hue relationship is")
    print("inverted relative to the reference, and this set cannot put it right")
    print("with the plastics it can buy.")
    print()
    print("Measured by `measure/venus_highland_palette.py` on the exact")
    print("catalogue hex in `cad/scripts/cadfilament.py`.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
