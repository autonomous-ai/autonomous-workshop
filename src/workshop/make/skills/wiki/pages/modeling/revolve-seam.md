---
title: Seams of revolves, cylinders and spheres
tags: [revolve, seam, cylinder, sphere, ellipsoid, dimple, render, invalid-topology, self-intersecting]
aliases: [seam edge, panel line, revolved seam, sphere seam, cutting tool seam, revolve seam at +X, ellipsoid seam, scaled sphere, sphere pole, fused spheres, seam meridian, cylinder seam placement]
sources:
  - skills/cad/references/build123d-modeling.md ("A revolve puts its seam at +X"; before the move)
  - "toolchain: verified with a marker probe; dimple cuts measured on a 16 mm cube"
  - "experience: scaled-sphere legs and paws fused onto bodies failed BRepAlgoAPI_Check until their seams were turned"
  - "experience: dozens of sphere lumps fused around a ring fell apart or came back invalid with parallel seams"
  - "experience: a plenum tube's end disc tangent to a branch pipe left a face the mesher declined"
related: [operation-families, boolean-pitfalls, kernel-validity, frames-and-rotations, unmeshable-faces]
updated: 2026-10-10
---

# Seams of revolves, cylinders and spheres

Every periodic surface the kernel builds (a revolve, a `Cylinder`, a
`Sphere`, and an ellipsoid scaled from one) has a seam edge, and a sphere also
has two poles. Where they land decides whether a part renders clean, whether a
cut with it is valid, and whether a fuse of several of them checks clean.

## Where the seam lands

A 360° `revolve` leaves a seam edge where its profile started, and sketching
on `Plane.XZ` places that seam at **+X**. If the presentation camera looks
down +X, every revolved casting renders with a thin panel line down its
visible face — on parts whose whole point is a smooth, sealed surface.

This is not limited to `revolve`: a plain `Cylinder` primitive seams at +X
too, verified with a marker probe. Any large smooth camera-facing cylinder is
affected. To put a cylinder's seam where you want it, build it on
`Plane(origin, x_dir=seam, z_dir=axis)`; keep it off the places where branches
and other bodies meet the wall ([[unmeshable-faces#an-end-disc-tangent-to-a-neighbour]]).

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

## A fused ellipsoid's seam can make a sound fuse read as self-intersecting

Ellipsoids made by scaling a sphere (a leg, a paw, toes) and fused across one
another can pass every other check and still fail `BRepAlgoAPI_Check` as
`selfIntersecting` (so `inspect validate` fails the part), for some copies and
not others. What cleared it was turning the sphere's seam meridian about its
pole **before scaling**, so it faces away from where the other pieces cut it,
together with fusing the pieces one at a time rather than as one multi-tool
union. Of four legs, seams at +X or -X left one leg or another failing; at -Y
all four checked clean.

No seam direction is safe in general: a paw fused onto a revolved dome failed
with its seam at +Y and checked clean at +X, -X and 45 deg, and moving the
same paw 0.1 mm in height flipped the result as well. So assert the check in
the builder right after each fuse
(`BRepAlgoAPI_Check(solid.wrapped, True, True).IsValid()`), the same check the
gate runs, before writing the STEP rather than after; on a failure try the
seam's quarter-turns before touching any dimension.

A scaled sphere fails on its own too: a half-ellipsoid (scaled sphere cut by a
box) for an eye dome checked `selfIntersecting` with nothing fused to it. The
round replacements that also survive the STEP the gate meshes:

- **Round-plan dome, height at most its radius:** a spherical cap — a true
  `Sphere` of radius `(r² + c²) / 2c` cut by a box. Analytic, valid, meshes.
- **Taller round boss:** a cylinder with a filleted top edge (plane, cylinder,
  torus), not a dome.
- **Spheroid along one axis:** a half ellipse revolved about its *long* axis
  checked and meshed. A quarter ellipse revolved about a short axis (the pole
  on the axis, as for an oblate dome) validated in memory but its pole face
  did not tessellate once written to STEP and read back, which fails
  `render_views --compare-step` with `comparison mesh omitted N face(s)`.

## Moving the polar axis of an ellipsoid seed

A trimmed ellipsoid relief can remain present in a valid source body but vanish
from its fused STEP export. Rotating a sphere about its polar axis moves only the
longitude seam; it does not move the parameterisation's poles. If turning the
seam does not resolve the trim, reorient the polar axis of the **unit sphere
before nonuniform scaling**. For example:

```python
seed = Rot(90, 0, 0) * Rot(0, 0, 90) * Sphere(1)
ellipsoid = Pos(*center) * scale(seed, by=radii)
```

The seed's spherical envelope is rotationally invariant, so this changes the
surface parameterisation without changing the intended ellipsoid radii or pose.
Rotating the already-scaled ellipsoid does not have that property. This is a
candidate construction repair, not a general export guarantee: test retained
material in the imported physical STEP and inspect the exterior, as described in
[[build123d-operations-and-export#nested-recess-order-can-produce-a-valid-source-that-loses-its-shell-in-step]].

## Many spheres fused into a band: turn each pole along its normal

Dozens of overlapping spheres (fluff lumps around a ring) with their default
seams all parallel fell apart into loose solids when fused one at a time, and
came back as one solid that failed `is_valid` when fused in one call: fuse
grouping alone is not the fix. Rotating each sphere so its pole points along
its own surface normal moved the seams and poles off the neighbours'
intersection curves, and the fuse came back as one valid solid. Lumps sunk
along an inclined normal also stick out sideways past the band they sit on:
measure the built outline, do not compute it from the nominal radius.

## Hiding the seam from the camera

Rotate the finished body about Z so the seam lands away from the camera. Two
cautions:

- A body carrying discrete features (a bolt ring, a stud circle) must be
  rotated by a whole number of feature pitches, or left alone and its
  *prototype* rotated instead — ring helpers that only translate their
  prototype do not move the ring when the prototype is seam-hidden.
- A body offset from the origin is rotated about its own axis
  ([[frames-and-rotations#rotating-a-body-that-sits-off-the-origin]]).

Prove the fix with two renders — the seam absent from the camera face **and**
present on the far side. Without the second render you cannot tell a hidden
seam from one that was never visible at that angle.
