# ADR 0101: Spark runs leave out the Invent-route skills and cadgen's tests

- **Status:** Accepted on 2026-11-11 (owner decision on the dead-weight audit).
- **Scope:** the domain skills `AgentRun` copies into **new** runs. Frozen
  and running runs keep what they materialized.
- **Relates to:** ADR 0016 (selectable routes), ADR 0061 (Spark's Make owns
  verification; host-only Release), ADR 0100 (domain skill budget).

## Context

Every run copied all eleven vendored domain skills. In 24 recorded Spark runs,
`product-design` and `design-reference` were never used. `manual-design` serves
only PDF-first Release, and Spark Release is host-only (ADR 0061). The cad
skill also vendors the upstream `cadgen` package's own test suite
(`scripts/packages/cadgen/tests/`, about 30 KB), which no run executes.

## Decision

- A new run whose route has no Invent stage (Spark) is created without
  `INVENT_ROUTE_DOMAIN_SKILLS`: `design-reference`, `manual-design` and
  `product-design`. Forge and Quest runs, and a run created with no route,
  receive every skill as before. The checkpoint's `domain_skills` (ADR 0100)
  records exactly which skills a run carries.
- `design-vault` stays in every route. The host writes the vault snapshot
  before every Make phase, Spark included, and the Make finalizer refuses a
  snapshot whose tool is missing.
- No new run receives `cad/scripts/packages/cadgen/tests/`. A refresh never
  adds it to a run that lacks it. A run that already carries it keeps
  refreshing it byte-for-byte, so an older run's inputs never shrink.
- The vendored trees, `LOCK.json` and `PROVENANCE.md` are unchanged. Only the
  run copy is filtered.

## Consequences

- A Spark run copies about 119 KB less: 88 KB of skills plus 30 KB of tests.
- A host refresh only touches skills a run already carries, so a Spark run
  never gains the left-out skills, and a frozen run keeps its own.
- `cad`'s SKILL.md still names `$product-design` for an open prose request. A
  Spark run never has one, since it builds from a sealed Design Contract.
  `references/make-playtest.md` now says which routes carry the two skills.
