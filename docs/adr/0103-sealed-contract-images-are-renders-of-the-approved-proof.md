# ADR 0103: Once sealed, a contract's images are renders of the Approved Proof

- **Status:** Accepted on 2026-11-11 (owner decision, Rein). Implemented on
  main for new seals (APPROVAL schema 4); not yet run live.
- **Amends:** ADR 0096 (and the ADR 0093 rule it quotes) "a Proof is never
  a Reference Image", after the seal only. It also amends ADR 0102 and its
  2026-11-11 amendment: for a schema 4 seal the approved side of every
  review is the contract's own reference image. Neither the in-run render
  of the approved STEP nor `approved/assembly/` is used.
- **Unchanged:** seals of schema 2 and 3, and every run seeded from one.
  So are unseeded runs and design before Stage 4 approval.

## Context

ADR 0102 took the AI Reference Images out of a seeded build's review. It
put renders of the approved Proof beside the model instead: the Component's
approved STEP rendered in the run, and, from its amendment, assembly
renders sealed under `approved/assembly/`. The contract's Reference and
Guide Images were still the design-time AI drawings. A seeded run still
sealed them into `WISH.json`, and its Component Workers and Manager still
read them.

After the owner approves the Contract Proof, those images have one job: to
keep the build from drifting from the approved design. An AI drawing, or a
picture the Proof has since moved away from, does that badly. The approved
CAD itself does it exactly.

## Decision

1. **The seal replaces every contract image.** `seal_proof.py seal`
   renders each Reference Image and Guide Image of the contract from the
   approved Proof, with no AI:
   - A Reference Image is rendered by `render_review`, as an assembly round
     renders the model, at its own Reference Camera. An assembly reference
     comes from the Proof's one assembly entry. A `geometry:<id>` reference
     comes from that Component in its Display Pose (`assembly_pose` of its
     `gen_step()`, instance 1).
   - A Guide Image is rendered by `proof_views.py guide` as the same
     column-per-view sheet, at the cameras it was drawn from, with a 10 mm
     bar. A guide that names one geometry shows that Component; any other
     guide shows the assembly. The cameras come from `--guide-view
     FILE=AZ,EL`, or from the `<stem>.views.json` that `proof_views.py
     guide` now writes beside every sheet.
   - Each render is written under the contract's own file name, in that
     name's format, so `check_reference_names`, `check_guide_names` and
     `workshop wish --ref/--guide` keep working unchanged.
   - Each original moves to `<contract-dir>/design-refs/`, which no run
     reads. A re-seal renders again and keeps the archive. It refuses when
     the image it would replace is neither the earlier seal's render nor
     archived, so a newer design image is never lost.
   - `APPROVAL.json` schema 4 records each image as `contract_images`:
     `{file, kind: "reference", shows, camera, sha256}` or `{file, kind:
     "guide", shows, views, sha256}`, in the contract's order.
   - The seal refuses, before it moves or writes anything, on any of:
     - a reference without a Reference Camera;
     - a guide with no camera;
     - a guide of transformation `steps`, which no single render shows;
     - a render that fails or writes nothing;
     - a Proof without exactly one assembly entry.
2. **The run seals exactly those bytes.** `workshop wish|fix
   --seed-source` (`check_launch_images`) refuses a schema 4 seed unless
   every recorded image is passed with the recorded sha256. A design-time
   image has other bytes, so it never reaches a run. `validate_seed`
   checks that the records are the contract's references, at their
   cameras, and its guides.
3. **One set of approved images.** In a run that froze ADR 0102's review
   with a schema 4 seal, the approved side of each review is the contract's
   own reference image, sealed under `wish-references/`:
   - A Component Review packet (ADR 0102 decisions 1 to 3) composes the
     run's `geometry:<id>` reference images, after checking each one's hash
     and camera against the seal, beside the changed Component in its
     Display Pose. Nothing is rendered from the approved STEP in the run.
   - The assembly look (the ADR 0102 amendment) composes the run's
     assembly reference images the same way. `approved/assembly/` is no
     longer written.
   - The packet keeps `basis: "approved-proof"` and empty `references`.
     It binds the images as `approved.contract_images` (file -> sha256),
     with the sealed paths and the composed copies. The review answers,
     refusals, Shape Rounds and acceptance are those of ADR 0102.
   - A missing image, other bytes, or a Component with no recorded render
     is a visual error.
4. **The host refusal stays.** `verify_made_seed`, given the seal's
   `contract_images`:
   - refuses a deviation's Component Review unless its packet binds, as
     `contract_images`, exactly the seal's renders of that Component, shows
     only those bytes and binds no Reference Image;
   - refuses the assembly look unless it binds exactly the seal's assembly
     renders.

   A packet rendered from the approved STEP, a schema 3 assembly packet,
   and any look against the references are therefore refused in such a
   run.
5. **When a Proof is a Reference Image.** Before approval, ADR 0096's rule
   holds: the Proof is never a Reference Image. The Proof Critic and Stage
   3a's compares measure the Proof against the AI references, and the
   owner approves the Proof beside them. At the seal, the references
   *become* the approved Proof's renders. From then on, everything that
   reads a contract image (the run, its Workers, its Reviewer,
   `build-a-toy`) reads the approved CAD, never the AI drawing. The AI
   images stay in `design-refs/` as the record of how the design was
   reached.

## Consequences

- One image set means one source of truth after approval. The Component
  Worker's sealed reference, the Guide Images it reads and the reviewer's
  approved side all show the approved CAD.
- A seal now renders, so it takes longer by one render per contract image.
- A new design change after a seal goes through Stage 4 again. The new AI
  image goes in place, and the earlier one stays in `design-refs/`.
- Old seals (schema 2, 3) and runs seeded from them are unchanged. Resealing
  an existing toy switches it over.
