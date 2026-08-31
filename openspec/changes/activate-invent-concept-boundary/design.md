## Context

See `proposal.md` for motivation. This change builds on the completed but not yet archived `restore-dormant-concept-contracts` change. That prerequisite provides route-aware schema-v2 `PreRenderConcept` and `SealedConcept` values, exact provenance and round checks, five canonical source documents under `artifacts/concept/rNNNN/concept/`, pure structural evaluation, and check-only sealing over already-present image bytes. It intentionally has no packet, finalizer, effect, checkpoint, or Make wiring.

Current Forge and Quest Invent packets bind the routed Wish, complete roster, universal blueprint, output paths, and revision inputs. One `invent` finalizer derives assignment and `NativeInvented` from a four-field creative source, preserves `source.json`, and proposes exactly those three artifacts. The host independently validates them and transitions to Make. Spark performs equivalent selection and compact invention inside Make. Current `NativeMade` schema v1 binds assignment and Invented but has no Concept identity.

Concept activation crosses native authorship, trusted host validation, credential-bearing effects, durable waits, checkpoint compatibility, Make contracts, and acceptance traces. The following architecture constraints remain load-bearing:

- one Wish-wide native session and one Goal per active stage;
- no Python research, prompt chain, candidate fan-out, semantic judge, or repair loop;
- no standalone Concept stage or native turn;
- exact immutable run capabilities choose behavior on resume;
- credentials and provider-private state never enter the native process or public artifacts;
- only host-rehashed exact bytes, durable receipts, and deterministic gates advance the run;
- ambiguous effects reconcile before retry; and
- Spark's frozen fast path is not expanded by an Invent-only change.

## Goals / Non-Goals

**Goals:**

- Make Concept mandatory and observable inside newly marked Forge/Quest Invent attempts.
- Preserve a strict before/effect/after boundary: native pre-render source, host image effect, host-sealed exact Concept.
- Make the accepted sealed Concept a load-bearing input to Forge/Quest Make and its exact Made identity.
- Reuse the existing Invent checkpoint, Goal, rejection budget, wait semantics, Make-to-Invent edge, and shared revision budget.
- Make normal configured rendering complete automatically while making missing configuration, outages, and ambiguous transmission truthful and resumable.
- Prove route, compatibility, privacy, tamper, effect, and downstream fidelity through deterministic and real-session acceptance.

**Non-Goals:**

- Activate Concept for Spark or add an Invent turn to Spark.
- Add a `concept` stage, Goal, transition, checkpoint, status value, or CLI subcommand.
- Let the host generate research, prompts, physical facts, component plans, or quality judgments.
- Treat Concept art as product, Playtest, physical, manufacture, publication, or delivery evidence.
- Restore the historical vision inspector or let a provider's semantic score gate the run.
- Migrate or reinterpret an existing private run in place.
- Guarantee automatic recovery from a provider that cannot prove the outcome of an already transmitted request.

## Decisions

### 1. Freeze activation with an Invent Concept capability marker

Add immutable `references/invent-concept-v1.md` to newly materialized projects and its exact hash to checkpoint inputs. The host enables it only for new Forge and Quest checkpoints whose materialized finalizer advertises the matching compound protocol. The marker is included in the Invent and Make stage subjects. Spark ignores it and retains its current compound Make contract; unmarked runs retain their older exact packets and gates.

Capability detection follows the existing materialized-protocol pattern used for effort routes, direct Release, Make-to-Invent revision, and Spark economics. It does not infer activation from the presence of installed Concept code or schemas.

**Alternative considered:** activate every Forge/Quest run whenever the installed host can import `workshop.concept`. Rejected because resume would reinterpret frozen checkpoints and could request artifacts their run-local finalizer cannot create.

### 2. Extend the existing Invent packet and finalizer instead of creating a Concept packet

For a marked Forge/Quest attempt, `STAGE.json.inputs` adds:

- the marker binding;
- canonical pre-render root `artifacts/concept/rNNNN/concept`;
- canonical pre-render contract path `artifacts/concept/rNNNN/pre-render.json`;
- canonical sealed contract path `artifacts/concept/rNNNN/sealed.json`;
- a sanitized effect-evidence path `artifacts/concept/rNNNN/effect.json`; and
- for revisions, exact prior sealed Concept, effect-evidence, and revision-input bindings.

The Manager still writes the four-field Invent creative source and additionally writes `brief.json`, `research.json`, `prompts.json`, `descriptor.json`, and `derived_wish.json` at the packet-named root. The materialized `invent` command gains a packet-gated `--concept-root` input. It derives assignment and `NativeInvented`, preserves the creative source, constructs the v2 `invent` provenance from those exact bytes, loads and structurally evaluates the pre-render tree, writes `pre-render.json`, and writes one `agent-outcome.json` listing assignment, Invented, creative source, pre-render contract, and its exact five-file source manifest.

The finalizer performs no provider call and writes neither image bytes nor the sealed contract. Its output remains an authored proposal, not a passed gate.

**Alternative considered:** add a second finalizer invocation after host rendering. Rejected because the native turn has already returned, image bytes are host-owned, and asking Codex to finalize them would blur effect authority and add an unnecessary continuation.

### 2a. Publish the complete authored Concept input shape with the frozen capability

The immutable `invent-concept-v1.md` reference is the agent-facing contract,
not merely a workflow overview. It MUST enumerate a canonical skeleton for
each of `brief.json`, `research.json`, `prompts.json`, `descriptor.json`, and
`derived_wish.json`, including every nested required field, value constraint,
cross-file key relationship, role-reference order, pre-render versus sealed
descriptor distinction, and the two canonical SHA-256 derivations. The
skeletons guide authored source only; they do not expose host-private effect
state, provider metadata, or a host-side design judgment.

This keeps structural ownership where it belongs: the deterministic finalizer
still rejects malformed bytes, while the native Manager receives enough exact
contract information to author a conforming first proposal without inspecting
implementation code or discovering fields through rejection cycles.

**Alternative considered:** link the agent to Python validators or schema
implementation. Rejected because implementation is not the product-run
interface and does not provide a stable, compact, complete authoring contract.

### 3. Split the Invent host gate into pre-effect and post-effect phases under one checkpoint

The host handles a ready marked Invent proposal in this order:

1. reopen and validate the checkpoint/subject binding and exact proposal artifact set;
2. reconstruct assignment, Invented, preserved creative source, and pre-render Concept from disk;
3. re-run assignment/invention consistency, provenance, round/revision freshness, exact source manifests, derived-Wish preservation, and structural evaluation;
4. persist the validated pending proposal in private host state;
5. prepare or reconcile the image-effect operations;
6. after every role has a successful receipt and atomically installed image, call the existing pure `seal_pre_render_concept` boundary;
7. write canonical `sealed.json` and a bounded sanitized aggregate `effect.json` that binds role, intent hash, provider-profile hash, and returned-byte hash but omits credentials, provider operation ids, raw responses, and private error text;
8. independently reopen the sealed tree and effect state; then emit one passed Invent gate and atomically apply the Invent-to-Make transition with all accepted artifacts.

The private pending record is checkpoint-, subject-, proposal-, and pre-render-hash bound. If the command exits during effect handling, the checkpoint remains `invent`; resume processes this record before launching another Codex turn. Successful effects therefore do not repeat Invent cognition.

Authored source failures before step 4 enter a new bounded Invent proposal-rejection record modeled on current Make/Playtest rejection handling. Effect waits after step 4 retain the exact pending proposal and do not count as agent rejection or lifecycle revision.

**Alternative considered:** apply the Invent gate before rendering and treat image sealing as preparation for Make. Rejected because a checkpoint would claim Invent passed without the mandatory Concept bytes and later effect failure would strand state between accepted stages.

### 4. Use a Concept-specific durable effect ledger beside the existing Factory ledger

Add a narrow runtime effect store for Concept roles rather than widening the Factory-oriented `EffectStore` schema, whose identities assume Release, pack, handoff, product, and Playtest bindings. The new host-private SQLite tables record one aggregate Concept effect plus one operation per role. Each operation identity hashes:

- product id, stage checkpoint and subject;
- pre-render Concept and source-manifest identities;
- role and canonical output path;
- exact instruction hash;
- ordered reference roles and byte hashes;
- provider-profile id and hash, pinned origin, model, and request-schema version.

States are `planned`, `sending`, `succeeded`, `rejected`, and `unknown`, with transition tokens preventing stale completions. An aggregate becomes succeeded only when the exact required role set has succeeded and the bytes rehash. New source produces new operation identities; superseded rows remain immutable audit history.

The ledger API remains deterministic substrate. It does not order roles creatively, compose prompts, inspect images semantically, or decide whether the design is good.

**Alternative considered:** encode all image roles as one generic Factory effect. Rejected because one partial multi-request response would hide which transmission became ambiguous and would couple Concept safety to unrelated Release fields.

### 5. Record disclosed prospective rendering authority at marked run creation

The run authorization record advances to a compatible new schema that preserves Factory and Git publication fields and adds a Concept-render authority block for marked Forge/Quest runs. The block names the stable provider profile, its non-secret profile hash, and the allowed transmitted data classes: drawing instruction text and exact prior-role images. CLI help, run creation output, and documentation state that selecting a newly marked Forge/Quest route grants this host-side image-generation authority. Spark records no such authority.

Provider credentials live only in a private Workshop credentials file and are loaded after Codex exits. Missing profile configuration or credentials creates a typed Invent wait before transmission. Authorization does not imply success and cannot bypass the effect ledger.

**Alternative considered:** treat credential presence as consent. Rejected because secrets are capability, not authorization, and may predate the Wish.

### 6. Implement one narrow production adapter profile with conservative ambiguity handling

The integration boundary exposes one host-only image client protocol and one configured production profile adapted from the prior OpenRouter image work. The profile pins the HTTPS origin, explicit model and request schema, prohibits cross-origin redirects, bounds references/request/response/time, sends one image request per role, sniffs returned media, and returns exact bytes plus bounded provider metadata. The stable effect idempotency key is sent only where the provider contract accepts it.

Immediate authenticated HTTPS success can produce a receipt bound to exact returned bytes. If a provider supplies a durable operation id and authenticated status endpoint, the adapter uses them for reconciliation. If it does not, a post-transmission timeout or disconnect becomes `unknown`; Workshop does not pretend that repeating an image purchase is safe. A pre-transmission failure or authenticated absence may retry under the same intent within a small host-owned transport bound.

The adapter never constructs prompts, selects reference order, writes files, updates checkpoints, or evaluates visual meaning. Deterministic tests inject a transport double at this outbound boundary.

**Alternative considered:** restore the historical inline provider retries. Rejected because retrying after an uncertain paid transmission can duplicate cost and return different pixels under one supposed identity.

### 7. Install image bytes atomically and keep private receipt detail out of the workspace

Each successful role response is validated in a host-private temporary file, bounded and content-sniffed, then atomically placed at the path declared by the locked descriptor. Before placement, the host proves the target parent is the real canonical Concept root and the target is absent or already contains exactly the reconciled bytes. Links, special nodes, unexpected files, path drift, and conflicting existing bytes fail closed.

The workspace receives only image bytes, `sealed.json`, and sanitized `effect.json`. Provider operation ids, raw request/response bodies, credentials, transport diagnostics, and internal reconciliation state remain under the private host-state root. Status exposes only `invent` waiting plus a bounded safe reason.

**Alternative considered:** persist complete provider responses beside the Concept. Rejected because they can contain private identifiers or unstable metadata and are unnecessary for downstream exact-byte binding.

### 8. Version `NativeMade` and Make gates only for marked Forge/Quest runs

Introduce a Made schema that adds `concept_sha256` and the sanitized `concept_effect_sha256` to the existing exact upstream identity vector. The marked Make packet carries the full sealed Concept plus artifact bindings so the run-local finalizer can rehash it before sealing Made. Unmarked finalizers keep producing schema v1 and remain readable unchanged.

Marked Make performs three additional deterministic checks:

1. the sealed Concept and sanitized effect record still rehash and match the packet;
2. stable component keys in the Concept brief equal the product's declared component keys exactly; and
3. no file anywhere in the exact product manifest has a SHA-256 equal to any sealed Concept image.

The brief's numerical constraints are authoritative instructions; image semantics remain native-agent judgment. The host does not use vision or score adherence. The existing signature-review images must be freshly rendered from actual product geometry and remain product evidence, distinct from Concept art.

**Alternative considered:** store the Concept only in the Make packet and omit it from Made identity. Rejected because downstream gates could no longer prove which design the sealed product was built from.

### 9. Bind Concept into existing revision and invalidation behavior

For marked runs, Make-to-Invent evidence adds the standing sealed Concept and sanitized effect identities. Quest fundamental feedback still returns to `invent`; build-only feedback still returns to `make`. Entering re-Invent archives the prior assignment, Invented, source, pre-render/sealed Concept, images, effect evidence, Made tree, and downstream artifacts under their existing round histories, then invalidates Invent and everything downstream. It consumes exactly the existing one shared lifecycle revision; image retries within one pending Invent proposal do not consume it.

The new Invent packet supplies prior exact Concept and revision evidence. V2 provenance uses `standing_concept_sha256` and `revision_input_sha256`; stale or missing values fail before provider transmission.

**Alternative considered:** create a Concept-only revision edge. Rejected because design changes already belong to Invent and another edge would reintroduce Concept as lifecycle state.

### 10. Update native instructions and acceptance evidence as one protocol version

The materialized Invent reference is expanded with the detailed Concept-authoring sequence already adopted in the integration plan: research, fact attribution, brief, stable components, mechanism/component reconciliation, derived Wish, drawing roles, self-check, and pre-render finalization. The Make reference explains numerical precedence, exact component correspondence, fresh product renders, and Concept-pixel exclusion. The root Manager remains responsible for the single finalizer; a selected Inventor may author bounded content but cannot trigger effects or gates.

Deterministic E2E gains active marked Forge/Quest fixtures and role-level effect doubles, including waits, ambiguity, tamper, revisions, and Spark/unmarked absence. Real-Codex acceptance proves one Invent turn authors the source, host effects occur after exit, and the same session resumes at Make. Documentation and the Concept integration ledger change from dormant/deferred to active for Forge/Quest only.

Private run archives preserve exact Concept contracts and images. Optional public toy snapshots may include sanitized Concept source and images only under the existing explicit public-snapshot rules; they omit host-private effects, provider ids, operation ids, credentials, raw responses, and private Wish context. Factory publication continues to receive only the verified product and manual handoff.

**Alternative considered:** land finalizer, effects, and Make binding as separately deployable activation steps. Rejected for production enablement because any intermediate host/finalizer combination could claim an active Concept while omitting either images or downstream binding. Implementation may use internal commits, but the marker is not shipped until the entire acceptance matrix passes.

## Risks / Trade-offs

- **[Risk] The prerequisite dormant change is still unarchived and may change contract paths or identities.** → Integrate and archive it first, then rebase this change and rerun strict validation before implementation.
- **[Risk] One image per overall/component role increases cost and can make Forge/Quest slower.** → Keep Spark unchanged, render each locked role once, reuse exact prior-role references, and permit retries only for safely absent operations.
- **[Risk] A provider without authenticated post-transmission reconciliation can strand a run in unknown state.** → Preserve exact intent and partial receipts, never blind-retry, expose a bounded operator need, and document provider capability limits before activation.
- **[Risk] Host-written images appear beside agent-authored source and could blur ownership.** → Keep separate pre-render and sealed contracts, manifests, effect receipts, and private operation state; the host never edits source content.
- **[Risk] Made schema versioning affects many gates and fixtures.** → Select the schema from frozen finalizer/capability bytes, retain v1 readers and paths, and cover marked plus unmarked route matrices.
- **[Risk] Concept images may imply impossible geometry.** → Treat brief numbers as binding, keep semantic judgment native, require exact component correspondence, and preserve the evidence-bound Make-to-Invent escape for genuine Concept contradictions.
- **[Risk] Research or provider metadata may leak through public snapshots.** → Keep raw receipts and operation data private, sanitize optional public Concept copies, and add secret/privacy scans over workspace-to-public composition.
- **[Trade-off] Forge/Quest Invent now spans native work plus a host effect and can wait after the native turn.** → The wait remains on the same checkpoint and proposal, avoiding a new Goal or repeated cognition while keeping effect truthfulness.

## Migration Plan

1. Merge and archive `restore-dormant-concept-contracts`; verify its v2 schemas and exact paths are the main-spec and code baseline.
2. Add failure-first tests for capability selection, frozen-run absence, compound packet/finalizer artifacts, pending Invent proposal state, and Made schema versioning.
3. Add the host-private Concept effect ledger and adapter protocol with deterministic transport tests, authorization, reconciliation, atomic output, and privacy boundaries; keep activation marker absent from distributable product-run assets.
4. Extend the materialized Invent finalizer and source instructions, then the host pre-effect validation and bounded Invent rejection path.
5. Add host effect orchestration, pending-proposal wait/resume, sealed Concept finalization, and atomic Invent gate application.
6. Version marked Make packets, Made contracts, exact rehash, component equality, pixel exclusion, and revision bindings.
7. Add the frozen marker and authorization schema only after all component and workflow tests pass; verify Spark and every unmarked fixture remain byte-compatible.
8. Run deterministic Spark/Forge/Quest E2E, real-Codex marked Forge/Quest acceptance, packaging/install tests, effect ambiguity/reconciliation tests, privacy/secret scans, full offline tests, strict OpenSpec validation, and `git diff --check`.
9. Update architecture, product-run, Concept integration, evidence, and public-archive documentation to describe Forge/Quest activation and Spark deferral without claiming visual quality or physical proof.

Rollback disables the marker for newly created runs and removes new adapter availability while retaining readers for every already-created marked checkpoint and its private effect state. A marked run must continue with the exact materialized protocol or be explicitly left waiting; it cannot be downgraded to the older Invent/Make contracts after creation.
