# Foundation architecture

Inventors depend on Foundation; Foundation never imports an inventor. The
shared layer owns invariants and durable effects, while each inventor owns its
niche, taste, creative process, and stronger domain-specific evaluation.

## Target composition: Alice on Foundation

Alice shows the intended boundary between an inventor and its shared
infrastructure.

```text
+--------------------------------------------------------------+
| ALICE - INVENTOR-SPECIFIC                                    |
| owns what to invent and what "good" feels like               |
|                                                              |
| TASTE.md                  values and creative boundaries      |
| prompts + roles           how Alice thinks                    |
| game logic + evaluators   what Alice makes and tests          |
| workflow                  composes Foundation APIs            |
+-------------------------------+------------------------------+
                                |
                                | imports stable APIs
                                v
+--------------------------------------------------------------+
| FOUNDATION - SHARED BY EVERY INVENTOR                        |
| owns how work runs safely and repeatably                     |
|                                                              |
| state + leases + budgets   artifacts + evidence gates         |
| CAD + creation skills     publication + exact receipts        |
| registry + scaffolding    port interfaces                     |
+-------------------------------+------------------------------+
                                |
                                | calls ports
                                v
+--------------------------------------------------------------+
| ADAPTER IMPLEMENTATIONS                                      |
| connect Foundation ports to provider APIs                    |
+-------------------------------+------------------------------+
                                |
                                | call
                                v
+--------------------------------------------------------------+
| EXTERNAL SERVICES                                            |
| AI models | CAD, slicer, printer | Panda and Factory          |
+--------------------------------------------------------------+
```

The dependency direction is one-way: Alice imports Foundation; Foundation never
imports Alice. Foundation defines the ports. Their adapter implementations can
live with Alice or in a shared integration package; external platform behavior
does not move into Foundation.

## How Alice is built

1. Scaffold Alice's package, manifest, `TASTE.md`, workflow entry point, CLI,
   and starter test.
2. Add Alice's prompts, roles, game logic, evaluators, and reward hypothesis.
3. Compose the Foundation capabilities her workflow needs instead of rebuilding
   state, artifact, evidence, budget, CAD, or publication infrastructure.
4. Implement the required Foundation ports for models, CAD, evaluation,
   publishing, and fulfillment.
5. Test Alice's creative behavior and the shared Foundation invariants together.

Alice may add stages or strengthen gates, but cannot waive Foundation's
artifact, identity, spend, safety, or publication floors.

The same construction works for the next inventor: replace Alice's files while
reusing Foundation unchanged.

## Runtime flow

Alice asks Foundation to act. Foundation authorizes and records the operation,
an adapter performs it, and its receipt returns through Foundation for
verification before Alice can advance. Missing, stale, or ambiguous evidence
stops the flow instead of being treated as success.

This section describes the target composition, not a claim that migration is
complete. Alice currently executes Foundation at the content-addressed artifact
and canonical packet boundary while retaining her mature local workflow,
SQLite state, leases, evidence graph, and release authority. See
[ADOPTION.md](ADOPTION.md) for the exact current boundary.

## Ownership boundary

| Inventor owns | Foundation owns | Platform adapter owns |
|---|---|---|
| niche and customer | product identity and lifecycle | authentication and token refresh |
| taste and creative thesis | leases, revisions, events, budgets | API/version negotiation |
| prompts and roles | artifact packaging and provenance | remote retry/reconciliation calls |
| mechanic/domain generators | gate and receipt shapes | mapping remote DTOs to receipts |
| niche evaluators and thresholds | effect/outbox state | Panda, Grid, media, slicer, Factory transport |
| reward hypothesis | common safety/release floors | staging contract tests |

Foundation never imports an inventor. An inventor may add stages or stricter gates,
but cannot waive Foundation artifact, identity, safety, spend, or publication rules.

## Durable flow

```text
idea -> researched -> rules -> simulated -> built -> validated -> reviewed
                                                                    |
                         exact artifact + cumulative gates ----------+
                                                                    v
                     receipt-bound draft -> exact-history live readback
```

The default graph permits bounded repair edges, parking, and killing as well as
the forward path. Parking is not a shortcut: a parked product can only resume
the stage it left (or be killed). Its evidence floor is cumulative. `validated`
requires rules-lint, CAD, and printability; `reviewed` and `draft` require all
three plus playtest and novelty. Every result a caller supplies must pass and
identify the selected artifact, including optional results. Every supplied gate
must also match a declared `GatePolicy`: evaluator identity, exact non-floating
version, config SHA-256, maximum future-clock skew, and optional maximum age.
The board-game default allows five minutes of future skew, expires novelty
after seven days, and expires playtest evidence after 30 days. Gate evidence has
its own safe path and SHA-256. Changing bytes, evaluator configuration, or the
evidence clock therefore invalidates a prior pass rather than carrying it
forward.

`draft` and `live` both require a durable outbox intent ID, its exact stored
receipt, packet identity, and expected owner. The intent must belong to the
product and be `succeeded` for draft or `live` for live. `PublicationOutcome`
pairs this intent ID with the authenticated import receipt so adapters cannot
discard the durable identity. The `draft -> live` edge cannot change the intent
or artifact bytes. The public receipt must also preserve the recorded draft's
packet/artifact hashes, owner, design ID, root ID, slug, current-history ID, and
project URL. It must report that the published history is that same current
history and prove the requested active listing.

## Mutation, leases, and budgets

Every transition uses an expected revision. The raw store operation is the
private `InventorStore._transition` compare-and-swap primitive;
`Pipeline.advance` is the policy-bearing interface. Inventor code must not call
the primitive directly.

Workers acquire an expiring opaque random lease token. While a lease is active,
the exact current token fences transitions, product-bound spend, publication
intent preparation, and publication effect issuance. A missing, expired, or
replaced token cannot mutate on behalf of that lease. Lease renewal retains the
same token, and release only succeeds for the current token. Acquisition and
renewal TTLs are bounded to 1 second through 24 hours, preventing an accidental
effectively permanent claim.

Lease ownership and effect completion are separate concerns. Store schema v3
mints a fresh `effect_token` whenever an intent enters `sending` or
`publishing`. Every completion path from that in-flight state must present the
exact token, which is cleared when the attempt finishes. If a proven rejection
permits a corrected attempt, the correction receives a new token; a late
callback from the earlier attempt cannot overwrite it. Databases marked schema
v1 or v2 are upgraded to v3; corrupt, future, or unsupported versions fail
closed.

Budget authority belongs to a persisted `budget_policies` row, not to the
caller attempting a spend. Each policy fixes a bucket's limit and UTC window
and cannot be changed or overlapped until its active window ends. Budget and
lease-window decisions use Foundation's clock, never an inventor-supplied timestamp.
A first reservation supplies a globally unique `spend_key`, amount in micros,
phase, optional product, and note in one transaction. Its row snapshots the
policy start/end/limit and `remaining_after_micros`. Replaying the exact
reservation returns that original captured result even after later spends;
reusing its key with changed fields is a conflict. Product-bound first writes
use the same lease fence as state changes. Daemon, CLI, and human repair paths
therefore share one ledger and cannot pick their own limit or look-back
interval.

`InventorStore.budget_status(bucket)` is the observation path: it returns the
persisted policy plus active/used/remaining values through a read-only
connection. It does not insert a spend row, consume a `spend_key`, or change the
policy.

The event chain records the previous event hash and a canonical hash of every
transition. Verification checks both the chain and the final product row,
including revision, stage, artifact, metadata, and timestamps. It makes
accidental or unaudited mutation detectable; it is not a replacement for host
access control or signed remote receipts. Runtime directories created by Foundation
are private and SQLite database/WAL/SHM files are mode `0600` on POSIX hosts.

## Evidence model

A release fact has three layers:

1. The artifact manifest identifies exact files, bytes, executable bits, and
   a deterministic tree digest.
2. A `GatePolicy` pins evaluator/version/config and freshness, while each gate
   receipt binds evidence path/hash/time to the artifact. The CAD gate binds a
   canonical `CadReleaseBundle` over its manifest, exact validator policy, and
   all substrate-specific receipts rather than trusting a Boolean.
3. The Foundation Panda receipt identifies both packet and embedded artifact hashes,
   inventor owner, design/root/history IDs, status, project URL, and observation
   time. The coordinator reads, verifies, hashes, and uploads one immutable byte
   buffer, so this local receipt identifies the bytes actually sent.

Only authenticated Panda readback where `status=public`,
`published_history_id == current_history_id`, and the listing is active at the
persisted request's exact price with currency `USD` and a non-empty SKU supports
a `live` transition. Panda does not currently echo the packet or artifact hash,
so its response is not yet an independent remote attestation of stored bytes.

## Artifact packet boundary

Artifact discovery is fail-closed around paths and content. On capable POSIX
hosts, each source path is opened component-by-component from a root directory
descriptor with `O_NOFOLLOW`; fallback hosts compare lstat/opened identities.
The final packet is likewise read through a no-follow regular-file identity
before hashing. Symlinks, parent-directory replacement, path
traversal/backslash ambiguity, destination-inside-source packaging, and
mid-hash/mid-pack replacement are rejected. Default exclusions are
case-insensitive and cover environment/auth/credential/token files, source
backups, private keys, runtime databases, bytecode, transcripts, inputs, editor
state, and VCS internals. A high-confidence content scan rejects recognized key
and credential patterns without printing values.

Foundation caps a source artifact at 4,096 entries, each expanded member at 95 MiB,
total expanded content at 512 MiB, and the final upload packet at 50 MiB. The
ZIP contains sorted files plus one reserved `_inventor-artifact.json`; fixed
timestamps and `0644`/`0755` modes make metadata reproducible. Members use
`ZIP_STORED`, avoiding zlib-version-dependent DEFLATE output. Before upload,
the Panda adapter also rejects ZIP comments, extra/encrypted/non-stored members,
revalidates every member hash, size, permission, inventory, total, and artifact
digest from the in-memory packet bytes, and reapplies excluded-name and secret-
content rules to every payload. A hand-built manifest-valid ZIP therefore
cannot bypass the builder's publishability policy.

## Publication safety

Panda import is synchronous and non-idempotent. Foundation first proves that the
packet artifact is the product's selected artifact, then writes the exact
metadata, packet hash, embedded artifact hash, expected owner, and API origin to
an intent. Entering `sending` persists a fresh effect token before POST. Import
always specifies `status=draft`; a successful adapter call returns
`PublicationOutcome(intent_id, receipt)`.

```text
planned -> sending -> succeeded (proven draft)
              |  \
              |   `-> rejected             allowlisted proven-no-effect status
              `----> unknown               every ambiguous/unexpected outcome

succeeded -> publishing -> live            exact public readback
                 |     \
                 |      `-> succeeded       proven no effect; attempt retained
                 `--------> live_unknown    every ambiguous/non-public outcome
```

The proven-no-effect status allowlist is deliberately explicit: `400`, `401`,
`403`, `404`, `405`, `406`, `410`, `411`, `412`, `413`, `414`, `415`, `416`,
`417`, `421`, `422`, `426`, `428`, `431`, and `451`. Redirects, `409`, `429`,
other unexpected statuses (including unexpected 2xx), transport failures, and
5xx responses never authorize another non-idempotent request. A proven import
rejection becomes `rejected` and requires corrected content/new packet; it is
not treated as a successful draft.

There is currently no safe automated exit from an unknown import. Authenticated
design readback exposes neither the uploaded packet/tree hash nor an idempotency
identity, so an operator-supplied slug cannot prove which bytes created it.
Foundation's Panda reconciler therefore fails closed and never reissues that POST.
Panda must expose a content-bound receipt or accept a durable idempotency key
before import reconciliation can be automated.

Draft-to-public persists an exact request containing price, expected owner, and
API origin and a fresh effect token before POST. An allowlisted proven-no-effect
response appends that request/error/time to `live_attempts`, clears the active
request/token, and returns the same durable intent to its proven draft so a
corrected explicit price can be made. Any potentially accepted, oversized,
duplicate-key, or malformed outcome remains `live_unknown`. Authenticated GET
reconciliation can resolve it only when the exact draft history is public and
the active listing proves the requested price, `USD`, and a non-empty SKU. One
GET that still reports draft does not prove the publish POST failed and never
authorizes a second POST.

Import metadata is an allowlist: required title (maximum 300 characters),
description (20,000), category (100), prompt (50,000), license (100), and at
most 50 unique tags of 100 characters. Unknown fields, empty supplied values,
duplicate tags, and secret-shaped normalized content are rejected before HTTP.
Response bodies are capped at 2 MiB, response status/header/body types are
validated, and duplicate JSON object keys are rejected before any durable
receipt is accepted.

The backend currently lacks scoped service principals for multiple autonomous
creators. `owner_id` verification prevents a token for the wrong person/agent
from silently publishing, but credential provisioning and refresh remain a
platform adapter gap.

## CAD boundary

Foundation supports build123d, CadQuery/cadpy, and future engines through one manifest:
canonical parts, placed assemblies, STEP and per-part meshes, topology
expectations, materials/orientations, fits, motions, print profile, tool/skill
versions, and unresolved physical claims.

Release uses a `CadReleaseBundle`, whose SHA-256 canonically covers the project
manifest, complete validator requirements, and all receipts. A CAD lifecycle
gate must bind this bundle hash in both its evidence object and evidence hash.
The bundle requires a non-empty validator policy and an exactly matching set of
receipts. Each policy entry pins validator name, exact version, configuration
SHA-256, substrate, and named checks. It cannot waive Foundation's `manifest`, `brep`,
`mesh-topology`, `dimensions`, `interference`, `bed-packing`, `slicer`,
`form-review`, and `safety` floor; any critical physical claim also requires
`physical-claims`. Duplicate validators/checks, missing checks, stale artifact
hashes, version/config drift, and any `held` or `failed` result block release.

The three independent substrates are enforced, not descriptive tags.
Deterministic tools own manifest/BREP/mesh/dimension/interference/bed/slicer
checks; independent review owns form and safety; critical claims add the
physical substrate. A Foundation check appearing under the wrong substrate blocks
release. Each check carries typed measurements and an evidence path/hash that
must exist in the manifest's `evidence_files` map.

All ten Foundation checks define typed minimum/pass semantics, including exact
Booleans, finite numeric bounds, counts, and non-empty review scope where
appropriate; `{"checked": true}` cannot stand in for measurements. Release and
bundle hashing revalidate nested manifest, requirement, receipt, check, and
measurement contracts, including finite JSON, depth/size, safe paths, pinned
versions, and hashes. Mutating a nested object after dataclass construction
therefore cannot preserve a valid bundle.

The project manifest pins the slicer/print profile hash and declares at least
one physical claim. A passed claim must carry both a safe relative evidence path
and evidence SHA-256. Process exit zero, a model's opinion, watertightness alone,
or an exception converted to zero interference is insufficient. Slicer-backed
DFM and calibrated fit evidence are separate from deterministic form/beauty
review. Compliance, fatigue, friction, living hinges, snap life, and
print-in-place release remain `held` without simulation or physical coupons for
the exact material/process.

## Scaffold/runtime boundary

New scaffolds target Python 3.11+ even though the dependency-free Foundation package
supports Python 3.9+. Runtime placement never depends on the process working
directory: an editable checkout discovers its `inventor.json` and uses
`<inventor>/.runtime/state.sqlite`; an installed package uses
`~/.local/share/autonomous-inventors/<id>/state.sqlite`. The optional
`<ID>_RUNTIME` root must be absolute. This prevents two launch locations from
silently creating separate queues. The generated CLI exposes `init`,
`create <product-id>` (register at the initial stage/revision), and `status`
(list product, stage/revision, and artifact binding).

## Registry and snapshot boundary

Registry strings are bounded and reject ASCII control characters. An upstream
snapshot must use an absolute credential-free HTTPS repository URL without
query/fragment, a full lowercase commit SHA, and an ISO import date. Entrypoints
use an allowlisted interpreter shape and their resolved module/script must be a
real file contained by the inventor folder; inventor-folder, manifest, or target
symlinks cannot escape that boundary.

Imported source preservation is independently enforced by
[`../snapshots.lock.json`](../snapshots.lock.json). The offline
[`../tools/verify_snapshot_locks.py`](../tools/verify_snapshot_locks.py)
canonicalizes every tracked/unignored snapshot path with its mode, byte count,
and SHA-256, then verifies the tree digest, upstream commit, aggregate counts,
and exact coverage of all `upstream-snapshot` manifests. CI runs this verifier,
so an added, removed, mode-changed, or byte-changed imported file fails before
migration code is trusted.

## Platform boundary

- `autonomous-vibe`/cadpy: generation and artifact donor; no Tauri dependency.
- Panda backend: HTTP adapter for import, slice, upload, publish, catalog.
- Harness/Grid: model/agent adapters, never embedded control planes.
- media gateway: experimental adapter only after webhook auth/idempotency fixes.
- Factory/Store: fulfillment port only; its backend was not available to audit.

See [ECOSYSTEM.md](ECOSYSTEM.md) for pinned evidence and contract drift.
