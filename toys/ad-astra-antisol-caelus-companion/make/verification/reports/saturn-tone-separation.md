# Saturn's tones, measured

`ref/saturn-sol.png` is the softest image in the reference set: a
cream-to-pale-tan globe whose bands are wide, soft-edged and low in
contrast, whose strongest band is barely darker than its neighbours,
and whose northern part is lighter than its southern. The build this
corrects wore four `cocoa_brown` bands on a `yellow` globe -- one of
the highest-contrast pairings in the palette -- so it read as a
hard-striped gold ball. This is the measurement the replacement tone
was chosen on.

Luma is Rec. 709 on 0..255. The globe is `yellow` #FFD834 and is unchanged by
this correction, as is the `white` #FFFEF7 ring.

## The palette, on paper

| filament | sealed hex | sealed luma | as the render shows it | rendered luma |
|---|---|---|---|---|
| `yellow` | #FFD834 | 212.5 | #FFED7D | 232.7 |
| `sunflower_yellow` | #FFB549 | 188.9 | #FFDB92 | 221.5 |
| `beige` | #F7E6DE | 233.0 | #FBF4F0 | 245.1 |
| `white` | #FFFEF7 | 253.7 | #FFFFFB | 254.4 |
| `cocoa_brown` | #8E3C06 | 73.5 | #C5852A | 140.2 |

`render_review` applies its own `_linear_to_srgb` to channels that
are already sRGB, so every image in `snap/` is encoded twice. That
lifts mid-tones hard and leaves the top end almost untouched, so a
dark tone separates *better* in the images than the sealed hex
suggests and a light one *worse*. `measure/filament-value.md` is
where that was first measured, and it is why the light candidates
below measure so much closer than their sealed hex suggests: the
`yellow` globe is already near the top of the encode.

## The numbers the Wish asks for

Measured on the rendered pixels, at each frame, with one region
repainted between two otherwise identical renders.

| separation | on | frame | pixels | mean | least | most |
|---|---|---|---:|---:|---:|---:|
| `sunflower_yellow` against the `yellow` globe | `bands` | hero | 102049 | **9.5** | 3.7 | 12.7 |
| `sunflower_yellow` against the `yellow` globe | `bands` | sheet | 98177 | **9.3** | 3.7 | 12.7 |
| `sunflower_yellow` against the `yellow` globe | `bands` | quarter | 102292 | **9.4** | 3.7 | 12.7 |
| `beige` against the `yellow` globe | `bands` | hero | 102049 | **10.1** | 3.9 | 13.7 |
| `beige` against the `yellow` globe | `bands` | sheet | 98177 | **10.0** | 4.0 | 14.4 |
| `beige` against the `yellow` globe | `bands` | quarter | 102292 | **10.1** | 4.0 | 14.4 |
| `white` against the `yellow` globe | `bands` | hero | 102049 | **16.8** | 7.4 | 22.0 |
| `white` against the `yellow` globe | `bands` | sheet | 98177 | **16.5** | 7.4 | 22.0 |
| `white` against the `yellow` globe | `bands` | quarter | 102292 | **16.9** | 7.4 | 22.0 |
| `cocoa_brown` against the `yellow` globe | `southbelt` | hero | 9964 | **41.3** | 31.4 | 52.6 |
| `cocoa_brown` against the `yellow` globe | `southbelt` | sheet | 1469 | **35.7** | 32.0 | 41.9 |
| `cocoa_brown` against the `yellow` globe | `southbelt` | quarter | 10587 | **41.5** | 31.4 | 52.8 |
| `cocoa_brown` against the `sunflower_yellow` bands | `southbelt` | hero | 9964 | **36.2** | 27.6 | 46.3 |
| `cocoa_brown` against the `sunflower_yellow` bands | `southbelt` | sheet | 1469 | **31.3** | 28.2 | 36.8 |
| `cocoa_brown` against the `sunflower_yellow` bands | `southbelt` | quarter | 10587 | **36.4** | 27.6 | 46.5 |
| `cocoa_brown` against `beige` bands | `southbelt` | hero | 9964 | **46.8** | 35.4 | 59.8 |
| `cocoa_brown` against `beige` bands | `southbelt` | sheet | 1469 | **40.5** | 36.1 | 47.6 |
| `cocoa_brown` against `beige` bands | `southbelt` | quarter | 10587 | **47.1** | 36.0 | 59.8 |
| the `white` cap against the `yellow` globe | `cap` | hero | 48495 | **16.1** | 8.4 | 22.0 |
| the `white` cap against the `yellow` globe | `cap` | sheet | 59854 | **15.7** | 8.4 | 22.0 |
| the `white` cap against the `yellow` globe | `cap` | quarter | 46703 | **16.1** | 8.4 | 22.0 |
| a `beige` cap against the `yellow` globe | `cap` | hero | 48495 | **11.2** | 8.4 | 14.5 |
| a `beige` cap against the `yellow` globe | `cap` | sheet | 59854 | **11.0** | 8.4 | 14.5 |
| a `beige` cap against the `yellow` globe | `cap` | quarter | 46703 | **11.2** | 8.1 | 14.5 |

| separation | mean across the three frames |
|---|---:|
| `sunflower_yellow` against the `yellow` globe | **9.4** |
| `beige` against the `yellow` globe | **10.1** |
| `white` against the `yellow` globe | **16.7** |
| `cocoa_brown` against the `yellow` globe | **39.5** |
| `cocoa_brown` against the `sunflower_yellow` bands | **34.7** |
| `cocoa_brown` against `beige` bands | **44.8** |
| the `white` cap against the `yellow` globe | **16.0** |
| a `beige` cap against the `yellow` globe | **11.2** |

## The reference points this set already has

A luma number means nothing on its own, so here are the separations
this set has already measured and already judged.

| separation | measured | the judgement that was made on it |
|---|---:|---|
| `dark_gray` on Mercury's gray globe | 21.8 | invisible; the Mercury correction exists to replace it |
| `beige` on Venus's amber globe | 20.2 | the thinnest in the set, kept, and it reads |
| `beige` on Jupiter's orange globe | 30.5 | clear |
| `cocoa_brown` on Venus's amber globe | 33.5 | clear, and not swamping |
| `cocoa_brown` on Mercury's gray globe | 45.5 | clear |
| `black` on Venus's amber globe | 91.1 | reads as a hole in the print |

## The dark band, as a picture

The Wish allows one darker band, `cocoa_brown`, at -14/-30, and only
if it measures as distinguishable without dominating. Distinguishable
is a number and it is above. Dominating is not, so it is rendered:

- `snap/worlds/saturn-dark-band-kept.png` -- the piece as built, with the one darker band;
- `snap/worlds/saturn-dark-band-dropped.png` -- the same piece with that band in the
  band filament, so the only thing that differs between the two
  images is whether the band is dark.

Those two are the Sol piece, and on the Sol piece the answer is easy
because the band is at -14/-30 and the Sol piece leans its north pole
toward the lens: most of that band is below the ring and near the
lower limb. **The Anti-Sol piece is the hard case and it is the one
that has to be looked at**, because the opposite lean brings the same
band round to the middle of the visible face. So the same pair is
rendered on that army too:

- `snap/worlds/saturn-dark-band-kept-anti.png` -- the Anti-Sol piece as built;
- `snap/worlds/saturn-dark-band-dropped-anti.png` -- the same piece with the band in the
  band filament.

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

## The cap, as a picture

The same question is asked of the bright northern region. `white` is
the lightest tone this piece already carries -- it is the ring -- and
`beige` is the next one down. Requirement 3 asks for *a wide soft
brightening on an already light globe*, so soft is the test and it is
rendered rather than argued:

- `snap/worlds/saturn-cap-white.png` -- the cap in `white` #FFFEF7;
- `snap/worlds/saturn-cap-beige.png` -- the cap in `beige` #F7E6DE.

