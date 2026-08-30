# ADR 0023: Bound Spark turns and review the promised relationship

- Status: Accepted
- Date: 2026-08-30
- Owners: Runtime, Workflow, Make, product-run instruction, and CAD skill maintainers
- Relates to: ADR 0019 (Spark economics), ADR 0020 (signature evidence), ADR 0021 (Spark compaction), ADR 0022 (blind review)
- Supersedes for new runs: ADR 0022's schema-v2 signature review and Spark v2's one-hour native-turn boundary

## Context

Moonwake Turn tested the blind-review-first workflow in a real published Spark
run. It completed in 1 hour 20 minutes 45 seconds. Its telemetry recorded
4,040,564 input tokens, 29,364 output tokens, and two measured turns out of
three. Those numbers are a floor, not a total: the first Make turn exhausted
the old one-hour launcher boundary without emitting a terminal usage event.
The recovery turn reused the same checkpointed session and completed Make, but
the missing turn makes a claimed 83.6% reduction from Moonchase Fox invalid.

The run also showed that prompted work order was insufficient. The Manager
repeated broad build, export, render, and verification activity inside one
native turn before finalization. One stage attempt therefore hid many costly
inner cycles. The final manual was excellent, but the product still missed the
Wish's exact semantic relationship: the Wish required a whale leaping
*through* a crescent moon, while the blind critic recorded a crescent moon
*beside* a whale-like animal. Schema v2 asked whether the overall signature was
unmistakable, so shared nouns could pass despite a wrong action or relationship.

Quality and economics remain conjunctive. The response cannot be a shorter
turn that waives proof, nor a stronger review that permits unbounded rebuilds.

## Decision

New Codex Spark runs freeze `references/spark-economics-v3.md`. They retain low
reasoning effort and the 64,000-token automatic compaction ceiling, and add a
20-minute boundary to each native Make or Release turn. A timeout still reaps
only the current launcher process and resumes the exact checkpointed session,
stage packet, Goal, and workspace through the existing bounded recovery path.
It does not create another session, finish a stage, or waive a gate. The limit
is per native turn, not a promise that the whole stage or run finishes in 20
minutes. The non-default timeout is included in the private Codex runtime-policy
hash; changing it on resume fails closed. Historical default-timeout sessions
retain their prior hash shape.

The v3 work order is explicit: establish one real candidate, use narrow checks,
obtain one bounded blind review, perform at most one coherent visual repair,
run one integrated final verifier, and finalize before the turn boundary.
Existing exact bytes are durable work; a recovery turn must finish the missing
critical path rather than restart exploration or regenerate passed artifacts.

New Make finalizers require schema-v3 `SIGNATURE-REVIEW.json`. One independent
native critic receives only the exact final candidate images and records these
unprompted reads separately:

- the held object;
- the subjects;
- the action or transformation; and
- the spatial or causal relationship between the subjects.

Only after those reads are preserved does the same critic receive the exact
Wish and compare subjects, action, and relationship separately. Matching nouns
is insufficient: `beside` is not `through`, a static fish is not a leaping
whale, and a sequence of camera angles is not a state change. One critic may
perform at most two review rounds: the initial blind read and, after one focused
repair, one blind rereview.

The materialized CAD `verify_project` tool enforces the cost order. Every real
final-mode invocation requires the canonical schema-v3 review and verifies its
exact image hashes before running geometry work. `--quick` iteration and
`--dry-run` planning remain available before review. A successful final report
records the exact review hash. This deterministic boundary validates structure,
ordering, declarations, and bytes; it does not interpret imagery or become a
Python aesthetic judge.

## Alternatives considered

### Count the partial Moonwake telemetry as the new baseline

Rejected. A missing one-hour turn can only make the actual total larger. Partial
telemetry is useful as a measured floor, never as proof of a reduction.

### Add more critics or a host-side vision score

Rejected. More critics add spend, and a Python-owned semantic judge violates
the native-agent boundary. One bounded native critic provides the cognitive
read; the host checks exact evidence and stopping conditions.

### Trust instructions to delay final verification

Rejected. Moonwake demonstrated repeated expensive work inside one attempt.
The deterministic verifier must refuse the expensive path until review evidence
exists.

## Consequences

- A runaway Spark turn loses at most 20 minutes before bounded same-session
  recovery rather than one hour.
- The public evidence distinguishes a correct object with the wrong verb or
  relationship from a faithful signature experience.
- Make cannot use the complete verifier as its visual iteration loop.
- Frozen v1, v2, and unmarked Spark runs retain their original timeout,
  compaction, review schema, and materialized verifier bytes.
- The 2,461,602-input-token whole-run target remains unproven until a new
  permanent production Spark has complete telemetry and wins a blind product
  comparison. This ADR narrows spend; it does not declare the economics goal
  achieved.

## Verification

- Workflow tests prove v3 Spark selects low reasoning, 64k compaction, and a
  1,200-second timeout while v2, v1, Forge, and unmarked runs retain prior
  policy.
- Finalizer tests reject schema-v3 reviews with false subject, action, or
  relationship agreement, stale image hashes, or more than two rounds.
- CAD tests prove a final run without the review refuses before `check_layout`,
  while quick and dry-run paths remain available.
- CAD self-check and skill-lock tests bind the revised final verifier.
- A permanent production challenger must provide complete per-turn telemetry,
  stay at or below 2,461,602 gross input tokens, pass every deterministic gate,
  and be strongly preferred for its exact signature experience before the
  combined quality-and-economics objective is achieved.
