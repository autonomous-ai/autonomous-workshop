## Context

See `proposal.md` — Why. Constraints this design has to work inside:

- `concept.py`'s three ports (`WishResearcher`, `ConceptArtist`, `ExplodeInspector`) are unchanged and unaware of which implementation satisfies them; this change only chooses implementations and deletes the ones not chosen, per the existing (unchanged) `agent-concept-adapters` requirement that "Concept keeps taking exactly one implementation per capability."
- `AgentWishResearcher.__call__` today builds `door_request = {"wish": ..., "taste": ..., "lane": ..., "round": ...}` and nothing else — no instructions, no attribution rules. `OpenAICompatibleWishResearcher._research_prompt()` builds the equivalent HTTP prompt by concatenating the same wish/taste/lane facts with a fixed `_INSTRUCTIONS` string stating the required output shape and the attribution rule (source or `decided_because`, never both, never neither).
- `AgentWishResearcher._parse()` already calls `OpenAICompatibleWishResearcher._components(...)` and `OpenAICompatibleWishResearcher._findings(...)` directly as static methods on the class this change deletes — that dependency has to be broken before the class can go, not papered over.
- `concept_agent_session_door_from_env()` currently loops over all three of `_ROLE_ENV_PREFIXES` unconditionally. Once `AgentConceptArtist` and `AgentExplodeInspector` are deleted, nothing ever calls the door under the `concept-images` or `exploded-view-check` roles again, so requiring their environment configuration to build the door serves no one.
- The three surviving classes (`OpenRouterConceptArtist`, `OpenAICompatibleExplodeInspector`, `AgentWishResearcher`) keep their current names. Only the classes with no surviving purpose (`AgentConceptArtist`, `AgentExplodeInspector`, `OpenAICompatibleWishResearcher`) are deleted.

## Goals / Non-Goals

**Goals:**
- Exactly one implementation per Concept capability, with the unused alternative actually deleted rather than left importable and untested-in-anger.
- Close the actual functional gap in the surviving wish-research adapter (no task framing) as part of making it the sole implementation, not as an afterthought.
- One importable function that returns a fully usable Concept capability with this exact, now-uncontested wiring.

**Non-Goals:**
- Choosing this wiring as any inventor's or the CLI's default. No existing call site changes.
- Changing the agent door's (`AgentSessionDoor`/`AgentRoleConfig`) own generic contract — role dispatch, workspace isolation, wall-clock/budget enforcement stay exactly as `agent-door` already specifies, and it keeps supporting arbitrary roles for whatever a future Make/Playtest door needs.
- Verifying that an operator's configured `wish-research` tools actually perform real search. That remains unverifiable from inside this codebase, exactly as already true for every other role's tool configuration.
- Renaming any of the three surviving classes (`OpenRouterConceptArtist`, `OpenAICompatibleExplodeInspector`, `AgentWishResearcher`) or their source files. Nothing in this change requires touching their names or their internal request/response logic — only the classes with no surviving purpose are removed.

## Decisions

### The unused alternative per capability is deleted, not deprecated or left importable

`AgentConceptArtist`, `AgentExplodeInspector`, and `OpenAICompatibleWishResearcher` are removed outright, along with anything only they used (`ROLE_CONCEPT_IMAGES`, `ROLE_EXPLODED_VIEW_CHECK`, and every HTTP-transport concern in `wish_researcher_openrouter.py` — retries, SSE streaming, the chat-completions request shape, its own citation-to-source mapping).

**Alternative considered:** keep them importable but unwired, as they are today, and only add the new entry point. Rejected — the user's explicit direction is one implementation per port; keeping three untested-in-anger, never-wired implementations around after settling the question of which one is used is exactly the dead-code-for-a-choice-no-one-exercises this change is meant to end.

### The wish-research parsing logic `AgentWishResearcher` depends on moves with it, not away from it

`_components()`, `_findings()`, and the required-field list (`_REQUIRED_ANSWER_FIELDS`) move out of `OpenAICompatibleWishResearcher` and into `concept_agent_adapters.py` as free functions, before that class is deleted. The research instructions string (`_INSTRUCTIONS`) moves the same way, renamed `RESEARCH_INSTRUCTIONS`. Once nothing in `wish_researcher_openrouter.py` is referenced from outside it, the file is deleted entirely.

**Alternative considered:** keep `wish_researcher_openrouter.py` alive as a shared-utilities module, deleting only the `OpenAICompatibleWishResearcher` class itself. Rejected — a module named after the HTTP adapter it no longer contains is a worse landing spot for shared parsing logic than the module of the one implementation that now actually uses it; nothing else would ever import from it again.

### The surviving classes keep their current names

`OpenRouterConceptArtist`, `OpenAICompatibleExplodeInspector`, and `AgentWishResearcher` are not renamed. `src/inventor_workshop/__init__.py`'s exports change only by removing the three deleted classes — nothing about the three survivors' names or their re-export changes.

**Alternative considered:** rename the survivors to the bare port name (`ConceptArtist`, `ExplodeInspector`, `WishResearcher`), since there is now only one implementation each. Rejected — this would collide with `concept.py`'s own same-named Callable type aliases at `__init__.py`'s top level, and the user decided against taking on that rename and its export fallout for this change.

### The agent door's environment constructor is narrowed to the one role it will ever be asked for

`concept_agent_session_door_from_env()` (staying in `concept_agent_adapters.py`, alongside the sole remaining agent adapter) reads and requires only `AGENT_DOOR_LAUNCH_COMMAND` and the `wish-research` role's own `_TOOLS`/`_ALLOWED_PATHS`/`_WALL_CLOCK_SECONDS`/`_MAX_BUDGET_MICROS`. The per-role loop over `_ROLE_ENV_PREFIXES` and the now-unused `ROLE_CONCEPT_IMAGES`/`ROLE_EXPLODED_VIEW_CHECK` constants go with it.

**Alternative considered:** generalize the function to accept a caller-chosen subset of roles (an earlier version of this design), keeping all three roles' env-parsing paths alive for a hypothetical future caller. Rejected once the two other agent adapters are actually deleted — a "which roles do you want" parameter for a function that only ever has one real role to offer is speculative generality for a case this change itself just closed off. `AgentSessionDoor`/`AgentRoleConfig` underneath remain fully general for whenever Make or Playtest needs a door of their own; only this Concept-specific environment constructor narrows.

### The wiring entry point fails closed per capability, before any of the three is exercised

`concept_capabilities_from_env()` builds all three in a fixed order — `concept-images`, `exploded-view-check`, `wish-research` — each via its own `.from_env()` (the door via the now wish-research-only environment constructor). Each step's `ContractError` is caught and re-raised naming that capability's own `Need` string (`concept-images`, `exploded-view-check`, `wish-research`), chained via `from exc`. Nothing is invoked over the network or a subprocess during construction — every `.from_env()` only validates environment presence — so "fails before any capability runs" falls out of that for free.

**Alternative considered:** let each adapter's own `ContractError` propagate unwrapped. Rejected — those messages name the class (`"OpenRouterConceptArtist.from_env requires..."`), not the capability (`concept-images`); the spec requirement calls for naming the capability, matching how the rest of the system (`Need`, the door's own role names) already talks about these three things.

### `budget_micros` for the wish-research door call is its own, separate, required setting

The wish-research adapter takes a `budget_micros` at construction — distinct from the door role's own optional `max_budget_micros` ceiling, which only caps, never supplies, a call's budget. `concept_capabilities_from_env()` reads a new required env var, `CONCEPT_WISH_RESEARCH_BUDGET_MICROS`, for this.

**Alternative considered:** reuse the role's `AGENT_DOOR_WISH_RESEARCH_MAX_BUDGET_MICROS` (already optional) as both the ceiling and the requested amount. Rejected — the two numbers answer different questions ("what's the most this role may ever spend" vs. "what is this call asking for"), and conflating them would make the ceiling unconfigurable independently of the per-call ask, a distinction `AgentRoleConfig.max_budget_micros`'s own docstring already draws.

## Risks / Trade-offs

- **Deleting `AgentConceptArtist`/`AgentExplodeInspector` forecloses reviving an agent-backed image or inspection path without rewriting it from scratch.** → Accepted deliberately: neither was ever wired into a real run, and the pattern (a thin adapter dispatching through `ModelDoor`) is still fully documented by the surviving wish-research adapter and the unchanged `agent-door` spec if it's ever wanted again.
- **Nothing enforces that the operator's configured `wish-research` tools actually include real web search.** → Out of scope by design (see Non-Goals); the same unverifiable-from-inside-the-codebase trust boundary already applies to every role's tool configuration and to the OpenRouter web plugin the deleted HTTP researcher used to lean on. Documented as an operational expectation, not a spec requirement, since it cannot be checked in code.
- **This change adds a wiring entry point nothing calls yet.** → Deliberate (see proposal's Non-Goals); wiring a specific inventor to it is a separate, later choice.

## Migration Plan

1. In `wish_researcher_openrouter.py`, extract `_components`, `_findings`, `_REQUIRED_ANSWER_FIELDS`, and `_INSTRUCTIONS` (renamed `RESEARCH_INSTRUCTIONS`) as free functions/constants; move them into `concept_agent_adapters.py`.
2. Update `AgentWishResearcher` to call the moved `_components`/`_findings` functions directly and to send `instructions: RESEARCH_INSTRUCTIONS` in its door request; extend its tests.
3. Delete `AgentConceptArtist`, `AgentExplodeInspector`, `ROLE_CONCEPT_IMAGES`, `ROLE_EXPLODED_VIEW_CHECK` from `concept_agent_adapters.py`.
4. Narrow `concept_agent_session_door_from_env()` to the `wish-research` role only; update its tests.
5. Delete `wish_researcher_openrouter.py` and `tests/test_wish_researcher_openrouter.py`, migrating any still-relevant parsing-logic test cases into `tests/test_concept_agent_adapters.py`.
6. Update `src/inventor_workshop/__init__.py` to drop the three deleted classes' exports. `OpenRouterConceptArtist`, `OpenAICompatibleExplodeInspector`, and `AgentWishResearcher` keep their existing names and exports unchanged.
7. Add `concept_capabilities.py` with `concept_capabilities_from_env()`, and its own tests covering full success and one failure case per capability's missing configuration.
8. Document in `README.md` and `docs/ARCHITECTURE.md`.

Rollback is reverting the change: nothing existing calls the new module, and every deletion is confined to this repository's own source and tests (no persisted artifact shape, external API, or inventor profile depends on any of the removed names). No existing name is renamed, so no rollback is needed on that front.
