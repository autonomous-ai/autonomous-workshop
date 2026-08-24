# Current Workshop adoption

Alice, Bob, and Eve execute shared Workshop code on normal product paths. Each
keeps its characterized creative state machine while the Workshop owns a
narrow, tested infrastructure boundary. This avoids competing lifecycle
authorities while common behavior moves into one place.

| Inventor | Shared boundary used today | Inventor-local authority retained |
|---|---|---|
| Alice | Deterministic artifact serialization and effect-time artifact verification; the service seals the exact `src/inventor_workshop` checkout into its runtime identity. | Stronger SQLite leases, evidence graph, release decision, effect reconciliation, and production-manifest hash. |
| Bob | Artifact identity and payload, shared CAD/STEP skills, stable logical product, durable draft/live intent, and authenticated external receipt. | Queue, reward, research, simulation, table play, and creative budget behavior. |
| Eve | Post-build content-addressed snapshot, safe artifact staging, stable logical product, and durable draft intent/receipt. | JSON creative queue, great-books loop, Inspections, journal, and reward ledger. |

Some native code and persisted data still use Workshop 0.3 compatibility names
such as `PackedArtifact`, `Sender`, `Stamp`, and `Clockwork`. Those names do not
add stages to the public Wish/Taste/Make/Inspect model.

## Current catalog integration

The catalog adapter currently targets
`https://panda-social-api.autonomous.ai/api/v1`, backed by
`autonomous-ai/panda-social-backend`. **Panda is a legacy deployed-service
codename**, not the name of a Workshop subsystem or public developer API.

Bob and Eve's launchd installers pin the exact repository `src` directory so
an unrelated same-version global install cannot satisfy a scheduled runtime by
accident.

Their Workshop SQLite database is the only authority for outside effects.
Inventor-local `send.json` files are readable projections and cannot authorize
a retry. A logical slug stays bound to its first selected artifact. Corrected
bytes require a new slug until the runtime has an atomic logical-product
revision contract, because retrying an unknown non-idempotent import could
create a duplicate design.

Alice intentionally retains its mature store. Its integration independently
verifies Workshop's deterministic artifact contract while preserving stricter
existing gates. The always-on worker hashes the explicit mutable Workshop
checkout and copies the same files into its owner-only execution snapshot.

## Verification

CI installs the repository-root package before testing every native inventor
and exercises these runtime ranges:

- Workshop: Python 3.9 and 3.13;
- Alice: Python 3.11 and 3.13, plus its service snapshot path on macOS;
- Bob: Python 3.9 and 3.12;
- Eve: Python 3.9 and 3.12 with its pinned test graph.

The suites exercise real adapter paths, not only import smokes. Alice proves
artifact parity and effect-time tamper rejection. Bob proves draft, ambiguous
import, live, readback, redirect, and launchd behavior. Eve proves builder
snapshots, draft receipts, changed-artifact retry fencing, and FIFO/symlink
refusal.

Run the complete offline checks from the repository root:

```bash
python3 tools/scan_secrets.py
python3 tools/verify_skill_locks.py
python3 tools/verify_snapshot_locks.py
workshop inventors --root inventors --check-entrypoints
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_*.py'
```

Then run each inventor's documented test command. No test needs a model,
catalog credential, printer, or paid provider.

## New inventors

`workshop new` creates a schema-v4 inventor with credential-free `doctor`,
`make`, and `status` commands and a direct Make/Inspect loop. See
[BUILD_AN_INVENTOR.md](BUILD_AN_INVENTOR.md).

## Next migration slice

The stricter target in [MIGRATION.md](MIGRATION.md) is not a claim about every
line of native inventor code. The next shared slice is an atomic logical-product
artifact revision, followed by lifecycle, lease, and budget bridges backed by
golden transition fixtures. Alice, Bob, and Eve keep stronger native behavior
until Workshop proves equivalent behavior.
