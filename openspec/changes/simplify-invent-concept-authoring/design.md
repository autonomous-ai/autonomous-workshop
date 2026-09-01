## Context

See `proposal.md` for motivation. The current marked Forge/Quest protocol freezes `invent-concept-v1.md`, accepts `invent --source ... --concept-root ...`, and requires the native turn to author the routed Invent source plus five strict files under the Concept root. The finalizer and host separately validate those exact bytes, the host renders a fixed overall/component role graph after native exit, and Make receives a sealed Concept whose common useful fields are the physical brief, image descriptor and manifest, Concept identity, effect identity, and stable component keys.

The new protocol must preserve four architectural boundaries:

- one persistent native session and one Invent Goal, with no Concept lifecycle stage;
- native ownership of research, physical design, component decisions, and image instructions;
- host-only credentials, durable effects, reconciliation, and exact-byte sealing; and
- deterministic Make gates over sealed identities, component equality, copied pixels, CAD, review, Playtest, manual, and publication.

It must also coexist with immutable materialized v1 runs and the current deep Invent source-handoff recovery behavior.

## Goals / Non-Goals

**Goals:**

- Reduce native Invent/Concept authorship to two nonduplicative creative inputs.
- Make the authoring sequence output-first and feasible inside the existing bounded Invent turn and recovery.
- Preserve a normalized, typed, hash-bound Concept boundary for Make and downstream revisions.
- Spend Concept image effects on form and signature communication rather than a category-blind fixed view inventory.
- Keep research and provenance truthful without requiring synthetic browsing or agent-computed canonical hashes.
- Make every v2 behavior additive and frozen so v1, Spark, and unmarked runs remain resumable.

**Non-Goals:**

- Creating CAD, STEP, STL, meshes, slicer output, or physical evidence during Invent.
- Adding a Concept stage, Goal, turn, checkpoint, transition, agent framework, host model judge, prompt chain, or Python-owned cognitive loop.
- Weakening Make proof, final CAD verification, blind review, Playtest, Release, Factory, or external-effect gates.
- Activating the simplified Concept boundary for Spark in this change.
- Migrating or rewriting already-materialized v1 workspaces or published product archives.

## Decisions

### 1. Freeze an additive `invent-concept-v2` capability

New marked Forge and Quest runs freeze a new immutable `references/invent-concept-v2.md` plus a matching finalizer protocol marker. The v1 reference, schemas, finalizer interface, fixed roles, and readers remain packaged and selected only for v1 checkpoints. The checkpoint subject binds the exact capability hash and Concept contract version.

The route remains `Wish -> Invent -> Make` and the new marker adds no lifecycle state. A new deep runtime-profile revision retains current reasoning, compaction, timeout, proof, and gate economics but updates Invent recovery's source-handoff prompt to recognize the two required inputs. It does not change a frozen older profile.

**Alternative considered:** revise `invent-concept-v1.md` in place. Rejected because materialized run bytes and same-session recovery are immutable protocol authority.

### 2. Author one consolidated Invent source and one visual plan

The existing `--source` document remains a strict object with `selected_inventor_id`, roster-covering `ranking`, `concept`, and `research`. For v2, `concept` becomes the complete agent-owned physical authority rather than a compact record duplicated into `brief.json`.

Its contract includes:

- title, summary, object/category, signature interaction, anti-generic signature, intended experience, and non-negotiable constraints;
- applicable envelope, print stance, wall/minimum-feature or fit constraints only when meaningful to the design;
- stable components with key, name, purpose, form, build-critical measurements, placement, interfaces, assembly relationship, and contribution to the signature interaction;
- a traced interaction/causal path through the components;
- the smallest exact Make proof that can falsify the hardest relationship or intended form;
- constraint records with semantic ids and a basis that points either to a recorded research finding or a deliberate decision rationale;
- assumptions and unresolved risks.

`research` contains `sources` and `findings`, both of which may be empty together when no external uncertainty remains. A source stores its stable origin, bounded supporting excerpt, and retrieval time; the finalizer derives excerpt hashes. A finding cites sources. Deliberate decisions live in the concept and are not disguised as findings. Build-critical constraints cite a finding or decision id, while ordinary original names and features need no duplicate attribution ledger.

The packet names one canonical v2 visual-plan path. The finalizer interface becomes:

```text
invent --source <invent-source.json> --visual-plan <packet visual_plan_path>
```

`--concept-root` remains the packet-gated v1 interface and is rejected for v2. The finalizer preserves the exact source as the existing Invent `source.json` and the exact visual-plan bytes at their packet path.

**Alternative considered:** keep `brief.json` and `research.json` agent-authored alongside the Invent source. Rejected because it preserves the cross-file restatement and drift that this change removes.

### 3. Use an ordered adaptive visual-plan schema

`visual-plan.json` is a strict v2 object with `schema_version`, `kind`, `presentation`, and ordered `roles`. Each role has:

- a unique safe `id`;
- a `kind`: `primary-form`, `signature-experience`, `assembly`, `alternate-view`, or `component`;
- a nonempty `purpose` stating the unique information it communicates;
- a complete agent-authored `instruction`;
- zero or more ordered earlier role ids in `appearance_references`;
- zero or more stable component keys in `subject_components`.

Exactly one primary-form role is first and has no references. At least one signature-experience role is required. The ordered role list contains at least two and no more than 20 roles, producing the same number of Concept images. All other roles must justify information not already communicated. Component keys must exist in the consolidated source. References form an acyclic prefix graph because every reference must point to an earlier role. The finalizer rejects a 21st role before any provider intent or transmission. Because the capability is frozen, changing this ceiling later requires a new capability version rather than mutating v2.

The provider request binds two exact agent-owned inputs without adding design content: the role instruction and a canonical normalized physical-constraint block projected from the consolidated source. The adapter serializes those exact blocks with fixed protocol labels and supplies only declared earlier image bytes. This is deterministic transport composition, not host prompt authorship.

The signature role must communicate the promised action, transformation, perceptual result, or relationship. For state-changing products it names distinct states; another viewpoint of one unchanged state is invalid. A one-piece product may legitimately stop at primary plus signature. Multipart products earn assembly or component roles only when a named relationship would otherwise remain hidden.

**Alternative considered:** retain front/top/bottom/exploded plus all components and add a signature image. Rejected because it increases provider cost and native prompt work while retaining irrelevant views for many open-ended products.

### 4. Normalize into a versioned durable Concept instead of exposing raw authoring to Make

The v2 finalizer derives a versioned pre-render Concept v3 from the two exact authored inputs and packet bindings. The durable contract keeps a stable normalized view:

- provenance bound to Wish, assignment, Taste, blueprint, Invented contract, exact two authored files, round, and revision inputs;
- normalized physical `brief` projected losslessly from `source.concept`;
- normalized `research` with finalizer-derived excerpt and record identities;
- normalized ordered `drawing_instructions` projected from the visual plan;
- a path-only `descriptor` whose safe paths are derived from role ids;
- an exact routed-Wish binding and constraint identity derived from the host Wish plus normalized build-critical constraints;
- an author-source manifest, normalized-content identities, and `concept_sha256`.

The finalizer may persist canonical projection files for audit or compatibility, but they are explicitly finalizer-owned outputs and are never requested from the native session. The pre-render identity binds both exact authored bytes and all derived projections. Missing or ambiguous design content fails normalization; the finalizer never selects defaults.

The sealed Concept v3 retains the same high-level accessors required by Make: normalized brief, adaptive descriptor, image manifest, source identity, and whole Concept identity. Typed source and installed-finalizer readers accept v2 and v3 additively and expose a common normalized view. Host stage gates independently perform the same projection and identity checks rather than trusting finalizer prose.

**Alternative considered:** make Make read `invent-source.json` and `visual-plan.json` directly. Rejected because raw authoring layout would leak into every downstream gate and turn a local authoring simplification into a lifecycle-wide schema dependency.

### 5. Derive paths, hashes, routed-Wish preservation, and research identities

Descriptor paths follow a fixed safe mapping such as `images/<role-id>.png`; a collision or unsafe id is rejected. The finalizer computes canonical hashes for excerpts, sources, normalized content, manifests, routed-Wish bindings, and contracts. The native session never copies host Wish fields into a derived file or calculates a canonical hash.

The normalized routed-Wish binding copies product id, objective, context, and Wish identity from the packet and combines only the exact normalized build-critical constraint projection. The host can prove preservation without trusting agent copy work. Make receives normalized constraints through the sealed Concept, not an agent-authored `derived_wish.json`.

**Alternative considered:** keep `derived_wish.json` agent-authored because it is already validated. Rejected because copying host-owned bytes and calculating their identity adds only a mismatch surface; deterministic derivation preserves stronger provenance.

### 6. Keep host effects durable while making the role graph generic

Effect intents remain per role and bind checkpoint, subject, pre-render identity, role id and kind, exact instruction, exact normalized constraint block, ordered reference hashes, derived path, provider profile/model, and request format. The host walks the validated ordered roles rather than hardcoding four overall roles followed by components.

All existing authority, credential isolation, pre-transmission intent, ambiguity classification, authenticated reconciliation, safe retry, byte sniffing, atomic install, bounded receipts, and unknown-state behavior remain unchanged. Aggregate success requires exactly the declared role set. Changing roles, instructions, normalized constraints, references, or paths produces a different pre-render identity and effect identities.

**Alternative considered:** let the provider decide additional useful views. Rejected because it breaks exact role completeness, cost bounds, agent creative ownership, and idempotent effect identity.

### 7. Give Make a common normalized packet plus an adaptive role summary

For v3 Concepts, the Make packet continues to carry the full sealed Concept and effect artifacts, their identities, and `required_product_component_keys`. It additionally exposes a bounded derived `concept_visual_roles` summary containing each role id, kind, purpose, sealed path, and image hash so the Manager can find primary, signature, and need-driven images without learning the raw author schema.

The routed Make reference changes only its Concept handoff section:

- normalized brief and build-critical numerical constraints are authoritative;
- primary and signature images are the initial visual design references;
- optional adaptive roles are consulted for their named need only;
- absent fixed views are not blockers;
- every CAD part, exact product state, proof render, final render, and review remains freshly generated;
- Concept pixels and research remain non-evidentiary.

The Make finalizer and host gate parse v2 or v3 sealed Concepts through their common normalized view, independently rehash the whole tree and effect evidence, compare `product.json.components` against the direct packet key set, reject any product-tree hash equal to a Concept image hash, and bind the unchanged Made v2 identity to `concept_sha256` and `concept_effect_sha256`. No Made schema bump is needed because it already binds opaque Concept identities rather than raw source fields.

Make-to-Invent revision evidence likewise continues to bind those two identities. A new Invent round receives the prior consolidated source, visual plan, normalized sealed Concept, research, and feedback; it changes only justified content and receives new exact identities.

**Alternative considered:** remove Concept checks from Make because the simplified source is easier to validate. Rejected because authoring ergonomics do not reduce downstream tamper, drift, or evidence risk.

### 8. Preserve output-first recovery and prove real-agent usability before activation

The new deep profile keeps current budgets but changes Invent recovery to a two-input source handoff:

1. if both exact inputs exist, invoke the finalizer immediately;
2. otherwise author or repair the smallest missing contract-complete input, then invoke the finalizer;
3. do not reread the roster, repeat research, spawn new exploration, or polish before the first finalizer attempt.

Finalizer rejection is bounded, safe feedback for a focused source repair; it is not a host cognitive loop. The normal native turn still owns the repair.

Activation is withheld until deterministic Forge/Quest routes and opt-in authenticated Codex acceptance prove: discovery from materialized context, first-pass or bounded-recovery finalization, host-only adaptive effects after exit, same-session Make resume, no hidden schema overlay, and unchanged final product gates. Reports measure protocol usability without claiming concept or image quality.

**Alternative considered:** enable v2 after unit tests because normalization is deterministic. Rejected because the original problem is agent usability under a bounded native turn, which deterministic fixtures cannot prove.

## Risks / Trade-offs

- **[Risk] A richer consolidated source can become another oversized free-form blob.** → Publish a complete v2 skeleton, bounded fields, one filled nontrivial example, and a preflight that names semantic omissions without exposing host internals.
- **[Risk] Optional research can become an excuse for unsupported physical claims.** → Require provenance for externally grounded or build-critical constraints and fail when a necessary factual uncertainty remains unresolved; allow emptiness only for genuinely deliberate original decisions.
- **[Risk] Adaptive roles may omit a view Make later needs.** → Require primary and signature roles, require each interface and component relationship to be traceable in the normalized brief, and preserve Make-to-Invent revision for a genuinely build-blocking Concept omission.
- **[Risk] Deterministic request serialization could be mistaken for host prompt authorship.** → Bind and preserve the exact instruction and exact canonical constraint block separately in every intent and receipt; fixed labels add no semantic content.
- **[Risk] Supporting v2 and v3 sealed contracts duplicates readers.** → Centralize a pure normalized view in the trusted Concept package and mirror its narrow validation in the no-dependency finalizer with round-trip parity tests.
- **[Risk] Provider calls may still grow with complex products.** → Cap the frozen v2 plan at 20 roles/images, require every optional role to state unique value, expose role count before transmission, and reject an over-limit plan without letting the host drop declared roles.
- **[Risk] The new capability lands while `activate-invent-concept-boundary` is still in progress.** → Treat v1 activation as the compatibility baseline, implement v2 additively, and do not expose the v2 marker until the v1 branch contracts and tests are integrated.
- **[Trade-off] Durable normalized projections still contain some repeated data.** → Accept storage duplication at the trusted boundary because it removes native authorship burden and keeps downstream contracts self-contained.

## Migration Plan

1. Integrate and validate the active v1 Concept boundary as the frozen compatibility baseline; record its exact marker, finalizer, packet, contract, and Make bytes.
2. Add v2 failure-first schemas, normalized readers, packet selection, author-source preservation, and no-dependency finalizer parity while leaving the v2 marker unavailable to new runs.
3. Add adaptive role planning and effect execution behind the exact v2 marker; retain all v1 fixed-role code and fixtures.
4. Add common normalized Make readers, `concept_visual_roles`, v3 packet validation, unchanged Made bindings, component equality, pixel exclusion, and revision behavior.
5. Materialize the v2 reference and matching deep-profile recovery instructions only after source/package lock tests reproduce exact bytes.
6. Run unit, workflow, integration, packaging, deterministic route, wait/resume, ambiguity, archive/privacy, and compatibility tests.
7. Run opt-in authenticated Forge and Quest acceptance from clean private runs. Record first finalizer timing, bounded rejections, role execution, same-session Make resume, and all truthful limitations.
8. Expose the v2 marker only after the complete acceptance matrix passes. Rollback disables v2 selection for future runs while retaining all v2 readers and leaving existing v2 checkpoints resumable; it never downgrades a frozen run to v1.
