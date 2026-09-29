---
title: Single-view metrology
tags: [metrology, vanishing-point, cross-ratio, perspective, height, measurement, homography]
aliases: [vanishing line, horizon line, measuring from one photo, criminisi, reference height, projective geometry]
sources:
  - https://www.microsoft.com/en-us/research/wp-content/uploads/1999/01/Criminisi_iccv1999.pdf
  - https://www.robots.ox.ac.uk/~lav/Papers/criminisi_etal_ijcv2000/criminisi_etal_ijcv2000.html
  - https://en.wikipedia.org/wiki/Vanishing_point
  - https://en.wikipedia.org/wiki/Cross-ratio
  - https://pmc.ncbi.nlm.nih.gov/articles/PMC5795906/
related: [camera-model-and-focal-length, lens-distortion, camera-pose-from-a-photo, scale-anchors, perspective-and-hidden-views]
updated: 2026-09-23
---

# Single-view metrology

One perspective photo, with no camera calibration, still gives real
measurements if the scene contains straight parallel edges and one known
length. This is the method (Criminisi, Reid and Zisserman, *Single View
Metrology*, ICCV 1999 / IJCV 2000) behind measuring a person's height from a
security camera, and it applies to reading an object off a photo taken on a
table.

## Vanishing points and the vanishing line

- Lines parallel in 3D converge in the image to one **vanishing point**. The
  vanishing point is the image of that 3D direction, so it tells you the
  direction.
- The vanishing points of all directions within a plane lie on one line, the
  plane's **vanishing line**; for the ground or a tabletop it is the horizon.
- One-point perspective: the image plane is perpendicular to one set of
  parallels. Two-point: the image plane cuts two axes. Three-point: the
  camera is tilted, so verticals converge too.

The vanishing line partitions the scene: a point imaged *on* it is at the
camera's height above the reference plane, a point above it is farther from
the plane, a point below is closer.

## What one view gives you

With the vanishing line `l` of a reference plane (the table, the floor) and
the vanishing point `v` of a direction not parallel to it (usually vertical),
you can compute:

1. **Distances between parallel planes** in the reference direction: heights
   of points above the table, up to one common scale factor.
2. **Ratios of lengths of parallel segments and ratios of areas** on the
   reference plane or any plane parallel to it.
3. **The camera's position.**

One known length in the reference direction fixes the scale, and then every
other measurement in that direction is metric. Areas on two different
parallel planes cannot be compared directly unless one region is first
projected onto the other plane.

## Measuring a height with a reference

The top `t` and base `b` of an upright object, the vertical vanishing point
`v` and the point `i` where line `tb` meets the vanishing line are four
collinear points. Their **cross-ratio**

```text
(A, B; C, D) = (AC · BD) / (BC · AD)
```

is preserved by perspective projection, so its image value gives the ratio of
the object's height to the camera's height above the plane. A second upright
of known height in the same scene (a door, a can, a box) converts that ratio
to millimetres. The top and base must correspond: the line joining them must
pass through the vertical vanishing point.

Published accuracy: a person computed at 178.8 cm against a true 180 cm, and
190.6 cm against 190 cm on a distortion-corrected security image. The 3-sigma
uncertainty shrank as more reference heights were added (a filing cabinet and a
table). Error comes from locating the vanishing line, the vanishing point and
the top and base points, and the method propagates it to a stated uncertainty.

## Recovering focal length and principal point

For square pixels and zero skew, the directions of two orthogonal vanishing
points `v1` and `v2` are perpendicular, which gives (derived from the pinhole
model):

```text
(v1 - p) · (v2 - p) + f² = 0        p = principal point (often the image centre)
```

With three mutually orthogonal vanishing points, the principal point is the
orthocentre of their triangle. Both break down with weak perspective (long
focal length): the vanishing points run off towards infinity and cannot be
located accurately. That is the telephoto shot you wanted for measuring, so
use the ratio methods above there.

## Using it on a reference photo

1. Correct lens distortion first ([[lens-distortion]]).
2. Pick the reference plane (the surface the object stands on) and trace two
   pairs of parallel edges on it: tiles, a table edge, the object's own base
   edges. Intersect each pair to get the vanishing line.
3. Trace two or more verticals (object edges, a wall corner) for the vertical
   vanishing point.
4. Find one known length in the scene ([[known-object-sizes]]); prefer one
   standing on the same plane.
5. Compute heights by cross-ratio; compute plan dimensions as ratios on the
   plane. Record the result as `[inferred]`, with the reference used
   ([[scale-anchors]]).

If the photo shows no parallel edges and no known object, single-view
metrology cannot help, and the scale stays `[assumed]`.
