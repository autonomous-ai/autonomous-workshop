# ADR 0096: The approved Contract Proof is the build, and Workshop certifies it

- Status: Proposed on 2026-11-02 from the owner's direction of the same day.
  Nothing is implemented. The plan is
  [docs/plans/0096-seeded-build-plan.md](../plans/0096-seeded-build-plan.md).
  Open questions are listed at the end and must be answered before any code.
- Date: 2026-11-02
- Amends: ADR 0093 (the Proof sees no image; "a Proof is never a Reference
  Image, and nothing compares it with the model"; the deferred "Proof's CAD
  source as Make's starting skeleton"), ADR 0094 decision 4 (the kept
  Proof reader), and for **seeded runs only** ADR 0075 (where the second
  reader lives), ADR 0076/0077/0080/0081 (Component Workers, the Component
  Reviewer and Shape Rounds) and the assembly blind review of ADRs
  0022/0023/0060.
- Relates to: ADR 0061 (Spark keeps Make's own verification), ADR 0063
  (print gates on the source), ADR 0065/0069 (a correction run starts from
  a source and carries unchanged parts by hash), ADR 0072 (every
  requirement carried), ADR 0082 (Interfaces), ADR 0085 (in-run
  amendments), ADR 0092 (kits), ADR 0095 (powered toys).

## Context

Since ADR 0094 the Contract Proof runs make_round's own print gates on a
project laid out as Make lays one out. Two builds have now been compared
with their Proofs (`toys-spec/_workflow/CONCEPT-DRIFT-standalone.html`,
2026-11-01, measured with OCP on the STEP files):

- **K4 turtle keycap set.** 9 of 9 Components of build v02 match the kept
  Proof to 0.01 mm³ in volume and 0.01 mm in size. The whole set's
  silhouette at ref-01's camera overlaps 99.97%. The only extra material
  is a hidden 9.4 mm³ pocket in the base.
- **NCH cabinet pilot.** 13 of 13 Parts match the Proof in size, volume
  within 0-0.8%.
- **The build adds nothing visible but colour.** What Make adds is
  evidence: motion, the final CAD gate, receipts and the STEP package.
- **Make spent 33.6 cost units on K4 v01** re-typing a model that already
  existed, mostly in component rounds and reviews.
- **The only drift Make caused came from an in-run Manager ruling.** On
  K4 v01 a ruling on a Blocked Report changed the Grumpy and Wink faces
  (ADR 0081's #97 rule then bound the reviewer to it). Fix v02 spent 18
  units, partly to bring the faces back to the Proof.
- **Drift from the concept enters in design, not in Make**
  (CONCEPT-DRIFT Part 2): printability choices taken one detail at a
  time, shapes the Inventor wrote for the mechanism or engraving, and
  references drawn from the contract. No step after Stage 1 compares
  anything with the Concept Image.

`toys-spec/_workflow/PROOF-COST-standalone.html` (2026-10-31) prices the
design side: a whole design costs 16-25 units, 45-65% of one build. A
first Proof build or a fresh read costs 0.7-1.7 units, an amendment to the
kept Proof 0.1-0.5. The coordinator, not the Proof, is 55-60% of design
cost.

On the beaver coaster's arms the owner ran the review this ADR proposes,
live: an independent critic compared the Proof with the references and
the concept, round after round, until it agreed, and only then did the
owner see it at Stage 4.

So the run's most expensive work reproduces geometry the owner has already
approved, and its in-run judgement is the one place that has moved a
build away from it.

## Decision

### 1. The Proof becomes the official build, reviewed in design

- **The kept Proof sees the images.** Its first build stays contract-only,
  so its first `GUESSES.md` lists the contract's real silences. From its
  second round on, the kept Proof receives the Reference Images, Guide
  Images, the chosen Concept Image and its three views, and each Stage 3a
  compare. It models to them, and every number it takes from an image
  becomes a contract amendment the same round: the contract keeps saying
  everything the Proof builds.
- **A Proof Critic replaces the Component Reviewer and the blind review.**
  A fresh subagent that never wrote Proof code compares the Proof with
  each reference at its Reference Camera, with the concept at the concept's
  cameras, and with every requirement row. Rounds go on until it agrees.
  It judges as the Component Reviewer does: differences, Reference
  Conflicts (ADR 0084) and camera mismatch (ADR 0083). One critic thread is
  kept for the design and reused, as ADR 0077 reuses a reviewer, so its
  cache survives.
- **A cap, then the owner.** After five rounds that changed the Proof's
  geometry, the critic's open differences go to Stage 4 as lines under
  their compares, for the owner to decide. Nothing is accepted silently,
  the same rule as ADR 0076's Component Acceptance, with the owner as the
  decider instead of the reviewer.
- **The critic writes a record.** `proof/CRITIC.json`: per round, per
  Component and for the assembly, the verdict, each difference, and the
  hashes of the Proof sources and compare images it judged. Its last round
  carries one verdict per requirement id, which is what ADR 0072 needs.
- **One fresh contract-only read stays, and is measured.** Once the critic
  agrees, one fresh Proof subagent that has seen no image builds the final
  contract, as ADR 0094 decision 4 has it. A script then compares its
  STEP with the kept Proof's, Part by Part, by volume, bounding box and
  two-way Boolean difference (the method of CONCEPT-DRIFT Part 1). Any
  difference over tolerance is a silent gap in the contract: something
  the kept Proof built from an image that the words never say. It is
  closed in the contract before Stage 4. This matters more than before:
  a fix run, DETECT and every later amendment read the contract, not the
  Proof's code.
- **The owner's approval is the acceptance record.** Stage 4 shows the
  owner each reference beside the Proof, the concept beside the Proof, and
  the critic's open lines. On approval, Stage 5 writes
  `proof/APPROVAL.json`: the contract's sha256, the Proof tree's manifest
  (every source file's sha256), each Component's B-rep identity and carry
  key as make_round computes them, the assembly identity, the
  `CRITIC.json` hash, the fresh-read diff's hash, the make_round tool hash
  the gates ran under, the nozzle, and `approved_by: owner` with the date.

### 2. A seeded run certifies and packages

- **`--seed-source DIR`** on `workshop wish` and `workshop fix`, only with
  `--contract`, only on Spark. The host refuses it unless `DIR` holds an
  `APPROVAL.json` whose contract hash is the sealed contract's and whose
  manifest matches every file in `DIR`. It seals the Proof tree with the
  Wish as an immutable input, as `fix` seals its source archive (ADR 0065),
  and freezes `seed` into `MAKE-OPTIONS.json` (a new schema). No resume
  can add or drop it.
- **The run starts from the Proof's project.** Its `params.py`,
  `features/` and every `part_<id>.step.py` become Make's project. The
  Shared Helpers are frozen as ADR 0082 freezes them, after their samples
  pass.
- **An approved Component carries its approval.** Each component round
  builds and gates the Component as today. When its B-rep identity and
  carry key equal the ones in `APPROVAL.json`, the round carries the
  design approval as its review (`review.carried_from: "seed-approval"`),
  the way ADR 0081 carries a review forward. No Component Worker is
  spawned, no Component Reviewer is asked, no Shape Round is counted.
- **The assembly carries it too.** When every Component carries and the
  assembly identity equals the approved one, the assembly review is the
  critic's assembly verdict and its per-requirement verdicts. The blind
  review does not run.
- **What the run still does, unchanged:** host-verified bytes and hashes;
  the print gates at the frozen nozzle in each component round and in
  `verify_project --print-gates` for a print-ready claim; every Coupled
  Interface check and separable Keep-out Envelope (ADR 0082); the motion
  check (`--check-motion`); `--powered` and the host's power-report check
  (ADR 0095); Bought Parts; mesh, interference and insertion (ADR 0088);
  `make_round --full`; STEP export; Print Sheets; the kit Manual; README;
  receipts; DETECT; publication. A gate never trusts the design's own run
  of it: every gate runs again in the run on the sealed bytes.
- **Fix rounds stay for real defects.** If a gate, Interface, motion or
  power check fails in the run, the Manager may change the Component.
  The changed Component loses its carried approval and goes through
  today's path: one Component Worker and one Component Reviewer (ADRs
  0077/0080/0081), Shape Rounds counted. The receipt and `workshop status
  --json` list it as a **seed deviation** with the gate that forced it.
- **No in-run rulings on the approved shape.** A seeded run raises no
  Blocked Report about shape and makes no Manager ruling on one. A
  Contract Contradiction stops the run with a need. `build-a-toy` answers
  it in design: the kept Proof, the critic, the owner if visible, a new
  `APPROVAL.json`, then `workshop fix --seed-source`. ADR 0085's in-run
  amendment stays available for an invisible fix.
- **The receipt says where acceptance came from.** `seed: {approval_sha256,
  proof_manifest_sha256, critic_sha256, deviations: [...]}`, and the
  run report prints "approved in design by the owner on <date>; N
  Components certified unchanged; M deviations".

### 3. Where independence and trust now live

AGENTS.md says model prose and self-scores are proposals, and only
host-verified bytes, deterministic checks and reconciled receipts advance a
gate. ADR 0075 required a second reader besides the Manager for any
Component acceptance. Under this ADR:

| What | Who | What the host can verify |
|---|---|---|
| The geometry is what was approved | host | sha256 of every seed file against `APPROVAL.json`; B-rep identity of every built Component against the approved identity |
| It prints, moves, is powered, fits | host-run deterministic gates | the same gates as today, rerun in the run on the sealed bytes |
| It looks like the references and the concept | the Proof Critic (fresh, never wrote Proof code), then the owner | only that `CRITIC.json` and `APPROVAL.json` bind the exact Proof hash the run built; not the judgement itself |
| The contract says what the Proof builds | the fresh contract-only read and its STEP diff | the diff report's hash in `APPROVAL.json` |
| A changed Component still looks right | the Component Reviewer, as today | as today (ADR 0081 and its #77 extension) |

- **The second reader is stronger, not weaker.** Before, the second
  reader was one low-effort model per Component. Now it is a fresh critic
  plus the owner, the only reader whose acceptance is not a proposal.
- **What gets weaker.** The host cannot prove that a critic ran, that it
  was fresh, or that the owner approved. `APPROVAL.json` is operator
  input, like the contract and the reference images already are: the
  operator who runs `workshop wish --seed-source` vouches for it. The host
  verifies only that the approval binds the exact bytes it builds. Today's
  in-run reviewer evidence on Claude Code (ADR 0081 #77: the guard saw the
  reviewer start and read every image) has no equivalent in design. The
  receipt must therefore say "approved in design", never "reviewed in
  run".
- **Model judgement is still only a proposal.** The critic's agreement
  only lets the design reach Stage 4. Two things advance the build: the
  owner's approval and the gates the host reruns.

### 4. Compatibility and lifecycles

- **Unseeded runs, frozen runs, schemas 1-10:** unchanged. Every run
  without `seed` keeps workers, reviewers, the blind review and all
  current rules. Frozen runs keep the tool bytes they materialized.
- **Spark:** the only lifecycle that accepts a seed. ADR 0061 holds: the
  host does not rerun the verifier. It checks the seed binding and reads
  Make's sealed records, as ADR 0095 reads the power report.
- **Forge:** refused. Invent would create a concept that the sealed Proof
  already fixes.
- **Quest:** refused for now. Playtest could later follow a seeded Make
  unchanged; that needs its own decision.
- **Runtimes:** the seeded path needs no reviewer evidence from the
  runtime, so Codex and Claude Code behave the same. This also ends the
  Codex/Claude split of ADR 0081 #77 for seeded runs.
- **`workshop fix` of a seeded toy:** with a new `--seed-source`, unchanged
  Components carry by STEP hash (ADR 0069) and changed ones carry the new
  approval. Without one, the fix runs today's path.

## Considered options

- **Seed Make but keep workers, reviewers and the blind review**
  (CONCEPT-DRIFT option 3). Saves an estimated 10-20 units per build and
  keeps in-run review evidence. Rejected as the default: the reviewers
  would re-judge geometry the owner approved, and a reviewer or ruling
  is the one in-run step that has moved a build away from it (K4 v01).
- **Drop the fresh contract-only read** now that the build no longer
  depends on the contract's words. Not recommended. Fix runs, DETECT and
  amendments still read the contract, and a kept Proof that sees images
  will fill silences from them. One read is about 1.3 units, and its diff
  is deterministic.
- **Seal the concept as a Make reference** (CONCEPT-DRIFT option 7).
  Rejected there and here: the contract wins, so a sealed concept only
  produces Reference Conflicts.
- **Have the host rerun a model critic in the run.** Rejected. It would
  be a Python-owned model judge, which AGENTS.md forbids, and the same
  re-review this ADR removes.
- **Ship the Proof without rerunning gates in the run.** Rejected. Gate
  code and catalogues can change between design and build, and the host
  needs its own run of every gate.

## Consequences

- **Cost moves from Make to design.** Make keeps only certification and
  packaging. Estimate, not yet measured: a seeded K4-sized build costs
  about 6-12 units instead of 33.6. Design gains about 1-2.5 units of
  critic rounds and image-aware Proof rounds. Net about 15-25 units saved
  per toy, plus the drift fix rounds avoided (K4 v02 was 18 units).
- **Design cost leaves Workshop's token accounting.** design-a-toy runs
  outside the host, so `--max-tokens` and the run's TOKENS no longer cover
  modelling. `APPROVAL.json` carries the design's measured cost for
  information only.
- **The Proof's code quality now ships.** The Proof prompt must ask for
  production CAD: the print-details library, true arcs rather than faceted
  engraving (K4's heads had 123-253 faces against Make's 45-51), and
  readable helpers. A worker that must repair a seed deviation edits code
  it did not write.
- **design-a-toy becomes heavier and more important.** Its coordinator
  context is already the largest design cost. The critic and the compares
  must stay in subagents.
- **Kits and powered toys:** the Proof already writes `print_parts()`
  (ADR 0092). The Manual, Print Sheets and the power report stay Make
  work.

## Open questions for the owner

1. Is the critic's cap five geometry-changing rounds, with open lines
   going to the owner at Stage 4? Or does it run without a cap until it
   agrees, as on the beaver arms?
2. One critic thread for the whole toy, or one per Component plus one for
   the assembly? The second is closer to today's reviewer and costs more.
3. Should the critic also hold a Concept Checklist (CONCEPT-DRIFT
   solution 1), or only the concept image at its cameras?
4. A seed deviation that is visible: should it stop the run and return to
   design, or go through the in-run Component Reviewer as proposed?
5. Fresh-read diff tolerance: is the proposed 1% volume per Part and
   0.1 mm per bounding-box side right? (The cabinet's Make-vs-Proof spread
   was 0-0.8%.)
6. Pilot toy: the beaver coasters (at Stage 4 now), or a rebuild of K4 as a
   measured A/B?
