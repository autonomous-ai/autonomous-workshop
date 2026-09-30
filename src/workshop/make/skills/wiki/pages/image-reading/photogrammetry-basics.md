---
title: Photogrammetry basics
tags: [photogrammetry, structure-from-motion, scan, mesh, point-cloud, capture]
aliases: [sfm, photo scan, 3d scanning from photos, meshroom, colmap, realitycapture, metashape]
sources:
  - https://en.wikipedia.org/wiki/Photogrammetry
  - https://www.formlabs.com/blog/photogrammetry-guide-and-software-comparison/
related: [mesh-to-step-conversion, mesh-measurement, image-types-and-views, silhouettes-and-visual-hull]
updated: 2026-09-23
---

# Photogrammetry basics

When the user can photograph the real object many times, photogrammetry
turns the photos into a mesh. That mesh is a measured reference, far better
than any single view, but it is still a mesh, so the rebuild route is the
mesh route ([[mesh-to-step-conversion]], [[mesh-measurement]]).

## How it works

Structure from motion finds the same surface points in overlapping photos
taken from different positions and triangulates them. The result is a sparse
then dense point cloud, which is meshed. Absolute scale comes only from a
known distance in the scene (a scale bar or a reference object); without one
the model is correct in shape and arbitrary in size.

## Capture rules

- **Overlap**: at least 50 % between consecutive photos, 60–80 % ideal.
- **Count and coverage**: 40–50 photos are typically enough for one object,
  shot in two elevation bands (about 10° and 45°) plus close-ups of detailed
  areas.
- **Never move the object during the shoot.**
- **Light**: diffuse and constant (an overcast day is the model), with no
  hard directional shadows.
- **Background**: contrasting colour. A feature-rich backdrop such as
  newspaper helps alignment.
- **Camera**: an 8 MP phone is the minimum, 18 MP+ is better; a sharp, deep
  depth of field; a tripod in low light; avoid fisheye unless the software
  models it ([[lens-distortion]]).
- **Scale**: include a ruler or an object of known size, flat on the same
  support.

## Surfaces that fail

Dark, shiny, transparent, textureless, very thin or completely flat
surfaces give the solver nothing to match, and leave holes or noise. The
fix is to dull the surface temporarily (3D-scanning spray, dry shampoo,
chalk, matte spray paint or tape), avoid transparent objects, or use a laser
scanner instead.

## Software

| tool | licence | notes |
|---|---|---|
| Meshroom (AliceVision) | free, open source | many parameters; slow |
| COLMAP | free, open source | research standard; fast |
| RealityCapture / RealityScan | commercial | best detail in comparative tests |
| Agisoft Metashape | commercial | reliable on mechanical objects |
| 3DF Zephyr | commercial | guided workflow |

## What to expect

After cleanup, deviations of about 0.1–0.5 mm are achievable on objects of
low to medium geometric complexity; laser scanning remains better for higher
precision. No tool delivers a watertight, print-ready mesh directly: expect
cleanup in MeshLab or Meshmixer before converting.
