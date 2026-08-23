# Current core adoption

Alice, Bob, and Eve all execute shared core on normal product paths. This is a
deliberate incremental migration: each inventor keeps its characterized
creative state machine while core owns infrastructure at a narrow, tested
boundary. It avoids a dual-written lifecycle while still removing the most
dangerous publication and artifact duplication.

| Inventor | Executed shared-core boundary | Inventor-local authority retained |
|---|---|---|
| Alice | `publish.packet` builds a core artifact manifest and canonical packet identity; the Vibe adapter reconstructs and verifies the complete binding before an effect. The always-on service explicitly hashes the clean tracked `core/src/inventor_core` checkout and seals those bytes with Alice's code. | Alice's stronger SQLite leases, evidence graph, release decision, effect reconciliation, and production-manifest hash. |
| Bob | Canonical product packet, shared CAD/STEP skills, stable logical publication product, durable Panda draft/live intent, and exact authenticated live readback. | Bob's queue, reward, research, simulation, table play, and budget behavior. |
| Eve | Post-build content-addressed snapshot, safe canonical packet staging, stable logical publication product, and durable Panda draft intent/receipt. | Eve's JSON creative queue, great-books loop, gates, journal, and reward ledger. |

Bob and Eve's launchd installers resolve and persist the exact sibling
`core/src` path, so an unrelated same-version global install cannot satisfy a
scheduled runtime by accident.

Bob and Eve use `state/inventor-core.sqlite3` only as publication authority.
Their local `published.json` and `_core-publication.json` files are readable
projections; they cannot authorize a retry. A logical slug stays bound to its
first selected artifact. Corrected bytes require a new slug until core has an
atomic artifact-revision contract, because creating a new product after an
unknown non-idempotent import could duplicate a Panda design.

Alice intentionally does not replace its mature store with the younger core
store. Its release bridge independently verifies core's deterministic artifact
contract while preserving stricter existing gates. Editable development
installs are safe for the service boundary because every worker identity check
hashes the explicit mutable core checkout, while the same `inventor_core` files
are copied into the owner-only execution snapshot used by isolated children.

## Compatibility contract

CI installs the same local `core/` package before testing every native inventor
and exercises these runtime ranges:

- core: Python 3.9 and 3.13;
- Alice: Python 3.11 and 3.13, plus its service snapshot path on macOS;
- Bob: Python 3.9 and 3.12;
- Eve: Python 3.9 and 3.12 with its pinned test graph.

The inventor suites contain real adapter-path tests, not only import smokes:
Alice proves packet parity and effect-time tamper rejection; Bob proves draft,
ambiguous import, live, readback, redirect, and launchd behavior; Eve proves
builder snapshots, draft receipts, changed-artifact retry fencing, and
nonblocking FIFO/symlink refusal.

Run the complete offline policy and compatibility checks from the repository
root:

```bash
python3 core/tools/scan_secrets.py
python3 core/tools/verify_snapshot_locks.py
PYTHONPATH=core/src python3 -m inventor_core registry --root . --check-entrypoints
PYTHONPATH=core/src python3 -m unittest discover -s core/tests -p 'test_*.py'
```

Then run each inventor's documented test command. No test needs a model,
Panda credential, printer, or paid provider.

## Next migration slice

The stricter definition in [MIGRATION.md](MIGRATION.md) remains the target, not
a claim about current code. The next shared slice is an atomic logical-product
artifact revision, followed by core lifecycle/lease/budget adapters backed by
golden transition fixtures. Only after those fixtures agree should Bob or Eve's
creative queue be replaced. Alice should keep any stronger native invariant
unless core first proves equivalent behavior.
