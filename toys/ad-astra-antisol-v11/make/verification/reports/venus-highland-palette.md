# Is there a warmer highland tone in the palette?

Venus's globe is `sunflower_yellow` #FFB549: hue 35.6 degrees, saturation 0.71, luma
188.9 of 255. The Magellan reference's bright highland terrain
measures hue 38 at saturation 0.66 against a ground of hue 30 at
0.83 -- so on the real planet the bright terrain is **warmer and
yellower** than the ground. `beige` #F7E6DE is hue 19.2 at
saturation 0.10, which is **pinker and cooler** than this globe. The
relationship is inverted. This table is whether the shop stocks
anything that would put it the right way round.

| filament | stock | hex | hue | saturation | luma | brighter than the globe | warm 25-60 | chroma >= 0.20 |
|---|---|---|---:|---:|---:|---|---|---|
| `beige` | pla lite | #F7E6DE | 19.2 | 0.10 | 233.0 | yes | no | no |
| `black` | pla lite | #000000 | 0.0 | 0.00 | 0.0 | no | no | no |
| `blue` | pla lite | #004EA8 | 212.1 | 1.00 | 67.9 | no | no | yes |
| `cocoa_brown` | pla lite | #8E3C06 | 23.8 | 0.96 | 73.5 | no | no | yes |
| `cyan` | pla lite | #00FFFF | 180.0 | 1.00 | 200.8 | yes | no | yes |
| `dark_beige` | petg basic | #DBC8B6 | 29.2 | 0.17 | 202.7 | yes | yes | no |
| `dark_brown` | petg basic | #4F2C1D | 18.0 | 0.63 | 50.4 | no | no | yes |
| `dark_gray` | pla lite | #6F6E6D | 30.0 | 0.02 | 110.1 | no | yes | no |
| `gray` | pla lite | #9FA19F | 120.0 | 0.01 | 160.4 | no | no | no |
| `green` | pla lite | #00BB31 | 135.7 | 1.00 | 137.3 | no | no | yes |
| `misty_blue` | petg basic | #688197 | 208.1 | 0.31 | 125.3 | no | no | yes |
| `navy_blue` | petg basic | #0086D6 | 202.4 | 1.00 | 111.3 | no | no | yes |
| `orange` | pla lite | #FF671F | 19.3 | 0.88 | 130.1 | no | no | yes |
| `pine_green` | petg basic | #034638 | 167.5 | 0.96 | 54.7 | no | no | yes |
| `red` | pla lite | #FF0000 | 0.0 | 1.00 | 54.2 | no | no | yes |
| `reflex_blue` | petg basic | #001489 | 231.2 | 1.00 | 24.2 | no | no | yes |
| `sunflower_yellow` | pla lite | #FFB549 | 35.6 | 0.71 | 188.9 | no | yes | yes |
| `white` | pla lite | #FFFEF7 | 52.5 | 0.03 | 253.7 | yes | yes | no |
| `yellow` | pla lite | #FFD834 | 48.5 | 0.80 | 212.5 | yes | yes | yes |

## The answer

**`yellow` satisfies all three.** Each is examined below.

- **`yellow` #FFD834** is brighter, warm and chromatic on paper. It is
  not taken for two measured reasons. It separates only 23.5 luma
  levels from the globe on the sealed channels, against `beige`'s
  44.1 -- and in the canonical render, where the separation that
  matters was measured on the pixels themselves, it comes to 9.6
  against `beige`'s 20.2, the weakest marking separation anywhere
  in this set. And it is Saturn's own globe filament, so Venus's
  highlands would be the same plastic as the globe of the world
  this revision is separately required to keep Venus distinct
  from. `measure/venus-tone-separation.md` and
  `measure/venus-saturn-separation.md` are those two measurements.

`dark_beige` #DBC8B6 is the nearest miss and is worth naming: hue
29.2 at saturation 0.17, warm but barely chromatic, and 13.8 luma
levels from the globe against `beige`'s 44.1, so it would be harder
to see, not easier. It is also PETG where this set is entirely PLA,
which would break the set's own rule that the whole thing prints in
one material family on one machine, and it would be a fourteenth
filament.

`white` #FFFEF7 separates furthest of all at 64.8, and it is the one
the reviewer's complaint applies to *most*: at saturation 0.03 it is
the least chromatic thing in the palette.

## What this build did

It kept `beige`, which the Wish names, and records the objection
rather than burying it. Given the palette, `beige` is also the best
available answer on the measure that decides whether a marking can
be seen at all: of the tones brighter than the globe it separates
second furthest, and the one that separates further is less
chromatic still. The reviewer is right that the hue relationship is
inverted relative to the reference, and this set cannot put it right
with the plastics it can buy.

Measured by `measure/venus_highland_palette.py` on the exact
catalogue hex in `cad/scripts/cadfilament.py`.
