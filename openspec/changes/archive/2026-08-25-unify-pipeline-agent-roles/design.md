## Context

See `proposal.md` — Why. The relevant constraints on the approach:

- `doors.py` already defines the protocol this change builds on: `ModelDoor.run(role, request, budget_micros)`. Its own docstring says newer *idempotent-effect* integrations (Send, Deliver) should move to `integrations.Adapter`; it says nothing of the kind about `ModelDoor`, and `make.py` imports it today for `Workbench`. `ports.py`'s `AgentPort` is the *earlier* (Workshop 0.1) name for the same idea, kept only so `src/inventor_core` — an explicitly-labelled 0.1 compatibility namespace — can still read old runtimes. This change targets `doors.py`, not `ports.py`, so a later proposal extending the same door to Make/Playtest has one contract to build on, not two.
- `_http.py`'s `Transport` is already an injected seam so every existing HTTP adapter can be tested without touching the network. The same shape — an injectable "how do I actually reach the outside world" seam — is what lets a new subprocess-based door stay testable.
- Concept's three ports (`WishResearcher`, `ConceptArtist`, `ExplodeInspector`) are plain typed callables, each independently injected into `DefaultConcept`. Nothing about their shape needs to change for a new implementation to satisfy them.

## Goals / Non-Goals

**Goals:**

- One real `ModelDoor` implementation, so Concept's three capabilities can be wired to one real agent instead of three independent scripted adapters.
- Reuse what already works: the existing HTTP adapters remain a valid, cheaper alternative for these three single-shot roles; nothing about Concept's own behavior changes.
- The new door fails closed exactly like the existing adapters do: an unconfigured role waits truthfully, a failed or dishonest result is refused, nothing is fabricated to keep a round moving.
- Tight, role-scoped tool access for the launched agent process, so "the agent can run Bash" never becomes "the agent can touch anything on the machine."
- Land a contract (`ModelDoor` implementation shape, role vocabulary, result contract) that a later Make/Playtest proposal can extend without rework.

**Non-Goals:**

- Make and Playtest. No `CadDoor`, no `Workbench` composition, no `MakeJob`/`PlaytestJob` wrapper, no change to `WorkshopTools`. These are explicitly a separate, later proposal — see `proposal.md`.
- Replacing or deprecating `OpenRouterConceptArtist`, `OpenAICompatibleExplodeInspector`, or `OpenAICompatibleWishResearcher`. They stay as the cheaper, deterministic-enough option for callers who don't need an agent for those three roles.
- Picking one specific coding-agent product as *the* implementation. The door's launch command is caller-supplied, the same way every existing adapter's base URL is.
- Deliver, or any real-world fulfillment integration.
- Changing `ConceptImages`, `ConceptBrief`, `WishResearch`, or any other existing record's shape. This change adds producers of those shapes; it does not touch the shapes themselves.

## Decisions

### The role vocabulary is Concept's existing `Need` capability strings

A role name is exactly one of `wish-research`, `concept-images`, `exploded-view-check` — the same strings Concept's own `Need`s already carry. No new naming scheme is introduced for this change's scope.

**Alternative considered:** a fresh, door-specific role vocabulary. Rejected — it would mean every `Need` needed a second name purely for wiring, and the two vocabularies could drift out of sync with no mechanism forcing them to agree. It also would not compose cleanly with a later proposal that reuses `toys.py`'s `ToyTask.task_id` strings for Make/Playtest roles.

### The door talks to its agent process through a file-based result contract, not parsed stdout

The launched process is expected to write one JSON file, at a path the door tells it about, before exiting. The door reads that file after the process exits; a missing or malformed file is a failed call, regardless of what the process printed. Stdout/stderr are captured for diagnostics only, never parsed for the result.

**Alternative considered:** parsing a structured final message out of the process's stdout (the shape a headless CLI's `--output-format json` mode already produces). Rejected as the *primary* contract — an agent process that also logs progress, or whose final message wraps the JSON in prose, makes stdout parsing fragile in exactly the way `wish_researcher_openrouter.py` already had to guard against for a chat model's answer. A fixed output file has no such ambiguity. A caller-supplied launcher may still *use* a CLI's own JSON stdout mode internally to build that file — that is the launcher's business, not the door's contract.

### Per-role configuration owns tool scope, workspace contents, and budget; the door enforces it, never a role's own prompt

Each configured role carries: the tools/file access the launched process gets, what (if anything) is pre-populated into its workspace before it starts, the wall-clock bound, and the dollar budget. The door builds the process's actual permission boundary from this configuration — never from anything the role's request or the agent's own output claims about itself. For this change's three roles, that access is narrow: `wish-research` needs web search and no file-write access beyond its own result file; `concept-images` and `exploded-view-check` need whatever image-generation/vision access their launcher provides and no Bash/network access beyond that.

**Alternative considered:** trusting the launched agent to stay within an access boundary it's merely told about in its prompt. Rejected outright — that is not an enforcement mechanism, and this repository's whole ethic is that a boundary that isn't checked isn't a boundary (see `CONTRIBUTING.md` — "An inventor may strengthen a gate but must not create a bypass around a shared floor").

### Wall-clock is a hard bound; dollar budget is enforced where it can be, reported where it can only be observed

The door can always kill a process once its configured wall-clock bound elapses — that requires no cooperation from the process. A dollar budget can be enforced *before starting* (refuse a call whose configured budget is non-positive) and checked incrementally if the launcher can report spend as it goes, but a process that goes straight from "under budget" to "way over" between two cost reports can only be caught after the fact. The door treats wall-clock as the hard backstop and dollar budget as enforced whenever the launcher can report it.

**Alternative considered:** treating `budget_micros` as advisory-only, matching nothing more than what the existing HTTP adapters do with a timeout. Rejected — `ModelDoor.run`'s signature already names `budget_micros` as a real parameter, and a caller wiring a real agent needs to trust the number means something, even knowing the enforcement is necessarily best-effort past the point a launcher can report spend.

### The three Concept adapters are thin translators, not a rewrite of Concept

`AgentWishResearcher`, `AgentConceptArtist`, and `AgentExplodeInspector` each take a `ModelDoor` and satisfy the exact existing port signature Concept already calls. Each adapter's job is: build the door's request mapping from its typed input, call the door with its capability's role name, and strictly parse the door's structured result back into the typed return value the port already promises — reusing the same strict-parsing posture (missing fact raises, unattributed field raises) `wish_researcher_openrouter.py` already established, not a looser one.

**Alternative considered:** changing `DefaultConcept` to hold one `ModelDoor` instead of three separate ports. Rejected — it would touch `concept.py`, `ConceptContext` construction, and every existing Concept test for no behavioral gain; the three-port shape already works and the adapters can sit entirely behind it.

## Risks / Trade-offs

- **Running an autonomous agent with real tool access is a real blast-radius increase over a single HTTP call.** → Every role's tool/file access is configured, not inferred from a prompt (see Decisions), and each call runs in a workspace created fresh for it.
- **Dollar budget cannot be preempted with certainty for a launcher that only reports cost after the fact.** → Called out explicitly in Decisions rather than papered over; wall-clock remains a hard, always-enforceable backstop regardless.
- **An agent role can still be wrong about the world, same as a researched Concept already can be today.** → Unchanged by this proposal: a bad researched breakdown is still caught the same way it already is — attribution rules refuse an unsourced/undecided fact, and a bad design still only survives until Playtest rejects it, whenever Playtest exists to do so.
- **Two integration shapes (agent-backed vs. the existing single-shot HTTP adapters) now coexist for Concept's three roles.** → Deliberate (see Non-Goals); an operator who wants determinism and lower cost for those three still has it, and nothing forces a choice between the two paths.
- **A launched process that hangs without producing output ties up its budget until the wall-clock bound fires.** → That bound is mandatory per role configuration (see the agent-door spec), not optional, so the worst case is a bounded stall, never an unbounded one.
- **Scoping this change to Concept only means Make and Playtest remain exactly as unimplemented as they are today.** → Intentional; a smaller, independently-landable, independently-reviewable change was preferred over one that also had to get CAD generation and seeded simulation right. The role vocabulary and door contract landed here are chosen so the later proposal extends rather than reworks them.

## Migration Plan

1. Land `AgentSessionDoor` and its injectable process-launcher seam, plus the deterministic fixture launcher, with nothing yet wired into any `WorkshopTools`. Inert until configured, exactly like the existing OpenRouter adapters were on landing.
2. Land the three Concept adapters (`AgentWishResearcher`, `AgentConceptArtist`, `AgentExplodeInspector`) and their tests against the fixture launcher. Concept's own behavior is unchanged; only a new way to satisfy its existing ports exists.
3. Update `docs/ARCHITECTURE.md`, `README.md`, and `CONTRIBUTING.md`.

Rollback is reverting the change: nothing it adds is on a path any existing caller executes by default, and no persisted artifact shape changes.

## Open Questions

- The exact shape of the per-role tool/file access configuration (an explicit allow-list of tool names? a directory allow-list plus a fixed tool set?) is an implementation detail of `AgentSessionDoor`'s configuration, not a change to any spec's observable behavior — the agent-door spec only requires that access is role-scoped and enforced, not the configuration format. Settle it in `tasks.md`/implementation.
