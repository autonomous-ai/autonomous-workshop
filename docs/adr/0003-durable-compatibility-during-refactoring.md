# ADR 0003: Preserve durable compatibility during source refactoring

- Status: Superseded by ADR 0012
- Date: 2026-08-25
- Owners: Runtime, Artifacts, Integrations, and Repository maintainers

## Context

ADR 0012 replaced this migration-era policy for product-run and Inventor
formats with a deliberate native-runtime hard cut. Its durable-effect rule
remains: authenticated external intents and receipts are never rewritten or
blindly retried.

The component refactor renames and moves Python code, skills, schemas, and
tests. The repository also contains durable Workshop databases, manifests,
event chains, receipts, artifact trees, locked skills, and historical evidence.
Source clarity does not justify altering evidence or making an old run
unreadable.

## Decision

Python source compatibility and durable-data compatibility are governed
separately.

The refactor may introduce a deliberate Python API break in a release candidate.
It must preserve or explicitly version readers for:

- SQLite schema and event versions;
- manifest and receipt versions;
- persisted stage and field names, including historical vocabulary;
- canonical JSON, hashes, signatures, locks, and artifact identity;
- skill and schema bytes and executable modes when a change is only a move;
- checked-in evidence, product files, and provenance records.

Historical records are never rewritten merely to adopt `workshop` module names
or current lifecycle vocabulary. A new writer may emit a new version only when
its reader accepts every supported previous version and a fixture proves the
migration. When old evidence is no longer safe to trust, the reader reports an
explicit unsupported or invalid status instead of silently upgrading it.

Outside-effect intent remains durable before execution. An ambiguous outcome
is reconciled through authenticated readback; it is not retried as a fresh
effect. Refactoring cannot weaken idempotency or receipt binding.

## Alternatives considered

### Rewrite old state into the new shape

Rejected because it destroys byte identity, complicates incident analysis, and
can convert missing historical evidence into an apparent modern success.

### Keep the old source architecture forever

Rejected because reader compatibility does not require retaining tangled
implementation or public Python aliases indefinitely.

### Preserve all Python imports permanently

Rejected because a second live namespace would duplicate ownership. A bounded,
behavior-free compatibility facade is sufficient when external consumers
require one deprecation release.

## Consequences

Migration work carries explicit golden fixtures and versioned readers. Package
resource moves require byte and mode verification, not only import tests.
Release notes distinguish API breaks from durable compatibility.

Some historical names remain in serialized data after source modules are gone.
That is evidence preservation, not incomplete refactoring.

## Compatibility and migration

Before moving an owner, capture golden fixtures for all supported state,
manifest, schema, event, lock, receipt, and artifact versions. After each move,
run those fixtures through an installed wheel from outside the checkout.

If a compatibility facade is required, document its removal version, test that
canonical packages do not import it, and prevent it from owning state or
behavior.

## Verification

- Golden replay tests cover every supported persisted version.
- Canonical bytes and hashes match pre-refactor fixtures exactly.
- Installed skill and schema resources match locks and executable modes.
- Retry and reconciliation tests prove no duplicate outside effect.
- Release notes name every intentional writer-version or API change.
