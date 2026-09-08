# Architecture decision records

Architecture Decision Records capture durable choices about component
boundaries, dependency direction, public lifecycle vocabulary, persisted data,
and packaging. They explain why a decision exists so contributors do not need
oral history to work safely.

Use the next four-digit number and this structure:

```markdown
# ADR NNNN: Decision title

- Status: Proposed
- Date: YYYY-MM-DD
- Owners: affected component roles

## Context
## Decision
## Alternatives considered
## Consequences
## Compatibility and migration
## Verification
```

Statuses are `Proposed`, `Accepted`, `Superseded by ADR NNNN`, or `Rejected`.
Do not rewrite an accepted decision to reverse its meaning; add a superseding
ADR. Small factual corrections that do not change the decision are allowed.

## Index

The effective rule at the end of each chain is summarized in the root
`AGENTS.md`; this table is the full list with the current status of each
record.

| ADR | Status |
|---|---|
| [ADR 0001: Component-oriented source layout](0001-component-oriented-source-layout.md) | Accepted |
| [ADR 0002: Dependency and orchestration boundaries](0002-dependency-and-orchestration-boundaries.md) | Superseded by ADR 0012 |
| [ADR 0003: Preserve durable compatibility during source refactoring](0003-durable-compatibility-during-refactoring.md) | Superseded by ADR 0012 |
| [ADR 0012: Codex-orchestrated native runtime](0012-codex-orchestrated-runtime.md) | Accepted |
| [ADR 0013: Make Release manual-first and publication optional](0013-manual-first-release.md) | Superseded by ADR 0014 |
| [ADR 0014: End Workshop at a published, print-ready Release](0014-terminal-published-release.md) | Accepted |
| [ADR 0015: Defer Playtest from the executable fast path](0015-defer-playtest.md) | Accepted |
| [ADR 0016: Selectable effort routes](0016-selectable-effort-routes.md) | Accepted |
| [ADR 0017: Portable Workshop Manager runtimes](0017-portable-workshop-managers.md) | Accepted |
| [ADR 0018: Evidence-bound Make-to-Invent revision](0018-evidence-bound-make-to-invent.md) | Accepted |
| [ADR 0019: Freeze a lower-cost Codex profile for Spark](0019-frozen-spark-economics-profile.md) | Accepted |
| [ADR 0020: Require signature-experience evidence and batch manual review](0020-signature-experience-evidence.md) | Accepted |
| [ADR 0021: Compact Spark context and bind final signature review](0021-compacted-spark-and-signature-review.md) | Accepted |
| [ADR 0022: Blind signature review before final verification](0022-blind-review-before-final-verification.md) | Accepted |
| [ADR 0023: Bound Spark turns and review the promised relationship](0023-bounded-spark-turn-and-semantic-review.md) | Accepted |
| [ADR 0024: Treat quality economics as a comparative North Star](0024-comparative-quality-economics.md) | Accepted |
| [ADR 0025: Bind Make review to form and the declared CAD project](0025-bind-review-to-form-and-cad-project.md) | Accepted |
| [ADR 0026: Preserve Wish-critical form through Make repair](0026-preserve-wish-form-through-make.md) | Accepted |
| [ADR 0027: Bind every printable before visual review](0027-bind-all-printables-before-visual-review.md) | Accepted |
| [ADR 0028: Bound Forge and Quest turns without lowering reasoning](0028-bound-deep-effort-turns.md) | Accepted |
| [ADR 0029: Keep destructive CAD freshness host-owned](0029-host-owned-fresh-cad-rebuild.md) | Accepted |
| [ADR 0030: Shape deep effort by stage and persist proof first](0030-stage-shaped-deep-economics.md) | Superseded by ADR 0031 |
| [ADR 0031: Bind the deep profile and bound first proof](0031-bind-deep-profile-and-bound-first-proof.md) | Superseded by ADR 0032 |
| [ADR 0032: Restore Make depth and blindly review first proof](0032-restore-make-depth-and-blindly-review-first-proof.md) | Superseded by ADR 0033 |
| [ADR 0033: Phase deep Make at a proof checkpoint](0033-phase-deep-make-at-a-proof-checkpoint.md) | Superseded by ADR 0034 |
| [ADR 0034: Bind proof to executable CAD entrypoints](0034-bind-proof-to-executable-cad-entrypoints.md) | Superseded by ADR 0035 |
| [ADR 0035: Remove proof startup and scheduling leaks](0035-remove-proof-startup-and-scheduling-leaks.md) | Superseded by ADR 0036 |
| [ADR 0036: Reserve the proof runway for product bytes](0036-reserve-proof-runway-for-product-bytes.md) | Superseded by ADR 0037 |
| [ADR 0037: Raise the deep compaction ceiling to 256k](0037-raise-deep-compaction-ceiling.md) | Superseded by ADR 0038 |
| [ADR 0038: Prove product states and bound the final-source handoff](0038-prove-product-states-and-bound-final-source.md) | Superseded by ADR 0039 |
| [ADR 0039: Make Invent recovery a source handoff](0039-make-invent-recovery-a-source-handoff.md) | Superseded by ADR 0040 |
| [ADR 0040: Make proof recovery a sealing handoff](0040-make-proof-recovery-a-sealing-handoff.md) | Superseded by ADR 0041 |
| [ADR 0041: Resume final Make at recovery](0041-resume-final-make-at-recovery.md) | Accepted |
| [ADR 0042: Connect each Inventor through browser authorization](0042-browser-issued-factory-credential.md) | Accepted |
| [ADR 0043: Freeze agent, model, and reasoning effort](0043-freeze-agent-model-and-effort.md) | Accepted |
| [ADR 0044: Scope component-CAD network access](0044-scope-component-cad-network.md) | Accepted |
| [ADR 0045: Own agent-selected dependencies](0045-own-agent-selected-dependencies.md) | Accepted |
| [ADR 0046: Explicit twenty-minute turns for budgeted Spark](0046-budgeted-spark-twenty-minute-turns.md) | Superseded by ADR 0049 |
| [ADR 0047: Match evidence to motion and persist native execution budgets](0047-motion-review-and-persistent-native-budget.md) | Superseded by ADR 0048 |
| [ADR 0048: Persistent native-turn budgets](0048-persistent-native-turn-budgets.md) | Superseded by ADR 0049 |
| [ADR 0049: Product-wide native token budgets](0049-product-wide-token-budget.md) | Accepted |
| [ADR 0050: Retain structured terminal-failure diagnostics](0050-structured-terminal-failure-diagnostics.md) | Accepted |
| [ADR 0051: Sixty-minute emergency watchdog per native turn](0051-sixty-minute-turn-watchdog.md) | Accepted |
