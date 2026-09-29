---
title: Faces the mesher declines
tags: [tessellation, mesh, render, triangulation, occ, face]
aliases: [tessellate, BRepMesh_IncrementalMesh, NbNodes, triangulation None, unmeshable face, render crash]
sources:
  - "toolchain: build123d Shape.tessellate() raises when OCC leaves a face untriangulated (reproducible)"
  - skills/image-to-cad/scripts/render_views.py (_mesh_face_by_face, the reference implementation)
  - "experience: a cone fused 0.01 mm into a loft left a 0.013 mm2 face no gate could mesh"
related: [kernel-validity, modeling-failure-modes]
updated: 2026-09-28
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

## Mesh face by face and count the skips

Run `BRepMesh_IncrementalMesh` on the occurrence, then walk its faces with
`TopExp_Explorer`, skip each face where `BRep_Tool.Triangulation_s` returns
`None`, and print how many were skipped. The picture keeps everything else,
and the count says how much is missing.
`skills/image-to-cad/scripts/render_views.py` (`_mesh_face_by_face`) is the
reference implementation.
