# Migration to Workshop 0.4

Workshop 0.4 makes the repository and language match the product: the
repository itself is Autonomous Workshop, inventor code lives under
`inventors/`, and the public loop has only Wish, Taste, Make, and Inspect.

Migration is incremental. Preserve characterized behavior and persisted
effects while moving one tested boundary at a time. Current native adoption is
recorded in [ADOPTION.md](ADOPTION.md).

## Repository layout

The former nested `workshop/` contents now live at the repository root:

| Before 0.4 | 0.4 |
|---|---|
| `workshop/src/` | `src/` |
| `workshop/skills/` | `skills/` |
| `workshop/schemas/` | `schemas/` |
| `workshop/docs/` | `docs/` |
| `workshop/tests/` | `tests/` |
| `workshop/tools/` | `tools/` |
| `pip install -e workshop` | `pip install -e .` |
| from an inventor: `pip install -e ../../workshop` | `pip install -e ../..` |

Distribution, import, and CLI names do not change:

- distribution `inventor-workshop`;
- Python package `inventor_workshop`;
- CLI `workshop`;
- per-inventor runtime directory `.workshop/`.

The local runtime folder keeps its name because it distinguishes generated
state from inventor source; it is unrelated to the removed repository nesting.

## Name and schema history

| Version | Distribution / import | Manifest feature field |
|---|---|---|
| 0.1 | `autonomous-inventor-core` / `inventor_core` | `core_features` |
| 0.2 | `inventor-foundation` / `inventor_foundation` | `foundation_features` |
| 0.3 | `inventor-workshop` / `inventor_workshop` | `workshop_features` |
| 0.4 | `inventor-workshop` / `inventor_workshop` | none |

Schema v4 requires `checks` but has no Workshop feature inventory. Every
inventor in this repository already shares the Workshop; listing implementation
pieces in each inventor's identity created noise and coupled manifests to
internal names.

Readers remain compatible with exactly one historical feature field for the
declared schema:

- schema v1: `core_features`;
- schema v2: `foundation_features` plus `checks`;
- schema v3: reviewed `workshop_features` plus `checks`;
- schema v4: `checks`, with no feature field.

`inventor_foundation` and `inventor_core` remain direct import shims. They do
not own separate behavior or state.

## Public vocabulary

New inventor-facing code and documentation teach only:

```text
Wish + Taste -> Make <-> Inspect
```

The six short-lived Workshop 0.3 metaphors become literal implementation
names:

| Workshop 0.3 | Workshop 0.4 treatment |
|---|---|
| `PackedArtifact` | `Artifact`; exact serialized bytes remain available |
| `PackPlan` | `ArtifactPlan` |
| `pack_artifact()` | `bundle_artifact()` |
| `inspect_pack()` | `inspect_artifact()` |
| `Sender` | `Runtime` outside-effect operation |
| `Clockwork` | `Runtime` |
| qualified `*Door` | ordinary provider adapter |
| `Stamp` | `Receipt` |
| `Box` | no technical concept; say product or delivery |

All names in the left column remain compatibility aliases for at least this
migration cycle. Existing inventor commands such as `send`, task names such as
`pack.product`, environment variables, and persisted filenames are not silently
renamed; treat them as characterized operational interfaces and migrate them
separately when useful.

Historical names before 0.3 remain readable too:

| Older name | Current meaning |
|---|---|
| `TasteProfile`, `load_taste_profile()` | `Taste`, `load_taste()` |
| `CreationBrief` | `Wish` |
| `Forge.create()` | `Workbench.make()`, then `Workbench.inspect()` |
| `CreationResult` | `MakeResult` |
| `GateResult`, `GatePolicy` | `InspectionResult`, `InspectionPolicy` |
| `Pipeline`, `PipelineSpec` | `Workflow`, `WorkflowSpec` |
| `InventorStore` | `Runtime` |
| `build_artifact_manifest()` | `seal_artifact()` |
| `build_publish_packet()` | `bundle_artifact()` |
| `Launchpad` | `Runtime` outside-effect operation |
| `Portal` | provider adapter |
| `PublicationReceipt` | `Receipt` |

## Workflow migration

New default workflows contain Make and Inspect only. Inspect returns either a
successful result or useful feedback to another Make attempt. Artifact
serialization and outside effects are operations around that loop, not stages
every inventor must traverse.

Custom and persisted 0.3 workflows that contain `pack` and `send` remain
readable. Do not rewrite their event history. New workflows should avoid those
stages unless they are truly domain-specific names rather than Workshop
plumbing.

## Artifact compatibility

Keep two hashes distinct:

- the logical artifact-tree hash;
- the exact serialized payload hash.

Persisted `pack_sha256` fields remain readable and writable where changing the
storage contract would create risk. Canonical code can read the same value as
`payload_sha256`. Do not merge these hashes: equal logical files can still have
different transferred bytes.

Existing `pack/` directories and ZIP files remain valid. New prose calls them
serialized artifacts or payloads.

## Runtime and effect compatibility

Keep durable database names and fields—including `send_intents`, `door_name`,
`stamp_json`, and `pack_sha256`—in place. Renaming a table for vocabulary alone
adds migration risk without improving the architecture.

For every outside effect:

1. reuse one stable intent/idempotency identity;
2. record the exact request before execution;
3. use a separate attempt fence;
4. bind the receipt to the request, logical artifact, and exact payload;
5. hold timeouts, redirects, malformed success bodies, unexpected statuses,
   and uncertain readbacks for reconciliation.

Never dual-write two effect authorities. Inventor-local JSON may remain a
readable projection, but only the runtime ledger can authorize retry.

Canonical metadata still reads persisted `_workshop_*`, `_foundation_*`, and
`_core_*` keys. If more than one generation is present, values must agree or
the operation fails closed.

## State paths

A clean inventor uses an inventor-documented database under `.workshop/`.
Existing `.workshop/clockwork.sqlite3` files continue in place. A new name may
be used only for a fresh inventor or through an explicit tested migration.

When resolving old paths:

1. prefer an explicitly configured canonical path;
2. otherwise continue exactly one existing database in place;
3. refuse multiple independent candidates;
4. never merge authorities by modification time.

## Recommended order for a mature inventor

1. Characterize current transitions, artifacts, failures, and reconciliation.
2. Establish one root `TASTE.md` and exact binding.
3. Adopt immutable Workshop artifact identity and serialization.
4. Make the Workshop runtime the only outside-effect authority.
5. Bind every Inspection and evidence file to exact artifact bytes.
6. Move lifecycle, leases, and budgets only after golden fixtures prove parity.
7. Simplify operational names only after all entry points use one authority.

Alice should keep any stronger native invariant until Workshop proves
equivalent behavior. Bob can move narrower boundaries sooner, but must not
dual-write lifecycle or effect authority.

## Verification

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_*.py' -v
workshop check inventors --run
python tools/verify_skill_locks.py
python tools/verify_snapshot_locks.py
python tools/scan_secrets.py
```

Test canonical and compatibility imports, old state fixtures, conflicting
authority rejection, installed wheels, and ambiguous outside effects before
deleting any legacy name.
