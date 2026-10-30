---
title: Porting an OpenSCAD model to build123d
tags: [openscad, build123d, port, scad, transform, verification, remix]
aliases: [scad to step, port openscad, openscad remix, rotate order openscad, fn polygons, compare to stl, scad port]
sources:
  - https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Transformations (rotate([x,y,z]) applies X, then Y, then Z)
  - https://en.wikibooks.org/wiki/OpenSCAD_User_Manual/Other_Language_Features ($fn sets the segment count of every circle)
  - "experience: a print-in-place infinity cube ported line by line and checked against its author's own STL"
related: [cadquery-to-build123d, build123d-builder-and-algebra, boolean-pitfalls, brep-vs-source, print-in-place-mechanisms]
updated: 2026-10-27
---

# Porting an OpenSCAD model to build123d

An MIT or CC-licensed `.scad` is often the cleanest base to remix. It is a
program, not a mesh, so it ports dimension for dimension. That beats recovering
source from an STL, which keeps no radius and no intent.

## Transforms

- `translate(t) rotate([a, b, c]) X` is `T · Rz(c) · Ry(b) · Rx(a) · X`. Write
  it as `Pos(*t) * Rot(0, 0, c) * Rot(0, b, 0) * Rot(a, 0, 0) * shape`, one axis
  per `Rot`, and never pass all three angles to one `Rot` and hope its Euler
  order matches.
- `cylinder(h, r1, r2)` and `cube(size)` start at the origin on +Z (and at the
  min corner). Reproduce that with `align=Align.MIN` in Z (and all axes for the
  box), not the build123d centre default.
- `rotate([-90, 0, 0])` turns +Z into +Y, and `rotate([90, 0, 0])` turns it
  into −Y.
- Read every placement into a 4 x 4 matrix (`loc.wrapped.Transformation()`)
  when you need a point or axis from it; `Location * Vector` is not defined.

## What legitimately changes

- **Circles.** `$fn = 100` makes every cylinder a 100-gon inscribed in its
  circle. A true circle differs radially by at most r·(1 − cos(π/n)), which is
  0.002 mm on r = 4.4. Volume differs by about 0.07 % of each cylinder.
- **Coincident unions.** A `union()` of solids that only touch on a face (a
  pin standing on a pocket wall) fuses in CGAL. In OCC, sink the touching part
  a little into solid material so the fuse is robust; the printed volume is
  unchanged.
- **Sacrificial features.** Breakaway ties or support threads that the `.scad`
  unions into the part can be kept as their own labelled solids, trimmed to the
  air they bridge. The print entry's fused union then restores the original
  body count.

## Verify against the author's own export

Most `.scad` repositories ship the STLs their author rendered. That STL is the
reference, and you need no OpenSCAD install to use it: read it as data.

1. Compare the bounding box, the total volume, and the connected bodies one by
   one (volume and box each). A print-in-place model has one body per free
   group, so a missing tie or a fused hinge shows up as a body-count difference.
2. Measure the two-way surface distance on dense samples (about 0.08 mm apart,
   KD-tree), then re-measure every sample over the sampling floor exactly,
   point to triangle, against the triangles that own its nearest samples. Raw
   nearest-sample distances overstate the deviation by up to the sample
   spacing. Re-measuring each one in a Python loop costs millions of
   iterations; vectorise it over the k nearest candidates.
3. Write the deviations down: circles, any sunk roots, any re-labelled
   solids. Nothing else should differ.
