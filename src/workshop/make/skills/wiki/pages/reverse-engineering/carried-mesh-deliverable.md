---
title: Carrying a mesh as the deliverable
tags: [mesh, step, sewing, mesh-boolean, inlay, decimation, file-size, triangles, reverse-engineering]
aliases: [carried mesh, carry the mesh, identical to the mesh, mesh inlay, decimate mesh, reduce triangles, smaller step file, quadric decimation, mesh simplification, lighter step]
sources:
  - "toolchain: manifold3d boolean output sewn per triangle with BRepBuilderAPI_Sewing (OCP 7.9): coincident pairs at 2e-12 mm and 1e-6 mm edges each made the solid invalid until welded / sewn at 1e-7"
  - "toolchain: manifold3d 3.x, a surface-following inlay cut from a carried head: host minus (host & prism - moved host) left one edge on four triangles and an invalid sewn solid; prism minus moved host did not"
  - https://vtk.org/doc/nightly/html/classvtkQuadricDecimation.html
  - https://manifoldcad.org/docs/html/classmanifold_1_1_manifold.html
  - "toolchain: VTK 9.6 vtkQuadricDecimation (volume preserving) against manifold3d 3.x simplify on organic shells: quadric kept 15 % of triangles within 0.047 mm; simplify at 0.05 kept 14 % at 0.12 mm and lost 2-3 % of thin fins' volume"
  - "toolchain: OCCT STEP writer, planar faces sewn one per triangle: about 1.1 KB of file per face"
related: [mesh-to-step-conversion, brep-vs-source, mesh-measurement, mass-properties-and-measurement, low-poly-sculpt-from-a-field]
updated: 2026-10-10
---

# Carrying a mesh as the deliverable

Only carried triangles are identical to the mesh; every re-authored surface is
an approximation of it. When a user asks for a result guaranteed identical to
the file, that is what they get, and it is said plainly
([[mesh-to-step-conversion]]). The cost is a STEP with one planar face per
triangle, and rules for every feature added to it.

## Building each body from the mesh

Build each body from the mesh in source (split the shells, cut inlays out of
their hosts on the meshes with a mesh boolean, sew each result) and assert,
per body, a valid solid whose volume equals the mesh's. A mesh boolean's
output is closed and shares its vertices exactly, but it is not clean enough
for the kernel as it comes:

- **Weld coincident vertices first**, at about 1e-9 mm, and drop the triangles
  that then have two corners on one point. A cut leaves vertex pairs a few
  1e-12 mm apart; the needle triangle between them makes a face
  `BRepCheck_Analyzer` rejects, and the whole solid with it.
- **Keep the sewing tolerance below the shortest real edge.** A cut also leaves
  real edges near 1e-6 mm; sewn at 1e-6 they merge, and the face beside them
  comes out with a doubled edge. Where neighbours share vertices exactly, sew
  at 1e-7.
- **Do not simply drop a zero-area triangle.** Its middle vertex lies on the
  neighbour's long edge, so dropping it leaves a T-junction and an invalid
  solid. Welding handles the needle case. Do not flip edges on an area
  threshold either: a micro-triangle (all edges ~1e-5 mm) is tiny, not flat,
  and a flip loop keyed on area cycles on it.

Sewing costs about 0.4 ms a triangle on such output (13 s for 34k triangles,
3.5 min for 127k), so cache the sewn solids keyed on the mesh and the code.
The STEP then carries one face per triangle, about 1.1 KB of file each:
70k-face bodies write files of 240 MB and more, and an assembly `interfere`
over them takes ten minutes. To make the file lighter, thin each shell before
it is cut ([[#thinning-under-a-measured-distance-budget]]).

## Adding features to a carried mesh

A feature added to a carried body (a colour inlay, a pocket for a glued part)
is cut on the meshes before sewing, like the designer's own inlays, so every
body stays carried triangles and neighbours still share their vertices.

- **An inlay that follows the surface is a layer of moved copies.** Let
  `behind(t)` be the body moved `t` back along the view direction: a point is
  inside it exactly when stepping `t` forward lands inside the body. The layer
  from depth `r` to `r + d` inside an outline is
  `prism & (behind(r) - behind(r + d))`, and the host loses
  `prism - behind(r + d)`. Stop the prism's column short of every internal
  cavity along the view direction: the same formula lines each cavity's back
  wall with a second skin.
- **Never subtract a solid whose face is the host's own surface.**
  `host ^ prism - behind(t)` has the host's surface as its front face;
  subtracting it from the host leaves a zero-thickness fin where the two
  coincide. After welding, one edge is shared by four triangles; sewing then
  reports no free edges and no multiple edges, and only `BRepCheck` on the
  solid fails. Subtract `prism - behind(t)`, which reaches out past the
  surface and shares no face with it.
- **Check that every edge is shared by exactly two triangles before sewing.**
  It is milliseconds against minutes of sewing, and it names the place.
- **Clear a pocket against the buried inlays, not the visible ones.** A
  designer often sinks an inlay as a bulb well under the surface around it,
  so a crown that looks solid can hold only a few millimetres of host over an
  inlay. Measure the boundary-to-boundary distance from the pocket to every
  other body (`distance_to`,
  [[mass-properties-and-measurement#minimum-distance-is-boundary-to-boundary]]),
  and tilt a pocket's axis towards the local surface normal: its rim then
  sits level, and the key needs less depth.
- **To replace a designer's inlay, start from the host's raw shell.** The host
  as carried has the old inlay's slot cut in it; its own shell is whole
  underneath (the slicer unions the two), so take the new inlay out of that
  shell, and the old slot is simply gone.
- **An inlay can be what holds its host up in print.** An inlay sunk behind a
  flared part can be the support under it; replace it wholesale and the flare
  prints over air. Keep the old inlay where the host hides it from the viewing
  side (the host's outline seen along that axis — manifold3d `project()`,
  offset in by a ledge's width, extruded — intersected with the old inlay) and
  add the new shape outside that.
- **Drop zero-volume films after each boolean** (pieces under ~1e-3 mm3): a
  cut through a shared plane leaves degenerate four-triangle pieces.
- **One curved part makes every facet write its pcurves.** The STEP writer
  leaves out the 2D edge curves only when every face in the file is planar. A
  single revolved part beside carried bodies turns them on for all the
  triangles, and the file grows about 2.4 times (a faceted sphere: 4.8 MB
  alone, 11.6 MB with one cylinder beside it). Expect the combined assembly
  to be that much larger than the plates it is made of. When the combined
  file has to be small, give the view-only assembly entry the curved part
  faceted: mesh it within the carried bodies' tolerance, sew the triangles
  into a solid, and assert that tolerance sits inside the fit clearance round
  it, so the view clashes where the print does. The file then drops back to
  the sum of its plates. The printed part keeps its analytic surface.

## Thinning under a measured distance budget

An exported organic sculpt carries far more triangles than its surface needs.
Fewer triangles cost a bounded, measured distance from the designer's surface.

- **Thin each shell before anything is cut from it.** Host and inlay then come
  from the same thinned shells, so they still share every vertex where they
  meet. Thinning each body after its cuts moves the two sides of a shared face
  independently and opens gaps or overlaps between them.
- **Set the budget from the smallest designed clearance, not from the
  printer.** A running gap between print-in-place links is thinned from both
  sides, so it can close by up to twice the budget. An eighth of the least gap
  keeps it; measure the gaps on the thinned bodies (`distance_to`,
  [[mass-properties-and-measurement#minimum-distance-is-boundary-to-boundary]])
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

## When thinning does not hold

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
  ([[#adding-features-to-a-carried-mesh]]).

## Checks

- Per body: a valid sewn solid whose volume equals its mesh's.
- Per thinned shell: triangles before and after, the two-way distance, and
  the volume change, printed by the project's own fidelity script.
- Every designed clearance between carried bodies, measured on the thinned
  bodies against the unthinned ones.
- `inspect validate` on each plate, compared with the flags the unthinned
  bodies raised; `inspect interfere` on the assembly.
- The printable entries' minimum Z in `check_fit`.
