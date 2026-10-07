---
title: Low-poly sculpt from a field
tags: [organic, figurine, low-poly, faceted, decimation, sdf, mesh, sewing, step]
aliases: [lowpoly figure, faceted sculpture, polygonal statue, low poly, signed distance field, skeleton field, marching cubes, quadric decimation figure]
sources:
  - https://vtk.org/doc/nightly/html/classvtkFlyingEdges3D.html
  - https://vtk.org/doc/nightly/html/classvtkQuadricDecimation.html
  - https://iquilezles.org/articles/distfunctions/
  - "experience: a seated low-poly figure (crossed legs, arms across the lap, a screen in the hands) built from a posed skeleton field, decimated, cut with exact booleans and sewn into one solid"
related: [mesh-to-step-conversion, thinning-a-carried-mesh, organic-likeness, loft-organic-bodies, silhouette-likeness, smooth-skin-from-a-field]
updated: 2026-10-05
---

# Low-poly sculpt from a field

How to make a figure whose look is real planar facets (a "low-poly" statue)
when the pose defeats lofts: limbs crossing a body, crossed legs, hands
reaching across a lap. Read it before choosing lofted segments or convex hulls
for a faceted figurine.

## Rule or formula

- **Model the pose as a field, facet it by reduction.** Each mass is a
  primitive with an exact or bound-correct distance (ellipsoid, round cone,
  rounded slab); masses blend with a polynomial smooth minimum; the field is
  cut flat at the desk with `max(d, -z)`. Sample it on a grid
  (1.5 mm for a 250 mm figure), contour it with `vtkFlyingEdges3D`, and reduce
  with `vtkQuadricDecimation` (volume preserving) to the facet count the
  reference shows. The facets are the reduction's triangles: large where the
  surface is flat (thighs, back), small where it bends (wrists, fingers),
  which is the layout low-poly artists aim for. Lofts self-intersect where a
  limb crosses the body; convex hull segments leave a seam at every joint.
- **The facet count is a look parameter, not a likeness one.** Silhouette IoU
  moved by under 0.002 between 900 and 2400 triangles on a whole figure;
  choose the count by comparing shaded renders with the reference's facet
  size (about 1300 triangles read like a printed low-poly statue at 250 mm).
- **Flip the winding.** For a field that is positive outside, flying edges
  emits inward-facing triangles: manifold3d reports a negative volume.
  Reverse each triangle's vertex order.
- **Re-cut the base after reducing.** Quadric reduction leaves the flat
  bottom's vertices within a few hundredths of a millimetre of the plane, so
  the contact face is no longer one plane and `min(Z)` is not 0. Trim a 0.3 mm
  slice (`trim_by_plane`) and translate it back down; the face is then exact.
- **Build exact features on the triangles, then sew once.** Union the exact
  parts (a screen cradle wedge as a convex hull trimmed by planes) and cut
  every pocket and channel with manifold3d booleans on the reduced mesh, then
  sew the finished mesh into one solid
  ([[mesh-to-step-conversion#carrying-a-mesh-as-the-deliverable]]). A soft
  copy of an exact part inside the field gives the blends (palms into a
  cradle) and is covered by the exact part.
- **Wall checks read the field.** Sample the field along a buried feature's
  axis (a cable channel, a plug pocket's corners): the wall is `-field - r`.
  It is milliseconds and names the shallow station, where a section of the
  sewn solid costs seconds and only says "thin somewhere".

The same field delivered smooth instead of faceted (real curved faces, not
denser triangles) is [[smooth-skin-from-a-field]].

## When it does not hold

- A smooth union bulges where masses meet at a narrow angle; a large blend
  radius at a junction fattens the silhouette there (a jaw blended into a
  cranium with a 16 mm radius cost 0.003 IoU). Shape a head as one tapered
  ellipsoid (an egg) rather than two blended ones.
- The field is not a distance after anisotropic scaling (flattened legs);
  multiply by the smallest scale so it stays a lower bound, and keep the blend
  radii modest.

## Checks

- Every edge used by exactly two triangles before sewing; one shell after.
- `min(Z) == 0` and the contact face's area, read off the triangles at Z = 0.
- A shaded render at the reference's camera beside the reference, for facet size.
