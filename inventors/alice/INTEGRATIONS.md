# Workshop, storefront, CAD, and simulation integrations

This map separates current production contracts from useful experiments. Alice
must not revive a retired path simply because its code is convenient.

> **Current publishing ruling (2026-08-24).** Alice sends inspected models and
> product facts only through the shared Workshop. Factory generates use-case,
> story blocks, images, and video on the server. The former
> `page_builder.ShopDoorAdapter` mutation path is retired and fails before any
> subprocess or remote write; it remains only for authenticated read-only
> reconciliation of an already-bound legacy draft. Any later description of
> `vibe-ideas/board-game/tools/publish.py` as an active writer is historical
> archaeology, not an operating instruction.

Names containing `panda` below are immutable upstream repository identifiers,
not Alice or Workshop vocabulary. The active commerce boundary is a storefront
adapter. The implementation class `ShopDoorAdapter` retains its historical name
for compatibility.

## Repository authority

| State | Repository | Alice decision |
|---|---|---|
| Hot | `autonomous-ai/panda-social-backend` | Storefront API, import, slicing, publication, and order authority |
| Hot | `autonomous-ai/panda-social-cc-agent` | Production CAD gate, artifact identity, worker/CDN patterns |
| Hot | `autonomous-ai/ecm-website` | Canonical `/factory` customer experience |
| Warm | `autonomous-ai/panda-mobile` | Consumer client, not an inventor contract |
| Dead redirect | `autonomous-ai/panda-website` | Do not integrate |
| Retired | `autonomous-ai/panda-ccr` | Do not integrate; token pool superseded it |
| Parked | `autonomous-ai/panda-social-pi-agent` | Historical engine experiment only |
| Frozen/public | `autonomous-ai/autonomous-vibe` desktop | Historical UX/code reference only |
| Maintained reference | `autonomous-org/projects/leonardo` | Reuse leases, process isolation, receipts, immutable packets |
| Team experiment | `reinSPQR/vibe-ideas` | Borrow board-game content, physical manifests, and critique patterns |
| Team inventor | `nohope88/text2game` | Connected CAD/DFM runtime at an exact clean commit: reuse its rules, CAD, gate, render, and print-preparation stages; never its legacy publisher |
| Team CAD work | `peterat617/text-to-3d` | Borrow verified CAD helpers with the corrections below |
| Team CAD toolchain | `nohope88/text2cad` | Clean, commit-pinned runtime prerequisite for text2game phases 2/3 CAD, measurement, gating, and render helpers; exclude its old admin/completion logic |

## Text2game invention to Workshop model-only draft

Alice treats the internal repositories as one R&D library, not as mutually
exclusive products. The supported board-game path deliberately composes their
strongest parts:

```text
Alice accepted game and exact rules
  -> text2game's separated rules, CAD, repair, gate, render, and slice stages
  -> deterministic, hash-preserving Workshop product package
  -> shared Workshop model-only draft import
  -> Factory server enrichment for copy, images, and video
  -> authenticated private storefront draft readback
  -> Dee reviews and clicks publish
```

The exporter takes Alice's structured accepted rules as authority; it does not
lossily reinterpret `gdd.md`. It copies only verified in-root regular files,
binds the source repository commit and every accepted rule/CAD artifact hash,
and creates the Vibe workspace atomically. It never calls
`text2game/publish.py`, never changes the Vibe queue to `shipped`, and never
performs a remote write. A separate Alice gate must accept the exported
workspace before Workshop may import its model-only draft.

This is a connected runtime, not only an export format. The Alice integration
was reviewed against `nohope88/text2game` commit
`0285137beedb4602f0cb06ebb18046ff018c41b6`; an enabled deployment must name that
exact 40-hex commit (or undergo a new review for a new pin). Startup and every
operation reject a symlinked, dirty, or differently checked-out source tree.
Alice verifies the pinned trees, then copies an explicit reviewed runtime
allowlist—not the full repositories—into one private directory per durable
operation. Both legacy publishers and credential-like backups are outside that
allowlist. Alice never runs in the shared checkout or shares upstream `out/`
between candidates. The exact accepted `gdd.md`, `components.json`, and
`mechanisms.json` are staged first. The pinned non-LLM `consistency.py` must
produce a well-formed report with no `high` finding before phase 1 is allowed to
start.

The sibling `nohope88/text2cad` checkout is independently required clean and
pinned (the reviewed checkout is commit
`fb9bc30e93afb4296693db58fb53cc1d66afeb1e`). Its selected gate/CAD-skill
subtree, CAD Python interpreter, slicer, slicer profile, Git, Codex executable,
and dedicated Codex home are explicit adapter inputs rather than ambient tool
discovery. Executable/profile bytes and both selected repository trees are
rechecked before and after every phase. Upstream `uv run ...` and plain
`python` calls resolve through operation-local shims to the exact pinned CAD
interpreter, so no dynamic package environment is certified accidentally.

Each of phases 1, 2, and 3 is launched separately and must satisfy its own
receipt/artifact gate before the next begins. Every launch first records a
durable `sending` state; a crash or timeout is reconciled from exact output and
is never converted into a blind rerun. The adapter forces `CODEX_JOBS=all`,
`CODEX_SANDBOX=workspace-write`, and `CODEX_FALLBACK=0`. Thus text2game's Codex
workers get the copied workspace they need without running in the shared source
checkout, and cannot silently fall back to its Claude lane, whose upstream tool
grant includes host Bash. Shared-vault
ingest, concept video, Telegram/publisher credentials, and both text2game
publish paths are disabled or rejected.

The pinned upstream login preflight checks only for the existence of
`~/.codex/auth.json` and does not honor `CODEX_HOME`. Alice therefore places a
non-secret marker at that path inside the private operation `HOME`; it never
copies the real auth file. The Codex process itself still receives the
owner-only dedicated `CODEX_HOME` and must pass an actual login-status probe.

`text2game/publish.py` is intentionally excluded. It uses a legacy importer
whose draft behavior cannot be verified from the current source, can return
success when owner credentials are missing, writes its local receipt before all
viewer work finishes, and has no operation-key reconciliation or immutable
rich-page readback. Its useful invention and CAD work remains reusable; its
publisher is not the production boundary.

## Workshop draft and future publication

The historically named `pack.product` task uses Workshop's canonical artifact
boundary. It archives Alice's exact inspected production manifest as
`product.json`, requires that entry's SHA-256 to equal Alice's already-reviewed
`production_packet_hash`, and emits `_workshop_pack` with the content-addressed
artifact and archive identities. The storefront adapter calls the compatibility
API `inspect_pack()` and compares the complete binding before the runtime creates
a durable effect intent. This adds a shared, reconstructable artifact contract
without replacing Alice's stricter release policy, evidence ledger, or effect
state machine.

For durable compatibility, Alice can still read and dispatch already-stored
`publish.packet`, `publish.invoke_pipeline`, and `publish.verify_page` rows.
New work is always `pack.product`, `send.to_shop`, and `send.verify_shop`; these
persisted task names remain compatibility identifiers, not Workshop stages.

For the always-on worker, the Workshop package is also part of Alice's
service identity. Installation passes the explicit repository `src` checkout to the
sealed worker: identity checks continue to hash that mutable checkout, while
all Alice and `inventor_workshop` imports used for execution resolve from the
owner-only release snapshot. The bootstrap disables Python site initialization
with `-I -S` before adding that snapshot, preventing editable-install `.pth`
hooks from pre-caching an unsealed Workshop module.

Alice uses Workshop's shared model-only import and the normal public flip. It
does **not** contain a copywriter, image generator, video generator, or
product-page renderer:

```text
verified production workspace + slug
  -> Workshop sealed product packet
  -> private model-only storefront draft
  -> authenticated readback + remote artifact hashes for that exact history
  -> prototype print + production validation of that draft history
  -> Dee's one-click review and public flip of the same history (current)
  -> Factory server enrichment for copy, images, and video
  -> capability-gated automatic Vibe public flip (future `live` mode)
  -> anonymous storefront readback -> Alice public-page verification
```

Workshop is the only supported mutation entry point. It calls the backend's
model-only import service without a thumbnail multipart field and without
`use_case`/`story_blocks` writes, so CDN snapshots, `_tree.json`, GLB,
`design_history`, and unique slugs retain their production semantics while
Factory remains authoritative for generated page media and copy.

The deployed enrichment worker remains out of band and can add further public
merchandising. The San Francisco chess set and Arrows Across the River are the
reference pages.

Alice persists a caller operation key and immutable packet hash before the
first write. Current storefront writes are not server-idempotent, so a timeout
or disconnect after a create, message, edit, or publish is terminally
`ambiguous`: the worker does not retry. An operator or a dedicated reconciler
must read remote state and attach the original remote id before work resumes.
Successful publication is also not enough. Alice polls the anonymous public
design record and requires the expected price, active listing, hero/use-case
media, three story sections with media, print specifications, assembly parts,
and at least five visual assets before recording `page_ready`. Video is checked
when the existing pipeline produces it, but current reference pages show that
video is not a guaranteed output.

Catalog category is an explicit warning rather than a page blocker: Arrows has
no category and the San Francisco set has historically shown the wrong one.
Alice should provide the intended category upstream and keep the warning open
for merchandising/SEO cleanup.

`alice.page_builder.ShopDoorAdapter` is a retired compatibility reader; its
class name and the old `PageBuilderAdapter` alias remain only for legacy
receipts. New invocations fail before local preparation or remote mutation. An
existing exact sidecar may be authenticated and reconciled read-only; a bare
`published.json` is ambiguous and is never adopted. Historical Vibe source and
helper pins remain evidence for that reconciliation only. They cannot activate
`publish.py`, `publishdesign`, cover uploads, page copy, or a second importer.
All new models go through Workshop.

A known game remains bound to its exact storefront design ID and history. An
identity mismatch, missing capability, or unknown outcome must never cause
Alice to create another design. All Alice-authored descriptions must end with
the exact suffix `By Alice.` with no trailing whitespace.

`alice.vibe_pipeline.VibePipeline.run` still owns the earlier text-only
create/resume flow where needed. The release worker uses `publish_existing`:
its immutable packet must contain `manufacturing.vibe_design` with the already
verified `design_id`, `slug`, `history_id`, `project_url`, `project_sha256`, and
artifact hashes from the draft receipt and subsequent physical evidence. The
adapter recalculates the packet hash before it sends anything, calls publish
without another generation job, and rereads the finished public page. This
prevents a newly generated, unprinted artifact from replacing the game that
cleared production.

### Draft import boundary

Alice has no low-level draft importer. `ShopDoorClient.create_draft` and its
`FactoryClient` alias fail before archive access, authentication, or HTTP. The
shared Workshop owns the model-only import request, durable intent, and Stamp.
Alice consumes the resulting design/history/project identity through read-only
reconciliation. This keeps an inventor from attaching local thumbnails,
use-case copy, story blocks, or video to the Factory page.

### Current risk envelope and desirable backend hardening

The provider import endpoint does not honor an idempotency key. Workshop owns
the durable pre-write intent and treats a timeout after commit as ambiguous;
Alice cannot route around that fence with her retired client or page writer.

Public publishing is currently **blocked**, not merely degraded. The checked
storefront deployment does not advertise both public-write capabilities Alice
requires: `packet_hash_bound_publish` and `sku_currency_bound_publish`. The
write boundary must atomically compare the caller's expected history and
project, apply the exact reviewed SKU, price, and USD currency, and return those
fields with the accepted history/project/packet/policy binding. Factory's page
enrichment happens only after that write and is consumed through readback; it
is never inventor-authored or a publish precondition. The Vibe adapter fails
capability preflight before its POST when any part is missing. A partial local
backend change that merely accepts extra JSON fields is not sufficient and is
not deployment evidence. The production semantic change needs explicit owner
authorization, review, tests on the required Go toolchain and Mongo environment,
and deployment before Alice can be marked live-ready.

These limitations do not require a second page-generation system or a
permanent per-product manual approval. Once the backend contract is real, the
Vibe adapter will still use a durable one-shot write, state the exact price,
and stop for reconciliation whenever a result is ambiguous.

The backend should still be hardened to enforce:

1. `idempotent_import`: unique `(owner_id, idempotency_key)` with an immutable
   request hash; same request returns the original receipt, different request
   under the key returns `409`.
2. `packet_hash_bound_publish`: publish atomically accepts and compares the
   expected design/history/project, publication packet hash, and policy hash,
   then returns all of them.
3. `sku_currency_bound_publish`: the same write atomically applies and echoes
   the exact reviewed SKU, price in cents, and `USD`; no estimated default or
   later listing mutation may silently replace them.
4. `server_enrichment_readback`: after publish, Factory-generated copy, images,
   and video are available through authenticated and anonymous reads without an
   inventor mutation endpoint.
5. `order_to_print_job`: each paid SKU/order maps to the exact published
   CAD/BOM packet and one idempotent print job.

`alice.shop_door.ShopDoorClient` is now a read/reconcile compatibility client.
Its direct `create_draft` method fails before reading an archive or opening
HTTP, and the old `alice.factory.FactoryClient` alias cannot revive it. Only
Workshop may perform the model-only draft import. The capability-gated
`publish_live` method describes the stronger future API, while authenticated
GETs preserve read-only reconciliation of existing server content.

On an ambiguous current import, Alice records `ambiguous`, inspects the owner's
drafts and retained `alice-provenance.json`, and never retries automatically.

## CAD creation and acceptance

The production CREATE gate is `panda-social-cc-agent`'s CADCode `create-check`.
It requires solid finite positive-volume geometry, no blocking warnings,
overall STEP/STL/metadata, STEP and STL per named part, unique part names,
review renders plus X/Y/Z sections, no disconnected assembly parts, and a
source-bound receipt. Alice adds independent hashes for every per-part STL
because the current final manifest does not bind placed parts strongly enough.

The canonical Alice CAD receipt is `alice.cad-verification.v1`:

```text
run_id, attempt_id, candidate_id, source_sha256
artifacts[]: role, path, sha256, bytes
geometry: is_solid, volume_mm3, bbox_mm
checks[]: id, kind, pass|fail|inconclusive, runtime, input hash,
          observed value, threshold, receipt hash
physical_condition_manifest_sha256
interaction_matrix
open_physical_items[]
repair_rounds
slice profile, time, mass, volume, filament, dimensions, parts, gcode hash
overall: verified|held|failed
```

Required inconclusive checks and unavailable slicers yield `held`, never pass.
Alice immediately rehashes accepted source, STEP, STL, parts, renders, manifest,
and ZIP before upload.

### `text-to-3d` lessons Alice keeps

Peter's current `main` at
`f18aebe4698d92ffccf07d94e2d624b08d30e667` is a CAD skill and validator
library, not a second inventor or publisher. Alice selectively vendors/adapts
its pure fit derivations and STL topology checks, and borrows its ordered
project-verification and motion-manifest contracts. The fit table is carried as
a versioned printer/material/nozzle calibration profile; its 0.4-mm-nozzle
defaults are not universal manufacturing truth.

The transplanted implementation lives in `src/alice/cad_validation.py`; its MIT
attribution is retained in `THIRD_PARTY_NOTICES.md`. Alice kept the dimensionally
correct fit derivations, strict STL topology/body checks, and explicit
motion-evaluator outcome contract. It did not copy Peter's renderer, unlocked
JSON budget/cache/lock state, or any path that treats a missing body, absent
layout, mesh error, or collision-evaluator exception as a pass.

Useful checks include fresh project verification, bed fit, mesh inspection, and
motion/collision. Alice wraps them with stricter contracts because the current
experiment has known false-success modes:

- remove stale `__cadgen__` output before every fresh generation;
- isolate a candidate from stale generators elsewhere in the worktree;
- fail bed-fit when expected parts/layout entries are absent;
- treat nonmanifold or unexpected shell/body count as failure;
- turn boolean-intersection exceptions into `inconclusive`, never zero
  collision;
- keep threads, snap compliance, living hinges, and friction as physical open
  items until a suitable real test exists;
- keep budgets in Alice's transactional store, not an unlocked JSON file.

The two CAD layouts are not interchangeable. Peter's current scripts expect a
build123d/cadgen `<slug>.step.py` plus `*_lib.py`/`part_*.step.py` tree, while
text2game emits CadQuery `parts/<id>.py`, assembled STEP, and
`fe_parts/<id>.stl`. The first operational draft keeps text2game's generator
and runs the hardened Peter-derived checks over its exported meshes. A
build123d backend can be evaluated later against the same fixed Alice receipt;
it does not block the draft pipeline.

`vibe-ideas` contributes the distinction between canonical parts (printability)
and placed instances (interactions), plus physical-condition manifests. Every
relevant part pair needs a runnable collision, clearance, contact, or motion
check—or an explicit open item.

## Digital game adapter

The digital adapter accepts an executable game definition and seeded policies,
then emits typed metrics and replayable traces. OpenSpiel is the initial
reference for search/RL and games with explicit state/action contracts; Ludii
is the historical/ludeme reference. Social, dexterity, and hidden-communication
games may need custom engines and earlier human escalation.

Required output includes input and implementation hashes, seed, engine version,
players/policies, game count, completion/stalemate rate, duration distribution,
seat/faction win rates, first-player advantage, decision entropy, repeated
states, dominant strategy search, exploit traces, and confidence limits.

## Future fulfillment adapter contract

No operational order reader, printer, QA, or shipping adapter is present in
this checkout. The configured command slots are contract boundaries, not proof
of a working fulfillment deployment.

The other production adapters are equally explicit: diagnostics must attest
licensed/cited source readback, independent prior-art search, deterministic
rules validation, executable seeded simulations, authenticated blind-human
results, artifact-hash readback, authenticated market evidence, and
authenticated external outcomes. A command that merely returns `ready: true`
cannot activate draft or live mode.

The current order boundary consumes a paid order containing the confirmed
publication id, packet hash, exact SKU, quantity, and opaque destination
reference. It fans out one immutable intent keyed by a one-way hash of the
order id. That intent contains the published artifact map plus the hash-verified
per-set manufacturing slice: process, print profile, canonical material
specification, complete BOM paths and quantities, and packing instructions. The
print, authenticated QA, and shipment receipts must echo that exact recipe and
its hashes in addition to the intent, packet, SKU, and quantity. Repeated polls
of the same order resolve to the same print and shipment tasks. Payment and
address data remain behind the storefront adapter. Detailed slicer, machine, lot, cost, failure,
support, and return measurements arrive through the separate outcomes contract
rather than being inferred from shipment success.

Readiness derives `order_to_print_job` only when authenticated, version-matched
diagnostics prove the primitives on both sides: `delivery` must advertise
`paid_order_readback`; `print_fulfillment` must advertise
`authenticated_manufacturing_readback`,
`idempotent_print_by_operation_key`, `reconcile_print_by_operation_key`, and
`reconcile_qa_ship_by_operation_key`. A self-asserted composite capability is
ignored. Draft and live physical effects separately require CAD
`idempotent_cad_by_operation_key`/`reconcile_cad_by_operation_key` and print
prototype/production idempotency plus reconciliation capabilities. Every first
effect and reconciliation payload is bound by `effect_operation_key`,
`task_input_sha256`, and `reconcile_only`.

## Repository pieces deliberately excluded

- `vibe-ideas`' `publish.py` and compiled backend import bridge are the board-
  game draft entry point. Its local `published.json` alone is not production
  truth; authenticated backend readback and remote artifact hashes are.
- `text2cad`'s CAD libraries are a text2game runtime prerequisite, but its old
  admin route and log-string/timeout completion markers are excluded. A timeout
  is not success.
- `autonomous-vibe` is frozen; Alice integrates the live CAD worker and backend,
  not the desktop app.
