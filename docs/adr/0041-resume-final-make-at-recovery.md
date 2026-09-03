# ADR 0041: Resume final Make at recovery

## Status

Accepted — 2026-08-31.

## Context

Production Forge `wish-20260831-182830-9cbbe7b0` validated v12's proof
sealing: proof recovery reached its marker in 2m26s instead of v11's 13m33s.
Final Make then wrote a complete source tree and reached print preflight. Two
recoverable turns stopped before a proposal, so the operator used the normal
CLI resume.

That new invocation forgot the in-memory continuation flag. Although the valid
proof marker and final source remained durable, Workshop replayed the
15-minute source-handoff profile before allowing normal 30-minute recovery.
The same session spent that replay repairing already-authored CAD. This was
bounded and safe, but needlessly expensive.

The run also exposed a bad interaction between aggressive context economy and
specialist guidance. Final recovery prohibited every optional CAD reference.
When fixed preflight reported shell thickness failures, Codex repeatedly made
scalar geometry changes and regenerated the product. The CAD skill already
contains the exact constant-wall and all-regions repair method in
`references/print-optimisation.md`, but the recovery prompt forbade reading it.

## Decision

New Forge and Quest runs freeze `deep-economics-v13.md`.

- The first final-Make continuation after proof still receives the 15-minute
  source handoff, followed by normal 30-minute recovery.
- An explicit `workshop resume` on a checkpointed v13 Make Goal with a valid
  proof marker starts directly in normal recovery. It resumes the same native
  session and immutable stage; no new Goal or gate is created.
- Final recovery still rejects unrelated reference browsing. If the current
  fixed preflight specifically fails wall thickness, Codex reads the complete
  saved region table and the one print-optimisation reference before one
  source repair. It repairs all reported regions together and uses
  constant-wall shell construction instead of blind scalar probing.
- Frozen v12 and older runs retain their materialized policy.

## Consequences

Manual resume no longer pays a second 15-minute final-source phase. Specialist
context remains progressive and evidence-triggered rather than always loaded.
No quality threshold changes: strict fit, mesh, 0.4 mm thickness, exact-state
rendering, blind review, integrated verification, Playtest where selected,
publication readback, and GitHub snapshot integrity remain mandatory.

This is host turn selection plus native-agent instruction. It does not add a
Python repair loop, model judge, prompt chain, or second agent runtime.
