## Context

See `proposal.md` for motivation. Current `main` already implements the ADR 0016 Spark/Forge/Quest routes, terminal published Release, deterministic production-boundary E2E, and the effort-aware real-Codex acceptance tier. It intentionally removed `src/workshop/concept/` from production while retaining main specs written for the older active Concept topology.

The useful source-branch material is concentrated in deterministic types and rules: exact routed-Wish preservation (`948a34d`), round freshness (`ea34822`), pre-render versus sealed descriptor handling (`25e647d`/`c2873bd`), strict tree rehashing, and brief/research/instruction validation. The source branch's workflow wiring assumes standalone Match, active Concept, inline provider calls during gate evaluation, Make/Playtest Concept edges, and pre-terminal private Deliver. Those assumptions cannot cross into current `main`.

The current creative boundary also differs from the source branch. Forge and Quest author assignment plus Invented contracts during Invent and preserve `source.json`; Spark authors the same provenance inside Make from one combined creative source. The future Concept protocol must bind either origin without creating a standalone Concept stage: it will be a compound sub-boundary of Invent for Forge/Quest and folded Make for Spark. This change establishes only the route-neutral data needed by that later wiring and cannot add artifacts to either live route.

## Goals / Non-Goals

**Goals:**

- Restore reusable, typed, exact-byte Concept data and pure structural checks as a component-owned dormant package.
- Preserve historical schema-v1 readability without interpreting it as the new route-aware contract.
- Define a new route-aware contract that can bind Forge/Quest Invent source or Spark folded creative source with the same assignment, Invented, Taste, blueprint, Wish, and revision guarantees.
- Keep pre-render source identity distinct from sealed image identity so later host effects cannot be confused with agent finalization.
- Establish that future Concept authoring and sealing extend the first active creative stage rather than adding a lifecycle stage, Goal, or native turn.
- Make lifecycle non-interference mechanically testable, not only documented.

**Non-Goals:**

- Add a `concept` finalizer subcommand, stage packet, native Goal, checkpoint state, transition, rejection loop, or wait/resume path.
- Persist Spark's currently ephemeral combined source or change current Invent/Make artifacts; the dormant contract accepts a caller-supplied source binding for future wiring only.
- Restore an image-provider adapter, choose a provider, authorize transmission, create an effect intent, render pixels, or reconcile remote state.
- Bind Concept into NativeMade, Playtested, NativeRelease, Factory, public archives, or current product-run instructions.
- Activate the compound Concept sub-boundary for Spark, Forge, or Quest. A later activation change must version the affected stage packets, finalizers, gates, waits, downstream bindings, and frozen routes without adding a standalone Concept stage.

## Decisions

### 1. Extract the contract layer; do not cherry-pick the feature implementation

Implementation will use the source branch as reference and re-create only component-owned files under `src/workshop/concept/`: data contracts, strict readers, exact-tree validation, structural rules, and schemas. It will not copy edits to `workflow/native_run.py`, `workflow/stage_gates.py`, `.agents/product-run/`, the run-local finalizer, integrations, Make, Playtest, Release, or runtime process handling.

The dormant package may import narrow shared primitives from `workshop._validation`, `workshop.artifacts`, `workshop.errors`, `workshop.wish`, `workshop.match.native`, and `workshop.invent.native`. It must not import `workshop.workflow`, `workshop.runtime`, `workshop.integrations`, or credential/effect modules. A policy test will enforce this one-way dependency boundary.

**Alternative considered:** cherry-pick `948a34d`, `ea34822`, or the final feature-branch tree and delete obvious workflow calls. Rejected because those commits share files with obsolete topology and effect behavior; deletion-by-inspection is weaker than rebuilding against current contracts.

### 2. Keep historical schema v1 readable and introduce an explicit route-aware v2

The source branch's `autonomous-workshop.concept` schema v1 will be restored as a strict compatibility reader, including its exact upstream fields, pre-render/sealed descriptor distinction, and whole-tree validation. It remains dormant and is never accepted into a current checkpoint.

A schema-v2 contract will add one canonical provenance object with:

- `origin`: exact enum `invent` or `spark-make`;
- routed Wish hash plus product id, objective, and context identity;
- assignment, selected Taste, blueprint, and Invented hashes;
- safe in-run creative-source path and SHA-256;
- round;
- nullable standing-Concept and revision-input identities whose presence rules distinguish initial from revision contracts.

Both origins require the caller to provide the exact accepted assignment and Invented contracts and the exact source bytes they came from. The v2 validator rehashes the source, checks `NativeInvented.assert_context(assignment)`, checks every duplicated binding, and then validates round/revision freshness against an explicit expected-context object. `origin` changes validation expectations but does not select a lifecycle route.

V1 and v2 use separate schema files and explicit parsers. No v1 payload is upgraded implicitly, and no v2 field is guessed from a v1 contract.

**Alternative considered:** extend schema v1 in place. Rejected because adding route origin and creative-source freshness would silently reinterpret historical hashes and make old exact identities ambiguous.

### 3. Model pre-render and sealed states as separate contract types

V2 will use distinct pre-render and sealed types sharing immutable source and provenance records:

- the pre-render form binds `brief.json`, `research.json`, `prompts.json`, `derived_wish.json`, and a descriptor whose leaves contain only canonical image output paths;
- the sealed form binds those same exact source identities plus a descriptor whose leaves contain path and SHA-256, and a manifest containing each exact regular image.

Conversion is a deterministic constructor over caller-supplied, already-present bytes. It does not call a provider, read credentials, mutate workflow state, or write a gate. The constructor reopens every file, rejects mixed descriptor leaf shapes, requires the complete role set, and returns a new sealed value. Any future host protocol remains responsible for effect records and atomic file placement before calling this boundary.

**Alternative considered:** retain one v1 class that infers state from descriptor shape. Rejected for new data because an explicit type boundary prevents pre-render source from being mistaken for completed effect output. V1 retains inference only for exact compatibility.

### 4. Keep structural evaluation pure and separate from gate decisions

The evaluator consumes a validated in-memory Concept tree, routed Wish, and expected context. It checks only deterministic structure:

- required physical facts and positive dimensions;
- complete component form, dimensions, placement, and interfaces;
- exactly-one source-or-decision attribution for every required fact;
- bounded source/findings records and exact derived-Wish preservation;
- complete overall/component drawing instructions, reference ordering, safe distinct descriptor paths, and exploded component naming;
- complete manifests and exact hashes for sealed data.

It returns a bounded evidence mapping describing checks performed or raises a typed contract/artifact error naming the failed rule. It does not return `StageGateDecision`, choose a transition, write an artifact, score semantics, inspect pixels, or claim buildability/printability.

**Alternative considered:** restore `evaluate_concept_stage` behind a feature flag. Rejected because even disabled lifecycle code would mix proposal parsing, effect execution, sealing, gate evidence, and transitions before their current-route design exists.

### 5. Fold future Concept work into the first active creative stage

Concept is a data, validation, and host-effect sub-boundary, not a lifecycle stage. A future activation change will extend the existing first creative stage:

- Forge and Quest use one Invent Goal and native turn to select the Inventor, invent the product, and author the complete pre-render Concept source;
- Spark uses its existing folded Make Goal and native turn to author the compact Invented provenance and any enabled pre-render Concept source before geometry is accepted;
- no route receives a `concept` stage value, Concept Goal, separate native turn, forward transition, pass-through artifact, or Concept-only checkpoint;
- the native turn finalizes only authored pre-render bytes, then returns to the host;
- the host validates those bytes, performs any separately authorized and durable image effect, reconciles exact returned bytes, seals the Concept identity, and decides whether the owning creative stage may advance.

For Forge and Quest, the detailed Concept-authoring portion inside Invent is:

1. Freeze the invention's design intent: signature interaction, anti-generic signature, mechanism, intended experience, and non-negotiable constraints.
2. Separate factual research from deliberate design decisions. Every required physical fact receives exactly one source attribution or one recorded decision and reason.
3. Author the physical brief: object, category, positive envelope, wall thickness, fit target, distinctive features, print orientation and support policy, assumptions, and unresolved risks.
4. Define every component with a stable key, purpose, form, positive dimensions, placement, interfaces, and assembly relationship.
5. Reconcile interaction and construction by tracing the intended interaction through the components, naming motion, fit, load, and assembly dependencies, and removing contradictions between the mechanism and physical breakdown.
6. Author the derived-Wish record while preserving the routed product id, objective, and context exactly and placing researched constraints in their separate field.
7. Author the visual plan: `front`, `top`, `bottom`, `exploded`, and one role per component, each with complete drawing instructions, a shared bounded presentation treatment, deterministic prior-role references, and one safe distinct output path.
8. Evaluate the source for placeholders, missing roles, unattributed facts, duplicate paths, component-name drift, dimension conflicts, and unsupported claims; revise the authored source rather than asking the host to repair it.
9. Emit the pre-render Concept source. It contains no image bytes and makes no rendering, buildability, printability, physical-test, or product-evidence claim.
10. Finalize the compound creative-stage proposal and return. Only the host may validate, execute or reconcile an authorized image effect, seal exact image bytes, and advance to Make.

This sequence keeps one native Goal and lets one stage gate bind both Invented provenance and the eventual sealed Concept while retaining a before/effect/after boundary inside host processing.

**Alternative considered:** reactivate Concept between Invent and Make. Rejected because it adds a native Goal, turn, checkpoint, and transition for work that belongs to the same creative commitment, increases every applicable route's turn cost, and conflicts with the effort model's folded-first-creative-stage direction.

### 6. Treat Spark provenance as supported data, not live wiring

The v2 provenance validator supports `spark-make` and tests it against a fixture containing the exact combined creative source and the assignment/Invented contracts derived from it. This proves the data model will not force a standalone Match or Invent turn later.

Current Spark finalization is deliberately untouched and therefore does not start preserving this source merely because the dormant type can bind it. The later activation design must persist the combined source and author the enabled Concept source inside that same folded Make Goal. It may not introduce a standalone Invent or Concept stage for Spark. That wiring is lifecycle-visible and cannot be smuggled into this component slice.

**Alternative considered:** update current Spark Make to preserve source now. Rejected because it would change a live artifact set and deterministic E2E in a change whose acceptance contract promises route non-interference.

### 7. Package schemas through the existing component discovery boundary

Concept schemas will live under `src/workshop/concept/schemas/`, be included by project package data, and be registered in `workshop.artifacts.schema_registry` alongside other component-owned schemas. Source-tree, wheel/sdist, and installed no-dependency acceptance tests will verify discovery and exact bytes.

Registration is the only existing shared registry change. It exposes inert files and does not import the Concept runtime package or activate behavior.

**Alternative considered:** keep the schema only beside tests until activation. Rejected because package/discovery drift is exactly what this slice is intended to settle independently.

### 8. Prove dormancy with architecture and route regression tests

Focused unit tests will cover canonical round-trips, duplicate keys, finite JSON, size bounds, safe paths, links/special nodes, manifest drift, routed-Wish rewriting, both provenance origins, missing/extra roles, pre-render/sealed confusion, and stale rounds/revision inputs.

Architecture tests will assert the dormant package has no workflow/runtime/integration imports and that importing/evaluating it does not inspect credentials, use network transports, or create files outside caller-owned test roots. Existing stage enumeration and packet tests plus the required deterministic Spark/Forge/Quest E2E remain the regression proof that no Concept turn, artifact, gate, wait, or binding appeared.

**Alternative considered:** rely only on the absence of edits to workflow files. Rejected because indirect imports or schema-registration side effects can still violate dormancy.

## Risks / Trade-offs

- **[Risk] V2 may encode provenance differently from the later compound-stage activation design.** → Keep route origin and exact identities general, omit lifecycle fields, and revise the dormant schema before activation if the owning-stage gate needs a different binding.
- **[Risk] Restoring v1 may look like support for resuming old active-Concept runs.** → Label v1 as parse/validation compatibility only and add no checkpoint dispatch; documentation must not claim historical run resumability from this slice.
- **[Risk] Current main specs contain active standalone-Concept promises that no longer match code or the selected direction.** → Archive explicit removals with migration notes and replace them with testable dormant requirements plus an explicit prohibition on a future standalone Concept stage.
- **[Risk] Schema discovery changes can break minimal installations.** → Add wheel/sdist and no-dependency schema-discovery tests and keep schema loading free of optional image/provider libraries.
- **[Risk] A sealing helper could become an unsafe effect shortcut.** → Accept only local already-present bytes, perform no writes or calls, expose no credentials, and name the result structural/exact-byte validation rather than provider completion evidence.
- **[Trade-off] This slice adds code that production routes do not yet use.** → The separation is intentional: it makes the data boundary independently reviewable and testable before expensive or lifecycle-visible behavior depends on it.

## Migration Plan

1. Add failing focused tests for v1 compatibility, v2 provenance and freshness, structural validation, exact tree handling, package discovery, forbidden imports, and current-route absence.
2. Restore and adapt the narrow Concept package and schemas until those tests pass, without editing active workflow/finalizer/integration code.
3. Run component tests, package acceptance, current workflow/packet tests, and the required deterministic E2E route matrix.
4. Update `docs/CONCEPT_PHASE_INTEGRATION_PLAN.md` and change notes so `948a34d` and the contract portion of `ea34822` are marked restored, the future compound creative-stage direction is explicit, and finalizer, image effect, and activation work remain deferred.
5. Merge this slice before proposing the dependent pre-render finalizer protocol.

Rollback removes the dormant package, schema registration, tests, and documentation disposition. Because the package has no checkpoint or external-effect wiring, rollback requires no run-state migration and must leave current effort routes untouched.
