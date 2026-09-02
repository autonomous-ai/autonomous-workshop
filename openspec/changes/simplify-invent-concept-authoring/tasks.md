## 1. Freeze the Compatibility Baseline

- [x] 1.1 Finish and record the active `invent-concept-v1` marker, packet, finalizer, sealed-contract, fixed-role, and Make-reader bytes as the compatibility baseline; verify the existing marked Forge and Quest suites pass unchanged.
- [x] 1.2 Add failure-first tests proving historical v1 checkpoints still require six authored files and fixed roles after v2 code is installed; verify resume produces the same identities and downstream packet fields.
- [x] 1.3 Add route-selection tests proving Spark, unmarked runs, and older frozen effort profiles cannot select the simplified capability; verify their materialized files and stage traces are byte-for-byte unchanged.

## 2. Define the Two-Input Authoring Contracts

- [x] 2.1 Add strict typed schemas for the v2 consolidated Invent source, including selection, ranking, physical concept, stable components, interaction trace, proof target, decisions, research, assumptions, and unresolved risks; verify valid and malformed fixtures with focused contract tests.
- [x] 2.2 Add strict typed schemas for the ordered adaptive visual plan, including the frozen 2-to-20 role bound, role kinds, purposes, complete instructions, appearance references, and component subjects; verify 20 roles are accepted while 21 roles, duplicate ids, forward references, cycles, missing required roles, unknown component keys, and unjustified optional roles are rejected.
- [x] 2.3 Add fixtures for a minimal one-piece concept and a multipart concept with need-driven roles; verify each fixture authors exactly `invent-source.json` and `visual-plan.json` and contains no CAD or finalizer-owned projection.
- [x] 2.4 Add research validation that permits jointly empty sources/findings but requires support for externally grounded build-critical constraints and reasons for deliberate numerical constraints; verify unsupported facts and fabricated attribution patterns fail.

## 3. Normalize and Finalize Concept v3

- [x] 3.1 Implement pure normalization from the two authored inputs and packet bindings into the normalized brief, research, routed-Wish binding, drawing instructions, descriptor, source manifest, and canonical identities; verify deterministic golden fixtures and repeated-run identity equality.
- [x] 3.2 Derive safe image paths and canonical hashes in the normalizer, rejecting unsafe or colliding role ids; verify the native fixtures never calculate hashes or author descriptor, manifest, or derived-Wish files.
- [x] 3.3 Add the sealed pre-render and rendered Concept v3 contracts plus a common normalized reader for v2 and v3; verify round-trip parsing preserves all Make-facing fields and rejects mixed-version or ambiguous trees.
- [x] 3.4 Extend the installed no-dependency finalizer with the packet-gated `invent --source ... --visual-plan ...` interface while retaining `--concept-root` only for v1; verify wrong-version flags and extra authored Concept inputs fail before effects.
- [x] 3.5 Mirror normalization and identity validation independently in the host gate; verify tampering with either authored input or any derived projection is detected even when finalizer output claims success.
- [x] 3.6 Add source/package lock tests for the v2 schemas, reference, finalizer, and protocol marker; verify materialized bytes match their recorded hashes.

## 4. Execute Adaptive Concept Effects

- [x] 4.1 Replace the v2 fixed-role planner with an ordered validated role-graph planner capped at 20 roles while retaining the v1 planner; verify minimal and multipart plans produce exactly their declared role order and paths and a 21-role plan creates no effect intent.
- [x] 4.2 Serialize each provider request from the exact authored role instruction plus the canonical normalized constraint block and declared earlier image bytes; verify request-capture tests show no host-authored design content or undeclared reference.
- [x] 4.3 Bind v2 effect intents and receipts to the checkpoint, pre-render identity, role facts, exact request inputs, provider profile, and derived path; verify any role, instruction, constraint, reference, or path change yields a distinct identity.
- [x] 4.4 Preserve pre-transmission intent, credential isolation, reconciliation, safe retry, byte validation, atomic install, and unknown-state behavior for arbitrary role counts; verify partial completion, ambiguous effects, and resume reuse with deterministic provider fakes.
- [x] 4.5 Seal exactly the validated adaptive role set and reject missing, extra, duplicate, changed, or mixed-proposal images; verify aggregate Concept and effect hashes cover every and only declared role.

## 5. Update the Make Handoff Without Weakening Proof

- [x] 5.1 Build Make packets from the common normalized Concept reader and add the bounded `concept_visual_roles` summary while retaining sealed Concept, effect, Invented, and ordered component-key bindings; verify v2 and v3 packet fixtures expose the same stable Make boundary.
- [x] 5.2 Update the routed Make reference to treat normalized physical facts as authoritative and adaptive images as non-evidentiary design direction; verify package tests contain no mandatory front/top/bottom/exploded or per-component Concept-image assumption for v3.
- [x] 5.3 Update the Make finalizer and host gate to accept sealed Concept v3 through the common view while independently rehashing the Concept and effect trees; verify tampered identities and raw-authoring dependencies fail.
- [x] 5.4 Preserve exact equality between normalized stable component keys and `product.json.components`, recursive Concept-pixel exclusion, and Made v2 bindings to the two opaque Concept hashes; verify component mismatch and copied-pixel regression tests fail as before.
- [x] 5.5 Preserve early mechanism/form proof, print preflight, fresh exact-CAD states and renders, blind signature review, integrated verification, Quest Playtest, Release manual validation, and publication gates; verify the existing Make-to-Release route matrix passes for v3 without waivers.
- [x] 5.6 Bind Make-to-Invent revision requests to the sealed v3 Concept/effect identities and provide prior source, visual plan, normalized Concept, research, and feedback to the next Invent round; verify invalidation and the shared revision budget behave unchanged.

## 6. Materialize Native Guidance and Recovery

- [x] 6.1 Add the immutable `invent-concept-v2` reference with a bounded skeleton and one nontrivial example that makes the two outputs, anti-CAD boundary, adaptive roles, and finalizer call explicit; verify materialized product runs contain the exact frozen reference.
- [x] 6.2 Add a matching deep runtime-profile revision with the existing reasoning, compaction, timeout, and economics settings; verify only new marked Forge and Quest runs select it.
- [x] 6.3 Update Invent source-handoff recovery to finalize immediately when both inputs exist and otherwise repair only the smallest missing input before finalizing; verify recovery tests do not rerank, research, delegate, or restart exploration first.
- [x] 6.4 Keep v2 selection disabled until all activation evidence is present and add rollback behavior that blocks future selection without downgrading frozen v2 runs; verify disabled selection and frozen-resume tests.

## 7. Prove Workflow and Ownership Fidelity

- [x] 7.1 Extend deterministic Forge and Quest route doubles so they write only the two native inputs and call the public finalizer; verify an ownership guard rejects doubles that write normalized projections, hashes, images, receipts, gates, or Make bindings.
- [x] 7.2 Cover minimal one-piece roles, multipart roles, the 20-role success boundary, the 21-role pre-effect rejection boundary, invalid dependencies, revised role sets, missing roles, ambiguous effects, component mismatch, and copied pixels in deterministic end-to-end tests; verify traces remain `Wish -> Invent -> Make` with no Concept lifecycle event.
- [x] 7.3 Add wait/resume, archive, privacy, invalidation, and source-package compatibility tests for v3; verify credentials and private product artifacts never enter native transcripts or public archives.
- [ ] 7.4 Run the complete unit, workflow, integration, packaging, deterministic route, and frozen-compatibility suites plus `git diff --check`; record exact passing commands and any intentionally skipped authenticated tests.

## 8. Validate Real-Agent Usability and Activate

- [ ] 8.1 Run opt-in authenticated Forge acceptance from a clean private run with no schema overlay; verify real Codex discovers the v2 reference, authors both inputs, finalizes directly or through bounded repair, exits before host effects, and resumes the same session at Make.
- [ ] 8.2 Run the equivalent opt-in Quest acceptance through Make and required Playtest; verify the simplified Invent boundary does not alter Playtest, Release, publication, or external-effect authority.
- [ ] 8.3 Produce the narrow acceptance report with capability version, session continuity, turn timing/count, finalizer rejection count, authored-input hashes, role count, effect resume, and Make transition; verify it makes no unsupported quality, buildability, performance, or economics claim.
- [ ] 8.4 Enable the v2 marker for new marked Forge and Quest runs only after the deterministic matrix and authenticated acceptance pass; verify new runs freeze v2 while existing v1 and v2 checkpoints remain exactly resumable.
- [x] 8.5 Update architecture and operator documentation with implemented behavior, frozen compatibility, rollback, and the Invent-versus-Make responsibility boundary; verify OpenSpec strict validation and documentation link checks pass.
