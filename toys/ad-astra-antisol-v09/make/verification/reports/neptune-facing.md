# Neptune's markings against the camera

Dot product of each marking against the view axis, at the two
frames the whole set is photographed from and at the per-world
frames the two Neptunes are rendered at on their own, on both
armies. +1 is dead-on, 0 is the limb, -1 is the far side.

Every number below is measured on the exact rings
`parts/neptune_atlas.py` hands the build, at the exact cameras
`snap_frames.py` and `world_views.py` declare.  The facing floor this
placement was solved against is **+0.30**, not zero.

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

That last column is the whole reason this brief's previous attempt
failed. A camera whose sub-point is at latitude +51.5 reaches a
marking at latitude L with a dot product of at best cos(51.5 - L),
whatever longitude the marking is drawn at, so at a floor of +0.30
the Sol state-sheet camera cannot reach ANYTHING south of -21.1.
A southern-weighted set of streaks therefore cannot be made to face
that camera by choosing longitudes. Latitude is a lever here, not a
fixed input, and the latitudes below were solved together with the
longitudes rather than chosen first and carried in longitude after.

## Every streak, at the two product frames

Each streak's own centre, and -- because the centre of a 9 mm streak
says little about its ends -- the worst of its ring vertices.

| streak | lat | lon | hero Sol | hero Anti | sheet Sol | sheet Anti | worst vertex, any frame |
|---|---:|---:|---:|---:|---:|---:|---:|
| `s1` * | -52 | -14.5 | -0.17 | +0.44 | -0.39 | +0.37 | -0.67 |
| `s2` * | -37 | -77.6 | +0.29 | +0.66 | +0.02 | +0.44 | -0.16 |
| `s3` | -10 | -102.5 | +0.57 | +0.58 | +0.37 | +0.35 | -0.06 |
| `s4` | +4 | -108.4 | +0.67 | +0.52 | +0.53 | +0.32 | -0.21 |
| `s5` | +17 | -22.2 | +0.70 | +0.87 | +0.64 | +0.97 | +0.40 |
| `s6` | +28 | +18.5 | +0.30 | +0.36 | +0.40 | +0.60 | -0.20 |
| `s7` | +38 | -44.2 | +0.94 | +0.83 | +0.93 | +0.90 | +0.66 |
| `s8` | +47 | -114.9 | +0.81 | +0.34 | +0.86 | +0.30 | -0.17 |

`*` marks a streak the Sol piece's own cameras cannot reach.

| frame | army | streaks at or above +0.30, of 8 |
|---|---|---:|
| hero | Sol | **6** |
| hero | Anti-Sol | **8** |
| state sheet | Sol | **6** |
| state sheet | Anti-Sol | **8** |

The least is 6 of 8, which is the clear majority the brief asks
for, in both frames and on both pieces. The two that fall short of
it on the Sol piece are `s1` and `s2`, at latitudes -52 and -37:
they are ANTI-SOL-ONLY FEATURES and are named as such here, in
`parts/neptune_atlas.py` and in the product's limitations. They are
kept rather than moved north because the reference's clouds are
southern-weighted, because the Anti-Sol piece shows them plainly,
and because two deep southern wisps are what stops the northern six
reading as a ladder.

## The dark spot and its companion

The spot's facing was in the objective the latitudes and longitudes
were solved against, not checked afterwards. Its latitude is not
free: the brief fixes it at -22, the real one.

| marking | lat | lon | hero Sol | hero Anti | sheet Sol | sheet Anti | worst vertex, any frame |
|---|---:|---:|---:|---:|---:|---:|---:|
| `spot` | -22.0 | -65.2 | +0.53 | +0.86 | +0.28 | +0.70 | +0.16 |
| `companion` | -9.1 | -63.2 | +0.71 | +0.94 | +0.49 | +0.82 | +0.45 |

The spot clears the floor at three of the four cameras. At the Sol
state-sheet frame it reaches +0.28, and that is its CEILING rather
than a placement mistake: a marking at latitude -22 can do no
better than +0.28 against a camera whose sub-point is +51.5, at any
longitude at all, and the longitude that reaches it is the one the
spot is drawn at. The brief fixes the latitude; the ceiling follows.
On the other three cameras, and on both per-world spot frames below,
the spot is well clear. The companion clears the floor everywhere.

## The per-world frames

These are the frames `snap/worlds/neptune-*.png` are rendered at, and
they are the frames the brief's placement test is decided on.

- `spot` (azimuth -82, elevation 0): the Great Dark Spot in the middle of the picture, a clean oval about twice as wide as it is tall, low and south of the equator, with its small bright companion cloud just off its upper edge and short white streaks scattered above and below it, none of them reaching round the planet
- `opposite` (azimuth 98, elevation 0): the far face: the ends of the same streaks coming round the two limbs, bare blue globe across the middle, and no dark spot anywhere in the picture
- `polar` (elevation 61.7, azimuth 0 on the Sol piece and 180 on
  the Anti-Sol one): straight down each piece's own leaning north
  pole. The two cameras differ because the lean does: that frame is
  where the mirrored obliquity is plainest.

| marking | per-world spot Sol | per-world spot Anti | per-world opposite Sol | per-world opposite Anti |
|---|---:|---:|---:|---:|
| `s1` | +0.17 | +0.28 | -0.17 | -0.28 |
| `s2` | +0.75 | +0.83 | -0.75 | -0.83 |
| `s3` | +0.91 | +0.94 | -0.91 | -0.94 |
| `s4` | +0.90 | +0.89 | -0.90 | -0.89 |
| `s5` | +0.49 | +0.45 | -0.49 | -0.45 |
| `s6` | -0.14 | -0.21 | +0.14 | +0.21 |
| `s7` | +0.65 | +0.57 | -0.65 | -0.57 |
| `s8` | +0.63 | +0.53 | -0.63 | -0.53 |
| `companion` | +0.92 | +0.94 | -0.92 | -0.94 |
| `spot` | +0.86 | +0.91 | -0.86 | -0.91 |

- `spot`, Sol: 6 of 8 streaks at or above +0.30.
- `spot`, Anti-Sol: 6 of 8 streaks at or above +0.30.
- `opposite`, Sol: 0 of 8 streaks at or above +0.30.
- `opposite`, Anti-Sol: 0 of 8 streaks at or above +0.30.

The `opposite` frame is where the zero is the point. Every one of
the eight streaks is short, so the face opposite the spot carries
nothing but the eastern ends of three of them coming round one limb
and bare blue globe across the middle. A band would have been there
in full. That picture is the proof of the correction's negative
requirement -- no streak circles the planet -- and it is why the
frame is rendered rather than a second decorative angle.
