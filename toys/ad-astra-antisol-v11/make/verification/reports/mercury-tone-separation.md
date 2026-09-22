# Mercury's tones, measured

Mercury's globe is Ø13.78 mm, the smallest in the set. The question
this answers is which filaments a reader of the product images can
actually tell apart on a ball that size, and the answer is measured
three ways: on the sealed channels, on those channels as the review
renderer encodes them, and on the rendered pixels themselves.

Luma is Rec. 709 on 0..255. The globe is `gray` #9FA19F.

## The palette, on paper

| filament | sealed hex | sealed luma | as the render shows it | rendered luma |
|---|---|---|---|---|
| `gray` | #9FA19F | 160.4 | #CFD0CF | 207.8 |
| `dark_gray` | #6F6E6D | 110.1 | #B0AFAF | 175.6 |
| `cocoa_brown` | #8E3C06 | 73.5 | #C5852A | 140.2 |
| `black` | #000000 | 0.0 | #000000 | 0.0 |
| `beige` | #F7E6DE | 233.0 | #FBF4F0 | 245.1 |
| `white` | #FFFEF7 | 253.7 | #FFFFFB | 254.4 |

The render column is not decoration. `render_review` applies its own
`_linear_to_srgb` to channels that are already sRGB, so every image in
`snap/` is encoded twice, which lifts the mid-tones hard and leaves the
top end almost untouched. A dark tone therefore separates *better* in
the images than the sealed hex suggests, and a light one *worse*.
`measure/filament-value.md` is where that was first measured.

## The terrain tone: what the set carried, and what replaces it

The seven smooth plains and the Caloris rim are one tone. It has to
read as rock on a small gray ball: dark enough to separate, not so
dark that it reads as a gap in the print.

### Measured at the hero frame (azimuth -55, elevation 22)

| candidate | region | pixels | mean separation | least | most |
|---|---|---|---|---|---|
| `dark_gray` | plains | 10240 | **21.8** | 12.0 | 28.7 |
| `dark_gray` | caloris_rim | 5271 | **33.5** | 30.5 | 36.5 |
| `cocoa_brown` | plains | 10240 | **45.5** | 25.3 | 60.4 |
| `cocoa_brown` | caloris_rim | 5271 | **69.8** | 63.2 | 74.8 |
| `black` | plains | 10240 | **139.6** | 77.0 | 184.7 |
| `black` | caloris_rim | 5271 | **214.2** | 194.7 | 228.7 |

### Measured at the sheet frame (azimuth -45, elevation 35.264)

| candidate | region | pixels | mean separation | least | most |
|---|---|---|---|---|---|
| `dark_gray` | plains | 11216 | **22.0** | 11.0 | 29.5 |
| `dark_gray` | caloris_rim | 5299 | **33.6** | 29.7 | 36.5 |
| `cocoa_brown` | plains | 11216 | **45.9** | 22.6 | 61.6 |
| `cocoa_brown` | caloris_rim | 5299 | **70.0** | 63.1 | 75.8 |
| `black` | plains | 11216 | **141.0** | 71.0 | 188.7 |
| `black` | caloris_rim | 5299 | **214.7** | 193.7 | 230.7 |

## The Caloris floor

The floor is the brightest thing on the reference, brighter than the
globe, and the only stocked filaments lighter than `gray` are these
two. The boundary a reader actually reads is the floor against the
rim around it rather than against the globe, so both are measured.

### Measured at the hero frame (azimuth -55, elevation 22)

| candidate | against | pixels | mean separation | least | most |
|---|---|---|---|---|---|
| `beige` | the gray globe | 2693 | **35.3** | 29.3 | 38.6 |
| `white` | the gray globe | 2693 | **36.9** | 29.3 | 45.2 |

### Measured at the sheet frame (azimuth -45, elevation 35.264)

| candidate | against | pixels | mean separation | least | most |
|---|---|---|---|---|---|
| `beige` | the gray globe | 2711 | **34.9** | 28.3 | 38.6 |
| `white` | the gray globe | 2711 | **36.7** | 28.3 | 46.1 |

Against the rim, on the sealed channels and as rendered:

| pair | sealed | as rendered |
|---|---|---|
| `beige` against `cocoa_brown` | 159.5 | 104.9 |
| `white` against `cocoa_brown` | 180.2 | 114.3 |
| `beige` against `white` | 20.7 | 9.4 |

The last row is the set's known weak pair, and it is why the Earth
reviewer could not reliably tell beige from white. Only one of the
two is used on Mercury, so that pair never occurs here.

## What was chosen

- **Terrain: `cocoa_brown`.** It is the darkest tone in the palette
  that still reads as rock. `black` separates further on every
  measure above and was not taken: a black patch on a 13.78 mm gray
  ball reads as a hole in the print rather than as terrain, and the
  reference's darkest terrain is a mid grey-brown, not black.
- **Caloris floor: `white`.** It separates further than `beige` from
  the globe on every measure above, and Mercury spends a third
  filament to have it.

What it cost is in `README.md` and in the product limitations:
Mercury now prints in three filaments rather than two, and
`cocoa_brown` is a warm brown rather than a neutral grey, so Mercury's
plains are the same family of colour as Mars's albedo and Jupiter's
and Saturn's bands. That is a real cost and it was paid deliberately:
the neutral alternative, `dark_gray`, is the tone this correction
exists to replace.

Measured by `measure/mercury_tone_separation.py` on the exact solids
`parts/world.py` builds, through `cad/scripts/render_review`.
