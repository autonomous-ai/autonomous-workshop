# Mercury's markings against the camera

Dot product of each marking's own direction against the view axis,
at the two frames the product is photographed from, on both armies.
+1 is dead-on, 0 is the limb, -1 is the far side.

Mercury's obliquity is 0.03 degrees, the smallest in the set, so the
mirrored lean that distinguishes the two armies moves a marking by
almost nothing -- 0.06 degrees between the two pieces. That is the
planet rather than a mistake: Earth at 23.44 degrees and Uranus at
97.77 separate widely on the same measurement.

**It is also why the two columns below no longer agree.** Until the
Antisol Mirror revision they did, to two decimals, because both
armies carried the map at the same longitudes and the lean had
nothing to give -- which is the defect that revision corrects. The
Anti-Sol piece now draws every marking at a MIRRORED longitude,
reflected about that piece's own facing meridian at -49.99 degrees,
and the `longitude` column below is the SOL piece's; the Anti-Sol
longitude is beside it. `measure/mirror-meridian.md` is the whole
transform and `parts/markings.markings_for` is where it lives.

What has NOT changed is how squarely each marking faces the lens.
The reflection preserves the facing dot product exactly at the
meridian it is solved about, and the two photographed frames are
five degrees either side of it, so the two columns below are very
nearly the same set of numbers dealt to different plains rather than
a set of worse ones. `measure/mirror-meridian.md` measures that
residual: no ring centroid moves by more than 0.159.

## The hero frame: azimuth -55, elevation 22

| marking | latitude | Sol longitude | Anti-Sol longitude | Sol | Anti-Sol | faces the camera |
|---|---:|---:|---:|---:|---:|---|
| `plain_north_west` | +18.0 | +24.0 | -124.0 | +0.28 | +0.43 | yes |
| `plain_equatorial` | +6.0 | +48.0 | -148.0 | -0.17 | -0.01 | no |
| `plain_south_lead` | -22.0 | +118.0 | +142.0 | -0.99 | -0.96 | no |
| `plain_south_mid` | -10.0 | +138.0 | +122.0 | -0.95 | -0.98 | no |
| `plain_high_north` | +38.0 | +205.0 | +55.0 | +0.10 | -0.02 | no |
| `plain_far_side` | -6.0 | +255.0 | +5.0 | +0.55 | +0.42 | yes |
| `plain_trailing` | +2.0 | +162.0 | +98.0 | -0.73 | -0.81 | no |
| `caloris` | +30.0 | -50.0 | -50.0 | +0.99 | +0.99 | yes |

3 of the 7 plains face this camera; the best of them is +0.55.

## The state sheet frame: azimuth -45, elevation 35.264

| marking | latitude | Sol longitude | Anti-Sol longitude | Sol | Anti-Sol | faces the camera |
|---|---:|---:|---:|---:|---:|---|
| `plain_north_west` | +18.0 | +24.0 | -124.0 | +0.46 | +0.33 | yes |
| `plain_equatorial` | +6.0 | +48.0 | -148.0 | +0.02 | -0.12 | no |
| `plain_south_lead` | -22.0 | +118.0 | +142.0 | -0.94 | -0.97 | no |
| `plain_south_mid` | -10.0 | +138.0 | +122.0 | -0.90 | -0.88 | no |
| `plain_high_north` | +38.0 | +205.0 | +55.0 | +0.14 | +0.24 | yes |
| `plain_far_side` | -6.0 | +255.0 | +5.0 | +0.35 | +0.46 | yes |
| `plain_trailing` | +2.0 | +162.0 | +98.0 | -0.71 | -0.63 | no |
| `caloris` | +30.0 | -50.0 | -50.0 | +0.99 | +0.99 | yes |

4 of the 7 plains face this camera; the best of them is +0.46.

## What the numbers decided

**The plains did not move.** Three of the seven face the hero camera
and four face the state sheet, the best at +0.55 and +0.46. That is
an ordinary albedo map seen from one side, not a pattern hiding round
the back: Venus's and Jupiter's markings measured -0.03 and -0.49
before they were carried, with no rendered view showing any of them.
Mercury's patches were always in frame -- they could not be seen
because `dark_gray` on `gray` is 21.8 luma levels on a 13.78 mm ball
(`measure/mercury-tone-separation.md`), which is a contrast problem
and is what this revision repairs. Carrying them in longitude would
have moved a pattern that was not lost and thrown away the centres
the set already had.

**Caloris was placed by this table.** Its latitude is fixed at +30 by
the Wish; its longitude is free because this set fixes no meridian on
Mercury. A feature at +30 faces a frame most squarely when its
longitude matches that frame's azimuth, and the two azimuths are -55
and -45, so -50 is the midpoint. It measures +0.99 and +0.99 -- the
most nearly dead-on any marking in this set gets, at both frames and
on both armies.

**And -50 is why Caloris barely moves under the mirror.** The
Anti-Sol piece reflects about -49.99, so the basin sits within a
fortieth of a degree of its own mirror's fixed point and the seven
plains swing around it. The one feature this globe is recognised by
stays square to the lens on both pieces while the terrain either
side of it changes hands, which is what the correction was for.

Measured by `measure/mercury_facing.py` on the exact rings in
`parts/mercury_atlas.py` and the exact cameras in `snap_frames.py`.
