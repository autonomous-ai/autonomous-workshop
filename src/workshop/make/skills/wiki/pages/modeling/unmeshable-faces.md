---
title: Faces the mesher declines
tags: [tessellation, mesh, render, triangulation, occ, face]
aliases: [tessellate, BRepMesh_IncrementalMesh, NbNodes, triangulation None, unmeshable face, render crash]
sources:
  - "toolchain: build123d Shape.tessellate() raises when OCC leaves a face untriangulated (reproducible)"
  - skills/image-to-cad/scripts/render_views.py (_mesh_face_by_face, the reference implementation)
  - "experience: a cone fused 0.01 mm into a loft left a 0.013 mm2 face no gate could mesh"
  - "experience: a window-outline fillet on a revolved spline shell left two planar faces unmeshed in the whole shape; another radius segfaulted"
  - skills/image-to-cad/scripts/render_views.py (tessellate_comparison)
related: [kernel-validity, modeling-failure-modes, revolve-seam, fuse-pitfalls]
updated: 2026-10-10
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

## An opened colour region inside another inlay

Opening a 2D colour region (`offset(offset(face, -w/2), +w/2)`, to drop horns
under a line wide) moves its outline off the arcs it was cut from by a hair.
When that region lies inside another inlay (a moon's grey shadow on its cream
disc), resolving the two leaves the neighbour with near-coincident arcs, and
its flush prism had two planar faces the mesher refused while `validate`
passed. Open only regions that border the body colour; inside another inlay,
cut the shadow without the opening and shape it so its horns meet the rim at a
wide angle (about 50°) rather than a hairline.

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

## A model-unit tolerance needs absolute deflection

build123d's mesh call uses relative deflection, which scales the error by edge
size, so a distance in model units (a quarter pixel, a gate's chord error)
passed through it is not that distance. Mesh with relative deflection off,
clear cached triangulations first (`BRepTools.Clean_s`), and bound the angular
deflection too: chordal error alone leaves the angular subdivision free, and a
STEP round trip that reparameterises an unchanged face then picks different
silhouette triangles. Interior triangle error can reach twice the boundary
deflection setting. `render_views.tessellate_comparison` is the reference
implementation, and it requires every face to mesh.

## An end disc tangent to a neighbour

The slivers that the mesher declines are made by tidy geometry too: a plenum
tube whose flat end sat exactly one pipe radius beyond the axis of a charge pipe
that branches off it, so the end disc was tangent to the branch, left a cylinder
face the mesher would not triangulate; so did the flat end disc of an angled
runner whose edge poked out through the wall of the tube it was meant to end
inside. Run every end of a tube either clearly past the surface it meets (more
than a radius) or entirely inside it (the whole disc, not its centre), and
keep the seam of a cylinder away from the branches
([[revolve-seam#where-the-seam-lands]]). Tessellate each face of each built
part once (`face.tessellate(0.1)` in a try block) before the first render.

## Two solids that share only a circle mesh non-manifold

Two solids that meet only along one shared circle (a lofted cone ending
exactly on the rim of the part below) pass `validate` but tessellate
non-manifold: `check_mesh` reports edges shared by more than two faces and
pinched vertices. End one body 1-1.5 mm inside the other so the surfaces
cross instead of sharing the edge
([[fuse-pitfalls#fusing-pieces-that-share-faces]]).

## A boolean edge's nodes arrive apart from its two faces

Each face of a boolean-made edge meshes that edge from its own pcurve on its
own surface, so the two faces place the shared nodes up to the edge's
tolerance apart, often 1e-6 to 1e-5 mm on a narrow planar ring (a bore's
step). A weld that merges vertices by rounding to a 1e-6 grid splits those
pairs into open edges, and which pairs split depends on where the part sits:
the same valid solid moved by a fraction of a millimetre read 0, 4, 20 or 84
open edges. Weld by distance (a k-d tree, 1e-5), never by grid cell.
