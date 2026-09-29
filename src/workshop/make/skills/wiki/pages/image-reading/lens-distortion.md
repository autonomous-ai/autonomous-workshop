---
title: Lens distortion
tags: [distortion, barrel, pincushion, lens, calibration, photo, correction]
aliases: [barrel distortion, pincushion distortion, mustache distortion, radial distortion, brown-conrady, fisheye]
sources:
  - https://en.wikipedia.org/wiki/Distortion_(optics)
  - https://en.wikipedia.org/wiki/Pinhole_camera_model
  - https://www.microsoft.com/en-us/research/wp-content/uploads/1999/01/Criminisi_iccv1999.pdf
related: [camera-model-and-focal-length, single-view-metrology, measuring-reference-photos]
updated: 2026-09-23
---

# Lens distortion

Lens distortion bends straight lines. It is a property of the lens, separate
from perspective, which depends only on where the camera stood
([[camera-model-and-focal-length#perspective-depends-on-position-not-on-the-lens]]).
A distorted photo breaks every straight-line method: vanishing points,
cross-ratios and edge-length ratios all assume the pinhole model.

## The three kinds

| kind | what happens | how it looks | typical source |
|---|---|---|---|
| **barrel** | magnification *decreases* away from the optical axis | straight lines bow outward, the image looks spherical | wide-angle and fisheye lenses, zooms at the wide end |
| **pincushion** | magnification *increases* away from the axis | straight lines bow inward toward the centre | telephoto lenses |
| **mustache** | barrel near the centre turning to pincushion at the edge | horizontal lines wave like a moustache | some compact wide lenses |

Radial distortion is zero at the image centre and grows with distance from
it. A part photographed in the middle of the frame is least affected; one
near a corner, most.

## Recognising it in a reference photo

- Find an edge that must be straight — a table edge, a door frame, the
  object's own long edge — and lay a straight line over it. A bow toward or
  away from the centre is distortion. An edge that is straight but tilted is
  perspective, not distortion.
- Check where the object sits in the frame: near the border, assume it is
  distorted unless you checked.
- Ultra-wide phone shots (0.5×) are always strongly barrel-distorted.

## Correcting it

The Brown–Conrady model describes radial and tangential (decentering)
distortion with polynomial coefficients; a negative first radial coefficient
`K1` is barrel, a positive one is pincushion. A division model is often more
accurate for severe distortion.

- **Calibrated correction**: lens-profile databases (Lensfun, DxO) or a
  checkerboard calibration give the coefficients; software warps the image
  with the inverse.
- **Manual correction**: GIMP, Photoshop or ImageMagick distortion filters,
  tuned until known-straight edges are straight.
- Correct before measuring. Single-view metrology corrects radial distortion
  first even on security-camera images ([[single-view-metrology]]).

## What it means for the CAD

- A barrel-distorted photo makes a flat face look domed and a box look
  bulged. Do not model a crown that only the lens put there.
- A silhouette compared against a distorted reference loses likeness at the
  edges however good the model ([[silhouette-likeness]]); crop to the centre
  or correct the reference first.
