---
title: Sketch algebra, winding and extrude direction
tags: [sketch, polygon, winding, extrude, direction, align, mirror, shapelist, build123d]
aliases: [2D union, clockwise polygon, mirrored points, Plane.XZ normal, align None, ShapeList concatenation]
sources:
  - skills/cad/references/build123d-modeling.md (sketch algebra, align and failure-mode sections; before the move)
  - "experience: two modules independently shipped off-centre cutters from assuming align=None means centred"
  - "experience: a disc body extruded with a negative amount from a spline face landed above its bevel cap"
related: [operation-families, kernel-validity, modeling-failure-modes]
updated: 2026-10-05
---

# Sketch algebra, winding and extrude direction

Every trap on this page is silent: each part builds, has positive volume and
passes `validate`; only the assembly is wrong, and only where two parts happen
to overlap does `interfere` notice.

## 2D unions decay

Chained 2D unions are fragile in three stacked ways:

- `Circle + Circle` returns a fused `Face`, and the next `Face + Polygon`
  falls into raw shape fuse returning an unregularized face pile; once any
  step yields a `ShapeList`, later `+` is Python list concatenation, not
  geometry. Build each profile as ONE multi-operand fuse: `first + [rest...]`.
- A CLOCKWISE-wound `Polygon` fuses as a reversed face: the union "succeeds"
  but shatters into mixed-normal fragments and `extrude()` runs along the
  reversed normals — solids appear mirrored below the plane. Wind every
  polygon CCW. **Mirroring a point list reverses its winding**: mirror with
  `[(-y, z) for y, z in reversed(pts)]`, or the extrude silently runs the
  other way and the cutter lands off the part.
- `ShapeList & Sketch` used as a regularizing clip returns an EMPTY list with
  no error, and the following extrude quietly produces a zero-volume part.
  Apply the `& clip` intersection exactly once, LAST, on the single fused
  profile.

The same list trap applies in 3D: `solid += helper()` where the helper returns
a *list* turns the accumulator into a `ShapeList`, and the failure surfaces
much later as an anytree `Cannot add non-node object` from inside
`Compound(children=...)`.

## State the extrude direction

`extrude(sketch, amount, dir=(0, 1, 0))` takes the sign out of the winding's
hands, and that matters most on `Plane.XZ`, whose normal is **−Y**:
`extrude(Plane.XZ * sk, +t)` runs *toward −Y*, so a barrel you meant to build
rearward along a +Y bore axis lands in front of the cover instead — and a
clockwise polygon in the same file then runs the opposite way again, so two
prisms written identically end up in different half-spaces. Put it in one
helper:

```python
def _prism(sketch, y0, length):
    return Pos(0, y0, 0) * extrude(Plane.XZ * sketch, length, dir=(0, 1, 0))
```

A `Face(wire)` built from a periodic spline sampled off a `shapely` ring takes
its normal from the ring's winding, so it can face −Z: `extrude(face, -t)`
meant to run down then runs up and fuses inside the body above it, and only
the bounding box shows it. Pass `dir=(0, 0, -1)` with a positive amount.

## align None is the raw OCC datum

`Cylinder`/`Cone` with `align=(None, None, None)` sit base-at-z=0 (XY
centred); `Box` sits with its CORNER at the origin. Code written assuming
"None means centred" produces silently wrong geometry — off-centre slots,
inverted countersinks, cutters that remove nothing because they sit entirely
above the surface. Two independent modules shipped defects from this exact
assumption. Default alignment IS centred; reserve `align=None` for when the
raw datum is genuinely wanted.

## Open profiles

An open sketch profile produces an invalid or missing face. Close every
profile intended to become a face (`close=True` on a `Polyline`, then
`make_face()`), and a revolve profile must also touch the axis
([[operation-families#revolve]]).

## A mirrored outline extrudes the other way

When one outline serves both sides of a symmetric body by mapping its local x to
`sign * y`, the left copy winds the opposite way round. `extrude(Face(wire),
amount)` follows the face normal, so the left copy goes *into* the part while the
right goes out. If the pocket and the insert are built from the same outline
the mistake is invisible to the gates: the pocket is cut the same wrong way, the
insert sits exactly in it, `validate` and `interfere` pass, and a skin of wall
covers a window that is not there. One side of a cab lost its glass this way
(left glass volume exactly half of the right one: the part-sized slab was clipped
by a box meant for the outward direction). State the direction on every
extrusion built from a mirrored outline (`dir=Vector(0, 0, 1)` in the frame's own
z) and compare the volume of the two mirrored parts; they must be equal.
