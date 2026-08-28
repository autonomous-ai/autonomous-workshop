# Governance

Autonomous Workshop is maintained in public. Decisions favor truthful product
claims, durable evidence, narrow component boundaries, and a contribution path
that does not require knowing the repository's history.

## Roles

- **Contributor:** anyone who reports an issue, improves documentation, adds an
  inventor, or submits code, a skill, or a schema change.
- **Component DRI:** the individual accountable for one component's public
  contracts, implementation, documentation, and tests.
- **Backup maintainer:** a second individual able to review and operate that
  component when its DRI is unavailable.
- **Repository maintainer:** a maintainer responsible for architecture,
  packaging, releases, governance, and protected repository settings.
- **Security reviewer:** a repository maintainer explicitly reviewing secrets,
  provenance, outside effects, or trust-boundary changes.

Current assignments are in [MAINTAINERS.md](MAINTAINERS.md).

## Decision levels

### Routine component change

A component DRI may approve a focused change contained within that component
when its public contracts, durable formats, evidence floors, and effects do not
change. Tests and documentation remain part of the same ownership boundary.

### Cross-component contract change

Changes to data exchanged between components require approval from the DRI of
every affected component. The pull request must state the direction of the
dependency and include contract or integration tests.

### High-risk change

The following require the owning DRI plus a repository maintainer or security
reviewer who is not the author when another qualified reviewer is available:

- durable state, migrations, event ordering, leases, retries, or budgets;
- schemas, canonical JSON, hashes, artifact identity, locks, or sealing;
- Playtest, Release, delivery, or other non-bypassable evidence floors;
- credential handling, provider boundaries, network calls, or physical effects;
- packaging, release automation, dependency provenance, or license changes;
- component boundary exceptions or new top-level packages.

If only one qualified maintainer exists, the exception must be called out in
the pull request and the change must remain reversible. A post-merge review is
scheduled when a second qualified maintainer becomes available.

### Architecture decision

A change that creates a component, changes dependency direction, replaces a
durable contract, or alters public lifecycle vocabulary requires an Architecture
Decision Record under `docs/adr/`. An ADR records context, the decision,
alternatives, consequences, compatibility, and rollback. Accepted ADRs are not
silently rewritten; a new ADR supersedes them.

## Component boundary

Each Workshop component owns one source directory under `src/workshop/` and a
mirrored test directory under `tests/`. Skills, schemas, and fixtures belong to
their producing component. Root test suites cover architecture, packaging,
integration, and end-to-end behavior.

Components import public contracts, never a sibling's private implementation.
Workflow alone sequences stages. Integrations implement ports declared by the
owning component. CLI and inventor profiles consume public Workshop APIs; the
Workshop library never imports either application.

The accepted boundary is documented in [ADR 0001](../docs/adr/0001-component-oriented-source-layout.md)
and [ADR 0002](../docs/adr/0002-dependency-and-orchestration-boundaries.md).

## Contribution and review process

1. Keep a pull request focused on one component or one explicit contract.
2. Name the owning component and change class in the pull request template.
3. Include tests at the narrowest responsible layer and integration tests for
   cross-component behavior.
4. Record user-visible or compatibility-relevant changes under `changes/`.
5. Obtain CODEOWNERS approval and every additional approval required above.
6. Merge only after required CI, secret, provenance, packaging, and lock checks
   pass.

Large migrations should use mechanical moves before behavioral redesign. A
temporary compatibility facade may keep intermediate commits green, but it has
an owner, a removal release, and no independent behavior.

## Releases and compatibility

Repository maintainers prepare releases from a green protected branch. A
release candidate is required for namespace changes, persisted-data migrations,
or changes to installed skills and schemas.

Public Python compatibility follows the documented release policy. Durable
state, manifests, evidence, receipts, hashes, and artifact bytes receive the
stronger rules in [ADR 0003](../docs/adr/0003-durable-compatibility-during-refactoring.md):
old evidence is read by versioned readers and is not rewritten to match new
source names.

## Conduct and security

All participation follows [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md). Security
reports follow [SECURITY.md](SECURITY.md), not a public issue. Maintainers may
pause or revert a release when safety, provenance, durability, or truthful
product claims are uncertain.
