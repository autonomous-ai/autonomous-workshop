# Saturn's surface, against the 0.4 mm nozzle

Saturn's globe is Ø26.00 mm, so one degree of arc is 0.2269 mm and the
0.4 mm nozzle is 1.76 degrees of it. Every number below is an arc
along the globe's own surface, which is what the slicer lays down;
none of them is a chord or a projected width.

## The five bands

| band | latitudes | drawn | width deg | width mm | nozzle widths |
|---|---|---|---:|---:|---:|
| North Polar Band (`npb`) | +46 to +55 | plain band | 9.0 | **2.04** | 5.1 |
| North Temperate Band (`ntb`) | +18 to +33 | wavy outline | 15.0 | **3.40** | 8.5 |
| Equatorial Band (`eqb`) | +2 to +10 | plain band | 8.0 | **1.82** | 4.5 |
| South Temperate Belt (`stb`) | -30 to -14 | wavy outline | 16.0 | **3.63** | 9.1 |
| South South Band (`ssb`) | -50 to -38 | plain band | 12.0 | **2.72** | 6.8 |

The narrowest is the Equatorial Band at 8.0 degrees, **1.82 mm**, 4.5 nozzle
widths. Nothing here is close to the nozzle.

## What the wave does to the two widest

Each wavy boundary carries two harmonics totalling 2.5 degrees, so a
band's width breathes as the two boundaries move independently. The
worst case is what has to print, so it is swept over the whole globe
at a tenth of a degree rather than taken at the drawn latitudes.

| band | drawn width | narrowest | widest | narrowest mm | nozzle widths |
|---|---:|---:|---:|---:|---:|
| North Temperate Band | 15.0 | **10.53** | 19.21 | **2.39** | 6.0 |
| South Temperate Belt | 16.0 | **11.89** | 18.98 | **2.70** | 6.7 |

## The gaps between markings

Bare globe has to print too: a gap under the nozzle is a colour
boundary the slicer cannot resolve. Wavy boundaries are taken at
their extreme excursion toward the neighbour, not at their drawn
latitude.

| from | to | gap deg | gap mm | nozzle widths |
|---|---|---:|---:|---:|
| South South Band | South Temperate Belt | 5.50 | **1.25** | 3.1 |
| South Temperate Belt | Equatorial Band | 13.63 | **3.09** | 7.7 |
| Equatorial Band | North Temperate Band | 5.58 | **1.27** | 3.2 |
| North Temperate Band | North Polar Band | 10.87 | **2.47** | 6.2 |
| North Polar Band | the bright cap at +58 | 3.00 | **0.68** | 1.7 |

The tightest gap on this globe is the 3.00 degrees, **0.68 mm**,
between North Polar Band and the bright cap -- 1.7 nozzle widths of bare globe.

## The rings

Each wavy band is 6 longitude sectors of 60 degrees, sampled every
6 degrees of longitude, walked south boundary west to east and
north boundary back. Neighbouring sectors share their seam vertices
exactly, so the radial plane each throws is one plane for both and
the lenses fuse into one annulus along an ordinary flat face.

| ring | vertices | shortest edge deg | shortest edge mm | narrowest neck mm |
|---|---:|---:|---:|---:|
| `ntb_sector1` | 22 | 4.908 | **1.114** | **2.781** |
| `ntb_sector2` | 22 | 4.989 | **1.132** | **3.105** |
| `ntb_sector3` | 22 | 5.054 | **1.147** | **2.963** |
| `ntb_sector4` | 22 | 4.908 | **1.114** | **3.343** |
| `ntb_sector5` | 22 | 4.989 | **1.132** | **3.468** |
| `ntb_sector6` | 22 | 5.054 | **1.147** | **2.399** |
| `stb_sector1` | 22 | 5.112 | **1.160** | **3.123** |
| `stb_sector2` | 22 | 5.109 | **1.159** | **3.819** |
| `stb_sector3` | 22 | 5.126 | **1.163** | **2.704** |
| `stb_sector4` | 22 | 5.205 | **1.181** | **3.270** |
| `stb_sector5` | 22 | 5.062 | **1.149** | **3.296** |
| `stb_sector6` | 22 | 5.203 | **1.181** | **3.307** |

The shortest ring edge anywhere on this globe is 4.908 degrees,
**1.114 mm**, on `ntb_sector4`. This set holds a ring edge to 0.50 mm -- a
quarter of a nozzle over the 0.40 mm the printer can lay down -- and
every edge here clears it by a factor of two.

## The wave itself

| boundary | harmonics | amplitude deg | amplitude mm | nozzle widths |
|---|---|---:|---:|---:|
| ntb, south | 3 + 5 | 2.5 | 0.57 | 1.4 |
| ntb, north | 2 + 4 | 2.5 | 0.57 | 1.4 |
| stb, south | 2 + 5 | 2.5 | 0.57 | 1.4 |
| stb, north | 3 + 4 | 2.5 | 0.57 | 1.4 |

The wave is 0.57 mm at full excursion, 1.4 nozzle widths, so it is a
shape the printer can resolve rather than noise. No two of the four
boundaries carry the same pair of harmonics or the same phases, and
none of them is Jupiter's: the two planets stand on one board and a
shared wave would read as one pattern printed twice.

## The ring system

Unchanged by this correction, and named here so that it is on the
record rather than assumed.

| value | mm |
|---|---:|
| `RING_INNER_D` | 26.00 |
| `RING_OUTER_D` | 30.00 |
| `RING_THICKNESS` | 1.40 |
| `RING_GLOBE_BITE` | 1.00 |
| `RING_WEB_INNER_R` | 5.00 |
| `RING_WEB_OVERLAP` | 0.45 |
| `RING_WEB_DROP` | 0.30 |
| `RING_WEB_SECTORS` | 96 |
| `RING_WEB_SLOPE` | 1.08 (47.2 deg from horizontal) |

The ring plate is 1.40 mm thick and projects 2.00 mm past the globe
on every side. Its shortest edge is that 2.00 mm projection and its
narrowest neck is its 1.40 mm section -- 5.0 and 3.5 nozzle widths
respectively, both well clear. Neither number moved in this run.

## Filaments

| role | filament | hex |
|---|---|---|
| globe | `yellow` | #FFD834 |
| the four light bands | `sunflower_yellow` | #FFB549 |
| the one darker band | `cocoa_brown` | #8E3C06 |
| the bright northern cap | `white` | #FFFEF7 |
| the ring | `white` | #FFFEF7 |

**Saturn prints in 4 surface filaments** -- `cocoa_brown`, `sunflower_yellow`, `white`, `yellow` -- where it printed
in three. The disc and the numeral are counted separately, as they
are everywhere in this set: every piece carries `white` and `black`
for those, and they are the ownership cue rather than the planet.
No new spool: `sunflower_yellow` was already loaded for the Sol den plug and for
Venus's globe, `cocoa_brown` for the belt tiles and four other worlds, and
`white` for this piece's own ring.

## The ring's colour against the globe's

The ring and the globe touch: the plate's bore is 1.00 mm inside the
globe's own radius, so the annulus leaves the surface at the
equator and the two bodies share that boundary all the way round.
The ring is `white` #FFFEF7 and the globe is `yellow` #FFD834, which is the
largest value step on the piece after the numeral, and it is the
step that reads the ring as a separate object rather than as a
flange of the ball. `measure/saturn-tone-separation.md` measures it
beside the band tones. The cap above +58 is `white` too, so the
brightest thing at the top of the globe and the brightest thing
across its middle are one filament -- which is what the reference
shows, where the ring and the northern globe are the same cream.

## Not drawn

Saturn's globe is Ø26.00 mm, so one degree of arc is 0.2269 mm and a 0.4 mm nozzle is 1.76 degrees of it. Considered and rejected, with the arithmetic each was rejected on. The north polar hexagon: it is real, and it is at the pole this piece is looked at from, which is exactly why it was considered. It spans 29000 km, 28.5 degrees of arc, 6.47 mm -- the figure would fit. Its visible edge would not. That edge is a jet-stream boundary; at the widest published reading, 500 km, it is 0.49 degrees or 0.11 mm, a quarter of one nozzle width, and the nozzle needs 1.76 degrees or 1792 km, three and a half times the feature. Printed at the width the printer can lay down it is four times too fat and reads as a moulding line round the pole; printed at the width it really is, it cannot be printed at all. The polar vortex eye inside it is finer again. The Great White Spot storms appear once a Saturnian year and are not what the reference shows. Spokes in the ring are a transient radial shadowing, light rather than material, and a solid annulus cannot carry them. The ring divisions: the printed ring projects 2.00 mm beyond the globe and that stands for 62117 km of real ring, so one millimetre of it is 31058 km; the Cassini division at 4700 km is 0.15 mm and the Encke gap at 325 km is 0.010 mm, against a 0.4 mm nozzle. And the shadow the ring casts on the globe is light rather than material: printed it becomes a permanent dark band, which is the opposite of the soft low-contrast surface this correction exists to produce. No stippling and no fine ribs stand in for any of them: the set's material rules forbid deliberate grit and at this size it would print as noise.
