---
title: Estimating the camera pose from a photo
tags: [camera, elevation, azimuth, ellipse, horizon, pose, viewpoint, orthographic]
aliases: [camera angle, viewing angle, camera elevation, view direction, circle in perspective, ellipse ratio]
sources:
  - https://smallpond.ca/jim/scale/ellipse.html
  - https://en.wikipedia.org/wiki/Vanishing_point
  - https://www.microsoft.com/en-us/research/wp-content/uploads/1999/01/Criminisi_iccv1999.pdf
  - https://en.wikipedia.org/wiki/Perspective_distortion
related: [camera-model-and-focal-length, single-view-metrology, silhouette-likeness, perspective-and-hidden-views]
updated: 2026-09-23
---

# Estimating the camera pose from a photo

A likeness check renders the model from the camera the reference was taken
from, and a dimension read off an oblique view has to be un-foreshortened.
Both need the camera's elevation (how far above the object's horizontal
plane) and azimuth (how far round). The photo carries both if you know what to
look at.

## Elevation from a circle

A circle seen obliquely is an ellipse. Under orthographic viewing, with `k` =
minor axis / major axis:

```text
cos γ = k        γ = angle between the circle's axis and the line of sight
```

For a horizontal circle (a wheel lying flat, a cup rim, a round base) seen
from elevation `e` above its plane, `γ = 90° − e`, so `sin e = k`:

| minor/major | elevation above the circle's plane |
|---|---|
| 0.17 | 10° |
| 0.50 | 30° |
| 0.71 | 45° |
| 0.87 | 60° |
| 1.00 | 90° (straight down) |

The major axis stays perpendicular to the line of sight, and the minor axis
lies along the projection of the circle's axis. The sign is ambiguous
(`cos x = cos −x`): the same ellipse is seen from above or below, left or
right, so settle the side from other cues (which face is visible, shading).
The relation assumes orthographic viewing; in a close perspective shot, the
ellipse's centre is not the image of the circle's centre, and ellipses nearer
the horizon line are flatter than those far from it.

## Elevation and tilt from lines

- **The horizon (vanishing line of the ground or table)**: a point imaged on
  it is at camera height ([[single-view-metrology#vanishing-points-and-the-vanishing-line]]).
  An object whose top edge sits on the horizon was shot from its own height;
  if you can see its top face, the camera was above it.
- **Converging verticals**: vertical edges that converge (three-point
  perspective) mean the camera was tilted. Converging downward means it looked
  down. Parallel verticals mean the image plane was vertical (level camera, or
  corrected in software).

## Azimuth from visible faces

For a box of width `W` and depth `D` rotated by azimuth `a` from a front
view, orthographic projected widths are `W·cos a` (front) and `D·sin a`
(side) (derived from the projection). If `W` and `D` are known or their ratio
is, the ratio of the two visible face widths gives `a`; if `a` is known (a
3/4 view is often near 45°), it gives `D/W`. This is the same arithmetic as
the 3/4 width/depth split in [[perspective-and-hidden-views#the-34-widthdepth-split]],
run in the other direction.

## Perspective vs orthographic

The formulas above assume a distant camera. Check first:
[[camera-model-and-focal-length#size-is-inversely-proportional-to-distance]]
gives how much bigger the near face is drawn. If that is more than a few
percent, either take the pose from the telephoto shot, or search the camera in
the likeness gate rather than typing it ([[silhouette-likeness]]).

## Recording the pose

State azimuth and elevation, the cue each came from (ellipse ratio, horizon,
face ratio), and the ambiguity you resolved and how. A pose read from one
ellipse is `[inferred]`, and a pose searched by the likeness gate is
`[measured]`.
