# ADR 0039: Make Invent recovery a source handoff

- Status: Accepted
- Date: 2026-08-31
- Owners: Runtime, workflow, and product-run protocol maintainers
- Supersedes for new runs: ADR 0038's `deep-economics-v10` profile

## Context

Production Quest `wish-20260831-153128-dde436ba` exhausted its 20-minute Invent
turn and 10-minute medium recovery without a proposal. The recovery wrote a
30,018-byte `invent-source.json` only 71 seconds before timeout. That exact
source passed the deterministic finalizer in an isolated copy in 0.2 seconds;
a normal operator resume then finalized and passed Invent in 3m34s.

The existing recovery instruction already prohibited renewed exploration and
said to finalize immediately. It still permitted enough interpretation that
Codex spent almost the complete recovery synthesizing a large source before its
first durable write. The bounded recovery needs an exact action order.

## Decision

New Forge and Quest runs freeze `deep-economics-v11.md`.

- Invent retains its initial 20-minute high-reasoning turn, compact complete-
  roster index, top-three full-agent reads, and 10-minute medium recovery.
- Recovery is a source handoff, not a creative continuation.
- Its first action checks only whether `work/invent-source.json` exists.
- Existing source goes immediately to the exact Invent finalizer before reads,
  edits, plans, research, child waits, review, or refinement.
- Missing source is written in the first file edit from the strongest decision
  already in context; the next action invokes the finalizer.
- Only a concrete deterministic finalizer error authorizes a focused repair.
  The remaining time is repair reserve.
- V10 keeps its exact original recovery. V11 otherwise preserves v10's 256k
  compaction, exact-state Make proof, final-source handoff, and every gate.

## Consequences

Recovery may seal a less polished concept than another long synthesis pass, but
it only runs after the full high-reasoning Invent allowance. A durable,
contract-valid concept can proceed to Make and be tested against exact evidence;
an unfinalized concept cannot. The host still does not choose or score the
concept, write model output, or waive the Invent gate.

Tests bind v10 compatibility, v11 profile selection, action-first recovery,
the unchanged Make proof and final-source boundaries, and 256k compaction. A
fresh production run remains required to measure the economic effect.
