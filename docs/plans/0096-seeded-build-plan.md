# Plan: the approved Proof is the build (ADR 0096)

Status: draft for the owner, 2026-11-02. Nothing here is implemented.
Each phase is one PR with deterministic tests, per AGENTS.md. Phases 1 and
2 can run in parallel. Phase 3 needs 2, phase 4 needs 3, and the pilot
needs all of them.

## Phase 0: owner decisions

Decided on 2026-11-02 (ADR 0096, "Owner decisions"):
- a critic cap of 5;
- one critic for the whole toy, with a close look at one Component only
  when needed;
- a Concept Checklist;
- a visible deviation goes through the in-run reviewer and is shown
  before publication;
- a diff tolerance of 1% volume, 0.1 mm per bounding-box side and a
  two-way difference of at most 1%;
- every Proof follows Make's rules;
- the beaver coaster pilot.

- no contract-only first round and no contract-only fresh read. The
  Approved Proof owns the shape and the contract keeps what gates measure
  or the owner decides (ADR 0096 decision 1c). `proof_diff` replaces the
  contract-only read wherever it protected the shape (decision 2b).

## Phase 1: design-a-toy (skill only, no host change)

Files under `.claude/skills/design-a-toy/`:

- **`proof-prompt.md`** (ADR 0096 decision 1b: the Proof follows Make's
  authoring rules exactly, so its source can seed the build)
  1. **Opening paragraph.**
     - "You check the contract; you do not design. Read only the Design
       Contract" becomes: "You build the toy the owner will approve and
       Workshop will ship."
     - It reads the contract, the references, the Guide Images, the
       concept and its three views, and `CONCEPT-CHECKLIST.md`, from
       round 1.
     - The contract owns function, critical dimensions, Interfaces,
       print choices, colours, Bought Parts and electrical (ADR 0096
       decision 1c). The images own the shape.
     - The Make rule homes below are allowed in every round.
  2. **New "Write it as Make writes it" section.** It points at these
     homes and copies none of their text:
     - `.agents/product-run/.agents/skills/autonomous-workshop/references/make.md`
       § Pipeline step 1: the component list, the overhang repair order,
       the shared files, the install commands, the Interfaces paragraph
       and the Shared Helper sample paragraph;
     - `src/workshop/make/agents/component-worker.toml`: the Shared
       Helper, `assembly_pose`, instance, decorative-detail, Print Piece,
       kit and blunt-tip bullets.

     Wherever they say "the Manager" or "the worker", the Proof does
     both.
  3. **Layout step, before any part.**
     - `uv run python src/workshop/make/skills/print-details/scripts/print_details.py --install <OUT>`,
       plus `--install-print <OUT> --wish <draft WISH>` for a `print`
       section and `make-round/scripts/kit_tree.py --install` for a tree.
       Phase 2 must check that these work on a contract outside a run,
       or add a `--contract` input as `--print-gates-only` has.
     - Never edit the installed files.
  4. **Detail step.**
     - Every listed decorative detail goes through `Details(nozzle=…)`;
       every point or rib end through `blunt_tip` / `rib_end`.
     - A Detail Refusal goes into `FINDINGS.md` under "Refused detail",
       with the passing value the refusal names. It is never modelled by
       hand and never silently dropped.
  5. **Joint step.**
     - Before each joint, fit, clearance or gear, run
       `src/workshop/make/skills/wiki/scripts/wiki search …` and `show …`.
     - Write `# wiki: <slug>` beside the value and add the page's
       `assert`.
     - A fit the contract does not give is a guess, because fits are a
       contract field, with the page cited.
  6. **Standard-part step.** Every gear, bearing and fastener comes from
     `src/workshop/make/skills/cad/scripts/stdpart` (`bd_warehouse`,
     `py_gearworks`). No hand-written involute.
  7. **Shared Helper step.**
     - `params.py` and `features/` hold only Interface values, joint
       sections and standard profiles.
     - One `samples/<name>.step.py` per helper.
     - `make_round <OUT> --shared-helpers --contract <CONTRACT>` must
       pass before step 4's print gates. Phase 3 adds a standalone mode
       if the current one needs run state.
  8. **Surfaces.** True arcs and sweeps, not engraving built from many
     small flat faces.
  9. **New "Model the shape from the images" section (round 1 on).**
     - Measure each reference, Guide Image and concept view with
       `src/workshop/make/skills/image-to-cad/SKILL.md` Steps 1-4b and 6:
       triage, `measure_image.py`, the cross-check gate, scale anchor,
       three views, per-component description, the operation map. Never
       Step 5 or Step 8.
     - Build the shape to those measurements and the checklist's traits.
       A shape number stays in the Proof.
     - Write to `GUESSES.md` only a number that falls in a contract
       field: a fit, a critical dimension, an Interface pose, a colour,
       a bought part. The coordinator closes those in the contract; the
       list must reach zero.
     - Where the images and a contract field disagree, the contract
       wins. Write it under "Image vs contract" in `FINDINGS.md`, so the
       coordinator can decide whether to amend the contract or edit the
       image.
  10. **Gate failures, split** (ADR 0096 decision 1b):
      - A failure forced by a contract value stays a finding:
        "never change the model to pass it".
      - A failure on the Proof's own shape is repaired under make.md's
        overhang order and listed under "Shape repairs" for the critic.
  11. **Kept unchanged.** The print-gates command, `FINDINGS.md`'s
      contradiction and placement rules, and the amendment re-read.
  12. **Remove.** The "contract has to stand on its words" sentence, and
      "the list must reach zero" for shape choices.
  13. **Reply line.** Add the counts of refused details, wiki citations
      and shape repairs.
- **New `critic-prompt.md`** (the Proof Critic)
  - It reads: the compares (`proof_views.py refs`/`compare`, the concept
    at its cameras), the requirement rows, Interface text, the prose
    sections, the owner's Stage 1 printability decisions (so it does
    not ask for a detail the owner left out), and the Proof's "Shape
    repairs".
  - It is now the only reader that judges the shape before the owner.
  - It never reads or writes the Proof's code.
  - Its verdicts are the Component Reviewer's: agree, differences,
    Reference Conflict, camera mismatch.
  - Its last round gives one verdict per requirement id.
  - It writes `proof/CRITIC.json`; its schema lives in the prompt.
  - One thread for the whole toy, kept and reused for the whole design.
  - **Close look.** When it cannot settle a Component from the whole-toy
    compares, it asks for that Component alone at its Reference Camera
    and its Guide Image cameras (`proof_views.py compare` on the one
    `part_<id>.step.py`). The same thread judges it, and `CRITIC.json`
    records why.
  - **Concept Checklist.** It judges every trait in
    `CONCEPT-CHECKLIST.md` at the concept's cameras: kept, lost, or
    changed by a named owner decision. A lost required trait is a
    difference.
- **New `checklist-prompt.md` and a Stage 1 step.**
  - After the three views, a fresh subagent that sees only the concept
    and its three views writes `CONCEPT-CHECKLIST.md`: 8-12 traits, with
    measured ratios where possible.
  - The owner marks each required or changeable. This costs about 0.3
    units and two minutes of the owner's time.
- **`SKILL.md` Stage 3a**
  - Step 1: the kept Proof sees images, the concept and the checklist
    from round 1.
  - Step 2: guesses to zero only for contract fields.
  - New step: the critic loop until it agrees, capped at 5
    geometry-changing rounds.
  - Step 6 (the fresh read) is removed.
  - The rule "the Proof runs again after every amendment" stays. Each
    amendment then runs `proof_diff` against the last Approved Proof,
    so a visible change goes to the critic and the owner.
  - Remove "a Proof is never a Reference Image, and nothing compares it
    with the model" and the Trial F caveat that the build differs from
    the Proof.
- **`SKILL.md` Stage 4.** Open with concept | Proof | 50% overlay at the
  concept's cameras and the checklist count, then each reference compare, then the critic's open
  lines. Approving now means "this is what ships".
- **`SKILL.md` Stage 5**
  - Run the new `scripts/seal_proof.py`, which writes `APPROVAL.json`.
  - Hand off to `build-a-toy` with the contract and the proof directory.
  - The "what happens next" text: Workshop certifies, not rebuilds.
- **`proof_diff` (shared tool, not a skill script).**
  - It lives at `src/workshop/make/proof_diff.py`, with a CLI, so that
    design, Make, the host and DETECT run the same bytes.
  - It compares two STEP files or two projects Part by Part with OCP:
    volume, the bounding box in the print stance and the Display Pose,
    and the two-way Boolean difference (only-A plus only-B).
  - It passes a Part at |dV| ≤ 1%, each bounding-box side ≤ 0.1 mm, and
    the two-way difference ≤ 1% of volume.
  - When the Boolean fails, it reports `boolean: failed` and judges on
    volume and bounding box alone.
  - It writes JSON and exits 1 over tolerance.
  - Design calls it in Stage 3a after each amendment and in Stage 5.
- **`scripts/seal_proof.py`**
  - Calls make_round's own identity and carry-key code; it does not
    reimplement them. To make this possible, Phase 3 exposes
    `make_round --identities-only <project> --contract`.
  - Exports each Component's approved STEP (print stance and Display
    Pose) into `proof/approved/`.
  - Writes `APPROVAL.json`:
    - the contract's sha256 and the manifest;
    - each Component's identity and carry key, and each STEP's sha256,
      volume per Part and bounding box;
    - the assembly identity;
    - the hashes of `CRITIC.json`, `CONCEPT-CHECKLIST.md` and the
      make_round tool;
    - the nozzle, `approved_by` and the date;
    - the design's cost from `tokens.py`. Also the sha256 of `src/workshop/make/skills/LOCK.json`
    and of the installed `features/print_details.py`.
  - Refuses a project that breaks decision 1b: no installed
    `features/print_details.py`, a joint value with no `# wiki:` and
    `assert`, or a `samples/` helper freeze that did not pass.
- **Tests:**
  - `proof_diff`: identical; a hidden pocket over 1%; an add-and-remove
    change with a net dV of 0 that the two-way difference catches; a
    0.2 mm bounding-box change; a faceted-vs-arc pair where the Boolean
    fails.
  - `seal_proof`: a manifest mismatch refuses.
- **`LESSONS.md`:** nothing new until the pilot.

## Phase 2: host (`src/cli/`, `src/workshop/wish/`, `src/workshop/workflow/`)

- **Contract schema 11** (`src/workshop/wish/design_contract.py`).
  - Schema 10 plus `shape: "approved-proof"`.
  - Geometry-scoped form rows and prose sections are optional.
  - The host refuses schema 11 without `--seed-source`.
  - Schemas 1-10 parse as before.
- **CLI.** `wish --seed-source DIR` and `fix --seed-source DIR`.
  - Refused without `--contract`.
  - Refused with `--workflow forge|quest`.
- **Validation,** a pure function in `src/workshop/wish/seed.py`. It
  refuses:
  - a missing `APPROVAL.json`, or an unknown schema;
  - a contract sha256 that is not the sealed contract's;
  - a missing, extra or changed file against the manifest;
  - a symlink or a path outside `DIR`;
  - a missing `CRITIC.json`, `CONCEPT-CHECKLIST.md` or approved STEP,
    or one whose hash differs;
  - a geometry in the contract with no Component in the manifest.
- **Sealing.** Copy the tree into the run as an immutable input, covered
  by the existing hash manifest.
- **Freezing.** Write `MAKE-OPTIONS.json` schema 3 `seed: {approval_sha256,
  manifest_sha256}`. A resume cannot add or drop it. Schemas 1 and 2 read
  as before.
- **Receipt and status.** Add `seed` and `seed_deviations` to the
  checkpoint, the run receipt and `workshop status --json`. The CLI prints
  "approved in design by the owner on <date>".
- **Archive.** The published toy archive and the local toy project
  carry the Approved Proof (code, `proof/approved/` STEP,
  `APPROVAL.json`) as a required artifact. `fix` of a schema 11 toy
  without it is refused.
- **Make acceptance.** The host runs `proof_diff` itself, on the sealed
  approved STEP and the made STEP, for every Component and the assembly.
  This is a byte comparison, not a verifier rerun. The host check
  refuses:
  - a carried `seed-approval` review whose identity is not in the sealed
    approval;
  - an assembly review carried from the critic when any Component
    deviated;
  - a deviation over tolerance without its Component Review;
  - on `fix`, a Component over tolerance against the Approved Proof
    without a new approval.

  It does not rerun any gate (ADR 0061).
- **Tests:** a failure-path test for each refusal above, plus the
  frozen-run test that a schema 2 `MAKE-OPTIONS` run is unchanged.

## Phase 3: make-round (`src/workshop/make/skills/make-round/`, guard, hook)

- **`round_policy` gains a seed input.**
  - A component round whose identity and carry key equal the approval's
    is passed and locked, with `review.carried_from: "seed-approval"`.
  - A different identity is a deviation, and the round runs `proof_diff`
    against the approved STEP.
    - Within tolerance: passed and locked, with
      `review.carried_from: "seed-approval"`, and the diff recorded in
      the round.
    - Over tolerance: "passed, awaiting review", with the ADR 0081 rules
      from Shape Round 0.
- **Assembly carry.** When every Component carries and the assembly
  identity matches, the assembly review is composed from `CRITIC.json`'s
  assembly verdict and its requirement verdicts, and the blind-review
  requirement is skipped. Any deviation restores the blind review.
- **Kept as is:** `--full`, `--interface`, `--shared-helpers`,
  `--powered`, `--print-gates`.
- **Standalone modes for the Proof.** `--shared-helpers` (and the
  `print_details.py --install-print` / `kit_tree.py --install` inputs)
  take `--contract` outside a run, as `--print-gates-only` does. They
  write only inside the project.
- **Toolchain drift in a seeded run.** When the seed's
  `features/print_details.py` differs from the run's library bytes,
  reinstall the library and rebuild. A changed shape fingerprint is a
  seed deviation.
- **`--identities-only`** for `seal_proof.py`: build and hash, with no
  gates, renders or state.
- **Guard and hook.** On a seeded run, a component round of an
  approved Component needs no `component-worker` nonce, because the root
  runs it. A deviation still needs a worker's nonce (ADR 0080).
- **Tests:**
  - the pure policy table: carry, deviation, helper change after carry,
    a carry key that differs only in its rows;
  - an assembly carry refused after a deviation;
  - the nonce rule.

## Phase 4: product-run instructions and build-a-toy

- **Product-run `AGENTS.md` and `references/make.md`:** a short "seeded
  run" path.
  - Run the Shared Helper freeze, then one component round per
    Component, then the Interfaces, the assembly and `--full`.
  - Spawn workers only for a deviation.
  - Never rule on shape; a contradiction is a need.
  - This text is read only when `seed` is set, so unseeded runs re-send
    no new tokens (ADR 0094 decision 6).
- **`build-a-toy` `SKILL.md`**
  - Step 2: add `--seed-source <contract-dir>/proof`.
  - Step 6: `fix --seed-source` after a design-side amendment.
  - "Fixing a Contract Contradiction at the root": in seeded runs, use
    the kept Proof, the critic, the owner if visible, then re-seal.
  - Root amendments: the kept Proof rebuilds, then `proof_diff` runs
    against the last Approved Proof. Within tolerance, re-seal without
    waiting for the owner. Over tolerance, the critic judges and the
    owner approves.
  - Before publication, show the owner every visible seed deviation.
  - Folding in ADR 0085 amendments: unchanged. A visible ADR 0085
    amendment is refused by `proof_diff`.
- **`DETECT.md`:**
  - New `shape:<geometry>` row: `proof_diff` of each made Component
    against the Approved Proof it was seeded from.
  - For schema 11, drop `extents:` and form rows.
  - Keep `envelope` when stated, and keep `print:`, `count:`, motion,
    power and the contract-owned requirement rows.
  - Seed deviations within tolerance go into `notes`.
  - Schemas 1-10 are unchanged.

## Phase 5: pilot and measurement

- **Toy:** the beaver coasters (owner, 2026-11-02),
  currently at Stage 4.
- **Measure:**
  - design cost split into Proof, critic, checklist and coordinator;
  - Make cost against K4's 33.6;
  - seed deviations;
  - gates;
  - the owner's verdict.
- **Success:**
  - Make at or below 12 units with 0 deviations, or every deviation
    traced to a gate;
  - every `proof_diff` in the build within tolerance, or the deviation
    shown to the owner;
  - the owner says the build is what they approved.
- **Optional A/B:** reseed K4 from its kept Proof, so the cost is
  compared on one toy.

## Estimated savings (estimates until Phase 5 measures them)

| Item | Today (measured) | Seeded (estimate) |
|---|---|---|
| Make, K4-sized | 33.6 units | 6-12 units (build, gates, Interfaces, `--full`, export, Manual) |
| Drift fix rounds | K4 v02: 18 units, partly face drift | 0 for in-run ruling drift |
| Design: critic rounds | none | +0.5-1.5 units (2-4 rounds at about 0.3) |
| Design: image-aware Proof rounds | 0.1-0.5 per amendment | about the same; images add some context |
| Fresh contract-only read | 1.1-1.7 units | 0 (dropped; `proof_diff` is free) |
| Contract-only first Proof round | 0.7-0.85 units, then rebuilt | 0 (round 1 already sees images) |
| **Net per toy** | | **about 16-27 units saved** |

## Risks

- **Proof code a worker must repair.** Mitigated by the production-CAD
  rules in `proof-prompt.md`.
- **The coordinator's context grows.** The critic and the compares stay
  in subagents (PROOF-COST: the coordinator is 55-60% of design cost).
- **Gate or catalogue drift between design and build.** Every gate is
  rerun in the run; a failure is a deviation or a need, never ignored.
- **Rebuilding without the Proof's code is harder** (ADR 0096
  Consequences).
  - A schema 11 contract alone does not define the shape.
  - Mitigation: the archive keeps the code and the STEP files, the STEP
    files outlive the toolchain, and `fix` refuses a toy without its
    Approved Proof.
- **A small visible change under 1%.** A changed engraved face, for
  example, may stay inside the tolerance. The two-way difference
  narrows this, every deviation is still listed, and the pilot measures
  it on K4's v01 faces.
- **The approval can be forged by whoever runs the CLI.** Recorded
  honestly in ADR 0096 §3: it is operator input, like the contract.
