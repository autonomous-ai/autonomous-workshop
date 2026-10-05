# ADR 0060: Construct and reconcile declared motion states

- Status: Implemented locally; native transfer evaluation pending
- Date: 2026-09-09
- Scope: new bundled CAD skill; older materialized runs retain their bytes

## Problem

A reviewed animation can implement a different motion law from the collision
manifest. Hashes bind the supplied source, states, movie and review, but do not
prove their correspondence. In a reproduced keyed-rotor case, the animation
counter-rotated the shaft against the wheel while the manifest co-rotated them.
The latter was clear; the former intersected. Refreshing provenance preserved
the contradiction.

## Decision

Make's deterministic CAD tools construct presentation states from the same
source-built reference assembly, placed occurrence index and pose functions
used by `check_motion`. A named group moves each descendant once. Ambiguous
labels and overlapping moving selections fail explicitly. The constructor
supports the existing rotation/translation order and nonuniform pose tables;
the native agent continues to author the mechanical model and select the
meaningful presentation samples and camera.

Motion evidence version 2 records the assembly entry, project Python sources,
motion manifest, every coupled condition's selected sample indices, the hash of
every generated state, camera and animation. The tool renders with occurrence colors and
one frame of reference. Validation first checks provenance and the existing
independent review, then reconstructs the expected states and GIF and compares
their bytes. Rehashing an incorrect state or unrelated animation is insufficient.
The source and manifest are rechecked after reconstruction.

The motion-review schema and two-round critic limit remain unchanged. A new
movie needs a review of its new evidence. Version 1 evidence is not promoted by
the new tool; frozen older workspaces keep the original copied validator.
This is a deterministic construction and artifact check, not a Python
reasoning loop, new agent runtime or physical dynamics engine.

## Evidence and limits

Deterministic fixtures cover altered and rehashed states/movies, omitted motion
conditions, nested groups and ancestor placements, repeated labels, overlapping
movers, nonuniform rotation plus translation, fixed framing and stale review.
The retained failure is also replayed outside the running native cohort.

This proves correspondence to a declared motion model, not correctness of that
model or a complete product. Existing drive, collision, insertion, retention
and STEP checks remain required. In particular, repairing the
animation does not repair an uncaptured crank. The full STEP and the
physical product still need their own verification. Native adoption, held-out
Wish fidelity and human acceptance remain unproven until measured.

## Superseded in part (2026-09-10)

ADR 0062 makes STEP the only geometry format the toolchain writes. The
constructor, the reconstruction comparison and evidence schema 2 all stand;
the states are now tessellated in memory and bound by hash instead of being
written as `measure/motion-states/state-*.stl`, which a sealed product manifest
would reject.

## Amended: no fixed state byte limit (2026-10-03, #93)

Generation refused a posed state whose canonical encoding exceeded 20 MiB
(about 419k triangles). That cap was the size limit of the on-disk state
files this ADR originally wrote. Once ADR 0062 moved the states into memory
it protected nothing: validation never checked it, and it fired only after
every state was posed and every frame rendered. It did decide geometry: a
Broken God run swapped locked, contract-required rivets for bosses and then
blocked, because round rivets and bosses both exceeded it.

The cap is removed. A state is the assembly's own tessellation at the fixed
`motion_states.TOLERANCE`; generation and validation build it identically
and the hash binding is unchanged, so a changed or rehashed state still
fails. The work stays bounded by the 48-state limit and the optional
deadline. A coarser presentation tessellation was rejected: a small round
feature's triangle count is set by the angular tolerance (a sphere is about
8,000 triangles at any radius), so it would need a second, adaptive
tolerance, and remeshing a shape that already carries a finer triangulation
would make the hash depend on call order. No print or geometry gate changes.
Materialized runs keep their copied tool bytes, including the cap.
