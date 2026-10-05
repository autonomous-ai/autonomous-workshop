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

- [0068: Cancellable geometry and disclosed unverified handoff](0068-cancellable-geometry-and-unverified-handoff.md)
- [0069: Corrections carry byte-identical parts forward](0069-correction-carry-forward.md)
- [0070: A redundant final sweep reuses its verdict and exits zero](0070-redundant-final-sweep-reuses-its-verdict.md)
- [0071: Component rounds fan out, bounded by host width](0071-bounded-component-round-fan-out.md)
- [0072: A gate that can verify nothing must refuse](0072-a-gate-that-verifies-nothing-refuses.md)
- [0073: Carry Forward compares geometry, not STEP bytes](0073-carry-forward-compares-geometry-not-step-bytes.md)
- [0074: Every Component is scored against its own sealed image](0074-every-component-scored-against-its-own-image.md)
- [0075: Component review compares form, and acceptance needs a second reader](0075-component-review-compares-form-and-acceptance-needs-a-second-reader.md)
- [0076: A Component passes on an independent review, not a likeness score](0076-component-passes-on-an-independent-review-not-a-likeness-score.md)
- [0077: Component Workers and a root-owned Component Reviewer](0077-component-workers-and-a-root-owned-reviewer.md)
- [0080: Component Workers author their Components, and a hook admits their rounds](0080-component-workers-author-and-a-hook-admits-their-rounds.md)
- [0081: Shape Rounds follow Component Reviews](0081-shape-rounds-follow-component-reviews.md)
- [0082: Interfaces between Components](0082-interfaces-between-components.md)
- [0083: Compare each reference in the Display Pose at its Reference Camera](0083-compare-in-the-display-pose-at-the-reference-camera.md)
- [0084: The reviewer reads Interface text, and the Design Contract wins over its references](0084-interface-text-and-reference-conflicts.md)
- [0085: An invisible Contract Amendment may be made inside a run, confirmed by a fresh reader](0085-in-run-contract-amendments-for-invisible-fixes.md)
- [0086: Spark Make expands the Wish before building](0086-spark-make-expands-the-wish.md)
- [0087: Make rounds review one sheet and judge plan and reference apart](0087-make-round-review-sheet-and-split-verdict.md)
