# Jupiter's three tones, measured

`ref/jupiter-sol.png` has three values, not two: a mid orange base,
darker belts, and bright cream zones between them. The build this
corrects had `orange` and `cocoa_brown` only, so the bright zones
were bare globe and the piece lost the alternating rhythm that makes
Jupiter legible. This is the measurement the third filament was
chosen on.

Luma is Rec. 709 on 0..255. The globe is `orange` #FF671F and the belts are
`cocoa_brown` #8E3C06; both are unchanged by this correction.

## The palette, on paper

| filament | sealed hex | sealed luma | as the render shows it | rendered luma |
|---|---|---|---|---|
| `orange` | #FF671F | 130.1 | #FFAA62 | 183.1 |
| `cocoa_brown` | #8E3C06 | 73.5 | #C5852A | 140.2 |
| `beige` | #F7E6DE | 233.0 | #FBF4F0 | 245.1 |
| `sunflower_yellow` | #FFB549 | 188.9 | #FFDB92 | 221.5 |
| `yellow` | #FFD834 | 212.5 | #FFED7D | 232.7 |
| `white` | #FFFEF7 | 253.7 | #FFFFFB | 254.4 |

`render_review` applies its own `_linear_to_srgb` to channels that
are already sRGB, so every image in `snap/` is encoded twice. That
lifts mid-tones hard and leaves the top end almost untouched, so a
dark tone separates *better* in the images than the sealed hex
suggests and a light one *worse*. `measure/filament-value.md` is
where that was first measured.

## The two numbers the Wish asks for, for every candidate

Measured on the rendered pixels, at each frame, with the zones
repainted between two otherwise identical renders.

| candidate | against | frame | pixels | mean | least | most |
|---|---|---|---:|---:|---:|---:|
| `beige` | the `orange` globe | hero | 107830 | **46.6** | 21.0 | 66.5 |
| `beige` | the `orange` globe | sheet | 90011 | **47.6** | 21.0 | 66.5 |
| `beige` | the `orange` globe | spot | 122113 | **44.7** | 21.0 | 66.5 |
| `beige` | the `cocoa_brown` belts | hero | 107830 | **78.4** | 35.9 | 108.5 |
| `beige` | the `cocoa_brown` belts | sheet | 90011 | **80.1** | 35.9 | 108.5 |
| `beige` | the `cocoa_brown` belts | spot | 122113 | **75.3** | 35.9 | 108.5 |
| `sunflower_yellow` | the `orange` globe | hero | 107830 | **28.8** | 12.6 | 41.7 |
| `sunflower_yellow` | the `orange` globe | sheet | 90011 | **29.5** | 12.6 | 41.7 |
| `sunflower_yellow` | the `orange` globe | spot | 122113 | **27.6** | 12.6 | 40.9 |
| `sunflower_yellow` | the `cocoa_brown` belts | hero | 107830 | **60.7** | 27.4 | 83.9 |
| `sunflower_yellow` | the `cocoa_brown` belts | sheet | 90011 | **62.0** | 27.4 | 83.9 |
| `sunflower_yellow` | the `cocoa_brown` belts | spot | 122113 | **58.2** | 27.4 | 83.5 |
| `yellow` | the `orange` globe | hero | 107830 | **37.3** | 17.1 | 53.7 |
| `yellow` | the `orange` globe | sheet | 90011 | **38.2** | 17.1 | 53.7 |
| `yellow` | the `orange` globe | spot | 122113 | **35.8** | 17.1 | 53.6 |
| `yellow` | the `cocoa_brown` belts | hero | 107830 | **69.2** | 31.2 | 95.9 |
| `yellow` | the `cocoa_brown` belts | sheet | 90011 | **70.7** | 31.2 | 95.9 |
| `yellow` | the `cocoa_brown` belts | spot | 122113 | **66.3** | 31.2 | 95.5 |
| `white` | the `orange` globe | hero | 107830 | **52.9** | 24.5 | 71.9 |
| `white` | the `orange` globe | sheet | 90011 | **53.9** | 24.5 | 71.8 |
| `white` | the `orange` globe | spot | 122113 | **51.0** | 24.5 | 71.9 |
| `white` | the `cocoa_brown` belts | hero | 107830 | **84.7** | 38.6 | 114.7 |
| `white` | the `cocoa_brown` belts | sheet | 90011 | **86.5** | 38.6 | 114.7 |
| `white` | the `cocoa_brown` belts | spot | 122113 | **81.5** | 38.6 | 114.7 |

## The decision, on one line each

| candidate | mean vs globe | mean vs belts | already in the set as |
|---|---:|---:|---|
| `beige` | 46.3 | 77.9 | Earth's dryland, Venus's highlands |
| `sunflower_yellow` | 28.6 | 60.3 | the Sol den plug and, since the Venus correction, Venus's whole globe |
| `yellow` | 37.1 | 68.7 | Saturn's globe |
| `white` | 52.6 | 84.2 | Sol discs, Anti-Sol numerals, Mercury's Caloris floor, Mars's caps, Earth's ice, Uranus's band, Neptune's streaks, Saturn's ring |

## What was chosen, and why

- **The zones are `beige` #F7E6DE.** It separates 46.3 luma levels
  from the `orange` globe and 77.9 from the `cocoa_brown` belts,
  averaged over the three frames. Both are clear: the thinnest
  marking separation anywhere in this set is the 20.2 `beige` makes
  on Venus's amber globe, and the separation this revision exists to
  replace as invisible is the 21.8 `dark_gray` made on Mercury's.
  It is also the reference's own tone: the bright zones in
  `ref/jupiter-sol.png` are a warm cream, not an amber and not a
  pure white.
- **`sunflower_yellow` was measured and refused.** At 28.6 against
  the globe it is the narrowest of the four -- it is an amber on an
  orange -- and it is the one filament in this set already carrying
  two jobs: the Sol den plug, and since the Venus correction the
  whole of Venus's globe. Giving it a third on the largest world in
  the set is what would have made Jupiter and Venus read as
  relatives. Because it was not taken, the Wish's hero-frame
  Jupiter-beside-Venus check is not required; the two globes stay
  `orange` and `sunflower_yellow`, which is where they already were.
- **`yellow` at 37.1 is Saturn's globe** and would have put Saturn's
  own colour on Jupiter's zones, one rank away on the ladder.
- **`white` at 52.6 measures furthest of the four** and was not
  taken. It is already the brightest feature on four other worlds --
  Mars's caps, Mercury's Caloris floor, Earth's ice and Saturn's
  ring -- and on the reference Jupiter's zones are cream rather than
  white. The gap between it and `beige` is 6.3 luma levels, which
  is what that choice cost, stated rather than hidden.
- **Jupiter now prints in four filaments** -- `orange`,
  `cocoa_brown`, `beige` and `red` -- where it printed in three.
  That ties it with Earth as the most expensive world in the set;
  Mercury, Mars, Venus, Neptune and Saturn take three and Uranus
  takes two. No new spool: all four were already loaded for this
  set, `beige` for Earth's dryland and Venus's highlands.

Measured by `measure/jupiter_tone_separation.py` on the exact solids
`parts/world.py` builds, through `cad/scripts/render_review`.
