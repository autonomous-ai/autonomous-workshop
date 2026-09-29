---
title: Frames, planes and rotations
tags: [plane, frame, rotation, transform, build123d, sign-error, rodrigues]
aliases: [Plane.rotated, local frame, coordinate frame, rotate a plane, twist, sweep angle, inverse map]
sources:
  - skills/cad/references/build123d-modeling.md ("Rotating a plane"; before the move)
  - "toolchain: Plane.rotated() composes in world axes (reproducible on any non-global plane)"
  - "experience: a hand-derived rail frame with one flipped sign buried a face 6 mm inside its housing"
related: [build123d-selectors, loft-organic-bodies, loft-pitfalls]
updated: 2026-09-23
---

# Frames, planes and rotations

## Plane.rotated() composes in world axes

`Plane.rotated()` composes its matrix in **world axes, not the plane's own**.
On a plane whose axes are not the global ones this is the single most
expensive trap in the library, because the result is a valid solid of the
wrong shape.

For a spanwise aerofoil section — `x_dir=(-1,0,0)`, `z_dir=(0,1,0)`, i.e.
local +x rearward and the normal along +Y — `plane.rotated((0, 0, twist))`
reads like a pitch and is actually a **yaw about world Z**. Measured on a
200 mm chord: a 20° "twist" put the trailing edge at `(812.0, -68.4, 99.4)`
when it should be at `(812.1, 0.0, 168.4)`. The section slid 68 mm sideways
out of its own spanwise station and rose nothing.

Nothing downstream catches it. The loft succeeds, the solid is closed,
watertight and free of self-intersections, and `scripts/inspect refs --facts`
passes it. Only looking at a render finds it.

## Build the frame from direction vectors

```python
# incidence about the span axis, then yaw the whole frame
t, s = math.radians(twist_deg), math.radians(sweep_deg)
x_dir  = Vector(-math.cos(t) * math.cos(s), -math.cos(t) * math.sin(s), math.sin(t))
normal = Vector(-math.sin(s), math.cos(s), 0.0)
plane = Plane(origin=Vector(*origin), x_dir=x_dir, z_dir=normal)
```

The same applies to rolling a section about a swept member's own axis: use a
Rodrigues rotation about that axis rather than `Plane.rotated()`.

## Write the inverse and assert the round trip

A frame you derive by hand has two sign choices per axis and no feedback: a
wrong one still builds, still validates, and only surfaces as a clash
somewhere else. Measured on a rail placed by `Rot(0, -elev, 0)`: writing
`+z*sin` where the rotation gives `-z*sin` buried the rail's rear face 6 mm
inside the housing, and six downstream placements — a catch, a slot, two pins,
a slider — had been positioned against the bad map before `inspect interfere`
found it.

```python
def to_world(x, y): ...
def to_local(X, Y): ...
assert all(math.isclose(a, b, abs_tol=1e-9)
           for a, b in zip((3.0, 5.0), to_local(*to_world(3.0, 5.0))))
```

Two lines, and they fail at import time instead of six features later.

## A loft station frame from a lateral reference, never from Z

```python
def _station_wire(centre, tangent, half_h, half_w):
    t = Vector(*tangent).normalized()
    x = Vector(0, 1, 0).cross(t)          # lateral reference
    if x.length < 1e-6:                   # only if the spine runs along Y
        x = Vector(0, 0, 1).cross(t)
    plane = Plane(origin=Vector(*centre), x_dir=x.normalized(), z_dir=t)
    return (plane * Ellipse(half_h, half_w)).wire()
```

The obvious frame — `x_dir = Z × tangent` — degenerates the moment the spine
turns vertical, and a curled tail, a hook, a handle or an S-bend all do that.
`Z × t` goes to zero there and the loft fails or twists. A lateral reference
(`Y × t`) stays well conditioned for any spine that stays roughly in the XZ
plane, which is what a side-view-driven station table always produces.

Note what the frame does to the ellipse's arguments: with `x_dir` in the XZ
plane, `Ellipse(a, b)` takes **a = half-height, b = half-width**. Getting this
backwards produces a body that is correct in silhouette from the side and
wrong from the front, which one view will not show you.

## Rotating a body that sits off the origin

A body offset from the origin must be rotated about **its own** axis: build it
at the origin, rotate, then translate. Rotating in place about global Z flies
it across the model. Repeated features placed by a helper that only translates
its prototype must have the *prototype* rotated, not the ring.
