# ADR 0038: Prove product states and bound the final-source handoff

- Status: Accepted
- Date: 2026-08-31
- Owners: Runtime, workflow, Make tooling, and product-run protocol maintainers
- Supersedes for new runs: ADR 0037's `deep-economics-v9` profile

## Context

The production Quest `wish-20260831-123720-43b4ec40` validated v8's liveness
fix: early Make authored source in 5m44s and completed its proof marker in
12m14s, whereas v7 authored no Make source in two turns. It then exposed two
new defects.

The early root review accepted a three-frame signature sheet even though all
frames showed one unchanged mesh from nearby camera angles. Final Make repeated
that mistake. The promised three skies were not visually distinguishable.
`render_product --motion-sheet` truthfully rotates one mesh for presentation;
the workflow had incorrectly treated those poses as mechanism-state evidence.

After the proof marker, final Make spent its entire first 30-minute high turn
reading references and searching assembly/tool APIs. It authored no final
product bytes. Recovery wrote the complete baseline about 9m30s later, but the
remaining time ended on strict fit failures: an upper shell below the print
datum, disconnected bodies, and no project fit audit. The product remained
unpublished. Root plus its small Inventor child used about 1.60M input tokens
(about 336k uncached) and 25.2k output tokens.

Invent also dumped and reread all fourteen full custom-agent TOMLs before
shortlisting. The exact Taste header already contains the name and bounded
description needed for cheap first-pass routing.

## Decision

New Codex Forge and Quest runs freeze `deep-economics-v10.md`, retaining v9's
256k automatic compaction ceiling.

- `STAGE.json` includes a deterministic compact discovery index derived from
  every bound Inventor's exact Taste header. Invent ranks the complete index
  and reads only the best three full custom agents before selection.
- Early Make retains the 16-minute medium source-first runway, but authors one
  shared proof helper and three exact product-state entries.
- `render_product --state-sheet` renders two to five exact state STLs from one
  fixed camera and rejects visually indistinguishable frames. Motion sheets
  remain available only as viewpoint presentation of one unchanged mesh.
- The host accepts v10's proof marker only when the helper, three state sources,
  three STEP files, three distinct STL files, held image, state sheet, and root
  finding are stable regular files in the current round.
- The first high final-Make continuation has a 15-minute source-handoff
  boundary. Its first bounded read contains the proof, current contracts, and
  CAD skill; the next action must persist complete final product source.
  Optional references, API searches, helper rediscovery, and planning calls
  wait until source exists.
- If that boundary expires, normal 30-minute recovery resumes the exact Goal
  and durable bytes. All final CAD, review, Playtest, manual, publication, and
  GitHub requirements remain unchanged.

## Consequences

The early proof now spends modestly more deterministic CAD work to answer the
right visual question. It prevents an unchanged object from passing as a
transformation and gives final Make reusable state geometry. The shorter first
final boundary caps documentation-only waste without discarding productive
source.

The discovery index is a host-derived view of immutable bytes, not a Python
router or score. Codex still interprets the Wish, ranks every Inventor, reads
the strongest complete Taste candidates, and chooses. The state renderer is a
deterministic presentation/evidence tool, not an aesthetic judge.

## Compatibility and verification

V9 retains its 256k ceiling and old one-mesh proof and 30-minute final Make.
V8 and every older frozen profile retain their exact marker, prompts, timeout,
compaction, and motion-sheet behavior. Tests bind v10's profile hash,
16-minute proof, 15-minute final-source handoff, normal recovery, complete
roster index, stable three-state marker files, distinct-state renderer refusal,
and frozen v9/v8 compatibility. A fresh production Quest must still pass and
publish before v10 counts as an economic success.
