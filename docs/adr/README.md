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
