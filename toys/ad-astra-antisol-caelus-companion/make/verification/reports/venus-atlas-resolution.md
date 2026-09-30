# Venus's radar atlas at globe scale

Venus's globe is Ø16.53 mm, so its radius is 8.265 mm and one degree
of arc is 0.1443 mm.  The nozzle is 0.40 mm, which is the narrowest
colour boundary the printer can lay down and 2.77 degrees of arc here
-- against 2.74 degrees on Earth, 2.63 on Mars and 3.33 on Mercury,
the other three worlds in this set drawn from outlines.

The rings are stylised silhouettes of the major highland and lowland
provinces at the accuracy a globe this size can hold, not Magellan
mapping. The names are the real ones so that a reader can check them.

## Every ring

`aphrodite_terra` is the feature as drawn; `aphrodite_west` and
`aphrodite_east` are the two rings the build actually sweeps, and
their union is the first of them exactly. The last column is why:
`features/patches.py` refuses a ring whose vertices reach more than
72 degrees from the ring's own mean axis, because past that a
vertex's radial line runs nearly parallel to the tool's own section
planes and the construction stops being well conditioned.

| ring | tone | vertices | perimeter mm | shortest edge mm | narrowest neck mm | half-angle deg |
|---|---|---:|---:|---:|---:|---:|
| `aphrodite_terra` | as drawn, not swept | 24 | 46.52 | 1.22 | 1.18 | 77.23 **over** |
| `aphrodite_west` | highland | 14 | 26.66 | 1.28 | 1.28 | 42.68 |
| `aphrodite_east` | highland | 15 | 29.27 | 1.22 | 1.18 | 48.45 |
| `ishtar_terra` | highland | 14 | 20.70 | 0.97 | 0.97 | 30.79 |
| `beta_regio` | highland | 6 | 8.15 | 1.12 | 1.12 | 10.74 |
| `phoebe_regio` | highland | 6 | 8.13 | 1.01 | 1.01 | 10.94 |
| `alpha_regio` | highland | 6 | 6.77 | 0.93 | 0.93 | 8.73 |
| `themis_regio` | highland | 6 | 5.82 | 0.66 | 0.66 | 8.15 |
| `lada_terra` | highland | 8 | 11.17 | 1.04 | 1.04 | 15.70 |
| `atalanta_planitia` | lowland | 9 | 18.03 | 1.60 | 1.60 | 28.66 |
| `guinevere_planitia` | lowland | 8 | 18.18 | 1.72 | 1.72 | 30.51 |
| `lavinia_planitia` | lowland | 7 | 11.48 | 1.35 | 1.35 | 16.17 |

**Aphrodite's waist is 1.184 mm**, which is 8.21 degrees of arc and
2.96 nozzle widths, at the vertex (206, 10) against the edge from
(212, 4) to (202, -2). It is the narrowest point of the one feature
this piece is recognised by, it clears the nozzle as drawn, and so
**no vertex of it was widened or moved**.

## The amber between two rings of the same tone

Two boundaries of one tone running closer than the nozzle would
print as one region. Aphrodite's two build rings are left out: they
are one highland by construction and overlap by design.

| channel | tone | width mm |
|---|---|---|
| beta_regio / phoebe_regio | highland | 2.24 |
| phoebe_regio / themis_regio | highland | 2.01 |
| alpha_regio / lada_terra | highland | 3.26 |

Every pair not listed is more than 4.00 mm apart. The two tones are
not compared here: a highland and a lowland may touch or overlap,
and the subtraction below is what decides which one wins.

## The strip the highlands leave in a lowland

`highland` is subtracted out of `lowland`, so where a plain's
boundary runs close to a highland it sits inside, the darker strip
left between them is that narrow. A lowland ring that *crosses* a
highland leaves no strip at all there, which is the sound answer
rather than a thin one: the amber simply reaches the plain and the
brown runs out in a wedge instead of a thread.

| lowland | cut by | crossings | boundary inside mm | under the nozzle mm | narrowest strip mm |
|---|---|---:|---:|---:|---|
| atalanta_planitia | highland | 2 | 1.93 | 0.00 | - |
| guinevere_planitia | highland | 4 | 5.62 | 0.00 | - |
| lavinia_planitia | highland | 0 | 0.00 | 0.00 | - |

Nothing of any plain lies inside a highland, so the subtraction
removes nothing and leaves no strip. It is kept because the
structure is what the pattern requires -- where the two do meet, the
highland is the one that wins -- and because a subtraction that is
empty today is what keeps a later vertex move honest.

## What the collar buries

This is Venus's own column and it is the price of the inversion.
The globe is sunk 2.00 mm into its disc and carried by a seat cone
springing at piece-latitude -42, so nothing below that parallel of
the **piece** is visible. Venus's obliquity is 177.36 degrees, which
puts the planet's north pole into that collar, so on this world the
buried hemisphere is the northern one. Measured by sampling each
province's interior and carrying it into the piece frame at the
mirrored lean.

| province | piece latitude, Sol | visible | piece latitude, Anti-Sol | visible |
|---|---|---:|---|---:|
| `aphrodite_terra` | -11.1 to +27.9 | 100% | -8.8 to +24.0 | 100% |
| `ishtar_terra` | -73.7 to -51.4 | 0% | -78.2 to -54.4 | 0% |
| `beta_regio` | -38.5 to -17.6 | 100% | -33.5 to -12.4 | 100% |
| `phoebe_regio` | -2.5 to +15.4 | 100% | +2.5 to +20.6 | 100% |
| `alpha_regio` | +19.3 to +34.1 | 100% | +18.6 to +33.9 | 100% |
| `themis_regio` | +28.5 to +41.5 | 100% | +33.5 to +46.6 | 100% |
| `lada_terra` | +55.3 to +73.9 | 100% | +52.5 to +72.1 | 100% |
| `atalanta_planitia` | -54.6 to -25.6 | 68% | -53.3 to -26.3 | 66% |
| `guinevere_planitia` | -33.4 to -7.1 | 100% | -31.4 to -4.2 | 100% |
| `lavinia_planitia` | +34.1 to +55.1 | 100% | +33.8 to +55.6 | 100% |

- **atalanta_planitia** -- 36 per cent of it is inside the collar for the same reason; the northern two thirds of the plain are visible.
- **ishtar_terra** -- drawn in full and invisible on the printed piece. Venus's 177.36 degree obliquity puts the planet's north pole at the bottom of the piece, and the globe is sunk 2.00 mm into its disc and carried by a seat cone springing at piece-latitude -42, so everything north of about Venusian +42 is inside the collar. Ishtar runs from +54 to +76 and lands entirely within it on both armies. It is not nothing in the solid, and that is measured rather than assumed: the part of it above the disc's own cut survives as a 3.04 mm3 body of `beige` spanning piece-latitude -49.29 to -41.89, which the shop will print and nobody will see -- its top edge clears the parallel where the collar springs by 0.11 degrees, 0.016 mm of arc. It is kept in the atlas because it is a real province of the supplied data and because the reason it cannot be seen is the inversion this revision is forbidden to correct -- not because anything about it is wrong.

## What the atlas does not draw

The reference is a radar mosaic and most of what is loudest in it
cannot be carried at this size. Stated rather than left for a reader
to notice.

- **Maxwell Montes** -- the highest ground on the planet, and relief rather than albedo. Every marking on Venus is a flush colour inlay, so the globe's outer surface stays a true sphere; a raised massif would be the one thing on this world that breaks it.
- **any terminator, limb shading or polar cap** -- the reference is a whole-globe mosaic assembled from many orbits and shows none of them.
- **craters** -- Venus has about a thousand and the largest, Mead, is 270 km across, which is 1.3 degrees of arc and 0.18 mm here -- under half a nozzle width, with no room for a rim and a floor inside it.
- **the clouds** -- deliberately. The reference is the surface mapped through the atmosphere, and a cloud pattern and a radar map are two pictures of two different objects. The Mariner-10 ultraviolet cloud Y this revision deletes was the other one.
- **the radar filaments** -- tesserae, lava channels, fracture belts and the ragged bright texture that makes the reference look like beaten gold. The globe is Ø16.53 mm, so one degree of arc is 0.1443 mm and the 0.4 mm nozzle is 2.77 degrees of arc. A radar filament a few tens of kilometres wide is 0.2 to 0.5 degrees on a planet 12,104 km across, a fifth of one nozzle width. None of it survives, and none of it is approximated: the set's material rules forbid deliberate grit, and stippling or fine ribs at this size print as noise rather than as texture.

## Simplifications

- **aphrodite_terra** -- built as two overlapping rings, `aphrodite_west` and `aphrodite_east`, rather than as one. Not a change to the feature: the two share 28 degrees of longitude, their union is the drawn ring exactly, and both cut chords lie inside that union where neither is a boundary of the highland. No vertex moved and no width changed. The reason is the outline construction's own limit -- `features/patches.py` refuses a ring reaching more than 72 degrees from its own mean axis, and Aphrodite as drawn reaches 77.23. The two halves reach 42.68 and 48.45. Its narrowest neck is 1.184 mm either way, which is 2.96 nozzle widths, so no widening was needed.

## Verdict

Nothing in Venus's atlas falls under the 0.40 mm nozzle at this
globe size: no ring edge, no neck, no amber channel between two
rings of one tone, and no subtracted strip. Every one of the ten
provinces the atlas carries is drawn -- none was dropped, none
was shrunk to a dot and none was replaced by a circle. The four
small Regios, which the atlas warns are near the floor, measure
0.66 to 1.12 mm at their narrowest against a 0.40 mm nozzle.

Measured by `measure/venus_atlas_resolution.py` on the exact rings
in `parts/venus_atlas.py`.
