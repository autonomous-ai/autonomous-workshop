# Neptune's markings against the camera

Dot product of each marking against the view axis, at the two
frames the whole set is photographed from and at the per-world
frames the two Neptunes are rendered at on their own, on both
armies. +1 is dead-on, 0 is the limb, -1 is the far side.

Every number below is measured at the exact cameras `snap_frames.py`
and `world_views.py` declare, on the exact latitudes and the exact
ring `parts/neptune_atlas.py` hands the build. The yardstick is the
**+0.30** facing floor the archived placement was solved against.

## What this revision changed about this question

The archived build's clouds were eight SHORT streaks, so each had a
longitude and each could be on the wrong face; keeping them visible
was a solved optimisation over eight latitudes and eight longitudes
against four cameras at once.

This revision's clouds are three CLOSED latitude bands. A closed
band spans every longitude, so there is no longitude to solve and no
way for one to be hidden by rotation: at any camera, some arc of it
faces the lens as squarely as its own latitude allows. The whole
placement problem is gone, and with it most of this report's former
evidentiary value. That is a consequence of the owner's decision and
it is stated plainly rather than re-dressed as a check that passed.

What is left worth measuring is the DARK SPOT, which is short, and
which requirement 2 says must not move.

## Where each camera is looking

Neptune's obliquity is 28.32 degrees and a Sol world leans its north
pole toward +X, so the two armies do not share a sub-point and the
Sol piece's cameras both look DOWN on its northern hemisphere.

| frame | azimuth | elevation | army | sub-latitude | sub-longitude |
|---|---:|---:|---|---:|---:|
| hero | -55 | 22.000 | Sol | +35.6 | -69.1 |
| hero | -55 | 22.000 | Anti-Sol | +4.4 | -49.6 |
| state sheet | -45 | 35.264 | Sol | +51.5 | -67.9 |
| state sheet | -45 | 35.264 | Anti-Sol | +13.6 | -36.4 |
| per-world hero | -55 | 22.000 | Sol | +35.6 | -69.1 |
| per-world hero | -55 | 22.000 | Anti-Sol | +4.4 | -49.6 |
| per-world spot | -82 | 0.000 | Sol | +3.8 | -82.9 |
| per-world spot | -82 | 0.000 | Anti-Sol | -3.8 | -82.9 |
| per-world opposite | 98 | 0.000 | Sol | -3.8 | +97.1 |
| per-world opposite | 98 | 0.000 | Anti-Sol | +3.8 | +97.1 |
| per-world polar | 0 | 61.680 | Sol | +90.0 | +0.0 |
| per-world polar | 180 | 61.680 | Anti-Sol | +90.0 | +90.0 |

## The three bands, at every frame

The best dot product any point of each band reaches, walked at one
degree of longitude and a tenth of a degree of latitude rather than
taken from the formula. A closed band cannot be hidden by rotation,
but it can be hidden by LATITUDE: its whole circle falls behind the
limb when the camera's sub-latitude is more than 90 degrees from it.
That does happen on this globe and the table says where.

| band | latitudes | hero Sol | hero Anti-Sol | state sheet Sol | state sheet Anti-Sol |
|---|---|---:|---:|---:|---:|
| `b1` | -46 to -41 | +0.23 | +0.70 | -0.04 | +0.58 |
| `b2` | +11 to +15 | +0.94 | +0.99 | +0.80 | +1.00 |
| `b3` | +30 to +33 | +1.00 | +0.90 | +0.95 | +0.96 |

The worst any band does at either product frame on either army is
**-0.04**, against the archived floor of +0.30.

**2 of the 12 band/frame/army cases fall below that floor, and
1 of those falls behind the limb outright:**

- `b1` at the hero frame on the Sol piece: +0.23
- `b1` at the state sheet frame on the Sol piece: -0.04 -- **behind the limb**

This is not a placement fault and it is not repairable without
moving a band, which the owner's instruction forbids. It is the
same geometric fact the archived build recorded about its own
two southernmost streaks: the Sol piece leans its north pole
toward the lens, so both of its cameras look DOWN on the
northern hemisphere -- the state-sheet sub-point sits at +51.5 --
and a camera there reaches a marking at latitude L at best at
cos(51.5 - L), whatever longitude it is drawn at. At a floor of
+0.30 that camera cannot reach anything south of about -21.

`b1` is drawn at -46 to -41, which is south of that line. On the
ANTI-Sol piece, which leans the same pole away, it reaches
+0.70 at the hero frame and +0.58 at the state sheet and is
plainly visible. So `b1` is, in this build, an ANTI-SOL-ONLY
FEATURE at the set's two photographed frames -- exactly the role
`s1` and `s2` held in the archived build, inherited by the band
that stands where they stood. It is recorded here, in the
product's limitations and in the spec rather than left for a
reader of the Sol piece to report as a missing band.

Across the per-world frames as well, rather than asserted:

| frame | army | `b1` best |
|---|---|---:|
| per-world hero | Sol | +0.23 |
| per-world hero | Anti-Sol | +0.70 |
| per-world spot | Sol | +0.71 |
| per-world spot | Anti-Sol | +0.80 |
| per-world opposite | Sol | +0.80 |
| per-world opposite | Anti-Sol | +0.71 |
| per-world polar | Sol | -0.66 |
| per-world polar | Anti-Sol | -0.66 |

The two level per-world frames, `spot` and `opposite`, show all
three bands on both pieces, and `opposite` is the frame that
shows them unbroken. The per-world `hero` frame is the product
frame and carries the same figure. The polar frame looks down
the leaning north pole, so `b1` is behind the limb there on both
armies by construction -- that frame exists to show the pole,
not the southern band. So `b1` is in the evidence, at the frames
that can reach it, and the pictures say which those are.

## The dark spot, at every frame

The spot's own centre, and -- because a 5.35 mm oval is not a point
-- the worst any VERTEX of its ring reaches at the same camera.

| frame | army | centre | worst vertex | archived centre | |
|---|---|---:|---:|---:|---|
| hero | Sol | +0.53 | +0.43 | +0.53 | unmoved |
| hero | Anti-Sol | +0.86 | +0.76 | +0.86 | unmoved |
| state sheet | Sol | +0.28 | +0.16 | +0.28 | unmoved |
| state sheet | Anti-Sol | +0.70 | +0.56 | +0.70 | unmoved |
| per-world hero | Sol | +0.53 | +0.43 | -- | |
| per-world hero | Anti-Sol | +0.86 | +0.76 | -- | |
| per-world spot | Sol | +0.86 | +0.75 | -- | |
| per-world spot | Anti-Sol | +0.91 | +0.80 | -- | |
| per-world opposite | Sol | -0.86 | -0.93 | -- | |
| per-world opposite | Anti-Sol | -0.91 | -0.97 | -- | |
| per-world polar | Sol | -0.37 | -0.48 | -- | |
| per-world polar | Anti-Sol | -0.37 | -0.48 | -- | |

Every product-frame figure reproduces the archived one to two
decimal places, on both armies: **the dark spot did not move.**
Its +0.28 at the Sol state sheet is its CEILING rather than a
placement mistake -- at latitude -22, against a sub-point of
+51.5, no longitude does better -- and that was true of the
archived build for the same reason.

## The per-world frames, and what they now show

- `hero` (azimuth -55, elevation 22): the product's own azimuth: three closed white bands running the whole way round a blue globe, unequal in width and unevenly spaced, with the dark oval below the lowest of them
- `spot` (azimuth -82, elevation 0): the Great Dark Spot in the middle of the picture, a clean oval about twice as wide as it is tall, low and south of the equator, with bare blue globe all round it and the nearest white band a clear band-width below it
- `opposite` (azimuth 98, elevation 0): the far face: the same three white bands, unbroken, because a closed band has no far face -- and no dark spot anywhere in the picture
- `polar`, sol (azimuth 0, elevation 61.7): down the north pole of the sol world
- `polar`, anti (azimuth 180, elevation 61.7): down the north pole of the anti world

The `opposite` frame is the one that changed meaning. On the
archived build it was the proof of the correction's central negative
requirement -- no streak circles the planet -- because the far face
carried only the ends of streaks and bare globe. On this revision it
shows the same three bands, unbroken, because that is what a closed
band is. It is kept and rendered for exactly that reason: it is now
the picture that proves the bands DO ring the planet, which is what
the owner asked for and what the beach-ball reading follows from.

