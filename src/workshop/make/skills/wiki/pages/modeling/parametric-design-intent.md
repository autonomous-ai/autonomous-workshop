---
title: Parametric design intent and stable references
tags: [parametric, design-intent, topological-naming, reference, feature-order, robustness]
aliases: [topological naming problem, TNP, toponaming, face index changes, robust references, datum planes, design intent]
sources:
  - https://github.com/FreeCAD/FreeCAD-documentation/blob/main/wiki/Topological_naming_problem.md
  - https://www.ondsel.com/blog/toponaming-problem-is-history/
  - https://build123d.readthedocs.io/en/latest/tips.html
  - https://occt3d.com/dev/doc/overview/html/specification__boolean_operations.html
related: [build123d-selectors, construction-strategy, feature-build-order, occt-boolean-options]
updated: 2026-09-23
---

# Parametric design intent and stable references

A parametric model is meant to rebuild correctly when a number changes. Most
failures to do so trace to one cause: a feature referenced *a piece of
generated geometry by its identity or index*, and the edit renumbered or
reshaped that geometry.

## The topological naming problem

In FreeCAD's words, a shape "changing its internal name after a modeling
operation (pad, cut, union, chamfer, fillet, etc.)" breaks the features that
depend on it. Names like `Face6` and `Edge3` are type plus index. When an edit
adds or removes faces, indices are reused, and nothing tracks which is which.
A sketch attached to `Face6` jumps to a different face, or the fillet on
`Edge3` lands on the wrong edge, and the rebuild often *succeeds* with the
wrong result. (FreeCAD 1.0 added mitigation; code-CAD has the same problem
whenever a selection is an index.)

In build123d the same trap is `part.faces()[5]`, or `sort_by(...)[k]` on a
list whose length changes with a parameter.

## Reference stable things

In order of robustness:

1. **Origin planes, axes and named parameters.** Place a feature at
   `Plane.XY.offset(HEIGHT)`, not on "the top face". FreeCAD's advice is the
   same: attach sketches to the coordinate planes, not to faces, edges or
   vertices of the solid. The cost is that the feature no longer follows the
   face automatically, so the relationship has to live in the parameters
   (`HEIGHT` used by both).
2. **Datum geometry you create yourself** (a `Plane`, an `Axis`, a
   `Location` computed from parameters). It depends on numbers, not on the
   topology of the result.
3. **Geometric queries with a unique answer**: the planar face whose normal
   is +Z and whose centre is highest, or the circular edges of radius R. These
   survive renumbering as long as the query stays unique. Assert that it
   returns exactly one match.
4. **Operation history**: the faces a specific cut `Generated()`, or
   `Select.LAST` in a builder
   ([[occt-boolean-options#history-which-faces-came-from-where]]).
5. **Bare indices**, never.

## Feature order protects intent

- Primary shape, then additive features, then subtractive features, then
  finishing (fillets and chamfers last), as the build123d tips also advise.
  The ordering rules are in [[feature-build-order]] and
  [[construction-strategy#boolean-order]].
- Build sketches in 2D and extrude, rather than editing 3D topology. The 2D
  profile is a stable, parameter-driven reference.
- A feature that depends on a finishing operation (a hole placed on a filleted
  face) inherits that operation's fragility. Place it from the parameter
  instead.

## Test the intent, not the one value

A parametric model is proven only when it rebuilds across its declared range.
Rebuild at the minimum, nominal and maximum of each driving parameter, and
assert the invariants: solid count, the selection queries each return one
match, volumes move in the expected direction.
