# Autonomous inventor ecosystem map

> Research snapshot: 2026-08-23. Every code link below is pinned to the commit that was inspected; private-repository links require `autonomous-ai` organization access.

## Outcome

The Workshop is the shared inventor workshop. Each inventor brings its `TASTE.md`—the creative judgment that makes its work recognizable—and its niche knowledge. Workshop supplies **Make**, **Inspect**, **Pack**, and **Send**. A qualified **Door** adapts one external service: `ShopDoor` reaches an optional catalog, while `DeliveryDoor` reaches printing, commerce, or fulfillment.

Here and throughout this audit, **Panda is the legacy codename of the current external catalog/publication backend** represented by the `panda-*` repositories and APIs. It is never a Workshop subsystem. The exact historical names remain in this document because they identify real repositories, files, and contracts.

Workshop should own the parts that must be identical for every inventor: artifact identity and Packing, deterministic Inspection evidence, bounded repair, resumable job state, Stamps, and narrow Doors. It should not absorb the current catalog backend, Factory, Vibe, ecommerce, print-farm, media-provider, or model-provider implementations. Those remain independently deployed systems reached through Doors.

The highest-value donors are:

- [`autonomous-vibe`](https://github.com/autonomous-ai/autonomous-vibe/tree/fcaacde5eb3bd97f01aed4ab7b81a09faa9dc81d) for CAD generation, validation, print preparation, and the legacy Panda client contract.
- [`panda-social-cc-agent`](https://github.com/autonomous-ai/panda-social-cc-agent/tree/70113cd986f1b5f1dfb645673d63169617a4ae2a) for leases, checkpoints, content-addressed workspaces, artifact publication, and human-input pauses.
- [`autonomous-circuit`](https://github.com/autonomous-ai/autonomous-circuit/tree/0edb4544426c3329e492f96546c21cf36ca1cf26) for evidence-based evaluators, bounded repair, golden components, and safety/refusal policy.
- [`autonomous-tv`](https://github.com/autonomous-ai/autonomous-tv/tree/bcdb477aef10d926aaf103bfd1b116b0559a83a1) for provider interfaces, deterministic mocks, content-addressed incremental caches, and cheap preflight before paid work.
- [`autonomous-harness`](https://github.com/autonomous-ai/autonomous-harness/tree/f06febd6ea180eedd4d57507bd801a6833745619) for an agent-engine protocol that does not bind Workshop to one CLI or model vendor.

The current catalog backend sits behind a `ShopDoor`; it is not a code dependency. Factory fulfillment is farther downstream behind a `DeliveryDoor`, and its backend source was not present in the audited organization.

## Scope and method

An authenticated GitHub inventory returned exactly **64 organization-owned repositories: 22 public and 42 private**. The organization metadata reported 42 owned private repositories and 42 total private repositories, so the credentials used for this audit exposed the complete private inventory at the time of the snapshot. One repository, `autonomous-lamp`, was archived. The complete classification is at the end of this document.

For the 15 repositories with a plausible Workshop or integration role, the audit inspected documentation and implementation at a pinned default-branch commit rather than relying on repository descriptions. The decision labels used below are:

- **Vendor/extract**: bring a small, generic contract or implementation into Workshop with provenance and tests; do not copy the enclosing application.
- **Door**: implement a Workshop-owned port over a versioned network or process boundary.
- **Depend**: consume a separately versioned artifact at an explicit pin.
- **Reference**: use the implementation to understand live behavior, but do not couple Workshop to it.
- **Ignore**: do not use it for the inventor Workshop.

## Target boundary

```text
inventors/<name>
    TASTE.md + niche lore + prompts
                  |
                  v
Workshop:      Make
                 |  +-- uses CadDoor ----> cadpy/tools
                 |  `-- uses ModelDoor --> Harness/Grid
                 v
                Inspect
                 |
                 v
                Pack
                 |
                 v
                Sender
                   +-- uses ShopDoor ----> optional catalog -> legacy Panda API
                   `-- uses DeliveryDoor -> Store/Factory
```

Workshop should be usable without live credentials. Deterministic Make collaborators, Inspections, and Door doubles must exercise the complete lifecycle before an inventor is allowed to invoke paid generation, send a design, or request fulfillment. Inventors may make their Inspections stricter, but they must not bypass the common artifact, safety, identity, or Sender contracts.

The Workshop artifact boundary should be a content-addressed Pack containing source, manufacturing outputs, previews, a tree manifest, provenance, and Inspection evidence. Remote identifiers are annotations on that immutable local identity; a mutable slug from the legacy Panda backend, database record, or model-authored success message is not the artifact identity.

## Pinned integration and donor map

| Repository | Inspected commit | Main surface / language | Workshop decision |
|---|---|---|---|
| `autonomous-vibe` | [`fcaacde`](https://github.com/autonomous-ai/autonomous-vibe/tree/fcaacde5eb3bd97f01aed4ab7b81a09faa9dc81d) | CAD packages and desktop integrations; Python, TypeScript/JavaScript, Rust | **Vendor/extract** CAD contracts and canonical skills; **Door** for slicing, printing, and the legacy Panda API |
| `panda-social-backend` | [`8f122be`](https://github.com/autonomous-ai/panda-social-backend/tree/8f122beb489b5bafe14ac7aa60165dadcbb9d125) | Panda API and catalog; Go | **Door** over HTTP/OpenAPI; never share its Mongo models |
| `panda-social-cc-agent` | [`70113cd`](https://github.com/autonomous-ai/panda-social-cc-agent/tree/70113cd986f1b5f1dfb645673d63169617a4ae2a) | Production generation worker; Python | **Vendor/extract** generic job/artifact primitives only |
| `panda-social-pi-agent` | [`e39a96d`](https://github.com/autonomous-ai/panda-social-pi-agent/tree/e39a96d7658902e97cb3ed145993355832c8586c) | Older alternate Pi executor; Python | **Ignore** as a runtime; retain the engine-substitution lesson |
| `panda-ccr` | [`cd408cb`](https://github.com/autonomous-ai/panda-ccr/tree/cd408cb0dc4ba9074b8141889ad001fa31f35242) | Claude Code Router fork; TypeScript | **Ignore**; use the generic model/agent port instead |
| `panda-website` | [`fdb84d0`](https://github.com/autonomous-ai/panda-website/tree/fdb84d0698cb2b1461a74c5ae88155fb36ddd2bf) | Older Panda web client; TypeScript/Next.js | **Reference** viewer ideas only; its publish request is stale |
| `panda-mobile` | [`adc114f`](https://github.com/autonomous-ai/panda-mobile/tree/adc114ffcf9484427322e56f09fe4c12f9bf590f) | Panda and Store clients; TypeScript/Expo | **Reference** current commerce handoff; no code dependency |
| `ecm-website` | [`3c3fd22`](https://github.com/autonomous-ai/ecm-website/tree/3c3fd22a8c1b07cd96c4489cfc9bf6a9ac78d879) | Current Factory/Vibe UI and BFF clients; TypeScript/Next.js | **Reference** live orchestration and publish behavior |
| `media-gen-gateway` | [`a42ee97`](https://github.com/autonomous-ai/media-gen-gateway/tree/a42ee9719bb8c56674830edbcc885f3fa2521917) | Async media gateway; Python/FastAPI | **Door, experimental** after auth and correctness hardening |
| `autonomous-harness` | [`f06febd`](https://github.com/autonomous-ai/autonomous-harness/tree/f06febd6ea180eedd4d57507bd801a6833745619) | Agent protocol and CLI; TypeScript | **Vendor/depend** on schemas and conformance; one `ModelDoor` |
| `autonomous-circuit` | [`0edb454`](https://github.com/autonomous-ai/autonomous-circuit/tree/0edb4544426c3329e492f96546c21cf36ca1cf26) | Autonomous physical-product inventor; Python/TypeScript | **Vendor/extract** generic evaluation and safety patterns |
| `autonomous-tv` | [`bcdb477`](https://github.com/autonomous-ai/autonomous-tv/tree/bcdb477aef10d926aaf103bfd1b116b0559a83a1) | Autonomous media pipeline; Python/TypeScript | **Vendor/extract** generic providers, mocks, caching, and critic separation |
| `autonomous-grid` | [`8964c40`](https://github.com/autonomous-ai/autonomous-grid/tree/8964c404ec336017a5d7becfcb446f42cdde21b5) | OpenAI-compatible local/remote inference; Python | **Door** as an optional model/media service |
| `autonomous-grid-be` | [`77130ef`](https://github.com/autonomous-ai/autonomous-grid-be/tree/77130ef6b3cebf30721803fc96749080db17ef5a) | Grid auth/control plane; Python/FastAPI | **Ignore** in Workshop; deployment concern only |
| `github-templates` | [`fcdcc0b`](https://github.com/autonomous-ai/github-templates/tree/fcdcc0bc2ed39685dbef1b33e23347055326da7f) | Reusable CI workflows; YAML/Docker | **Depend** only at a pin and after secret-handling hardening |

### `autonomous-vibe`: canonical CAD and print donor

The repository already separates the useful capabilities from the human-facing desktop shell:

- [`packages/cadpy/README.md`](https://github.com/autonomous-ai/autonomous-vibe/blob/fcaacde5eb3bd97f01aed4ab7b81a09faa9dc81d/packages/cadpy/README.md) describes the narrow Python surface for geometry generation, topology/validation, hashing, STEP/STL export, and sidecars. This is the best implementation donor for a Workshop `CadDoor`.
- [`packages/cadjs/README.md`](https://github.com/autonomous-ai/autonomous-vibe/blob/fcaacde5eb3bd97f01aed4ab7b81a09faa9dc81d/packages/cadjs/README.md) is UI-agnostic parsing/rendering code. Vendor only if inventors need a shared preview renderer; it should not become a requirement for headless generation.
- [`skills/cadcode/SKILL.md`](https://github.com/autonomous-ai/autonomous-vibe/blob/fcaacde5eb3bd97f01aed4ab7b81a09faa9dc81d/skills/cadcode/SKILL.md) and [`skills/step-parts/SKILL.md`](https://github.com/autonomous-ai/autonomous-vibe/blob/fcaacde5eb3bd97f01aed4ab7b81a09faa9dc81d/skills/step-parts/SKILL.md) encode printability, function, aesthetics, and the `step.parts` workflow. They belong in Make and Inspect: Workshop should own one versioned canonical copy and distribute it to inventors, because copied skill trees in workers will otherwise drift.
- [`docs/panda-interfaces.md`](https://github.com/autonomous-ai/autonomous-vibe/blob/fcaacde5eb3bd97f01aed4ab7b81a09faa9dc81d/docs/panda-interfaces.md) is a useful frozen integration contract, while [`social.rs`](https://github.com/autonomous-ai/autonomous-vibe/blob/fcaacde5eb3bd97f01aed4ab7b81a09faa9dc81d/desktop/src-tauri/src/commands/social.rs) shows the deployed import, refresh, exchange, profile, and design calls. These are evidence for a Door, not code to embed in Workshop.
- [`slicer.rs`](https://github.com/autonomous-ai/autonomous-vibe/blob/fcaacde5eb3bd97f01aed4ab7b81a09faa9dc81d/desktop/src-tauri/src/commands/slicer.rs) implements OrcaSlicer invocation and deterministic pre-screening. [`printer.rs`](https://github.com/autonomous-ai/autonomous-vibe/blob/fcaacde5eb3bd97f01aed4ab7b81a09faa9dc81d/desktop/src-tauri/src/commands/printer.rs) spans Bambu discovery, FTPS, MQTT, cloud, and Studio integration. Preserve both behind optional slicer/printer Doors; most autonomous inventors should create a manufacturable Pack without requiring a local printer.

Do not depend on the whole Tauri desktop application. It couples reusable CAD logic to browser login, local OS state, printers, and a human workflow.

### Current catalog Door (legacy codename: Panda)

[`panda-social-backend/docs/swagger.yaml`](https://github.com/autonomous-ai/panda-social-backend/blob/8f122beb489b5bafe14ac7aa60165dadcbb9d125/docs/swagger.yaml) is the broad current API inventory. Relevant surfaces under `/api/v1` are:

- identity: `/auth/oauth/{provider}`, `/auth/device/login`, `/auth/exchange`, and `/auth/refresh`;
- generation: `/generate`, `/designs/{slug}/remix`, `/jobs/{id}`, plus job events/messages/retry/stop;
- artifacts and publication: `POST /designs/import`, `/uploads`, `POST /designs/{slug}/slice`, `POST /designs/{slug}/publish`, and listing/product reads;
- catalog: `/listing`, `/products`, and `/products/{sku}`.

[`docs/worker-contract.md`](https://github.com/autonomous-ai/panda-social-backend/blob/8f122beb489b5bafe14ac7aa60165dadcbb9d125/docs/worker-contract.md) defines the important storage contract: a content-addressed, immutable `project_url` tree, complete source in object/CDN storage, `_tree.json`, and explicit API-versus-worker field ownership. Make should generate the same sort of immutable local bundle, and Sender should retain authenticated readback as a Stamp.

The current import implementation in [`services/import.go`](https://github.com/autonomous-ai/panda-social-backend/blob/8f122beb489b5bafe14ac7aa60165dadcbb9d125/services/import.go) is synchronous, non-idempotent, and defaults to public unless the client requests `status=draft`. It de-gits the upload and writes an immutable CDN snapshot. At this pin its relevant limits are 100 MiB uploaded, 512 MiB expanded, 4,096 entries, 256 MiB per expanded archive entry, and 95 MiB per published file. Every Sender must therefore import as a draft, fence retries locally by artifact hash, and reconcile an ambiguous response instead of blindly retrying.

Publishing is a JSON request whose media/attachments must already be hosted URLs; the current limit is 12 attachments. [`apis/handlers_listing.go`](https://github.com/autonomous-ai/panda-social-backend/blob/8f122beb489b5bafe14ac7aa60165dadcbb9d125/apis/handlers_listing.go) mints an immutable SKU and computes the current price floor from sliced weight, 30% waste, material cost, and shipping. Sender should use `ShopDoor` and retain its Stamp, not reproduce the backend's pricing logic.

The recommended autonomous sequence is:

1. Read the inventor's Taste, then let its Make create with the canonical CAD skill and domain knowledge.
2. Inspect deterministic geometry, artifact, safety, and printability evidence; optionally slice or test-print locally.
3. Pack the accepted artifact and its Inspection evidence.
4. Let the Sender call `POST /designs/import` with `status=draft`; persist the returned owner, slug, history IDs, status, and `project_url` against the exact bundle hash.
5. `POST /designs/{slug}/slice` and poll the design/job read until the slice is terminal.
6. Upload showcase media through `/uploads`.
7. `POST /designs/{slug}/publish` with JSON listing data, hosted media/attachment URLs, and any assembly colors; read the design back and prove the published history equals the accepted history.
8. Let the catalog backend mint the SKU through its Door; send commerce and fulfillment through `DeliveryDoor` to the external Store/Factory boundary.

The catalog Door must not import Panda's Go models or access its Mongo collections. API and worker field ownership are deliberate, and direct database sharing would make every inventor sensitive to backend migrations.

### `panda-social-cc-agent`: job and artifact primitive donor

The production code is more useful than the older narrative documentation. [`app/worker.py`](https://github.com/autonomous-ai/panda-social-cc-agent/blob/70113cd986f1b5f1dfb645673d63169617a4ae2a/app/worker.py) and the job modules—[`schemas.py`](https://github.com/autonomous-ai/panda-social-cc-agent/blob/70113cd986f1b5f1dfb645673d63169617a4ae2a/app/utils/jobs/schemas.py), [`store.py`](https://github.com/autonomous-ai/panda-social-cc-agent/blob/70113cd986f1b5f1dfb645673d63169617a4ae2a/app/utils/jobs/store.py), [`worker_runtime.py`](https://github.com/autonomous-ai/panda-social-cc-agent/blob/70113cd986f1b5f1dfb645673d63169617a4ae2a/app/utils/jobs/worker_runtime.py), [`job_runner.py`](https://github.com/autonomous-ai/panda-social-cc-agent/blob/70113cd986f1b5f1dfb645673d63169617a4ae2a/app/utils/jobs/job_runner.py), [`phase_runner.py`](https://github.com/autonomous-ai/panda-social-cc-agent/blob/70113cd986f1b5f1dfb645673d63169617a4ae2a/app/utils/jobs/phase_runner.py), and [`checkpoint.py`](https://github.com/autonomous-ai/panda-social-cc-agent/blob/70113cd986f1b5f1dfb645673d63169617a4ae2a/app/utils/jobs/checkpoint.py)—demonstrate leases, compare-and-set ownership, heartbeats, cooperative stop, resumable phases, and parked input/review states.

[`artifact_identity.py`](https://github.com/autonomous-ai/panda-social-cc-agent/blob/70113cd986f1b5f1dfb645673d63169617a4ae2a/app/utils/jobs/artifact_identity.py), [`artifact_publisher.py`](https://github.com/autonomous-ai/panda-social-cc-agent/blob/70113cd986f1b5f1dfb645673d63169617a4ae2a/app/utils/jobs/artifact_publisher.py), and [`workspace_manager.py`](https://github.com/autonomous-ai/panda-social-cc-agent/blob/70113cd986f1b5f1dfb645673d63169617a4ae2a/app/utils/cc/workspace_manager.py) implement the strongest reusable ideas: byte-bound artifact identity, a content-addressed source tree, files published before `_tree.json`, accepted-artifact salvage, and durable event history.

Extract these as pure state machines and storage interfaces. Do not vendor the worker wholesale: it is coupled to Panda billing, Mongo/Go-owned fields, Cloud Run, Claude credentials, thumbnails, and deployment policy. The generic Workshop vocabulary should be small—`queued`, `running`, `awaiting_input`, `reviewing`, `succeeded`, `failed`, `canceled` plus a reason—while backend-specific statuses stay inside its Door.

### Cross-domain autonomous-inventor donors

`autonomous-circuit` is the clearest precedent for a physical-product inventor. Its [`README.md`](https://github.com/autonomous-ai/autonomous-circuit/blob/0edb4544426c3329e492f96546c21cf36ca1cf26/README.md), [`docs/circuit-interfaces.md`](https://github.com/autonomous-ai/autonomous-circuit/blob/0edb4544426c3329e492f96546c21cf36ca1cf26/docs/circuit-interfaces.md), and [`AGENTS.md`](https://github.com/autonomous-ai/autonomous-circuit/blob/0edb4544426c3329e492f96546c21cf36ca1cf26/AGENTS.md) require parsed-artifact gates rather than trusting process exit codes, two independent verification substrates, bounded repair/review, known-good components, failure-corpus regression, and explicit safety/refusal. Workshop should generalize these into Inspection results bound to the exact artifact hash. A model's statement that a product is safe or printable is never sufficient evidence.

`autonomous-tv` demonstrates how to make an expensive creative pipeline testable. [`docs/video-interfaces.md`](https://github.com/autonomous-ai/autonomous-tv/blob/bcdb477aef10d926aaf103bfd1b116b0559a83a1/docs/video-interfaces.md), [`providers/base.py`](https://github.com/autonomous-ai/autonomous-tv/blob/bcdb477aef10d926aaf103bfd1b116b0559a83a1/packages/dramapy/src/dramapy/providers/base.py), [`providers/mock.py`](https://github.com/autonomous-ai/autonomous-tv/blob/bcdb477aef10d926aaf103bfd1b116b0559a83a1/packages/dramapy/src/dramapy/providers/mock.py), and [`render_cache.py`](https://github.com/autonomous-ai/autonomous-tv/blob/bcdb477aef10d926aaf103bfd1b116b0559a83a1/packages/dramapy/src/dramapy/render_cache.py) separate provider contracts from implementations, supply deterministic mocks, hash inputs for incremental reruns, and run preflight before paid rendering. Carry those patterns into the Make and its Doors, not the video domain model. For inventors, unchanged CAD/manufacturing stages should not be regenerated merely because copy or preview media changed.

### Agent and media Doors

[`autonomous-harness/provider/spec/README.md`](https://github.com/autonomous-ai/autonomous-harness/blob/f06febd6ea180eedd4d57507bd801a6833745619/provider/spec/README.md) specifies JSON-RPC 2.0 plus server-sent events for `agent.list`, `agent.send`, `agent.history`, `turn.cancel`, `agent.create`, `agent.rename`, `agent.delete`, and `agent.recap`. Its contract includes provider-owned history, client-generated turn IDs, one terminal event, cancellation, and resumable input-required turns; [`event.json`](https://github.com/autonomous-ai/autonomous-harness/blob/f06febd6ea180eedd4d57507bd801a6833745619/provider/spec/schema/event.json) is the machine-readable event schema. Workshop should vendor or pin the schema and conformance fixtures and provide one `ModelDoor`. [`cli/src/engines/types.ts`](https://github.com/autonomous-ai/autonomous-harness/blob/f06febd6ea180eedd4d57507bd801a6833745619/cli/src/engines/types.ts) is useful evidence for normalizing engine-specific events.

[`autonomous-grid/README.md`](https://github.com/autonomous-ai/autonomous-grid/blob/8964c404ec336017a5d7becfcb446f42cdde21b5/README.md) and [`local/server.py`](https://github.com/autonomous-ai/autonomous-grid/blob/8964c404ec336017a5d7becfcb446f42cdde21b5/local/server.py) expose OpenAI-compatible `/v1/chat/completions` and `/v1/responses` plus image/video generation. Treat Grid as one optional HTTP Door; do not make its private control plane a Workshop dependency.

[`media-gen-gateway/app/apis/media.py`](https://github.com/autonomous-ai/media-gen-gateway/blob/a42ee9719bb8c56674830edbcc885f3fa2521917/app/apis/media.py) provides `POST /media/generations` and `GET /media/generations/{id}` with the shapes in [`app/schemas.py`](https://github.com/autonomous-ai/media-gen-gateway/blob/a42ee9719bb8c56674830edbcc885f3fa2521917/app/schemas.py). It is not ready to be a trusted default: [`app/apis/hooks.py`](https://github.com/autonomous-ai/media-gen-gateway/blob/a42ee9719bb8c56674830edbcc885f3fa2521917/app/apis/hooks.py) has no visible webhook authentication/signature check at this pin, request-ID disagreement is handled with an assertion, and inline result data is not consistently copied into the persisted response path. Keep any Door experimental until signature verification, explicit conflict handling, result persistence, idempotency, and contract tests exist.

### Consumer references and delivery boundary

The current web client is useful for identifying deployed behavior. [`ecm-website/src/services/apiv3/vibeSession.ts`](https://github.com/autonomous-ai/ecm-website/blob/3c3fd22a8c1b07cd96c4489cfc9bf6a9ac78d879/src/services/apiv3/vibeSession.ts) proxies a site JWT to Panda; [`remix/api.ts`](https://github.com/autonomous-ai/ecm-website/blob/3c3fd22a8c1b07cd96c4489cfc9bf6a9ac78d879/src/views/Vibe2Page/remix/api.ts) and [`remix/service.ts`](https://github.com/autonomous-ai/ecm-website/blob/3c3fd22a8c1b07cd96c4489cfc9bf6a9ac78d879/src/views/Vibe2Page/remix/service.ts) cover create/remix/edit, SSE, pause, retry, and stop; [`social/api.ts`](https://github.com/autonomous-ai/ecm-website/blob/3c3fd22a8c1b07cd96c4489cfc9bf6a9ac78d879/src/views/Vibe2Page/social/api.ts) shows the current upload/slice/publish JSON flow. These calls are evidence for the catalog Door.

Commerce is a separate service boundary. [`panda-mobile/src/services/commerce-service.ts`](https://github.com/autonomous-ai/panda-mobile/blob/adc114ffcf9484427322e56f09fe4c12f9bf590f/src/services/commerce-service.ts), [`autonomous-store-client.ts`](https://github.com/autonomous-ai/panda-mobile/blob/adc114ffcf9484427322e56f09fe4c12f9bf590f/src/services/autonomous-store-client.ts), and [`constants/config.ts`](https://github.com/autonomous-ai/panda-mobile/blob/adc114ffcf9484427322e56f09fe4c12f9bf590f/src/constants/config.ts) call the external `https://apiv2.autonomous.ai/api/v1` Store service for cart, summary, address verification, order lookup, and hosted secure checkout. The direct mobile checkout function is a stub. No repository among the 64 contains the corresponding Store/print-farm/order/shipment backend, so Workshop can define `DeliveryDoor` but cannot safely vendor fulfillment logic from this organization snapshot.

## Current contract drift

When sources disagree, use current backend implementation plus authenticated readback as truth, then current Swagger, then the active `ecm-website` client. Treat older clients and prose as historical evidence.

| Area | Drift found | Required response |
|---|---|---|
| Design import/storage | [`docs/design-import-api.md`](https://github.com/autonomous-ai/panda-social-backend/blob/8f122beb489b5bafe14ac7aa60165dadcbb9d125/docs/design-import-api.md) still describes creating a Gitea repository and carries old size guidance; [`services/import.go`](https://github.com/autonomous-ai/panda-social-backend/blob/8f122beb489b5bafe14ac7aa60165dadcbb9d125/services/import.go) de-gits uploads into an immutable CDN tree with different limits. | Generate a pinned Panda contract fixture from implementation/OpenAPI and test it against staging; do not implement Gitea behavior. |
| Publish request | [`panda-website/src/services/api/designs.ts`](https://github.com/autonomous-ai/panda-website/blob/fdb84d0698cb2b1461a74c5ae88155fb36ddd2bf/src/services/api/designs.ts) sends multipart publish media; current backend Swagger and [`ecm-website/social/api.ts`](https://github.com/autonomous-ai/ecm-website/blob/3c3fd22a8c1b07cd96c4489cfc9bf6a9ac78d879/src/views/Vibe2Page/social/api.ts) use JSON with previously uploaded URLs. | `ShopDoor` uses JSON URLs and cross-repo contract tests. |
| Worker documentation | [`panda-social-cc-agent/docs/generation-worker.md`](https://github.com/autonomous-ai/panda-social-cc-agent/blob/70113cd986f1b5f1dfb645673d63169617a4ae2a/docs/generation-worker.md) contains an obsolete banner, while the worker/job/artifact modules are active production code. | Extract behavior from code/tests and write new Workshop-native state-machine documentation. |
| Hosted authentication | [`autonomous-vibe/social.rs`](https://github.com/autonomous-ai/autonomous-vibe/blob/fcaacde5eb3bd97f01aed4ab7b81a09faa9dc81d/desktop/src-tauri/src/commands/social.rs) contains a hosted login URL that no longer matches the current backend identity surface. | Keep login outside Workshop; require an injected credential source and test token refresh/exchange against a versioned environment. |
| Agent gateway | [`panda-social-backend/docs/agent-gateway.md`](https://github.com/autonomous-ai/panda-social-backend/blob/8f122beb489b5bafe14ac7aa60165dadcbb9d125/docs/agent-gateway.md) describes a dormant, not-deployed gateway, and `/agent-creator` represents one server-configured identity rather than many inventor principals. | Use a Harness `ModelDoor` for execution and design explicit service identity before unattended sending. |
| CI secret transport | [`github-templates/.github/workflows/docker-build-and-push.yaml`](https://github.com/autonomous-ai/github-templates/blob/fcdcc0bc2ed39685dbef1b33e23347055326da7f/.github/workflows/docker-build-and-push.yaml) passes repository credentials as Docker build arguments. | Do not copy as-is; switch to short-lived credentials and BuildKit secret mounts, and pin reusable workflow refs. |

## Gaps to close before ten inventors

These are platform gaps or Workshop obligations, not reasons to couple the inventor implementation to an application repository.

1. **Per-inventor service identity.** The inspected legacy Panda flows are human OAuth/PKCE/refresh, import ownership comes from the bearer token, and the dormant agent route maps to one configured account. Define a distinct principal for every inventor, scoped credentials, revocation/rotation, and explicit creator attribution. A human token shared by ten unattended agents is not an acceptable boundary.
2. **End-to-end idempotency.** The catalog backend's import is non-idempotent. The Sender must use artifact-tree hash plus a durable local outbox/intent, never blind-retry an unknown response, and add platform support for `Idempotency-Key` or artifact-hash lookup. Publishing and media upload need the same treatment.
3. **Versioned contracts and drift tests.** Pin OpenAPI/schema fixtures, add consumer-driven tests for import/upload/slice/publish/readback, and expose a capability/version endpoint. A passing unit test against a hand-written mock cannot detect the Gitea, multipart, or login drift recorded above.
4. **Verified Inspections.** Every Inspection result must name the evaluator, record evidence, and bind to the exact artifact bytes. Sender may send only the accepted history and must retain authenticated readback as a Stamp; never trust an HTTP success alone or an LLM's self-evaluation.
5. **One canonical skill distribution path.** CAD skills were copied across Vibe and worker repositories. Workshop now installs and fingerprints one canonical skill tree; the Make and Inspect still need compatibility metadata, fixtures, and a release/update policy so ten inventors do not fork printability rules.
6. **Isolation and secret hygiene.** Give each run an isolated workspace and each inventor least-privilege secrets. Fail packaging when it encounters environment files, tokens, private keys, VCS internals, unsafe links, traversal, or disallowed binaries; do not rely solely on the catalog backend's server-side stripping.
7. **Normalized lifecycle and recovery.** Workshop needs leases, heartbeats, compare-and-set transitions, cancellation, checkpoints, input/review pauses, bounded repair budgets, and crash recovery. Map provider-specific status explosions into a small common lifecycle with a structured reason.
8. **`DeliveryDoor` contract.** The Store/Factory backend was unavailable in the 64-repository inventory. Before inventors can autonomously sell physical goods, document quote, material/profile, manufacturability, order, refund, shipment, webhook-authentication, and sandbox contracts with the owning team. Until then, stop Sender at a verified catalog listing/SKU.
9. **Door cost and determinism controls.** Supply deterministic model/media/CAD doubles, cache Make stages by complete input hashes, run Inspect preflight before paid calls, record cost/latency/provenance, and cap repair attempts. A retry must resume the failed stage rather than regenerate an entire product.
10. **Operational policy.** Define per-inventor quotas, concurrency, audit logs, kill switches, rollout/canary behavior, failure-corpus regression, and category-specific refusal rules before multiplying agents.

## Complete 64-repository classification

The following groups are mutually exclusive and exhaustive for the authenticated organization inventory on 2026-08-23.

### Deep-inspected donors and integrations — 15

[`autonomous-vibe`](https://github.com/autonomous-ai/autonomous-vibe), [`panda-social-backend`](https://github.com/autonomous-ai/panda-social-backend), [`panda-social-cc-agent`](https://github.com/autonomous-ai/panda-social-cc-agent), [`panda-social-pi-agent`](https://github.com/autonomous-ai/panda-social-pi-agent), [`panda-ccr`](https://github.com/autonomous-ai/panda-ccr), [`panda-website`](https://github.com/autonomous-ai/panda-website), [`panda-mobile`](https://github.com/autonomous-ai/panda-mobile), [`ecm-website`](https://github.com/autonomous-ai/ecm-website), [`media-gen-gateway`](https://github.com/autonomous-ai/media-gen-gateway), [`autonomous-harness`](https://github.com/autonomous-ai/autonomous-harness), [`autonomous-circuit`](https://github.com/autonomous-ai/autonomous-circuit), [`autonomous-tv`](https://github.com/autonomous-ai/autonomous-tv), [`autonomous-grid`](https://github.com/autonomous-ai/autonomous-grid), [`autonomous-grid-be`](https://github.com/autonomous-ai/autonomous-grid-be), [`github-templates`](https://github.com/autonomous-ai/github-templates).

These are the only organization repositories for which the audit found a plausible reusable Workshop primitive or a direct integration boundary. The detailed decision for each is above.

### Current consolidation target — 1

[`autonomous-workshop`](https://github.com/autonomous-ai/autonomous-workshop).

This repository is the destination for shared Workshop plus one `inventors/<id>/`
folder per autonomous inventor; it is not an external donor.

### Physical-product artifact references, not reusable runtime infrastructure — 8

[`autonomous-computer`](https://github.com/autonomous-ai/autonomous-computer), [`private-autonomous-2x5090`](https://github.com/autonomous-ai/private-autonomous-2x5090), [`private-4xRTX-PRO-6000`](https://github.com/autonomous-ai/private-4xRTX-PRO-6000), [`autonomous-desk`](https://github.com/autonomous-ai/autonomous-desk), [`autonomous-chair`](https://github.com/autonomous-ai/autonomous-chair), [`autonomous-pod`](https://github.com/autonomous-ai/autonomous-pod), [`autonomous-robot`](https://github.com/autonomous-ai/autonomous-robot), [`autonomous-dc`](https://github.com/autonomous-ai/autonomous-dc).

These may supply product examples, BOM/CAD conventions, or category failure cases later, but the audit found no common inventor runtime to depend on. Treat them as corpus inputs only after licensing, provenance, and format review.

### Adjacent agent/product platforms, not required by inventor Workshop — 22

[`autonomous-code-website`](https://github.com/autonomous-ai/autonomous-code-website), [`autonomous-code-be`](https://github.com/autonomous-ai/autonomous-code-be), [`autonomous-code-ccr`](https://github.com/autonomous-ai/autonomous-code-ccr), [`autonomous-code`](https://github.com/autonomous-ai/autonomous-code), [`autonomous-intern`](https://github.com/autonomous-ai/autonomous-intern), [`intern-mcp-server`](https://github.com/autonomous-ai/intern-mcp-server), [`intern-chat`](https://github.com/autonomous-ai/intern-chat), [`private-intern-skills`](https://github.com/autonomous-ai/private-intern-skills), [`private-intern-developer-sdk`](https://github.com/autonomous-ai/private-intern-developer-sdk), [`intern-use-case`](https://github.com/autonomous-ai/intern-use-case), [`autonomous-os`](https://github.com/autonomous-ai/autonomous-os), [`autonomous-terminal`](https://github.com/autonomous-ai/autonomous-terminal), [`agent-status`](https://github.com/autonomous-ai/agent-status), [`harness-terminal`](https://github.com/autonomous-ai/harness-terminal), [`deepseek-harness-cli`](https://github.com/autonomous-ai/deepseek-harness-cli/tree/1927776a56d094cdcc84024030057ccbee9bf319), [`autonomous-grid-cli`](https://github.com/autonomous-ai/autonomous-grid-cli), [`autonomous-grid-app`](https://github.com/autonomous-ai/autonomous-grid-app), [`autonomous-grid-app-downloads`](https://github.com/autonomous-ai/autonomous-grid-app-downloads), [`autonomous-presentation`](https://github.com/autonomous-ai/autonomous-presentation), [`autonomous-spreadsheets`](https://github.com/autonomous-ai/autonomous-spreadsheets), [`picoclaw`](https://github.com/autonomous-ai/picoclaw), [`openclaw-lobster`](https://github.com/autonomous-ai/openclaw-lobster).

These overlap with coding agents, shells, model routing, office creation, or agent UI. Workshop should reach such systems only through qualified Doors such as `ModelDoor`; importing their application frameworks would widen the dependency surface without improving the physical-product lifecycle.

### Unrelated smart-device or general application infrastructure — 18

[`ecm-sds`](https://github.com/autonomous-ai/ecm-sds), [`ecm-sds-admin`](https://github.com/autonomous-ai/ecm-sds-admin), [`ecm-sds-mobile`](https://github.com/autonomous-ai/ecm-sds-mobile), [`go2_middle_layer`](https://github.com/autonomous-ai/go2_middle_layer), [`autonomous-lamp`](https://github.com/autonomous-ai/autonomous-lamp) (archived; moved to Autonomous OS), [`sphere`](https://github.com/autonomous-ai/sphere), [`autonomous-key`](https://github.com/autonomous-ai/autonomous-key), [`lumi-metrics-worker`](https://github.com/autonomous-ai/lumi-metrics-worker), [`private-autonomous-desk-display`](https://github.com/autonomous-ai/private-autonomous-desk-display), [`origami-apps`](https://github.com/autonomous-ai/origami-apps), [`origami-be`](https://github.com/autonomous-ai/origami-be), [`commander-backend`](https://github.com/autonomous-ai/commander-backend), [`commander-website`](https://github.com/autonomous-ai/commander-website), [`commander-firmware`](https://github.com/autonomous-ai/commander-firmware), [`sds-firmware-desk-ai`](https://github.com/autonomous-ai/sds-firmware-desk-ai), [`autonomous-macroz`](https://github.com/autonomous-ai/autonomous-macroz), [`.github`](https://github.com/autonomous-ai/.github), [`autonomous-docs`](https://github.com/autonomous-ai/autonomous-docs).

These are device backends, firmware, dashboards, apps, metrics, or organization administration. Ignore them for the inventor Workshop. Revisit a specific repository only when an inventor gains a direct device-control requirement.

## Not verified

- The proprietary Store/Factory backend behind `apiv2.autonomous.ai`, print-farm scheduling, payment, order, and shipment services was not in the 64-repository organization inventory and therefore was not inspected.
- Live staging calls were not made; endpoint behavior is inferred from pinned backend code, Swagger, and current clients. Contract tests against a non-production environment remain required.
- Private links are exact but will return not-found to readers without organization access.
- Repository state can move after this snapshot. Update pins and rerun drift checks before adopting donor code or changing a production Door.
