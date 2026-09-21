# The facing meridian, and the reflection taken about it

## The two cameras this is solved against

`parts/markings.PHOTOGRAPHED_VIEWS` restates `snap_frames.HERO_VIEW`
and `snap_frames.SHEET_VIEW` so that the marking table depends on
nothing that loads a renderer. The two must agree, and that is
checked here rather than trusted:

- `markings.PHOTOGRAPHED_VIEWS` = `((-55.0, 22.0), (-45.0, 35.264))`
- `(snap_frames.HERO_VIEW, snap_frames.SHEET_VIEW)` = `((-55.0, 22.0), (-45.0, 35.264))`
- they agree: **yes**

## C, world by world and frame by frame

C is the longitude of the view axis carried back into the globe's own
planet frame -- `planet_frame` inverted, applied to the camera
direction. The two frames give two values about ten degrees apart,
and one meridian has to serve both, so the mean is taken. It is a
circular mean, so a pair straddling the +/-180 seam cannot average to
the meridian behind the globe.

| world | side | hero C | state sheet C | spread | mean | adjustment | C used |
|---|---|---:|---:|---:|---:|---:|---:|
| mercury | sol | -55.0099 | -45.0150 | 9.9949 | -50.0125 | none | -50.0125 |
| mercury | anti | -54.9901 | -44.9850 | 10.0051 | -49.9875 | none | -49.9875 |
| venus | sol | -125.8362 | -136.2605 | 10.4244 | -131.0483 | +5.00 | -126.0483 |
| venus | anti | -124.0880 | -133.6178 | 9.5297 | -128.8529 | +5.00 | -123.8529 |
| jupiter | sol | -56.0897 | -46.6528 | 9.4369 | -51.3713 | +15.00 | -36.3713 |
| jupiter | anti | -54.0168 | -43.5182 | 10.4986 | -48.7675 | +15.00 | -33.7675 |

Only the **anti** rows are used: the Sol piece keeps exactly what it
has, and its rows are here so that the two can be compared.

Mercury takes the plain mean. Venus does not clear the floor at its
mean and is adjusted by +5.00 degrees; the sweep that chose that
number is below, under *Adjusting the meridian until it clears*.

## The identity, confirmed numerically

The claim is that facing is preserved EXACTLY by L -> 2C - L when C
is that frame's own meridian, at any obliquity. Swept over a grid of
latitudes and longitudes on both worlds and at both frames, on the
Anti-Sol piece, the largest absolute change in the dot product is:

| world | frame | largest |facing(L) - facing(2C - L)| over the grid |
|---|---|---:|
| mercury | hero | 5.27e-16 |
| mercury | state sheet | 4.44e-16 |
| venus | hero | 5.13e-16 |
| venus | state sheet | 6.66e-16 |
| jupiter | hero | 6.66e-16 |
| jupiter | state sheet | 4.44e-16 |

6.66e-16 over 9504 sample points is floating-point noise, so the identity
holds in this build as derived. It is the mean meridian, not the
identity, that costs anything, and that cost is measured below.

## The two obvious flips, and why neither is taken

Mercury's Caloris basin is the test: it is at latitude +30 and
longitude -50, and -50 was itself measured as the longitude that puts
it squarely in front of both cameras. Each candidate transform is
applied to it and the facing re-read on the Anti-Sol piece.

| transform | Caloris longitude becomes | hero facing | state sheet facing | verdict |
|---|---:|---:|---:|---|
| none -- what the piece has today | -50.00 | +0.987 | +0.993 | the defect: same as Sol |
| negate longitude, L -> -L | +50.00 | -0.021 | +0.227 | on the limb at the hero frame |
| the lean's own mirror plane, L -> 180 - L | +230.00 | +0.395 | +0.350 | three-quarters away, measured below |
| reflect about the facing meridian, L -> 2C - L | -49.98 | +0.987 | +0.993 | **taken** |

The brief that asked for this correction described the second trap as
putting Caloris *on the far side*. Measured here it does not go quite
that far: L -> 180 - L sends the basin to longitude +230, which is 80
degrees off the camera meridian rather than 180, and it reads +0.395
at the hero frame rather than negative. It is still the wrong answer
by a long way -- it takes the one feature this globe is recognised by
from dead-on to a glancing three-quarter view, and it would be the
second-worst thing that could be done to the piece -- but the
measurement is reported as it came out rather than as it was
described. The first trap is as described: at the hero frame
negating longitude puts Caloris at -0.021, which is the limb exactly.

Caloris is very nearly ON the facing meridian already -- that is what
-50 was solved to be -- so the reflection leaves it almost exactly
where it is and swings the seven plains around it. That is the shape
of the correction on this world: the basin stays in front of the
camera and the terrain on either side of it changes hands.

## Every ring vertex, at both frames, on both pieces

The floor is **+0.30**, and what it is applied to is a FEATURE: a
ring's own centroid direction, which is the form
`measure/venus-facing.md` and `measure/mercury-facing.md` already
report this set in. The gate is that anything which cleared the floor
on the Sol piece still clears it on the mirrored Anti-Sol piece.

Every ring VERTEX is measured too and reported beside it, as the
count over the floor, because the brief asked for the vertices and
because a centroid can hide a ring that swung half off the globe.
The vertex counts are evidence and not a second gate, and one row
shows why: Mercury's `plains` ring 2 is the equatorial plain, whose
centroid reads +0.013 at the state sheet frame -- it is ON the limb
on the Sol piece and did not clear the floor there either. Three of
its nineteen vertices creep over +0.30 on the Sol piece and none do
on the mirrored one. Nothing that was visible became invisible: a
feature already at the limb moved along the limb.

A ring marked `sector` is one of six that seam into one belt closed
right round the globe. It is reported like any other ring and it is
NOT gated on its own, because it is not a feature: the belt it
belongs to has material at every longitude on both pieces, and a
reflection moves which sector sits in front of the lens without
moving the belt. Those markings are gated whole, in *The two wavy
belts are closed bands* below. Everything else is gated ring by
ring, exactly as Mercury and Venus already were.

### mercury

Mean meridian C = -49.9875 degrees, taken as -49.9875.

| ring | kind | frame | Sol centroid | Anti centroid | change | Sol vertices over +0.30 | Anti vertices over +0.30 |
|---|---|---|---:|---:|---:|---:|---:|
| `plains` ring 1 | feature | hero | +0.309 | +0.456 | +0.146 | 10 of 21 | 12 of 21 |
| `plains` ring 1 | feature | state sheet | +0.481 | +0.352 | -0.128 | 12 of 21 | 10 of 21 |
| `plains` ring 2 | feature | hero | -0.178 | -0.020 | +0.159 | 0 of 19 | 3 of 19 |
| `plains` ring 2 | feature | state sheet | +0.013 | -0.126 | -0.139 | 3 of 19 | 0 of 19 |
| `plains` ring 3 | feature | hero | -0.992 | -0.961 | +0.032 | 0 of 16 | 0 of 16 |
| `plains` ring 3 | feature | state sheet | -0.928 | -0.956 | -0.028 | 0 of 16 | 0 of 16 |
| `plains` ring 4 | feature | hero | -0.947 | -0.971 | -0.024 | 0 of 14 | 0 of 14 |
| `plains` ring 4 | feature | state sheet | -0.891 | -0.870 | +0.021 | 0 of 14 | 0 of 14 |
| `plains` ring 5 | feature | hero | +0.108 | -0.019 | -0.127 | 6 of 20 | 4 of 20 |
| `plains` ring 5 | feature | state sheet | +0.132 | +0.242 | +0.110 | 7 of 20 | 9 of 20 |
| `plains` ring 6 | feature | hero | +0.564 | +0.431 | -0.133 | 14 of 15 | 9 of 15 |
| `plains` ring 6 | feature | state sheet | +0.362 | +0.479 | +0.117 | 8 of 15 | 11 of 15 |
| `plains` ring 7 | feature | hero | -0.740 | -0.825 | -0.085 | 0 of 12 | 0 of 12 |
| `plains` ring 7 | feature | state sheet | -0.722 | -0.648 | +0.074 | 0 of 12 | 0 of 12 |
| `caloris_rim` ring 1 | feature | hero | +0.987 | +0.987 | -0.000 | 23 of 23 | 23 of 23 |
| `caloris_rim` ring 1 | feature | state sheet | +0.993 | +0.993 | +0.000 | 23 of 23 | 23 of 23 |
| `caloris_floor` ring 1 | feature | hero | +0.987 | +0.987 | -0.000 | 13 of 13 | 13 of 13 |
| `caloris_floor` ring 1 | feature | state sheet | +0.993 | +0.993 | +0.000 | 13 of 13 | 13 of 13 |

### venus

Mean meridian C = -128.8529 degrees, taken as -123.8529.

| ring | kind | frame | Sol centroid | Anti centroid | change | Sol vertices over +0.30 | Anti vertices over +0.30 |
|---|---|---|---:|---:|---:|---:|---:|
| `highland` ring 1 | feature | hero | +0.756 | +0.731 | -0.025 | 12 of 14 | 12 of 14 |
| `highland` ring 1 | feature | state sheet | +0.825 | +0.605 | -0.220 | 14 of 14 | 10 of 14 |
| `highland` ring 2 | feature | hero | +0.913 | +0.916 | +0.004 | 15 of 15 | 15 of 15 |
| `highland` ring 2 | feature | state sheet | +0.786 | +0.879 | +0.092 | 13 of 15 | 15 of 15 |
| `highland` ring 3 | feature | hero | -0.382 | -0.439 | -0.057 | 0 of 14 | 0 of 14 |
| `highland` ring 3 | feature | state sheet | -0.517 | -0.666 | -0.149 | 0 of 14 | 0 of 14 |
| `highland` ring 4 | feature | hero | -0.812 | -0.798 | +0.013 | 0 of 6 | 0 of 6 |
| `highland` ring 4 | feature | state sheet | -0.902 | -0.720 | +0.182 | 0 of 6 | 0 of 6 |
| `highland` ring 5 | feature | hero | -0.641 | -0.594 | +0.047 | 0 of 6 | 0 of 6 |
| `highland` ring 5 | feature | state sheet | -0.616 | -0.376 | +0.240 | 0 of 6 | 0 of 6 |
| `highland` ring 6 | feature | hero | -0.469 | -0.453 | +0.016 | 0 of 6 | 0 of 6 |
| `highland` ring 6 | feature | state sheet | -0.211 | -0.342 | -0.131 | 0 of 6 | 0 of 6 |
| `highland` ring 7 | feature | hero | -0.342 | -0.281 | +0.061 | 0 of 6 | 0 of 6 |
| `highland` ring 7 | feature | state sheet | -0.226 | -0.009 | +0.217 | 0 of 6 | 0 of 6 |
| `highland` ring 8 | feature | hero | +0.132 | +0.168 | +0.036 | 1 of 8 | 2 of 8 |
| `highland` ring 8 | feature | state sheet | +0.392 | +0.337 | -0.056 | 5 of 8 | 4 of 8 |
| `lowland` ring 1 | feature | hero | +0.367 | +0.337 | -0.030 | 5 of 9 | 5 of 9 |
| `lowland` ring 1 | feature | state sheet | +0.101 | +0.170 | +0.070 | 3 of 9 | 3 of 9 |
| `lowland` ring 2 | feature | hero | -0.994 | -0.995 | -0.001 | 0 of 8 | 0 of 8 |
| `lowland` ring 2 | feature | state sheet | -0.936 | -0.950 | -0.014 | 0 of 8 | 0 of 8 |
| `lowland` ring 3 | feature | hero | -0.276 | -0.244 | +0.033 | 0 of 7 | 0 of 7 |
| `lowland` ring 3 | feature | state sheet | -0.006 | -0.071 | -0.065 | 0 of 7 | 0 of 7 |

### jupiter

Mean meridian C = -48.7675 degrees, taken as -33.7675.

| ring | kind | frame | Sol centroid | Anti centroid | change | Sol vertices over +0.30 | Anti vertices over +0.30 |
|---|---|---|---:|---:|---:|---:|---:|
| `bands` ring 1 | sector | hero | +0.972 | +0.831 | -0.141 | 22 of 22 | 22 of 22 |
| `bands` ring 1 | sector | state sheet | +0.907 | +0.866 | -0.040 | 22 of 22 | 22 of 22 |
| `bands` ring 2 | sector | hero | +0.420 | +0.902 | +0.481 | 14 of 22 | 22 of 22 |
| `bands` ring 2 | sector | state sheet | +0.535 | +0.780 | +0.245 | 17 of 22 | 22 of 22 |
| `bands` ring 3 | sector | hero | -0.460 | +0.149 | +0.609 | 0 of 22 | 8 of 22 |
| `bands` ring 3 | sector | state sheet | -0.235 | +0.036 | +0.272 | 0 of 22 | 5 of 22 |
| `bands` ring 4 | sector | hero | -0.792 | -0.676 | +0.116 | 0 of 22 | 0 of 22 |
| `bands` ring 4 | sector | state sheet | -0.637 | -0.624 | +0.013 | 0 of 22 | 0 of 22 |
| `bands` ring 5 | sector | hero | -0.251 | -0.758 | -0.507 | 0 of 22 | 0 of 22 |
| `bands` ring 5 | sector | state sheet | -0.279 | -0.552 | -0.273 | 0 of 22 | 0 of 22 |
| `bands` ring 6 | sector | hero | +0.642 | +0.008 | -0.634 | 19 of 22 | 5 of 22 |
| `bands` ring 6 | sector | state sheet | +0.510 | +0.211 | -0.300 | 16 of 22 | 9 of 22 |
| `bands` ring 7 | sector | hero | +0.793 | +0.677 | -0.116 | 22 of 22 | 21 of 22 |
| `bands` ring 7 | sector | state sheet | +0.638 | +0.625 | -0.013 | 22 of 22 | 21 of 22 |
| `bands` ring 8 | sector | hero | +0.234 | +0.739 | +0.505 | 9 of 22 | 22 of 22 |
| `bands` ring 8 | sector | state sheet | +0.254 | +0.527 | +0.273 | 10 of 22 | 18 of 22 |
| `bands` ring 9 | sector | hero | -0.646 | -0.013 | +0.633 | 0 of 22 | 5 of 22 |
| `bands` ring 9 | sector | state sheet | -0.518 | -0.218 | +0.299 | 0 of 22 | 0 of 22 |
| `bands` ring 10 | sector | hero | -0.979 | -0.837 | +0.142 | 0 of 22 | 0 of 22 |
| `bands` ring 10 | sector | state sheet | -0.924 | -0.881 | +0.043 | 0 of 22 | 0 of 22 |
| `bands` ring 11 | sector | hero | -0.424 | -0.903 | -0.479 | 0 of 22 | 0 of 22 |
| `bands` ring 11 | sector | state sheet | -0.539 | -0.784 | -0.244 | 0 of 22 | 0 of 22 |
| `bands` ring 12 | sector | hero | +0.439 | -0.161 | -0.600 | 15 of 22 | 1 of 22 |
| `bands` ring 12 | sector | state sheet | +0.208 | -0.058 | -0.266 | 8 of 22 | 2 of 22 |
| `spot` ring 1 | feature | hero | +0.689 | +0.588 | -0.101 | 13 of 13 | 13 of 13 |
| `spot` ring 1 | feature | state sheet | +0.508 | +0.506 | -0.002 | 13 of 13 | 13 of 13 |
| `collar` ring 1 | feature | hero | +0.689 | +0.588 | -0.101 | 18 of 18 | 18 of 18 |
| `collar` ring 1 | feature | state sheet | +0.508 | +0.506 | -0.002 | 18 of 18 | 18 of 18 |

## The two wavy belts are closed bands

Jupiter's North and South Equatorial Belts are the only markings in
this set drawn as longitude sectors, and they are the reason the
ring-by-ring floor above cannot be the whole gate on this world.
This is the measurement that replaces it, and it has two halves:
that the sectors really do close, and that the belt they close into
still faces the camera after the reflection.

Closure first. The sectors are sorted by their western edge; each
one's eastern edge must be the next one's western edge to within
0.0001 degrees, which is the rounding `belt_sector_ring` applies to its
own vertices, and the spans must total 360.

| world and piece | marking | rings | spans total | largest seam gap | closed |
|---|---|---:|---:|---:|---|
| jupiter sol | `bands` belt 1 | 6 | 360.0000 | 0.00e+00 | yes |
| jupiter sol | `bands` belt 2 | 6 | 360.0000 | 0.00e+00 | yes |
| jupiter anti | `bands` belt 1 | 6 | 360.0000 | 0.00e+00 | yes |
| jupiter anti | `bands` belt 2 | 6 | 360.0000 | 0.00e+00 | yes |

Then the belt itself. The floor is applied to the marking: the most
square-on point anywhere on it, at each frame, on each piece. A belt
that has material at every longitude cannot lose the camera, and
this is the number that says so rather than the argument.

| world | belt | frame | Sol best facing | Anti best facing | change | Sol vertices over +0.30 | Anti vertices over +0.30 |
|---|---|---|---:|---:|---:|---:|---:|
| jupiter | `bands` belt 1 | hero | +0.996 | +0.997 | +0.001 | 55 of 132 | 57 of 132 |
| jupiter | `bands` belt 1 | state sheet | +0.943 | +0.953 | +0.010 | 55 of 132 | 58 of 132 |
| jupiter | `bands` belt 2 | hero | +0.869 | +0.889 | +0.020 | 46 of 132 | 49 of 132 |
| jupiter | `bands` belt 2 | state sheet | +0.728 | +0.770 | +0.042 | 40 of 132 | 41 of 132 |

The vertex counts move by a sector's worth because the reflection
moves where the seams fall, not because the belt moved: a seam is a
flat face between two lenses of the same filament and it is not
visible on the printed part at all.

## The mirror, as the camera sees it

The facing table above says the correction costs nothing. This says
what it BUYS. Each ring's centroid is projected into the camera's own
image plane and reported as millimetres left or right of the centre of
the ball -- negative left, positive right -- beside its height. A
mirror pair is one where every ring a reader can SEE changes the side
it is on.

Measured at each world's own per-piece frame, which is the camera the
single-piece and pair renders in `snap/worlds/` use, because that is
the picture a reader is actually given. A ring on the far hemisphere
is listed with its numbers and marked `hidden`: it has a screen
position in the arithmetic and none in the picture, so it is not asked
to change sides. A ring that sits within a twentieth of the globe's
radius of the centre line on BOTH pieces is marked `on the meridian`
and is not asked either: it is its own mirror image, which is what
Caloris was chosen to be. Both tests have to hold on both pieces, so
a feature that starts near the centre and ends 6 mm away is checked
like any other. A belt sector is marked `sector` and is not asked
either: it is a piece of one closed band, and which sector faces the
lens is not something a reader can see.

The frame used per world is the FIRST one that world declares in
`world_views.FRAMES`, which is by construction its signature face --
`caloris` on Mercury, `aphrodite` on Venus, `spot` on Jupiter. Each
world's second frame looks at the face its recognisable features are
not on, where there is nothing for a mirror to move.

### mercury, at `mercury-<side>-caloris.png`: azimuth -50.0, elevation +20.0

| ring | seen? | Sol u mm | Anti u mm | changes sides | Sol v mm | Anti v mm | v moves mm |
|---|---|---:|---:|---|---:|---:|---:|
| `plains` ring 1 | yes | +6.22 | -6.22 | yes | +1.41 | +1.41 | 0.001 |
| `plains` ring 2 | no | +6.75 | -6.75 | hidden | +1.17 | +1.17 | 0.001 |
| `plains` ring 3 | no | +1.35 | -1.36 | hidden | +0.03 | +0.02 | 0.005 |
| `plains` ring 4 | no | -1.02 | +1.01 | hidden | +1.35 | +1.35 | 0.004 |
| `plains` ring 5 | yes | -5.36 | +5.36 | yes | +4.32 | +4.32 | 0.001 |
| `plains` ring 6 | yes | -5.65 | +5.66 | yes | -1.79 | -1.79 | 0.003 |
| `plains` ring 7 | no | -3.59 | +3.58 | hidden | +2.12 | +2.11 | 0.003 |
| `caloris_rim` ring 1 | yes | +0.00 | +0.00 | on the meridian | +1.19 | +1.20 | 0.005 |
| `caloris_floor` ring 1 | yes | +0.00 | +0.00 | on the meridian | +1.19 | +1.20 | 0.005 |

**3 of the 3 rings a reader can see at this frame change sides.**
Their heights move by at most 0.003 mm, which is nothing: this
frame's own meridian and the meridian the reflection is solved
about are the same to a hundredth of a degree, so at this
camera the transform is an exact left-to-right flip of the
picture. Caloris is the exception and it is the point: at
longitude -50.00 against a meridian of -49.99 it is very nearly
a fixed point of its own mirror, so the one feature this globe
is recognised by stays square to the lens while all seven
plains around it change hands. That is why the pair still
reads as a PAIR rather than as two unrelated worlds.

### venus, at `venus-<side>-aphrodite.png`: azimuth -46.0, elevation +12.0

| ring | seen? | Sol u mm | Anti u mm | changes sides | Sol v mm | Anti v mm | v moves mm |
|---|---|---:|---:|---|---:|---:|---:|
| `highland` ring 1 | yes | +4.44 | -6.45 | yes | +1.10 | +1.20 | 0.096 |
| `highland` ring 2 | yes | -4.23 | +1.55 | yes | +0.10 | -0.51 | 0.612 |
| `highland` ring 3 | no | +2.95 | -2.76 | hidden | -7.59 | -7.26 | 0.324 |
| `highland` ring 4 | no | -3.65 | +5.65 | hidden | -2.51 | -2.53 | 0.022 |
| `highland` ring 5 | no | -4.39 | +6.51 | hidden | +2.50 | +2.38 | 0.119 |
| `highland` ring 6 | no | +5.42 | -3.40 | hidden | +4.76 | +5.33 | 0.573 |
| `highland` ring 7 | no | -3.64 | +5.33 | hidden | +5.89 | +5.74 | 0.149 |
| `highland` ring 8 | no | +2.92 | -2.30 | hidden | +7.73 | +7.93 | 0.200 |
| `lowland` ring 1 | yes | -3.96 | +2.07 | yes | -6.26 | -6.70 | 0.435 |
| `lowland` ring 2 | no | +2.08 | +0.66 | hidden | -1.31 | -0.84 | 0.473 |
| `lowland` ring 3 | no | +3.76 | -2.07 | hidden | +6.72 | +7.11 | 0.391 |

**3 of the 3 rings a reader can see at this frame change sides.**
Their heights move by up to 0.612 mm as well, and that is
expected rather than a fault. Carried back into the globe's
own frame, this camera looks down longitude -133.56, and the
reflection is solved about -123.85 -- a different meridian. A
reflection about a meridian the camera is NOT looking down
moves a marking up or down the ball as well
as across it. At the two frames the product itself is
photographed at, which is what the reflection was solved for,
the facing table above is the measurement that matters.
Aphrodite Terra -- rings 1 and 2, the feature this globe is
recognised by -- crosses from one side of the ball to the
other and stays in front of the camera.

### jupiter, at `jupiter-<side>-spot.png`: azimuth -48.0, elevation +5.0

| ring | seen? | Sol u mm | Anti u mm | changes sides | Sol v mm | Anti v mm | v moves mm |
|---|---|---:|---:|---|---:|---:|---:|
| `bands` ring 1 | no | +0.13 | +6.12 | sector | +1.27 | +2.58 | 1.311 |
| `bands` ring 2 | no | +11.51 | -7.01 | sector | +1.61 | +2.06 | 0.444 |
| `bands` ring 3 | no | +11.51 | -13.25 | sector | +3.33 | +2.48 | 0.846 |
| `bands` ring 4 | no | +0.14 | -6.38 | sector | +4.63 | +3.36 | 1.271 |
| `bands` ring 5 | no | -11.31 | +6.80 | sector | +4.02 | +3.61 | 0.408 |
| `bands` ring 6 | no | -11.24 | +12.98 | sector | +2.73 | +3.62 | 0.884 |
| `bands` ring 7 | no | -0.13 | +6.37 | sector | -4.61 | -3.34 | 1.272 |
| `bands` ring 8 | no | +11.19 | -6.72 | sector | -4.49 | -4.09 | 0.402 |
| `bands` ring 9 | no | +11.19 | -12.92 | sector | -2.94 | -3.82 | 0.881 |
| `bands` ring 10 | no | -0.15 | -6.04 | sector | -1.85 | -3.15 | 1.301 |
| `bands` ring 11 | no | -11.49 | +6.99 | sector | -1.74 | -2.18 | 0.444 |
| `bands` ring 12 | no | -11.41 | +13.14 | sector | -3.85 | -3.02 | 0.835 |
| `spot` ring 1 | yes | -0.21 | +6.15 | yes | -6.55 | -5.36 | 1.196 |
| `collar` ring 1 | yes | -0.21 | +6.15 | yes | -6.55 | -5.36 | 1.196 |

**2 of the 2 rings a reader can see at this frame change sides.**
Their heights move by up to 1.196 mm as well, and that is
expected rather than a fault. Carried back into the globe's
own frame, this camera looks down longitude -47.84, and the
reflection is solved about -33.77 -- a different meridian. A
reflection about a meridian the camera is NOT looking down
moves a marking up or down the ball as well
as across it. At the two frames the product itself is
photographed at, which is what the reflection was solved for,
the facing table above is the measurement that matters.
The Great Red Spot -- the one feature this globe is
recognised by, and on this world the only marking of any
kind that carries a longitude -- crosses from one side of
the ball to the other and stays in front of the camera.

## What the mirror buys, in millimetres

A swing has to be big enough to see across a table, and on Jupiter
that is the whole question, so it is reported in the units a reader
has: degrees of great-circle arc, and millimetres on the globe the
feature is drawn on. One degree of arc on a globe of diameter d is
pi * d / 360 -- a degree is a 360th of the circumference, not a
180th -- so on Jupiter's 26.97 mm globe it is 0.2354 mm.

The distance column is the great-circle separation between where the
feature sits on the Sol piece and where it sits on the Anti-Sol one,
not the longitude difference: latitude does not move, so a swing of
L degrees of longitude at latitude p covers LESS than L degrees of
arc, and at large swings much less. Both are given.

| world | marking | longitude on Sol | on Anti-Sol | swing, degrees of longitude | distance, degrees of arc | distance, mm |
|---|---|---:|---:|---:|---:|---:|
| mercury | `plains` ring 1 | +22.57 | -122.55 | -145.12 | 129.18 | 15.53 |
| mercury | `plains` ring 2 | +49.14 | -149.11 | +161.75 | 156.86 | 18.86 |
| mercury | `plains` ring 3 | +117.98 | +142.04 | +24.06 | 22.68 | 2.73 |
| mercury | `plains` ring 4 | +138.56 | +121.46 | -17.10 | 16.91 | 2.03 |
| mercury | `plains` ring 5 | -153.99 | +54.02 | -151.99 | 102.27 | 12.30 |
| mercury | `plains` ring 6 | -105.36 | +5.38 | +110.74 | 110.33 | 13.27 |
| mercury | `plains` ring 7 | +161.38 | +98.65 | -62.73 | 62.72 | 7.54 |
| mercury | `caloris_rim` ring 1 | -50.00 | -49.97 | +0.03 | 0.03 | 0.00 |
| mercury | `caloris_floor` ring 1 | -50.00 | -49.98 | +0.02 | 0.02 | 0.00 |
| venus | `highland` ring 1 | -168.49 | -79.22 | +89.27 | 85.44 | 12.32 |
| venus | `highland` ring 2 | -103.04 | -144.67 | -41.63 | 40.91 | 5.90 |
| venus | `highland` ring 3 | +134.38 | -22.09 | -156.48 | 37.20 | 5.37 |
| venus | `highland` ring 4 | +15.59 | +96.71 | +81.12 | 71.78 | 10.35 |
| venus | `highland` ring 5 | +13.70 | +98.59 | +84.89 | 83.28 | 12.01 |
| venus | `highland` ring 6 | +95.05 | +17.24 | -77.81 | 67.84 | 9.79 |
| venus | `highland` ring 7 | +13.58 | +98.71 | +85.12 | 64.12 | 9.25 |
| venus | `highland` ring 8 | +115.15 | -2.85 | -118.00 | 41.19 | 5.94 |
| venus | `lowland` ring 1 | -92.68 | -155.03 | -62.35 | 46.24 | 6.67 |
| venus | `lowland` ring 2 | +60.79 | +51.51 | -9.28 | 8.74 | 1.26 |
| venus | `lowland` ring 3 | +89.68 | +22.62 | -67.06 | 45.01 | 6.49 |
| jupiter | `spot` ring 1 | -48.00 | -19.54 | +28.46 | 26.35 | 6.20 |
| jupiter | `collar` ring 1 | -48.00 | -19.54 | +28.46 | 26.35 | 6.20 |

Jupiter's row is the one this correction exists for. The spot swings
+28.46 degrees of longitude, which at latitude -22.00 is 26.35 degrees
of great-circle arc and 6.20 mm on a globe 26.97 mm across. The spot
itself is 3.06 mm long, so it moves by about two of its own lengths.

## Adjusting the meridian until it clears

At the plain mean of the two cameras, Venus does not clear: Atalanta
Planitia reads +0.367 on the Sol piece at the hero frame and falls to
+0.266 on the mirrored piece. The brief's instruction for that case
is to move the meridian until it clears rather than to accept it, so
the meridian was swept at a hundredth of a degree and every
adjustment scored on the worst margin any Sol-clearing feature has
left on the Anti-Sol piece. Mercury is swept the same way and
reported beside it, as the evidence that its mean needed nothing.

Jupiter is swept over a wider range, at the same hundredth of a
degree, because its problem is the opposite one: its mean CLEARS
comfortably and buys nothing, so the sweep is looking for how far
the meridian can be pushed rather than whether it has to move at
all. Belt sectors are excluded from the sweep for the same reason
they are excluded from the gate: they are scored whole, above.

Two scores are reported for every world, and only ONE of them is the
gate. The gate is the ring-centroid margin, which is what a FEATURE
faces at, and it is the score Mercury and Venus were sealed on. The
every-vertex margin beside it is the stricter reading the Jupiter
brief asked for: not a feature's facing but its worst single vertex.
Mercury and Venus do not clear that stricter score at any adjustment
and never did -- a ring lying along the limb has vertices that dip
under the floor on BOTH pieces, which is the same thing the vertex
counts in the ring table already show and which their own reports
recorded when they were written. Nothing about those two worlds has
changed here; the column is reported so that Jupiter's figure can be
read against something. Jupiter clears the stricter score too, over
a range 37 degrees wide, which is why the stricter score is the one
its adjustment was chosen on.

| world | scored on | adjustments that clear | mean clears | best adjustment | its worst margin | taken | its worst margin |
|---|---|---|---|---:|---:|---:|---:|
| mercury | ring centroid | -1.97 to +4.47 degrees | yes | +1.44 | +0.0898 | +0.00 | +0.0523 |
| mercury | every vertex | none, at any adjustment | no | -0.71 | -0.1245 | +0.00 | -0.1459 |
| venus | ring centroid | +2.26 to +9.55 degrees | no | +4.98 | +0.0367 | +5.00 | +0.0365 |
| venus | every vertex | none, at any adjustment | no | -0.32 | -0.1105 | +5.00 | -0.2549 |
| jupiter | ring centroid | -21.77 to +27.79 degrees | yes | +3.01 | +0.2733 | +15.00 | +0.2061 |
| jupiter | every vertex | -15.55 to +21.57 degrees | yes | +3.01 | +0.1768 | +15.00 | +0.0995 |

Mercury's mean clears with 0.05 in hand and is taken unchanged.
Venus's does not, and is moved +5.00 degrees -- the whole number
beside the sweep's own maximum at +4.98, which costs 0.0002 of margin
and reads as a decision rather than as an optimiser's last two
digits. What that adjustment amounts to is that Venus's reflection is
solved about the HERO camera's own meridian instead of the mean of
the two, because the hero frame is the one Atalanta is tight at.

Jupiter's mean clears and is still refused, and the reason is the
swing column. Reflecting a feature at longitude L about a meridian C
lands it at 2C - L, so the swing is twice the distance from the
feature to the meridian, and this world's spot is 0.77 degrees from
its mean meridian. Taking the mean and stopping would move the Great
Red Spot from -48.00 to -49.54: 1.54 degrees of longitude, 1.42 of
great-circle arc and 0.33 mm on a globe 26.97 mm across -- a piece
whose hash changed and whose appearance did not. It is also the
WRONG WAY: the spot is already west of the mean meridian, so a
reflection about that mean carries it a third of a millimetre
further west, not east.

The adjustment taken is +15.00 degrees. It is not the sweep's own
maximum, because on this world the maximum buys the least: the rule
is to take the LARGEST whole degree that still keeps at least half
the margin the best adjustment could buy, scored on the stricter
every-vertex column. +16 keeps 0.0865 of a 0.1768 peak and falls
short of half; +15 keeps 0.0995 and is what is taken. It puts the
spot at longitude -19.54: a swing of 28.46 degrees of longitude,
which at latitude -22 is 26.35 degrees of great-circle arc and 6.20
mm on a ball 26.97 mm across. The spot is 3.06 mm long, so it moves
by two of its own lengths.

## What the mean meridian costs

If the reflection used each frame's own C the facing would be
preserved to the last decimal, and there would be two different
Anti-Sol pieces. One meridian serves both frames, so each frame is
read off a reflection solved some degrees away from it -- about five
either way on Mercury, and on Venus about a fifth of a degree at the
hero frame and about ten at the state sheet, which is where the
adjustment put it. This is the size of that: the largest facing
change of any ring centroid, and the largest change of any single
ring vertex, on each world. It is the price of the correction and it
is paid in how squarely a marking faces the lens, never in whether
it is on the near hemisphere at all.

Belt sectors are left out of this table for the same reason they are
left out of the gate: a sector's facing changes by whatever the
reflection does to the seams, and none of that is a change to the
belt. Every other ring on all three worlds is here.

| world | frame | largest centroid change | largest vertex change |
|---|---|---:|---:|
| mercury | hero | 0.1586 | 0.1612 |
| mercury | state sheet | 0.1392 | 0.1412 |
| venus | hero | 0.0607 | 0.0637 |
| venus | state sheet | 0.2399 | 0.3029 |
| jupiter | hero | 0.1010 | 0.1976 |
| jupiter | state sheet | 0.0020 | 0.0501 |

## Verdict

Nothing that cleared the +0.30 floor on a Sol piece fails it on
its mirrored Anti-Sol twin, at either photographed frame, on any
of the three worlds. Mercury holds at the plain mean of the two
cameras; Venus holds at the mean moved +5.00 degrees to clear
Atalanta Planitia; Jupiter holds at the mean moved +15.00 degrees,
which was chosen to make the swing visible rather than to clear a
floor, and which leaves the worst spot or collar vertex 0.0995
above it. Each adjustment is recorded above with the sweep that
chose it.

Measured by `measure/mirror_meridian.py` on the exact rings
`parts/markings.markings_for` returns and the exact cameras in
`snap_frames.py`.
