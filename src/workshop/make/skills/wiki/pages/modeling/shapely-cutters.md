---
title: Cutters built from shapely polygons
tags: [shapely, cutter, prism, boolean, performance, polygon, buffer, extrude]
aliases: [shapely prism cutter, polygon cutter slow, buffer cutter, shapely to build123d, cutter from a 2d polygon, sliver shards]
sources:
  - "experience: eight lofted segments trimmed by 64-sided arc prisms ran past two minutes; true circles took two seconds"
  - "experience: a sliver cleanup returned 1349 pieces, two of them real; filtering by area took the tray from over ten minutes to 0.4 s"
  - "experience: a ring clipped by a polygon extruded downward into the part and left a closed void"
related: [boolean-pitfalls, sketch-and-extrude-direction, kernel-validity, construction-strategy]
updated: 2026-10-05
---

# Cutters built from shapely polygons

`shapely` is the quick way to compute a 2D region (an offset, a clipped ring,
the sliver left between two outlines); turning it into a prism cutter has
three traps.

## Arcs drawn as polygons make cutters slow

A cutter extruded from a polygon that approximates arcs (a `shapely` buffer,
a circle as 64 segments) cuts a B-spline body in minutes where the same cut
with true circles takes seconds: every facet is a planar face the kernel
intersects with the spline. Eight lofted segments trimmed by 64-sided arc
prisms had not finished after two minutes; with `Cylinder` arcs and
straight-sided wedges the same eight took two seconds. Build every arc as a
circle, and keep polygons for straight-sided regions; when one must be grown,
mitre it (`buffer(d, join_style=2)`) so it keeps its vertex count instead of
gaining an arc at each corner.

`shapely` set operations between two polygonisations of the same arc (an
outline minus its own opening, `a - a.buffer(-d).buffer(d)`) return the real
pieces plus about a thousand zero-area shards along the shared boundary. Made
into prisms, each shard is one more cutter: a tray that builds in 0.4 s ran
past ten minutes. Keep only pieces above an area floor (`g.area > 0.01`)
before building cutters.

## Say which way the prism runs

A `Face` made from a polygon takes its normal from the polygon's winding, and a
clipped or differenced polygon can come back wound either way: `extrude(face,
h)` then runs down into the part instead of up out of it, and a groove becomes
a closed void under the surface that only the shell count shows, and an
`intersect` with it comes back `None` (empty), not an error. Pass
`dir=(0, 0, 1)` in the one helper every cutter goes through
([[sketch-and-extrude-direction#state-the-extrude-direction]]).
