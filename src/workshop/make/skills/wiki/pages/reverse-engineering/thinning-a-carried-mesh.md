---
title: Thinning a carried mesh
tags: [mesh, step, decimation, file-size, triangles, reverse-engineering]
aliases: [decimate mesh, reduce triangles, smaller step file, quadric decimation, mesh simplification, lighter step]
sources:
  - https://vtk.org/doc/nightly/html/classvtkQuadricDecimation.html
  - https://manifoldcad.org/docs/html/classmanifold_1_1_manifold.html
  - "toolchain: VTK 9.6 vtkQuadricDecimation (volume preserving) against manifold3d 3.x simplify on organic shells: quadric kept 15 % of triangles within 0.047 mm; simplify at 0.05 kept 14 % at 0.12 mm and lost 2-3 % of thin fins' volume"
  - "toolchain: OCCT STEP writer, planar faces sewn one per triangle: about 1.1 KB of file per face"
related: [mesh-to-step-conversion, brep-vs-source, mesh-measurement]
updated: 2026-09-28
---

# Thinning a carried mesh

A body carried from a mesh writes one planar STEP face per triangle, about
1.1 KB of file each, and an exported organic sculpt carries far more triangles
than its surface needs. A lighter file means fewer triangles, and that costs a
bounded, measured distance from the designer's surface. Read this before
thinning any body carried as in
[[mesh-to-step-conversion#carrying-a-mesh-as-the-deliverable]].

## Rule or formula

- **Thin each shell before anything is cut from it.** Host and inlay then come
  from the same thinned shells, so they still share every vertex where they
  meet. Thinning each body after its cuts moves the two sides of a shared face
  independently and opens gaps or overlaps between them.
- **Set the budget from the smallest designed clearance, not from the
  printer.** A running gap between print-in-place links is thinned from both
  sides, so it can close by up to twice the budget. An eighth of the least gap
  keeps it; measure the gaps after thinning (`min_gap` on the thinned bodies)
  rather than trusting the arithmetic.
- **Use volume-preserving quadric decimation** (VTK `vtkQuadricDecimation`
  with `VolumePreservationOn`), and measure the result both ways: every vertex
  and a spread of surface samples of each mesh against the other's surface.
  manifold3d's `simplify(tol)` is the wrong tool here: it removes vertices
  without moving the rest, so a shell shrinks: the measured distance runs to
  twice the tolerance, and thin fins lose percent of their volume.
- **Accept a reduction only if the result is still one closed manifold of the
  same genus within the budget, and try reductions from the top down.** Whether
  a reduction holds is not monotonic in it (a defect appears at one level and
  not at the next), so bisection settles on a needlessly low one.
- **Tessellate what you add to the same budget.** A revolved pocket cut into a
  thinned body at 128 facets and 20 points a millimetre put back more triangles
  than the whole thinned body had. A circumscribed polygon of `n` facets stands
  `r (1 / cos(pi / n) - 1)` outside its circle, and a chord of length `s` falls
  `s^2 / (8 R)` inside a curve of radius `R`: choose `n` and `s` so both stay
  under the budget.

## When it does not hold

- **A normal-facing test against the source mesh cannot find fold-overs in an
  organic export.** Such a mesh has its own cusps and near-zero-area slivers,
  and scores as folded against itself. Leave fold detection to the kernel's
  self-intersection check on the sewn solid, and compare its flags with the
  unthinned bodies'.
- **Volume preservation moves a flat underside.** It pushes a bed-flat face a
  few thousandths of a millimetre through its plane, so a printable body no
  longer sits at Z = 0. Clamp each thinned vertex to no lower than the
  shell's own lowest point.
- **A curved part elsewhere in the file still multiplies it.** Thinning shrinks
  every file by the same factor, but an assembly that holds one revolved or
  lofted part beside the carried bodies still writes every facet's pcurves
  ([[mesh-to-step-conversion#adding-features-to-a-carried-mesh]]).

## Checks

- Per shell: triangles before and after, the two-way distance, and the volume
  change, printed by the project's own fidelity script.
- Every designed clearance between carried bodies, measured on the thinned
  bodies against the unthinned ones.
- `inspect validate` on each plate, compared with the flags the unthinned
  bodies raised; `inspect interfere` on the assembly.
- The printable entries' minimum Z in `check_fit`.
