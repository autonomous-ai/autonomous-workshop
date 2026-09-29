---
title: B-spline surfaces from height grids
tags: [bspline, surface, height-field, grid, crown, control-net, occ, ringing]
aliases: [GeomAPI_PointsToBSplineSurface, Geom_BSplineSurface, 2.5D surface, relief surface, surface fitting, control points]
sources:
  - "toolchain: GeomAPI_PointsToBSplineSurface least-squares fit rings on a steep-in-flat height grid (reproducible)"
  - The NURBS Book (Piegl and Tiller), convex hull property of B-spline surfaces
related: [kernel-validity, boolean-pitfalls, loft-pitfalls]
updated: 2026-09-23
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

Degree, knots and continuity in general: [[nurbs-bspline-basics]].
