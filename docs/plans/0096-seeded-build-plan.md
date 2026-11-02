# Plan: the approved Proof is the build (ADR 0096)

Status: draft for the owner, 2026-11-02. Nothing here is implemented.
Each phase is one PR with deterministic tests, per AGENTS.md. Phases 1 and
2 can run in parallel. Phase 3 needs 2, phase 4 needs 3, and the pilot
needs all of them.

## Phase 0: owner answers

The six open questions at the end of ADR 0096. Defaults if the owner does
not answer: cap 5, one critic thread, no checklist yet, a visible deviation
goes through the in-run reviewer, 1% / 0.1 mm, beaver pilot.

## Phase 1: design-a-toy (skill only, no host change)

Files under `.claude/skills/design-a-toy/`:

- **`proof-prompt.md`**
  - Round 1 stays contract-only: the guess list must be honest.
  - New section "When you are sent images": from round 2, the kept Proof
    reads the references, Guide Images, the concept and its three views,
    and the compares. Every number taken from an image goes into
    `GUESSES.md` as "from image", so the coordinator amends the contract
    that round. The list must still reach zero.
  - Production CAD rules: the print-details library, true arcs and
    sweeps instead of faceted engraving, named helpers in `features/`,
    only Interface values and joint sections in `params.py` (ADR 0082).
    The run will ship this code.
  - Unchanged: the print-gates command, `FINDINGS.md`, kit
    `print_parts()`.
- **New `critic-prompt.md`** (the Proof Critic)
  - It reads: the compares (`proof_views.py refs`/`compare`, the concept
    at its cameras), the requirement rows, Interface text, the prose
    sections, and the owner's Stage 1 printability decisions (so it does
    not ask for a detail the owner left out).
  - It never reads or writes the Proof's code.
  - Its verdicts are the Component Reviewer's: agree, differences,
    Reference Conflict, camera mismatch.
  - Its last round gives one verdict per requirement id.
  - It writes `proof/CRITIC.json`; its schema lives in the prompt.
  - Kept and reused for the whole design.
- **`SKILL.md` Stage 3a**
  - Step 1: the kept Proof sees images from round 2.
  - New step: the critic loop until it agrees, with the cap from Phase 0.
  - Step 6: the fresh read, then a new `proof_views.py diff` (below).
  - Remove "a Proof is never a Reference Image, and nothing compares it
    with the model" and the Trial F caveat that the build differs from
    the Proof.
- **`SKILL.md` Stage 4.** Open with concept | Proof | 50% overlay at the
  concept's cameras, then each reference compare, then the critic's open
  lines. Approving now means "this is what ships".
- **`SKILL.md` Stage 5**
  - Run the new `scripts/seal_proof.py`, which writes `APPROVAL.json`.
  - Hand off to `build-a-toy` with the contract and the proof directory.
  - The "what happens next" text: Workshop certifies, not rebuilds.
- **`scripts/proof_views.py diff A B`**
  - Compares two Proof projects Part by Part with OCP: volume, bounding
    box, two-way Boolean difference, the method of CONCEPT-DRIFT Part 1.
  - When the Boolean fails on faceted faces (as on K4's heads), it falls
    back to volume and bounding box.
  - It writes `proof/fresh-diff.json` and exits 1 over tolerance.
- **`scripts/seal_proof.py`**
  - Calls make_round's own identity and carry-key code; it does not
    reimplement them. To make this possible, Phase 3 exposes
    `make_round --identities-only <project> --contract`.
  - Writes `APPROVAL.json`: the contract's sha256, the manifest, each
    Component's identity and carry key, the assembly identity, the hashes
    of `CRITIC.json`, `fresh-diff.json` and the make_round tool, the
    nozzle, `approved_by`, the date, and the design's cost from
    `tokens.py`.
- **Tests:** unit tests for `diff` (identical, a hidden pocket, a
  faceted-vs-arc pair) and for `seal_proof` (a manifest mismatch refuses).
- **`LESSONS.md`:** nothing new until the pilot.

## Phase 2: host (`src/cli/`, `src/workshop/wish/`, `src/workshop/workflow/`)

- **CLI.** `wish --seed-source DIR` and `fix --seed-source DIR`.
  - Refused without `--contract`.
  - Refused with `--workflow forge|quest`.
- **Validation,** a pure function in `src/workshop/wish/seed.py`. It
  refuses:
  - a missing `APPROVAL.json`, or an unknown schema;
  - a contract sha256 that is not the sealed contract's;
  - a missing, extra or changed file against the manifest;
  - a symlink or a path outside `DIR`;
  - a missing `CRITIC.json` or `fresh-diff.json`, or one whose hash
    differs;
  - a fresh diff that is not passing;
  - a geometry in the contract with no Component in the manifest.
- **Sealing.** Copy the tree into the run as an immutable input, covered
  by the existing hash manifest.
- **Freezing.** Write `MAKE-OPTIONS.json` schema 3 `seed: {approval_sha256,
  manifest_sha256}`. A resume cannot add or drop it. Schemas 1 and 2 read
  as before.
- **Receipt and status.** Add `seed` and `seed_deviations` to the
  checkpoint, the run receipt and `workshop status --json`. The CLI prints
  "approved in design by the owner on <date>".
- **Make acceptance.** The host check refuses:
  - a carried `seed-approval` review whose identity is not in the sealed
    approval;
  - an assembly review carried from the critic when any Component
    deviated;
  - a deviation without its Component Review.

  It does not rerun any gate (ADR 0061).
- **Tests:** a failure-path test for each refusal above, plus the
  frozen-run test that a schema 2 `MAKE-OPTIONS` run is unchanged.

## Phase 3: make-round (`src/workshop/make/skills/make-round/`, guard, hook)

- **`round_policy` gains a seed input.**
  - A component round whose identity and carry key equal the approval's
    is passed and locked, with `review.carried_from: "seed-approval"`.
  - A different identity is a deviation. It goes to "passed, awaiting
    review" with the ADR 0081 rules from Shape Round 0.
- **Assembly carry.** When every Component carries and the assembly
  identity matches, the assembly review is composed from `CRITIC.json`'s
  assembly verdict and its requirement verdicts, and the blind-review
  requirement is skipped. Any deviation restores the blind review.
- **Kept as is:** `--full`, `--interface`, `--shared-helpers`,
  `--powered`, `--print-gates`.
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
  - Folding in ADR 0085 amendments: unchanged.
- **`DETECT.md`:** unchanged. It reads the contract and Make's gate rows.
  Seed deviations are copied into `notes`.

## Phase 5: pilot and measurement

- **Toy:** the owner's choice; the default is the beaver coasters,
  currently at Stage 4.
- **Measure:**
  - design cost split into Proof, critic, fresh read and coordinator;
  - Make cost against K4's 33.6;
  - seed deviations;
  - gates;
  - the owner's verdict.
- **Success:**
  - Make at or below 12 units with 0 deviations, or every deviation
    traced to a gate;
  - the fresh diff closed before Stage 4;
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
| Fresh read | 1.1-1.7 units, already required | unchanged, plus a free diff |
| **Net per toy** | | **about 15-25 units saved** |

## Risks

- **Proof code a worker must repair.** Mitigated by the production-CAD
  rules in `proof-prompt.md`.
- **The coordinator's context grows.** The critic and the compares stay
  in subagents (PROOF-COST: the coordinator is 55-60% of design cost).
- **Gate or catalogue drift between design and build.** Every gate is
  rerun in the run; a failure is a deviation or a need, never ignored.
- **The approval can be forged by whoever runs the CLI.** Recorded
  honestly in ADR 0096 §3: it is operator input, like the contract.
