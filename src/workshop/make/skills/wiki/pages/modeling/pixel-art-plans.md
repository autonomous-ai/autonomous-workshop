---
title: Pixel-art plans — building and printing a stepped outline
tags: [pixel-art, raster, grid, cells, stepped-outline, multi-colour, non-manifold, width-check]
aliases: [pixel art, pixel grid, ascii grid, raster plan, voxel plan, stepped plan, pixel key, cell union, corner contact]
sources:
  - "experience: ten pixel-art key covers built from ASCII grids on one shared base, each through the mesh, overhang and thickness gates"
  - "toolchain: shapely unary_union and build123d 0.11 on OCP 7.9"
  - "experience: a pixel brick chimney printed in four colour parts"
  - "experience: a voxel tree and pot on a lamp shade"
  - "experience: pixel-art plates built from cell maps: float-mm unions left slivers, and pockets meeting at a corner failed validate"
related: [perspective-and-hidden-views, sketch-and-extrude-direction, shapely-cutters, fdm-multi-material-design, fdm-minimum-feature-sizes, fillet-chamfer-pitfalls]
updated: 2026-10-10
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
union once (`affine_transform`). A pitch on a binary lattice (k/2^n mm), or
coordinates rounded to about 9 decimals before the union, also avoids it.
Assert that each colour field has as many faces as it has edge-connected
islands in the grid.

**Trace, then extrude once.** Merge each colour's cells into row runs, stack
equal runs into rectangles, union, and extrude the outline once with a stated
direction ([[shapely-cutters#say-which-way-the-prism-runs]]). The result is
all planar faces with no seam faces; `validate` and `interfere` each take
under a second.

Scale the shapely polygon, not the build123d sketch: scaling a sketch by
different amounts in X and Y turns its straight edges into B-splines.

## Corners that only touch

Two cells of one raised field that meet only at a corner extrude into prisms
sharing a single vertical edge: `check_mesh` fails on non-manifold edges and
pinched vertices, and the print has a knife edge there. So does a hole touching
another hole or the outline at one corner, and two flush inlay pockets meeting
only at a corner (a cheek diagonal to an eye). Each is valid to shapely; the
extruded solid fails `validate` with `invalidTopology`/`selfIntersecting`.
Pixel diagonals do this by design. Scan the grid for corner-only contacts
before building (assert there are none left) and fix each one:

- bridge it with one cell, or cut a notch no wider than a nozzle at the
  corner;
- or cut the polygon at every ring-to-ring touch point and extrude the pieces
  as separate solids;
- for two inlay pockets, overlap them by a fraction of a cell (0.15 cell or
  0.4 mm) so they share a face, or inset the smaller inlay by 0.2 mm a side.

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

## Voxel relief that prints upright

Brick or voxel relief on a part printed upright passes the gates when it is
0.8-1.0 mm proud and its top edges are bevelled at about 35 deg from vertical.
Thinner relief fails `check_thickness` where it wraps a corner. Deeper relief
with square tops fails the ledge rule. A bevel at exactly 45 deg tessellates
just past the limit and is flagged. Stepped tiers print the same way: bevel
each step's underside, or print the part upside down so every step becomes an
upward-facing ledge.

A white voxel subject on a white backdrop cannot be masked automatically for
likeness. Trace its outline on the voxel grid of a crop rotated to the
subject's own axes, from a script kept in `measure/`.

A strap that wraps every layer of a voxel box, like a gift ribbon, cannot
come from a filament change. Make it its own drop-in part: the strap region
outside the box core, minus the core, with flat inner leg faces and legs that
only thicken toward the top, so it slides straight down. Cut the box's
channel from the same region grown by the fit clearance. A 3D voxel bow
prints with no overhang as two flat profiles crossing at half-depth notches:
cut one knot column above the lap line and the other below it, and check
each half stays one piece. A one-voxel lid ledge rides on a one-voxel 45 deg
chamfer of the lid's bottom edges, which keeps the body rows crisp.

Build a 3D voxel body as one extruded slab per row: chamfer the slab's
convex edges and cut V-grooves at the cube boundaries. Fusing one chamfered
box per cube leaves tunnels through the solid where interior chamfers meet.
Rows of odd and even width sit half a cube apart, so they must be separate
slabs. Clip the top grooves to the exposed tread. A tread between two equal
rows is empty, and `&` with an empty compound raises `ValueError`, so skip
it. Turning a square voxel footprint 45 deg on a curved host multiplies its
reach by sqrt 2; stepping off the corner cells recovers the clearance and
stays in style.

## Audits on a crisp plan

Read step levels and widths from the outline's own straight edges. An outline
sampled along its wire cuts every square corner, so a width scan sees each
step twice. And compare build123d's `geom_type` with the `GeomType` enum: a
comparison with the string `"LINE"` or `"PLANE"` is always false, and the audit
silently finds nothing.
