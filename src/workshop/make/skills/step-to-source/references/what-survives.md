# What a B-rep keeps, and what it destroys

Read this when a recovery is refused, when deciding whether to promise that a
supplied file can be made parametric, or before re-parameterising a recovered
entry.

## What the export destroys

The shape of a planes-and-cylinders solid rebuilds exactly. Everything that
made it editable (names, relationships, mate derivations, boolean operands,
mirror pairs, module structure, fillets as features) is gone, so **change one
number and nothing follows it**. The full table, and why AP242 design history
is not worth hoping for:
`skills/wiki/pages/reverse-engineering/brep-vs-source.md`
(`wiki show brep-vs-source#shape-and-source-are-two-questions`).

## Re-parameterising a recovered entry

The order matters, because only the first two steps are provably safe.

1. **Name the dimensions.** Hoist the numbers that carry meaning into one
   parameter block with provenance comments saying they were measured from the
   named STEP. Leave incidental profile coordinates alone; naming every vertex
   produces noise, not parameters.
2. **Restore the relationships.** Any dimension that was derived must be
   derived again - a bore is `shaft + clearance` through `cadfits`, a wall is
   `outer - inner`. Never type both halves of a mate independently; that is the
   defect the repository's fit audit exists to catch, and a recovered file
   arrives full of it.
3. **Re-apply features.** Chamfers and fillets recovered as geometry become
   `chamfer()` / `fillet()` on selected edges, using the radii and half-angles
   `step_probe` reported. This is also the fix for an approximated fillet:
   recover the sharp body, apply the fillet in source, and the result is both
   exact and editable.
4. **Verify after each step.** Steps 1 and 2 must not move a single face, and
   `step_verify` against the original STEP is what proves it - run it after
   each, not once at the end, or a typo in step 1 is discovered as a mystery in
   step 3. Step 3 deliberately changes the surface kinds; expect the face-kind
   lines to differ and the volume to move by the blend volume.

## When a recovery is refused

The refusal names the slab and the surface kind. What each kind usually means,
and why surface kinds alone do not predict a refusal, is in
`wiki show brep-vs-source#what-a-refusal-is-telling-you`. The routes, in the
order worth trying:

- **Curved taper (torus):** recover the sharp body and re-apply the blend in
  source; `--loft-tapers` is the fallback when the blend must stay geometry,
  and it reports what it cost.
- **No extrusion axis:** re-author it from measurements (`re-authoring.md`).
  A purchased component that only has to be seated stays under
  `<project>/ref/` with a `cadmount` seat.
- **Ellipse or spline profile:** check the axis in `step_probe` first; if the
  curve is real, author that profile by hand.
- **Topology changing inside one slab:** split the model to give the feature
  its own boundary, or author the feature by hand.
- **A converted mesh of a mechanical part:** re-author it (`re-authoring.md`).

## The comparison

`step_verify` exits on the symmetric difference, reports the volume delta
without deciding on it, escalates OpenCASCADE's fuzzy value only as far as
needed and reports which value answered, and reports an uncomputable
comparison as a failure. Why: `wiki show
brep-vs-source#why-the-comparison-is-a-symmetric-difference`.
