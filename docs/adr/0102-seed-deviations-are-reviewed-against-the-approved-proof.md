# ADR 0102: A visible seed deviation is reviewed against the Approved Proof

- **Status:** Accepted on 2026-11-11 (owner decision, Rein). Implemented on
  main for new seeded runs; not yet run live.
- **Amends:** ADR 0096 decision 2 ("Over tolerance") and decision 3 (the
  "A changed Component still looks right" row), for seeded runs created from
  now on. For those runs it also amends the review of ADRs 0077, 0080, 0083
  and 0084: what the Component Reviewer compares, and which answers it has.
- **Unchanged:** unseeded runs, every contract before schema 11, and every
  run seeded before this ADR (MAKE-OPTIONS schema 3 or 4). They keep the
  review against the Reference Images.

## Context

ADR 0096 made the owner-approved Contract Proof the build. A seeded run
starts from the Proof's project. A Component equal to the approved one
carries the owner's approval, and a change within `proof_diff` tolerance
keeps it. A change over tolerance is a visible **seed deviation**. Until
now it went "through today's path": one Component Worker and one Component
Reviewer, who compared the changed Component with its AI Reference Image.

That asked the wrong question. The owner already approved the Proof's
shape at Stage 4, after the Proof Critic had compared it with the
references. A forcing gate (a print gate, an Interface, motion, power) now
changed it. What is left to judge is whether the changed Component still
looks like the approved one, apart from what the gate needed. Whether it
looks like the reference image was settled in design. Asking it again in
the run reopens a settled decision. The reviewer could also send the
Component back toward an image the owner chose not to follow, and spend
Shape Rounds on differences the approved Proof already had.

## Decision

1. **The packet compares with the approved Component.** In a new seeded
   run, a component round that the approval does not lock (exact or within
   tolerance) composes, at each Reference Camera, the **Approved Proof's
   Component** beside the changed Component.
   - The approved side is the sealed `seed/approved/part_<id>.step`, placed
     by the sealed approved source's `assembly_pose` (instance 1 for a
     geometry whose count is above 1). It is rendered by `render_review`
     at the same cameras as the changed side. It is never built from the
     round's sources.
   - The changed side is the Component in its Display Pose, as ADR 0083
     renders it.
   - The print-stance sheet (front, top, iso and the rest) stays as it is.
   - The packet records `basis: "approved-proof"` and binds by sha256 the
     approved STEP, the approved source and every approved render. Its
     `references` is empty: **no AI Reference Image is in the packet or
     composed into it.** A changed render or a changed STEP makes the
     packet stale.
   - The Reference Camera still chooses the view. It is a camera, not an
     image.
   - A seed without the approved STEP or source, or a Component with no
     Reference Camera, gets a visual error, not a review against something
     else.
2. **The review.**
   - The reviewer answers `matches_plan` and **`matches_approved`**. It
     does not answer `matches_reference`, which is recorded as `null`
     because the packet shows no reference.
   - It **agrees** when the shape is the approved one, or when every
     difference is one the forcing gate explains: a thicker wall, a
     teardrop roof, a filled overhang, a moved peg.
   - It **disagrees** with a list of differences from the approved render,
     each `{feature, approved, model}`. The Component Worker reads them and
     repairs back toward the approved source and STEP, which ADR 0096
     already gives it as its shape.
   - The record carries `basis` and the `packet_sha256` it judged.
   - Shape Round counting and the Component Acceptance after five Shape
     Rounds are unchanged (ADR 0081). So are reviewer binding (ADR 0081
     #77) and Ruling Disputes (issue #97).
3. **No camera mismatch, no Reference Conflict.** Both are refused for such
   a packet.
   - A camera mismatch (ADR 0083) says that the side of the model facing
     the camera is not the side an image drawn by eye shows. Here both
     sides are exact renders of B-reps, posed by `assembly_pose` and seen
     from one camera. If the poses differ, that is a difference to list,
     because the forcing fix changed how the part stands.
   - A Reference Conflict (ADR 0084) says that an AI image shows what the
     contract forbids. The approved Proof already passed the contract in
     design, and no AI image is shown.
   - Neither answer can arise, so neither is accepted. A review that needs
     one is a disagreement with a listed difference.
4. **The host refuses a review against the references.** Before Make is
   accepted, `verify_made_seed` (with the run's frozen review basis) checks
   every deviation locked by a Component Review, whether within or over
   tolerance. It refuses one whose review:
   - does not name `basis: "approved-proof"`;
   - names no round or packet hash;
   - judged a packet that is missing from its round or changed;
   - judged a packet that does not compare with the Approved Proof, or
     that binds a Reference Image;
   - judged a packet whose approved STEP is not the sealed one.

   A seed lock (exact or within tolerance) still needs no review. The host
   still measures every deviation itself with `proof_diff`. No gate is
   removed or weakened.
5. **Frozen per run.** A new seeded launch freezes
   `seed.review: "approved-proof"` in `MAKE-OPTIONS.json` (schema 5,
   schema 4 plus `review`). No resume, tool refresh or batch rebind adds
   or drops it. `motion_policy.seed_review()` and the host's
   `frozen_seed_review()` read it. A run seeded before keeps reviewing
   against the references. Because the host's check is host code and so
   always current, it reads the frozen basis. Otherwise it would refuse
   those older runs.
6. **Reference Images are a design input.** They are read in design:
   Stage 3a's Contract Proof, the Proof Critic and the owner's Stage 4
   review. In a new seeded build:
   - the Component Reviewer compares with the approved render, never a
     reference;
   - the Component Worker builds from the approved source and STEP and
     views no reference (its instructions say so; nothing enforces it);
   - the assembly review carries the critic's verdict (ADR 0096 partial
     carry), which a deviation reviewed under this ADR still allows.
   - **Not yet changed:** when the assembly carry does not hold (a
     Component Acceptance, an open round), the assembly round's pending
     look still composes the sealed assembly Reference Image, as in any
     run. Replacing it needs an approved assembly render in the seed,
     which `APPROVAL.json` does not seal today. That is a follow-up, not
     part of this decision.
7. **The owner still sees every visible deviation.** `build-a-toy` shows
   each over-tolerance `seed_deviations` entry before publication, as ADR
   0096 requires. It now shows the deviation **beside the approved Proof
   render**: the round's `compare-NN.png`, which already holds both, or the
   Proof's own render with the made one.

## Considered options

- **Keep the reference review (status quo).** Rejected by the owner. It
  re-asks a question Stage 4 already answered, and it can push the
  Component away from the approved shape.
- **Show both the reference and the approved render.** Rejected. Two
  targets invite the reviewer to trade one against the other. The approved
  render is the one the owner chose.
- **Use only `proof_diff` and no reviewer.** Rejected. An over-tolerance
  diff says that the shape moved, not whether it moved only where the gate
  needed. A deterministic measure that separates "a thicker wall" from "a
  redrawn face" is not available yet (ADR 0096 2b leaves the surface limit
  open).

## Consequences

- A visible deviation is judged against what the owner approved. Shape
  Rounds go back toward the Proof, never toward an image the owner did not
  follow.
- The Component Reviewer of a seeded run never sees an AI image. Its
  `toml` instructions describe both packets, and the packet's `basis` says
  which one it is reading.
- An older seeded run in flight is unchanged. Resuming it never switches
  its review.
- The approved render is posed by the approved source's `assembly_pose`
  on the sealed STEP, without the Print Piece decals the changed side may
  carry. A decal is art on paper, not form (ADR 0091), and the reviewer
  judges form.
