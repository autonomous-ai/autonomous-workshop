## Why

Concept's three capabilities — `wish-research`, `concept-images`, `exploded-view-check` — each have a real, working implementation (`OpenAICompatibleWishResearcher`, `OpenRouterConceptArtist`, `OpenAICompatibleExplodeInspector`), and `wish-research` now also has an agent-backed alternative (`AgentWishResearcher`, landed in `unify-pipeline-agent-roles`). None of the three is wired into a reusable, committed entry point anywhere in this repository: every real Concept run to date (e.g. `inventors/alice/toys/nyc-skyline-chess-set-v2`) was produced by hand-constructing `DefaultConcept(...)` in a one-off, uncommitted script against the HTTP adapters. Nothing preserves that wiring for the next run, and nothing exists today that uses the agent-door adapters for anything beyond their own unit tests.

The image and inspection HTTP adapters have a real track record; the agent-door adapters do not, but their tool-using process model is a better fit for wish-research specifically, which needs genuine grounded search rather than trusting a single provider's built-in web plugin. This change commits to that split, makes it real and reusable, and closes the specific gap that makes `AgentWishResearcher` unfit for that job today: it sends the agent process raw facts and a role name, but never the task instructions or attribution rules that make a researched breakdown trustworthy — the OpenRouter wish researcher carries that text explicitly; the agent-backed one carries none of it.

## What Changes

- Add `concept_capabilities_from_env()`, a real wiring entry point (`concept_capabilities.py`) that returns one fully-configured `DefaultConcept`: `concept-images` and `exploded-view-check` satisfied by the existing HTTP adapters, `wish-research` satisfied by the agent-door adapter. Construction fails closed, naming whichever underlying capability's configuration is missing, rather than returning a partially-configured Concept.
- Settle each of Concept's three capabilities on exactly one implementation, and delete the other: keep the HTTP adapters for `concept-images` and `exploded-view-check` (`OpenRouterConceptArtist`, `OpenAICompatibleExplodeInspector`) and delete their never-used agent-backed counterparts (`AgentConceptArtist`, `AgentExplodeInspector`); keep the agent-door adapter for `wish-research` and delete the HTTP one (`OpenAICompatibleWishResearcher`), moving the parsing logic the agent adapter already depends on (`_components`, `_findings`, its required-field list) out of that class and into a free function before deleting it. This empties `wish_researcher_openrouter.py` entirely, so the module is removed.
- Give the wish-research adapter the same task instructions and attribution rules the deleted HTTP researcher used to send, so a launched agent process is told what to decide and how to attribute it, instead of being expected to already know the wish-research contract by convention alone.
- Narrow the agent-door environment constructor to build a door for the `wish-research` role only — it no longer reads or requires `concept-images`/`exploded-view-check` tool, path, or wall-clock configuration, since no adapter will ever request the door under those roles again.
- Document the new entry point, the one-implementation-per-port state, and the operational expectation that the `wish-research` role's configured tools must include a real web-search capability for the agent-backed path to be worth using over an HTTP one.

**Not changed / explicitly out of scope:**
- `DefaultConcept`, `ConceptContext`, `ConceptImages`, and the surviving adapters' own request/response behavior toward their external endpoint or process — this change deletes the unused alternative per capability; it does not change what the survivor sends or how it parses a response, and none of the three surviving classes is renamed.
- The agent door's (`doors.ModelDoor`/`AgentSessionDoor`/`AgentRoleConfig`) own generic contract — role dispatch, workspace isolation, budget/wall-clock enforcement — is unchanged; it still supports arbitrary roles for a future Make/Playtest door.
- Make and Playtest remain unimplemented; this change is scoped to Concept's three capabilities only.
- No inventor profile, CLI flag, or `WorkshopTools` default is changed to call the new entry point automatically — wiring it into a specific inventor's run remains that inventor's own explicit choice, consistent with how every existing adapter is opt-in.

## Capabilities

### New Capabilities
- `workshop/concept-capability-wiring`: `concept_capabilities_from_env()`, the one committed entry point that assembles Concept's three capabilities as HTTP (images, exploded-view-check) plus agent-door (wish-research), failing closed and naming whichever capability's configuration is missing.

### Modified Capabilities
- `workshop/agent-concept-adapters`: pared down to the one surviving agent-backed adapter (wish-research) — the requirements describing the deleted agent-backed image and exploded-view-check adapters are removed. The surviving wish-research adapter gains a requirement that its door request carries research instructions and attribution rules, and the shared door's environment constructor gains a requirement that it configures the `wish-research` role only.
- `workshop/wish-researcher-openrouter`: retired entirely — every requirement is removed, since the HTTP wish researcher it describes is deleted in favor of the agent-backed one.

## Impact

- New module: `src/inventor_workshop/concept_capabilities.py` (`concept_capabilities_from_env`).
- Removed module: `src/inventor_workshop/wish_researcher_openrouter.py`. Its still-needed parsing logic (`_components`, `_findings`, the required-field list, the research instructions text) moves into `concept_agent_adapters.py`.
- Modified: `src/inventor_workshop/concept_agent_adapters.py` — `AgentConceptArtist` and `AgentExplodeInspector` deleted; `AgentWishResearcher` gains the instructions field in its door request and absorbs the parsing logic moved from the removed module; the environment door constructor is narrowed to the `wish-research` role only. `AgentWishResearcher` keeps its name.
- `src/inventor_workshop/__init__.py`: drop the deleted classes' exports (`AgentConceptArtist`, `AgentExplodeInspector`, `OpenAICompatibleWishResearcher`). No other export changes — `OpenRouterConceptArtist` and `OpenAICompatibleExplodeInspector` keep their names and exports as-is.
- Tests: `tests/test_wish_researcher_openrouter.py` removed (parsing-logic coverage migrates into `tests/test_concept_agent_adapters.py`); `tests/test_concept_agent_adapters.py` updated for the deleted classes and the new instructions field. `tests/test_concept_artist_openrouter.py`, `tests/test_concept_explode_inspector.py`, `tests/test_concept_real_providers_pipeline.py`, and `tests/test_env.py` are untouched — nothing they test is renamed or removed.
- `README.md`, `docs/ARCHITECTURE.md`: document the new entry point, the one-implementation-per-port state, and the tool-configuration expectation for `wish-research`.
- No change to any persisted artifact shape, `concept_sha256`/artifact hashing, `DefaultConcept`, or any surviving adapter's own request or response handling.
- No existing caller is changed to use the new entry point; nothing that runs today changes behavior as a result of this change landing.
