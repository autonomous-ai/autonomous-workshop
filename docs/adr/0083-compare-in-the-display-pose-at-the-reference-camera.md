# ADR 0083: Compare each reference in the Display Pose at its Reference Camera

- Status: Accepted as an experiment on branch `rein/remove-likeness`;
  implemented and deterministically tested; not yet validated by a live run
- Date: 2026-10-02
- Owners: the Design Contract (`wish/design_contract.py`,
  `.claude/skills/build-a-toy/CONTRACT-FORMAT.md`, `design-a-toy`), the
  `make-round` skill, the Component Reviewer definition
  (`src/workshop/make/agents/component-reviewer.toml`), product-run Make
  instructions (`references/make.md`), the host's resume path and receipt
  (`workflow/agent_run.py`, `workflow/native_run.py`, `cli/main.py`)
- Amends: ADR 0075 and ADR 0076 (what the comparison shows), ADR 0082 (which
  Components define `assembly_pose`)
- Issue: #81; extended by ADR 0085's issue #100 amendment (2026-10-04): an Owner
  Contract Amendment on resume shares `CONTRACT-AMENDMENTS.json` with the
  camera amendments

## Context

A Component Review compares a sealed reference image with `compare-NN.png`,
the model rendered beside it (ADR 0075, ADR 0076). In Contract Mode that
comparison almost never showed the model from the reference's viewpoint:

- `make_round` rendered the comparison at the reference's declared `@AZ,EL`
  camera, else from `front`. A schema 1 or 2 Design Contract reference has
  only `file` and `shows`, so every Contract Mode comparison was captioned
  "front (no declared camera)".
- The model was rendered in its own STEP frame, its **print stance**. The
  front of a print stance is unrelated to the reference's view.

In Broken God attempt 12 (`wish-20261001-174150-c474fc99`, 26 recorded
reviews) the gear-staff showed its halo edge-on, the heart-core its side and
arm-left one end; only legs-pelvis, which prints upright, lined up. Reviewers
judged from `top.png` and `iso.png` instead, and some recorded differences
were probably view artefacts that spent Shape Rounds. The comparison ADR 0075
makes the review's evidence was unusable for three of the four locked
Components.

## Decision

1. **Design Contract schema 3.** Every reference, the assembly reference
   included, carries `"camera": [AZ, EL]` in degrees, in the Display Pose
   (assembly) frame, in `render_review`'s convention (azimuth 0 looks from
   +X, -90 from the front, -Y; elevation 90 looks down). AZ is in -180..180
   and EL in -90..90. The camera is required in schema 3 and refused before
   it. Schema 3 keeps schema 2's Interfaces section.
2. **Display Pose comparison.** Under schema 3 every Component defines
   `assembly_pose(shape, pose)`; a component round of one that does not is
   refused before anything is built. For a component round `make_round`
   renders `assembly_pose(shape, None)` of the Component's own build at each
   reference's camera and composes `compare-NN.png` from that render. For a
   geometry whose count is above 1 it places the first instance
   (`instance=1`); the reference draws one. `front`, `top` and `iso` stay in
   the print stance, where the reviewer judges print-facing surfaces. An
   assembly round shows its sealed assembly reference from that reference's
   camera.
3. **The camera is estimated by eye.** design-a-toy estimates each camera at
   Stage 3b, rounded to 15 degrees, and writes down the cue it read it from
   ("front and left faces visible, seen slightly from above"). The person
   approves the cameras with the images at Stage 4. There is no silhouette
   pose search (ADR 0076 removed it).
4. **A third verdict: camera mismatch.** A Component Reviewer may answer
   `camera_mismatch` instead of `agrees`, only for an obvious mismatch: the
   side of the model that faces the camera is not the side the reference
   shows (the reference shows the gear's face, the model its edge). It names
   the reference file and the landmarks each side shows, and is never used
   for proportion, thickness or detail. `make_round --record-review` refuses
   one without landmarks or on a round compared without a Reference Camera.
   It is not a Component Review in the policy: the Component stays awaiting
   review, no Shape Round is spent, and nothing is written to `review.json`,
   so the Component Worker gets no repair text. The summary carries the need.
5. **A camera mismatch stops the run with a need**, which the Workshop
   Manager submits with the stage finalizer. The build-a-toy agent answers it
   with `workshop resume <wish-id> --reference-camera FILE=AZ,EL`. The host
   records a **camera-only amendment**: it writes the run-root
   `CONTRACT-AMENDMENTS.json` through the same verified input writer that
   rebinds `MAKE-OPTIONS.json`, rebinds the input manifest in a new
   checkpoint revision and appends a `reference-camera-amendment` record to
   its private host-correction ledger, naming the file, what it shows, the
   sealed camera and the camera before and after. `WISH.json`, the sealed
   requirements and every image keep their bytes and hashes, and the run
   continues in the same session without restarting. `make_round` reads the
   amended camera; a rerun of the unchanged B-rep shows the new view and a
   changed camera never carries an earlier review. The run's receipt lists
   every amendment, and its report prints one line per amendment.

## Consequences

- A reviewer finally sees the Component from where its reference was drawn,
  so Shape Rounds are spent on form rather than on view artefacts.
- Every schema 3 Component must define `assembly_pose`, even one in no
  Interface; it costs one placement function and makes the Display Pose
  explicit for every Component.
- A wrong camera estimate costs one need and one resume, not a Shape Round
  and not a restart.
- The amendment path changes a camera only. Any other contract change still
  needs a new run or a correction (`workshop fix`).

## Compatibility

Schema 1 and 2 contracts parse as before, and their component rounds keep the
declared-camera-else-front comparison in the print stance. A frozen run keeps
its materialized `make_round` and reviewer definition on resume. A run whose
contract is before schema 3 refuses `--reference-camera`.

## Rejected

- Automatic camera estimation or a silhouette search (ADR 0076).
- Neighbour renders at ±30° for the reviewer: too costly for catching obvious
  mismatches.
- Print-gate changes (a separate issue).
