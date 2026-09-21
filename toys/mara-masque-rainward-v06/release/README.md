# Rainward Emberfan

**You supply two ordinary six-sided dice and a cup each. Everything else is in
the box.** The dice can be any standard 1-6 cubes and the cups any ordinary
dice cups; nothing printed here replaces them, and no spinner, wheel or other
randomiser is substituted for them.

A printed backgammon set built as a small Sun. Twenty-four radial lanes in two
tones of orange fan out from a raised centre bar, and the rim is a crown of
forty-eight separate curled flames standing off the disc's own circular edge,
no two the same length. Thirty teardrop drops - fifteen cream, fifteen dark
brown - travel the lanes under the ordinary 1911 rules, which come with the set
in full in `RULES.md`.

## What arrives

| part | count | filament |
|---|---:|---|
| Sun board | 1 | orange |
| lane tile, light | 12 | yellow |
| lane tile, dark | 12 | cocoa brown |
| drop, stream A | 15 | beige |
| drop, stream B | 15 | dark brown |

Fifty-five printed parts. The board is 186.7 by 188.5 mm across the flames and
6.2 mm tall. Each lane tile drops into its own pocket in the board and is
located by a key on its underside; the tiles are separate parts so each point
carries its own tone.

## Playing

`RULES.md` carries the complete rules, the historical sources they come from,
and a rule-by-rule ledger of how each one is represented here. In short: take
the fifteen drops of one tone and a cup, set two, five, three and five drops on
your own 24, 13, 8 and 6 points, and race them home and off. Landing on a point
holding a single enemy drop sends it to the centre bar, and it must re-enter
before its owner moves anything else.

The four bank boundaries - 24/1, 6/7, 12/13 and 18/19 - are marked by four
engraved radial ticks on the centre bar top. The bar itself is flat and
unobstructed: a drop bridges a tick.

## Printing

Every part prints flat on its own underside with no support and no bridging.
Print the Sun board underside down, each lane tile top face down so its
locating key points up, and each drop on its flat bottom. The wall gate at a
0.4 mm nozzle and the overhang gate at 45 degrees pass on all fifty-five parts;
the reports are in `cad/measure/`.

**Print readiness is not claimed.** No print of this set has been made. Nothing
here claims physical handling, tile retention in its pocket, stack stability,
durability, or how anyone responds to it. Dice fairness is a property of the
dice you supply. Motion is unverified: the set has no moving mechanism and
motion checks are disabled for this run.

## What is in this tree

- `RULES.md` - the complete rules and their sources, carried byte for byte from
  the set this one corrects.
- `DESIGN.md` - what the correction changed, and every carried-over number as
  measured on the built geometry.
- `BLIND-REVIEWS.md` - one independent critic's reads, verbatim, over three
  rounds, and what became of each thing it flagged.
- `product.json` - the measured facts in machine-readable form.
- `assembled.step`, `assembled.step.json` - the whole set in its opening
  position, and the package that names each of the fifty-five occurrences.
- `parts/` - one printable solid per occurrence, named for the filament it
  prints in.
- `cad/` - the parametric source, its generated STEP files, the measurement
  scripts, every gate report, and the canonical renders under `cad/snap/`.
- `states/` - the exact STEP for each of the three demonstrated positions.
