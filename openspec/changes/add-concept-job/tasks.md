## 1. Records and the job set

- [ ] 1.1 Add `ConceptBrief` to `src/inventor_workshop/jobs.py` as a frozen dataclass validated in `__post_init__`: `object`, `category`, `envelope_mm` (3 positive floats), `wall_mm` (positive float), `features`, `print` (`orientation`, `supports`), `components` (1..12 entries), `fits` (`target`, `ref_mm`, `clearance_mm`) or `None`, and `assumptions`. Give it `to_dict()` returning canonical JSON, matching the `to_dict()` convention of its siblings.
- [ ] 1.1a Add `ConceptComponent` as its own frozen record, required by every `components` entry: unique `key`, `name`, `purpose`, plus the geometry a component image is drawn from without seeing it — `form`, `dimensions_mm` (3 positive floats), `placement`, and `interfaces` (design.md D3a). Reject a component missing any of the geometry fields.
- [ ] 1.2 Add `ConceptImages` to `jobs.py`: `root`, `manifest`, `brief`, `overall` (`front`/`top`/`bottom`/`exploded` relative paths), `components` (path per brief component key), `round`. Validate every path with the same rules `_safe_relative_file` applies in `instructions.py:149-169` — relative, no parent traversal, resolves inside root, permitted image suffix — and require all paths distinct. Expose `concept_sha256` and `assert_current()`.
- [ ] 1.2a Require an in-root `concept.json` descriptor carrying the brief and a role-to-path entry for every image, validated the way `ProductInstructions` validates its in-root `product.json` (`jobs.py:373-405`): must exist, must be valid UTF-8 JSON, and must agree exactly with the record's roles and paths. Reject a descriptor naming a missing file or omitting an image present in the set.
- [ ] 1.2b Enforce the filename convention: each overall image's filename identifies its role, each component image's filename identifies its component key.
- [ ] 1.3 Reject in `ConceptImages` any component image whose key is absent from the brief, any brief component with no image, a symlinked root or image, and a root whose bytes no longer match the manifest.
- [ ] 1.4 Add `ConceptImages.from_root()` classmethod building the manifest with `build_artifact_manifest(root, created_at="content-addressed")`, mirroring `Made.from_root` (`jobs.py:202-209`).
- [ ] 1.5 Add `ConceptContext` to `jobs.py`: `wish`, `taste`, `blueprint`, `round`, `workspace`, `feedback`, `playtest_rounds`, `previous` (prior `ConceptImages` or `None`), `refine_depth`. Reuse `MakeContext`'s validation rules for workspace absoluteness, round bounds, and `Feedback` typing.
- [ ] 1.6 Add `"concept"` to `WORKSHOP_JOBS` in `toys.py:22` between `"wish"` and `"make"`, and update the module docstring and the `ToyTask.job` error message that both currently enumerate five jobs.
- [ ] 1.7 Add concept entries to `TOY_TASKS` in `toys.py` so `ToyBlueprint` job coverage (`toys.py:310-311`) holds for every lane, with `capability` values the truthful-need path can name.
- [ ] 1.8 Export the new records from `src/inventor_workshop/__init__.py` and add them to `jobs.py`'s `__all__`.
- [ ] 1.9 Add unit tests for each record's validation rules in `tests/test_jobs_instructions_deliver.py` (or a sibling `tests/test_concept_records.py`), covering every rejection in 1.1-1.5.

## 2. The Concept job

- [ ] 2.1 Create `src/inventor_workshop/concept.py` with `DefaultConcept(concept_artist=None)`, mirroring `DefaultInstructions`' constructor shape (`instructions.py:217-223`).
- [ ] 2.2 Implement the design-facts block builder: render the brief's `fits.target` with count and `ref_mm`, `fits.clearance_mm`, `envelope_mm`, `wall_mm`, and `features` under the heading `DESIGN FACTS (these are physical constraints — respect them exactly)`. Return `""` for an absent brief so callers can concatenate unconditionally.
- [ ] 2.3 Add the shared presentation clause constant: neutral flat design-study presentation, no dramatic lighting, no studio scene, no reflections, no background props.
- [ ] 2.4 Implement the anchor (`front`) prompt: the object, the Taste-derived style descriptor, "exactly one complete object", silhouette/proportions/construction legible for a later CAD build, no text/dimensions/logos/watermarks/people/hands/props, plus the design-facts block and the presentation clause. Exclude anything the design holds, mounts to, or rests on (design.md D5).
- [ ] 2.5 Implement the `top` and `bottom` prompts as edits of the anchor: reference image 1 is the front view of the same object, depict it unchanged from the named angle, preserve every shape/proportion/feature/material/finish, only the camera angle changes. Append the same two shared blocks.
- [ ] 2.5a Implement the `exploded` prompt, generated with `front`/`top`/`bottom` as references: the same object with every component separated along its assembly axes, each one wholly visible, none hidden behind, inside, or overlapping another. Name every component from the brief explicitly. Append the same two shared blocks.
- [ ] 2.6 Implement the per-component prompt (design.md D3a): reference image 1 is the exploded view, show only the named component alone as it appears there, and carry that component's own `form`, `dimensions_mm`, `placement`, and `interfaces` as the source of its shape. The prompt must inherit material, finish, palette, and form language from the references, and must not instruct the model to read the component's shape off a view that does not show it. Append the same two shared blocks.
- [ ] 2.7 Implement brief derivation from `Wish.objective`, `Wish.constraints`, `Taste`, and `ToyBlueprint`, including each component's geometry fields, and record every fact the Wish did not determine in `assumptions`. Keep CAD verbs and exact measurements out of the style descriptor (design.md D8).
- [ ] 2.8 Implement generation order in `DefaultConcept.__call__`: fresh-and-empty workspace check, brief first, then `front`, then `top`/`bottom` referencing `front`, then `exploded` referencing all three, then each component referencing `exploded` and `front`. Fail the whole concept if any image a later request depends on cannot be produced.
- [ ] 2.8a Implement the exploded-view completeness check before any component image is generated: confirm the exploded view accounts for as many distinct separated parts as the brief names; on shortfall regenerate once with the missing components named explicitly, then fail rather than drawing components from an incomplete explode.
- [ ] 2.9 Raise `WaitingFor(Need("concept", "concept-images", ...))` when `concept_artist` is `None`, with reason and instructions naming the missing capability, following `instructions.py:232-242`.
- [ ] 2.10 Fail rather than return a partial concept when the provider omits a required image; validate the returned path mapping the way `DefaultInstructions` validates `raw_media` (`instructions.py:269-278`).
- [ ] 2.11 Implement refine: when the context carries feedback and a previous concept, anchor on the previous round's `front`, carry the accumulated edit list in the prompt, and re-anchor from the brief's facts once `refine_depth` reaches the cap (4).
- [ ] 2.12 Mark concept image provenance `concept_art: True`, the inverse of the STL renderer's record (`tools/build_showcase_products.py:806-819`).
- [ ] 2.12a Write the `concept.json` descriptor into the concept root before sealing, so the brief and the role assignments are covered by the same manifest as the pixels (design.md D5a).
- [ ] 2.13 Seal the concept root and return `ConceptImages.from_root(...)`; re-check the context after generation, since a remote provider may be slow.
- [ ] 2.13a Add a concept-handoff text builder that names each attached image by position and role — front, top, bottom, exploded, then one per component key — and states their standing relative to each other, following `concept_phase.py:706-735`. Include the brief as structured JSON alongside it.
- [ ] 2.14 Add tests asserting the consistency contract directly: `front` is generated with no image reference; `top`/`bottom` reference `front` and are phrased as edits; `exploded` references all three overall views; every component prompt references `exploded`; the design-facts block and presentation clause appear in every prompt including the anchor. These mirror `tests/test_concept_gen.py:322` and `:371` in the source repo.
- [ ] 2.14a Add a test that no component prompt instructs the model to reproduce the component's shape from a reference in which it is not wholly visible, and that every component prompt carries that component's own `form`, `dimensions_mm`, `placement`, and `interfaces`.
- [ ] 2.15 Add tests for the waiting path, the partial-provider failure, refine anchoring, and the refine-depth re-anchor.
- [ ] 2.15a Add tests for the exploded-view completeness check: a complete explode proceeds, an incomplete one regenerates once, and a still-incomplete one fails the concept without producing component images.
- [ ] 2.15b Add tests for labelling: the descriptor round-trips every role, a descriptor disagreeing with the files is rejected, relabelling a sealed concept changes its hash, the handoff text names every attachment supplied and no others, and no prompt requests a caption in the pixels.

## 3. Workshop orchestration

- [ ] 3.1 Add `ConceptJob = Callable[[ConceptContext], ConceptImages]` beside `MakeJob` in `workshop.py:60`.
- [ ] 3.2 Add a `concept` field to `WorkshopTools` (`workshop.py:704-720`) and resolve it in the `Workshop` constructor beside `make_job` (`:797-804`).
- [ ] 3.3 Add `_missing_concept` beside `_missing_make` (`workshop.py:723-732`), raising a truthful `WaitingFor` for job `concept`.
- [ ] 3.4 Add `"concept"` to the `_advance` legal-transition table (`workshop.py:915-944`): `wish -> concept`, `concept -> (concept, make)`.
- [ ] 3.5 Call the concept job at the top of each round in `Workshop.run` (`workshop.py:1341`), before `MakeContext` is constructed, with its own `round_root / "concept"` workspace. Catch `WaitingFor` and park via `self._wait(...)` with job `"concept"`.
- [ ] 3.6 Verify the returned concept: it must be a `ConceptImages`, its root must sit inside the concept workspace (`_inside`, as `workshop.py:1367` does for `Made`), and its round must match.
- [ ] 3.7 Advance the run to `make` with the concept hash recorded, then pass the concept into `MakeContext`.
- [ ] 3.8 Re-check `concept.assert_current()` when Make returns, and reject a `Made` whose `product["components"]` does not match the brief's component keys.
- [ ] 3.8a Reject a `Made` whose artifact tree contains any file whose sha256 matches an image in that round's concept manifest, so concept pixels cannot ride into the product (design.md D11).
- [ ] 3.8b Add the same byte-level check to the Instructions media path: refuse a product image whose sha256 matches an image in the concept the product was built from.
- [ ] 3.9 Record `concept_sha256` on the run and in `WorkshopRun.to_dict()`.
- [ ] 3.10 Add `concept_sha256` to the Instructions resume checkpoint payload (`workshop.py:557-608`) and to both strict key-set checks (`:1122`, `:1145-1157`), so a resume cannot restore a different concept.
- [ ] 3.11 Add `concept_images` to `MakeContext` as an optional field defaulting to absent, validating that a supplied concept is current and belongs to the same round.
- [ ] 3.12 Add `"concept"` to the default `Feedback.invalidates` handling so Playtest feedback can invalidate the design as well as the build.

## 4. Fixture provider and existing consumers

- [ ] 4.1 Write a deterministic fixture concept artist that renders small synthetic images from the brief, clearly labelled as a fixture and not shipped as a real provider (design.md, Risks).
- [ ] 4.2 Wire the fixture into `tests/test_toy_workshop.py`'s `WorkshopTools` so the existing end-to-end runs reach Deliver again.
- [ ] 4.3 Wire it into `tools/build_showcase_products.py` and confirm the five checked-in showcase bundles still build.
- [ ] 4.4 Confirm `inventors/bob/profile.py`, `inventors/leo/profile.py`, and `tests/test_inventor_profiles.py:27` still pass with `concept_images` absent from their `MakeContext` construction.
- [ ] 4.5 Add concept tasks to every shipped blueprint that names its own tasks, so `ToyBlueprint` assembly succeeds.
- [ ] 4.6 Update `scaffold.py` (`:74-123`, `:189-198`) to generate a `concept` hook alongside `make`, and update `tests/test_scaffold.py:263` and `tests/test_cli.py:97`.

## 5. End-to-end verification

- [ ] 5.1 Add an end-to-end test walking wish → concept → make → playtest → instructions → deliver with the fixture artist, asserting the run records the concept hash and that Make received the concept for its round.
- [ ] 5.2 Add a test that a run with no concept provider parks at job `concept` with the expected `Need`, and that Make is never called.
- [ ] 5.3 Add a test that feedback invalidating `concept` reaches the next round's `ConceptContext` and that the next concept reflects the requested change.
- [ ] 5.4 Add a test that a concept whose bytes change between Concept returning and Make returning fails the round with an artifact error.
- [ ] 5.5 Add a test that a concept image set cannot satisfy the Instructions media roles.
- [ ] 5.5a Add a test that a `Made` whose artifact tree copies a concept image is rejected, and that an Instructions product image with concept bytes is rejected — including the case where the build followed the concept closely and the substitution would have gone unnoticed.
- [ ] 5.6 Run the full suite and confirm no previously passing test regressed.

## 6. Documentation

- [ ] 6.1 Update the pipeline diagram and the jobs table in `README.md:112-117` and `:176-186` to six jobs.
- [ ] 6.2 Update `docs/ARCHITECTURE.md`: the flow line (`:51-61`), the job-contracts record exchange (`:221-247`), the customization table (`:207-211`), and the module map (`:388-402`) for the new `concept.py`.
- [ ] 6.3 Add a Concept section to `docs/BUILD_AN_INVENTOR.md` beside the custom-Make guidance (`:302-336`), covering the provider seam and what following a concept obliges Make to do.
- [ ] 6.4 Reaffirm in `docs/ARCHITECTURE.md:354` that concept art guides Make and never stands in as product proof, now that concept art is a first-class record.
- [ ] 6.5 Update `docs/ADOPTION.md` and `docs/MIGRATION.md` for the six-job set and the blueprint migration.
