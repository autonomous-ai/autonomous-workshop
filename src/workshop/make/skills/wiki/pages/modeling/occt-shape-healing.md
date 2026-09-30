---
title: OpenCASCADE shape healing
tags: [occt, healing, shapefix, shapeanalysis, unify, sewing, repair]
aliases: [ShapeFix_Shape, ShapeFix_Wire, ShapeFix_Face, ShapeFix_Shell, ShapeFix_Solid, ShapeAnalysis_FreeBounds, ShapeUpgrade_UnifySameDomain, BRepBuilderAPI_Sewing, fix shape]
sources:
  - https://occt3d.com/dev/doc/overview/html/occt_user_guides__shape_healing.html
  - https://occt3d.com/dev/doc/refman/html/class_shape_upgrade___unify_same_domain.html
related: [occt-topology-and-tolerance, occt-boolean-options, kernel-validity, mesh-to-step-conversion]
updated: 2026-09-23
---

# OpenCASCADE shape healing

Healing repairs topology an import, a sewing pass or a failed operation left
broken. It belongs on imported references and converted meshes. On shapes
your own generator built, a heal hides a defect whose fix belongs in the
source. Every fixer can grow tolerances, so check the result the same way you
would check a boolean.

## The fixers

| tool | fixes |
|---|---|
| `ShapeFix_Shape` | everything below, recursively. The high-level entry: set precision, max and min tolerance, run, read the status |
| `ShapeFix_Wire` | edge order, small edges, disconnected edges (closes gaps by inserting edges), 3D/2D curve consistency, degenerated edges, self-intersecting wires (cuts edges at the crossing) |
| `ShapeFix_Face` | wire orientation on the face, a missing seam on a closed (periodic) surface whose wires are closed in 3D but not in parameter space |
| `ShapeFix_Shell` | makes face orientations in a shell coherent |
| `ShapeFix_Solid` | builds a valid solid from shells and fixes its orientation |
| `ShapeFix_ShapeTolerance` | sets or limits tolerances on a shape and its sub-shapes (`LimitTolerance(min, max)`) |

Parameters that matter: the **working precision** (what counts as a
problem), the **maximum tolerance** (how far a fix may grow tolerances) and
the **minimum tolerance** (edges shorter than this are removed). Statuses are
`ShapeExtend_OK` (nothing to do), `ShapeExtend_DONE*` (fixed) and
`ShapeExtend_FAIL*` (could not fix), so read them instead of assuming success.

## The analysers: find before you fix

- `ShapeAnalysis_FreeBounds`: free boundaries, meaning wires made of edges
  used by only one face. On a shape meant to be a closed solid, any free bound
  is a hole in the skin.
- `ShapeAnalysis_Wire`: edge order, small edges, disconnected edges,
  self-intersection, closure in parameter space.
- `ShapeAnalysis_CheckSmallFace`: "spot" faces (smaller than precision) and
  "strip" faces (smaller than precision in one direction). These are typical
  leftovers of booleans on near-coincident surfaces.

## Merge same-domain faces: ShapeUpgrade_UnifySameDomain

It merges neighbouring faces or edges lying on the same surface or curve.

```text
ShapeUpgrade_UnifySameDomain(shape, UnifyEdges=true, UnifyFaces=true, ConcatBSplines=false)
  SetLinearTolerance(v)    default Precision::Confusion()
  SetAngularTolerance(v)   default Precision::Angular()
  AllowInternalEdges(bool) default false (non-manifold cases)
  KeepShape(s)             protect a vertex (no edge merge) or edge (no face merge)
  SetSafeInputMode(bool)   default true: the input is not modified
  Build(); Shape(); History()
```

- `ConcatBSplines=true` also joins neighbouring B-spline/Bézier edges that
  meet with C1 continuity.
- It preserves solid, shell and compsolid structure, and will not merge faces
  if that would break sharing between shells.
- Use `History()` to map old faces to merged ones, so a selection made before
  the merge can be carried over.
- Cost: merging a large coplanar region into one face builds very long
  boundary loops, which is the known slow case when unifying converted meshes
  ([[mesh-to-step-conversion#sewing-cost-is-not-linear-in-facet-count]]).

Splitting goes the other way (`ShapeUpgrade_ShapeDivideContinuity`,
`...DivideAngle`, `...DivideArea`, `ShapeUpgrade_ShapeConvertToBezier`). It
is useful when a downstream tool needs faces below some continuity, angle or
area.

## A repair order that works

1. Analyse: free bounds, small faces, self-intersection (the BOP check,
   [[occt-boolean-options#check-the-arguments-first-bopalgo_argumentanalyzer]]).
2. Sew open shells if the faces are coincident but unshared
   ([[occt-topology-and-tolerance#shared-sub-shapes-and-locations]]).
3. `ShapeFix_Shape` with an explicit max tolerance.
4. Make a solid from a closed shell (`ShapeFix_Solid`).
5. Unify same-domain faces.
6. Re-check validity, volume and the maximum tolerance. A healed shape whose
   tolerance grew to fractions of a millimetre will misbehave in the next
   boolean ([[occt-topology-and-tolerance#tolerance]]).
