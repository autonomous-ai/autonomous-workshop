---
title: Sweeps and helices
tags: [sweep, helix, coil, spring, path, frenet, transition, pipe]
aliases: [pipe shell, BRepOffsetAPI_MakePipeShell, swept profile, is_frenet, binormal, auxiliary spine, Transition.RIGHT, Transition.ROUND, multisection sweep, swept spring, coil spring model, tube along path]
sources:
  - .venv/lib/python3*/site-packages/build123d/operations_generic.py (sweep)
  - .venv/lib/python3*/site-packages/build123d/topology/three_d.py (Solid.sweep, Solid.sweep_multi, _set_sweep_mode)
  - .venv/lib/python3*/site-packages/build123d/topology/one_d.py (Edge.make_helix)
  - https://occt3d.com/dev/doc/refman/html/class_b_rep_offset_a_p_i___make_pipe_shell.html
  - "toolchain: build123d 0.11.1 on OCP, every number below measured with small shapes"
related: [build123d-operations-and-export, operation-families, frames-and-rotations, kernel-validity, printed-threads, element-libraries, springs, boolean-pitfalls]
updated: 2026-09-23
---

# Sweeps and helices

`sweep()` is `BRepOffsetAPI_MakePipeShell`. Almost every way to get it wrong
returns a solid with `is_valid == True` — a zero-volume sweep, a half-swept
corner, a coil whose turns overlap. The only reliable check is the volume
identity in [[#pappus-is-the-sweep-assert]]. Choosing a sweep over a loft or
an extrusion: [[operation-families#sweep]].

## The profile is swept where it is, not moved to the path

build123d calls `Add(wire, WithContact=False, WithCorrection=False)` (except
in `normal=` mode). OCCT therefore neither translates the section onto the
spine nor turns it normal to the tangent. A profile you drew at the origin is
swept at the origin, offset from the path.

Measured on `Helix(4, 12, 10)`, circle r = 1 (expected volume 593.38):

| profile placement | `is_valid` | volume |
|---|---|---|
| `Circle(1)` on XY at the origin | True | 37.70 |
| `Plane.XZ * Circle(1)` at the origin | True | **0.00** |
| `Plane.XZ * Pos(10, 0) * Circle(1)` (at the start, not normal to tangent) | True | 592.18 |
| `Plane(origin=path.position_at(0), z_dir=path.tangent_at(0)) * Circle(1)` | True | 593.38 |

A profile at the start but tilted off the tangent shrinks the volume by the
cosine of the tilt (3.64° here: 593.38·cos → 592.18). Always build the section
plane from the path:

```python
path = Helix(pitch=p.pitch, height=p.coil_h, radius=p.coil_r)
start = Plane(origin=path.position_at(0), z_dir=path.tangent_at(0))
coil = sweep(start * Circle(p.wire_d / 2), path=path, is_frenet=True)
```

In a builder, a `BuildLine` exposes its path as `l.wire()` (`l.line` is a
`Curve` and has no `position_at`); open the `BuildSketch` on the plane built
from it, then call `sweep()` with no arguments.

## Frame modes: is_frenet, binormal, normal

| argument | OCCT mode | the section… | use |
|---|---|---|---|
| `is_frenet=False` (default) | corrected Frenet (minimum twist) | creeps round a helix | planar or gently curved paths |
| `is_frenet=True` | Frenet | stays locked to the helix axis | helices, coils, threads |
| `binormal=<Edge/Wire>` | auxiliary spine, curvilinear equivalence | points at the matching point on the guide | helix with a non-round section, twisted rails |
| `normal=<vector>` | **fixed `gp_Ax2`** (sections stay parallel) | does not rotate at all | straight-ish paths only |

Measured with a 2 × 1 rectangle swept round `Helix(4, 40, 10)` (10 turns):
with `is_frenet=False` the end face is rotated ~24° after the first turn; with
`is_frenet=True` or `binormal=Helix(4, 40, 5)` (a coaxial helix of the same
pitch) the end face is still axial (Z extent 0.998 for a 1.0 edge). All three
volumes equal area × length.

`normal=(0, 0, 1)` on the same helix returned a valid solid of volume
**80.0** (expected 1259.2): the name suggests a binormal, but build123d maps a
vector to OCCT's fixed-trihedron mode, which keeps every section parallel to
the first. Do not pass `normal=` for a curved path.

Frenet is undefined where curvature is zero; on a path with straight segments
or inflections it flips the section. Use Frenet for helices and
`is_frenet=False` or a `binormal` guide elsewhere.

## Corners: the default transition silently drops material

`transition` only matters where the path is C0 (a polyline corner). The
default is `Transition.TRANSFORMED`, and on a 90° corner it is wrong:

| path `Polyline((0,0,0),(20,0,0),(20,20,0))` | 4 × 4 square | r = 2 circle |
|---|---|---|
| `TRANSFORMED` (default) | **valid=False**, vol 320 (expected ~640) | valid, vol **251.3** — only the first leg |
| `Transition.RIGHT` (mitred) | valid, vol 640.0 | — |
| `Transition.ROUND` | valid, vol 636.6 | valid, vol 500.4 |

A 20° corner with `TRANSFORMED` stayed valid but still lost ~3 % of the
expected volume. Rules:

- Any path with a corner: pass `transition=Transition.RIGHT` (mitre) or
  `Transition.ROUND`, or better, fillet the path —
  `FilletPolyline(*pts, radius=r)` gives a C1 path whose sweep is exact
  (4 × 4 square, r 5: vol 605.66 = 16 × path length).
- `multisection=True` ignores `transition` entirely (it is not passed to
  `Solid.sweep_multi`), so a multisection path must be C1.

## Pappus is the sweep assert

When the section's centroid lies on the path and the section stays normal to
it, **volume = section area × path length** (Pappus–Guldinus). It held to
1e-7 relative on a helix coil, exactly on a filleted polyline, a closed ring
and a hollow tube (a face with an inner wire — `Solid.sweep` sweeps each wire
and cuts, so holes in the section work). Every failure above breaks it. Put
it in the generator:

```python
expected = section.area * path.length
assert abs(solid.volume - expected) / expected < 1e-3, (solid.volume, expected)
```

It does **not** catch self-intersection, because an overlapping sweep double
counts to exactly the same number (below).

## Self-intersection passes is_valid

- A coil with pitch 1.5 and wire Ø2 (turns overlap): `is_valid` True, volume
  = area × length exactly, `BRepAlgoAPI_Check` False — after **28 s** on a
  3-turn coil (22 s for the clean version). Too slow for a generator.
- A 180° arc of radius 0.5 swept with a r = 1 circle: `is_valid` True,
  `BRepAlgoAPI_Check` False.

Guard it algebraically instead, before building:

```python
assert p.pitch >= p.wire_d + p.coil_gap_min, "adjacent turns overlap"
assert p.bend_r_min > p.section_r_max, "section folds over itself on the inside of the bend"
```

(`bend_r_min` is the path's smallest radius of curvature; the section's
largest distance from the path point must stay inside it.)

## Helix construction

`Helix(pitch, height, radius, center=(0,0,0), direction=(0,0,1),
cone_angle=0, lefthand=False)` is an edge object; it works in `BuildLine` and
in algebra mode. It wraps a 2D line onto a cylindrical (or conical, with
`cone_angle`) surface, so it is one exact edge — not a spline approximation:
`Helix(4, 12, 10).length` = 188.877144843, analytic
3·√((2π·10)² + 4²) = 188.877144843. It starts at `(radius, 0, 0)` and ends
at `(radius, 0, height)` when height is a whole number of pitches.
`Edge.make_helix` has the same signature (`normal`, `angle`) and returns an
`Edge`.

## Swept springs and coils

A swept circle on `Helix` with `is_frenet=True` is the modelled spring: a
3-turn coil sweeps in ~0.05 s. Size the spring itself from
[[springs#helical-compression-spring]]; the geometry rules are the pitch
guard above and closed/ground ends if it must stand: sweep only the active
turns and add the end turns as separate zero-pitch rings (a `Torus` or a
swept closed circle), overlapping the coil so the fuse is one solid.

## Threads come from the element library

A triangle swept on a helix and fused to a core is valid (0.7 s for a
5-turn M10-like ridge), but it is not a thread: no standard profile, no
crest/root truncation, no fade-out at the ends, no mating clearance. Take
threads from `skills/cad/scripts/stdpart` (`IsoThread`, `TrapezoidalThread`,
`PlasticBottleThread` from `bd_warehouse`, see [[element-libraries]]), and
the printed profile, clearance and orientation from [[printed-threads]].

## Multi-section sweep

`sweep([s0, s1, ...], path=..., multisection=True)` blends between sections
placed along the path (each on a plane built from `position_at` /
`tangent_at` at its station). Circle → square on a spline: valid, one solid,
7 faces. Sections must be ordered along the path and the path must be C1
(transition is ignored). For more than two very different sections a
[[loft-pitfalls]]-style loft is usually easier to control.

## Checks

```python
path = Helix(p.pitch, p.coil_h, p.coil_r)
start = Plane(origin=path.position_at(0), z_dir=path.tangent_at(0))
section = start * Circle(p.wire_d / 2)
coil = sweep(section, path=path, is_frenet=True)
assert p.pitch >= p.wire_d + p.coil_gap_min
assert p.coil_r > p.wire_d / 2
assert abs(start.z_dir.dot(path.tangent_at(0)) - 1) < 1e-9     # section normal to path
assert len(coil.solids()) == 1 and coil.is_valid
assert abs(coil.volume - section.area * path.length) < 1e-3 * coil.volume
```
