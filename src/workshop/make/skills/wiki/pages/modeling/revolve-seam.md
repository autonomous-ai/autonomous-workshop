---
title: The revolve seam at +X
tags: [revolve, seam, cylinder, sphere, dimple, render, invalid-topology]
aliases: [seam edge, panel line, revolved seam, sphere seam, cutting tool seam]
sources:
  - skills/cad/references/build123d-modeling.md ("A revolve puts its seam at +X"; before the move)
  - "toolchain: verified with a marker probe; dimple cuts measured on a 16 mm cube"
related: [operation-families, boolean-pitfalls, kernel-validity, frames-and-rotations]
updated: 2026-09-23
---

# The revolve seam at +X

## Where the seam lands

A 360° `revolve` leaves a seam edge where its profile started, and sketching
on `Plane.XZ` places that seam at **+X**. If the presentation camera looks
down +X, every revolved casting renders with a thin panel line down its
visible face — on parts whose whole point is a smooth, sealed surface.

This is not limited to `revolve`: a plain `Cylinder` primitive seams at +X
too, verified with a marker probe. Any large smooth camera-facing cylinder is
affected.

## As a cutting tool the seam makes an invalid solid

**As a cutting tool the same seam produces an INVALID SOLID, not a cosmetic
line.** A `Sphere` subtracted to make a dimple carries its seam at local +X;
if that seam ends up inside the remaining material the result fails
`BRepCheck_Analyzer`, `BRepAlgoAPI_Check` and `inspect validate`
(`invalidTopology`, `openShell`, `selfIntersecting`) while still reporting a
plausible volume and a single solid. Measured on a 16 mm cube with 1.6 mm
dimples: identical cuts passed on `+Z`, `+Y` and `-Y` and failed on `-X`. It
is per-face, so cutting one pip at a time and checking after each is what
localises it — the whole-die cut just fails.

Turn the tool's seam OUT of the part before subtracting:

```python
_SEAM_OUT = {(0, 0, 1): (0, -90, 0), (0, 0, -1): (0, 90, 0),
             (1, 0, 0): (0, 0, 0),   (-1, 0, 0): (0, 0, 180),
             (0, 1, 0): (0, 0, 90),  (0, -1, 0): (0, 0, -90)}

def dimple(radius, normal):          # normal = the face's outward direction
    return Rot(*_SEAM_OUT[normal]) * Sphere(radius)
```

## Hiding the seam from the camera

Rotate the finished body about Z so the seam lands away from the camera. Two
cautions:

- A body carrying discrete features (a bolt ring, a stud circle) must be
  rotated by a whole number of feature pitches, or left alone and its
  *prototype* rotated instead — ring helpers that only translate their
  prototype do not move the ring when the prototype is seam-hidden.
- A body offset from the origin must be rotated about **its own** axis: build
  it at the origin, rotate, then translate. Rotating in place about global Z
  flies it across the model.

Prove the fix with two renders — the seam absent from the camera face **and**
present on the far side. Without the second render you cannot tell a hidden
seam from one that was never visible at that angle.
