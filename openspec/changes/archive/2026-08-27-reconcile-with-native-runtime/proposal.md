## Why

While this branch built the Concept phase, `main` replaced the architecture it was built on. `src/inventor_workshop/` is gone; the Workshop is now a native coding-agent manager where one Codex session does all cognitive work and Python is a narrow trusted host that owns identity, lifecycle, contracts, gates, and effects. `AGENTS.md` and `docs/NATIVE_AGENT_RUNTIME.md` now forbid, by name, the three mechanisms this branch is built from: Python prompt chains, Python-spawned agent processes, and Python-side candidate generation. `DefaultConcept`'s prompt builders, `AgentSessionDoor`, and the OpenRouter/OpenAI adapter pair cannot be ported — they are the things the rewrite removed.

The design work behind them survives intact, because it was never really about the Python. `main` has an `invent` stage whose `InventedV2.concept` and `InventedV2.research` are free-form `Mapping[str, Any]` with **no structural contract at all** — only `title` and `summary` are length-checked (`src/workshop/invent/native.py:92-93`). Make's entire design input is that object plus the Wish text and a lane blueprint, yet `product-to-cad/SKILL.md:18-22` already orders the agent to "freeze the visual target" and even warns it never to let CAD likeness grade a reference CAD itself generated — a Concept stage's job, with no Concept stage to do it. The migrated legacy toys carry hand-made `art-direction/` folders, one containing the literal image-generation prompt, proving the practice existed before the architecture had a place for it.

So this change keeps what the branch decided and discards how it executed: the researched-not-defaulted brief, per-fact attribution, complete per-component specification, sealed research, and concept-governs-Make adherence become a real stage with a deterministic host gate — which is precisely the work `main` reserves for Python.

## What Changes

- **BREAKING** — Adopt `main` wholesale. `src/inventor_workshop/` and every module in it (`concept.py`, `agent_session.py`, `concept_agent_adapters.py`, `concept_artist_openrouter.py`, `concept_explode_inspector.py`, `wish_researcher_openrouter.py`, `doors.py`, `jobs.py`) is deleted, along with `skills/`, `web/`, `bin/`, `schemas/`, `snapshots.lock.json`, and `upstreams.json`. `openspec/` is branch-owned and stays.
- **Add `concept` as the sixth run stage**, between Invent and Make: `Wish → Match → Invent → Concept → Make ⇄ Playtest → Release → Deliver`. It gets a `STAGE.json` packet, a `concept.sealed-v1` gate, a `concept_sha256` binding on `NativeMade`, and a place in Playtest's backward-invalidation set, following the existing per-stage pattern exactly.
- **The native session authors the concept; Python never composes a prompt.** In the Concept turn Codex researches the Wish through its own web search and writes a `ConceptBrief` (object, category, envelope in mm, wall thickness, features, print stance, per-component form/dimensions/placement/interfaces, fit target, assumptions), a research record (each finding against a source with excerpt hash and retrieval time, or a recorded decision with its reason), and one drawing instruction per image role. The host validates that structure; it does not write, score, or choose any of it.
- **Concept images are drawn by a host integration, not by the agent.** Codex runs under a permission profile with the sandbox network disabled, so it cannot reach an image model even in principle. A new `src/workshop/integrations/concept_images.py` transports the agent-authored prompts to an image provider between native turns, under the credential-isolation rules the Factory adapter already establishes. It composes nothing — it renders what the brief specified, verifies the returned bytes, and seals them.
- **A missing image credential parks the run**, reusing the proven Release/Factory wait: the stage proposal is accepted, the effect cannot run, and the run records a `waiting` outcome with a concrete `Need` rather than proceeding to Make without a concept.
- **The exploded-view check stops being a second model call.** The vision-model inspector is deleted. Component correspondence is enforced where the host can actually settle it in bytes: `Made`'s declared components must match the brief's components one-to-one, and no file in the product tree may carry a concept image's bytes.
- **ABO becomes a declarative Inventor.** Its 5,416 lines of Python across 11 modules collapse to a schema-v7 bundle — `inventor.json` (one lane, `invented-games`, `source.kind=upstream-snapshot`, hash-bound extension inventory), `TASTE.md`, and a required `abo-inventor` skill — plus one optional `abo-rules-engine` skill whose `scripts/` keep the genuinely specialist deterministic parts (the abstract game engine and its simulation harness). Its Make job, Playtest job, research module, feedback loop, and model-seat orchestration are deleted; the native session and the shared stages do that work.
- **`snapshots.lock.json` is not reintroduced.** ABO's imported-tree provenance moves onto `main`'s existing mechanism: per-extension `artifact_sha256` in the manifest, plus `UPSTREAM.md`.

## Capabilities

### New Capabilities

- `workshop/native-agent-runtime`: The native turn completion boundary —
  external `turn.completed` remains authoritative, with a checkpoint-bound
  30-second quiet fallback documented explicitly as a temporary band-aid
  pending investigation and repair of the missing CLI event translation.
- `workshop/concept-stage`: Concept as a host-gated native stage — its position and transitions, the `STAGE.json` inputs it receives, what the native turn must author, the deterministic gate over that output, the sealed `concept_sha256` it produces, how a later round revises rather than restarts, and what it waits for when an effect cannot run.
- `workshop/concept-image-integration`: The host-side image adapter — that it transports agent-authored drawing instructions rather than composing them, credential isolation and the scrubbed-environment boundary, reference accumulation across roles, writing and sealing returned bytes into the concept tree, and the failure and waiting surfaces that stop a run instead of completing it.

### Modified Capabilities

- `workshop/concept-images`: The concept artifact keeps its brief rules, role set, mutual-consistency anchors, self-describing descriptor, sealing, and concept-art-is-not-evidence prohibition — but is now authored by the native agent and drawn by the host integration, so every requirement phrased around a `ConceptArtist` port is restated against the stage and its gate.
- `workshop/wish-research`: Research stays sealed with the concept and attributable fact by fact, but is performed by the native session inside the Concept turn instead of an injected `WishResearcher` port, and the derived-Wish write-back is expressed as a host-validated record rather than a Python return value.
- `workshop/make-concept-adherence`: Make binds to the concept through `NativeMade.concept_sha256` and the Make `STAGE.json` packet rather than a `MakeContext` field; image roles are named in the packet; and the component-correspondence and no-concept-pixels checks become the Make gate's deterministic obligations.
- `workshop/abo-inventor`: ABO is restated as a schema-v7 declarative bundle — exactly one lane capability, an `extensions` inventory with per-tree `artifact_sha256`, one required `abo-inventor` skill — replacing the v5 manifest, its twelve capability strings, and its executable entry point.
- `workshop/abo-make`: ABO no longer owns a `MakeContext -> Made` contract. The rules-to-engine translation and its declared-assumption discipline survive as obligations on the native Make turn and ABO's hash-bound deterministic tool; STEP-first CAD comes from the shared locked `cad` skill.
- `workshop/abo-playtest`: ABO no longer owns a `PlaytestContext -> Playtested` contract. Its evidence obligations are restated against the shared native Playtest stage and the `game-simulation` check its lane blueprint already requires.

### Removed Capabilities

Each is deleted because `main`'s architecture forbids the mechanism it specifies, not because the concern went away; where a concern survives, the capability that now carries it is named.

- `workshop/agent-door`: Python-spawned, Python-scheduled agent processes. The runtime starts and resumes exactly one root session and "does not schedule agents in Python."
- `workshop/agent-concept-adapters`: Door-backed capability adapters; nothing remains to adapt once Concept has no injected ports.
- `workshop/concept-capability-wiring`: Wired three ports into a Concept job; there are no ports and no job to wire.
- `workshop/concept-explode-inspector`: A second model API for vision. Replaced by native render inspection plus the deterministic component checks in `workshop/make-concept-adherence`.
- `workshop/concept-artist-openrouter`: Named one vendor and one model as contract. Replaced by `workshop/concept-image-integration`, which assumes no vendor.
- `workshop/concept-job`: Specified Concept as a Python callable over a `ConceptContext`. Replaced by `workshop/concept-stage`.
- `workshop/abo-game-research`: ABO-owned research as a Python capability. Research is now the Concept stage's native work; ABO's game-specific judgment lives in its Taste and skill.

## Impact

- **New component** `src/workshop/concept/` (`README.md`, `__init__.py`, `native.py`, `native_gate.py`, `schemas/`), registered in `.github/components.toml`, `tests/architecture/test_component_layout.py`, and `tests/architecture/test_component_import_graph.py`.
- **Eight hard-coded tables** gain a stage: `AGENT_RUN_STAGES`, `_FORWARD_TRANSITIONS`, `_UPSTREAM_STAGE` (`workflow/agent_run.py`), `_FORWARD` and the gate ids (`workflow/stage_gates.py`), `_prepare_stage_input`, `_process_agent_outcome`, and `native_stage_prompt` (`workflow/native_run.py`).
- **Native completion fallback**: `runtime/codex.py` waits 30 quiet seconds
  after a completed agent message and a bounded proposal for the exact current
  checkpoint and subject when external `turn.completed` is missing. This is a
  temporary mitigation, not the root-cause fix.
- **The agent-side finalizer is a second half that must agree byte-for-byte**: `.agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py` gains a `concept` subcommand, `STAGES`/`FORWARD`/`STAGE_FIELDS` entries, and a contract builder producing canonical JSON identical to `concept/native.py`.
- **Instructions**: a `references/concept.md` in the workflow skill, a routing line in its `SKILL.md`, and a Concept bullet in each of the six Inventors' `<id>-inventor/SKILL.md` stage-contribution lists.
- `src/workshop/make/` gains `concept_sha256` on `NativeMade` plus the component-correspondence and image-byte checks; `integrations/` gains one adapter, still importable only by `workflow/native_run.py`.
- **New credential** for the image provider, in `$WORKSHOP_HOME/credentials/`, loaded only outside a native turn and never entering the Codex subprocess. This is a second model credential beyond the developer's Codex subscription, so `README.md`'s quick-start promise needs an accurate qualification: without it a run parks at Concept.
- Docs: `README.md`, `docs/ARCHITECTURE.md`, `docs/NATIVE_AGENT_RUNTIME.md`, `docs/BUILD_AN_INVENTOR.md`, and the floorplan diagram all name the stage list and must gain Concept.
- Tests: `tests/concept/`, extensions to `tests/workflow/`, `tests/make/`, and `tests/end_to_end/test_native_full_run.py` (whose `_OneSessionProductAgent` needs an `_author_concept` turn and whose fake effects need an image adapter, asserting as `_FactoryEffects` does that no credential ever reaches a launcher argument).
- One `changes/<id>.added.md` fragment, per the repository's changelog convention.
- Not addressed here: the two untracked 26 MB run-output trees under `inventors/alice/toys/` are real evidence the old pipeline worked end to end, but they are generated artifacts and the repository keeps generated CAD and media out of Git.
