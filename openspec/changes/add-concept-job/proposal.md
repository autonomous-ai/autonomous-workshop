## Why

Make is handed a `MakeContext` that is entirely abstract — a `Wish.objective` in prose, a `Taste`, and a `ToyBlueprint` — and is asked to produce printable geometry in one leap. Nothing between Wish and Make commits to *what the thing actually looks like*, so every Make round reinterprets the brief from scratch, and a Playtest rejection cannot distinguish "the design was wrong" from "the build drifted from the design".

The `panda-social-cc-agent` pipeline solved the same problem with a concept phase that locks the design facts, then anchors a set of mutually consistent images the CAD build treats as ground truth (`docs/concept-phase-v3/proposal.md`). This change ports that design into the Workshop's job contracts: a **Concept** job between Wish and Make that turns the abstract `MakeContext` into one concrete, visualized design, and hands Make images it must follow.

## What Changes

- **New `concept` job**, sixth in `WORKSHOP_JOBS`, ordered between `wish` and `make`. Signature follows the existing job protocol: `ConceptJob = Callable[[ConceptContext], ConceptImages]`.
- **Design facts are locked before any image is drawn.** Concept derives a `ConceptBrief` from the Wish, Taste, and blueprint — `object`, `category`, `envelope_mm`, `wall_mm`, `fits`, `features`, `print`, `components`, `assumptions` — and every image prompt carries those facts verbatim as a physical-constraint block. This mirrors panda's `locked` shape (`app/utils/jobs/schemas.py:118-139`), which deliberately matches the `design-brief` its CAD stage consumes so no translation layer is needed.
- **A consistent image set, produced by anchoring, not by re-describing.** `front` is generated first, then `top` and `bottom` as edits of it — "the same object, unchanged, only the camera angle changes" — which is how panda keeps its views from reinterpreting the object (`app/utils/jobs/concept_gen.py:241-297`).
- **Geometry is anchored in text, appearance in images.** Panda anchors everything on the front view, which is safe for its whole-object views but not for ours: a component hidden behind another is not in the front view at all, so asking for it "as it appears in the reference" is an instruction to invent. So the brief specifies each component's form, dimensions, placement, and interfaces — text cannot occlude — and the image references supply only material, finish, palette, and form language, which are global to the object and visible in any view.
- **An exploded view, generated before the component views.** One image showing every component separated and wholly visible, produced from `front`/`top`/`bottom` and then used as the reference for each component image. It is checked for component completeness before any component is drawn, so no component image is ever derived from a view that does not show it.
- **Per-component images.** Concept enumerates the design's components into the brief and draws each one in isolation. This extends panda's view set — its per-image axis is `(style set × view)` and components exist there only as text — and the enumeration also becomes the upstream source for the `components` list that Instructions already publishes (`instructions.py:298`).
- **`MakeContext` gains a `concept_images` field** carrying the sealed concept — the brief, the image paths by role, and the content-addressed `concept_sha256`. It is optional and defaults to empty, so existing `MakeContext` call sites keep working.
- **Every image says what it is, outside its own pixels.** The role travels in the record, in a sealed in-root `concept.json` descriptor whose filenames match the roles, and in the handoff text that names each attachment by position. No role is captioned into an image, because concept images are fed back to the image model as references and text inside a reference is text the next image can inherit.
- **Make must build to the concept.** When `concept_images` is present it is the primary reference for form, proportion, and part breakdown; the Wish objective remains the statement of intent, and the brief's numbers remain the physical constraints.
- **Concept waits truthfully when it cannot draw.** With no image provider configured the job raises `WaitingFor(Need("concept", "concept-images", ...))` rather than inventing a design, matching how `DefaultInstructions` handles a missing `media_maker` (`instructions.py:232-242`).
- **Concept art directs the build but never evidences it.** An instruction is not evidence: the concept says what should be built, a product image says what was built. `ConceptImages` is a structurally distinct record that can never satisfy the Instructions media roles, and — because a faithful build makes the substitution tempting — the concept's *bytes* are barred from the product artifact and the product page too. This preserves the rule in `docs/ARCHITECTURE.md:354` and the warning in `instructions.py:239-240` as something enforced rather than stated.
- **BREAKING**: `WORKSHOP_JOBS` grows from five to six entries. `ToyBlueprint` requires blueprint tasks to cover exactly that set (`toys.py:310-311`), so every shipped blueprint gains `concept` tasks. The `_advance` stage machine (`workshop.py:915-944`), `Need.job`, `Feedback.invalidates`, `WorkshopRun.job`, the CLI, and the "five jobs" wording throughout the docs all change with it.

## Capabilities

### New Capabilities
- `workshop/concept-job`: The Concept job itself — its position between Wish and Make, its `ConceptContext` input, its `ConceptImages` output, its per-round refine behavior when Playtest feedback arrives, and its truthful waiting when no image capability exists.
- `workshop/concept-images`: The concept image set contract — the locked design brief, the required overall views (`front`, `top`, `bottom`), the per-component views, the anchoring rule that makes them depict one same design, path and format validation, content-addressed sealing, and the prohibition on using concept art as product proof.
- `workshop/make-concept-adherence`: How Make receives `concept_images` on `MakeContext` and what it means to follow it — which parts of the concept are binding, what the Workshop verifies at the boundary, and how a Playtest rejection revises the concept rather than only the build.

### Modified Capabilities
<!-- openspec/specs/ is currently empty; this change introduces the first capabilities.
     The five existing jobs have no spec files to delta against, so their behavior
     changes (job registry growth, stage machine, blueprint coverage) are captured as
     Impact below and as requirements inside the new capabilities above. -->

## Impact

**Contracts** — `src/inventor_workshop/jobs.py`: new `ConceptContext`, `ConceptBrief`, `ConceptImages` frozen dataclasses; `MakeContext` gains `concept_images`. `src/inventor_workshop/toys.py:22`: `WORKSHOP_JOBS` gains `"concept"`; `TOY_TASKS` gains concept tasks so `ToyBlueprint` coverage (`toys.py:310`) still holds.

**Orchestration** — `src/inventor_workshop/workshop.py`: new `ConceptJob` type alias next to `MakeJob` (`:60`), a `concept` slot on `WorkshopTools` (`:704`) with a `_missing_concept` truthful fallback beside `_missing_make` (`:723`), the concept call inside the round loop before `MakeContext` is built (`:1341-1354`), a `"concept"` entry in the `_advance` legal-transition table (`:915-944`), and `concept_sha256` in the Instructions resume checkpoint plus its strict key-set checks (`:557-608`, `:1145-1157`).

**New module** — `src/inventor_workshop/concept.py`: `DefaultConcept`, the prompt builders (design-facts block, neutral-presentation clause, anchor and chained-edit prompts), and the `concept_artist` provider seam. Kept out of `workshop.py`, which is already 1,559 lines.

**Downstream consumers of `MakeContext`** — `tools/build_showcase_products.py:1212`, `scaffold.py:86` (generated inventor hook), `inventors/bob/profile.py`, `inventors/leo/profile.py`, and the test fixtures in `tests/test_toy_workshop.py:52` and `tests/test_inventor_profiles.py:27`. All keep working unchanged because the field is optional.

**Docs** — the pipeline line in `README.md:112-117` and `:176-186`, `docs/ARCHITECTURE.md:51-61`, `:221-247` (job contracts diagram), `:207-211` (customization table), `:388-402` (module map), plus `docs/BUILD_AN_INVENTOR.md:302-336`, `docs/ADOPTION.md`, and `docs/MIGRATION.md`.

**Not in scope** — no image provider is shipped. This repo has no image model at all; every existing image is a deterministic STL render (`tools/build_showcase_products.py:728`), and an STL does not exist yet at Concept time. Concept therefore ships with the provider seam and waits truthfully until an inventor supplies one. Panda's interactive explore-and-select loop (three style directions parked for a human pick) is also out of scope: `Workshop.run` is autonomous and has no user park points, so the inventor's `Taste` selects the style instead.
