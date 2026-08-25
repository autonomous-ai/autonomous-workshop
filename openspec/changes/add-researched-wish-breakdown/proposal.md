## Why

The step that breaks a Wish down into physical facts does no work. `derive_brief()` (`src/inventor_workshop/concept.py:414`) reads `wish.constraints`, and where a key is absent it substitutes a hardcoded default: a 120 × 120 × 60 mm envelope, a 2.4 mm wall, a single component called `body`, and a "distinctive feature" that is the objective sentence pasted back verbatim. Nothing ever fills `wish.constraints` — the inventor profiles set `{"lane", "audience"}` and stop (`inventors/alice/profile.py:31`), so the default path is the only path a real Wish takes.

The result is a brief that carries no information the Wish did not already carry. For the wish *"Have Alice create a really cool chess set with NYC building style"*, the concept locked one 120 mm cube named "Body", six assumptions all reading "The Wish did not state X; Concept decided \<default\>", and a feature list quoting the wish back at itself. Every downstream consumer inherits that emptiness: the image prompts carry meaningless millimetres, the exploded view has one part to separate, `_assert_product_follows_concept` checks Make against a one-item component list, and CAD is asked to build a cube. Concept is meant to be the job that decides what the object actually is; today it decides nothing, and the emptiness is sealed into `concept_sha256` and shipped forward as if it were a decision.

## What Changes

- Add a `WishResearcher` capability to Concept: an injected port, in the same shape as `concept_artist` and `explode_inspector`, that receives the Wish, the Taste, and the lane blueprint and returns a researched breakdown — the object and category, the envelope and wall thickness, the fit target, the print stance, the distinctive features, and a real multi-part component breakdown with per-component form, dimensions, placement, and interfaces.
- Require the research to be **grounded and cited**. Every physical fact the breakdown states SHALL be attributable: either to a named source the researcher read, or to a recorded decision Concept made in the absence of one. A number with neither is refused.
- Seal the research beside the pixels. The concept root gains a `research/` subtree — `findings.json` mapping each claim to its source ids, and `sources/NNN.json` recording each source's URL, title, the exact excerpt relied on, its sha256, and when it was retrieved. `build_artifact_manifest` already hashes the whole concept root, so the research seals into `concept_sha256` for free and cannot be swapped after the fact.
- Make `derive_brief()` a consumer of research rather than a generator of defaults. It keeps its two existing jobs — carrying a standing brief forward through a refining round, and folding accumulated feedback edits into `assumptions` — and loses the hardcoded envelope, wall, feature, orientation, support, and single-`body` fallbacks.
- **BREAKING**: Concept waits when no researcher is configured. `DefaultConcept` raises `WaitingFor(Need("concept", "wish-research", ...))` alongside the existing `concept-images` and `exploded-view-check` needs, and the run parks at `concept` rather than proceeding on invented numbers. A Workshop that today reaches Make with the default brief will now park until a researcher is injected.
- Write the researched constraints back into a **derived** Wish record — the routed Wish's `product_id`, `objective`, and `context`, plus the researched `constraints` — recorded alongside the concept and written to `artifact/wish.json`. The routed Wish is never mutated: `RoutingContext.wish_sha256` (`src/inventor_workshop/manager.py:563`) binds the untouched words that matching was decided from, and the derived record names both hashes so the two can never be confused.
- Add `OpenAICompatibleWishResearcher`, a real researcher backed by a caller-configured OpenAI-compatible chat endpoint with web search enabled — base URL, API key, and model all supplied by the caller, no vendor hardcoded — following `OpenAICompatibleExplodeInspector` exactly. Not wired into any inventor by this change.
- Add `tools/wish_research_fixture.py`, a deterministic fixture researcher kept out of `src/` for the same reason `tools/concept_fixture.py` is, so the test suite and `tools/build_showcase_products.py` still exercise the whole pipeline with no model and no network.

## Capabilities

### New Capabilities
- `workshop/wish-research`: The researched wish breakdown — the `WishResearcher` port contract, what a breakdown must decide, the citation rule that separates a sourced fact from a recorded decision, the sealed `research/` record, and the derived Wish write-back that leaves the routed Wish untouched.
- `workshop/wish-researcher-openrouter`: A real `WishResearcher` backed by a caller-configured OpenAI-compatible chat endpoint with web search — request shape, source extraction, strict parsing into a breakdown, and failure behavior.

### Modified Capabilities
- `workshop/concept-job`: Concept gains a third truthful wait (`wish-research`) and a stated order of work within a round — research, then brief, then images — so no image is drawn against a fact that was never decided.
- `workshop/concept-images`: The brief's facts must now be researched and attributable rather than defaulted. `assumptions` must distinguish a fact taken from a source from a fact Concept decided, a single-component breakdown is legitimate only when the research concluded the design is one part, and the sealed concept includes the research record it was derived from.

## Impact

- `src/inventor_workshop/concept.py` — new `WishResearcher` port and `WishResearchRequest` / `WishResearch` records, `derive_brief()` rewritten around research, `DefaultConcept.__init__` gains a `wish_researcher` argument and its `__call__` gains the research step and the `research/` write, `_write_descriptor` records the research binding and the derived Wish.
- `src/inventor_workshop/jobs.py` — `ConceptImages` carries and re-checks the research record; the `research/` subtree participates in the existing manifest seal.
- `src/inventor_workshop/workshop.py` — `WorkshopTools` gains the researcher so it is installed once per Workshop, and the run records the derived Wish alongside the concept hash.
- New module `src/inventor_workshop/wish_researcher_openrouter.py` — adapter only, not wired into `DefaultConcept` by default.
- New runtime configuration for anyone using the adapter: a base URL, API key, and model, read through `load_dotenv` like the existing endpoints. No new Python package dependency; HTTP stays on stdlib `urllib` via `_http.py`.
- `tools/build_showcase_products.py` and the test suite inject the new fixture researcher; `tools/concept_fixture.py` is unchanged.
- Existing sealed showcase toys under `inventors/*/toys/` keep their recorded `concept_sha256` and are not re-derived by this change.
- `docs/ARCHITECTURE.md` and `README.md` describe Concept's work as research → brief → images, and name `wish-research` among the capabilities a run can wait for.
