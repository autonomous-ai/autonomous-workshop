# ADR 0040: Make proof recovery a sealing handoff

- Status: Accepted
- Date: 2026-08-31
- Supersedes for new runs: ADR 0039's `deep-economics-v11` profile

## Context

Production Quest `wish-20260831-163206-abbea127` produced three visibly distinct
fixed-camera states, but proof recovery repeatedly edited geometry, generated
measurement variants, and rerendered for 13m33s before writing its finding.
A host path bug then rejected the correct marker because evidence lived under
the documented CAD project. After that bug was fixed, the resumed native
session still preferred more final-CAD work over rewriting the marker.

The run also showed why file presence is insufficient: `proof.py` changed after
an earlier state sheet. The session regenerated correctly, but the host did not
deterministically require that freshness.

## Decision

New Forge and Quest runs freeze `deep-economics-v12.md`.

- Proof recovery is a sealing handoff, not a second design turn.
- Complete current evidence goes directly to the finding and exact marker.
- Missing or stale outputs are regenerated from unchanged source first.
- Research, delegation, measurement variants, and aesthetic refinement are
  forbidden before sealing; only a deterministic tool error permits one repair.
- The host resolves exactly one real direct or CAD-project proof directory and
  rejects symlinks or ambiguity.
- V12 marker validation requires generated states to be newer than proof source,
  renders newer than their STL inputs, and the finding newer than the renders.
- V11 and older runs retain their frozen prompts and timing; the corrected
  CAD-project path resolution remains a protocol bug fix.

## Consequences

Early proof can stop once it has answered the direction question. Final Make
retains responsibility for refinement, strict CAD, blind review, and the full
stage finalizer. Freshness checks bind exact bytes without judging aesthetics.
