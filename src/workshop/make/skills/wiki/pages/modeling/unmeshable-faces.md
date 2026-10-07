---
title: Faces the mesher declines
tags: [tessellation, mesh, render, triangulation, occ, face]
aliases: [tessellate, BRepMesh_IncrementalMesh, NbNodes, triangulation None, unmeshable face, render crash]
sources:
  - "toolchain: build123d Shape.tessellate() raises when OCC leaves a face untriangulated (reproducible)"
  - skills/image-to-cad/scripts/render_views.py (_mesh_face_by_face, the reference implementation)
  - "experience: a cone fused 0.01 mm into a loft left a 0.013 mm2 face no gate could mesh"
  - "experience: a window-outline fillet on a revolved spline shell left two planar faces unmeshed in the whole shape; another radius segfaulted"
related: [kernel-validity, modeling-failure-modes]
updated: 2026-10-04
---

# Faces the mesher declines

## One face kills a whole-shape tessellation

`Shape.tessellate()` raises
`AttributeError: 'NoneType' object has no attribute 'NbNodes'` when OCC
declined to triangulate a face. A renderer that tessellates per occurrence
therefore dies on the first such face anywhere in an assembly — no partial
image, no count, just the traceback.

It is not rare, and it is not a validity failure: recovered plates have shown
16 such faces across one assembly whose solids were all valid, with
`inspect validate` passing every occurrence. Only the mesher objects.

It matters because an appearance review is what catches a model that is
geometrically sound and visually wrong; losing it to one face means shipping
on silhouettes. A STEP round-trip fallback does not help: it only recovers a
stale face *representation*, not a face the mesher refuses.

## A hair's overlap makes the face

The face the mesher declines is often a sliver the model made. A cone fused to
a loft's flat end, carried 0.01 mm past it so the two would overlap, left a
0.013 mm² planar face at their meeting ring, and every print gate on the part
died on it. Meet a flat end exactly (same radius, same plane), or stop short
and leave a ledge the print can carry; do not overlap by a hair. After any
change, tessellate each built solid once at the gate's tolerance and find the
face that raises before the gate does.

## A fillet along a cut's outline on a revolved surface

Filleting the outer edges of a window cut through a revolved spline shell (the
cut's flat sides meeting the shell's surface) returned a valid solid whose two
flat side faces the whole-shape mesher (relative deflection, as
`Shape.tessellate` calls it) left untriangulated, while meshing each face on
its own succeeded; at other radii the same fillet crashed the process outright.
Give such an edge its thickness by construction instead: splay the cut's sides
(a ruled loft between a narrower inner outline and a wider outer one) so they
meet the surface at a larger angle.

## Mesh face by face and count the skips

Run `BRepMesh_IncrementalMesh` on the occurrence, then walk its faces with
`TopExp_Explorer`, skip each face where `BRep_Tool.Triangulation_s` returns
`None`, and print how many were skipped. The picture keeps everything else,
and the count says how much is missing.
`skills/image-to-cad/scripts/render_views.py` (`_mesh_face_by_face`) is the
reference implementation.

## Absolute deflection for source-to-export comparisons

A tessellation tolerance derived from pixel size is a distance in model units.
It must be passed to OCCT with relative deflection disabled. build123d's normal
mesh call uses relative deflection, which scales the error by edge size; a
quarter-pixel distance passed through that API can produce visibly different
outlines for identical source and STEP B-reps.

Clear cached triangulations before an absolute comparison mesh. Require every
face to mesh, since a partial silhouette cannot prove an export unchanged.
Keep the existing numeric comparison floor and fix the meshing units instead
of accepting numerical drift. A curved-shape regression should premesh with
relative deflection and confirm that the comparison replaces it with a mesh
whose measured triangle error meets the stated model-unit bound. OCCT's
interior triangulation may deviate by twice its boundary deflection setting;
do not equate the API argument with an exact interior error limit. Export
comparison fixtures must have closed sections and valid geometry, so a missing
face does not make a round-trip test pass on two equally incomplete meshes.

## An end disc tangent to a neighbour

The slivers that the mesher declines are made by tidy geometry too: a plenum
tube whose flat end sat exactly one pipe radius beyond the axis of a charge pipe
that branches off it, so the end disc was tangent to the branch, left a cylinder
face the mesher would not triangulate; so did the flat end disc of an angled
runner whose edge poked out through the wall of the tube it was meant to end
inside. Run every end of a tube either clearly past the surface it meets (more
than a radius) or entirely inside it (the whole disc, not its centre), and
keep the seam of a cylinder away from the branches (`Plane(origin, x_dir=seam,
z_dir=axis)` puts it where you say). Tessellate each face of each built part
once (`face.tessellate(0.1)` in a try block) before the first render.
