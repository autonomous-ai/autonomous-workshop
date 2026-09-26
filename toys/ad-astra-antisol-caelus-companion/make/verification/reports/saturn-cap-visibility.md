# Saturn's bright cap: one army shows it, the other hides it

The cap is on the north only, above +58 degrees, because the
reference brightens toward the north pole and says nothing about the
south. Saturn's obliquity is 26.73 degrees and a Sol world leans its
north pole toward +X while its Anti-Sol mirror leans it toward -X, so
at the product's own camera the cap is in plain view on one piece and
all but gone on the other. **That is the lean that already
distinguishes the two armies, not a mirror failure**, and this report
exists so that a later reader does not have to take that on trust.

## The two pieces are the same piece, leaning the other way

Every colour body of the two pieces, compared role by role on solid
count, exact volume and x bounds. Two of the seven are *meant* to
differ and are named first, because they are the set's own ownership
cue rather than a fault:

- the **disc**: a Sol disc flares outward as it rises (Ø33.00 bottom to
  Ø34.00 top) and an Anti-Sol disc tapers inward (Ø34.00 to Ø33.00), so
  the two are different solids by design and carry different colours,
  `white` against `black`;
- the **numeral**: the same digit in the same place, in `black` on the
  Sol piece and `white` on the Anti-Sol one.

Everything else is the same description built twice.

| role | Sol filament | Anti filament | solids | Sol volume mm3 | Anti volume mm3 | difference | of the role |
|---|---|---|---:|---:|---:|---:|---:|
| `disc` | `white` | `black` | 1 | 4393.336636 | 4397.326696 | 3.99e+00 | 0.0908% |
| `numeral` | `black` | `white` | 4 | 3.784015 | 3.784014 | 1.50e-06 | 0.0000% |
| `globe` | `yellow` | `yellow` | 1 | 8231.817012 | 8231.919818 | 1.03e-01 | 0.0012% |
| `bands` | `sunflower_yellow` | `sunflower_yellow` | 4 | 534.066095 | 534.065135 | 9.60e-04 | 0.0002% |
| `southbelt` | `cocoa_brown` | `cocoa_brown` | 1 | 299.512270 | 299.437865 | 7.44e-02 | 0.0248% |
| `cap` | `white` | `white` | 1 | 176.300253 | 176.298832 | 1.42e-03 | 0.0008% |
| `ring` | `white` | `white` | 1 | 574.192167 | 574.192096 | 7.11e-05 | 0.0000% |

| role | Sol x bounds | Anti x bounds | departure from an x mirror |
|---|---|---|---:|
| `disc` | -16.9370 .. 16.9370 | -17.0000 .. 17.0000 | 6.30e-02 |
| `numeral` | -1.4000 .. 1.4000 | -1.4000 .. 1.4000 | 1.73e-14 |
| `globe` | -12.9347 .. 12.9200 | -12.9200 .. 12.9712 | 3.65e-02 |
| `bands` | -12.7493 .. 13.0000 | -13.0000 .. 12.7493 | 1.78e-15 |
| `southbelt` | -13.0000 .. 10.1058 | -9.7425 .. 13.0000 | 3.63e-01 |
| `cap` | -1.1940 .. 11.1115 | -11.1115 .. 1.1940 | 2.95e-13 |
| `ring` | -13.7119 .. 13.7119 | -13.7119 .. 13.7119 | 0.00e+00 |

### The one difference that is neither designed nor noise

`globe` and `southbelt` differ by 1.03e-01 and 7.44e-02 mm3 -- 0.0012% and
0.0248% of their own volume -- where every other marking agrees to
better than 2e-03. That is not kernel noise and it has one cause,
which is measured here rather than guessed at.

The globe is cut flat where it enters the disc, at Z = 5.00, which is
piece latitude -57.80 degrees. A planet-frame point sits lowest in the
piece at the meridian the piece leans along, where its piece latitude
is its planet latitude minus the 26.73 degree obliquity -- so any
marking that reaches below planet latitude -31.07 degrees is buried by
the disc at that meridian. **And the lean meridian is longitude 0 on
the Sol piece and longitude 180 on the Anti-Sol one.**

| | longitude 0 (the Sol lean meridian) | longitude 180 (the Anti-Sol one) |
|---|---:|---:|
| `stb` wave on the south boundary | -0.509 deg | -2.479 deg |
| south boundary latitude | -30.509 | -32.479 |
| below the -31.07 burial line by | nothing, it is 0.556 deg clear | 1.413 deg |

So the Anti-Sol piece buries 0.074 mm3 more of its widest southern
band inside its own disc than the Sol piece does, and its globe keeps
0.103 mm3 more in consequence. It is the same band drawn from the same
five numbers with the same wave; what differs is which part of it the
disc hides, and the disc hides it at the bottom of the globe where
the ball enters its own base. Nothing above the seat line differs on
either piece. The four light bands, which include the other wavy one,
agree to 9.60e-04 mm3 and their x bounds mirror to 2e-15 mm.

This is stated rather than removed. Narrowing the wave until it
cleared the burial line on both meridians would have meant a
different amplitude on one boundary of one band, which is a visible
change made to hide an invisible one.

## Where the pole points, frame by frame

The dot product of the planet's own north pole against the view axis.
+1 is the pole straight at the lens, 0 is the pole square across the
picture, -1 is the pole straight away.

| frame | azimuth | elevation | Sol pole . view | Anti pole . view |
|---|---:|---:|---:|---:|
| hero | -55 | 22 | **+0.574** | **+0.095** |
| state sheet | -45 | 35.264 | **+0.775** | **+0.256** |
| quarter | -55 | 20 | **+0.548** | **+0.063** |
| ring plane | -90 | 0 | **+0.000** | **-0.000** |
| down the sol pole | 0 | 63.27 | **+1.000** | --  |
| down the anti pole | 180 | 63.27 | -- | **+1.000**  |

## How many pixels of the cap each frame actually shows

Counted rather than predicted: the piece is rendered twice at each
frame with the cap repainted to the globe's own filament and nothing
else altered, and the pixels that move are the cap's. Frames are 700
pixels square.

| frame | Sol cap pixels | Anti cap pixels | Anti as a share of Sol |
|---|---:|---:|---:|
| hero | **29333** | **8882** | 30% |
| state sheet | **36220** | **13090** | 36% |
| quarter | **28246** | **8030** | 28% |
| ring plane | **6356** | **6308** | 99% |
| down its OWN north pole | **42908** | **41874** | 97.6% |

Two things to read off that table, both stated exactly rather than
rounded.

**The Wish's expectation is very nearly what happens, and the
remaining difference is worth naming.** At the hero frame the Sol
piece shows its cap over 29333 pixels and the Anti-Sol piece over 8882 --
30 per cent as much. The Anti-Sol cap is not gone: its pole stands
+0.095 against the view axis, a few degrees off square, so what
survives is a thin crescent along the upper limb rather than a region
on the face of the ball. Called what it is: on the Sol piece the
bright cap is something you look at, and on the Anti-Sol piece it is
an edge you notice. It is not hidden completely at any frame the
product is photographed from, and this report says so rather than
repeating the expectation.

**Each piece's own polar frame shows its own cap, and shows the same
amount of it** -- 42908 pixels against 41874, 2.41 per cent apart. That is
the mirror stated again in pixels: the cap is on both pieces and it
is the same cap. What differs at a shared camera is only which way
the piece leans.

Measured by `measure/saturn_cap_visibility.py` on the exact solids
`parts/world.py` builds, through `cad/scripts/render_review`.
