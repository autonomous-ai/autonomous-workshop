---
title: Camera model, focal length and perspective
tags: [camera, pinhole, focal-length, field-of-view, perspective, phone, telephoto, wide-angle]
aliases: [angle of view, fov, 35mm equivalent, crop factor, lens compression, perspective distortion, smartphone lens]
sources:
  - https://en.wikipedia.org/wiki/Pinhole_camera_model
  - https://en.wikipedia.org/wiki/Angle_of_view_(photography)
  - https://en.wikipedia.org/wiki/Perspective_distortion
  - https://www.howtogeek.com/iphone-camera-lenses-explained-what-do-wide-ultra-wide-and-telephoto-lenses-do/
related: [lens-distortion, single-view-metrology, camera-pose-from-a-photo, perspective-and-hidden-views, measuring-reference-photos]
updated: 2026-09-23
---

# Camera model, focal length and perspective

Every measurement taken off a photo assumes a camera model. This page is the
model and the numbers that tell you how far a reference photo is from the
orthographic view a CAD elevation is. Read it before trusting any ratio of
two lengths that sit at different depths.

## The pinhole model

A point `(X, Y, Z)` in camera coordinates projects to image coordinates

```text
x = f · X / Z        y = f · Y / Z
```

where `f` is the focal length (optical centre to image plane). Everything
about perspective follows from the division by depth `Z`: an object's image
size is inversely proportional to its distance. The model is a first-order
approximation only — it has no lens distortion ([[lens-distortion]]), no blur
and no pixel grid.

## Size is inversely proportional to distance

The apparent size ratio of two equal objects equals the inverse ratio of
their distances from the camera. For a single object of depth `D` whose near
face is at distance `Z`:

```text
near face scale / far face scale = (Z + D) / Z
```

| camera distance Z | object depth D | near face drawn larger by |
|---|---|---|
| 300 mm (phone held close) | 100 mm | 1.33× |
| 1000 mm | 100 mm | 1.10× |
| 3000 mm | 100 mm | 1.03× |

(Computed from the formula.) So a close phone shot of a desk object is not an
elevation: the side nearest the lens is a third larger than the back. Measure
widths only on a face roughly perpendicular to the view and at one depth, or
take the ratio from a far shot.

## Perspective depends on position, not on the lens

Two shots from the same camera position have identical perspective geometry
whatever the lens; focal length only crops. "Wide-angle distortion" (near
things huge, noses big) is really *close camera* distortion, and "telephoto
compression" (depth flattened) is *far camera*. The practical rule for a
reference photo that should approximate orthographic: stand far back and zoom
in, never step in with the wide lens. Portrait practice uses 85–135 mm
(35 mm-equivalent) for the same reason.

## Angle of view

For a rectilinear lens, `α = 2 · arctan(d / 2f)` with `d` the sensor dimension.
35 mm-equivalent focal lengths refer to a 36 × 24 mm frame, diagonal 43.3 mm.

| equivalent f | diagonal | horizontal | vertical |
|---|---|---|---|
| 24 mm | 84.1° | 73.7° | 53.1° |
| 50 mm | 46.8° | 39.6° | 27.0° |
| 85 mm | 28.6° | 23.9° | 16.1° |
| 135 mm | ~20° | ~16° | ~11° |

A sensor smaller than 35 mm narrows the view by its crop factor: a 50 mm lens
on a 1.6× crop body frames like 80 mm.

## Phone cameras

Phones quote 35 mm-equivalent focal lengths. Recent iPhones: main camera
about 24–26 mm (1×), ultra-wide about 13 mm (0.5×), telephoto 77 mm (3×),
100 mm (4×) or 120 mm (5×) depending on model, plus 28 mm and 35 mm crops of
the main sensor. Diagonal angles of view from the formula above: 13 mm ≈ 118°,
26 mm ≈ 80°, 77 mm ≈ 31°, 120 mm ≈ 20°.

What that means for a reference photo:

- **0.5× ultra-wide**: strong barrel distortion and extreme near/far scaling —
  do not measure off it.
- **1× main**: usable if the camera was at least several object-lengths away;
  a close product shot at 1× is the common case of a front face drawn 20–30 %
  large.
- **3×–5× telephoto**: closest to orthographic a phone gets; prefer it, and
  ask for it when requesting new photos ([[image-types-and-views]]).

EXIF usually records the focal length (and often its 35 mm equivalent); read
it before deciding how much perspective to correct.

## Checks before measuring a photo

- Is the measured length at one depth? If not, correct by `(Z + D) / Z` or
  measure on another view.
- Which lens? Ultra-wide shots are for identification only.
- Straight edges near the frame border bowed? Correct distortion first
  ([[lens-distortion]]).
- Do parallel edges converge? Then vanishing-point methods apply
  ([[single-view-metrology]]).
