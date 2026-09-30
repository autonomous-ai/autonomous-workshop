# Venus's three tones, measured

The reference `ref/venus-radar-surface.png` has three values: mid
amber plains, brighter rough highlands and darker smooth lowlands.
The globe carries the mid tone, so the markings need one filament
above it and one below, and this is the measurement those two were
chosen on.

Luma is Rec. 709 on 0..255. The globe is `sunflower_yellow` #FFB549.

## The palette, on paper

| filament | sealed hex | sealed luma | as the render shows it | rendered luma |
|---|---|---|---|---|
| `sunflower_yellow` | #FFB549 | 188.9 | #FFDB92 | 221.5 |
| `beige` | #F7E6DE | 233.0 | #FBF4F0 | 245.1 |
| `white` | #FFFEF7 | 253.7 | #FFFFFB | 254.4 |
| `yellow` | #FFD834 | 212.5 | #FFED7D | 232.7 |
| `cocoa_brown` | #8E3C06 | 73.5 | #C5852A | 140.2 |
| `dark_gray` | #6F6E6D | 110.1 | #B0AFAF | 175.6 |
| `black` | #000000 | 0.0 | #000000 | 0.0 |

`render_review` applies its own `_linear_to_srgb` to channels that
are already sRGB, so every image in `snap/` is encoded twice. That
lifts mid-tones hard and leaves the top end almost untouched, so a
dark tone separates *better* in the images than the sealed hex
suggests and a light one *worse*. `measure/filament-value.md` is
where that was first measured.

## The three numbers the Wish asks for

Measured on the rendered pixels, at each frame, with one region
repainted between two otherwise identical renders.

| separation | frame | pixels | mean | least | most |
|---|---|---|---|---|---|
| highland `beige` against the globe | hero | 17425 | **20.2** | 10.7 | 25.6 |
| lowland `cocoa_brown` against the globe | hero | 3409 | **33.3** | 28.4 | 39.9 |
| lowland against highland | hero | 3409 | **43.0** | 37.0 | 51.9 |
| highland `beige` against the globe | sheet | 18090 | **20.2** | 9.7 | 25.6 |
| lowland `cocoa_brown` against the globe | sheet | 1656 | **33.2** | 27.4 | 51.2 |
| lowland against highland | sheet | 1656 | **42.9** | 35.9 | 66.3 |
| highland `beige` against the globe | aphrodite | 17506 | **20.2** | 10.5 | 25.6 |
| lowland `cocoa_brown` against the globe | aphrodite | 3912 | **34.0** | 28.4 | 40.7 |
| lowland against highland | aphrodite | 3912 | **43.9** | 37.1 | 52.9 |

- highland `beige` against the globe: 20.2 at the hero frame, 20.2 at the sheet frame, 20.2 at the aphrodite frame.
- lowland `cocoa_brown` against the globe: 33.3 at the hero frame, 33.2 at the sheet frame, 34.0 at the aphrodite frame.
- lowland against highland: 43.0 at the hero frame, 42.9 at the sheet frame, 43.9 at the aphrodite frame.

## Does the darker tone swamp the globe?

This is the question the Wish reserves judgement on, so it is
answered with the same measurement applied to the two filaments
darker than `cocoa_brown` in the palette.

| candidate | frame | pixels | mean separation from the globe | least | most |
|---|---|---|---|---|---|
| `cocoa_brown` | hero | 3409 | **33.3** | 28.4 | 39.9 |
| `cocoa_brown` | sheet | 1656 | **33.2** | 27.4 | 51.2 |
| `cocoa_brown` | aphrodite | 3912 | **34.0** | 28.4 | 40.7 |
| `dark_gray` | hero | 3409 | **18.9** | 15.9 | 23.0 |
| `dark_gray` | sheet | 1656 | **18.9** | 15.7 | 29.4 |
| `dark_gray` | aphrodite | 3912 | **19.3** | 15.9 | 23.2 |
| `black` | hero | 3409 | **90.5** | 78.7 | 108.3 |
| `black` | sheet | 1656 | **90.3** | 75.7 | 139.6 |
| `black` | aphrodite | 3912 | **92.5** | 78.9 | 111.2 |

| candidate | mean across the three frames | against `black` |
|---|---|---|
| `cocoa_brown` | 33.5 | 37% of the way to a hole in the print |
| `dark_gray` | 19.0 | 21% of the way to a hole in the print |
| `black` | 91.1 | 100% of the way to a hole in the print |

## The brighter tone

| candidate | frame | pixels | mean separation from the globe | least | most |
|---|---|---|---|---|---|
| `beige` | hero | 17425 | **20.2** | 10.7 | 25.6 |
| `beige` | sheet | 18090 | **20.2** | 9.7 | 25.6 |
| `beige` | aphrodite | 17506 | **20.2** | 10.5 | 25.6 |
| `white` | hero | 17425 | **27.9** | 15.0 | 33.3 |
| `white` | sheet | 18090 | **27.9** | 14.0 | 33.3 |
| `white` | aphrodite | 17506 | **28.0** | 14.8 | 33.4 |
| `yellow` | hero | 17425 | **9.6** | 5.0 | 12.1 |
| `yellow` | sheet | 18090 | **9.6** | 4.4 | 12.1 |
| `yellow` | aphrodite | 17506 | **9.6** | 5.0 | 12.1 |

## What was chosen, and what it cost

- **Highlands: `beige` #F7E6DE.** The Wish's intended answer, and it
  is taken. The number is reported plainly rather than softened: at
  20.2 luma levels it is the *thinnest* marking separation anywhere
  in this set, and it is below the 21.8 that `dark_gray` managed on
  Mercury's globe -- the separation that revision exists to replace
  as invisible. Two things make it read here where that one did not,
  and both are in the evidence rather than in the argument. The first
  is area: Aphrodite Terra covers about 17,400 pixels of a 900-pixel
  frame, a band running limb to limb, where Mercury's plains were
  separate patches a few millimetres across. The second is hue --
  `beige` is a pink-cream and the globe is an amber, so the boundary
  carries a colour step that luma does not count.
  `snap/worlds/venus-<side>-aphrodite.png` is where that claim is
  checked, and it is what the blind review was shown.
- **`white` was measured and not taken.** It separates 27.9, some
  7.7 levels further, and it is the brighter tone the reference's
  highlands arguably deserve. It was not taken because the Wish names
  `beige` and because `white` is already the brightest feature on
  three other worlds in this set -- Mars's caps, Mercury's Caloris
  floor and Earth's ice -- so Venus in `beige` is the one that stays
  its own colour. `yellow` at 9.6 is not a candidate at all.
- **Lowlands: `cocoa_brown` #8E3C06, on all three plains.** The Wish
  reserved the right to cut the two smaller plains if this tone
  swamped the globe, and measured, it does not: 33.5 luma levels
  against the amber, which is 37 per cent of the step `black` makes
  and close to the 45.5 `cocoa_brown` makes against Mercury's gray.
  `black` at 91.1 is the one that would read as a hole in the print.
  So **Atalanta, Guinevere and Lavinia are all drawn**, and none was
  dropped. `dark_gray` at 19.0 is the tone that would have vanished.
- **Venus now prints in three filaments** -- `sunflower_yellow`,
  `beige` and `cocoa_brown` -- where it printed in two. That is the
  set's ordinary number: Earth takes four, Mercury, Mars, Neptune,
  Saturn, Jupiter and now Venus take three, and Uranus alone takes
  two. No new spool: all three were already loaded for this set.

Measured by `measure/venus_tone_separation.py` on the exact solids
`parts/world.py` builds, through `cad/scripts/render_review`.
