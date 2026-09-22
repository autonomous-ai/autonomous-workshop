# Jupiter's belts, zones and spot at globe scale

Jupiter's globe is Ø26.97 mm, so its radius is 13.485 mm and one degree
of arc is 0.2354 mm.  The nozzle is 0.40 mm, which is the narrowest
colour boundary the printer can lay down and 1.70 degrees of arc
here.  This is the most forgiving world in the set: the same nozzle
is 3.33 degrees on Mercury and 2.74 on Earth.

## The six belts

Two of them wave, so their width varies along their own length and
the least of it is what has to clear the nozzle. The South
Equatorial Belt also bends 7.0 degrees north over the Great Red
Spot, which is where its narrowest width is.

| belt | latitudes | drawn as | width deg | width mm | least mm | nozzles |
|---|---|---|---|---:|---:|---:|
| North North Temperate Belt | +38 to +43 | `band` | 5.00 | 1.18 | **1.18** | 2.9 |
| North Temperate Belt | +24 to +31 | `band` | 7.00 | 1.65 | **1.65** | 4.1 |
| North Equatorial Belt | +7 to +17 | `outline` | 7.03 to 13.13 | 3.09 | **1.65** | 4.1 |
| South Equatorial Belt | -20 to -7 | `outline` | 7.20 to 17.26 | 4.06 | **1.69** | 4.2 |
| South Temperate Belt | -34 to -27 | `band` | 7.00 | 1.65 | **1.65** | 4.1 |
| South South Temperate Belt | -46 to -40 | `band` | 6.00 | 1.41 | **1.41** | 3.5 |

## The five zones

A zone is bounded by the belts on either side of it, so where one of
those waves the zone waves with it. These are the widths that
actually print, measured after the belt cut rather than as drawn.

| zone | latitudes | width deg | width mm | least mm | nozzles |
|---|---|---|---:|---:|---:|
| Equatorial Zone | -7 to +7 | 9.62 to 18.13 | 4.27 | **2.26** | 5.7 |
| North Tropical Zone | +17 to +24 | 4.73 to 9.50 | 2.24 | **1.11** | 2.8 |
| South Tropical Zone | -27 to -20 | 4.52 to 14.00 | 3.30 | **1.06** | 2.7 |
| North Temperate Zone | +31 to +38 | 7.00 | 1.65 | **1.65** | 4.1 |
| South Temperate Zone | -40 to -34 | 6.00 | 1.41 | **1.41** | 3.5 |

## The wave, and what it costs the belts it is drawn on

| boundary | nominal | swings to | amplitude deg | amplitude mm |
|---|---:|---|---:|---:|
| NEB south | +7 | +4.61 to +9.47 | 2.50 | 0.588 |
| NEB north | +17 | +14.50 to +19.27 | 2.50 | 0.588 |
| SEB north | -7 | -9.41 to -4.54 | 2.50 | 0.588 |
| SEB south | -20 | -22.48 to -13.00 | 2.50 | 0.588 |

The two belts that carry it are 10.00 and 13.00 degrees wide nominally,
so a 2.5 degree wave on each boundary could in principle take 50 per
cent of the narrower of them. It does not: the two boundaries carry
different harmonics, so they never reach their extremes at the same
longitude, and the narrowest the North Equatorial Belt actually gets
is 7.03 degrees. The four belts left as plain circles of
latitude are 5, 7, 7, 6 degrees wide; the same wave would take
all of the narrowest of them, which is why they do not carry it.

## The two oval rings

| ring | vertices | semi-axes deg | perimeter mm | shortest edge mm | narrowest neck mm |
|---|---:|---|---:|---:|---:|
| `spot` | 13 | 6.5 by 4.5 | 8.08 | **0.514** | 1.04 |
| `collar` | 18 | 8.5 by 6.5 | 11.04 | **0.538** | 1.07 |

The collar is the annulus left when the spot is subtracted out of
the outer ring, so the number that has to clear the nozzle is the
gap between the two ovals rather than either ring on its own:
2.00 degrees of arc, **0.471 mm**, 1.2 nozzles, on every side.

## The spot, the collar and the belts around them

| measurement | degrees | mm | nozzles |
|---|---:|---:|---:|
| spot, top to bottom | -17.5 to -26.5 | 2.12 | 5.3 |
| spot, side to side | 13.0 wide | 3.06 | 7.6 |
| collar annulus | 2.00 | 0.471 | 1.2 |
| bright zone between collar and belt, least | 2.16 | 0.507 | 1.3 |
| collar buried in the South Temperate Belt | 1.50 tall, 10.86 wide | 2.56 wide | 6.4 |

The last row is a stated decision rather than a defect. The spot is
9.0 degrees of arc tall centred at -22 and the South Tropical Zone
is 7 degrees deep, so a collar wide enough to print at all reaches
past -27 into the South Temperate Belt. Biting a second hollow out
of that belt is not available -- the correction requires the four
narrow belts to stay plain circles of latitude -- so the collar gives
way there instead, and over 11.7 degrees of longitude the collar and
that belt are one continuous `cocoa_brown` region. Both are the same
filament, so nothing prints differently; what a reader sees is the
spot's collar touching the belt below it.

## What Jupiter does not draw

Jupiter's globe is the largest in the set at Ø26.97 mm, so one degree of arc is 0.2354 mm and a 0.4 mm nozzle is 1.70 degrees of it. The reference shows white ovals in the temperate belts, polar hoods, festoons hanging off the North Equatorial Belt, plumes, and fine filamentary turbulence along every belt edge. None of it is drawn. The white ovals subtend 2 to 4 degrees, which is one to two nozzle widths with no room for a boundary either side; the festoons are under a degree wide; the turbulence is finer again. A marking that narrow prints as a single-extrusion thread and reads as a print defect, and the set's material rules forbid deliberate grit. The one irregularity that IS drawn is the 2.5 degree wave on the two widest belt boundaries -- 0.59 mm, over five nozzle widths -- and it is drawn because at that size it is a shape rather than noise.

## Verdict

Nothing on this globe falls under the 0.40 mm nozzle. The narrowest
belt anywhere along its length is 1.18 mm (2.9 nozzles), the
narrowest zone is 1.06 mm (2.7 nozzles), the collar annulus is
0.471 mm (1.2 nozzles), the bright zone between the collar and the
hollowed belt above it is 0.507 mm (1.3 nozzles), and the shortest
edge of either oval ring is 0.514 mm (1.3 nozzles).

One number is deliberately NOT a nozzle clearance: a `band` region
is a lens that reaches its full depth at its own middle and tapers
to nothing at its own edges, so the last fraction of a degree of
each of the four plain belts is a skin thinner than one 0.2 mm
layer. That is how every band marking in this set has always been
built -- Saturn's belts, Neptune's streaks, Uranus's band -- and it
is a depth, not a width: the colour boundary the nozzle has to lay
down is the one measured above. Jupiter's zones are `shell` regions
and do not taper: they are 1.14 mm deep from edge to edge, 0.06 mm
short of the 1.20 mm the outline markings reach, for the reason
`parts/jupiter_atlas.py` measures.

Measured by `measure/jupiter_atlas_resolution.py` on the exact
latitudes, waves and rings in `parts/jupiter_atlas.py`.
