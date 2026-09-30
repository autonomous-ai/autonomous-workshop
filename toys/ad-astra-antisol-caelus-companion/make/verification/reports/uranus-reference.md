# What the two Uranus references actually carry

Measured on the sealed images themselves rather than described. Luma is
Rec. 709 on 0..255; a column's value is the 75th percentile of the ball
pixels in it, which follows the lighter material without chasing the
specular highlight.

## The globe's colour, against the filament it prints in

| | mean RGB | luma |
|---|---|---:|
| `ref/uranus-sol.png`, the ball | 161, 200, 206 | 192.7 |
| `ref/uranus-anti.png`, the ball | 147, 202, 213 | 191.5 |
| `cyan` #00FFFF, the filament | 0, 255, 255 | 200.8 |

**The reference globe is a pale desaturated ice blue and the filament is
a saturated neon.** The references sit around 160, 199, 204 -- red at
four fifths of blue -- and `cyan` is 0, 255, 255, with no red at all.
There is no pale blue in the 13 filaments this set stocks. **That gap
cannot be closed by any choice of marking** and is recorded as a
limitation rather than compensated for.

## How loud the surface is

| army | column luma across the ball | spread |
|---|---|---:|
| Sol | 171.4 to 213.9 | 42.6 |
| Anti-Sol | 177.7 to 219.6 | 42.0 |

The whole ball, limb to limb, spans about 42 luma levels -- and most of
that is the lighting gradient across a sphere, not a marking. **There is
no bold stripe in either image.** What there is is one broad, soft-edged
lighter zone with no boundary a reader could point to: the column
profile rises and falls over a third of the ball rather than stepping.

## Where the lighter region is, and whether it belongs to the piece

| army | brightest column |
|---|---:|
| Sol | +0.20 of the silhouette radius |
| Anti-Sol | -0.55 of the silhouette radius |

**The brightest part of the ball is +0.75 radii apart on the two armies.**
Both images are lit the same way, so a feature of the LIGHT would sit
in the same place in both. This one does not: it moves three quarters of
a radius when the piece is mirrored. **It is carried by the object, not
by the lamp.**

That much is measured. What it does NOT settle is which feature it is.
A polar hood and an equatorial band both mirror with the piece, so the
mirroring alone cannot choose between them, and the camera azimuth of
these two sealed images is not recorded anywhere this run can read -- so
this report does not claim the bright region sits on the leaning side.
What does choose between them is the shape and the planet. The shape:
this region has no edges at all, and a band has two. The planet: Uranus
points a pole at the Sun for forty years at a time, so a bright polar
hood is the feature its atmosphere actually carries and an equatorial
belt is not. The correction takes the hood, at both poles, and
`measure/uranus-facing.md` measures what the built piece then shows at
the product's own cameras: a broad region over the outer face on the
side the piece leans toward, from 0.2 to 0.4 of the silhouette radius
out to the limb, on both armies.

## What is not in either image

- **No ring.** Neither reference shows one anywhere. The ring in this
  revision is an owner instruction that overruled an earlier version of
  its own brief, and it is recorded as that in `product.json`, in the
  design contract and in `measure/uranus-ring.md` -- not as an
  observation.
- **No hard boundary anywhere on the globe.** A flush colour inlay
  cannot reproduce that; `measure/uranus-atlas-resolution.md` has the
  arithmetic.
- **No banding, no storm, no spot, no moon.**

Measured by `measure/uranus_reference_read.py` on the sealed references.
