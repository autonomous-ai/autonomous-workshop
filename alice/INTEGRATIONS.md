# Panda, Vibe, Factory, CAD, and simulation integrations

This map separates current production contracts from useful experiments. Alice
must not revive a retired path simply because its code is convenient.

## Repository authority

| State | Repository | Alice decision |
|---|---|---|
| Hot | `autonomous-ai/panda-social-backend` | Factory API, import, slicing, publication, and order authority |
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

## Text2game invention to existing rich-page draft

Alice treats the internal repositories as one R&D library, not as mutually
exclusive products. The supported board-game path deliberately composes their
strongest parts:

```text
Alice accepted game and exact rules
  -> text2game's separated rules, CAD, repair, gate, render, and slice stages
  -> deterministic, hash-preserving export into a Vibe board-game workspace
  -> vibe-ideas board-game/tools/publish.py <slug>
  -> authenticated, complete private Factory draft
  -> Dee reviews and clicks publish
```

The exporter takes Alice's structured accepted rules as authority; it does not
lossily reinterpret `gdd.md`. It copies only verified in-root regular files,
binds the source repository commit and every accepted rule/CAD artifact hash,
and creates the Vibe workspace atomically. It never calls
`text2game/publish.py`, never changes the Vibe queue to `shipped`, and never
performs a remote write. A separate Alice gate must accept the exported
workspace before the existing rich-page adapter can run.

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

## Existing rich-page draft and future Vibe public publish

Alice uses the production operator already built in `reinSPQR/vibe-ideas` and
the normal Vibe public flip. It does **not** contain a second copywriter, image
generator, video generator, or product-page renderer:

```text
verified production workspace + slug
  -> vibe-ideas board-game/tools/publish.py <slug>
  -> private Panda/Vibe draft with rules, use case, story, specs, and covers
  -> authenticated readback + remote artifact hashes for that exact history
  -> prototype print + production validation of that draft history
  -> Dee's one-click review and public flip of the same history (current)
  -> capability-gated automatic Vibe public flip (future `live` mode)
  -> deployed page observer/enrichment, if produced
  -> anonymous Factory readback -> Alice public-page verification
```

The existing draft operator is the supported local entry point. It calls the
hot backend's own import services, so CDN snapshots, `_tree.json`, GLB,
thumbnails, `design_history`, and unique slugs retain their production
semantics. It also fills the current product-page fields from the production
workspace: complete `RULES.md`, the use-case block, rules walkthrough story
blocks, print specs, description, and approved covers. Alice invokes that
operator; it never reimplements those transformations.

The deployed enrichment worker remains out of band and can add further public
merchandising. The San Francisco chess set and Arrows Across the River are the
reference pages.

Alice persists a caller operation key and immutable packet hash before the
first write. Current Vibe/Factory writes are not server-idempotent, so a timeout
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

`alice.page_builder.PageBuilderAdapter` owns the private-draft handoff. It is
available only in `draft` or `live`. Its reviewed configuration pins the exact
clean Vibe Git commit, interpreter bytes, `publish.py`, its local import closure
(`journal.py`, `telegram.py`, and `animation_gate.py`), the Git executable, and
the compiled `publishdesign` helper. Its command is exactly one absolute
interpreter followed by that checkout's absolute
`board-game/tools/publish.py`; wrappers, flags, extra arguments, and another
operator path are rejected. Alice internally adds fixed Python isolation flags,
appends only `<slug>`, and never uses `--force`. Untracked files under the tools
directory, bytecode caches, hidden index state, replacement refs, source drift,
or a missing/mismatched helper all fail readiness. The operator must statically declare
`RULES_ARCHIVE_CONTRACT = "project-rules-byte-exact-v1"`; Alice pins its source
hash against configuration and rechecks the complete execution boundary
immediately before the import. The reviewed
upstream change is preserved in
`integrations/vibe-ideas-exact-rules.patch` because the current maintainer
checkout cannot push to that repository. For ordinary Vibe workspaces, the
source queue must still say `shipped`. A text2game export can bypass that older
pre-draft owner gate only when its Alice receipt, complete artifact map,
project hash, rules hash, root `idea.json` copy, source-artifact manifest,
operation key, and input hash all match; the operator does not mutate the queue
or claim an owner shipped it. `gate.json` must still
pass. Readiness also requires an authenticated read of a configured private
draft whose owner and current history match exactly and which has no published
history. `PANDA_OWNER_ID` must be that same owner; backend and GCS inputs are
explicit owner-only local files, and a Vibe-workspace `.env` is forbidden so it
cannot rehydrate messaging or process-injection variables. Telegram remains
forced off for the Alice invocation. The CAD and DFM receipts must agree on
a relative-path artifact hash map. Alice hashes the whole project, writes a
small `alice-provenance.json`, persists a canonical input hash and operation
key, then authenticates back to the draft and streams every accepted artifact
plus provenance from its immutable `project_url` to verify the bytes. The
receipt binds `design_id`, canonical remote `slug`, `history_id`, `project_url`,
`project_sha256`, artifact hashes, and the rich-page fields. A local
`published.json` without Alice's matching sidecar is ambiguous and is never
adopted automatically. The CDN fetch is intentionally anonymous and accepts
only a configured credential-free HTTPS host with redirects disabled.

This first-import path is never a revision fallback. A known game is durably
bound to its exact Factory design ID and canonical slug; any later improvement
must append a history to that record or stop. Blindcap is currently public, and
the deployed version-import route immediately publishes a replacement history,
so its improvements remain local until Factory advertises an atomic staged-
version capability that preserves the old public history for review. A 404,
identity mismatch, collision-suffixed slug, or missing capability must never
cause Alice to create another design. All Alice-authored descriptions must end
with the exact suffix `By Alice.` with no trailing whitespace.

The current Alice checkout does not execute `publishdesign -dry-run` during
`doctor`: adding that credential-bearing Mongo/GCS probe was not authorized by
the execution boundary. Before operational activation, an accountable operator
must run the pinned helper's documented read-only dry run and verify the exact
owner, draft status, database, and bucket. It must be a first-import dry run
over a nonempty absolute project archive with positive byte count and one or
more absolute cover paths; content-only probes do not qualify. Alice accepts
only a canonical, owner-only manual receipt whose configured SHA-256 binds that
captured result to the exact Vibe/operator/helper, backend config, and GCS
credential hashes. The receipt is revalidated in `doctor` and immediately
before the effect; no receipt, stale local binding, or changed byte can claim
draft readiness.

`alice.vibe_pipeline.VibePipeline.run` still owns the earlier text-only
create/resume flow where needed. The release worker uses `publish_existing`:
its immutable packet must contain `manufacturing.vibe_design` with the already
verified `design_id`, `slug`, `history_id`, `project_url`, `project_sha256`, and
artifact hashes from the draft receipt and subsequent physical evidence. The
adapter recalculates the packet hash before it sends anything, calls publish
without another generation job, and rereads the finished public page. This
prevents a newly generated, unprinted artifact from replacing the game that
cleared production.

### Low-level draft import

The live draft endpoint is:

```http
POST /api/v1/designs/import
Authorization: Bearer <dedicated Alice owner token>
Content-Type: multipart/form-data

file=<zip>
status=draft
title=<title>
description=<description>
category=<category>
tags=<repeatable>
license=<license>
prompt=<provenance-safe prompt>
```

Alice always sends `status=draft`; omission currently defaults to public. The
archive safety ceiling is 95 MiB, with a generator defining `gen_step` or a
`project.json`. Recommended retained artifacts are `project.json`, `spec.md`,
canonical assembled STL, GLB, review and section images, and
`alice-provenance.json`. The backend regenerates `_tree.json`.

A successful `201` includes `id`, `slug`, `status`, `current_history_id`,
optional `published_history_id`, and `project_url`. Alice persists the receipt,
reads the design back, requests slicing exactly once, then polls the slice GET.
Repeated slice POST resets/requeues the job and is prohibited.

### Current risk envelope and desirable backend hardening

The import endpoint does not honor an idempotency key. A timeout after commit
can create a duplicate if retried. Alice therefore claims one durable sender
before launching the existing import operator; a second worker stops, and any
post-launch uncertainty is terminally ambiguous.

Public publishing is currently **blocked**, not merely degraded. The checked
Factory deployment does not advertise all three public-write capabilities
Alice requires: `packet_hash_bound_publish`, `sku_currency_bound_publish`, and
`rich_page_bound_publish`. The write boundary must atomically compare the
caller's expected history and project plus the complete rich-page precondition,
apply the exact reviewed SKU, price, and USD currency, and return those fields
with the accepted history/project/packet/policy binding. The Vibe adapter fails
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
4. `rich_page_bound_publish`: the same write rejects an incomplete or different
   rich page and echoes the accepted rich-page/history/project precondition.
5. `order_to_print_job`: each paid SKU/order maps to the exact published
   CAD/BOM packet and one idempotent print job.

`alice.factory.FactoryClient` remains the low-level verified draft importer.
Its capability-gated `publish_live` method describes the stronger future API;
the supported board-game draft handoff is the existing `vibe-ideas` operator,
and the public flip remains `alice.vibe_pipeline`.

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
address data remain in Factory. Detailed slicer, machine, lot, cost, failure,
support, and return measurements arrive through the separate outcomes contract
rather than being inferred from shipment success.

Readiness derives `order_to_print_job` only when authenticated, version-matched
diagnostics prove the primitives on both sides: `factory_order` must advertise
`paid_order_readback`; `print_fulfillment` must advertise
`authenticated_manufacturing_readback`,
`idempotent_print_by_operation_key`, `reconcile_print_by_operation_key`, and
`reconcile_qa_ship_by_operation_key`. A self-asserted composite capability is
ignored. Draft and live physical effects separately require CAD
`idempotent_cad_by_operation_key`/`reconcile_cad_by_operation_key` and print
prototype/production idempotency plus reconciliation capabilities. Every first
send and reconciliation payload is bound by `effect_operation_key`,
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
