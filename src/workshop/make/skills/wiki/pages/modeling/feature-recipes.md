---
title: Additive and subtractive feature recipes
tags: [feature, boss, rib, hole, shell, slot, text, groove, decoration, crescent, lune, leaf]
aliases: [feature table, standoff, counterbore, countersink, hollow, engraving, inlay, stripe, two-circle profile, petal, feather, fan tail, crease, midrib]
sources:
  - skills/image-to-cad/references/build123d-operations.md (feature tables, conformal decoration, crescent solve; before the move)
  - "experience: a crescent read off pixels pinched to two thirds of its width and failed a proportion ledger"
related: [operation-families, construction-strategy, boolean-pitfalls, build123d-selectors, text-patterns-and-surface-detail, ribs-and-stiffening]
updated: 2026-09-28
---

# Additive and subtractive feature recipes

## Additive features

| Feature | Call | Frame | Risk |
|---|---|---|---|
| Boss / standoff / post | `with Locations(pts): Cylinder(r, h)` | inside floor | Must **overlap** the floor, not touch it — a tangent boss reads as a disconnected body |
| Rib / gusset | `extrude(profile, amount=t)` then `+` | plane of the rib | Root it into **both** faces it stiffens |
| Flange / foot | `extrude(Rectangle(w, d), amount=t)` | base face | — |
| Handle following a curve | `sweep(is_frenet=True)` | own path plane | Both ends must intersect the body |
| Repeated bosses | `with GridLocations(dx, dy, nx, ny): ...` | the face they sit on | One row in the table, not four |
| Repeated around an axis | `with PolarLocations(r, n): ...` | the face | Rotate the prototype, not the ring |
| Painted stripe / inlay / lens | `(inflated_body - raw_body) & tool` | — | See below |

Sizing ribs and gussets: [[ribs-and-stiffening]].

## A leaf, a petal, a feather

A pointed leaf whose half-width is concave along its length, w(s) ∝ s^p (1 − s)
(widest at p / (p + 1), pointed at the tip at a finite angle), with superellipse
sections whose half-thickness is a fixed share of w, is a convex solid: a norm
bounded by a concave function. Build it as the convex hull of its sampled
sections plus a ball at the tip, which blunts the point for the sharp-point
rule ([[toy-safety-constraints#sharp-points-and-edges]]). A hull is closed,
2-manifold and never self-intersecting however coarsely it is sampled, which a
loft or a Minkowski-rounded slab is not. A leaf that lies on the bed is the
same solid cut at its mid plane, its tip ball lifted so the tip stays thick.

Put grooves and ridges on it as chains of capsules (the hull of consecutive
balls) whose centres sit a set offset from the leaf's own surface below each
point: cut, a groove keeps its depth over the dome; added, a ridge keeps its
height. A crease down the middle, a midrib, a feather's slanted barbs are all
this. Ease a groove's depth to zero at both ends, and cut each leaf's crease
before leaves are united: a cutter that follows one leaf's surface can sit
wholly inside a thicker neighbour and leave a closed void.

## Conformal surface decoration

A stripe, a badge, or a lens that follows a sculpted skin is a *skin patch*,
not a prism. Build the base form twice from the same helper — once at nominal,
once inflated by the relief height — subtract to get a shell, then intersect
that shell with a simple tool box or sphere. Do **not** `offset()` a
spline-bounded solid; the kernel returns Null for some inward deltas.

Two measured details:

- compute the shell **once** and intersect it with each tool — the
  alternative, `(inflated & tool) - raw` per tool, was 2.2× slower on a
  200-face body;
- centre a lens tool **on** the surface — anchor it by solving the section for
  the surface point rather than placing it by eye, because a tool that misses
  the skin intersects to `None` and the failure surfaces far downstream as
  `NoneType has no attribute label`.

Text, patterns and texture — fonts, wrapping, one boolean for a whole pattern,
face-count cost: [[text-patterns-and-surface-detail]].

## Subtractive features

| Feature | Call | Frame | Risk |
|---|---|---|---|
| Through hole | `Hole(radius)` | the face it enters | `Hole` goes through all — use `CounterBoreHole`/`depth=` for blind |
| Counterbored screw hole | `CounterBoreHole(r, cb_r, cb_depth)` | the face the head sits in | — |
| Countersunk hole | `CounterSinkHole(r, csk_r)` | same | — |
| Hollow interior | `offset(body, -p.wall, openings=body.faces().sort_by(Axis.Z)[-1])` | the face(s) removed | Shell **before** adding interior bosses, or it hollows them too |
| Recess / cavity with draft | `body -= loft([rim, mid, floor])` | wires on offset planes | Tool must break the rim plane by ≥1 mm |
| Wheel arch / side scallop | `body -= Cylinder(...) & half_space` | — | A full-width cylinder **severs** the body into pieces; clip the tool to the outboard side |
| Slot | `SlotOverall(w, h)` in a sketch, then cut | its own plane | — |
| Engraved text / logo | `Text(s, size)` in a sketch, `extrude(amount=-depth)` | the face | Below ~1.5 mm wide it will not print — deepen or drop |
| Decorative groove (ex-parting-line) | a revolved or extruded cutter | — | 0.4–0.8 mm deep is enough to read |

Batch the tools in one list operation and keep each batch internally disjoint
([[boolean-pitfalls#multi-tool-booleans]]).

## Crescents, lunes and two-circle profiles

`Circle(R) - Pos(d, 0) * Circle(r)` is the whole construction, and the trap is
in where `r` and `d` come from. **Do not read them off the pixels.** The cut
circle's edge is an *inferred* boundary — in a render it is a lit inner arc,
not a silhouette, and a few pixels of error in a radius you cannot see directly
propagates into the tip positions, which is the one thing the eye checks.

Measure the two things the image shows honestly instead, then solve:

- **ψ** — the half-angle from the crescent's centre to its two tips. Read the
  tip coordinates; they are corner features and localise to a pixel.
- **t** — the rim thickness at its widest, opposite the gap. A clean
  edge-to-edge span.

Then, with the outer radius `R` also observed:

```text
r = R + d - t                       # thickness definition
cos ψ = (R² + d² - r²) / (2 R d)    # circle-intersection condition
```

Two equations, two unknowns — substitute and solve the linear result for `d`.

Worked, from a crescent on a 1024 px render: R 25.56, tips subtending 88.8°,
rim 9.05 mm thick → d 5.47, r 21.98. Reading `r` and `d` straight off the
pixels instead gave r 26.62, d 10.11, which **pinched the crescent to two
thirds of its width** and failed a ±10 % proportion-ledger assertion at
−33.5 %. The shape still looked like a crescent from every angle; only the
ledger caught it.

The same substitution applies to any lune, C-clip, split ring, or hook profile
built from two circles: solve from the features you can localise, never from
the radius you cannot.
