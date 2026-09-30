---
title: build123d selectors
tags: [selector, build123d, faces, edges, topology, sort-by, group-by, filter-by]
aliases: [face selection, edge selection, selector cookbook, topology selection, ShapeList]
sources:
  - skills/image-to-cad/references/build123d-operations.md (selector cookbook; before the move)
  - skills/cad/references/build123d-modeling.md (selection practices; before the move)
related: [frames-and-rotations, construction-strategy, modeling-failure-modes]
updated: 2026-09-23
---

# build123d selectors

The selector is where image-derived specs most often fail to build. build123d
selects with `ShapeList` methods, not with CadQuery's string mini-language.

## Selector cookbook

| Selector | Selects | Use for |
|---|---|---|
| `.faces().sort_by(Axis.Z)[-1]` | Topmost face | Working on the top |
| `.faces().sort_by(Axis.Z)[0]` | Bottom face | Feet, base features |
| `.faces().group_by(Axis.Z)[-2]` | Second band from the top | The **inside floor** of a shelled box |
| `.faces().sort_by(Axis.X)[-1]` | Outermost face on an axis | Side-wall features |
| `.faces().filter_by(Plane.XY)` | All horizontal planar faces | Excluding curved faces from a fillet |
| `.edges().filter_by(Axis.Z)` | All edges parallel to Z | The corner-radius set |
| `.edges().group_by(Axis.Z)[-1]` | Highest edge band | Top rim only |
| `.faces().filter_by(GeomType.PLANE)` | Planar faces only | Keeping a fillet off a lofted skin |
| `Plane.XY.offset(h)` | A plane at a height | A feature with no face to land on |
| `Plane(origin=..., x_dir=..., z_dir=...)` | An explicit frame | Angled features, leaning faces |

## Rules for stable selection

Avoid fragile topology order. Select by, in order of preference:

- axis or normal;
- location or bounding position;
- plane grouping;
- feature intent;
- a stable construction plane;
- an inspected local selector ref for downstream validation.

Three rules from experience:

1. **Build angled frames from explicit direction vectors.** `Plane.rotated()`
   composes in **world axes, not the plane's own**; on a plane whose axes are
   not the global ones, what reads as a pitch is a yaw, and the result is a
   valid solid of the wrong shape that passes every deterministic check
   ([[frames-and-rotations]]).
2. **Prefer position/axis selection to list indexes** that depend on
   construction order. Any boolean or fillet invalidates the ordering.
3. **Re-select after every boolean.** A face list captured before a cut refers
   to faces that no longer exist.

Faces and edges have no persistent intent labels through STEP export: inspect
them by occurrence, shape, ordinal, surface/curve type and measured geometry.

Translating CadQuery string selectors: [[cadquery-to-build123d#selector-translation]].
