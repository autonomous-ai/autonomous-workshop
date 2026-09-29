---
title: build123d builder mode and algebra mode
tags: [build123d, builder, algebra, buildpart, buildsketch, buildline, mode, location, placement]
aliases: [builder mode, algebra mode, BuildPart, BuildSketch, BuildLine, context manager, Mode.SUBTRACT, pending faces, Pos, Rot]
sources:
  - https://build123d.readthedocs.io/en/latest/key_concepts.html
  - https://build123d.readthedocs.io/en/latest/key_concepts_builder.html
  - https://build123d.readthedocs.io/en/latest/key_concepts_algebra.html
  - https://build123d.readthedocs.io/en/latest/tips.html
related: [build123d-operations-and-export, build123d-selectors, frames-and-rotations, sketch-and-extrude-direction, cadquery-to-build123d]
updated: 2026-09-23
---

# build123d builder mode and algebra mode

build123d offers two ways to write the same model. Builder mode uses context
managers that keep a running total, and algebra mode uses plain objects combined
with operators. Both produce the same OCCT shapes and can be mixed, as long as
you know where a builder's result lives.

## The object model

Topology, from simplest to most complex: `Vertex` (a 0D point), `Edge` (a 1D
curve segment), `Wire` (connected edges, open or closed), `Face` (a bounded
surface), `Shell` (connected faces), `Solid` (a bounded volume) and `Compound`
(a container of any of these), all subclasses of `Shape`. Geometry that places
things: `Location` (translation plus rotation), `Plane` (origin plus x/y/z
directions) and `Axis` (origin plus direction).

A `Location` has `position` and `orientation`. Four methods change it:
`locate()` sets it absolutely, `located()` does the same on a copy, `move()`
applies a relative change, and `moved()` applies it to a copy. Locations
compose with `*` and invert with `-`.

## Builder mode

Three builders, each publishing one result:

| builder | builds | result | before placement |
|---|---|---|---|
| `BuildPart` | 3D solids | `.part` | `.part_local` |
| `BuildSketch` | 2D faces | `.sketch` | `.sketch_local` |
| `BuildLine` | 1D curves | `.line` | `.line_local` |

- **Nesting.** A `BuildSketch` inside a `BuildPart` hands its faces to the
  parent as `pending_faces` when it exits. The next `extrude()`, `revolve()` or
  `loft()` consumes them without being given them. Pending geometry can be read
  as `<builder>.pending_faces` / `.pending_edges`.
- **Every sketch works on its own local `Plane.XY`.** The plane you pass
  (the first argument) is applied only when the builder publishes. So
  `sort_by()` inside a sketch declared on a non-XY plane sorts in local
  coordinates, which can give unexpected, apparently random picks. Nested
  builders do not inherit the parent's placement either.
- **`BuildLine` inside `BuildSketch`** reorients coordinates in ways that are
  often not intended. The docs advise the default placement.
- **`Mode` decides how a new object combines with the running total:**
  `ADD` (the default for most objects), `SUBTRACT` (the default for `Hole`
  classes), `INTERSECT`, `REPLACE` (discard the total, keep the new object) and
  `PRIVATE` (build it but do not combine it).
- **Location contexts** multiply positions onto everything created inside them:
  `Locations` (an explicit list), `GridLocations` (a Cartesian array),
  `PolarLocations` (a circular pattern with rotation) and `HexLocations`.
  Nested contexts compound.

### The builder trap: objects add themselves when created

An object joins the active builder the moment it is constructed. So
`Cylinder(1, 2).moved(...)` moves only a temporary Python copy, and the
builder keeps the unmoved cylinder. Place an object *before* creating it, with
a `Locations` context or a placement argument, never with a method chained
afterwards.

## Algebra mode

Objects are values, and operators combine them:

| operator | meaning | example |
|---|---|---|
| `+` | union | `Box(1, 2, 3) + Cylinder(0.2, 5)` |
| `-` | difference | `Box(1, 2, 3) - Cylinder(0.2, 5)` |
| `&` | intersection | `Box(1, 2, 3) & Cylinder(0.2, 5)` |
| `*` | placement | `Plane.XZ * Pos(1, 2, 3) * Rot(0, 100, 45) * Box(1, 2, 3)` |
| `@` | position on an edge or wire at a parameter | |
| `%` | tangent on an edge or wire at a parameter | |

The general pattern is `Plane * Location * object`. `Pos()` translates and
`Rot()` rotates, and they compose left to right onto the object at the far
right. `*` binds tighter than `+`/`-`, so
`Plane.XZ * Rot(X=30) * Box(1, 2, 3) + Plane.YZ * Pos(X=-1) * Cylinder(0.2, 5)`
needs no parentheses. Boolean results are `Compound`s. The order in which
rotations compose is its own trap: [[frames-and-rotations]].

## Mixing the two

A builder's shape is not an algebra value until you take it out: use
`with BuildPart() as bp: ...` and then `bp.part`. `Select.LAST` inside a
builder refers to what the most recent operation created, which is how builder
code picks the edges a fillet should touch.

## Practices the docs recommend

- **Design in 2D, then go to 3D.** 3D operations are slower and fail more
  often than a sketch followed by `extrude()`/`revolve()`.
- **Fillets and chamfers last** ([[fillet-chamfer-pitfalls]]).
- **Never build self-intersecting topology**, even at one vertex: "these
  topologies will almost certainly be invalid" ([[kernel-validity]]).
- **Select from the top of the topology down**: a face first, then its edges.
- **Shallow copies for repeated parts** (fasteners, bearings, chain links) are
  much faster. A change to one changes them all.
- **If one operation fails, try another family**: a multi-section `sweep()`
  that fails may succeed as a `loft()` ([[operation-families]]).
