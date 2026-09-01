## 1. Characterize the Dormant Boundary

- [x] 1.1 Add source-branch compatibility fixtures for schema-v1 pre-render and sealed Concept contracts, including the exact `948a34d` routed-Wish and `ea34822` round-freshness cases, and verify focused tests fail while `src/workshop/concept/` is absent.
- [x] 1.2 Add architecture tests that forbid Concept imports from workflow, runtime, integrations, credentials, and effect modules and that assert import/evaluation performs no network, credential, checkpoint, stage-packet, or out-of-root write; verify the tests fail against representative forbidden dependencies.
- [x] 1.3 Add current-route regression assertions for stage enumeration, Spark/Forge/Quest packets, Made fields, revision edges, and absence of Concept stages/Goals/turns/transitions/artifacts/gates/waits; verify the assertions pass before implementation and remain the non-interference baseline for the future merged creative-stage direction.

## 2. Restore Exact Concept Contracts

- [x] 2.1 Recreate the component-owned `src/workshop/concept/` package with strict finite canonical JSON, bounded text and files, duplicate-key rejection, safe relative paths, regular-file enforcement, and typed contract/artifact errors; verify focused tests reject malformed JSON, unsafe paths, links, special nodes, and over-limit inputs.
- [x] 2.2 Restore the compatibility-only schema-v1 DerivedWish and Concept reader from `feat/concept-phase` without checkpoint dispatch or implicit upgrade, and verify canonical pre-render/sealed round-trips plus exact routed-Wish rewrite rejection.
- [x] 2.3 Implement the schema-v2 provenance and expected-context records for `invent` and `spark-make` origins, binding Wish, product id/objective/context, assignment, Taste, blueprint, Invented, creative-source, round, standing Concept, and revision identities; verify both origins pass with exact bytes and each substituted or stale field fails by name.
- [x] 2.4 Implement distinct schema-v2 pre-render and sealed Concept types with canonical round roots, source manifests, path-only versus hashed descriptors, complete overall/component roles, and whole-tree identities; verify mixed states, missing or extra roles, duplicate paths, hash drift, and changed tree bytes fail closed.
- [x] 2.5 Add the deterministic local conversion boundary from validated pre-render source plus already-present image bytes to a sealed value, with no writes, provider calls, credentials, effect records, or gate decisions; verify incomplete files remain pre-render only and complete exact files reproduce a stable sealed identity.

## 3. Restore Structural Evaluation

- [x] 3.1 Port and adapt the brief evaluator for required object/category, positive envelope and wall thickness, print stance, fit target, distinctive features, and complete component form/dimensions/placement/interfaces; verify every missing, placeholder, non-positive, or objective-restating case is rejected with its rule.
- [x] 3.2 Implement research and fact-attribution checks, derived-Wish preservation, complete overall/component drawing instructions, deterministic reference ordering, safe descriptors, and exploded component naming; verify unknown, missing, dual, duplicate, or inconsistent inputs fail and valid source returns bounded check-only evidence.
- [x] 3.3 Prove evaluator purity with tests that it neither repairs/defaults data nor returns workflow gate/transition objects, inspects pixels, claims semantic quality/buildability/printability, mutates input trees, or performs an external effect.

## 4. Package and Discover Schemas

- [x] 4.1 Add separate component-owned v1 and v2 Concept JSON schemas and register them through the existing schema discovery boundary without importing Concept runtime code; verify source-tree discovery returns both exact files.
- [x] 4.2 Include `concept/schemas/*.json` in wheel and sdist package data and extend installed no-dependency acceptance; verify built artifacts contain the same schema bytes and discovery succeeds in the isolated installation.

## 5. Prove Current Workflow Non-Interference

- [x] 5.1 Run the focused Concept, artifact-schema, Wish, Match, Invent, Make, workflow-stage, and packet test suites and verify no current contract or checkpoint shape changes and no standalone Concept lifecycle identity is introduced.
- [x] 5.2 Run the required deterministic E2E fidelity matrix with `WORKSHOP_RUN_DETERMINISTIC_E2E=1` and verify traces remain exactly Spark `Make -> Release`, Forge `Invent -> Make -> Release`, and Quest `Invent -> Make -> Playtest -> Release`, with no Concept proof residue.
- [x] 5.3 Run static dependency/credential/network policy checks and the relevant packaging tests, and verify dormant Concept code cannot reach provider transports, credentials, effect ledgers, stage finalization, or lifecycle mutation.

## 6. Reconciliation Documentation and Final Verification

- [x] 6.1 Update `docs/CONCEPT_PHASE_INTEGRATION_PLAN.md` so `948a34d` and the contract/freshness portion of `ea34822` are marked restored, schema-v1 is compatibility-only, and the later integration target is a Concept sub-boundary of Forge/Quest Invent and Spark folded Make rather than a standalone stage; verify the commit-disposition table has no ambiguous status and finalizer wiring, durable image effects, downstream bindings, and activation remain deferred.
- [x] 6.2 Add a concise change note and update architecture/component documentation to describe dormant v1/v2 contracts, the future compound creative-stage boundary, and narrow evidence claims without implying active Concept, a separate Concept Goal/turn/checkpoint, resumable historical Concept runs, visual quality, publication, manufacture, or delivery.
- [x] 6.3 Run the full offline test suite, strict OpenSpec validation, package build/install acceptance, secret scan, and `git diff --check`; record exact commands and passing results before the change is considered implementation-complete.
