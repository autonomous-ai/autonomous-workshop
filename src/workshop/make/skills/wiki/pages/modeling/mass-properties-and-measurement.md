---
title: Mass properties and measurement
tags: [volume, area, mass, center-of-mass, inertia, bounding-box, distance, clearance, measurement]
aliases: [center of mass, centre of gravity, CoM, CenterOf.MASS, CenterOf.BOUNDING_BOX, matrix_of_inertia, principal_properties, radius_of_gyration, moment of inertia, distance_to, distance_to_with_closest_points, BRepExtrema_DistShapeShape, GProp_GProps, minimum distance, weight estimate, bounding box optimal]
sources:
  - "experience: ten wordmark-inlaid plates whose region-sum audit failed under one integration call or the other"
  - .venv/lib/python3*/site-packages/build123d/topology/shape_core.py (area, matrix_of_inertia, principal_properties, radius_of_gyration, compute_mass, combined_center, bounding_box, distance_to_with_closest_points)
  - .venv/lib/python3*/site-packages/build123d/topology/composite.py (Compound.volume, Compound.center)
  - .venv/lib/python3*/site-packages/build123d/geometry.py (BoundBox.from_topo_ds, BoundBox.is_inside)
  - "toolchain: build123d 0.11.1 on OCP, every number below measured with small shapes"
  - "toolchain: a traced 650-sample spline plate whose default volume read 14-80 % high while precise integration and its mesh agreed"
related: [kernel-validity, occt-topology-and-tolerance, boolean-pitfalls, parametric-design-intent, mechanism-verification, filament-properties]
updated: 2026-10-08
---

# Mass properties and measurement

What build123d measures, in which frame, and where the number means
something other than it seems. Every measurement here is cheap (milliseconds
on small parts) and belongs in the generator as an `assert`.

## Volume, area, length

- `shape.volume` for a `Solid`/`Part` is `BRepGProp.VolumeProperties` —
  exact on analytic solids (sphere, torus, cylinder: relative error 2e-16)
  and ~1e-7 on a swept helix. Edges and faces return `volume == 0.0`.
- **Not on faces bounded by many-pole B-splines.** On a plate whose sections
  are one periodic spline through 650 samples, the default integration read
  a ruled loft as 7530 mm³ against 6624 (14 % high), the same body after three
  cuts as 11546 against 6427 (80 %), and gave a plain extrude of that face
  -140 at a tight tolerance; `check_fit`'s volume column printed the wrong
  figure too. The geometry was sound: `BRepGProp.VolumeProperties_s(shape.wrapped,
  props, 1e-6, True)` and the volume of the tessellation agreed to 0.1 %.
  For mass or volume asserts on such a body use that call, or the mesh.
- **And not that call on text.** On solids bounded by text-glyph faces (an
  inlaid wordmark) the same `1e-6, True` call read one letter 5 % high, and
  the colour regions of a plate summed 0.2–0.3 mm³ away from the plate they
  were cut from; the default call came within 0.01–0.07 mm³, and the
  tessellated pieces within 0.001. Neither integration is safe on every
  surface family, so audit a split (regions against their whole) with a
  relative tolerance, about 1e-4 of the whole, or on the mesh, never with an
  absolute 0.05 mm³.
- `shape.area` sums every face; `edge.length` / `wire.length` for curves.
- **`Compound.volume` sums its solids without fusing.** Two 10 mm cubes
  overlapping by half: compound 2000, fused 1500. An assembly compound's
  volume is not the material volume; an overlap is invisible in it. Fuse
  first, or compare the sum against the fused volume to *measure* overlap.
- An empty result is not `None`: the intersection of two face-touching boxes
  is an empty `Compound` with volume 0. Assert on volume, not truthiness.

## Center: MASS, BOUNDING_BOX, GEOMETRY

| call | returns |
|---|---|
| `part.center()` | centre of mass (default `CenterOf.MASS`), density 1 |
| `part.center(CenterOf.BOUNDING_BOX)` | middle of the bounding box |
| `part.center(CenterOf.GEOMETRY)` | **raises `ValueError`** on Solid/Part/Compound |
| `edge.center()` | default is `CenterOf.GEOMETRY` (mid-parameter point) |

They differ exactly where it matters: an L of two 20×4×4 bars has mass
centre (6.44, 6.44, 2) and bounding-box centre (10, 10, 2). Use MASS for
balance, tipping and centre-of-gravity checks; BOUNDING_BOX only for
placement.

## Density-weighted centre of mass for mixed materials

build123d has no density: `Shape.combined_center([...])` and
`Compound.center()` both weight by volume. For an assembly of different
materials weight each part yourself:

```python
parts = [(steel_pin, RHO_STEEL), (body, RHO_PLA)]   # g/mm^3, provenance in params
m = [s.volume * rho for s, rho in parts]
com = sum((s.center() * mi for (s, _), mi in zip(parts, m)), Vector()) / sum(m)
```

A Ø4 × 10 steel pin 50 mm above a 20 × 20 × 5 PLA plate: volume-weighted
centre z = 2.96, density-weighted z = 14.23 — the pin is 29 % of the mass
and 6 % of the volume. For printed parts use an effective density for the print
settings (perimeters are solid, infill is not), not the filament's ([[filament-properties]],
[[perimeters-infill-and-strength]]).

## Inertia: about the centre of mass, density 1

- `part.matrix_of_inertia` (a property) is the 3×3 tensor **about the centre
  of mass**, in world axes, with mass = volume. A 10×20×30 box: Ixx =
  650000 = V(b²+c²)/12; moving it 100 mm leaves the matrix unchanged.
- `part.principal_properties` gives `[(axis, moment), ...]`.
- `part.radius_of_gyration(axis)` is about the given axis and applies the
  parallel-axis term: 6.455 about Z through the box, 100.21 about Z with the
  box moved 100 mm.
- `static_moments` are first moments about the world planes.
- Scale to real units: `I_real [g·mm²] = I * rho [g/mm³]`.

## Bounding boxes

- `shape.bounding_box()` defaults to `optimal=True` in 0.11.1 — it is the
  tight box. `optimal=False` bounds the control hull and over-reports:
  a loft measured 30.08 wide optimal and **42.24** non-optimal; a planar
  spline 11.69 vs 12.97. Exact on analytic shapes either way. (Raw OCC
  `Bnd_Box.Add` is the non-optimal one: [[kernel-validity#bounding-boxes-over-report-on-b-spline-faces]].)
- **Do not use `BoundBox.is_inside`.** Its body returns `not (other strictly
  inside self)`: `big.is_inside(small)` is False, and two disjoint boxes
  return True. Compare `min`/`max` directly:

```python
def box_within(inner, outer, tol=0.0):
    return all(getattr(outer.min, a) - tol <= getattr(inner.min, a) and
               getattr(inner.max, a) <= getattr(outer.max, a) + tol for a in "XYZ")
```

## Minimum distance is boundary to boundary

`a.distance_to(b)` and `a.distance_to_with_closest_points(b)` →
`(d, point_on_a, point_on_b)` wrap `BRepExtrema_DistShapeShape`; `b` may be
a point. It is fast: sphere-to-torus 8 ms, a 3-turn coil to a rod 70 ms,
exact to ~1e-6 on curved faces.

It measures between **boundaries**, not volumes:

- touching or overlapping solids → 0.0;
- a 2 mm cube entirely inside a 20 mm cube → **9.0**;
- a point inside a 10 mm cube, 5 mm from each face → **5.0**.

A clearance assert on `distance_to` alone therefore passes a part that is
buried inside another. Pair it with a containment or overlap test:

```python
d, pa, pb = rotor.distance_to_with_closest_points(housing)
assert d >= p.run_clearance, (d, pa, pb)          # pa/pb say where it is tight
assert (rotor & housing).volume < 1e-6             # and they do not overlap at all
assert not housing.solids()[0].is_inside(rotor.center())
```

`Solid.is_inside(point, tolerance=1e-6)` is the point-in-solid test.
`Solid.touch(other)` returns the contact faces/edges without interior
overlap (two stacked boxes: one face, area 100). Motion sweeps and
assembly clearance proofs are [[mechanism-verification]].

## Tolerance of the numbers

Measurements are as precise as the geometry, not as the kernel tolerance
(1e-7 by default, [[occt-topology-and-tolerance#tolerance]]): compare volumes
with a relative bound (1e-6 for analytic solids, 1e-3 when the shape went
through a B-spline, sweep or boolean), distances with an absolute bound of
~1e-5 mm. Frozen values in a validation module need the same bounds, never
`==`.

## Checks

```python
V = part.volume
assert V > 0 and len(part.solids()) == 1
assert abs(V - p.expected_volume) / p.expected_volume < 1e-3
bb = part.bounding_box()                       # optimal by default
assert bb.size.Z <= p.bed_h and bb.min.Z >= -1e-6
com = part.center()                            # CenterOf.MASS
assert abs(com.X - p.foot_center_x) <= p.foot_half_w, "tips over"
assert moving.distance_to(fixed) >= p.clearance and (moving & fixed).volume < 1e-6
```
