## 1. Freeze Earlier Contracts and Add Failure-First Coverage

- [x] 1.1 Record the exact v1 fixed-role and v2 adaptive capability, schema, finalizer, prompt/effect, packet, and runtime-profile bytes as compatibility fixtures; verify source/package lock tests reproduce every recorded hash.
- [x] 1.2 Add resume tests proving v1 still accepts only its six-file fixed contract and v2 still accepts only its adaptive `visual-plan.json`; verify neither version accepts the new flag, schema, role ids, or prompt protocol.
- [x] 1.3 Add failure-first Concept v4 tests for missing/extra fixed view keys, missing/extra component keys, unsafe keys, empty notes, more than 16 components, and cross-version inputs; verify every case fails before an effect intent exists.

## 2. Define Fixed-View Authoring and Concept v4 Contracts

- [x] 2.1 Add the strict fixed-view instruction schema with `appearance`, exact front/top/bottom/exploded notes, and an exact component-keyed note map; verify valid one-piece and multipart fixtures round-trip canonically while derived roles retain source-array order.
- [x] 2.2 Implement pure derivation of the `4 + component_count` role sequence, explicit role kinds, purposes, canonical paths, and fixed predecessor graph; verify one component yields five roles and sixteen components yields the accepted 20-role boundary.
- [x] 2.3 Reject a seventeenth component, role/path collisions, mismatched component notes, undeclared roles, adaptive role kinds, a reordered derived/sealed role list, and a missing exploded component name; verify normalization reports the violated fixed rule without defaulting or truncating content.
- [x] 2.4 Add pre-render and sealed Concept v4 typed contracts binding the exact two authored files, fixed prompt-protocol version, normalized projections, descriptor, image manifest, and identities; verify canonical golden fixtures and tamper cases.
- [x] 2.5 Extend the common normalized Concept reader to v4 and expose exact ordered `visual_roles` plus `component_visuals`; verify v2, v3, and v4 preserve their version-specific bytes while presenting the stable Make boundary.

## 3. Extend the Materialized Invent Finalizer

- [x] 3.1 Add the packet-gated `invent --source ... --visual-instructions ...` interface for the new marker while retaining v1 `--concept-root` and v2 `--visual-plan`; verify wrong-version flags and mixed inputs fail closed.
- [x] 3.2 Mirror fixed-key validation, role derivation, path derivation, prompt-protocol binding, and Concept v4 normalization in the no-dependency finalizer; verify parity tests produce the same identities as the package implementation.
- [x] 3.3 Extend the independent host Invent gate to reread both authored files and reproduce the v4 contract; verify changed source, instructions, packet paths, component order, prompt version, or claimed identities are rejected.
- [x] 3.4 Add author-write-boundary checks proving the native process cannot author derived roles, prompts, descriptors, manifests, images, effects, receipts, gates, or sealed Concepts; verify deterministic fixtures fail if they cross those boundaries.

## 4. Compile and Execute CAD-Legible Image Requests

- [x] 4.1 Implement the frozen common presentation block and role-specific front/top/bottom/exploded/component blocks using the panda-derived same-object, direct-view, print-only, neutral-presentation, and no-clutter rules; verify golden request tests cover every required clause without adding product features.
- [x] 4.2 Compile each request from separately bound appearance, role note, normalized role facts, and prompt protocol; verify capture tests distinguish exact agent-owned and protocol-owned bytes and show numerical brief facts in the applicable request.
- [x] 4.3 Update the Concept effect planner for front first, parallel-safe top/bottom after front, exploded after all three overall images, and bounded parallel component effects after exploded; verify request captures preserve exact predecessor ordering regardless of execution scheduling.
- [x] 4.4 Bind every intent and receipt to the v4 pre-render identity, fixed role facts, exact blocks, predecessor hashes, canonical path, and provider configuration; verify changing any bound input changes the effect identity and prevents stale reuse.
- [x] 4.5 Reuse current authorization, credential isolation, reconciliation, safe retry, response limits, byte sniffing, atomic installation, and unknown-state paths for v4; verify partial success, ambiguous transmission, provider wait, and resume do not duplicate completed effects.
- [x] 4.6 Seal exactly the fixed ordered role set and rehash the complete image tree; verify missing, extra, duplicate, changed, linked, mixed-proposal, or wrong-order bytes prevent Invent advancement.

## 5. Update Make Reconstruction Handoff

- [x] 5.1 Add v4 Make packet fields for the exact fixed-role summary and stable-key `component_visuals` map while preserving sealed Concept/effect identities and `required_product_component_keys`; verify packet fixtures are deterministic and bounded.
- [x] 5.2 Update routed Make guidance to use overall views for envelope/silhouette, exploded for assembly/part identity, and isolated views for component form/interfaces, with normalized numerical facts authoritative; verify materialized reference tests contain the complete mapping.
- [x] 5.3 Extend the Make finalizer and host gate to parse and independently rehash Concept v4 through the common reader; verify stale Concept/effect bindings, component mismatches, and copied Concept pixels fail as they do for earlier versions.
- [x] 5.4 Preserve early exact-state proof, fresh product renders, blind schema-v4 signature review, integrated CAD verification, Quest Playtest, Release PDF validation, and publication gates; verify the existing full route matrix passes without accepting Concept images as evidence.
- [x] 5.5 Bind Make-to-Invent revision to prior v4 source, fixed instructions, sealed Concept/effect identities, and exact feedback; verify a stable-component change deterministically replaces the component-role set and invalidates downstream artifacts within the shared revision budget.

## 6. Materialize, Freeze, and Route the New Capability

- [x] 6.1 Add `invent-concept-v3.md` with the exact two-input skeleton, fixed image list, depiction-note example, anti-CAD boundary, finalizer command, and immediate-finalization recovery rule; verify clean materialized workspaces contain the exact locked bytes.
- [x] 6.2 Add the matching immutable runtime-profile revision without changing current Invent reasoning, compaction, timeout, turn budget, or source-handoff economics; verify only new marked Forge and Quest runs select it.
- [x] 6.3 Add capability selection and rollback controls so v3 remains unavailable until acceptance passes, can later be enabled only for new runs, and can be disabled without downgrading frozen v3 checkpoints; verify creation/resume selection tests across Spark, unmarked, v1, v2, and v3 runs.
- [x] 6.4 Update stage packets, recovery inputs, artifact registration, archive/privacy allowlists, package data, and source locks for the new instruction path; verify no prompt, provider credential, private image byte, or effect identifier enters public or native-readable state improperly.

## 7. Prove End-to-End Behavior

- [x] 7.1 Update deterministic Forge and Quest native doubles to author only source plus fixed instructions and call the production finalizer; verify a two-component run produces exactly six provider calls and resumes the same session at Make with the sealed v4 identities.
- [x] 7.2 Add deterministic one-piece, 16-component boundary, 17-component rejection, invalid-key, predecessor failure, partial-effect, ambiguous-effect, resume, revision, and exact-sealing scenarios; verify production finalizers, gates, coordinators, and checkpoint transitions are not mocked.
- [x] 7.3 Run focused Concept, workflow, integration, Make, packaging, deterministic E2E, frozen-compatibility, wait/resume, archive/privacy, Playtest, and Release suites; record exact commands and results and verify `git diff --check` succeeds.
- [ ] 7.4 Run opt-in authenticated Forge acceptance from a clean private workspace; verify real Codex discovers the fixed contract, authors two inputs, finalizes within bounded recovery, exits before effects, and resumes the same session at Make.
- [ ] 7.5 Run equivalent opt-in authenticated Quest acceptance through Playtest and Release; verify the fixed Concept inventory changes no downstream proof, credential, or publication authority.
- [x] 7.6 Produce a narrow acceptance report binding capability/profile versions, authored hashes, component/role counts, finalizer rejections, effect reconciliation, session continuity, and terminal gates; verify it makes no unsupported visual-quality, reconstructability, printability, or physical-performance claim.

## 8. Document and Activate

- [x] 8.1 Add an architecture decision recording why deterministic construction views replace adaptive Concept roles while signature evidence remains in Make; verify architecture links and supersession notes distinguish v1, v2, and v3 behavior.
- [x] 8.2 Update runtime, Concept integration, operator, and product-run documentation with the fixed role graph, prompt ownership, 20-image/16-component bound, visual limitations, recovery, and rollback; verify documentation describes implemented versus not-yet-enabled behavior truthfully.
- [x] 8.3 Run `openspec validate fix-concept-image-set-for-cad --strict` and all repository documentation/package lock checks; resolve every failure without weakening a production gate.
- [ ] 8.4 Enable `invent-concept-v3` only after deterministic and authenticated acceptance evidence passes; verify new Forge/Quest runs freeze v3 while every existing checkpoint resumes under its original contract.
