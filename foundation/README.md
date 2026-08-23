# Inventor Foundation

Foundation is the shared control plane for autonomous inventors. It is deliberately
small, standard-library-only on Python 3.9+, and usable without model, CAD,
Panda, or Factory credentials.

The name is intentional: every inventor is built on this layer. A future
`foundation/knowledge/` can hold shared research, memory, and failure corpora;
`foundation/forge/` can own product-generation machinery. Neither describes
the full lifecycle, identity, evidence, and publication platform as accurately
as Foundation.

The folder and product are now named Foundation. The v1 distribution, Python
module, CLI alias, manifest field, environment variables, SQLite filenames,
and receipt keys retain their established `core` identifiers for compatibility.
Those machine identities include `autonomous-inventor-core`, `inventor_core`,
`inventor-core`, and `core_features`; they will change only through a versioned
migration that can still read existing publication authority and sealed worker
snapshots.

Start with the three [architecture diagrams](docs/ARCHITECTURE.md): the system
layers, the anatomy of a new inventor, and the invention-to-publication flow.

## Implemented contracts

- `manifest`: discover and validate one bounded, control-free `inventor.json`
  plus a regular, non-empty root `TASTE.md` per immediate folder under
  `inventors/`; provenance URLs cannot carry credentials, and resolved
  entrypoints cannot escape through symlinks.
- `scaffold`: atomically create a new Foundation-connected inventor package with
  `init`, `create <product-id>`, and `status` commands.
- `store`: private revision-CAS transitions behind lifecycle policy, opaque
  lease fencing, schema-v3 per-attempt effect tokens, immutable budget-policy
  snapshots, hash-chained events, and durable publish intents in a private
  SQLite/WAL database.
- `artifacts`: safe-path manifests and reproducible publish zips identified by
  SHA-256; no-follow reads and final sender checks keep bounded, stored ZIP
  members free of environment files, secrets, backups, runtime databases,
  transcripts, VCS internals, keys, and unsafe links.
- `lifecycle`: explicit legal edges, policy-pinned and freshness-bounded gates,
  cumulative artifact evidence, and durable-intent-bound `draft`/`live`
  transitions.
- `cad`: an engine-neutral part/project manifest plus a canonical
  `CadReleaseBundle` across deterministic and independent-review substrates,
  adding physical verification for critical claims. Foundation release checks cannot
  be waived.
- `panda`: injected-bearer HTTP adapter and outbox coordinator for draft import,
  `PublicationOutcome` identity, explicit-price publication, ambiguity
  handling, and exact active-listing readback.
- `ports`: narrow protocols for agents, CAD, evaluation, publishing, and
  fulfillment.

These contracts do not select a model, judge whether a game is fun, implement
Factory fulfillment, or certify a mesh merely because an upstream script exits
zero. Those decisions need adapters and domain evidence.

Alice, Bob, and Eve now execute these contracts at their real artifact and/or
publication boundaries while retaining their characterized creative state
machines. See the [adoption map](docs/ADOPTION.md) for the exact ownership and
compatibility matrix; “uses Foundation” is not presented as a completed flag-day
lifecycle migration.

## Quick start

Run all Foundation tests and inspect the registry:

```bash
PYTHONPATH=foundation/src python3 -m unittest discover -s foundation/tests -v
PYTHONPATH=foundation/src python3 -m inventor_core registry --root inventors
```

Build an immutable product manifest and reproducible Panda packet:

```bash
PYTHONPATH=foundation/src python3 -m inventor_core artifact path/to/product \
  --output path/to/artifact.json
PYTHONPATH=foundation/src python3 -m inventor_core pack path/to/product \
  path/to/product.zip
```

Programmatic adapters use the public `build_publish_packet()` and
`inspect_publish_packet()` functions. Operator status uses
`InventorStore.latest_publish_intent()` rather than querying Foundation's private
SQLite schema.

Create the next inventor:

```bash
PYTHONPATH=foundation/src python3 -m inventor_core new word-games \
  --name Ada --niche "printable word games" --root inventors
```

Generated inventors target Python 3.11 or newer. In an editable checkout their
state is always `<inventor>/.runtime/state.sqlite`, independent of the caller's
working directory. An installed inventor uses
`~/.local/share/autonomous-inventors/<id>/state.sqlite`; an explicit
`<ID>_RUNTIME` override must be absolute. Foundation itself remains compatible with
Python 3.9+. After installation, `<package> create <product-id>` registers a new
product at the initial lifecycle revision and `<package> status` lists products,
stages, revisions, and artifact binding.

Or install the local CLI:

```bash
python3 -m pip install -e foundation
inventor-foundation registry --root inventors
```

`inventor-core` remains an equivalent compatibility alias.

## Skills

- [`skills/cad`](skills/cad/) and [`skills/step-parts`](skills/step-parts/)
  are the single canonical copies previously carried by Bob. Bob keeps
  compatibility symlinks; new inventors use the Foundation paths directly.
- [`skills/product-to-cad`](skills/product-to-cad/) is the shared concept-to-
  manufacturable-CAD workflow. It separates form/beauty review from topology,
  fit, motion, slicer, safety, and physical-test evidence.

The current CAD scripts are valuable diagnostics, not a release certificate.
Read [skill provenance](skills/PROVENANCE.md) and the
[architecture](docs/ARCHITECTURE.md) before wiring a final gate.

## Safety-critical details

The default board-game graph carries its evidence floor forward: validation
requires rules, CAD, and printability; review and draft additionally require
playtest and novelty. Every supplied result must pass and identify the selected
artifact, even when it was not required by name. Every gate must match its
`GatePolicy` evaluator, exact version, and config hash, carry hash-bound evidence,
and fall within its clock policy. The default allows at most five minutes of
future skew; novelty expires after seven days and playtest evidence after 30
days. CAD-gated transitions additionally bind the canonical `CadReleaseBundle`
hash. `draft -> live` cannot change artifact bytes or durable intent and must
preserve the recorded draft's packet, artifact, inventor owner, design, root,
slug, current history, and project URL.

Call `Pipeline.advance`, not `InventorStore._transition`. When a product has an
active lease, its current token fences transitions, product-bound spend, and
publication preparation/effect issuance. Starting `sending` or `publishing`
mints a second opaque `effect_token`; only that attempt can record its response,
so a late completion cannot overwrite a corrected attempt. Lease acquisition
and renewal are capped at 24 hours; renewal extends the same fencing token.
Budget limits and time windows are immutable while active and use Foundation's clock.
Each first spend stores its policy window/limit and resulting balance. Repeating
the exact `spend_key` returns that captured result; changing any field under the
same key is a conflict. `InventorStore.budget_status()` reads policy, use, and
remaining balance without reserving spend.

Packets contain at most 4,096 source entries, are limited to 50 MiB on disk,
and enforce 95 MiB per expanded file and 512 MiB total expanded content. They
use fixed ordering, timestamps, permission modes, and `ZIP_STORED` so packet
bytes do not vary with zlib versions. Source reads walk parent directories with
no-follow handles where the host supports them. The importer opens the packet
without following path replacements, validates its canonical ZIP form,
embedded manifest, and every member, reapplies filename and content-secret
policy at send time, then uploads the exact byte buffer it hashed.

Draft import returns `PublicationOutcome(intent_id, receipt)`, not a
free-floating receipt. The lifecycle accepts it only when that durable intent
belongs to the product, is in the required outbox state, and stores the exact
receipt and packet. The same intent ID must reach `live`. A Foundation receipt records
both the packet SHA-256 and its embedded artifact SHA-256. This does **not**
repair a limitation in Panda: current import readback exposes neither identity
nor an idempotency key. If an import is accepted but its response is lost or
malformed, Foundation leaves the intent `unknown`; supplying a slug is not safe
reconciliation and the import is never retried. Panda must add idempotency or a
content-bound receipt to make that recovery safe.

Only Panda statuses explicitly classified as proven-no-effect can be treated as
rejection instead of ambiguity: `400`, `401`, `403`, `404`, `405`, `406`,
`410`, `411`, `412`, `413`, `414`, `415`, `416`, `417`, `421`, `422`, `426`,
`428`, `431`, and `451`. Redirects, conflicts, throttling, unexpected success
statuses, transport failures, and 5xx responses remain ambiguous. For the
public flip, ambiguity becomes `live_unknown`; one authenticated `draft`
readback never authorizes retry. `live` requires the exact current history plus
an active listing at the requested price, currency `USD`, and a non-empty SKU.
A proven publish rejection records the exact request in `live_attempts` before
permitting a corrected price.

Import metadata is allowlisted, bounded, and secret-scanned; Panda response
bodies are capped at 2 MiB and duplicate JSON keys are rejected. These checks
run before a response can produce a durable receipt.

Every one of the ten Foundation CAD checks has typed, engine-neutral pass semantics;
generic truthy measurements are not evidence. CAD manifests, requirements,
checks, measurements, and bundle hashes revalidate their nested finite-JSON,
path, version, and hash contracts so mutation after construction fails closed.

The three imported inventor snapshots are locked by byte count, executable/
symlink mode, commit, and canonical tree SHA-256 in
[`snapshots.lock.json`](snapshots.lock.json). CI runs
[`tools/verify_snapshot_locks.py`](tools/verify_snapshot_locks.py) offline and
fails if snapshot inventory, bytes, modes, manifest coverage, or commit pins
drift.

Credentials enter through a broker or environment injection at the adapter
boundary and must never be persisted in Git, manifests, prompts, traces, or
publish packets.
