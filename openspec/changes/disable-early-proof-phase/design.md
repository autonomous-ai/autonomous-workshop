## Context

New Forge and Quest runs on the base revision freeze `deep-economics-v13.md`. V13 retains the 256k context fix from v9 but still divides Make into a medium early-proof turn, a host marker/receipt handoff, a high source-transfer turn, and ordinary recovery. The proof was intended as durable liveness evidence when short turns frequently ended before useful CAD existed. In the two HCMC chess-set runs, however, the mandated source reuse turned generic proof geometry into an accidental visual-design anchor.

The proof is not a lifecycle gate, but it is operationally load-bearing: launch selection, finalization markers, receipt creation, timeout selection, recovery, cleanup, and prompts all depend on the frozen capability. Removing prose alone would leave it active; deleting the machinery would break historical runs.

## Goals / Non-Goals

**Goals**

- Give new deep Make one uninterrupted high-reasoning path from sealed Invent to complete final product.
- Preserve all authoritative Make, Quest, Release, and effect boundaries.
- Preserve exact resumability of v13 and older checkpoints.
- Measure whether the exact prior Wish improves, rather than claiming improvement from architecture alone.

**Non-Goals**

- No new Concept stage.
- No host-side visual judge or aesthetic score.
- No conversion of existing runs to v14.
- No change to publication credentials, effect ownership, or Factory behavior.

## Decisions

### 1. Freeze v14 and name v13 compatibility explicitly

`DEEP_ECONOMICS_CAPABILITY_PATH` identifies new v14 runs. The old current constant becomes `DEEP_ECONOMICS_V13_CAPABILITY_PATH`. A direct-profile classifier recognizes v14, while the phased-profile helper recognizes v13 through the older proof profiles. Because every new run materializes the whole product-run reference tree, marker precedence must select v14 even when historical files are also present.

### 2. Direct Make uses the ordinary finalizer from turn one

V14 Make launches at high reasoning, 256k compaction, and the normal 30-minute boundary. It uses `agent-outcome.json` immediately. Direct dispatch does not discover proof files, validate or consume `.make-proof-ready.json`, create/read a proof receipt, or choose proof/source-specific turns. Recoverable and explicit-resume continuations use the existing same-session, same-stage, same-Goal recovery over durable product bytes.

### 3. Invent authority replaces proof geometry authority

The Make prompt batches the exact Wish, current `STAGE.json`, sealed `NativeInvented`, selected Inventor, Make reference, and CAD skill. It asks for a coherent complete self-contained CAD baseline early and permits narrow engineering coupons for uncertain facts. A coupon is never mandatory final form. No Concept-image tree is assumed because the active main lifecycle has none.

### 4. Final gates remain unchanged

Removal applies only to the intermediate proof protocol. Accepted-Invent binding, inventory, strict fit, mesh validity, 0.4 mm wall thickness, exact-state evidence, final hash-bound blind semantic review, integrated CAD verification, Quest Playtest, Release manual, authenticated publication, and snapshot integrity remain authoritative.

### 5. Authenticated evidence must follow stage-varying economics

The mock-session audit validates one session/model and the expected reasoning per stage: Spark low; Forge/Quest high for Invent and Make, medium later. It rejects current Forge/Quest proof paths, markers, and host proof receipts. Agent-owned `.cad-scratch/` is permitted only during Make.

## Risks / Trade-offs

- A long direct turn could still fail before finalization. Mitigation: persist complete source early and retain bounded ordinary recovery.
- A generic coupon could still influence design. Mitigation: instructions explicitly subordinate coupons to sealed Invent and forbid mandatory reuse.
- Profile detection could accidentally select v13 because all references are materialized. Mitigation: explicit v14 precedence tests on a real new-run fixture.
- Removing historical code would strand old runs. Mitigation: retain and test representative v13, v12, v10, and older paths.
- Fresh Invent makes the same-Wish comparison imperfect. Mitigation: report that confound and compare each final both to the Wish and its own sealed Invent requirements.

## Migration Plan

1. Add v14 marker and direct dispatch without deleting historical handlers.
2. Update prompts/assets/tests and authenticated trace audit.
3. Run focused and full deterministic verification.
4. Run authenticated Forge/Quest acceptance.
5. Launch the exact prior Forge Wish, preserve hash-bound evidence privately, conduct a blind comparison, and document measured results.

Rollback may select v13 for new runs again, but must retain v14 recognition for already-created v14 checkpoints.
