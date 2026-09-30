---
title: Landmark audits read topology, not probes
tags: [landmark, audit, topology, is-inside, cost, measurement, ocp]
aliases: [check_landmarks, is_inside cost, probing a solid, edge filtering, geom_type]
sources:
  - skills/cad/references/image-derived-verification.md
  - "toolchain: Shape.is_inside cost grows with face count — 0.38 ms on a 34-face solid, 2.9–15 ms on a 108-face one (reproducible)"
related: [silhouette-likeness, repeated-scene-likeness]
updated: 2026-09-23
---

# Landmark audits read topology, not probes

A landmark audit is project code, so nothing in the toolchain bounds its cost
— and "probe the solid until I find the surface" is the easiest way to make one
ledger row cost more than every deterministic gate together. An audit must
measure the returned geometry rather than restating the arithmetic that
created it; reading the solid's own topology does that best.

## One row, two ways

Counting the four ridge crests on each hose barb of a six-part assembly:

| method | cost |
|---|---|
| walk a radial probe along each barb, bisecting for the outer radius — 4 400 `Shape.is_inside` calls | **61.1 s** |
| read the crest circles off the solid's own edges — `geom_type == CIRCLE`, radius, centre on the port axis | **0.004 s** |

61.1 s was 62 % of that project's entire gate suite, on a model whose
`inspect validate` costs 2.2 s and `inspect interfere` 1.0 s. The topology
read is also the better measurement: it *identifies* each crest instead of
sampling near one, and it stays falsifiable — sabotaging the ridge count to 3
makes it report 3, removing the crest land makes it report 2.

## Why probing gets worse over time

- **`is_inside` scales with face count.** On one assembly it cost 0.38 ms on a
  34-face rotor and 2.9–15 ms on a 108-face housing. Fillets added to fix a
  thickness failure tripled the housing's faces — and quadrupled a landmark row
  that had nothing to do with them.
- **A bisection is not the fix.** Replacing a 130-step linear walk with a
  9-step bisection cut the row by 5× and left it the slowest thing in the run.
  Changing *what* is measured beat changing *how* by three more orders of
  magnitude.

## The order to reach for

1. `edges()` / `faces()` filtered by `geom_type`, radius, axis or position.
2. A `Location` or bounding-box read.
3. `is_inside` and boolean intersections last, with a call budget in mind.

Small details need their own landmark target because the global silhouette can
hide their omission; keep silhouette questions in the likeness gate and exact
distances and alignments in `inspect measure/align/frame`.
