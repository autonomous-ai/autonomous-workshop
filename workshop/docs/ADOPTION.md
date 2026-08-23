# Current Workshop adoption

Alice, Bob, and Eve all execute shared Workshop on normal product paths. This
is a deliberate incremental migration: each inventor keeps its characterized
creative state machine while Workshop owns infrastructure at a narrow, tested
boundary. It avoids a dual-written lifecycle while removing the most dangerous
Send and artifact duplication.

| Inventor | Executed Workshop boundary | Inventor-local authority retained |
|---|---|---|
| Alice | `_workshop_pack` builds and re-inspects one canonical Workshop Pack; the Vibe integration reconstructs and verifies the complete artifact/Pack binding before an effect. The always-on service hashes the tracked `workshop/src/inventor_workshop` checkout and seals those bytes with Alice’s code. | Alice’s stronger SQLite leases, evidence graph, release decision, effect reconciliation, and production-manifest hash. |
| Bob | Canonical Pack, shared Make CAD/STEP skills, stable logical product, durable Sender draft/live intent, and exact authenticated Stamp readback. | Bob’s queue, reward, research, simulation, table play, and budget behavior. |
| Eve | Post-build content-addressed snapshot, safe canonical Pack staging, stable logical product, and durable Sender draft intent/Stamp. | Eve’s JSON creative queue, great-books loop, Inspections, journal, and reward ledger. |

The storefront Door currently targets
`https://panda-social-api.autonomous.ai/api/v1`, backed by
`autonomous-ai/panda-social-backend`. **Panda is a legacy backend codename** used
here only to identify that deployed service and its provenance. It is not the
name of a Workshop subsystem or public developer API.

Bob and Eve’s launchd installers resolve and persist the exact repository-root
`workshop/src` path, so an unrelated same-version global install cannot
satisfy a scheduled runtime by accident.

Bob and Eve use a Workshop-owned SQLite database only as Sender authority.
Their inventor-local Send files are readable projections; they cannot
authorize a retry. A logical slug stays bound to its first selected artifact.
Corrected bytes require a new slug until Workshop has an atomic
artifact-revision contract, because creating a new product after an unknown
non-idempotent import could duplicate a storefront design.

Alice intentionally does not replace its mature store with the younger
Workshop store. Its release bridge independently verifies Workshop’s
deterministic artifact contract while preserving stricter existing gates.
Editable development installs are safe for the service boundary because every
worker identity check hashes the explicit mutable Workshop checkout, while
the same `inventor_workshop` files are copied into the owner-only execution
snapshot used by isolated children.

## Adoption verification

CI installs the same local `workshop/` package before testing every native
inventor and exercises these runtime ranges:

- Workshop: Python 3.9 and 3.13;
- Alice: Python 3.11 and 3.13, plus its service snapshot path on macOS;
- Bob: Python 3.9 and 3.12;
- Eve: Python 3.9 and 3.12 with its pinned test graph.

The inventor suites contain real Door-path tests, not only import smokes:
Alice proves Pack parity and effect-time tamper rejection; Bob proves draft,
ambiguous import, live, readback, redirect, and launchd behavior; Eve proves
builder snapshots, draft Stamps, changed-artifact retry fencing, and
nonblocking FIFO/symlink refusal.

Run the complete offline policy and adoption checks from the repository root:

```bash
python3 workshop/tools/scan_secrets.py
python3 workshop/tools/verify_skill_locks.py
python3 workshop/tools/verify_snapshot_locks.py
workshop inventors --root inventors --check-entrypoints
python3 -m unittest discover -s workshop/tests -p 'test_*.py'
```

Then run each inventor’s documented test command. No test needs a model,
storefront credential, printer, or paid provider.

## New-inventor path

New inventors do not wait for the native-agent migration. The current
`workshop new` scaffolder produces schema-v3 `workshop_features`,
imports `inventor_workshop`, and includes credential-free `doctor`, `make`,
and `status` commands. See [BUILD_AN_INVENTOR.md](BUILD_AN_INVENTOR.md).

## Next migration slice

The stricter definition in [MIGRATION.md](MIGRATION.md) remains the target, not
a claim about current native-inventor code. The next shared slice is an atomic
logical-product artifact revision, followed by Workshop lifecycle, lease, and
budget bridges backed by golden transition fixtures. Only after those fixtures
agree should Bob or Eve’s creative queue be replaced. Alice should keep any
stronger native invariant unless Workshop first proves equivalent behavior.
