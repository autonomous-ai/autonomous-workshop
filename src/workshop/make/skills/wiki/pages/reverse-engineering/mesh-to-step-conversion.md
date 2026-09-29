---
title: Converting a mesh to STEP
tags: [stl, mesh, step, conversion, sewing, backend, units, reverse-engineering]
aliases: [stl to step, mesh to brep, sew triangles, 2step, stltostp, unit detection, analytic surface restoration]
sources:
  - skills/stl-to-step/references/backends.md
  - skills/stl-to-step/references/deciding-without-asking.md
  - https://github.com/yaneony/2STEP-Converter
  - https://github.com/slugdev/stltostp
  - "toolchain: sew on a 109k-facet organic mesh ran 2h36m-2h53m with no file; 2step converted it in 39 s"
  - "toolchain: manifold3d boolean output sewn per triangle with BRepBuilderAPI_Sewing (OCP 7.9): coincident pairs at 2e-12 mm and 1e-6 mm edges each made the solid invalid until welded / sewn at 1e-7"
  - "toolchain: manifold3d 3.x, a surface-following inlay cut from a carried head: host minus (host & prism - moved host) left one edge on four triangles and an invalid sewn solid; prism minus moved host did not"
related: [brep-vs-source, mesh-measurement, authoring-from-a-reference, thinning-a-carried-mesh]
updated: 2026-09-28
---

# Converting a mesh to STEP

An STL carries no analytic geometry: every curve was replaced by facets before
the file was written. So no conversion restores a radius, and none recovers
design intent. A converted STEP is a reference to measure and re-author, not a
deliverable, with one exception: a user who asks for a result guaranteed
identical to the file gets the file's own triangles (see
[[#carrying-a-mesh-as-the-deliverable]]); say so plainly rather than promise a
re-authoring will be exact. Backend install, flags and cache policy stay in
`skills/stl-to-step/references/backends.md`.

## What each kind of converter can and cannot do

| converter kind | does | does not |
|---|---|---|
| **repair + restore** (2STEP-Converter, on OpenCASCADE) | repairs and orients the mesh, sews shells, closes small planar gaps, promotes shells to solids, merges coplanar faces, then **reconstructs complete spheres, cylinders, cones and verified straight through-holes as analytic surfaces**, and re-validates its own output | hand back the vertices it was given: repair, the coplanar merge and a restored cylinder (which stands outside the polygon that approximated it) all move them |
| **facet merge** (stltostp, C++; the built-in `sew`) | each triangle becomes a face, faces sew into shells, closed shells become solids, edge-connected coplanar faces merge | repair a mesh, or restore any analytic surface |

- **An analytic bore is worth more than anything downstream can recover.** A
  bore restored as a real cylinder has a radius and an axis a probe reads
  exactly. A faceted bore has neither, and no later stage can recover them.
- **Restoration needs a complete primitive to find.** On a 223k-triangle
  organic body the repairing converter merged to 49k planar faces, repaired a
  mesh the facet-merge converters could not have taken at all, and restored
  **nothing** (`analytic surfaces none`). That is expected on anything
  freeform, not a failure. Restoration happens only where the mesh holds whole
  spheres, cylinders, cones or straight through-holes. On an organic body, the
  reason to use the repairing converter is the repair and the merge.
- **stltostp's raw output is not directly readable.** It writes the shape
  representation with **no product structure** (no `PRODUCT`, no
  `SHAPE_DEFINITION_REPRESENTATION`). The file is textually complete, and
  OpenCASCADE reads it as empty: zero roots to transfer, and transferring the
  representation entity directly fails too. A minimal AP214 wrapper fixes it
  without touching a coordinate. It also writes an **`OPEN_SHELL`** inside a
  surface model rather than a solid, so nothing has an inside until the faces
  are sewn and promoted.
- **A mesh with holes or non-manifold edges** converts, on a non-repairing
  backend, to a shell with no inside. It cannot be cut, mounted against,
  measured for volume or printed. Either repair it or get a closed export.
  Holes in a slicer or scanner export mean a bad export, not a hard problem.
  One special case: a mesh reported "not closed" only because of non-manifold
  edges (0 boundary edges) converts to closed solids even on a non-repairing
  backend.

## Sewing cost is not linear in facet count

Raw `BRepBuilderAPI_Sewing` scales tolerably on clean meshes (2k/8k/32k facets
at 0.16/0.96/5.35 s; 16k at 2.4 s, 64k at 14.5 s). The whole pipeline does not:

- a defective 109k-triangle organic mesh ran for 2 h 36 min, still in
  `BRepBuilderAPI_Sewing::FindCandidates`. In another run it burned 2 h 53 min
  of CPU, exited 0 and wrote no file. The repairing converter, which fits
  surfaces before sewing, converted the same body in 39 s;
- the cost is driven by **free edges that find no partner**, and by
  `ShapeUpgrade_UnifySameDomain` merging a **large coplanar region** (for
  example a 107 × 220 mm flat base pad) into single faces with enormous boundary
  loops. A defective 109k mesh can outlast a clean 300k one.

Through the whole built-in pipeline the cost per facet climbs with the count,
so a subset never predicts the whole mesh: on one 109k-triangle body, 0.09 s
per 1k triangles at 2k, 0.15 at 16k, 0.23 at 64k, each doubling costing
2.2–2.6× the one before; at 80k it had not finished in 11 minutes. There is
no safe facet threshold to quote.

The predictor is defects and coplanar area, not facet count. For a mesh above
~50k facets with large flat regions, go straight to the repairing converter,
or reduce the mesh first. Sewing is one C++ call that never returns to the
interpreter while it works, so a Python signal handler cannot interrupt it.
Only a child process that can be killed makes a timeout real.

A scan or organic shape converts to a solid with tens of thousands of faces
that every later gate crawls through. Convert a reduced copy for measurement,
then re-author the part.

## Carrying a mesh as the deliverable

Only carried triangles are identical to the mesh; every re-authored surface is
an approximation of it. When that is what the user chose, build each body from
the mesh in source (split the shells, cut inlays out of their hosts on the
meshes with a mesh boolean, sew each result) and assert, per body, a valid
solid whose volume equals the mesh's. A mesh boolean's output is closed and
shares its vertices exactly, but it is not clean enough for the kernel as it
comes:

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
The STEP then carries one face per triangle: 70k-face bodies write
files of 240 MB and more, and an assembly `interfere` over them takes ten
minutes.

To make that file lighter, thin each shell before it is cut, under a measured
distance budget: [[thinning-a-carried-mesh]].

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
  cavity along the view direction (nostrils, a socket): the same formula
  lines each cavity's back wall with a second skin.
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
  designer sinks an inlay (an eye white, a gill) as a bulb well under the
  surface around it, so a crown that looks solid can hold a few millimetres
  of host over an inlay. Measure `min_gap` from the pocket to every other
  body, and tilt a pocket's axis towards the local surface normal: its rim
  then sits level, and the key needs less depth.
- **To replace a designer's inlay, start from the host's raw shell.** The host
  as carried has the old inlay's slot cut in it; its own shell is whole
  underneath (the slicer unions the two), so take the new inlay out of that
  shell, and the old slot is simply gone.
- **An inlay can be what holds its host up in print.** A frill sunk behind a
  head that prints back-down carries the head's flared back and the stalks
  above it; replace it wholesale and they print over air. Keep the old inlay
  where the host hides it from the viewing side (the host's outline seen along
  that axis — manifold3d `project()`, offset in by a ledge's width, extruded —
  intersected with the old inlay) and add the new shape outside that.
- **Drop zero-volume films after each boolean** (pieces under ~1e-3 mm3): a
  cut through a shared plane leaves degenerate four-triangle pieces.
- **One curved part makes every facet write its pcurves.** The STEP writer
  leaves out the 2D edge curves only when every face in the file is planar. A
  single revolved part beside carried bodies turns them on for all the
  triangles, and the file grows about 2.4 times (a faceted sphere: 4.8 MB
  alone, 11.6 MB with one cylinder beside it). Expect the combined assembly
  to be that much larger than the plates it is made of. When the combined
  file has to be small (a Factory upload carries it twice, as itself and as
  the primary model), give the view-only assembly entry the curved part
  faceted: mesh it within the carried bodies' tolerance, sew the triangles
  into a solid, and assert that tolerance sits inside the fit clearance round
  it, so the view clashes where the print does. The file then drops back to
  the sum of its plates. The printed part keeps its analytic surface.

## What no conversion gives back

- **Curves.** A Ø8 bore in an STL is a polygon of chords, so it measures a
  fraction under 8 mm. The error is in the mesh, not the conversion, and no
  converter restores the radius or the design intent.
- **A solid from an open mesh.** A mesh with holes sews into a shell with no
  inside. No tolerance fixes it: repair the mesh or get a better export.
- **A usable solid from a crossing mesh.** Crossing surfaces convert without
  complaint and fail every boolean afterwards (below).
- **Units.** A scale factor sizes the solid and the volume it is checked
  against alike, so nothing in the file can confirm it
  ([[mesh-to-step-conversion#units-read-from-the-size-the-file-claims-to-be]]).
- **Assembly.** Converting a set of meshes says nothing about whether the
  parts are placed ([[kit-assembly-poses]]).
- **Faces exactly on the mesh.** A repairing converter can leave faces proud of
  the mesh, so keep the STL for measuring datums
  ([[mesh-measurement#which-source-to-trust-for-which-number]]).

## Why the conversion check is volume

Accept a converter's output only if a solid exists, `BRepCheck_Analyzer` calls
it valid, the bounding box agrees, and the solid's volume matches the volume
computed directly from the triangles.

Volume is the right measure here, unlike in source recovery
([[brep-vs-source#why-the-comparison-is-a-symmetric-difference]]). The two
shapes are meant to bound the same material, so any loss or gain is a defect.
The mesh volume needs no solid to compute, which makes it an independent
reference rather than a restatement of what the converter believed. A backend
that restores a cylinder where facets were differs by the facet error. That is
why the tolerance is a percentage, not zero, and why the number is always
printed. The check belongs inside the conversion chain: a converter that
returns 0 and writes an unusable file has failed, and a return code cannot see
that.

**`BRepCheck_Analyzer` does not look for self-intersection.** The kernel's BOP
check does, so a solid whose faces cut through each other passes the first and
fails the second (and the repository's `validate`). No conversion repairs it.
A mesh whose surfaces cross converts cleanly into a solid whose faces cross,
and the defect belongs to whatever wrote the mesh. Catch it from the mesh's
crossing count before choosing a backend.

## Units, read from the size the file claims to be

An STL carries no units. The only evidence is that real parts are not 0.2 mm
across and not 40 m across. Read the largest bounding-box dimension as mm, in,
cm, m, ft, in that order, and take the first reading that lands in
**10 mm – 5000 mm**.

- mm wins whenever it is plausible, because that is what the rest of the
  toolchain means by a number.
- A reading under **1 mm** is not a part in any workshop, so rescaling is the
  only interpretation left, and the decision is `measured`.
- Between 1 mm and 10 mm both readings are possible: a 4 mm part and a
  101.6 mm inch export look identical. Keep the millimetre reading, because a
  wrong rescale mangles the geometry while a kept reading only mislabels it.
  Stamp the decision `assumed`, name the other reading, and declare it rather
  than asking.
- **A set settles what one file cannot.** Parts exported from one assembly
  share a unit, so a 7 mm washer beside a 170 mm frame is a 7 mm washer.
- Nothing plausible in any unit: convert as mm and say what the bounding box
  came out at. A declared wrong scale is cheap to fix; a silent one is a part
  that fails at assembly.
- A closed mesh whose volume check fails with a correct shape and a large
  bounding-box delta is a units problem.

Scale the verification volume along with the solid, so a declared unit is
checked rather than trusted.
