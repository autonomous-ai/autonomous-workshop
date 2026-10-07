---
title: B-spline surfaces from height grids
tags: [bspline, surface, height-field, grid, crown, control-net, occ, ringing]
aliases: [GeomAPI_PointsToBSplineSurface, Geom_BSplineSurface, 2.5D surface, relief surface, surface fitting, control points]
sources:
  - "toolchain: GeomAPI_PointsToBSplineSurface least-squares fit rings on a steep-in-flat height grid (reproducible)"
  - The NURBS Book (Piegl and Tiller), convex hull property of B-spline surfaces
  - "experience: 12 constant-depth groove booleans on a 89 x 113-pole dune surface ran over 7 minutes unfinished; the same ripples in the pole heights built the whole body in 26 s"
related: [kernel-validity, boolean-pitfalls, loft-pitfalls]
updated: 2026-10-04
---

# B-spline surfaces from height grids

A 2.5D relief — a crown, a dome, an embossed card — is often rebuilt from a
regular grid of measured heights. Fitting a surface *through* that grid is the
wrong construction; using the grid *as the control net* is the right one.

## Fitting through the grid rings

`GeomAPI_PointsToBSplineSurface(arr, DegMin, DegMax, Continuity, Tol3D)`
solves a global least-squares system, and it rings badly when a height grid
has a steep region inside a large flat surround — which is what a measured
crown grid always looks like once the field is padded past the footprint with
edge values.

Measured on an 81×110 grid at 1.5 mm pitch, heights **0.01 .. 13.85 mm**:

| settings | resulting surface Z |
|---|---|
| deg(3,8) C2 tol 0.1 | **-278 .. +295** |
| deg(3,3) C2 tol 0.1 | **-4052 .. +4172** |
| deg(3,3) C1 tol 0.1 | **-2.2e6 .. +3.7e6** |
| deg(3,8) C1 tol 0.1 | -1.6 .. 16.4 (bounded, still wrong) |

The failure is silent and downstream-consistent: a `prism - extrude(crown)`
cut then removes almost nothing, so plates came back up to +77 % heavy in 6
solids, and one with **negative volume in 10 solids** — and `validate`,
`interfere` and `check_fit` all passed that wreckage.

## Use the grid as the control net

**The fix is not a better tolerance.** Build a `Geom_BSplineSurface` whose
**poles are the grid** (uniform clamped knots, degree 3 both ways, X/Y poles
evenly spaced). A B-spline lies inside the convex hull of its control net, so
the crown cannot leave the measured height range — by construction, not by
luck. Rebuilt this way, the same plates landed within **4.0 %** of their
meshes, each one solid, and the slowest dropped from 26.5 s to 2.9 s.

The cost is that the surface smooths the net rather than interpolating it,
which is the approximation a gridded measurement already declares.

## Assert the height range

Assert the face's Z bounding box lies inside the grid's own range. That assert
is what turns this from a silent 77 % error into a build failure. Measure the
bounding box with `BRepBndLib.AddOptimal_s`, not the control-hull `Add`
([[kernel-validity#bounding-boxes-over-report-on-b-spline-faces]]).

## Flat where the net is flat

A cubic patch depends on the poles within two spans of it. Where all of those
poles lie on one plane, the surface lies **exactly** in that plane (the convex
hull again). An organic surface can therefore carry a truly flat face for a
flush part, a display lens or a label, inside its freeform: make the height
function planar there, and keep the flush feature at least two pole spacings
from any kink (a ridge, a toe), because the net rounds every kink over about
two spacings each side.

## Texture belongs in the net

Ripples, flutes and grooves on a height field cost nothing when they are added
to the pole heights, and a great deal as booleans: twelve groove cuts against
a 9 800-pole surface ran over seven minutes without finishing, while the same
ripples in the net built the whole body in 26 s. The net smooths what it
carries, by a gain at the poles of

```text
g(n) = (4 + 2 cos(2 pi / n)) / 6      n = poles per wavelength
       n = 4: 0.67   n = 5: 0.77   n = 8: 0.90
```

so scale the pole amplitude by `1 / g`, and keep `n >= 4`: below that the
texture aliases or vanishes. Through-slots (a grille) are still booleans; cut
them as a few straight prisms, not as surface-following grooves.

## A solid from the face

`split(box, face, keep=Keep.BOTTOM)` turns the face into a solid when the face
overruns the box on every side; make the pole domain a few millimetres larger
than the box. A constant-depth skin made as `outer - Pos(0, 0, -d) * outer`
fails when the two solids share their side walls; build the subtracted copy
with a wider footprint so only the top surfaces nearly agree
([[boolean-pitfalls]]).

Degree, knots and continuity in general: [[nurbs-bspline-basics]].
