---
title: Pixel-art plans — building and printing a stepped outline
tags: [pixel-art, raster, grid, cells, stepped-outline, multi-colour, non-manifold, width-check]
aliases: [pixel art, pixel grid, ascii grid, raster plan, voxel plan, stepped plan, pixel key, cell union, corner contact]
sources:
  - "experience: ten pixel-art key covers built from ASCII grids on one shared base, each through the mesh, overhang and thickness gates"
  - "toolchain: shapely unary_union and build123d 0.11 on OCP 7.9"
related: [perspective-and-hidden-views, sketch-and-extrude-direction, fdm-multi-material-design, fdm-minimum-feature-sizes, fillet-chamfer-pitfalls]
updated: 2026-10-08
---

# Pixel-art plans — building and printing a stepped outline

A pixel-art object is a plan whose every edge sits on a grid, filled in
colour by cell. Transcribe it as a character grid (one character per colour
field, `.` for empty) and build the plan and every field from that one grid,
so outline and colours cannot drift apart. Reading the grid off an image:
[[perspective-and-hidden-views#a-rectilinear-plan-is-read-on-a-grid-not-traced]].

## Build cells in grid units, then scale

Placing each cell in millimetres (`x0 = x_left + c * pitch`, far edge
`x0 + pitch`) makes the shared edge of two neighbours two different floats
whenever the pitch is not a binary fraction. `unary_union` then keeps one
polygon per cell: a door frame came back as 23 faces and a whole bow as 118,
and nothing failed until a width check measured the slivers between them.
Build the cells on integer coordinates, union them, and scale and place the
union once (`affine_transform`). A pitch on a binary lattice (k/2^n mm) also
avoids it. Assert that each colour field has as many faces as it has
edge-connected islands in the grid.

Scale the shapely polygon, not the build123d sketch: scaling a sketch by
different amounts in X and Y turns its straight edges into B-splines.

## Corners that only touch

Two cells of one raised field that meet only at a corner extrude into prisms
sharing a single vertical edge: `check_mesh` fails on non-manifold edges and
pinched vertices, and the print has a knife edge there. Pixel diagonals do this
by design. Scan the grid for corner-only contacts before building and either
bridge them with one cell or cut a notch no wider than a nozzle at the corner.
Two fields may share an edge or stand at least one cell apart, never touch at a
point.

## Width checks punish small squares

A two-line width check by morphological opening (erode then dilate by the half
width, compare areas) takes `r²(1 − π/4)` from every convex right-angle corner.
With `r = 0.4` a square loses 0.137 mm², so it passes a 3 % area tolerance only
from 2.14 mm a side, and a strip drawn at exactly the limit width vanishes.
Grow small squares a few hundredths, or keep detail pitches above the limit.

## Placing features on a stepped plan

- **Odd grids for axis features.** A hole, a knot or a clapper an odd number
  of cells wide lands on whole cells only when the axis runs through a cell
  centre: use an odd column count.
- **Raised cells keep off the steps.** A raised pixel diagonal to a step's
  inside corner sits 0 mm from the outline; every raised cell needs all eight
  neighbours inside the plan plus the edge round's keep-out.
- **A ring hole's wall is a rounded buffer.** A row `d` below a square hole
  needs its edge at least `√(w² − d²)` beyond the hole's corner for a wall `w`,
  and the keep-out round a hole at an apex erases any raised detail there; the
  hollow under a raised chevron is the better place for it.
- **A round or rectangular tag in a stepped body** is bounded by the narrowest
  rows above and below it: work out the depth window first and centre the
  pocket in it.
- **A colour boundary that ends at an inside corner** lies on a face tangent
  to the front-edge round there. Give that corner a small plan round (about
  0.5 mm) and run the boundary across the arc, and run the field's other sides
  out into the air.

## Audits on a crisp plan

Read step levels and widths from the outline's own straight edges. An outline
sampled along its wire cuts every square corner, so a width scan sees each
step twice. And compare build123d's `geom_type` with the `GeomType` enum: a
comparison with the string `"LINE"` or `"PLANE"` is always false, and the audit
silently finds nothing.
