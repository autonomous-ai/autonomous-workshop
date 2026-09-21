# Venus's corrected surface, measured on the built solids

Sampled 0.10 mm under the sphere, in the planet's own frame, carried
into the piece by the same obliquity the part uses, and classified
against every colour body of the world. `H` is the `beige` highland,
`o` is the `cocoa_brown` lowland, `.` is bare `sunflower_yellow`
globe, and a blank is off the piece -- the globe is sunk 2.00 mm into
its disc and cut at the disc's top face, so that part of the ball
does not exist.

One degree of arc is 0.1443 mm on this Ø16.53 globe and the nozzle is
0.40 mm, so a printable feature has to hold 2.77 degrees.

## Every filament on this world

Read off the build rather than off the source: `parts/world.py`
returns one body per colour and this is that list.

| body | filament |
|---|---|
| `disc` | `white` |
| `numeral` | `black` |
| `globe` | `sunflower_yellow` |
| `highland` | `beige` |
| `lowland` | `cocoa_brown` |

**Venus carries 5 filaments: `beige`, `black`, `cocoa_brown`, `sunflower_yellow`, `white`.**
**There is no `orange` anywhere on this world**: not one of the 5 bodies carries it.
The globe is `sunflower_yellow` #FFB549 and the two marking tones are the only others.
The `white` disc and `black` numeral are the Sol ownership cue and
are not markings; the Anti-Sol piece swaps them and nothing else.

## The whole surface

Venusian longitude -180 to +180 east across, latitude +78 down to
-78, every 3 degrees. Sol army. Longitudes carry the atlas's
+90 degree offset, because this is the built piece rather than the
drawn map.

```
       |         |         |         |         |         |         |         |         |         |         |         |         |
   +78                                                                                                                          
   +75                                                                                                                          
   +72                                                                                                                          
   +69                                                                                                                          
   +66                                                                                                                          
   +63                                                                                                                          
   +60                                                                                                                          
   +57                                                                                                                          
   +54                                                                                                                          
   +51 ........................                                                                         ........................
   +48 ..........................ooooooooooooo..........                       .................................................
   +45 ........................oooooooooooooooo.................................................................................
   +42 ......................oooooooooooooooooo.................................................................................
   +39 ....................ooooooooooooooooooo..................................................................................
   +36 ...................oooooooooooooooooooo..................................................................................
   +33 ...................ooooooooooooooooooo..........................HHHH.....................................................
   +30 .....................ooooooooooooooo............................HHHH..........ooooooooo..................................
   +27 ..........................oooo.................................HHHHH........oooooooooooo.................................
   +24 ...............................................................HHHHH.......oooooooooooooo................................
   +21 ...............................................................HHHHH.....oooooooooooooooo................................
   +18 ................................................................HHH.....oooooooooooooooo.................................
   +15 .......................................................................ooooooooooooooooo.................................
   +12 .......................................................................ooooooooooooooooo.................................
    +9 ......................................HH..................................ooooooooooo....................................
    +6 ...................................HHHHHH................................................................................
    +3 ................................HHHHHHHHH................................................................................
    +0 HHHH.........................HHHHHHHHHH...............................................................................HHH
    -3 HHHHHH.....................HHHHHHHHHH...........................HHH.................................................HHHHH
    -6 HHHHHHHH................HHHHHHHHHHH............................HHHHH..............................................HHHHHHH
    -9 HHHHHHHHHH............HHHHHHHHHH...............................HHHHH............................................HHHHHHHHH
   -12 HHHHHHHHHHHH.......HHHHHHHHHHH................................HHHHHH...........................................HHHHHHHHHH
   -15 ..HHHHHHHHHHHHHHHHHHHHHHHHHH..................................HHHHH............................................HHHHHHHH..
   -18 .....HHHHHHHHHHHHHHHHHHHHH.....................................................................................HHHHH.....
   -21 .......HHHHHHHHHHHHHHHH....................................................................HHH...........................
   -24 ..........HHHHHHHHH.......................................................................HHHHH..........................
   -27 ..........................................................................................HHHHH..........................
   -30 .........................................................................................HHHHH...........................
   -33 ................................................................HHH........................HHH...........................
   -36 ...............................................................HHHH.......................oooo...........................
   -39 ...............................................................HHHHH..................oooooooooo.........................
   -42 ...............................................................HHHH..................ooooooooooo.........................
   -45 ....................................................................................oooooooooooo.........................
   -48 ...................................................................................ooooooooooooo.........................
   -51 ....................................................................................ooooooooooo..........................
   -54 .....................................................................................oooooooo............................
   -57 .............................................................................................HHHHHHHHHHHHH...............
   -60 ..........................................................................................HHHHHHHHHHHHHHHHHHH............
   -63 .......................................................................................HHHHHHHHHHHHHHHHHHHHHHH...........
   -66 ........................................................................................HHHHHHHHHHHHHHHHHHHHHH...........
   -69 .........................................................................................HHHHHHHHHHHHHHHHHHH.............
   -72 .............................................................................................HHHHHHHHHHH.................
   -75 .........................................................................................................................
   -78 .........................................................................................................................
       |         |         |         |         |         |         |         |         |         |         |         |         |
```

## Does Aphrodite come out as one highland?

The `H` cells above, flooded four-ways with the longitude seam
joined. Aphrodite is built as two overlapping rings, so the question
is whether the boolean agreed that they are one region.

| group | cells | provinces whose centre falls in it |
|---|---:|---|
| highland 1 | 228 | `aphrodite_west`, `aphrodite_east` |
| highland 2 | 107 | `lada_terra` |
| highland 3 | 26 | `beta_regio` |
| highland 4 | 24 | `phoebe_regio` |
| highland 5 | 21 | `alpha_regio` |
| highland 6 | 16 | `themis_regio` |
| lowland 1 | 124 | `atalanta_planitia` |
| lowland 2 | 112 | `guinevere_planitia` |
| lowland 3 | 69 | `lavinia_planitia` |

**Aphrodite's two build rings land in one group.** The overlap fused, so the highland is continuous across the whole 152 degrees of longitude it is drawn over and reads as one province rather than two.

Its widest row is latitude -12, 117 degrees of longitude wide
-- 16.9 mm of arc on a Ø16.53 globe, which is the longest
continuous marking anywhere in this set.

## Is the pattern still inverted?

Venus's obliquity is 177.36 degrees and the planet frame is what turns
this map over. A northern province must therefore come out **low**
on the piece and a southern one **high**. If this table ever agreed
in sign, the inversion would have been quietly corrected.

| province | Venusian latitude | piece latitude, Sol | piece latitude, Anti-Sol | inverted |
|---|---:|---:|---:|---|
| `aphrodite_terra` | -15.1 | +17.7 | +12.5 | yes |
| `ishtar_terra` | +71.0 | -69.1 | -72.7 | yes |
| `beta_regio` | +25.6 | -28.2 | -23.1 | yes |
| `phoebe_regio` | -10.1 | +7.5 | +12.6 | yes |
| `alpha_regio` | -27.3 | +27.5 | +27.0 | yes |
| `themis_regio` | -38.3 | +35.7 | +40.9 | yes |
| `lada_terra` | -65.8 | +66.8 | +64.5 | yes |
| `atalanta_planitia` | +40.7 | -40.5 | -40.7 | yes |
| `guinevere_planitia` | +19.5 | -20.7 | -18.2 | yes |
| `lavinia_planitia` | -46.1 | +46.1 | +46.1 | yes |

**Every province changes sign on both armies: the frame still inverts the map.**
This is the reason `ishtar_terra` cannot be seen: Venusian +71 lands
at piece -69.1, below the -42 where the seat cone springs.

## Is anything raised?

Every marking is a flush colour inlay reaching 1.20 mm into the
globe, so the colour bodies must add back up to the printed part
exactly and the outer surface must still be a true sphere.

| measure | mm3 |
|---|---:|
| the 5 colour bodies added up | 6678.5853 |
| the printed part `part_world_venus_sol` | 6678.5853 |
| difference | 0.000002 |

The printed part is built from the disc and the ball directly and
never sees a marking, so this is two independent constructions
agreeing rather than one measured against itself. Nothing a marking
adds can face downward and nothing protrudes: the markings are
inside the sphere, not on it.

## Are the two armies still mirrors?

1647 points classified on both armies at half this grid's resolution.
**0 disagree on which marking they carry.** The two pieces carry the same map; what differs is the direction the
globe leans, which is the ownership cue and is mirrored by
construction. The collar cuts the two at Venusian latitudes 5.28
degrees apart, so a point near its edge can be on one piece and
inside the other's disc; those points are excluded above and are
measured as visible fractions in `measure/venus-atlas-resolution.md`.

Measured by `measure/venus_surface_scan.py` on the exact solids
`parts/world.py` builds.
