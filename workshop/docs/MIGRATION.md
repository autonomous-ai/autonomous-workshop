# Migration to Workshop 0.3

Workshop 0.3 establishes the vocabulary and contract the next generation of
inventors should share. Migration is incremental: preserve characterized
inventor behavior and persisted effects while moving one tested boundary at a
time.

Current native adoption is recorded in [ADOPTION.md](ADOPTION.md).

## Name and schema history

| Version | Distribution / import | Manifest feature field |
|---|---|---|
| 0.1 | `autonomous-inventor-core` / `inventor_core` | `core_features` |
| 0.2 | `inventor-foundation` / `inventor_foundation` | `foundation_features` |
| 0.3 | `inventor-workshop` / `inventor_workshop` | `workshop_features` |

New code uses:

- folder `workshop/`;
- distribution `inventor-workshop`;
- import `inventor_workshop`;
- CLI `workshop`;
- manifest schema v3;
- runtime `.workshop/clockwork.sqlite3` for a clean inventor.

`inventor_foundation` and `inventor_core` are direct compatibility shims to
the same canonical modules. They never chain through one another and never own
separate behavior or state.

## Public API map

| Before 0.3 | Workshop 0.3 |
|---|---|
| `TasteProfile`, `load_taste_profile()` | `Taste`, `load_taste()` |
| `CreationBrief` | `Wish` |
| `Forge.create()` | `Workbench.make()`, then `Workbench.inspect()` |
| `CreationResult` | `MakeResult` |
| `GateResult`, `GatePolicy` | `InspectionResult`, `InspectionPolicy` |
| unbundled gate arguments | artifact-bound `Inspection` |
| `Pipeline`, `PipelineSpec` | `Workflow`, `WorkflowSpec` |
| `InventorStore` | `Clockwork` |
| `build_artifact_manifest()` | `seal_artifact()` |
| `build_publish_packet()` | `pack_artifact()` |
| publish packet | `PackedArtifact` |
| `Launchpad` | `Sender` |
| `Portal` | a qualified Door such as `ShopDoor` |
| `PublicationReceipt` | `Stamp` |
| `PublicationOutcome` | `SendResult` |

Former names remain aliases for existing runtimes. New documentation,
scaffolds, manifests, and emitted metadata use only Workshop names.

## Manifest compatibility

Readers accept exactly one feature field for the declared schema:

- schema v1: `core_features`;
- schema v2: `foundation_features`;
- schema v3: `workshop_features` plus declared `checks`.

Schema v3 validates features against the reviewed catalog. A document that
mixes feature fields is rejected, even if their values happen to match. New
scaffolds emit v3 only.

Schemas are included in the wheel and discoverable with:

```bash
workshop schemas list
workshop schemas path
```

## Durable metadata compatibility

Canonical send requests emit:

```text
_workshop_artifact_sha256
_workshop_owner_id
_workshop_api_origin
```

Readers also accept the corresponding `_foundation_*` and `_core_*` keys. If
more than one generation is present, every value must agree. A conflict fails
closed before an outside effect.

Keep accurate generic database tables—products, events, leases, budgets, and
send intents—in place. Renaming durable tables for atmosphere creates risk and
no developer value. Branded metadata may be migrated only after its schema and
authority are validated.

## State path migration

A clean inventor uses `.workshop/clockwork.sqlite3` or an inventor-documented
equivalent under its runtime root. Existing inventor databases may continue in
place.

When resolving old paths:

1. prefer an explicitly configured canonical Workshop path;
2. otherwise continue one existing legacy database in place;
3. refuse multiple independent candidates;
4. never merge two authorities by modification time;
5. emit only the canonical path on a fresh install.

The same conflict rule applies to environment variables. A canonical and
legacy value may coexist only when they resolve to the same exact authority.

## Evidence migration

Old `Pipeline.advance(..., gates=...)` remains available for characterized
0.2 callers. Canonical `Workflow.advance(..., inspection=...)` requires an
`Inspection` bundle whenever the target stage has checks.

Migrate by:

1. sealing the exact artifact with `ArtifactManifest`;
2. placing every inspection evidence file inside that inventory;
3. recording the evidence path and SHA-256 in `InspectionResult`;
4. constructing `Inspection(manifest, results)`;
5. passing that object into the Workflow transition.

This closes the old gap where a valid-looking result could name the artifact
hash without proving its evidence belonged to the sealed artifact.

For a CAD result, hash its real evidence file normally and put that digest in
`evidence_sha256`. Bind the release separately with
`evidence["cad_release_sha256"] = cad_release.sha256`. The report file digest
is not the release-bundle digest.

## Pack and Send migration

Use `pack_artifact()` instead of inventor-local ZIP builders. It preserves the
same deterministic and secret-scanning floors while returning canonical
`PackedArtifact` names.

Canonical callers must pass that object into the state change:

```python
workflow.advance(clockwork, product_id, "pack", revision, packed=packed)
```

Workflow revalidates the Pack, compares its artifact identity with the product
accepted by Inspect, and records `pack_sha256` in the Clockwork event. The old
`Pipeline` remains a compatibility layer; new `Workflow` paths do not accept a
bare Pack hash for this transition.

Use `Sender` with a qualified Door. Preserve one logical send intent across
draft/live/reconciliation. Do not re-send after a timeout, unexpected status,
redirect, malformed success body, or uncertain readback. A trustworthy
`Stamp`—not a local flag—is the transition evidence.

The currently deployed shop backend still uses a historical Panda service URL.
That name is retained only in the concrete URL, credential fallback, and
provenance documentation. It is not a Workshop subsystem name.

## Recommended order for a mature inventor

1. **Characterize first.** Freeze golden transitions, artifacts, failures, and
   effect-reconciliation fixtures.
2. **Adopt Taste.** Establish one root `TASTE.md` and exact binding.
3. **Adopt Pack.** Replace duplicate artifact/ZIP code without changing the
   inventor's creative state machine.
4. **Adopt Send.** Make the Workshop outbox the only effect authority; keep old
   JSON files as projections.
5. **Adopt Inspection.** Bind every result and evidence file to exact artifact
   bytes.
6. **Adopt Clockwork.** Move lifecycle, leases, and budgets only after golden
   fixtures prove behavioral parity.
7. **Delete duplication.** Remove old infrastructure only after tests prove no
   entry point still reaches it.

Alice should keep any stronger native invariant until Workshop proves
equivalent behavior. Bob and Eve can move narrower boundaries sooner, but may
not dual-write two lifecycle or send authorities.

## Verification

```bash
PYTHONPATH=workshop/src python -m unittest discover \
  -s workshop/tests -p 'test_*.py' -v
workshop check inventors --run
python workshop/tools/verify_skill_locks.py
python workshop/tools/verify_snapshot_locks.py
python workshop/tools/scan_secrets.py
```

Test both canonical and compatibility imports, old state fixtures, conflicting
authority rejection, fresh installed wheels, and ambiguous outside effects
before deleting a legacy name.
