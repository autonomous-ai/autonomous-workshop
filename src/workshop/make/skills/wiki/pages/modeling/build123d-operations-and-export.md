---
title: build123d operations, joints and STEP export
tags: [build123d, operations, extrude, revolve, loft, sweep, offset, export, step, joints, color, label]
aliases: [export_step, import_step, operation parameters, RigidJoint, RevoluteJoint, connect_to, step colours, step labels]
sources:
  - https://build123d.readthedocs.io/en/latest/operations.html
  - https://build123d.readthedocs.io/en/latest/import_export.html
  - https://build123d.readthedocs.io/en/latest/joints.html
  - "experience: an assembly measured through a new Compound of its parts exported with its part names gone"
related: [build123d-builder-and-algebra, operation-families, cad-joint-types, step-file-format, sweeps-and-helices, mass-properties-and-measurement]
updated: 2026-09-28
---

# build123d operations, joints and STEP export

A lookup page: which operation exists for which dimension, the parameters that
matter, the joints API contract, and what `export_step` writes. For choosing an
operation family from the object's form, see [[operation-families]].

## Operations by dimension

| operation | applies to | does |
|---|---|---|
| `extrude()` | 3D | draws a 2D shape into 3D |
| `revolve()` | 3D | swings a 2D shape about an axis |
| `loft()` | 3D | a solid through sections ([[loft-pitfalls]]) |
| `sweep()` | 2D, 3D | 1D/2D section(s) along a path |
| `thicken()` | 3D | expands 2D sections into solids |
| `draft()` | 3D | adds a draft taper to faces |
| `fillet()` / `chamfer()` | 2D, 3D | radius or bevel on vertices or edges |
| `full_round()` | 2D | rounds off a face along an edge |
| `offset()` | 1D, 2D, 3D | insets or outsets a shape |
| `mirror()` | 1D, 2D, 3D | mirrors about a plane |
| `split()` | 1D, 2D, 3D | divides by a plane |
| `section()` | 3D | 2D slices from a solid |
| `project()` | 0D, 1D, 2D | projects points, lines or faces |
| `make_face()` / `make_hull()` | 2D | a face from edges / a convex hull |
| `trace()` | 2D | converts lines into faces |
| `scale()` | 1D, 2D, 3D | resizes |
| `make_brake_formed()` | 3D | sheet-metal parts |
| `bounding_box()`, `insert()` | any | adds a box shape / inserts an object |

Key parameters:

- `extrude(amount, dir, until, target, both, taper, clean, mode)`. `until`
  plus `target` extrudes up to existing geometry, and `both` goes both ways.
- `revolve(profiles, axis, revolution_arc, clean, mode)`. The seam lands at
  +X: [[revolve-seam]].
- `sweep(sections, path, multisection, is_frenet, transition, normal,
  binormal, clean, mode)`. `is_frenet` and `normal`/`binormal` control section
  twist along the path.
- `loft(sections, ruled, clean, mode)`. `ruled=True` gives straight segments
  between sections, which do not overshoot.
- `offset(amount, openings, kind, side, closed, min_edge_length, mode)`.
  `openings` names the faces to remove when shelling a solid. Note that a
  plain negative offset shrinks the solid instead of hollowing it:
  [[wall-thickness-and-hollowing]].

Sweep frame modes, corner transitions and helices, with measured failures:
[[sweeps-and-helices]]. Volume, centre of mass, bounding boxes and distances:
[[mass-properties-and-measurement]].

## Joints API contract

The five joint classes are `RigidJoint`, `RevoluteJoint`, `LinearJoint`,
`CylindricalJoint` and `BallJoint`. They take `label` (unique within a part),
`to_part`, and then `joint_location` (Rigid, Ball) or `axis` (Revolute,
Linear, Cylindrical) plus `angular_range` / `linear_range`.

- `a.joints["x"].connect_to(b.joints["y"])` keeps **a's** part fixed and
  **moves b's** part.
- Valid pairs: Rigid↔Rigid; Ball↔Rigid (`angles`); Revolute↔Rigid (`angle`);
  Linear↔Rigid or Revolute (`position`); Cylindrical↔Rigid (`position`,
  `angle`).
- A value outside the declared range raises an exception, which is a free
  limit check.
- `connect_to()` repositions once and is not a live constraint. Inside a
  `BuildPart` the `to_part` is optional, because the builder attaches the
  joints on exit.

When to use a joint at all, and which type: [[cad-joint-types]].

## Imports inside a generator

Import sibling modules at the top of a generator's module, never inside a
function that `gen_step()` calls. The generation runner puts the project
directory on the path while it imports the entry, and not while it runs
`gen_step()`. A late `import sibling` therefore works in a plain script and in
the audit, then fails under `gen` with `ModuleNotFoundError`. When two modules
would import each other, move the shared constant into the module both
already import.

## export_step and import_step

```python
export_step(to_export, file_path, unit=Unit.MM, write_pcurves=True,
            precision_mode=PrecisionMode.AVERAGE, timestamp=None) -> bool
import_step(filename) -> Compound
```

- Labels and colours on shapes are written. In an assembly (a `Compound` with
  children), a child without its own colour inherits its nearest ancestor's.
- The default unit is millimetres. `write_pcurves` keeps the curves-on-surface
  (on by default). `precision_mode` maps shape tolerances onto the STEP
  uncertainty value (least / average / greatest), the same as OCCT's
  `write.precision.mode` ([[step-file-format#what-the-translator-writes]]).
- `import_step` returns one `Compound`. Its children are the solids, and
  labels come back when the file carried them.

## A Compound takes the children it is given

`Compound(children=[...])` makes itself the parent of every shape in the list
(the tree is `anytree`), and a node has one parent, so each shape leaves the
compound that held it. Wrapping an assembly's parts in a new `Compound` to get
one bounding box over several modules empties those modules. The failure is
silent: the exported STEP keeps every solid, because the parent's OCCT shape
was built before, but the moved parts lose their product names.
Measure without building a tree: combine each part's own `bounding_box()`, or
wrap copies.
- A child's `bounding_box()` is in its **parent's** frame. The parent's
  `location` is not applied to it. This holds for any `Compound`, not only an
  imported one: after `Pos(10, 0, 0) * compound`, the compound's box moves and
  `compound.children[0]` does not. Two consequences follow.
  - An assembly exported as an exploded view, or with sub-assembly
    transforms, diffs cleanly part against part inside one group while whole
    groups sit apart in the world. Compose the ancestor locations before you
    compare positions across groups, and never read a whole group's offset as
    a moved part.
  - To carry a marker edge through a transform written for a whole part,
    transform the edge on its own. Wrapping it in a `Compound` with the part
    and reading it back from `.children` returns it unmoved.

Other writers: `export_stl`, `export_obj` (mesh with UVs), `export_gltf`,
`export_brep` (the OCCT native B-rep), 3MF via `Mesher.write()`, and
`ExportDXF`/`ExportSVG` for 2D drawings. Only the STEP and BREP writers keep
exact geometry. All the others tessellate.
