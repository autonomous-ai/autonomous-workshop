## Why

Concept's three capabilities — `wish-research`, `concept-images`, `exploded-view-check` — are each satisfied today by a bespoke, single-shot HTTP adapter (`wish_researcher_openrouter.py`, `concept_artist_openrouter.py`, `concept_explode_inspector.py`), each independently configured with its own base URL, API key, and model. That shape works, and it is inherently script-driven: it cannot be handed to an agent as "one thing to run" without the agent separately understanding and juggling three unrelated adapter configurations.

`doors.py` already defines a more general contract for exactly this kind of capability — `ModelDoor.run(role, request, budget_micros)`, documented as running "one bounded model **or agent** role" — and `make.py`'s `Workbench` already expects to be handed one. Nothing implements `ModelDoor` for real anywhere in the repository today. This proposal closes that gap for Concept specifically: it gives Concept's three capabilities a real, agent-backed implementation of that same contract, so an operator (or an AI agent asked to run a Wish) has one consistent thing to configure for everything Concept needs, instead of three.

Make and Playtest need the same contract and have none of it — not even the non-agentic version Concept had. That is a materially larger piece of work (real CAD generation, real seeded simulation) and is deliberately left to a separate, later proposal rather than folded in here.

## What Changes

- Add a real, vendor-agnostic `ModelDoor` implementation (`AgentSessionDoor`) backed by an actual tool-using coding-agent process (caller-supplied launch command, e.g. a headless CLI invocation) rather than a single HTTP request. It runs one named role at a time, in a workspace scoped to that role, under a wall-clock and dollar budget (`budget_micros`), and returns the role's structured JSON result.
- Define the role vocabulary this change uses: Concept's existing `Need` capability strings (`wish-research`, `concept-images`, `exploded-view-check`). No second naming scheme is introduced for these three; a future proposal extending the door to Make/Playtest is expected to reuse `toys.py`'s existing `ToyTask.task_id` strings the same way, but that extension is not part of this change.
- Add three thin adapters — `AgentWishResearcher`, `AgentConceptArtist`, `AgentExplodeInspector` — that satisfy Concept's existing `WishResearcher` / `ConceptArtist` / `ExplodeInspector` ports by dispatching through one shared `ModelDoor`, as an alternative to the existing OpenRouter-specific adapters. Concept's contract, `ConceptImages`, and every existing test for it are unchanged; only a new way to wire the same three ports is added.
- Add `tools/agent_door_fixture.py`, a deterministic in-process fake `ModelDoor` (no subprocess, no network) covering the three roles above, so the test suite and `tools/build_showcase_products.py` keep running offline. It supersedes nothing — `tools/concept_fixture.py` and `tools/wish_research_fixture.py` are unaffected.
- Document the new wiring in `docs/ARCHITECTURE.md`, `README.md`, and `CONTRIBUTING.md`: what a role is, the vocabulary, how to point the agent door at a real coding-agent process, and the security scoping each role's tool access is bound to.

**Not changed / explicitly out of scope:**
- The existing `OpenRouterConceptArtist`, `OpenAICompatibleExplodeInspector`, and `OpenAICompatibleWishResearcher` adapters are untouched and remain valid, cheaper alternatives for an operator who does not need agentic depth for those three single-shot roles.
- `Make` and `Playtest` are not addressed. `WorkshopTools.make` and `.playtest` still default to their `_missing_make`/`_missing_playtest` stubs after this change, exactly as they do today. A real `ModelDoor`-backed implementation for those two jobs — including whatever `Workbench` composition and `WorkshopTools` wiring that needs — is a separate, later proposal. `Instructions` therefore remains blocked; this change does not claim to unblock it.
- `Deliver` is not addressed, for the same reason it was already out of scope: it depends on a real carrier/fulfillment integration, a different kind of gap than "needs an agent."

## Capabilities

### New Capabilities
- `workshop/agent-door`: The real `ModelDoor` implementation — role dispatch, per-role workspace and tool scoping, budget accounting and enforcement, structured-result parsing, failure behavior, and the deterministic test fixture.
- `workshop/agent-concept-adapters`: The three thin adapters that satisfy Concept's existing `WishResearcher` / `ConceptArtist` / `ExplodeInspector` ports by dispatching through a shared `ModelDoor`, and how they compose with (never replace) the existing OpenRouter-specific adapters.

### Modified Capabilities
- None. `concept-job` and `concept-images` describe behavior and data shapes, never which adapter implementation is wired; this change adds new implementations behind the same ports and contexts, so no existing requirement changes.

## Impact

- New modules: `src/inventor_workshop/agent_session.py` (`AgentSessionDoor`), `src/inventor_workshop/concept_agent_adapters.py` (`AgentWishResearcher`, `AgentConceptArtist`, `AgentExplodeInspector`).
- `src/inventor_workshop/doors.py` — read, not modified; `AgentSessionDoor` implements its existing `ModelDoor` protocol as-is.
- New fixture: `tools/agent_door_fixture.py`, injected wherever tests or `tools/build_showcase_products.py` need Concept's three capabilities satisfied offline.
- New runtime configuration for anyone using the real agent door: a caller-supplied launch command for the agent process, plus per-role budget and tool-scope settings, read the same way existing adapter configuration is (`load_dotenv`, no hardcoded vendor or binary).
- `docs/ARCHITECTURE.md`, `README.md`, `CONTRIBUTING.md` gain the role vocabulary, the agent-door wiring instructions, and the tool-scoping/security expectations for each role.
- No change to any persisted artifact shape, `concept_sha256`/artifact hashing, or existing sealed showcase toys.
- `WorkshopTools` is not changed by this proposal — no new field is added to it. A convenience seam for wiring one agent across multiple jobs is left for the later Make/Playtest proposal, once there is more than one job for it to compose.
