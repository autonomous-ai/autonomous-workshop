# ADR 0094: One print gate, a kept Proof reader, and no duplicate reads

- Status: Accepted by the owner on 2026-10-28 (proposals B, C, D and E of
  `toys-spec/_workflow/SIMPLIFY.html`). Decisions 3 to 5 are implemented
  in `design-a-toy` and `build-a-toy`. Decisions 1, 2 and 6 are
  implemented on branch `workflow-simplify`; see the commits that cite
  this ADR. Nothing is validated by a live run yet.
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
   - `wall_min_mm` remains in the schema for the kit insertion sweep's step
     size. Whether a contract should state it at all is left open for the
     owner.
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
     Component Acceptance, without a separate blind critic read. The
     assembly blind review is unchanged.
   - Text that serves only frozen runs, older schemas, Forge/Quest or fix
     runs moves out of the files a new Spark Make reads on every turn.
   - Each repeated rule keeps one home. The short forms in the product-run
     AGENTS.md stay, because only that file survives every compaction.
   - The text no longer says the host reruns the verifier for Spark.

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
- **Component references edited from the Proof render by default
  (proposal F).** Not decided; the owner asked for a comparison of detail
  first.

## Consequences

- A design costs fewer Proof rounds and no Stage 3e subagents.
- Design and Make share one gate.
- `build-a-toy` stops raising findings Make never optimised for.
- Older contracts and frozen runs keep what they sealed and materialized.
