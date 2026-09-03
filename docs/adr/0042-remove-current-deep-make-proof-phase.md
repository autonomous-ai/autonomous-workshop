# ADR 0042: Remove the early-proof phase from current deep Make

- Status: Accepted
- Date: 2026-09-03
- Owners: Runtime, Workflow, Make, product-run instruction, and quality-economics maintainers
- Relates to: ADR 0037 (256k deep compaction)
- Supersedes for new runs: ADR 0030's proof-first deep Make, ADR 0033's proof checkpoint, ADR 0038's proof-to-source handoff, and ADR 0041's current-profile proof-resume routing

## Context

The phased Forge/Quest Make path was introduced when short native context
windows and setup-heavy turns frequently ended before durable CAD existed. ADR
0037 later raised every deep stage's automatic-compaction ceiling to 256,000
tokens, but the separate proof turn, marker, private receipt, and source
handoff remained.

Two later Ho Chi Minh City landmark-chess runs exposed a different failure.
The rushed proof used simple generic shapes, and the final-source instruction
required those shapes to be reused. The proof therefore stopped being merely
liveness evidence and became an accidental visual-design anchor. Main has no
separate Concept phase: Forge and Quest pass a sealed `NativeInvented` JSON
contract from Invent to Make.

## Decision

New Codex Forge and Quest runs freeze `deep-economics-v14.md`. They retain one
Wish-wide session, one Goal per stage, index-first Invent, its 20-minute high
turn and 10-minute medium source-finalization recovery, 256k compaction,
medium later stages, normal bounded recovery, and the eight-turn invocation
cap.

Make starts directly at high reasoning with the normal 60-minute native-turn
boundary. It reads the exact Wish, sealed Invent result, Inventor guidance,
Make reference, and CAD skill in one bounded batch, then persists a coherent
complete self-contained CAD baseline early. It may create a narrow engineering
coupon, but no host phase requires a generic blockout to become final geometry.

V14 Make does not create or consume `review/early-proof/`,
`.make-proof-ready.json`, a proof-acceptance receipt, a 16-minute medium proof
turn, or a 15-minute proof-to-source handoff. It uses the ordinary
checkpoint-bound `agent-outcome.json` finalization marker from its first turn.
Recovery continues the exact same session, stage, Goal, packet, and durable
product bytes.

Every authoritative final boundary remains: accepted-Invent binding, complete
inventory, fit, mesh, 0.4 mm wall thickness, exact-state evidence where the
Wish needs it, final hash-bound blind review, integrated verification, Quest
Playtest, PDF manual validation, authenticated Factory publication, and
snapshot integrity.

Deep-v13 and older markers remain immutable historical capabilities. The host
keeps their proof discovery, validation, marker, receipt, timeout, handoff,
recovery, and explicit-resume behavior so existing runs remain resumable.

## Alternatives considered

### Keep the proof turn but stop requiring source reuse

Rejected for this experiment. It would retain the extra turn and handoff costs
and would not test whether the phase became obsolete after 256k compaction.

### Delete proof handling globally

Rejected. Existing checkpoints can be before or after proof acceptance and
must resume their frozen protocol exactly.

### Add a host-side visual score

Rejected. Semantic and aesthetic comparison remains native-agent work over
exact renders. The host continues to verify contracts, hashes, and declared
evidence rather than interpreting visual quality.

## Consequences

- Current deep Make gets one uninterrupted high-reasoning path from the Invent
  handoff to exact final-product evidence.
- Liveness relies on early complete-source guidance and ordinary bounded
  recovery rather than a special proof marker.
- A new same-Wish run must determine whether quality actually improves; the
  architecture change alone is not evidence of improvement.
- Reverting which profile new runs receive must not remove v14 recognition,
  because any already-created v14 run remains bound to it.

## Verification

- Profile and launcher tests prove v14 uses high reasoning, 256k compaction,
  60-minute Make turns, `agent-outcome.json`, and no proof receipt.
- Frozen v13, v12, v10, and older tests retain their exact proof semantics.
- Mock-session Forge and Quest traces contain one direct Make phase and reject
  fabricated proof state.
- The exact prior HCMC landmark-chess Wish is rerun and compared with both
  proof-phased baselines using exact final renders and complete available
  timing/token telemetry.
