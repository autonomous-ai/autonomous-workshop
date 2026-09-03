## Context

See `proposal.md` for motivation. The current `invent-concept-v2` capability asks a bounded Forge/Quest Invent turn to author two inputs: a consolidated physical source and an adaptive `visual-plan.json`. The plan chooses 2 through 20 roles from `primary-form`, `signature-experience`, `assembly`, `alternate-view`, and `component`; the host later renders that graph and normalizes it into sealed Concept v3. Make sees the normalized brief and a generic role summary.

This change must retain the one-session architecture, keep Concept inside Invent, preserve host-only image credentials and durable effects, and leave frozen v1/v2 runs resumable. It also cannot make the deterministic host a visual judge or let Concept pixels become product evidence.

The sibling `panda-social-cc-agent` supplies useful prompt precedents rather than a contract to copy wholesale. Its `concept_view_prompt` establishes a front anchor, phrases later views as the same object with only the camera changed, carries locked design facts, requests one complete object, and excludes text, logos, people, props, scenes, reflections, and dramatic lighting. Its print-only spec-sheet prompt removes held or mounted objects and asks for consistent construction detail. Workshop extends those ideas to bottom, exploded, and isolated-component roles because its Make phase reconstructs a component-complete CAD project rather than consuming only a style sheet.

## Goals / Non-Goals

**Goals:**

- Make the Concept image inventory a deterministic consequence of stable components.
- Give Make predictable direct, assembly, and isolated-part references with minimal visual clutter.
- Reduce Invent's second authored input from role planning to bounded depiction notes.
- Preserve exact creative ownership: Invent decides the product, components, appearance, and what each required view must expose; the host supplies only frozen camera and presentation protocol.
- Preserve durable effect safety, exact sealing, normalized Make bindings, and frozen compatibility.

**Non-Goals:**

- Adding a signature-experience Concept image beyond the fixed set. The signature remains in the normalized concept and is proved by fresh CAD states/renders and blind review in Make.
- Proving by deterministic inspection that returned pixels are visually correct, mutually consistent, or reconstructable.
- Generating CAD, dimensions, annotations, blueprints, meshes, or product evidence during Invent.
- Adding a Concept stage, a provider-driven view choice, a host model critic, a Python prompt chain, or additional native turns.
- Migrating an existing v1 or v2 run to the new role contract.

## Decisions

### 1. Freeze `invent-concept-v3` and Concept v4 additively

New marked Forge and Quest runs freeze an immutable `invent-concept-v3.md` capability and matching finalizer protocol. The runtime profile receives a matching additive revision with the current Invent reasoning, compaction, timeout, and source-handoff economics unchanged. Existing `invent-concept-v1` and `invent-concept-v2` references, schemas, finalizer interfaces, readers, and effect planners remain packaged and selected from the checkpoint-bound marker.

The new finalizer still receives exactly two authored inputs:

```text
invent --source <invent-source.json> --visual-instructions <packet path>
```

Using a new flag prevents a v2 adaptive plan from being silently reinterpreted as fixed-view input. The finalizer derives pre-render Concept v4, while the host independently repeats validation and normalization.

**Alternative considered:** mutate visual-plan schema v2 in place. Rejected because frozen adaptive runs bind those exact bytes and because one filename/flag accepting two incompatible meanings creates an unsafe resume surface.

### 2. Replace role planning with a fixed-key depiction document

The second authored input is a strict object:

```json
{
  "schema_version": 3,
  "kind": "autonomous-workshop.fixed-concept-view-instructions",
  "appearance": "Matte warm-white body with a muted blue moving core and crisp part boundaries.",
  "views": {
    "front": "Make the defining front silhouette and opening fully visible.",
    "top": "Expose the top opening and wall relationship without changing the object.",
    "bottom": "Expose the flat print stance and underside retention features.",
    "exploded": "Separate shell, core, and cap along their assembly axes; show every mating surface."
  },
  "components": {
    "shell": "Show the complete shell alone with the inner capture ledge visible.",
    "core": "Show the complete moving core alone with both axle interfaces visible.",
    "cap": "Show the complete cap alone with its keyed insertion feature visible."
  }
}
```

`views` has exactly four keys. `components` has exactly the stable source component key set; JSON object member order is not semantic. The host always derives component roles in normalized source-array order. Each value is a bounded nonempty depiction note, not a full provider prompt or a role proposal. `appearance` is the one agent-owned visual-language carrier shared by every image. The source remains authoritative for forms, measurements, placements, interfaces, assembly relationships, and signature contribution, so those facts are not copied into the instruction document.

The finalizer derives role ids and canonical paths:

```text
front                     -> images/front.png
top                       -> images/top.png
bottom                    -> images/bottom.png
exploded                  -> images/exploded.png
component:<stable-key>    -> images/components/<stable-key>.png
```

The existing total limit remains 20, so a fixed-view Concept can declare at most 16 stable components. The finalizer rejects a larger source before effect planning and names the count conflict.

**Alternative considered:** keep the adaptive array but validate that it happens to contain fixed ids. Rejected because the agent would still spend effort authoring known kinds, purposes, references, subjects, and order, and array structure would continue to imply that role selection is creative work.

**Alternative considered:** derive all prompts from the physical source and remove the second input. Rejected because material, finish, palette, intended visible emphasis, and the most useful way to expose an interface remain creative decisions that should not be invented by Python.

### 3. Compile prompts from agent facts plus one frozen protocol

Concept v4 derives one drawing instruction per fixed role by combining four separately identity-bound blocks:

1. the exact agent-owned `appearance` string;
2. the exact agent-owned note for the role;
3. the role-relevant normalized physical facts from `invent-source.json`; and
4. a versioned protocol-owned camera/presentation block.

The protocol does not choose form or add product features. It standardizes how already-authored design information is presented, analogous to a serializer with fixed field labels. Its common block requires:

- exactly one complete product or component, except that exploded contains the one complete separated component set;
- direct orthographic-like view, centered subject, constant orientation, useful scale, and edges/silhouette fully in frame;
- a pure white or very light neutral background with flat neutral lighting and restrained matte materials;
- no perspective drama, wide-angle distortion, depth of field, reflections, cast-shadow staging, scene, text, dimension annotation, arrows, labels, logos, watermarks, people, hands, fit targets, held objects, mounted objects, or unrelated props.

Role blocks add only fixed semantics:

- `front`: face the declared front directly and establish the appearance anchor from text and any authorized user subject/style references.
- `top`: show the same unchanged object directly from above; use front as the appearance reference.
- `bottom`: show the same unchanged object directly from below; use front as the appearance reference and keep the declared underside/print stance legible.
- `exploded`: use front, top, and bottom in that order; separate every named stable component along understandable assembly axes without hiding or redesigning parts.
- `component:<key>`: use exploded as the appearance reference; show only that complete part and include its normalized form, measurements, placement, interfaces, and assembly relationship.

The exact frozen prompt protocol and normalized fact blocks are included separately in the pre-render, effect-intent, and receipt identities. A protocol revision therefore requires a new capability version and cannot reuse old provider results.

**Alternative considered:** ask Invent to repeat the full common prompt in every role. Rejected because repetition consumes the bounded turn, invites drift, and makes clauses such as “no text” impossible to evolve or verify as one frozen protocol.

### 4. Use one fixed acyclic reference chain

The host executes roles serially where dependencies require it:

```text
front
  +--> top -----+
  +--> bottom --+--> exploded --> component:1 ... component:N
```

Top and bottom may run in parallel after front. Component effects may run in parallel after exploded, subject to the existing effect coordinator's bounded concurrency. The declared ordered references remain exact even when independent siblings execute concurrently.

This extends panda's “same object, different camera” anchoring while addressing occlusion. External views cannot reveal an internal part, so component roles anchor appearance to exploded and geometry to the text brief. The exploded image itself receives all three overall views and every component's textual facts.

There is no general pixel critic. The host can prove only that the prompt names every component and that every role returned one valid byte sequence. If the provider omits or distorts a part despite that prompt, Make treats text as authority and may use the existing Concept-defect revision boundary only when exact evidence shows the Concept prevents a conforming build.

**Alternative considered:** derive all component images from front alone. Rejected because hidden components are absent from the anchor, turning “same part” into an invitation to hallucinate.

### 5. Normalize and seal Concept v4 behind the common Make view

Pre-render and sealed Concept v4 retain the v3 high-level boundary: exact authored input identities, normalized brief and research, drawing instructions, descriptor, routed Wish, image manifest, Concept identity, and sealed effect identity. The version changes because the second authored-input schema and role semantics change materially.

The common normalized reader accepts sealed Concept v2, v3, and v4. For v4, `visual_roles` is always the fixed ordered set and exposes `id`, explicit fixed `kind`, purpose derived from the role contract, path, and image hash. Make additionally receives a direct `component_visuals` map from each stable key to its isolated image record. That map is a deterministic convenience projection, not a new source of truth.

The Make guidance starts reconstruction with front/top/bottom for overall envelope and silhouette, exploded for assembly order and part boundaries, and each component image for isolated form and interfaces. It explicitly resolves conflicts in favor of normalized numerical facts. Every product file, CAD state, render, signature sheet, review, and final verification remains freshly generated.

**Alternative considered:** teach Make to infer the fixed mapping from filenames. Rejected because exact role meaning belongs in the packet contract, not in path conventions or model guesses.

### 6. Preserve signature quality in Make rather than adding a sixth role family

Removing the adaptive `signature-experience` Concept image does not remove the concept's `signature_interaction`, `anti_generic_signature`, interaction trace, or Make proof target. Those remain in the consolidated source and normalized brief. Make still must construct exact states, render the canonical signature sheet, and pass the blind review of form, subjects, action, relationship, anti-generic signature, desirability, and overall experience before integrated verification.

The fixed Concept views are construction references. The signature sheet is evidence rendered from actual CAD. Keeping those responsibilities separate avoids paying for a Concept image that cannot prove product behavior and honors the user's exact fixed inventory.

**Alternative considered:** silently retain `signature-experience` in addition to the requested roles. Rejected because it violates the exact-set requirement and conflates concept direction with verified product outcome.

### 7. Keep revision, recovery, and activation bounded

Invent recovery follows the current source-handoff rule: if source and fixed-view instructions exist, finalize immediately; otherwise repair only the smallest missing/rejected input, then finalize. It does not reopen role selection. An Invent revision receives the prior source, prior fixed instruction document, sealed Concept/effect identities, and exact feedback; stable component changes deterministically change the required component-image set and all downstream identities.

Activation remains gated behind unit, workflow, integration, packaging, deterministic route, wait/resume, compatibility, and opt-in authenticated Codex acceptance. Rollback disables the marker for future runs but retains v4 readers and never rewrites a frozen checkpoint.

## Risks / Trade-offs

- **[Risk] Direct image-generation models may still produce perspective or inconsistent geometry.** → Use one frozen minimal presentation protocol, cumulative appearance references, normalized facts in every request, and preserve text as authority; do not overclaim structural validation as visual proof.
- **[Risk] Four overall images are redundant for a simple one-piece concept.** → Accept deterministic provider cost because predictable CAD reconstruction is the requested priority; retain the 20-image ceiling and expose the exact count before transmission.
- **[Risk] A 16-component cap may reject legitimate complex concepts.** → Fail during Invent before effects with the exact count; the native agent may consolidate product-level component keys only when that remains truthful, otherwise the run needs a future higher-cap capability rather than an implicit truncation.
- **[Risk] Protocol-owned prompt text could drift into host creative authorship.** → Limit it to fixed camera, layout, and exclusion rules; identity-bind it separately; keep appearance, form, features, component decomposition, and emphasis agent-owned.
- **[Risk] Exploded output may omit a named part even when the request is complete.** → State the limitation, use the brief as the component authority, and do not add a host vision judge. A future semantic review would require its own architecture decision.
- **[Trade-off] Concept v4 adds another readable contract version.** → Centralize all downstream access through the existing normalized reader and retain version-specific parsing only at the Concept boundary.

## Migration Plan

1. Record v1 fixed-role and v2 adaptive schemas, materialized references, finalizer interfaces, prompt/effect identities, and resume fixtures as immutable compatibility baselines.
2. Add failure-first tests for fixed instruction keys, source-order component derivation, the 16-component boundary, canonical paths, reference graph, and cross-version rejection.
3. Implement Concept v4 types, pure normalization, common-reader support, and no-dependency finalizer parity behind an unavailable marker.
4. Add fixed prompt compilation and effect planning while reusing the current authorization, credential isolation, intent, reconciliation, byte validation, atomic install, and sealing machinery.
5. Add the Make fixed-role and component maps, routed reconstruction guidance, exact rehashing, component equality, and Concept-pixel exclusion without modifying CAD or signature gates.
6. Materialize `invent-concept-v3.md`, the matching finalizer and runtime-profile reference, package locks, and bounded recovery wording.
7. Run focused unit/integration suites, full deterministic Forge/Quest routes, wait/resume and revision cases, packaging checks, all frozen compatibility suites, strict OpenSpec validation, and `git diff --check`.
8. Run opt-in authenticated Forge and Quest acceptance from clean private workspaces. Enable the marker for new runs only after exact two-input authoring, fixed-role rendering, same-session Make resume, and unchanged final gates pass. Rollback disables only future selection.
