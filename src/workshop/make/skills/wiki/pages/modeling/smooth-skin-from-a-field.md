---
title: Smooth skin from a field
tags: [organic, figurine, smooth, subdivision, bezier, patch, sdf, sewing, step]
aliases: [smooth figure, catmull-clark, acc patches, approximate catmull-clark, bicubic patches, sdf to brep, smooth sculpt, quad net, b-spline skin]
sources:
  - "Loop, C. and Schaefer, S. (2008) Approximating Catmull-Clark subdivision surfaces with bicubic patches, ACM Transactions on Graphics 27(1)"
  - https://vtk.org/doc/nightly/html/classvtkQuadricDecimation.html
  - "toolchain: OCP 7.9 Geom_BezierSurface faces sewn with BRepBuilderAPI_Sewing at 1e-6; OCC booleans against polyhedral tools on a 5500-patch skin"
  - "experience: a seated figure built as a distance field, delivered as a smooth B-rep instead of reduced triangles"
  - "experience: a small figurine skin split into two print halves with colour regions, read by the mesh, wall and overhang gates"
  - "experience: a chibi figure on a perch with exact belt, fins, ears and a carried lantern, and a wind-blown cape printed as its own sheet"
related: [low-poly-sculpt-from-a-field, mesh-to-step-conversion, nurbs-bspline-basics, kernel-validity, organic-likeness]
updated: 2026-10-10
---

# Smooth skin from a field

How to turn a posed distance field (the masses of
[[low-poly-sculpt-from-a-field]]) into a real smooth B-rep: curved faces a
slicer and a viewer tessellate at their own resolution, not triangles. Read it
before delivering an organic field as dense planar triangles, which stay flat
facets in every viewer and cost about 1.1 KB of STEP per triangle.

## Rule or formula

- **Patches from a quad net, one bicubic Bezier per quad.** Contour the field,
  reduce it to a coarse triangle net (`vtkQuadricDecimation`, a few thousand
  triangles for a 250 mm figure), turn it into quads, and build each quad's
  4 x 4 control net by Loop and Schaefer's approximation: interior point at
  corner `v` of valence `n` is `(n v + 2 (e_next + e_prev) + d) / (n + 5)`;
  each edge point is the mean of the two faces' interior points beside it;
  each corner is the mean of the interior points round it (the Catmull-Clark
  limit point). Neighbours then share every boundary curve exactly, so the
  faces sew with no free edge, and the surface is the C2 bicubic B-spline
  wherever the net is regular.
- **One tangent plane at every corner.** Project each vertex's edge points
  into the plane through its corner (normal from the summed cross products of
  the edge points round it). The edge points stay shared, so the skin stays
  watertight, and the patches meet with a common tangent plane at every
  corner; along an edge next to an irregular vertex they are only
  tangent-close.
- **Pair triangles before splitting.** Splitting every triangle into three
  quads gives every patch two irregular corners. Pairing edge-adjacent
  triangles into quads first (squarest pair first; refuse a pair that leaves
  either end of the removed diagonal with fewer than three faces, which has no
  tangent plane), then one Catmull-Clark split of the mixed net, made most
  vertices regular: seam angle p90 fell from 2.45 to 0.72 deg and p99 from 9.7
  to 3.8 deg, with 30 % fewer patches.
- **Fit the net to the field, not the field to the net.** The limit surface of
  a net sitting on the field lies inside it on convex parts. Move every net
  vertex along the field's normal by the field value at its limit point,
  `v -= f(L(v)) * grad f / |grad f|`; twelve rounds put the limit points within
  0.06 mm and the whole patch surface within 0.12 mm at p99.
- **Cut exact planes after, never sample them.** A crease (the flat bottom) in
  the net is rounded by the patches. Push the skin's floor below the desk with
  a rounded maximum, `-smin(-d, z + drop, k)`, and cut the desk plane from the
  sewn solid with an OCC boolean. Keep any exact part's soft copy in the field
  inset (1-2 mm) so the exact part covers the fit's ripple at its edges.
- **Cut features with OCC booleans against polyhedral tools.** The same
  manifold3d tools that cut a triangle twin (hulls, capsules, boxes) become
  OCC solids (sew each component) and cut the sewn skin; a 5500-patch skin
  took about 20 s for a cradle union, eight cavities, a cable channel, posts
  and pilots, and stayed one valid solid.
- **Keep a triangle twin for audits.** Tessellate each patch n x n (4 x 4 is
  within a few hundredths of a millimetre) and weld by distance, not by
  rounding: two patches evaluate a shared boundary from the same poles in
  opposite directions and agree to about 1e-13 mm, and a rounding grid can
  split such a pair. Cut the twin with the same tools in manifold3d and let
  wall, ray and section audits read it.

## Cost

- Net, fit and patches: about 8 s for 2600 triangles (5500 patches); sewing
  1 s; the booleans about 20 s.
- STEP: about 4.5 KB per patch (16 poles, four boundary curves and their
  pcurves), so 5500 patches write about 27 MB per copy, and an assembly that
  places the part again writes it again.

## When it does not hold

- **Laplacian relaxation of the reduced net made it worse.** Moving vertices to
  their neighbours' centroid and projecting back slid vertices across thin gaps
  (between fingers and a plate) and flipped patches: p99 normal error rose from
  10 to 22 deg. Leave the reduction's layout.
- **Creases tighter than a patch.** A concave blend narrower than the net's
  spacing (an armpit, an ankle on the desk) keeps the largest seam angles
  (tens of degrees at the worst point). Raise the blend radius there or the
  triangle count, not the fit rounds.
- **A feature smaller than a patch folds the patches over it.** A sharp edge in
  the field (an exact part's soft copy left as a plain intersection of planes)
  and a carved groove ending in a small pit (a sternum groove stopping between
  two masses) each made patches cross themselves: `BRepCheck_Analyzer` called
  the sewn solid valid, and only the self-interference check
  (`BRepAlgoAPI_Check(shape, True, True)`) found them, as face pairs
  clustered at the feature. Round every edge of a soft copy (a smooth maximum
  of its planes) and end a groove where the surface round it is flat; then run
  the self-interference check on the bare skin before any boolean, where it
  names the feature, rather than on the finished part.
- **A corner tangent projected to nothing meshes with zero-area triangles.**
  Projecting an edge point into its corner's tangent plane shortens it; when
  the edge point lies nearly along the normal it shrinks to almost zero, the
  patch corner degenerates, and its tessellation carries zero-area triangles
  that the mesh gate drops into holes. Rescale the projected vector to the
  edge point's original distance from the corner.
- **A degenerate net makes the same slivers.** Weld the contour before
  decimating it (an unwelded contour decimates into a non-manifold net); after
  decimation collapse edges much shorter than the mean, under the link
  condition and freezing the one-ring of every collapse (two collapses side by
  side in one pass broke manifoldness); flip needle triangles (smallest angle
  under about 15 deg); then relax vertices only within their tangent plane
  and project them back onto the zero set. On a compact figure with no thin
  gaps this cleared every zero-area triangle; mind the gap warning above.
- **Keep the net off a plane an exact cut will follow.** With a grid plane
  on the split plane, net vertices sit on it and the exact split runs through
  patch corners, leaving sliver faces that tessellate with holes. Offset the
  sampling grid by half a cell from every exact cutting plane.
- **Eyes and lines are colour, not bumps.** Small spheres for eyes and a thin
  tube for a mouth line, blended into the field, folded the patches round
  their rims. Leave the skin smooth there, fold in only features several
  patches wide (a nose), and split the colour regions off with exact tools a
  little larger than each feature: the print union stays one watertight skin.
- **The bounding box of a trimmed patch is loose**: see
  [[kernel-validity#bounding-boxes-over-report-on-b-spline-faces]].

## Crisp parts and sheets beside the skin

- **Build thin and crisp features exactly, then fuse them.** A cape, a bag
  handle, gauntlet fins, sharp ear tips or a belt with sub-millimetre steps
  folds the patches or comes out soft when it is put in the field. Leave a
  soft, inset copy in the field only where the exact part sits.
- **No grazing contact at a junction.** A bar leaving a dome tangentially, a
  stem 0.1 mm from a bar, or ball ends resting on a dome each cracks the
  union's tessellation: open edges, or slivers that make the overhang gate
  refuse. Overlap clearly or keep 0.4 mm apart, and run a bar through a
  junction instead of ending it in a ball.
- **Colour regions are exact cuts of the one skin.** Cut the regions one tool
  after another, and drop crumbs under 0.05 mm³. A tool plane that grazes the
  skin leaves unmeshable sliver faces, so keep every plane off tangency. A
  dozen tools on a few thousand patches take minutes, not seconds.
- **Pin small tips before cleaning the net.** Short-edge collapse and
  tangential relaxation after decimation erode a tip under a millimetre: the
  cone that carried a fist disappeared. Freeze the vertices near such tips
  through both steps, and make support cones fat primitives.
- **Thicken a sheet on its control net.** Offset a B-spline sheet's net by
  plus and minus half the thickness along the net normals, build both faces
  from the offset nets, close the border with ruled faces and sew. `thicken`
  and `BRepOffset` give offset surfaces that took the self-interference check
  from seconds to minutes, and slowed every later boolean. Every fold's radius
  must exceed half the thickness, or the offset crosses itself.
- **Lay a sheet a clearance off a body along its normal.** A sheet stored as
  depth over a frontal plane, offset along the depth axis, gets too little
  clearance where the body slopes. Half a thickness along the normal is that
  half times `sqrt(1 + |grad x|^2)` along the depth axis. Cap the factor near
  silhouettes, where the slope runs away. Then sample the body's field at the
  inner face and push the sheet back by any shortfall.
- **Cut openings in a leaning or folded sheet along its normal.** A
  fixed-direction prism leaves knife wedges, which the thickness gate reads as
  walls. Ease the folds out near the cut.

### A cape in the wind

A cape whose hem comes back to the base reads as a cape hanging behind the
figure, however much it billows. For wind to read at a glance, the cape has to
leave the body and stream out sideways past the base, with its trailing edge
in the air. That shape cannot print attached to an upright figure, so print
it as its own sheet, standing on its trailing edge with its folds running
along the wind. It prints without support while its depth slope along the
print's vertical stays under tan 45 deg. Enforce that with a one-sided limiter,
`x[i] = min(x[i], x[i-1] + m * step)`, run forwards and backwards along each
vertical column of the depth grid. It only moves the sheet away from the
body, so it cannot create a clash. Join the cape to the figure with level
pins ([[fdm-joining-split-prints]]), and give the figure's back under it a
finished surface.

## Checks

- Sewing reports no free and no multiple edges, one shell; the solid is valid
  and passes the self-interference check (about 50 s on 5500 patches).
- Field value at a dense sample of every patch (p99 within the budget) and the
  angle between patch normals at shared boundary samples (p90, p99).
- Review shading with normals from the patch derivatives. A flat-shaded review
  render of long thin patches shows streaks that are its own triangles, not
  ripple in the surface.
