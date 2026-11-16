# ADR 0094: One print gate, a kept Proof reader, and no duplicate reads

- Status: Accepted by the owner on 2026-10-28 (proposals B, C, D and E of
  `toys-spec/_workflow/SIMPLIFY.html`), and decision 7 on 2026-10-29. All
  seven decisions are implemented
  on branch `workflow-simplify` with deterministic tests: decision 1 as
  `make_round --print-gates-only`, decision 6 in the Make finalizer,
  `verify_project` and the product-run files. Nothing is validated by a
  live run yet.
- Date: 2026-10-28
- Amends: ADR 0093 (the Proof's print gates and its rounds), ADR 0072 and
  issues #54/#55 (geometry blind reads), `design-a-toy` Stages 3b, 3c and
  3e, `build-a-toy` DETECT.md
- Relates to: ADR 0061 (Spark keeps Make's own verification), ADR 0076 (no
  IoU), ADR 0077 (Component Reviewers), ADR 0092 (kit Parts gated alone)

## Context

The owner found the design-to-build workflow too heavy. A cost map built
from real transcripts (cost units: fresh input 1, cache write 1.25, cache
read 0.1, output 5) found:

- **Proof cost.** Each Contract Proof round costs about 4-5M tokens, 1.1
  cost units and 17-23 minutes. The harness's "~175k subagent tokens" was
  the final context only. The ADR 0093 cabinet pilot ran nine rounds, about
  9.7 units, and rounds 4 to 6 found no real defect. Its whole design phase
  cost about 31 units, against 50 for the complete Night Charms Hall build.
- **Two print gates.** The Proof called the CAD gates itself. Make gated
  through make_round with its own context. The cabinet's first build
  stopped after three component rounds (about 9 units) because the Proof
  had gated each kit Part flat while Make gated the assembled Component.
- **Two overhang limits.** `design-a-toy` Stage 3c and its audit asked for
  52 degrees. The gate fails below 45. The pilot's audit flagged three
  faces at 45-48 degrees that the gate passes.
- **Two acceptance rules.** DETECT still scored silhouettes at IoU 0.90
  and measured walls against `wall_min_mm`. Make has done neither since ADR
  0076: it gates every wall at the nozzle's print minimum. Night Charms
  Hall completed, accepted by Make, and DETECT raised 17 findings: 8
  likeness, 6 walls unverified, 3 extents.
- **Duplicate design checks.** Stage 3e's claims, lint and audit added no
  real defect in the 0093 pilot that the Proof and its compares had not
  shown. Its lint raised two false errors on Print Pieces. Stage 3b's
  hand-measured aspect, landmarks, masses, dimensioned features and outline
  repeat what the Proof overlay shows.
- **Duplicate component reads.** The blind critic's `geometry_blind_reads`
  re-read each Component sheet its Component Reviewer had already judged.
  The rule predates the Component Reviewer by five days (2026-09-24 against
  ADR 0077, 2026-09-29).
- **Instruction weight.** The files a Spark Make root re-sends on every
  turn hold about 31k tokens. Some of that is text for frozen runs, older
  schemas, Forge/Quest and fix runs. Some rules are written in three or four
  places.

## Decision

1. **One print gate.** The Contract Proof runs make_round's own gate code,
   in a mode that needs no Workshop run, on its project laid out as Make
   lays one out. A contract whose Proof passes cannot fail Make's gates for
   a reason the Proof never measured. The Proof's "At the limit" list also
   names every face designed between 45 and 52 degrees.
2. **45 degrees is the only overhang limit.** 52 is the print-details
   library's design margin: the facets of a face designed exactly at the
   limit can land past it. `design-a-toy` gives margin where it changes
   nothing a reference shows, and refuses nothing between 45 and 52.
3. **Detection reads Make's results.**
   - DETECT drops its likeness layer and its `wall:<geometry>` check.
   - `print:<geometry>` reads the final verification's `check_mesh`,
     `check_overhang` and `check_thickness` rows in `CAD-GATE.json`.
   - Component Acceptances and Reference Conflicts are copied into `notes`,
     never into findings.
   - Envelope, extents, count, motion and requirement rows stay.
4. **A kept Proof reader and one fresh read.**
   - One Proof subagent is kept for the whole design, and every amendment
     goes to it.
   - One fresh Proof subagent reads the finished contract before Stage 4.
   - Another fresh read runs only after a change of shape, size or
     position, never after a change of words alone.
   - `build-a-toy` root amendments run the Proof too.
5. **Design checks go through the Proof.**
   - Stage 3e (claims, lint, audit) is removed. The Proof reports a fact
     stated twice with two values as a contradiction, and lists placement
     failures.
   - Stage 3b reads outline, landmarks, masses and counts off the Proof
     compares. It keeps four checks: the Reference Camera, joint features,
     Part colours and visible faces.
   - Stage 3c starts from the Proof's gates and keeps the human's
     fine-detail choices, the placement rules and the resolution order.
   - The ceiling-over-a-moving-part check moves to Stage 3d with the other
     motion checks.
   - `contract_lint.py` stays for the kit tree and the host parser.
6. **No duplicate reads in Make, new runs only.**
   - A geometry-scoped requirement row is bound to its Component's current
     passing packet and to that Component's recorded agreeing review or
     Component Acceptance, quoting the review's reason, without a separate
     blind critic read. A geometry whose review is not proven (no bound
     reviewer, as on Codex, or an older run) keeps its blind read. The
     assembly blind review is unchanged.
   - Text that serves only frozen runs, older schemas, Forge/Quest or fix
     runs moves out of the files a new Spark Make reads on every turn.
   - Each repeated rule keeps one home. The short forms in the product-run
     AGENTS.md stay, because only that file survives every compaction.
   - The text no longer says the host reruns the verifier for Spark.

7. **No `wall_min_mm` in new contracts** (owner, 2026-10-29).
   - `wall_min_mm` came with ADR 0072 (2026-09-24) so that DETECT could
     hold each geometry's thinnest wall to it. Make never measured it: it
     gates every wall at the nozzle's print minimum. The only other use was
     the step size of a kit's insertion sweep.
   - Design Contract schema 9 is schema 8 with `wall_min_mm` refused on
     every geometry. `design-a-toy` writes every new contract as schema 9.
   - A schema 9 kit's insertion sweep samples at two print lines (0.8 mm at
     a 0.4 mm nozzle).
   - A section that must be thicker for strength says so in its
     requirement rows.
   - Schemas 1 to 8 and frozen runs keep what they sealed.

## Considered options

- **Keep-alive pings or a one-hour cache (proposal A).** Re-pricing the
  Hall transcripts gave these results:
  - Keep-alive pings: 2.5 units (5%) cheaper, but about 14M more tokens
    counted against the run's token budget.
  - A one-hour cache: 1.5 units dearer.
  - For design, either would save 5-6 units.

  The owner declined both as not worth it.
- **The Proof's CAD as Make's skeleton.** Still deferred (ADR 0093) until a
  pilot build gives numbers.
- **Reusing print-gate results across scopes.** Rounds already reuse a
  passing gate within one scope: component round to component round,
  assembly round to assembly round, and a final sweep that did not change.
  They do not reuse it from a component round into the first assembly round
  or the final verification. Night Charms Hall's final verification spent
  554 of its 1656 s re-measuring print gates. That costs wall-clock time,
  not money, and the owner rejected the change as not worth it (2026-10-29).
- **Component references edited from the Proof render by default
  (proposal F).** Pending. On the cabinet the edited images kept every
  ornament the free drawings had, and added surface detail. They lost only
  what the contract decided against. But the cabinet is one toy of box
  shapes. The owner will try it on an organic shape, the K4 turtle keycap's
  `design-a-toy` run, before it becomes the default; until then it stays
  the trial of ADR 0093.

## Amendment 2026-11-16: the Proof checks interference as the assembly round does

- **Gap.** An assembly round and final verification run `inspect interfere`
  on the assembled object (issue #118). Any two printed bodies whose
  boolean intersection is over the cad skill's 1.0 mm3 tolerance fail,
  named by pair, volume and place. The check runs in every Workshop run,
  seeded or not: the seeded batch's assembly round runs it too.
  `--print-gates-only`, the Contract Proof's gate, ran only per-Component
  checks. The Kyoto Gion Proof (round 20) therefore passed every gate while
  holding three collisions, which a hand-written scan found: a roof eave in
  two stone lanterns (30 and 5 mm3), the same eave in a wall and its cap
  (11 and 24 mm3), and a lantern in a deck rail (41 and 12 mm3). Its seeded
  run's assembly round would have failed, after the owner had approved the
  Proof.
- **Decision.** `make_round --print-gates-only` on the whole project now
  runs the same `inspect interfere` job on the assembly entry (the one
  non-part `*.step.py`, or `--entry`), after every part builds. It uses the
  same parser and passing verdicts as the round: `pass`, or `unverified`
  when its time allowance ran out with nothing found. A clash, an entry
  that cannot build for it, or a part that did not build fails it. The
  summary records `interference` and adds `interfere` to its `checks`.
  `seal_proof.py` refuses a summary without `interfere` and names a failing
  clash. A `--component` run, or a project with no single assembly entry,
  checks no assembly and does not claim the check.
- **Same tolerance, no exemption list.** The Proof's check is the round's
  check, so the Proof never passes what its build then refuses:
  - The tolerance is the cad skill's 1.0 mm3. The Kyoto collisions were 5
    to 41 mm3, and touching faces leave slivers under it.
  - No pair is exempt. A declared fit cut with its clearance (fixed +0.1,
    moving +0.2 total) leaves a gap, so it passes without one; `check_fit`
    and the Interface checks still own its size. A pair that truly
    interpenetrates by design, such as a press fit, already fails the
    run's assembly round. Exempting it only in the Proof would let the
    owner approve a build that cannot pass. Such a toy needs its own
    decision on the round's check; this amendment changes neither gate.
- **Where it runs.**
  - Contract Proof: `make_round --print-gates-only`, which `seal_proof` requires.
  - Every Workshop run: the assembly round, unchanged.
  - Final verification: `verify_project`'s inspect batch, unchanged.

  Frozen runs keep their materialized make_round bytes.
- Implemented with deterministic tests, plus real B-rep tests: an overlap
  fails naming both bodies and 200 mm3, while touching bodies and a 0.1 mm
  gap pass. No live Proof has run it yet.

## Consequences

- A design costs fewer Proof rounds and no Stage 3e subagents.
- Design and Make share one gate.
- `build-a-toy` stops raising findings Make never optimised for.
- Older contracts and frozen runs keep what they sealed and materialized.
