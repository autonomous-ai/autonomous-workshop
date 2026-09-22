# Mars's three filaments, by value

## What the shop is sealed to show

`colors.py` seals the catalogue sRGB hex on every leaf part,
unconverted, which is what the Make contract asks for and what the
listing and the host renders read.

| filament | sealed hex | relative luminance |
|---|---|---|
| `red` | #FF0000 | 0.2126 |
| `cocoa_brown` | #8E3C06 | 0.0900 |
| `white` | #FFFEF7 | 0.9886 |

**The albedo is darker than the globe it sits in**, 0.0900 against 0.2126.

| pair | contrast ratio | reads as |
|---|---|---|
| albedo against globe | 1.88:1 | mostly a difference in hue |
| caps against globe | 3.96:1 | a difference in lightness |
| caps against albedo | 7.42:1 | a difference in lightness |

So the direction is right and the margin is thin. At 1.88:1 the
albedo clears the globe in value but sits under the 3.0:1 at which
a reader sees lightness rather than colour, and `cocoa_brown` is the
warmer and yellower of the two. At a glance the markings read as a
change of colour more than as darkness. Mars is required to keep
exactly these three filaments, so this is stated and not fixed.

## What the review renderer shows instead

`cad/scripts/render_review` applies its `_linear_to_srgb` to the
channels it is handed. The channels it is handed are already sRGB,
so every colour in `snap/` is encoded twice. The table below applies
that same encode to each sealed value.

| filament | sealed | as the review renderer shows it | luminance |
|---|---|---|---|
| `red` | #FF0000 | #FF0000 | 0.2126 |
| `cocoa_brown` | #8E3C06 | #C5852A | 0.2884 |
| `white` | #FFFEF7 | #FFFFFB | 0.9949 |

A double encode lifts a mid-tone hard and cannot lift a channel that
is already at 1.0, so `cocoa_brown` climbs from 0.0900 to 0.2884 while
`red` only goes from 0.2126 to 0.2126. In those images, and only in
those images, the albedo comes out **lighter** than the globe.

This is a property of the review renderer, not of the product: the
sealed STEP carries the catalogue hex and nothing in `parts/` was
authored in linear light. It is recorded because an independent
reader of `snap/` measured the images right and would reasonably
conclude the wrong thing about the printed piece, and because every
visual judgement in this run was made on those same images.

## Verdict

Sealed: the albedo is darker than the globe, by a thin 1.88:1.
Shown in `snap/`: lighter, because those renders double-encode.
Both are stated so neither is mistaken for the other.

Measured by `measure/filament_value.py` on `params.FILAMENT_HEX` and
on `render_review`'s own encode.
