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
- **Amended** on 2026-11-11 (owner decision, Rein): a seeded build uses no
  AI Reference Image anywhere in review, the assembly look included. See
  the amendment at the end.

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
   - when the assembly carry does not hold (a Component Acceptance, an
     open round), the assembly round's look compares with the Approved
     Proof's own assembly render, never the assembly Reference Image. See
     the 2026-11-11 amendment below; a seal without that render keeps the
     earlier look.
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

## Amendment 2026-11-11: the assembly look compares with the Approved Proof

The owner confirmed the intent: a seeded build must not use AI Reference
Images anywhere in review. Decision 6 left one place. When the Approved
Proof's assembly review does not carry (a Component Acceptance, an open
round), the assembly round's pending look composed the sealed assembly
Reference Image beside the model. It now composes the Approved Proof's own
assembly instead.

1. **The seal renders the approved assembly.** `seal_proof.py seal` writes
   `APPROVAL.json` schema 3: schema 2 plus `assembly_renders`.
   - The seal runs the CAD skill's `render_review` on the Proof's one
     assembly entry (`*.step.py` that is not a `part_`) at each distinct
     `[AZ, EL]` Reference Camera of the contract's `shows: "assembly"`
     references. These are the same cameras, and the same `az{AZ}_el{EL}.png`
     names, at which an assembly round renders the model.
   - It seals each render under `approved/assembly/` (so it is in the
     manifest) and records it as `{file, camera, sha256}`.
   - A contract with no assembly camera seals an empty list. A render that
     fails, a missing render or a Proof without exactly one entry refuses
     the seal.
   - The host's `validate_seed` accepts schema 2 and 3. For schema 3 it
     checks that each render is in the manifest as sealed, is named for its
     camera, and that the cameras are the contract's.
2. **The assembly round compares with it.** In a run that froze the
   review (`seed.review: "approved-proof"`, decision 5) and whose seal
   carries `assembly_renders`, an assembly round whose look the Approved
   Proof's review does not carry:
   - composes, at each sealed render's camera, that render beside the model
     rendered at the same camera. The render is copied from `seed/` after
     its sha256 is checked; it is never rebuilt in the run;
   - writes a packet with `basis: "approved-proof"`, empty `references`,
     and `approved: {assembly_renders, sealed, renders}`, which binds the
     sealed files and their copies by sha256. A changed copy or a changed
     sealed render makes the packet stale. A missing or changed sealed
     render is a visual error, never a fall-back to the reference;
   - the camera is the sealed render's own. A host-recorded camera
     amendment (ADR 0083) moves a Reference Image's camera, and no
     Reference Image is shown here.
3. **The Manager's look.** `--record-visual` on such a packet takes
   `matches_approved` instead of `matches_reference`. It lists each
   difference as `{feature, approved, model, decision, reason}`.
   `matches_reference` is refused, and so is a reference-shaped difference
   or a pass with `matches_approved` false. Everything else (findings, the
   observation, `--full`) is unchanged.
4. **Carrying an earlier look.** An earlier recorded pass carries (issue
   #244) only when its packet has the same basis and the same sealed
   renders as the new one. A look taken beside the references never stands
   for one the run must take beside the Approved Proof.
5. **The host refuses a look against the references.** Before Make is
   accepted, `verify_made_seed` (with the frozen basis and the seal's
   `assembly_renders`) reads the last assembly round. The Approved Proof's
   carried review (`carried_from: "seed-approval"`) passes. Otherwise the
   look that stands is either that round's or the earlier round's it
   carried from. The host refuses that look when:
   - it has no recorded feedback or no packet;
   - the feedback or the summary binds another packet hash;
   - its packet lacks `basis: "approved-proof"`, binds a Reference Image,
     names other sealed renders, or shows copies that are not the sealed
     bytes;
   - its feedback answers `matches_reference` or omits `matches_approved`.
6. **Existing seals keep the current behaviour.** A schema 2 seal carries
   no assembly render. A run seeded from one compares its assembly look
   with the Reference Image as before, and the host does not check that
   look. That holds even in a run that froze the review. A new seal is
   needed to switch an existing toy over.

No gate is weakened. The Component Review of decisions 1 to 4, the blind
review and `--full` are unchanged. The renders are B-rep renders, as the
model side is, so neither a camera mismatch nor a Reference Conflict can
arise here either.
