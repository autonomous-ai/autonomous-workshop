## 1. Extract the parsing logic the surviving wish-research adapter depends on

- [x] 1.1 In `wish_researcher_openrouter.py`, identify `_components`, `_findings`, `_REQUIRED_ANSWER_FIELDS`, and `_INSTRUCTIONS` as the only pieces `AgentWishResearcher` needs.
- [x] 1.2 Move `_components` and `_findings` into `concept_agent_adapters.py` as module-level functions (no longer static methods of `OpenAICompatibleWishResearcher`); move `_REQUIRED_ANSWER_FIELDS` alongside them.
- [x] 1.3 Move `_INSTRUCTIONS` into `concept_agent_adapters.py`, renamed `RESEARCH_INSTRUCTIONS`, and add it to `__all__`.
- [x] 1.4 Update `AgentWishResearcher._parse()` to call the moved `_components`/`_findings` functions directly instead of `OpenAICompatibleWishResearcher._components`/`_findings`.

## 2. Give the wish-research adapter real task framing

- [x] 2.1 In `AgentWishResearcher.__call__`, add `"instructions": RESEARCH_INSTRUCTIONS` to `door_request`, alongside the existing `wish`/`taste`/`lane`/`round` fields.
- [x] 2.2 Extend `test_concept_agent_adapters.py` to assert the door request includes `instructions` equal to `RESEARCH_INSTRUCTIONS`.

## 3. Delete the unused agent-backed adapters and their role constants

- [x] 3.1 Delete `AgentConceptArtist` and `AgentExplodeInspector` from `concept_agent_adapters.py`.
- [x] 3.2 Delete `ROLE_CONCEPT_IMAGES` and `ROLE_EXPLODED_VIEW_CHECK` (keep `ROLE_WISH_RESEARCH`).
- [x] 3.3 Remove their test coverage from `test_concept_agent_adapters.py` (keep and extend wish-research coverage).

## 4. Narrow the agent door's environment constructor to wish-research only

- [x] 4.1 In `concept_agent_session_door_from_env()`, drop the loop over `_ROLE_ENV_PREFIXES`; read and require only `AGENT_DOOR_LAUNCH_COMMAND` and the `wish-research` role's `_TOOLS`/`_ALLOWED_PATHS`/`_WALL_CLOCK_SECONDS`/`_MAX_BUDGET_MICROS`.
- [x] 4.2 Update its tests: drop cases about `concept-images`/`exploded-view-check` env vars; keep and confirm the missing-wish-research-config failure case.

## 5. Delete the HTTP wish researcher and its now-empty module

- [x] 5.1 Delete `OpenAICompatibleWishResearcher` and everything in `wish_researcher_openrouter.py` left unused after task 1 (`ENV_WISH_RESEARCHER_*`, `CHAT_COMPLETIONS_PATH`, `WEB_SEARCH_PLUGIN_ID`, retry/streaming/prompt-building helpers, `_extract_json_object`, `_research_prompt`, its own `_sources`).
- [x] 5.2 Confirm nothing else imports from `wish_researcher_openrouter`; delete the file.
- [x] 5.3 Delete `tests/test_wish_researcher_openrouter.py`, migrating any test cases for `_components`/`_findings` parsing behavior not already covered into `tests/test_concept_agent_adapters.py`.

## 6. Fix up the package's top-level exports

- [x] 6.1 In `src/inventor_workshop/__init__.py`, remove the exports for the deleted classes (`AgentConceptArtist`, `AgentExplodeInspector`, `OpenAICompatibleWishResearcher`).
- [x] 6.2 Leave `OpenRouterConceptArtist`, `OpenAICompatibleExplodeInspector`, and `AgentWishResearcher`'s imports and `__all__` entries exactly as they are today — no rename.
- [x] 6.3 Grep the repository for any other reference to the removed names and update it.

## 7. The wiring entry point

- [x] 7.1 Add `src/inventor_workshop/concept_capabilities.py` with `concept_capabilities_from_env(*, dotenv_path: Optional[str] = None) -> DefaultConcept`.
- [x] 7.2 Implement construction in order: `OpenRouterConceptArtist.from_env(dotenv_path=dotenv_path)`, `OpenAICompatibleExplodeInspector.from_env(dotenv_path=dotenv_path)`, then `concept_agent_session_door_from_env(dotenv_path=dotenv_path)` plus reading the new `CONCEPT_WISH_RESEARCH_BUDGET_MICROS` env var to construct `AgentWishResearcher(door, budget_micros)`.
- [x] 7.3 Catch each step's `ContractError` and re-raise one naming that capability (`concept-images`, `exploded-view-check`, `wish-research`), chained with `from exc`.
- [x] 7.4 Return `DefaultConcept(concept_artist, explode_inspector, None, wish_researcher)`.
- [x] 7.5 Add `concept_capabilities.py`'s exports to `src/inventor_workshop/__init__.py`.
- [x] 7.6 Add `tests/test_concept_capabilities.py`: a full-success case (using each underlying adapter's own override/injection seams to avoid real network or subprocess calls) asserting the returned `DefaultConcept` carries the expected adapter types; one failure case per capability's missing configuration, asserting the raised error names that capability and that no other capability was constructed.

## 8. Documentation

- [x] 8.1 Update `README.md`'s "Connecting the shared Concept capabilities" section: one implementation per capability (names unchanged), `concept_capabilities_from_env()`, and the `CONCEPT_WISH_RESEARCH_BUDGET_MICROS` env var.
- [x] 8.2 Document the operational expectation that `AGENT_DOOR_WISH_RESEARCH_TOOLS` must name a tool that gives the launched process real web-search access for the agent-backed path to add anything over an HTTP one — noting this cannot be verified by the code itself.
- [x] 8.3 Update `docs/ARCHITECTURE.md` to reflect the one-implementation-per-port state, the new entry point, and the shared `RESEARCH_INSTRUCTIONS` constant's new home.

## 9. Verification

- [x] 9.1 Run the full test suite; confirm no lingering reference to `AgentConceptArtist`, `AgentExplodeInspector`, or `OpenAICompatibleWishResearcher` remains anywhere in `src/`, `tests/`, `tools/`, `README.md`, or `docs/`, and that `OpenRouterConceptArtist`/`OpenAICompatibleExplodeInspector`/`AgentWishResearcher` are unchanged in name everywhere they're used.
