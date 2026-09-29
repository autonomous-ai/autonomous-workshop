# Measuring a reference

The evidence a part is re-authored and assembled from. Measure before the
references are released. Afterwards the only record left is what was frozen
into `params.py` and `validation.py`.

Which source to trust for each kind of number (STEP for analytic faces, the
STL for anything faceted, because a converter's repair can move faces) is in
`skills/wiki/pages/reverse-engineering/mesh-measurement.md`
(`wiki show mesh-measurement#which-source-to-trust-for-which-number`).

Everything below runs on triangles, from an STL or a tessellated STEP, with
numpy and shapely alone. It never touches the CAD daemon, so it can run while
another job holds it.

## Instruments

| instrument | what it answers | how |
|---|---|---|
| **flat levels** | floor, ledge and top heights, and the area at each | group facets with normal ±Z by height and sum their area; an upward level of 794.7 mm2 at z = 25.5 is a ledge |
| **section polygon** | the exact outline at one height | intersect every triangle with the plane, polygonize the segments, fill even-odd |
| **circle fit** | bore and boss diameters and centres | least squares on a section loop's vertices; facet vertices lie *on* the true circle, so the fit recovers the radius, not the chord |
| **section sheet** | what the part is | plot 12–16 filled sections (z, then x and y) on a grid and look at them |
| **rotation-overlap scan** | D-flat direction, gear tooth phase | rotate one section against another in small steps; the answer is the angle of zero or minimal overlap area |

Read sections from a sheet first, then take numbers from vertex lists; keep
readings that land between round numbers and never round an asymmetry away
(`wiki show mesh-measurement#principles-that-make-mesh-readings-exact`).

## Instruments that lied

Five naive implementations returned wrong readings on real parts: section
endpoints that do not meet, even-odd fill by face, a cut plane through
vertices, angles from point statistics, and penetration depth from winding
numbers. Each failure and its fix:
`wiki show mesh-measurement#instruments-that-lied`. Implement the instruments
above with those fixes.

## Comparing source against the reference

While the reference exists, tessellate the built solid and cut both at the
same planes (5 per axis at 8–92 % of the extent, plus every level that
matters), and report per-cut area, IoU and the symmetric-difference centroid.
Use `step_verify` against an exact STEP. The report format, and what agreement
to expect against a mesh:
`wiki show mesh-measurement#comparing-source-against-the-reference`. How to
freeze the figures is in `re-authoring.md`.
