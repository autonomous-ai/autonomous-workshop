# Venus's markings against the camera

Dot product of each province's own direction against the view axis,
at the two frames the product is photographed from, on both armies.
+1 is dead-on, 0 is the limb, -1 is the far side.

Every longitude below carries `venus_atlas.LONGITUDE_OFFSET`,
**+90 degrees**, applied to the whole marking set at once.

**And since the Antisol Mirror revision the Anti-Sol piece carries
them MIRRORED.** Venus's obliquity is 177.36 degrees, so its two
pieces differ by 5.28 degrees of lean -- the same turn measured each
way round -- and the pair showed the same face twice. The Anti-Sol
piece now reflects every marking longitude about that piece's own
facing meridian at -123.85 degrees. The `longitude` column below is
the SOL piece's; the Anti-Sol longitude is beside it, and the two
facing columns are read off the piece each one is actually built as.
`measure/mirror-meridian.md` is the whole transform, the sweep that
chose that meridian, and the per-ring table at both frames.

## The offset was measured, not inherited

The deleted cloud Y carried -135 degrees. That number was chosen for
a pattern that no longer exists and has no authority over radar
data, so it was discarded and every whole degree swept instead. The
criterion is Aphrodite Terra's worst facing across both frames and
both armies, because Aphrodite is the feature this piece is
recognised by.

| offset | Aphrodite, worst of the four cases | Aphrodite vertices on the near hemisphere, worst case |
|---:|---:|---:|
| -135 | -0.470 | 21% |
| +0 | -0.122 | 46% |
| +73 | +0.761 | 88% |
| +103 **chosen** | +0.910 | 92% |
| +133 | +0.698 | 75% |
| +180 | +0.094 | 58% |

The sweep's maximum is +103 degrees and it is the offset the atlas
carries. At it every one of Aphrodite's 24 vertices is on the near
hemisphere in all four cases, so the whole silhouette is presented
rather than a piece of it, and the worst of the four centroid
readings is +0.870. The old -135 measures -0.470 on the same test,
which is why it was not inherited.

## The hero frame: azimuth -55, elevation 22

| province | tone | latitude | Sol longitude | Anti-Sol longitude | Sol | Anti-Sol | faces the camera |
|---|---|---:|---:|---:|---:|---:|---|
| `aphrodite_terra` | highland | -13.4 | 226.1 | 246.1 | +0.98 | +0.97 | yes |
| `ishtar_terra` | highland | +71.0 | 134.4 | 337.9 | -0.38 | -0.44 | no |
| `beta_regio` | highland | +25.6 | 15.6 | 96.7 | -0.81 | -0.80 | no |
| `phoebe_regio` | highland | -10.1 | 13.7 | 98.6 | -0.64 | -0.59 | no |
| `alpha_regio` | highland | -27.3 | 95.1 | 17.2 | -0.47 | -0.45 | no |
| `themis_regio` | highland | -38.3 | 13.6 | 98.7 | -0.34 | -0.28 | no |
| `lada_terra` | highland | -65.8 | 115.1 | 357.1 | +0.13 | +0.17 | yes |
| `atalanta_planitia` | lowland | +40.7 | 267.3 | 205.0 | +0.37 | +0.34 | yes |
| `guinevere_planitia` | lowland | +19.5 | 60.8 | 51.5 | -0.99 | -0.99 | no |
| `lavinia_planitia` | lowland | -46.1 | 89.7 | 22.6 | -0.28 | -0.24 | no |

## The state sheet frame: azimuth -45, elevation 35.264

| province | tone | latitude | Sol longitude | Anti-Sol longitude | Sol | Anti-Sol | faces the camera |
|---|---|---:|---:|---:|---:|---:|---|
| `aphrodite_terra` | highland | -13.4 | 226.1 | 246.1 | +0.94 | +0.87 | yes |
| `ishtar_terra` | highland | +71.0 | 134.4 | 337.9 | -0.52 | -0.67 | no |
| `beta_regio` | highland | +25.6 | 15.6 | 96.7 | -0.90 | -0.72 | no |
| `phoebe_regio` | highland | -10.1 | 13.7 | 98.6 | -0.62 | -0.38 | no |
| `alpha_regio` | highland | -27.3 | 95.1 | 17.2 | -0.21 | -0.34 | no |
| `themis_regio` | highland | -38.3 | 13.6 | 98.7 | -0.23 | -0.01 | no |
| `lada_terra` | highland | -65.8 | 115.1 | 357.1 | +0.39 | +0.34 | yes |
| `atalanta_planitia` | lowland | +40.7 | 267.3 | 205.0 | +0.10 | +0.17 | yes |
| `guinevere_planitia` | lowland | +19.5 | 60.8 | 51.5 | -0.94 | -0.95 | no |
| `lavinia_planitia` | lowland | -46.1 | 89.7 | 22.6 | -0.01 | -0.07 | no |

## The single-piece frames

`snap/worlds/` renders each Venus piece alone at the two azimuths
below, measured the same way: the azimuth that puts the named
province most squarely in front of the camera on both armies at 12
degrees of elevation. Venus is upside down, so an azimuth is not a
Venusian longitude here -- the obliquity turns the map over before
the camera sees it, which is why both were swept rather than read
off the atlas.

| frame | azimuth | elevation | what it is aimed at | Sol | Anti-Sol |
|---|---:|---:|---|---:|---:|
| `venus-<side>-aphrodite.png` | -46.0 | +12.0 | `aphrodite_terra` | +1.00 | +0.94 |
| `venus-<side>-beta_phoebe.png` | +164.0 | +12.0 | `beta_regio` | +0.76 | +0.07 |
| `venus-<side>-beta_phoebe.png` | +164.0 | +12.0 | `phoebe_regio` | +1.00 | +0.15 |
| the same frame, checked negatively | +164.0 | +12.0 | `aphrodite_terra` | -0.76 | -0.57 |

The last row is the check that the second frame really is the far
face: Aphrodite is behind the globe in it, so nothing in
`venus-<side>-beta_phoebe.png` is the feature the first frame shows.

## Can one camera show Aphrodite and the plains at once?

No, and the reason is Venus's own geography rather than a framing
choice. Aphrodite dominates one hemisphere and the three major
plains lie largely on the other, so a camera cannot present both.
This is the sweep that establishes it, and it is recorded because an
independent reader of the single-piece frames asked for exactly that
camera and it does not exist.

The index below is the fraction of a province's own ring vertices
that are both on the near hemisphere and above the parallel where
the seat collar springs -- so it counts what a reader can actually
see -- taken at the worse of the two armies, at 12 degrees of
elevation.

| azimuth | Aphrodite | Atalanta | Guinevere | Lavinia | plains total |
|---:|---:|---:|---:|---:|---:|
| -180 | 0.17 | 0.00 | 0.62 | 0.57 | 1.20 |
| -165 | 0.23 | 0.00 | 0.38 | 0.29 | 0.66 |
| -150 | 0.30 | 0.00 | 0.38 | 0.00 | 0.38 |
| -135 | 0.40 | 0.00 | 0.12 | 0.00 | 0.12 |
| -120 | 0.54 | 0.22 | 0.00 | 0.00 | 0.22 |
| -105 | 0.71 | 0.22 | 0.00 | 0.00 | 0.22 |
| -90 | 0.79 | 0.33 | 0.00 | 0.00 | 0.33 |
| -75 | 0.86 | 0.44 | 0.00 | 0.00 | 0.44 |
| -60 | 0.93 | 0.56 | 0.00 | 0.00 | 0.56 |
| -45 | 0.93 | 0.56 | 0.00 | 0.00 | 0.56 |
| -30 | 0.82 | 0.44 | 0.00 | 0.00 | 0.44 |
| -15 | 0.75 | 0.33 | 0.00 | 0.00 | 0.33 |
| +0 | 0.68 | 0.22 | 0.00 | 0.00 | 0.22 |
| +15 | 0.54 | 0.11 | 0.00 | 0.00 | 0.11 |
| +30 | 0.40 | 0.00 | 0.12 | 0.00 | 0.12 |
| +45 | 0.27 | 0.00 | 0.38 | 0.14 | 0.52 |
| +60 | 0.17 | 0.00 | 0.62 | 0.43 | 1.05 |
| +75 | 0.10 | 0.00 | 0.88 | 0.71 | 1.59 |
| +90 | 0.00 | 0.00 | 1.00 | 1.00 | 2.00 |
| +105 | 0.00 | 0.00 | 1.00 | 1.00 | 2.00 |
| +120 | 0.00 | 0.00 | 1.00 | 1.00 | 2.00 |
| +135 | 0.00 | 0.00 | 1.00 | 1.00 | 2.00 |
| +150 | 0.00 | 0.00 | 1.00 | 1.00 | 2.00 |
| +165 | 0.03 | 0.00 | 1.00 | 0.86 | 1.86 |

Where Aphrodite is best presented, at azimuth -60, it reaches 0.93
and the plains reach 0.56 between them. Where the plains are best
presented, at azimuth +90, they reach 2.00 and Aphrodite falls to
0.00. There is no azimuth at which both are high.

`venus-<side>-aphrodite.png` is therefore aimed at Aphrodite, which
is the feature the piece is recognised by, and
`venus-<side>-beta_phoebe.png` is the frame where the plains read as
terrain. Neither frame is the whole surface and neither is claimed
to be.

## The poles, and which one the obliquity actually produces

Venus's obliquity is 177.36 degrees, so its north pole points very
nearly straight **down**. The camera that looks down it is therefore
below the board and sees the underside of the disc; the frame that
shows this world's visible pole region is the south one. Both are
rendered, and the north one is kept as the evidence of exactly that.

| frame | side | azimuth | elevation | what it sees |
|---|---|---:|---:|---|
| `venus-sol-polar.png` | north | +0.00 | -87.36 | the underside of the disc; no part of the globe |
| `venus-sol-south-polar.png` | south | +180.00 | +87.36 | the globe from above, with the disc as a ring around it |
| `venus-anti-polar.png` | north | +180.00 | -87.36 | the underside of the disc; no part of the globe |
| `venus-anti-south-polar.png` | south | +0.00 | +87.36 | the globe from above, with the disc as a ring around it |

Measured by `measure/venus_facing.py` on the exact rings in
`parts/venus_atlas.py` and the exact cameras in `snap_frames.py`
and `world_views.py`.
