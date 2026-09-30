---
title: Measuring a mesh or tessellated reference
tags: [measurement, mesh, stl, section, circle-fit, iou, reverse-engineering, reference]
aliases: [measure stl, section polygon, slice mesh, circle fit bore, rotation overlap scan, mesh instruments]
sources:
  - skills/step-to-source/references/measuring.md
  - shapely polygonize and even-odd fill semantics (shapely documentation)
  - "experience: mesh instruments that returned wrong readings on real parts, and the fix for each"
related: [brep-vs-source, authoring-from-a-reference, kit-assembly-poses]
updated: 2026-09-23
---

# Measuring a mesh or tessellated reference

How to read trustworthy numbers off triangles (an STL, or a tessellated
STEP), and the instruments that lie when done naively. The procedure and tool
list stay in `skills/step-to-source/references/measuring.md`.

## Which source to trust for which number

| number | best source | why |
|---|---|---|
| exact radius, axis, chamfer angle of an analytic face | the STEP, read from the kernel's own surface parameters | a parameter, not a fit |
| anything on a faceted solid: outline, level, bore, mating datum | the **STL**, if it still exists | a converter's repair can move faces: one repairing backend left a converted frame 0.3 mm proud on every face, and a datum read off it produced a 7.7 mm³ clash |
| the same, when only a STEP exists | the tessellated STEP | same instruments, on its triangles |

Measuring on triangles needs only numpy and shapely. It never touches the CAD
kernel, so it can run while a CAD job holds the daemon.

## Principles that make mesh readings exact

- **Facet vertices lie on the true circle.** A least-squares fit to a section
  loop's vertices therefore recovers the radius, not the chord.
- **Flat levels come from area, not from points.** Group the facets whose
  normal is ±Z by height and sum their area. An upward level with hundreds of
  mm² at one height is a ledge.
- **Look first, then take numbers.** Read a sheet of 12–16 filled sections (in
  z, then x and y) before reading vertex lists.
- **The designer's values show through.** Walls come out at 2.0, a rim at
  45°, a slot at 3.8: round numbers are the design. When a reading lands
  between round numbers (−4.49 against 4.40), keep the reading and say so.
  Never round a measured asymmetry away.
- **Angles come from a scan.** Rotate one section against another in small
  steps. The answer is the angle of zero or minimal overlap area, which gives
  D-flat direction and gear tooth phase.

## Instruments that lied

Each of these produced a wrong reading on a real part:

- **Section endpoints that do not meet.** Interpolate each crossing edge from
  its lexicographically smaller vertex, so the two triangles sharing an edge
  produce the same point bit for bit. Otherwise endpoints miss by 1e-15,
  polygonize drops loops, and whole slices come back empty.
- **Even-odd fill by face.** Fill as the XOR of each polygonized face's
  *exterior*. `polygonize` returns a ring face with a hole *and* the hole's own
  face, and a ring can have less area than its hole. XOR-ing faces sorted by
  area filled every open box solid.
- **A cut plane through vertices.** When the plane passes exactly through mesh
  vertices the fill comes back wrong: a whole gear section read as solid.
  Jitter the plane (`h + 1.2e-5`) rather than cutting at the round height the
  facets were modelled on, and use the raw segments for anything precise.
- **Angles from point statistics.** A D-flat estimated as "mean angle of the
  points inside r − 0.4" read 67° where the flat was at 90° (about 20° off).
  Scan the angle instead.
- **Section chaining on exact end points, after a rotation.** Interpolating
  each crossing from the lexicographically smaller vertex makes the two facets
  sharing an edge agree bit for bit *while the mesh sits where it was written*.
  Transform it - to try a pose, to seat one part on another - and the two
  copies of one vertex come out of the arithmetic differing in the last bits.
  The walk never closes, the ring is dropped, and the section comes back
  **empty**. Nothing raises: an overlap measured that way reads as zero, and a
  pose search happily reports the clashing pose as clear. Snap end points
  within about 1e-7 mm before chaining, and sanity-check a transformed mesh by
  integrating its sections back to its volume the way an untransformed one is
  checked.
- **Penetration depth from winding numbers.** Point sampling with a KD-tree
  distance to vertices reported 6.9 mm and 1.9 mm for contacts that measured
  0.09 mm² and 0.03 mm² in section. Use it only to flag pairs, and confirm
  every flag with a section overlap area. A pairwise scan of a 15-part kit took
  4.4 min.

## Comparing source against the reference

While the reference still exists, tessellate the built solid and cut both at
the same planes: 5 per axis at 8–92 % of the extent, plus every level that
matters. Report each cut:

```text
z=3.68  mesh 99.065  src 99.033  IoU 0.9997  symdiff 0.033 at (1.29, 4.15)
```

The centroid of the symmetric difference says where to look. A diff sheet
(red: reference only, green: source only) says what is wrong. Against an exact
STEP, the solid symmetric difference answers directly
([[brep-vs-source#why-the-comparison-is-a-symmetric-difference]]). Against a
faceted solid that self-intersects, per-cut IoU is the reliable number.

## What agreement to expect against a mesh

Acceptance measured on a first set of re-authored parts:

| part kind | volume vs mesh | section IoU |
|---|---|---|
| straight-edged (a cable cap) | −0.03 % | ≥ 0.998 |
| turned, 70–90-gon mesh (a cover, a pin) | +0.3 to +0.6 % | ≥ 0.94 at cuts through the chamfer or edge, ≥ 0.995 elsewhere |

A turned part that comes out slightly **over** its mesh is the expected sign,
because the mesh's chords cut inside the true circle. Coming out under means a
feature is missing. Organic bodies get their own, looser numbers. Record the
numbers actually reached, not aspirational ones.
