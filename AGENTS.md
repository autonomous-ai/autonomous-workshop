# Autonomous Workshop agent instructions

`AGENTS.md` is directory-scoped guidance, not a role selector. This root file
applies to any coding-agent session operating in the source repository. Shared
architecture rules come first. The section **Coding agents building this
repository** is specifically for agents modifying, reviewing, testing, or
documenting Workshop; it is not the product-run workflow.

A normal product run is launched in a separate persistent toy project. The host
materializes the complete `.agents/product-run/` template there, including its
root `AGENTS.md` and nested `.agents/skills/autonomous-workshop/SKILL.md`.

## Shared runtime architecture

Autonomous Workshop is a thin, trustworthy workflow harness around a native
coding-agent runtime. Codex is the implemented Manager runtime; Claude Code and
Grok Build are planned adapters to the same boundary. One product run gives the
selected runtime the cognitive and tool-using work. The Workshop host retains
lifecycle order, durable state, deterministic gates, budgets, and authorized
external effects.

The root native Codex session is the Workshop Manager. It may use Codex-native
subagents for bounded parallel or specialist work, including matching and
working as the selected Inventor. Those agents remain children of the one
product-run session; they are not Python workers or separately launched Codex
processes.

All implementation and product-run work must preserve these boundaries:

- `workshop wish` persists the exact Wish and frozen effort, creates a private
  run workspace, and launches one native coding-agent session for the first
  enabled creative stage.
- `workshop resume` resumes that exact session id. Stages are durable lifecycle
  checkpoints, not separate one-shot model sessions or personas.
- Native Codex performs Inventor selection, research, concept exploration,
  creation, inspection, and repair with its own tools and applicable skills.
- New runs freeze one selectable lifecycle: Spark is `Wish -> Make -> Release`,
  Forge is `Wish -> Invent -> Make -> Release`, and Quest is
  `Wish -> Invent -> Make -> Playtest -> Release`. Passed-through stages create
  no turn, artifact, gate, or evidence. Spark/Forge Release explicitly records
  Playtest `not-run`; Quest requires passing Playtest evidence. Frozen older
  runs retain their materialized protocol when resumed.
- New Codex Spark runs also freeze their versioned economics capability and use
  one low-reasoning native session across Make and Release. Forge, Quest, other
  Managers, and older unmarked Spark runs retain their prior runtime profile.
  This changes cognitive spend only; every deterministic product and
  publication gate remains identical.
- A capable Forge or Quest Make attempt may return directly to Invent only when
  exact preserved evidence proves that the sealed concept prevents any
  conforming build. Quest Playtest returns directly to Make for implementation
  defects or to Invent for concept defects. Every backward edge records a
  failed host gate, invalidates the named downstream artifacts, and consumes
  the one shared lifecycle revision budget. Spark has no separate Invent stage
  to return to, and frozen runs gain no capability they did not materialize.
- Every active Invent, Make, Playtest, or Release attempt uses
  one native Codex Goal with one objective, proof artifacts, and a verifiable
  stopping condition: the current stage finalizer succeeds. Inventor selection
  is folded into the first active creative stage instead of a separate Match
  turn. Only one Goal is active at a time. Codex works toward it by observing,
  acting, evaluating exact output,
  and improving. That loop is native-agent behavior, not a Python program.
  Wish is a host boundary rather than an agent Goal. Authenticated publication
  is the host-owned effect portion of Release; physical Operations begin only
  after Workshop completes.
- An Inventor is a declared specialist bundle. `TASTE.md` governs creative
  judgment; `inventor.json` identifies the specialist and binds its exact
  extension trees; the required `<id>-inventor` skill defines its
  primary method, while optional additional Inventor-prefixed skill trees may
  contain scripts, references, assets, and tested deterministic tools for
  specialist craft. Custom code may not become an agent scheduler,
  prompt loop, lifecycle engine, or effect path.
- The host materializes every eligible Inventor as an official project-scoped
  Codex custom agent under `.codex/agents/`, bound to its exact identity, Taste,
  and skill bytes. That directory is the sole Inventor roster in a run. Codex
  owns native spawning, routing, and synthesis. The root session alone receives
  host stage authority and submits a stage proposal; child agents cannot
  advance gates or perform external effects.
- Python is narrow trusted substrate: typed contracts, deterministic tools and
  gates, artifact hashing, checkpoints, exclusive run-mutation locks, budgets, sandbox/session
  boundaries, authorization, idempotency, receipts, and reconciliation.
- External-effect credentials never enter the native agent subprocess. The
  host alone performs authorized Factory, payment, manufacture, postage,
  carrier, or other authenticated effects.
- Model prose and self-scores are proposals. Only host-verified exact bytes,
  deterministic checks, and reconciled receipts advance a gate.

## Coding agents building this repository

This section is for agents building the Workshop itself. It does not tell the
per-Wish product-run agent how to Invent, Make, or Playtest a product.

Do not add a second Python agent framework. Python stage agents, structured
model calls, profile subprocesses, and Python-owned scoring or reward loops are
not extension points. Never add Python prompt chains, browsing strategy,
candidate fan-out, model judges, stage-role views, or repair reasoning.

Read `docs/NATIVE_AGENT_RUNTIME.md`,
`docs/adr/0012-codex-orchestrated-runtime.md`, and
`docs/adr/0013-manual-first-release.md`, and
`docs/adr/0014-terminal-published-release.md`, and
`docs/adr/0015-defer-playtest.md`, and
`docs/adr/0016-selectable-effort-routes.md`, and
`docs/adr/0019-frozen-spark-economics-profile.md`, and
`docs/adr/0020-signature-experience-evidence.md`, and
`docs/adr/0021-compacted-spark-and-signature-review.md` before changing the CLI, runtime,
workflow, product-run instructions, or lifecycle orchestration. ADR 0013
supersedes ADR 0012's page-first Release details; ADR 0014 supersedes their
optional-publication and executable-Deliver details. ADR 0015 supersedes the
active Playtest stage while preserving truthful omission and frozen-run
compatibility. ADR 0016 supersedes ADR 0015's fixed topology for new runs while
preserving its truthful omission contract for Spark and Forge. The
native-session path is the production architecture. ADR 0019 freezes a
lower-cost Codex profile only for new marked Spark runs without changing their
gates or upgrading older sessions. ADR 0020 adds exact signature-experience
evidence and batched manual review without adding a host-side judge. ADR 0021
adds a frozen Spark compaction ceiling, final signature-review evidence, and a
bounded simple-manual path without splitting the Wish-wide session.
Preserve useful deterministic contracts and tests; do not reintroduce removed
cognitive orchestration as a compatibility layer.

## Repository ownership

- `src/cli/`: argument parsing, output formatting, and exit codes only.
- `src/workshop/runtime/`: native engine adapters and trusted state/effect
  boundaries.
- `src/workshop/workflow/`: lifecycle protocol, checkpoints, invalidation,
  frozen-run repair budgets, and the trusted whole-run host composition.
- `src/workshop/<stage>/`: stage-owned public contracts and deterministic tools.
- `src/workshop/make/skills/`: reusable domain skills owned by Make.
- `.agents/product-run/`: complete template materialized only into a toy
  project; its nested `.agents/skills/autonomous-workshop/` is intentionally
  invisible to repo-builder sessions.
- `.agents/product-run/.agents/skills/autonomous-workshop/scripts/stage_proposal.py`:
  run-local deterministic finalizer for exact stage contracts and outcome
  proposals; it does not reason or advance gates.
- `tests/<component>/`: tests mirroring the component that owns the behavior.

Keep the `src/` layout and the single `workshop` library namespace. The `cli`
package is its installed sibling under `src/`; CLI tests remain under
top-level `tests/`.

### Working rules

- Preserve unrelated user and agent changes in the shared worktree.
- Add contract and failure-path tests with every runtime or workflow change.
- Use deterministic fakes for CI; never weaken production gates to make a test
  pass.
- Never commit credentials, `.env` files, transcripts, run workspaces, build
  outputs, or private customer artifacts.
- Do not claim physical manufacture, delivery, publication, or live readiness
  from mocked or model-generated evidence.
- Keep documentation explicit about implemented behavior versus an accepted
  target that is still migrating.
- Make small coherent commits so other builder agents can pull frequently.

Builder agents may inspect the product-run skill when implementing or testing
its protocol. They must not treat that skill as authority to manufacture a
product, bypass a host gate, publish, or access effect credentials during
ordinary repository work.

## Product-run agents

A product-run agent follows the materialized product-run `AGENTS.md` and the
`autonomous-workshop` skill in its isolated run root. It performs one Wish's
cognitive work, reads the current immutable `STAGE.json`, and uses the
run-local proposal finalizer to propose compact outcomes to the host. It does
not use the builder-only section above as a product workflow, modify the
Workshop source as part of making a toy, or bypass host-owned gates and effect
authority.
