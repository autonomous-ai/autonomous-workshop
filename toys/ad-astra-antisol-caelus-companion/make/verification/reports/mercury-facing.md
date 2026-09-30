# Mercury's markings against the camera

Dot product of each marking's own direction against the view axis,
at the two frames the product is photographed from, on both armies.
+1 is dead-on, 0 is the limb, -1 is the far side.

Mercury's obliquity is 0.03 degrees, the smallest in the set, so the
mirrored lean that distinguishes the two armies moves a marking by
almost nothing and the Sol and Anti-Sol columns agree to two decimals.
That is the planet, not a mistake in the mirror: Earth at 23.44
degrees and Uranus at 97.77 separate widely on the same measurement.

## The hero frame: azimuth -55, elevation 22

| marking | latitude | longitude | Sol | Anti-Sol | faces the camera |
|---|---:|---:|---:|---:|---|
| `plain_north_west` | +18.0 | +24.0 | +0.28 | +0.28 | yes |
| `plain_equatorial` | +6.0 | +48.0 | -0.17 | -0.17 | no |
| `plain_south_lead` | -22.0 | +118.0 | -0.99 | -0.99 | no |
| `plain_south_mid` | -10.0 | +138.0 | -0.95 | -0.95 | no |
| `plain_high_north` | +38.0 | +205.0 | +0.10 | +0.10 | yes |
| `plain_far_side` | -6.0 | +255.0 | +0.55 | +0.55 | yes |
| `plain_trailing` | +2.0 | +162.0 | -0.73 | -0.73 | no |
| `caloris` | +30.0 | -50.0 | +0.99 | +0.99 | yes |

3 of the 7 plains face this camera; the best of them is +0.55.

## The state sheet frame: azimuth -45, elevation 35.264

| marking | latitude | longitude | Sol | Anti-Sol | faces the camera |
|---|---:|---:|---:|---:|---|
| `plain_north_west` | +18.0 | +24.0 | +0.46 | +0.46 | yes |
| `plain_equatorial` | +6.0 | +48.0 | +0.02 | +0.02 | yes |
| `plain_south_lead` | -22.0 | +118.0 | -0.94 | -0.94 | no |
| `plain_south_mid` | -10.0 | +138.0 | -0.90 | -0.90 | no |
| `plain_high_north` | +38.0 | +205.0 | +0.14 | +0.13 | yes |
| `plain_far_side` | -6.0 | +255.0 | +0.35 | +0.35 | yes |
| `plain_trailing` | +2.0 | +162.0 | -0.71 | -0.71 | no |
| `caloris` | +30.0 | -50.0 | +0.99 | +0.99 | yes |

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

Measured by `measure/mercury_facing.py` on the exact rings in
`parts/mercury_atlas.py` and the exact cameras in `snap_frames.py`.
