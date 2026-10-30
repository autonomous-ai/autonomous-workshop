---
title: build123d operations and STEP export
tags: [build123d, operations, extrude, revolve, loft, sweep, offset, export, step, color, label]
aliases: [export_step, import_step, operation parameters, step colours, step labels]
sources:
  - "experience: an extruded offset-curve band vanished from its STEP on re-import; a sampled periodic spline survived"
  - https://build123d.readthedocs.io/en/latest/operations.html
  - https://build123d.readthedocs.io/en/latest/import_export.html
  - "experience: an assembly measured through a new Compound of its parts exported with its part names gone"
  - "experience: a revolved offset() envelope lost its offset-curve face in the STEP; the drum cut by it read back as an open shell"
  - "experience: a revolved pumpkin core whose STEP read back with negative face areas"
  - "toolchain: offset of a B-spline section face failed; offsetting a 360-point polygon of the same wire worked"
related: [build123d-builder-and-algebra, operation-families, cad-joint-types, step-file-format, sweeps-and-helices, mass-properties-and-measurement]
updated: 2026-10-12
---

# build123d operations and STEP export

A lookup page: which operation exists for which dimension, the parameters that
matter, and what `export_step` writes. For choosing an operation family from
the object's form, see [[operation-families]]; for the joints API,
[[cad-joint-types#joints-api-contract]].

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

### A solid on an offset curve is written and not read back

A face bounded by `offset()`'s 2D result -- offset curves -- extruded into a
solid exports without error, and `import_step` returns the file one solid
short: the offset band was the only part missing, while every spline, cone
and torus solid beside it came back to the cubic millimetre. Nothing but a
round trip shows it. Rebuild such an outline before extruding: sample the
offset wire (`position_at` every ~0.5 mm) and pass the points to
`Edge.make_spline(..., periodic=True)`. Round-trip any entry that uses a new
construction: `export_step`, `import_step`, and compare solid count and volume.

Revolved, the same edges fail differently: the solid is written, but the face
swept by the offset curve is dropped, and the solid reads back as an open
*shell* one face short (a clearance envelope made by shrinking an (r, z) region
with `offset()`, then revolving it, lost its whole barrel top). Anything cut
with that envelope inherits the face and the defect. `inspect validate` on the
generator checks the in-memory solid and passes; only the source-versus-STEP
drift render (`render_views --compare-step`) sees the missing area. Convert
the offset face before using it -- `Face(BRepBuilderAPI_NurbsConvert(face.wrapped,
True).Shape())` -- which turns every offset curve into a plain B-spline; the
round trip then returns the solid with every face.

### A revolved half-ellipse sketch breaks on the STEP round trip

A spheroid revolved from a half `Ellipse` sketch (ellipse intersected with a
rectangle) passes every source check. After a STEP write and read, its faces
come back with negative area, and the volume of a lone spheroid went from
26 229 to 39 344 mm^3. `render_views --compare-step` then fails with
"comparison mesh omitted N face(s)". Revolve a wire of one elliptic arc
(`Edge.make_ellipse`) plus its chord instead; that round-trips cleanly.

### Nested recess order can produce a valid source that loses its shell in STEP

A trimmed ellipsoid can pass source BOP validation yet return from STEP as
several small cavity solids, with its exterior missing. Those imported pieces
can also pass BOP validation. Validity therefore does not establish round-trip
completeness: compare per-region solid counts, adaptive volumes and bounds,
then inspect actual exported views.

When raw primitives and individual cuts roundtrip, isolate the combination of
overlapping recess tools. Cutting a small nested detail before its larger
enclosing recess can leave export-unstable trims. Subtract the largest envelopes
first, then apply the smaller details and interface cuts sequentially. Prove
empty source differences in both directions, exact partition coverage and
disjointness, and a successful new STEP roundtrip. Dropping an apparently
redundant small cutter is not equivalent unless its residual difference is
empty. Seam rotation, generic healing, NURBS conversion or disabling pcurves
are possible diagnostics, not substitutes for that proof.

Check the fused physical entry separately from its coloured assembly. Independent
colour solids can retain a small exterior relief that disappears from the
physical STEP, even when both physical bodies report valid topology. Derive an
interior probe near each required relief's exposed tip and test it in the source,
the imported physical body and the corresponding imported colour region. A
failed physical probe cannot be cleared by a correct coloured preview. Localise
source-minus-STEP residuals to those feature envelopes before trying further mass
integration methods; an invalid reverse residual does not establish equivalence.

## Small traps

- `Vector.get_angle(other)` returns **degrees**. Wrapping it in
  `math.degrees()` turns a 90° rod into one rotated 5157°, and every rod built
  that way lands at the wrong angle without an error.
- `offset(open_wire, d)` returns a closed `Wire`, not a `Face`. `extrude` of
  that wire makes a zero-volume shell, and the first boolean with it fails as
  "Cannot intersect shape with empty compound". `make_face()` it first.
- `Location * Vector` raises (`Multiplied(): incompatible function
  arguments`). Carry a point with `(loc * Location(tuple(p))).position`.
- `Face.center()` is the point at the middle of the face's parameter range,
  which lies **on** a curved surface: a full cylindrical wall of radius 2
  reports X = -2, not its axis. A landmark that locates a bore, peg or
  socket by its wall face needs `bounding_box().center()` or
  `center(CenterOf.MASS)`.
- `Face.make_surface(exterior, surface_points)` needs a `Wire`; a list of
  edges fails `non planar face is invalid`. `Solid.thicken` past the concave
  radius returns an invalid solid without raising, and the functional
  `thicken()` thickens each face separately and fuses
  ([[freeform-surfaces-in-build123d]]).

## Offsetting a B-spline section

A planar face whose boundary is a B-spline (a section cut through a lofted
body) does not `offset` reliably in OCC. Sample the wire to a polygon (about
360 points), rebuild the face from it, and offset that.

## A Compound takes the children it is given

`Compound(children=[...])` makes itself the parent of every shape in the list
(the tree is `anytree`), and a node has one parent, so each shape leaves the
compound that held it. Wrapping an assembly's parts in a new `Compound` to get
one bounding box over several modules empties those modules. The failure is
silent: the exported STEP keeps every solid, because the parent's OCCT shape
was built before, but the moved parts lose their product names.
Measure without building a tree: combine each part's own `bounding_box()`, or
wrap copies.
A child's own box is in its parent's frame
([[mass-properties-and-measurement#bounding-boxes]]).
