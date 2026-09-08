# ADR 0051: Construct and reconcile declared motion states

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
motion manifest, every coupled condition's selected sample indices, generated
STL states, camera and animation. The tool renders with occurrence colors and
one frame of reference. Validation first checks provenance and the existing
independent review, then reconstructs the expected meshes and GIF and compares
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
model or a complete product. Existing drive, collision, insertion, retention,
STEP/export and print checks remain required. In particular, repairing the
animation does not repair an uncaptured crank. The full exported STEP and the
physical product still need their own verification. Native adoption, held-out
Wish fidelity and human acceptance remain unproven until measured.
