"""Is Mars's albedo darker than the globe it sits in, and where does it look lighter?

An independent critic, shown this build's review renders cold, reported that
the albedo is *lighter* than the globe -- "the hue is right; the value is
inverted" -- and named it the highest-leverage thing left to fix.  They
measured the images correctly.  The conclusion about the product is still
wrong, and the difference between those two statements is this file.

Two different things carry colour here.

The **sealed channels** are what the shop and the listing read.  The Make
contract is explicit that a part's `Color(r, g, b)` channels are the sRGB hex
you want shown, authored unconverted, and `colors.py` does exactly that.  On
those channels `cocoa_brown` is darker than `red`, which is what the Wish asks
for.

The **review renderer** is a different consumer.  `cad/scripts/render_review`
carries a `_linear_to_srgb` and applies it to the channels it is handed, so it
treats a sealed sRGB value as though it were linear light and encodes it a
second time.  A double encode lifts mid-tones hard and leaves a channel that is
already 1.0 alone, so `cocoa_brown` rises a long way and `red` does not move at
all -- and in those images, and only in those images, the albedo comes out
lighter than the globe.

This measures both, so the difference is a number rather than an argument.

    "$WORKSHOP_PYTHON" measure/filament_value.py > measure/filament-value.md

Exit 0 when the sealed channels put the albedo darker than the globe.
"""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

import params as P                                            # noqa: E402

#: The two ends of Mars's three-filament palette, plus the caps.
MARS = ("red", "cocoa_brown", "white")

#: The contrast ratio at which a value difference reads as shading rather than
#: as a change of hue.  Below it two colours are told apart by their colour,
#: not by their lightness.
SHADING_RATIO = 3.0


def channels(hex_value: str) -> tuple[float, float, float]:
    return tuple(int(hex_value[index:index + 2], 16) / 255.0
                 for index in (1, 3, 5))


def srgb_to_linear(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def linear_to_srgb(value: float) -> float:
    """`render_review`'s own encode, copied so this measures what it does."""
    return 12.92 * value if value <= 0.0031308 else 1.055 * value ** (1 / 2.4) - 0.055


def luminance(rgb) -> float:
    red, green, blue = (srgb_to_linear(channel) for channel in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(one: float, other: float) -> float:
    high, low = max(one, other), min(one, other)
    return (high + 0.05) / (low + 0.05)


def as_hex(rgb) -> str:
    return "#%02X%02X%02X" % tuple(
        max(0, min(255, round(channel * 255.0))) for channel in rgb
    )


def main() -> int:
    print("# Mars's three filaments, by value")
    print()
    print("## What the shop is sealed to show")
    print()
    print("`colors.py` seals the catalogue sRGB hex on every leaf part,")
    print("unconverted, which is what the Make contract asks for and what the")
    print("listing and the host renders read.")
    print()
    print("| filament | sealed hex | relative luminance |")
    print("|---|---|---|")
    sealed = {}
    for name in MARS:
        rgb = channels(P.FILAMENT_HEX[name])
        sealed[name] = luminance(rgb)
        print("| `%s` | %s | %.4f |" % (name, P.FILAMENT_HEX[name], sealed[name]))
    print()
    globe, albedo, caps = sealed["red"], sealed["cocoa_brown"], sealed["white"]
    darker = albedo < globe
    print("**The albedo is %s than the globe it sits in**, %.4f against %.4f."
          % ("darker" if darker else "LIGHTER", albedo, globe))
    print()
    print("| pair | contrast ratio | reads as |")
    print("|---|---|---|")
    for label, one, other in (
        ("albedo against globe", albedo, globe),
        ("caps against globe", caps, globe),
        ("caps against albedo", caps, albedo),
    ):
        ratio = contrast(one, other)
        print("| %s | %.2f:1 | %s |"
              % (label, ratio,
                 "a difference in lightness" if ratio >= SHADING_RATIO
                 else "mostly a difference in hue"))
    print()
    ratio = contrast(albedo, globe)
    print("So the direction is right and the margin is thin. At %.2f:1 the" % ratio)
    print("albedo clears the globe in value but sits under the %.1f:1 at which"
          % SHADING_RATIO)
    print("a reader sees lightness rather than colour, and `cocoa_brown` is the")
    print("warmer and yellower of the two. At a glance the markings read as a")
    print("change of colour more than as darkness. Mars is required to keep")
    print("exactly these three filaments, so this is stated and not fixed.")
    print()

    print("## What the review renderer shows instead")
    print()
    print("`cad/scripts/render_review` applies its `_linear_to_srgb` to the")
    print("channels it is handed. The channels it is handed are already sRGB,")
    print("so every colour in `snap/` is encoded twice. The table below applies")
    print("that same encode to each sealed value.")
    print()
    print("| filament | sealed | as the review renderer shows it | luminance |")
    print("|---|---|---|---|")
    shown = {}
    for name in MARS:
        rgb = channels(P.FILAMENT_HEX[name])
        doubled = tuple(linear_to_srgb(channel) for channel in rgb)
        shown[name] = luminance(doubled)
        print("| `%s` | %s | %s | %.4f |"
              % (name, P.FILAMENT_HEX[name], as_hex(doubled), shown[name]))
    print()
    print("A double encode lifts a mid-tone hard and cannot lift a channel that")
    print("is already at 1.0, so `cocoa_brown` climbs from %.4f to %.4f while"
          % (albedo, shown["cocoa_brown"]))
    print("`red` only goes from %.4f to %.4f. In those images, and only in"
          % (globe, shown["red"]))
    print("those images, the albedo comes out **%s** than the globe."
          % ("lighter" if shown["cocoa_brown"] > shown["red"] else "darker"))
    print()
    print("This is a property of the review renderer, not of the product: the")
    print("sealed STEP carries the catalogue hex and nothing in `parts/` was")
    print("authored in linear light. It is recorded because an independent")
    print("reader of `snap/` measured the images right and would reasonably")
    print("conclude the wrong thing about the printed piece, and because every")
    print("visual judgement in this run was made on those same images.")
    print()
    print("## Verdict")
    print()
    if darker:
        print("Sealed: the albedo is darker than the globe, by a thin %.2f:1."
              % ratio)
        print("Shown in `snap/`: lighter, because those renders double-encode.")
        print("Both are stated so neither is mistaken for the other.")
    else:
        print("**The sealed albedo is not darker than the globe.**")
    print()
    print("Measured by `measure/filament_value.py` on `params.FILAMENT_HEX` and")
    print("on `render_review`'s own encode.")
    return 0 if darker else 1


if __name__ == "__main__":
    raise SystemExit(main())
