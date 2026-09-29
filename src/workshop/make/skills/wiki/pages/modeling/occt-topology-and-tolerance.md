---
title: OpenCASCADE topology and tolerance
tags: [occt, opencascade, topology, tolerance, orientation, brep, shape-type]
aliases: [TopAbs_ShapeEnum, TopoDS, TShape, TopLoc_Location, shape orientation, FORWARD REVERSED, compsolid, shape tolerance]
sources:
  - https://occt3d.com/dev/doc/overview/html/occt_user_guides__modeling_data.html
  - https://occt3d.com/dev/doc/overview/html/specification__boolean_operations.html
  - https://occt3d.com/dev/doc/overview/html/occt_user_guides__shape_healing.html
related: [occt-boolean-options, occt-shape-healing, kernel-validity, build123d-builder-and-algebra]
updated: 2026-09-23
---

# OpenCASCADE topology and tolerance

build123d and CadQuery are thin layers over OCCT. When a kernel error surfaces,
it is phrased in OCCT's terms: shape types, orientation, shared sub-shapes and
tolerances. This page is the vocabulary.

## Shape types

`TopAbs_ShapeEnum`, from most complex to simplest:

| type | is |
|---|---|
| `COMPOUND` | a group of any topological objects |
| `COMPSOLID` | solids connected by their faces |
| `SOLID` | a part of space bounded by shells |
| `SHELL` | faces connected by their edges, open or closed |
| `FACE` | a bounded part of a surface |
| `WIRE` | edges connected by their vertices |
| `EDGE` | a bounded curve |
| `VERTEX` | a point |
| `SHAPE` | the generic term for any of these |

Practical consequences:

- A boolean result is often a `COMPOUND` even when it holds one solid. Assert
  `len(shape.solids()) == 1` instead of checking the type.
- A closed `SHELL` is not a `SOLID`: it has no inside until it is made one
  ([[occt-shape-healing]]).

## Orientation decides which side is material

`TopAbs_Orientation`:

- `FORWARD`: the interior is the default region.
- `REVERSED`: the interior is the complement.
- `INTERNAL`: both sides are interior, so the boundary lies inside material.
- `EXTERNAL`: neither side is, so the boundary lies outside material.

For an edge bounding a face, the default region is on the left of the edge
along its natural direction. For a face bounding a solid, the default region
is on the negative side of the normal. A solid whose faces all point inward is
"inverted": it can pass some validity checks and still report negative or
wrong volume ([[kernel-validity#validity-is-not-positive-volume]]).

## Shared sub-shapes and locations

A `TopoDS_Shape` is a handle to a shared `TopoDS_TShape` plus a
`TopLoc_Location` and an orientation. Many shapes can reference one
`TShape` in different places, which is how repeated instances cost almost
nothing, and why a shallow copy moves with its original's geometry
([[build123d-builder-and-algebra#practices-the-docs-recommend]]).

Two faces of a valid solid *share* their common edge: it is the same `TShape`,
not two coincident copies. A shell with two coincident but unshared edges has
a gap as far as topology is concerned, and sewing exists to merge them.

## Tolerance

- Only vertices, edges and faces carry a tolerance ("In Open CASCADE
  Technology only vertices, edges and faces have tolerances"). It is a
  geometric slack: a vertex is valid anywhere within its tolerance of the
  curve ends it joins.
- **Shapes interfere when "the distance between the underlying geometry of
  shapes is less or equal to the sum of tolerances of the shapes."** This is
  why a boolean between a part with large tolerances (from an imported file,
  or from a previous healing pass) and a clean part can merge features that are
  visibly apart, and why near-coincident faces either fuse or fail
  ([[boolean-pitfalls#near-coincident-surfaces-collapse-the-boolean]]).
- Intersections grow tolerances. A vertex on an edge gets
  `Max(Tol(V), D + Tol(E))`, where D is the projection distance, and a new
  face/face vertex gets a sphere enclosing its source tolerance spheres.
  Long boolean chains accumulate slack. Checking the maximum tolerance on a
  result is a cheap health signal.
- Healing tools take a working precision, a maximum tolerance (how far a fix
  may grow tolerances) and a minimum tolerance (the smallest edge to keep):
  [[occt-shape-healing]].

## What a boolean argument must be

From the Boolean Operations specification:

- each argument is valid in terms of `BRepCheck_Analyzer`;
- an argument is not self-interfering: its sub-shapes that touch must share
  the touching entities;
- the underlying geometry of faces and edges is at least C1 continuous.

Violating any of these gives undefined results, not an error. The argument
analyzer checks them before you run the operation:
[[occt-boolean-options#check-the-arguments-first-bopalgo_argumentanalyzer]].
