# Jupiter's markings against the camera

Dot product of each marking's own direction against the view axis,
at the two frames the whole set is photographed from and at the
per-world frame the two Jupiters are rendered at on their own, on
both armies. +1 is dead-on, 0 is the limb, -1 is the far side.

Jupiter's obliquity is 3.13 degrees, the second smallest in the set,
so the mirrored lean that distinguishes the two armies moves a
marking by very little and the Sol and Anti-Sol columns stay close.
That is the planet, not a mistake in the mirror: Venus at 177.36 and
Uranus at 97.77 separate widely on the same measurement.

## The Great Red Spot's centre

| frame | azimuth | elevation | Sol | Anti-Sol |
|---|---:|---:|---:|---:|
| hero | -55 | 22 | +0.69 | +0.74 |
| state sheet | -45 | 35.264 | +0.51 | +0.57 |
| per-world spot frame | -48 | 5 | +0.87 | +0.91 |

## Every vertex of both ovals

The worst vertex is what decides whether the whole marking is in
frame, not the centre.

| marking | frame | Sol worst | Sol best | Anti-Sol worst | Anti-Sol best |
|---|---|---:|---:|---:|---:|
| `spot` | hero | **+0.63** | +0.74 | **+0.68** | +0.79 |
| `spot` | state sheet | **+0.44** | +0.57 | **+0.50** | +0.63 |
| `spot` | per-world spot frame | **+0.83** | +0.91 | **+0.87** | +0.94 |
| `collar` | hero | **+0.60** | +0.77 | **+0.65** | +0.81 |
| `collar` | state sheet | **+0.41** | +0.60 | **+0.47** | +0.66 |
| `collar` | per-world spot frame | **+0.81** | +0.92 | **+0.85** | +0.95 |

## The belts and zones

A belt runs all the way round the globe, so half of it faces the
camera at every frame by construction and the only question its
facing answers is which latitudes are in view. Reported at the
longitude that faces each camera, which is the azimuth itself.

| marking | latitudes | hero Sol | hero Anti-Sol | sheet Sol | sheet Anti-Sol |
|---|---|---:|---:|---:|---:|
| North North Temperate Belt | +38 to +43 | +0.96 | +0.94 | +1.00 | +0.99 |
| North Temperate Belt | +24 to +31 | +1.00 | +0.99 | +0.98 | +1.00 |
| North Equatorial Belt | +7 to +17 | +0.98 | +0.99 | +0.90 | +0.93 |
| South Equatorial Belt | -20 to -7 | +0.80 | +0.83 | +0.63 | +0.69 |
| South Temperate Belt | -34 to -27 | +0.58 | +0.63 | +0.38 | +0.45 |
| South South Temperate Belt | -46 to -40 | +0.39 | +0.45 | +0.17 | +0.24 |
| Equatorial Zone | -7 to +7 | +0.91 | +0.94 | +0.79 | +0.84 |
| North Tropical Zone | +17 to +24 | +1.00 | +1.00 | +0.96 | +0.98 |
| South Tropical Zone | -27 to -20 | +0.68 | +0.72 | +0.49 | +0.55 |
| North Temperate Zone | +31 to +38 | +0.98 | +0.97 | +1.00 | +1.00 |
| South Temperate Zone | -40 to -34 | +0.49 | +0.54 | +0.27 | +0.34 |

## What the numbers say

- **The -110 degree carry is preserved exactly.** The spot's centre
  is still latitude -22, longitude -48, which is where that carry
  put it. Nothing in this correction moved it; the oval is drawn
  about the same point the three circles were drawn about.
- **It still faces both photographed cameras on both armies.** The
  centre measures +0.69 and +0.74 at the hero frame and +0.51 and
  +0.57 at the state sheet, so the worst of the four is +0.51 --
  positive at every frame on every army, against the -0.49 the
  original build measured before the carry.
- **And so does the whole oval, not just its centre.** The worst
  vertex of the red ring over both armies and both photographed
  frames is +0.44. The spot this revision draws is 13 degrees of arc
  across where the three circles spanned 37, so it sits further
  inside the near hemisphere than the marking it replaces did.

Measured by `measure/jupiter_facing.py` on the exact rings in
`parts/jupiter_atlas.py` and the exact cameras in `snap_frames.py`
and `world_views.py`.
