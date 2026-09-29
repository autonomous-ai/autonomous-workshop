---
title: Reading CadQuery examples in build123d
tags: [cadquery, build123d, selector, workplane, migration, translation]
aliases: [cadquery selectors, string selectors, workplane stack, fluent api, port cadquery]
sources:
  - https://build123d.readthedocs.io/en/latest/introduction.html
  - https://build123d.readthedocs.io/en/latest/key_concepts.html
  - https://cadquery.readthedocs.io/en/latest/selectors.html
related: [build123d-builder-and-algebra, build123d-selectors, element-libraries]
updated: 2026-09-23
---

# Reading CadQuery examples in build123d

Most published OCCT-in-Python examples are CadQuery. Both libraries sit on
the same kernel (OCP), so the geometry transfers; the syntax does not. This
page is only what you need to translate an example.

## The model differs

| | CadQuery | build123d |
|---|---|---|
| style | fluent chaining: `Workplane("XY").box(...).faces(">Z").hole(...)` | context managers (`with BuildPart():`) or algebra (`Box(...) - Cylinder(...)`) |
| state | a workplane stack; each call returns a new workplane | the builder's running total, or plain variables |
| selection | string selectors | Python operators on `ShapeList` plus enums (`Axis`, `GeomType`, `SortBy`) |
| options | string literals | enums, so the IDE completes them |
| intermediate results | hard to capture mid-chain | every object is a variable you can print or assert on |

## Selector translation

CadQuery string selectors and their build123d
equivalents (`>`/`<` sort, `>>`/`<<` group, `|` filter):

| CadQuery | meaning | build123d |
|---|---|---|
| `">Z"` | farthest in +Z | `part.faces().sort_by(Axis.Z)[-1]` |
| `"<Z"` | farthest in −Z | `part.faces().sort_by(Axis.Z)[0]` |
| `"\|Z"` | parallel to Z | `.filter_by(Axis.Z)` |
| `"%Plane"`, `"%Circle"`, `"%Line"` | by geometry type | `.filter_by(GeomType.PLANE)` / `CIRCLE` / `LINE` |
| `">Z[1]"`, `"<Z[-2]"` | indexed among the sorted | sort, then index |
| `">>Z[-2]"` | by centre location | `.group_by(Axis.Z)` then index a group |
| `"\|Z and >Y"`, `or`, `not`, `exc` | set logic | Python list logic / `ShapeList` filtering |

`#Z` (perpendicular to Z) and `+Z`/`-Z` (normal aligned with ±Z) also exist in
CadQuery. In build123d you filter by the face normal. Stable selection rules
(prefer a group or a geometric test over an index) are in
[[build123d-selectors]].

## Workplanes become planes and locations

`.faces(">Z").workplane()` creates a working plane on the selected face. The
build123d equivalent is `Plane(face)`, or a sketch placed on the face, followed
by operations in that plane. Placing on a face ties the feature to that face's
identity. Where you can, place from a named parameter (a height or an offset)
instead ([[parametric-design-intent#reference-stable-things]]).

## CadQuery-only libraries

Libraries built on CadQuery objects (cq_warehouse, cq_gears and similar)
cannot be mixed directly with build123d objects. Their build123d counterparts
and the reasons are in [[element-libraries#cadquery-libraries-that-do-not-apply]].
