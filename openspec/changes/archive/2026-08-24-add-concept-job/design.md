## Context

See proposal.md — Why. This document records how the `panda-social-cc-agent` concept phase maps onto the Workshop's contracts, and where the two must deliberately diverge.

**What the Workshop gives us.** Jobs are plain callables (`Context -> Result`), wired through `WorkshopTools` and resolved per inventor (`workshop.py:797-804`). There is no base class and no registry beyond the `WORKSHOP_JOBS` tuple (`toys.py:22`). Contexts are frozen dataclasses validated by hand in `__post_init__`; there is no pydantic. Outputs that own files are sealed by a content-addressed `ArtifactManifest` and re-checked at every boundary (`Made.assert_current`, `jobs.py:215`). A job that lacks a real capability raises `WaitingFor(Need(...))` rather than fabricating evidence (`instructions.py:232-242`).

**What panda gives us.** Its concept phase is five self-gating stages called in fixed order from `job_runner.py:1012-1148`, carrying a single Mongo document field `concept_spec` whose `stage` key is the only flow control (`schemas.py:106-139`). The parts worth porting are the *shape of the design*, not the transport: lock the facts first, anchor one image, derive every other image from that anchor as an edit, and hand the build stage a brief in a shape it already parses plus the images as first-class inputs.

**Where the two diverge, and why it matters.** Panda's loop is interactive — it parks at `AWAITING_QUESTIONS` and `AWAITING_CONCEPT_SELECTION`, proposes three style directions, and waits for a human to pick one. `Workshop.run` is autonomous: it runs to delivered, waiting, or a bounded stop, and its only park mechanism is `WaitingFor`. There is no seat for a human to choose a style from. Three consequences follow, and they are the load-bearing adaptations in this design: the questionnaire becomes fact derivation from the Wish, the style choice becomes the inventor's `Taste`, and — because nobody is looking at the pictures to judge fit — the concept can be print-only from the first image instead of only at selection.

## Goals / Non-Goals

**Goals:**

- One concrete, visualized design per round that Make builds against, with the same anchoring guarantee panda relies on to keep views depicting one object.
- Per-component images, which panda does not have. Its per-image axis is `(style_set × view)`; components exist there only as text in the separate `image_spec.parts` field.
- The brief's numbers travel with every image, so the model that draws the design and the job that builds it are working from the same millimetres.
- Concept fits the Workshop's existing discipline: frozen records, content-addressed seals, truthful waiting, and no new persistence format.

**Non-Goals:**

- **No image provider ships.** This repo has no image model; every existing image is a deterministic STL render (`tools/build_showcase_products.py:728`), and no STL exists at Concept time. We ship the seam and wait.
- **No explore-and-select loop.** Three style directions parked for a human pick has no meaning in an autonomous run.
- **No pixel critic.** Panda has none either — its only "critic" is the two-pass feedback triage, and its image validation is purely structural (`concept_gen.py:413-445`). Adding an automated image-versus-geometry conformance check is a research problem, not a prerequisite for this change. The one exception is the exploded view's component-completeness count (D3a) — a single structural check on the one image the rest of the set depends on, not a judgement about whether any image is *good*.
- **No new persistence format.** The concept lives as files under the round workspace, sealed like every other Workshop artifact.

## Decisions

### D1 — Concept is a sixth job, not a stage inside Make

`WORKSHOP_JOBS` grows to six and Concept gets the same status as its siblings.

*Why.* A `Need` is validated against the job set (`jobs.py:79`), so an internal stage could not raise a truthful "I cannot draw" need — and truthful waiting is the whole reason Concept can ship before an image provider exists. A stage also could not appear as a run status or be named by `Feedback.invalidates`, which D4 depends on.

*Cost, accepted.* `ToyBlueprint` requires blueprint tasks to cover exactly the job set (`toys.py:310-311`), so every shipped blueprint must gain `concept` tasks or fail assembly. This is a hard break with no partial version — relaxing the coverage check to spare the migration was considered and rejected, because that check is what makes a blueprint an honest declaration of what an inventor actually does.

*Alternative rejected.* Concept as an internal step of `Workshop.run` before `make_job` — smallest diff, but gives up the need, the status, and the feedback routing.

### D2 — Concept runs per round, inside the existing loop

The round loop becomes `concept -> make -> playtest`, with feedback from round N reaching Concept in round N+1.

*Why.* Panda's v3 proposal identifies "the loop re-rolls when the user wants to steer" as its central defect (`docs/concept-phase-v3/proposal.md:9-31`): a rejection produced three brand-new directions rather than a correction of the one the user half-liked. Its fix is `refine` — anchor on the existing set and apply the feedback as edits. The Workshop already has exactly the loop that needs this: `Playtested` returns `Feedback`, which flows into the next round's context. Putting Concept inside that loop means a design flaw gets fixed in the design.

*Alternative rejected.* Concept once before the loop, frozen for all rounds. Cheaper, but every Playtest rejection would then be answerable only by changing the build — which is the mistake panda spent a version fixing.

### D3 — Consistency is anchor chaining. Not seeds, not one multi-image call, not a critic

`front` is generated first from text alone. `top`, `bottom`, and every component image are then generated **with the front image attached as the first reference**, and their prompt is phrased as an edit of it rather than as a fresh description of the object.

This is panda's mechanism verbatim (`phase_runner.py:2294-2302`, `concept_gen.py:288-297`):

> `"Reference image 1 is the FRONT VIEW of {obj}, already in the style: {style}. Depict the SAME object, unchanged, from a clear {angle} view. Preserve every shape, proportion, feature, material, and finish choice from the reference — only the camera angle changes."`

*Why.* Panda recorded the rationale when it rejected the obvious alternative (`docs/concept-phase-v2/phase-3.md:16-24`): generating all angles independently was rejected during design because *nothing would guarantee they depict the same object*. That reasoning holds here unchanged.

*Alternatives rejected.* A shared seed — panda passes no seed anywhere, and a seed pins sampling noise, not object identity. A single call returning a multi-view sheet — this is what panda's spec sheet does *at the end*, from three already-consistent references; asking for it up front gives every view the resolution of one panel and no anchor for the component views to chain from. An iterative critique loop — no general critic exists, and a self-verification generated alongside the thing it judges tends to rationalize it, which is exactly why panda split its feedback triage into two separate turns (`phase_runner.py:2425-2428`).

*Limit of this mechanism, addressed in D3a.* Chaining every image off `front` is sound for panda, whose derived views are whole-object views of the same silhouette. It breaks for per-component views, which panda does not have: a component occluded in the front view is not in the anchor, so "show it as it appears in reference image 1" asks the model to invent it — and it will.

Two shared blocks ride on **every** prompt in the set, anchor included:

- The design-facts block, panda's `_locked_design_cues` (`concept_gen.py:177-231`) — `Holds: …, each 150 x 150 x 50.5 mm` / `Clearance …` / `Approximate envelope …` / `Distinctive features …`, under the heading *"DESIGN FACTS (these are physical constraints — respect them exactly)"*. Its v3 fix is worth inheriting rather than re-discovering: the original dropped `fits.ref_mm` and `fits.clearance_mm`, so the model was told the name of the thing it had to hold and never its size.
- The presentation clause, `NEUTRAL_PRESENTATION` (`concept_gen.py:134-137`) — neutral flat design study, no dramatic lighting, no studio scene, no reflections, no background props.

### D3a — Occlusion: geometry is anchored in text, appearance in images, and an exploded view sits between them

A single front view cannot be the sole anchor for a component set, because it does not contain the information a component view needs. Three changes, together:

**1. Split what the anchor is doing.** The `front` image was carrying two jobs at once: *what this design looks like* and *what its geometry is*. Only the first survives occlusion. So:

- **Geometry comes from the brief.** `ConceptBrief.components[]` gains `form`, `dimensions_mm`, `placement`, and `interfaces` — enough to draw a part without seeing it. Text does not occlude, and the brief is complete by construction where any single view is not.
- **Appearance comes from the references.** Material, finish, palette, surface treatment, and form language are global properties of the object; they are legible in a view regardless of which parts that view hides. A component prompt inherits those from the references and takes its shape from the specification.

The rule that falls out: never instruct the model to reproduce a shape "as it appears in" a reference unless that shape is wholly visible in a reference supplied with that request.

**2. Accumulate references instead of always using `front`.** `top` and `bottom` see `front`; `exploded` sees all three. Each later image has strictly more of the object to be consistent with, at no extra cost.

**3. Add an exploded view, and generate it before the components.** One image showing every component separated along its assembly axes, none hidden behind another. It is the one image where every part is visible *by construction*, which makes it the right reference for the component views — a component image is then derived from a picture that actually shows the component.

Generation order becomes: `front` → `top`, `bottom` → `exploded` → each component. Four overall images plus N components; one call more than before.

*Why not the alternatives.* Referencing `front` plus `top` plus `bottom` for components — better than `front` alone, but three external views still show nothing of an internal part, so it narrows the failure without closing it. A per-component text spec with no exploded view — closes the hallucination but loses the visual tie, so the parts stop looking like they came from the same object. Rendering ground truth from geometry — the honest fix, and unavailable: no mesh exists until Make runs, which is the whole reason Concept exists.

*Residual limit, stated plainly.* Fully internal geometry — a hollow, a boss inside a shell — is visible in no external view and not reliably in an exploded one either. For that, the brief's specification is the only carrier, and the images are illustration. This is a limit of concept imagery, not something the design can engineer away.

**Verification, narrowly scoped.** Because every component image depends on it, the exploded view gets a completeness check before the component views are drawn: does it show as many distinct separated parts as the brief names? Fail → regenerate once with the missing components named → fail again → the concept fails. This is not the general pixel critic rejected in Non-Goals; it is one structural count on the single image the rest of the set hangs off.

### D4 — Per-component images extend the chain; the component list comes from the brief

Concept enumerates the design's components into `ConceptBrief.components`, then draws each one from its own specification, anchored on the exploded view for appearance (D3a): *"Reference image 1 is the exploded view of the complete object. Show only the `<component>`, alone, matching how it appears there. Its form is: … Its bounding dimensions are: … It meets: …"*

*Why here.* Panda has no equivalent and needs none — it hands its build stage a whole-object sheet. This repo's Make must produce printable parts, and `Made.product["components"]` already exists as the list Instructions publishes as "what arrives" (`instructions.py:298`, `:315`). Today that list is invented during Make. Deciding it in Concept means the parts are settled before geometry, and the same anchor that keeps `top` honest keeps the part views honest.

*Consequence.* The concept's component list becomes binding on Make — a product whose components contradict the brief is rejected. This is the one place we enforce adherence structurally rather than by prompt.

### D5 — Every concept image is print-only from the start

No concept image ever depicts the thing the design holds, mounts to, or rests on.

*Why we can, and panda cannot.* Panda deliberately keeps the fit target visible during explore rounds so the *user* can judge the fit relationship, then strips it at selection with a dedicated spec-sheet call (`docs/concept-phase-v3/proposal.md:196-253`). That extra image exists to close a real risk it names: the handoff tells the build stage the selected images are "the primary visual reference for the final shape" while nothing stopped those images from including the held object, so the build stage could be handed a picture of the part *plus* what it holds and told "build what you see."

No human judges fit in an autonomous run, so the reason for showing the target never arises — and with it, the whole class of bug disappears. Applying panda's print-only rule to every image from the first one removes the risk at its source and saves the extra generation call.

*Trade-off.* We lose a visual check that clearance reads correctly. The brief still carries `fits.ref_mm` and `fits.clearance_mm` as numbers into every prompt, and Playtest remains the place where fit is actually evidenced.

### D5a — Every image is labelled, in three places, none of them the pixels

An image set where the consumer cannot tell the top view from the bottom view is not much better than no set at all — and a model handed four unlabelled renders will guess, confidently. So the role travels three ways, and never as a caption:

1. **In the record.** `ConceptImages.overall` is keyed by role and `.components` by component key. This is the in-memory answer for a programmatic Make.
2. **On disk, in a sealed descriptor.** `concept.json` in the concept root carries the brief plus the role-to-path map, mirroring the in-root `product.json` that `ProductInstructions` already requires (`jobs.py:373-375`). Because it lives inside the sealed root, the brief and the role assignments are covered by the same manifest as the pixels — a concept cannot be silently relabelled without changing its `concept_sha256`. Filenames match roles too, which is what makes the directory legible to a human and to any transport where an agent opens files by path.
3. **In the handoff text.** Where Make is an agent receiving attachments, the prompt names each one by position: which image is the front, the top, the bottom, the explode, and which component each remaining image shows.

Point 3 is panda's mechanism directly. Its handoff prompt numbers the attachments — *"Image {sheet_n} is the print-only reference sheet — this is what to build. Images {n+1}-{n+3} are the selected front/side/top views and are secondary context"* (`concept_phase.py:714-725`) — and pairs that with the brief as a JSON fence. It has no captions in any image, and its build stage still knows exactly what it is looking at.

*Why not burn a caption into the image.* The tempting fix is the wrong one here. Concept images are fed back to the image model as references, with instructions to preserve what they show — so text inside a reference is text the next image can inherit, and a component view rendered from a captioned explode may come back carrying a fragment of the caption. Every concept prompt already bars text, dimensions, logos, and watermarks for exactly this reason (`concept_gen.py:273-297`); a role caption would be the one piece of text we deliberately added back. Compositing the label after generation avoids the garbling problem but not the contamination one, since the composited file is what gets passed as the reference.

### D6 — The provider is an injected callback; without it, Concept waits

`DefaultConcept(concept_artist=...)` mirrors `DefaultInstructions(media_maker=...)` (`instructions.py:199-223`) exactly: the callback writes images into the supplied workspace and returns relative paths by role; with no callback the job raises `WaitingFor(Need("concept", "concept-images", ...))`.

*Why.* It is the established seam for exactly this situation, it keeps provider choice central rather than per-inventor, and it lets this change land complete and honest in a repo with no image model. Panda's own backend is one HTTP call behind a similar boundary (`concept_gen.py:448-502`, OpenRouter `openai/gpt-image-2`, no seed, no temperature, `n=1`) — nothing about the design assumes that particular provider.

### D7 — The brief is a frozen record whose keys match what already flows downstream

`ConceptBrief` mirrors panda's `locked` shape — `object`, `category`, `fits`, `envelope_mm`, `wall_mm`, `features`, `print`, `assumptions` — plus `components`.

*Why that shape.* Panda chose it so its build stage needs no translation layer: `locked.*` is deliberately byte-compatible with the `design-brief` JSON the `shape-analysis` skill already emits (`schemas.py:112-116`). The same discipline applies here: the keys that continue downstream (`components`, and the feature and limitation vocabulary) should match what `Made.product` and the Instructions page already use, so nothing is renamed in flight.

*Divergence.* Panda's `locked` is filled by a questionnaire turn that asks the user up to four questions. There is no user to ask. Concept derives the facts from `Wish.objective`, `Wish.constraints`, the `Taste`, and the blueprint, and records every fact the Wish did not determine in `assumptions` — which is what panda's lock turn does for unanswered questions anyway.

### D8 — Taste supplies the style, so Concept never asks about aesthetics

Panda's questionnaire prompt is explicit that it must **never** ask about aesthetics, style, or form language, because a later step shows the user three real image directions (`concept_phase.py:492-572`). Here that later step does not exist, and the inventor's `Taste` is already the repo's answer to "whose aesthetic is this" — it gates routing (`manager.py:938-997`) and is re-asserted throughout a run (`workshop.py:1305`, `:1371`).

So the style descriptor in the anchor prompt comes from the Taste. Panda's constraint on descriptor content is worth keeping: no CAD verbs (fillet, chamfer, bevel, radius, draft angle) and no exact measurements in the style text — numbers belong in the design-facts block, where they are constraints rather than adjectives.

### D9 — Sealing and identity

The concept root is sealed with `build_artifact_manifest` into `concept_sha256`, and `ConceptImages.assert_current()` re-checks it at every boundary — when `MakeContext` is built, and again when Make returns, since generation may be remote and slow. This is the same treatment `Made` and `ProductInstructions` already get (`jobs.py:198`, `:377`).

`concept_sha256` joins the run record and the Instructions resume checkpoint, including its strict key-set checks (`workshop.py:557-608`, `:1145-1157`), so a resumed run cannot silently build against a different concept than the one it parked on.

### D10 — Adherence is enforced where it can be, advisory where it cannot

Three levels, honestly labelled:

1. **Structural, enforced.** The concept's bytes are frozen and re-checked; the round binding is checked; the product's component list must match the brief's.
2. **Numeric, enforced by precedence.** Where an image and the brief's millimetres disagree, the numbers govern. This ordering is stated in the contract so an inventor's Make has a rule rather than a judgement call.
3. **Visual, advisory.** Nothing verifies that returned geometry looks like the concept. Panda is in the same position and handles it by putting the obligation in the build-stage system prompt — *"judge the parts, assembly, and cross-sections against the approved plan … AND the chosen concept/reference images"* (`create_flow.py:285-295`). We do the same for agent-backed inventors, and rely on Playtest plus `Feedback` invalidating `concept` as the correction loop.

Claiming more than this would be the kind of untruth the rest of the codebase is built to prevent.

### D11 — Concept art directs the build and never evidences it

These are the same artifact in two roles, and the roles must not be confused: **an instruction is not evidence**. The concept says what should be built. A product image says what was built. D10 requires Make to follow the concept; this decision forbids the concept from standing in for a picture of the result. Nothing is in tension — the second rule exists *because* of the first.

That is worth stating plainly, because the better adherence gets, the more reasonable the substitution starts to look. If Make builds faithfully, the concept images resemble the product, and someone will ask why the product page cannot use them. The answer is that resemblance is the point of failure, not the justification: the whole purpose of a product image is to reveal a divergence between what was designed and what was actually made. A concept image cannot reveal that divergence, because it is one of the two things being compared. Allowing the substitution would hide the discrepancy at exactly the moment it matters.

**Type-level separation, which is not sufficient on its own.** `ConceptImages` is its own record with its own role vocabulary. It has no `hero`/`play`/`detail`/`parts`/`box` keys, so it cannot be passed where `DefaultInstructions` expects media, and `ProductInstructions` re-validates those five roles independently (`jobs.py:406-452`). Provenance is marked `concept_art: True`, the inverse of the STL renderer's `"concept_art": False` (`tools/build_showcase_products.py:806-819`).

**Byte-level separation, which is the part that actually closes it.** The type rule stops the record from being passed; it does nothing about copied pixels. Artifact roots already carry images — `inventors/alice/toys/five-job-checkers/artifact/images/hero.png` is a real path — so nothing structural stopped a Make from writing a concept image into its artifact tree and letting it flow onward into the product page. Two checks close that: the Workshop refuses a `Made` containing any file whose bytes match an image in that round's concept, and Instructions refuses a product image whose bytes match one. Both are exact `sha256` comparisons against the concept manifest, which we already compute for sealing.

Together these preserve the standing rule in `docs/ARCHITECTURE.md:354` and the warning already written into the Instructions need — *"do not substitute concept art for product proof"* (`instructions.py:239-240`) — as something enforced rather than merely stated.

### D12 — New module, not a bigger `workshop.py`

`DefaultConcept`, the prompt builders, and the provider seam go in `src/inventor_workshop/concept.py`. `workshop.py` is 1,559 lines; the records go in `jobs.py` beside their siblings and only the call-site hook goes in `workshop.py`. Panda made the same call for the same reason when `phase_runner.py` reached 2,458 lines (`docs/concept-phase-v3/proposal.md:314-316`).

## Risks / Trade-offs

**Refine drift — the main technical risk.** Each round re-renders from the previous round's image, so small reinterpretations compound. Panda names this as the principal risk in its refine design and mitigates two ways (`docs/concept-phase-v3/proposal.md:284-288`): cap the consecutive-refine depth, then re-anchor from the design's locked facts; and keep the *accumulated* edit list in the prompt rather than trusting the image alone to carry earlier corrections. → Adopt both. Proposed cap: 4 consecutive refines.

**Round backstop counts the wrong thing.** Panda's `CONCEPT_MAX_ROUNDS` guard trips on legitimate refine-heavy sessions when refines and explores share a counter (`docs/concept-phase-v3/proposal.md:289-291`). → Concept's refine depth is counted separately from the Workshop's `playtest_rounds`, which continues to bound the run.

**Nothing checks that the built thing looks like the concept.** → Stated as advisory in D10; Playtest is the loop that catches it. Do not describe this change as guaranteeing visual adherence.

**No provider means the whole pipeline parks.** Every existing showcase and test run would stop at `concept` the moment the job is added. → The fixture and showcase paths get a deterministic concept artist that writes small synthetic images from the brief, so `tests/` and `tools/build_showcase_products.py` keep running end-to-end. It is labelled as a fixture, never shipped as a real provider.

**Cost grows with component count.** Panda spends 9 calls per explore round; we spend `4 + N_components` per round — three overall views, the exploded view, and one per part — and a design with a dozen parts is expensive. → Cap the component count in the brief (proposed: 12) and fail the brief above it rather than silently truncating the image set.

**The exploded view becomes a single point of failure.** Every component image depends on it, so a bad explode corrupts the whole component set rather than one image. → The completeness check plus one regeneration (D3a) catches the common failure, missing parts. A merely *inaccurate* explode still propagates, which is why each component prompt also carries that component's own written specification rather than trusting the picture alone.

**Fully internal geometry is illustrated, not depicted.** No external or exploded view reliably shows a feature inside a shell. → The brief carries it; the images do not claim to. Do not describe a component image as evidence of internal geometry.

**The six-job break lands everywhere at once.** Blueprints, the stage machine, the CLI, the docs, and every "five jobs" string change together. → Migration plan below; there is no incremental path, so it goes in as one change with the tests updated alongside.

**A wrong fact in the brief propagates as ground truth.** Panda's triage defaults an ambiguous claim to style-only precisely because a wrong write to `locked` becomes what the build stage treats as truth (`docs/concept-phase-v3/proposal.md:301-304`). → Feedback that does not unambiguously name a physical fact revises presentation and form, not the numbers; ambiguous claims default to non-numeric.

## Migration Plan

1. Land the records and the job set together — `ConceptContext` / `ConceptBrief` / `ConceptImages` in `jobs.py`, `"concept"` in `WORKSHOP_JOBS`, concept entries in `TOY_TASKS` — so `ToyBlueprint` coverage never observes a broken intermediate state.
2. Add the `_advance` transition, the `WorkshopTools.concept` slot, and `_missing_concept`. At this point a run with no concept provider parks at `concept` with a truthful need; nothing silently degrades.
3. Add `concept_images` to `MakeContext` as an optional field. Existing call sites and inventor `make` hooks keep working untouched.
4. Add the fixture concept artist and repoint `tests/` and `tools/build_showcase_products.py` at it, restoring end-to-end runs.
5. Update the docs and the generated scaffold last, once the contract is settled.

**Rollback.** The field is optional and the job has a waiting fallback, so reverting is removing `"concept"` from `WORKSHOP_JOBS` and its blueprint tasks; sealed concepts from earlier runs become inert files that nothing reads.

## Open Questions

- The exact refine-depth cap (proposed 4) and component cap (proposed 12). Both are tunable constants that change no contract, no requirement, and no task.
- Whether a later inventor-supplied provider wants an aspect-ratio and resolution knob on the seam, as panda has (`CONCEPT_IMAGE_ASPECT`, `CONCEPT_IMAGE_RESOLUTION`). Deferrable until a real provider exists — the callback returns paths, so adding provider-side settings changes nothing on this side of the boundary.
